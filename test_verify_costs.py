#!/usr/bin/env python3
"""
Verify that Anthropic events are being sent with costs.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "sdk" / "python"))

from llmobserve import observe, section, set_customer_id
from llmobserve.pricing import compute_cost
import anthropic

# API Keys - use environment variables
import os
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "https://llmobserve-api-production-d791.up.railway.app")

if not LLMOBSERVE_API_KEY or not ANTHROPIC_API_KEY:
    print("ERROR: LLMOBSERVE_API_KEY and ANTHROPIC_API_KEY environment variables must be set")
    sys.exit(1)

print("="*70)
print("🔍 VERIFYING ANTHROPIC COST CALCULATION")
print("="*70)

# Test SDK cost calculation first
print("\n1. Testing SDK cost calculation:")
test_cost = compute_cost('anthropic', 'claude-3-haiku-20240307', 20, 50)
print(f"   ✅ SDK calculates: \${test_cost:.8f} for 20+50 tokens")
if test_cost == 0.0:
    print("   ❌ ERROR: SDK returning $0!")
    sys.exit(1)

# Initialize SDK
print("\n2. Initializing SDK...")
observe(
    collector_url=COLLECTOR_URL,
    api_key=LLMOBSERVE_API_KEY,
    use_instrumentors=True
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Make a call and verify cost is calculated
print("\n3. Making Anthropic API call...")
with section("agent:cost_verification"):
    set_customer_id("verify_costs")
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=30,
        messages=[{"role": "user", "content": "Say hello"}]
    )
    
    print(f"   ✅ Response: {response.content[0].text}")
    print(f"   📊 Tokens: {response.usage.input_tokens} input + {response.usage.output_tokens} output")
    
    # Calculate expected cost
    expected_cost = compute_cost(
        'anthropic',
        'claude-3-haiku-20240307',
        response.usage.input_tokens,
        response.usage.output_tokens
    )
    print(f"   💰 Expected cost: \${expected_cost:.8f}")

# Flush events
print("\n4. Flushing events...")
time.sleep(2)
from llmobserve.transport import flush_events
flush_events()
print("   ✅ Events flushed!")

print("\n" + "="*70)
print("✅ VERIFICATION COMPLETE!")
print("="*70)
print("\n💡 Check dashboard - Claude should show costs > $0")
print("   Expected: ~$0.00001+ for this call")

