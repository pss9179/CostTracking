#!/usr/bin/env python3
"""
Test script to verify multi-user API key isolation and tracking.

This script tests:
1. Multiple LLMObserve API keys (different users)
2. Multiple provider API keys (OpenAI, Anthropic)
3. Data isolation between users
4. Customer tracking
5. Agent/section labeling

Requirements:
- LLMObserve API keys (from dashboard at http://localhost:3000/settings)
- Provider API keys (OpenAI, Anthropic) - your actual LLM service keys
- Collector running on http://localhost:8000
"""

import os
import sys
import time
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent / "sdk" / "python"))

from llmobserve import observe, section, set_customer_id
from openai import OpenAI

# Try to import Anthropic
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic SDK not installed. Install with: pip install anthropic")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# LLMObserve API Keys (get from http://localhost:3000/settings)
# Create multiple accounts or API keys to test isolation
LLMOBSERVE_API_KEY_USER1 = os.getenv("LLMOBSERVE_API_KEY_USER1", "")
LLMOBSERVE_API_KEY_USER2 = os.getenv("LLMOBSERVE_API_KEY_USER2", "")

# Provider API Keys (your actual OpenAI/Anthropic keys)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Collector URL
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")

# ============================================================================
# VALIDATION
# ============================================================================

if not LLMOBSERVE_API_KEY_USER1:
    print("❌ ERROR: LLMOBSERVE_API_KEY_USER1 not set")
    print("   Get it from: http://localhost:3000/settings")
    print("   Or set: export LLMOBSERVE_API_KEY_USER1='llmo_sk_...'")
    sys.exit(1)

if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not set")
    print("   Set it: export OPENAI_API_KEY='sk-...'")
    sys.exit(1)

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_user1_openai(api_key: str):
    """Test User 1 with OpenAI."""
    print("\n" + "="*70)
    print("👤 USER 1 - OpenAI Tests")
    print("="*70)
    
    # Initialize LLMObserve for User 1
    observe(
        collector_url=COLLECTOR_URL,
        api_key=api_key
    )
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Test 1: Simple call
    print("\n📝 Test 1: Simple GPT-4o-mini call")
    with section("agent:user1_chatbot"):
        set_customer_id("customer_a")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello in 3 words"}],
            max_tokens=10
        )
        print(f"   ✅ Response: {response.choices[0].message.content}")
        print(f"   💰 Tokens: {response.usage.total_tokens}")
    
    # Test 2: Different customer
    print("\n📝 Test 2: Different customer")
    with section("agent:user1_processor"):
        set_customer_id("customer_b")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Count to 3"}],
            max_tokens=10
        )
        print(f"   ✅ Response: {response.choices[0].message.content}")
        print(f"   💰 Tokens: {response.usage.total_tokens}")
    
    # Test 3: Multiple calls
    print("\n📝 Test 3: Multiple calls (batch)")
    with section("agent:user1_batch"):
        set_customer_id("customer_c")
        for i in range(3):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Task {i+1}"}],
                max_tokens=5
            )
            print(f"   ✅ Call {i+1}: {response.usage.total_tokens} tokens")
    
    print("\n✅ User 1 tests completed!")


def test_user2_openai(api_key: str):
    """Test User 2 with OpenAI."""
    print("\n" + "="*70)
    print("👤 USER 2 - OpenAI Tests")
    print("="*70)
    
    # Initialize LLMObserve for User 2
    observe(
        collector_url=COLLECTOR_URL,
        api_key=api_key
    )
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Test 1: Different agent
    print("\n📝 Test 1: User 2 agent")
    with section("agent:user2_researcher"):
        set_customer_id("customer_x")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "What is AI?"}],
            max_tokens=20
        )
        print(f"   ✅ Response: {response.choices[0].message.content[:50]}...")
        print(f"   💰 Tokens: {response.usage.total_tokens}")
    
    # Test 2: Different model
    print("\n📝 Test 2: Different model")
    with section("agent:user2_analyzer"):
        set_customer_id("customer_y")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Explain Python"}],
            max_tokens=15
        )
        print(f"   ✅ Response: {response.choices[0].message.content[:50]}...")
        print(f"   💰 Tokens: {response.usage.total_tokens}")
    
    print("\n✅ User 2 tests completed!")


def test_user1_anthropic(api_key: str):
    """Test User 1 with Anthropic."""
    if not ANTHROPIC_AVAILABLE:
        print("\n⚠️  Skipping Anthropic tests (SDK not installed)")
        return
    
    if not ANTHROPIC_API_KEY:
        print("\n⚠️  Skipping Anthropic tests (API key not set)")
        return
    
    print("\n" + "="*70)
    print("👤 USER 1 - Anthropic (Claude) Tests")
    print("="*70)
    
    # Initialize LLMObserve for User 1
    observe(
        collector_url=COLLECTOR_URL,
        api_key=api_key
    )
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Test 1: Claude Haiku
    print("\n📝 Test 1: Claude Haiku")
    with section("agent:user1_claude"):
        set_customer_id("customer_claude")
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=20,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print(f"   ✅ Response: {response.content[0].text[:50]}")
        print(f"   💰 Input tokens: {response.usage.input_tokens}")
        print(f"   💰 Output tokens: {response.usage.output_tokens}")
    
    print("\n✅ User 1 Anthropic tests completed!")


def main():
    """Run all tests."""
    print("="*70)
    print("🧪 MULTI-USER API KEY TESTING")
    print("="*70)
    print(f"\n📋 Configuration:")
    print(f"   Collector URL: {COLLECTOR_URL}")
    print(f"   User 1 API Key: {LLMOBSERVE_API_KEY_USER1[:30]}...")
    if LLMOBSERVE_API_KEY_USER2:
        print(f"   User 2 API Key: {LLMOBSERVE_API_KEY_USER2[:30]}...")
    else:
        print(f"   User 2 API Key: Not set (optional)")
    print(f"   OpenAI API Key: {'✅ Set' if OPENAI_API_KEY else '❌ Not set'}")
    print(f"   Anthropic API Key: {'✅ Set' if ANTHROPIC_API_KEY else '❌ Not set'}")
    
    # Test User 1
    test_user1_openai(LLMOBSERVE_API_KEY_USER1)
    
    # Test User 2 (if provided)
    if LLMOBSERVE_API_KEY_USER2:
        time.sleep(1)  # Small delay between users
        test_user2_openai(LLMOBSERVE_API_KEY_USER2)
    
    # Test Anthropic (if available)
    if ANTHROPIC_AVAILABLE and ANTHROPIC_API_KEY:
        time.sleep(1)
        test_user1_anthropic(LLMOBSERVE_API_KEY_USER1)
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED!")
    print("="*70)
    print(f"""
📊 Next Steps:

1. Check Dashboard: http://localhost:3000/dashboard
   - You should see costs for User 1
   - If User 2 tested, verify data isolation

2. Check Customers Page: http://localhost:3000/customers
   - Should see: customer_a, customer_b, customer_c
   - If User 2 tested: customer_x, customer_y

3. Check Features Page: http://localhost:3000/features
   - Should see agents: user1_chatbot, user1_processor, user1_batch
   - If User 2 tested: user2_researcher, user2_analyzer

4. Verify Data Isolation:
   - Login as User 1 → Should only see User 1's data
   - Login as User 2 → Should only see User 2's data
   - No cross-contamination ✅

5. Test Multiple Provider API Keys:
   - OpenAI: Should work (tested above)
   - Anthropic: Should work if API key provided
   - Both should appear in dashboard under different providers
""")

if __name__ == "__main__":
    main()





