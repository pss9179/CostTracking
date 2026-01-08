# Railway Performance Fix - Eliminating Cold Starts

## The Problem

Railway containers go to sleep after ~2-3 minutes of inactivity. When a user visits the site after the container sleeps:
- **Cold start time**: 2-3 minutes (container wake-up)
- **Database cold**: 30-60 seconds (connection establishment)
- **Warm response time**: 0.1-0.3 seconds

This creates a terrible user experience where the dashboard takes 2+ minutes to load.

## IMMEDIATE FIX NEEDED

### Step 1: Enable Railway "Always On" (RECOMMENDED - $5/month)

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click on your `llmobserve-api` service
3. Go to **Settings** tab
4. Under **Networking** or **Deploy**, find **Sleep Settings**
5. **Disable** container sleeping / Enable "Always On"

**Cost**: ~$5-10/month extra on Railway
**Effect**: Container never sleeps = instant responses

### Step 2: Set Up UptimeRobot (FREE - Do This Now!)

Even with Always On, you should monitor uptime:

1. Go to [UptimeRobot](https://uptimerobot.com/) - it's free
2. Create an account
3. Click **Add New Monitor**
4. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: LLMObserve API
   - **URL**: `https://llmobserve-api-production-d791.up.railway.app/warm`
   - **Monitoring Interval**: **1 minute** (use the minimum!)
5. Save

This ensures the container and database stay warm.

## Why `/warm` Instead of `/health`?

- `/health` - Only checks if container is running (doesn't touch database)
- `/warm` - Pings the database to keep connection pool active

Always use `/warm` for keep-alive pings!

## Verification Commands

Test if the fix is working:

```bash
# Should respond in < 2 seconds when warm
time curl -s "https://llmobserve-api-production-d791.up.railway.app/warm"

# Run 3 times - all should be fast
for i in 1 2 3; do
  echo "Request $i:"
  time curl -s "https://llmobserve-api-production-d791.up.railway.app/health"
done
```

**Expected results after fix:**
- All requests: < 2 seconds
- Database time: < 1000ms

**If still slow:**
- Check Railway dashboard for container restarts
- Verify UptimeRobot is pinging successfully
- Check database region matches service region

## Code Changes Made

1. **Added DB keepalive** - Background task pings database every 60 seconds
2. **Added startup warm-up** - Database warmed on container start
3. **GitHub Action** - Pings `/warm` every 2 minutes (backup to UptimeRobot)

