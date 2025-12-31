# Quick Cloudflare Setup Checklist

## ⚡ 5-Minute Setup

### Step 1: Create Cloudflare Account (2 min)
- [ ] Go to https://dash.cloudflare.com/sign-up
- [ ] Sign up (free tier)
- [ ] Verify email

### Step 2: Add Your Domain (2 min)
- [ ] Click "Add a Site"
- [ ] Enter your domain (or Railway subdomain)
- [ ] Select Free plan
- [ ] Follow DNS setup instructions

### Step 3: Create API Subdomain (1 min)
- [ ] Go to DNS → Records
- [ ] Add CNAME record:
  - Name: `api`
  - Target: `llmobserve-api-production-d791.up.railway.app`
  - **Proxy: ON** (orange cloud) ⚠️ CRITICAL!
- [ ] Save

### Step 4: Update Frontend (1 min)
- [ ] Go to Vercel Dashboard → Your Project → Settings → Environment Variables
- [ ] Update `NEXT_PUBLIC_COLLECTOR_URL` to: `https://api.yourdomain.com`
- [ ] Redeploy frontend

### Step 5: Test (1 min)
- [ ] Open your app
- [ ] Reload dashboard
- [ ] Check Network tab - should be < 1 second! ✅

---

## 🎯 What You'll Get

- ✅ **99% of requests**: Instant (< 1 second)
- ✅ **New data**: Appears within 5-15 minutes automatically
- ✅ **No more 30-50 second waits**

---

## 🚨 Common Mistakes

1. **Forgetting to enable Proxy** (orange cloud) - Won't cache without this!
2. **Not updating Vercel env var** - Frontend still hits Railway directly
3. **Not redeploying frontend** - Old code still uses Railway URL

---

## 📞 Need Help?

See full guide: `CLOUDFLARE_SETUP.md`

