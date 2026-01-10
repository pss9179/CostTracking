#!/usr/bin/env python3
"""
Debug test for hard cap checking.
"""

import os
import sys
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("llmobserve").setLevel(logging.DEBUG)

# Set API keys
os.environ["LLMOBSERVE_API_KEY"] = "llmo_sk_ecb97196a31d6ef4ac4ddf7cc2360e15ede84f8109bf966d"
os.environ["OPENROUTER_API_KEY"] = "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"

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk/python"))

# First, let's manually test the cap check API
print("=" * 70)
print("🔍 DEBUG: Testing cap check API directly")
print("=" * 70)

import requests

api_key = os.environ["LLMOBSERVE_API_KEY"]
collector_url = "https://llmobserve-api-production-d791.up.railway.app"

# Test the /caps/check endpoint directly
print(f"\n1. Testing /caps/check endpoint...")
try:
    response = requests.get(
        f"{collector_url}/caps/check",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"provider": "openrouter"},
        timeout=30,
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

# Now test with the SDK's cap check function
print(f"\n2. Testing SDK's check_spending_caps function...")
try:
    from llmobserve.caps import check_spending_caps, should_check_caps
    
    print(f"   should_check_caps(): {should_check_caps()}")
    
    result = check_spending_caps(provider="openrouter")
    print(f"   Result: {result}")
except Exception as e:
    print(f"   Error: {type(e).__name__}: {e}")

# Now let's import and configure llmobserve properly
print(f"\n3. Initializing LLMObserve and making test call...")
import llmobserve
from llmobserve import BudgetExceededError
from openai import OpenAI

llmobserve.observe(api_key=api_key)

# Create OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

print("\n4. Making LLM call (should be blocked if cap exceeded)...")
try:
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[{"role": "user", "content": "Say 'test'"}],
        max_tokens=5,
    )
    print(f"   ✅ Call succeeded: {response.choices[0].message.content}")
    print("   ⚠️  Hard cap did NOT block!")
except BudgetExceededError as e:
    print(f"   🚫 Blocked by hard cap!")
    print(f"   {e}")
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)

