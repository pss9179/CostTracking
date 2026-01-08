# ✅ Vercel Settings Checklist

## Issues Found in Your Dashboard

1. ⚠️ **Warning Banner**: Production Overrides differ from Project Settings
2. 🔧 **Build Command**: May not match `package.json` script
3. 📁 **Root Directory**: Need to verify it's set to `web`

## Fix Steps

### 1. Expand "Production Overrides" Section
- Click to expand and see what's different
- Note the settings shown there

### 2. Update Build Command
**Current in package.json**: `next build --webpack`

**In Vercel Dashboard:**
- Framework Settings → Build Command
- Toggle "Override" to **ON**
- Set to: `npm run build`
- This will use your package.json script which includes `--webpack`

### 3. Verify Root Directory
**Settings → General → Root Directory**
- Should be: `web`
- If blank or wrong, set it to `web`

### 4. Remove Production Overrides (Recommended)
- Expand "Production Overrides"
- Remove any overrides that conflict
- This will sync production with Project Settings

### 5. Verify Settings Match vercel.json
Your `vercel.json` has:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

**Project Settings should match:**
- Build Command: `npm run build` ✅
- Output Directory: `.next` ✅
- Framework: Next.js ✅

### 6. Redeploy
After fixing:
- Go to Deployments tab
- Click "Redeploy" on latest deployment
- Or push a new commit

---

## Expected Result

After fixing:
- ✅ Warning banner disappears
- ✅ All deployments use consistent settings
- ✅ Sign-in page works correctly
- ✅ Build uses `--webpack` flag as intended


