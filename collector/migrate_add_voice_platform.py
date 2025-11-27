"""
Database migration: Add voice_platform column to traceevent table.

Run this script to add the missing column for cross-platform voice tracking.

Usage:
    python migrate_add_voice_platform.py
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(database_url)

# SQL statements to add column
migrations = [
    """
    ALTER TABLE trace_events 
    ADD COLUMN IF NOT EXISTS voice_platform VARCHAR(50);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_trace_events_voice_platform 
    ON trace_events(voice_platform);
    """,
]

def run_migration():
    """Run all migration statements."""
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for i, migration_sql in enumerate(migrations, 1):
                print(f"\n[{i}/{len(migrations)}] Running migration...")
                print(migration_sql.strip())
                
                try:
                    conn.execute(text(migration_sql))
                    print(f"✅ Migration {i} completed successfully")
                except OperationalError as e:
                    error_msg = str(e).lower()
                    if "already exists" in error_msg or "duplicate" in error_msg:
                        print(f"⚠️  Column/index already exists, skipping...")
                    else:
                        print(f"❌ Migration {i} failed: {e}")
                        trans.rollback()
                        return False
                except Exception as e:
                    print(f"❌ Migration {i} failed: {e}")
                    trans.rollback()
                    return False
            
            trans.commit()
            print("\n✅ All migrations completed successfully!")
            return True
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

