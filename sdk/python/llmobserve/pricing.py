"""
Pricing registry baked into SDK for client-side cost calculation.
Synced with collector/pricing/registry.json
"""
from typing import Dict, Any, Optional

# Baked-in pricing registry (matches collector) - Updated with latest OpenAI pricing
PRICING_REGISTRY: Dict[str, Any] = {
    # GPT-5 models
    "openai:gpt-5": {
        "input": 0.00000125,
        "output": 0.00001
    },
    "openai:gpt-5-mini": {
        "input": 0.00000025,
        "output": 0.000002
    },
    "openai:gpt-5-nano": {
        "input": 0.00000005,
        "output": 0.0000004
    },
    "openai:gpt-5-pro": {
        "input": 0.000015,
        "output": 0.00012
    },
    
    # GPT-4.1 models (fine-tunable)
    "openai:gpt-4.1": {
        "input": 0.000003,
        "output": 0.000012,
        "training": 0.000025
    },
    "openai:gpt-4.1-mini": {
        "input": 0.0000008,
        "output": 0.0000032,
        "training": 0.000005
    },
    "openai:gpt-4.1-nano": {
        "input": 0.0000002,
        "output": 0.0000008,
        "training": 0.0000015
    },
    "openai:o4-mini": {
        "input": 0.000004,
        "output": 0.000016,
        "training_per_hour": 100.0
    },
    
    # Realtime API (text)
    "openai:gpt-realtime": {
        "input": 0.000004,
        "output": 0.000016,
        "cached_input": 0.0000004
    },
    "openai:gpt-realtime-mini": {
        "input": 0.0000006,
        "output": 0.0000024,
        "cached_input": 0.00000006
    },
    
    # Realtime API (audio)
    "openai:gpt-realtime-audio": {
        "input": 0.000032,
        "output": 0.000064,
        "cached_input": 0.0000004
    },
    "openai:gpt-realtime-mini-audio": {
        "input": 0.00001,
        "output": 0.00002,
        "cached_input": 0.0000003
    },
    
    # Realtime API (image)
    "openai:gpt-realtime-image": {
        "input": 0.000005,
        "cached_input": 0.0000005
    },
    "openai:gpt-realtime-mini-image": {
        "input": 0.0000008,
        "cached_input": 0.00000008
    },
    
    # Sora video generation
    "openai:sora-2": {
        "per_second": 0.10
    },
    "openai:sora-2-pro-720": {
        "per_second": 0.30
    },
    "openai:sora-2-pro-1024": {
        "per_second": 0.50
    },
    
    # Image generation API
    "openai:gpt-image-1": {
        "input": 0.000005,
        "output": 0.00004,
        "cached_input": 0.00000125
    },
    "openai:gpt-image-1-mini": {
        "input": 0.0000025,
        "output": 0.000008,
        "cached_input": 0.0000002
    },
    
    # GPT-4 models (legacy)
    "openai:gpt-4o": {
        "input": 0.0000025,
        "output": 0.00001
    },
    "openai:gpt-4o-mini": {
        "input": 0.00000015,
        "output": 0.0000006
    },
    "openai:gpt-4-turbo": {
        "input": 0.00001,
        "output": 0.00003
    },
    "openai:gpt-4": {
        "input": 0.00003,
        "output": 0.00006
    },
    "openai:gpt-3.5-turbo": {
        "input": 0.0000005,
        "output": 0.0000015
    },
    
    # O1 models
    "openai:o1-preview": {
        "input": 0.000015,
        "output": 0.00006
    },
    "openai:o1-mini": {
        "input": 0.000003,
        "output": 0.000012
    },
    
    # Embeddings
    "openai:text-embedding-3-small": {
        "input": 0.00000002,
        "output": 0.0
    },
    "openai:text-embedding-3-large": {
        "input": 0.00000013,
        "output": 0.0
    },
    "openai:text-embedding-ada-002": {
        "input": 0.0000001,
        "output": 0.0
    },
    
    # Audio
    "openai:whisper-1": {
        "per_minute": 0.006
    },
    "openai:tts-1": {
        "per_character": 0.000015
    },
    "openai:tts-1-hd": {
        "per_character": 0.00003
    },
    
    # Images (DALL-E)
    "openai:dall-e-3": {
        "standard_1024": 0.040,
        "standard_1792": 0.080,
        "hd_1024": 0.080,
        "hd_1792": 0.120
    },
    "openai:dall-e-2": {
        "1024": 0.020,
        "512": 0.018,
        "256": 0.016
    },
    
    # Built-in tools
    "openai:code-interpreter": {
        "per_session": 0.03
    },
    "openai:file-search-storage": {
        "per_gb_day": 0.10
    },
    "openai:file-search-tool": {
        "per_1k_calls": 2.50
    },
    "openai:web-search-tool": {
        "per_1k_calls": 10.00
    },
    "openai:moderation": {
        "input": 0.0,
        "output": 0.0
    },
    "openai:vector-store-storage": {
        "per_gb_day": 0.10
    },
    
    # Other providers
    "anthropic:claude-3-opus": {
        "input": 0.000015,
        "output": 0.000075
    },
    "anthropic:claude-3-sonnet": {
        "input": 0.000003,
        "output": 0.000015
    },
    # Pinecone Database operations
    "pinecone:storage": {
        "per_gb_month": 0.33
    },
    "pinecone:write-units": {
        "per_million": 4.0,
        "per_million_enterprise": 6.0
    },
    "pinecone:read-units": {
        "per_million": 16.0,
        "per_million_enterprise": 24.0
    },
    "pinecone:query": {
        "per_million": 16.0,
        "per_million_enterprise": 24.0
    },
    "pinecone:upsert": {
        "per_million": 4.0,
        "per_million_enterprise": 6.0
    },
    "pinecone:delete": {
        "per_million": 4.0,
        "per_million_enterprise": 6.0
    },
    "pinecone:update": {
        "per_million": 4.0,
        "per_million_enterprise": 6.0
    },
    "pinecone:fetch": {
        "per_million": 16.0,
        "per_million_enterprise": 24.0
    },
    "pinecone:list": {
        "per_million": 16.0,
        "per_million_enterprise": 24.0
    },
    "pinecone:describe_index_stats": {
        "per_million": 16.0,
        "per_million_enterprise": 24.0
    },
    "pinecone:import-from-storage": {
        "per_gb": 1.0
    },
    "pinecone:backup": {
        "per_gb_month": 0.10
    },
    "pinecone:restore-from-backup": {
        "per_gb": 0.15
    },
    # Pinecone Inference - Embedding
    "pinecone:llama-text-embed-v2": {
        "per_million_tokens": 0.16
    },
    "pinecone:multilingual-e5-large": {
        "per_million_tokens": 0.08
    },
    "pinecone:pinecone-sparse-english-v0": {
        "per_million_tokens": 0.08
    },
    # Pinecone Inference - Reranking
    "pinecone:pinecone-rerank-v0": {
        "per_1k_requests": 2.0
    },
    "pinecone:bge-reranker-v2-m3": {
        "per_1k_requests": 2.0
    },
    "pinecone:cohere-rerank-v3.5": {
        "per_1k_requests": 2.0
    }
}


def compute_cost(
    provider: str,
    model: Optional[str],
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0
) -> float:
    """
    Compute cost for a given operation.
    
    Args:
        provider: Provider name (e.g., "openai", "pinecone")
        model: Model name (e.g., "gpt-5", None for per_call pricing)
        input_tokens: Number of input tokens (non-cached)
        output_tokens: Number of output tokens
        cached_tokens: Number of cached input tokens (OpenAI prompt caching)
    
    Returns:
        Cost in USD
    """
    # Build key
    if model:
        key = f"{provider}:{model}"
    else:
        key = provider
    
    pricing = PRICING_REGISTRY.get(key, {})
    
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
    # Handle cached tokens separately - they cost 10% of regular input
    regular_input_cost = pricing.get("input", 0.0) * input_tokens
    cached_input_cost = pricing.get("cached_input", pricing.get("input", 0.0) * 0.1) * cached_tokens
    output_cost = pricing.get("output", 0.0) * output_tokens
    
    return regular_input_cost + cached_input_cost + output_cost
