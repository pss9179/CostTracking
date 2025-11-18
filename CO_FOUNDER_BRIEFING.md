# LLMObserve - Technical Briefing for Co-Founder

**Updated:** November 18, 2025  
**Status:** Production-ready, deployed, generating revenue

---

## 🎯 What We Built

**LLMObserve = Automatic LLM cost tracking for developers**

**Value prop:** Add 2 lines of code → see exactly what your LLM APIs cost → optimize what matters.

**Business model:** $8/month subscription, all features included.

---

## 🏗️ System Architecture (High-Level)

```
User's Python App
    ↓ (SDK patches HTTP clients)
LLMObserve Collector (Railway - FastAPI + PostgreSQL)
    ↓ (REST API)
Dashboard (Vercel - Next.js + React)
    ↓ (User views)
Browser
```

### **Components:**

1. **Python SDK** (`llmobserve` package on PyPI)
   - Patches HTTP clients at import time
   - Injects tracking headers into API requests
   - Buffers events, sends to collector every 500ms

2. **Collector Backend** (FastAPI on Railway)
   - Receives events via POST /events
   - Calculates costs using pricing database
   - Stores in PostgreSQL
   - Serves analytics endpoints

3. **Web Dashboard** (Next.js on Vercel)
   - Clerk authentication
   - Real-time cost visualization
   - Agent breakdown, trends, exports
   - Stripe integration ($8/month)

4. **AI Auto-Instrument** (NEW - KILLER FEATURE)
   - Backend `/api/ai-instrument` endpoint
   - Uses OUR Anthropic API key (included in subscription)
   - Claude analyzes Python code, suggests labels
   - CLI: `llmobserve preview` and `llmobserve instrument --auto-apply`
   - Creates .bak backup before changes
   - Works for ANY agent pattern (not framework-specific)

---

## 🔬 How Tracking Works (Technical)

### **Core Mechanism: HTTP Interception**

**Problem:** Users make LLM API calls (OpenAI, Anthropic, etc.). We need to track every call without manual logging.

**Solution:** Patch Python HTTP client libraries to inject tracking metadata.

### **Step-by-Step:**

1. **User installs SDK:**
   ```bash
   pip install llmobserve
   ```

2. **User adds 2 lines:**
   ```python
   import llmobserve
   llmobserve.observe(collector_url="...", api_key="...")
   ```

3. **SDK patches HTTP clients:**
   - `httpx.Client.send` → wrapped
   - `requests.Session.request` → wrapped
   - `aiohttp.ClientSession._request` → wrapped
   - `urllib3.PoolManager.request` → wrapped

4. **On every HTTP request, SDK injects headers:**
   ```
   X-LLMObserve-Run-ID: uuid
   X-LLMObserve-Span-ID: uuid
   X-LLMObserve-Section: agent:researcher
   X-LLMObserve-Customer-ID: customer_123
   X-LLMObserve-API-Key: user's API key
   ```

5. **Request goes to OpenAI/Anthropic/etc as normal**
   - No proxy, no man-in-the-middle
   - Request/response unchanged

6. **SDK reads response:**
   - Parses tokens, model, status
   - Creates event object
   - Adds to buffer

7. **Buffer flushes every 500ms:**
   ```
   POST https://llmobserve-production.up.railway.app/events
   Body: [event1, event2, event3, ...]
   ```

8. **Collector processes events:**
   - Validates API key (Clerk user ID)
   - Computes cost: `(input_tokens * input_price) + (output_tokens * output_price)`
   - Stores in PostgreSQL
   - Returns 201 Created

9. **Dashboard fetches data:**
   ```
   GET /runs (list of execution sessions)
   GET /events/provider-stats (cost breakdown)
   ```

10. **User sees real-time costs in browser**

---

## 💡 Key Technical Decisions

### **1. HTTP Interception vs SDK Monkey-Patching**

**Why HTTP?**
- ✅ Universal: Works with ANY API (LLMs, vector DBs, custom)
- ✅ Stable: SDKs change, HTTP doesn't
- ✅ Zero-config: No manual wrapping

**vs. Monkey-patching OpenAI SDK:**
- ❌ Breaks when OpenAI updates
- ❌ Only works for OpenAI (need separate code for Anthropic, Google, etc.)
- ❌ Fragile

### **2. No Proxy/MITM**

**We DON'T intercept traffic.**
- Requests go directly to OpenAI/Anthropic
- We just inject headers that WE read (providers ignore them)
- Safer, faster, no SSL issues

### **3. Batch Flushing**

Instead of one HTTP request per event:
- Buffer events in memory
- Flush every 500ms
- Send batch to collector

