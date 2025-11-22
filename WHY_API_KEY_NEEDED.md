# Why Users Need an API Key

## The Simple Answer

**The API key is REQUIRED** - you can't use the SDK without it!

When you `import llmobserve`, you still need to call `observe()` with your API key:

```python
import llmobserve

# ❌ This won't work - no API key!
llmobserve.observe(collector_url="...")
# Error: No API key provided

# ✅ This works - API key required!
llmobserve.observe(
    collector_url="https://your-collector.com",
    api_key="llmo_sk_..."  # ← REQUIRED!
)
```

---

## Why API Key is Needed

### 1. **Authentication**
The API key authenticates you with the backend:
- Backend needs to know: "Who is sending this cost data?"
- API key = Your identity/account
- Without it, backend rejects requests

### 2. **Data Ownership**
The API key links costs to your account:
- Your costs → Your dashboard
- Other users' costs → Their dashboards
- Without API key → Backend doesn't know where to store data

### 3. **Security**
Prevents unauthorized access:
- Only you can send costs to your account
- Can't see other users' data
- Can't spam the backend

---

## Complete User Flow

### Step 1: Get API Key
```
1. Sign up at dashboard
2. Go to Settings
3. Click "Create API Key"
4. Copy the key: llmo_sk_abc123...
```

### Step 2: Install Package
```bash
pip install llmobserve
```

### Step 3: Use SDK (API Key Required!)
```python
import llmobserve

# You MUST provide the API key here!
llmobserve.observe(
    collector_url="https://your-collector.com",
    api_key="llmo_sk_abc123..."  # ← From Step 1
)

# Now your code runs and costs are tracked
```

### Step 4: View Dashboard
- Costs appear in YOUR dashboard
- Linked to YOUR account via API key

---

## What Happens Without API Key?

### Option 1: SDK Won't Work
```python
llmobserve.observe(collector_url="...")
# Warning: No API key provided - using unauthenticated mode
# Backend rejects requests → No costs tracked
```

### Option 2: SDK Uses Dev Mode (Current Behavior)
Looking at `observe.py` line 141-143:
```python
if not api_key:
    logger.warning("[llmobserve] No API key provided - using unauthenticated mode")
    api_key = "dev-mode"  # Placeholder
```

But this won't work in production - backend needs real API key!

---

## Alternative: Environment Variable

Users can also set API key as env var:

```bash
export LLMOBSERVE_API_KEY="llmo_sk_abc123..."
```

Then in code:
```python
import llmobserve

# SDK reads from env var automatically
llmobserve.observe(collector_url="...")
```

---

## Summary

**User does this:**
1. Get API key from dashboard
2. `pip install llmobserve`
3. Use SDK: `llmobserve.observe(api_key="...")`
4. Costs tracked → Appear in dashboard

**Why API key?**
- Authenticates you
- Links costs to your account
- Secures your data

**Without API key:**
- SDK won't work properly
- Costs won't be tracked
- Dashboard stays empty

---

## Updated User Flow Document

The user flow should be:

```
1. Sign up → Get API key
2. pip install llmobserve
3. llmobserve.observe(api_key="...")  ← API key REQUIRED
4. Run code → Costs tracked
5. View dashboard → See your costs
```

**That's it!** Simple and clear.

