# Semantic Sections Guide

## Overview

Semantic sections enable hierarchical cost visualization and debugging across agent, tool, and multi-step logic. They allow you to trace nested execution flows and understand exactly where costs are incurred in complex LLM applications.

## Key Concepts

### Semantic Labels

Use semantic prefixes to categorize your traced operations:

- **`agent:<name>`** — For orchestrators or autonomous agents
- **`tool:<name>`** — For external API or function calls  
- **`step:<name>`** — For multi-step logic or workflows

### Hierarchical Tracing

Sections can be nested to create parent-child relationships. The full path is captured as `section_path` (e.g., `agent:researcher/tool:web_search/step:analyze`).

### Backward Compatibility

**Important:** Hierarchical tracing is **opt-in**. If you don't use nested sections, your traces remain flat with no overhead or schema changes to worry about.

## Usage

### Basic Section Context Manager

The simplest way to create hierarchical traces is with the `section()` context manager:

```python
from llmobserve import observe, section
import openai

# Initialize tracking
observe("http://localhost:8000")

# Create nested sections
with section("agent:researcher"):
    # Agent-level logic
    with section("tool:web_search"):
        # Web search call (automatically tracked)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Search for..."}]
        )
    
    with section("step:analyze_results"):
        # Analysis step
        analysis = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Analyze..."}]
        )
```

**Result:** Events are traced with `section_path`:
- `agent:researcher/tool:web_search`
- `agent:researcher/step:analyze_results`

### Decorator Helper (Optional)

For cleaner code, use the `@trace()` decorator:

```python
from llmobserve import trace

@trace(agent="researcher")
async def research_agent(query: str):
    """Entire function is traced as agent:researcher"""
    result = await search_web(query)
    return await analyze(result)

@trace(tool="web_search")
async def search_web(query: str):
    """Traced as tool:web_search"""
    response = client.chat.completions.create(...)
    return response

@trace(step="analyze")
async def analyze(data):
    """Traced as step:analyze"""
    return client.chat.completions.create(...)
```

**Nested calls automatically inherit hierarchy:**
```
agent:researcher
├─ agent:researcher/tool:web_search
└─ agent:researcher/step:analyze
```

### Multi-Step Workflow Example

```python
from llmobserve import section

with section("agent:data_pipeline"):
    # Step 1: Extract
    with section("step:extract"):
        raw_data = fetch_data()
    
    # Step 2: Transform
    with section("step:transform"):
        with section("tool:openai_embed"):
            embeddings = client.embeddings.create(...)
    
    # Step 3: Load
    with section("step:load"):
        with section("tool:pinecone_upsert"):
            index.upsert(vectors=embeddings)
```

**Trace hierarchy:**
```
agent:data_pipeline
├─ agent:data_pipeline/step:extract
├─ agent:data_pipeline/step:transform
│  └─ agent:data_pipeline/step:transform/tool:openai_embed
└─ agent:data_pipeline/step:load
   └─ agent:data_pipeline/step:load/tool:pinecone_upsert
```

### Agent Orchestration Example

```python
from llmobserve import section

async def run_agent_workflow(task: str):
    with section("agent:coordinator"):
        # Planner agent
        with section("agent:planner"):
            plan = await create_plan(task)
        
        # Execute each step
        for step in plan:
            with section(f"agent:executor"):
                with section(f"tool:{step.tool_name}"):
                    result = await execute_tool(step)
        
        # Synthesize results
        with section("agent:synthesizer"):
            return await synthesize_results()
```

## Dashboard Visualization

### Hierarchical Trace View

When you use nested sections, the dashboard displays an interactive tree:

```
agent:researcher (expand/collapse)
├─ tool:web_search       $0.002   150ms   [ok]
├─ step:analyze_results  $0.001   120ms   [ok]
└─ tool:pinecone_query   $0.0005  80ms    [ok]
```

**Features:**
- Expand/collapse branches
- Aggregate costs per subtree
- See full execution flow
- Identify bottlenecks

### Flat View Fallback

If no hierarchy is detected (no `parent_span_id`), the dashboard automatically falls back to a flat event list:

```
retrieval  openai  chat  $0.002  [ok]
reasoning  openai  chat  $0.003  [ok]
action     openai  chat  $0.001  [ok]
```

## Best Practices

### 1. Use Semantic Prefixes Consistently

