# Database Migration: Add Stripe Columns

## Problem
The database is missing Stripe subscription columns, causing errors:
- `stripe_customer_id`
- `stripe_subscription_id`
- `subscription_status`
- `promo_code`

## Solution

### Option 1: Run Migration Script (Recommended)

1. **SSH into Railway or run locally:**
   ```bash
   cd collector
   python migrate_add_stripe_columns.py
   ```

2. **Or run via Railway CLI:**
   ```bash
   railway run python collector/migrate_add_stripe_columns.py
   ```

### Option 2: Manual SQL (If script doesn't work)

Run these SQL commands in your Railway database:

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

### Option 3: Via Railway Dashboard

1. Go to Railway Dashboard → Your Project → Database
2. Click "Query" or "Connect"
3. Run the SQL commands above

## Verify Migration

After running, verify columns exist:
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('stripe_customer_id', 'stripe_subscription_id', 'subscription_status', 'promo_code');
```

You should see all 4 columns listed.

