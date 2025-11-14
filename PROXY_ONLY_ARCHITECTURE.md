# Proxy-Only Architecture (No Monkey Patching)

## Overview

**All API calls now route through the reverse proxy** - no monkey patching for OpenAI or Pinecone.

## Why This Change?

### Problem with Monkey Patching

1. **SDK Updates Break Tracking**: When OpenAI or Pinecone update their SDKs, monkey patching breaks
2. **Fragile**: Depends on SDK internals that can change without notice
3. **Maintenance Burden**: Need to update instrumentors every SDK release
4. **Version Conflicts**: Different SDK versions require different patches

### Solution: Reverse Proxy

1. **SDK-Agnostic**: Works with any SDK version - no code changes needed
2. **Universal Coverage**: Works with OpenAI, Pinecone, GraphQL, any HTTP API
3. **Stable**: Proxy parses HTTP requests/responses, not SDK internals
4. **Transparent**: Requests forwarded unchanged (like Kong)

## Architecture

```
Your Code
    ↓
HTTP Request (httpx/requests/aiohttp)
    ↓
SDK Intercepts → Adds Context Headers
    ↓
Routes to Proxy (http://localhost:9000/proxy)
    ↓
Proxy Forwards to Actual API (OpenAI/Pinecone/etc)
    ↓
Proxy Parses Response → Calculates Cost → Emits Event
    ↓
Returns Response to Your Code
```

## Changes Made

### 1. OpenAI & Pinecone Instrumentors Disabled

**File**: `sdk/python/llmobserve/instrumentation/__init__.py`

- OpenAI instrumentor removed from registry
- Pinecone instrumentor removed from registry
- Commented out with explanation

### 2. Proxy Auto-Starts by Default

**File**: `sdk/python/llmobserve/observe.py`

- Proxy auto-starts on port 9000 if not provided
- All API calls route through proxy by default
- Can be disabled by explicitly setting `proxy_url=None`

### 3. Updated Logging

- Clear messages about proxy usage
- Warnings if proxy not available
- Info about universal coverage

## Usage

### Basic Usage (Proxy Auto-Starts)

```python
import llmobserve

# Proxy auto-starts on port 9000
llmobserve.observe(
    collector_url="http://localhost:8000"
)

# All API calls automatically route through proxy
import openai
client = openai.OpenAI()
response = client.chat.completions.create(...)  # Tracked via proxy!
```

### Manual Proxy URL

```python
import llmobserve

# Use existing proxy
llmobserve.observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"
)
```

### Disable Proxy (Not Recommended)

```python
import llmobserve

# Explicitly disable proxy (API calls won't be tracked!)
llmobserve.observe(
    collector_url="http://localhost:8000",
    proxy_url=None
)
```

## What Works Through Proxy

### ✅ Fully Supported

- **OpenAI**: All endpoints (chat, embeddings, images, audio)
- **Pinecone**: All operations (upsert, query, fetch, update, delete)
- **GraphQL**: All queries, mutations, subscriptions
- **Any HTTP API**: Universal coverage

### ✅ Provider Detection

Proxy automatically detects providers by URL:
- `api.openai.com` → OpenAI
- `pinecone.io` → Pinecone
- `api.anthropic.com` → Anthropic
- `graphql` endpoints → GraphQL
- And 30+ more providers

### ✅ Response Parsing

Proxy parses responses and extracts:
- **OpenAI**: Tokens (input/output/cached), model, cost
- **Pinecone**: Operation count, cost
- **GraphQL**: Operation type, complexity, data size
- **Generic APIs**: Request/response metadata

## Benefits

1. **No SDK Updates Breaking Tracking**: Proxy works with any SDK version
2. **Universal Coverage**: Works with any HTTP API automatically
3. **GraphQL Support**: Built-in GraphQL parsing (like Kong)
4. **Stable**: No dependency on SDK internals
5. **Transparent**: Requests forwarded unchanged

## Migration

### Old Code (Still Works)

```python
import llmobserve

# Old way - still works, but now uses proxy
llmobserve.observe(
    collector_url="http://localhost:8000",
    use_instrumentors=False  # Default now
)
```

### New Code (Recommended)

```python
import llmobserve

# New way - proxy auto-starts
llmobserve.observe(
    collector_url="http://localhost:8000"
    # Proxy auto-starts, OpenAI/Pinecone tracked via proxy
)
```

## Performance

### Latency Impact

- **Extra Network Hop**: ~1-5ms (local proxy)
- **Parsing Overhead**: ~0.1-1ms (response parsing)
- **Total Overhead**: ~1-6ms per API call

### Benefits Outweigh Cost

- **Stability**: No breaking changes when SDKs update
- **Universal**: Works with any API without code changes
- **Maintainability**: One codebase for all providers

## Troubleshooting

### Proxy Not Starting?

```bash
# Check if port 9000 is available
lsof -i :9000

# Install proxy dependencies
pip install fastapi uvicorn httpx
```

### API Calls Not Tracked?

1. Check proxy is running: `curl http://localhost:9000/health`
2. Check logs for proxy URL
3. Verify `proxy_url` is set in config

### Want to Use Instrumentors?

```python
# Other providers can still use instrumentors
llmobserve.observe(
    collector_url="http://localhost:8000",
    use_instrumentors=True  # For Anthropic, Cohere, etc.
    # OpenAI/Pinecone still use proxy (disabled)
)
```

## Future

- **All Providers via Proxy**: Eventually move all providers to proxy
- **GraphQL Enhancements**: Query complexity limits, rate limiting
- **Performance**: Caching, connection pooling
- **Observability**: Proxy metrics, latency tracking

