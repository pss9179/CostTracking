"""
Authentication and tenant management endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Tenant, TenantCreate
from auth import generate_api_key, get_current_tenant

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/tenants", response_model=Dict[str, str])
def create_tenant(
    *,
    session: Session = Depends(get_session),
    tenant_data: TenantCreate
) -> Dict[str, str]:
    """
    Create a new tenant with API key.
    
    Returns the tenant_id and api_key.
    """
    # Check if tenant_id already exists
    existing = session.exec(
        select(Tenant).where(Tenant.tenant_id == tenant_data.tenant_id)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tenant '{tenant_data.tenant_id}' already exists"
        )
    
    # Generate API key
    api_key = generate_api_key()
    
    # Create tenant
    tenant = Tenant(
        tenant_id=tenant_data.tenant_id,
        name=tenant_data.name,
        api_key=api_key
    )
    
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "api_key": api_key,
        "message": "Tenant created successfully. Store the API key securely - it won't be shown again."
    }


@router.get("/tenants", response_model=List[Dict[str, Any]])
def list_tenants(
    *,
    session: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """
    List all tenants (admin only - no authentication required for MVP).
    
    In production, this should require admin authentication.
    """
    statement = select(Tenant).order_by(Tenant.created_at.desc())
    tenants = session.exec(statement).all()
    
    return [
        {
            "tenant_id": t.tenant_id,
            "name": t.name,
            "created_at": t.created_at.isoformat(),
            "api_key_preview": f"{t.api_key[:15]}..." if len(t.api_key) > 15 else "***"
        }
        for t in tenants
    ]


@router.get("/me")
async def get_current_tenant_info(
    tenant_id: str = Depends(get_current_tenant),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get current authenticated tenant's information.
    
    Requires X-API-Key header.
    """
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    tenant = session.exec(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "tenant_id": tenant.tenant_id,
        "name": tenant.name,
        "created_at": tenant.created_at.isoformat()
    }


@router.delete("/tenants/{tenant_id}")
def delete_tenant(
    *,
    tenant_id: str,
    session: Session = Depends(get_session)
) -> Dict[str, str]:
    """
    Delete a tenant (admin only - no authentication for MVP).
    
    In production, this should require admin authentication.
    Note: This does NOT delete the tenant's trace events.
    """
    tenant = session.exec(
        select(Tenant).where(Tenant.tenant_id == tenant_id)
    ).first()
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    session.delete(tenant)
    session.commit()
    
    return {
        "message": f"Tenant '{tenant_id}' deleted successfully"
    }

