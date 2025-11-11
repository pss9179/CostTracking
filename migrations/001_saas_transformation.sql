-- SaaS Transformation: Remove tenants, add users and API keys
--
-- This migration transforms the multi-tenant local system into a SaaS platform
-- Run this on PostgreSQL only (not SQLite)

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id VARCHAR(255) UNIQUE NOT NULL,  -- Clerk's user ID
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(50) DEFAULT 'free'
);

CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_users_email ON users(email);

-- Create API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,  -- Hashed API key
    key_prefix VARCHAR(20) NOT NULL,  -- First few chars for display (e.g., "llmo_sk_abc...")
    name VARCHAR(100) NOT NULL,  -- User-friendly name
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    revoked_at TIMESTAMP,
    
    CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(user_id, revoked_at) WHERE revoked_at IS NULL;

-- Modify trace_events table
-- Remove tenant_id, add user_id
ALTER TABLE trace_events 
    DROP COLUMN IF EXISTS tenant_id,
    ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_trace_events_user_id ON trace_events(user_id);
CREATE INDEX IF NOT EXISTS idx_trace_events_user_created ON trace_events(user_id, created_at DESC);

-- customer_id remains unchanged (represents end-users of our customers)

-- Create usage tracking table (for future billing)
CREATE TABLE IF NOT EXISTS usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    event_count INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(12, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, period_start)
);

CREATE INDEX idx_usage_logs_user_period ON usage_logs(user_id, period_start DESC);

-- Comments
COMMENT ON TABLE users IS 'User accounts (linked to Clerk authentication)';
COMMENT ON TABLE api_keys IS 'API keys for SDK authentication';
COMMENT ON TABLE usage_logs IS 'Monthly usage aggregates for billing';
COMMENT ON COLUMN api_keys.key_hash IS 'bcrypt hash of the full API key';
COMMENT ON COLUMN api_keys.key_prefix IS 'Displayable prefix (e.g., llmo_sk_abc...)';

