-- Migration: Add customer_id column for per-customer tracking within tenants
ALTER TABLE trace_events ADD COLUMN customer_id TEXT NULL;
CREATE INDEX IF NOT EXISTS idx_customer_id ON trace_events(customer_id);

