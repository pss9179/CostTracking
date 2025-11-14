"""
Example: Track ANY API with Custom Pricing

This shows how to track costs for ANY HTTP API!
Just add pricing to collector/pricing/registry.json
"""
import httpx
import os
from llmobserve import observe, section

# Initialize tracking - proxy intercepts ALL HTTP calls
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"
)

print("🚀 Tracking ANY API calls...\n")

# Example 1: Track OpenAI (already supported)
with section("llm:chat"):
    client = httpx.Client()
    response = client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'sk-test')}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello!"}]
        }
    )
    print(f"✅ OpenAI call tracked! Status: {response.status_code}")

# Example 2: Track ANY custom API
# Just add pricing to registry.json:
# {
#   "myapi:endpoint": {
#     "per_call": 0.001
#   }
# }
with section("custom:api_call"):
    response = httpx.get("https://httpbin.org/json")
    print(f"✅ Custom API tracked! Status: {response.status_code}")

print("\n✅ Check dashboard at http://localhost:3000 to see costs!")

