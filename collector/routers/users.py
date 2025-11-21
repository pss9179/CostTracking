"""
User management endpoints (for Clerk webhooks).
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from db import get_session
from models import User, APIKey
from auth import generate_api_key, hash_api_key, get_key_prefix

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
    Manually sync a user from Clerk (called during onboarding).
    This is the PRIMARY way users are created - webhook is backup.
    Updates existing user or creates new one.
    
    Request body should include:
    - id: Clerk user ID
    - email_addresses: [{ email_address: "..." }]
    - first_name, last_name (optional)
    - user_type: "solo_dev" or "saas_founder" (optional)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    clerk_user_id = clerk_user.get("id")
    email = clerk_user.get("email_addresses", [{}])[0].get("email_address")
    first_name = clerk_user.get("first_name", "")
    last_name = clerk_user.get("last_name", "")
    user_type = clerk_user.get("user_type", "solo_dev")  # Default to solo_dev
    name = f"{first_name} {last_name}".strip() or None
    
    if not clerk_user_id or not email:
        logger.error(f"[Users/Sync] Missing required data: clerk_user_id={clerk_user_id}, email={email}")
        raise HTTPException(status_code=400, detail="Missing required user data: id and email_addresses required")
    
    # Check if user already exists by clerk_user_id
    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    existing_user = session.exec(statement).first()
    
    # Also check by email in case user exists with different clerk_user_id
    if not existing_user and email:
        email_statement = select(User).where(User.email == email)
        existing_user = session.exec(email_statement).first()
        if existing_user and not existing_user.clerk_user_id:
            # Update existing user with clerk_user_id
            existing_user.clerk_user_id = clerk_user_id
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
    
    if existing_user:
        # Update existing user with latest info from Clerk
        if email and existing_user.email != email:
            existing_user.email = email
        if name:
            existing_user.name = name
        # Only update user_type if it's provided and different
        if user_type and user_type != existing_user.user_type:
            existing_user.user_type = user_type
        session.add(existing_user)
        session.commit()
        session.refresh(existing_user)
        
        return {
            "message": "User updated successfully",
            "user_id": str(existing_user.id),
            "user_type": existing_user.user_type,
            "created": False,
        }
    
    # Create new user (PRIMARY creation method - called during onboarding)
    logger.info(f"[Users/Sync] Creating new user: {email} (Clerk ID: {clerk_user_id}, Type: {user_type})")
    try:
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            name=name,
            user_type=user_type,  # Set user type from signup
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        # Handle race condition: user might have been created by another request
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            logger.warning(f"[Users/Sync] Race condition detected, user was created by another request. Looking up again...")
            session.rollback()
            # Try to find the user again
            statement = select(User).where(User.clerk_user_id == clerk_user_id)
            user = session.exec(statement).first()
            if not user and email:
                email_statement = select(User).where(User.email == email)
                user = session.exec(email_statement).first()
            if not user:
                raise HTTPException(status_code=500, detail=f"Failed to create or find user after race condition: {str(e)}")
            # User found, continue with existing user
            logger.info(f"[Users/Sync] Found existing user after race condition: {user.email} (ID: {user.id})")
        else:
            raise
    
    logger.info(f"[Users/Sync] User created: {user.email} (ID: {user.id})")
    
    # Auto-generate first API key for new users
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
    
    logger.info(f"[Users/Sync] API key created for user {user.email}: {key_prefix}...")
    
    return {
        "message": "User created successfully",
        "user_id": str(user.id),
        "user_type": user.user_type,
        "api_key": api_key,  # Return first key for onboarding
        "api_key_prefix": key_prefix,
        "created": True,
    }

