# Collector Restart Instructions

## ✅ Fixed: Database URL Updated

The issue was that there are **two** `.env` files:
1. Root `.env` (was using old Supabase URL) ❌
2. `collector/.env` (had correct Railway URL) ✅

**Both have been updated** to use Railway PostgreSQL.

## 🔄 To Restart Collector Properly

### Option 1: Stop and Restart Manually

1. **Find the collector process:**
   ```bash
   ps aux | grep uvicorn
   ```

2. **Stop it:**
   - Find the process ID (PID)
   - Kill it: `kill <PID>`
   - Or press Ctrl+C in the terminal where it's running

3. **Restart with venv activated:**
   ```bash
   cd collector
   source venv/bin/activate
   uvicorn main:app --reload
   ```

### Option 2: Use the Background Process (Already Started)

The collector is already running in the background. However, it may have loaded the old database URL before we fixed the root `.env` file.

**To ensure it picks up the new URL:**
1. The collector should auto-reload when files change (--reload flag)
2. Or restart it manually using Option 1

## ✅ Verify It's Working

After restart, check:

1. **Health endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Database connection:**
   ```bash
   cd collector
   source venv/bin/activate
   python3 -c "from sqlalchemy import create_engine, text; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✅ Connected!'); conn.close()"
   ```

3. **Check dashboard:**
   - Visit: http://localhost:3000/dashboard
   - Should show tracked events

## 📋 Quick Command Reference

```bash
# Activate venv and start collector
cd collector
source venv/bin/activate
uvicorn main:app --reload

# Or if you want to run in background:
cd collector
source venv/bin/activate
nohup uvicorn main:app --reload > collector.log 2>&1 &
```

## 🔍 Troubleshooting

### If collector still uses old database:
1. Make sure you restarted it after updating `.env`
2. Check which `.env` file is being loaded:
   ```bash
   cd collector
   source venv/bin/activate
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"
   ```

### If uvicorn not found:
- Always activate venv first: `source venv/bin/activate`
- Or use full path: `./venv/bin/uvicorn main:app --reload`



