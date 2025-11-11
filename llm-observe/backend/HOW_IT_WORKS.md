# How Function-Level Workflow Tracing Works

## Overview

Yes, this will work for **all your agent calls, API calls, etc.** Here's how:

## How It Works

### 1. **API Calls (OpenAI, Pinecone, etc.)**
✅ **Already working** - Your existing instrumentors (OpenAI, Pinecone, etc.) automatically create spans for API calls.

### 2. **Function-Level Workflow Spans**
✅ **Now working** - Functions are wrapped to create workflow spans that group all API calls within that function.

### 3. **The Flow**

```
User calls simulate_agent_workflow()
  ↓
@workflow_trace decorator creates: workflow.simulate_agent_workflow (root span)
  ↓
First API call: openai.chat.completions.create()
  ↓
ensure_root_span("openai") checks for workflow span → finds it!
  ↓
Creates: llm.request (child of workflow.simulate_agent_workflow)
  ↓
Second API call: pinecone.Index().query()
  ↓
ensure_root_span("pinecone") checks for workflow span → finds it!
  ↓
Creates: pinecone.query (child of workflow.simulate_agent_workflow)
  ↓
Third API call: openai.chat.completions.create()
  ↓
Creates: llm.request (child of workflow.simulate_agent_workflow)
  ↓
Function ends → workflow span closes
```

## What Gets Traced

### ✅ **Automatically Traced (No Code Changes Needed)**

1. **All API calls** via instrumentors:
   - OpenAI (`openai.chat.completions.create()`)
   - Pinecone (`index.query()`, `index.upsert()`, etc.)
   - Anthropic, Cohere, Mistral, Gemini, etc. (if instrumentors installed)

2. **Functions with `@workflow_trace` decorator**:
   - `simulate_agent_workflow()` ✅ (already wrapped)
   - `run_fake_app()` ✅ (already wrapped)
   - Any function you add `@workflow_trace` to

3. **Functions matching patterns** (if import hook works):
   - Functions ending in `_workflow`, `_agent`, `_handler`
   - Configurable via `LLMOBSERVE_FUNCTION_PATTERNS`

### ⚠️ **Manual Wrapping Required**

For functions that are imported before `llmobserve` is imported, you need to manually add `@workflow_trace`:

```python
from llmobserve.tracing.function_tracer import workflow_trace

@workflow_trace
async def my_agent_function():
    # All API calls here will be children of workflow.my_agent_function
    response = openai.chat.completions.create(...)
    return response
```

## Trace Structure

### Before (Without Function Tracing)
```
auto.workflow.openai (root)
  └── llm.request (child)

auto.workflow.pinecone (root)
  └── pinecone.query (child)

auto.workflow.openai (root)
  └── llm.request (child)
```
**Problem**: Each API call creates its own root span - no grouping!

### After (With Function Tracing)
```
workflow.simulate_agent_workflow (root)
  ├── llm.request (child) - GPT query generation
  ├── pinecone.query (child) - Vector search
  └── llm.request (child) - GPT summarization
```
**Solution**: All API calls grouped under one workflow span!

## Example: Your Current Code

### `simulate_agent_workflow()` ✅

```python
@workflow_trace  # ← Creates workflow span
async def simulate_agent_workflow() -> dict:
    # Workflow span: workflow.simulate_agent_workflow
    
    # API call 1 → llm.request (child)
    query_resp = await client.chat.completions.create(...)
    
    # API call 2 → pinecone.query (child)
    results = await index.query(...)
    
    # API call 3 → llm.request (child)
    summary_resp = await client.chat.completions.create(...)
    
    return result
```

**Result**: All 3 API calls are grouped under `workflow.simulate_agent_workflow`!

## Edge Cases Handled

✅ **Nested functions**: Inner functions inherit parent's workflow span
✅ **Async functions**: Context propagates via `contextvars`
✅ **Threading**: Context copied to threads
✅ **Exceptions**: Workflow span always ends (finally block)
✅ **Recursive functions**: Each call gets its own workflow span
✅ **Functions with no API calls**: Still get workflow spans (for visibility)

## Configuration

Set these environment variables to control behavior:

```bash
# Enable/disable function tracing (default: true)
LLMOBSERVE_AUTO_FUNCTION_TRACING=true

# Function name patterns to wrap (default: *_workflow,*_agent,*_handler)
LLMOBSERVE_FUNCTION_PATTERNS="*_workflow,*_agent,*_handler"

# Modules to exclude (default: test,__pycache__)
LLMOBSERVE_EXCLUDE_MODULES="test,__pycache__,migrations"
```

## Testing

To verify it's working:

1. **Call your agent function**:
   ```bash
   curl -X POST http://localhost:8000/demo/simulate-agent
   ```

2. **Check the trace**:
   - Should see `workflow.simulate_agent_workflow` as root span
   - Should see 3 child spans: `llm.request`, `pinecone.query`, `llm.request`
   - All should have the same `trace_id`

3. **Check the dashboard**:
   - Workflow should appear in the workflows table
   - Trace tree should show the hierarchy

## Summary

✅ **API calls**: Automatically traced (no changes needed)
✅ **Agent functions**: Wrapped with `@workflow_trace` decorator
✅ **Grouping**: All API calls within a function are grouped under one workflow span
✅ **Context propagation**: Works across async, threading, nested calls
✅ **Edge cases**: Handled (exceptions, recursion, etc.)

**Bottom line**: Yes, this will work for all your agent calls and API calls! 🎉


