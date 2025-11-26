"""
Live test with real OpenAI API calls
"""
import os
import sys
import uuid
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

import llmobserve
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key=os.getenv("LLMOBSERVE_API_KEY", "your-api-key-here"),
    tenant_id="live_test"
)

from llmobserve import section, set_run_id, set_customer_id
from openai import OpenAI

print("="*80)
print("🚀 LIVE TEST - REAL OPENAI API CALLS")
print("="*80)

# OpenAI key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ Error: OPENAI_API_KEY environment variable not set")
    print("   Set it with: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

run_id = str(uuid.uuid4())
set_run_id(run_id)
set_customer_id("live_customer")

print(f"\n📊 Run ID: {run_id}")
print(f"📊 Customer: live_customer")
print(f"📊 Tenant: live_test")

print("\n🎯 Making API calls...")

with section("test_call"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello in 3 words"}],
        max_tokens=10
    )
    print(f"✅ Response: {response.choices[0].message.content}")
    print(f"💰 Tokens: {response.usage.total_tokens}")

print("\n✅ DONE! Check dashboard at http://localhost:3000")
print(f"   Look for run ID: {run_id}")
print()


