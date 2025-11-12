# Clerk Webhook Setup Guide

## 🎯 Goal
Connect Clerk to your backend so new signups automatically get users + API keys created.

---

## Step 1: Expose Backend with ngrok

### Option A: Manual ngrok (Recommended)
```bash
# In a new terminal:
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123xyz.ngrok-free.app -> http://localhost:8000
```

**Copy that HTTPS URL** (e.g., `https://abc123xyz.ngrok-free.app`)

### Option B: Skip ngrok (for later)
If you deploy to a real server, use your actual domain instead.

---

## Step 2: Configure Clerk Webhook

1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Select your application ("superb-toucan-96" based on your keys)
3. Navigate to **Webhooks** (left sidebar)
4. Click **"Add Endpoint"**

### Webhook Configuration:
- **Endpoint URL**: `https://YOUR-NGROK-URL.ngrok-free.app/webhooks/clerk`
  - Example: `https://abc123xyz.ngrok-free.app/webhooks/clerk`
  
- **Subscribe to events**:
  - ✅ `user.created`
  - ✅ `user.updated`  
  - ✅ `user.deleted`

- **Click "Create"**

---

## Step 3: Test the Flow

### A) Sign Up
1. Go to `http://localhost:3000`
2. You should be redirected to sign-in (Clerk middleware protecting routes)
3. Click **"Sign Up"**
4. Create an account with email/password

### B) Check Backend Logs
```bash
# Watch backend logs:
tail -f /tmp/backend.log
```

You should see:
```
[Clerk Webhook] Received event: user.created
[Clerk Webhook] Created user your-email@example.com with API key llmo_...
```

### C) Check Settings Page
1. After signup, go to `http://localhost:3000/settings`
2. You should see:
   - Your user info (email, name, user type)
   - Your auto-generated API key (starts with `llmo_`)
3. **Copy the API key!**

---

## Step 4: Test with SDK

Create a test script:

```python
# test_clerk_user.py
import llmobserve
import openai
from dotenv import load_dotenv

load_dotenv()

# Use YOUR API key from Settings page
llmobserve.observe(
    api_key="llmo_YOUR_KEY_HERE",  # ← Paste from Settings
    customer_id="test_customer_123"
)

# Make a tracked API call
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

print("✅ Cost tracked! Check your dashboard.")
```

Run it:
```bash
python test_clerk_user.py
```

### D) Check Dashboard
1. Go to `http://localhost:3000`
2. You should see:
   - Total cost updated
   - Recent runs
   - Provider breakdown (OpenAI)

---

## Troubleshooting

### "Failed to fetch run undefined"
**Fix**: This is from the old test data. Clear it:
```bash
rm collector/collector.db
# Restart backend - it will recreate the DB
```

### Webhook not firing
1. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
2. Check Clerk webhook logs in dashboard
3. Verify backend is accessible: `curl https://YOUR-NGROK-URL.ngrok-free.app/health`

### No API key in Settings
1. Check backend logs for errors
2. Manually create one:
   - Go to Settings
   - Click "Generate New API Key"
   - Give it a name
   - Copy the key (shown only once!)

---

## Production Deployment (Later)

When you deploy to production:

1. **Update Clerk Webhook URL**:
   - Change from `https://xyz.ngrok-free.app/webhooks/clerk`
   - To: `https://your-domain.com/webhooks/clerk`

2. **Add Webhook Signature Verification** (IMPORTANT!):
   ```python
   # In clerk_webhook.py, add:
   from svix.webhooks import Webhook
   
   webhook = Webhook(CLERK_WEBHOOK_SECRET)
   payload = webhook.verify(request.body, request.headers)
   ```

3. **Environment Variables**:
   ```bash
   CLERK_SECRET_KEY=sk_live_...  # Use live key, not test
   CLERK_WEBHOOK_SECRET=whsec_...  # From Clerk webhook settings
   DATABASE_URL=postgresql://...  # Use PostgreSQL in prod
   ```

---

## Current Status

✅ **Backend**: Running with Clerk integration
✅ **Frontend**: Clerk sign-in/sign-up working
✅ **Webhook handler**: Ready at `/webhooks/clerk`
✅ **API key management**: `/clerk/api-keys` endpoints
⏳ **ngrok**: Need to start manually
⏳ **Clerk webhook**: Need to configure in dashboard

**Next**: Start ngrok, configure Clerk, test signup!

---

## Quick Commands

```bash
# Start ngrok
ngrok http 8000

# Watch backend logs
tail -f /tmp/backend.log

# Test backend health
curl http://localhost:8000/health

# Test ngrok forwarding
curl https://YOUR-NGROK-URL.ngrok-free.app/health

# Check frontend
open http://localhost:3000
```

---

**Once webhook is configured, the entire flow will work!** 🎉

