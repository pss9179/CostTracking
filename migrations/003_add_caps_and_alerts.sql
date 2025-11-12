-- Migration 003: Add Spending Caps and Alerts
-- Created: 2025-11-12
-- Description: Add spending caps and alert functionality for cost control

-- Create spending_caps table
CREATE TABLE IF NOT EXISTS spending_caps (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Cap scope
    cap_type TEXT NOT NULL,  -- 'global', 'provider', 'model', 'agent', 'customer'
    target_name TEXT,  -- Target name (e.g., 'openai', 'gpt-4', 'research_agent', 'customer_123')
    
    -- Cap limits
    limit_amount REAL NOT NULL,  -- Dollar amount cap
    period TEXT NOT NULL,  -- 'daily', 'weekly', 'monthly'
    
    -- Alert settings
    alert_threshold REAL NOT NULL DEFAULT 0.8,  -- Alert when % of cap is reached
    alert_email TEXT NOT NULL,  -- Email to send alerts to
    
    -- Status
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_alerted_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for spending_caps
CREATE INDEX IF NOT EXISTS idx_caps_user_id ON spending_caps(user_id);
CREATE INDEX IF NOT EXISTS idx_caps_enabled ON spending_caps(enabled);

-- Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cap_id UUID NOT NULL REFERENCES spending_caps(id) ON DELETE CASCADE,
    
    -- Alert details
    alert_type TEXT NOT NULL,  -- 'threshold_reached', 'cap_exceeded'
    current_spend REAL NOT NULL,
    cap_limit REAL NOT NULL,
    percentage REAL NOT NULL,
    
    -- Context
    target_type TEXT NOT NULL,
    target_name TEXT NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    
    -- Notification
    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user_id ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_cap_id ON alerts(cap_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);

