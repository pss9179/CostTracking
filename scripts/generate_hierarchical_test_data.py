"""
Generate hierarchical test data with proper parent-child span relationships.

Creates a realistic agent trace with nested sections:
└─ agent:research_assistant
   ├─ step:gather_data
   │  ├─ tool:web_search
   │  │  ├─ embedding
   │  │  └─ vector_search
   ├─ step:analyze
   │  └─ chat (gpt-4o)
   └─ step:synthesize
      └─ chat (gpt-4o-mini)
"""
import requests
import uuid
from datetime import datetime, timedelta

API_KEY = "llmo_sk_d184d2df8968d4f8365f7b1b85f4647d4bdadcc3798a0573"
BASE_URL = "http://localhost:8000"


def generate_hierarchical_run():
    """Generate a single run with hierarchical trace data."""
    
    run_id = str(uuid.uuid4())
    base_time = datetime.utcnow()
    
    # Generate span IDs upfront to link parent-child relationships
    span_agent = str(uuid.uuid4())
    span_gather = str(uuid.uuid4())
    span_web_search = str(uuid.uuid4())
    span_embedding = str(uuid.uuid4())
    span_vector = str(uuid.uuid4())
    span_analyze = str(uuid.uuid4())
    span_analyze_llm = str(uuid.uuid4())
    span_synthesize = str(uuid.uuid4())
    span_synthesize_llm = str(uuid.uuid4())
    
    events = [
        # 1. Root: Agent starts (hypothetical parent event)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_agent,
            "parent_span_id": None,  # Root node
            "section": "agent",
            "section_path": "agent:research_assistant",
            "span_type": "agent",
            "provider": "internal",
            "endpoint": "orchestrate",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 5523.7,  # Total agent duration
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time).isoformat()
        },
        
        # 2. Step: Gather Data (child of agent)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_gather,
            "parent_span_id": span_agent,  # Parent = agent
            "section": "gather_data",
            "section_path": "agent:research_assistant/step:gather_data",
            "span_type": "step",
            "provider": "internal",
            "endpoint": "gather",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 2234.5,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=10)).isoformat()
        },
        
        # 3. Tool: Web Search (child of gather_data)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_web_search,
            "parent_span_id": span_gather,  # Parent = gather_data
            "section": "web_search",
            "section_path": "agent:research_assistant/step:gather_data/tool:web_search",
            "span_type": "tool",
            "provider": "internal",
            "endpoint": "search",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 334.5,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=20)).isoformat()
        },
        
        # 4. Embedding call (child of web_search)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_embedding,
            "parent_span_id": span_web_search,  # Parent = web_search
            "section": "embedding",
            "section_path": "agent:research_assistant/step:gather_data/tool:web_search/embedding",
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
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=30)).isoformat()
        },
        
        # 5. Vector search (child of web_search)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_vector,
            "parent_span_id": span_web_search,  # Parent = web_search
            "section": "vector_search",
            "section_path": "agent:research_assistant/step:gather_data/tool:web_search/vector_search",
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
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=180)).isoformat()
        },
        
        # 6. Step: Analyze (child of agent)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_analyze,
            "parent_span_id": span_agent,  # Parent = agent
            "section": "analyze",
            "section_path": "agent:research_assistant/step:analyze",
            "span_type": "step",
            "provider": "internal",
            "endpoint": "analyze",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 1890.4,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=2250)).isoformat()
        },
        
        # 7. LLM call in analyze (child of analyze)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_analyze_llm,
            "parent_span_id": span_analyze,  # Parent = analyze
            "section": "analyze_llm",
            "section_path": "agent:research_assistant/step:analyze/llm:chat",
            "span_type": "llm",
            "provider": "openai",
            "endpoint": "chat",
            "model": "gpt-4o",
            "input_tokens": 2800,
            "output_tokens": 600,
            "cost_usd": 0.024,
            "latency_ms": 1780.5,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=2300)).isoformat()
        },
        
        # 8. Step: Synthesize (child of agent)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_synthesize,
            "parent_span_id": span_agent,  # Parent = agent
            "section": "synthesize",
            "section_path": "agent:research_assistant/step:synthesize",
            "span_type": "step",
            "provider": "internal",
            "endpoint": "synthesize",
            "model": None,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0.0,
            "latency_ms": 1092.1,
            "status": "ok",
            "is_streaming": False,
            "stream_cancelled": False,
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=4150)).isoformat()
        },
        
        # 9. LLM call in synthesize (child of synthesize)
        {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "span_id": span_synthesize_llm,
            "parent_span_id": span_synthesize,  # Parent = synthesize
            "section": "synthesize_llm",
            "section_path": "agent:research_assistant/step:synthesize/llm:chat",
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
            "customer_id": "alice_customer_123",
            "created_at": (base_time + timedelta(milliseconds=4200)).isoformat()
        },
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
        total_cost = sum(e['cost_usd'] for e in events)
        print(f"✅ Created hierarchical run: {run_id[:12]}...")
        print(f"   └─ agent:research_assistant (${total_cost:.6f})")
        print(f"      ├─ step:gather_data")
        print(f"      │  └─ tool:web_search (embedding + vector)")
        print(f"      ├─ step:analyze (gpt-4o)")
        print(f"      └─ step:synthesize (gpt-4o-mini)")
        return run_id
    else:
        print(f"❌ Failed to create events: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


if __name__ == "__main__":
    print("🌳 Generating HIERARCHICAL Test Data")
    print("=" * 60)
    
    run_ids = []
    for i in range(3):
        print(f"\n📦 Run {i+1}/3:")
        run_id = generate_hierarchical_run()
        if run_id:
            run_ids.append(run_id)
    
    print("\n" + "=" * 60)
    print("✅ Hierarchical test data generation complete!")
    print(f"\n📊 View dashboard: http://localhost:3000")
    print(f"🌳 Click into any run to see the tree structure!")
    
    if run_ids:
        print(f"\n🔗 Example run detail:")
        print(f"   http://localhost:3000/runs/{run_ids[0]}")

