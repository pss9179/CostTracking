"""
Add Custom API Pricing to Registry

This script shows how to add pricing for ANY API to the registry.
"""
import json
import sys
from pathlib import Path

# Path to pricing registry
registry_path = Path(__file__).parent.parent / "collector" / "pricing" / "registry.json"

# Load existing registry
with open(registry_path, "r") as f:
    registry = json.load(f)

# Example: Add pricing for custom APIs
custom_pricing = {
    # Stripe payment processing
    "stripe:charges.create": {"per_call": 0.003},
    "stripe:subscriptions.create": {"per_call": 0.01},
    
    # Twilio SMS
    "twilio:messages.create": {"per_call": 0.0075},
    
    # Custom API examples
    "myapi:endpoint": {"per_call": 0.001},
    "myapi:token_based": {
        "input": 0.000001,   # per input token
        "output": 0.000002   # per output token
    },
    "myapi:per_million": {
        "per_million": 10.0  # $10 per million calls
    },
    "myapi:character_based": {
        "per_1k_chars": 0.015  # $0.015 per 1k characters
    },
    "myapi:duration_based": {
        "per_minute": 0.006  # $0.006 per minute
    }
}

# Merge with existing registry
registry.update(custom_pricing)

# Save updated registry
with open(registry_path, "w") as f:
    json.dump(registry, f, indent=2)

print("✅ Added custom API pricing!")
print(f"\nAdded {len(custom_pricing)} pricing entries:")
for key in custom_pricing.keys():
    print(f"  - {key}")

print("\n💡 Now any HTTP call to these APIs will be tracked!")
print("   Just use httpx/requests through the SDK and costs will be calculated.")

