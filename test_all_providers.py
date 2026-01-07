#!/usr/bin/env python3
"""
Test script to verify tracking works for multiple providers.

Supports:
- OpenAI (direct)
- Anthropic (direct)
- Google (direct)
- OpenRouter (100+ models via one API)
- Any other provider via HTTP interceptor

Usage:
    export OPENAI_API_KEY=sk-...
    export ANTHROPIC_API_KEY=sk-...
    export GOOGLE_API_KEY=...
    export OPENROUTER_API_KEY=sk-or-...
    export LLMOBSERVE_API_KEY=...
    export LLMOBSERVE_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
    # OR: export NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
    
    python3 test_all_providers.py
"""
import os
import sys
import time

# Initialize LLMObserve SDK FIRST (before importing any provider SDKs)
import llmobserve

# Get collector URL from either env var (SDK checks both)
collector_url = os.getenv("LLMOBSERVE_COLLECTOR_URL") or os.getenv("NEXT_PUBLIC_COLLECTOR_URL") or "http://localhost:8000"

if collector_url == "http://localhost:8000":
    print("⚠️  WARNING: Using default localhost collector URL.")
    print("   Set LLMOBSERVE_COLLECTOR_URL env var to point to your production collector!")
    print()

llmobserve.observe(
    collector_url=collector_url,
    api_key=os.getenv("LLMOBSERVE_API_KEY")
)

print("=" * 60)
print("LLM Cost Tracking - Multi-Provider Test")
print("=" * 60)
print()

results = []

# Test 1: OpenAI
if os.getenv("OPENAI_API_KEY"):
    print("📋 Test 1: OpenAI (gpt-4o-mini)")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello' in one word."}],
            max_tokens=10
        )
        
        print(f"   ✅ Success: {response.choices[0].message.content}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage.total_tokens}")
        results.append(("OpenAI", "gpt-4o-mini", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(("OpenAI", "gpt-4o-mini", False))
else:
    print("📋 Test 1: OpenAI - SKIPPED (no OPENAI_API_KEY)")
    results.append(("OpenAI", "gpt-4o-mini", None))

print()

# Test 2: Anthropic
if os.getenv("ANTHROPIC_API_KEY"):
    print("📋 Test 2: Anthropic (claude-3-haiku)")
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'Hello' in one word."}]
        )
        
        print(f"   ✅ Success: {response.content[0].text}")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage.input_tokens + response.usage.output_tokens}")
        results.append(("Anthropic", "claude-3-haiku", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(("Anthropic", "claude-3-haiku", False))
else:
    print("📋 Test 2: Anthropic - SKIPPED (no ANTHROPIC_API_KEY)")
    results.append(("Anthropic", "claude-3-haiku", None))

print()

# Test 3: Google Gemini
if os.getenv("GOOGLE_API_KEY"):
    print("📋 Test 3: Google Gemini (gemini-1.5-flash)")
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'Hello' in one word.")
        
        print(f"   ✅ Success: {response.text}")
        print(f"   Model: gemini-1.5-flash")
        if hasattr(response, "usage_metadata"):
            print(f"   Tokens: {response.usage_metadata.total_token_count}")
        results.append(("Google", "gemini-1.5-flash", True))
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        results.append(("Google", "gemini-1.5-flash", False))
else:
    print("📋 Test 3: Google - SKIPPED (no GOOGLE_API_KEY)")
    results.append(("Google", "gemini-1.5-flash", None))

print()

# Test 4: OpenRouter (Multiple models via one API)
if os.getenv("OPENROUTER_API_KEY"):
    print("📋 Test 4: OpenRouter (Multiple models)")
    
    openrouter_models = [
        ("openai/gpt-4o-mini", "OpenAI via OpenRouter"),
        ("anthropic/claude-3-haiku", "Anthropic via OpenRouter"),
        ("google/gemini-1.5-flash", "Google via OpenRouter"),
        ("mistralai/mistral-small", "Mistral via OpenRouter"),
    ]
    
    for model_id, description in openrouter_models:
        try:
            import httpx
            
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "HTTP-Referer": "https://github.com/llmobserve/test",
                    "X-Title": "LLMObserve Test"
                },
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
                    "max_tokens": 10
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"   ✅ {description}: {data['choices'][0]['message']['content']}")
            print(f"      Model: {data['model']}")
            if 'usage' in data:
                print(f"      Tokens: {data['usage']['total_tokens']}")
            results.append(("OpenRouter", model_id, True))
        except Exception as e:
            print(f"   ❌ {description}: {e}")
            results.append(("OpenRouter", model_id, False))
else:
    print("📋 Test 4: OpenRouter - SKIPPED (no OPENROUTER_API_KEY)")
    print("   💡 OpenRouter is great for testing multiple models with one API key!")
    print("   Get your key: https://openrouter.ai/keys")
    results.append(("OpenRouter", "multiple", None))

print()
print("=" * 60)
print("Summary")
print("=" * 60)

success_count = sum(1 for _, _, status in results if status is True)
total_count = sum(1 for _, _, status in results if status is not None)

for provider, model, status in results:
    if status is True:
        print(f"✅ {provider} ({model})")
    elif status is False:
        print(f"❌ {provider} ({model})")
    else:
        print(f"⏭️  {provider} ({model}) - SKIPPED")

print()
print(f"Results: {success_count}/{total_count} tests passed")
print()
print("💡 Check your dashboard to see if all calls were tracked!")
print(f"   Collector URL: {collector_url}")
print()
print("⏳ Waiting 5 seconds for events to flush...")
time.sleep(5)
print("✅ Done! Check your dashboard now.")
