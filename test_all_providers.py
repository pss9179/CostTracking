"""
Comprehensive test with multiple providers including VAPI.
Tests: OpenAI (multiple models), Pinecone, VAPI, and more.
"""
import os
import sys
import time
import requests

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
print("PROVIDER 1: OpenAI GPT-4o-mini")
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
            print(f"  ✅ GPT-4o-mini call {i+1}: {response.usage.total_tokens} tokens, ${response.usage.total_tokens * 0.00000015:.6f}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER 2: OpenAI GPT-3.5-turbo")
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
print("PROVIDER 3: OpenAI GPT-4o (Premium Model)")
print("=" * 70)

set_customer_id("customer_gamma")
print("👤 Customer: customer_gamma\n")

with section("agent:premium_bot"):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Explain AI in 15 words."}
            ],
            max_tokens=25
        )
        print(f"  ✅ GPT-4o call: {response.usage.total_tokens} tokens")
        print(f"     Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("PROVIDER 4: OpenAI Embeddings (text-embedding-3-small)")
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
print("PROVIDER 5: VAPI (Voice AI)")
print("=" * 70)

set_customer_id("customer_vapi_user")
print("👤 Customer: customer_vapi_user\n")

vapi_private_key = os.getenv("VAPI_PRIVATE_KEY")
vapi_assistant_id = os.getenv("VAPI_ASSISTANT_ID")

if vapi_private_key:
    with section("agent:voice_assistant"):
        try:
            # List assistants
            headers = {
                "Authorization": f"Bearer {vapi_private_key}",
                "Content-Type": "application/json"
            }
            
            print("  📞 Fetching VAPI assistants...")
            response = requests.get(
                "https://api.vapi.ai/assistant",
                headers=headers
            )
            
            if response.status_code == 200:
                assistants = response.json()
                print(f"  ✅ VAPI API call successful: {len(assistants)} assistants found")
                
                # Get specific assistant details if ID is available
                if vapi_assistant_id:
                    print(f"  📞 Fetching assistant details: {vapi_assistant_id[:20]}...")
                    detail_response = requests.get(
                        f"https://api.vapi.ai/assistant/{vapi_assistant_id}",
                        headers=headers
                    )
                    if detail_response.status_code == 200:
                        print(f"  ✅ Assistant details retrieved")
                    else:
                        print(f"  ⚠️  Assistant details: {detail_response.status_code}")
            else:
                print(f"  ⚠️  VAPI API returned: {response.status_code}")
            print()
        except Exception as e:
            print(f"  ❌ VAPI error: {e}\n")
else:
    print("  ⚠️  VAPI_PRIVATE_KEY not found, skipping\n")

print("=" * 70)
print("PROVIDER 6: Pinecone Vector Database")
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
print("PROVIDER 7: Heavy Usage Simulation (GPT-4o-mini)")
print("=" * 70)

set_customer_id("customer_heavy_user")
print("👤 Customer: customer_heavy_user (15 rapid calls)\n")

with section("agent:bulk_processor"):
    success_count = 0
    for i in range(15):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Task {i+1}"}],
                max_tokens=10
            )
            success_count += 1
            if i % 5 == 0:
                print(f"  ✅ Progress: {success_count}/15 calls...")
        except Exception as e:
            print(f"  ❌ Error on call {i+1}: {e}")
    print(f"  ✅ Completed {success_count}/15 calls\n")

print("=" * 70)
print("PROVIDER 8: Mixed Model Usage")
print("=" * 70)

set_customer_id("customer_mixed")
print("👤 Customer: customer_mixed\n")

with section("agent:smart_router"):
    models = [
        ("gpt-4o-mini", "Fast task"),
        ("gpt-3.5-turbo", "Medium task"),
        ("gpt-4o", "Complex task"),
        ("gpt-4o-mini", "Another fast task"),
        ("gpt-3.5-turbo", "Another medium task")
    ]
    
    for model, task in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": task}],
                max_tokens=15
            )
            print(f"  ✅ {model}: {response.usage.total_tokens} tokens")
        except Exception as e:
            print(f"  ❌ {model} error: {e}")
    print()

print("=" * 70)
print("PROVIDER 9: OpenAI Embeddings (Large Batch)")
print("=" * 70)

set_customer_id("customer_embeddings")
print("👤 Customer: customer_embeddings\n")

with section("agent:semantic_search"):
    batch_texts = [
        "Artificial intelligence",
        "Machine learning algorithms",
        "Neural networks",
        "Deep learning models",
        "Natural language processing"
    ]
    
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch_texts
        )
        print(f"  ✅ Batch embedding: {response.usage.total_tokens} tokens for {len(batch_texts)} texts")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()

print("=" * 70)
print("✅ ALL PROVIDER TESTS COMPLETED!")
print("=" * 70)
print(f"""
📊 Dashboard Summary:

Providers Tested:
  ✅ OpenAI (gpt-4o, gpt-4o-mini, gpt-3.5-turbo, embeddings)
  ✅ VAPI (Voice AI API calls)
  ✅ Pinecone (Vector database)

Customers Created:
  - customer_alpha (3 calls)
  - customer_beta (4 calls)
  - customer_gamma (1 call)
  - customer_delta (3 calls)
  - customer_vapi_user (VAPI calls)
  - customer_epsilon (Pinecone)
  - customer_heavy_user (15 calls)
  - customer_mixed (5 calls)
  - customer_embeddings (batch)

Agents Created:
  - agent:chatbot
  - agent:assistant
  - agent:premium_bot
  - agent:search_engine
  - agent:voice_assistant
  - agent:vector_search
  - agent:bulk_processor
  - agent:smart_router
  - agent:semantic_search

Total Calls: ~35+ API calls across multiple providers

🎯 Go to http://localhost:3000/dashboard to see:
   1. Provider breakdown (OpenAI, VAPI, Pinecone)
   2. Model breakdown (gpt-4o vs gpt-4o-mini vs gpt-3.5-turbo vs embeddings)
   3. Cost comparison (GPT-4o is ~30x more expensive than GPT-4o-mini)
   4. Customer breakdown (9 different customers)
   5. Agent breakdown (9 different agents)
   6. Time series of API usage
""")








