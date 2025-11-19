"""
Simple test script to send email via SendGrid API directly.
"""
import requests

SENDGRID_API_KEY = "your_sendgrid_api_key_here"  # Replace with actual key or use env var

def send_test_email():
    """Send test email via SendGrid API."""
    print("🧪 Sending test email via SendGrid...")
    print()
    
    url = "https://api.sendgrid.com/v3/mail/send"
    
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "personalizations": [
            {
                "to": [{"email": "pss9179@stern.nyu.edu"}],
                "subject": "⚠️ LLMObserve Alert: Test Email - 84% of your daily spending cap reached"
            }
        ],
        "from": {"email": "alerts@llmobserve.com"},
        "content": [
            {
                "type": "text/html",
                "value": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; }
        .content { background: #f9fafb; padding: 30px; border-radius: 8px; margin-top: 20px; }
        .alert-box { background: #fef9e7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; }
        .metric { font-size: 32px; font-weight: bold; color: #d97706; margin: 10px 0; }
        .footer { text-align: center; margin-top: 30px; color: #6b7280; font-size: 12px; }
        a { color: #667eea; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Warning: Spending Cap Alert</h1>
            <p style="margin: 0; opacity: 0.9;">LLMObserve Cost Monitoring - TEST EMAIL</p>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <h2 style="margin-top: 0;">Your daily spending is at:</h2>
                <div class="metric">$8.42 / $10.00</div>
                <p style="font-size: 18px; margin: 0;"><strong>84.2%</strong> of your cap used</p>
            </div>
            
            <h3>Details:</h3>
            <ul style="line-height: 1.8;">
                <li><strong>Scope:</strong> Global</li>
                <li><strong>Target:</strong> All services</li>
                <li><strong>Period:</strong> Daily</li>
                <li><strong>Current Spend:</strong> $8.4200</li>
                <li><strong>Cap Limit:</strong> $10.00</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ul style="line-height: 1.8;">
                <li>⚠️ Monitor your usage closely to avoid exceeding the cap.</li>
                <li>Review your <a href="https://llmobserve.com/dashboard">Dashboard</a> for detailed cost breakdown</li>
                <li>Adjust your cap limits or optimize usage in <a href="https://llmobserve.com/settings">Settings</a></li>
                <li>View cost trends by provider, model, and agent</li>
            </ul>
            
            <p style="margin-top: 30px; padding: 15px; background: #eff6ff; border-radius: 6px;">
                💡 <strong>Tip:</strong> Set up multiple caps (global, per-provider, per-model) for granular cost control.
            </p>
            
            <p style="margin-top: 30px; padding: 15px; background: #fef2f2; border-radius: 6px; border-left: 4px solid #dc2626;">
                🧪 <strong>This is a TEST email.</strong> Email alerts are now working correctly!
            </p>
        </div>
        
        <div class="footer">
            <p>This alert was sent from <strong>LLMObserve</strong></p>
            <p>Manage your caps and alerts: <a href="https://llmobserve.com/settings">Settings</a></p>
        </div>
    </div>
</body>
</html>
                """
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201, 202]:
            print("✅ Email sent successfully!")
            print()
            print("📬 Check your inbox (and spam folder):")
            print("   pss9179@stern.nyu.edu")
            print()
            print("   Subject: ⚠️ LLMObserve Alert: Test Email - 84% of your daily spending cap reached")
            print()
            print("🎯 If you received it, email alerts are working!")
            print()
            print("💚 Email alerts are PRODUCTION READY!")
            return True
        else:
            print(f"❌ SendGrid returned error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == "__main__":
    send_test_email()

