# LLMObserve - Quick Start (Copy & Paste Ready)

**Track every LLM API call automatically. Know exactly what you're spending.**

---

## 🚀 Step 1: Install (30 seconds)

```bash
pip install llmobserve
```

---

## 🔑 Step 2: Get Your API Key

1. Go to: **https://llmobserve.com/settings**
2. Sign in
3. Click "Create New API Key"
4. Copy your key (starts with `llmo_sk_...`)

---

## ⚡ Step 3: Add to Your Code (2 lines!)

**Copy this to the TOP of your main file:**

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"  # Replace with your key from Step 2
)
```

**That's it!** All your LLM API calls are now tracked automatically.

---

## ✅ Complete Example

```python
# 1. Initialize llmobserve (add this at the top)
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_your_key_here"  # Get from https://llmobserve.com/settings
)

# 2. Use your LLM libraries normally - they're tracked automatically!
from openai import OpenAI

client = OpenAI(api_key="your-openai-key")

# This call is automatically tracked - no changes needed!
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

**View your costs at:** https://llmobserve.com/dashboard

---

## 🎯 What Gets Tracked Automatically

✅ **All LLM Providers:**
- OpenAI (GPT-4, GPT-4o, GPT-3.5, etc.)
- Anthropic (Claude)
- Google (Gemini)
- Cohere
- Together AI
- Groq
- Mistral
- And 40+ more!

✅ **All Metrics:**
- Cost (USD) - calculated automatically
- Token usage (input + output)
- Latency
- Model used
- Status (success/error)

---

## 📊 Optional: Organize Costs by Section

Want to see which parts of your app cost the most?

```python
from llmobserve import section

# Track costs by feature
with section("user_query"):
    response = client.chat.completions.create(...)

with section("data_processing"):
    response = client.chat.completions.create(...)

# View breakdown by section in dashboard!
```

---

## 👥 Optional: Track Costs Per Customer (Multi-Tenant)

Building a SaaS? Track costs per customer:

```python
from llmobserve import set_customer_id

# Set customer ID for this session
set_customer_id("customer_123")

# All API calls now associated with this customer
response = client.chat.completions.create(...)

# View per-customer costs in dashboard!
```

---

## 🎓 Real-World Example: Chatbot

```python
# Initialize llmobserve once at startup
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_your_key_here"
)

from llmobserve import section, set_customer_id
from openai import OpenAI

client = OpenAI(api_key="your-openai-key")

def handle_user_message(user_id: str, message: str):
    # Track costs per user
    set_customer_id(user_id)
    
    # Step 1: Classify intent
    with section("intent_classification"):
        intent = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"Classify: {message}"}]
        )
    
    # Step 2: Generate response
    with section("response_generation"):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": message}]
        )
    
    return response.choices[0].message.content

# All costs tracked automatically!
# View breakdown by section and customer in dashboard
```

---

## 🌐 View Your Dashboard

**Go to:** https://llmobserve.com/dashboard

You'll see:
- Total costs (hourly, daily, weekly, monthly)
- Breakdown by provider (OpenAI, Anthropic, etc.)
- Breakdown by model (GPT-4, Claude, etc.)
- Breakdown by section (if using sections)
- Breakdown by customer (if using customer IDs)
- Cost trends over time
- Export to CSV/JSON

---

## 🔧 Advanced Features

### Set Spending Caps
```python
# Set in dashboard: Settings → Spending Caps
# - Per customer caps
# - Per agent caps
# - Global caps
```

### Hierarchical Sections
```python
with section("agent:researcher"):
    with section("tool:web_search"):
        # Tracked as "agent:researcher/tool:web_search"
        search_results = api_call()
```

### Framework Integration
```python
# Works with:
# - LangChain
# - CrewAI
# - AutoGen
# - LlamaIndex
# - Any framework that uses HTTP APIs
```

---

## ❓ FAQ

### Q: Do I need to change my existing code?
**A:** No! Just add 2 lines at the top. Everything else works as-is.

### Q: What if llmobserve breaks?
**A:** It's fail-safe. If tracking fails, your app continues normally.

### Q: Does it slow down my API calls?
**A:** No. Tracking happens asynchronously in the background.

### Q: What about API keys and security?
**A:** Your LLM API keys never leave your server. Only usage metadata is sent to llmobserve.

### Q: Can I self-host?
**A:** Yes! See SELF_HOSTING.md

### Q: How much does it cost?
**A:** $5/month for unlimited tracking. No per-call fees.

---

## 🆘 Troubleshooting

### Not seeing data in dashboard?

1. **Check API key:** Make sure you copied the full key from settings
2. **Wait a few seconds:** Events are batched and sent every 500ms
3. **Check collector URL:** Should be `https://llmobserve-api-production-d791.up.railway.app`
4. **Check logs:** Look for `[llmobserve]` messages in your console

### "Invalid API key" error?

- Go to https://llmobserve.com/settings
- Create a new API key
- Copy the full key (starts with `llmo_sk_`)
- Replace in your code

### Still having issues?

- Email: support@llmobserve.com
- Discord: https://discord.gg/llmobserve
- GitHub Issues: https://github.com/yourusername/llmobserve/issues

---

## 📚 More Documentation

- **Full API Reference:** https://llmobserve.com/docs/api
- **Integration Guides:** https://llmobserve.com/docs/integrations
- **Self-Hosting:** https://llmobserve.com/docs/self-hosting
- **Examples:** https://github.com/yourusername/llmobserve/tree/main/examples

---

## 🎉 You're Done!

That's literally it. Add 2 lines, get automatic cost tracking.

**Start tracking now:** https://llmobserve.com

```python
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"
)
# Done! All LLM calls now tracked.
```

