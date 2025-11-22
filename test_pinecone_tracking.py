"""
Test script to verify Pinecone cost tracking with LLMObserve.
"""
import os
import sys
import time

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sdk', 'python'))

from llmobserve import observe

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

# Check if Pinecone is installed
try:
    from pinecone import Pinecone, ServerlessSpec
    print("✅ Pinecone library found")
except ImportError:
    print("❌ Pinecone library not installed. Install with: pip install pinecone-client")
    sys.exit(1)

# Get Pinecone credentials
pinecone_api_key = os.getenv("PINECONE_API_KEY")
index_name = os.getenv("PINECONE_INDEX_NAME", "test")

if not pinecone_api_key:
    print("❌ PINECONE_API_KEY not found in environment")
    sys.exit(1)

print(f"📌 Using Pinecone index: {index_name}\n")

print("=" * 60)
print("TEST 1: Initialize Pinecone Client")
print("=" * 60)

try:
    pc = Pinecone(api_key=pinecone_api_key)
    print("✅ Pinecone client initialized")
    print()
except Exception as e:
    print(f"❌ Error initializing Pinecone: {e}\n")
    sys.exit(1)

print("=" * 60)
print("TEST 2: List Indexes")
print("=" * 60)

try:
    indexes = pc.list_indexes()
    print(f"✅ Found {len(indexes)} indexes")
    for idx in indexes:
        print(f"   - {idx.name}")
    print()
except Exception as e:
    print(f"❌ Error listing indexes: {e}\n")

print("=" * 60)
print("TEST 3: Query Operations (if index exists)")
print("=" * 60)

try:
    # Check if index exists
    index_list = [idx.name for idx in pc.list_indexes()]
    
    if index_name in index_list:
        index = pc.Index(index_name)
        print(f"✅ Connected to index: {index_name}")
        
        # Try a simple query
        query_vector = [0.1] * 1536  # Standard OpenAI embedding dimension
        results = index.query(
            vector=query_vector,
            top_k=3,
            include_metadata=True
        )
        
        print(f"✅ Query executed successfully")
        print(f"   Matches found: {len(results.get('matches', []))}")
        print()
    else:
        print(f"⚠️  Index '{index_name}' not found. Skipping query test.")
        print(f"   Available indexes: {index_list}")
        print()
except Exception as e:
    print(f"❌ Error querying index: {e}\n")

print("=" * 60)
print("✅ Pinecone tests completed!")
print("=" * 60)
print("\n📊 Check the dashboard at http://localhost:3000/dashboard")
print("   to see the tracked Pinecone costs!")

