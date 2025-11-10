"""Database connection setup using SQLModel."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from llmobserve.config import settings

# Use SQLite for local development (or DATABASE_URL if provided)
if settings.direct_database_url:
    # Use provided DATABASE_URL (PostgreSQL/Supabase)
    database_url = settings.direct_database_url
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
else:
    # Use SQLite for local development
    db_path = Path(__file__).parent.parent.parent / "llmobserve.db"
    database_url = f"sqlite:///{db_path}"
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
    from sqlmodel import Session
    return Session(engine)

