# gRPC Cost Configuration Guide

## How to Track Costs for gRPC APIs That Don't Support ORCA

If a gRPC API doesn't implement ORCA (the standard), you can manually configure costs.

## Two Ways to Track gRPC Costs

### 1. ✅ ORCA (Automatic - Standard)

**Works automatically** if the gRPC server implements ORCA:

```python
import grpc
import llmobserve

llmobserve.observe(collector_url="http://localhost:8000")

# If server supports ORCA, cost is tracked automatically!
channel = grpc.insecure_channel("api.example.com:50051")
stub = YourServiceStub(channel)
response = stub.YourMethod(request)
# ✅ Cost automatically extracted from ORCA trailing metadata
```

### 2. ⚙️ Manual Configuration (Fallback)

**Configure costs manually** for APIs that don't support ORCA:

```python
import grpc
import llmobserve

llmobserve.observe(collector_url="http://localhost:8000")

# Configure cost for a specific gRPC method
llmobserve.configure_grpc_cost(
    service="my_service",
    method="Query",
    cost_per_call=0.000016  # $0.000016 per call
)

# Now make gRPC calls - costs will be tracked!
channel = grpc.insecure_channel("api.example.com:50051")
stub = MyServiceStub(channel)
response = stub.Query(request)
# ✅ Cost tracked using configured value: $0.000016
```

## Configuration Examples

### Example 1: Specific Method

```python
# Set cost for Pinecone Query method
llmobserve.configure_grpc_cost(
    service="pinecone",
    method="Query",
    cost_per_call=0.000016  # $16 per million queries
)
```

### Example 2: All Methods in a Service

```python
# Set default cost for all methods in a service
llmobserve.configure_grpc_cost(
    service="my_service",
    method="*",  # Wildcard for all methods
    cost_per_call=0.001  # $0.001 per call
)

# Or simpler:
llmobserve.configure_grpc_cost(
    service="my_service",
    cost_per_call=0.001  # Applies to all methods
)
```

### Example 3: Global Default

```python
# Set default cost for ALL gRPC calls (if not configured)
llmobserve.configure_grpc_cost(
    service="*",  # Global wildcard
    method="*",
    cost_per_call=0.0001  # $0.0001 per call default
)
```

### Example 4: Multiple Services

```python
# Configure different costs for different services
llmobserve.configure_grpc_cost("pinecone", "Query", 0.000016)
llmobserve.configure_grpc_cost("pinecone", "Upsert", 0.000004)
llmobserve.configure_grpc_cost("vertex_ai", "Predict", 0.00001)
llmobserve.configure_grpc_cost("my_service", "*", 0.001)
```

## How It Works

### Priority Order

1. **ORCA cost** (if server supports it) - ✅ Automatic, most accurate
2. **Configured cost** (if you set it) - ⚙️ Manual, but works for any API
3. **$0.00** (if neither available) - Still tracks latency/metadata

### Example Flow

```python
# 1. Configure cost (optional)
llmobserve.configure_grpc_cost("my_service", "Query", 0.000016)

# 2. Make gRPC call
response = stub.Query(request)

# 3. Cost tracking happens automatically:
#    - First tries ORCA (if server supports it)
#    - Falls back to configured cost ($0.000016)
#    - Falls back to $0.00 (still tracks latency)
```

## Finding gRPC Method Names

To configure costs, you need to know the service and method names:

```python
# gRPC method path format: "/Service/Method"
# Example: "/pinecone.Query/Query"
#          Service: "pinecone"
#          Method: "Query"

# The interceptor automatically extracts these from the method path
```

### How to Find Method Names

1. **Check your gRPC client code:**
   ```python
   stub = MyServiceStub(channel)
   # Method name is usually the function name
   stub.Query(...)  # Method = "Query"
   stub.Upsert(...)  # Method = "Upsert"
   ```

2. **Check logs:**
   ```python
   # Enable debug logging to see method names
   llmobserve.set_log_level("DEBUG")
   # You'll see: "[llmobserve] Tracked gRPC call: /service.Method/Method"
   ```

3. **Check gRPC server documentation**

## Complete Example

```python
import grpc
import llmobserve

# Initialize
llmobserve.observe(collector_url="http://localhost:8000")

# Configure costs for services that don't support ORCA
llmobserve.configure_grpc_cost("pinecone", "Query", 0.000016)
llmobserve.configure_grpc_cost("pinecone", "Upsert", 0.000004)
llmobserve.configure_grpc_cost("my_custom_service", "*", 0.001)

# Make gRPC calls - costs tracked automatically!
channel = grpc.insecure_channel("api.example.com:50051")
stub = PineconeStub(channel)

# This will use configured cost: $0.000016
response = stub.Query(query_request)

# This will use configured cost: $0.000004
response = stub.Upsert(upsert_request)

# If server supports ORCA, ORCA cost takes priority
# If not, configured cost is used
# If neither, cost = $0.00 (but latency still tracked)
```

## Clearing Configurations

```python
# Clear all configured costs
llmobserve.clear_grpc_costs()
```

## Best Practices

1. **Try ORCA first** - Check if your gRPC server supports ORCA (it's the standard)
2. **Configure known services** - Set costs for services you know don't support ORCA
3. **Use wildcards** - Set default costs for entire services
4. **Set global default** - Use `service="*"` for a fallback default

## Summary

- ✅ **ORCA**: Automatic, works for any API that supports it
- ⚙️ **Manual Config**: Works for any API, but requires you to set costs
- 📊 **Both**: ORCA takes priority, falls back to configured cost

**Result**: You can track costs for **ANY gRPC API** - either automatically (ORCA) or manually (configured)!

