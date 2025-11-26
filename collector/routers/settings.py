"""
User settings API endpoints.

Handles user preferences including pricing plan settings for accurate cost tracking.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional

from collector.database import get_session
from collector.models import (
    PricingSettings,
    PricingSettingsUpdate,
    PricingSettingsResponse,
    User,
)
from collector.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])

# Valid plan options for each provider
VALID_PLANS = {
    "cartesia": [
        "pro-monthly", "pro-yearly",
        "startup-monthly", "startup-yearly",
        "scale-monthly", "scale-yearly"
    ],
    "elevenlabs": ["creator", "pro", "scale", "business"],
    "playht": ["creator", "pro", "growth", "business"],
}

# Pricing lookup tables (cost per 1K chars/credits)
CARTESIA_PRICING = {
    "pro-monthly": 0.050,
    "pro-yearly": 0.040,
    "startup-monthly": 0.039,
    "startup-yearly": 0.031,
    "scale-monthly": 0.037,
    "scale-yearly": 0.030,
}

ELEVENLABS_TTS_PRICING = {
    "creator": 0.30,  # per 1K chars
    "pro": 0.24,
    "scale": 0.18,
    "business": 0.12,
}

PLAYHT_PRICING = {
    "creator": 0.050,  # per 1K chars
    "pro": 0.040,
    "growth": 0.035,
    "business": 0.030,
}


@router.get("/pricing", response_model=PricingSettingsResponse)
async def get_pricing_settings(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get user's pricing settings for all providers.
    Returns defaults if no settings exist.
    """
    settings = session.exec(
        select(PricingSettings).where(PricingSettings.user_id == user.id)
    ).first()
    
    if not settings:
        # Return defaults
        return PricingSettingsResponse(
            cartesia_plan="startup-yearly",
            elevenlabs_tier="pro",
            playht_plan="pro",
            updated_at=datetime.utcnow(),
        )
    
    return PricingSettingsResponse(
        cartesia_plan=settings.cartesia_plan,
        elevenlabs_tier=settings.elevenlabs_tier,
        playht_plan=settings.playht_plan,
        updated_at=settings.updated_at,
    )


@router.post("/pricing", response_model=PricingSettingsResponse)
async def update_pricing_settings(
    updates: PricingSettingsUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Update user's pricing settings.
    Only updates fields that are provided.
    """
    # Validate plans
    if updates.cartesia_plan and updates.cartesia_plan not in VALID_PLANS["cartesia"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Cartesia plan. Valid options: {VALID_PLANS['cartesia']}"
        )
    
    if updates.elevenlabs_tier and updates.elevenlabs_tier not in VALID_PLANS["elevenlabs"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ElevenLabs tier. Valid options: {VALID_PLANS['elevenlabs']}"
        )
    
    if updates.playht_plan and updates.playht_plan not in VALID_PLANS["playht"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid PlayHT plan. Valid options: {VALID_PLANS['playht']}"
        )
    
    # Get or create settings
    settings = session.exec(
        select(PricingSettings).where(PricingSettings.user_id == user.id)
    ).first()
    
    if not settings:
        settings = PricingSettings(user_id=user.id)
        session.add(settings)
    
    # Update fields
    if updates.cartesia_plan:
        settings.cartesia_plan = updates.cartesia_plan
    if updates.elevenlabs_tier:
        settings.elevenlabs_tier = updates.elevenlabs_tier
    if updates.playht_plan:
        settings.playht_plan = updates.playht_plan
    
    settings.updated_at = datetime.utcnow()
    
    session.commit()
    session.refresh(settings)
    
    return PricingSettingsResponse(
        cartesia_plan=settings.cartesia_plan,
        elevenlabs_tier=settings.elevenlabs_tier,
        playht_plan=settings.playht_plan,
        updated_at=settings.updated_at,
    )


@router.get("/pricing/options")
async def get_pricing_options():
    """
    Get all valid pricing plan options and their rates.
    Useful for populating dropdowns in the UI.
    """
    return {
        "cartesia": {
            "options": VALID_PLANS["cartesia"],
            "rates": CARTESIA_PRICING,
            "unit": "per 1K characters",
            "description": "Cartesia Sonic TTS pricing by plan",
        },
        "elevenlabs": {
            "options": VALID_PLANS["elevenlabs"],
            "rates": ELEVENLABS_TTS_PRICING,
            "unit": "per 1K characters",
            "description": "ElevenLabs TTS pricing by tier",
        },
        "playht": {
            "options": VALID_PLANS["playht"],
            "rates": PLAYHT_PRICING,
            "unit": "per 1K characters",
            "description": "PlayHT TTS pricing by plan",
        },
    }

