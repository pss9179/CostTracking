#!/usr/bin/env python3
"""
Simple OpenRouter test with explicit event sending for debugging.
"""
import os
import sys
import time
import json
import httpx

# Configuration
OPENROUTER_API_KEY = "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"
LLMOBSERVE_API_KEY = "llmo_sk_e4b4d9b464e40b7f66f0fb52dbfc1beafcb6a3ac5f0659c0"
COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app"

# Models to test (updated with correct OpenRouter model IDs)
MODELS_TO_TEST = [
    # OpenAI
    "openai/gpt-4o-mini",
    "openai/gpt-4o",
    # Anthropic
    "anthropic/claude-3.5-sonnet",
    # Meta
    "meta-llama/llama-3.1-8b-instruct",
    # Mistral
    "mistralai/mistral-7b-instruct",
    # DeepSeek
    "deepseek/deepseek-chat",
]

def call_openrouter(model: str, prompt: str = "Say 'test' in one word."):
    """Make a direct call to OpenRouter."""
    start_time = time.time()
    
    response = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://llmobserve.com",
            "X-Title": "LLMObserve Test"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 20,
        },
        timeout=30.0
    )
    
    latency_ms = (time.time() - start_time) * 1000
    
    if response.status_code != 200:
        return None, f"Error {response.status_code}: {response.text[:100]}", latency_ms
    
    data = response.json()
    usage = data.get("usage", {})
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    return {
        "model": data.get("model", model),
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "content": content,
    }, None, latency_ms

def send_event(provider: str, model: str, input_tokens: int, output_tokens: int, latency_ms: float, customer_id: str = "openrouter_test"):
    """Send event to LLMObserve collector."""
    import uuid
    from datetime import datetime
    
    event_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    
    event = {
        "id": event_id,
        "run_id": run_id,
        "span_id": span_id,
        "parent_span_id": None,
        "section": f"openrouter_test:{provider}",
        "section_path": f"openrouter_test/{provider}/{model.replace('/', '_')}",
        "span_type": "llm_call",
        "provider": provider,
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": model,
        "tenant_id": None,  # Will be set from API key
        "customer_id": customer_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": 0,
        "cost_usd": 0.0,  # Will be calculated server-side
        "latency_ms": latency_ms,
        "status": "ok",
        "is_streaming": False,
        "stream_cancelled": False,
        "event_metadata": {
            "test_run": True,
            "openrouter_model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "semantic_label": None,
        "voice_call_id": None,
        "audio_duration_seconds": None,
        "voice_segment_type": None,
        "voice_platform": None
    }
    
    response = httpx.post(
        f"{COLLECTOR_URL}/events/",
        headers={
            "Authorization": f"Bearer {LLMOBSERVE_API_KEY}",
            "Content-Type": "application/json"
        },
        json=[event],
        timeout=10.0
    )
    
    return response.status_code, response.text

def main():
    print("=" * 60)
    print("SIMPLE OPENROUTER TEST WITH EXPLICIT EVENT SENDING")
    print("=" * 60)
    
    results = []
    
    for model in MODELS_TO_TEST:
        print(f"\n--- Testing: {model} ---")
        
        # Make the API call
        result, error, latency_ms = call_openrouter(model)
        
        if error:
            print(f"  ❌ API Error: {error}")
            continue
        
        print(f"  ✅ API Success:")
        print(f"     Response: {result['content'][:50]}...")
        print(f"     Input tokens: {result['input_tokens']}")
        print(f"     Output tokens: {result['output_tokens']}")
        print(f"     Latency: {latency_ms:.0f}ms")
        
        # Extract provider from model name
        provider = model.split("/")[0] if "/" in model else "openrouter"
        actual_model = result.get("model", model)
        
        # Send event to collector
        status, response_text = send_event(
            provider=provider,
            model=actual_model,
            input_tokens=result['input_tokens'],
            output_tokens=result['output_tokens'],
            latency_ms=latency_ms,
            customer_id="openrouter_comprehensive_test"
        )
        
        if status in [200, 201]:
            print(f"  ✅ Event sent successfully: {response_text[:100]}")
        else:
            print(f"  ❌ Event send failed ({status}): {response_text[:100]}")
        
        results.append({
            "model": model,
            "actual_model": actual_model,
            "input_tokens": result['input_tokens'],
            "output_tokens": result['output_tokens'],
            "latency_ms": latency_ms,
            "event_status": status
        })
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total models tested: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r['event_status'] in [200, 201])}")
    
    total_input = sum(r['input_tokens'] for r in results)
    total_output = sum(r['output_tokens'] for r in results)
    print(f"Total input tokens: {total_input}")
    print(f"Total output tokens: {total_output}")
    
    # Verify by checking dashboard stats
    print("\n--- Verifying events in dashboard ---")
    response = httpx.get(
        f"{COLLECTOR_URL}/dashboard/stats",
        headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"},
        timeout=10.0
    )
    
    if response.status_code == 200:
        stats = response.json()
        print(f"Dashboard stats:")
        print(f"  Total cost: ${stats.get('total_cost', 0):.6f}")
        print(f"  Call count: {stats.get('call_count', 0)}")
        print(f"  Avg latency: {stats.get('avg_latency_ms', 0):.0f}ms")
    else:
        print(f"Failed to get dashboard stats: {response.status_code}")
    
    return results

if __name__ == "__main__":
    results = main()
    
    with open("/Users/ethanzheng/Documents/GitHub/CostTracking/test_simple_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to test_simple_results.json")

