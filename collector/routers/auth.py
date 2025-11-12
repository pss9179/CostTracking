"""
Authentication and API key management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import User, APIKey, APIKeyCreate, APIKeyResponse, APIKeyListItem
from auth import generate_api_key, hash_api_key, get_key_prefix, get_current_user, get_current_user_id
from uuid import UUID

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    *,
    session: Session = Depends(get_session),
    key_data: APIKeyCreate,
    user_id: UUID = Depends(get_current_user_id)
) -> APIKeyResponse:
    """
    Create a new API key for the current user.
    
    Requires authentication (existing API key or session).
    Returns the full API key - save it securely, it won't be shown again.
    """
    # Generate API key
    api_key_plain = generate_api_key()
    key_hash = hash_api_key(api_key_plain)
    
    # Create API key record
    api_key = APIKey(
        user_id=user_id,
        key_hash=key_hash,
        name=key_data.name,
        key_prefix=get_key_prefix(api_key_plain)
    )
    
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    
    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        api_key=api_key_plain,  # Only time the full key is returned
        created_at=api_key.created_at
    )


@router.get("", response_model=List[APIKeyListItem])
async def list_api_keys(
    *,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id)
) -> List[APIKeyListItem]:
    """
    List all API keys for the current user.
    
    Does not return the actual key values, only metadata.
    """
    statement = select(APIKey).where(
        APIKey.user_id == user_id,
        APIKey.revoked_at.is_(None)
    ).order_by(APIKey.created_at.desc())
    
    api_keys = session.exec(statement).all()
    
    return [
        APIKeyListItem(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            created_at=key.created_at,
            last_used_at=key.last_used_at
        )
        for key in api_keys
    ]


@router.delete("/{key_id}")
async def revoke_api_key(
    *,
    key_id: UUID,
    session: Session = Depends(get_session),
    user_id: UUID = Depends(get_current_user_id)
) -> dict:
    """
    Revoke an API key.
    
    The key will no longer be usable for authentication.
    """
    from datetime import datetime
    
    api_key = session.get(APIKey, key_id)
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    if api_key.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this API key")
    
    if api_key.revoked_at:
        raise HTTPException(status_code=400, detail="API key already revoked")
    
    api_key.revoked_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    
    return {"message": "API key revoked successfully"}


@router.get("/me")
async def get_current_user_info(
    user: User = Depends(get_current_user)
) -> dict:
    """
    Get current authenticated user's information.
    
    Requires Authorization: Bearer <api_key> header.
    """
    return {
        "id": str(user.id),
        "clerk_user_id": user.clerk_user_id,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }
