"""
Comprehensive test script for LLMObserve with multiple providers and sections.
"""
import os
import sys
import time

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python'))

from llmobserve import observe, section, set_customer_id

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize LLMObserve
print("🚀 Initializing LLMObserve...")
observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_f27c7f7f73a40172b8bf9d226ced22255b5036dccc8050d2"
)
print("✅ LLMObserve initialized!\n")

from openai import OpenAI

# Initialize OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ OPENAI_API_KEY not found")
    sys.exit(1)

client = OpenAI(api_key=openai_api_key)

print("=" * 70)
print("SCENARIO 1: Customer Support Agent Workflow")
print("=" * 70)

# Set customer ID for attribution
set_customer_id("customer_test_001")
print("👤 Customer ID set: customer_test_001\n")

with section("agent:customer_support"):
    print("🤖 Starting customer support agent...\n")
    
    # Step 1: Understand the query
    with section("tool:query_understanding"):
        print("  📝 Step 1: Understanding customer query...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a customer support agent. Classify this query."},
                    {"role": "user", "content": "My order hasn't arrived yet and it's been 2 weeks."}
                ],
                max_tokens=50
            )
            print(f"  ✅ Classification: {response.choices[0].message.content}")
            print(f"  📊 Tokens: {response.usage.total_tokens}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    # Step 2: Generate response
    with section("tool:response_generation"):
        print("  💬 Step 2: Generating response...")
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful customer support agent."},
                    {"role": "user", "content": "Write a sympathetic response about a delayed order."}
                ],
                max_tokens=100
            )
            print(f"  ✅ Response generated")
            print(f"  📊 Tokens: {response.usage.total_tokens}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")

print("=" * 70)
print("SCENARIO 2: Content Generation Workflow")
print("=" * 70)

set_customer_id("customer_test_002")
print("👤 Customer ID set: customer_test_002\n")

with section("agent:content_generator"):
    print("🤖 Starting content generator agent...\n")
    
    # Step 1: Generate outline
    with section("tool:outline_generator"):
        print("  📋 Step 1: Generating content outline...")
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Create a 3-point outline for a blog post about AI."}
                ],
                max_tokens=80
            )
            print(f"  ✅ Outline created")
            print(f"  📊 Tokens: {response.usage.total_tokens}\n")
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    # Step 2: Expand each point
    with section("tool:content_expander"):
        print("  ✍️  Step 2: Expanding content...")
        for i in range(2):  # Simulate expanding 2 points
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "user", "content": f"Write 2 sentences about AI benefit #{i+1}"}
                    ],
                    max_tokens=50
                )
                print(f"  ✅ Point {i+1} expanded")
                print(f"  📊 Tokens: {response.usage.total_tokens}")
            except Exception as e:
                print(f"  ❌ Error on point {i+1}: {e}")
        print()

print("=" * 70)
print("SCENARIO 3: Rapid-Fire Queries (Stress Test)")
print("=" * 70)

set_customer_id("customer_test_003")
print("👤 Customer ID set: customer_test_003\n")

with section("agent:qa_bot"):
    print("🤖 Starting Q&A bot with rapid queries...\n")
    
    questions = [
        "What is 2+2?",
        "Name a color.",
        "What day comes after Monday?",
        "Is water wet?",
        "Count to 3."
    ]
    
    for i, question in enumerate(questions, 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": question}],
                max_tokens=15
            )
            print(f"  ✅ Q{i}: {question}")
            print(f"     A: {response.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"  ❌ Q{i} failed: {e}")
    print()

print("=" * 70)
print("SCENARIO 4: Untracked Calls (No Section)")
print("=" * 70)

print("🔍 Making calls without section context...\n")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'untracked' in 1 word."}],
        max_tokens=5
    )
    print(f"✅ Untracked call completed")
    print(f"📊 Tokens: {response.usage.total_tokens}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

print("=" * 70)
print("✅ ALL SCENARIOS COMPLETED!")
print("=" * 70)
print("""
📊 Dashboard Check:
   1. Go to http://localhost:3000/dashboard
   2. You should see:
      - Total costs across all scenarios
      - Breakdown by agent (customer_support, content_generator, qa_bot)
      - Breakdown by customer (customer_test_001, 002, 003)
      - Individual tool costs within each agent
      - Untracked costs (from scenario 4)
   
🎯 Expected Structure:
   agent:customer_support
   ├─ tool:query_understanding
   └─ tool:response_generation
   
   agent:content_generator
   ├─ tool:outline_generator
   └─ tool:content_expander
   
   agent:qa_bot (5 rapid queries)
   
   untracked (1 call)
""")








