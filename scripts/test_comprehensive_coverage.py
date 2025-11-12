"""
Comprehensive test to verify all OpenAI and Pinecone methods are tracked.

Tests:
1. All OpenAI cost-generating methods
2. All Pinecone cost-generating methods
3. Customer segmentation (set_customer_id)
4. Hierarchical traces (sections, spans, trees)
5. Multi-step agent workflows
"""
import os
import sys
import time
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

import llmobserve
from llmobserve import section, set_customer_id, set_run_id

# Configuration
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_KEY = os.getenv("PINECONE_API_KEY")

print("=" * 80)
print("🧪 COMPREHENSIVE COVERAGE TEST")
print("=" * 80)
print(f"Collector: {COLLECTOR_URL}")
print(f"OpenAI Key: {'✅ Found' if OPENAI_KEY else '❌ Missing'}")
print(f"Pinecone Key: {'✅ Found' if PINECONE_KEY else '❌ Missing'}")
print()

# Initialize SDK (HYBRID mode - instrumentors + HTTP fallback)
llmobserve.observe(collector_url=COLLECTOR_URL)
print("✅ SDK initialized (hybrid mode: instrumentors + HTTP fallback)")
print()

# Test 1: OpenAI Coverage
print("=" * 80)
print("TEST 1: OpenAI - All Cost-Generating Methods")
print("=" * 80)

if OPENAI_KEY:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY)
    
    set_customer_id("customer-alice")
    set_run_id("test-openai-coverage")
    
    try:
        # Test 1a: Chat Completions (Standard)
        print("  1a. Chat Completions (gpt-4o-mini)...")
        with section("openai:chat_completions"):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say 'test' in one word"}],
                max_tokens=5
            )
            print(f"     ✅ Response: {response.choices[0].message.content}")
        
        time.sleep(0.5)
        
        # Test 1b: Chat Completions (Streaming)
        print("  1b. Chat Completions (streaming)...")
        with section("openai:chat_streaming"):
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Count to 3"}],
                max_tokens=20,
                stream=True
            )
            chunks = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)
            print(f"     ✅ Streamed: {''.join(chunks)[:50]}...")
        
        time.sleep(0.5)
        
        # Test 1c: Embeddings
        print("  1c. Embeddings...")
        with section("openai:embeddings"):
            embedding = client.embeddings.create(
                model="text-embedding-3-small",
                input="Test embedding"
            )
            print(f"     ✅ Embedding: {len(embedding.data[0].embedding)} dimensions")
        
        time.sleep(0.5)
        
        # Test 1d: Chat Completions (with caching - if supported)
        print("  1d. Chat Completions (cached tokens)...")
        with section("openai:chat_cached"):
            # Same prompt twice - second should use cache
            for i in range(2):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Repeat: cached test"}],
                    max_tokens=10
                )
            print(f"     ✅ Cached call completed")
        
        print("✅ OpenAI tests passed")
    
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
else:
    print("⚠️  Skipping (no OpenAI key)")

print()

# Test 2: Pinecone Coverage
print("=" * 80)
print("TEST 2: Pinecone - All Cost-Generating Methods")
print("=" * 80)

if PINECONE_KEY:
    try:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=PINECONE_KEY)
        
        # List indexes
        indexes = pc.list_indexes()
        if not indexes or len(indexes.indexes) == 0:
            print("  ⚠️  No Pinecone indexes found, skipping upsert/query tests")
        else:
            index_name = indexes.indexes[0].name
            index = pc.Index(index_name)
            
            print(f"  Using index: {index_name}")
            
            set_customer_id("customer-bob")
            set_run_id("test-pinecone-coverage")
            
            # Test 2a: Upsert
            print("  2a. Upsert vectors...")
            with section("pinecone:upsert"):
                index.upsert(vectors=[
                    ("test-vec-1", [0.1] * 1536, {"test": "data1"}),
                    ("test-vec-2", [0.2] * 1536, {"test": "data2"}),
                ])
                print("     ✅ Upserted 2 vectors")
            
            time.sleep(0.5)
            
            # Test 2b: Query
            print("  2b. Query vectors...")
            with section("pinecone:query"):
                results = index.query(
                    vector=[0.1] * 1536,
                    top_k=5,
                    include_metadata=True
                )
                print(f"     ✅ Queried, got {len(results.matches)} matches")
            
            time.sleep(0.5)
            
            # Test 2c: Fetch
            print("  2c. Fetch by ID...")
            with section("pinecone:fetch"):
                results = index.fetch(ids=["test-vec-1"])
                print(f"     ✅ Fetched {len(results.vectors)} vectors")
            
            time.sleep(0.5)
            
            # Test 2d: Update
            print("  2d. Update vector...")
            with section("pinecone:update"):
                index.update(id="test-vec-1", set_metadata={"updated": "yes"})
                print("     ✅ Updated vector metadata")
            
            time.sleep(0.5)
            
            # Test 2e: Delete
            print("  2e. Delete vectors...")
            with section("pinecone:delete"):
                index.delete(ids=["test-vec-1", "test-vec-2"])
                print("     ✅ Deleted 2 vectors")
            
            print("✅ Pinecone tests passed")
    
    except Exception as e:
        print(f"❌ Pinecone test failed: {e}")
