"""
Quick migration script using the same DB connection as the collector.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Import after loading env
from db import engine
from sqlalchemy import text

print("Running migration: Add voice_platform column to trace_events...")

migrations = [
    "ALTER TABLE trace_events ADD COLUMN IF NOT EXISTS voice_platform VARCHAR(50);",
    "CREATE INDEX IF NOT EXISTS idx_trace_events_voice_platform ON trace_events(voice_platform);",
]

try:
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for i, sql in enumerate(migrations, 1):
                print(f"[{i}/{len(migrations)}] Executing: {sql[:50]}...")
                conn.execute(text(sql))
                print(f"✅ Migration {i} completed")
            
            trans.commit()
            print("\n✅ All migrations completed successfully!")
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

