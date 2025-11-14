"""
Migrate pricing from JSON file to Supabase database.

This script reads pricing from collector/pricing/registry.json and inserts it into
the Supabase pricing table, avoiding duplicates.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add collector to path
collector_path = Path(__file__).parent.parent / "collector"
sys.path.insert(0, str(collector_path))

from db import get_session
from sqlmodel import Session, select
from models import Pricing  # We'll need to create this model


def load_json_pricing() -> Dict[str, Any]:
    """Load pricing from JSON file."""
    json_path = Path(__file__).parent.parent / "collector" / "pricing" / "registry.json"
    with open(json_path, "r") as f:
        return json.load(f)


def convert_json_to_pricing_entries(json_pricing: Dict[str, Any]) -> list:
    """
    Convert JSON pricing format to database entries.
    
    JSON format: {"provider:model": {"input": 0.001, "output": 0.002}}
    DB format: provider="provider", model="model", pricing_data={"input": 0.001, "output": 0.002}
    """
    entries = []
    
    for key, pricing_data in json_pricing.items():
        # Parse key format: "provider:model" or "provider"
        if ":" in key:
            provider, model = key.split(":", 1)
        else:
            provider = key
            model = None
        
        # Determine pricing type
        pricing_type = "token_based"  # default
        if "per_call" in pricing_data:
            pricing_type = "per_call"
        elif "per_million" in pricing_data:
            pricing_type = "per_million"
        elif "per_1k_chars" in pricing_data or "per_1k_emails" in pricing_data or "per_1k_requests" in pricing_data:
            pricing_type = "per_1k"
        elif "per_minute" in pricing_data:
            pricing_type = "per_minute"
        elif "per_second" in pricing_data:
            pricing_type = "per_second"
        elif "percentage" in pricing_data:
            pricing_type = "percentage"
        
        entries.append({
            "provider": provider,
            "model": model,
            "pricing_type": pricing_type,
            "pricing_data": pricing_data,
            "description": f"{provider}{':' + model if model else ''} pricing",
            "source": "migrated_from_json",
            "is_active": True
        })
    
    return entries


def migrate_pricing(session: Session):
    """Migrate pricing from JSON to database."""
    print("📦 Loading pricing from JSON file...")
    json_pricing = load_json_pricing()
    print(f"   Found {len(json_pricing)} pricing entries")
    
    print("\n🔄 Converting to database format...")
    entries = convert_json_to_pricing_entries(json_pricing)
    print(f"   Converted to {len(entries)} database entries")
    
    print("\n💾 Inserting into Supabase...")
    inserted = 0
    skipped = 0
    
    for entry in entries:
        # Check if already exists
        statement = select(Pricing).where(
            Pricing.provider == entry["provider"],
            Pricing.model == entry["model"]
        )
        existing = session.exec(statement).first()
        
        if existing:
            print(f"   ⏭️  Skipping {entry['provider']}:{entry['model'] or 'N/A'} (already exists)")
            skipped += 1
        else:
            pricing = Pricing(**entry)
            session.add(pricing)
            print(f"   ✅ Added {entry['provider']}:{entry['model'] or 'N/A'}")
            inserted += 1
    
    session.commit()
    
    print(f"\n✅ Migration complete!")
    print(f"   Inserted: {inserted}")
    print(f"   Skipped: {skipped}")
    print(f"   Total: {len(entries)}")


if __name__ == "__main__":
    print("🚀 Starting pricing migration to Supabase...\n")
    
    session = next(get_session())
    try:
        migrate_pricing(session)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

