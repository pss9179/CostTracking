"""
Clerk Authentication Middleware
Verifies Clerk session tokens and extracts user information.
"""

import logging
import os
import base64
import json
from typing import Optional
from fastapi import HTTPException, Request, Depends
from fastapi import Request as FastAPIRequest
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from models import User
from db import get_session

logger = logging.getLogger(__name__)
# Use auto_error=True to see what's happening with missing tokens
security = HTTPBearer(auto_error=False)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_DOMAIN = "superb-toucan-96.clerk.accounts.dev"  # From your .env


async def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify Clerk JWT token by decoding it.
    For MVP, we decode without full verification (production should verify signature).
    Returns user data if valid, None otherwise.
    """
    if not CLERK_SECRET_KEY:
        logger.warning("[Clerk Auth] CLERK_SECRET_KEY not set, skipping verification")
        return None
    
    try:
        # Decode JWT (format: header.payload.signature)
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning(f"[Clerk Auth] Invalid JWT format: {len(parts)} parts")
            return None
        
        # Decode payload (base64url)
        payload = parts[1]
        # Add padding if needed
        padding = len(payload) % 4
        if padding:
            payload += '=' * (4 - padding)
        
        decoded = base64.urlsafe_b64decode(payload)
        token_data = json.loads(decoded)
        
        logger.info(f"[Clerk Auth] Token decoded successfully. Claims: {list(token_data.keys())}")
        
        # Extract user ID from JWT claims (Clerk uses 'sub' for user ID)
        clerk_user_id = token_data.get("sub") or token_data.get("user_id") or token_data.get("id")
        if not clerk_user_id:
            logger.warning(f"[Clerk Auth] No user ID in token. Available keys: {list(token_data.keys())}")
            return None
        
        logger.info(f"[Clerk Auth] Extracted Clerk user ID: {clerk_user_id}")
        
        return {
            "clerk_user_id": clerk_user_id,
            "session_id": token_data.get("sid"),
        }
    
    except Exception as e:
        logger.error(f"[Clerk Auth] Error decoding token: {type(e).__name__}: {e}", exc_info=True)
        import traceback
        logger.error(f"[Clerk Auth] Traceback: {traceback.format_exc()}")
        return None


async def get_current_clerk_user(
    request: FastAPIRequest,
    session: Session = Depends(get_session)
) -> User:
    """
    Extract and verify Clerk user from Authorization header.
    Returns User model from database.
    """
    # Manually extract Authorization header
    auth_header = request.headers.get("Authorization")
    logger.info(f"[Clerk Auth] Authorization header: {auth_header[:50] if auth_header else 'None'}...")
    
    if not auth_header:
        logger.warning("[Clerk Auth] No Authorization header found")
        logger.warning(f"[Clerk Auth] All headers: {dict(request.headers)}")
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    # Extract Bearer token
    if not auth_header.startswith("Bearer "):
        logger.warning(f"[Clerk Auth] Invalid Authorization header format: {auth_header[:50]}")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    logger.info(f"[Clerk Auth] === STARTING TOKEN VERIFICATION ===")
    logger.info(f"[Clerk Auth] Received token (first 50 chars): {token[:50]}...")
    logger.info(f"[Clerk Auth] Token length: {len(token)}")
    
    # Verify token with Clerk and decode to get user info
    clerk_user_id = None
    email = None
    name = None
    
    try:
        logger.info("[Clerk Auth] Calling verify_clerk_token...")
        clerk_data = await verify_clerk_token(token)
        logger.info(f"[Clerk Auth] verify_clerk_token returned: {clerk_data}")
        if not clerk_data:
            logger.error(f"[Clerk Auth] verify_clerk_token returned None - token verification failed. Token starts with: {token[:20] if token else 'None'}...")
            raise HTTPException(status_code=401, detail=f"CLERK_AUTH_FAILED: Invalid or expired token (token starts with: {token[:20] if token else 'None'}...)")
        
        clerk_user_id = clerk_data["clerk_user_id"]
        logger.info(f"[Clerk Auth] Token verified, Clerk user ID: {clerk_user_id}")
        
        # Decode token again to get email/name from payload
        token_parts = token.split('.')
        if len(token_parts) == 3:
            payload = token_parts[1]
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            try:
                decoded_payload = base64.urlsafe_b64decode(payload)
                token_payload = json.loads(decoded_payload)
                email = token_payload.get("email") or f"user_{clerk_user_id[:8]}@clerk.local"
                name = token_payload.get("name") or None
            except Exception as decode_error:
                logger.warning(f"[Clerk Auth] Failed to decode token payload: {decode_error}")
                email = f"user_{clerk_user_id[:8]}@clerk.local"
                name = None
        else:
            email = f"user_{clerk_user_id[:8]}@clerk.local"
            name = None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Clerk Auth] Exception in verify_clerk_token: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Token verification error: {str(e)}")
    
    if not clerk_user_id:
        raise HTTPException(status_code=401, detail="Could not extract user ID from token")
    
    # Look up user in local DB, create if doesn't exist (lazy user creation)
    try:
        # First check by clerk_user_id (primary lookup)
        statement = select(User).where(User.clerk_user_id == clerk_user_id)
        user = session.exec(statement).first()
        
        if not user and email:
            # Also check by email in case user exists with different clerk_user_id
            # (shouldn't happen, but handles edge cases)
            email_statement = select(User).where(User.email == email)
            user = session.exec(email_statement).first()
        
        if not user:
            # WARNING: User should have been created via webhook or /users/sync
            # This is a fallback - log as warning so we know webhook/sync failed
            logger.warning(f"[Clerk Auth] ⚠️ User not found in DB for Clerk ID: {clerk_user_id}")
            logger.warning(f"[Clerk Auth] ⚠️ This should have been created via webhook or /users/sync")
            logger.warning(f"[Clerk Auth] ⚠️ Auto-creating as fallback - check webhook configuration!")
            
            # Auto-create user from Clerk data (fallback only)
            # Ensure email is set (fallback if not extracted from token)
            if not email:
                email = f"user_{clerk_user_id[:8]}@clerk.local"
            
            # Check again by email before creating (race condition protection)
            email_check = select(User).where(User.email == email)
            existing_by_email = session.exec(email_check).first()
            if existing_by_email:
                logger.warning(f"[Clerk Auth] User with email {email} already exists, updating clerk_user_id")
                # Update existing user with clerk_user_id if missing
                if not existing_by_email.clerk_user_id:
                    existing_by_email.clerk_user_id = clerk_user_id
                    session.add(existing_by_email)
                    session.commit()
                    session.refresh(existing_by_email)
                return existing_by_email
            
            try:
                user = User(
                    clerk_user_id=clerk_user_id,
                    email=email,
                    name=name,
                    user_type="solo_dev",  # Default, can be updated later via /users/sync
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                
                logger.warning(f"[Clerk Auth] ⚠️ Auto-created user: {user.email} (ID: {user.id}) - webhook may have failed")
            except Exception as create_error:
                # Handle race condition: another request might have created the user
                if "unique constraint" in str(create_error).lower() or "duplicate key" in str(create_error).lower():
                    logger.warning(f"[Clerk Auth] Race condition detected, user was created by another request. Looking up again...")
                    session.rollback()
                    # Try to find the user again
                    statement = select(User).where(User.clerk_user_id == clerk_user_id)
                    user = session.exec(statement).first()
                    if not user and email:
                        email_statement = select(User).where(User.email == email)
                        user = session.exec(email_statement).first()
                    if user:
                        logger.info(f"[Clerk Auth] Found user after race condition: {user.email} (ID: {user.id})")
                    else:
                        raise HTTPException(status_code=500, detail=f"Failed to create or find user after race condition")
                else:
                    raise
        else:
            logger.info(f"[Clerk Auth] User found: {user.email} (ID: {user.id})")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Clerk Auth] Exception looking up user: {type(e).__name__}: {e}", exc_info=True)
        import traceback
        logger.error(f"[Clerk Auth] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def get_optional_clerk_user(
    request: FastAPIRequest,
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Extract Clerk user if token provided, otherwise return None.
    Used for endpoints that can work with or without auth.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    try:
        return await get_current_clerk_user(request, session)
    except HTTPException:
        return None

