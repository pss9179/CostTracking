# Why Moving to Subdomain Might Break Things

You're right - just changing the domain shouldn't break API calls. But there are **2 external services** that need to know about your new domain:

## 🔐 Issue 1: Clerk Configuration (Most Likely)

**Clerk blocks requests from domains it doesn't recognize.** If you moved from `your-app.vercel.app` to `app.llmobserve.com`, Clerk needs to be updated.

### Fix in Clerk Dashboard:

1. Go to https://dashboard.clerk.com
2. Select your app
3. Go to **Paths** tab
4. Update these URLs:
   - Sign-in URL: `https://app.llmobserve.com/sign-in`
   - Sign-up URL: `https://app.llmobserve.com/sign-up`
   - After sign-in: `https://app.llmobserve.com/dashboard`
   - After sign-up: `https://app.llmobserve.com/onboarding`

5. Go to **Allowed Origins** tab
6. **Add**: `https://app.llmobserve.com`
7. **Keep**: `https://llmobserve.com` (for Framer)
8. **Remove**: Old Vercel domain if you're not using it anymore

**This is probably why API calls are failing** - Clerk is blocking authentication because the domain isn't allowed.

## 🌐 Issue 2: Backend CORS (Less Likely)

If your backend has `ALLOWED_ORIGINS` set to specific domains (not `*`), it needs to include the subdomain.

### Check Railway Backend:

1. Go to Railway Dashboard → Your Service → Variables
2. Check `ALLOWED_ORIGINS` value:
   - ✅ If it's `*` → You're good (allows all)
   - ❌ If it's a list → Add `https://app.llmobserve.com`

**If you need to update:**
```bash
cd collector
railway variables set ALLOWED_ORIGINS="*"
railway up
```

## 🧪 Quick Test

**Test if it's a Clerk issue:**

1. Open `https://app.llmobserve.com/dashboard` in browser
2. Open DevTools → Console
3. Look for errors like:
   - `Clerk: Invalid origin`
   - `Clerk: Domain not allowed`
   - Authentication errors

**Test if it's a CORS issue:**

1. Open DevTools → Network tab
2. Filter by "Fetch/XHR"
3. Try to load dashboard
4. Look for API calls to your backend
5. Check if they show:
   - ❌ CORS error → Backend CORS issue
   - ❌ 401 Unauthorized → Clerk/auth issue
   - ❌ 404 → Wrong backend URL

## ✅ What Should Work Without Changes

- ✅ Vercel deployment (just works)
- ✅ Environment variables (same values)
- ✅ Backend API (if CORS allows `*`)
- ✅ Database connections (unchanged)

## ❌ What Needs Configuration

- ❌ **Clerk allowed origins** (MUST update)
- ❌ **Clerk redirect URLs** (should update)
- ❌ **Backend CORS** (only if not set to `*`)

## 🎯 Most Likely Fix

**90% chance it's Clerk:**

1. Go to Clerk Dashboard
2. Add `https://app.llmobserve.com` to **Allowed Origins**
3. Update **Paths** to use `app.llmobserve.com`
4. Refresh your dashboard

That should fix it immediately!