**Good:**
```python
with section("agent:planner"):
    with section("tool:web_search"):
        ...
```

**Avoid:**
```python
with section("my_planner"):  # No semantic prefix
    with section("search"):    # Ambiguous
        ...
```

### 2. Keep Hierarchy Shallow (3-4 levels max)

**Good:**
```
agent:coordinator
└─ agent:worker
   └─ tool:openai_chat
```

**Avoid (too deep):**
```
agent:main
└─ agent:sub1
   └─ agent:sub2
      └─ agent:sub3
         └─ agent:sub4
            └─ tool:openai_chat  # Hard to visualize
```

### 3. Label All Cost-Generating Operations

Ensure every LLM or API call happens inside a labeled section for accurate attribution.

### 4. Combine with Tenant/Customer Tracking

```python
from llmobserve import set_tenant_id, set_customer_id, section

# Set tenant and customer context
set_tenant_id("acme-corp")
set_customer_id("user_123")

# Nested agent workflow
with section("agent:support_bot"):
    with section("tool:openai_chat"):
        response = client.chat.completions.create(...)
```

**Result:** Costs are attributed to both:
- Tenant: `acme-corp`
- Customer: `user_123`
- Semantic path: `agent:support_bot/tool:openai_chat`

## API Reference

### `section(name: str)`

Context manager for labeling code sections.

**Parameters:**
- `name` (str): Section label with optional semantic prefix (`agent:`, `tool:`, `step:`)

**Returns:** Context manager

**Example:**
```python
with section("agent:researcher"):
    # Your code here
    pass
```

### `@trace(agent=None, tool=None, step=None)`

Decorator for automatically labeling functions.

**Parameters:**
- `agent` (str, optional): Agent name (e.g., "planner", "executor")
- `tool` (str, optional): Tool name (e.g., "web_search", "calculator")
- `step` (str, optional): Step name (e.g., "validate", "transform")

**Priority:** `agent` > `tool` > `step` (uses first non-None value)

**Example:**
```python
@trace(agent="researcher")
async def my_agent():
    ...
```

## Advanced: Async Safety

The SDK uses `contextvars.ContextVar` for async-safe context propagation. This means:

✅ **Works with async/await:**
```python
@trace(agent="worker")
async def async_worker():
    await asyncio.gather(
        task1(),  # Inherits agent:worker context
        task2(),  # Inherits agent:worker context
    )
```

✅ **Works with concurrent tasks:**
```python
async def run_parallel():
    await asyncio.gather(
        agent_a(),  # Independent context
        agent_b(),  # Independent context
    )
```

## Migration from Flat Sections

**No migration needed!** Hierarchical tracing is fully backward-compatible.

**Before (flat):**
```python
with section("retrieval"):
    search()

with section("reasoning"):
    analyze()
```

**After (hierarchical, optional):**
```python
with section("agent:researcher"):
    with section("tool:search"):
        search()
    with section("step:analyze"):
        analyze()
```

Both work, and existing flat traces will continue to display correctly.

## Troubleshooting

### "No hierarchical structure detected"

This means your events don't have `parent_span_id` set. Possible causes:

1. **Not using nested sections:** Each section must be inside another for hierarchy.
2. **Old SDK version:** Ensure you're using the latest `llmobserve` version.
3. **Flat sections only:** Single-level sections produce flat traces by design.

**Solution:** Use nested `section()` calls or the `@trace()` decorator.

### Section paths not showing in dashboard

1. **Check database migration:** Ensure `section_path` column exists in `trace_events`.
2. **Restart collector:** Run `make dev-api` to apply migrations.
3. **Clear old data:** Old events won't have `section_path` populated.

## Examples Repository

See `/scripts/test_run.py` for complete working examples of:
- Nested agent workflows
- Tool call hierarchies
- Multi-step pipelines
- Mixed flat and hierarchical traces

## Summary

✅ **Opt-in:** No changes required for existing code  
✅ **Async-safe:** Works with asyncio and concurrent execution  
✅ **Backward-compatible:** Flat traces still work  
✅ **Semantic labels:** `agent:`, `tool:`, `step:` for clear categorization  
✅ **Visual dashboard:** Interactive tree view for hierarchical traces

**Get started:**
```python
from llmobserve import observe, section

observe("http://localhost:8000")

with section("agent:my_agent"):
    with section("tool:openai_chat"):
        # Your LLM calls here
        pass
```

