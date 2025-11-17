# Railway Deployment Troubleshooting

## Quick Checklist Before Deploying:

1. ✅ **Service Created**: Go to Railway dashboard → "wonderful-delight" project → You should see a service
2. ✅ **Service Linked**: Run `railway service` in the collector directory to link
3. ✅ **Environment Variables Set**: Run `./railway_deploy_now.sh`

---

## Common Issues:

### Issue 1: "No service linked"
**Fix:**
```bash
cd collector
railway service
# Select your service when prompted
```

### Issue 2: "Multiple services found"
**Fix:**
```bash
railway service <service-name>
# Or specify service when deploying:
railway up --service <service-name>
```

### Issue 3: Database Connection Fails
**Check:**
1. Verify DATABASE_URL is set: `railway variables`
2. Test connection locally first
3. If still fails, try Railway PostgreSQL instead

### Issue 4: Build Fails
**Check:**
1. `requirements.txt` exists in collector directory
2. Railway auto-detects Python
3. Check logs: `railway logs`

---

## Step-by-Step Deployment:

```bash
# 1. Navigate to collector
cd collector

# 2. Link to project (if not already)
railway link --project wonderful-delight

# 3. Link to service (if multiple services exist)
railway service <your-service-name>

# 4. Deploy
./railway_deploy_now.sh

# 5. Check logs if issues
railway logs

# 6. Get URL
railway domain
```

---

## If Database Still Fails:

**Option A: Use Railway PostgreSQL (Easiest)**
1. Railway Dashboard → New → Database → PostgreSQL
2. Copy connection string
3. Update: `railway variables --set "DATABASE_URL=<railway-postgres-url>"`

**Option B: Check Supabase Settings**
1. Supabase Dashboard → Settings → Database
2. Check "Network restrictions" - should be "Allow all" or your Railway IPs
3. Try connection pooling URL from dashboard

---

## View Logs:

```bash
# Real-time logs
railway logs

# Specific service logs
railway logs --service <service-name>

# Last 100 lines
railway logs | tail -100
```

---

## Verify Deployment:

```bash
# Get your URL
railway domain

# Test health endpoint
curl https://your-app.up.railway.app/health

# Should return:
# {"status":"ok","service":"llmobserve-collector","version":"0.2.0"}
```



