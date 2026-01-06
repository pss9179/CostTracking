"""
Pricing utilities for computing costs from usage data.
Loads pricing from Supabase database (falls back to JSON file if DB unavailable).
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from sqlmodel import Session, select
from db import SessionLocal
from models import Pricing

# Load pricing registry
PRICING_FILE = Path(__file__).parent / "pricing" / "registry.json"

# Cache for pricing registry (loaded from DB)
_PRICING_CACHE: Optional[Dict[str, Any]] = None


def load_pricing_registry() -> Dict[str, Any]:
    """
    Load pricing registry from Supabase database.
    Falls back to JSON file if database is unavailable.
    """
    global _PRICING_CACHE
    
    # Return cached version if available
    if _PRICING_CACHE is not None:
        return _PRICING_CACHE
    
    try:
        # Try to load from database
        session = SessionLocal()
        try:
            statement = select(Pricing).where(Pricing.is_active == True)
            pricing_entries = session.exec(statement).all()
            
            registry = {}
            for entry in pricing_entries:
                # Build key: "provider:model" or "provider"
                if entry.model:
                    key = f"{entry.provider}:{entry.model}"
                else:
                    key = entry.provider
                
                # Convert pricing_data dict to JSON-compatible format
                registry[key] = entry.pricing_data
            
            _PRICING_CACHE = registry
            print(f"[Pricing] Loaded {len(registry)} pricing entries from database")
            return registry
            
        finally:
            session.close()
            
    except Exception as e:
        # Fallback to JSON file
        print(f"[Pricing] Database unavailable, falling back to JSON file: {e}")
        try:
            with open(PRICING_FILE, "r") as f:
                registry = json.load(f)
                _PRICING_CACHE = registry
                return registry
        except FileNotFoundError:
            print(f"[Pricing] JSON file not found, returning empty registry")
            return {}


def save_pricing_registry(registry: Dict[str, Any]) -> None:
    """
    Save pricing registry.
    Note: This saves to JSON file for backward compatibility.
    To add pricing to database, use SQL INSERT or the migration script.
    """
    with open(PRICING_FILE, "w") as f:
        json.dump(registry, f, indent=2)
    
    # Clear cache so next load picks up changes
    global _PRICING_CACHE
    _PRICING_CACHE = None


def clear_pricing_cache():
    """Clear pricing cache to force reload from database."""
    global _PRICING_CACHE
    _PRICING_CACHE = None


def normalize_provider(provider: str) -> str:
    """Normalize provider name for pricing lookup."""
    provider = provider.lower().strip()
    
    # Provider name mappings
    mappings = {
        "meta-llama": "meta",
        "mistralai": "mistral",
        "nousresearch": "nous",
        "perplexity": "perplexity",
        "togethercomputer": "together",
        "01-ai": "yi",
        "databricks": "databricks",
        "amazon": "amazon",
        "tiiuae": "tiiuae",
        "cognitivecomputations": "cognitive",
    }
    
    return mappings.get(provider, provider)


def normalize_model(model: str) -> str:
    """Normalize model name for pricing lookup."""
    import re
    model = model.lower().strip()
    
    # Remove date suffixes (e.g., -20240307)
    model = re.sub(r'-\d{8}$', '', model)
    
    # NOTE: Don't remove -v1/-v2 suffixes globally as some models like
    # Amazon Nova use them as part of the actual model name (nova-pro-v1)
    # These are handled by trying exact match first in compute_cost()
    
    # Normalize common model name patterns
    normalizations = {
        # Llama variants
        r'llama-3\.1-(\d+)b-instruct': r'llama-3.1-\1b',
        r'llama-3\.2-(\d+)b-instruct': r'llama-3.2-\1b',
        r'llama-3-(\d+)b-instruct': r'llama-3-\1b',
        # Mistral variants  
        r'mistral-(\d+)b-instruct.*': r'mistral-\1b',
        r'mixtral-8x(\d+)b-instruct.*': r'mixtral-8x\1b',
        # DeepSeek
        r'deepseek-chat.*': 'deepseek-chat',
        r'deepseek-coder.*': 'deepseek-coder',
        r'deepseek-r1.*': 'deepseek-r1',
        # Qwen
        r'qwen-2\.5-(\d+)b-instruct': r'qwen-2.5-\1b',
        r'qwen-2-(\d+)b-instruct': r'qwen-2-\1b',
        # Claude
        r'claude-3\.5-sonnet.*': 'claude-3.5-sonnet',
        r'claude-3-5-sonnet.*': 'claude-3.5-sonnet',
        r'claude-3-haiku.*': 'claude-3-haiku',
        r'claude-3-5-haiku.*': 'claude-3.5-haiku',
        r'claude-3\.5-haiku.*': 'claude-3.5-haiku',
        # Gemini
        r'gemini-flash-1\.5.*': 'gemini-1.5-flash',
        r'gemini-pro-1\.5.*': 'gemini-1.5-pro',
        r'gemini-2\.0-flash.*': 'gemini-2.0-flash',
    }
    
    for pattern, replacement in normalizations.items():
        normalized = re.sub(pattern, replacement, model)
        if normalized != model:
            return normalized
    
    return model


def compute_cost(
    provider: str,
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    registry: Optional[Dict[str, Any]] = None
) -> float:
    """
    Compute cost for a given operation.
    
    Args:
        provider: Provider name (e.g., "openai", "pinecone")
        model: Model name (e.g., "gpt-4o", None for per_call pricing)
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        registry: Optional pricing registry (loads from file if not provided)
    
    Returns:
        Cost in USD
    """
    if registry is None:
        registry = load_pricing_registry()
    
    # Store originals for fallback attempts
    original_provider = provider.lower().strip()
    original_model = model.lower().strip() if model else None
    
    # Normalize provider and model names
    normalized_provider = normalize_provider(original_provider)
    normalized_model = normalize_model(original_model) if original_model else None
    
    # Build key with fallback for model name variations
    pricing = {}
    if original_model:
        # 1. Try exact match with original names first
        key = f"{original_provider}:{original_model}"
        pricing = registry.get(key, {})
        
        # 2. Try with normalized provider but original model
        if not pricing:
            key = f"{normalized_provider}:{original_model}"
            pricing = registry.get(key, {})
        
        # 3. Try with original provider but normalized model
        if not pricing:
            key = f"{original_provider}:{normalized_model}"
            pricing = registry.get(key, {})
        
        # 4. Try fully normalized
        if not pricing:
            key = f"{normalized_provider}:{normalized_model}"
            pricing = registry.get(key, {})
        
        # 5. If still not found, try matching by model family (progressively shorter names)
        if not pricing and original_model and "-" in original_model:
            parts = original_model.split("-")
            if len(parts) >= 3:
                for i in range(len(parts) - 1, 2, -1):  # Start from full name minus 1, go down
                    test_model = "-".join(parts[:i])
                    # Try with both providers
                    for prov in [original_provider, normalized_provider]:
                        test_key = f"{prov}:{test_model}"
                        if test_key in registry:
                            pricing = registry[test_key]
                            break
                    if pricing:
                        break
    else:
        # No model, try provider-level pricing
        key = f"{original_provider}"
        pricing = registry.get(key, {})
        if not pricing:
            key = f"{normalized_provider}"
            pricing = registry.get(key, {})
    
    # Check for per_call pricing
    if "per_call" in pricing:
        return pricing["per_call"]
    
    # Check for per_million pricing (Pinecone read/write units)
    if "per_million" in pricing:
        # Use standard pricing by default (not enterprise)
        return pricing["per_million"] / 1_000_000  # Convert to per-call cost
    
    # Check for per_million_tokens pricing (Pinecone embedding models)
    if "per_million_tokens" in pricing:
        total_tokens = input_tokens + output_tokens
        return (pricing["per_million_tokens"] / 1_000_000) * total_tokens
    
    # Check for per_1k_requests pricing (Pinecone reranking)
    if "per_1k_requests" in pricing:
        return pricing["per_1k_requests"] / 1000  # Convert to per-request cost
    
    # Check for per_gb pricing (Pinecone storage operations)
    if "per_gb" in pricing:
        return pricing["per_gb"]
    
    # Check for per_gb_month pricing (Pinecone storage)
    if "per_gb_month" in pricing:
        return pricing["per_gb_month"]
    
    # Check for per_minute pricing (audio)
    if "per_minute" in pricing:
        return pricing["per_minute"]
    
    # Check for per_character pricing (TTS)
    if "per_character" in pricing:
        return pricing["per_character"]
    
    # Check for per_second pricing (Sora)
    if "per_second" in pricing:
        return pricing["per_second"]
    
    # Check for per_session pricing (Code Interpreter)
    if "per_session" in pricing:
        return pricing["per_session"]
    
    # Check for per_gb_day pricing (File Search Storage)
    if "per_gb_day" in pricing:
        return pricing["per_gb_day"]
    
    # Check for per_1k_calls pricing (Tools)
    if "per_1k_calls" in pricing:
        return pricing["per_1k_calls"] / 1000
    
    # Token-based pricing (default)
    input_cost = pricing.get("input", 0.0) * input_tokens
    output_cost = pricing.get("output", 0.0) * output_tokens
    
    return input_cost + output_cost

