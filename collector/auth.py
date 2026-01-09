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

# Debug: Print when module loads
print("[AUTH MODULE] auth.py module loaded!", flush=True)
import sys
sys.stderr.write("[AUTH MODULE] auth.py module loaded (stderr)!\n")
sys.stderr.flush()


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
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.write("[AUTH FUNC] ===== get_current_user FUNCTION CALLED! =====\n")
    sys.stderr.write(f"[AUTH FUNC] authorization header: {authorization}\n")
    sys.stderr.write("=" * 80 + "\n")
    sys.stderr.flush()
    print("[AUTH FUNC] get_current_user FUNCTION CALLED!", flush=True)
    print(f"[AUTH FUNC] authorization={authorization}", flush=True)
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
    
    # Log to stderr and logger (AUTH_VERSION_20250108_v2)
    import sys
    sys.stderr.write(f"[AUTH v2] ========== AUTH VERSION 20250108_v2 ==========\n")
    sys.stderr.write(f"[AUTH v2] Token extracted: {token[:40]}...\n")
    sys.stderr.write(f"[AUTH v2] Token length: {len(token)}\n")
    sys.stderr.write(f"[AUTH v2] Token repr first 20: {repr(token[:20])}\n")
    sys.stderr.write(f"[AUTH v2] Starts with llmo_sk_: {token.startswith('llmo_sk_')}\n")
    sys.stderr.flush()
    logger.error(f"[AUTH v2] Token received: {token[:30]}...")
    logger.error(f"[AUTH v2] Starts with llmo_sk_: {token.startswith('llmo_sk_')}")
    
    # Check if it's an API key (starts with llmo_sk_)
    if token.startswith("llmo_sk_"):
        sys.stderr.write("[AUTH] ✅ Detected API key - entering API key validation branch\n")
        sys.stderr.flush()
        logger.error(f"[AUTH] Detected API key, validating...")
        print(f"[AUTH DEBUG] Validating API key...", flush=True)
        logger.info(f"[Auth] Validating API key: {token[:20]}...")
        # Validate API key
        try:
            logger.error(f"[AUTH] Executing database query...")
            statement = select(APIKey).where(APIKey.revoked_at.is_(None))
            api_keys = session.exec(statement).all()
            logger.error(f"[AUTH] Found {len(api_keys)} non-revoked API keys in database")
            
            matched_key = None
            logger.error(f"[AUTH] Checking {len(api_keys)} keys...")
            for i, key in enumerate(api_keys):
                logger.error(f"[AUTH] Checking key {i+1}/{len(api_keys)}: {key.key_prefix}")
                if verify_api_key_hash(token, key.key_hash):
                    matched_key = key
                    logger.error(f"[AUTH] ✅ API key MATCHED! User ID: {key.user_id}")
                    break
            
            if not matched_key:
                logger.error(f"[AUTH] ❌ API key NOT found in database after checking {len(api_keys)} keys")
                raise HTTPException(
                    status_code=401,
                    detail="API_KEY_AUTH_FAILED: Invalid or revoked API key",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[AUTH] ❌ Exception during API key validation: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=401,
                detail=f"API_KEY_AUTH_ERROR: {str(e)}",
            )
        
        # Update last_used_at
        logger.error(f"[AUTH] ✅ Updating last_used_at for matched key...")
        matched_key.last_used_at = datetime.utcnow()
        session.add(matched_key)
        session.commit()
        
        # Get user
        logger.error(f"[AUTH] ✅ Getting user from database...")
        user = session.get(User, matched_key.user_id)
        if not user:
            logger.error(f"[AUTH] ❌ User not found for ID: {matched_key.user_id}")
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )
        logger.error(f"[AUTH] ✅✅✅ SUCCESS! Returning user: {user.email}")
        return user
    
    else:
        # Assume it's a Clerk JWT
        import sys
        sys.stderr.write("[AUTH] ⚠️ Token does NOT start with llmo_sk_ - falling back to Clerk Auth\n")
        sys.stderr.write(f"[AUTH] Token was: {token[:50]}...\n")
        sys.stderr.flush()
        # Import locally to avoid circular import
        from clerk_auth import get_current_clerk_user
        sys.stderr.write("[AUTH] Calling get_current_clerk_user...\n")
        sys.stderr.flush()
        return await get_current_clerk_user(request, session)


async def get_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> Optional[UUID]:
    """
    Convenience dependency to get user ID from API key or Clerk token.
    
    CRITICAL: Returns None ONLY if no authorization header provided.
    If an invalid auth is provided, the exception is raised to reject the request.
    This ensures:
    1. Valid auth = events stored with correct user_id
    2. Invalid auth = request rejected (no data stored)
    3. No auth = request rejected (API key required for event ingestion)
    """
    # SECURITY: Require authentication for event ingestion
    # Previously this was "MVP mode" allowing unauthenticated access, 
    # but that caused events to go into "default_tenant" bucket without user_id
    if not authorization:
        logger.warning("[AUTH] No authorization header - rejecting request")
        raise HTTPException(
            status_code=401,
            detail="Authorization required. Provide API key: Authorization: Bearer llmo_sk_...",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user - let HTTPException propagate (don't fail-open!)
    user = await get_current_user(request, authorization, session)
    return user.id
