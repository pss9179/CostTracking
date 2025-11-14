# 🚀 Deploy from GitHub - Auto-Deploy Setup

This guide sets up **automatic deployments** from your GitHub repo. Every time you push to `main`, both Render and Vercel will automatically deploy!

## Your GitHub Repo
**Repo:** `https://github.com/pss9179/CostTracking`

---

## Part 1: Render (Backend) - Connect to GitHub

### Step 1: Create Service from GitHub

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Web Service"**
3. Click **"Connect GitHub"** (if not already connected)
4. Authorize Render to access your repos
5. Select repo: **`pss9179/CostTracking`**

### Step 2: Configure Service Settings

**Basic Settings:**
- **Name:** `llmobserve-api`
- **Region:** Choose closest to you
- **Branch:** `main` (or `Suriya` if you want that branch)
- **Root Directory:** `collector`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Auto-Deploy:** ✅ **Enabled** (deploys on every push to `main`)

### Step 3: Set Environment Variables

In Render dashboard → Your Service → Environment:

```bash
DATABASE_URL=postgresql://postgres:EIPloItGt5NBmrLn@db.vcecetcumnreuzojtqin.supabase.co:5432/postgres
ENV=production
SERVICE_NAME=llmobserve-api
ALLOW_CONTENT_CAPTURE=false
CLERK_SECRET_KEY=sk_test_I7GpNhomWiN13A3IHGEIm6G11zVmKIPMjAQZ2D8h5k
ALLOWED_ORIGINS=*
```

**Email (optional - set if you have it):**
```bash
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-key-here
```

### Step 4: Deploy!

Click **"Create Web Service"** - Render will:
1. Clone your repo
2. Install dependencies
3. Start your service
4. Give you a URL like: `https://llmobserve-api.onrender.com`

**✅ Done!** Now every push to `main` will auto-deploy.

---

## Part 2: Vercel (Frontend) - Connect to GitHub

### Step 1: Import Project from GitHub

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Find **`pss9179/CostTracking`** and click **"Import"**

### Step 2: Configure Project Settings

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** `web`

**Build Settings:**
- **Build Command:** `npm run build` (default)
- **Output Directory:** `.next` (default)
- **Install Command:** `npm install` (default)

**Environment Variables:**
Click **"Environment Variables"** and add:

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_bWVldC1zd2luZS0yNC5jbGVyay5hY2NvdW50cy5kZXYk
CLERK_SECRET_KEY=sk_test_I7GpNhomWiN13A3IHGEIm6G11zVmKIPMjAQZ2D8h5k
NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-api.onrender.com
```
*(Update the collector URL after you get your Render URL)*

**Production Branch:** `main` (or `Suriya`)

### Step 3: Deploy!

Click **"Deploy"** - Vercel will:
1. Clone your repo
2. Install dependencies
3. Build your Next.js app
4. Deploy to production
5. Give you a URL like: `https://cost-tracking-xyz.vercel.app`

**✅ Done!** Now every push to `main` will auto-deploy.

---

## Part 3: Update URLs After First Deploy

### 1. Get Your Render URL

After Render deploys, copy your service URL (e.g., `https://llmobserve-api.onrender.com`)

### 2. Update Vercel Environment Variable

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update `NEXT_PUBLIC_COLLECTOR_URL` to your Render URL
3. Redeploy (or wait for next push)

### 3. Update Render ALLOWED_ORIGINS

1. Go to Render Dashboard → Your Service → Environment
2. Update `ALLOWED_ORIGINS` to your Vercel URL:
   ```bash
   ALLOWED_ORIGINS=https://your-app.vercel.app
   ```
3. Service will auto-restart

---

## How Auto-Deploy Works

### Render
- ✅ **Auto-deploys** on every push to `main` branch
- ✅ **Auto-restarts** when you change environment variables
- ✅ View logs in Render dashboard

### Vercel
- ✅ **Auto-deploys** on every push to `main` branch
- ✅ **Preview deployments** for pull requests
- ✅ **Production deployments** for `main` branch
- ✅ View logs in Vercel dashboard

---

## Testing Auto-Deploy

1. Make a small change (add a comment somewhere)
2. Commit and push:
   ```bash
   git add .
   git commit -m "test auto-deploy"
   git push origin main
   ```
3. Watch the magic happen:
   - Render dashboard will show "Building..." then "Live"
   - Vercel dashboard will show "Building..." then "Ready"

---

## Useful Commands

### Check Deployment Status

**Render:**
- Dashboard: https://dashboard.render.com
- View logs: Dashboard → Your Service → Logs

**Vercel:**
- Dashboard: https://vercel.com/dashboard
- View logs: Dashboard → Your Project → Deployments → Click deployment → Logs

### Manual Deploy Trigger

**Render:**
- Dashboard → Your Service → Manual Deploy → Deploy latest commit

**Vercel:**
- Dashboard → Your Project → Deployments → Click "..." → Redeploy

---

## Troubleshooting

### Render Build Fails

1. Check logs in Render dashboard
2. Verify `collector/requirements.txt` exists
3. Check Python version compatibility

### Vercel Build Fails

1. Check logs in Vercel dashboard
2. Verify `web/package.json` exists
3. Check for TypeScript errors (fix locally first)

### Environment Variables Not Working

1. **Render:** Make sure they're set in dashboard (not just in code)
2. **Vercel:** Make sure they're set for "Production" environment
3. Redeploy after adding env vars

---

## Next Steps

1. ✅ Connect Render to GitHub → Auto-deploy backend
2. ✅ Connect Vercel to GitHub → Auto-deploy frontend
3. ✅ Set environment variables
4. ✅ Test by pushing a change
5. 🎉 Enjoy automatic deployments!

**Now every time you push to GitHub, your app automatically updates!** 🚀

