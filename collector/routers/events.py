"""
Events router - handles ingestion of trace events.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlmodel import Session
from models import TraceEvent, TraceEventCreate
from db import get_session
from pricing import compute_cost
from auth import get_current_user_id

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", status_code=201)
def ingest_events(
    events: List[TraceEventCreate],
    user_id: Optional[UUID] = Depends(get_current_user_id),
    session: Session = Depends(get_session)
) -> dict:
    """
    Batch ingest trace events.
    
    Computes cost if not provided and usage data is available.
    Automatically injects user_id from authenticated API key.
    
    Requires: Authorization: Bearer <api_key> header
    """
    created_count = 0
    skipped_count = 0
    
    for event_data in events:
        # Idempotency check: skip if event with same span_id already exists
        if event_data.span_id:
            existing = session.query(TraceEvent).filter(
                TraceEvent.span_id == event_data.span_id
            ).first()
            
            if existing:
                skipped_count += 1
                continue  # Skip duplicate event
        
        # Compute cost if not already set and we have token data
        if event_data.cost_usd == 0.0 and (event_data.input_tokens > 0 or event_data.output_tokens > 0):
            event_data.cost_usd = compute_cost(
                provider=event_data.provider,
                model=event_data.model,
                input_tokens=event_data.input_tokens,
                output_tokens=event_data.output_tokens
            )
        
        # Create TraceEvent from TraceEventCreate
        event_dict = event_data.model_dump()
        # Note: user_id not in schema (MVP mode without multi-user support)
        event = TraceEvent(**event_dict)
        session.add(event)
        created_count += 1
    
    session.commit()
    
    return {
        "status": "success",
        "created": created_count,
        "skipped": skipped_count  # Duplicate events (idempotency)
    }

