# 🚀 Migrate Service to US East

Render doesn't support changing regions for existing services. You need to create a new service in US East.

## Step 1: Create New Service in US East

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Web Service"**
3. Connect GitHub → Select `pss9179/CostTracking`
4. **IMPORTANT:** When selecting region, choose **"US East (Virginia)"** or **"US East"**
5. Configure:
   - **Name:** `llmobserve-api` (or `llmobserve-api-us-east`)
   - **Branch:** `main`
   - **Root Directory:** `collector`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** `Starter` (free tier)

## Step 2: Copy Environment Variables

From your Oregon service, copy these env vars to the new US East service:

```bash
DATABASE_URL=postgresql://postgres:EIPloItGt5NBmrLn@db.vcecetcumnreuzojtqin.supabase.co:5432/postgres
ENV=production
SERVICE_NAME=llmobserve-api
ALLOW_CONTENT_CAPTURE=false
CLERK_SECRET_KEY=sk_test_I7GpNhomWiN13A3IHGEIm6G11zVmKIPMjAQZ2D8h5k
ALLOWED_ORIGINS=*
```

## Step 3: Deploy

Click **"Create Web Service"** - it will deploy to US East.

## Step 4: Update Frontend (Vercel)

Once you get the new US East URL, update Vercel:
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update `NEXT_PUBLIC_COLLECTOR_URL` to the new US East Render URL
3. Redeploy

## Step 5: Delete Old Oregon Service (Optional)

Once everything works:
1. Go to old service: `srv-d4bn7aripnbc73felpd0`
2. Settings → Delete Service

---

**New Service ID will be different** - something like `srv-xxxxx`



