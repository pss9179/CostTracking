# 🔧 Fix Vercel Deployment Configuration Issues

## Issues Found

1. ⚠️ **Warning**: "Configuration Settings in the current Production deployment differ from your current Project Settings"
2. 🔧 **Build Command Mismatch**: Your `package.json` uses `next build --webpack` but Vercel might be using default `next build`
3. 📁 **Production Overrides**: There are overrides in production that differ from project settings

## Fix Steps

### Step 1: Check Production Overrides

In Vercel Dashboard:
1. Click on the **"Production Overrides"** section (expand it)
2. Note what settings are different
3. Either:
   - **Option A**: Remove the overrides and use Project Settings
   - **Option B**: Update Project Settings to match Production Overrides

### Step 2: Fix Build Command

Your `package.json` has:
```json
"build": "next build --webpack"
```

**In Vercel Dashboard:**
1. Go to **Settings** → **General** → **Framework Settings**
2. Find **"Build Command"**
3. Click **"Override"** toggle to ON
4. Set it to: `npm run build` (this will use your package.json script)
   - OR directly: `next build --webpack`

### Step 3: Verify Root Directory

Since your project is in `/web` folder:
1. Go to **Settings** → **General**
2. Check **"Root Directory"**
3. Should be set to: `web`
4. If not, set it to `web` and save

### Step 4: Check Output Directory

Your `vercel.json` specifies:
```json
"outputDirectory": ".next"
```

**In Vercel Dashboard:**
1. **Framework Settings** → **Output Directory**
2. Should be: `.next` (Next.js default)
3. If override is ON, make sure it's set to `.next`

### Step 5: Remove Production Overrides (Recommended)

To sync everything:
1. Expand **"Production Overrides"** section
2. Remove any overrides that differ from Project Settings
3. This will make all deployments use the same settings

### Step 6: Redeploy

After fixing settings:
1. Go to **Deployments** tab
2. Click **"Redeploy"** on the latest deployment
3. Or push a new commit to trigger auto-deploy

---

## Recommended Configuration

### Project Settings (should match vercel.json):
- **Framework Preset**: Next.js ✅
- **Build Command**: `npm run build` (uses `next build --webpack` from package.json)
- **Output Directory**: `.next` ✅
- **Install Command**: Default (auto-detected) ✅
- **Development Command**: `next dev` ✅

### Root Directory:
- Should be: `web` (if deploying from monorepo root)

---

## Quick Fix Checklist

- [ ] Expand "Production Overrides" and check what's different
- [ ] Set Build Command override to: `npm run build`
- [ ] Verify Root Directory is set to `web`
- [ ] Remove conflicting Production Overrides
- [ ] Redeploy the project

---

## After Fixing

1. The warning banner should disappear
2. New deployments will use consistent settings
3. Sign-in page should work correctly