**Why?** Reduces network overhead, prevents rate limiting our own API.

### **4. Fail-Open Design**

If tracking fails (network error, API down, etc.):
- User's code continues normally
- We log the error, don't raise
- Never break user's production app

---

## 🤖 AI Auto-Instrumentation (NEW Feature)

### **The Problem:**
Users see "Untracked: $50" in dashboard. They think: "WTF is this? Which agent?"

### **The Solution:**
AI analyzes their code and adds labels automatically.

### **How It Works:**

1. **User runs CLI:**
   ```bash
   llmobserve preview my_agent.py
   ```

2. **CLI sends code to our backend:**
   ```
   POST https://llmobserve.com/api/ai-instrument
   Headers: Authorization: Bearer {user's LLMObserve API key}
   Body: { code: "...", file_path: "my_agent.py" }
   ```

3. **Backend calls Claude API (our key):**
   ```python
   anthropic.messages.create(
       model="claude-3-5-sonnet",
       messages=[{
           "role": "user",
           "content": f"Analyze this code and suggest where to add @agent decorators..."
       }]
   )
   ```

4. **Claude returns JSON:**
   ```json
   {
     "suggestions": [
       {
         "type": "decorator",
         "line_number": 15,
         "function_name": "research_agent",
         "suggested_label": "researcher",
         "reason": "Makes multiple LLM calls, orchestrates workflow"
       }
     ]
   }
   ```

5. **Backend returns to CLI**

6. **CLI shows suggestions to user:**
   ```
   Found 2 suggestions:
   1. Line 15 - Add @agent("researcher")
   2. Line 42 - Add @agent("writer")
   ```

7. **User applies (optional):**
   ```bash
   llmobserve instrument my_agent.py --auto-apply
   ```

8. **CLI modifies code:**
   - Creates `.bak` backup
   - Adds decorators/imports
   - Saves modified file

### **Why This is Smart:**
- Uses OUR Anthropic API key (included in $8/month)
- User doesn't need extra setup
- Cost per analysis: ~$0.01 (negligible)
- Works for ANY agent code (not just frameworks)
- **Killer UX:** Dashboard shows "Untracked costs" → button → one command → organized

### **User Flow:**
1. User sees "Untracked: $50" on dashboard
2. Clicks "✨ AI Auto-Instrument" button
3. Goes to docs, sees it's included
4. Runs: `llmobserve preview my_agent.py`
5. Sees suggestions, applies with `--auto-apply`
6. Dashboard now shows: "researcher: $30, writer: $20"

### **How AI Detects Agents:**
Claude is trained on millions of Python codebases. It recognizes:
- Function names (e.g., "agent", "researcher")
- LLM API calls (openai, anthropic, ANY provider)
- Control flow (loops, multiple calls)
- Comments/docstrings

**It's semantic analysis, not keyword matching.**

---

## 🗄️ Data Model

### **PostgreSQL Schema:**

**Table: `users`**
- `id` (UUID, primary key)
- `clerk_user_id` (string, unique) ← Clerk auth
- `api_key` (string, unique) ← For SDK auth
- `email`, `created_at`, etc.
- `stripe_customer_id`, `stripe_subscription_id`, `subscription_status`

**Table: `trace_events`**
- `id` (UUID, primary key)
- `run_id` (UUID) ← Groups one execution
- `span_id`, `parent_span_id` (UUID) ← Hierarchical tracing
- `section` (string) ← Label (e.g., "agent:researcher")
- `section_path` (string) ← Full path (e.g., "agent:researcher/tool:search")
- `provider` (string) ← "openai", "anthropic", etc.
- `model` (string) ← "gpt-4", "claude-3-5-sonnet", etc.
- `endpoint` (string) ← "/v1/chat/completions"
- `input_tokens`, `output_tokens` (int)
- `cost_usd` (decimal) ← Calculated
- `latency_ms` (int)
- `status` (string) ← "ok", "error", "rate_limited"
- `customer_id` (string, nullable) ← Multi-tenant tracking
- `tenant_id` (string) ← User's org/account
- `user_id` (UUID, foreign key → users)
- `created_at` (timestamp)

**Table: `pricing`**
- `id` (UUID)
- `provider`, `model` (string)
- `input_price_per_1k_tokens`, `output_price_per_1k_tokens` (decimal)
- `updated_at`

**Indexes:**
- `run_id` (for fast run queries)
- `user_id` (for fast user queries)
- `created_at` (for time-series queries)
- `section` (for agent breakdown)

---

## 💰 Pricing & Cost Calculation

### **How We Calculate Costs:**

