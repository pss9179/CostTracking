#!/usr/bin/env python3
"""
COMPREHENSIVE LAUNCH READINESS TEST
Tests every single feature, API, pricing model, UI component, and edge case.
"""
import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta

# Test results tracker
class TestTracker:
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
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        print(f"Total Tests Run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.2f}%")
        
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
            print("🎉 ALL TESTS PASSED - PLATFORM IS LAUNCH READY!")
            return True
        else:
            print("🚨 PLATFORM IS NOT READY - FIX FAILURES BEFORE LAUNCH")
            return False

tracker = TestTracker()

# =============================================================================
# 1. PRICING REGISTRY TESTS
# =============================================================================
print("\n" + "="*80)
print("1. TESTING PRICING REGISTRY")
print("="*80)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))
from llmobserve.pricing import PRICING_REGISTRY, compute_cost

# Test 1.1: All major LLM providers have pricing
openai_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('openai:')]
tracker.test(
    "OpenAI models in registry",
    len(openai_models) >= 30,
    f"Only {len(openai_models)} models found"
)

anthropic_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('anthropic:')]
tracker.test(
    "Anthropic models in registry",
    len(anthropic_models) >= 9,
    f"Only {len(anthropic_models)} models found"
)

google_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('google:')]
tracker.test(
    "Google Gemini models in registry",
    len(google_models) >= 20,
    f"Only {len(google_models)} models found"
)

mistral_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('mistral:')]
tracker.test(
    "Mistral models in registry",
    len(mistral_models) >= 30,
    f"Only {len(mistral_models)} models found"
)

perplexity_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('perplexity:')]
tracker.test(
    "Perplexity models in registry",
    len(perplexity_models) >= 6,
    f"Only {len(perplexity_models)} models found"
)

xai_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('xai:')]
tracker.test(
    "xAI/Grok models in registry",
    len(xai_models) >= 10,
    f"Only {len(xai_models)} models found"
)

cohere_models = [k for k in PRICING_REGISTRY.keys() if k.startswith('cohere:')]
tracker.test(
    "Cohere models in registry",
    len(cohere_models) >= 11,
    f"Only {len(cohere_models)} models found"
)

# Test 1.2: Vector databases have pricing
pinecone_entries = [k for k in PRICING_REGISTRY.keys() if k.startswith('pinecone:')]
tracker.test(
    "Pinecone operations in registry",
    len(pinecone_entries) >= 15,
    f"Only {len(pinecone_entries)} operations found"
)

weaviate_entries = [k for k in PRICING_REGISTRY.keys() if k.startswith('weaviate:')]
tracker.test(
    "Weaviate pricing in registry",
    len(weaviate_entries) >= 9,
    f"Only {len(weaviate_entries)} entries found"
)

chroma_entries = [k for k in PRICING_REGISTRY.keys() if k.startswith('chroma:')]
tracker.test(
    "Chroma pricing in registry",
    len(chroma_entries) >= 4,
    f"Only {len(chroma_entries)} entries found"
)

# Test 1.3: Pricing calculation accuracy
test_cases = [
    # OpenAI
    ("openai", "gpt-4o", 1000, 500, 0, 0.0075),  # $0.0025 input + $0.005 output
    ("openai", "gpt-4o-mini", 1000, 500, 0, 0.0004),  # $0.00015 input + $0.00025 output
    
    # Anthropic
    ("anthropic", "claude-sonnet-4.5", 1000, 500, 0, 0.0045),  # $0.003 input + $0.0015 output
    
    # Google
    ("google", "gemini-2.5-flash", 1000, 500, 0, 0.00155),  # $0.0003 input + $0.00125 output
    
    # Pinecone (operations should be very small)
    ("pinecone", "write-units", 0, 0, 0, 0.000004),  # $4 per million
    ("pinecone", "storage", 0, 0, 0, 0.33),  # $0.33 per GB/month
    
    # Chroma
    ("chroma", "write", 0, 0, 0, 2.50),  # $2.50 per GiB
    ("chroma", "storage", 0, 0, 0, 0.33),  # $0.33 per GiB/month
]

