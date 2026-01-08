"""
Cost calculation for proxy.

Uses the same pricing registry as the collector.
"""
import json
import os
from typing import Dict, Any, Optional

# Load pricing registry
PRICING_REGISTRY = {}


def load_pricing_registry():
    """
    Load pricing registry from collector API (which reads from Supabase).
    Falls back to JSON file if API unavailable.
    """
    global PRICING_REGISTRY
    
    # Try to load from collector API (which reads from Supabase)
    collector_url = os.getenv("COLLECTOR_URL", "http://localhost:8000")
    try:
        import httpx
        response = httpx.get(f"{collector_url}/pricing/", timeout=5.0)
        if response.status_code == 200:
            PRICING_REGISTRY = response.json()
            print(f"[Proxy Pricing] Loaded {len(PRICING_REGISTRY)} pricing entries from collector API")
            return
    except Exception as e:
        print(f"[Proxy Pricing] Failed to load from API, trying JSON file: {e}")
    
    # Fallback: load from JSON file
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
            print(f"[Proxy Pricing] Loaded {len(PRICING_REGISTRY)} pricing entries from JSON file")
    except FileNotFoundError:
        print(f"[Proxy Pricing] JSON file not found, using empty registry")
        PRICING_REGISTRY = {}


# Load on module import
load_pricing_registry()


def get_tenant_tier(tenant_id: Optional[str], provider: str) -> Optional[str]:
    """
    Get the tier for a tenant/provider combination.
    Queries the collector API to get tier configuration.
    """
    if not tenant_id or tenant_id == "default_tenant":
        return None
    
    try:
        import httpx
        collector_url = os.getenv("COLLECTOR_URL", "http://localhost:8000")
        response = httpx.get(
            f"{collector_url}/provider-tiers/?tenant_id={tenant_id}",
            timeout=2.0
        )
        if response.status_code == 200:
            tiers = response.json()
            for tier_config in tiers:
                if tier_config.get("provider") == provider and tier_config.get("is_active"):
                    return tier_config.get("tier")
    except Exception:
        # Fail silently - fall back to default pricing
        pass
    
    return None


