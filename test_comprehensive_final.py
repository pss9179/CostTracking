#!/usr/bin/env python3
"""
Comprehensive OpenRouter test - All supported models with cost verification.
"""
import os
import sys
import time
import json
import uuid
from datetime import datetime
import httpx

# Configuration
OPENROUTER_API_KEY = "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"
LLMOBSERVE_API_KEY = "llmo_sk_e4b4d9b464e40b7f66f0fb52dbfc1beafcb6a3ac5f0659c0"
COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app"

# All models to test organized by provider
ALL_MODELS = [
    # OpenAI
    ("openai/gpt-4o-mini", "OpenAI GPT-4o Mini"),
    ("openai/gpt-4o", "OpenAI GPT-4o"),
    ("openai/gpt-4-turbo", "OpenAI GPT-4 Turbo"),
    ("openai/gpt-3.5-turbo", "OpenAI GPT-3.5 Turbo"),
    
    # Anthropic
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
    ("anthropic/claude-3-haiku", "Claude 3 Haiku"),
    ("anthropic/claude-3-opus", "Claude 3 Opus"),
    
    # Google
    ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash (Free)"),
    ("google/gemini-flash-1.5-8b", "Gemini Flash 1.5 8B"),
    
    # Meta Llama
    ("meta-llama/llama-3.1-8b-instruct", "Llama 3.1 8B"),
    ("meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B"),
    ("meta-llama/llama-3.2-3b-instruct", "Llama 3.2 3B"),
    
    # Mistral
    ("mistralai/mistral-7b-instruct", "Mistral 7B"),
    ("mistralai/mixtral-8x7b-instruct", "Mixtral 8x7B"),
    ("mistralai/mistral-large", "Mistral Large"),
    
    # DeepSeek
    ("deepseek/deepseek-chat", "DeepSeek Chat"),
    ("deepseek/deepseek-r1", "DeepSeek R1"),
    
    # Qwen
    ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B"),
    ("qwen/qwen-2.5-7b-instruct", "Qwen 2.5 7B"),
    
    # Other providers
    ("microsoft/phi-3-medium-128k-instruct", "Microsoft Phi-3 Medium"),
    ("nousresearch/hermes-3-llama-3.1-405b", "Nous Hermes 3 405B"),
]

def call_openrouter(model: str, prompt: str = "Count from 1 to 3."):
    """Make a direct call to OpenRouter."""
    start_time = time.time()
    
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://llmobserve.com",
                "X-Title": "LLMObserve Comprehensive Test"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 30,
            },
            timeout=60.0
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return None, f"HTTP {response.status_code}: {response.text[:100]}", latency_ms
        
        data = response.json()
        
        if "error" in data:
            return None, f"API Error: {data['error']}", latency_ms
        
        usage = data.get("usage", {})
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return {
            "model": data.get("model", model),
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "content": content,
        }, None, latency_ms
        
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return None, str(e), latency_ms

