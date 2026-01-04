#!/usr/bin/env python3
"""
Fix tenant_id and costs for ALL events in production database.
This ensures:
1. tenant_id matches user_id (for dashboard filtering)
2. All events with tokens have costs > 0
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
    print("🔧 Fixing tenant_id and costs for ALL events...")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"📡 Database: {db_url.split('@')[-1] if '@' in db_url else 'local'}\n")
    
    init_db()
    session = SessionLocal()
    
    try:
        # Find ALL events with tokens
        statement = select(TraceEvent).where(
            (TraceEvent.input_tokens > 0) | (TraceEvent.output_tokens > 0)
        )
        
        events = list(session.exec(statement).all())
        print(f"📊 Found {len(events)} events with tokens\n")
        
        if len(events) == 0:
            print("⚠️  No events found with tokens")
            return
        
        tenant_fixed = 0
        cost_fixed = 0
        
        for event in events:
            updated = False
            
            # Fix tenant_id: if user_id exists, look up User to get clerk_user_id
            if event.user_id:
                from models import User
                user = session.get(User, event.user_id)
                if user and user.clerk_user_id:
                    # Use Clerk user ID as tenant_id (dashboard filters by this)
                    if event.tenant_id != user.clerk_user_id:
                        old_tenant = event.tenant_id
                        event.tenant_id = user.clerk_user_id
                        tenant_fixed += 1
                        updated = True
                        print(f"  🔧 Fixed tenant_id: {old_tenant} → {event.tenant_id} (clerk_user_id)")
                elif event.tenant_id != str(event.user_id):
                    # Fallback: use user_id as string if no clerk_user_id
                    old_tenant = event.tenant_id
                    event.tenant_id = str(event.user_id)
                    tenant_fixed += 1
                    updated = True
                    print(f"  🔧 Fixed tenant_id: {old_tenant} → {event.tenant_id} (user_id fallback)")
            
            # Fix cost: if cost is 0 but we have tokens, calculate it
            if event.cost_usd == 0.0 and (event.input_tokens > 0 or event.output_tokens > 0):
                new_cost = compute_cost(
                    provider=event.provider,
                    model=event.model,
                    input_tokens=event.input_tokens,
                    output_tokens=event.output_tokens
                )
                
                if new_cost > 0:
                    event.cost_usd = new_cost
                    cost_fixed += 1
                    updated = True
                    print(f"  💰 Fixed cost: {event.provider}/{event.model or 'N/A'}: ${new_cost:.8f}")
            
            if updated:
                session.add(event)
        
        session.commit()
        
        print(f"\n✅ Fix complete!")
        print(f"   Tenant IDs fixed: {tenant_fixed}")
        print(f"   Costs fixed: {cost_fixed}")
        print(f"   Total events processed: {len(events)}")
        
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

