"""
User management endpoints (for Clerk webhooks).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, UserCreate
from ..auth import generate_api_key, hash_api_key, get_key_prefix
from ..models import APIKey

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/clerk-webhook")
async def clerk_webhook(
    payload: dict,
    session: Session = Depends(get_session),
):
    """
    Webhook endpoint for Clerk user events.
    
    Automatically creates a User record when someone signs up.
    Also generates their first API key.
    """
    event_type = payload.get("type")
    
    if event_type == "user.created":
        data = payload.get("data", {})
        clerk_user_id = data.get("id")
        email = data.get("email_addresses", [{}])[0].get("email_address")
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        name = f"{first_name} {last_name}".strip() or None
        
        if not clerk_user_id or not email:
            raise HTTPException(status_code=400, detail="Missing required user data")
        
        # Check if user already exists
        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            return {"message": "User already exists", "user_id": str(existing_user.id)}
        
        # Create user
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            name=name,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        
        # Auto-generate first API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = get_key_prefix(api_key)
        
        first_key = APIKey(
            user_id=user.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Default API Key",
        )
        session.add(first_key)
        session.commit()
        
        return {
            "message": "User created successfully",
            "user_id": str(user.id),
            "api_key_created": True,
        }
    
    return {"message": "Event received"}


@router.post("/sync")
async def sync_user_from_clerk(
    clerk_user: dict,
    session: Session = Depends(get_session),
):
    """
    Manually sync a user from Clerk (for testing/onboarding).
    
    Request body should include:
    - id: Clerk user ID
    - email_addresses: [{ email_address: "..." }]
    - first_name, last_name (optional)
    """
    clerk_user_id = clerk_user.get("id")
    email = clerk_user.get("email_addresses", [{}])[0].get("email_address")
    first_name = clerk_user.get("first_name", "")
    last_name = clerk_user.get("last_name", "")
    name = f"{first_name} {last_name}".strip() or None
    
    if not clerk_user_id or not email:
        raise HTTPException(status_code=400, detail="Missing required user data")
    
    # Check if user already exists
    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        return {
            "message": "User already exists",
            "user_id": str(existing_user.id),
            "created": False,
        }
    
    # Create user
    user = User(
        clerk_user_id=clerk_user_id,
        email=email,
        name=name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Auto-generate first API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = get_key_prefix(api_key)
    
    first_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name="Default API Key",
    )
    session.add(first_key)
    session.commit()
    session.refresh(first_key)
    
    return {
        "message": "User created successfully",
        "user_id": str(user.id),
        "api_key": api_key,  # Return first key for onboarding
        "api_key_prefix": key_prefix,
        "created": True,
    }

