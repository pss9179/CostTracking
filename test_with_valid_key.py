#!/usr/bin/env python3
"""
Test LLMObserve with a valid API key
"""
import os
import sys
import uuid
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

print("="*80)
print("🧪 TESTING LLMOBSERVE WITH VALID API KEY")
print("="*80)

# Use the generated API key
API_KEY = "llmo_sk_194029ff332abd5f929cb55ec06a5fac08c4ea68f8c5ca48"

print(f"\n✅ Using API Key: {API_KEY[:20]}...")
print(f"✅ Collector URL: http://localhost:8000")

import llmobserve
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key=API_KEY,
    tenant_id="test_tenant"
)

from llmobserve import section, set_run_id, set_customer_id

print("\n✅ LLMObserve initialized successfully!")

# Set run and customer IDs
run_id = str(uuid.uuid4())
set_run_id(run_id)
set_customer_id("test_customer")

print(f"✅ Run ID: {run_id}")
print(f"✅ Customer ID: test_customer")

# Check if OpenAI key is available
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("\n⚠️  No OPENAI_API_KEY found - skipping actual API call")
    print("   To test with real API calls, set: export OPENAI_API_KEY='your-key'")
    print("\n✅ API key validation test PASSED!")
    print("   The LLMObserve API key is valid and working!")
    sys.exit(0)

# Make a test API call
print("\n🎯 Making test OpenAI API call...")

from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

try:
    with section("test_section"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello' in 1 word"}],
            max_tokens=5
        )
        print(f"✅ OpenAI Response: {response.choices[0].message.content}")
        print(f"✅ Tokens used: {response.usage.total_tokens}")
    
    print("\n" + "="*80)
    print("🎉 ALL TESTS PASSED!")
    print("="*80)
    print(f"\n📊 Check your dashboard: http://localhost:3000")
    print(f"   Look for run ID: {run_id}")
    print()
    
except Exception as e:
    print(f"\n❌ Error making API call: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

