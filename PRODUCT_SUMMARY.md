# LLMObserve Product Summary

## What We Built

**LLMObserve** is an automatic cost tracking and observability platform for AI agents and LLM applications. It tracks costs across ALL APIs (not just LLMs) and provides semantic cost attribution without requiring code changes.

---

## Key Features

### 1. **Automatic Cost Tracking (Zero Code Changes)**
- Patches HTTP clients (`httpx`, `requests`, `aiohttp`, `urllib3`) automatically
- Intercepts ALL API calls at network level
- No decorators, no wrappers, no code changes needed
- Just call `llmobserve.observe(api_key="...")` once

### 2. **Universal API Coverage (37+ Providers)**
Tracks costs for:
- **LLMs**: OpenAI, Anthropic, Google Gemini, Cohere, Mistral, etc.
- **Voice AI**: ElevenLabs, Twilio, AssemblyAI, Deepgram
- **Vector DBs**: Pinecone, Weaviate, Qdrant, Milvus, Chroma
- **Payments**: Stripe, PayPal
- **Communication**: Twilio, SendGrid
- **Any HTTP API**: Just add pricing config

### 3. **Semantic Cost Attribution**
- CLI command (`llmobserve analyze .`) scans codebase
- Automatically infers semantic labels from file structure
- Maps `file:function → semantic_label` (e.g., "Summarization", "Botting")
- Dashboard shows: "Summarization: $45.20 (60%)"

### 4. **Step-by-Step Agent Execution Tracking**
Shows complete agent execution with ALL API calls:
```
Agent Run: abc-123
├─ Step 1: OpenAI call → $0.12
├─ Step 2: Twilio SMS → $0.01
├─ Step 3: Pinecone query → $0.003
├─ Step 4: Stripe charge → $0.003
└─ Step 5: OpenAI call → $0.08
Total: $0.216
```

### 5. **Per-Customer Cost Tracking**
- Track costs per customer/end-user
- Set spending caps per customer
- Generate invoices based on usage

### 6. **Real-Time Dashboard**
- Cost breakdown by provider, semantic section, customer
- Execution traces with step-by-step costs
- Spending alerts and budget limits
- Historical trends and analytics

---

## How It Works

### Architecture

**1. SDK (Python)**
- Patches HTTP clients at import time
- Intercepts all API calls automatically
- Extracts costs from responses (tokens, pricing)
- Buffers events locally
- Flushes to collector backend

**2. CLI Tool**
- `llmobserve analyze .` - Scans codebase for semantic sections
- Uses AST parsing + heuristics to infer semantic labels
- Creates `.llmobserve/semantic_map.json`
- Maps file:function → semantic_label

**3. Backend Collector**
- Receives events from SDK
- Calculates costs using pricing database
- Stores in PostgreSQL
- Provides REST API for dashboard

**4. Dashboard (Next.js)**
- Real-time cost visualization
- Semantic cost breakdown
- Execution traces
- Customer management
- Settings and API key management

---

## Technical Implementation

### HTTP Interception
```python
# SDK patches HTTP clients:
original_send = httpx.Client.send

def patched_send(request):
    # Inject context headers
    request.headers["X-LLMObserve-Run-ID"] = run_id
    request.headers["X-LLMObserve-Section"] = current_section
    
    # Make request
    response = original_send(request)
    
    # Extract costs from response
    event = create_event_from_response(response)
    buffer.add_event(event)
    
    return response
```

### Semantic Mapping
```python
# CLI analyzes codebase:
# agents/summarizer.py → "Summarization"
# streaming/twitch.py → "TwitchStreaming"
# bot/response.py → "Botting"

# SDK uses semantic map at runtime:
def summarize_article():
    response = openai.ChatCompletion.create(...)
    # SDK looks up: "agents/summarizer.py" → "Summarization"
    # Tags cost: {semantic_label: "Summarization", cost: $0.15}
```

### Cost Calculation
- Pricing database with per-model token costs
- Formula: `(input_tokens * input_price) + (output_tokens * output_price)`
- Supports per-call, per-minute, per-request pricing
- Handles batch APIs, rate limits, retries

