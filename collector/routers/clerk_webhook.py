"""
Clerk Webhook Handler
Syncs Clerk users to local database and auto-generates API keys.
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select
import json
from typing import Optional

from models import User, APIKey
from db import get_session
from auth import generate_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/clerk", tags=["webhooks"])


@router.post("")
async def handle_clerk_webhook(
    request: Request,
    session: Session = Depends(get_session)
):
    """
    Handle Clerk webhook events (user.created, user.updated, user.deleted).
    Creates/updates users in local DB and auto-generates API keys.
    """
    try:
        # Get webhook payload
        payload = await request.json()
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        logger.info(f"[Clerk Webhook] Received event: {event_type}")
        
        if event_type == "user.created":
            await handle_user_created(data, session)
        elif event_type == "user.updated":
            await handle_user_updated(data, session)
        elif event_type == "user.deleted":
            await handle_user_deleted(data, session)
        else:
            logger.warning(f"[Clerk Webhook] Unhandled event type: {event_type}")
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"[Clerk Webhook] Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_user_created(data: dict, session: Session):
    """Create user in local DB and generate API key."""
    clerk_user_id = data.get("id")
    email = data.get("email_addresses", [{}])[0].get("email_address")
    
    if not clerk_user_id or not email:
        logger.error("[Clerk Webhook] Missing user ID or email")
        return
    
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
            logger.info(f"[Clerk Webhook] Updated existing user {email} with Clerk ID {clerk_user_id}")
            return
    
    if existing_user:
        logger.info(f"[Clerk Webhook] User {email} already exists, skipping")
        return
    
    # Create user
    try:
        user = User(
            clerk_user_id=clerk_user_id,
            email=email,
            name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or None,
            subscription_tier="free"
        )
        session.add(user)
        session.flush()  # Get user ID
        
        # Auto-generate API key
        api_key = generate_api_key()
        api_key_record = APIKey(
            user_id=user.id,
            key_hash=api_key,  # Will be hashed by model
            key_prefix=api_key[:12],
            name="Default API Key"
        )
        session.add(api_key_record)
        session.commit()
        
        logger.info(f"[Clerk Webhook] Created user {email} with API key {api_key_record.key_prefix}...")
    except Exception as e:
        # Handle race condition: user might have been created by another request
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            logger.warning(f"[Clerk Webhook] Race condition detected, user was created by another request. Looking up again...")
            session.rollback()
            # Try to find the user again
            statement = select(User).where(User.clerk_user_id == clerk_user_id)
            user = session.exec(statement).first()
            if not user and email:
                email_statement = select(User).where(User.email == email)
                user = session.exec(email_statement).first()
            if user:
                logger.info(f"[Clerk Webhook] Found existing user after race condition: {user.email} (ID: {user.id})")
            else:
                logger.error(f"[Clerk Webhook] Failed to create or find user after race condition: {str(e)}")
        else:
            raise


async def handle_user_updated(data: dict, session: Session):
    """Update user in local DB."""
    clerk_user_id = data.get("id")
    email = data.get("email_addresses", [{}])[0].get("email_address")
    
    if not clerk_user_id:
        return
    
    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    user = session.exec(statement).first()
    
    if not user:
        logger.warning(f"[Clerk Webhook] User {clerk_user_id} not found, creating...")
        await handle_user_created(data, session)
        return
    
    # Update user fields
    if email:
        user.email = email
    if data.get("first_name") or data.get("last_name"):
        user.name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or None
    
    session.add(user)
    session.commit()
    logger.info(f"[Clerk Webhook] Updated user {email}")


async def handle_user_deleted(data: dict, session: Session):
    """Soft-delete user (keep data for historical tracking)."""
    clerk_user_id = data.get("id")
    
    if not clerk_user_id:
        return
    
    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    user = session.exec(statement).first()
    
    if user:
        # Mark user as deleted (you could add a `deleted_at` field)
        # For now, just log it
        logger.info(f"[Clerk Webhook] User {user.email} deleted (keeping data)")
    else:
        logger.warning(f"[Clerk Webhook] User {clerk_user_id} not found for deletion")

