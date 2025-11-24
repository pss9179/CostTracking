"""
Test script with multiple providers to see diverse dashboard data.
Tests: OpenAI (multiple models), Pinecone, and simulated providers.
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
print("PROVIDER TEST 1: OpenAI GPT-4o-mini (Multiple Calls)")
print("=" * 70)

set_customer_id("customer_alpha")
print("👤 Customer: customer_alpha\n")

with section("agent:chatbot"):
    for i in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Say hello #{i+1}"}],
                max_tokens=20
            )
            print(f"  ✅ GPT-4o-mini call {i+1}: {response.usage.total_tokens} tokens")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER TEST 2: OpenAI GPT-3.5-turbo (Different Customer)")
print("=" * 70)

set_customer_id("customer_beta")
print("👤 Customer: customer_beta\n")

with section("agent:assistant"):
    for i in range(4):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Count to {i+1}"}],
                max_tokens=15
            )
            print(f"  ✅ GPT-3.5-turbo call {i+1}: {response.usage.total_tokens} tokens")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER TEST 3: OpenAI GPT-4o (Premium Model)")
print("=" * 70)

set_customer_id("customer_gamma")
print("👤 Customer: customer_gamma\n")

with section("agent:premium_bot"):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain quantum computing in 20 words."}
            ],
            max_tokens=30
        )
        print(f"  ✅ GPT-4o call: {response.usage.total_tokens} tokens")
        print(f"     Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER TEST 4: OpenAI Embeddings")
print("=" * 70)

set_customer_id("customer_delta")
print("👤 Customer: customer_delta\n")

with section("agent:search_engine"):
    texts = [
        "Machine learning is awesome",
        "Python is a great language",
        "Data science rocks"
    ]
    
    for i, text in enumerate(texts, 1):
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            print(f"  ✅ Embedding {i}: {response.usage.total_tokens} tokens")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER TEST 5: Pinecone Vector Database")
print("=" * 70)

set_customer_id("customer_epsilon")
print("👤 Customer: customer_epsilon\n")

try:
    from pinecone import Pinecone
    
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "test")
    
    if pinecone_api_key:
        with section("agent:vector_search"):
            pc = Pinecone(api_key=pinecone_api_key)
            print(f"  ✅ Pinecone client initialized")
            
            # List indexes
            indexes = pc.list_indexes()
            print(f"  ✅ Listed {len(indexes)} indexes")
            
            # Try to query if index exists
            index_list = [idx.name for idx in indexes]
            if index_name in index_list:
                index = pc.Index(index_name)
                query_vector = [0.1] * 1536
                results = index.query(
                    vector=query_vector,
                    top_k=3,
                    include_metadata=True
                )
                print(f"  ✅ Query executed: {len(results.get('matches', []))} matches")
            print()
    else:
        print("  ⚠️  Pinecone API key not found, skipping\n")
except ImportError:
    print("  ⚠️  Pinecone library not installed, skipping\n")
except Exception as e:
    print(f"  ❌ Pinecone error: {e}\n")

print("=" * 70)
print("PROVIDER TEST 6: Mixed Workload (Different Customers & Agents)")
print("=" * 70)

# Customer 1: Heavy GPT-4o-mini user
set_customer_id("customer_heavy_user")
print("👤 Customer: customer_heavy_user (10 calls)\n")

with section("agent:bulk_processor"):
    for i in range(10):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Task {i+1}"}],
                max_tokens=10
            )
            if i % 3 == 0:
                print(f"  ✅ Batch call {i+1}/10...")
        except Exception as e:
            print(f"  ❌ Error on call {i+1}: {e}")
    print(f"  ✅ Completed 10 calls\n")

# Customer 2: Mixed model usage
set_customer_id("customer_mixed")
print("👤 Customer: customer_mixed (mixed models)\n")

with section("agent:smart_router"):
    models = ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o-mini", "gpt-3.5-turbo"]
    for i, model in enumerate(models, 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Test {i}"}],
                max_tokens=10
            )
            print(f"  ✅ {model}: {response.usage.total_tokens} tokens")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("✅ ALL PROVIDER TESTS COMPLETED!")
print("=" * 70)
print(f"""
📊 Dashboard Summary:

Expected Providers:
  - OpenAI (multiple models: gpt-4o, gpt-4o-mini, gpt-3.5-turbo, embeddings)
  - Pinecone (if available)

Expected Customers:
  - customer_alpha (3 calls)
  - customer_beta (4 calls)
  - customer_gamma (1 call)
  - customer_delta (3 calls)
  - customer_epsilon (Pinecone)
  - customer_heavy_user (10 calls)
  - customer_mixed (4 calls)

Expected Agents:
  - agent:chatbot
  - agent:assistant
  - agent:premium_bot
  - agent:search_engine
  - agent:vector_search
  - agent:bulk_processor
  - agent:smart_router

Total Expected Calls: ~25+ OpenAI calls + Pinecone operations

🎯 Go to http://localhost:3000/dashboard to see:
   1. Provider breakdown (OpenAI vs Pinecone)
   2. Model breakdown (gpt-4o vs gpt-4o-mini vs gpt-3.5-turbo)
   3. Customer breakdown (7 different customers)
   4. Agent breakdown (7 different agents)
   5. Cost comparison between models
""")





