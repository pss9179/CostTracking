"""
User settings API endpoints.

Handles user preferences including pricing plan settings for accurate cost tracking.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

from db import get_session
from models import User
from clerk_auth import get_current_clerk_user

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
    "deepgram": ["payg", "growth"],
    "speechmatics": ["selfserve", "scaling"],
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


class PricingSettingsUpdate(BaseModel):
    cartesia_plan: Optional[str] = None
    elevenlabs_tier: Optional[str] = None
    playht_plan: Optional[str] = None
    deepgram_tier: Optional[str] = None
    speechmatics_tier: Optional[str] = None


class PricingSettingsResponse(BaseModel):
    cartesia_plan: str = "startup-yearly"
    elevenlabs_tier: str = "pro"
    playht_plan: str = "pro"
    deepgram_tier: str = "payg"
    speechmatics_tier: str = "selfserve"
    updated_at: datetime


# In-memory storage for now (would be in DB in production)
_user_settings: Dict[str, Dict[str, Any]] = {}


@router.get("/pricing")
async def get_pricing_settings(
    current_user = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """
    Get user's pricing settings for all providers.
    Returns defaults if no settings exist.
    """
    user_id = str(current_user.id)
    
    if user_id in _user_settings:
        settings = _user_settings[user_id]
        return PricingSettingsResponse(
            cartesia_plan=settings.get("cartesia_plan", "startup-yearly"),
            elevenlabs_tier=settings.get("elevenlabs_tier", "pro"),
            playht_plan=settings.get("playht_plan", "pro"),
            deepgram_tier=settings.get("deepgram_tier", "payg"),
            speechmatics_tier=settings.get("speechmatics_tier", "selfserve"),
            updated_at=settings.get("updated_at", datetime.utcnow()),
        )
    
    # Return defaults
    return PricingSettingsResponse(
        cartesia_plan="startup-yearly",
        elevenlabs_tier="pro",
        playht_plan="pro",
        deepgram_tier="payg",
        speechmatics_tier="selfserve",
        updated_at=datetime.utcnow(),
    )


@router.post("/pricing")
async def update_pricing_settings(
    updates: PricingSettingsUpdate,
    current_user = Depends(get_current_clerk_user),
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
    
    if updates.deepgram_tier and updates.deepgram_tier not in VALID_PLANS["deepgram"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Deepgram tier. Valid options: {VALID_PLANS['deepgram']}"
        )
    
    if updates.speechmatics_tier and updates.speechmatics_tier not in VALID_PLANS["speechmatics"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Speechmatics tier. Valid options: {VALID_PLANS['speechmatics']}"
        )
    
    user_id = str(current_user.id)
    
    # Get or create settings
    if user_id not in _user_settings:
        _user_settings[user_id] = {
            "cartesia_plan": "startup-yearly",
            "elevenlabs_tier": "pro",
            "playht_plan": "pro",
            "deepgram_tier": "payg",
            "speechmatics_tier": "selfserve",
            "updated_at": datetime.utcnow(),
        }
    
    settings = _user_settings[user_id]
    
    # Update fields
    if updates.cartesia_plan:
        settings["cartesia_plan"] = updates.cartesia_plan
    if updates.elevenlabs_tier:
        settings["elevenlabs_tier"] = updates.elevenlabs_tier
    if updates.playht_plan:
        settings["playht_plan"] = updates.playht_plan
    if updates.deepgram_tier:
        settings["deepgram_tier"] = updates.deepgram_tier
    if updates.speechmatics_tier:
        settings["speechmatics_tier"] = updates.speechmatics_tier
    
    settings["updated_at"] = datetime.utcnow()
    
    return PricingSettingsResponse(
        cartesia_plan=settings["cartesia_plan"],
        elevenlabs_tier=settings["elevenlabs_tier"],
        playht_plan=settings["playht_plan"],
        deepgram_tier=settings["deepgram_tier"],
        speechmatics_tier=settings["speechmatics_tier"],
        updated_at=settings["updated_at"],
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
        "deepgram": {
            "options": VALID_PLANS["deepgram"],
            "description": "Deepgram Pay As You Go vs Growth tier",
        },
        "speechmatics": {
            "options": VALID_PLANS["speechmatics"],
            "description": "Speechmatics Self-Serve vs Scaling tier",
        },
    }
