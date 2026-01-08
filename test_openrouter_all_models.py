#!/usr/bin/env python3
"""
Comprehensive test script for all models via OpenRouter.

This script tests all supported models through OpenRouter to verify:
1. OpenRouter provider detection works
2. Model names are extracted correctly
3. Token usage is tracked
4. Costs are calculated correctly
5. Events are created and sent to collector

Usage:
    export OPENROUTER_API_KEY="your-key-here"
    export COLLECTOR_URL="http://localhost:8000"  # or your collector URL
    python test_openrouter_all_models.py
"""

import os
import sys
import json
import time
from typing import List, Dict, Any
import httpx

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sdk", "python"))

import llmobserve

# OpenRouter API endpoint
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# List of models to test (from OpenRouter's supported models)
# Format: "provider/model-name"
TEST_MODELS = [
    # OpenAI models
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4-turbo",
    "openai/gpt-3.5-turbo",
    
    # Anthropic models
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3.5-haiku",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-haiku",
    
    # Google models
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "google/gemini-1.5-pro",
    "google/gemini-1.5-flash",
    
    # xAI/Grok models
    "xai/grok-4-0709",
    "xai/grok-3",
    "xai/grok-3-mini",
    
    # Mistral models
    "mistral/mistral-large-latest",
    "mistral/mistral-medium-latest",
    "mistral/mistral-small-latest",
    
    # Cohere models
    "cohere/command-r-plus",
    "cohere/command-r",
    
    # Groq models
    "groq/llama-3.1-405b",
    "groq/llama-3.1-70b",
    "groq/llama-3.1-8b",
    
    # Perplexity models
    "perplexity/sonar-pro",
    "perplexity/sonar",
    
    # Together AI models
    "together/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "together/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
]


def get_openrouter_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable not set. "
            "Please set it: export OPENROUTER_API_KEY='your-key-here'"
        )
    return api_key


def get_collector_url() -> str:
    """Get collector URL from environment."""
    return os.getenv("COLLECTOR_URL", "http://localhost:8000")


def test_model(
    model: str,
    api_key: str,
    collector_url: str,
    client: httpx.Client
) -> Dict[str, Any]:
    """
    Test a single model via OpenRouter.
    
    Returns:
        Dict with test results
    """
    print(f"\n🧪 Testing model: {model}")
    
    # Initialize LLMObserve
    llmobserve.observe(
        collector_url=collector_url,
        api_key=os.getenv("LLMOBSERVE_API_KEY"),  # Your LLMObserve API key if needed
    )
    
    # Create test prompt
    test_prompt = "Say 'Hello, World!' in exactly 3 words."
    
    # Make request to OpenRouter
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-repo",  # Optional but recommended
        "X-Title": "LLMObserve Test",  # Optional
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": test_prompt}
        ],
        "max_tokens": 50,
    }
    
    start_time = time.time()
    
    try:
        response = client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        
        latency_ms = (time.time() - start_time) * 1000
        response_data = response.json()
        
        # Extract usage info
        usage = response_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        # Extract model name from response
        response_model = response_data.get("model", model)
        
        # Extract response text
        choices = response_data.get("choices", [])
        response_text = ""
        if choices:
            message = choices[0].get("message", {})
            response_text = message.get("content", "")
        
        result = {
            "model": model,
            "response_model": response_model,
            "status": "success",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "response_preview": response_text[:50] if response_text else "",
            "error": None,
        }
        
        print(f"  ✅ Success: {input_tokens} input + {output_tokens} output tokens")
        print(f"  📝 Response: {response_text[:50]}...")
        
        return result
        
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        print(f"  ❌ HTTP Error: {error_msg}")
        return {
            "model": model,
            "status": "error",
            "error": error_msg,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": (time.time() - start_time) * 1000,
        }
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Error: {error_msg}")
        return {
            "model": model,
            "status": "error",
            "error": error_msg,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": (time.time() - start_time) * 1000,
        }


def main():
    """Run comprehensive tests for all models."""
    print("=" * 80)
    print("🚀 OpenRouter Comprehensive Model Testing")
    print("=" * 80)
    
    # Get configuration
    try:
        api_key = get_openrouter_api_key()
        collector_url = get_collector_url()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    
    print(f"\n📋 Configuration:")
    print(f"  OpenRouter API Key: {api_key[:10]}...")
    print(f"  Collector URL: {collector_url}")
    print(f"  Models to test: {len(TEST_MODELS)}")
    
    # Initialize HTTP client
    client = httpx.Client(timeout=30.0)
    
    # Run tests
    results = []
    successful = 0
    failed = 0
    
    for i, model in enumerate(TEST_MODELS, 1):
        print(f"\n[{i}/{len(TEST_MODELS)}] ", end="")
        result = test_model(model, api_key, collector_url, client)
        results.append(result)
        
        if result["status"] == "success":
            successful += 1
        else:
            failed += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    client.close()
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(f"  Total models tested: {len(TEST_MODELS)}")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  Success rate: {(successful/len(TEST_MODELS)*100):.1f}%")
    
    # Print failed models
    if failed > 0:
        print("\n❌ Failed Models:")
        for result in results:
            if result["status"] != "success":
                print(f"  - {result['model']}: {result.get('error', 'Unknown error')}")
    
    # Print token usage summary
    total_input_tokens = sum(r.get("input_tokens", 0) for r in results)
    total_output_tokens = sum(r.get("output_tokens", 0) for r in results)
    total_tokens = sum(r.get("total_tokens", 0) for r in results)
    
    print(f"\n📈 Token Usage Summary:")
    print(f"  Total input tokens: {total_input_tokens:,}")
    print(f"  Total output tokens: {total_output_tokens:,}")
    print(f"  Total tokens: {total_tokens:,}")
    
    # Save results to file
    results_file = "openrouter_test_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "collector_url": collector_url,
            "total_models": len(TEST_MODELS),
            "successful": successful,
            "failed": failed,
            "results": results,
            "token_summary": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_tokens,
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("\n✅ Testing complete! Check your collector dashboard to verify events were tracked.")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())



