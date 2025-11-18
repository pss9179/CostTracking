# Database Migration - For Suriya

✅ Migration completed successfully!

## Quick Fix Needed

The database is missing Stripe subscription columns. This is a 30-second fix.

## Option 1: Railway Dashboard (Easiest - 2 minutes)

1. Go to https://railway.app
2. Login with your account
3. Open the project (should be "wonderful-delight" or similar)
4. Click on the **Database** service (or PostgreSQL service)
5. Click **"Query"** or **"Connect"** tab
6. Copy and paste this SQL:

```sql
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'free';

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS promo_code VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id);
```

7. Click **"Run"** or **"Execute"**
8. Done! ✅

## Option 2: Railway CLI (If you have it installed)

```bash
cd collector
railway login  # Login if not already
railway service  # Select the service if prompted
railway run python migrate_add_stripe_columns.py
```

**Or share your Railway token:**
1. Go to https://railway.app/account/tokens
2. Create/copy a token
3. Share it with Pranav so he can run: `railway login --token <your-token>`

## That's it!

This fixes the database errors. The migration is safe - it won't break anything if run multiple times.

