"""
Simple email/password authentication (no external providers).
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from db import get_session
from models import User, UserSignup, UserLogin, UserResponse, APIKey, APIKeyResponse
from auth import hash_api_key, generate_api_key, get_key_prefix
import bcrypt
import jwt

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT secret (in production, load from env var)
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def create_jwt_token(user_id: UUID) -> str:
    """Create a JWT token for a user."""
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Optional[UUID]:
    """Decode a JWT token and return user_id."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return UUID(payload["user_id"])
    except Exception:
        return None


async def get_current_user_from_jwt(
    authorization: Optional[str] = Header(None),
    session: Session = Depends(get_session)
) -> User:
    """Get current user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = parts[1]
    user_id = decode_jwt_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.post("/signup", response_model=dict)
def signup(
    user_data: UserSignup,
    session: Session = Depends(get_session)
) -> dict:
    """
    Create a new user account and automatically generate an API key.
    
    Returns:
        - JWT token for frontend authentication
        - API key for SDK usage (shown once!)
        - User info
    """
    # Check if user already exists
    existing = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        subscription_tier="free"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Auto-generate API key
    api_key = generate_api_key()
    api_key_record = APIKey(
        user_id=user.id,
        key_hash=hash_api_key(api_key),
        key_prefix=get_key_prefix(api_key),
        name="Default API Key",
        created_at=datetime.utcnow()
    )
    session.add(api_key_record)
    session.commit()
    session.refresh(api_key_record)
    
    # Create JWT token
    jwt_token = create_jwt_token(user.id)
    
    return {
        "token": jwt_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
            "subscription_tier": user.subscription_tier
        },
        "api_key": {
            "key": api_key,  # Show full key only once!
            "key_prefix": api_key_record.key_prefix,
            "name": api_key_record.name,
            "created_at": api_key_record.created_at.isoformat()
        }
    }


@router.post("/login", response_model=dict)
def login(
    credentials: UserLogin,
    session: Session = Depends(get_session)
) -> dict:
    """
    Login with email and password.
    
    Returns:
        - JWT token
        - User info
    """
    # Find user
    user = session.exec(
        select(User).where(User.email == credentials.email)
    ).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    jwt_token = create_jwt_token(user.id)
    
    return {
        "token": jwt_token,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
            "subscription_tier": user.subscription_tier
        }
    }


@router.get("/me", response_model=dict)
async def get_me(
    user: User = Depends(get_current_user_from_jwt),
    session: Session = Depends(get_session)
) -> dict:
    """
    Get current user info.
    """
    # Get user's API keys (without full keys)
    api_keys = session.exec(
        select(APIKey).where(APIKey.user_id == user.id).where(APIKey.revoked_at.is_(None))
    ).all()
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "created_at": user.created_at.isoformat(),
            "subscription_tier": user.subscription_tier
        },
        "api_keys": [
            {
                "id": str(key.id),
                "name": key.name,
                "key_prefix": key.key_prefix,
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None
            }
            for key in api_keys
        ]
    }


@router.post("/api-keys", response_model=dict)
async def create_api_key(
    name: str,
    user: User = Depends(get_current_user_from_jwt),
    session: Session = Depends(get_session)
) -> dict:
    """
    Create a new API key for the current user.
    """
    # Generate API key
    api_key = generate_api_key()
    api_key_record = APIKey(
        user_id=user.id,
        key_hash=hash_api_key(api_key),
        key_prefix=get_key_prefix(api_key),
        name=name,
        created_at=datetime.utcnow()
    )
    session.add(api_key_record)
    session.commit()
    session.refresh(api_key_record)
    
    return {
        "key": api_key,  # Show full key only once!
        "key_prefix": api_key_record.key_prefix,
        "name": api_key_record.name,
        "created_at": api_key_record.created_at.isoformat()
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user: User = Depends(get_current_user_from_jwt),
    session: Session = Depends(get_session)
) -> dict:
    """
    Revoke an API key.
    """
    api_key = session.get(APIKey, key_id)
    
    if not api_key or api_key.user_id != user.id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.revoked_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    
    return {"status": "success", "message": "API key revoked"}

