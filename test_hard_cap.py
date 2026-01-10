#!/usr/bin/env python3
"""
Test hard cap blocking behavior.

Since your caps are already exceeded ($0.219 spent vs $0.010 limit),
this should demonstrate that LLM calls are being blocked.
"""

import os
import sys

# Set API keys
os.environ["LLMOBSERVE_API_KEY"] = "llmo_sk_ecb97196a31d6ef4ac4ddf7cc2360e15ede84f8109bf966d"
os.environ["OPENROUTER_API_KEY"] = "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"

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk/python"))

import llmobserve
from llmobserve import BudgetExceededError
from openai import OpenAI

print("=" * 70)
print("🧪 TESTING HARD CAP BLOCKING")
print("=" * 70)
print("""
Your current spending: $0.219
Your hard cap limit:   $0.010

Since you've exceeded the cap, LLM calls should be BLOCKED!
""")

# Initialize LLMObserve
llmobserve.observe(api_key=os.environ["LLMOBSERVE_API_KEY"])

# Create OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

print("\n📤 Attempting to make an LLM call...")
print("-" * 70)

try:
    response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[{"role": "user", "content": "Say hello!"}],
        max_tokens=20,
    )
    print(f"✅ Response: {response.choices[0].message.content}")
    print("\n⚠️  Call succeeded - Hard cap did NOT block this request!")
    print("   This could mean:")
    print("   1. The cap check is failing open (network issue)")
    print("   2. The cap is not properly configured as 'hard block'")
    print("   3. The SDK is not checking caps before requests")
    
except BudgetExceededError as e:
    print("🚫 SUCCESS! Hard cap is working correctly!")
    print("-" * 70)
    print(f"   Error: {e}")
    print("\n   Exceeded caps:")
    for cap in e.exceeded_caps:
        print(f"   - {cap['cap_type']}: ${cap['current']:.4f} / ${cap['limit']:.4f} ({cap['period']})")
    print("\n✅ Hard caps are properly blocking LLM calls!")
    
except Exception as e:
    print(f"❌ Unexpected error: {type(e).__name__}: {e}")
    print("\n   This is a different error, not a budget exceeded error.")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

