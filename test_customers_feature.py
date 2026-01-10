#!/usr/bin/env python3
"""
Test the Customers feature by making LLM calls with customer IDs set.
"""
import os
import time

# Set environment variables before importing llmobserve
os.environ["LLMOBSERVE_COLLECTOR_URL"] = "https://llmobserve-api-production-d791.up.railway.app"
os.environ["LLMOBSERVE_API_KEY"] = os.getenv("LLMOBSERVE_API_KEY", "")

from llmobserve import observe, set_customer_id
import openai

# Get API keys from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLMOBSERVE_API_KEY = os.getenv("LLMOBSERVE_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ OPENROUTER_API_KEY not set!")
    exit(1)

if not LLMOBSERVE_API_KEY:
    print("❌ LLMOBSERVE_API_KEY not set!")
    exit(1)

print("=" * 60)
print("CUSTOMER FEATURE TEST")
print("=" * 60)

# Initialize LLMObserve
observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key=LLMOBSERVE_API_KEY,
)
print("✅ LLMObserve initialized")

# Create OpenAI client pointing to OpenRouter
client = openai.OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Test customers to simulate
test_customers = [
    {"id": "customer_acme_corp", "name": "Acme Corp", "calls": 3},
    {"id": "customer_techstart_io", "name": "TechStart.io", "calls": 2},
    {"id": "customer_bigdata_inc", "name": "BigData Inc", "calls": 4},
    {"id": "user_john_doe@example.com", "name": "John Doe", "calls": 2},
    {"id": "user_jane_smith@example.com", "name": "Jane Smith", "calls": 1},
]

# Use cheap models for testing
cheap_models = [
    "openai/gpt-3.5-turbo",
    "mistralai/mistral-7b-instruct",
    "meta-llama/llama-3.2-1b-instruct",
]

print(f"\nTesting {len(test_customers)} customers with LLM calls...\n")

total_calls = 0
for customer in test_customers:
    print(f"👤 Customer: {customer['name']} ({customer['id']})")
    
    # Set the customer ID - all subsequent calls will be tagged with this
    set_customer_id(customer['id'])
    
    for i in range(customer['calls']):
        model = cheap_models[i % len(cheap_models)]
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Say 'Hello {customer['name']}!' in exactly 5 words."}],
                max_tokens=20,
            )
            
            result = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            print(f"   ✅ Call {i+1}: {model.split('/')[-1]} - {tokens_used} tokens - '{result[:30]}...'")
            total_calls += 1
            
        except Exception as e:
            print(f"   ❌ Call {i+1}: {model} - Error: {str(e)[:50]}")
        
        time.sleep(0.5)  # Rate limiting
    
    print()

print("=" * 60)
print(f"SUMMARY: {total_calls} calls across {len(test_customers)} customers")
print("=" * 60)

# Wait for events to be flushed
print("\n⏳ Waiting 5 seconds for events to flush to collector...")
time.sleep(5)

print("\n✅ Test complete! Check the Customers tab on the dashboard.")
print("   URL: https://app.llmobserve.com/customers")



