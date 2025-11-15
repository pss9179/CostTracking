# Connect Vercel to GitHub for Automatic Deployments

## Why Connect to GitHub?

✅ **Automatic deployments** - Push to GitHub → Auto-deploy to Vercel  
✅ **Preview deployments** - Every PR gets its own preview URL  
✅ **Version control** - Easy rollbacks and deployment history  
✅ **Team collaboration** - Share preview links with your team  

## Step-by-Step Guide

### Step 1: Push Your Code to GitHub (If Not Already Done)

First, make sure your latest changes are committed and pushed:

```bash
# From your project root
cd /Users/gsuriya/Downloads/CostTracking

# Check status
git status

# Add and commit changes
git add .
git commit -m "Fixed TypeScript errors and prepared for production"

# Push to GitHub
git push origin main
```

### Step 2: Connect Vercel Project to GitHub

#### Option A: Through Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Navigate to your project (likely named "web")

2. **Go to Project Settings**
   - Click on your project
   - Go to **"Settings"** tab
   - Click **"Git"** in the left sidebar

3. **Connect Repository**
   - Click **"Connect Git Repository"**
   - Select **GitHub**
   - Authorize Vercel to access your GitHub (if not already done)
   - Search for your repository: `CostTracking` (or whatever your repo is named)
   - Click **"Connect"**

4. **Configure Build Settings**
   - **Root Directory:** `web`
   - **Framework Preset:** Next.js
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next`
   - Click **"Save"**

5. **Done!** 🎉
   - Vercel will now automatically deploy when you push to `main`
   - Pull requests will get preview deployments

#### Option B: Delete and Re-Import (Alternative)

If Option A doesn't work, you can re-import the project:

1. **Delete Current Project** (don't worry, just the Vercel project)
   - Go to: https://vercel.com/dashboard
   - Click on your "web" project
   - Settings → General → Delete Project
   - Type the project name to confirm

2. **Import from GitHub**
   - Click **"Add New"** → **"Project"**
   - Click **"Import Git Repository"**
   - Select GitHub and authorize if needed
   - Find your `CostTracking` repository
   - Click **"Import"**

3. **Configure Settings**
   - **Root Directory:** `web` ⚠️ IMPORTANT!
   - **Framework:** Next.js (auto-detected)
   - Add environment variables (same as before):
     ```
     NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_YOUR_KEY
     CLERK_SECRET_KEY=sk_live_YOUR_SECRET
     NEXT_PUBLIC_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
     NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
     NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
     ```
   - Click **"Deploy"**

### Step 3: Configure Branch Deployments

After connecting, configure which branches trigger deployments:

1. Go to **Project Settings** → **Git**
2. **Production Branch:** Set to `main` (or `master`)
3. **Enable Preview Deployments:**
   - ✅ Enable automatic deployments for all branches
   - ✅ Enable preview deployments for pull requests

### Step 4: Test the Setup

```bash
# Make a small change
cd /Users/gsuriya/Downloads/CostTracking
echo "# LLM Observe - Connected to Vercel" >> web/README.md

# Commit and push
git add web/README.md
git commit -m "Test Vercel auto-deploy"
git push origin main
```

Watch your Vercel dashboard - you should see a new deployment start automatically! 🚀

## What Happens Now?

### On Every Push to `main`:
1. ✅ Vercel detects the push
2. ✅ Automatically builds your Next.js app
3. ✅ Runs type checks and tests
4. ✅ Deploys to production URL
5. ✅ You get a notification (email/Slack if configured)

### On Every Pull Request:
1. ✅ Vercel creates a preview deployment
2. ✅ Gets a unique URL like `your-app-git-branch-name.vercel.app`
3. ✅ Comments on the PR with the preview link
4. ✅ Team can review changes before merging

## Vercel CLI Still Useful For:

Even with GitHub connected, the CLI is still useful for:

- **Quick deployments:** `vercel` (deploys current working directory)
- **Environment variables:** `vercel env add`
- **Logs:** `vercel logs`
- **Domain management:** `vercel domains add`

## Workflow Example

```bash
# 1. Create a new feature
git checkout -b feature/new-dashboard

# 2. Make changes
# ... edit files ...

# 3. Commit and push
git add .
git commit -m "Add new dashboard feature"
git push origin feature/new-dashboard

# 4. Vercel automatically creates preview deployment
# Check Vercel dashboard for preview URL

# 5. Create PR on GitHub
# Vercel comments on PR with preview link

# 6. Review, test, and merge
git checkout main
git merge feature/new-dashboard
git push origin main

# 7. Vercel automatically deploys to production!
```

## Rollback if Needed

If a deployment breaks something:

1. Go to Vercel dashboard
2. Click **"Deployments"**
3. Find the last working deployment
4. Click **"⋮"** → **"Promote to Production"**

Or use Git:

```bash
# Revert the commit
git revert HEAD
git push origin main

# Vercel will automatically deploy the reverted version
```

## Configure Deployment Notifications

Get notified about deployments:

1. Go to **Project Settings** → **Integrations**
2. Add:
   - **Slack** - Get deployment notifications
   - **GitHub Checks** - Show deployment status on PRs
   - **Email** - Deployment success/failure emails

## Troubleshooting

### Build fails on Vercel but works locally?

**Check:**
- Environment variables are set in Vercel dashboard
- Node version matches (check `package.json` engines field)
- Root directory is set to `web`

### Vercel not detecting pushes?

**Solutions:**
1. Check GitHub webhook:
   - Go to GitHub repo → Settings → Webhooks
   - Should see a webhook for `hooks.vercel.com`
   - Click it and check recent deliveries
2. Re-connect the repository in Vercel settings

### Preview deployments not working?

**Check:**
- Project Settings → Git → Preview Deployments is enabled
- GitHub app has permission to read PRs
- Branch is not ignored in deployment settings

## Best Practices

✅ **Always test locally first:** `npm run build` before pushing  
✅ **Use preview deployments:** Test features before merging to main  
✅ **Enable preview comments:** Let Vercel comment on PRs with deployment links  
✅ **Set up status checks:** Require successful Vercel deployment before merging  
✅ **Monitor deployments:** Check Vercel dashboard after pushing  

## Next Steps After Setup

1. ✅ Add deployment status badge to README
2. ✅ Configure custom domain
3. ✅ Set up analytics (Vercel Analytics)
4. ✅ Enable Web Vitals monitoring
5. ✅ Add GitHub branch protection rules

---

**Once connected, your workflow becomes:**

```
Code → Git Push → Automatic Deploy → Live! 🚀
```

No more manual deployments! 🎉