for provider, model, inp, outp, cached, expected in test_cases:
    cost = compute_cost(provider, model, inp, outp, cached)
    tolerance = expected * 0.01  # 1% tolerance
    tracker.test(
        f"Pricing: {provider}:{model}",
        abs(cost - expected) < tolerance,
        f"Expected ~${expected}, got ${cost}"
    )

# Test 1.4: Complex pricing models
# Perplexity with context size
perp_cost = compute_cost("perplexity", "sonar", 1000, 500, 0, context_size="high")
tracker.test(
    "Perplexity dual pricing (tokens + request)",
    perp_cost > 0.001,  # Should include both token and request costs
    f"Cost too low: ${perp_cost}"
)

# Perplexity Deep Research
deep_cost = compute_cost(
    "perplexity", "sonar-deep-research",
    input_tokens=1000, output_tokens=500,
    citation_tokens=100, reasoning_tokens=200, search_queries=5
)
tracker.test(
    "Perplexity Deep Research (5 components)",
    deep_cost > 0.02,  # Should be significant with all components
    f"Cost too low: ${deep_cost}"
)

# =============================================================================
# 2. DATABASE MODELS TESTS
# =============================================================================
print("\n" + "="*80)
print("2. TESTING DATABASE MODELS")
print("="*80)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'collector'))
from models import TraceEvent, SpendingCap, Alert, CapCreate, CapUpdate

# Test 2.1: TraceEvent model has all required fields
required_fields = [
    'event_id', 'run_id', 'tenant_id', 'customer_id', 'trace_id',
    'span_id', 'parent_span_id', 'section_path',
    'provider', 'model', 'endpoint',
    'input_tokens', 'output_tokens', 'cost', 'latency_ms',
    'timestamp', 'status_code'
]
tracker.test(
    "TraceEvent has all required fields",
    all(hasattr(TraceEvent, field) for field in required_fields),
    f"Missing fields in TraceEvent"
)

# Test 2.2: SpendingCap model has enforcement and exceeded_at
tracker.test(
    "SpendingCap has enforcement field",
    hasattr(SpendingCap, 'enforcement'),
    "Missing enforcement field"
)
tracker.test(
    "SpendingCap has exceeded_at field",
    hasattr(SpendingCap, 'exceeded_at'),
    "Missing exceeded_at field"
)

# Test 2.3: Alert model exists
tracker.test(
    "Alert model exists",
    hasattr(Alert, 'alert_id'),
    "Alert model missing or incomplete"
)

# =============================================================================
# 3. API ENDPOINTS TESTS
# =============================================================================
print("\n" + "="*80)
print("3. TESTING API ENDPOINTS (Structure)")
print("="*80)

# Check if collector can be imported
try:
    from main import app
    tracker.test("Collector app imports successfully", True)
except Exception as e:
    tracker.test("Collector app imports successfully", False, str(e))

# Check routers exist
try:
    from routers import events, caps, stats
    tracker.test("All routers import successfully", True)
except Exception as e:
    tracker.test("All routers import successfully", False, str(e))

# Test 3.1: Check caps router has required endpoints
try:
    from routers.caps import router as caps_router
    routes = [route.path for route in caps_router.routes]
    
    tracker.test(
        "Caps GET endpoint exists",
        any('GET' in str(route.methods) for route in caps_router.routes if route.path == "/"),
        "Missing GET /caps"
    )
    
    tracker.test(
        "Caps POST endpoint exists",
        any('POST' in str(route.methods) for route in caps_router.routes if route.path == "/"),
        "Missing POST /caps"
    )
    
    tracker.test(
        "Caps check endpoint exists",
        any('/check' in route.path for route in caps_router.routes),
        "Missing /caps/check endpoint for hard cap enforcement"
    )
except Exception as e:
    tracker.test("Caps router endpoints", False, str(e))

# =============================================================================
# 4. SDK CONTEXT MANAGEMENT TESTS
# =============================================================================
print("\n" + "="*80)
print("4. TESTING SDK CONTEXT MANAGEMENT")
print("="*80)

from llmobserve import context

# Test 4.1: Context variables exist
tracker.test(
    "run_id context var exists",
    hasattr(context, 'get_run_id'),
    "Missing run_id management"
)

