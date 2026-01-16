"""
Background service to monitor spending caps and trigger alerts.

Runs periodically to check all enabled caps and send email alerts when thresholds are reached.
"""
import asyncio
import logging

from sqlmodel import Session, select

from models import SpendingCap, User
from db import SessionLocal
from cap_alerts import maybe_send_cap_alert

logger = logging.getLogger(__name__)

# Import cap calculation functions
from routers.caps import get_period_dates, calculate_current_spend


async def check_all_caps():
    """Check all enabled spending caps and trigger alerts if needed."""
    logger.info("[CapMonitor] Starting cap check cycle...")
    
    session = None
    try:
        session = SessionLocal()
        
        # Get all enabled caps
        caps = session.exec(
            select(SpendingCap).where(SpendingCap.enabled == True)
        ).all()
        
        logger.info(f"[CapMonitor] Checking {len(caps)} enabled caps")
        
        for cap in caps:
            try:
                await check_single_cap(session, cap)
                session.commit()  # Commit after each successful cap check
            except Exception as e:
                logger.error(f"[CapMonitor] Error checking cap {cap.id}: {e}")
                # Rollback and get a fresh session to continue
                try:
                    session.rollback()
                except Exception:
                    pass
                # Close and recreate session to clear invalid state
                try:
                    session.close()
                except Exception:
                    pass
                session = SessionLocal()
        
        logger.info("[CapMonitor] Cap check cycle complete")
    except Exception as e:
        logger.error(f"[CapMonitor] Error in cap check cycle: {e}")
        if session:
            try:
                session.rollback()
            except Exception:
                pass
    finally:
        if session:
            try:
                session.close()
            except Exception:
                pass


async def check_single_cap(session: Session, cap: SpendingCap):
    """Check a single spending cap and trigger alert if needed."""
    # Calculate period dates
    period_start, period_end = get_period_dates(cap.period)
    
    # Look up user to get clerk_user_id for proper data isolation
    user = session.get(User, cap.user_id)
    clerk_user_id = user.clerk_user_id if user else None
    
    # Calculate current spend with clerk_user_id for proper filtering
    current_spend = calculate_current_spend(
        session,
        cap.user_id,
        cap.cap_type,
        cap.target_name,
        period_start,
        period_end,
        clerk_user_id=clerk_user_id,
        sub_scope=getattr(cap, 'sub_scope', None),
        sub_target=getattr(cap, 'sub_target', None),
    )
    
    # Determine if alert should be triggered
    should_alert = False
    alert_type = None
    
    if current_spend >= cap.limit_amount:
        alert_type = "cap_exceeded"
        should_alert = True
    elif percentage >= (cap.alert_threshold * 100):
        alert_type = "threshold_reached"
        should_alert = True
    
    if not should_alert:
        # No alert needed
        return
    
    await maybe_send_cap_alert(
        session=session,
        cap=cap,
        current_spend=current_spend,
        period_start=period_start,
        period_end=period_end,
        alert_type=alert_type,
        user=user,
    )


async def run_cap_monitor(check_interval_seconds: int = 300):
    """
    Run the cap monitor service continuously.
    
    Args:
        check_interval_seconds: How often to check caps (default: 5 minutes)
    """
    logger.info(f"[CapMonitor] Starting service (check interval: {check_interval_seconds}s)")
    
    while True:
        try:
            await check_all_caps()
        except Exception as e:
            logger.error(f"[CapMonitor] Unexpected error: {e}", exc_info=True)
        
        # Wait before next check
        await asyncio.sleep(check_interval_seconds)


if __name__ == "__main__":
    # For standalone testing
    logging.basicConfig(level=logging.INFO)
    asyncio.run(check_all_caps())

