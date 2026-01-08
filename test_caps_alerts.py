#!/usr/bin/env python3
"""
Test Spending Caps and Alerts with the published llmobserve-sdk

This script tests:
1. Creating spending caps via the API
2. Making LLM calls that approach/exceed caps
3. Verifying that BudgetExceededError is raised when cap is exceeded
4. Testing alerts notifications
"""
import os
import sys
import time
import httpx

# Test configuration
COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # Set via: export OPENROUTER_API_KEY='sk-or-v1-xxx'

# Get API key from environment or use a test key
# You can set this via: export LLMOBSERVE_API_KEY='llmo_sk_xxx'
API_KEY = os.getenv("LLMOBSERVE_API_KEY", "")

# Instructions for getting API key:
# 1. Go to https://app.llmobserve.com/settings
# 2. Create a new API key or use an existing one
# 3. Set it: export LLMOBSERVE_API_KEY='llmo_sk_xxx'

def test_caps_check_endpoint():
    """Test the /caps/check endpoint directly."""
    print("\n" + "="*60)
    print("TEST 1: Direct Caps Check Endpoint")
    print("="*60)
    
    if not API_KEY:
        print("⚠️  No API key set. Skipping authenticated cap check.")
        print("   Set LLMOBSERVE_API_KEY environment variable to test with auth.")
        return
    
    try:
        response = httpx.get(
            f"{COLLECTOR_URL}/caps/check",
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"provider": "openai", "model": "gpt-4o"},
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("allowed"):
                print("✅ Request allowed - no caps exceeded")
            else:
                print("🚫 Request blocked - cap exceeded!")
                for cap in result.get("exceeded_caps", []):
                    print(f"   - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f}")
        elif response.status_code == 401:
            print("❌ Invalid API key")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_list_caps():
    """Test listing existing caps."""
    print("\n" + "="*60)
    print("TEST 2: List Existing Caps")
    print("="*60)
    
    if not API_KEY:
        print("⚠️  No API key set. Skipping.")
        return
    
    try:
        response = httpx.get(
            f"{COLLECTOR_URL}/caps/",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            caps = response.json()
            if caps:
                print(f"Found {len(caps)} caps:")
                for cap in caps:
                    print(f"  - {cap.get('cap_type', 'unknown')}: "
                          f"${cap.get('limit_amount', 0):.2f}/{cap.get('period', '?')} "
                          f"(enforce: {cap.get('enforce_type', '?')})")
            else:
                print("No caps configured yet.")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_create_cap():
    """Test creating a spending cap."""
    print("\n" + "="*60)
    print("TEST 3: Create a Test Spending Cap")
    print("="*60)
    
    if not API_KEY:
        print("⚠️  No API key set. Skipping.")
        return
    
    # Create a very low cap for testing ($0.01 daily)
    cap_data = {
        "cap_type": "global",
        "period": "daily",
        "limit_amount": 0.01,  # Very low for testing
        "enforce_type": "hard",  # Will block requests
        "alert_threshold_percent": 50
    }
    
    try:
        response = httpx.post(
            f"{COLLECTOR_URL}/caps/",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=cap_data,
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code in [200, 201]:
            print("✅ Cap created successfully!")
        else:
            print(f"❌ Failed to create cap")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_sdk_with_caps():
    """Test the SDK with caps enforcement."""
    print("\n" + "="*60)
    print("TEST 4: SDK with Caps Enforcement")
    print("="*60)
    
    try:
        # Import the published SDK (package is llmobserve-sdk, module is llmobserve)
        from llmobserve import observe, BudgetExceededError
        from llmobserve.caps import check_spending_caps
        
        print("✅ Successfully imported llmobserve (from llmobserve-sdk package)")
        
        # Initialize observe
        observe(
            collector_url=COLLECTOR_URL,
            api_key=API_KEY if API_KEY else "test_key_for_demo",
        )
        print("✅ observe() initialized")
        
        # Test manual cap check
        print("\nTesting manual cap check...")
        try:
            result = check_spending_caps(
                provider="openai",
                model="gpt-4o"
            )
            print(f"Cap check result: {result}")
        except BudgetExceededError as e:
            print(f"🚫 Budget exceeded: {e}")
        except Exception as e:
            print(f"Cap check error: {e}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure llmobserve-sdk is installed: pip install llmobserve-sdk")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_make_llm_call_with_caps():
    """Make an actual LLM call and verify caps are checked."""
    print("\n" + "="*60)
    print("TEST 5: Make LLM Call with Caps Enforcement")
    print("="*60)
    
    try:
        from llmobserve import observe, set_customer_id, BudgetExceededError
        
        # Initialize
        observe(
            collector_url=COLLECTOR_URL,
            api_key=API_KEY if API_KEY else "test_key",
        )
        
        # Set a test customer
        set_customer_id("test_caps_customer")
        
        print("\nMaking OpenRouter API call...")
        
        # Make an API call via OpenRouter
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Say 'caps test' in 2 words"}],
                "max_tokens": 10
            },
            timeout=30.0
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API call successful!")
            print(f"   Model: {result.get('model')}")
            print(f"   Response: {result['choices'][0]['message']['content']}")
            usage = result.get('usage', {})
            print(f"   Tokens: {usage.get('prompt_tokens', 0)} in, {usage.get('output_tokens', 0)} out")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   {response.text}")
            
    except BudgetExceededError as e:
        print(f"🚫 Budget exceeded (caps working!):")
        print(f"   {e}")
        for cap in e.exceeded_caps:
            print(f"   - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_alerts_endpoint():
    """Test the alerts endpoint."""
    print("\n" + "="*60)
    print("TEST 6: Alerts Endpoint")
    print("="*60)
    
    if not API_KEY:
        print("⚠️  No API key set. Skipping.")
        return
    
    try:
        response = httpx.get(
            f"{COLLECTOR_URL}/alerts/",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10.0
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            alerts = response.json()
            if alerts:
                print(f"Found {len(alerts)} alerts:")
                for alert in alerts[:5]:  # Show first 5
                    print(f"  - {alert.get('alert_type', 'unknown')}: {alert.get('message', '')[:50]}...")
            else:
                print("No alerts yet.")
        else:
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("="*60)
    print("LLMOBSERVE-SDK CAPS & ALERTS TEST")
    print("="*60)
    print(f"\nCollector URL: {COLLECTOR_URL}")
    print(f"API Key: {'***' + API_KEY[-8:] if API_KEY else 'NOT SET'}")
    print(f"OpenRouter Key: {'***' + OPENROUTER_API_KEY[-8:] if OPENROUTER_API_KEY else 'NOT SET'}")
    
    if not API_KEY:
        print("\n⚠️  WARNING: LLMOBSERVE_API_KEY not set!")
        print("   Set it to test authenticated features:")
        print("   export LLMOBSERVE_API_KEY='llmo_sk_xxx'")
    
    # Run tests
    test_caps_check_endpoint()
    test_list_caps()
    # test_create_cap()  # Uncomment to create a cap
    test_sdk_with_caps()
    test_make_llm_call_with_caps()
    test_alerts_endpoint()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

