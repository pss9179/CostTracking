# 🚀 Deploy Frontend to Vercel - Quick Start

## What You Need

Before starting, have ready:
- [ ] Your Railway backend URL (e.g., `https://xxxxx.up.railway.app`)
- [ ] GitHub account (for easy deployment)
- [ ] Vercel account (free - sign up at vercel.com)

## 5-Minute Deployment

### Step 1: Go to Vercel
1. Visit [https://vercel.com](https://vercel.com)
2. Click **"Sign Up"** or **"Log In"** (use GitHub)

### Step 2: Import Project
1. Click **"Add New"** → **"Project"**
2. Import your GitHub repository
3. **IMPORTANT:** Set **Root Directory** to `web`

### Step 3: Configure Environment Variables
Click "Environment Variables" and add these **one by one**:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
pk_live_YOUR_CLERK_PUBLISHABLE_KEY

CLERK_SECRET_KEY
sk_live_YOUR_CLERK_SECRET_KEY

NEXT_PUBLIC_COLLECTOR_URL
https://YOUR-RAILWAY-APP.up.railway.app

NEXT_PUBLIC_SUPABASE_URL
https://your-project.supabase.co

NEXT_PUBLIC_SUPABASE_ANON_KEY
your_supabase_anon_key
```

**⚠️ CRITICAL:** Replace `YOUR-RAILWAY-APP` with your actual Railway URL!

### Step 4: Deploy
1. Click **"Deploy"**
2. Wait 2-3 minutes for build
3. You'll get: `https://your-app.vercel.app`

### Step 5: Update Clerk
1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Select your app → **"Paths"**
3. Update **Application URL** to: `https://your-app.vercel.app`
4. Add to **Allowed Origins**: `https://your-app.vercel.app`

### Step 6: Test
Visit your Vercel URL and try to:
- [ ] Load the page
- [ ] Sign in with Clerk
- [ ] View the dashboard

## That's It! 🎉

Your app is now live:
- **Frontend:** `https://your-app.vercel.app` (Vercel)
- **Backend:** `https://xxxxx.up.railway.app` (Railway)
- **Database:** Supabase
- **Auth:** Clerk

## Troubleshooting

**Can't connect to backend?**
```bash
# Check if backend is running
curl https://YOUR-RAILWAY-APP.up.railway.app/health
```
- If this fails, check Railway dashboard

**Build failed?**
- Check Vercel build logs
- Verify all env variables are set
- Try: `cd web && npm run build` locally

**Clerk errors?**
- Double-check Clerk env variables
- Ensure Vercel URL is added to Clerk allowed origins

## Need More Help?

See detailed guide: `DEPLOY_FRONTEND_VERCEL.md`

## Next Steps

Once everything works:
1. Monitor logs in Vercel dashboard
2. Consider adding a custom domain
3. Set up error monitoring (Sentry)
4. Share your app! 🚀

