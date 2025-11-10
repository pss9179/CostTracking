"""Database connection setup using SQLModel with SQLite."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

from llmobserve.models import CostEvent

# SQLite database path
_db_path = Path(__file__).parent.parent.parent / "llmobserve.db"
database_url = f"sqlite:///{_db_path}"

# Create engine
engine = create_engine(
    database_url,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite-specific
)


def init_db() -> None:
    """Initialize database schema (create tables)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session (for use with context manager)."""
    return Session(engine)

