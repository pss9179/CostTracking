"""
Spending Caps API Router

Endpoints for managing spending caps and viewing alerts.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlmodel import Session, select, func, and_, or_

from models import (
    SpendingCap,
    Alert,
    CapCreate,
    CapUpdate,
    CapResponse,
    AlertResponse,
    TraceEvent,
    User,
)
from db import get_session
from clerk_auth import get_current_clerk_user
from auth import get_current_user as auth_get_current_user  # Explicit import for API key auth

# Verify import worked
import sys
sys.stderr.write(f"[CAPS IMPORT] auth_get_current_user imported: {auth_get_current_user}\n")
sys.stderr.write(f"[CAPS IMPORT] auth_get_current_user location: {auth_get_current_user.__module__}\n")
sys.stderr.flush()

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/caps", tags=["caps"])

# Debug: Print when module loads to verify deployment
print("[CAPS MODULE] caps.py module loaded - API key auth enabled!", flush=True)


def get_period_dates(period: str) -> tuple[datetime, datetime]:
    """Calculate start and end dates for a period."""
    now = datetime.utcnow()
    
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "weekly":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Next month
        if now.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    else:
        raise ValueError(f"Invalid period: {period}")
    
    return start, end


def calculate_current_spend(
    session: Session,
    user_id: UUID,
    cap_type: str,
    target_name: Optional[str],
    period_start: datetime,
    period_end: datetime,
) -> float:
    """Calculate current spend for a cap."""
    query = select(func.sum(TraceEvent.cost_usd)).where(
        and_(
            TraceEvent.user_id == user_id,
            TraceEvent.created_at >= period_start,
            TraceEvent.created_at < period_end,
        )
    )
    
    # Add scope filters
    if cap_type == "provider" and target_name:
        query = query.where(TraceEvent.provider == target_name)
    elif cap_type == "model" and target_name:
        query = query.where(TraceEvent.model_id == target_name)
    elif cap_type == "agent" and target_name:
        query = query.where(TraceEvent.agent == target_name)
    elif cap_type == "customer" and target_name:
        query = query.where(TraceEvent.customer_id == target_name)
    # 'global' doesn't add any filter
    
    result = session.exec(query).first()
    return float(result or 0.0)


@router.post("/", response_model=CapResponse)
async def create_cap(
    cap_data: CapCreate,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Create a new spending cap."""
    # Validate period
    if cap_data.period not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Period must be 'daily', 'weekly', or 'monthly'")
    
    # Validate cap_type
    if cap_data.cap_type not in ["global", "provider", "model", "agent", "customer"]:
        raise HTTPException(status_code=400, detail="Invalid cap_type")
    
    # Validate target_name for non-global caps
    if cap_data.cap_type != "global" and not cap_data.target_name:
        raise HTTPException(status_code=400, detail=f"target_name required for cap_type '{cap_data.cap_type}'")
    
    # Validate enforcement
    if cap_data.enforcement not in ["alert", "hard_block"]:
        raise HTTPException(status_code=400, detail="Enforcement must be 'alert' or 'hard_block'")
    
    cap = SpendingCap(
        user_id=user.id,
        cap_type=cap_data.cap_type,
        target_name=cap_data.target_name,
        limit_amount=cap_data.limit_amount,
        period=cap_data.period,
        enforcement=cap_data.enforcement,
        alert_threshold=cap_data.alert_threshold,
        alert_email=cap_data.alert_email,
    )
    
    session.add(cap)
    session.commit()
    session.refresh(cap)
    
    # Calculate current spend
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    logger.info(f"Created spending cap: {cap.cap_type} ${cap.limit_amount}/{cap.period} for user {user.email}")
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        enforcement=cap.enforcement,
        exceeded_at=cap.exceeded_at,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.get("/", response_model=List[CapResponse])
