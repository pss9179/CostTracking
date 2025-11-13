-- Migration: Add hard cap enforcement fields
-- Adds enforcement mode and tracking for when caps are exceeded

-- Add enforcement field (alert vs hard_block)
ALTER TABLE spending_caps ADD COLUMN enforcement TEXT NOT NULL DEFAULT 'alert';

-- Add exceeded_at timestamp to track when cap was hit
ALTER TABLE spending_caps ADD COLUMN exceeded_at TIMESTAMP NULL;

-- Add index for quick lookups by enforcement type
CREATE INDEX idx_caps_enforcement ON spending_caps(user_id, enforcement, enabled);

-- Add index for cap_type for efficient filtering
CREATE INDEX idx_caps_type ON spending_caps(cap_type, enabled);

-- Add comments
COMMENT ON COLUMN spending_caps.enforcement IS 'Enforcement mode: alert (email only) or hard_block (prevent requests)';
COMMENT ON COLUMN spending_caps.exceeded_at IS 'Timestamp when cap was first exceeded in current period';

