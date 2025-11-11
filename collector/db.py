"""
Database setup and session management.
"""
from sqlmodel import create_engine, SQLModel, Session
from typing import Generator

# SQLite database
DATABASE_URL = "sqlite:///./collector.db"

# Create engine with check_same_thread=False for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
    connect_args={"check_same_thread": False}
)


def init_db():
    """Create all tables. Called on app startup."""
    SQLModel.metadata.create_all(engine)


def run_migrations():
    """Run database migrations for existing DBs."""
    import sqlite3
    
    db_path = DATABASE_URL.replace("sqlite:///./", "")
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
    
    # Check if section_path column exists (for hierarchical tracing)
    if "section_path" not in columns:
        cursor.execute("ALTER TABLE trace_events ADD COLUMN section_path TEXT NULL")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_section_path ON trace_events(section_path)")
        conn.commit()
        print("[Migration] Added section_path column to trace_events table")
    
    # Check if cached_tokens column exists (for OpenAI prompt caching)
    if "cached_tokens" not in columns:
        cursor.execute("ALTER TABLE trace_events ADD COLUMN cached_tokens INTEGER DEFAULT 0")
        conn.commit()
        print("[Migration] Added cached_tokens column to trace_events table")
    
    # Check if is_streaming column exists (for streaming responses)
    if "is_streaming" not in columns:
        cursor.execute("ALTER TABLE trace_events ADD COLUMN is_streaming INTEGER DEFAULT 0")
        conn.commit()
        print("[Migration] Added is_streaming column to trace_events table")
    
    # Check if stream_cancelled column exists (for cancelled streams)
    if "stream_cancelled" not in columns:
        cursor.execute("ALTER TABLE trace_events ADD COLUMN stream_cancelled INTEGER DEFAULT 0")
        conn.commit()
        print("[Migration] Added stream_cancelled column to trace_events table")
    
    conn.close()


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes to get a database session."""
    with Session(engine) as session:
        yield session

