"""
Events router - handles ingestion of trace events.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from models import TraceEvent, TraceEventCreate
from db import get_session
from pricing import compute_cost

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", status_code=201)
def ingest_events(
    events: List[TraceEventCreate],
    session: Session = Depends(get_session)
) -> dict:
    """
    Batch ingest trace events.
    
    Computes cost if not provided and usage data is available.
    """
    created_count = 0
    
    for event_data in events:
        # Compute cost if not already set and we have token data
        if event_data.cost_usd == 0.0 and (event_data.input_tokens > 0 or event_data.output_tokens > 0):
            event_data.cost_usd = compute_cost(
                provider=event_data.provider,
                model=event_data.model,
                input_tokens=event_data.input_tokens,
                output_tokens=event_data.output_tokens
            )
        
        # Create TraceEvent from TraceEventCreate
        event = TraceEvent(**event_data.model_dump())
        session.add(event)
        created_count += 1
    
    session.commit()
    
    return {
        "status": "success",
        "created": created_count
    }

