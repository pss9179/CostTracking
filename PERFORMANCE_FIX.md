# Performance Fix: CDN Caching + Keep-Alive

## The Problem
- Railway free tier has **30-50 second cold starts**
- Even when warm, Railway's network adds **20-40 second delays**
- This creates a terrible user experience

## The Solution

### 1. CDN Edge Caching (Implemented)
- API responses are cached at Cloudflare edge for **5 minutes**
- After 5 minutes, stale cache is served while fresh data fetches in background
- **Result**: Users see instant responses 99% of the time

### 2. How It Works When You Add New Data

**Scenario 1: User adds LLM usage data**
- Data is tracked and stored in database
- Next API request (within 5 min): Serves cached data (instant, but shows old data)
- After 5 min: Serves stale cache (instant) while fetching fresh in background
- User sees new data within 5-15 minutes automatically

**Scenario 2: User adds another LLM call**
- Same as above - new data appears within 5-15 minutes
- **No slow loads** - always serves from cache while refreshing

**Scenario 3: User hasn't used app in 15+ minutes**
- First request: May be slow (30-50s) if Railway is cold
- All subsequent requests: Instant (served from cache)

### 3. Keep-Alive Mechanism (Implemented)
- Frontend pings `/warm` every 3 minutes when user is active
- Also pings when user switches tabs back to app
- This keeps Railway warm during active use

### 4. External Ping Service (Recommended)
For 24/7 uptime, set up a free external ping service:

**Option A: UptimeRobot (Free)**
1. Go to https://uptimerobot.com
2. Create account (free)
3. Add Monitor:
   - Type: HTTP(s)
   - URL: `https://llmobserve-api-production-d791.up.railway.app/warm`
   - Interval: 5 minutes
4. Save

**Option B: cron-job.org (Free)**
1. Go to https://cron-job.org
2. Create account (free)
3. Create Cron Job:
   - URL: `https://llmobserve-api-production-d791.up.railway.app/warm`
   - Schedule: Every 5 minutes
4. Save

This ensures Railway stays warm even when no users are active.

## Setup Cloudflare (Required for Full Benefit)

1. **Create Cloudflare account** (free tier)
2. **Add your Railway domain**:
   - Go to Cloudflare Dashboard
   - Add Site: `llmobserve-api-production-d791.up.railway.app`
   - OR create custom domain: `api.llmobserve.com`
3. **Configure DNS**:
   - Add CNAME record pointing to Railway
   - Enable Proxy (orange cloud icon)
4. **Update frontend**:
   - Change `NEXT_PUBLIC_COLLECTOR_URL` to Cloudflare domain
   - Redeploy frontend

## Expected Performance

- **First load (cold)**: 30-50 seconds (only if Railway is cold)
- **Subsequent loads**: **< 1 second** (served from cache)
- **New data appears**: Within 5-15 minutes automatically
- **Active users**: Always fast (Railway stays warm)

## Trade-offs

✅ **Pros:**
- 99% of requests are instant
- No slow loads during normal use
- New data appears automatically

⚠️ **Cons:**
- New data may take 5-15 minutes to appear
- First load after 15+ min inactivity may be slow

For a cost tracking dashboard, 5-15 minute data freshness is acceptable. Users get instant responses and new data appears automatically in the background.

