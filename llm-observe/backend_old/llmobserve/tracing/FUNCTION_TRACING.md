# Function-Level Workflow Tracing

## Overview

The function-level workflow tracer automatically creates workflow spans for function executions, ensuring that all API calls within a function are grouped under a single workflow trace.

## How It Works

### Automatic Function Wrapping

When `llmobserve` is imported, functions are automatically wrapped to create workflow spans:

1. **Function Entry**: When a function starts, a workflow span is created immediately (before any code runs)
2. **API Calls**: All API calls within the function automatically become children of the workflow span
3. **Function Exit**: The workflow span ends when the function returns or raises an exception

### Context Propagation

Workflow context is propagated through:
- **Nested function calls**: Inner functions inherit the parent's workflow span
- **Async functions**: Context propagates via `contextvars` to async tasks
- **Threading**: Context is copied to new threads
- **Multiprocessing**: Context is serialized and restored in child processes
- **Celery tasks**: Context is injected into task headers

## Configuration

### Environment Variables

- `LLMOBSERVE_AUTO_FUNCTION_TRACING`: Enable/disable function tracing (default: `true`)
- `LLMOBSERVE_FUNCTION_PATTERNS`: Comma-separated patterns for functions to wrap (default: `*_workflow,*_agent,*_handler`)
- `LLMOBSERVE_EXCLUDE_MODULES`: Comma-separated module patterns to exclude (default: `test,__pycache__`)

### Examples

```bash
# Disable function tracing
export LLMOBSERVE_AUTO_FUNCTION_TRACING=false

# Wrap all functions (use "*" pattern)
export LLMOBSERVE_FUNCTION_PATTERNS="*"

# Wrap only specific patterns
export LLMOBSERVE_FUNCTION_PATTERNS="*_workflow,*_agent"

# Exclude test modules
export LLMOBSERVE_EXCLUDE_MODULES="test,__pycache__,migrations"
```

## Usage Examples

### Basic Function

```python
import llmobserve  # Auto-enables function tracing
import openai

def my_workflow():
    # Workflow span created here (workflow.my_workflow)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
    # API call becomes child of workflow.my_workflow
    return response

# Call the function
result = my_workflow()
```

### Async Function

```python
import llmobserve
import openai

async def async_workflow():
    # Workflow span created here (workflow.async_workflow)
    response = await openai.chat.completions.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
    return response

# Call the async function
result = await async_workflow()
```

### Nested Functions

```python
import llmobserve
import openai

def outer_workflow():
    # Workflow span: workflow.outer_workflow
    def inner_helper():
        # Inherits workflow.outer_workflow span
        response = openai.chat.completions.create(...)
        return response
    
    return inner_helper()

result = outer_workflow()
```

### Multiple API Calls

```python
import llmobserve
import openai
from pinecone import Pinecone

def agent_workflow():
    # Workflow span: workflow.agent_workflow
    
    # First API call (child of workflow.agent_workflow)
    query = openai.chat.completions.create(...)
    
    # Second API call (child of workflow.agent_workflow)
    results = Pinecone().Index("test").query(...)
    
    # Third API call (child of workflow.agent_workflow)
    summary = openai.chat.completions.create(...)
    
    return summary

result = agent_workflow()
```

## Edge Cases

### Functions with No API Calls

Functions without API calls still get workflow spans (for visibility):

```python
def helper_function():
    # Workflow span created (workflow.helper_function)
    # No API calls, but span shows function execution time
    return "result"
```

### Recursive Functions

Each recursive call gets its own workflow span:

```python
def recursive_function(n):
    # Each call gets: workflow.recursive_function
    if n > 0:
        return recursive_function(n - 1)
    return n
```

### Exception Handling

Workflow spans always end, even on exceptions:

```python
def failing_workflow():
    # Workflow span created
    try:
        raise ValueError("error")
    except ValueError:
        # Span ends here, exception recorded
        raise
```

### Generator Functions

Generator functions are wrapped, but each `yield` doesn't create a new span:

```python
def generator_workflow():
    # Workflow span: workflow.generator_workflow
    yield "first"
    # API calls here use same workflow span
    yield "second"
```

## Trace Structure

### Before Function Tracing

```
auto.workflow.openai (root)
  └── llm.request (child)
```

### After Function Tracing

```
workflow.my_workflow (root)
  └── llm.request (child)
  └── pinecone.query (child)
  └── llm.request (child)
```

## Limitations

1. **Performance Overhead**: Function wrapping adds ~1-5μs per call
2. **Memory**: Contextvars stored per execution context
3. **Multiprocessing**: Requires explicit context serialization
4. **C Extensions**: Cannot wrap functions in C extensions
5. **Functions that never return**: Span stays open until function returns

## Manual Control

### Disable Function Tracing

```python
import os
os.environ["LLMOBSERVE_AUTO_FUNCTION_TRACING"] = "false"
import llmobserve
```

### Manually Wrap Functions

```python
from llmobserve.tracing.function_tracer import wrap_function

@wrap_function
def my_function():
    # Manually wrapped function
    pass
```

### Check Current Workflow Span

```python
from llmobserve.tracing.function_tracer import get_current_workflow_span

def my_function():
    span = get_current_workflow_span()
    if span:
        print(f"Current workflow: {span.name}")
```

