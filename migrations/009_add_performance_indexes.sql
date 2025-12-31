-- Performance indexes for dashboard queries
-- These indexes dramatically speed up queries that filter by user_id and created_at
-- Run this migration on your production database (Supabase SQL Editor or Railway)

-- Critical composite index for all dashboard queries
-- Covers: by-provider, by-model, by-section, timeseries, daily stats
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trace_user_created 
  ON trace_events(user_id, created_at DESC);

-- Composite index for provider-specific queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trace_user_provider_created 
  ON trace_events(user_id, provider, created_at DESC);

-- Composite index for section/feature queries  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trace_user_section_created 
  ON trace_events(user_id, section, created_at DESC);

-- Composite index for customer queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trace_user_customer_created 
  ON trace_events(user_id, customer_id, created_at DESC);

-- Update query planner statistics
ANALYZE trace_events;

-- Verify indexes were created
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'trace_events' 
ORDER BY indexname;

