"""
Test script to generate sample LLM runs with varying models and patterns.

This script:
- Tests multiple OpenAI models (GPT-5, GPT-4.1, GPT-4o, etc.)
- Tries real OpenAI/Pinecone API calls if keys are available
- Falls back to mocking if keys are not present
- Creates runs with different characteristics to show cost tracking
"""
import os
import sys
import time
import uuid
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent.parent / "sdk" / "python"
sys.path.insert(0, str(sdk_path))

from llmobserve import observe, section, set_run_id, set_customer_id


def mock_openai_call(model: str, input_tokens: int, output_tokens: int, endpoint: str = "chat") -> None:
    """Mock an OpenAI call by directly adding an event."""
    from llmobserve import buffer, context, pricing
    
    cost = pricing.compute_cost(
        provider="openai",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )
    
    # Get hierarchical section information
    section_path = context.get_section_path()
    span_id = context.get_current_span_id() or str(uuid.uuid4())
    parent_span_id = context.get_parent_span_id()
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "section": context.get_current_section(),
        "section_path": section_path,  # NEW: Full hierarchical path
        "span_type": "llm",
        "provider": "openai",
        "endpoint": endpoint,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "latency_ms": 200 + (input_tokens / 10),
        "status": "ok",
        "event_metadata": {"test": True, "model_family": model.split("-")[0]}
    }
    
    buffer.add_event(event)
    time.sleep(0.1)  # Simulate API latency


def mock_pinecone_call(operation: str = "query") -> None:
    """Mock a Pinecone call by directly adding an event."""
    from llmobserve import buffer, context, pricing
    
    cost = pricing.compute_cost(provider="pinecone", model=None)
    
    # Get hierarchical section information
    section_path = context.get_section_path()
    span_id = context.get_current_span_id() or str(uuid.uuid4())
    parent_span_id = context.get_parent_span_id()
    
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "section": context.get_current_section(),
        "section_path": section_path,  # NEW: Full hierarchical path
        "span_type": "vector_db",
        "provider": "pinecone",
        "endpoint": operation,
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": cost,
        "latency_ms": 50,
        "status": "ok",
        "event_metadata": {"test": True}
    }
    
    buffer.add_event(event)
    time.sleep(0.05)


