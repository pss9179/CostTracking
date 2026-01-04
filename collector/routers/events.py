"""
Events router - handles ingestion of trace events.

FEATURES:
- Batch ingestion with idempotency
- Automatic cost calculation with batch API discounts
- Clock skew detection
- Rate limit event filtering
- Failed request filtering (5xx errors)
"""
from typing import List, Optional
from uuid import UUID
import time
import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session
from models import TraceEvent, TraceEventCreate
from db import get_session
from pricing import compute_cost
from auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", status_code=201)
def ingest_events(
    events: List[TraceEventCreate],
    user_id: Optional[UUID] = Depends(get_current_user_id),
    session: Session = Depends(get_session),
    # Optional headers for advanced features
    x_llmobserve_timestamp: Optional[str] = Header(None, alias="X-LLMObserve-Timestamp"),
    x_llmobserve_batch_api: Optional[str] = Header(None, alias="X-LLMObserve-Batch-API"),
    x_llmobserve_discount: Optional[str] = Header(None, alias="X-LLMObserve-Discount")
) -> dict:
    """
    Batch ingest trace events with advanced features.
    
    FEATURES:
    - Idempotency (skip duplicates based on span_id)
    - Automatic cost calculation
    - Batch API discount (50% for OpenAI Batch API)
    - Clock skew detection
    - Rate limit event filtering (429)
    - Failed request filtering (5xx)
    
    HEADERS:
    - Authorization: Bearer <api_key> (required)
    - X-LLMObserve-Timestamp: Unix timestamp for clock skew detection
    - X-LLMObserve-Batch-API: "true" if using batch API
    - X-LLMObserve-Discount: Discount multiplier (e.g., "0.5" for 50% off)
    """
    try:
        created_count = 0
        skipped_count = 0
        filtered_count = 0
        
        # Validate timestamp for clock skew
        if x_llmobserve_timestamp:
            try:
                # Ensure it's a string before converting to float
                timestamp_str = str(x_llmobserve_timestamp) if x_llmobserve_timestamp else None
                if timestamp_str:
                    client_timestamp = float(timestamp_str)
                    server_timestamp = time.time()
                    clock_skew = abs(client_timestamp - server_timestamp)
                    
                    if clock_skew > 300:  # 5 minutes
                        logger.warning(
                            f"[events] Clock skew detected: {clock_skew:.2f}s "
                            f"(user_id={user_id})"
                        )
            except (ValueError, TypeError) as e:
                logger.error(f"[events] Invalid timestamp header: {x_llmobserve_timestamp} - {e}")
        
        # Parse discount if provided
        discount_multiplier = 1.0
        if x_llmobserve_batch_api == "true" and x_llmobserve_discount:
            try:
                discount_multiplier = float(x_llmobserve_discount)
                logger.info(f"[events] Batch API discount applied: {discount_multiplier}")
            except ValueError:
                logger.error(f"[events] Invalid discount header: {x_llmobserve_discount}")
        
        # Process each event
        for event_data in events:
            # Extract status_code from event_metadata if available
            status_code = None
            if event_data.event_metadata and isinstance(event_data.event_metadata, dict):
                status_code = event_data.event_metadata.get("http_status")
            
            # Filter out rate limit events (429)
            if status_code == 429:
                filtered_count += 1
                logger.debug(f"[events] Filtered rate limit event (429)")
                continue
            
            # Filter out server errors (5xx) - these typically aren't charged
            if status_code and 500 <= status_code < 600:
                filtered_count += 1
                logger.debug(f"[events] Filtered server error ({status_code})")
                continue
            
            # Idempotency check: skip if event with same span_id already exists
            if event_data.span_id:
                from sqlmodel import select
                statement = select(TraceEvent).where(TraceEvent.span_id == event_data.span_id)
                existing = session.exec(statement).first()
                
                if existing:
                    skipped_count += 1
                    continue  # Skip duplicate event (likely retry)
            
            # CRITICAL: Always compute cost if we have token data, even if SDK sent 0
            # This ensures costs are never $0 for valid API calls
            if event_data.input_tokens > 0 or event_data.output_tokens > 0:
                if event_data.cost_usd == 0.0:
                    # SDK didn't calculate cost, compute it server-side
                    base_cost = compute_cost(
                        provider=event_data.provider,
                        model=event_data.model,
                        input_tokens=event_data.input_tokens,
                        output_tokens=event_data.output_tokens
                    )
                    
                    # Apply batch API discount
                    event_data.cost_usd = base_cost * discount_multiplier
                    
                    if base_cost > 0:
                        logger.info(
                            f"[events] Computed cost server-side: "
                            f"{event_data.provider}/{event_data.model}: "
                            f"${base_cost:.6f} → ${event_data.cost_usd:.6f}"
                        )
                elif discount_multiplier < 1.0:
                    # SDK sent cost, but apply batch API discount
                    original_cost = event_data.cost_usd
                    event_data.cost_usd = original_cost * discount_multiplier
                    logger.debug(
                        f"[events] Applied {discount_multiplier}x discount: "
                        f"${original_cost:.6f} → ${event_data.cost_usd:.6f}"
                    )
            
            # Create TraceEvent from TraceEventCreate
            event_dict = event_data.model_dump()
            
            # Handle tenant_id: CRITICAL for dashboard filtering
            # Dashboard filters by Clerk user ID, so tenant_id must match clerk_user_id
            if user_id:
                # Look up User to get clerk_user_id for tenant_id
                from models import User
                user = session.get(User, user_id)
                if user and user.clerk_user_id:
                    # Use Clerk user ID as tenant_id so dashboard can filter correctly
                    event_dict["tenant_id"] = user.clerk_user_id
                else:
                    # Fallback: use user_id as string if no clerk_user_id
                    event_dict["tenant_id"] = str(user_id)
                event_dict["user_id"] = user_id
            elif not event_dict.get("tenant_id"):
                event_dict["tenant_id"] = "default_tenant"
            
            try:
                event = TraceEvent(**event_dict)
                session.add(event)
                created_count += 1
            except Exception as e:
                logger.error(f"[events] Failed to create event: {e}")
                logger.error(f"[events] Event dict: {event_dict}")
                import traceback
                logger.error(f"[events] Traceback: {traceback.format_exc()}")
                # Continue processing other events
                continue
        
        # Commit all events at once
        try:
            session.commit()
        except Exception as e:
            logger.error(f"[events] Failed to commit events: {e}")
            import traceback
            logger.error(f"[events] Traceback: {traceback.format_exc()}")
            session.rollback()
            raise
        
        logger.info(
            f"[events] Ingested {created_count} events, "
            f"skipped {skipped_count} duplicates, "
            f"filtered {filtered_count} invalid (user_id={user_id})"
        )
        
        return {
            "status": "success",
            "created": created_count,
            "skipped": skipped_count,
            "filtered": filtered_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[events] Fatal error ingesting events: {e}")
        import traceback
        logger.error(f"[events] Traceback: {traceback.format_exc()}")
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to ingest events: {str(e)}")
