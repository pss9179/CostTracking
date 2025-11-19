# LLMObserve - Automatic LLM Cost Tracking

**Track every LLM API call. Know exactly what you're spending. Optimize what matters.**

> Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers.  
> AI-powered instrumentation included. $5/month.

---

## 🚀 Quick Start (2 lines of code)

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key="your-api-key-here"  # Get from llmobserve.com/settings
)

# That's it! All your LLM calls are now tracked automatically.
```

**Get your API key:** https://llmobserve.com/settings

---

## ✨ What You Get

### 1. **Automatic Cost Tracking**
- Every LLM API call is tracked automatically
- Real-time cost calculation with up-to-date pricing
- Works with ANY HTTP-based API (LLMs, vector DBs, custom APIs)

### 2. **AI-Powered Instrumentation** (NEW)
- One command labels all your agents automatically
- No manual wrapping needed
- Creates `.bak` backup before changes
- **Included in subscription - no extra cost**

```bash
llmobserve preview my_agent.py         # See suggestions
llmobserve instrument --auto-apply     # Apply changes
```

### 3. **Beautiful Dashboard**
- See costs by agent, provider, customer, time
- Real-time updates every 30 seconds
- Export to CSV/JSON
- "Untracked" bucket shows unlabeled costs (nothing hidden)

### 4. **Multi-Tenant Support**
- Track costs per customer (perfect for SaaS)
- Isolated data views
- Customer-level analytics

---

## 📦 Installation

```bash
pip install llmobserve
```

**Set credentials:**
```bash
export LLMOBSERVE_COLLECTOR_URL="https://llmobserve-production.up.railway.app"
export LLMOBSERVE_API_KEY="your-api-key-here"
```

---

## 🎯 How It Works

### **Zero-Config Tracking**
We patch Python HTTP clients (`httpx`, `requests`, `aiohttp`, `urllib3`) to inject tracking headers. No SDK-specific code. Works with ANY API.

```python
import llmobserve
from openai import OpenAI

llmobserve.observe(collector_url="...", api_key="...")

client = OpenAI()
response = client.chat.completions.create(...)  # ← Automatically tracked!
```

### **Optional Labeling (Organize Costs)**
Add labels to see which agents/tools cost the most:

```python
from llmobserve import agent, section

@agent("researcher")
def research_agent(query):
    # All API calls here labeled as "agent:researcher"
    return openai_call()

# Or use context manager
with section("agent:writer"):
    response = openai_call()
```

### **AI Auto-Instrumentation**
Let AI add labels for you:

```bash
llmobserve preview my_code.py           # Preview suggestions
llmobserve instrument --auto-apply      # Apply automatically
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
│  → Real-time updates (30s polling)                   │
│  → Export to CSV/JSON                                │
└──────────────────────────────────────────────────────┘
```

**Key Design:**
- **HTTP Interception:** Universal, SDK-agnostic, stable
- **No Monkey-Patching:** Works when SDKs update
- **Fail-Open:** If tracking breaks, your app continues

---

## 📊 What We Track

### ✅ **Automatically Tracked**
- **LLM Providers:** OpenAI, Anthropic, Google, Cohere, Together, Hugging Face, Perplexity, Groq, Mistral, etc.
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
- Label agents with `@agent("name")` or `section("agent:name")`
- Hierarchical tracking (agent → tool → step)
- "Untracked" bucket for unlabeled costs
- AI can auto-label your code

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

### **Spending Caps**
Set in dashboard → Settings → Spending Caps

### **Hierarchical Tracing**
```python
with section("agent:researcher"):
    with section("tool:web_search"):
        # Tracked as "agent:researcher/tool:web_search"
        search_results = api_call()
    
    with section("tool:summarize"):
        summary = llm_call()
```

### **Framework Integration**
```python
from llmobserve import wrap_all_tools

# LangChain, CrewAI, AutoGen, etc.
tools = [search_tool, calculator]
wrapped_tools = wrap_all_tools(tools)
agent = Agent(tools=wrapped_tools)
```

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
python -m uvicorn main:app --reload

# Run web dashboard
cd web
npm install
npm run dev
```

### **Environment Variables**
```bash
# SDK
LLMOBSERVE_COLLECTOR_URL=https://llmobserve-production.up.railway.app
LLMOBSERVE_API_KEY=your-api-key

# Backend (Railway)
DATABASE_URL=postgresql://...
CLERK_SECRET_KEY=sk_...
ANTHROPIC_API_KEY=sk-ant-...  # For AI instrumentation

# Frontend (Vercel)
NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-production.up.railway.app
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
ANTHROPIC_API_KEY=sk-ant-...  # For AI instrumentation
```

---

## 📚 Documentation

- **Full Docs:** https://llmobserve.com/docs
- **API Reference:** https://llmobserve.com/docs#api-reference
- **How It Works:** See `HOW_TRACKING_WORKS.md`
- **Example Flow:** See `EXAMPLE_USER_FLOW.md`

---

## 💰 Pricing

**$5/month** - Unlimited tracking, all features included:
- ✅ Unlimited API calls tracked
- ✅ All providers (40+)
- ✅ Multi-tenant support
- ✅ AI auto-instrumentation
- ✅ Spending caps
- ✅ Export to CSV/JSON
- ✅ Priority support

**Try it:** https://llmobserve.com

---

## 🤝 Support

- **Email:** support@llmobserve.com
- **Docs:** https://llmobserve.com/docs
- **Issues:** GitHub Issues

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
- **AI Labeling:** One command auto-instruments your code
- **Transparent:** "Untracked" bucket shows all costs (nothing hidden)
- **Simple:** 2 lines to start, optional labeling for organization

---

**Get started in 60 seconds:** https://llmobserve.com

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key="your-api-key"
)

# You're done. Start building.
```
