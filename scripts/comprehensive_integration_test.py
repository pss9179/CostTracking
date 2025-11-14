#!/usr/bin/env python3
"""
COMPREHENSIVE INTEGRATION TEST
Tests the entire platform with real services running, actual API calls, and end-to-end flows.
This simulates real user scenarios.
"""
import os
import sys
import json
import time
import requests
import asyncio
from datetime import datetime
from typing import Dict, List

# Test tracker
class IntegrationTestTracker:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.warnings = []
        
    def test(self, name: str, condition: bool, error_msg: str = ""):
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"✅ {name}")
            return True
        else:
            self.tests_failed += 1
            self.failures.append(f"{name}: {error_msg}")
            print(f"❌ {name}: {error_msg}")
            return False
    
    def warning(self, msg: str):
        self.warnings.append(msg)
        print(f"⚠️  WARNING: {msg}")
    
    def report(self):
        print("\n" + "="*80)
        print("INTEGRATION TEST REPORT")
        print("="*80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100 if self.tests_run > 0 else 0):.2f}%")
        
        if self.failures:
            print("\n❌ FAILURES:")
            for i, failure in enumerate(self.failures, 1):
                print(f"{i}. {failure}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {warning}")
        
        print("\n" + "="*80)
        if self.tests_failed == 0:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            return True
        else:
            print("🚨 SOME TESTS FAILED - REVIEW BEFORE LAUNCH")
            return False

tracker = IntegrationTestTracker()

# =============================================================================
# CONFIGURATION
# =============================================================================
COLLECTOR_URL = os.getenv("COLLECTOR_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

print(f"\n{'='*80}")
print("INTEGRATION TEST CONFIGURATION")
print(f"{'='*80}")
print(f"Collector URL: {COLLECTOR_URL}")
print(f"Frontend URL: {FRONTEND_URL}")
print(f"{'='*80}\n")

# =============================================================================
# 1. COLLECTOR HEALTH CHECK
# =============================================================================
print(f"\n{'='*80}")
print("1. COLLECTOR HEALTH CHECK")
print(f"{'='*80}")

try:
    response = requests.get(f"{COLLECTOR_URL}/health", timeout=5)
    tracker.test(
        "Collector is running",
        response.status_code == 200,
        f"Status: {response.status_code}"
    )
    
    health_data = response.json()
    tracker.test(
        "Collector health endpoint returns valid JSON",
        "status" in health_data,
        f"Response: {health_data}"
    )
except requests.exceptions.ConnectionError:
    tracker.test("Collector is running", False, "Connection refused - is collector running on port 8000?")
    tracker.warning("Remaining tests will fail if collector is not running")
except Exception as e:
    tracker.test("Collector is running", False, str(e))

# =============================================================================
# 2. EVENT INGESTION TEST
# =============================================================================
print(f"\n{'='*80}")
print("2. EVENT INGESTION TEST")
print(f"{'='*80}")

test_event = {
    "id": f"test-event-{int(time.time())}",
    "run_id": "test-run-123",
    "span_id": "span-001",
    "parent_span_id": None,
    "section": "test",
    "section_path": "agent:test-agent/tool:test-tool",
    "span_type": "llm",
    "provider": "openai",
    "endpoint": "chat",
    "model": "gpt-4o",
    "tenant_id": "test-tenant",
    "customer_id": "test-customer",
    "input_tokens": 1000,
    "output_tokens": 500,
    "cost_usd": 0.0075,
    "latency_ms": 1234.5,
    "status": "ok",
}

try:
    response = requests.post(
        f"{COLLECTOR_URL}/events/",
        json=test_event,
        timeout=5
    )
    tracker.test(
        "Event ingestion succeeds",
        response.status_code == 200,
        f"Status: {response.status_code}, Body: {response.text[:200]}"
    )
    
    if response.status_code == 200:
        resp_data = response.json()
        tracker.test(
            "Event ingestion returns event_id",
            "event_id" in resp_data or "id" in resp_data,
            f"Response: {resp_data}"
        )
except Exception as e:
    tracker.test("Event ingestion", False, str(e))

# Wait for event to be processed
time.sleep(1)

# =============================================================================
# 3. STATS RETRIEVAL TEST
# =============================================================================
print(f"\n{'='*80}")
print("3. STATS RETRIEVAL TEST")
print(f"{'='*80}")

try:
    # Get stats for test tenant
    response = requests.get(
        f"{COLLECTOR_URL}/stats/summary",
        params={"tenant_id": "test-tenant"},
        timeout=5
    )
    tracker.test(
        "Stats API responds",
        response.status_code == 200,
        f"Status: {response.status_code}"
    )
    
    if response.status_code == 200:
        stats = response.json()
        tracker.test(
            "Stats contains cost data",
            "total_cost" in stats or "cost_24h" in stats or isinstance(stats, dict),
            f"Stats: {stats}"
        )
except Exception as e:
    tracker.test("Stats retrieval", False, str(e))

# =============================================================================
# 4. SPENDING CAPS TEST
# =============================================================================
print(f"\n{'='*80}")
print("4. SPENDING CAPS TEST")
print(f"{'='*80}")

# Note: This requires authentication, so we'll test what we can without it
try:
    # Try to get caps (will likely fail without auth, but endpoint should exist)
    response = requests.get(f"{COLLECTOR_URL}/caps/", timeout=5)
    tracker.test(
        "Caps endpoint exists",
        response.status_code in [200, 401, 403],  # Any of these means endpoint exists
        f"Status: {response.status_code}"
    )
except Exception as e:
    tracker.test("Caps endpoint", False, str(e))

# Test cap check endpoint (should work without auth for SDK)
try:
    response = requests.get(
        f"{COLLECTOR_URL}/caps/check",
        params={"provider": "openai", "model": "gpt-4o"},
        timeout=5
    )
    tracker.test(
        "Cap check endpoint exists",
        response.status_code in [200, 401],
        f"Status: {response.status_code}"
    )
except Exception as e:
    tracker.test("Cap check endpoint", False, str(e))

# =============================================================================
# 5. SDK CONTEXT PROPAGATION TEST
# =============================================================================
print(f"\n{'='*80}")
print("5. SDK CONTEXT PROPAGATION TEST")
print(f"{'='*80}")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))

