#!/usr/bin/env python3
"""
Recalculate costs for existing events that have cost_usd=0.0.

This fixes events that were stored before pricing data was loaded.
"""
import sys
import os
from pathlib import Path

# Add collector to path
sys.path.insert(0, str(Path(__file__).parent / "collector"))

from db import SessionLocal, init_db
from models import TraceEvent
from pricing import compute_cost
from sqlmodel import select

def main():
    print("🔄 Recalculating costs for existing events...")
    
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"📡 Database: {db_url.split('@')[-1] if '@' in db_url else 'local'}\n")
    
    # Initialize database
    init_db()
    
    # Create session
    session = SessionLocal()
    
    try:
        # Find events with cost_usd=0.0 that have token data
        statement = select(TraceEvent).where(
            TraceEvent.cost_usd == 0.0
        ).where(
            (TraceEvent.input_tokens > 0) | (TraceEvent.output_tokens > 0)
        )
        
        events = session.exec(statement).all()
        total = len(list(events))
        
        if total == 0:
            print("✅ No events need cost recalculation")
            return
        
        print(f"📊 Found {total} events with cost_usd=0.0\n")
        
        # Recalculate costs
        updated = 0
        failed = 0
        
        # Reset statement to get fresh results
        events = session.exec(statement).all()
        
        for event in events:
            try:
                # Recalculate cost
                new_cost = compute_cost(
                    provider=event.provider,
                    model=event.model,
                    input_tokens=event.input_tokens,
                    output_tokens=event.output_tokens
                )
                
                if new_cost > 0:
                    event.cost_usd = new_cost
                    session.add(event)
                    updated += 1
                    
                    if updated <= 10:  # Show first 10 updates
                        print(f"   ✅ {event.provider}:{event.model or 'N/A'} - ${new_cost:.8f}")
                else:
                    failed += 1
                    if failed <= 5:
                        print(f"   ⚠️  {event.provider}:{event.model or 'N/A'} - No pricing found")
                        
            except Exception as e:
                failed += 1
                if failed <= 5:
                    print(f"   ❌ Error calculating cost for {event.provider}:{event.model}: {e}")
        
        # Commit all changes
        session.commit()
        
        print(f"\n✅ Recalculation complete!")
        print(f"   Updated: {updated}")
        print(f"   Failed (no pricing): {failed}")
        print(f"   Total processed: {total}")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()

