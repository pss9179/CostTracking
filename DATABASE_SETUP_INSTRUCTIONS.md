# Database Setup Instructions

## ⚠️ Important: Railway PostgreSQL Connection

The Railway PostgreSQL database uses **internal hostnames** (`postgres.railway.internal`) that only work **inside Railway's network**.

For **local development**, you have two options:

### Option 1: Use Railway's Public Connection String (Recommended)

1. Go to Railway Dashboard → Your Project → PostgreSQL Service
2. Click on "Connect" or "Variables" tab
3. Look for `DATABASE_PUBLIC_URL` or `PGHOST` variable
4. Copy the **public** connection string (not the internal one)

The public connection string should look like:
```
postgresql://postgres:PASSWORD@containers-us-west-XXX.railway.app:5432/railway
```

5. Update your local `.env` file:
```bash
cd collector
# Edit .env file and set:
DATABASE_URL=<public-railway-postgres-url>
```

### Option 2: Use Railway Proxy (For Local Development)

Railway CLI can create a proxy to the database:

```bash
cd collector
railway connect postgres
```

This will create a local proxy and give you a connection string.

---

## ✅ What We Fixed

1. **Anthropic Instrumentation**: ✅ Fixed
   - Updated test script to use `use_instrumentors=True`
   - Anthropic calls will now be tracked

2. **Database Configuration**: ⚠️ Needs Public URL
   - Railway variables set (for Railway deployment)
   - Local .env needs public Railway PostgreSQL URL

---

## 🧪 Next Steps

1. **Get Railway Public PostgreSQL URL**:
   - Railway Dashboard → PostgreSQL Service → Connect/Variables
   - Copy `DATABASE_PUBLIC_URL` or public connection string

2. **Update Local .env**:
   ```bash
   cd collector
   # Edit .env file:
   DATABASE_URL=<public-railway-postgres-url>
   ```

3. **Test Connection**:
   ```bash
   python3 -c "from sqlalchemy import create_engine; import os; from dotenv import load_dotenv; load_dotenv(); engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✅ Connected!'); conn.close()"
   ```

4. **Restart Collector**:
   ```bash
   cd collector
   uvicorn main:app --reload
   ```

5. **Run Tests**:
   ```bash
   python3 test_platform_comprehensive.py
   ```

---

## 📋 Railway Variables (For Deployment)

These are set correctly for Railway deployment:
- `DATABASE_URL` = `postgresql://postgres:UUqeMWqFJkFvePVGWPsBevDrJbytyHlb@postgres.railway.internal:5432/railway`
- This works **inside Railway** but not locally

---

## 🔍 Troubleshooting

### If you can't find public URL:
1. Railway Dashboard → PostgreSQL → Settings → Networking
2. Enable "Public Networking" if available
3. Or use Railway CLI proxy: `railway connect postgres`

### If connection still fails:
1. Check Railway PostgreSQL service is running
2. Verify credentials are correct
3. Check firewall/network restrictions
4. Try Railway proxy: `railway connect postgres`





