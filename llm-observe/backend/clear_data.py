#!/usr/bin/env python3
"""Clear all spans and traces from the database."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from sqlmodel import Session, select, delete
from llmobserve.storage.db import get_session, engine
from llmobserve.storage.models import SpanSummary, Trace


def clear_all_data():
    """Clear all spans and traces from the database."""
    print("🗑️  Clearing all data from database...")
    
    with get_session() as session:
        # Delete all spans
        spans_deleted = session.exec(delete(SpanSummary)).rowcount
        print(f"   ✓ Deleted {spans_deleted} spans")
        
        # Delete all traces
        traces_deleted = session.exec(delete(Trace)).rowcount
        print(f"   ✓ Deleted {traces_deleted} traces")
        
        session.commit()
    
    print("✅ All data cleared successfully!")
    print("\nYou can now run workflows to see fresh data.")


if __name__ == "__main__":
    try:
        clear_all_data()
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

