# How LLMObserve Tracking Works

## Complete System Architecture

### 1. **Cost Tracking - How We Capture Every API Call**

#### HTTP Interception (Core Mechanism)
- **What:** We patch Python HTTP clients (`httpx`, `requests`, `aiohttp`, `urllib3`) at import time
- **When:** Happens automatically when user calls `observe()`
- **How:** Every outgoing HTTP request gets intercepted BEFORE it's sent

**Flow:**
```
User Code → HTTP Client → [Our Patch] → Add Headers → Send Request → Capture Response
```

**What We Inject:**
- `X-LLMObserve-Run-ID`: Unique ID for this execution session
- `X-LLMObserve-Span-ID`: Unique ID for this specific API call
- `X-LLMObserve-Parent-Span-ID`: Links to parent operation (for hierarchies)
- `X-LLMObserve-Section`: Current label (e.g., "agent:researcher")
- `X-LLMObserve-Section-Path`: Full hierarchy (e.g., "agent:researcher/tool:web_search")
- `X-LLMObserve-Customer-ID`: End-user identifier (optional)
- `X-LLMObserve-Timestamp`: Client timestamp (for clock skew detection)

**What We Track:**
- Provider (OpenAI, Anthropic, Google, Pinecone, etc.) - detected from URL
- Model name - extracted from response
- Input/output tokens - parsed from response body
- Cost - calculated using our pricing database
- Latency - measured from request start to response end
- Status - success/error/rate-limited

#### Cost Calculation
- **Where:** Backend (`collector/pricing.py`)
- **When:** When events are ingested
- **How:** `compute_cost(provider, model, input_tokens, output_tokens)`
- **Database:** PostgreSQL table `pricing` with per-model token costs
- **Formula:** `(input_tokens * input_price) + (output_tokens * output_price)`

---

### 2. **Agent & Workflow Tracking - How We Organize Costs**

#### Manual Labeling (Primary Method)
Users have **3 ways** to label their code:

**A) `section()` Context Manager**
```python
with section("agent:researcher"):
    with section("tool:web_search"):
        # API calls here are labeled automatically
        response = openai_call()
```

**B) `@agent` Decorator**
```python
@agent("researcher")
def my_agent_function():
    # All API calls in this function are labeled
    response = openai_call()
```

**C) `wrap_all_tools()` for Frameworks**
```python
tools = [web_search, calculator]
wrapped_tools = wrap_all_tools(tools)  # Each tool gets labeled
agent = Agent(tools=wrapped_tools)
```

#### How Labels Propagate
- **Storage:** `contextvars` (thread-safe, async-safe)
- **Stack:** Labels are pushed/popped as code enters/exits sections
- **Hierarchy:** Section path is built as: `"agent:researcher/tool:web_search/step:analyze"`

**Example Flow:**
```
1. User enters: with section("agent:researcher")
   → Stack: ["agent:researcher"]
   
2. User enters: with section("tool:web_search")
   → Stack: ["agent:researcher", "tool:web_search"]
   
3. HTTP interceptor reads stack
   → Injects: X-LLMObserve-Section-Path: "agent:researcher/tool:web_search"
   
4. User exits tool section
   → Stack: ["agent:researcher"]
   
5. User exits agent section
   → Stack: []
```

---

### 3. **Step Classification - How We Organize UI**

