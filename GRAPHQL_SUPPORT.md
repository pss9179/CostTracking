# GraphQL Support in LLMObserve Proxy

## Overview

The LLMObserve proxy now supports **GraphQL request tracking** similar to how Kong handles GraphQL. GraphQL requests are automatically detected, parsed, and tracked with full metadata while being forwarded transparently to the backend.

## How It Works (Like Kong)

Just like Kong, the proxy:

1. **Intercepts HTTP requests** - All HTTP/HTTPS requests go through the proxy
2. **Detects GraphQL automatically** - No configuration needed
3. **Parses GraphQL operations** - Extracts queries, mutations, subscriptions
4. **Tracks metadata** - Operation names, complexity, field counts
5. **Forwards transparently** - Requests pass through unchanged to backend
6. **Tracks responses** - Parses GraphQL responses for errors and data size

## Features

### ✅ Automatic Detection

GraphQL requests are detected by:
- Content-Type headers (`application/graphql`, `application/json`)
- Request body patterns (queries, mutations, subscriptions)
- GraphQL keywords in the request

### ✅ Operation Parsing

Extracts:
- **Operation type**: `query`, `mutation`, or `subscription`
- **Operation name**: Named operations (e.g., `GetUser`, `CreatePost`)
- **Field count**: Number of fields requested
- **Complexity score**: Simple complexity estimation based on:
  - Field count
  - Nested depth
  - Variables count
- **Variables**: GraphQL variables passed with the request

### ✅ Response Tracking

Tracks:
- **Data size**: Size of returned data
- **Error count**: Number of errors in response
- **Field count**: Number of fields in response data

### ✅ Transparent Forwarding

Like Kong, requests are:
- Forwarded **unchanged** to the backend
- Headers preserved (except LLMObserve tracking headers)
- Body content preserved exactly
- Response returned as-is to client

## Usage

No code changes needed! GraphQL requests are automatically tracked when routed through the proxy.

### Example GraphQL Request

```python
import httpx
import llmobserve

# Initialize LLMObserve (sets up proxy routing)
llmobserve.observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"  # Proxy URL
)

# Make GraphQL request - automatically tracked!
response = httpx.post(
    "https://api.example.com/graphql",
    json={
        "query": "query GetUser($id: ID!) { user(id: $id) { name email } }",
        "variables": {"id": "123"}
    }
)
```

### Tracked Event Metadata

The proxy emits events with GraphQL-specific metadata:

```json
{
  "span_type": "graphql_call",
  "endpoint": "graphql.query.GetUser",
  "event_metadata": {
    "graphql_operation_type": "query",
    "graphql_operation_name": "GetUser",
    "graphql_field_count": 2,
    "graphql_complexity_score": 5,
    "graphql_response_data_size": 1024,
    "graphql_response_error_count": 0
  }
}
```

## Supported Formats

### JSON Format (Standard)
```json
{
  "query": "query { user { name } }",
  "variables": {}
}
```

### Raw GraphQL String
```
query GetUser { user { name email } }
```

### Mutations
```json
{
  "mutation": "mutation CreatePost($title: String!) { createPost(title: $title) { id } }"
}
```

### Subscriptions
```json
{
  "subscription": "subscription OnMessage { messageAdded { id text } }"
}
```

## Implementation Details

### Files Added/Modified

1. **`proxy/graphql_parser.py`** - GraphQL parsing logic
   - `is_graphql_request()` - Detection
   - `parse_graphql_request()` - Request parsing
   - `extract_graphql_endpoint()` - Endpoint extraction
   - `parse_graphql_response()` - Response parsing

2. **`proxy/main.py`** - Proxy integration
   - GraphQL detection in request handler
   - GraphQL metadata in events
   - Transparent forwarding

3. **`proxy/providers.py`** - Endpoint detection
   - GraphQL endpoint detection from URLs

## Testing

Run the test suite:

```bash
python3 scripts/test_graphql.py
```

Tests cover:
- ✅ GraphQL detection (JSON, raw, mutations)
- ✅ Query parsing (operation type, name, fields)
- ✅ Endpoint extraction
- ✅ Response parsing (data size, errors)

## Benefits

1. **Zero Configuration** - Works automatically for any GraphQL API
2. **Full Visibility** - Track all GraphQL operations with metadata
3. **No Code Changes** - Existing GraphQL clients work as-is
4. **Transparent** - Requests pass through unchanged (like Kong)
5. **Cost Tracking** - GraphQL calls tracked alongside other API calls

## Comparison with Kong

| Feature | Kong | LLMObserve Proxy |
|---------|------|------------------|
| GraphQL Detection | ✅ | ✅ |
| Request Parsing | ✅ | ✅ |
| Transparent Forwarding | ✅ | ✅ |
| Operation Tracking | ✅ | ✅ |
| Cost Tracking | ❌ | ✅ |
| Complexity Analysis | ✅ | ✅ |
| Response Analysis | ✅ | ✅ |

## Next Steps

Future enhancements could include:
- GraphQL query complexity limits (like Kong)
- Per-operation rate limiting
- GraphQL schema introspection
- Query caching based on operation name
- GraphQL-specific cost models