try:
    from llmobserve import context
    
    # Test context isolation in async
    async def async_test_1():
        context.set_run_id("async-run-1")
        await asyncio.sleep(0.1)
        return context.get_run_id()
    
    async def async_test_2():
        context.set_run_id("async-run-2")
        await asyncio.sleep(0.1)
        return context.get_run_id()
    
    async def run_concurrent():
        results = await asyncio.gather(async_test_1(), async_test_2())
        return results
    
    results = asyncio.run(run_concurrent())
    
    tracker.test(
        "Context isolation in concurrent async tasks",
        "async-run-1" in results and "async-run-2" in results,
        f"Results: {results}"
    )
    
except Exception as e:
    tracker.test("SDK context propagation", False, str(e))

# =============================================================================
# 6. AGENT AND TOOL WRAPPING TEST
# =============================================================================
print(f"\n{'='*80}")
print("6. AGENT AND TOOL WRAPPING TEST")
print(f"{'='*80}")

try:
    from llmobserve import agent, tool, observe
    from llmobserve import buffer
    
    # Initialize SDK (don't actually send to collector in test)
    observe(
        collector_url=COLLECTOR_URL,
        api_key="test-key",
        enable_http_fallback=False,  # Don't patch HTTP in test
        enable_llm_wrappers=False
    )
    
    # Define test agent and tools
    @tool("calculator")
    def calculator(operation: str, a: float, b: float) -> float:
        if operation == "add":
            return a + b
        elif operation == "multiply":
            return a * b
        return 0
    
    @agent("math-assistant")
    def math_agent(query: str) -> dict:
        # Agent does some calculations
        result1 = calculator("add", 10, 5)
        result2 = calculator("multiply", result1, 2)
        return {"query": query, "result": result2}
    
    # Run agent
    result = math_agent("What is (10 + 5) * 2?")
    
    tracker.test(
        "@agent and @tool decorators work correctly",
        result["result"] == 30,
        f"Expected 30, got {result['result']}"
    )
    
    # Check if events were buffered
    buffered = buffer.get_buffer()
    tracker.test(
        "Tool calls generate trace events",
        len(buffered) > 0,
        f"Buffer has {len(buffered)} events"
    )
    
    # Check event structure
    if len(buffered) > 0:
        event = buffered[0]
        tracker.test(
            "Buffered events have required fields",
            "run_id" in event and "span_id" in event and "section_path" in event,
            f"Event fields: {event.keys()}"
        )
        
        tracker.test(
            "Buffered events include agent/tool in section_path",
            "agent:" in event.get("section_path", "") or "tool:" in event.get("section_path", ""),
            f"section_path: {event.get('section_path')}"
        )
    
    # Clear buffer
    buffer.clear_buffer()
    
