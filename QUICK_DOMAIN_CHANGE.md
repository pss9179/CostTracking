# 🚀 Quick Domain Change Guide

## TL;DR: What You Need to Do

You're moving from `llmobserve.com` → `yourdomain.com` (Framer frontend).

**3 CRITICAL things you MUST change:**

---

## 1️⃣ **SendGrid Email Domain** (MOST IMPORTANT)

### In SendGrid Dashboard:
1. Go to: https://app.sendgrid.com/settings/sender_auth/senders
2. Add new sender: `alerts@yourdomain.com`
3. Go to: https://app.sendgrid.com/settings/sender_auth
4. Click "Authenticate Your Domain" → Add `yourdomain.com`
5. Add the DNS records they give you (CNAME records)
6. Wait 24-48 hours for verification ⏰

### In Your Code:
**File:** `collector/email_service.py` (Line 21)
```python
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@yourdomain.com")  # ← Change this
```

**Also update these URLs in same file (Lines 128-140):**
```python
# Line 128
https://app.llmobserve.dev/dashboard  →  https://yourdomain.com/dashboard

# Line 129
https://app.llmobserve.dev/settings  →  https://yourdomain.com/settings

# Line 140
https://app.llmobserve.dev/settings  →  https://yourdomain.com/settings
```

**Railway Env Vars:**
```bash
FROM_EMAIL=alerts@yourdomain.com
```

---

## 2️⃣ **Clerk Authentication URLs**

### In Clerk Dashboard:
1. Go to: https://dashboard.clerk.com → Your app
2. **Paths tab:**
   - Sign-in: `https://yourdomain.com/sign-in`
   - Sign-up: `https://yourdomain.com/sign-up`
   - After sign-in: `https://yourdomain.com/dashboard`
   - After sign-up: `https://yourdomain.com/onboarding`

3. **Allowed origins tab:**
   - Remove: `llmobserve.com`, `app.llmobserve.dev`
   - Add: `yourdomain.com`, `www.yourdomain.com`

---

## 3️⃣ **Backend CORS (Allow New Domain)**

**File:** `collector/main.py` (Around line 46)

```python
origins = [
    "https://yourdomain.com",        # ← Add this
    "https://www.yourdomain.com",    # ← Add this
    "http://localhost:3000",
]
```

**Then redeploy to Railway:**
```bash
cd /Users/pranavsrigiriraju/CostTracking/collector
railway up
```

---

## 4️⃣ **Stripe Checkout URLs** (Optional but Recommended)

**File:** `web/app/api/stripe/checkout/route.ts` (Lines 54-55)

```typescript
success_url: `https://yourdomain.com/settings?success=true`,
cancel_url: `https://yourdomain.com/settings?canceled=true`,
```

---

## 🎯 Do I Need to Update Anything Else?

### ✅ **YES - Update These:**
- SendGrid sender email & domain verification (CRITICAL)
- Clerk redirect URLs (CRITICAL)
- Backend CORS whitelist (CRITICAL)
- Email template links in `email_service.py` (users will see these)
- Stripe success/cancel URLs (for good UX)

### ❌ **NO - Keep These As-Is:**
- Railway backend URL (stays `llmobserve-api-production-d791.up.railway.app`)
- Stripe webhook URL (points to Railway, not your frontend)
- Database connections
- API keys

---

## ⚡ Quick Test After Changes

### Test 1: Email Sending
```bash
curl -X POST https://llmobserve-api-production-d791.up.railway.app/health
# Should return: {"status":"ok"}
```

### Test 2: CORS
Open browser console on `yourdomain.com` and run:
```javascript
fetch('https://llmobserve-api-production-d791.up.railway.app/health')
  .then(r => r.json())
  .then(console.log)
// Should NOT show CORS error
```

### Test 3: Clerk Login
Visit `yourdomain.com/sign-in` → Should work without redirect loops

---

## 📝 Files to Edit Summary

1. `collector/email_service.py` - Line 21, Lines 128-140
2. `collector/main.py` - CORS origins list
3. `web/app/api/stripe/checkout/route.ts` - Lines 54-55 (if keeping Next.js)

**Then:**
- Redeploy backend to Railway
- Update Railway env var: `FROM_EMAIL=alerts@yourdomain.com`
- Update Clerk dashboard settings
- Add SendGrid DNS records

---

## 🚨 CRITICAL: SendGrid Domain Verification

**Without this, your emails will:**
- Not send at all ❌
- Go to spam folder 📧
- Show as "unverified sender" ⚠️

**What to do:**
1. Add DNS records SendGrid gives you (usually 3 CNAME records)
2. Wait 24-48 hours for DNS propagation
3. SendGrid will show green checkmark when verified ✅
4. Test with the script in `DOMAIN_CHANGE_CHECKLIST.md`

---

## 🎯 Bottom Line

**If you only change 3 things:**
1. SendGrid domain verification
2. Clerk redirect URLs
3. Backend CORS whitelist

**You'll be 95% good to go!** 🚀

Everything else is nice-to-have for better UX.

