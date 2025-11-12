"""
Clear all data from the collector database.

This script removes all trace events from the database for a clean test.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import Session, select, delete
from collector.db import engine
from collector.models import TraceEvent

def clear_all_data():
    """Delete all trace events from the database."""
    with Session(engine) as session:
        # Count before deletion
        count_stmt = select(TraceEvent)
        before_count = len(session.exec(count_stmt).all())
        
        # Delete all events
        delete_stmt = delete(TraceEvent)
        session.exec(delete_stmt)
        session.commit()
        
        print(f"✅ Cleared {before_count} events from database")

if __name__ == "__main__":
    print("🗑️  Clearing all data from collector database...")
    clear_all_data()
    print("✅ Database cleared successfully!")

