#!/usr/bin/env python3
"""
Test script for LLMObserve Spending Caps & Alerts

This script tests:
1. Soft caps (email alerts at thresholds)
2. Hard caps (blocking LLM calls when exceeded)

Usage:
    python test_caps.py
"""

import os
import sys
import time

# Set API keys
os.environ["LLMOBSERVE_API_KEY"] = "llmo_sk_ecb97196a31d6ef4ac4ddf7cc2360e15ede84f8109bf966d"
os.environ["OPENROUTER_API_KEY"] = "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"

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk/python"))

import llmobserve
from llmobserve import section, set_customer_id, BudgetExceededError
from openai import OpenAI

# Initialize LLMObserve
print("=" * 60)
print("🔍 TESTING LLMOBSERVE SPENDING CAPS & ALERTS")
print("=" * 60)

llmobserve.observe(
    api_key=os.environ["LLMOBSERVE_API_KEY"],
    # collector_url is auto-set to production
)

# Create OpenRouter client (uses OpenAI-compatible API)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def make_llm_call(prompt: str, model: str = "mistralai/mistral-7b-instruct:free"):
    """Make a simple LLM call via OpenRouter (using free tier model)."""
    print(f"\n📤 Making LLM call with model: {model}")
    print(f"   Prompt: {prompt[:50]}...")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        result = response.choices[0].message.content
        print(f"   ✅ Response: {result[:100]}...")
        return result
    except BudgetExceededError as e:
        print(f"   🚫 BUDGET EXCEEDED! Cap hit.")
        print(f"      Message: {e}")
        for cap in e.exceeded_caps:
            print(f"      - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f}")
        raise
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        raise


def test_basic_tracking():
    """Test 1: Basic cost tracking (no caps)."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Cost Tracking")
    print("=" * 60)
    
    # Make a few calls to establish baseline
    with section("test:basic_tracking"):
        make_llm_call("Say 'Hello World' in exactly 3 words.")
        time.sleep(1)
        make_llm_call("What is 2 + 2?")
        time.sleep(1)
    
    print("\n✅ Basic tracking test complete!")
    print("   Check your dashboard to see these costs.")


def test_soft_cap_alerts():
    """Test 2: Soft cap with email alerts."""
    print("\n" + "=" * 60)
    print("TEST 2: Soft Cap (Email Alerts)")
    print("=" * 60)
    print("""
    To test soft cap alerts:
    
    1. Go to https://app.llmobserve.com/caps
    2. Create a new cap:
       - Type: Global (or Provider: openrouter)
       - Limit: $0.001 (very low to trigger quickly)
       - Period: Daily
       - Enforcement: Alert Only (soft cap)
       - Alert Threshold: 80%
       - Alert Email: ethanzzheng@gmail.com
    3. Run this script to make LLM calls
    4. Check your email for alerts!
    """)
    
    with section("test:soft_cap"):
        for i in range(3):
            make_llm_call(f"Test call {i+1}: Say something short.")
            time.sleep(1)
    
    print("\n📧 Check ethanzzheng@gmail.com for alert emails!")


def test_hard_cap_blocking():
    """Test 3: Hard cap that blocks LLM calls."""
    print("\n" + "=" * 60)
    print("TEST 3: Hard Cap (Blocks Requests)")
    print("=" * 60)
    print("""
    To test hard cap blocking:
    
    1. Go to https://app.llmobserve.com/caps
    2. Create a new cap:
       - Type: Global
       - Limit: $0.0001 (extremely low)
       - Period: Daily
       - Enforcement: Hard Block
       - Alert Email: ethanzzheng@gmail.com
    3. Run this script - calls should be BLOCKED after cap is hit!
    """)
    
    calls_made = 0
    calls_blocked = 0
    
    with section("test:hard_cap"):
        for i in range(5):
            try:
                make_llm_call(f"Hard cap test {i+1}: Count to 3.")
                calls_made += 1
                time.sleep(1)
            except BudgetExceededError:
                calls_blocked += 1
                print(f"   🛑 Call {i+1} was BLOCKED by hard cap!")
    
    print(f"\n📊 Results: {calls_made} calls succeeded, {calls_blocked} calls blocked")
    
    if calls_blocked > 0:
        print("✅ Hard cap is working! LLM calls are being blocked.")
    else:
        print("⚠️  No calls were blocked. Either:")
        print("   - You haven't set up a hard cap yet")
        print("   - The cap limit is higher than your current spend")


def check_current_caps():
    """Check current caps via API."""
    print("\n" + "=" * 60)
    print("CHECKING CURRENT CAPS")
    print("=" * 60)
    
    import requests
    
    api_key = os.environ["LLMOBSERVE_API_KEY"]
    collector_url = "https://llmobserve-api-production-d791.up.railway.app"
    
    try:
        # This endpoint requires Clerk auth, so we'll just show the dashboard link
        print(f"\n🔗 View your caps at: https://app.llmobserve.com/caps")
        print(f"🔗 View alerts at: https://app.llmobserve.com/caps (Alerts tab)")
    except Exception as e:
        print(f"Error checking caps: {e}")


def trigger_cap_check():
    """Manually trigger cap check cycle."""
    print("\n" + "=" * 60)
    print("TRIGGERING CAP CHECK (SENDS ALERTS IF THRESHOLDS HIT)")
    print("=" * 60)
    
    import requests
    
    collector_url = "https://llmobserve-api-production-d791.up.railway.app"
    
    try:
        response = requests.post(f"{collector_url}/caps/check-now", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cap check triggered: {result.get('message', 'Success')}")
        else:
            print(f"⚠️  Cap check returned: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Error triggering cap check: {e}")


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         LLMOBSERVE SPENDING CAPS & ALERTS TEST               ║
╠══════════════════════════════════════════════════════════════╣
║  This script will:                                            ║
║  1. Make LLM calls to track costs                            ║
║  2. Test soft caps (email alerts)                            ║
║  3. Test hard caps (blocking)                                ║
║                                                               ║
║  Email alerts will be sent to: ethanzzheng@gmail.com         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check current caps
    check_current_caps()
    
    # Run tests
    test_basic_tracking()
    
    # Wait for events to flush
    print("\n⏳ Waiting for events to flush to collector...")
    time.sleep(3)
    
    # Trigger cap check to send any pending alerts
    trigger_cap_check()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("""
    1. Go to https://app.llmobserve.com/caps
    
    2. CREATE A SOFT CAP:
       - Click "Add Cap"
       - Type: Global
       - Limit: $0.01 (1 cent)
       - Period: Daily
       - Enforcement: Alert Only
       - Alert at: 80%
       - Email: ethanzzheng@gmail.com
       
    3. CREATE A HARD CAP:
       - Click "Add Cap" 
       - Type: Global
       - Limit: $0.001 (0.1 cent)
       - Period: Daily
       - Enforcement: Hard Block
       - Email: ethanzzheng@gmail.com
       
    4. Run this script again:
       python test_caps.py
       
    5. Check your email for alerts!
    """)


if __name__ == "__main__":
    main()

