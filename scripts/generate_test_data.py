"""
Generate test trace data for development.
"""
import requests
import uuid
from datetime import datetime

API_KEY = "llmo_sk_d184d2df8968d4f8365f7b1b85f4647d4bdadcc3798a0573"
BASE_URL = "http://localhost:8000"

def generate_test_events():
    """Generate some test trace events."""
    
    run_id = str(uuid.uuid4())
    
    events = [
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": str(uuid.uuid4()),
            "parent_span_id": None,
            "section": "agent:research",
            "section_path": "agent:research_assistant",
            "span_type": "llm",
            "provider": "openai",
            "endpoint": "chat",
            "model": "gpt-4o",
            "input_tokens": 1500,
            "output_tokens": 800,
            "cost_usd": 0.0375,
            "latency_ms": 2340.5,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "enduser_001"
        },
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": str(uuid.uuid4()),
            "parent_span_id": None,
            "section": "embedding",
            "section_path": "tool:web_search/embedding",
            "span_type": "llm",
            "provider": "openai",
            "endpoint": "embeddings",
            "model": "text-embedding-3-small",
            "input_tokens": 450,
            "output_tokens": 0,
            "cost_usd": 0.00009,
            "latency_ms": 145.2,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "enduser_001"
        },
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": str(uuid.uuid4()),
            "parent_span_id": None,
            "section": "vector_search",
            "section_path": "tool:web_search/pinecone:query",
            "span_type": "vector_db",
            "provider": "pinecone",
            "endpoint": "query",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0004,
            "latency_ms": 89.3,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "enduser_001"
        },
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": str(uuid.uuid4()),
            "parent_span_id": None,
            "section": "synthesis",
            "section_path": "agent:research_assistant/step:synthesize",
            "span_type": "llm",
            "provider": "openai",
            "endpoint": "chat",
            "model": "gpt-4o-mini",
            "input_tokens": 3200,
            "output_tokens": 450,
            "cost_usd": 0.000705,
            "latency_ms": 892.1,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "enduser_001"
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{BASE_URL}/events/",
        json=events,
        headers=headers
    )
    
    if response.status_code == 201:
        print(f"✅ Created {len(events)} test events for run {run_id}")
        print(f"   Total cost: ${sum(e['cost_usd'] for e in events):.6f}")
    else:
        print(f"❌ Failed to create events: {response.status_code}")
        print(f"   Response: {response.text}")

if __name__ == "__main__":
    print("Generating test data...")
    
    # Generate multiple runs
    for i in range(5):
        print(f"\n Run {i+1}/5:")
        generate_test_events()
    
    print("\n✅ Test data generation complete!")
    print(f"\n📊 View dashboard at: http://localhost:3000")
    print(f"🔍 Check runs: curl -H 'Authorization: Bearer {API_KEY}' {BASE_URL}/runs/latest")

