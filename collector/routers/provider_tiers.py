"""
API routes for managing provider tier configurations.
Allows users to specify which tier/plan they're on for each provider.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from sqlmodel import Session, select
from db import get_session
from models import ProviderTier
from clerk_auth import get_optional_clerk_user

router = APIRouter(prefix="/provider-tiers", tags=["provider-tiers"])


@router.get("/")
async def get_provider_tiers(
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),
    request: Request = None,
    session: Session = Depends(get_session)
) -> List[dict]:
    """Get provider tier configurations for a tenant."""
    # Get tenant_id from query param or from Clerk user
    if not tenant_id:
        clerk_user = await get_optional_clerk_user(request)
        if clerk_user:
            tenant_id = clerk_user.id
    
    if not tenant_id:
        return []
    
    statement = select(ProviderTier).where(
        ProviderTier.tenant_id == tenant_id,
        ProviderTier.is_active == True
    )
    
    tiers = session.exec(statement).all()
    
    return [
        {
            "id": str(t.id),
            "provider": t.provider,
            "tier": t.tier,
            "plan_name": t.plan_name,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in tiers
    ]


@router.post("/")
async def create_or_update_provider_tier(
    provider: str,
    tier: str,
    plan_name: Optional[str] = None,
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),
    request: Request = None,
    session: Session = Depends(get_session)
) -> dict:
    """Create or update provider tier configuration."""
    # Get tenant_id from query param or from Clerk user
    if not tenant_id:
        clerk_user = await get_optional_clerk_user(request)
        if not clerk_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        tenant_id = clerk_user.id
    
    # Check if tier already exists
    existing = session.exec(
        select(ProviderTier).where(
            ProviderTier.tenant_id == tenant_id,
            ProviderTier.provider == provider,
            ProviderTier.is_active == True
        )
    ).first()
    
    if existing:
        # Update existing
        existing.tier = tier
        existing.plan_name = plan_name
        from datetime import datetime
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        
        return {
            "id": str(existing.id),
            "provider": existing.provider,
            "tier": existing.tier,
            "plan_name": existing.plan_name,
            "is_active": existing.is_active,
            "created_at": existing.created_at.isoformat(),
            "updated_at": existing.updated_at.isoformat(),
        }
    else:
        # Create new
        from datetime import datetime
        new_tier = ProviderTier(
            tenant_id=tenant_id,
            provider=provider,
            tier=tier,
            plan_name=plan_name,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(new_tier)
        session.commit()
        session.refresh(new_tier)
        
        return {
            "id": str(new_tier.id),
            "provider": new_tier.provider,
            "tier": new_tier.tier,
            "plan_name": new_tier.plan_name,
            "is_active": new_tier.is_active,
            "created_at": new_tier.created_at.isoformat(),
            "updated_at": new_tier.updated_at.isoformat(),
        }


@router.delete("/{provider}")
async def delete_provider_tier(
    provider: str,
    tenant_id: Optional[str] = Query(None, description="Tenant ID"),
    request: Request = None,
    session: Session = Depends(get_session)
) -> dict:
    """Delete (deactivate) provider tier configuration."""
    # Get tenant_id from query param or from Clerk user
    if not tenant_id:
        clerk_user = await get_optional_clerk_user(request)
        if not clerk_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        tenant_id = clerk_user.id
    
    existing = session.exec(
        select(ProviderTier).where(
            ProviderTier.tenant_id == tenant_id,
            ProviderTier.provider == provider,
            ProviderTier.is_active == True
        )
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Provider tier not found")
    
    existing.is_active = False
    from datetime import datetime
    existing.updated_at = datetime.utcnow()
    session.add(existing)
    session.commit()
    
    return {"message": "Provider tier deactivated"}

