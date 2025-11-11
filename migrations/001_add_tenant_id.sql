-- Migration: Add tenant_id column for multi-tenant support
ALTER TABLE trace_events ADD COLUMN tenant_id TEXT NULL;
CREATE INDEX IF NOT EXISTS idx_tenant_id ON trace_events(tenant_id);

