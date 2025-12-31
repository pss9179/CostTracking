# Cloudflare Setup Guide - Fix Slow Loading

This guide will set up Cloudflare CDN to make your API responses instant (< 1 second) instead of 30-50 seconds.

## Prerequisites

- Cloudflare account (free tier works)
- Access to your domain's DNS settings (if using custom domain)
- OR Railway domain: `llmobserve-api-production-d791.up.railway.app`

## Option 1: Using Railway Domain (Easiest)

### Step 1: Create Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up for free account
3. Verify your email

### Step 2: Add Railway Domain to Cloudflare

1. In Cloudflare Dashboard, click **"Add a Site"**
2. Enter: `llmobserve-api-production-d791.up.railway.app`
3. Select **Free** plan
4. Click **"Continue"**

### Step 3: Configure DNS

Cloudflare will scan your domain. Since this is a Railway subdomain:

1. Click **"Continue"** (skip DNS scan)
2. You'll see DNS records - **don't add any yet**
3. Click **"Continue"** to finish setup

### Step 4: Get Cloudflare Proxy Domain

1. Go to **DNS** → **Records**
2. Click **"Add record"**
3. Configure:
   - **Type**: CNAME
   - **Name**: `api-cdn` (or any subdomain you want)
   - **Target**: `llmobserve-api-production-d791.up.railway.app`
   - **Proxy status**: ✅ **Proxied** (orange cloud) - **IMPORTANT!**
4. Click **"Save"**

You'll get a domain like: `api-cdn.llmobserve-api-production-d791.up.railway.app`

**Note**: This might not work perfectly with Railway's subdomain. Better option below.

---

## Option 2: Using Custom Domain (Recommended)

If you have a custom domain (e.g., `llmobserve.com`):

### Step 1: Add Domain to Cloudflare

1. Go to Cloudflare Dashboard
2. Click **"Add a Site"**
3. Enter your domain: `llmobserve.com`
4. Select **Free** plan
5. Click **"Continue"**

### Step 2: Update Nameservers

1. Cloudflare will show you 2 nameservers (e.g., `alice.ns.cloudflare.com`)
2. Go to your domain registrar (where you bought the domain)
3. Update nameservers to Cloudflare's nameservers
4. Wait 5-60 minutes for DNS propagation

### Step 3: Add API Subdomain

1. In Cloudflare Dashboard → **DNS** → **Records**
2. Click **"Add record"**
3. Configure:
   - **Type**: CNAME
   - **Name**: `api` (or `api-cdn`)
   - **Target**: `llmobserve-api-production-d791.up.railway.app`
   - **Proxy status**: ✅ **Proxied** (orange cloud) - **CRITICAL!**
4. Click **"Save"**

Your API will be available at: `https://api.llmobserve.com` (or `https://api-cdn.llmobserve.com`)

---

## Step 4: Update Frontend Environment Variable

### If Using Vercel:

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Find `NEXT_PUBLIC_COLLECTOR_URL`
5. Update to your Cloudflare domain:
   - Option 1: `https://api-cdn.llmobserve-api-production-d791.up.railway.app`
   - Option 2: `https://api.llmobserve.com` (if using custom domain)
6. Click **"Save"**
7. **Redeploy** your frontend (Vercel will auto-deploy or trigger manually)

### If Using Local Development:

Update `.env.local`:
```bash
NEXT_PUBLIC_COLLECTOR_URL=https://api.llmobserve.com
```

---

## Step 5: Verify It Works

### Test 1: Check Cloudflare is Proxying

```bash
curl -I https://api.llmobserve.com/health
```

Look for headers:
- `cf-ray` - Confirms Cloudflare is proxying
- `server: cloudflare` - Confirms it's working

### Test 2: Test Caching

```bash
# First request (cache miss - may be slow)
time curl https://api.llmobserve.com/stats/dashboard-all?hours=168&days=7 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Second request (cache hit - should be instant < 1s)
time curl https://api.llmobserve.com/stats/dashboard-all?hours=168&days=7 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Second request should be **< 1 second**!

### Test 3: Check Browser

1. Open your app: `https://app.llmobserve.com`
2. Open browser DevTools → Network tab
3. Reload dashboard
4. Check API request timing - should be **< 1 second** after first load

---

## Step 6: Configure Cloudflare Settings (Optional but Recommended)

### Enable Caching

1. Go to **Caching** → **Configuration**
2. Set **Caching Level**: Standard
3. Set **Browser Cache TTL**: Respect Existing Headers (we set this in code)

### Enable Auto Minify (Performance)

1. Go to **Speed** → **Optimization**
2. Enable **Auto Minify** for JavaScript, CSS, HTML

### Enable Compression

1. Go to **Speed** → **Optimization**
2. Enable **Brotli** compression

---

## Troubleshooting

### "502 Bad Gateway" Error

**Problem**: Cloudflare can't reach Railway

**Solution**:
1. Check Railway is running: `curl https://llmobserve-api-production-d791.up.railway.app/health`
2. Verify CNAME target is correct
3. Wait 5-10 minutes for DNS propagation

### Still Slow After Setup

**Problem**: Cache not working

**Solution**:
1. Check `Cache-Control` headers in response:
   ```bash
   curl -I https://api.llmobserve.com/stats/dashboard-all?hours=168&days=7 \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
2. Should see: `cache-control: public, s-maxage=300, ...`
3. If not, check backend code deployed correctly

### CORS Errors

**Problem**: API requests blocked

**Solution**:
1. Check Railway CORS settings allow Cloudflare domain
2. Update `ALLOWED_ORIGINS` in Railway to include Cloudflare domain

---

## Expected Results

✅ **Before Cloudflare**: 30-50 second loads
✅ **After Cloudflare**: < 1 second loads (after first request)

✅ **First request**: May be slow (cache miss)
✅ **All subsequent requests**: Instant (< 1 second)

✅ **New data appears**: Within 5-15 minutes automatically

---

## Next Steps

1. ✅ Set up external ping service (UptimeRobot) to keep Railway warm
2. ✅ Monitor Cloudflare analytics to see cache hit rate
3. ✅ Adjust cache TTL if needed (currently 5 minutes)

---

## Support

If you get stuck:
1. Check Cloudflare dashboard for errors
2. Check Railway logs: `railway logs`
3. Test API directly: `curl https://api.llmobserve.com/health`

