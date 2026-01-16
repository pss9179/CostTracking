"""
Shared alerting logic for spending caps.

Used by both the background cap monitor and the /caps/check endpoint
to avoid duplicate alert handling and keep behavior consistent.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select, and_

from models import Alert, SpendingCap, User
from email_service import send_alert_email

logger = logging.getLogger(__name__)


async def maybe_send_cap_alert(
    session: Session,
    cap: SpendingCap,
    current_spend: float,
    period_start: datetime,
    period_end: datetime,
    alert_type: str,
    user: Optional[User] = None,
) -> bool:
    """
    Create an alert record and send email if needed.

    Returns True if an email was sent, False otherwise.
    """
    # Guard invalid alert types
    if alert_type not in ("threshold_reached", "cap_exceeded"):
        logger.warning(f"[CapAlerts] Invalid alert_type={alert_type} for cap {cap.id}")
        return False

    # Resolve user and email target
    if user is None:
        user = session.get(User, cap.user_id)
    to_email = (cap.alert_email or "").strip() or (user.email if user else "")

    if not to_email:
        logger.warning(f"[CapAlerts] No alert email available for cap {cap.id}")

    # Cooldown to avoid spam
    cooldown_minutes = 60
    if cap.last_alerted_at:
        time_since_alert = datetime.utcnow() - cap.last_alerted_at
        if time_since_alert < timedelta(minutes=cooldown_minutes):
            logger.debug(f"[CapAlerts] Skipping alert for cap {cap.id} (cooldown)")
            return False

    # Avoid duplicate alerts in the same period
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
        logger.debug(f"[CapAlerts] Alert already exists for cap {cap.id} in current period")
        return False

    percentage = (current_spend / cap.limit_amount * 100) if cap.limit_amount > 0 else 0

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
    session.flush()

    email_sent = False
    if to_email:
        email_sent = await send_alert_email(
            to_email=to_email,
            alert_type=alert_type,
            target_type=cap.cap_type,
            target_name=cap.target_name or "all services",
            current_spend=current_spend,
            cap_limit=cap.limit_amount,
            percentage=percentage,
            period=cap.period,
        )

    alert.email_sent = email_sent
    if email_sent:
        alert.email_sent_at = datetime.utcnow()

    session.add(alert)
    cap.last_alerted_at = datetime.utcnow()
    session.add(cap)

    logger.info(
        f"[CapAlerts] Alert triggered for cap {cap.id}: {alert_type} "
        f"({current_spend:.2f}/{cap.limit_amount:.2f} = {percentage:.1f}%) "
        f"email_sent={email_sent}"
    )

    return email_sent
