# 🚂 Deploy to Railway - Step-by-Step Guide

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app (free $5 credit/month)
2. **GitHub Account**: Your code should be on GitHub
3. **Database URL**: Your Supabase connection string

---

## Step 1: Install Railway CLI (2 minutes)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Or with Homebrew (Mac)
brew install railway
```

---

## Step 2: Login to Railway (1 minute)

```bash
railway login
```

This will open your browser to authenticate.

---

## Step 3: Initialize Railway Project (2 minutes)

```bash
cd collector

# Initialize Railway project (links to GitHub repo)
railway init
```

**Choose:**
- "Create new project" → Name it `llmobserve-backend`
- "Link to existing project" → If you already have one

---

## Step 4: Set Environment Variables (3 minutes)

```bash
# Database (use your Supabase URL with port 6543)
railway variables set DATABASE_URL="postgresql://postgres:3ioIruC2XuyUPwnN@db.tsfzeoxffnfaiyqrlqwb.supabase.co:6543/postgres"

# Environment
railway variables set ENV=production
railway variables set SERVICE_NAME=llmobserve-api
railway variables set ALLOW_CONTENT_CAPTURE=false

# Clerk (get from Clerk dashboard - Production keys)
railway variables set CLERK_SECRET_KEY="sk_live_YOUR_KEY_HERE"

# CORS (allow all for now)
railway variables set ALLOWED_ORIGINS="*"

# Email Service (choose ONE):

# Option A: SendGrid (recommended)
railway variables set EMAIL_PROVIDER=sendgrid
railway variables set SENDGRID_API_KEY="SG.YOUR_KEY_HERE"

# Option B: SMTP (Gmail)
# railway variables set EMAIL_PROVIDER=smtp
# railway variables set SMTP_HOST="smtp.gmail.com"
# railway variables set SMTP_PORT="587"
# railway variables set SMTP_USERNAME="your-email@gmail.com"
# railway variables set SMTP_PASSWORD="your-app-password"
```

---

## Step 5: Deploy! (5 minutes)

```bash
# Deploy to Railway
railway up
```

Railway will:
1. ✅ Detect Python
2. ✅ Install dependencies from `requirements.txt`
3. ✅ Start with `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. ✅ Assign a public URL

**Wait for deployment to complete** (2-3 minutes)

---

## Step 6: Get Your Backend URL (1 minute)

```bash
# Get your Railway URL
railway domain
```

**Example output:**
```
https://llmobserve-backend-production.up.railway.app
```

**✅ Copy this URL** - you'll need it for the frontend!

---

## Step 7: Test Your Backend (1 minute)

```bash
# Test health endpoint
curl https://your-app.up.railway.app/health
```

**Expected response:**
```json
{"status":"ok","service":"llmobserve-collector","version":"0.2.0"}
```

---

## Step 8: Deploy Frontend to Vercel (5 minutes)

```bash
cd ../web

# Install Vercel CLI (if not already installed)
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# Set environment variables
vercel env add NEXT_PUBLIC_COLLECTOR_URL production
# When prompted, paste: https://your-app.up.railway.app

vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY production
# When prompted, paste: pk_live_YOUR_KEY

vercel env add CLERK_SECRET_KEY production
# When prompted, paste: sk_live_YOUR_KEY

# Deploy to production
vercel --prod
```

---

## ✅ You're Done!

**Your app is live:**
- **Backend**: `https://your-app.up.railway.app`
- **Frontend**: `https://your-app.vercel.app`

---

## Troubleshooting

### Database Connection Issues

If you still get database errors:

1. **Check Railway logs:**
   ```bash
   railway logs
   ```

2. **Try Railway's PostgreSQL** (easier than Supabase):
   - Railway Dashboard → New → Database → PostgreSQL
   - Copy the connection string
   - Update `DATABASE_URL`:
     ```bash
     railway variables set DATABASE_URL="postgresql://postgres:xxx@containers-us-west-xxx.railway.app:5432/railway"
     ```

### View Logs

```bash
# View real-time logs
railway logs

# View specific service logs
railway logs --service your-service-name
```

### Update Environment Variables

```bash
# List all variables
railway variables

# Update a variable
railway variables set DATABASE_URL="new-url"

# Delete a variable
railway variables delete VARIABLE_NAME
```

### Redeploy

```bash
# Redeploy after code changes
railway up

# Or push to GitHub (if connected)
git push origin main
```

---

## Next Steps

1. ✅ **Add Custom Domain** (optional):
   - Railway Dashboard → Settings → Domains
   - Add your domain (e.g., `api.yourdomain.com`)

2. ✅ **Update Clerk Webhooks**:
   - Clerk Dashboard → Webhooks
   - Update webhook URL to: `https://your-app.up.railway.app/webhooks/clerk`

3. ✅ **Monitor Usage**:
   - Railway Dashboard → Metrics
   - Track CPU, memory, and network usage

---

## Cost

**Railway Free Tier:**
- $5 credit/month
- Enough for small-medium apps
- Pay-as-you-go after that

**Typical costs:**
- Backend: $5-10/month
- Database: $5/month (if using Railway PostgreSQL)

---

## Need Help?

1. Check Railway logs: `railway logs`
2. Railway docs: https://docs.railway.app
3. Railway Discord: https://discord.gg/railway



