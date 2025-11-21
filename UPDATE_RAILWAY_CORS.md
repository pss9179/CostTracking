# How to Add app.llmobserve.com to Railway CORS

## Option 1: Via Railway Dashboard (Easiest)

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Select your backend service** (the one running your collector/API)
3. Click on **Variables** tab (or **Settings** → **Variables**)
4. Look for `ALLOWED_ORIGINS` variable
5. **Click Edit** (or Add if it doesn't exist)
6. **Set value to:**
   ```
   *
   ```
   (This allows all origins - easiest option)

   **OR** if you want specific domains:
   ```
   https://app.llmobserve.com,https://llmobserve.com,http://localhost:3000
   ```
   (Comma-separated list)

7. **Save**
8. Railway will automatically redeploy

## Option 2: Via Railway CLI

```bash
cd collector

# Login if needed
railway login

# Set ALLOWED_ORIGINS to allow all (easiest)
railway variables set ALLOWED_ORIGINS="*"

# OR set specific domains
railway variables set ALLOWED_ORIGINS="https://app.llmobserve.com,https://llmobserve.com,http://localhost:3000"

# Redeploy (usually happens automatically, but you can force it)
railway up
```

## Option 3: Check Current Value First

**See what's currently set:**
```bash
cd collector
railway variables
```

This will show all environment variables including `ALLOWED_ORIGINS`.

## ✅ Recommended: Use `*` (Allow All)

**Easiest and most flexible:**
```bash
railway variables set ALLOWED_ORIGINS="*"
```

This allows requests from any origin, so you don't need to update it every time you add a domain.

## 🎯 After Updating

1. Railway will automatically redeploy
2. Wait 1-2 minutes for deployment
3. Test your dashboard: `https://app.llmobserve.com/dashboard`
4. Check Network tab to see if API calls work now

## 📋 Quick Checklist

- [ ] Go to Railway Dashboard → Your Service → Variables
- [ ] Find `ALLOWED_ORIGINS`
- [ ] Set to `*` (or add `https://app.llmobserve.com` to list)
- [ ] Save
- [ ] Wait for redeploy
- [ ] Test dashboard





