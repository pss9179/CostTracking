"""
Stripe webhook and subscription management endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import User
from clerk_auth import get_current_clerk_user

router = APIRouter(prefix="/users/stripe", tags=["stripe"])


@router.post("/webhook")
async def stripe_webhook(
    payload: dict,
    session: Session = Depends(get_session),
):
    """
    Handle Stripe webhook events to update user subscription status.
    """
    clerk_user_id = payload.get("clerk_user_id")
    stripe_customer_id = payload.get("stripe_customer_id")
    stripe_subscription_id = payload.get("stripe_subscription_id")
    subscription_status = payload.get("subscription_status", "free")
    
    user = None
    
    # Try to find user by clerk_user_id first
    if clerk_user_id:
        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        user = session.exec(statement).first()
    
    # If not found and we have subscription_id, try finding by subscription_id
    if not user and stripe_subscription_id:
        statement = select(User).where(User.stripe_subscription_id == stripe_subscription_id)
        user = session.exec(statement).first()
    
    # If still not found and we have customer_id, try finding by customer_id
    if not user and stripe_customer_id:
        statement = select(User).where(User.stripe_customer_id == stripe_customer_id)
        user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update subscription info
    if stripe_customer_id:
        user.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id:
        user.stripe_subscription_id = stripe_subscription_id
    user.subscription_status = subscription_status
    if subscription_status == "active":
        user.subscription_tier = "pro"
    elif subscription_status == "canceled":
        user.subscription_tier = "free"
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {"message": "Subscription updated", "user_id": str(user.id)}


@router.post("/promo-code")
async def apply_promo_code(
    promo_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_clerk_user),
):
    """
    Apply a promo code to give user free access.
    """
    promo_code = promo_data.get("promo_code", "").upper()
    
    # Valid promo codes (you can make this dynamic later)
    valid_codes = ["FREETEST", "TEST2024", "BETA"]
    
    if promo_code not in valid_codes:
        raise HTTPException(status_code=400, detail="Invalid promo code")
    
    # Apply promo code
    current_user.promo_code = promo_code
    current_user.subscription_status = "active"
    current_user.subscription_tier = "pro"
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return {
        "message": "Promo code applied successfully",
        "subscription_status": current_user.subscription_status,
    }

