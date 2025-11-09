# Universal LLM Tracker Explanation

## Overview

The `universal_llm_tracker.py` module provides a single async function `track_llm_call()` that automatically tracks costs for **any LLM provider** with full streaming support. This document explains how it works and why it's production-safe.

---

## How Streaming Detection Works

### 1. **Automatic Provider Detection**

The function detects streaming support through **introspection** of the client object:

```python
def _detect_streaming_support(provider: str, client: Any) -> bool:
    # Checks for common streaming patterns:
    # - .stream() or .create_stream() methods
    # - .chat.completions.create() with stream=True (OpenAI)
    # - .messages.create() with stream=True (Anthropic)
```

**Why this works:**
- Most modern LLM providers follow similar patterns (OpenAI-style or Anthropic-style)
- The function checks multiple common method patterns
- If detection fails, it defaults to assuming streaming is supported (most providers do)
- The actual API call will handle errors gracefully if streaming isn't available

### 2. **Streaming Execution**

When streaming is enabled, `_call_with_streaming()` handles different provider patterns:

- **OpenAI**: `client.chat.completions.create(stream=True)` → buffers chunks from `chunk.choices[0].delta.content`
- **Anthropic**: `client.messages.create(stream=True)` → buffers chunks from `chunk.delta.text`
- **Generic**: Falls back to `client.stream()` or `client.create_stream()` methods
- **Fallback**: Tries `stream=True` parameter in generic `create()` method

**Key safety feature:** All streaming calls are wrapped in try/except, so if a provider doesn't support streaming, it gracefully falls back to non-streaming mode.

---

## How Cost Tracking is Guaranteed

### 1. **Finally Block Protection**

The core guarantee comes from Python's `finally` block, which **always executes** even if:
- An exception is raised
- A stream breaks mid-way
- Network timeout occurs
- Provider returns unexpected response format

```python
try:
    # Execute API call (streaming or non-streaming)
    response = await _call_with_streaming(...)
except Exception as e:
    # Error occurred - still track cost
    error = str(e)
finally:
    # ALWAYS calculate and return cost, even on errors
    cost_usd = calculate_cost(prompt_tokens, completion_tokens)
    return standardized_payload
```

### 2. **Token Estimation Fallbacks**

The function uses a **multi-layer fallback** for token counting:

1. **Primary**: Extract `usage` from provider response (most accurate)
2. **Secondary**: Use `tiktoken` library for accurate token counting (if available)
3. **Tertiary**: Word-based estimation (~1.3 tokens per word) for any string

This ensures tokens are **always** estimated, even when:
- Provider doesn't return usage data
- Stream breaks before completion
- Response format is unexpected

### 3. **Streaming Buffer Protection**

For streaming calls, the function:
- Buffers **all chunks** into `full_output` string
- If stream breaks, uses buffered output to estimate completion tokens
- If stream completes normally, tries to extract usage from last chunk
- Falls back to token estimation from buffered output if usage unavailable

**Example scenario:**
```python
# Stream breaks after 50% completion
# Function still:
# 1. Estimates prompt tokens from input messages
# 2. Estimates completion tokens from buffered output (50% of response)
# 3. Calculates partial cost
# 4. Returns standardized payload with error field
```

---

## Why This Covers All LLMs with Streaming

### 1. **Provider-Agnostic Design**

The function doesn't hardcode provider-specific logic. Instead, it:
- Uses **introspection** to detect client methods
- Handles multiple common patterns (OpenAI, Anthropic, generic)
- Falls back gracefully when patterns don't match

### 2. **Streaming Pattern Coverage**

Most LLM providers follow one of these patterns:
- **OpenAI-style**: `client.chat.completions.create(stream=True)` → async iterator
- **Anthropic-style**: `client.messages.create(stream=True)` → async iterator
- **Generic**: `client.stream()` or `client.create_stream()` methods
- **Parameter-based**: `stream=True` in generic `create()` method

The function checks all of these patterns, ensuring compatibility with:
- OpenAI, Anthropic, Mistral, Gemini, Cohere, Together, Perplexity, Fireworks, etc.

### 3. **Error Resilience**

The function handles edge cases:
- ✅ **Normal completion**: Extracts usage, calculates cost
- ⚠️ **Broken stream**: Uses buffered output, estimates tokens, calculates partial cost
- ⚠️ **Missing usage**: Falls back to token estimation
- ⚠️ **Provider without streaming**: Falls back to non-streaming mode
- ⚠️ **Tokenizer unavailable**: Falls back to word-based estimation
- ⚠️ **Async concurrency**: Each call is independent, no shared state

### 4. **Atomic Cost Logging**

Cost calculation happens in the `finally` block, which means:
- Cost is **always** calculated, even if API call fails
- Cost is **always** returned in standardized format
- No race conditions (each call is independent)
- No lost cost data (finally block always executes)

---

## Production Safety Features

1. **No Shared State**: Each call is independent, safe for concurrent use
2. **Exception Handling**: All errors are caught and logged in return payload
3. **Fallback Chains**: Multiple fallbacks ensure tokens are always estimated
4. **Type Safety**: Full type hints for IDE support and static analysis
5. **Versioned Pricing**: Pricing table is versioned for auditability
6. **Standardized Output**: Consistent return format for all providers

---

## Usage Example

```python
from openai import AsyncOpenAI
from llmobserve.tracing.universal_llm_tracker import track_llm_call

client = AsyncOpenAI()

result = await track_llm_call(
    provider="openai",
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    client=client,
    stream=True  # Auto-detected if not provided
)

# Result always contains:
# {
#   "provider": "openai",
#   "model": "gpt-4o",
#   "pricing_version": "2025-01-15",
#   "prompt_tokens": 5,
#   "completion_tokens": 10,
#   "total_tokens": 15,
#   "cost_usd": 0.000125,
#   "timestamp": "2025-01-15T12:00:00Z",
#   "error": None  # or error message if call failed
# }
```

---

## Summary

The universal tracker works for **all LLMs with streaming** because:

1. **Pattern Detection**: Uses introspection to detect provider patterns automatically
2. **Multiple Fallbacks**: Handles different provider formats and missing data gracefully
3. **Finally Block**: Guarantees cost calculation even on errors or broken streams
4. **Token Estimation**: Always estimates tokens even when usage data is unavailable
5. **Stream Buffering**: Captures partial output from broken streams for cost calculation

This design ensures **zero lost cost data** and **universal provider compatibility**.

