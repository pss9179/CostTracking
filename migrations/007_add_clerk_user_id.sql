-- Add Clerk user ID support to users table
-- Migration 007: Add clerk_user_id for Clerk authentication

-- SQLite version: Add new column
ALTER TABLE users ADD COLUMN clerk_user_id TEXT NULL;

-- Create unique index on clerk_user_id
CREATE UNIQUE INDEX idx_users_clerk_id ON users(clerk_user_id) WHERE clerk_user_id IS NOT NULL;

-- Note: password_hash column is already nullable in the updated schema.
-- Existing rows will have NULL clerk_user_id (email/password users).
-- New Clerk users will have NULL password_hash.

