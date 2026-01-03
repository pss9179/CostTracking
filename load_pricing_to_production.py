#!/usr/bin/env python3
"""
Load pricing data from registry.json into production database.

Usage:
    # Set production DATABASE_URL
    export DATABASE_URL="postgresql://user:pass@host:port/dbname"
    python load_pricing_to_production.py
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add collector to path
sys.path.insert(0, str(Path(__file__).parent / "collector"))

from db import SessionLocal, init_db
from models import Pricing
from sqlmodel import select

# Load pricing registry
registry_file = Path(__file__).parent / "collector" / "pricing" / "registry.json"
with open(registry_file, "r") as f:
    registry = json.load(f)

def determine_pricing_type(pricing_data: dict) -> tuple[str, dict]:
    """Determine pricing type and normalize pricing_data."""
    pricing_data = {k: v for k, v in pricing_data.items() if v is not None}
    
    if "per_call" in pricing_data:
        return "per_call", {"per_call": pricing_data["per_call"]}
    
    if "per_million" in pricing_data:
        return "per_million", {"per_million": pricing_data["per_million"]}
    
    if "per_million_tokens" in pricing_data:
        return "per_million_tokens", {"per_million_tokens": pricing_data["per_million_tokens"]}
    
    if "per_1k_requests" in pricing_data:
        return "per_1k_requests", {"per_1k_requests": pricing_data["per_1k_requests"]}
    
    if "per_gb" in pricing_data:
        return "per_gb", {"per_gb": pricing_data["per_gb"]}
    
    if "per_gb_month" in pricing_data:
        return "per_gb_month", {"per_gb_month": pricing_data["per_gb_month"]}
    
    if "per_minute" in pricing_data:
        return "per_minute", {"per_minute": pricing_data["per_minute"]}
    
    if "per_second" in pricing_data:
        return "per_second", {"per_second": pricing_data["per_second"]}
    
    if "per_character" in pricing_data:
        return "per_character", {"per_character": pricing_data["per_character"]}
    
    if "per_session" in pricing_data:
        return "per_session", {"per_session": pricing_data["per_session"]}
    
    # Token-based (default)
    return "token_based", {
        "input": pricing_data.get("input", 0.0),
        "output": pricing_data.get("output", 0.0),
        "cached_input": pricing_data.get("cached_input", 0.0)
    }

def main():
    print("🚀 Loading pricing data into production database...")
    print(f"📦 Loaded {len(registry)} pricing entries from JSON\n")
    
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nUsage:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        print("  python load_pricing_to_production.py")
        sys.exit(1)
    
    print(f"📡 Database: {db_url.split('@')[-1] if '@' in db_url else 'local'}\n")
    
    # Initialize database
    init_db()
    
    # Create session
    session = SessionLocal()
    
    try:
        inserted = 0
        updated = 0
        skipped = 0
        
        for key, pricing_data in registry.items():
            # Parse provider:model
            parts = key.split(":", 1)
            provider = parts[0]
            model = parts[1] if len(parts) > 1 else None
            
            # Determine pricing type
            pricing_type, normalized_data = determine_pricing_type(pricing_data)
            
            # Check if exists
            statement = select(Pricing).where(
                Pricing.provider == provider,
                Pricing.model == model,
                Pricing.is_active == True
            )
            existing = session.exec(statement).first()
            
            if existing:
                # Update existing
                existing.pricing_data = normalized_data
                existing.pricing_type = pricing_type
                existing.updated_at = datetime.utcnow()
                session.add(existing)
                updated += 1
                if updated <= 5:  # Show first 5 updates
                    print(f"   🔄 Updated {provider}:{model or 'N/A'}")
            else:
                # Insert new
                pricing = Pricing(
                    provider=provider,
                    model=model,
                    pricing_type=pricing_type,
                    pricing_data=normalized_data,
                    description=f"{provider}{':' + model if model else ''} pricing",
                    source="migrated_from_json",
                    is_active=True,
                    effective_date=datetime.utcnow()
                )
                session.add(pricing)
                inserted += 1
                if inserted <= 5:  # Show first 5 inserts
                    print(f"   ✅ Inserted {provider}:{model or 'N/A'}")
        
        # Commit all changes
        session.commit()
        
        print(f"\n✅ Migration complete!")
        print(f"   Inserted: {inserted}")
        print(f"   Updated: {updated}")
        print(f"   Total processed: {len(registry)}")
        
        # Verify Claude pricing
        print(f"\n🔍 Verifying Claude pricing...")
        claude_statement = select(Pricing).where(
            Pricing.provider == "anthropic",
            Pricing.is_active == True
        )
        claude_entries = session.exec(claude_statement).all()
        print(f"   Found {len(claude_entries)} Anthropic pricing entries")
        for entry in claude_entries[:5]:
            print(f"   - {entry.provider}:{entry.model or 'N/A'} ({entry.pricing_type})")
        
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

