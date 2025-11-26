# LLMObserve - Automatic LLM Cost Tracking

**Track every LLM API call. Know exactly what you're spending. Optimize what matters.**

> Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers.  
> Just 2 lines of code. $5/month.

---

## 🚀 Quick Start (60 seconds)

### 1. Install
```bash
pip install llmobserve
```

### Node.js / TypeScript
```bash
npm install llmobserve
```

### 2. Get Your API Key
Go to **https://llmobserve.com/settings** → Create API Key

### 3. Add to Your Code (2 lines!)
```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"  # Get from https://llmobserve.com/settings
)

# That's it! All your LLM calls are now tracked automatically.
```

### Node.js / TypeScript
```typescript
import { observe } from 'llmobserve';

observe({
  collectorUrl: "http://localhost:8000", // Or your production URL
  apiKey: "YOUR_API_KEY_HERE"
});

// Now use OpenAI/Anthropic/etc as normal
import OpenAI from 'openai';
const client = new OpenAI();
// ...
```

### 4. View Your Dashboard
**https://llmobserve.com/dashboard**

---

## ✨ What You Get

### 1. **Automatic Cost Tracking**
- Every LLM API call is tracked automatically
- Real-time cost calculation with up-to-date pricing
- Works with ANY HTTP-based API (LLMs, vector DBs, custom APIs)

### 2. **Beautiful Dashboard**
- See costs by provider, model, agent, customer, time
- Real-time updates
- Export to CSV/JSON
- "Untracked" bucket shows unlabeled costs (nothing hidden)

### 3. **Multi-Tenant Support**
- Track costs per customer (perfect for SaaS)
- Isolated data views
- Customer-level analytics

### 4. **Spending Caps**
- Set per-customer, per-agent, or global caps
- Proactive blocking before overspend
- Configurable limits

---

## 📦 Complete Example

```python
# Step 1: Initialize llmobserve (add this at the top of your main file)
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_your_key_here"  # Get from https://llmobserve.com/settings
)

# Step 2: Use your LLM libraries normally - they're tracked automatically!
from openai import OpenAI

client = OpenAI(api_key="your-openai-key")

# This call is automatically tracked - no changes needed!
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)

# View your costs at: https://llmobserve.com/dashboard
```

---

## 🎯 How It Works

### **Zero-Config Tracking**
We patch Python HTTP clients (`httpx`, `requests`, `aiohttp`, `urllib3`) to inject tracking headers. No SDK-specific code. Works with ANY API.

```python
import llmobserve
from openai import OpenAI

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="your-key"
)

client = OpenAI()
response = client.chat.completions.create(...)  # ← Automatically tracked!
```

### **Optional Labeling (Organize Costs)**
Add labels to see which agents/tools cost the most:

```python
from llmobserve import section

# Track costs by feature
with section("user_query"):
    response = client.chat.completions.create(...)

with section("data_processing"):
    response = client.chat.completions.create(...)

# View breakdown by section in dashboard!
```

### **Multi-Tenant Tracking**
Track costs per customer for SaaS applications:

```python
from llmobserve import set_customer_id

set_customer_id("customer_123")
response = client.chat.completions.create(...)

# View per-customer costs in dashboard!
```

---

## 📊 What We Track

### ✅ **Automatically Tracked**
- **LLM Providers:** OpenAI, Anthropic, Google, Cohere, Together, Hugging Face, Perplexity, Groq, Mistral, and 40+ more
- **Vector DBs:** Pinecone, Weaviate, Qdrant, Chroma (any HTTP-based)
- **Custom APIs:** Any HTTP API your code calls
- **Protocols:** HTTP/HTTPS, gRPC, WebSockets

### 📈 **Metrics Collected**
- Cost (USD with real-time pricing)
- Token usage (input + output)
- Latency (ms)
- Provider, model, endpoint
- Status (success/error/rate-limited)
- Customer ID (multi-tenant)
- Agent/tool labels (optional)

---

## 🎨 Features

### **Cost Tracking**
- Real-time cost calculation
- Per-call, per-agent, per-customer breakdown
- 40+ LLM providers supported
- Automatic pricing updates

### **Agent Tracking**
- Label agents with `section("agent:name")`
- Hierarchical tracking (agent → tool → step)
- "Untracked" bucket for unlabeled costs
- Nothing hidden

### **Multi-Tenancy**
- Track costs per end-customer
- Isolated data views
- Perfect for SaaS businesses

### **Spending Caps**
- Set per-customer, per-agent, or global caps
- Proactive blocking before overspend
- Configurable limits

