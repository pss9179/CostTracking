# 🔄 Domain Change Checklist

## Current Setup
- **Current Domain:** `llmobserve.com` / `app.llmobserve.dev`
- **New Frontend:** Framer (custom domain)
- **Backend:** Railway (`llmobserve-api-production-d791.up.railway.app`)

---

## 🚨 CRITICAL: What You MUST Change

### 1. **SendGrid Configuration** ⚠️ MOST IMPORTANT
SendGrid has strict domain verification requirements.

#### A. SendGrid Dashboard Changes
1. **Go to:** https://app.sendgrid.com/settings/sender_auth/senders
2. **Remove old sender:** `alerts@llmobserve.dev`
3. **Add new sender** with your new domain:
   - Email: `alerts@yourdomain.com` (or `noreply@yourdomain.com`)
   - From Name: `LLMObserve Alerts`
   
4. **Domain Authentication** (REQUIRED):
   - Go to: https://app.sendgrid.com/settings/sender_auth
   - Click "Authenticate Your Domain"
   - Add your new domain: `yourdomain.com`
   - Follow DNS instructions to add CNAME records
   - Wait for verification (can take 24-48 hours)

#### B. Environment Variable Changes
Update `FROM_EMAIL` in:

**Railway (Backend):**
```bash
# Go to Railway dashboard
# Variables → Add/Update:
FROM_EMAIL=alerts@yourdomain.com
```

**Local `.env`:**
```bash
FROM_EMAIL=alerts@yourdomain.com
```

**File:** `collector/email_service.py` (Line 21)
```python
FROM_EMAIL = os.getenv("FROM_EMAIL", "alerts@yourdomain.com")
```

---

### 2. **Stripe Configuration** 💳

#### A. Stripe Checkout URLs
**File:** `web/app/api/stripe/checkout/route.ts` (Lines 54-55)

```typescript
success_url: `${process.env.NEXT_PUBLIC_APP_URL || "https://yourdomain.com"}/settings?success=true`,
cancel_url: `${process.env.NEXT_PUBLIC_APP_URL || "https://yourdomain.com"}/settings?canceled=true`,
```

