"""
Example: How to use llmobserve in your own Python code

This shows you how to:
1. Import and initialize llmobserve
2. Make real OpenAI API calls
3. Track costs automatically
"""

import os
import sys
from pathlib import Path

# Add SDK to path (or install it: pip install -e sdk/python)
sdk_path = Path(__file__).parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from llmobserve import observe, section, set_run_id, set_customer_id
from openai import OpenAI
import uuid

# ============================================================================
# STEP 1: Get your API keys
# ============================================================================
# Load from .env file if it exists
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

load_env()

# Get your LLMObserve API key from: http://localhost:3000/settings
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY", "llmo_sk_9858c9a35578b19d96be7a373def01d5b7fedab72c3712a5")
print(f"🔑 Using LLMObserve API Key: {LLMOBSERVE_API_KEY[:30]}...")

# Your OpenAI API key (or any other API key)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found")
    print("   Add it to .env file: OPENAI_API_KEY='your-key-here'")
    print("   Or set it: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

# ============================================================================
# STEP 2: Initialize llmobserve
# ============================================================================
print("🔧 Initializing llmobserve...")

observe(
    collector_url="http://localhost:8000",  # Collector API URL
    proxy_url="http://localhost:9000",      # Proxy URL (must be running!)
    api_key=LLMOBSERVE_API_KEY,             # Your LLMObserve API key
    tenant_id="my_app"                      # Your tenant ID (can be anything)
)

print("✅ llmobserve initialized!")

# ============================================================================
# STEP 3: Configure OpenAI client to use the proxy
# ============================================================================
# IMPORTANT: Set base_url to route through the proxy
# The proxy intercepts httpx requests automatically, so we use the normal OpenAI URL
# but the SDK will route it through the proxy
client = OpenAI(
    api_key=OPENAI_API_KEY
    # Don't set base_url - the SDK intercepts httpx and routes through proxy automatically
)

# ============================================================================
# STEP 4: Make API calls - they'll be tracked automatically!
# ============================================================================

# Set a run ID for this session
run_id = str(uuid.uuid4())
set_run_id(run_id)

# Optional: Set customer ID for multi-tenant tracking
set_customer_id("customer_123")

print(f"\n📊 Run ID: {run_id}")
print("Making API calls...\n")

# Example 1: Simple chat completion
with section("user_query"):
    print("📝 Making chat completion...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer in one word."}
        ],
        temperature=0.7
    )
    print(f"   ✅ Response: {response.choices[0].message.content}")
    print(f"   💰 Tokens: {response.usage.total_tokens} (input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})")

# Example 2: Another call in a different section
with section("data_processing"):
    print("\n📝 Making another chat completion...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Explain Python in one sentence."}
        ]
    )
    print(f"   ✅ Response: {response.choices[0].message.content[:50]}...")
    print(f"   💰 Tokens: {response.usage.total_tokens}")

# Example 3: Embeddings
with section("embeddings"):
    print("\n📝 Making embeddings call...")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input="Hello, world!"
    )
    print(f"   ✅ Embedding dimensions: {len(response.data[0].embedding)}")
    print(f"   💰 Tokens: {response.usage.total_tokens}")

print("\n" + "="*70)
print("✅ ALL API CALLS COMPLETED!")
print("="*70)
print("\n📊 View your costs at: http://localhost:3000")
print(f"   • Look for tenant: 'my_app'")
print(f"   • Run ID: {run_id}")
print("   • All costs are tracked automatically!")
print("\n")

