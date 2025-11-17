# Deployment Guide

Complete guide for deploying LLM Observe to production.

## Architecture

```
┌──────────────────┐
│  Vercel (Frontend) │  ← app.llmobserve.com
│   Next.js + Clerk │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ Railway (Backend) │  ← api.llmobserve.com
│ FastAPI + Supabase│
└──────────────────┘
```

## Prerequisites

1. **Accounts Needed:**
   - [Vercel](https://vercel.com/) (free)
   - [Railway](https://railway.app/) (free $5 credit/month)
   - [Supabase](https://supabase.com/) (free tier)
   - [Clerk](https://clerk.com/) (free for 10K users)

2. **Domain (Optional):**
   - `app.llmobserve.com` → Vercel
   - `api.llmobserve.com` → Railway

---

## Part 1: Deploy Backend to Railway

### 1.1 Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create new project
cd /Users/pranavsrigiriraju/CostTracking/collector
railway init
```

### 1.2 Add Supabase PostgreSQL

In Railway dashboard:
1. Click "New" → "Database" → "PostgreSQL"
2. Or use existing Supabase connection string

### 1.3 Set Environment Variables

In Railway → Settings → Variables:

```bash
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
ENV=production
SERVICE_NAME=llmobserve-api
ALLOW_CONTENT_CAPTURE=false
```

### 1.4 Deploy

```bash
railway up
```

Railway will:
- Detect Python
- Install from `requirements.txt`
- Run using `Procfile`
- Assign a public URL (e.g., `llmobserve-production.up.railway.app`)

### 1.5 Verify Backend

```bash
curl https://your-app.up.railway.app/health
# Should return: {"status":"ok","service":"llmobserve-collector","version":"0.2.0"}
```

---

## Part 2: Deploy Frontend to Vercel

### 2.1 Connect to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy from web directory
cd /Users/pranavsrigiriraju/CostTracking/web
vercel
```

### 2.2 Set Environment Variables

In Vercel dashboard → Settings → Environment Variables:

```bash
# Clerk Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx
CLERK_SECRET_KEY=sk_live_xxxxx

# Backend API
NEXT_PUBLIC_COLLECTOR_URL=https://your-app.up.railway.app
```

### 2.3 Deploy to Production

```bash
vercel --prod
```

### 2.4 Verify Frontend

Visit your Vercel URL (e.g., `llmobserve.vercel.app`)

---

## Part 3: Custom Domains (Optional)

### 3.1 Frontend Domain (Vercel)

1. Go to Vercel → Project → Settings → Domains
2. Add `app.llmobserve.com`
3. Add DNS records (Vercel provides instructions):
   ```
   Type: A
   Name: app
   Value: 76.76.21.21
   ```

### 3.2 Backend Domain (Railway)

1. Go to Railway → Settings → Networking → Custom Domain
2. Add `api.llmobserve.com`
3. Add DNS record:
   ```
   Type: CNAME
   Name: api
   Value: your-app.up.railway.app
   ```

4. Update frontend env var:
   ```bash
   NEXT_PUBLIC_COLLECTOR_URL=https://api.llmobserve.com
   ```

---

## Part 4: Configure Clerk Webhooks

Clerk needs to sync users to our database.

### 4.1 Create Webhook

1. Go to Clerk Dashboard → Webhooks → Add Endpoint
2. Set URL: `https://api.llmobserve.com/users/clerk-webhook`
3. Subscribe to events:
   - `user.created`
   - `user.updated`
4. Copy Signing Secret

### 4.2 Add Webhook Secret to Railway

```bash
CLERK_WEBHOOK_SECRET=whsec_xxxxx
```

---

## Part 5: Test Production Deployment

### 5.1 Sign Up Flow

1. Visit `https://app.llmobserve.com`
2. Click "Sign Up"
3. Create account
4. Should redirect to `/onboarding`
5. See API key displayed

### 5.2 Test SDK

```python
from llmobserve import observe
from openai import OpenAI

observe(
    collector_url="https://api.llmobserve.com",
    api_key="llmo_sk_xxx"  # From onboarding
)

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "test"}]
)
```

### 5.3 Verify Dashboard

1. Go to `https://app.llmobserve.com`
2. Should see the test run
3. Cost, tokens, latency should be tracked

---

## Part 6: Monitoring & Maintenance

### 6.1 Railway Metrics

Monitor in Railway dashboard:
- CPU usage
- Memory usage
- Request count
- Response times

### 6.2 Supabase Database

Monitor in Supabase dashboard:
- Database size (500MB free tier)
- Connection count
- Query performance

### 6.3 Vercel Analytics

Free analytics in Vercel dashboard:
- Page views
- Unique visitors
- Performance scores

---

## Environment Variables Checklist

### Frontend (Vercel)
- ✅ `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
- ✅ `CLERK_SECRET_KEY`
- ✅ `NEXT_PUBLIC_COLLECTOR_URL`

### Backend (Railway)
- ✅ `DATABASE_URL`
- ✅ `ENV=production`
- ✅ `SERVICE_NAME=llmobserve-api`
- ✅ `ALLOW_CONTENT_CAPTURE=false`
- ✅ `CLERK_WEBHOOK_SECRET` (optional)

---

## Cost Breakdown

| Service | Free Tier | Paid Plans |
|---------|-----------|------------|
| Vercel | Unlimited hobby projects | $20/month Pro |
| Railway | $5/month credit | $5/month pay-as-you-go |
| Supabase | 500MB database | $25/month Pro |
| Clerk | 10K MAU | $25/month Pro |

**Initial Cost: $0** (using free tiers)

**Expected Cost at 100 users:**
- Railway: ~$5-10/month
- Other services: Free tier sufficient

---

## Troubleshooting

### Backend 500 Error

Check Railway logs:
```bash
railway logs
```

Common issues:
- Database connection failed → Check `DATABASE_URL`
- Missing environment variable → Verify all vars set

### Frontend Can't Connect to Backend

1. Check CORS settings in `collector/main.py`
2. Verify `NEXT_PUBLIC_COLLECTOR_URL` is correct
3. Test backend directly: `curl https://api.llmobserve.com/health`

### Clerk Sign-in Issues

1. Check allowed domains in Clerk dashboard
2. Verify redirect URLs include your Vercel domain
3. Ensure environment variables are correct

---

## Rollback Plan

### Revert Backend
```bash
cd collector
railway rollback
```

### Revert Frontend
In Vercel dashboard → Deployments → Previous deployment → "Promote to Production"

---

## Next Steps

After deployment:

1. ✅ Set up custom domains
2. ✅ Configure Clerk production instance
3. ✅ Enable SSL/HTTPS (automatic on Vercel & Railway)
4. ✅ Set up monitoring alerts
5. ✅ Publish SDK to PyPI
6. ✅ Create documentation site
7. ✅ Announce launch! 🎉

---

## Support

- Documentation: `https://docs.llmobserve.com` (coming soon)
- Issues: GitHub Issues
- Email: support@llmobserve.com






