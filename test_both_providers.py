#!/usr/bin/env python3
"""
Test both OpenAI and Anthropic to verify costs are tracked correctly.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sdk" / "python"))

from llmobserve import observe, section, set_customer_id
from llmobserve.pricing import compute_cost
import anthropic
from openai import OpenAI

# API Keys from environment
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "https://llmobserve-api-production-d791.up.railway.app")

if not LLMOBSERVE_API_KEY or not ANTHROPIC_API_KEY or not OPENAI_API_KEY:
    print("ERROR: LLMOBSERVE_API_KEY, ANTHROPIC_API_KEY, and OPENAI_API_KEY must be set")
    sys.exit(1)

print("="*70)
print("🧪 TESTING BOTH PROVIDERS - OpenAI & Anthropic")
print("="*70)

# Initialize SDK
print("\n1. Initializing SDK...")
observe(
    collector_url=COLLECTOR_URL,
    api_key=LLMOBSERVE_API_KEY,
    use_instrumentors=True
)

# Test OpenAI
print("\n2. Testing OpenAI...")
client_openai = OpenAI(api_key=OPENAI_API_KEY)

with section("agent:openai_test"):
    set_customer_id("test_customer")
    
    response_openai = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello in one word"}],
        max_tokens=10
    )
    
    print(f"   ✅ OpenAI Response: {response_openai.choices[0].message.content}")
    print(f"   📊 Tokens: {response_openai.usage.prompt_tokens} input + {response_openai.usage.completion_tokens} output")
    
    expected_cost_openai = compute_cost(
        'openai',
        'gpt-4o-mini',
        response_openai.usage.prompt_tokens,
        response_openai.usage.completion_tokens
    )
    print(f"   💰 Expected cost: \${expected_cost_openai:.8f}")

# Test Anthropic
print("\n3. Testing Anthropic...")
client_anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

with section("agent:anthropic_test"):
    set_customer_id("test_customer")
    
    response_anthropic = client_anthropic.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=30,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    
    print(f"   ✅ Anthropic Response: {response_anthropic.content[0].text}")
    print(f"   📊 Tokens: {response_anthropic.usage.input_tokens} input + {response_anthropic.usage.output_tokens} output")
    
    expected_cost_anthropic = compute_cost(
        'anthropic',
        'claude-3-haiku-20240307',
        response_anthropic.usage.input_tokens,
        response_anthropic.usage.output_tokens
    )
    print(f"   💰 Expected cost: \${expected_cost_anthropic:.8f}")

# Flush events
print("\n4. Flushing events...")
time.sleep(2)
from llmobserve.transport import flush_events
flush_events()
print("   ✅ Events flushed!")

print("\n" + "="*70)
print("✅ TEST COMPLETE!")
print("="*70)
print("\n💡 Check dashboard - both OpenAI and Anthropic should show costs > $0")
print("   Expected: OpenAI ~$0.00001+, Anthropic ~$0.00001+")