1. **Get pricing from database:**
   ```sql
   SELECT input_price_per_1k_tokens, output_price_per_1k_tokens 
   FROM pricing 
   WHERE provider = 'openai' AND model = 'gpt-4'
   ```

2. **Calculate:**
   ```python
   cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
   ```

3. **Store in event:**
   ```python
   event.cost_usd = cost
   ```

### **Pricing Database:**
- Manually updated (for now)
- Future: Auto-sync with provider APIs
- Covers 40+ models across OpenAI, Anthropic, Google, Cohere, etc.

---

## 🔐 Authentication & Multi-Tenancy

### **User Auth (Clerk):**
- Web dashboard uses Clerk (email/password, OAuth)
- User signs up → gets Clerk `user_id`
- Backend generates API key → stores with `clerk_user_id`

### **SDK Auth:**
```python
llmobserve.observe(api_key="llm_abc123...")
```
- SDK sends API key in headers
- Backend validates: `SELECT user_id FROM users WHERE api_key = ?`
- Attaches `user_id` to all events

### **Multi-Tenant:**
Users can track costs per end-customer:
```python
from llmobserve import set_customer_id
set_customer_id("customer_xyz")
```
- Sets `customer_id` in context
- Injected into all API call headers
- Stored in events
- Dashboard can filter by customer

**Use case:** SaaS founder wants to see "Which customers cost me the most?"

---

## 🎨 Dashboard Features

### **What Users See:**

1. **Overview (24h)**
   - Total cost
   - Total calls
   - Avg cost per call
   - Trend vs last week

2. **Agent Breakdown**
   ```
   researcher: $20.00 (50 calls)
   writer: $15.00 (30 calls)
   Untracked: $5.00 (10 calls)  ← Unlabeled costs
   ```

3. **Provider Breakdown**
   ```
   OpenAI (gpt-4): $30.00
   Anthropic (claude-3-5-sonnet): $10.00
   ```

4. **Time Series Chart**
   - Daily costs for last 7/30 days
   - Stacked by provider

5. **Runs List**
   - Each execution session
   - Click to see detailed trace

6. **Export**
   - CSV or JSON
   - All events or filtered

7. **Settings**
   - API key management
   - Spending caps
   - Subscription (Stripe)

### **"Untracked" Costs (Key UX):**
If user doesn't label agents, costs still show up as "Untracked."

**Why?** Transparency. Nothing hidden. Clear signal: "You should label these."

**CTA:**
```
[📚 Learn How to Label]  [✨ AI Auto-Instrument]
```

---

## 💳 Stripe Integration

### **Subscription Flow:**

1. User signs up (Clerk)
2. Redirected to onboarding
3. "Subscribe Now - $8/month" button
4. Redirects to Stripe Checkout
5. Stripe creates subscription
6. Webhook fires → our backend updates user:
   ```python
   user.subscription_status = "active"
   user.stripe_customer_id = event.customer
   ```
7. User can access dashboard

### **Promo Codes:**
```python
# Backend checks promo code
if promo_code in ["FREETEST", "TEST2024", "BETA"]:
    user.subscription_status = "active"
    user.subscription_tier = "pro"
```

---

## 📈 Metrics We Track (Internal)

**User Metrics:**
- Signups, active users, churn
- API keys generated
- Subscriptions (Stripe)

**Usage Metrics:**
- Events ingested per day
- Cost tracked (total across all users)
- Top agents, providers, models

**Performance:**
- Collector API latency (p50, p95)
- Buffer flush time
- Database query time

---

## 🚀 Deployment

### **Frontend (Vercel):**
- GitHub integration (auto-deploy on push)
- Environment: Node.js 18
- Env vars: Clerk keys, API URL

### **Backend (Railway):**
- Python 3.11
- PostgreSQL 15
- Env vars: Database URL, Clerk secret, Anthropic key

