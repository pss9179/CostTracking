#!/usr/bin/env python3
"""
Recalculate costs for ALL Anthropic events in production database.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "collector"))

from db import SessionLocal, init_db
from models import TraceEvent
from pricing import compute_cost
from sqlmodel import select

def main():
    print("🔄 Recalculating ALL Anthropic event costs...")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"📡 Database: {db_url.split('@')[-1] if '@' in db_url else 'local'}\n")
    
    init_db()
    session = SessionLocal()
    
    try:
        # Find ALL Anthropic events (regardless of current cost)
        statement = select(TraceEvent).where(
            TraceEvent.provider == 'anthropic'
        ).where(
            (TraceEvent.input_tokens > 0) | (TraceEvent.output_tokens > 0)
        )
        
        events = list(session.exec(statement).all())
        print(f"📊 Found {len(events)} Anthropic events with tokens\n")
        
        if len(events) == 0:
            print("⚠️  No Anthropic events found with tokens")
            return
        
        updated = 0
        for event in events:
            # Recalculate cost
            new_cost = compute_cost(
                provider=event.provider,
                model=event.model,
                input_tokens=event.input_tokens,
                output_tokens=event.output_tokens
            )
            
            if new_cost > 0:
                old_cost = event.cost_usd
                event.cost_usd = new_cost
                session.add(event)
                updated += 1
                
                print(f"  ✅ {event.model or 'N/A'}")
                print(f"     Tokens: {event.input_tokens}+{event.output_tokens}")
                print(f"     Cost: ${old_cost:.8f} → ${new_cost:.8f}")
            else:
                print(f"  ⚠️  {event.model or 'N/A'}: No pricing found")
        
        session.commit()
        
        print(f"\n✅ Recalculation complete!")
        print(f"   Updated: {updated} events")
        print(f"   Total: {len(events)} events")
        
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

