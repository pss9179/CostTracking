# How to Track ANY API - Quick Guide

## Yes, This Can Track ANY API! 🎯

The system uses a **reverse proxy** that intercepts ALL HTTP requests, so it can track costs for literally ANY HTTP API.

## How It Works

1. **SDK intercepts** your HTTP requests (httpx/requests/aiohttp)
2. **Routes through proxy** (adds context headers)
3. **Proxy forwards** to actual API
4. **Proxy parses response** and calculates cost
5. **Emits event** to collector

## Adding Custom API Pricing

### Step 1: Add Pricing to Registry

Edit `collector/pricing/registry.json`:

```json
{
  "myapi:endpoint": {
    "per_call": 0.001
  },
  "stripe:charges.create": {
    "per_call": 0.003
  },
  "twilio:messages.create": {
    "per_call": 0.0075
  },
  "myapi:token_based": {
    "input": 0.000001,
    "output": 0.000002
  }
}
```

### Step 2: Use the SDK

```python
from llmobserve import observe, section
import httpx

# Initialize (proxy auto-starts)
observe(collector_url="http://localhost:8000")

# Make ANY API call - automatically tracked!
with section("payment:process"):
    response = httpx.post(
        "https://api.stripe.com/v1/charges",
        headers={"Authorization": "Bearer sk_..."},
        json={"amount": 1000}
    )
    # ✅ Automatically tracked!
```

## Pricing Formats Supported

### Per-Call Pricing
```json
{
  "myapi:endpoint": {
    "per_call": 0.001  // $0.001 per call
  }
}
```

### Token-Based Pricing
```json
{
  "myapi:llm": {
    "input": 0.000001,   // per input token
    "output": 0.000002   // per output token
  }
}
```

### Per Million Pricing
```json
{
  "myapi:operations": {
    "per_million": 10.0  // $10 per million operations
  }
}
```

### Character-Based Pricing
```json
{
  "myapi:tts": {
    "per_1k_chars": 0.015  // $0.015 per 1k characters
  }
}
```

### Duration-Based Pricing
```json
{
  "myapi:audio": {
    "per_minute": 0.006  // $0.006 per minute
  }
}
```

## Current APIs Supported

✅ **LLMs**: OpenAI, Anthropic, Google, Cohere, Mistral, Groq  
✅ **Vector DBs**: Pinecone (HTTP + gRPC)  
✅ **Embeddings**: OpenAI, Voyage AI  
✅ **Audio**: OpenAI TTS/STT  
✅ **Images**: OpenAI DALL-E  
✅ **GraphQL**: Any GraphQL API  
✅ **gRPC**: Any gRPC API (ORCA or manual config)  
✅ **Custom**: ANY HTTP API (just add pricing!)

## Example: Track Stripe Payments

1. **Add pricing**:
```json
{
  "stripe:charges.create": {"per_call": 0.003},
  "stripe:subscriptions.create": {"per_call": 0.01}
}
```

2. **Use in code**:
```python
import httpx
from llmobserve import observe, section

observe(collector_url="http://localhost:8000")

with section("payment:charge"):
    response = httpx.post(
        "https://api.stripe.com/v1/charges",
        headers={"Authorization": f"Bearer {STRIPE_KEY}"},
        json={"amount": 1000, "currency": "usd"}
    )
    # ✅ Cost tracked: $0.003
```

## Example: Track Custom API

```python
import httpx
from llmobserve import observe, section

observe(collector_url="http://localhost:8000")

with section("custom:data_fetch"):
    response = httpx.get(
        "https://api.mycompany.com/v1/data",
        headers={"X-API-Key": "my-key"}
    )
    # ✅ Automatically tracked!
    # Add pricing: "mycompany:data": {"per_call": 0.0005}
```

## Updating Pricing via API

You can also update pricing via the API:

```bash
curl -X PUT http://localhost:8000/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "myapi:endpoint": {
      "per_call": 0.001
    }
  }'
```

## That's It!

**Any HTTP API** → Add pricing → Automatically tracked! 🚀