### **SDK (PyPI):**
```bash
cd sdk/python
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

## 🔧 Tech Stack

**Frontend:**
- Next.js 14 (React, TypeScript)
- Tailwind CSS + shadcn/ui
- Clerk (auth)
- Stripe (payments)
- Recharts (charts)

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL (Railway)
- SQLModel (ORM)
- Pydantic (validation)

**SDK:**
- Python 3.8+
- httpx, requests, aiohttp (patching)
- contextvars (context propagation)

**AI:**
- Claude 3.5 Sonnet (Anthropic API)

---

## 🎯 Key Differentiators

### **vs. Helicone, LangSmith, etc.:**

| Feature | LLMObserve | Competitors |
|---------|-----------|------------|
| Setup | 2 lines | 10-50 lines |
| Framework | Any (HTTP-based) | Specific SDKs |
| Cost | $8/month | $50-500/month |
| AI Labeling | ✅ Included | ❌ Manual |
| Multi-Tenant | ✅ Built-in | ⚠️ Enterprise only |
| Untracked Costs | ✅ Visible | ❌ Hidden |

### **Why We're Better:**
1. **HTTP interception** = works with ANY API, not just specific SDKs
2. **AI auto-labeling** = one command vs hours of manual work
3. **Transparent** = "untracked" bucket shows everything
4. **Simple** = 2 lines to start, optional labeling for organization
5. **Cheap** = $8/month vs $50-500

---

## 🐛 Known Issues / Future Work

### **Current Limitations:**
1. **Pricing updates** - Manual (need auto-sync)
2. **Alerts** - Basic (need email/Slack notifications)
3. **Multi-language** - Python only (JS/TypeScript next)
4. **Trace UI** - Basic (need flamegraph/waterfall view)

### **Roadmap:**
1. **Q4 2024:**
   - Auto pricing sync
   - Email alerts
   - Team accounts

2. **Q1 2025:**
   - JavaScript SDK
   - Flamegraph trace view
   - Anomaly detection

3. **Q2 2025:**
   - Self-hosted option
   - Enterprise plan
   - Advanced analytics

---

## 📊 Business Metrics (As of Nov 2024)

**Users:**
- X signups
- Y paying subscribers
- Z% conversion rate

**Revenue:**
- $Y MRR
- $Z total revenue

**Usage:**
- X million events tracked
- $Y total cost tracked (across all users)

*(Fill in actual numbers)*

---

## 🆘 Support & Operations

### **User Support:**
- Email: support@llmobserve.com
- Docs: llmobserve.com/docs
- Response time: < 24h

### **Monitoring:**
- Vercel analytics (frontend)
- Railway logs (backend)
- Sentry (error tracking - TODO)

### **Incident Response:**
1. Check Railway logs
2. Check Vercel deployment
3. Check PostgreSQL status
4. Roll back if needed (git revert + redeploy)

---

## 🔑 Environment Variables (Critical)

### **Frontend (Vercel):**
```
NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-production.up.railway.app
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
ANTHROPIC_API_KEY=sk-ant-...
```

### **Backend (Railway):**
```
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...
```

---

## 📚 Important Files

- `HOW_TRACKING_WORKS.md` - Complete technical deep-dive
- `EXAMPLE_USER_FLOW.md` - End-to-end user scenario
- `DEPLOYMENT_READINESS.md` - Production checklist
- `README.md` - Public-facing docs

---

## 💪 Strengths

1. **Simple UX** - 2 lines of code, instant value
2. **Universal** - Works with any HTTP-based API
3. **AI-powered** - Auto-instrumentation included
4. **Transparent** - "Untracked" bucket, nothing hidden
5. **Affordable** - $8/month vs $50-500 competitors

---

## ⚠️ Risks

1. **Pricing changes** - If OpenAI/Anthropic change pricing, we need to update manually
2. **SDK updates** - If HTTP clients change internals, patching breaks (rare but possible)
3. **Competition** - Big players (Datadog, New Relic) could enter space
4. **Scalability** - PostgreSQL may need sharding at 10M+ events/day

---

## 🎓 What You Need to Know

### **If User Reports "Costs Not Tracked":**
1. Check API key is valid (Settings page)
2. Check `observe()` is called before any API calls
3. Check HTTP client is supported (`httpx`, `requests`, `aiohttp`, `urllib3`)
4. Check logs for SDK errors

### **If Dashboard Shows Wrong Costs:**
1. Check pricing database for that provider/model
2. Check event `input_tokens` and `output_tokens` are correct
3. Check for duplicate events (idempotency issue)

### **If AI Instrumentation Fails:**
1. Check ANTHROPIC_API_KEY is set in Vercel
2. Check user's API key is valid
3. Check Claude API quota/rate limits

---

## 🚀 Quick Commands

```bash
# Deploy frontend
cd web && vercel --prod

# Deploy backend (auto via Railway)
git push origin main

# Publish SDK to PyPI
cd sdk/python
python setup.py sdist bdist_wheel
twine upload dist/*

# Run tests
cd collector && pytest
cd sdk/python && pytest
```

---

## 📞 Contact

- **Pranav:** [your email]
- **Co-founder:** [co-founder email]
- **Support:** support@llmobserve.com

---

**Last Updated:** November 18, 2025  
**Version:** 0.3.0  
**Status:** Production, revenue-generating

