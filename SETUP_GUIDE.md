# Quick Setup Guide

## Super Simple Setup

**Just set your API key and it works!**

```bash
export LLMOBSERVE_API_KEY=your_api_key_here  # Get from dashboard
```

```python
import llmobserve

# That's it! Uses production collector by default
llmobserve.observe()
```

**Done!** Your calls will show up in the dashboard automatically.

## Optional: Custom Collector URL

Only needed if you're running your own collector:

```bash
export LLMOBSERVE_COLLECTOR_URL=http://localhost:8000  # For local dev
```

Or pass it directly:
```python
llmobserve.observe(
    api_key="your_api_key",
    collector_url="http://localhost:8000"  # Only if custom
)
```

## Troubleshooting

### ❌ "collector_url required" error
**Fix:** Set the environment variable:
```bash
export LLMOBSERVE_COLLECTOR_URL=https://llmobserve-api-production-d791.up.railway.app
```

### ❌ "Could not reach collector URL" warning
**Possible causes:**
1. **Wrong URL** - Check the URL is correct
2. **Network issue** - Check your internet connection
3. **Server down** - Check if the collector is running

**Test manually:**
```bash
curl https://llmobserve-api-production-d791.up.railway.app/health
```

### ❌ Events not showing in dashboard
**Check:**
1. ✅ Collector URL is set correctly
2. ✅ API key is set (if required)
3. ✅ Check console/logs for error messages
4. ✅ Wait a few seconds for events to flush

**Enable debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Common Issues

### Using wrong env var name
- ✅ Use: `LLMOBSERVE_COLLECTOR_URL` or `NEXT_PUBLIC_COLLECTOR_URL`
- ❌ Don't use: `COLLECTOR_URL` (too generic)

### Missing trailing slash
- ✅ The SDK handles this automatically
- ✅ URLs like `https://api.example.com` work fine

### Localhost vs Production
- **Local dev:** `http://localhost:8000`
- **Production:** `https://llmobserve-api-production-d791.up.railway.app`

