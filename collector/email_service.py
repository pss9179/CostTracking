"""
Email notification service for alerts.

Supports SendGrid, AWS SES, and SMTP.
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Email provider config
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp")  # smtp, sendgrid, ses
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
AWS_SES_REGION = os.getenv("AWS_SES_REGION", "us-east-1")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@llmobserve.dev")


async def send_alert_email(
    to_email: str,
    alert_type: str,
    target_type: str,
    target_name: str,
    current_spend: float,
    cap_limit: float,
    percentage: float,
    period: str,
) -> bool:
    """
    Send an alert email to the user.
    
    Args:
        to_email: Recipient email
        alert_type: 'threshold_reached' or 'cap_exceeded'
        target_type: 'global', 'provider', 'model', 'agent', 'customer'
        target_name: Name of the target
        current_spend: Current spend amount
        cap_limit: Cap limit amount
        percentage: Percentage of cap used
        period: 'daily', 'weekly', 'monthly'
    
    Returns:
        True if email sent successfully, False otherwise
    """
    subject, body = _build_email_content(
        alert_type, target_type, target_name, current_spend, cap_limit, percentage, period
    )
    
    try:
        if EMAIL_PROVIDER == "sendgrid":
            return await _send_via_sendgrid(to_email, subject, body)
        elif EMAIL_PROVIDER == "ses":
            return await _send_via_ses(to_email, subject, body)
        else:
            return await _send_via_smtp(to_email, subject, body)
    except Exception as e:
        logger.error(f"Failed to send alert email to {to_email}: {e}")
        return False


def _build_email_content(
    alert_type: str,
    target_type: str,
    target_name: str,
    current_spend: float,
    cap_limit: float,
    percentage: float,
    period: str,
) -> tuple[str, str]:
    """Build email subject and body."""
    if alert_type == "threshold_reached":
        subject = f"⚠️ LLMObserve Alert: {percentage:.0f}% of your {period} spending cap reached"
        emoji = "⚠️"
        urgency = "Warning"
    else:  # cap_exceeded
        subject = f"🚨 LLMObserve Alert: Spending cap EXCEEDED for {period}"
        emoji = "🚨"
        urgency = "URGENT"
    
    target_display = target_name if target_type != "global" else "all services"
    
    body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 8px; margin-top: 20px; }}
        .alert-box {{ background: {"#fef2f2" if alert_type == "cap_exceeded" else "#fef9e7"}; border-left: 4px solid {"#dc2626" if alert_type == "cap_exceeded" else "#f59e0b"}; padding: 20px; margin: 20px 0; }}
        .metric {{ font-size: 32px; font-weight: bold; color: {"#dc2626" if alert_type == "cap_exceeded" else "#d97706"}; margin: 10px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }}
        a {{ color: #667eea; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{emoji} {urgency}: Spending Cap Alert</h1>
            <p style="margin: 0; opacity: 0.9;">LLMObserve Cost Monitoring</p>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <h2 style="margin-top: 0;">Your {period} spending is at:</h2>
                <div class="metric">${current_spend:.2f} / ${cap_limit:.2f}</div>
                <p style="font-size: 18px; margin: 0;"><strong>{percentage:.1f}%</strong> of your cap used</p>
            </div>
            
            <h3>Details:</h3>
            <ul style="line-height: 1.8;">
                <li><strong>Scope:</strong> {target_type.replace('_', ' ').title()}</li>
                <li><strong>Target:</strong> {target_display}</li>
                <li><strong>Period:</strong> {period.capitalize()}</li>
                <li><strong>Current Spend:</strong> ${current_spend:.4f}</li>
                <li><strong>Cap Limit:</strong> ${cap_limit:.2f}</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ul style="line-height: 1.8;">
                {"<li>🚨 <strong>IMMEDIATE ACTION REQUIRED:</strong> Your cap has been exceeded. Review your usage immediately.</li>" if alert_type == "cap_exceeded" else "<li>⚠️ Monitor your usage closely to avoid exceeding the cap.</li>"}
                <li>Review your <a href="https://app.llmobserve.dev/dashboard">Dashboard</a> for detailed cost breakdown</li>
                <li>Adjust your cap limits or optimize usage in <a href="https://app.llmobserve.dev/settings">Settings</a></li>
                <li>View cost trends by provider, model, and agent</li>
            </ul>
            
            <p style="margin-top: 30px; padding: 15px; background: #eff6ff; border-radius: 6px;">
                💡 <strong>Tip:</strong> Set up multiple caps (global, per-provider, per-model) for granular cost control.
            </p>
        </div>
        
        <div class="footer">
            <p>This alert was sent from <strong>LLMObserve</strong></p>
            <p>Manage your caps and alerts: <a href="https://app.llmobserve.dev/settings">Settings</a></p>
            <p style="margin-top: 20px; font-size: 10px;">
                You're receiving this because you set up a spending cap with email notifications.<br>
                To stop receiving these alerts, disable or delete the cap in your settings.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    return subject, body


async def _send_via_sendgrid(to_email: str, subject: str, body: str) -> bool:
    """Send email via SendGrid REST API."""
    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY not set")
        return False
    
    try:
        import httpx
        
        payload = {
            "personalizations": [
                {"to": [{"email": to_email}]}
            ],
            "from": {"email": FROM_EMAIL, "name": "LLMObserve Alerts"},
            "subject": subject,
            "content": [
                {"type": "text/html", "value": body}
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {SENDGRID_API_KEY}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        
        logger.info(f"Sent alert email via SendGrid to {to_email}, status: {response.status_code}")
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False


async def _send_via_ses(to_email: str, subject: str, body: str) -> bool:
    """Send email via AWS SES."""
    try:
        import boto3
        
        client = boto3.client("ses", region_name=AWS_SES_REGION)
        
        response = client.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": body}},
            },
        )
        
        logger.info(f"Sent alert email via SES to {to_email}, message_id: {response['MessageId']}")
        return True
    except Exception as e:
        logger.error(f"SES error: {e}")
        return False


async def _send_via_smtp(to_email: str, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not set, skipping email send (dev mode)")
        logger.info(f"Would send email to {to_email}: {subject}")
        return True  # Return True in dev mode for testing
    
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        
        # Add HTML body
        html_part = MIMEText(body, "html")
        msg.attach(html_part)
        
        # Connect and send
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Sent alert email via SMTP to {to_email}")
        return True
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return False

