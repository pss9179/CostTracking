"""
Background service to monitor spending caps and trigger alerts.

Runs periodically to check all enabled caps and send email alerts when thresholds are reached.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from sqlmodel import Session, select, and_

from models import SpendingCap, Alert, User
from db import SessionLocal
from email_service import send_alert_email

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
    
    # Calculate current spend
    current_spend = calculate_current_spend(
        session,
        cap.user_id,
        cap.cap_type,
        cap.target_name,
        period_start,
        period_end,
    )
    
    # Calculate percentage
    percentage = (current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0
    
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
    
    # Check if we already sent an alert recently (avoid spam)
    cooldown_minutes = 60  # Don't send same alert more than once per hour
    if cap.last_alerted_at:
        time_since_alert = datetime.utcnow() - cap.last_alerted_at
        if time_since_alert < timedelta(minutes=cooldown_minutes):
            logger.debug(f"[CapMonitor] Skipping alert for cap {cap.id} (cooldown)")
            return
    
    # Check if we already have an alert for this period
    existing_alert = session.exec(
        select(Alert).where(
            and_(
                Alert.cap_id == cap.id,
                Alert.period_start == period_start,
                Alert.alert_type == alert_type,
            )
        )
    ).first()
    
    if existing_alert:
        logger.debug(f"[CapMonitor] Alert already exists for cap {cap.id} in current period")
        return
    
    # Create alert record
    alert = Alert(
        user_id=cap.user_id,
        cap_id=cap.id,
        alert_type=alert_type,
        current_spend=current_spend,
        cap_limit=cap.limit_amount,
        percentage=percentage,
        target_type=cap.cap_type,
        target_name=cap.target_name or "global",
        period_start=period_start,
        period_end=period_end,
    )
    
    session.add(alert)
    session.flush()  # Get alert ID
    
    # Send email
    email_sent = await send_alert_email(
        to_email=cap.alert_email,
        alert_type=alert_type,
        target_type=cap.cap_type,
        target_name=cap.target_name or "all services",
        current_spend=current_spend,
        cap_limit=cap.limit_amount,
        percentage=percentage,
        period=cap.period,
    )
    
    # Update alert record
    alert.email_sent = email_sent
    if email_sent:
        alert.email_sent_at = datetime.utcnow()
    
    session.add(alert)
    
    # Update cap's last_alerted_at
    cap.last_alerted_at = datetime.utcnow()
    session.add(cap)
    
    logger.info(
        f"[CapMonitor] Alert triggered for cap {cap.id}: {alert_type} "
        f"({current_spend:.2f}/{cap.limit_amount:.2f} = {percentage:.1f}%) "
        f"email_sent={email_sent}"
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

