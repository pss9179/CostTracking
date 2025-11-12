"""
Clear test data from database.

Use this to remove old test data from previous test runs.
"""
import os
import sys
from pathlib import Path

# Add collector to path
sys.path.insert(0, str(Path(__file__).parent.parent / "collector"))

from db import get_session
from models import TraceEvent
from sqlmodel import select

def clear_test_data():
    """Clear all trace events from database."""
    print("=" * 80)
    print("🗑️  CLEARING TEST DATA")
    print("=" * 80)
    print()
    
    session = next(get_session())
    
    try:
        # Count events before deletion
        count_statement = select(TraceEvent)
        events = session.exec(count_statement).all()
        count = len(events)
        
        if count == 0:
            print("✅ Database is already empty")
            return
        
        print(f"Found {count} events in database")
        print()
        
        # Confirm deletion
        response = input("⚠️  Are you sure you want to delete ALL events? (yes/no): ")
        if response.lower() != "yes":
            print("❌ Cancelled")
            return
        
        # Delete all events
        for event in events:
            session.delete(event)
        
        session.commit()
        
        print(f"✅ Deleted {count} events")
        print()
        print("💡 Next steps:")
        print("   1. Run your test script: python scripts/test_agent.py")
        print("   2. Refresh the dashboard to see clean data")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    try:
        clear_test_data()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()