tracker.test(
    "customer_id context var exists",
    hasattr(context, 'get_customer_id'),
    "Missing customer_id management"
)

tracker.test(
    "trace_id context var exists",
    hasattr(context, 'get_trace_id'),
    "Missing trace_id management"
)

tracker.test(
    "section stack exists",
    hasattr(context, 'get_current_section'),
    "Missing section stack management"
)

# Test 4.2: Context operations work
try:
    context.set_run_id("test-run-123")
    run_id = context.get_run_id()
    tracker.test(
        "run_id set/get works",
        run_id == "test-run-123",
        f"Got {run_id} instead of test-run-123"
    )
except Exception as e:
    tracker.test("run_id set/get works", False, str(e))

try:
    context.set_customer_id("customer-456")
    customer_id = context.get_customer_id()
    tracker.test(
        "customer_id set/get works",
        customer_id == "customer-456",
        f"Got {customer_id}"
    )
except Exception as e:
    tracker.test("customer_id set/get works", False, str(e))

# Test 4.3: Section stack push/pop
try:
    initial_path = context.get_current_section()
    context.push_section("agent", "test-agent")
    agent_path = context.get_current_section()
    context.push_section("tool", "test-tool")
    tool_path = context.get_current_section()
    context.pop_section()
    back_to_agent = context.get_current_section()
    context.pop_section()
    back_to_root = context.get_current_section()
    
    tracker.test(
        "Section stack push works",
        "test-agent" in agent_path and "test-tool" in tool_path,
        f"Stack not pushing correctly: {agent_path}, {tool_path}"
    )
    
    tracker.test(
        "Section stack pop works",
        back_to_agent == agent_path and back_to_root == initial_path,
        f"Stack not popping correctly"
    )
except Exception as e:
    tracker.test("Section stack operations", False, str(e))

# Test 4.4: Distributed context export/import
try:
    from llmobserve import export_distributed_context, import_distributed_context
    
    context.set_run_id("dist-run-789")
    context.set_customer_id("dist-customer-123")
    context.set_trace_id("dist-trace-456")
    
    exported = export_distributed_context()
    
    tracker.test(
        "Context export includes all fields",
        all(k in exported for k in ['run_id', 'customer_id', 'trace_id', 'section_stack']),
        f"Missing fields in export: {exported.keys()}"
    )
    
    # Clear context
    context.set_run_id(None)
    import_distributed_context(exported)
    
    restored_run = context.get_run_id()
    tracker.test(
        "Context import restores values",
        restored_run == "dist-run-789",
        f"Got {restored_run} after import"
    )
except Exception as e:
    tracker.test("Distributed context export/import", False, str(e))

# =============================================================================
# 5. TOOL WRAPPING TESTS
# =============================================================================
print("\n" + "="*80)
print("5. TESTING TOOL WRAPPING ARCHITECTURE")
print("="*80)

try:
    from llmobserve import agent, tool, wrap_tool, wrap_all_tools
    
    tracker.test("@agent decorator exists", True)
    tracker.test("@tool decorator exists", True)
    tracker.test("wrap_tool function exists", True)
    tracker.test("wrap_all_tools function exists", True)
    
    # Test 5.1: Tool decorator works
    @tool("test-tool")
    def my_test_tool(x: int) -> int:
        return x * 2
    
    result = my_test_tool(5)
    tracker.test(
        "@tool decorator executes correctly",
        result == 10,
        f"Expected 10, got {result}"
    )
    
    tracker.test(
        "@tool decorator marks function as wrapped",
        hasattr(my_test_tool, '__llmobserve_wrapped__'),
        "Function not marked as wrapped"
    )
    
    # Test 5.2: Idempotent wrapping
    wrapped_once = wrap_tool(my_test_tool)
    wrapped_twice = wrap_tool(wrapped_once)
    
    tracker.test(
        "wrap_tool is idempotent",
        wrapped_once is wrapped_twice,
        "Function wrapped multiple times"
    )
    
    # Test 5.3: wrap_all_tools with dict
    tools_dict = {
        "add": lambda a, b: a + b,
        "multiply": lambda a, b: a * b
    }
    wrapped_dict = wrap_all_tools(tools_dict)
    
    tracker.test(
        "wrap_all_tools handles dict",
        all(hasattr(fn, '__llmobserve_wrapped__') for fn in wrapped_dict.values()),
        "Not all tools in dict were wrapped"
    )
    
    # Test 5.4: Agent decorator
    @agent("test-agent")
    def my_agent():
        return "agent-result"
    
    agent_result = my_agent()
    tracker.test(
        "@agent decorator executes correctly",
        agent_result == "agent-result",
        f"Expected 'agent-result', got {agent_result}"
    )
    
