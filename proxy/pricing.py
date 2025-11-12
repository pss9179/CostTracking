"""
Cost calculation for proxy.

Uses the same pricing registry as the collector.
"""
import json
import os
from typing import Dict, Any

# Load pricing registry
PRICING_REGISTRY = {}


def load_pricing_registry():
    """Load pricing registry from JSON file."""
    global PRICING_REGISTRY
    
    # Try to load from collector/pricing/registry.json
    registry_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "collector",
        "pricing",
        "registry.json"
    )
    
    try:
        with open(registry_path, "r") as f:
            PRICING_REGISTRY = json.load(f)
    except FileNotFoundError:
        # Fallback: load from environment or use defaults
        pass


# Load on module import
load_pricing_registry()


def calculate_cost(provider: str, usage: Dict[str, Any]) -> float:
    """
    Calculate cost from usage data.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        usage: Usage data dict with keys like model, input_tokens, output_tokens, etc.
    
    Returns:
        Cost in USD
    """
    model = usage.get("model")
    if not model:
        return 0.0
    
    pricing_key = f"{provider}:{model}"
    
    if pricing_key not in PRICING_REGISTRY:
        # Fallback: try without model
        pricing_key = provider
        if pricing_key not in PRICING_REGISTRY:
            return 0.0
    
    pricing = PRICING_REGISTRY[pricing_key]
    
    # Token-based (LLMs, embeddings)
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cached_tokens = usage.get("cached_tokens", 0)
    
    if input_tokens > 0 or output_tokens > 0:
        cost = 0.0
        
        if "input" in pricing:
            cost += input_tokens * pricing["input"]
        
        if "output" in pricing:
            cost += output_tokens * pricing["output"]
        
        if cached_tokens > 0 and "cached_input" in pricing:
            cost += cached_tokens * pricing["cached_input"]
        
        return cost
    
    # Character-based (TTS)
    character_count = usage.get("character_count", 0)
    if character_count > 0 and "per_1k_chars" in pricing:
        return (character_count / 1000) * pricing["per_1k_chars"]
    
    # Duration-based (STT, video)
    audio_seconds = usage.get("audio_seconds", 0.0)
    if audio_seconds > 0 and "per_minute" in pricing:
        return (audio_seconds / 60) * pricing["per_minute"]
    
    # Count-based (images, operations)
    image_count = usage.get("image_count", 0)
    if image_count > 0 and "per_image" in pricing:
        return image_count * pricing["per_image"]
    
    operation_count = usage.get("operation_count", 0)
    if operation_count > 0 and "per_million" in pricing:
        return (operation_count / 1_000_000) * pricing["per_million"]
    
    # Transaction-based (payments)
    transaction_amount = usage.get("transaction_amount", 0.0)
    if transaction_amount > 0 and "percentage" in pricing:
        return (transaction_amount * pricing["percentage"]) + pricing.get("fixed_fee", 0)
    
    return 0.0

