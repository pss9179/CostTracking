-- Database Migration: Add Stripe subscription columns
-- Run this SQL in Railway Dashboard → Database → Query

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

-- Verify migration
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name IN ('stripe_customer_id', 'stripe_subscription_id', 'subscription_status', 'promo_code');