### **Analytics**
- Daily/weekly/monthly trends
- Provider cost breakdown
- Model usage analysis
- Export to CSV/JSON

---

## 🛠️ Advanced Usage

### **Customer Tracking (SaaS)**
```python
from llmobserve import set_customer_id

set_customer_id("customer_123")  # Track this customer's costs
```

### **Hierarchical Tracing**
```python
from llmobserve import section

with section("agent:researcher"):
    with section("tool:web_search"):
        # Tracked as "agent:researcher/tool:web_search"
        search_results = api_call()
    
    with section("tool:summarize"):
        summary = llm_call()
```

### **Framework Integration**
```python
# Works with:
# - LangChain
# - CrewAI
# - AutoGen
# - LlamaIndex
# - Any framework that uses HTTP APIs
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│ Your Code + llmobserve SDK                           │
│  → Patches HTTP clients (httpx, requests, aiohttp)  │
│  → Injects tracking headers                          │
└─────────────────┬────────────────────────────────────┘
                  │
                  ↓ POST /events (batch, every 500ms)
┌──────────────────────────────────────────────────────┐
│ Collector API (Railway)                              │
│  → Calculates costs (pricing database)              │
│  → Stores events (PostgreSQL)                        │
│  → Serves analytics endpoints                        │
└─────────────────┬────────────────────────────────────┘
                  │
                  ↓ GET /runs, /events, /stats
┌──────────────────────────────────────────────────────┐
│ Dashboard (Next.js on Vercel)                        │
│  → Shows costs, trends, breakdowns                   │
│  → Real-time updates                                 │
│  → Export to CSV/JSON                                │
└──────────────────────────────────────────────────────┘
```

**Key Design:**
- **HTTP Interception:** Universal, SDK-agnostic, stable
- **No Monkey-Patching:** Works when SDKs update
- **Fail-Open:** If tracking breaks, your app continues

---

## 💰 Pricing

**$5/month** - Unlimited tracking, all features included:
- ✅ Unlimited API calls tracked
- ✅ All providers (40+)
- ✅ Multi-tenant support
- ✅ Spending caps
- ✅ Export to CSV/JSON
- ✅ Priority support

**Try it:** https://llmobserve.com

---

## 🔧 Development

### **Project Structure**
- `/web` - Next.js dashboard (Vercel)
- `/collector` - FastAPI backend (Railway)
- `/sdk/python` - Python SDK package
- `/docs` - Documentation

### **Local Development**
```bash
# Run collector locally
cd collector
python -m uvicorn main:app --reload --port 8000

# Run web dashboard
cd web
npm install
npm run dev
```

### **Environment Variables**
```bash
# SDK
LLMOBSERVE_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
LLMOBSERVE_API_KEY=your-api-key

# Backend (Railway)
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...

# Frontend (Vercel)
NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
```

---

## 📚 Documentation

- **Quick Start (Copy & Paste):** [QUICKSTART_COPY_PASTE.md](./QUICKSTART_COPY_PASTE.md)
- **Simple README:** [README_SIMPLE.md](./README_SIMPLE.md)
- **Full API Reference:** https://llmobserve.com/docs/api
- **How It Works:** [HOW_TRACKING_WORKS.md](./HOW_TRACKING_WORKS.md)
- **Example Flow:** [EXAMPLE_USER_FLOW.md](./EXAMPLE_USER_FLOW.md)
- **Integration Guides:** https://llmobserve.com/docs/integrations

---

## 🤝 Support

- **Email:** support@llmobserve.com
- **Docs:** https://llmobserve.com/docs
- **Discord:** https://discord.gg/llmobserve
- **GitHub Issues:** https://github.com/yourusername/llmobserve/issues

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🎯 Why LLMObserve?

### **vs. Manual Tracking**
❌ Manual logging everywhere  
❌ Outdated pricing  
❌ No dashboard  
✅ **LLMObserve: 2 lines of code, automatic tracking, beautiful UI**

### **vs. Competitors**
❌ Complex setup  
❌ Framework-specific  
❌ Expensive ($50-500/month)  
✅ **LLMObserve: Zero-config, any framework, $5/month**

### **The Difference**
- **HTTP Interception:** Works with ANY API, not just specific SDKs
- **Transparent:** "Untracked" bucket shows all costs (nothing hidden)
- **Simple:** 2 lines to start, optional labeling for organization
- **Fail-Safe:** Doesn't break your app if tracking fails

---

**Get started in 60 seconds:** https://llmobserve.com

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"
)

# You're done. Start building.
```
