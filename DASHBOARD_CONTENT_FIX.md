# Dashboard Content Not Loading - Debug Guide

## 🔍 Problem

The dashboard page loads (`app.llmobserve.com/dashboard`) but **no content/data** is showing. This means:
- ✅ Routing works (page loads)
- ✅ Clerk authentication works (user menu visible)
- ❌ API calls to backend are failing or not being made

## 🚨 Most Likely Issues

### Issue 1: Missing Environment Variable in Vercel

The `NEXT_PUBLIC_COLLECTOR_URL` environment variable is probably not set in Vercel.

**Check:**
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Look for `NEXT_PUBLIC_COLLECTOR_URL`

**If missing, add it:**
```bash
NEXT_PUBLIC_COLLECTOR_URL=https://your-backend-url.up.railway.app
```

**To find your backend URL:**
- Check Railway dashboard: https://railway.app/dashboard
- Or run: `cd collector && railway domain`

### Issue 2: Backend CORS Not Allowing Subdomain

Your backend might not be configured to allow requests from `app.llmobserve.com`.

**Fix in Railway backend (`collector/main.py`):**

```python
origins = [
    "https://app.llmobserve.com",      # ← Add this
    "https://llmobserve.com",          # Keep for Framer
    "https://www.llmobserve.com",      # Keep for Framer
    "http://localhost:3000",
]
```

**Then redeploy:**
```bash
cd collector
railway up
```

### Issue 3: Backend Not Running

Check if your Railway backend is actually running:

```bash
# Test backend health endpoint
curl https://your-backend-url.up.railway.app/health

# Should return: {"status":"ok",...}
```

## 🔧 Step-by-Step Fix

### Step 1: Verify Backend URL

1. **Find your Railway backend URL:**
   ```bash
   cd collector
   railway domain
   ```
   
   Or check Railway dashboard → Your Service → Settings → Networking

2. **Test backend is working:**
   ```bash
   curl https://your-backend-url.up.railway.app/health
   ```

### Step 2: Set Environment Variable in Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. **Settings** → **Environment Variables**
4. Click **Add New**
5. Add:
   - **Key**: `NEXT_PUBLIC_COLLECTOR_URL`
   - **Value**: `https://your-backend-url.up.railway.app` (from Step 1)
   - **Environment**: Production (and Preview if you want)
6. Click **Save**

### Step 3: Redeploy Vercel

After adding the env var, trigger a new deployment:

```bash
cd web
vercel --prod
```

Or just push to GitHub (if auto-deploy is enabled):
```bash
git commit --allow-empty -m "Trigger redeploy"
git push
```

### Step 4: Update Backend CORS

Make sure your backend allows requests from the subdomain:

**File:** `collector/main.py` (find the CORS origins list)

```python
origins = [
    "https://app.llmobserve.com",      # ← Add this
    "https://llmobserve.com",
    "https://www.llmobserve.com",
    "http://localhost:3000",
]
```

**Redeploy backend:**
```bash
cd collector
railway up
```

### Step 5: Test in Browser

1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Visit `https://app.llmobserve.com/dashboard`
4. Look for errors like:
   - `Failed to fetch`
   - `CORS error`
   - `NetworkError`
   - `[Dashboard] Error loading data`

5. Go to **Network** tab
6. Filter by "Fetch/XHR"
7. Look for API calls to your backend URL
8. Check if they're:
   - ✅ Returning 200 OK
   - ❌ Returning 404, 500, or CORS errors

## 🧪 Quick Test Script

Run this in browser console on `app.llmobserve.com/dashboard`:

```javascript
// Check if env var is set (won't work in production, but check Network tab)
console.log('Collector URL should be:', process.env.NEXT_PUBLIC_COLLECTOR_URL);

// Test backend directly
fetch('https://your-backend-url.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

## 📋 Checklist

- [ ] Backend is running (test `/health` endpoint)
- [ ] `NEXT_PUBLIC_COLLECTOR_URL` is set in Vercel environment variables
- [ ] Vercel deployment includes the env var (check deployment logs)
- [ ] Backend CORS allows `app.llmobserve.com`
- [ ] Backend CORS allows `https://app.llmobserve.com` (with https)
- [ ] Browser console shows no CORS errors
- [ ] Network tab shows API calls being made
- [ ] API calls return 200 OK (not 404/500)

## 🎯 Most Common Fix

**90% of the time, it's this:**

1. `NEXT_PUBLIC_COLLECTOR_URL` not set in Vercel → **Add it**
2. Redeploy Vercel → **Trigger new deployment**
3. Wait 2-3 minutes → **Check dashboard again**

## 🚀 After Fixing

Once fixed, you should see:
- ✅ Dashboard loads with data
- ✅ KPI cards show numbers
- ✅ Provider breakdown table populated
- ✅ Charts displaying data

## 📞 Still Not Working?

Check these:
1. **Browser console errors** - Share the exact error message
2. **Network tab** - Are API calls being made? What status codes?
3. **Vercel deployment logs** - Any build errors?
4. **Railway logs** - Is backend receiving requests? `railway logs`

---

## Quick Command Reference

```bash
# Check backend URL
cd collector && railway domain

# Test backend
curl https://your-backend-url.up.railway.app/health

# Redeploy frontend
cd web && vercel --prod

# Redeploy backend  
cd collector && railway up

# Check backend logs
cd collector && railway logs
```






