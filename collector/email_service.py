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
    """Build email subject and body with clean, minimal design."""
    
    # Determine alert severity
    is_exceeded = alert_type == "cap_exceeded"
    
    if is_exceeded:
        subject = f"🚨 Cap Exceeded: ${current_spend:.2f} / ${cap_limit:.2f} ({period})"
        status_color = "#dc2626"
        status_bg = "#fef2f2"
        status_text = "EXCEEDED"
    else:
        subject = f"⚠️ {percentage:.0f}% of {period} cap used (${current_spend:.2f}/${cap_limit:.2f})"
        status_color = "#f59e0b"
        status_bg = "#fffbeb"
        status_text = "WARNING"
    
    target_display = target_name if target_type != "global" else "All Services"
    
    # Progress bar width (cap at 100%)
    progress_width = min(percentage, 100)
    
    body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 520px; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: #0f172a; padding: 24px 32px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>
                                        <span style="color: white; font-size: 18px; font-weight: 600;">LLMObserve</span>
                                    </td>
                                    <td align="right">
                                        <span style="background: {status_bg}; color: {status_color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">{status_text}</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 32px;">
                            
                            <!-- Amount -->
                            <div style="text-align: center; margin-bottom: 24px;">
                                <div style="font-size: 42px; font-weight: 700; color: #0f172a; letter-spacing: -1px;">
                                    ${current_spend:.2f}
                                </div>
                                <div style="font-size: 14px; color: #64748b; margin-top: 4px;">
                                    of ${cap_limit:.2f} {period} limit
                                </div>
                            </div>
                            
                            <!-- Progress Bar -->
                            <div style="background: #e2e8f0; border-radius: 8px; height: 8px; margin: 20px 0; overflow: hidden;">
                                <div style="background: {status_color}; width: {progress_width}%; height: 100%; border-radius: 8px;"></div>
                            </div>
                            <div style="text-align: center; color: {status_color}; font-weight: 600; font-size: 14px; margin-bottom: 24px;">
                                {percentage:.1f}% used
                            </div>
                            
                            <!-- Details -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="background: #f8fafc; border-radius: 8px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 16px 20px; border-bottom: 1px solid #e2e8f0;">
                                        <span style="color: #64748b; font-size: 13px;">Scope</span>
                                        <div style="color: #0f172a; font-weight: 500; margin-top: 2px;">{target_type.replace('_', ' ').title()}</div>
                                    </td>
                                    <td style="padding: 16px 20px; border-bottom: 1px solid #e2e8f0;" align="right">
                                        <span style="color: #64748b; font-size: 13px;">Target</span>
                                        <div style="color: #0f172a; font-weight: 500; margin-top: 2px;">{target_display}</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 16px 20px;">
                                        <span style="color: #64748b; font-size: 13px;">Period</span>
                                        <div style="color: #0f172a; font-weight: 500; margin-top: 2px;">{period.capitalize()}</div>
                                    </td>
                                    <td style="padding: 16px 20px;" align="right">
                                        <span style="color: #64748b; font-size: 13px;">Remaining</span>
                                        <div style="color: #0f172a; font-weight: 500; margin-top: 2px;">${max(0, cap_limit - current_spend):.2f}</div>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <div style="text-align: center; margin-top: 28px;">
                                <a href="https://app.llmobserve.com/dashboard" style="display: inline-block; background: #0f172a; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 14px;">View Dashboard</a>
                            </div>
                            
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #f8fafc; padding: 20px 32px; border-top: 1px solid #e2e8f0;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="color: #64748b; font-size: 12px;">
                                        <a href="https://app.llmobserve.com/caps" style="color: #64748b; text-decoration: none;">Manage Caps</a>
                                        &nbsp;·&nbsp;
                                        <a href="https://app.llmobserve.com/settings" style="color: #64748b; text-decoration: none;">Settings</a>
                                    </td>
                                    <td align="right" style="color: #94a3b8; font-size: 11px;">
                                        LLMObserve
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
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

