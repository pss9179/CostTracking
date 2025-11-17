# Get Supabase Connection Pooling URL

## Quick Steps:

1. **Go to Supabase Dashboard:**
   - https://supabase.com/dashboard/project/tsfzeoxffnfaiyqrlqwb

2. **Navigate to Settings:**
   - Click "Settings" (gear icon) in left sidebar
   - Click "Database"

3. **Get Connection Pooling URL:**
   - Scroll down to "Connection string" section
   - Click "Connection pooling" tab (not "Direct connection")
   - Select "Session mode"
   - Copy the connection string

   It should look like:
   ```
   postgresql://postgres.tsfzeoxffnfaiyqrlqwb:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

4. **Enable Connection Pooling (if not already enabled):**
   - Connection pooling is usually enabled by default
   - If you see a toggle, make sure it's ON

---

## Alternative: Use Direct Connection on Port 6543

If pooling URL doesn't work, the direct connection on port 6543 should work (we tested this locally):

```
postgresql://postgres:3ioIruC2XuyUPwnN@db.tsfzeoxffnfaiyqrlqwb.supabase.co:6543/postgres
```

This is what we're currently using and it works locally. The issue is Railway's network being blocked, not the connection string format.

---

## If Railway Still Blocks:

**Use Railway's PostgreSQL instead:**
1. Railway Dashboard → New → Database → PostgreSQL
2. Copy the connection string
3. Update `DATABASE_URL` in Railway variables

This will work immediately with no firewall issues.



