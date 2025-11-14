# 🚀 Track ANY API - Complete Guide

## YES - This Can Track ANY API! 

The system uses a **reverse proxy** that intercepts ALL HTTP requests, so it can track costs for literally **ANY HTTP API**.

## How It Works

```
Your Code → HTTP Request → SDK Intercepts → Proxy → Actual API → Parse Response → Calculate Cost → Track!
```

1. **SDK intercepts** all HTTP requests (httpx/requests/aiohttp)
2. **Routes through proxy** (adds context headers)
3. **Proxy forwards** to actual API
4. **Proxy parses response** and calculates cost
5. **Emits event** to collector

## Quick Start: Track Any API

### Step 1: Initialize Tracking

```python
from llmobserve import observe, section
import httpx

# Initialize - proxy intercepts ALL HTTP calls
observe(
    collector_url="http://localhost:8000",
    proxy_url="http://localhost:9000"
)
```

### Step 2: Add Pricing

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
  }
}
```

### Step 3: Make API Calls

```python
# ANY HTTP call is automatically tracked!
with section("payment:process"):
    response = httpx.post(
        "https://api.stripe.com/v1/charges",
        headers={"Authorization": "Bearer sk_..."},
        json={"amount": 1000}
    )
    # ✅ Automatically tracked with cost!
```

## Pricing Formats Supported

### 1. Per-Call Pricing
```json
{
  "myapi:endpoint": {
    "per_call": 0.001  // $0.001 per call
  }
}
```

### 2. Token-Based Pricing
```json
{
  "myapi:llm": {
    "input": 0.000001,   // per input token
    "output": 0.000002   // per output token
  }
}
```

### 3. Per Million Pricing
```json
{
  "myapi:operations": {
    "per_million": 10.0  // $10 per million operations
  }
}
```

### 4. Character-Based Pricing
```json
{
  "myapi:tts": {
    "per_1k_chars": 0.015  // $0.015 per 1k characters
  }
}
```

### 5. Duration-Based Pricing
```json
{
  "myapi:audio": {
    "per_minute": 0.006  // $0.006 per minute
  }
}
```

## Currently Supported APIs (37+)

✅ **LLMs**: OpenAI, Anthropic, Google, Cohere, Mistral, Groq, AI21, HuggingFace, Together, Replicate, Perplexity, Azure OpenAI, AWS Bedrock

✅ **Voice AI**: ElevenLabs, AssemblyAI, Deepgram, PlayHT, Azure Speech, AWS Polly, AWS Transcribe

✅ **Embeddings**: OpenAI, Voyage AI

✅ **Images/Video**: Stability AI, Runway, AWS Rekognition

✅ **Vector DBs**: Pinecone, Weaviate, Qdrant, Milvus, Chroma, MongoDB Vector, Redis Vector, Elasticsearch Vector

✅ **Search**: Algolia

✅ **Payments**: Stripe, PayPal

✅ **Communication**: Twilio, SendGrid

✅ **GraphQL**: Any GraphQL API

✅ **gRPC**: Any gRPC API (ORCA or manual config)

✅ **Custom**: ANY HTTP API (just add pricing!)

## Examples

### Example 1: Track Stripe Payments

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
    # ✅ Cost tracked: $0.003 (if pricing added)
```

### Example 2: Track Custom API

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

### Example 3: Track Multiple APIs in One Flow

```python
from llmobserve import observe, section
import httpx

observe(collector_url="http://localhost:8000")

with section("agent:research"):
    # Call OpenAI
    with section("llm:query"):
        response = httpx.post("https://api.openai.com/v1/chat/completions", ...)
    
    # Call Pinecone
    with section("vector:search"):
        response = httpx.post("https://api.pinecone.io/query", ...)
    
    # Call Custom API
    with section("custom:enrich"):
        response = httpx.get("https://api.example.com/enrich", ...)
    
    # All tracked in hierarchical tree!
```

## Updating Pricing

### Via File
Edit `collector/pricing/registry.json`

### Via API
```bash
curl -X PUT http://localhost:8000/pricing \
  -H "Content-Type: application/json" \
  -d '{
    "myapi:endpoint": {
      "per_call": 0.001
    }
  }'
```

## Provider Detection

The proxy automatically detects providers from URLs:
- `api.stripe.com` → `stripe`
- `api.twilio.com` → `twilio`
- `api.openai.com` → `openai`
- `api.mycompany.com` → `unknown` (add pricing as `mycompany:endpoint`)

## That's It!

**Any HTTP API** → Add pricing → Automatically tracked! 🎯

Check your dashboard at `http://localhost:3000` to see all tracked calls!