#### Event Types
Every tracked event has a `span_type`:
- `"llm"` - LLM API calls (OpenAI, Anthropic, etc.)
- `"vector_db"` - Vector database calls (Pinecone, Weaviate, etc.)
- `"tool"` - Wrapped tool calls
- `"section"` - User-defined sections (for timing, no cost)
- `"http_fallback"` - Unclassified HTTP calls (any API we don't recognize)

#### Label Prefixes (Semantic Meaning)
Users can use semantic prefixes in their labels:
- `agent:` → Orchestrators or autonomous agents
- `tool:` → External API or function calls
- `step:` → Multi-step logic or workflows
- No prefix → Generic label

**Example:**
```python
with section("agent:researcher"):      # Agent-level tracking
    with section("tool:web_search"):   # Tool-level tracking
        with section("step:parse"):    # Step-level tracking
            # API call here
```

#### Dashboard Grouping Logic
**How Costs Are Aggregated:**

1. **Agent View** (`/agents`)
   - Groups all events by `section` label (first segment)
   - Events with `agent:` prefix → shown as agents
   - Events without any label → grouped under "untracked"
   
2. **Runs View** (`/runs`)
   - Groups by `run_id` (one run = one execution session)
   - Shows timeline of all events in that run
   
3. **Provider View** (`/costs`)
   - Groups by `provider` (OpenAI, Anthropic, etc.)
   - Shows cost breakdown by model

4. **Insights View** (`/insights`)
   - Aggregates across time windows
   - Shows trends, anomalies, top spenders

---

### 4. **"Untracked" Costs - What Happens When There's No Label**

#### Problem
User makes API calls but doesn't wrap them in `section()` or `@agent`.

#### Solution
- HTTP interceptor **still captures the cost** (nothing is hidden)
- Backend marks event with `section = "default"` or `section = "untracked"`
- Dashboard shows this in a special "Untracked" bucket

**UI Display:**
```
Agent Costs:
├─ researcher: $20.00
├─ writer: $15.00
└─ Untracked: $5.00  ← API calls without labels
```

**Why This Is Good:**
- User sees ALL costs, even unlabeled ones
- Clear signal: "You should label these!"
- No surprises in billing

---

### 5. **Data Flow - End to End**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER CODE                                                    │
│    with section("agent:researcher"):                            │
│        response = openai.ChatCompletion.create(...)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. HTTP INTERCEPTOR (SDK)                                       │
│    - Captures request before it's sent                          │
│    - Injects headers (Run ID, Span ID, Section, Customer)      │
│    - Routes through proxy (optional)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. API PROVIDER (OpenAI, Anthropic, etc.)                       │
│    - Processes request normally                                 │
│    - Returns response with token counts                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. HTTP INTERCEPTOR (SDK)                                       │
│    - Captures response                                          │
│    - Extracts tokens, model, status                             │
│    - Creates event object                                       │
│    - Adds to buffer                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. BUFFER & FLUSH (SDK)                                         │
│    - Batches events every 500ms                                 │
│    - Sends to collector via POST /events                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. COLLECTOR API (Backend)                                      │
│    - Receives batch of events                                   │
│    - Validates user API key                                     │
│    - Computes cost using pricing database                       │
│    - Checks for duplicates (idempotency)                        │
│    - Stores in PostgreSQL                                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. DATABASE (PostgreSQL)                                        │
│    Table: trace_events                                          │
│    Columns:                                                     │
│      - id, run_id, span_id, parent_span_id                      │
│      - section, section_path                                    │
│      - provider, model, endpoint                                │
│      - input_tokens, output_tokens, cost_usd                    │
│      - latency_ms, status                                       │
│      - customer_id, tenant_id                                   │
│      - created_at                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. DASHBOARD (Next.js)                                          │
│    - Queries events via GET /runs, GET /events/provider-stats  │
│    - Aggregates by agent, provider, time window                 │
│    - Displays charts, tables, costs                             │
│    - Shows "Untracked" for unlabeled costs                      │
└─────────────────────────────────────────────────────────────────┘
```

---

### 6. **What We Track vs What We Miss**

#### ✅ What We Track (Automatically)
- **All HTTP/HTTPS APIs:** OpenAI, Anthropic, Google, Cohere, Together, Hugging Face, etc.
- **Vector Databases:** Pinecone, Weaviate, Qdrant, Chroma (any HTTP-based)
- **Custom APIs:** Any API your code calls (shows as "http_fallback" if unknown)
- **All Protocols We Patch:**
  - `httpx` (sync + async)
  - `requests`
  - `aiohttp`
  - `urllib3`
  - `grpc` (gRPC over HTTP)
  - `websockets`

#### ⚠️ What We Miss (Edge Cases)
- **Native sockets:** If code uses raw `socket` library (rare)
- **Subprocess calls:** If code shells out to `curl` or external binaries
- **Non-Python code:** If calling C extensions or Rust that bypass Python HTTP
- **File I/O:** Local file operations (no cost to track)

**Reality Check:** 99.9% of LLM/AI APIs use HTTP. We catch everything that matters.

---

### 7. **Key Design Decisions**

#### Why HTTP Interception?
- **Universal:** Works with ANY API without SDK-specific code
- **Stable:** SDKs change, HTTP doesn't
- **Zero-config:** No manual wrapping for every API call

#### Why No Auto-Detection by Default?
- **Too magical:** Import-time patching is unpredictable
- **Framework fragility:** LangChain/CrewAI internals change constantly
- **Debugging hell:** Users don't expect side effects from imports

#### Why "Untracked" Category?
- **Transparency:** Never hide costs from users
- **Onboarding signal:** Shows what needs labeling
- **Fail-open design:** If labeling breaks, costs still appear

---

### 8. **Current Capabilities Summary**

| Feature | Status | How It Works |
|---------|--------|--------------|
| **Cost Tracking** | ✅ Production | HTTP interception on all requests |
| **Agent Labeling** | ✅ Production | `section()`, `@agent`, `wrap_all_tools()` |
| **Step Hierarchy** | ✅ Production | Nested sections build path |
| **Untracked Costs** | ✅ Production | Dashboard groups unlabeled costs |
| **Provider Detection** | ✅ Production | URL pattern matching |
| **Token Parsing** | ✅ Production | Response body parsing |
| **Cost Calculation** | ✅ Production | Pricing database lookup |
| **Spending Caps** | ✅ Production | Pre-request checks |
| **Customer Filtering** | ✅ Production | Multi-tenant isolation |
| **Export (CSV/JSON)** | ✅ Production | Client-side data export |
| **Real-time Updates** | ✅ Production | 30-second polling |

---

## Summary: The Core Value Proposition

**What we do better than anyone:**
1. **Zero-config cost tracking** - Just call `observe()`, costs appear automatically
2. **Nothing is hidden** - "Untracked" bucket shows unlabeled costs
3. **Stable** - No fragile SDK monkey-patching, pure HTTP interception
4. **Universal** - Works with any API (LLMs, vector DBs, custom APIs)
5. **Optional organization** - Label what matters, ignore the rest

**What we DON'T do:**
- Automatic framework detection (too fragile)
- Auto-wrapping at import (too magical)
- Guessing what code does (too unreliable)

**Philosophy:** Capture everything, make labeling easy but optional, never hide costs.

