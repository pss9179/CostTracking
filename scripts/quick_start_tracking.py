"""
Quick Start: Track ANY API

This script shows how to start tracking costs for ANY API.
"""
import httpx
import os
from llmobserve import observe, section

# Step 1: Initialize tracking
# The proxy intercepts ALL HTTP calls automatically
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"
)

print("🚀 Tracking initialized! All HTTP calls will be tracked.\n")

# Step 2: Make API calls - they're automatically tracked!
with section("test:api_calls"):
    # Example: Track OpenAI (already supported)
    print("📞 Making OpenAI call...")
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'sk-test')}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello!"}],
                "max_tokens": 10
            },
            timeout=10.0
        )
        print(f"   ✅ OpenAI tracked! Status: {response.status_code}\n")
    except Exception as e:
        print(f"   ⚠️ OpenAI call failed (expected if no key): {e}\n")
    
    # Example: Track ANY custom API
    # Just add pricing to registry.json first!
    print("📞 Making custom API call...")
    response = httpx.get("https://httpbin.org/json", timeout=5.0)
    print(f"   ✅ Custom API tracked! Status: {response.status_code}")
    print("   💡 Add pricing to registry.json to see costs!")

print("\n✅ Check dashboard at http://localhost:3000 to see tracked calls!")
print("\n💡 To add pricing for custom APIs:")
print("   1. Edit collector/pricing/registry.json")
print("   2. Add: \"myapi:endpoint\": {\"per_call\": 0.001}")
print("   3. Make HTTP calls - costs calculated automatically!")

