"""
Authentication utilities for API key validation.
"""
import secrets
import bcrypt
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import Header, HTTPException, Depends
from sqlmodel import Session, select
from .db import get_session
from .models import APIKey, User


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
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> User:
    """
    FastAPI dependency to validate API key and return current user.
    
    Usage:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    """
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
            detail="Invalid Authorization header format. Expected: Bearer <api_key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = parts[1]
    
    # Validate API key format
    if not api_key.startswith("llmo_sk_"):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format",
        )
    
    # Look up API key in database
    # Note: In production, you'd want to cache this or use a faster lookup
    statement = select(APIKey).where(APIKey.revoked_at.is_(None))
    api_keys = session.exec(statement).all()
    
    matched_key = None
    for key in api_keys:
        if verify_api_key_hash(api_key, key.key_hash):
            matched_key = key
            break
    
    if not matched_key:
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


async def get_current_user_id(
    user: User = Depends(get_current_user)
) -> UUID:
    """Convenience dependency to just get user ID."""
    return user.id
