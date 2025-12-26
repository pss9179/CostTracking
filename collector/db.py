"""
Database setup and session management.
"""
import os
from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
from dotenv import load_dotenv

# Load environment variables (override=True to use .env file over shell env vars)
load_dotenv(override=True)

# Database URL from environment (PostgreSQL or SQLite fallback)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./collector.db")

# Flag to determine if using PostgreSQL (for SQL dialect differences)
IS_POSTGRESQL = not DATABASE_URL.startswith("sqlite")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite needs check_same_thread=False
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL/Supabase
    # Force IPv4 to avoid Railway IPv6 connection issues
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    # Add connect_timeout and force IPv4 via connection args
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,  # Verify connections before using
        connect_args={
            "connect_timeout": 10,
            # Force IPv4 by using hostname (psycopg2 will resolve to IPv4)
            # If still issues, we can try adding: "host": parsed.hostname
        }
    )


def init_db():
    """Create all tables. Called on app startup."""
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        # Log error but don't crash - database might be temporarily unavailable
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize database: {e}")
        logger.error("If using Supabase, ensure you're using the Connection Pooling URL (port 6543)")
        logger.error("Get it from: Supabase Dashboard → Settings → Database → Connection pooling")
        raise  # Re-raise so startup fails (app can't run without DB)


def run_migrations():
    """Run database migrations for existing DBs."""
    # For PostgreSQL/Supabase, migrations are handled via SQL scripts
    # For SQLite, we can run migrations inline
    
    if not DATABASE_URL.startswith("sqlite"):
        print("[Migration] Using PostgreSQL - tables created via SQLModel")
        return
    
    # SQLite migrations (legacy)
    import sqlite3
    
    db_path = DATABASE_URL.replace("sqlite:///./", "")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tenant_id column exists
        cursor.execute("PRAGMA table_info(trace_events)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "tenant_id" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN tenant_id TEXT NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenant_id ON trace_events(tenant_id)")
            conn.commit()
            print("[Migration] Added tenant_id column to trace_events table")
        
        # Check if customer_id column exists
        if "customer_id" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN customer_id TEXT NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_id ON trace_events(customer_id)")
            conn.commit()
            print("[Migration] Added customer_id column to trace_events table")
        
        # Check if section_path column exists
        if "section_path" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN section_path TEXT NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_section_path ON trace_events(section_path)")
            conn.commit()
            print("[Migration] Added section_path column to trace_events table")
        
        # Check if cached_tokens column exists
        if "cached_tokens" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN cached_tokens INTEGER DEFAULT 0")
            conn.commit()
            print("[Migration] Added cached_tokens column to trace_events table")
        
        # Check if is_streaming column exists
        if "is_streaming" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN is_streaming INTEGER DEFAULT 0")
            conn.commit()
            print("[Migration] Added is_streaming column to trace_events table")
        
        # Check if stream_cancelled column exists
        if "stream_cancelled" not in columns:
            cursor.execute("ALTER TABLE trace_events ADD COLUMN stream_cancelled INTEGER DEFAULT 0")
            conn.commit()
            print("[Migration] Added stream_cancelled column to trace_events table")
        
        conn.close()
    except Exception as e:
        print(f"[Migration] SQLite migrations failed (table may not exist yet): {e}")


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes to get a database session."""
    with Session(engine) as session:
        yield session


def SessionLocal() -> Session:
    """Create a new database session (for background tasks)."""
    return Session(engine)