def send_event(provider: str, model: str, input_tokens: int, output_tokens: int, 
               latency_ms: float, customer_id: str = "comprehensive_test"):
    """Send event to LLMObserve collector."""
    event_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    
    event = {
        "id": event_id,
        "run_id": run_id,
        "span_id": span_id,
        "parent_span_id": None,
        "section": f"comprehensive_test:{provider}",
        "section_path": f"comprehensive_test/{provider}/{model.replace('/', '_')}",
        "span_type": "llm_call",
        "provider": provider,
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": model,
        "tenant_id": None,
        "customer_id": customer_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": 0,
        "cost_usd": 0.0,
        "latency_ms": latency_ms,
        "status": "ok",
        "is_streaming": False,
        "stream_cancelled": False,
        "event_metadata": {
            "test_suite": "comprehensive_openrouter",
            "openrouter_model": model,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "semantic_label": None,
        "voice_call_id": None,
        "audio_duration_seconds": None,
        "voice_segment_type": None,
        "voice_platform": None
    }
    
    try:
        response = httpx.post(
            f"{COLLECTOR_URL}/events/",
            headers={
                "Authorization": f"Bearer {LLMOBSERVE_API_KEY}",
                "Content-Type": "application/json"
            },
            json=[event],
            timeout=30.0
        )
        return response.status_code, response.text
    except Exception as e:
        return 500, f"Timeout/Error: {str(e)[:50]}"

def get_dashboard_stats():
    """Get current dashboard stats."""
    try:
        response = httpx.get(
            f"{COLLECTOR_URL}/dashboard/stats",
            headers={"Authorization": f"Bearer {LLMOBSERVE_API_KEY}"},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"  Warning: Failed to get stats: {e}")
    return None

def main():
    print("=" * 70)
    print("LLMOBSERVE COMPREHENSIVE MODEL TEST")
    print("=" * 70)
    print(f"Testing {len(ALL_MODELS)} models via OpenRouter")
    print(f"Collector: {COLLECTOR_URL}")
    print("=" * 70)
    
    # Get initial stats
    initial_stats = get_dashboard_stats()
    initial_count = initial_stats.get("call_count", 0) if initial_stats else 0
    initial_cost = initial_stats.get("total_cost", 0) if initial_stats else 0
    print(f"\nInitial stats: {initial_count} calls, ${initial_cost:.6f} total cost")
    
    results = []
    successful = 0
    failed = 0
    
    for model_id, model_name in ALL_MODELS:
        print(f"\n{'─' * 60}")
        print(f"Testing: {model_name}")
        print(f"Model ID: {model_id}")
        
        # Make the API call
        result, error, latency_ms = call_openrouter(model_id)
        
        if error:
            print(f"  ❌ API Error: {error[:80]}")
            failed += 1
            results.append({
                "model": model_id,
                "name": model_name,
                "status": "api_failed",
                "error": error
            })
            continue
        
        print(f"  ✅ API Success: {result['content'][:40]}...")
        print(f"     Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
        print(f"     Latency: {latency_ms:.0f}ms")
        
        # Extract provider and clean model name
        provider = model_id.split("/")[0] if "/" in model_id else "openrouter"
        actual_model = result.get("model", model_id)
        # Strip provider prefix from model name for pricing lookup
        # e.g., "openai/gpt-4o-mini" -> "gpt-4o-mini"
        if "/" in actual_model:
            clean_model = actual_model.split("/", 1)[1]
        else:
            clean_model = actual_model
        
        # Send event with clean model name for correct pricing lookup
        status, response_text = send_event(
            provider=provider,
            model=clean_model,
            input_tokens=result['input_tokens'],
            output_tokens=result['output_tokens'],
            latency_ms=latency_ms,
            customer_id="comprehensive_openrouter_test_v2"
        )
        
        event_success = status in [200, 201]
        if event_success:
            print(f"  ✅ Event tracked")
            successful += 1
        else:
            print(f"  ⚠️  Event tracking issue: {response_text[:50]}")
            failed += 1
        
        results.append({
            "model": model_id,
            "name": model_name,
            "actual_model": actual_model,
            "status": "success" if event_success else "event_failed",
            "input_tokens": result['input_tokens'],
            "output_tokens": result['output_tokens'],
            "latency_ms": latency_ms
        })
        
        time.sleep(0.3)
    
    # Get final stats
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    final_stats = get_dashboard_stats()
    final_count = final_stats.get("call_count", 0) if final_stats else 0
    final_cost = final_stats.get("total_cost", 0) if final_stats else 0
    
    new_calls = final_count - initial_count
    new_cost = final_cost - initial_cost
    
    print(f"\nModels tested: {len(ALL_MODELS)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"\nNew events tracked: {new_calls}")
    print(f"New cost tracked: ${new_cost:.6f}")
    print(f"\nTotal in dashboard:")
    print(f"  Calls: {final_count}")
    print(f"  Cost: ${final_cost:.6f}")
    print(f"  Avg latency: {final_stats.get('avg_latency_ms', 0):.0f}ms")
    
    # Calculate total tokens
    total_input = sum(r.get("input_tokens", 0) for r in results if r["status"] == "success")
    total_output = sum(r.get("output_tokens", 0) for r in results if r["status"] == "success")
    print(f"\nTokens used this test:")
    print(f"  Input: {total_input}")
    print(f"  Output: {total_output}")
    
    # Print failed models
    failed_models = [r for r in results if r["status"] != "success"]
    if failed_models:
        print(f"\nFailed models ({len(failed_models)}):")
        for r in failed_models:
            print(f"  - {r['name']}: {r.get('error', r['status'])[:50]}")
    
    print("\n" + "=" * 70)
    print("CHECK DASHBOARD: https://llmobserve.com/dashboard")
    print("=" * 70)
    
    return results

if __name__ == "__main__":
    results = main()
    
    with open("/Users/ethanzheng/Documents/GitHub/CostTracking/test_comprehensive_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to test_comprehensive_results.json")

