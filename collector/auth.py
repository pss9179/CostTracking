"""
Authentication and authorization for tenant-scoped access.

Supports API key-based authentication for tenants.
"""
import secrets
from typing import Optional
from fastapi import HTTPException, Header, Depends
from sqlmodel import Session, select
from db import get_session
from models import Tenant


def generate_api_key() -> str:
    """Generate a secure API key for a tenant."""
    return f"llmo_{secrets.token_urlsafe(32)}"


async def get_current_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    session: Session = Depends(get_session)
) -> Optional[str]:
    """
    Extract and validate tenant from API key.
    
    Returns tenant_id if authenticated, None if no key provided.
    Raises 401 if invalid key provided.
    """
    if not x_api_key:
        # No API key provided - allow access to all data (admin mode)
        return None
    
    # Look up tenant by API key
    statement = select(Tenant).where(Tenant.api_key == x_api_key)
    tenant = session.exec(statement).first()
    
    if not tenant:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return tenant.tenant_id


async def require_tenant(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: Session = Depends(get_session)
) -> str:
    """
    Require valid tenant authentication.
    
    Returns tenant_id or raises 401.
    """
    tenant_id = await get_current_tenant(x_api_key, session)
    
    if not tenant_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide X-API-Key header."
        )
    
    return tenant_id

