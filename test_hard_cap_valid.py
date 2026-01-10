#!/usr/bin/env python3
"""
Test hard cap blocking with VALID API key.
"""

import os
import sys

# NEW VALID API KEY
os.environ["LLMOBSERVE_API_KEY"] = "llmo_sk_bf2c0bc8c4002b49ff3df9af15b1bbc8bfcf2babc7e89f9b"
os.environ["OPENROUTER_API_KEY"] = "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"

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk/python"))

print("=" * 70)
print("🔍 TESTING CAPS WITH VALID API KEY")
print("=" * 70)

# First, test the /caps/check endpoint directly with the new key
import requests

api_key = os.environ["LLMOBSERVE_API_KEY"]
collector_url = "https://llmobserve-api-production-d791.up.railway.app"

print(f"\n1. Testing /caps/check with new API key...")
print(f"   Key: {api_key[:20]}...")

try:
    response = requests.get(
        f"{collector_url}/caps/check",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Response: {result}")
    
    if result.get("exceeded_caps"):
        print("\n   🚫 HARD CAPS EXCEEDED!")
        for cap in result["exceeded_caps"]:
            print(f"      - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f} ({cap['period']})")
    elif result.get("message") == "No active hard caps":
        print("\n   ⚠️  No hard caps found. Either:")
        print("      - The API key user doesn't have hard caps")
        print("      - The caps are not marked as 'hard_block'")
    else:
        print(f"\n   ✅ Caps OK: {result.get('message')}")
        
except Exception as e:
    print(f"   Error: {e}")

# Now test with SDK
print(f"\n2. Testing SDK cap check...")
import llmobserve
from llmobserve import BudgetExceededError
from openai import OpenAI

llmobserve.observe(api_key=api_key)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

print("\n3. Making LLM call (should be blocked if hard cap exceeded)...")
try:
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[{"role": "user", "content": "Say 'test'"}],
        max_tokens=5,
    )
    print(f"   ✅ Call succeeded: {response.choices[0].message.content}")
    print("   ⚠️  Hard cap did NOT block the request")
except BudgetExceededError as e:
    print(f"   🚫 BLOCKED by hard cap!")
    print(f"   Message: {e}")
    for cap in e.exceeded_caps:
        print(f"      - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f}")
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)

