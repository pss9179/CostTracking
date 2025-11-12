"""
Clerk Authentication Middleware
Verifies Clerk session tokens and extracts user information.
"""

import logging
import os
from typing import Optional
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
import httpx

from models import User
from db import get_session

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
CLERK_DOMAIN = "superb-toucan-96.clerk.accounts.dev"  # From your .env


async def verify_clerk_token(token: str) -> Optional[dict]:
    """
    Verify Clerk session token using Clerk's API.
    Returns user data if valid, None otherwise.
    """
    if not CLERK_SECRET_KEY:
        logger.warning("[Clerk Auth] CLERK_SECRET_KEY not set, skipping verification")
        return None
    
    try:
        # Verify token with Clerk's API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.clerk.com/v1/sessions/{token}/verify",
                headers={
                    "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=5.0
            )
            
            if response.status_code == 200:
                session_data = response.json()
                return {
                    "clerk_user_id": session_data.get("user_id"),
                    "session_id": session_data.get("id"),
                }
            else:
                logger.warning(f"[Clerk Auth] Token verification failed: {response.status_code}")
                return None
    
    except Exception as e:
        logger.error(f"[Clerk Auth] Error verifying token: {e}")
        return None


async def get_current_clerk_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Extract and verify Clerk user from Authorization header.
    Returns User model from database.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No authorization token provided")
    
    token = credentials.credentials
    
    # Verify token with Clerk
    clerk_data = await verify_clerk_token(token)
    if not clerk_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    clerk_user_id = clerk_data["clerk_user_id"]
    
    # Look up user in local DB
    statement = select(User).where(User.clerk_user_id == clerk_user_id)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User not found. Clerk ID: {clerk_user_id}. Please contact support."
        )
    
    return user


async def get_optional_clerk_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Extract Clerk user if token provided, otherwise return None.
    Used for endpoints that can work with or without auth.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_clerk_user(credentials, session)
    except HTTPException:
        return None

