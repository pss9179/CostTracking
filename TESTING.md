# Testing LLMObserve

## Simplified Testing Workflow

Instead of running separate test scripts, **use real API keys and test through the actual dashboard**. This gives you:
- ✅ Real user experience testing
- ✅ Immediate visual feedback
- ✅ Accurate authentication flow
- ✅ Per-user data isolation

## Quick Start

### 1. Start the Services

```bash
# Terminal 1: Start backend
cd collector && uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend
cd web && npm run dev
```

### 2. Create an Account

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Choose your user type:
   - **Solo Developer**: Just want to track your own costs
   - **SaaS Founder**: Want to track costs per customer
4. **Save your API key!** (shown only once)

### 3. Test with Your API Key

**Option A: Use the test script**

```bash
# Edit scripts/test_with_real_account.py
# Replace LLMOBSERVE_API_KEY with your actual key
python3 scripts/test_with_real_account.py
```

**Option B: Use in your own code**

```python
import llmobserve
from openai import OpenAI

# Initialize with your API key
llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_YOUR_KEY_HERE"  # From signup
)

# Optional: Track per-customer (for SaaS founders)
llmobserve.set_customer_id("customer_123")

# Your normal code
client = OpenAI()
with llmobserve.section("my_agent"):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
```

### 4. View in Dashboard

Refresh http://localhost:3000 and you'll see:
- **Dashboard**: Total costs, API calls, recent runs
- **Agents**: Hierarchical breakdown of agent/workflow costs
- **Customers** (SaaS only): Per-customer cost breakdown
- **Settings**: Manage your API keys

## User Types

### Solo Developer
- **Sees**: Dashboard → Agents → Settings
- **Tracks**: Personal project costs
- **Use case**: "How much did my RAG pipeline cost?"

### SaaS Founder
- **Sees**: Dashboard → Customers → Agents → Settings
- **Tracks**: Per-customer costs
- **Use case**: "Which customer is using the most tokens?"

## Environment Setup

Make sure your `.env` has:

```bash
# Backend database (use Supabase or local PostgreSQL)
DATABASE_URL=postgresql://...

# Your API keys for external services
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
```

## Tips

1. **Multiple accounts**: Create different accounts to test multi-user scenarios
2. **Customer tracking**: Use `llmobserve.set_customer_id()` to simulate different end-users
3. **Agent hierarchy**: Use nested `llmobserve.section()` calls to see the tree visualization
4. **Real production flow**: This is exactly how real users will use your product!

## What to Test

- [ ] Signup flow (solo dev vs SaaS founder)
- [ ] API key generation and usage
- [ ] OpenAI API calls tracking
- [ ] Pinecone operations tracking
- [ ] Agent hierarchies (nested sections)
- [ ] Per-customer cost tracking (for SaaS)
- [ ] Dashboard KPIs accuracy
- [ ] Navigation (correct tabs based on user type)
- [ ] Settings page (API key management)

## Troubleshooting

**"Failed to fetch" error**
- Make sure you're logged in
- Check backend is running on port 8000
- Verify your API key is correct

**No data showing up**
- Wait 2-3 seconds for events to flush
- Hard refresh the page (Cmd+Shift+R)
- Check backend logs for errors

**Wrong navigation tabs**
- Log out and log back in
- Check your user type in Settings
- Clear browser localStorage if needed

