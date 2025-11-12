"""
Direct test of proxy functionality (bypassing SDK).
"""
import httpx
import json

PROXY_URL = "http://localhost:9000"
OPENAI_KEY = "sk-test"  # Won't actually work but will test proxy

# Test 1: Direct call to proxy
print("Test 1: Direct call to proxy /health")
response = httpx.get(f"{PROXY_URL}/health")
print(f"  Response: {response.json()}")
print()

# Test 2: Proxy an OpenAI call (will fail auth but tests proxy logic)
print("Test 2: Proxy an OpenAI call through proxy")
try:
    response = httpx.post(
        f"{PROXY_URL}/proxy",
        headers={
            "X-LLMObserve-Run-ID": "test-run",
            "X-LLMObserve-Span-ID": "test-span",
            "X-LLMObserve-Parent-Span-ID": "",
            "X-LLMObserve-Section": "test-section",
            "X-LLMObserve-Section-Path": "test/section",
            "X-LLMObserve-Customer-ID": "test-customer",
            "X-LLMObserve-Target-URL": "https://api.openai.com/v1/chat/completions",
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Hello"}]
        }
    )
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")

