"""
API Key management endpoints.
"""
from datetime import datetime
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import (
    APIKey,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyListItem,
    User,
)
from auth import (
    generate_api_key,
    hash_api_key,
    get_key_prefix,
    get_current_user,
)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Generate a new API key for the authenticated user.
    
    The full API key is returned only once. Make sure to save it!
    """
    # Generate new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_key_prefix(api_key)
    
    # Create database record
    db_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=key_data.name,
    )
    
    session.add(db_key)
    session.commit()
    session.refresh(db_key)
    
    # Return response with full key (only time we show it!)
    return APIKeyResponse(
        id=db_key.id,
        name=db_key.name,
        key=api_key,  # Full plaintext key
        key_prefix=key_prefix,
        created_at=db_key.created_at,
    )


@router.get("", response_model=List[APIKeyListItem])
async def list_api_keys(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    List all API keys for the authenticated user.
    
    Does not include full keys, only prefixes for security.
    """
    statement = (
        select(APIKey)
        .where(APIKey.user_id == user.id)
        .where(APIKey.revoked_at.is_(None))
        .order_by(APIKey.created_at.desc())
    )
    
    keys = session.exec(statement).all()
    
    return [
        APIKeyListItem(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
        )
        for key in keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Revoke (delete) an API key.
    
    The key will no longer work for authentication.
    """
    # Get the key
    statement = select(APIKey).where(
        APIKey.id == key_id,
        APIKey.user_id == user.id,
    )
    key = session.exec(statement).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if key.revoked_at:
        raise HTTPException(status_code=400, detail="API key already revoked")
    
    # Soft delete by setting revoked_at
    key.revoked_at = datetime.utcnow()
    session.add(key)
    session.commit()
    
    return {"message": "API key revoked successfully"}

