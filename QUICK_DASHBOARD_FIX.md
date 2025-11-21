# Quick Dashboard Fix - Since Env Var is Set

## ✅ What's Already Done
- `NEXT_PUBLIC_COLLECTOR_URL` is set in Vercel ✅

## 🔍 Next Steps to Debug

### Step 1: Verify Vercel Has Redeployed

**Check if Vercel picked up the env var:**
1. Go to Vercel Dashboard → Your Project → **Deployments**
2. Check the **latest deployment timestamp**
3. Was it deployed **AFTER** you added the env var?

**If not, trigger a redeploy:**
```bash
cd web
vercel --prod
```

Or just push an empty commit:
```bash
git commit --allow-empty -m "Trigger redeploy for env var"
git push
```

### Step 2: Verify Backend URL Value

**Check what URL is set:**
1. In Vercel Dashboard → Settings → Environment Variables
2. Click the eye icon to reveal `NEXT_PUBLIC_COLLECTOR_URL`
3. Verify it matches your Railway backend URL

**Common formats:**
- ✅ `https://your-app.up.railway.app`
- ✅ `https://api.llmobserve.com` (if you have custom domain)
- ❌ `http://localhost:8000` (won't work in production)
- ❌ Missing `https://` prefix

### Step 3: Test Backend Directly

**Test if backend is accessible:**
```bash
# Replace with your actual backend URL
curl https://your-backend-url.up.railway.app/health
```

**Should return:**
```json
{"status":"ok","service":"llmobserve-collector","version":"0.2.0"}
```

**If it fails:**
- Backend might be down
- Check Railway dashboard → Logs

### Step 4: Check Browser Console

**On `app.llmobserve.com/dashboard`:**
1. Open DevTools (F12)
2. Go to **Console** tab
3. Look for errors like:
   - `Failed to fetch`
   - `NetworkError`
   - `[Dashboard] Error loading data: ...`

4. Go to **Network** tab
5. Filter by "Fetch/XHR"
6. Look for requests to your backend URL
7. Check status codes:
   - ✅ 200 = Success
   - ❌ 404 = Wrong URL
   - ❌ 500 = Backend error
   - ❌ CORS error = CORS issue

### Step 5: Verify Backend CORS

**Check Railway environment variables:**
1. Go to Railway Dashboard → Your Service → Variables
2. Look for `ALLOWED_ORIGINS`
3. Should be either:
   - `*` (allows all - should work)
   - OR include `https://app.llmobserve.com`

**If not set to `*` and doesn't include subdomain:**
```bash
cd collector
railway variables set ALLOWED_ORIGINS="*"
railway up
```

## 🎯 Most Likely Fix

**90% chance it's one of these:**

1. **Vercel needs redeploy** → Run `vercel --prod` or push to GitHub
2. **Backend URL is wrong** → Check the actual value matches Railway URL
3. **Backend is down** → Check Railway logs

## 🧪 Quick Test

**Run this in browser console on dashboard:**

```javascript
// This will show what URL the frontend is trying to use
// (Note: env vars are baked in at build time, so check Network tab instead)

// Test backend directly
fetch('YOUR_BACKEND_URL_HERE/health')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error);
```

Replace `YOUR_BACKEND_URL_HERE` with your actual Railway backend URL.

## 📋 Checklist

- [ ] Vercel has been redeployed AFTER adding env var
- [ ] Backend URL value is correct (matches Railway URL)
- [ ] Backend is running (test `/health` endpoint)
- [ ] Backend CORS allows `*` or includes `app.llmobserve.com`
- [ ] Browser console shows no errors
- [ ] Network tab shows API calls being made
- [ ] API calls return 200 OK (not 404/500/CORS)

## 🚀 After Fixing

Once fixed, refresh `app.llmobserve.com/dashboard` and you should see:
- ✅ KPI cards with numbers
- ✅ Provider breakdown table
- ✅ Charts with data
- ✅ Recent runs list






