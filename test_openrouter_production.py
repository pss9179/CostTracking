#!/usr/bin/env python3
"""
Comprehensive OpenRouter Test Suite for LLMObserve
Tests all supported models via OpenRouter and verifies tracking on production.
"""

import os
import sys
import time
import json

# Set environment variables BEFORE importing llmobserve
os.environ["OPENROUTER_API_KEY"] = "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"
os.environ["LLMOBSERVE_API_KEY"] = "llmo_sk_e4b4d9b464e40b7f66f0fb52dbfc1beafcb6a3ac5f0659c0"
os.environ["LLMOBSERVE_COLLECTOR_URL"] = "https://llmobserve-api-production-d791.up.railway.app"

# Add SDK to path
sys.path.insert(0, "/Users/ethanzheng/Documents/GitHub/CostTracking/sdk/python")

import llmobserve
from openai import OpenAI

# Initialize LLMObserve with production collector
print("=" * 60)
print("INITIALIZING LLMOBSERVE")
print("=" * 60)
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_e4b4d9b464e40b7f66f0fb52dbfc1beafcb6a3ac5f0659c0"
)
print("✅ LLMObserve initialized with production collector")

# Initialize OpenRouter client (OpenAI-compatible)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={
        "HTTP-Referer": "https://llmobserve.com",
        "X-Title": "LLMObserve Test Suite"
    }
)

# Models to test - organized by provider
MODELS_TO_TEST = [
    # OpenAI models
    ("openai/gpt-4o-mini", "OpenAI GPT-4o Mini"),
    ("openai/gpt-4o", "OpenAI GPT-4o"),
    
    # Anthropic models
    ("anthropic/claude-3-5-haiku-20241022", "Anthropic Claude 3.5 Haiku"),
    ("anthropic/claude-3-5-sonnet-20241022", "Anthropic Claude 3.5 Sonnet"),
    
    # Google models
    ("google/gemini-flash-1.5", "Google Gemini Flash 1.5"),
    ("google/gemini-pro-1.5", "Google Gemini Pro 1.5"),
    
    # Meta Llama models
    ("meta-llama/llama-3.1-8b-instruct", "Meta Llama 3.1 8B"),
    ("meta-llama/llama-3.1-70b-instruct", "Meta Llama 3.1 70B"),
    
    # Mistral models
    ("mistralai/mistral-7b-instruct", "Mistral 7B Instruct"),
    ("mistralai/mixtral-8x7b-instruct", "Mistral Mixtral 8x7B"),
    
    # Other providers
    ("perplexity/llama-3.1-sonar-small-128k-online", "Perplexity Sonar Small"),
    ("cohere/command-r", "Cohere Command R"),
    ("deepseek/deepseek-chat", "DeepSeek Chat"),
    ("qwen/qwen-2-7b-instruct", "Qwen 2 7B"),
]

def test_model(model_id: str, model_name: str, prompt: str = "Say 'Hello from LLMObserve test!' in exactly 5 words."):
    """Test a single model and return results."""
    print(f"\n{'─' * 50}")
    print(f"Testing: {model_name}")
    print(f"Model ID: {model_id}")
    print(f"{'─' * 50}")
    
    try:
        start_time = time.time()
        
        # Use section to label this test
        with llmobserve.section(f"test:{model_id.replace('/', '_')}"):
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7,
            )
        
        elapsed = time.time() - start_time
        
        # Extract response details
        content = response.choices[0].message.content if response.choices else "No response"
        usage = response.usage
        
        print(f"✅ SUCCESS")
        print(f"   Response: {content[:80]}{'...' if len(content) > 80 else ''}")
        print(f"   Input tokens: {usage.prompt_tokens if usage else 'N/A'}")
        print(f"   Output tokens: {usage.completion_tokens if usage else 'N/A'}")
        print(f"   Latency: {elapsed:.2f}s")
        
        return {
            "model": model_id,
            "name": model_name,
            "status": "success",
            "response": content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "latency": elapsed
        }
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)[:100]}")
        return {
            "model": model_id,
            "name": model_name,
            "status": "failed",
            "error": str(e)
        }

def main():
    print("\n" + "=" * 60)
    print("LLMOBSERVE COMPREHENSIVE MODEL TEST")
    print("=" * 60)
    print(f"Testing {len(MODELS_TO_TEST)} models via OpenRouter")
    print(f"Collector: https://llmobserve-api-production-d791.up.railway.app")
    print(f"Dashboard: https://llmobserve.com/dashboard")
    print("=" * 60)
    
    results = []
    successful = 0
    failed = 0
    
    for model_id, model_name in MODELS_TO_TEST:
        result = test_model(model_id, model_name)
        results.append(result)
        
        if result["status"] == "success":
            successful += 1
        else:
            failed += 1
        
        # Small delay between tests to avoid rate limiting
        time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total models tested: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    # Print failed models
    if failed > 0:
        print("\nFailed models:")
        for r in results:
            if r["status"] == "failed":
                print(f"  - {r['name']}: {r.get('error', 'Unknown error')[:50]}")
    
    # Calculate total tokens
    total_input = sum(r.get("input_tokens", 0) for r in results if r["status"] == "success")
    total_output = sum(r.get("output_tokens", 0) for r in results if r["status"] == "success")
    
    print(f"\nTotal tokens used:")
    print(f"  Input: {total_input}")
    print(f"  Output: {total_output}")
    
    print("\n" + "=" * 60)
    print("CHECK DASHBOARD FOR RESULTS")
    print("https://llmobserve.com/dashboard")
    print("=" * 60)
    
    # Give SDK time to flush events
    print("\nWaiting 5 seconds for events to be flushed...")
    time.sleep(5)
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Save results to file
    with open("/Users/ethanzheng/Documents/GitHub/CostTracking/test_results_openrouter.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nResults saved to test_results_openrouter.json")



