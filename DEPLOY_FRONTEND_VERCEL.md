# Deploy Frontend to Vercel

Now that your backend is deployed on Railway, let's deploy the frontend to Vercel.

## Prerequisites

✅ Backend deployed on Railway
✅ You have your Railway backend URL (e.g., `https://your-app.up.railway.app`)

## Step 1: Install Vercel CLI (Optional)

You can deploy via CLI or through the Vercel dashboard. For CLI:

```bash
npm install -g vercel
```

## Step 2: Deploy via Vercel Dashboard (Recommended)

### A. Sign Up/Login to Vercel

1. Go to [https://vercel.com](https://vercel.com)
2. Sign up or log in (use GitHub for easy integration)

### B. Import Your Project

1. Click **"Add New"** → **"Project"**
2. Import your GitHub repository (or upload the `web/` directory)
3. Vercel will auto-detect it's a Next.js project

### C. Configure Project Settings

**Root Directory:** `web`

**Framework Preset:** Next.js (auto-detected)

**Build Command:** `npm run build` (auto-detected)

**Output Directory:** `.next` (auto-detected)

### D. Configure Environment Variables

Click **"Environment Variables"** and add these:

```bash
# Clerk Authentication (REQUIRED)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_YOUR_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY=sk_live_YOUR_CLERK_SECRET_KEY

# Backend URL (REPLACE WITH YOUR RAILWAY URL)
NEXT_PUBLIC_COLLECTOR_URL=https://YOUR-RAILWAY-APP.up.railway.app

# Supabase (if needed for direct DB access)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Google OAuth (if using AI-CRM features)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Optional: Other services
VAPI_PUBLIC_KEY=your_vapi_public_key
```

**⚠️ IMPORTANT:** Replace `YOUR-RAILWAY-APP` with your actual Railway domain!

### E. Deploy

1. Click **"Deploy"**
2. Wait for build to complete (2-3 minutes)
3. You'll get a URL like: `https://your-app.vercel.app`

## Step 3: Alternative - Deploy via CLI

If you prefer the CLI:

```bash
cd web
vercel
```

Follow the prompts:
- Set up and deploy: **Y**
- Which scope: (your account)
- Link to existing project: **N**
- Project name: `llmobserve-frontend` (or your choice)
- Directory: `./` (already in web/)
- Override settings: **N**

Then add environment variables:

```bash
vercel env add NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
vercel env add CLERK_SECRET_KEY
vercel env add NEXT_PUBLIC_COLLECTOR_URL
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
```

Deploy to production:

```bash
vercel --prod
```

## Step 4: Update Clerk Configuration

Your frontend URL has changed, so update Clerk:

1. Go to [Clerk Dashboard](https://dashboard.clerk.com)
2. Select your application
3. Go to **"Paths"** or **"Application URLs"**
4. Update:
   - **Application URL:** `https://your-app.vercel.app`
   - **Allowed Origins:** Add `https://your-app.vercel.app`
   - **Allowed Redirect URLs:** Add `https://your-app.vercel.app/*`

## Step 5: Update CORS on Railway Backend

Your backend needs to accept requests from your Vercel frontend:

1. Go to Railway dashboard
2. Select your backend service
3. Add environment variable:
   ```
   ALLOWED_ORIGINS=https://your-app.vercel.app,https://llmobserve.com
   ```
4. Redeploy if necessary

## Step 6: Test Your Deployment

1. **Visit your frontend:** `https://your-app.vercel.app`
2. **Sign in** with Clerk
3. **Check connectivity:** The dashboard should load data from Railway backend
4. **Test API calls:** Try creating a project or viewing analytics

### Quick Test Commands

```bash
# Test frontend
curl https://your-app.vercel.app

# Test backend from frontend
curl https://YOUR-RAILWAY-APP.up.railway.app/health

# Test backend API
curl https://YOUR-RAILWAY-APP.up.railway.app/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### "Failed to fetch" errors

**Problem:** Frontend can't reach backend

**Solutions:**
1. Check `NEXT_PUBLIC_COLLECTOR_URL` is set correctly
2. Verify Railway backend is running: `curl https://your-railway.up.railway.app/health`
3. Check CORS settings on backend
4. Check browser console for exact error

### Build failures

**Problem:** Vercel build fails

**Solutions:**
1. Check all dependencies are in `package.json`
2. Verify Node version (16+ required)
3. Check build logs in Vercel dashboard
4. Try local build: `cd web && npm run build`

### Clerk authentication errors

**Problem:** Can't sign in

**Solutions:**
1. Verify Clerk environment variables are set
2. Check Clerk dashboard allowed URLs
3. Ensure domain matches exactly (no trailing slashes)

### API requests fail

**Problem:** 401 or 403 errors

**Solutions:**
1. Check backend logs on Railway
2. Verify Clerk webhook is configured
3. Test backend independently: `curl https://your-railway.up.railway.app/health`

## Production Checklist

- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway
- [ ] `NEXT_PUBLIC_COLLECTOR_URL` points to Railway
- [ ] Clerk URLs updated
- [ ] CORS configured on backend
- [ ] Test login flow
- [ ] Test API connectivity
- [ ] Check browser console for errors
- [ ] Monitor Vercel logs
- [ ] Monitor Railway logs

## Custom Domain (Optional)

### Add Custom Domain to Vercel

1. Go to Vercel project settings
2. Click **"Domains"**
3. Add your domain (e.g., `llmobserve.com`)
4. Follow DNS configuration instructions
5. Update Clerk allowed origins with your custom domain

### Add Custom Domain to Railway

1. Go to Railway project settings
2. Click **"Domains"**
3. Add custom domain (e.g., `api.llmobserve.com`)
4. Update DNS records as instructed
5. Update `NEXT_PUBLIC_COLLECTOR_URL` on Vercel

## Next Steps

Once deployed:

1. **Monitor logs:** Check both Vercel and Railway dashboards
2. **Test thoroughly:** Try all features (login, projects, analytics)
3. **Set up monitoring:** Consider adding Sentry or LogRocket
4. **Documentation:** Update README with your production URLs
5. **Share:** Your app is live! 🚀

## Support

- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app
- **Clerk Docs:** https://clerk.com/docs

---

**🎉 Once deployed, your architecture will be:**

```
Users → Vercel (Frontend) → Railway (Backend) → Supabase (Database)
                                ↓
                            Clerk (Auth)
```

Perfect for a production SaaS! 🚀