async def list_caps(
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """List all spending caps for the current user."""
    caps = session.exec(
        select(SpendingCap).where(SpendingCap.user_id == user.id).order_by(SpendingCap.created_at.desc())
    ).all()
    
    result = []
    for cap in caps:
        period_start, period_end = get_period_dates(cap.period)
        current_spend = calculate_current_spend(
            session, user.id, cap.cap_type, cap.target_name, period_start, period_end
        )
        
        result.append(CapResponse(
            id=cap.id,
            cap_type=cap.cap_type,
            target_name=cap.target_name,
            limit_amount=cap.limit_amount,
            period=cap.period,
            enforcement=cap.enforcement or "alert",
            exceeded_at=cap.exceeded_at,
            alert_threshold=cap.alert_threshold,
            alert_email=cap.alert_email or "",
            enabled=cap.enabled,
            current_spend=current_spend,
            percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
            created_at=cap.created_at,
            updated_at=cap.updated_at,
        ))
    
    return result


# =====================================================================
# SPECIFIC ROUTES - These MUST come before /{cap_id} routes!
# FastAPI matches routes in order, and /{cap_id} would catch these first.
# =====================================================================

@router.get("/alerts/", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """List alerts for the current user."""
    alerts = session.exec(
        select(Alert)
        .where(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(limit)
    ).all()
    
    return [
        AlertResponse(
            id=alert.id,
            alert_type=alert.alert_type,
            current_spend=alert.current_spend,
            cap_limit=alert.cap_limit,
            percentage=alert.percentage,
            target_type=alert.target_type,
            target_name=alert.target_name,
            period_start=alert.period_start,
            period_end=alert.period_end,
            email_sent=alert.email_sent,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


@router.get("/check-version")
async def check_version():
    """Return caps router version to verify deployment."""
    return {"version": "caps-router-v20250108-inline-auth", "inline_auth": True}


@router.get("/check")
async def check_caps(
    request: Request,
    provider: Optional[str] = Query(default=None, description="Provider name (e.g., 'openai')"),
    model: Optional[str] = Query(default=None, description="Model ID (e.g., 'gpt-4o')"),
    customer_id: Optional[str] = Query(default=None, description="Customer ID"),
    agent: Optional[str] = Query(default=None, description="Agent name"),
    session: Session = Depends(get_session),
):
    """
    Check if any hard caps would be exceeded for the given context.
    
    Called by SDK before making API calls to enforce hard blocks.
    Returns list of exceeded caps (empty if all clear).
    
    Supports both API keys (llmo_sk_*) and Clerk JWTs for authentication.
    API keys NEVER expire - they only stop working if manually revoked.
    """
    import sys
    import bcrypt
    from models import APIKey
    
    sys.stderr.write("[CHECK_CAPS] ========== /caps/check ENDPOINT v20250108 ==========\n")
    sys.stderr.flush()
    
    # Return version marker for verification
    debug_version = "caps-check-v20250108"
    
    # Get authorization header
    authorization = request.headers.get("Authorization")
    sys.stderr.write(f"[CHECK_CAPS] Authorization header: {authorization[:50] if authorization else 'None'}...\n")
    sys.stderr.flush()
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format. Expected: Bearer <token>")
    
    token = parts[1]
    user = None
    
    # === API KEY AUTHENTICATION (tokens starting with llmo_sk_) ===
    # API keys NEVER expire - they work forever until manually revoked
    if token.startswith("llmo_sk_"):
        sys.stderr.write(f"[CHECK_CAPS] Detected API key (llmo_sk_*) - validating INLINE\n")
        sys.stderr.flush()
        
        # Get all non-revoked API keys and check against them
        statement = select(APIKey).where(APIKey.revoked_at.is_(None))
        api_keys = session.exec(statement).all()
        sys.stderr.write(f"[CHECK_CAPS] Found {len(api_keys)} non-revoked API keys in database\n")
        sys.stderr.flush()
        
        matched_key = None
        for key in api_keys:
            try:
                if bcrypt.checkpw(token.encode('utf-8'), key.key_hash.encode('utf-8')):
                    matched_key = key
                    sys.stderr.write(f"[CHECK_CAPS] ✅ API key MATCHED! Key prefix: {key.key_prefix}\n")
                    sys.stderr.flush()
                    break
            except Exception as hash_err:
                sys.stderr.write(f"[CHECK_CAPS] Hash check error for {key.key_prefix}: {hash_err}\n")
                continue
        
        if not matched_key:
            sys.stderr.write(f"[CHECK_CAPS] ❌ API key NOT found in database\n")
            sys.stderr.flush()
            raise HTTPException(
                status_code=401, 
                detail="Invalid API key. Make sure you're using a valid key from your dashboard."
            )
        
        # Update last_used_at
        from datetime import datetime as dt
        matched_key.last_used_at = dt.utcnow()
        session.add(matched_key)
        session.commit()
        
        # Get the user
        user = session.get(User, matched_key.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found for API key")
        
        sys.stderr.write(f"[CHECK_CAPS] ✅ API key auth SUCCESS! User: {user.email}\n")
        sys.stderr.flush()
    
    # === CLERK JWT AUTHENTICATION (for browser/dashboard calls) ===
    else:
        sys.stderr.write(f"[CHECK_CAPS] Token doesn't start with llmo_sk_ - trying Clerk auth\n")
        sys.stderr.flush()
        # Fall back to Clerk auth for non-API-key tokens
        try:
            user = await get_current_clerk_user(request, session)
        except HTTPException as e:
            # Re-raise with clearer message
            raise HTTPException(
                status_code=401,
                detail=f"Authentication failed. Use an API key (llmo_sk_*) or valid Clerk session."
            )
    
    print(f"[CHECK_CAPS] check_caps function CALLED! user={user.email if user else None}", flush=True)
    sys.stderr.write(f"[CHECK_CAPS] User authenticated: {user.email if user else None}\n")
    sys.stderr.flush()
    
    # Get all active hard_block caps for this user
    caps = session.exec(
        select(SpendingCap).where(
            and_(
                SpendingCap.user_id == user.id,
                SpendingCap.enabled == True,
                SpendingCap.enforcement == "hard_block",
            )
        )
    ).all()
    
    if not caps:
        return {
            "allowed": True,
            "exceeded_caps": [],
            "message": "No active hard caps"
        }
    
    exceeded_caps = []
    
    for cap in caps:
        # Calculate period dates
        period_start, period_end = get_period_dates(cap.period)
        
        # Check if this cap applies to the current request context
        applies = False
        
        if cap.cap_type == "global":
            applies = True
        elif cap.cap_type == "provider" and provider and cap.target_name == provider:
            applies = True
        elif cap.cap_type == "model" and model and cap.target_name == model:
            applies = True
        elif cap.cap_type == "customer" and customer_id and cap.target_name == customer_id:
            applies = True
        elif cap.cap_type == "agent" and agent and cap.target_name == agent:
            applies = True
        
        if not applies:
            continue
        
        # Calculate current spend for this cap
        current_spend = calculate_current_spend(
            session, user.id, cap.cap_type, cap.target_name, period_start, period_end
        )
        
        # Check if exceeded
        if current_spend >= cap.limit_amount:
            exceeded_caps.append({
                "cap_id": str(cap.id),
                "cap_type": cap.cap_type,
                "target_name": cap.target_name,
                "limit": cap.limit_amount,
                "current": current_spend,
                "period": cap.period,
                "exceeded_at": cap.exceeded_at.isoformat() if cap.exceeded_at else None,
            })
            
            # Mark as exceeded if not already
            if not cap.exceeded_at:
                cap.exceeded_at = datetime.utcnow()
                session.add(cap)
    
    # Commit any exceeded_at updates
    if exceeded_caps:
        session.commit()
    
    return {
        "allowed": len(exceeded_caps) == 0,
        "exceeded_caps": exceeded_caps,
        "message": f"{len(exceeded_caps)} hard cap(s) exceeded" if exceeded_caps else "All caps OK"
    }


@router.post("/check-now")
async def trigger_cap_check():
    """
    Manually trigger a cap check cycle.
    This checks all enabled caps and sends email alerts for any thresholds reached.
    """
    try:
        from cap_monitor import check_all_caps
        await check_all_caps()
        return {"status": "success", "message": "Cap check completed, alerts sent if thresholds exceeded"}
    except Exception as e:
        logger.error(f"Error triggering cap check: {e}")
        raise HTTPException(status_code=500, detail=f"Cap check failed: {str(e)}")


@router.post("/test-email")
async def test_email(email: str = Query(..., description="Email address to send test to")):
    """
    Send a test email to verify email configuration is working.
    """
    try:
        from email_service import send_alert_email
        success = await send_alert_email(
            to_email=email,
            alert_type="threshold_reached",
            target_type="global",
            target_name="Test Alert",
            current_spend=85.00,
            cap_limit=100.00,
            percentage=85.0,
            period="monthly",
        )
        if success:
            return {"status": "success", "message": f"Test email sent to {email}"}
        else:
            return {"status": "error", "message": "Email send failed - check logs"}
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=f"Email test failed: {str(e)}")


# =====================================================================
# PARAMETERIZED ROUTES - Must be defined LAST (after all specific routes)
# /{cap_id} would otherwise catch /alerts, /check, etc.
# =====================================================================

@router.get("/{cap_id}", response_model=CapResponse)
async def get_cap(
    cap_id: UUID,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Get a specific spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        enforcement=cap.enforcement,
        exceeded_at=cap.exceeded_at,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.patch("/{cap_id}", response_model=CapResponse)
async def update_cap(
    cap_id: UUID,
    cap_update: CapUpdate,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Update a spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    if cap_update.limit_amount is not None:
        cap.limit_amount = cap_update.limit_amount
    if cap_update.alert_threshold is not None:
        cap.alert_threshold = cap_update.alert_threshold
    if cap_update.alert_email is not None:
        cap.alert_email = cap_update.alert_email
    if cap_update.enforcement is not None:
        if cap_update.enforcement not in ["alert", "hard_block"]:
            raise HTTPException(status_code=400, detail="Enforcement must be 'alert' or 'hard_block'")
        cap.enforcement = cap_update.enforcement
    if cap_update.enabled is not None:
        cap.enabled = cap_update.enabled
    
    cap.updated_at = datetime.utcnow()
    session.add(cap)
    session.commit()
    session.refresh(cap)
    
    period_start, period_end = get_period_dates(cap.period)
    current_spend = calculate_current_spend(
        session, user.id, cap.cap_type, cap.target_name, period_start, period_end
    )
    
    logger.info(f"Updated spending cap {cap_id} for user {user.email}")
    
    return CapResponse(
        id=cap.id,
        cap_type=cap.cap_type,
        target_name=cap.target_name,
        limit_amount=cap.limit_amount,
        period=cap.period,
        enforcement=cap.enforcement,
        exceeded_at=cap.exceeded_at,
        alert_threshold=cap.alert_threshold,
        alert_email=cap.alert_email,
        enabled=cap.enabled,
        current_spend=current_spend,
        percentage_used=(current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0,
        created_at=cap.created_at,
        updated_at=cap.updated_at,
    )


@router.delete("/{cap_id}")
async def delete_cap(
    cap_id: UUID,
    user: User = Depends(get_current_clerk_user),
    session: Session = Depends(get_session),
):
    """Delete a spending cap."""
    cap = session.get(SpendingCap, cap_id)
    if not cap or cap.user_id != user.id:
        raise HTTPException(status_code=404, detail="Cap not found")
    
    session.delete(cap)
    session.commit()
    
    logger.info(f"Deleted spending cap {cap_id} for user {user.email}")
    
    return {"status": "success", "message": "Cap deleted"}
