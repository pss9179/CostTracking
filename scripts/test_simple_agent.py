"""
Simple agent test with OpenAI and Pinecone to verify hierarchical tracking and costs.

This script tests:
1. Agent-level tracking with multiple tools
2. Proper hierarchy (agent → tool → API call)
3. Cost attribution to correct nodes
4. Customer segmentation
"""

import os
import sys
import time

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../sdk/python"))

# Load .env file
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(env_path)
print(f"✅ Loaded .env from: {env_path}")
print(f"   PINECONE_API_KEY: {'✅ Set' if os.getenv('PINECONE_API_KEY') else '❌ Not found'}")
print(f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not found'}")

import llmobserve
from llmobserve import section, set_customer_id
from openai import OpenAI
from pinecone import Pinecone

# Initialize LLMObserve with instrumentors for testing
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key="dev-mode",
    use_instrumentors=True  # Enable direct tracking for lower latency
)

# Initialize clients
openai_client = OpenAI()

# Initialize Pinecone (now loads from .env)
try:
    pinecone_client = Pinecone()
    print("✅ Pinecone client initialized")
except Exception as e:
    print(f"⚠️  Pinecone initialization failed: {e}")
    print("    Pinecone tests will be skipped")
    pinecone_client = None

def test_simple_research_agent():
    """Test a simple research agent with OpenAI and Pinecone."""
    print("\n🤖 Running Simple Research Agent Test...")
    print("=" * 60)
    
    # Set customer
    set_customer_id("test_customer_001")
    
    # Agent-level section
    with section("agent:research_assistant"):
        print("\n📋 Agent: Research Assistant")
        
        # Tool 1: Search vector database
        if pinecone_client:
            with section("tool:vector_search"):
                print("  🔍 Tool: Vector Search (Pinecone)")
                try:
                    from pinecone import ServerlessSpec
                    
                    # Get or create index
                    index_name = "test-index"
                    existing_indexes = [idx.name for idx in pinecone_client.list_indexes()]
                    
                    if index_name not in existing_indexes:
                        print(f"    Creating index: {index_name}")
                        pinecone_client.create_index(
                            name=index_name,
                            dimension=1536,
                            metric="cosine",
                            spec=ServerlessSpec(cloud="aws", region="us-east-1")
                        )
                        time.sleep(5)  # Wait for index to be ready
                    
                    index = pinecone_client.Index(index_name)
                    
                    # Upsert some test vectors
                    print("    Upserting test vectors...")
                    vectors = [
                        ("vec1", [0.1] * 1536, {"topic": "AI"}),
                        ("vec2", [0.2] * 1536, {"topic": "ML"}),
                        ("vec3", [0.3] * 1536, {"topic": "NLP"}),
                    ]
                    index.upsert(vectors=vectors)
                    
                    # Query vectors
                    print("    Querying vectors...")
                    results = index.query(
                        vector=[0.1] * 1536,
                        top_k=3,
                        include_metadata=True
                    )
                    print(f"    ✅ Found {len(results['matches'])} matches")
                    
                except Exception as e:
                    print(f"    ⚠️  Pinecone error: {e}")
        else:
            print("  ⏭️  Skipping Vector Search (Pinecone not configured)")
        
        # Tool 2: LLM Analysis
        with section("tool:llm_analysis"):
            print("  🧠 Tool: LLM Analysis (OpenAI)")
            try:
                # Generate embeddings
                print("    Generating embeddings...")
                embedding_response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input="What is machine learning?"
                )
                print(f"    ✅ Generated {len(embedding_response.data)} embeddings")
                
                # Chat completion
                print("    Running chat completion...")
                chat_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a research assistant."},
                        {"role": "user", "content": "Summarize the key concepts of machine learning in 2 sentences."}
                    ],
                    max_tokens=100
                )
                print(f"    ✅ Response: {chat_response.choices[0].message.content[:50]}...")
                
            except Exception as e:
                print(f"    ⚠️  OpenAI error: {e}")
        
        # Tool 3: Final synthesis
        with section("tool:synthesize"):
            print("  📝 Tool: Synthesize Results (OpenAI)")
            try:
                synthesis_response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are synthesizing research findings."},
                        {"role": "user", "content": "Create a brief conclusion."}
                    ],
                    max_tokens=50
                )
                print(f"    ✅ Synthesis: {synthesis_response.choices[0].message.content[:50]}...")
                
            except Exception as e:
                print(f"    ⚠️  OpenAI error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Research Agent Test Complete!")


def test_multi_customer_scenario():
    """Test multiple customers making agent calls."""
    print("\n👥 Running Multi-Customer Test...")
    print("=" * 60)
    
    customers = ["alice", "bob", "charlie"]
    
    for customer in customers:
        set_customer_id(customer)
        print(f"\n👤 Customer: {customer}")
        
        with section(f"agent:assistant_{customer}"):
            try:
                # Simple LLM call
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": f"Say hello to {customer}"}
                    ],
                    max_tokens=20
                )
                print(f"  ✅ Response: {response.choices[0].message.content}")
                
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Multi-Customer Test Complete!")


if __name__ == "__main__":
    print("\n" + "🚀 " + "=" * 58)
    print("  LLMOBSERVE SIMPLE AGENT TEST")
    print("  Testing: OpenAI + Pinecone + Hierarchical Tracking")
    print("=" * 60)
    
    # Run tests
    test_simple_research_agent()
    time.sleep(1)  # Brief pause
    test_multi_customer_scenario()
    
    # Flush all events before exiting
    print("\n⏳ Flushing events to collector...")
    from llmobserve import buffer
    buffer.flush_events()
    time.sleep(2)  # Wait for final flush
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("\n📊 Check the dashboard at http://localhost:3000")
    print("   - View hierarchical traces")
    print("   - Check cost attribution")
    print("   - Filter by customer")
    print("=" * 60 + "\n")

