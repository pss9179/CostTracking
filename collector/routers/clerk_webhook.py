"""
Clerk Webhook Handler
Syncs Clerk users to local database and auto-generates API keys.
"""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select
import json
from typing import Optional

from models import User, APIKey, Organization, OrganizationMembership
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
        elif event_type == "organization.created":
            await handle_organization_created(data, session)
        elif event_type == "organization.updated":
            await handle_organization_updated(data, session)
        elif event_type == "organization.deleted":
            await handle_organization_deleted(data, session)
        elif event_type == "organizationMembership.created":
            await handle_membership_created(data, session)
        elif event_type == "organizationMembership.updated":
            await handle_membership_updated(data, session)
        elif event_type == "organizationMembership.deleted":
            await handle_membership_deleted(data, session)
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


async def handle_organization_created(data: dict, session: Session):
    """Create organization in local DB."""
    from models import Organization
    
    org_id = data.get("id")
    name = data.get("name")
    slug = data.get("slug")
    image_url = data.get("image_url")
    
    if not org_id:
        return

    org = Organization(
        id=org_id,
        name=name,
        slug=slug,
        image_url=image_url
    )
    session.add(org)
    try:
        session.commit()
        logger.info(f"[Clerk Webhook] Created organization {name} ({org_id})")
    except Exception as e:
        session.rollback()
        logger.error(f"[Clerk Webhook] Failed to create organization: {e}")


async def handle_organization_updated(data: dict, session: Session):
    """Update organization in local DB."""
    from models import Organization
    
    org_id = data.get("id")
    if not org_id:
        return
        
    org = session.get(Organization, org_id)
    if not org:
        await handle_organization_created(data, session)
        return
        
    org.name = data.get("name", org.name)
    org.slug = data.get("slug", org.slug)
    org.image_url = data.get("image_url", org.image_url)
    
    session.add(org)
    session.commit()
    logger.info(f"[Clerk Webhook] Updated organization {org.name} ({org_id})")


async def handle_organization_deleted(data: dict, session: Session):
    """Delete organization from local DB."""
    from models import Organization
    
    org_id = data.get("id")
    if not org_id:
        return
        
    org = session.get(Organization, org_id)
    if org:
        session.delete(org)
        session.commit()
        logger.info(f"[Clerk Webhook] Deleted organization {org_id}")


async def handle_membership_created(data: dict, session: Session):
    """Create organization membership."""
    from models import OrganizationMembership, User
    
    org_id = data.get("organization", {}).get("id")
    user_id = data.get("public_user_data", {}).get("user_id")
    role = data.get("role")
    
    if not org_id or not user_id:
        return
        
    # Find local user
    statement = select(User).where(User.clerk_user_id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        logger.warning(f"[Clerk Webhook] User {user_id} not found for membership creation")
        return
        
    membership = OrganizationMembership(
        organization_id=org_id,
        user_id=user.id,
        role=role
    )
    session.add(membership)
    try:
        session.commit()
        logger.info(f"[Clerk Webhook] Created membership for user {user.email} in org {org_id}")
    except Exception as e:
        session.rollback()
        logger.error(f"[Clerk Webhook] Failed to create membership: {e}")


async def handle_membership_updated(data: dict, session: Session):
    """Update organization membership."""
    from models import OrganizationMembership, User
    
    org_id = data.get("organization", {}).get("id")
    user_id = data.get("public_user_data", {}).get("user_id")
    role = data.get("role")
    
    if not org_id or not user_id:
        return
        
    statement = select(User).where(User.clerk_user_id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        return
        
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user.id
    )
    membership = session.exec(mem_stmt).first()
    
    if not membership:
        await handle_membership_created(data, session)
        return
        
    membership.role = role
    session.add(membership)
    session.commit()
    logger.info(f"[Clerk Webhook] Updated membership for user {user.email} in org {org_id}")


async def handle_membership_deleted(data: dict, session: Session):
    """Delete organization membership."""
    from models import OrganizationMembership, User
    
    org_id = data.get("organization", {}).get("id")
    user_id = data.get("public_user_data", {}).get("user_id")
    
    if not org_id or not user_id:
        return
        
    statement = select(User).where(User.clerk_user_id == user_id)
    user = session.exec(statement).first()
    
    if not user:
        return
        
    mem_stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == org_id,
        OrganizationMembership.user_id == user.id
    )
    membership = session.exec(mem_stmt).first()
    
    if membership:
        session.delete(membership)
        session.commit()
        logger.info(f"[Clerk Webhook] Deleted membership for user {user.email} in org {org_id}")

