# 🔧 Fix Clerk Domain Restriction Issue

## Problem
You're using **production Clerk keys** (`pk_live_` and `sk_live_`) that are restricted to `llmobserve.com` domain. These keys won't work on:
- ❌ `localhost:3000` (local development)
- ❌ `*.vercel.app` (Vercel deployment)

## Solution: Use Test Keys for Development

### Step 1: Get Test Keys from Clerk

1. Go to **Clerk Dashboard**: https://dashboard.clerk.com
2. Select your application
3. Go to **API Keys** section
4. Look for **"Test"** or **"Development"** keys (they start with `pk_test_` and `sk_test_`)
5. If you don't see test keys, you may need to:
   - Switch to "Development" mode in Clerk dashboard
   - Or create a separate development application

### Step 2: Update Local Environment

Update your `.env.local` file:

```bash
cd web
# Backup current keys
cp .env.local .env.local.backup

# Edit .env.local and replace with test keys:
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY_HERE
CLERK_SECRET_KEY=sk_test_YOUR_TEST_SECRET_HERE
```

### Step 3: Configure Test Keys for Localhost

In Clerk Dashboard:
1. **Settings** → **Domains**
2. Under **Allowed Origins**, add:
   ```
   http://localhost:3000
   ```
3. Set **Application URL** to:
   ```
   http://localhost:3000
   ```

### Step 4: Restart Dev Server

```bash
# Stop current server (Ctrl+C)
# Then restart:
cd web
npm run dev
```

---

## Alternative: Configure Production Keys for Multiple Domains

If you want to use production keys everywhere:

### In Clerk Dashboard:
1. **Settings** → **Domains**
2. Add to **Allowed Origins**:
   ```
   http://localhost:3000
   https://*.vercel.app
   https://web-i81f1q7y9-pranavs-projects-78b1e712.vercel.app
   ```
3. Set **Application URL** to your production domain: `llmobserve.com`

**Note:** Production keys are typically restricted for security. Using test keys for development is the recommended approach.

---

## Quick Fix Script

Run this to switch to test keys (after you get them from Clerk):

```bash
cd web
# Edit .env.local manually with test keys
# Then restart:
npm run dev
```

---

## Verify It Works

1. Visit: http://localhost:3000/sign-in
2. Should see Clerk sign-in form (no errors)
3. Google OAuth button should appear (if configured)

---

## For Vercel Deployment

Use **production keys** (`pk_live_` and `sk_live_`) in Vercel environment variables, but make sure:
1. Vercel URL is added to Clerk **Allowed Origins**
2. Application URL in Clerk is set to your production domain


