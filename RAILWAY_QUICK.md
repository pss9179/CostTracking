# 🚂 Railway Deployment - Quick Guide

## 1. Install & Login (2 min)

```bash
npm install -g @railway/cli
railway login
```

## 2. Deploy Backend (5 min)

```bash
cd collector
railway init                    # Create new project
railway up                      # Deploy (auto-detects Python)
```

## 3. Set Environment Variables

**Via CLI:**
```bash
railway variables set DATABASE_URL="postgresql://postgres:3ioIruC2XuyUPwnN@db.tsfzeoxffnfaiyqrlqwb.supabase.co:6543/postgres"
railway variables set ENV=production
railway variables set CLERK_SECRET_KEY="sk_live_YOUR_KEY"
railway variables set ALLOWED_ORIGINS="*"
```

**Or via Dashboard:**
- Railway Dashboard → Your Project → Variables → Add variables

## 4. Get Your URL

```bash
railway domain
# Returns: https://your-app.up.railway.app
```

## 5. Test

```bash
curl https://your-app.up.railway.app/health
```

**✅ Done!** Your backend is live.

---

## Optional: Use Railway PostgreSQL (Easier than Supabase)

1. Railway Dashboard → New → Database → PostgreSQL
2. Copy connection string
3. Set `DATABASE_URL` to that string
4. Redeploy: `railway up`

---

## View Logs

```bash
railway logs
```

---

**That's it!** Railway auto-detects Python, installs dependencies, and runs your FastAPI app.



