# 🚀 Deploy Everything on Vercel

Yes! You can deploy **both frontend AND backend** on Vercel. Here's how:

---

## ⚠️ Important Limitations

**Vercel Serverless Functions:**
- ✅ Great for API endpoints
- ✅ Auto-scales
- ✅ Fast global CDN
- ❌ No background tasks (your `cap_monitor` won't work)
- ❌ 10-second timeout on free tier (60s on Pro)
- ❌ Cold starts (first request after inactivity is slower)
- ❌ Database connections need to be serverless-friendly

**Your FastAPI app has:**
- Background task (`cap_monitor`) - won't work on Vercel
- Database connections - need to be optimized for serverless

---

## Option 1: Adapt FastAPI for Vercel (Recommended)

### Step 1: Create Vercel API Handler

Create `api/index.py` in your project root:

```python
# api/index.py
from mangum import Mangum
import sys
import os

# Add collector to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'collector'))

from collector.main import app

# Wrap FastAPI app for Vercel
handler = Mangum(app, lifespan="off")  # Disable lifespan events (background tasks)

def lambda_handler(event, context):
    return handler(event, context)
```

### Step 2: Install Mangum

Add to `collector/requirements.txt`:
```
mangum>=0.17.0
```

### Step 3: Update Vercel Config

Update `vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"],
  "functions": {
    "api/index.py": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index"
    }
  ]
}
```

### Step 4: Remove Background Tasks

Comment out background tasks in `collector/main.py`:

```python
# @app.on_event("startup")
# async def on_startup():
#     """Initialize database tables and start background services."""
#     init_db()
#     run_migrations()
#     
#     # Start cap monitor in background
#     global cap_monitor_task
#     cap_monitor_task = asyncio.create_task(run_cap_monitor(check_interval_seconds=300))
#     logger.info("Started cap monitor background service")
```

**Note:** You'll need to handle cap monitoring differently (cron job, separate service, or on-demand)

### Step 5: Deploy

```bash
cd /Users/gsuriya/Downloads/CostTracking
vercel --prod
```

**Backend will be at:** `https://your-app.vercel.app/api/*`
**Frontend will be at:** `https://your-app.vercel.app`

---

## Option 2: Use Vercel's API Routes (Next.js API Routes)

Convert your FastAPI endpoints to Next.js API routes:

### Example: Create `web/app/api/events/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/db'; // Your database helper

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    // Your FastAPI logic here, converted to TypeScript
    const session = await getSession();
    // ... process events
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
```

**Pros:**
- Native Vercel support
- TypeScript
- Better integration with Next.js

**Cons:**
- Need to rewrite all endpoints
- More work upfront

---

## Option 3: Hybrid Approach (Best of Both Worlds)

**Frontend:** ✅ Vercel (perfect for Next.js)
**Backend:** Railway/Render (better for FastAPI with background tasks)

This is what most people do:
- Vercel for frontend (fast, optimized)
- Railway/Render for backend (full Python support, background tasks)

---

## Quick Setup: Deploy Frontend on Vercel (Already Done!)

Your frontend is already set up for Vercel:

```bash
cd web
vercel --prod
```

✅ **Frontend deployed!**

---

## Recommendation

**For your use case:**

1. **Frontend:** ✅ Keep on Vercel (already working)
2. **Backend:** 
   - **Option A:** Fix Render service (change Docker → Python) - Easiest
   - **Option B:** Adapt for Vercel serverless - More work, but everything in one place
   - **Option C:** Use Railway - Similar to Render, but easier Python setup

**My recommendation:** Fix Render (5 minutes) or use Railway (10 minutes). Vercel serverless works but requires refactoring and loses background tasks.

---

## Next Steps

**If you want everything on Vercel:**
1. Install Mangum: `pip install mangum`
2. Create `api/index.py` wrapper
3. Update `vercel.json`
4. Remove background tasks
5. Deploy

**If you want easiest path:**
1. Fix Render service (Docker → Python)
2. Keep frontend on Vercel
3. Done! 🎉

Which do you prefer?


