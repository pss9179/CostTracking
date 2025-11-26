# ✅ API Key Setup for Deployed Version

## **Status: Ready to Deploy!**

The code changes have been pushed to GitHub. Here's what you need to do:

## **Step 1: Verify Railway Auto-Deployment**

Railway should automatically deploy when you push to GitHub. Check:

1. Go to: https://railway.app/dashboard
2. Find your `llmobserve-api-production-d791` service
3. Check if there's a new deployment (should show latest commit)
4. If not deploying automatically, trigger manual deploy:
   ```bash
   railway up
   ```

## **Step 2: Create API Key on Production**

**Important:** API keys created locally won't work on production. You need to create one through the web dashboard:

1. **Go to:** https://app.llmobserve.com/settings
2. **Sign in** with Clerk (Google, GitHub, or email)
3. **Click "Create New API Key"**
4. **Give it a name** (e.g., "Production Key")
5. **Copy the key immediately** (you won't see it again!)
   - Format: `llmo_sk_...`

## **Step 3: Use the Production API Key**

```python
import llmobserve

llmobserve.observe(
    collector_url="https://llmobserve-api-production-d791.up.railway.app",
    api_key="llmo_sk_YOUR_KEY_FROM_DASHBOARD"  # ← Use the key from Step 2
)
```

## **Step 4: Test It Works**

Run this test script against production:

```python
import urllib.request
import json

API_KEY = "llmo_sk_YOUR_KEY_FROM_DASHBOARD"
COLLECTOR_URL = "https://llmobserve-api-production-d791.up.railway.app"

# Test caps/check endpoint
req = urllib.request.Request(f"{COLLECTOR_URL}/caps/check")
req.add_header("Authorization", f"Bearer {API_KEY}")

try:
    with urllib.request.urlopen(req, timeout=5) as response:
        print(f"✅ Status: {response.getcode()}")
        data = json.loads(response.read().decode())
        print(f"✅ Response: {data}")
        print("🎉 API key authentication works!")
except urllib.error.HTTPError as e:
    print(f"❌ Status: {e.code}")
    error = json.loads(e.read().decode())
    print(f"❌ Error: {error}")
```

## **What Changed:**

✅ `/caps/check` endpoint now supports API key authentication  
✅ Both API keys (`llmo_sk_...`) and Clerk JWT tokens work  
✅ Code is committed and pushed to GitHub  
✅ Ready for Railway auto-deployment  

## **Troubleshooting:**

### **If Railway hasn't deployed:**
```bash
cd collector
railway up
```

### **If API key doesn't work:**
1. Make sure you created it through the web dashboard (not locally)
2. Check Railway logs: https://railway.app/dashboard
3. Verify the collector URL is correct: `https://llmobserve-api-production-d791.up.railway.app`

### **If you see "CLERK_AUTH_FAILED":**
- This means the code hasn't deployed yet
- Wait for Railway to finish deploying
- Or manually trigger a redeploy

## **Summary:**

✅ **Code is ready** - pushed to GitHub  
⏳ **Railway needs to deploy** - should happen automatically  
📝 **You need to create API key** - through web dashboard  
🧪 **Test with production key** - use the script above  

Once Railway deploys and you create an API key through the dashboard, everything should work! 🚀

