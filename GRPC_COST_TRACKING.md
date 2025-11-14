# gRPC Cost Tracking - Standard Approaches

## Industry Standard: ORCA (Open Request Cost Aggregation)

**ORCA** is the **official gRPC standard** for cost/metrics tracking. It's how Google, Envoy, and other major tools handle gRPC cost tracking.

### How ORCA Works

1. **Server-Side**: gRPC servers report cost metrics in **trailing metadata**
2. **Client-Side**: Clients read cost data from trailing metadata
3. **Standard**: No protobuf parsing needed - costs come from server

```python
# Server reports cost in trailing metadata
trailing_metadata = [
    ("orca-cost", "0.000012"),  # Cost in USD
    ("orca-cpu-utilization", "0.5"),  # Optional: CPU usage
    ("orca-memory-utilization", "0.3"),  # Optional: Memory usage
]

# Client reads from trailing metadata
response = stub.SomeMethod(request)
cost = response.trailing_metadata().get("orca-cost")
```

## Standard Approaches (Ranked)

### 1. ✅ **ORCA (Recommended - Industry Standard)**

**Pros:**
- ✅ Official gRPC standard
- ✅ No protobuf parsing needed
- ✅ Server reports accurate costs
- ✅ Works with any gRPC service
- ✅ Used by Google, Envoy, Kong

**Cons:**
- ⚠️ Requires server-side support (servers must implement ORCA)
- ⚠️ Can't track costs for services you don't control

**Implementation:**
```python
# In gRPC interceptor - read trailing metadata
def intercept_unary_unary(self, continuation, client_call_details, request):
    response = continuation(new_details, request)
    
    # Read ORCA cost from trailing metadata
    trailing_metadata = dict(response.trailing_metadata())
    cost_usd = float(trailing_metadata.get("orca-cost", "0.0"))
    
    # Track cost
    track_grpc_call(cost_usd, ...)
    return response
```

### 2. ⚠️ **HTTP/2 Proxy (Like Envoy/Kong)**

**How it works:**
- Intercept at HTTP/2 level (gRPC uses HTTP/2)
- Parse protobuf messages
- Extract usage/cost data

**Pros:**
- ✅ Works without server changes
- ✅ Transparent to client
- ✅ Can parse any gRPC service

**Cons:**
- ❌ Requires protobuf schemas (.proto files)
- ❌ Complex to implement (need protobuf parser)
- ❌ Different schemas for each service
- ❌ Can't generically parse without schema

**Tools:**
- **Envoy Proxy** - Has gRPC support, can parse protobuf
- **Kong** - Supports gRPC with protobuf parsing
- **gRPC-Web** - Converts gRPC to HTTP/1.1

### 3. ⚠️ **Client-Side Protobuf Parsing**

**How it works:**
- Parse protobuf responses in interceptor
- Extract usage fields (tokens, operations, etc.)
- Calculate costs from usage

**Pros:**
- ✅ Works without server changes
- ✅ Client-side only

**Cons:**
- ❌ Requires protobuf schemas
- ❌ Need to know field names for each service
- ❌ Breaks when schemas change
- ❌ Complex to maintain

### 4. ❌ **gRPC Reflection (Not Recommended)**

**How it works:**
- Use gRPC reflection to introspect schemas
- Dynamically parse protobuf

**Pros:**
- ✅ No hardcoded schemas

**Cons:**
- ❌ Reflection adds overhead
- ❌ Not all services enable reflection
- ❌ Still need to know which fields = cost
- ❌ Complex implementation

## Recommended Approach for LLMObserve

### **Hybrid: ORCA + Fallback**

1. **Primary: ORCA** (when servers support it)
   - Read cost from trailing metadata
   - Works for Pinecone, Google Vertex AI, etc. (if they implement ORCA)

2. **Fallback: Known Service Parsing** (for specific services)
   - Parse protobuf for known services (Pinecone, Vertex AI)
   - Extract usage fields we know about
   - Calculate costs

3. **Fallback: Latency-Only Tracking** (for unknown services)
   - Track latency, metadata
   - Cost = $0.00 (can be configured manually)

## Implementation Plan

### Phase 1: ORCA Support (Standard)

```python
# In grpc_interceptor.py
def intercept_unary_unary(self, continuation, client_call_details, request):
    start_time = time.time()
    response = continuation(new_details, request)
    latency_ms = (time.time() - start_time) * 1000
    
    # Read ORCA cost from trailing metadata
    trailing_metadata = dict(response.trailing_metadata())
    cost_usd = float(trailing_metadata.get("orca-cost", "0.0"))
    
    # If ORCA cost available, use it
    if cost_usd > 0:
        track_grpc_call_with_cost(cost_usd, latency_ms, ...)
    else:
        # Fallback to parsing or latency-only
        track_grpc_call_fallback(response, latency_ms, ...)
    
    return response
```

### Phase 2: Known Service Parsing (Fallback)

```python
# Parse known services (Pinecone, Vertex AI)
def parse_known_service_response(service_name, response):
    if service_name == "pinecone":
        # Parse Pinecone protobuf response
        # Extract: operation_count, vector_count, etc.
        return extract_pinecone_usage(response)
    elif service_name == "vertex_ai":
        # Parse Vertex AI protobuf response
        # Extract: input_tokens, output_tokens
        return extract_vertex_ai_usage(response)
    return None
```

### Phase 3: Configurable Cost (Manual)

```python
# Allow manual cost configuration for unknown services
llmobserve.configure_grpc_cost(
    service="my-custom-service",
    method="MyMethod",
    cost_per_call=0.001  # $0.001 per call
)
```

## Comparison with Industry Tools

| Tool | Approach | Pros | Cons |
|------|----------|------|------|
| **Envoy** | HTTP/2 proxy + protobuf parsing | Universal, transparent | Complex, needs schemas |
| **Kong** | HTTP/2 proxy + protobuf parsing | Universal, transparent | Complex, needs schemas |
| **OpenTelemetry** | ORCA + interceptors | Standard, accurate | Requires server support |
| **ORCA (Standard)** | Server reports in metadata | Official standard, simple | Needs server support |

## Recommendation

**Start with ORCA support** - it's the standard way and works for services that implement it (Pinecone, Google Vertex AI, etc.).

**Add fallback parsing** for specific known services we care about (Pinecone, Vertex AI).

**Don't try to generically parse protobuf** - it's too complex and fragile.

## Next Steps

1. ✅ Implement ORCA trailing metadata reading
2. ✅ Add Pinecone protobuf parsing (known service)
3. ✅ Add Vertex AI protobuf parsing (known service)
4. ✅ Add configurable costs for unknown services
5. ⚠️ Consider HTTP/2 proxy later (if needed)