def calculate_cost(provider: str, usage: Dict[str, Any], endpoint: Optional[str] = None, tenant_id: Optional[str] = None) -> float:
    """
    Calculate cost from usage data.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic", "unknown", "openrouter")
        usage: Usage data dict with keys like model, input_tokens, output_tokens, etc.
        endpoint: Optional endpoint name (e.g., "charges.create", "messages.create")
    
    Returns:
        Cost in USD
    """
    model = usage.get("model")
    
    # For OpenRouter, extract the actual provider from model name
    # OpenRouter models are in format "provider/model-name" (e.g., "openai/gpt-4o")
    actual_provider = provider
    if provider == "openrouter" and model:
        # Extract provider from model name (e.g., "openai/gpt-4o" -> "openai")
        if "/" in model:
            actual_provider = model.split("/", 1)[0]
            # Normalize provider names
            provider_map = {
                "openai": "openai",
                "anthropic": "anthropic",
                "google": "google",
                "cohere": "cohere",
                "mistral": "mistral",
                "groq": "groq",
                "xai": "xai",
                "meta": "meta",
                "meta-llama": "meta",
                "perplexity": "perplexity",
                "together": "together",
                "deepseek": "deepseek",
                "01-ai": "01-ai",
            }
            actual_provider = provider_map.get(actual_provider.lower(), actual_provider.lower())
    
    # Get tenant tier if available
    tenant_tier = get_tenant_tier(tenant_id, actual_provider) if tenant_id else None
    
    # Try pricing lookup in order:
    # 1. provider:model:tier (tier-specific model pricing)
    # 2. provider:model (model pricing)
    # 3. provider:endpoint:tier (tier-specific endpoint pricing)
    # 4. provider:endpoint (endpoint pricing)
    # 5. provider:tier (tier-specific provider pricing)
    # 6. provider (fallback)
    
    pricing_key = None
    pricing = None
    
    # Use actual_provider for pricing lookup (not "openrouter")
    pricing_provider = actual_provider
    
    # Try tier-specific pricing first
    if tenant_tier:
        if model:
            pricing_key = f"{pricing_provider}:{model}:{tenant_tier}"
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
        
        if not pricing and endpoint:
            pricing_key = f"{pricing_provider}:{endpoint}:{tenant_tier}"
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
        
        if not pricing:
            pricing_key = f"{pricing_provider}:{tenant_tier}"
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
    
    # Fall back to non-tier-specific pricing
    if not pricing:
        if model:
            pricing_key = f"{pricing_provider}:{model}"
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
        
        # If no model or model-based pricing not found, try endpoint-based
        if not pricing and endpoint:
            pricing_key = f"{pricing_provider}:{endpoint}"
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
        
        # Fallback to provider-level pricing
        if not pricing:
            pricing_key = pricing_provider
            if pricing_key in PRICING_REGISTRY:
                pricing = PRICING_REGISTRY[pricing_key]
    
    if not pricing:
        return 0.0
    
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
    
    # Per-request (Perplexity) or per-call (custom APIs)
    cost = 0.0
    if "per_request" in pricing:
        cost += pricing["per_request"]
    elif "per_call" in pricing:
        cost += pricing["per_call"]
    
    # If we have per-call/per-request pricing, return it (don't check other metrics)
    if cost > 0:
        return cost
    
    # Per-second (Replicate, Runway)
    duration_seconds = usage.get("duration_seconds", 0.0)
    if duration_seconds > 0 and "per_second" in pricing:
        return duration_seconds * pricing["per_second"]
    
    # Per-minute (STT/Voice)
    audio_minutes = usage.get("audio_seconds", 0.0) / 60.0
    if audio_minutes > 0 and "per_minute" in pricing:
        return audio_minutes * pricing["per_minute"]
    
    # Per-character (TTS - already handled above via per_1k_chars)
    # Per million characters (AWS Polly)
    character_count = usage.get("character_count", 0)
    if character_count > 0 and "per_1m_chars" in pricing:
        return (character_count / 1_000_000) * pricing["per_1m_chars"]
    
    # Per 1k emails (SendGrid)
    email_count = usage.get("email_count", 0)
    if email_count > 0 and "per_1k_emails" in pricing:
        return (email_count / 1000) * pricing["per_1k_emails"]
    
    # Per 1k requests/records (Algolia)
    request_count = usage.get("request_count", 0)
    if request_count > 0:
        if "per_1k_requests" in pricing:
            return (request_count / 1000) * pricing["per_1k_requests"]
        elif "per_1k_records" in pricing:
            return (request_count / 1000) * pricing["per_1k_records"]
    
    # Per 1k images (AWS Rekognition)
    image_count = usage.get("image_count", 0)
    if image_count > 0 and "per_1k_images" in pricing:
        return (image_count / 1000) * pricing["per_1k_images"]
    
    # Per 1k tokens (HuggingFace)
    if "per_1k_tokens" in pricing and (input_tokens > 0 or output_tokens > 0):
        return ((input_tokens + output_tokens) / 1000) * pricing["per_1k_tokens"]
    
    # Storage-based pricing (Vector DBs, file storage)
    storage_gb = usage.get("storage_gb", 0.0)
    if storage_gb > 0:
        # Per GB per month (e.g., Pinecone storage)
        if "per_gb_month" in pricing:
            # Convert to per-day cost (approximate: divide by 30)
            return (storage_gb / 30.0) * pricing["per_gb_month"]
        # Per GB per day (e.g., OpenAI file storage)
        elif "per_gb_day" in pricing:
            return storage_gb * pricing["per_gb_day"]
        # One-time per GB (e.g., Pinecone import)
        elif "per_gb" in pricing:
            return storage_gb * pricing["per_gb"]
    
    return cost

