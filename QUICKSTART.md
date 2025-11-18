# 🚀 Quick Start - Get Running in 60 Seconds

## Step 1: Sign Up & Get API Key
1. Go to https://llmobserve.com
2. Click "Get Started - $8/month"
3. Sign up and subscribe
4. Go to **Settings** → copy your API key

---

## Step 2: Install SDK
```bash
pip install llmobserve
```

---

## Step 3: Add 2 Lines to Your Code
```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-production.up.railway.app",
    api_key="your-api-key-here"  # Paste from dashboard
)

# That's it! All your LLM calls are now tracked.
```

---

## Step 4: Run Your Code
```bash
python your_agent.py
```

---

## Step 5: Check Dashboard
Go to https://llmobserve.com/dashboard

You'll see:
- Total cost
- Calls made
- Which providers you're using
- "Untracked" costs (costs without labels)

---

## Step 6: Label Your Costs (Optional)

If you see "Untracked" costs on the dashboard, click **✨ AI Auto-Instrument**

Then run:
```bash
# Set credentials (one time)
export LLMOBSERVE_COLLECTOR_URL="https://llmobserve-production.up.railway.app"
export LLMOBSERVE_API_KEY="your-api-key"

# Preview suggestions
llmobserve preview your_agent.py

# Apply changes (creates backup)
llmobserve instrument your_agent.py --auto-apply
```

AI will add labels like:
```python
from llmobserve import agent

@agent("researcher")  # ← AI added this
def research_agent(query):
    # Your code stays the same
    return openai_call()
```

Now your dashboard shows: `researcher: $0.28` instead of `Untracked: $0.28`

---

## That's It!

**You're tracking all your LLM costs now.**

### What You Get:
- ✅ Every API call tracked automatically
- ✅ Real-time cost updates
- ✅ Beautiful dashboard
- ✅ AI can label your agents (optional)
- ✅ Export to CSV/JSON
- ✅ $8/month, unlimited usage

---

## Need Help?

- **Docs:** https://llmobserve.com/docs
- **Example:** See `EXAMPLE_USER_FLOW.md`
- **How It Works:** See `HOW_TRACKING_WORKS.md`
- **Email:** support@llmobserve.com

---

## Common Questions

**Q: Do I need to change my code?**  
A: Just add 2 lines at the top. That's it.

**Q: What if I use a custom LLM API?**  
A: It works! We track ANY HTTP API call.

**Q: Does it work with LangChain/CrewAI/etc?**  
A: Yes! Works with any framework, or no framework.

**Q: What if costs show as "Untracked"?**  
A: That's normal! Use AI auto-instrument to label them, or leave them (all costs are still tracked).

**Q: Do I need an Anthropic API key for AI features?**  
A: Nope! AI features are included. Just use your LLMObserve API key.

---

**Now go build something cool.** 🚀