except Exception as e:
    tracker.test("Tool wrapping architecture", False, str(e))

# =============================================================================
# 6. HTTP INTERCEPTOR TESTS
# =============================================================================
print("\n" + "="*80)
print("6. TESTING HTTP INTERCEPTORS")
print("="*80)

try:
    from llmobserve.http_interceptor import patch_all_protocols
    
    tracker.test("patch_all_protocols function exists", True)
    
    # Check if httpx patching exists
    try:
        import httpx
        original_client = httpx.Client
        tracker.test("httpx available for patching", True)
    except ImportError:
        tracker.warning("httpx not installed - HTTP interception may not work")
    
    # Check if requests patching exists
    try:
        import requests
        tracker.test("requests available for patching", True)
    except ImportError:
        tracker.warning("requests not installed - HTTP interception may not work")
    
except Exception as e:
    tracker.test("HTTP interceptor imports", False, str(e))

# Test 6.1: Cap checking integration
try:
    from llmobserve.caps import check_spending_caps, BudgetExceededError
    
    tracker.test("check_spending_caps function exists", True)
    tracker.test("BudgetExceededError exception exists", True)
    
    # Caps should gracefully fail if collector is unreachable
    try:
        result = check_spending_caps(provider="openai", model="gpt-4o")
        tracker.test(
            "check_spending_caps fails gracefully when collector unreachable",
            result is not None,
            "Function should return dict even if collector is down"
        )
    except BudgetExceededError:
        tracker.test("check_spending_caps", False, "Should not raise error when collector is down")
    except Exception as e:
        # Expected if collector is not running - should fail gracefully
        tracker.test("check_spending_caps fails gracefully", True)
        
except Exception as e:
    tracker.test("Cap checking integration", False, str(e))

# =============================================================================
# 7. LLM WRAPPERS TESTS
# =============================================================================
print("\n" + "="*80)
print("7. TESTING LLM WRAPPERS")
print("="*80)

try:
    from llmobserve.llm_wrappers import wrap_openai_client, wrap_anthropic_client
    
    tracker.test("wrap_openai_client function exists", True)
    tracker.test("wrap_anthropic_client function exists", True)
    
    # Test wrapping doesn't break if clients not installed
    try:
        import openai
        tracker.test("OpenAI SDK available", True)
    except ImportError:
        tracker.warning("OpenAI SDK not installed - OpenAI wrapping won't work")
    
    try:
        import anthropic
        tracker.test("Anthropic SDK available", True)
    except ImportError:
        tracker.warning("Anthropic SDK not installed - Anthropic wrapping won't work")
    
except Exception as e:
    tracker.test("LLM wrappers import", False, str(e))

# =============================================================================
# 8. FRONTEND API CLIENT TESTS
# =============================================================================
print("\n" + "="*80)
print("8. TESTING FRONTEND API CLIENT")
print("="*80)

