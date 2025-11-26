# LLMObserve - Automatic LLM Cost Tracking

**Track every LLM API call. 2 lines of code. $5/month.**

```python
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"
)
# Done! All LLM calls now tracked automatically.
```

---

## 🚀 Quick Start

### 1. Install
```bash
pip install llmobserve
```

### 2. Get API Key
Go to **https://llmobserve.com/settings** → Create API Key

### 3. Add to Your Code
```python
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_your_key_here"  # From step 2
)
```

### 4. View Dashboard
**https://llmobserve.com/dashboard**

---

## ✨ What You Get

✅ **Automatic Tracking**
- OpenAI, Anthropic, Google, Cohere, and 40+ providers
- All models (GPT-4, Claude, Gemini, etc.)
- Zero code changes needed

✅ **Real-Time Costs**
- Cost in USD (calculated automatically)
- Token usage (input + output)
- Latency per call
- Success/error rates

✅ **Beautiful Dashboard**
- Cost trends over time
- Breakdown by provider, model, section
- Multi-tenant support (track per customer)
- Export to CSV/JSON

✅ **Developer-Friendly**
- 2 lines to set up
- Works with any framework
- Fail-safe (doesn't break your app)
- Async (doesn't slow down calls)

---

## 📊 Complete Example

```python
# Initialize once at startup
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_your_key_here"
)

# Use your LLM libraries normally
from openai import OpenAI
client = OpenAI(api_key="your-openai-key")

# This is automatically tracked!
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

# View costs at: https://llmobserve.com/dashboard
```

---

## 🎯 Optional Features

### Organize by Section
```python
from llmobserve import section

with section("user_query"):
    response = client.chat.completions.create(...)

with section("data_processing"):
    response = client.chat.completions.create(...)
```

### Track Per Customer (Multi-Tenant)
```python
from llmobserve import set_customer_id

set_customer_id("customer_123")
response = client.chat.completions.create(...)
# Costs tracked per customer in dashboard
```

---

## 💰 Pricing

**$5/month** - Unlimited tracking, all features:
- ✅ Unlimited API calls tracked
- ✅ All providers (40+)
- ✅ Multi-tenant support
- ✅ Spending caps
- ✅ Export data
- ✅ Priority support

**Try it:** https://llmobserve.com

---

## 🆘 Support

- **Email:** support@llmobserve.com
- **Docs:** https://llmobserve.com/docs
- **Discord:** https://discord.gg/llmobserve

---

## 📚 Documentation

- **Quick Start:** [QUICKSTART_COPY_PASTE.md](./QUICKSTART_COPY_PASTE.md)
- **Full Guide:** [README.md](./README.md)
- **API Reference:** https://llmobserve.com/docs/api
- **Examples:** https://github.com/yourusername/llmobserve/tree/main/examples

---

**Get started in 60 seconds:** https://llmobserve.com

```python
import llmobserve
llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="YOUR_API_KEY_HERE"
)
```

