# Tool Wrapping Architecture

Technical documentation explaining how the tool wrapping system works.

## Table of Contents

1. [Overview](#overview)
2. [Why Manual Labeling Fails](#why-manual-labeling-fails)
3. [How Tool Wrapping Works](#how-tool-wrapping-works)
4. [Dual System Design](#dual-system-design)
5. [Implementation Details](#implementation-details)
6. [Span Priority System](#span-priority-system)
7. [Performance](#performance)

## Overview

The tool wrapping system provides automatic agent and tool cost tracking without manual labeling. It combines:

- **Agent decorators** (`@agent`) for marking entrypoints
- **Tool wrappers** (`wrap_tool`, `@tool`) for automatic nesting
- **LLM wrappers** for extracting tool_calls metadata
- **HTTP interceptors** as fallback for untracked calls
- **Context stack** (contextvars) for async-safe hierarchy

## Why Manual Labeling Fails

### Problem 1: Setup Code Not Captured

```python
# Manual labeling
def agent():
    client = openai.OpenAI()  # ❌ Setup cost not tracked
    with section("agent:researcher"):
        result = client.chat.completions.create(...)
```

**Why it fails**: API calls before `with section()` are missed.

**Solution**: Wrap the entire function:

```python
@agent("researcher")
def agent():
    client = openai.OpenAI()  # ✓ All code tracked
    result = client.chat.completions.create(...)
```

### Problem 2: Nested Tools

```python
# Manual labeling
def tool_a():
    with section("tool:A"):
        tool_b()  # ❌ tool_b's structure lost

def tool_b():
    # No section here - where does it go?
    pass
```

**Why it fails**: User must manually nest sections for every call.

**Solution**: Wrap functions, nesting happens automatically:

```python
@tool("A")
def tool_a():
    tool_b()  # ✓ Automatically nested

@tool("B")
def tool_b():
    pass

# Tree: tool:A/tool:B
```

### Problem 3: Framework Internals

```python
# LangChain agent
agent = initialize_agent(tools=[search, calc], llm=llm)
agent.run("Search and calculate")

# ❌ Can't add sections inside LangChain's internal code
```

**Why it fails**: Frameworks call tools internally, user code doesn't control the call site.

**Solution**: Wrap tools at registration:

```python
tools = wrap_all_tools([search, calc])
agent = initialize_agent(tools=tools, llm=llm)

# ✓ Tools are wrapped, LangChain's internal calls are tracked
```

### Problem 4: Dynamic Tool Selection

```python
# LLM decides which tool to call
response = llm.chat.completions.create(tools=[search, calc, summarize])

# ❌ Can't pre-label - don't know which tool LLM will choose
```

**Why it fails**: Tool choice is dynamic, no static labeling possible.

**Solution**: Wrap all tools upfront:

```python
tools = wrap_all_tools({"search": search, "calc": calc, "summarize": summarize})
# ✓ Whichever tool LLM chooses is already wrapped
```

### Problem 5: Third-Party Libraries

```python
# Tool calls a library function
def my_tool():
    with section("tool:my_tool"):
        third_party_lib.function()  # ❌ Can't modify library code

# ❌ Can't add sections inside third_party_lib
```

**Why it fails**: Can't modify external library code.

**Solution**: Wrap your tool, everything inside is tracked:

```python
@tool("my_tool")
def my_tool():
    third_party_lib.function()  # ✓ Tracked as part of my_tool
```

## How Tool Wrapping Works

### 1. Agent Decorator

Wraps an agent entrypoint function:

```python
@agent("researcher")
def my_agent(query):
    # Agent code
    pass
```

**What happens:**
1. Function is wrapped
2. On entry: Creates `agent:researcher` span, pushes to context stack
3. On exit (finally): Pops from stack, records duration
4. Exception handling: Captures error but re-raises

**Stack state:**
```
Entry:  []  →  ["agent:researcher"]
Exit:   ["agent:researcher"]  →  []
```

### 2. Tool Wrapper

Wraps any callable to create tool spans:

```python
@tool("web_search")
def search(query):
    # Tool code
    pass
```

**What happens:**
1. Function is wrapped (idempotent - no double wrapping)
2. On entry: Creates `tool:web_search` span, pushes to stack
3. On exit (finally): Pops from stack, records duration
4. Nested calls: Stack naturally maintains parent-child relationships

**Stack state for nested tools:**
```
Entry outer:  ["agent:A"]  →  ["agent:A", "tool:outer"]
Entry inner:  ["agent:A", "tool:outer"]  →  ["agent:A", "tool:outer", "tool:inner"]
Exit inner:   ["agent:A", "tool:outer", "tool:inner"]  →  ["agent:A", "tool:outer"]
Exit outer:   ["agent:A", "tool:outer"]  →  ["agent:A"]
```

### 3. Context Stack (ContextVars)

Uses Python's `contextvars` for async-safe span management:

```python
_section_stack_var: ContextVar[List[Dict[str, Any]]] = ContextVar("section_stack")

# Each entry contains:
{
    "label": "tool:web_search",
    "span_id": "uuid",
    "parent_span_id": "parent_uuid"
}
```

**Benefits:**
- **Async-safe**: Each async task has its own stack
- **No thread issues**: Isolated per execution context
- **Automatic cleanup**: Guaranteed by `with` statement / `finally`

### 4. Universal Tool Registration

`wrap_all_tools()` works with any tool format:

```python
def wrap_all_tools(tools):
    if isinstance(tools, dict):
        # AutoGen style
        return {name: wrap_tool(fn, name) for name, fn in tools.items()}
    
    elif isinstance(tools, list):
        # LangChain/CrewAI style
        wrapped = []
        for t in tools:
            if hasattr(t, "run"):
                # Tool object with .run() method
                t.run = wrap_tool(t.run, name)
            else:
                # Plain function
                wrapped.append(wrap_tool(t))
        return wrapped
    
    else:
        # Single function
        return wrap_tool(tools)
```

**Handles:**
- Dicts (AutoGen `function_map`)
- Lists (LangChain/CrewAI)
- Tool objects with `.run()` method
- Plain functions
- Mixed types

## Dual System Design

### Instrumentors vs Wrappers

**Instrumentors (existing):**
- Activated by default with `observe()`
- Provide basic cost tracking for all LLM calls
- Work with or without tool calling
- Simpler, less metadata

**LLM Wrappers (new):**
- User explicitly wraps client: `wrap_openai_client(client)`
- Extract `tool_calls` from responses as metadata
- Create proper span hierarchy for agent workflows
- More detailed, tool-specific

**Coexistence:**
Both can be active. If both emit spans, LLM wrapper takes priority (higher in span hierarchy).

### Priority System

When multiple span sources exist, priority order:

1. **Highest:** Agent/tool/LLM wrapper spans (explicit)
2. **Medium:** Legacy `section()` labels (backward compat)
3. **Lowest:** HTTP interceptor (fallback)

**Example:**
```python
@agent("researcher")
def agent():
    @tool("search")
    def search():
        response = http_client.get("api.com")  # HTTP interceptor active
        return response
    
    return search()
```

**Span hierarchy:**
```
agent:researcher (highest priority - explicit)
└── tool:search (highest priority - explicit)
    └── http://api.com (lowest priority - fallback)
```

The HTTP call is attributed to `tool:search`, not as a separate root span.

## Implementation Details

### Idempotent Wrapping

Prevents double-wrapping:

```python
def wrap_tool(func, name=None):
    # Check if already wrapped
    if getattr(func, "__llmobserve_wrapped__", False):
        return func  # Already wrapped, return as-is
    
    # ... wrapping logic ...
    
    wrapped.__llmobserve_wrapped__ = True
    wrapped.__llmobserve_original__ = func
    return wrapped
```

### Async Support

Detects async functions and wraps appropriately:

```python
def wrap_tool(func, name=None):
    is_async = inspect.iscoroutinefunction(func)
    
    if is_async:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # ... span management ...
            return await func(*args, **kwargs)
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # ... span management ...
            return func(*args, **kwargs)
        return sync_wrapper
```

### Error Handling

Exceptions are captured but re-raised (fail-open):

```python
try:
    result = func(*args, **kwargs)
    return result
except Exception as e:
    error_message = str(e)
    status = "error"
    raise  # Re-raise to preserve user's error handling
finally:
    # Emit span with error info
    buffer.add_event({
        "status": status,
        "event_metadata": {"error": error_message} if error_message else None
    })
    
    # Pop from stack
    stack.pop()
```

### Distributed Tracing

Maintains trace continuity across processes:

```python
def export_distributed_context():
    return {
        "trace_id": context.get_trace_id(),
        "span_id": current_span_id,
        "run_id": context.get_run_id(),
        "customer_id": context.get_customer_id(),
    }

def import_distributed_context(ctx):
    # Restore trace_id (maintains trace continuity)
    context.set_trace_id(ctx["trace_id"])
    context.set_run_id(ctx["run_id"])
    # New spans are children of the original trace
```

## Span Priority System

### How Priority Works

When an event is created, its span type determines priority:

```python
span_type = "agent"      # Priority 1 (highest)
span_type = "tool"       # Priority 1 (highest)
span_type = "llm"        # Priority 1 (highest)
span_type = "section"    # Priority 2 (medium)
span_type = "http_fallback"  # Priority 3 (lowest)
```

**Attribution logic:**
- If active span exists at higher priority, attribute cost there
- If no higher priority span, create new root span
- Untracked costs = costs with no agent/tool/llm parent

### Example Tree

```python
@agent("planner")
def planner():
    llm_call()  # Creates llm:openai span under agent:planner
    tool_a()    # Creates tool:A span under agent:planner
    
@tool("A")
def tool_a():
    llm_call()  # Creates llm:openai span under tool:A
    tool_b()    # Creates tool:B span under tool:A

@tool("B")
def tool_b():
    http_get()  # HTTP fallback, attributed to tool:B
```

**Resulting tree:**
```
agent:planner (span_type=agent)
├── llm:openai (span_type=llm)
└── tool:A (span_type=tool)
    ├── llm:openai (span_type=llm)
    └── tool:B (span_type=tool)
        └── http://api.com (span_type=http_fallback)
```

## Performance

### Overhead

- **Agent decorator**: ~0.1ms per call (span management)
- **Tool wrapper**: ~0.05ms per call (span management)
- **Context stack**: ~0.01ms per push/pop
- **HTTP fallback**: Already present, no extra overhead

**Total overhead per tool call:** ~0.2ms (negligible)

### Memory

- **Context stack**: ~100 bytes per span
- **Max depth**: No hard limit, but typical agent workflows stay under 10 levels
- **Async isolation**: Each async task has separate stack (no memory sharing)

### Scalability

- ✅ Thread-safe (contextvars)
- ✅ Async-safe (contextvars)
- ✅ Multi-process (via export/import context)
- ✅ No global state
- ✅ Garbage collected automatically

## Comparison

### Manual Labeling vs Tool Wrapping

| Feature | Manual `section()` | Tool Wrapping |
|---------|-------------------|---------------|
| Nested tools | ❌ Breaks | ✅ Automatic |
| Framework support | ❌ Can't modify | ✅ Works |
| Setup code | ❌ Missed | ✅ Included |
| Async support | ✅ Yes | ✅ Yes |
| Error handling | ✅ Yes | ✅ Yes |
| Maintenance | ❌ High (manual) | ✅ Low (automatic) |
| Accuracy | ⚠️ Depends on user | ✅ Guaranteed |

## Future Work

- **Auto-framework patching**: Automatically wrap tools when framework detects them
- **LLM streaming**: Extract tool_calls from streaming responses
- **More LLM providers**: Google Gemini, Mistral, etc.
- **Performance metrics**: Per-tool latency, memory usage
- **Cost optimization**: Suggest cheaper models based on tool usage patterns

