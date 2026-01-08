# 🔧 Fix Clerk Domain Error

## Error Message
```
Clerk: Production Keys are only allowed for domain "llmobserve.com".
API Error: The Request HTTP Origin header must be equal to or a subdomain of the requesting URL.
```

## Root Cause
Your **production Clerk keys** (`pk_live_` and `sk_live_`) are restricted to `llmobserve.com` domain only. When you try to use them on Vercel (`*.vercel.app`), Clerk rejects the request.

## Solution: Add Vercel Domain to Clerk

### Step 1: Go to Clerk Dashboard
👉 https://dashboard.clerk.com

### Step 2: Select Your Application
- Find the app with domain `llmobserve.com`
- This is the one using production keys

### Step 3: Configure Allowed Origins
1. Navigate to: **Settings** → **Domains**
2. Find **"Allowed Origins"** section
3. Click **"Add Origin"** or edit existing origins
4. Add your Vercel URLs:

**Option A: Add Specific URLs** (More Secure)
```
https://web-gdwr55tkl-pranavs-projects-78b1e712.vercel.app
https://web-sandy-six-94.vercel.app
https://web-pranavs-projects-78b1e712.vercel.app
```

**Option B: Use Wildcard** (Easier, Less Secure)
```
https://*.vercel.app
```

**Option C: Add Both** (Recommended)
```
https://llmobserve.com
https://*.vercel.app
http://localhost:3000
```

### Step 4: Set Application URL
In the same **Settings** → **Domains** section:
- **Application URL**: Keep as `https://llmobserve.com` (your production domain)
- This is your primary domain

### Step 5: Configure Redirect URLs
Under **"Redirect URLs"**, add:
```
https://*.vercel.app/*
http://localhost:3000/*
```

### Step 6: Save Changes
Click **"Save"** in Clerk dashboard

### Step 7: Test
1. Wait 1-2 minutes for changes to propagate
2. Visit: https://web-gdwr55tkl-pranavs-projects-78b1e712.vercel.app/sign-in
3. Error should be gone ✅

---

## Alternative Solution: Use Test Keys for Vercel

If you prefer to keep production keys production-only:

### Step 1: Get Test Keys
1. Go to Clerk Dashboard
2. Switch to **"Development"** mode (or create dev app)
3. Get test keys (`pk_test_` and `sk_test_`)

### Step 2: Update Vercel Environment Variables
```bash
cd web
vercel env rm NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
vercel env rm CLERK_SECRET_KEY production
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
# Paste: pk_test_YOUR_TEST_KEY
vercel env add CLERK_SECRET_KEY production
# Paste: sk_test_YOUR_TEST_SECRET
```

### Step 3: Configure Test Keys for Vercel
- In Clerk Dashboard (test/development app)
- Settings → Domains → Allowed Origins
- Add: `https://*.vercel.app`

### Step 4: Redeploy
```bash
vercel --prod
```

---

## Recommended Approach

**For Production**: Use production keys and add Vercel to Allowed Origins
- ✅ Keeps production keys for production domain
- ✅ Allows Vercel deployments to work
- ✅ Single set of keys to manage

**For Development**: Use test keys locally
- ✅ Test keys work on `localhost:3000`
- ✅ No domain restrictions
- ✅ Safe for development

---

## Quick Fix Checklist

- [ ] Go to Clerk Dashboard → Settings → Domains
- [ ] Add `https://*.vercel.app` to Allowed Origins
- [ ] Add `http://localhost:3000` (for local dev)
- [ ] Save changes
- [ ] Wait 1-2 minutes
- [ ] Test sign-in page

---

## Verify It Works

After adding domains:
1. Visit: https://web-gdwr55tkl-pranavs-projects-78b1e712.vercel.app/sign-in
2. Check browser console (F12)
3. Should see:
   - ✅ No Clerk domain errors
   - ✅ Sign-in form loads
   - ✅ Google OAuth button appears (if enabled)

---

## Why This Happens

Clerk production keys are domain-restricted for security:
- Prevents unauthorized use of your keys
- Protects against key theft
- Ensures keys only work on approved domains

Adding Vercel domains tells Clerk: "These domains are authorized to use these keys."


