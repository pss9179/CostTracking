"""
Authentication utilities for API key validation.
"""
import logging
import secrets
import bcrypt
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import Header, HTTPException, Depends, Request
from sqlmodel import Session, select
from db import get_session
from models import APIKey, User

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    Format: llmo_sk_{random_hex}
    """
    random_hex = secrets.token_hex(24)  # 48 characters
    return f"llmo_sk_{random_hex}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key using bcrypt."""
    return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_api_key_hash(api_key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    try:
        return bcrypt.checkpw(api_key.encode('utf-8'), key_hash.encode('utf-8'))
    except Exception:
        return False


def get_key_prefix(api_key: str, length: int = 12) -> str:
    """
    Get displayable prefix of API key.
    Example: llmo_sk_abc... (first 12 chars)
    """
    return api_key[:length] + "..." if len(api_key) > length else api_key


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> User:
    """
    FastAPI dependency to validate API key OR Clerk JWT and return current user.
    
    Usage:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    import sys
    sys.stderr.write(f"[AUTH] get_current_user called! authorization={authorization[:50] if authorization else None}...\n")
    sys.stderr.flush()
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    import sys
    print(f"[AUTH DEBUG] Token received: {token[:30]}...", flush=True)
    print(f"[AUTH DEBUG] Starts with llmo_sk_: {token.startswith('llmo_sk_')}", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Check if it's an API key (starts with llmo_sk_)
    if token.startswith("llmo_sk_"):
        print(f"[AUTH DEBUG] Validating API key...", flush=True)
        logger.info(f"[Auth] Validating API key: {token[:20]}...")
        # Validate API key
        statement = select(APIKey).where(APIKey.revoked_at.is_(None))
        api_keys = session.exec(statement).all()
        logger.info(f"[Auth] Found {len(api_keys)} non-revoked API keys in database")
        
        matched_key = None
        for key in api_keys:
            if verify_api_key_hash(token, key.key_hash):
                matched_key = key
                logger.info(f"[Auth] API key matched! User ID: {key.user_id}")
                break
        
        if not matched_key:
            logger.warning(f"[Auth] API key not found in database")
            raise HTTPException(
                status_code=401,
                detail="Invalid or revoked API key",
            )
        
        # Update last_used_at
        matched_key.last_used_at = datetime.utcnow()
        session.add(matched_key)
        session.commit()
        
        # Get user
        user = session.get(User, matched_key.user_id)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
        return user
    
    else:
        # Assume it's a Clerk JWT
        # Import locally to avoid circular import
        from clerk_auth import get_current_clerk_user
        return await get_current_clerk_user(request, session)


async def get_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> Optional[UUID]:
    """
    Convenience dependency to get user ID from API key or Clerk token.
    Returns None if no authorization provided (MVP mode).
    """
    # MVP mode: Allow unauthenticated access if no header
    if not authorization:
        return None
    
    try:
        user = await get_current_user(request, authorization, session)
        return user.id
    except HTTPException:
        # Invalid key - return None instead of raising (fail-open for MVP)
        return None
