#!/usr/bin/env python3
"""
Test script to verify model-specific caps work correctly.

This script:
1. Creates a model-specific cap for gpt-4o-mini ($0.01)
2. Makes an OpenAI API call with gpt-4o-mini
3. Verifies the call is blocked when cap is exceeded
"""
import os
import sys
import requests

# Initialize LLMObserve SDK FIRST (before importing OpenAI)
import llmobserve
llmobserve.observe(
    collector_url=os.getenv("NEXT_PUBLIC_COLLECTOR_URL", "http://localhost:8000"),
    api_key=os.getenv("LLMOBSERVE_API_KEY")
)

from openai import OpenAI

# Get environment variables
COLLECTOR_URL = os.getenv("NEXT_PUBLIC_COLLECTOR_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY")

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    print("   Set it with: export OPENAI_API_KEY=sk-...")
    sys.exit(1)

if not LLMOBSERVE_API_KEY:
    print("❌ ERROR: LLMOBSERVE_API_KEY not set")
    print("   Get it from your dashboard or set it with: export LLMOBSERVE_API_KEY=...")
    sys.exit(1)

print(f"✅ Using Collector: {COLLECTOR_URL}")
print(f"✅ OpenAI API Key: {OPENAI_API_KEY[:10]}...")
print(f"✅ LLMObserve API Key: {LLMOBSERVE_API_KEY[:10]}...")
print()

# Step 1: Get current user info
print("📋 Step 1: Getting user info...")
try:
    user_resp = requests.get(
        f"{COLLECTOR_URL}/users/me",
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
    )
    user_resp.raise_for_status()
    user_data = user_resp.json()
    user_id = user_data.get("id")
    print(f"   ✅ User ID: {user_id}")
except Exception as e:
    print(f"   ❌ Failed to get user info: {e}")
    sys.exit(1)

# Step 2: List existing caps
print("\n📋 Step 2: Checking existing caps...")
try:
    caps_resp = requests.get(
        f"{COLLECTOR_URL}/caps/",
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
    )
    caps_resp.raise_for_status()
    existing_caps = caps_resp.json()
    print(f"   ✅ Found {len(existing_caps)} existing caps")
    
    # Delete any existing gpt-4o-mini caps for clean test
    for cap in existing_caps:
        if cap.get("cap_type") == "model" and cap.get("target_name") == "gpt-4o-mini":
            print(f"   🗑️  Deleting existing gpt-4o-mini cap: {cap['id']}")
            requests.delete(
                f"{COLLECTOR_URL}/caps/{cap['id']}",
                headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
            )
except Exception as e:
    print(f"   ⚠️  Could not check existing caps: {e}")

# Step 3: Create a model-specific cap for gpt-4o-mini ($0.01)
print("\n📋 Step 3: Creating model-specific cap for gpt-4o-mini ($0.01)...")
try:
    cap_data = {
        "cap_type": "model",
        "target_name": "gpt-4o-mini",
        "limit_amount": 0.01,  # $0.01 - very low to trigger quickly
        "period": "daily",
        "enforcement": "hard_block",  # Hard block, not just alert
        "alert_threshold": 0.8,  # Alert at 80%
        "alert_email": None,
        "enabled": True
    }
    
    create_resp = requests.post(
        f"{COLLECTOR_URL}/caps/",
        json=cap_data,
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
    )
    create_resp.raise_for_status()
    cap = create_resp.json()
    cap_id = cap["id"]
    print(f"   ✅ Created cap: {cap_id}")
    print(f"      Type: {cap['cap_type']}")
    print(f"      Model: {cap['target_name']}")
    print(f"      Limit: ${cap['limit_amount']}/{cap['period']}")
    print(f"      Enforcement: {cap['enforcement']}")
except Exception as e:
    print(f"   ❌ Failed to create cap: {e}")
    if hasattr(e, 'response'):
        print(f"      Response: {e.response.text}")
    sys.exit(1)

# Step 4: Make an OpenAI API call with gpt-4o-mini
print("\n📋 Step 4: Making OpenAI API call with gpt-4o-mini...")
print("   This should be blocked if cap is exceeded...")

try:
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Make a call - this should be blocked if we've already spent $0.01
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'Hello, world!' in one word."}
        ],
        max_tokens=10
    )
    
    print(f"   ✅ API call succeeded!")
    print(f"      Response: {response.choices[0].message.content}")
    print(f"   ⚠️  NOTE: Cap was not exceeded, so call went through")
    print(f"      This means you haven't spent $0.01 on gpt-4o-mini yet today")
    
except Exception as e:
    error_str = str(e)
    if "BudgetExceededError" in error_str or "cap exceeded" in error_str.lower():
        print(f"   ✅ API call was BLOCKED by cap!")
        print(f"      Error: {error_str}")
        print(f"   🎉 SUCCESS: Model-specific cap enforcement is working!")
    else:
        print(f"   ❌ API call failed with unexpected error: {e}")
        print(f"      This might be an API key issue or network problem")

# Step 5: Check cap status
print("\n📋 Step 5: Checking cap status...")
try:
    cap_resp = requests.get(
        f"{COLLECTOR_URL}/caps/{cap_id}",
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
    )
    cap_resp.raise_for_status()
    cap_status = cap_resp.json()
    print(f"   ✅ Cap Status:")
    print(f"      Current Spend: ${cap_status.get('percentage_used', 0) * cap_status['limit_amount'] / 100:.4f}")
    print(f"      Limit: ${cap_status['limit_amount']}")
    print(f"      Percentage Used: {cap_status.get('percentage_used', 0):.2f}%")
    print(f"      Exceeded: {'Yes' if cap_status.get('exceeded_at') else 'No'}")
except Exception as e:
    print(f"   ⚠️  Could not check cap status: {e}")

# Step 6: Cleanup - delete the test cap
print("\n📋 Step 6: Cleaning up test cap...")
try:
    delete_resp = requests.delete(
        f"{COLLECTOR_URL}/caps/{cap_id}",
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"}
    )
    delete_resp.raise_for_status()
    print(f"   ✅ Deleted test cap")
except Exception as e:
    print(f"   ⚠️  Could not delete test cap: {e}")
    print(f"      You may want to delete it manually: {cap_id}")

print("\n✅ Test complete!")

