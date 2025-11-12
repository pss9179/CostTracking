"""
Test script that uses a REAL API key from a user account.
This way you can test and see the results in the actual dashboard!

Usage:
1. Sign up at http://localhost:3000/signup
2. Copy your API key
3. Update LLMOBSERVE_API_KEY below
4. Run this script
5. Refresh the dashboard to see your data!
"""

import os
import sys

# Add SDK to path
sys.path.insert(0, "/Users/pranavsrigiriraju/CostTracking/sdk/python")

import llmobserve
from openai import OpenAI

# ============================================================================
# CONFIGURE WITH YOUR API KEY FROM SIGNUP
# ============================================================================
LLMOBSERVE_API_KEY = "llmo_sk_YOUR_API_KEY_HERE"  # Replace with your API key!

# Initialize LLMObserve with your API key
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key=LLMOBSERVE_API_KEY,
    # If you're a SaaS founder, you can track per-customer:
    # customer_id="your_customer_id"
)

# ============================================================================
# Run your test code
# ============================================================================

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

print("🚀 Running test with OpenAI...")
print(f"📊 View results at: http://localhost:3000\n")

# Test 1: Simple call
with llmobserve.section("simple_test"):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say 'Hello World' and nothing else."}],
        max_tokens=10
    )
    print(f"✅ Simple test: {response.choices[0].message.content}")

# Test 2: Agent simulation
with llmobserve.section("agent:customer_support"):
    with llmobserve.section("step:understand_query"):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "What's the weather?"}],
            max_tokens=20
        )
        print(f"✅ Agent step 1: {response.choices[0].message.content[:50]}...")
    
    with llmobserve.section("step:generate_response"):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Tell me a joke"}],
            max_tokens=50
        )
        print(f"✅ Agent step 2: {response.choices[0].message.content[:50]}...")

print("\n✨ Done! Refresh your dashboard at http://localhost:3000")
print("💡 You should see:")
print("  - 3 API calls")
print("  - Costs broken down by section")
print("  - Agent hierarchy in the Agents tab")

