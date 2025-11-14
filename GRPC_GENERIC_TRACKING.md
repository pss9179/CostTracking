# Generic gRPC Cost Tracking (Like Kong)

## How It Actually Works

**You're right to question manual config!** Here's how we handle generic gRPC APIs:

## Three-Tier Cost Tracking (Automatic)

### 1. ✅ ORCA (Standard - Most Accurate)
**Works automatically** if server supports ORCA:
```python
# Server reports cost in trailing metadata
# Cost automatically extracted - no config needed!
```

### 2. ⚙️ Size-Based Estimation (Generic - Works for ANY API)
**Works automatically** for ANY gRPC API - no config needed:
```python
# Estimates cost based on request/response sizes
# No protobuf parsing needed - just measures bytes
# Generic heuristic: ~$0.000001 per KB transferred
```

### 3. 📝 Manual Config (Optional Override)
**Only if you want to override** the automatic estimation:
```python
# Optional: Set exact cost if you know it
llmobserve.configure_grpc_cost("my_service", "Query", 0.000016)
```

## How Kong Actually Works

**Kong doesn't magically parse protobuf** - it needs:
- **ORCA** (if server supports it) ✅
- **Protobuf schemas** (to parse responses) ⚠️
- **Plugins** (service-specific code) ⚠️

**What we do differently:**
- ✅ **ORCA** - Same as Kong (standard)
- ✅ **Size-based estimation** - Generic, no schemas needed (better than Kong!)
- ⚙️ **Manual config** - Optional override (like Kong plugins)

## Automatic Tracking (No Config Needed!)

```python
import grpc
import llmobserve

llmobserve.observe(collector_url="http://localhost:8000")

# Make ANY gRPC call - automatically tracked!
channel = grpc.insecure_channel("api.example.com:50051")
stub = AnyServiceStub(channel)
response = stub.AnyMethod(request)

# ✅ Cost automatically estimated from request/response sizes
# ✅ Works for ANY gRPC API - no config needed!
# ✅ If server supports ORCA, uses that instead (more accurate)
```

## Cost Sources (Priority Order)

1. **ORCA cost** (if server supports it) - Most accurate ✅
2. **Configured cost** (if you set it) - Exact, but manual ⚙️
3. **Size-based estimate** (automatic) - Generic, works for any API ✅

## Why Size-Based Estimation?

**Protobuf is binary** - you can't parse it without schemas. But we CAN:
- ✅ Measure request size (bytes)
- ✅ Measure response size (bytes)
- ✅ Estimate cost from size (heuristic)
- ✅ Works for ANY API - no schemas needed!

**This is actually BETTER than Kong** because:
- Kong needs protobuf schemas to parse
- We don't need schemas - just measure sizes
- Generic approach works for any gRPC API

## Example

```python
import grpc
import llmobserve

llmobserve.observe(collector_url="http://localhost:8000")

# ANY gRPC API - automatically tracked!
channel = grpc.insecure_channel("custom-api.com:50051")
stub = CustomServiceStub(channel)

# This call:
response = stub.ProcessData(large_request)  # 10KB request, 50KB response

# Gets tracked with:
# - Latency: 45ms
# - Request size: 10KB
# - Response size: 50KB  
# - Estimated cost: $0.00006 (based on 60KB total)
# - Cost source: "estimated" (or "orca" if server supports it)

# NO CONFIG NEEDED! Works automatically!
```

## When to Use Manual Config

**Only if:**
- You know the exact cost per call
- Size-based estimation is inaccurate for your use case
- You want to override the automatic estimation

**Otherwise:** Just use it - automatic tracking works for any gRPC API!

## Summary

- ✅ **ORCA**: Automatic, most accurate (if server supports it)
- ✅ **Size-based**: Automatic, works for ANY API (no config needed!)
- ⚙️ **Manual config**: Optional override (only if you want exact costs)

**Result**: Generic gRPC cost tracking that works for ANY API automatically - no manual config needed!

