"""
Sample Agent: Research Assistant with Tool Calls

Demonstrates:
- Multi-tenant isolation (acme-corp, bigco-inc)
- Customer-level tracking (alice, bob, charlie)
- Semantic sections (agent/tool/step)
- Context cleanup between "requests"
- Nested spans with proper parent_span_id
"""

import os
import sys
import time
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))

import llmobserve
from llmobserve import observe, section, set_customer_id, set_run_id
from llmobserve.retry_tracking import retry_block

# Check for API keys
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
COLLECTOR_URL = os.getenv("LLMOBSERVE_COLLECTOR_URL", "http://localhost:8000")

print("=" * 80)
print("🤖 AGENT TEST: Research Assistant with Multi-Tenant Context Isolation")
print("=" * 80)
print(f"Collector: {COLLECTOR_URL}")
print(f"OpenAI Key: {'✅ Found' if OPENAI_KEY else '❌ Missing (will simulate)'}")
print()

# Initialize observability
observe(collector_url=COLLECTOR_URL)

# Import OpenAI (if available)
try:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None
    print("✅ OpenAI SDK imported")
except ImportError:
    client = None
    print("❌ OpenAI SDK not found (install with: pip install openai)")

print()


def simulate_web_search(query: str) -> str:
    """Simulates a web search tool."""
    time.sleep(0.1)  # Simulate network latency
    return f"Search results for: {query}"


def simulate_database_lookup(entity: str) -> dict:
    """Simulates a database lookup tool."""
    time.sleep(0.05)
    return {
        "entity": entity,
        "data": {"revenue": "$1.2M", "employees": 50}
    }


def research_agent(query: str, use_llm: bool = True):
    """
    Main agent orchestrator.
    Demonstrates nested sections: agent → tool → step.
    """
    with section("agent:research_assistant"):
        print(f"  🤖 Agent processing: {query}")
        
        # Step 1: Web search
        with section("tool:web_search"):
            print(f"    🔍 Searching web...")
            results = simulate_web_search(query)
            print(f"    ✅ Found results")
        
        # Step 2: Database lookup
        with section("tool:database_lookup"):
            print(f"    💾 Looking up related data...")
            data = simulate_database_lookup("acme")
            print(f"    ✅ Retrieved data")
        
        # Step 3: LLM analysis (with retry tracking)
        with section("step:analyze_results"):
            print(f"    🧠 Analyzing with LLM...")
            
            if client and use_llm:
                # Simulate retry logic
                with retry_block(max_attempts=2, operation_name="llm_analysis"):
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a helpful research assistant."},
                                {"role": "user", "content": f"Analyze this: {results}\n\nData: {data}"}
                            ],
                            max_tokens=100
                        )
                        analysis = response.choices[0].message.content
                        print(f"    ✅ Analysis complete: {analysis[:50]}...")
                    except Exception as e:
                        print(f"    ⚠️  LLM error: {e}")
                        analysis = "[simulated analysis]"
            else:
                print(f"    ℹ️  Using mock LLM response")
                analysis = "[simulated analysis - install OpenAI SDK for real calls]"
        
        # Step 4: Format response
        with section("step:format_response"):
            print(f"    📝 Formatting final response...")
            response = {
                "query": query,
                "results": results,
                "data": data,
                "analysis": analysis
            }
            print(f"    ✅ Response ready")
        
        return response


def simulate_request(customer: str, query: str, request_num: int):
    """
    Simulates a single HTTP request with proper context isolation.
    In production, middleware would handle the reset + customer extraction.
    """
    print(f"\n{'=' * 80}")
    print(f"📨 REQUEST #{request_num}")
    print(f"   Customer: {customer}")
    print(f"   Query: {query}")
    print(f"{'=' * 80}")
    
    # === MIDDLEWARE SIMULATION ===
    # In production, ObservabilityMiddleware does this automatically
    
    # 1. Reset context (prevent bleed from previous request)
    set_run_id()  # Fresh run_id
    set_customer_id(None)  # Clear old customer
    # section_stack is automatically cleared when contextvars reset
    
    # 2. Extract from request (headers, JWT, etc.)
    set_customer_id(customer)
    
    print(f"✅ Context initialized: customer={customer}")
    print()
    
    # === APPLICATION CODE ===
    # Your actual route handler would be here
    
    try:
        result = research_agent(query, use_llm=(OPENAI_KEY is not None))
        print(f"\n✅ Request #{request_num} complete")
        return result
    except Exception as e:
        print(f"\n❌ Request #{request_num} failed: {e}")
        raise


def main():
    """
    Simulates multiple concurrent-style requests from different customers.
    Demonstrates that context doesn't bleed between requests.
    
    Creates diverse customer patterns:
    - alice: Heavy user (multiple calls, different queries)
    - bob: Medium user (couple queries)
    - charlie: Light user (single query)
    - diana: Power user (complex multi-step workflows)
    """
    
    # Scenario 1: Alice - Marketing analyst (heavy user)
    simulate_request(
        customer="alice",
        query="What are the latest AI trends?",
        request_num=1
    )
    
    time.sleep(0.3)
    
    # Scenario 2: Alice - Follow-up query
    simulate_request(
        customer="alice",
        query="Compare GPT-4 vs Claude pricing",
        request_num=2
    )
    
    time.sleep(0.3)
    
    # Scenario 3: Charlie - Product manager (light user)
    simulate_request(
        customer="charlie",
        query="Research competitor pricing",
        request_num=3
    )
    
    time.sleep(0.3)
    
    # Scenario 4: Diana - Data scientist (power user)
    simulate_request(
        customer="diana",
        query="Analyze sentiment across 1000 customer reviews",
        request_num=4
    )
    
    time.sleep(0.3)
    
    # Scenario 5: Bob - CEO (high-value queries)
    simulate_request(
        customer="bob",
        query="Analyze market competition",
        request_num=5
    )
    
    time.sleep(0.3)
    
    # Scenario 6: Bob - Follow-up
    simulate_request(
        customer="bob",
        query="What is our revenue forecast?",
        request_num=6
    )
    
    time.sleep(0.3)
    
    # Scenario 7: Sarah - Engineer (technical queries)
    simulate_request(
        customer="sarah",
        query="Debug this Python error: IndexError",
        request_num=7
    )
    
    # Flush remaining events
    time.sleep(2)
    
    print("\n" + "=" * 80)
    print("✅ ALL REQUESTS COMPLETE")
    print("=" * 80)
    print()
    print("📊 VERIFICATION STEPS:")
    print()
    print("1. Check collector received events:")
    print(f"   curl {COLLECTOR_URL}/runs/latest")
    print()
    print("2. Check customer breakdown:")
    print(f"   curl {COLLECTOR_URL}/runs/latest")
    print()
    print("3. Open dashboard:")
    print("   http://localhost:3000")
    print()
    print("Expected behavior:")
    print("  ✅ Each request has unique run_id")
    print("  ✅ Customer IDs tracked (alice, bob, charlie, diana, sarah)")
    print("  ✅ No context bleed between requests")
    print("  ✅ Nested sections visible in hierarchical trace")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

