-- Migration: Add password authentication to users
-- Date: 2025-11-12
-- Purpose: Enable email/password authentication

-- Add password_hash column (allow NULL initially for migration)
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Drop Clerk-specific column if it exists (SQLite doesn't support DROP COLUMN easily)
-- For SQLite, we'll just leave it - it won't hurt
-- For PostgreSQL, uncomment the next line:
-- ALTER TABLE users DROP COLUMN IF EXISTS clerk_user_id;

-- Migration complete
-- Existing users will have NULL password_hash (they need to reset password)
-- New users will have password_hash set during signup

