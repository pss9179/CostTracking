"""
Test script to send a sample alert email via SendGrid.
Run this to verify email alerts are working.
"""
import asyncio
import os
import sys

# Set environment variables for testing
os.environ["EMAIL_PROVIDER"] = "sendgrid"
os.environ["SENDGRID_API_KEY"] = os.getenv("SENDGRID_API_KEY", "your_sendgrid_api_key_here")
os.environ["FROM_EMAIL"] = "alerts@llmobserve.com"

# Add collector to path
sys.path.insert(0, 'collector')

from collector.email_service import send_alert_email

async def test_email():
    """Send a test alert email."""
    print("🧪 Testing SendGrid email alerts...")
    print(f"   To: pss9179@stern.nyu.edu")
    print(f"   From: alerts@llmobserve.com")
    print()
    
    success = await send_alert_email(
        to_email="pss9179@stern.nyu.edu",
        alert_type="threshold_reached",
        target_type="global",
        target_name="all services",
        current_spend=8.42,
        cap_limit=10.00,
        percentage=84.2,
        period="daily"
    )
    
    if success:
        print("✅ Email sent successfully!")
        print()
        print("📬 Check your inbox (and spam folder):")
        print("   pss9179@stern.nyu.edu")
        print()
        print("   Subject: ⚠️ LLMObserve Alert: 84% of your daily spending cap reached")
        print()
        print("🎯 If you received it, email alerts are working!")
    else:
        print("❌ Failed to send email")
        print("   Check the error messages above")
        print()
        print("💡 Troubleshooting:")
        print("   1. Verify SENDGRID_API_KEY is correct")
        print("   2. Check SendGrid dashboard for activity")
        print("   3. Make sure sender email is verified")

if __name__ == "__main__":
    asyncio.run(test_email())

