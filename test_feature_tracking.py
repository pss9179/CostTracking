"""
Test Feature Tracking with Real OpenAI Calls.

This script tests the `section()` context manager for feature-level cost tracking.
It makes real OpenAI API calls and sends the events to the production collector.
"""
import os
import sys
import time

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python'))

from openai import OpenAI
from llmobserve import observe, section, set_customer_id
from llmobserve.transport import flush_events

# Configuration
COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app"
LLMO_API_KEY = "llmo_sk_7d92be37ef5044a0552fd3b3f73789c68057a08353dae789"  # Real user API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

print("=" * 70)
print("🧪 FEATURE TRACKING TEST")
print("=" * 70)
print(f"\n📡 Collector: {COLLECTOR_URL}")
print(f"🔑 API Key: {LLMO_API_KEY[:20]}...")
print()

# Initialize LLMObserve
print("🚀 Initializing LLMObserve...")
observe(
    collector_url=COLLECTOR_URL,
    api_key=LLMO_API_KEY
)
print("✅ LLMObserve initialized!\n")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Test 1: Email Processing Feature
print("=" * 70)
print("FEATURE 1: Email Processing")
print("=" * 70)

with section("feature:email_processing"):
    print("📧 Summarizing email...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an email summarizer. Be concise."},
            {"role": "user", "content": "Summarize this email: Hi John, I wanted to follow up on our meeting yesterday. The project timeline looks good but we need to finalize the budget. Can you send me the latest numbers? Thanks, Sarah"}
        ],
        max_tokens=100
    )
    print(f"   ✅ Summary: {response.choices[0].message.content[:100]}...")
    print(f"   📊 Tokens: {response.usage.total_tokens}")

# Test 2: Document Summarization Feature
print("\n" + "=" * 70)
print("FEATURE 2: Document Summarization")
print("=" * 70)

with section("feature:document_summarization"):
    print("📄 Summarizing document...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a document summarizer."},
            {"role": "user", "content": "Summarize the key points of the following text: Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves."}
        ],
        max_tokens=100
    )
    print(f"   ✅ Summary: {response.choices[0].message.content[:100]}...")
    print(f"   📊 Tokens: {response.usage.total_tokens}")

# Test 3: Customer Support Feature (with nested sections)
print("\n" + "=" * 70)
print("FEATURE 3: Customer Support Agent")
print("=" * 70)

with section("agent:customer_support"):
    print("🤖 Running customer support agent...")
    
    # Step 1: Understand query
    with section("step:understand_query"):
        print("   📝 Understanding customer query...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract the main intent from customer message."},
                {"role": "user", "content": "I can't log into my account and I've tried resetting my password three times!"}
            ],
            max_tokens=50
        )
        intent = response.choices[0].message.content
        print(f"      ✅ Intent: {intent}")
    
    # Step 2: Generate response
    with section("step:generate_response"):
        print("   💬 Generating response...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful customer support agent."},
                {"role": "user", "content": f"Customer intent: {intent}\n\nProvide a helpful response."}
            ],
            max_tokens=100
        )
        print(f"      ✅ Response: {response.choices[0].message.content[:80]}...")

# Test 4: Code Generation Feature
print("\n" + "=" * 70)
print("FEATURE 4: Code Generation")
print("=" * 70)

with section("feature:code_generation"):
    print("💻 Generating code...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a Python code generator. Write clean, concise code."},
            {"role": "user", "content": "Write a function to calculate fibonacci sequence up to n terms"}
        ],
        max_tokens=200
    )
    print(f"   ✅ Generated code:\n{response.choices[0].message.content[:200]}...")

# Test 5: Data Analysis Feature  
print("\n" + "=" * 70)
print("FEATURE 5: Data Analysis")
print("=" * 70)

with section("feature:data_analysis"):
    print("📊 Analyzing data...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a data analyst. Provide insights."},
            {"role": "user", "content": "Given monthly sales data: Jan: $10k, Feb: $12k, Mar: $15k, Apr: $11k, May: $18k. What insights can you provide?"}
        ],
        max_tokens=150
    )
    print(f"   ✅ Analysis: {response.choices[0].message.content[:150]}...")

# Test 6: Research Agent with Multiple Steps
print("\n" + "=" * 70)
print("FEATURE 6: Research Agent")
print("=" * 70)

with section("agent:researcher"):
    print("🔬 Running research agent...")
    
    with section("tool:web_search"):
        print("   🔍 Simulating web search...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Simulate search results for a query."},
                {"role": "user", "content": "Search: latest trends in AI 2024"}
            ],
            max_tokens=100
        )
        search_results = response.choices[0].message.content
        print(f"      ✅ Found results")
    
    with section("step:analyze"):
        print("   📈 Analyzing results...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze and summarize the following search results."},
                {"role": "user", "content": f"Results: {search_results}"}
            ],
            max_tokens=100
        )
        print(f"      ✅ Analysis complete")
    
    with section("step:write_report"):
        print("   ✍️ Writing report...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Write a brief research report."},
                {"role": "user", "content": "Write a 2-sentence summary of AI trends in 2024."}
            ],
            max_tokens=100
        )
        print(f"      ✅ Report: {response.choices[0].message.content}")

# Flush all events to collector
print("\n" + "=" * 70)
print("📤 Flushing events to collector...")
print("=" * 70)

flush_events()
time.sleep(3)  # Give time for events to be sent

print("\n✅ All events sent!")
print("\n" + "=" * 70)
print("📊 CHECK THE DASHBOARD")
print("=" * 70)
print(f"\n🔗 Dashboard: https://app.llmobserve.com/dashboard")
print("\nExpected features to see:")
print("  - feature:email_processing")
print("  - feature:document_summarization")
print("  - agent:customer_support")
print("  - feature:code_generation")
print("  - feature:data_analysis")
print("  - agent:researcher")
print()

