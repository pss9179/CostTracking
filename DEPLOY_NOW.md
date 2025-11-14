# 🚀 DEPLOY NOW - Step-by-Step Guide

## Choose Your Path

### Option A: Quick Deploy (No Domain Needed) ⚡
**Time: 15 minutes**  
**Use Railway/Vercel subdomains - add custom domain later**

### Option B: Full Production (With Custom Domain) 🌐
**Time: 30 minutes**  
**Requires domain name**

---

## 🚀 OPTION A: Quick Deploy (Start Here!)

### Step 1: Install CLIs (2 minutes)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Install Vercel CLI
npm install -g vercel
```

### Step 2: Login to Services (2 minutes)

```bash
# Login to Railway
railway login

# Login to Vercel
vercel login
```

### Step 3: Get Your Credentials Ready

**You need:**
1. ✅ **Clerk Production Keys** (switch to Production in Clerk dashboard)
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx`
   - `CLERK_SECRET_KEY=sk_live_xxxxx`

2. ✅ **Database URL** (you already have this!)
   - `DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres`

3. ✅ **Email Service** (choose one):
   - **SendGrid** (easiest): Get API key from https://sendgrid.com
   - **SMTP**: Gmail app password
   - **AWS SES**: Access keys

### Step 4: Deploy Backend to Railway (5 minutes)

```bash
cd collector

# Initialize Railway project
railway init

# Set environment variables
railway variables set DATABASE_URL="your-database-url"
railway variables set ENV=production
railway variables set SERVICE_NAME=llmobserve-api
railway variables set ALLOW_CONTENT_CAPTURE=false
railway variables set CLERK_SECRET_KEY="sk_live_xxxxx"

# Email service (choose one):
# SendGrid:
railway variables set EMAIL_PROVIDER=sendgrid
railway variables set SENDGRID_API_KEY="SG.xxxxx"

# OR SMTP:
# railway variables set EMAIL_PROVIDER=smtp
# railway variables set SMTP_HOST="smtp.gmail.com"
# railway variables set SMTP_PORT="587"
# railway variables set SMTP_USERNAME="your-email@gmail.com"
# railway variables set SMTP_PASSWORD="your-app-password"

# CORS (allow all for now, update later)
railway variables set ALLOWED_ORIGINS="*"

# Deploy!
railway up

# Get your Railway URL
railway domain
# Copy this URL - you'll need it for frontend
```

**✅ Backend deployed!** Note your Railway URL (e.g., `your-app.up.railway.app`)

### Step 5: Deploy Frontend to Vercel (5 minutes)

```bash
cd ../web

# Initialize Vercel project
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
# Paste: pk_live_xxxxx

vercel env add CLERK_SECRET_KEY production
# Paste: sk_live_xxxxx

vercel env add NEXT_PUBLIC_COLLECTOR_URL production
# Paste: https://your-app.up.railway.app (from Step 4)

# Deploy to production!
vercel --prod
```

**✅ Frontend deployed!** Note your Vercel URL (e.g., `your-app.vercel.app`)

### Step 6: Update Clerk Webhooks (2 minutes)

1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Go to **Webhooks**
3. Update webhook URL to: `https://your-app.up.railway.app/webhooks/clerk`
4. Update allowed origins to: `https://your-app.vercel.app`

### Step 7: Test! (2 minutes)

```bash
# Test backend
curl https://your-app.up.railway.app/health

# Test frontend
open https://your-app.vercel.app
```

**🎉 You're live!** Users can now sign up and use your platform.

---

## 🌐 OPTION B: Full Production (With Custom Domain)

### Prerequisites

1. **Domain name** (e.g., `llmobserve.com`)
2. **All credentials from Option A**

### Step 1-5: Same as Option A

Deploy to Railway/Vercel subdomains first (use Option A steps 1-5).

### Step 6: Add Custom Domain to Railway

```bash
cd collector

# Add custom domain
railway domain add api.yourdomain.com

# Railway will give you DNS instructions
# Add CNAME record: api → railway-provided-hostname
```

### Step 7: Add Custom Domain to Vercel

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add: `app.yourdomain.com`
3. Vercel will give you DNS instructions
4. Add A record: `app` → Vercel IP

### Step 8: Update Environment Variables

**Railway:**
```bash
cd collector
railway variables set ALLOWED_ORIGINS="https://app.yourdomain.com,https://www.yourdomain.com"
```

**Vercel:**
```bash
cd web
vercel env rm NEXT_PUBLIC_COLLECTOR_URL production
vercel env add NEXT_PUBLIC_COLLECTOR_URL production
# Paste: https://api.yourdomain.com
```

### Step 9: Update Clerk

1. Update webhook URL: `https://api.yourdomain.com/webhooks/clerk`
2. Update allowed origins: `https://app.yourdomain.com`

### Step 10: Wait for DNS (5-60 minutes)

DNS propagation can take up to an hour. Check with:
```bash
curl https://api.yourdomain.com/health
curl https://app.yourdomain.com
```

**🎉 Full production deployment complete!**

---

## 🔧 Troubleshooting

### Backend won't start

```bash
# Check logs
railway logs

# Common issues:
# - DATABASE_URL wrong → Check connection string
# - Missing env vars → Check railway variables list
```

### Frontend shows errors

```bash
# Check Vercel logs
vercel logs

# Common issues:
# - Clerk keys wrong → Use production keys
# - Collector URL wrong → Use Railway URL
```

### Database connection fails

```bash
# Test connection
psql "your-database-url" -c "SELECT 1;"

# If fails, create new Supabase project:
# 1. Go to supabase.com
# 2. New project
# 3. Copy connection string
```

---

## 📋 Quick Checklist

**Before deploying:**
- [ ] Railway CLI installed
- [ ] Vercel CLI installed
- [ ] Logged into Railway
- [ ] Logged into Vercel
- [ ] Clerk production keys ready
- [ ] Database URL ready
- [ ] Email service credentials ready

**After deploying:**
- [ ] Backend health check works
- [ ] Frontend loads
- [ ] Can sign up with Clerk
- [ ] Can generate API key
- [ ] Can create spending cap
- [ ] Email alerts work (test with cap)

---

## 🎯 Next Steps After Deployment

1. **Test SDK integration:**
   ```python
   import llmobserve
   llmobserve.observe(
       collector_url="https://your-backend-url",
       api_key="your-api-key"
   )
   ```

2. **Monitor logs:**
   ```bash
   railway logs  # Backend
   vercel logs   # Frontend
   ```

3. **Set up monitoring:**
   - Railway dashboard for backend metrics
   - Vercel dashboard for frontend metrics
   - Clerk dashboard for user metrics

4. **Add custom domain** (if you used Option A):
   - Follow Option B steps 6-10

---

## 💰 Cost Estimate

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

## 🚨 Emergency Rollback

If something breaks:

```bash
# Rollback Railway
railway rollback

# Rollback Vercel
vercel rollback

# Or redeploy previous version
railway up
vercel --prod
```

---

## ✅ Ready?

**Start with Option A** (quick deploy) to get live in 15 minutes, then add custom domain later!

**Questions?** Check the deployment checklist or ask me! 🚀

