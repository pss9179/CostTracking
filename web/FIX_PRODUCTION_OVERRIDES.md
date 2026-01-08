# 🔧 Fix Production Overrides Mismatch

## What I See

**Production Overrides** (current deployment):
- Build Command: `npm run build` ✅
- Output Directory: `.next` ✅

**Issue**: These differ from your **Project Settings**, causing the warning.

## Solution: Sync Project Settings with Production Overrides

Since your Production Overrides are correct (they match `vercel.json`), you should copy them to Project Settings:

### Step 1: Update Project Settings

In Vercel Dashboard → **Settings** → **General** → **Framework Settings**:

1. **Build Command**:
   - Toggle **"Override"** to **ON**
   - Set to: `npm run build`
   - (This matches your Production Overrides)

2. **Output Directory**:
   - Toggle **"Override"** to **ON** (if not already)
   - Set to: `.next`
   - (This matches your Production Overrides)

### Step 2: Remove Production Overrides

After updating Project Settings:

1. Expand the **"Production Overrides"** section
2. Click to **remove/clear** the overrides
3. This will make production use Project Settings (which now match)

### Step 3: Verify Root Directory

Also check:
- **Settings** → **General** → **Root Directory**
- Should be: `web` (since your Next.js app is in `/web` folder)

### Step 4: Save and Redeploy

1. Click **"Save"** in Vercel dashboard
2. Go to **Deployments** tab
3. Click **"Redeploy"** on the latest deployment
4. The warning should disappear

---

## Why This Happens

Production Overrides are set per-deployment and can differ from Project Settings. This usually happens when:
- Settings were changed after a deployment
- Manual overrides were set for a specific deployment
- Project Settings weren't updated to match

---

## Expected Result

After syncing:
- ✅ Warning banner disappears
- ✅ All future deployments use Project Settings
- ✅ Production Overrides section is empty/removed
- ✅ Consistent builds across all deployments

---

## Quick Checklist

- [ ] Set Build Command override in Project Settings: `npm run build`
- [ ] Set Output Directory override in Project Settings: `.next`
- [ ] Verify Root Directory is `web`
- [ ] Remove Production Overrides
- [ ] Save settings
- [ ] Redeploy


