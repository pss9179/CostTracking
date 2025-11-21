# Dashboard 404 Error Fix

## 🔍 Problem
After pushing to GitHub, the dashboard shows:
- Error: "Failed to fetch provider stats (404):"
- Raw HTML/JavaScript code displayed

## 🎯 Root Cause
The backend API endpoint `/stats/by-provider` is returning 404. This means:

1. **Backend URL might be wrong** in Vercel environment variables
2. **Backend might be down** on Railway
3. **Route might not be accessible** (auth issue)

## ✅ Quick Fixes

### Fix 1: Verify Backend URL in Vercel

1. Go to **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
2. Check `NEXT_PUBLIC_COLLECTOR_URL` value
3. Click the **eye icon** to reveal it
4. Should be: `https://your-backend.up.railway.app` (your Railway URL)
5. **NOT**: `http://localhost:8000` or empty

### Fix 2: Test Backend Directly

**Test if backend is running:**
```bash
curl https://your-backend-url.up.railway.app/health
```

**Should return:**
```json
{"status":"ok","service":"llmobserve-collector","version":"0.2.0"}
```

**If it fails:**
- Backend is down → Check Railway dashboard
- Wrong URL → Update Vercel env var

### Fix 3: Test Stats Endpoint

**Test the actual endpoint (requires auth):**
```bash
# Get your Clerk token first, then:
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-backend-url.up.railway.app/stats/by-provider?hours=24
```

**If 404:**
- Route not registered → Check Railway logs
- Auth failing → Check Clerk token

### Fix 4: Check Railway Logs

```bash
cd collector
railway logs
```

Look for:
- Errors starting the app
- Route registration issues
- Database connection errors

## 🚨 Most Likely Issue

**90% chance:** `NEXT_PUBLIC_COLLECTOR_URL` in Vercel is wrong or pointing to wrong backend.

**Check:**
1. Vercel Dashboard → Settings → Environment Variables
2. Verify `NEXT_PUBLIC_COLLECTOR_URL` matches your Railway backend URL
3. If wrong, update it and redeploy

## 📋 Checklist

- [ ] `NEXT_PUBLIC_COLLECTOR_URL` is set in Vercel
- [ ] Value matches Railway backend URL exactly
- [ ] Backend `/health` endpoint works
- [ ] Backend is running (check Railway dashboard)
- [ ] Vercel has been redeployed after env var changes

## 🔧 After Fixing

1. Update env var in Vercel if needed
2. Redeploy Vercel (or wait for auto-deploy)
3. Refresh `app.llmobserve.com/dashboard`
4. Check Network tab - should see 200 OK for API calls






