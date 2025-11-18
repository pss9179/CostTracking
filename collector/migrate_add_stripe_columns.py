"""
Database migration: Add Stripe subscription columns to users table.

Run this script on Railway to add the missing columns:
- stripe_customer_id
- stripe_subscription_id
- subscription_status
- promo_code

Usage:
    python migrate_add_stripe_columns.py
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(database_url)

# SQL statements to add columns
migrations = [
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(50) DEFAULT 'free';
    """,
    """
    ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS promo_code VARCHAR(255);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id ON users(stripe_subscription_id);
    """,
]

def run_migration():
    """Run all migration statements."""
    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            try:
                print(f"Running migration {i}/{len(migrations)}...")
                conn.execute(text(migration))
                conn.commit()
                print(f"✓ Migration {i} completed")
            except OperationalError as e:
                # Check if column already exists (PostgreSQL specific)
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⚠ Migration {i} skipped (column/index already exists)")
                else:
                    print(f"✗ Migration {i} failed: {e}")
                    raise
        print("\n✅ All migrations completed successfully!")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

