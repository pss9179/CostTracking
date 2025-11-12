-- Migration: Add tenant_id for multi-tenancy support
-- Date: 2025-11-12
-- Purpose: Enable unified multi-tenancy while maintaining backward compatibility

-- Add tenant_id column with default value (SQLite compatible)
-- Note: IF NOT EXISTS is not standard SQL, use this for SQLite/PostgreSQL compat
ALTER TABLE trace_events ADD COLUMN tenant_id TEXT NOT NULL DEFAULT 'default_tenant';

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_tenant_id ON trace_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_created ON trace_events(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tenant_customer ON trace_events(tenant_id, customer_id);

-- Migration complete
-- All existing rows will have tenant_id = 'default_tenant'
-- New rows can specify their tenant_id explicitly
-- Note: COMMENT ON COLUMN is PostgreSQL-only, not supported in SQLite