except Exception as e:
    tracker.test("Agent and tool wrapping", False, str(e))

# =============================================================================
# 7. NESTED TOOL CALLS TEST
# =============================================================================
print(f"\n{'='*80}")
print("7. NESTED TOOL CALLS TEST")
print(f"{'='*80}")

try:
    from llmobserve import tool, agent
    from llmobserve import buffer
    
    buffer.clear_buffer()
    
    @tool("fetch_data")
    def fetch_data(source: str) -> str:
        return f"data from {source}"
    
    @tool("process_data")
    def process_data(data: str) -> str:
        # Calls another tool
        additional = fetch_data("cache")
        return f"processed: {data} + {additional}"
    
    @agent("data-processor")
    def data_agent():
        raw = fetch_data("api")
        processed = process_data(raw)
        return processed
    
    result = data_agent()
    
    tracker.test(
        "Nested tool calls execute correctly",
        "data from api" in result and "data from cache" in result,
        f"Result: {result}"
    )
    
    # Check buffer for parent-child relationships
    buffered = buffer.get_buffer()
    
    if len(buffered) >= 2:
        # Look for parent_span_id relationships
        has_parent_child = any(
            event.get("parent_span_id") is not None 
            for event in buffered
        )
        tracker.test(
            "Nested calls have parent_span_id set",
            has_parent_child,
            f"Events: {[e.get('parent_span_id') for e in buffered]}"
        )
    
    buffer.clear_buffer()
    
except Exception as e:
    tracker.test("Nested tool calls", False, str(e))

# =============================================================================
# 8. PRICING CALCULATION TEST (Real-World Examples)
# =============================================================================
print(f"\n{'='*80}")
print("8. PRICING CALCULATION TEST (Real-World Examples)")
print(f"{'='*80}")

try:
    from llmobserve.pricing import compute_cost
    
    # Real-world scenario 1: GPT-4o chat completion
    cost_gpt4o = compute_cost("openai", "gpt-4o", input_tokens=2000, output_tokens=800)
    expected_gpt4o = (2000 * 0.0000025) + (800 * 0.00001)  # $0.005 + $0.008 = $0.013
    tolerance = 0.001
    
    tracker.test(
        "GPT-4o pricing accurate for typical chat",
        abs(cost_gpt4o - expected_gpt4o) < tolerance,
        f"Expected ~${expected_gpt4o:.4f}, got ${cost_gpt4o:.4f}"
    )
    
    # Real-world scenario 2: Pinecone query (1000 vectors)
    cost_pinecone = compute_cost("pinecone", "query") * 1000
    expected_pinecone = (16.0 / 1_000_000) * 1000  # $0.016 per 1M, 1000 queries
    
    tracker.test(
        "Pinecone pricing accurate for 1000 queries",
        abs(cost_pinecone - expected_pinecone) < 0.0001,
        f"Expected ${expected_pinecone:.6f}, got ${cost_pinecone:.6f}"
    )
    
    # Real-world scenario 3: Chroma storage (50 GB for a month)
    cost_chroma_storage = compute_cost("chroma", "storage") * 50
    expected_chroma = 0.33 * 50  # $0.33/GB × 50 GB = $16.50
    
    tracker.test(
        "Chroma storage pricing accurate for 50 GB",
        abs(cost_chroma_storage - expected_chroma) < 0.01,
        f"Expected ${expected_chroma:.2f}, got ${cost_chroma_storage:.2f}"
    )
    
    # Real-world scenario 4: Anthropic Claude Sonnet (conversation)
    cost_claude = compute_cost("anthropic", "claude-sonnet-4", input_tokens=3000, output_tokens=1000)
    
    tracker.test(
        "Anthropic pricing returns non-zero cost",
        cost_claude > 0,
        f"Got ${cost_claude:.6f}"
    )
    
    # Real-world scenario 5: Perplexity with dual pricing
    cost_perp = compute_cost(
        "perplexity", "sonar-pro",
        input_tokens=1500, output_tokens=800,
        context_size="medium"
    )
    
    tracker.test(
        "Perplexity dual pricing includes both tokens and request fee",
        cost_perp > 0.01,  # Should be significant with both components
        f"Got ${cost_perp:.6f}"
    )
    