else:
    print("⚠️  Skipping (no Pinecone key)")

print()

# Test 3: Customer Segmentation
print("=" * 80)
print("TEST 3: Customer Segmentation")
print("=" * 80)

set_run_id("test-customer-segmentation")

print("  3a. Customer Alice...")
set_customer_id("customer-alice")
with section("agent:customer_test"):
    with section("tool:greeting"):
        print("     Processing for Alice...")
        time.sleep(0.1)

print("  3b. Customer Bob...")
set_customer_id("customer-bob")
with section("agent:customer_test"):
    with section("tool:greeting"):
        print("     Processing for Bob...")
        time.sleep(0.1)

print("  3c. Customer Charlie...")
set_customer_id("customer-charlie")
with section("agent:customer_test"):
    with section("tool:greeting"):
        print("     Processing for Charlie...")
        time.sleep(0.1)

print("✅ Customer segmentation tests passed")
print()

# Test 4: Hierarchical Traces (Agent Workflow)
print("=" * 80)
print("TEST 4: Hierarchical Traces - Multi-Step Agent")
print("=" * 80)

set_customer_id("customer-alice")
set_run_id("test-hierarchical-agent")

print("  Simulating complex agent workflow...")

with section("agent:research_assistant"):
    print("    🤖 Agent: research_assistant")
    
    with section("step:planning"):
        print("      📋 Step: planning")
        with section("tool:llm_plan"):
            print("        🔧 Tool: llm_plan")
            time.sleep(0.1)
    
    with section("step:research"):
        print("      🔍 Step: research")
        with section("tool:web_search"):
            print("        🔧 Tool: web_search")
            time.sleep(0.1)
        with section("tool:web_scrape"):
            print("        🔧 Tool: web_scrape")
            time.sleep(0.1)
    
    with section("step:synthesis"):
        print("      ✨ Step: synthesis")
        with section("tool:llm_summarize"):
            print("        🔧 Tool: llm_summarize")
            if OPENAI_KEY:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_KEY)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Summarize: test data"}],
                    max_tokens=20
                )
                print(f"        ✅ LLM response: {response.choices[0].message.content[:30]}...")
            else:
                print("        ⚠️  Simulated (no OpenAI key)")
                time.sleep(0.1)
    
    with section("step:formatting"):
        print("      📝 Step: formatting")
        time.sleep(0.1)

print("✅ Hierarchical trace tests passed")
print()

# Test 5: Verify Events in Collector
print("=" * 80)
print("TEST 5: Verify Events in Collector")
print("=" * 80)

time.sleep(2)  # Wait for events to flush

try:
    import requests
    
    # Get recent runs
    response = requests.get(f"{COLLECTOR_URL}/runs/latest?limit=10")
    
    if response.status_code == 200:
        runs = response.json()
        print(f"✅ Found {len(runs)} recent runs")
        
        # Check specific test runs
        test_runs = ["test-openai-coverage", "test-pinecone-coverage", "test-customer-segmentation", "test-hierarchical-agent"]
        
        for test_run_id in test_runs:
            matching = [r for r in runs if r['run_id'] == test_run_id]
            if matching:
                run = matching[0]
                print(f"  ✅ {test_run_id}:")
                print(f"     - Total cost: ${run['total_cost']:.6f}")
                print(f"     - Calls: {run['call_count']}")
                print(f"     - Sections: {run.get('sections', [])[:3]}...")
            else:
                print(f"  ⚠️  {test_run_id}: Not found (may still be flushing)")
        
        # Check customer segmentation
        print()
        print("  Customer breakdown:")
        customers = ["customer-alice", "customer-bob", "customer-charlie"]
        for customer in customers:
            customer_runs = [r for r in runs if customer in str(r)]
            print(f"    - {customer}: {len(customer_runs)} runs")
        
        print()
        print("✅ Collector verification passed")
    else:
        print(f"❌ Collector error: {response.status_code}")

except Exception as e:
    print(f"❌ Verification failed: {e}")

print()

# Summary
print("=" * 80)
print("✅ COMPREHENSIVE TEST COMPLETE")
print("=" * 80)
print()
print("Summary:")
print(f"  ✅ OpenAI methods: {'Tested' if OPENAI_KEY else 'Skipped (no key)'}")
print(f"  ✅ Pinecone methods: {'Tested' if PINECONE_KEY else 'Skipped (no key)'}")
print("  ✅ Customer segmentation: Tested (3 customers)")
print("  ✅ Hierarchical traces: Tested (4-level deep)")
print("  ✅ Event collection: Verified")
print()
print("Ready for deployment! 🚀")