#### B. Stripe Dashboard Webhook URL
1. **Go to:** https://dashboard.stripe.com/webhooks
2. **Update endpoint URL:**
   - Old: `https://llmobserve-api-production-d791.up.railway.app/webhooks/stripe`
   - New: Keep the same (Railway backend URL doesn't change)

3. **Update redirect URLs in Stripe products** (if any)

---

### 3. **Clerk Authentication** 🔐

#### A. Clerk Dashboard Changes
1. **Go to:** https://dashboard.clerk.com
2. **Navigate to:** Your app → "Paths"
3. **Update these URLs:**
   - **Sign-in URL:** `https://yourdomain.com/sign-in`
   - **Sign-up URL:** `https://yourdomain.com/sign-up`
   - **After sign-in URL:** `https://yourdomain.com/dashboard`
   - **After sign-up URL:** `https://yourdomain.com/onboarding`

4. **Update Allowed Origins:**
   - Remove: `https://llmobserve.com`, `https://app.llmobserve.dev`
   - Add: `https://yourdomain.com`, `https://www.yourdomain.com`

5. **Update Session Settings:**
   - Allowed redirect URLs: Add `https://yourdomain.com/*`

#### B. Clerk Webhook URL (if you have one)
Update in Clerk Dashboard → Webhooks:
- Old: `https://llmobserve-api-production-d791.up.railway.app/webhooks/clerk`
- New: Keep the same (or update if you changed backend)

---

### 4. **Environment Variables** 🔧

#### A. Vercel (New Framer Frontend)
If you're moving frontend to Framer, you'll need these env vars somewhere (either in Framer settings or a backend proxy):

```bash
# If Framer needs to call your backend
NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
NEXT_PUBLIC_APP_URL=https://yourdomain.com

# Clerk (if Framer supports it, otherwise handle auth via backend)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
```

#### B. Railway (Backend)
Add/Update in Railway dashboard:
```bash
FRONTEND_URL=https://yourdomain.com
FROM_EMAIL=alerts@yourdomain.com
```

#### C. Local `.env`
```bash
NEXT_PUBLIC_APP_URL=https://yourdomain.com
FROM_EMAIL=alerts@yourdomain.com
```

---

### 5. **CORS Configuration** 🌐

**File:** `collector/main.py`

Update allowed origins to include your new domain:

```python
# Production: specific domains (comma-separated)
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "http://localhost:3000",  # Keep for local dev
]
```

Deploy this change to Railway:
```bash
cd /Users/pranavsrigiriraju/CostTracking/collector
railway up
```

---

### 6. **Email Template Links** 📧

**File:** `collector/email_service.py` (Lines 128-140)

Update all hardcoded URLs in email templates:

```python
# Line 128
<li>Review your <a href="https://yourdomain.com/dashboard">Dashboard</a> for detailed cost breakdown</li>

# Line 129
<li>Adjust your cap limits or optimize usage in <a href="https://yourdomain.com/settings">Settings</a></li>

# Line 140
<p>Manage your caps and alerts: <a href="https://yourdomain.com/settings">Settings</a></p>
```

---

### 7. **Documentation & Marketing** 📝

Update all references in:

- `README.md` (Lines mentioning llmobserve.com)
- `DEPLOYMENT.md`
- Any marketing materials
- Social media links
- GitHub repo description

---

## 🔄 Migration Steps (Recommended Order)

### Phase 1: Pre-Migration Setup
1. ✅ Set up new Framer frontend at `yourdomain.com`
2. ✅ Add SendGrid sender with new domain
3. ✅ Add DNS records for SendGrid verification
4. ✅ Update Clerk dashboard settings
5. ✅ Update Stripe redirect URLs

### Phase 2: Backend Updates
1. ✅ Update `collector/email_service.py` (email links)
2. ✅ Update `collector/main.py` (CORS origins)
3. ✅ Deploy to Railway:
   ```bash
   cd collector
   railway up
   ```
4. ✅ Update Railway env vars:
   ```bash
   FROM_EMAIL=alerts@yourdomain.com
   FRONTEND_URL=https://yourdomain.com
   ```

### Phase 3: Frontend Updates (if keeping Next.js)
1. ✅ Update `web/app/api/stripe/checkout/route.ts`
2. ✅ Update env vars in Vercel/deployment platform
3. ✅ Redeploy frontend

### Phase 4: Verification
1. ✅ Test SendGrid email sending (check spam folder)
2. ✅ Test Clerk login/signup flow
3. ✅ Test Stripe checkout (use test mode)
4. ✅ Test API calls from new domain
5. ✅ Check browser console for CORS errors

---

## 🧪 Testing Commands

### Test SendGrid Email
```bash
cd /Users/pranavsrigiriraju/CostTracking
cat > test_email_new_domain.py << 'EOF'
import os
os.environ["FROM_EMAIL"] = "alerts@yourdomain.com"  # ← Change this
os.environ["SENDGRID_API_KEY"] = "YOUR_KEY"
os.environ["EMAIL_PROVIDER"] = "sendgrid"

import asyncio
from collector.email_service import send_alert_email

async def test():
    result = await send_alert_email(
        to_email="your@email.com",  # ← Change this
        alert_type="threshold_reached",
        target_type="global",
        target_name="All Services",
        current_spend=45.0,
        cap_limit=50.0,
        percentage=90.0,
        period="daily"
    )
    print(f"Email sent: {result}")

asyncio.run(test())
EOF
python3 test_email_new_domain.py
```

### Test CORS
```bash
curl -X OPTIONS \
  -H "Origin: https://yourdomain.com" \
  -H "Access-Control-Request-Method: POST" \
  https://llmobserve-api-production-d791.up.railway.app/health
```

---

## ⚠️ Common Gotchas

### 1. SendGrid Domain Not Verified
**Problem:** Emails not sending, or going to spam  
**Solution:** Must authenticate domain in SendGrid (48hr wait for DNS propagation)

### 2. CORS Errors
**Problem:** Browser blocking API calls  
**Solution:** Update `collector/main.py` origins list and redeploy to Railway

### 3. Clerk Redirect Loops
**Problem:** Users stuck in redirect loop after login  
**Solution:** Update ALL redirect URLs in Clerk dashboard (paths, origins, session URLs)

### 4. Stripe Webhooks Failing
**Problem:** Subscriptions not activating  
**Solution:** Check webhook URL is still correct (should point to Railway, not your frontend)

### 5. Email Links Broken
**Problem:** Users click email links, go to old domain  
**Solution:** Update all hardcoded URLs in `email_service.py`

---

## 📋 Quick Checklist

- [ ] SendGrid sender authenticated for new domain
- [ ] SendGrid DNS records added and verified
- [ ] `FROM_EMAIL` updated in Railway env vars
- [ ] `FROM_EMAIL` updated in `collector/email_service.py`
- [ ] Email template URLs updated in `email_service.py`
- [ ] CORS origins updated in `collector/main.py`
- [ ] Clerk sign-in/sign-up URLs updated
- [ ] Clerk allowed origins updated
- [ ] Stripe success/cancel URLs updated
- [ ] Railway backend redeployed
- [ ] Test email sent successfully
- [ ] Test Clerk login flow
- [ ] Test Stripe checkout
- [ ] Test API calls (no CORS errors)
- [ ] DNS propagation complete (24-48 hrs)

---

## 🆘 Need Help?

**SendGrid Issues:**
- Docs: https://docs.sendgrid.com/ui/account-and-settings/how-to-set-up-domain-authentication
- Support: https://support.sendgrid.com

**Clerk Issues:**
- Docs: https://clerk.com/docs/deployments/set-up-production-instance
- Support: https://clerk.com/support

**Railway Issues:**
- Docs: https://docs.railway.app/deploy/deployments
- Support: https://railway.app/help

---

## 📞 What to Tell Your Co-Founder

"We're moving the frontend to Framer with a new domain. Here's what needs updating:

1. **SendGrid** - New sender email (takes 24-48hrs for verification)
2. **Clerk** - Update redirect URLs
3. **Stripe** - Update success/cancel URLs
4. **Backend CORS** - Add new domain to whitelist
5. **Email templates** - Update all links to new domain

Backend stays on Railway at the same URL. This is mostly config changes, no code rewrites."

