"""
Test script using REAL OpenAI API calls with actual cost tracking.
Uses the user's API key and OpenAI key from .env
"""
import os
import sys
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from llmobserve import observe, section
from openai import OpenAI

# User's API key
LLMOBSERVE_API_KEY = "llmo_sk_9858c9a35578b19d96be7a373def01d5b7fedab72c3712a5"

# Load OpenAI key from .env
def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ ERROR: OPENAI_API_KEY not found in .env file")
    sys.exit(1)

print("=" * 70)
print("🧪 TESTING REAL OpenAI API CALLS WITH COST TRACKING")
print("=" * 70)
print(f"\n📡 Collector URL: http://localhost:8000")
print(f"🔑 LLMObserve API Key: {LLMOBSERVE_API_KEY[:20]}...")
print(f"🤖 OpenAI API Key: {OPENAI_API_KEY[:20]}...")
print("\nInitializing observability...\n")

# Initialize observability with user's API key
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000",  # Explicitly set proxy URL
    api_key=LLMOBSERVE_API_KEY,
    tenant_id="real_user_test"  # Use a unique tenant ID for real data
)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

print("✅ Observability initialized")
print("✅ OpenAI client initialized")
print("\nMaking real API calls...\n")

try:
    # Test 1: Simple chat completion with gpt-4o-mini (cheap)
    print("📝 Test 1: Simple chat completion (gpt-4o-mini)")
    with section("simple-chat"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            temperature=0.7
        )
        print(f"   ✓ Response: {response.choices[0].message.content[:50]}...")
        print(f"   ✓ Tokens: {response.usage.total_tokens} (input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})")
    
    # Test 2: More complex completion with gpt-4o
    print("\n📝 Test 2: Complex completion (gpt-4o)")
    with section("complex-reasoning"):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert Python developer."},
                {"role": "user", "content": "Explain the difference between async and sync functions in Python. Keep it brief."}
            ],
            temperature=0.5
        )
        print(f"   ✓ Response: {response.choices[0].message.content[:80]}...")
        print(f"   ✓ Tokens: {response.usage.total_tokens} (input: {response.usage.prompt_tokens}, output: {response.usage.completion_tokens})")
    
    # Test 3: Embeddings
    print("\n📝 Test 3: Text embeddings")
    with section("embeddings"):
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="This is a test sentence for embedding generation."
        )
        print(f"   ✓ Embedding dimensions: {len(response.data[0].embedding)}")
        print(f"   ✓ Tokens: {response.usage.total_tokens}")
    
    # Test 4: Another chat with different model
    print("\n📝 Test 4: Another chat completion (gpt-4o-mini)")
    with section("follow-up-chat"):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "What is 2+2? Just give the number."}
            ]
        )
        print(f"   ✓ Response: {response.choices[0].message.content}")
        print(f"   ✓ Tokens: {response.usage.total_tokens}")
    
    print("\n" + "=" * 70)
    print("✅ ALL REAL API CALLS COMPLETED")
    print("=" * 70)
    print("\n⏳ Waiting for events to flush to collector...")
    
    # Wait for events to flush
    import time
    time.sleep(2)
    
    print("\n📊 Check your dashboard at: http://localhost:3000")
    print("   • Look for tenant: 'real_user_test'")
    print("   • View costs by provider, model, and section")
    print("   • All costs are REAL based on actual API usage\n")
    
except Exception as e:
    print(f"\n❌ Error during API calls: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