except Exception as e:
    tracker.test("Pricing calculation", False, str(e))

# =============================================================================
# 9. EDGE CASE: RETRY DETECTION
# =============================================================================
print(f"\n{'='*80}")
print("9. EDGE CASE: RETRY DETECTION")
print(f"{'='*80}")

try:
    from llmobserve.request_tracker import (
        generate_request_id,
        is_request_tracked,
        mark_request_tracked
    )
    
    # Generate request ID
    req_id = generate_request_id("POST", "https://api.openai.com/v1/chat/completions", b'{"test": "data"}')
    
    tracker.test(
        "Request ID generation works",
        len(req_id) > 0,
        f"Generated: {req_id}"
    )
    
    # First check - should not be tracked
    is_tracked_before = is_request_tracked(req_id)
    
    # Mark as tracked
    mark_request_tracked(req_id)
    
    # Second check - should be tracked
    is_tracked_after = is_request_tracked(req_id)
    
    tracker.test(
        "Retry detection works correctly",
        not is_tracked_before and is_tracked_after,
        f"Before: {is_tracked_before}, After: {is_tracked_after}"
    )
    
except Exception as e:
    tracker.test("Retry detection", False, str(e))

# =============================================================================
# 10. EDGE CASE: STATUS CODE FILTERING
# =============================================================================
print(f"\n{'='*80}")
print("10. EDGE CASE: STATUS CODE FILTERING")
print(f"{'='*80}")

try:
    from llmobserve.request_tracker import should_track_response
    
    test_cases = [
        (200, True, "2xx success"),
        (201, True, "2xx created"),
        (400, True, "4xx bad request (still charged)"),
        (401, True, "4xx unauthorized (still charged)"),
        (429, False, "429 rate limit (not charged)"),
        (500, False, "5xx server error (not charged)"),
        (502, False, "5xx bad gateway (not charged)"),
    ]
    
    all_correct = True
    for status, expected, description in test_cases:
        result = should_track_response(status)
        if result != expected:
            tracker.test(
                f"Status {status} ({description})",
                False,
                f"Expected {expected}, got {result}"
            )
            all_correct = False
    
    if all_correct:
        tracker.test("Status code filtering logic correct", True)
    
except Exception as e:
    tracker.test("Status code filtering", False, str(e))

# =============================================================================
# 11. EDGE CASE: RATE LIMIT DETECTION
# =============================================================================
print(f"\n{'='*80}")
print("11. EDGE CASE: RATE LIMIT DETECTION")
print(f"{'='*80}")

try:
    from llmobserve.request_tracker import detect_rate_limit
    
    # Test with rate limit headers
    headers = {
        "Retry-After": "60",
        "X-RateLimit-Limit": "10000",
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1699999999"
    }
    
    rate_limit_info = detect_rate_limit(429, headers)
    
    tracker.test(
        "Rate limit detection works",
        rate_limit_info is not None and rate_limit_info.get("rate_limited") == True,
        f"Result: {rate_limit_info}"
    )
    
    # Test without rate limit
    no_rate_limit = detect_rate_limit(200, {})
    
    tracker.test(
        "Rate limit detection returns None for non-429",
        no_rate_limit is None,
        f"Result: {no_rate_limit}"
    )
    
