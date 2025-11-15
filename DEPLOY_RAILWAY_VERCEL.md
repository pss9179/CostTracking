# 🚀 Deploy to Railway + Vercel - Step by Step

## Architecture

```
Frontend (Vercel) → Backend API (Railway) → Database (Supabase)
```

---

## Part 1: Deploy Backend to Railway

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Login to Railway

```bash
railway login
```

This opens your browser to authenticate.

### Step 3: Create Railway Project

```bash
cd collector
railway init
```

This will:
- Create a new Railway project
- Link it to your current directory
- Ask you to name it (or use default)

### Step 4: Set Environment Variables

```bash
# Database (from your .env)
railway variables set DATABASE_URL="postgresql://postgres:EIPloItGt5NBmrLn@db.vcecetcumnreuzojtqin.supabase.co:5432/postgres"

# Basic config
railway variables set ENV=production
railway variables set SERVICE_NAME=llmobserve-api
railway variables set ALLOW_CONTENT_CAPTURE=false

# Clerk (from your .env)
railway variables set CLERK_SECRET_KEY="sk_test_I7GpNhomWiN13A3IHGEIm6G11zVmKIPMjAQZ2D8h5k"

# CORS (allow all for now, update with Vercel URL later)
railway variables set ALLOWED_ORIGINS="*"
```

### Step 5: Deploy!

```bash
railway up
```

Railway will:
- Detect Python automatically
- Install from `requirements.txt`
- Start with `uvicorn main:app` (from Procfile)
- Give you a URL like: `https://your-app.up.railway.app`

### Step 6: Get Your Backend URL

```bash
railway domain
```

**Copy this URL!** You'll need it for Vercel.

### Step 7: Test Backend

```bash
curl https://your-app.up.railway.app/health
```

Should return: `{"status":"ok","service":"llmobserve-collector","version":"0.2.0"}`

---

## Part 2: Deploy Frontend to Vercel

### Step 1: Login to Vercel (if not already)

```bash
cd ../web
vercel login
```

### Step 2: Deploy Frontend

```bash
vercel --prod
```

Or if you want to link to existing project:
```bash
vercel
```

### Step 3: Set Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_bWVldC1zd2luZS0yNC5jbGVyay5hY2NvdW50cy5kZXYk
CLERK_SECRET_KEY=sk_test_I7GpNhomWiN13A3IHGEIm6G11zVmKIPMjAQZ2D8h5k
NEXT_PUBLIC_COLLECTOR_URL=https://your-app.up.railway.app
```

**Important:** Replace `https://your-app.up.railway.app` with your actual Railway URL!

### Step 4: Redeploy with New Env Vars

```bash
vercel --prod
```

---

## Part 3: Connect Everything

### Update Railway CORS

After you get your Vercel URL, update Railway:

```bash
cd collector
railway variables set ALLOWED_ORIGINS="https://your-app.vercel.app"
```

### Update Clerk Webhooks

1. Go to Clerk Dashboard → Webhooks
2. Update webhook URL: `https://your-app.up.railway.app/webhooks/clerk`
3. Update allowed origins: `https://your-app.vercel.app`

---

## Part 4: Test Everything

1. **Backend:** `curl https://your-app.up.railway.app/health`
2. **Frontend:** Visit `https://your-app.vercel.app`
3. **Sign up:** Create account in frontend
4. **Get API key:** Go to Settings → API Keys
5. **Test SDK:** Use API key in your code

---

## Auto-Deploy from GitHub

### Railway

Railway auto-deploys from GitHub:
1. Railway Dashboard → Your Project → Settings → Source
2. Connect GitHub repo: `pss9179/CostTracking`
3. Set Root Directory: `collector`
4. Every push to `main` auto-deploys!

### Vercel

Vercel already auto-deploys (if connected):
- Every push to `main` → Auto-deploys frontend

---

## Useful Commands

### Railway

```bash
# View logs
railway logs

# View variables
railway variables

# Restart service
railway restart

# Open dashboard
railway open
```

### Vercel

```bash
# View logs
vercel logs

# List deployments
vercel ls

# Open dashboard
vercel open
```

---

## Troubleshooting

### Railway Build Fails

```bash
# Check logs
railway logs

# Common issues:
# - Missing requirements.txt → Check collector/requirements.txt exists
# - Wrong Python version → Railway auto-detects, but check Procfile
```

### Vercel Can't Connect to Railway

1. Check Railway URL is correct in `NEXT_PUBLIC_COLLECTOR_URL`
2. Check Railway CORS allows Vercel domain
3. Test Railway directly: `curl https://your-app.up.railway.app/health`

### Database Connection Fails

1. Check `DATABASE_URL` is correct
2. Verify Supabase allows connections from Railway IPs
3. Test connection: `psql "your-database-url" -c "SELECT 1;"`

---

## Cost Estimate

**Railway:**
- Free tier: $5 credit/month
- Usage: ~$5-10/month for moderate traffic

**Vercel:**
- Free tier: Unlimited for hobby projects
- Usage: Free for most use cases

**Total: ~$5-10/month** (mostly free!)

---

## Next Steps

1. ✅ Deploy backend to Railway
2. ✅ Deploy frontend to Vercel
3. ✅ Connect them together
4. ✅ Test signup flow
5. ✅ Test SDK integration
6. 🎉 You're live!