---

## What Makes It Unique

### vs Paid.ai
- **Paid.ai**: Requires manual Signals (`signal("email_sent")`), focuses on LLMs, manual decorators
- **LLMObserve**: Automatic tracking, tracks ALL APIs, zero code changes, semantic analysis

### vs LangSmith/Helicone
- **LangSmith/Helicone**: Focus on LLM costs, execution traces
- **LLMObserve**: Tracks ALL APIs (LLMs + Twilio + Stripe + Pinecone), semantic cost attribution

### Key Differentiators
1. **Automatic** - Zero code changes, works out of the box
2. **Universal** - Tracks ALL APIs, not just LLMs
3. **Semantic** - Automatically identifies expensive code sections
4. **Complete** - Shows step-by-step agent execution with all API costs

---

## User Flow

### Setup (3 Steps)
1. **Get API Key**: Dashboard → Settings → Create API Key
2. **Install**: `pip install llmobserve`
3. **Analyze**: `llmobserve analyze .` (creates semantic map)
4. **Use**: `llmobserve.observe(api_key="...")` in code

### Runtime
- SDK automatically intercepts all API calls
- Tags costs with semantic labels
- Sends events to backend
- Dashboard shows real-time costs

### Dashboard
- View costs by provider, semantic section, customer
- See execution traces with step-by-step costs
- Set spending caps and alerts
- Generate invoices

---

## Current Status

### ✅ Implemented
- HTTP interception (httpx, requests, aiohttp, urllib3)
- Cost tracking for 9+ providers (OpenAI, Anthropic, Pinecone, Stripe, Twilio, etc.)
- Semantic analysis CLI (`llmobserve analyze`)
- Dashboard with cost breakdown
- Per-customer tracking
- Spending caps

### 🚧 In Progress
- More provider instrumentors (28 providers planned)
- Enhanced semantic analysis (AI-based vs heuristic)
- Execution visualization improvements
- gRPC and WebSocket support

### 📋 Planned
- Multi-language SDKs (Node.js, Go, Ruby, Java)
- Advanced analytics and insights
- Cost optimization recommendations
- Team collaboration features

---

## Tech Stack

- **SDK**: Python (httpx, requests, aiohttp patching)
- **CLI**: Python (AST parsing, semantic analysis)
- **Backend**: Python FastAPI, PostgreSQL
- **Dashboard**: Next.js, TypeScript, Tailwind CSS
- **Auth**: Clerk (authentication, organizations)
- **Deployment**: Docker, cloud-ready

---

## Value Proposition

**For Solo Developers:**
- See where your money is going
- Optimize expensive features
- Set budgets and alerts
- No code changes needed

**For SaaS Founders:**
- Track costs per customer
- Bill customers accurately
- Set spending caps per customer
- Understand profitability

**For Teams:**
- Shared cost visibility
- Team budgets and alerts
- Cost optimization insights
- Execution debugging

---

## Key Metrics Tracked

- **Cost**: Per API call, per provider, per semantic section, per customer
- **Usage**: Token counts, request counts, latency
- **Execution**: Step-by-step agent runs with costs
- **Trends**: Historical costs, cost changes, spending patterns

---

## Example Use Cases

1. **AI Agent Cost Optimization**
   - Identify expensive semantic sections
   - Optimize high-cost features
   - Switch to cheaper models where appropriate

2. **Per-Customer Billing**
   - Track costs per customer
   - Generate accurate invoices
   - Set spending limits per customer

3. **Budget Management**
   - Set monthly spending caps
   - Get alerts at 80% threshold
   - Block requests at limit

4. **Debugging Expensive Operations**
   - See step-by-step execution costs
   - Identify slow/expensive API calls
   - Debug cost spikes

---

## Questions for Discussion

1. How does this compare to Paid.ai's approach?
2. What are the trade-offs between auto-instrumentation vs manual tagging?
3. How can we improve semantic analysis accuracy?
4. What features would make this more valuable?
5. How should we position this vs competitors?
6. What's the best go-to-market strategy?