def test_gpt5_models():
    """Test GPT-5 model family."""
    print("\n🔵 Testing GPT-5 Models...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("enduser_42")
    
    with section("document-analysis"):
        print("  • GPT-5 nano (fast classification)")
        mock_openai_call("gpt-5-nano", input_tokens=500, output_tokens=50)
        
    with section("reasoning"):
        print("  • GPT-5 mini (general tasks)")
        mock_openai_call("gpt-5-mini", input_tokens=1500, output_tokens=400)
        
    with section("complex-reasoning"):
        print("  • GPT-5 (advanced coding)")
        mock_openai_call("gpt-5", input_tokens=3000, output_tokens=1200)
        
    with section("expert-analysis"):
        print("  • GPT-5 pro (highest accuracy)")
        mock_openai_call("gpt-5-pro", input_tokens=2000, output_tokens=800)


def test_gpt41_models():
    """Test GPT-4.1 fine-tunable models."""
    print("\n🟢 Testing GPT-4.1 Models (Fine-tunable)...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("client_gamma")
    
    with section("classification"):
        print("  • GPT-4.1 nano")
        mock_openai_call("gpt-4.1-nano", input_tokens=400, output_tokens=20)
        
    with section("summarization"):
        print("  • GPT-4.1 mini")
        mock_openai_call("gpt-4.1-mini", input_tokens=2000, output_tokens=300)
        
    with section("code-generation"):
        print("  • GPT-4.1")
        mock_openai_call("gpt-4.1", input_tokens=1800, output_tokens=600)


def test_realtime_api():
    """Test Realtime API models."""
    print("\n🟡 Testing Realtime API...")
    
    set_run_id(str(uuid.uuid4()))
    
    with section("realtime-chat"):
        print("  • GPT Realtime (text)")
        mock_openai_call("gpt-realtime", input_tokens=500, output_tokens=200, endpoint="realtime")
        
    with section("voice-interaction"):
        print("  • GPT Realtime Audio")
        mock_openai_call("gpt-realtime-audio", input_tokens=1000, output_tokens=400, endpoint="realtime")


def test_legacy_models():
    """Test legacy GPT-4 and GPT-3.5 models."""
    print("\n🔴 Testing Legacy Models...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("user_alpha")
    
    with section("retrieval"):
        # Simulate embeddings
        print("  • Embeddings (text-embedding-3-small)")
        mock_openai_call("text-embedding-3-small", input_tokens=800, output_tokens=0, endpoint="embeddings")
        
        # Simulate Pinecone query
        print("  • Pinecone query")
        mock_pinecone_call("query")
        
    with section("generation"):
        print("  • GPT-4o-mini")
        mock_openai_call("gpt-4o-mini", input_tokens=1200, output_tokens=400)
        
    with section("verification"):
        print("  • GPT-4o")
        mock_openai_call("gpt-4o", input_tokens=2000, output_tokens=600)


def test_mixed_workload():
    """Test a mixed workload with multiple models."""
    print("\n🟣 Testing Mixed Workload (RAG + Reasoning)...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("beta_user_1")
    
    with section("retrieval"):
        print("  • Generate embeddings")
        mock_openai_call("text-embedding-3-small", input_tokens=500, output_tokens=0, endpoint="embeddings")
        
        print("  • Query Pinecone (3x)")
        for _ in range(3):
            mock_pinecone_call("query")
    
    with section("reranking"):
        print("  • GPT-5 nano for relevance scoring")
        mock_openai_call("gpt-5-nano", input_tokens=1500, output_tokens=100)
        
    with section("synthesis"):
        print("  • GPT-5 for answer synthesis")
        mock_openai_call("gpt-5", input_tokens=3500, output_tokens=1000)
        
    with section("refinement"):
        print("  • GPT-5 mini for cleanup")
        mock_openai_call("gpt-5-mini", input_tokens=1200, output_tokens=300)


def test_expensive_run():
    """Test an expensive run to show cost tracking."""
    print("\n💎 Testing Expensive Run (GPT-5 Pro)...")
    
    set_run_id(str(uuid.uuid4()))
    
    with section("deep-analysis"):
        print("  • GPT-5 Pro (large context)")
        mock_openai_call("gpt-5-pro", input_tokens=8000, output_tokens=3000)
        
    with section("follow-up"):
        print("  • GPT-5 Pro (detailed response)")
        mock_openai_call("gpt-5-pro", input_tokens=5000, output_tokens=2000)


def test_cost_comparison():
    """Test cost comparison between models on same task."""
    print("\n💰 Testing Cost Comparison (Same Task, Different Models)...")
    
    # Run 1: Using expensive model
    set_run_id(str(uuid.uuid4()))
    with section("task-execution"):
        print("  • Run 1: GPT-4o (expensive)")
        mock_openai_call("gpt-4o", input_tokens=2000, output_tokens=500)
    
    time.sleep(0.5)
    
    # Run 2: Using cheaper model
    set_run_id(str(uuid.uuid4()))
    with section("task-execution"):
        print("  • Run 2: GPT-5-nano (cheaper)")
        mock_openai_call("gpt-5-nano", input_tokens=2000, output_tokens=500)


def test_hierarchical_agent_workflow():
    """Test hierarchical tracing with nested agent, tool, and step sections."""
    print("\n🌳 Testing Hierarchical Agent Workflow...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("test_user_hierarchical")
    
    with section("agent:researcher"):
        print("  • Agent: Researcher (coordinator)")
        
        # Tool: Web search
        with section("tool:web_search"):
            print("    ├─ Tool: Web search")
            mock_openai_call("gpt-4o", input_tokens=500, output_tokens=200)
        
        # Step: Analyze results
        with section("step:analyze_results"):
            print("    ├─ Step: Analyze search results")
            mock_openai_call("gpt-4o-mini", input_tokens=1000, output_tokens=400)
        
        # Tool: Database query
        with section("tool:pinecone_query"):
            print("    ├─ Tool: Pinecone query")
            mock_pinecone_call("query")
        
        # Step: Synthesize findings
        with section("step:synthesize"):
            print("    └─ Step: Synthesize findings")
            mock_openai_call("gpt-4o", input_tokens=1500, output_tokens=600)


def test_multi_agent_orchestration():
    """Test multi-agent orchestration with nested hierarchy."""
    print("\n🤖 Testing Multi-Agent Orchestration...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("test_user_multiagent")
    
    with section("agent:coordinator"):
        print("  • Agent: Coordinator (main)")
        
        # Sub-agent: Planner
        with section("agent:planner"):
            print("    ├─ Agent: Planner")
            with section("tool:openai_chat"):
                print("      ├─ Tool: OpenAI chat (planning)")
                mock_openai_call("gpt-5-mini", input_tokens=800, output_tokens=300)
        
        # Sub-agent: Executor
        with section("agent:executor"):
            print("    ├─ Agent: Executor")
            with section("tool:openai_chat"):
                print("      ├─ Tool: OpenAI chat (execution)")
                mock_openai_call("gpt-4o", input_tokens=1200, output_tokens=500)
            
            with section("tool:pinecone_upsert"):
                print("      ├─ Tool: Pinecone upsert")
                mock_pinecone_call("upsert")
        
        # Sub-agent: Reviewer
        with section("agent:reviewer"):
            print("    └─ Agent: Reviewer")
            with section("tool:openai_chat"):
                print("      └─ Tool: OpenAI chat (review)")
                mock_openai_call("gpt-4o-mini", input_tokens=1000, output_tokens=400)


def test_data_pipeline_workflow():
    """Test data pipeline with ETL steps."""
    print("\n🔄 Testing Data Pipeline Workflow...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("test_user_pipeline")
    
    with section("agent:data_pipeline"):
        print("  • Agent: Data Pipeline")
        
        # Step 1: Extract
        with section("step:extract"):
            print("    ├─ Step: Extract data")
            mock_openai_call("gpt-5-nano", input_tokens=200, output_tokens=100)
        
        # Step 2: Transform
        with section("step:transform"):
            print("    ├─ Step: Transform data")
            with section("tool:openai_embed"):
                print("      ├─ Tool: OpenAI embeddings")
                mock_openai_call("text-embedding-3-small", input_tokens=5000, output_tokens=0)
            
            with section("tool:openai_chat"):
                print("      ├─ Tool: OpenAI chat (enrichment)")
                mock_openai_call("gpt-4o-mini", input_tokens=800, output_tokens=300)
        
        # Step 3: Load
        with section("step:load"):
            print("    └─ Step: Load to vector DB")
            with section("tool:pinecone_upsert"):
                print("      └─ Tool: Pinecone upsert")
                mock_pinecone_call("upsert")


def test_mixed_flat_and_hierarchical():
    """Test mixed flat and hierarchical sections (backward compatibility)."""
    print("\n🔀 Testing Mixed Flat and Hierarchical Sections...")
    
    set_run_id(str(uuid.uuid4()))
    set_customer_id("test_user_mixed")
    
    # Flat section (old style - still works!)
    with section("retrieval"):
        print("  • Flat section: retrieval")
        mock_pinecone_call("query")
    
    # Hierarchical section (new style)
    with section("agent:analyzer"):
        print("  • Hierarchical: agent:analyzer")
        with section("tool:openai_chat"):
            print("    └─ Tool: OpenAI chat")
            mock_openai_call("gpt-4o", input_tokens=1000, output_tokens=400)
    
    # Another flat section
    with section("synthesis"):
        print("  • Flat section: synthesis")
        mock_openai_call("gpt-4o-mini", input_tokens=500, output_tokens=200)


def main():
    """Main test runner."""
    print("=" * 70)
    print("🧪 TESTING COMPREHENSIVE MODEL COVERAGE + HIERARCHICAL TRACING")
    print("=" * 70)
    
    # Initialize observability
    collector_url = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")
    observe(collector_url)
    
    print(f"\n📡 Collector URL: {collector_url}")
    print("🔧 Mode: Mocked API calls (for fast testing)")
    print("\nStarting test runs...\n")
    
    try:
        # Test different model families with different tenants
        # tenant_id set via observe() call
        test_gpt5_models()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_gpt41_models()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_realtime_api()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_legacy_models()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_mixed_workload()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_expensive_run()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_cost_comparison()
        time.sleep(0.5)
        
        # NEW: Test hierarchical tracing scenarios
        print("\n" + "=" * 70)
        print("🌳 TESTING HIERARCHICAL TRACING")
        print("=" * 70)
        
        # tenant_id set via observe() call
        test_hierarchical_agent_workflow()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_multi_agent_orchestration()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_data_pipeline_workflow()
        time.sleep(0.5)
        
        # tenant_id set via observe() call
        test_mixed_flat_and_hierarchical()
        time.sleep(2)
        
        # Force flush - events auto-flush every 500ms
        print("\n⏳ Waiting for events to flush...")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        
        # Print tenant breakdown
        print("\nFetching per-tenant costs...")
        import requests
        try:
            tenant_stats = requests.get("http://localhost:8000/tenants/stats").json()
            print("\nPer-Tenant Cost Breakdown:")
            print("-" * 60)
            for t in tenant_stats:
                print(f"  {t['tenant_id']:20s} ${t['total_cost']:8.6f}  ({t['call_count']} calls)")
            print("-" * 60)
        except Exception as e:
            print(f"Could not fetch tenant stats: {e}")
        
        # Print customer breakdown for a tenant
        print("\nFetching per-customer costs for 'acme'...")
        try:
            customer_stats = requests.get("http://localhost:8000/tenants/acme/customers").json()
            print("\nPer-Customer Breakdown (Tenant: acme):")
            print("-" * 60)
            for c in customer_stats:
                print(f"  {c['customer_id']:20s} ${c['total_cost']:8.6f}  ({c['call_count']} calls)")
            print("-" * 60)
        except Exception as e:
            print(f"Could not fetch customer stats: {e}")
        
        print("\n📊 Dashboard: http://localhost:3000")
        print("📡 API Stats: http://localhost:8000/stats/by-provider")
        print("👥 Tenant Stats: http://localhost:3000/tenants")
        print("\nCheck your dashboard to see cost breakdown by:")
        print("  • Tenant (acme, beta-corp, gamma-inc, premium-client, hierarchical-demo)")
        print("  • Customer (enduser_42, client_gamma, user_alpha, beta_user_1, test_user_*)")
        print("  • Provider (OpenAI vs Pinecone)")
        print("  • Model family (GPT-5, GPT-4.1, GPT-4o, etc.)")
        print("  • Section (retrieval, reasoning, synthesis, etc.)")
        print("\n🌳 NEW: Hierarchical Tracing")
        print("  • Navigate to any run from 'hierarchical-demo' tenant")
        print("  • Switch to 'Hierarchical Trace' tab")
        print("  • Expand/collapse to see nested agent → tool → step hierarchy")
        print("  • View semantic paths like 'agent:researcher/tool:web_search'")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
