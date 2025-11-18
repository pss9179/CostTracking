# LLM Observe SDK

> **Automatic cost tracking and observability for LLM applications**

Track costs, tokens, latency, and errors for OpenAI, Anthropic, and other LLM providers with just 2 lines of code.

[![PyPI version](https://badge.fury.io/py/llmobserve.svg)](https://pypi.org/project/llmobserve/)
[![Python Versions](https://img.shields.io/pypi/pyversions/llmobserve.svg)](https://pypi.org/project/llmobserve/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- ✅ **Auto-instrumentation** - No code changes needed beyond initialization
- 📊 **Real-time tracking** - Costs, tokens, latency, errors
- 🔍 **Hierarchical tracing** - Track agents, tools, and workflows
- 👥 **Customer attribution** - Track costs per end-user
- 🎯 **Zero overhead** - Async buffering, sub-millisecond impact
- 🔒 **Privacy-first** - Optional prompt/response capture
- 🚀 **Production-ready** - Battle-tested, scalable architecture

## Supported Providers

- **OpenAI** (GPT-4, GPT-3.5, embeddings, images, audio, etc.)
- **Pinecone** (vector database operations)
- More coming soon! (Anthropic, Cohere, etc.)

## Quick Start

### 1. Install

```bash
pip install llmobserve
```

### 2. Get Your API Key

Sign up at [llmobserve.com](https://llmobserve.com) to get your API key.

### 3. Add 2 Lines of Code

```python
from llmobserve import observe
from openai import OpenAI

# Initialize observability
observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

# Use OpenAI as normal - all calls are tracked automatically!
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

That's it! 🎉 View your costs and metrics at [app.llmobserve.com](https://app.llmobserve.com)

## Advanced Usage

### Track Agents & Workflows

**Automatic Tracking (Zero Config):**
```python
from llmobserve import observe
from langchain.agents import AgentExecutor

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

# Agent tracking happens automatically - no manual labeling needed!
agent = AgentExecutor(...)
result = agent.run("query")  # Automatically tracked as agent
```

**Manual Labeling (Optional, for Better UX):**
```python
from llmobserve import observe, section

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

# Hierarchical tracking (optional - improves dashboard UX)
with section("agent:research_assistant"):
    with section("tool:web_search"):
        # Your search logic
        results = search_web(query)
    
    with section("tool:summarize"):
        # Your summarization logic
        summary = summarize(results)
```

**Key Points:**
- ✅ **Costs are always tracked** via HTTP interception (works everywhere)
- ✅ **Framework agents auto-tracked** (LangChain, CrewAI, AutoGen, LlamaIndex)
- ✅ **Manual labeling is optional** (improves dashboard UX but not required)
- ✅ **Untracked costs still shown** (labeled as "untracked" in dashboard)

Dashboard shows:
```
agent:research_assistant    $0.50  (10 calls)
├─ tool:web_search          $0.002  [ok]
└─ tool:summarize           $0.001  [ok]
untracked                   $0.10   (5 calls)  ← Costs without agent labels
```

### Track Costs Per Customer

```python
from llmobserve import observe, set_customer_id

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

# Set customer ID for cost attribution
set_customer_id("customer_xyz")

# All subsequent API calls are attributed to this customer
client = OpenAI()
response = client.chat.completions.create(...)
```

### Decorator Style

```python
from llmobserve import trace

@trace(agent="customer_support")
async def handle_support_request(message: str):
    # All OpenAI calls inside are automatically tracked
    response = await client.chat.completions.create(...)
    return response
```

### Framework Integration

#### FastAPI

```python
from fastapi import FastAPI
from llmobserve import ObservabilityMiddleware, observe

app = FastAPI()
app.add_middleware(ObservabilityMiddleware)

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

@app.post("/chat")
async def chat(request: Request):
    # Context is auto-reset per request
    # All OpenAI calls are tracked
    response = await client.chat.completions.create(...)
    return response
```

#### Flask

```python
from flask import Flask
from llmobserve import flask_before_request, observe

app = Flask(__name__)
app.before_request(flask_before_request)

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here"
)

@app.route("/chat")
def chat():
    # Context is auto-reset per request
    response = client.chat.completions.create(...)
    return response
```

## What Gets Tracked

For every LLM API call:

- ✅ **Costs** - Calculated using latest pricing
- ✅ **Tokens** - Input, output, and cached tokens
- ✅ **Latency** - Request duration in milliseconds
- ✅ **Status** - Success, error, timeout, etc.
- ✅ **Model** - Which model was used
- ✅ **Provider** - OpenAI, Anthropic, etc.
- ✅ **Section/Agent** - Hierarchical context
- ✅ **Customer ID** - For cost attribution
- ✅ **Timestamps** - When the call was made
- ⚠️ **Prompts/Responses** - Optional (disabled by default)

## Configuration

### Environment Variables

```bash
# Disable observability
LLMOBSERVE_DISABLED=1

# Enable content capture (prompts/responses)
ALLOW_CONTENT_CAPTURE=true
```

### Custom Flush Interval

```python
observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_your_key_here",
    flush_interval_ms=1000  # Flush every 1 second (default: 500ms)
)
```

## Dashboard Features

Visit [app.llmobserve.com](https://app.llmobserve.com) to view:

- 💰 **Cost Overview** - Total spend, trends, by provider/model
- 📊 **Run Details** - Individual request breakdowns
- 🎯 **Agent Analytics** - Which agents/workflows cost the most
- 👥 **Customer Breakdown** - Cost per end-user
- 🚨 **Alerts** - Cost spikes, errors, anomalies
- 📈 **Insights** - Auto-detected inefficiencies

## Self-Hosting

Want to run your own instance?

```bash
git clone https://github.com/yourusername/llmobserve
cd llmobserve

# Start collector API
cd collector
pip install -r requirements.txt
uvicorn main:app --port 8000

# Start dashboard
cd ../web
npm install
npm run dev
```

See [DEPLOYMENT.md](https://github.com/yourusername/llmobserve/blob/main/DEPLOYMENT.md) for production deployment guide.

## Architecture

```
┌─────────────────┐
│   Your App      │
│  + llmobserve   │  ← Auto-instruments OpenAI & Pinecone
│     SDK         │
└────────┬────────┘
         │ POST /events
         ↓
┌─────────────────┐
│  Collector API  │  ← FastAPI + PostgreSQL
│   (Backend)     │
└────────┬────────┘
         │ GET /runs, /stats
         ↓
┌─────────────────┐
│   Dashboard     │  ← Next.js + Clerk
│   (Frontend)    │
└─────────────────┘
```

## FAQ

**Q: Does this slow down my app?**
A: No. Events are buffered asynchronously with sub-millisecond overhead.

**Q: Are my prompts/responses sent to your servers?**
A: No, by default only metadata is sent (tokens, cost, latency). Set `ALLOW_CONTENT_CAPTURE=true` to enable content logging.

**Q: Can I use this in production?**
A: Yes! It's production-ready and tested at scale.

**Q: What about other LLM providers?**
A: Anthropic, Cohere, and others coming soon! Request support via GitHub issues.

**Q: How much does it cost?**
A: Free tier includes 10K tracked API calls/month. See [pricing](https://llmobserve.com/pricing).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/yourusername/llmobserve/blob/main/CONTRIBUTING.md).

## License

MIT License - see [LICENSE](https://github.com/yourusername/llmobserve/blob/main/LICENSE)

## Support

- 📖 [Documentation](https://docs.llmobserve.com)
- 🐛 [GitHub Issues](https://github.com/yourusername/llmobserve/issues)
- 💬 [Discord Community](https://discord.gg/llmobserve)
- 📧 [Email Support](mailto:support@llmobserve.com)

---

Made with ❤️ by the LLM Observe team