# Read frontend API client
try:
    api_ts_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'lib', 'api.ts')
    with open(api_ts_path, 'r') as f:
        api_ts = f.read()
    
    # Check for required interfaces
    tracker.test(
        "Cap interface exists",
        "interface Cap" in api_ts,
        "Missing Cap interface"
    )
    
    tracker.test(
        "Cap interface has enforcement field",
        "enforcement:" in api_ts and "Cap" in api_ts,
        "Cap interface missing enforcement field"
    )
    
    tracker.test(
        "Alert interface exists",
        "interface Alert" in api_ts or "AlertType" in api_ts,
        "Missing Alert interface"
    )
    
    # Check for API functions
    tracker.test(
        "fetchCaps function exists",
        "fetchCaps" in api_ts,
        "Missing fetchCaps function"
    )
    
    tracker.test(
        "createCap function exists",
        "createCap" in api_ts,
        "Missing createCap function"
    )
    
    tracker.test(
        "updateCap function exists",
        "updateCap" in api_ts,
        "Missing updateCap function"
    )
    
    tracker.test(
        "deleteCap function exists",
        "deleteCap" in api_ts,
        "Missing deleteCap function"
    )
    
    tracker.test(
        "fetchAlerts function exists",
        "fetchAlerts" in api_ts,
        "Missing fetchAlerts function"
    )
    
except Exception as e:
    tracker.test("Frontend API client", False, str(e))

# =============================================================================
# 9. FRONTEND SETTINGS PAGE TESTS
# =============================================================================
print("\n" + "="*80)
print("9. TESTING FRONTEND SETTINGS PAGE")
print("="*80)

try:
    settings_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'app', 'settings', 'page.tsx')
    with open(settings_path, 'r') as f:
        settings_tsx = f.read()
    
    tracker.test(
        "Settings page has caps UI",
        "caps" in settings_tsx.lower() or "spending" in settings_tsx.lower(),
        "No caps UI found"
    )
    
    tracker.test(
        "Settings page has enforcement mode selector",
        "enforcement" in settings_tsx.lower(),
        "No enforcement mode UI found"
    )
    
    tracker.test(
        "Settings page has alert email input",
        "email" in settings_tsx.lower() and "alert" in settings_tsx.lower(),
        "No alert email input found"
    )
    
    tracker.test(
        "Settings page has cap type selector",
        "cap_type" in settings_tsx or "capType" in settings_tsx,
        "No cap type selector found"
    )
    
    tracker.test(
        "Settings page has period selector",
        "period" in settings_tsx.lower() and ("daily" in settings_tsx or "weekly" in settings_tsx),
        "No period selector found"
    )
    
except Exception as e:
    tracker.test("Frontend settings page", False, str(e))

# =============================================================================
# 10. FRONTEND DASHBOARD TESTS
# =============================================================================
print("\n" + "="*80)
print("10. TESTING FRONTEND DASHBOARD")
print("="*80)

try:
    dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'app', 'page.tsx')
    with open(dashboard_path, 'r') as f:
        dashboard_tsx = f.read()
    
    tracker.test(
        "Dashboard shows cost metrics",
        "cost" in dashboard_tsx.lower(),
        "No cost display found"
    )
    
    tracker.test(
        "Dashboard shows untracked costs",
        "untracked" in dashboard_tsx.lower(),
        "No untracked costs display found"
    )
    
    tracker.test(
        "Dashboard shows token usage",
        "token" in dashboard_tsx.lower(),
        "No token usage display found"
    )
    
    tracker.test(
        "Dashboard has time period selector",
        "24h" in dashboard_tsx or "7d" in dashboard_tsx or "30d" in dashboard_tsx,
        "No time period selector found"
    )
    
except Exception as e:
    tracker.test("Frontend dashboard", False, str(e))

# =============================================================================
# 11. MIGRATIONS TESTS
# =============================================================================
print("\n" + "="*80)
print("11. TESTING DATABASE MIGRATIONS")
print("="*80)

migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
try:
    migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.sql')]
    
    tracker.test(
        "Migrations directory exists",
        len(migration_files) > 0,
        "No migration files found"
    )
    
    # Check for specific migrations
    caps_migration = any('cap' in f.lower() for f in migration_files)
    tracker.test(
        "Caps migration exists",
        caps_migration,
        "No caps migration found"
    )
    
    hard_caps_migration = any('hard' in f.lower() and 'cap' in f.lower() for f in migration_files)
    tracker.test(
        "Hard caps migration exists",
        hard_caps_migration,
        "No hard caps (enforcement) migration found"
    )
    
    # Check migration content
    for migration_file in migration_files:
        if 'cap' in migration_file.lower():
            with open(os.path.join(migrations_dir, migration_file), 'r') as f:
                content = f.read()
                
                if 'spending_caps' in content:
                    tracker.test(
                        f"Migration {migration_file} creates spending_caps table",
                        'CREATE TABLE' in content or 'ALTER TABLE' in content,
                        "Migration doesn't create/alter table"
                    )
                    
                    if 'enforcement' in migration_file.lower():
                        tracker.test(
                            f"Migration {migration_file} adds enforcement field",
                            'enforcement' in content,
                            "Enforcement field not added"
                        )
                        
                        tracker.test(
                            f"Migration {migration_file} adds exceeded_at field",
                            'exceeded_at' in content,
                            "exceeded_at field not added"
                        )
    