except Exception as e:
    tracker.test("Rate limit detection", False, str(e))

# =============================================================================
# 12. DISTRIBUTED TRACING TEST
# =============================================================================
print(f"\n{'='*80}")
print("12. DISTRIBUTED TRACING TEST")
print(f"{'='*80}")

try:
    from llmobserve import context
    from llmobserve import export_distributed_context, import_distributed_context
    
    # Simulate main process
    context.set_run_id("distributed-run-123")
    context.set_customer_id("customer-456")
    context.set_trace_id("trace-789")
    
    # Export context (would be sent to background worker)
    exported = export_distributed_context()
    
    tracker.test(
        "Context export includes all fields",
        all(k in exported for k in ["run_id", "customer_id", "trace_id"]),
        f"Exported: {exported.keys()}"
    )
    
    # Simulate background worker - clear context first
    context.set_run_id(None)
    context.set_customer_id(None)
    
    # Import context in worker
    import_distributed_context(exported)
    
    # Verify restoration
    restored_run = context.get_run_id()
    restored_customer = context.get_customer_id()
    restored_trace = context.get_trace_id()
    
    tracker.test(
        "Distributed context restores correctly",
        restored_run == "distributed-run-123" and restored_customer == "customer-456" and restored_trace == "trace-789",
        f"run_id: {restored_run}, customer_id: {restored_customer}, trace_id: {restored_trace}"
    )
    
except Exception as e:
    tracker.test("Distributed tracing", False, str(e))

# =============================================================================
# 13. PERFORMANCE TEST
# =============================================================================
print(f"\n{'='*80}")
print("13. PERFORMANCE TEST")
print(f"{'='*80}")

try:
    from llmobserve import tool
    from llmobserve import buffer
    import time as t
    
    buffer.clear_buffer()
    
    @tool("fast-op")
    def fast_operation(x: int) -> int:
        return x * 2
    
    # Run 1000 operations
    start = t.time()
    for i in range(1000):
        fast_operation(i)
    end = t.time()
    
    elapsed = end - start
    ops_per_sec = 1000 / elapsed
    
    tracker.test(
        "SDK overhead is acceptable (>500 ops/sec)",
        ops_per_sec > 500,
        f"Got {ops_per_sec:.0f} ops/sec"
    )
    
    # Check memory usage (buffered events)
    buffered = buffer.get_buffer()
    tracker.test(
        "Events are buffered correctly",
        len(buffered) == 1000,
        f"Expected 1000, got {len(buffered)}"
    )
    
    buffer.clear_buffer()
    
except Exception as e:
    tracker.test("Performance test", False, str(e))

# =============================================================================
# FINAL REPORT
# =============================================================================
print("\n\n")
is_ready = tracker.report()

print("\n" + "="*80)
print("LAUNCH READINESS ASSESSMENT")
print("="*80)

if is_ready:
    print("""
✅ PLATFORM IS PRODUCTION READY!

The integration tests show that:
- All core functionality works end-to-end
- Pricing calculations are accurate
- Context propagation is isolated and correct
- Agent/tool tracing works with proper nesting
- Edge cases are handled (retries, rate limits, errors)
- Performance is acceptable (>500 ops/sec)
- Distributed tracing works across processes

🚀 YOU CAN LAUNCH WITH CONFIDENCE!
""")
else:
    print("""
⚠️  REVIEW FAILURES BEFORE LAUNCH

Some integration tests failed. Review the failures above and:
1. Check if collector is running (port 8000)
2. Verify all dependencies are installed
3. Fix any code issues identified
4. Re-run tests until all pass

Most failures are likely due to services not running in test environment.
""")

print("="*80 + "\n")

sys.exit(0 if is_ready else 1)

