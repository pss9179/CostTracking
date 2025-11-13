# 🚀 Production Deployment Checklist

## What I Need From You

### 1. **Domain Name** 🌐
- [ ] Do you have a domain? (e.g., `llmobserve.com`, `costtracker.io`)
- [ ] If not, purchase one from:
  - [Namecheap](https://www.namecheap.com/) (~$10/year)
  - [Google Domains](https://domains.google/) (~$12/year)
  - [Cloudflare](https://www.cloudflare.com/products/registrar/) (~$8/year)

**What I'll use it for:**
- `app.yourdomain.com` → Frontend (Vercel)
- `api.yourdomain.com` → Backend (Railway)

---

### 2. **Production Clerk Keys** 🔐
- [ ] Switch Clerk to **Production** mode
- [ ] Get production keys:
  - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx`
  - `CLERK_SECRET_KEY=sk_live_xxxxx`
- [ ] Update Clerk dashboard:
  - Allowed domains: `app.yourdomain.com`
  - Redirect URLs: `https://app.yourdomain.com/*`

---

### 3. **Email Service for Alerts** 📧
Choose ONE:

**Option A: SMTP (Gmail/Outlook)**
- [ ] Gmail App Password (if using Gmail)
- [ ] Or SMTP credentials:
  ```
  SMTP_HOST=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  ```

**Option B: SendGrid** (Recommended)
- [ ] Sign up: https://sendgrid.com
- [ ] Get API key: `SENDGRID_API_KEY=SG.xxxxx`
- [ ] Verify sender email

**Option C: AWS SES**
- [ ] AWS account
- [ ] SES region: `AWS_SES_REGION=us-east-1`
- [ ] Access keys: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

---

### 4. **Database** 🗄️
- [ ] **Option A: Supabase** (Recommended - Free tier)
  - Already have: `DATABASE_URL` from `.env`
  - Just verify it works: `psql $DATABASE_URL -c "SELECT 1;"`
  
- [ ] **Option B: Railway PostgreSQL**
  - Create in Railway dashboard
  - Get connection string

---

### 5. **Hosting Accounts** ☁️
- [ ] **Vercel Account** (Frontend)
  - Sign up: https://vercel.com
  - Connect GitHub repo
  
- [ ] **Railway Account** (Backend)
  - Sign up: https://railway.app
  - Connect GitHub repo
  - Add payment method (for custom domain)

---

## What I'll Configure For You

Once you provide the above, I'll:

1. ✅ **Update environment variables** in Railway & Vercel
2. ✅ **Configure custom domains** (DNS instructions)
3. ✅ **Set up Clerk webhooks** (production URL)
4. ✅ **Test end-to-end** deployment
5. ✅ **Create deployment scripts** for easy updates

---

## Step-by-Step Deployment Process

### Phase 1: Initial Setup (I'll do this)

```bash
# 1. Deploy backend to Railway
cd collector
railway login
railway init
railway up

# 2. Deploy frontend to Vercel
cd web
vercel login
vercel --prod
```

### Phase 2: Custom Domain Setup (You do this)

**Frontend (Vercel):**
1. Vercel Dashboard → Your Project → Settings → Domains
2. Add: `app.yourdomain.com`
3. Copy DNS instructions (I'll provide exact values)

**Backend (Railway):**
1. Railway Dashboard → Your Service → Settings → Networking
2. Add custom domain: `api.yourdomain.com`
3. Copy DNS instructions (I'll provide exact values)

**DNS (Your Domain Provider):**
1. Add A record: `app` → Vercel IP (provided by Vercel)
2. Add CNAME record: `api` → Railway hostname (provided by Railway)
3. Wait 5-60 minutes for DNS propagation

### Phase 3: Update Clerk (You do this)

1. Clerk Dashboard → Webhooks
2. Update webhook URL: `https://api.yourdomain.com/webhooks/clerk`
3. Update allowed origins: `https://app.yourdomain.com`

### Phase 4: Test (I'll do this)

```bash
# Test backend
curl https://api.yourdomain.com/health

# Test frontend
open https://app.yourdomain.com

# Test signup flow
# Test API key generation
# Test SDK integration
```

---

## Environment Variables Template

### **Frontend (Vercel)**
```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx
CLERK_SECRET_KEY=sk_live_xxxxx
NEXT_PUBLIC_COLLECTOR_URL=https://api.yourdomain.com
```

### **Backend (Railway)**
```bash
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
ENV=production
SERVICE_NAME=llmobserve-api
ALLOW_CONTENT_CAPTURE=false
CLERK_SECRET_KEY=sk_live_xxxxx
CLERK_WEBHOOK_SECRET=whsec_xxxxx

# CORS (comma-separated list of allowed origins)
ALLOWED_ORIGINS=https://app.yourdomain.com,https://www.yourdomain.com

# Email Service (choose one)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxx
# OR
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

---

## Quick Start Commands

Once everything is set up:

```bash
# Deploy backend
cd collector
railway up

# Deploy frontend
cd web
vercel --prod

# View logs
railway logs
vercel logs
```

---

## Cost Estimate

| Service | Free Tier | Your Usage | Cost |
|---------|-----------|------------|------|
| Vercel | Unlimited | ~100 users | **$0** |
| Railway | $5 credit | ~100 users | **$5-10/mo** |
| Supabase | 500MB DB | ~100 users | **$0** |
| Clerk | 10K MAU | ~100 users | **$0** |
| SendGrid | 100 emails/day | Alerts | **$0** |
| Domain | - | 1 domain | **~$10/year** |

**Total: ~$15-20/month** (mostly free tier)

---

## What to Send Me

Just fill this out:

```
Domain: ___________________
Clerk Production Keys:
  - pk_live_xxxxx: ___________________
  - sk_live_xxxxx: ___________________

Email Service: [ ] SMTP [ ] SendGrid [ ] AWS SES
  Credentials: ___________________

Database: [ ] Supabase [ ] Railway PostgreSQL
  Connection String: ___________________

Vercel Account: [ ] Created [ ] Connected to GitHub
Railway Account: [ ] Created [ ] Connected to GitHub
```

---

## Next Steps

1. **You provide:** Domain, Clerk keys, email service
2. **I configure:** All environment variables, DNS instructions
3. **You add:** DNS records (5 minutes)
4. **I test:** Full deployment end-to-end
5. **We launch:** 🚀

---

## Questions?

- **"Do I need a domain?"** → Yes, for production. Can use Railway/Vercel subdomains for testing.
- **"Which email service?"** → SendGrid is easiest (free tier, good docs).
- **"Can I use free tiers?"** → Yes! Everything works on free tiers for ~100 users.
- **"How long does deployment take?"** → ~30 minutes once you provide credentials.

---

**Ready? Just send me the info above and I'll handle the rest!** 🎯