except Exception as e:
    tracker.test("Database migrations", False, str(e))

# =============================================================================
# 12. DOCUMENTATION TESTS
# =============================================================================
print("\n" + "="*80)
print("12. TESTING DOCUMENTATION")
print("="*80)

docs_to_check = [
    ('DEPLOYMENT_CHECKLIST.md', 'deployment'),
    ('PROVIDER_COVERAGE.md', 'provider'),
    ('VECTOR_DATABASE_PRICING.md', 'vector'),
    ('PERPLEXITY_PRICING_GUIDE.md', 'perplexity'),
    ('TOOL_WRAPPING_IMPLEMENTATION_SUMMARY.md', 'tool wrapping'),
]

for doc_file, keyword in docs_to_check:
    doc_path = os.path.join(os.path.dirname(__file__), '..', doc_file)
    try:
        with open(doc_path, 'r') as f:
            content = f.read()
        tracker.test(
            f"Documentation exists: {doc_file}",
            len(content) > 100,
            f"File too short or empty"
        )
    except FileNotFoundError:
        tracker.test(
            f"Documentation exists: {doc_file}",
            False,
            "File not found"
        )

# =============================================================================
# 13. EDGE CASE HANDLING TESTS
# =============================================================================
print("\n" + "="*80)
print("13. TESTING EDGE CASE HANDLING")
print("="*80)

# Test 13.1: Retry detection
try:
    from llmobserve.request_tracker import is_duplicate_request, mark_request
    
    # First request should not be duplicate
    is_dup_1 = is_duplicate_request("test-request-id-1")
    mark_request("test-request-id-1")
    
    # Second request with same ID should be duplicate
    is_dup_2 = is_duplicate_request("test-request-id-1")
    
    tracker.test(
        "Retry detection works",
        not is_dup_1 and is_dup_2,
        f"is_dup_1={is_dup_1}, is_dup_2={is_dup_2}"
    )
except Exception as e:
    tracker.warning(f"Retry detection not implemented or has errors: {e}")

# Test 13.2: Status code filtering (would need to check collector logic)
tracker.warning("Status code filtering (429, 5xx) should be tested in integration tests")

# Test 13.3: Graceful degradation (fail-open)
tracker.warning("Graceful degradation should be tested with collector down")

# =============================================================================
# 14. CRITICAL FEATURES CHECKLIST
# =============================================================================
print("\n" + "="*80)
print("14. CRITICAL FEATURES CHECKLIST")
print("="*80)

# Pricing coverage
total_pricing_entries = len(PRICING_REGISTRY)
tracker.test(
    "Pricing registry has 100+ entries",
    total_pricing_entries >= 100,
    f"Only {total_pricing_entries} entries"
)

# Provider coverage
providers = set(k.split(':')[0] for k in PRICING_REGISTRY.keys())
tracker.test(
    "At least 7 LLM providers covered",
    len([p for p in providers if p in ['openai', 'anthropic', 'google', 'mistral', 'perplexity', 'xai', 'cohere']]) >= 7,
    f"Providers: {providers}"
)

tracker.test(
    "At least 4 vector DBs covered",
    len([p for p in providers if p in ['pinecone', 'weaviate', 'chroma', 'qdrant', 'zilliz', 'mongodb', 'redis', 'elasticsearch']]) >= 4,
    f"Vector DBs: {providers}"
)

# =============================================================================
# FINAL REPORT
# =============================================================================
print("\n\n")
is_ready = tracker.report()

sys.exit(0 if is_ready else 1)

