"""
API Key management endpoints using Clerk authentication.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from models import User, APIKey, APIKeyListItem, APIKeyResponse
from db import get_session
from clerk_auth import get_current_clerk_user
from auth import generate_api_key
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clerk/api-keys", tags=["api-keys"])


@router.get("/me", response_model=dict)
async def get_current_user_with_keys(
    current_user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session)
):
    """Get current user's profile and API keys."""
    # Fetch user's API keys
    statement = select(APIKey).where(
        APIKey.user_id == current_user.id,
        APIKey.revoked_at == None
    )
    api_keys = session.exec(statement).all()
    
    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "clerk_user_id": current_user.clerk_user_id,
            "user_type": current_user.user_type,
            "created_at": current_user.created_at.isoformat(),
            "subscription_tier": current_user.subscription_tier
        },
        "api_keys": [
            {
                "id": str(key.id),
                "name": key.name,
                "key_prefix": key.key_prefix,
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None
            }
            for key in api_keys
        ]
    }


@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    name: str,
    current_user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session)
):
    """Create a new API key for the authenticated user."""
    # Generate new API key
    api_key = generate_api_key()
    
    # Create API key record
    api_key_record = APIKey(
        user_id=current_user.id,
        key_hash=api_key,  # Will be hashed by model
        key_prefix=api_key[:12],
        name=name
    )
    
    session.add(api_key_record)
    session.commit()
    session.refresh(api_key_record)
    
    logger.info(f"[Clerk API Keys] Created API key for user {current_user.email}")
    
    return APIKeyResponse(
        id=api_key_record.id,
        name=api_key_record.name,
        key=api_key,  # Full key returned only once!
        key_prefix=api_key_record.key_prefix,
        created_at=api_key_record.created_at
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session)
):
    """Revoke an API key."""
    # Find the API key
    statement = select(APIKey).where(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    )
    api_key = session.exec(statement).first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    # Mark as revoked
    api_key.revoked_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    
    logger.info(f"[Clerk API Keys] Revoked API key {api_key.key_prefix}... for user {current_user.email}")
    
    return {"status": "revoked", "key_id": key_id}

