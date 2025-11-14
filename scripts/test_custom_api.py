"""
Example: Track ANY API with custom pricing

This shows how to track costs for ANY HTTP API - just add pricing!
"""
import os
import sys
import httpx
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from llmobserve import observe, section

# Initialize tracking
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"  # Proxy intercepts ALL HTTP calls
)

# Example 1: Track Stripe API (payment processing)
with section("payment:process"):
    # This will be tracked automatically!
    # Just add pricing to registry.json: "stripe:charges.create": {"per_call": 0.003}
    response = httpx.post(
        "https://api.stripe.com/v1/charges",
        headers={"Authorization": f"Bearer {os.getenv('STRIPE_API_KEY', 'sk_test_...')}"},
        json={"amount": 1000, "currency": "usd"}
    )
    print(f"Stripe call tracked! Status: {response.status_code}")

# Example 2: Track Twilio API (SMS)
with section("communication:sms"):
    # Add pricing: "twilio:messages.create": {"per_call": 0.0075}
    response = httpx.post(
        "https://api.twilio.com/2010-04-01/Accounts/ACxxx/Messages.json",
        auth=("ACxxx", os.getenv("TWILIO_AUTH_TOKEN", "")),
        data={"To": "+1234567890", "From": "+0987654321", "Body": "Hello"}
    )
    print(f"Twilio call tracked! Status: {response.status_code}")

# Example 3: Track ANY custom API
with section("custom:api_call"):
    # Just make HTTP call - automatically tracked!
    # Add pricing: "myapi:endpoint": {"per_call": 0.001}
    response = httpx.get("https://api.example.com/v1/data")
    print(f"Custom API tracked! Status: {response.status_code}")

print("\n✅ All API calls tracked! Check dashboard at http://localhost:3000")

