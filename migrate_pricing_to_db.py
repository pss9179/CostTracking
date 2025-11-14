#!/usr/bin/env python3
"""
Migrate pricing data from registry.json to Supabase pricing table.
"""
import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

# Add collector to path
sys.path.insert(0, str(Path(__file__).parent / "collector"))

# Load pricing registry
registry_file = Path(__file__).parent / "collector" / "pricing" / "registry.json"
with open(registry_file, "r") as f:
    registry = json.load(f)

# Map pricing fields to pricing_type
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
    
    if "per_1k_calls" in pricing_data:
        return "per_1k_calls", {"per_1k_calls": pricing_data["per_1k_calls"]}
    
    if "per_1k_chars" in pricing_data:
        return "per_1k_chars", {"per_1k_chars": pricing_data["per_1k_chars"]}
    
    if "per_1k_emails" in pricing_data:
        return "per_1k_emails", {"per_1k_emails": pricing_data["per_1k_emails"]}
    
    if "per_1k_images" in pricing_data:
        return "per_1k_images", {"per_1k_images": pricing_data["per_1k_images"]}
    
    if "per_1k_records" in pricing_data:
        return "per_1k_records", {"per_1k_records": pricing_data["per_1k_records"]}
    
    if "per_1k_tokens" in pricing_data:
        return "per_1k_tokens", {"per_1k_tokens": pricing_data["per_1k_tokens"]}
    
    if "per_1m_chars" in pricing_data:
        return "per_1m_chars", {"per_1m_chars": pricing_data["per_1m_chars"]}
    
    if "per_gb" in pricing_data:
        return "per_gb", {"per_gb": pricing_data["per_gb"]}
    
    if "per_gb_month" in pricing_data:
        return "per_gb_month", {"per_gb_month": pricing_data["per_gb_month"]}
    
    if "per_gb_day" in pricing_data:
        return "per_gb_day", {"per_gb_day": pricing_data["per_gb_day"]}
    
    if "per_minute" in pricing_data:
        return "per_minute", {"per_minute": pricing_data["per_minute"]}
    
    if "per_second" in pricing_data:
        return "per_second", {"per_second": pricing_data["per_second"]}
    
    if "per_character" in pricing_data:
        return "per_character", {"per_character": pricing_data["per_character"]}
    
    if "per_session" in pricing_data:
        return "per_session", {"per_session": pricing_data["per_session"]}
    
    if "per_image" in pricing_data:
        return "per_image", pricing_data  # Keep all image size variants
    
    if "per_message" in pricing_data:
        return "per_message", {"per_message": pricing_data["per_message"]}
    
    if "percentage" in pricing_data:
        return "percentage", {
            "percentage": pricing_data["percentage"],
            "fixed_fee": pricing_data.get("fixed_fee", 0.0)
        }
    
    if "training" in pricing_data or "training_per_hour" in pricing_data:
        return "training", {
            "training": pricing_data.get("training"),
            "training_per_hour": pricing_data.get("training_per_hour")
        }
    
    # Token-based (default)
    return "token_based", {
        "input": pricing_data.get("input", 0.0),
        "output": pricing_data.get("output", 0.0),
        "cached_input": pricing_data.get("cached_input", 0.0)
    }

# Generate SQL INSERT statements
sql_statements = []
providers_seen = set()

for key, pricing_data in registry.items():
    # Parse provider:model
    parts = key.split(":", 1)
    provider = parts[0]
    model = parts[1] if len(parts) > 1 else None
    
    providers_seen.add(provider)
    
    # Determine pricing type
    pricing_type, normalized_data = determine_pricing_type(pricing_data)
    
    # Build description
    if model:
        description = f"{provider} {model} pricing"
    else:
        description = f"{provider} provider-level pricing"
    
    # Convert to JSON string for SQL
    pricing_json = json.dumps(normalized_data)
    
    # Generate INSERT statement
    if model:
        sql = f"""INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('{provider}', '{model}', '{pricing_type}', '{pricing_json}'::jsonb, '{description}', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();"""
    else:
        sql = f"""INSERT INTO pricing (provider, model, pricing_type, pricing_data, description, source)
VALUES ('{provider}', NULL, '{pricing_type}', '{pricing_json}'::jsonb, '{description}', 'official')
ON CONFLICT (provider, model, effective_date) DO UPDATE 
SET pricing_data = EXCLUDED.pricing_data,
    pricing_type = EXCLUDED.pricing_type,
    description = EXCLUDED.description,
    updated_at = NOW();"""
    
    sql_statements.append(sql)

# Print summary
print(f"Total pricing entries: {len(registry)}")
print(f"Unique providers: {len(providers_seen)}")
print(f"\nProviders: {sorted(providers_seen)}")
print(f"\nSQL statements generated: {len(sql_statements)}")

# Write SQL file
sql_file = Path(__file__).parent / "migrate_pricing.sql"
with open(sql_file, "w") as f:
    f.write("-- Migrate pricing data from registry.json to Supabase\n")
    f.write("-- Generated automatically\n\n")
    for sql in sql_statements:
        f.write(sql + "\n\n")

print(f"\n✅ SQL file written to: {sql_file}")
print(f"\nTo apply, run:")
print(f"  psql 'your_connection_string' -f {sql_file}")



