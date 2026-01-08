"""
Pricing registry baked into SDK for client-side cost calculation.
Synced with collector/pricing/registry.json
"""
from typing import Dict, Any, Optional

# Baked-in pricing registry (matches collector)
# Sources:
# - OpenAI: https://openai.com/api/pricing (verified Jan 2025)
# - Anthropic: https://www.anthropic.com/pricing (verified Jan 2025)
# - xAI: Pricing not publicly available - manual verification needed
PRICING_REGISTRY: Dict[str, Any] = {
    # GPT-5 models
    # Source: https://openai.com/api/pricing
    # Verified: Jan 2025
    "openai:gpt-5": {
        "input": 0.00000125,  # $1.25 per million tokens
        "output": 0.00001,  # $10.00 per million tokens
        "cached_input": 0.000000125  # $0.125 per million tokens (10% of input)
    },
    "openai:gpt-5-mini": {
        "input": 0.00000025,  # $0.25 per million tokens
        "output": 0.000002,  # $2.00 per million tokens
        "cached_input": 0.000000025  # $0.025 per million tokens (10% of input)
    },
    "openai:gpt-5-nano": {
        "input": 0.00000005,  # $0.05 per million tokens
        "output": 0.0000004,  # $0.40 per million tokens
        "cached_input": 0.000000005  # $0.005 per million tokens (10% of input)
    },
    "openai:gpt-5-pro": {
        "input": 0.000015,  # $15.00 per million tokens
        "output": 0.00012,  # $120.00 per million tokens
        "cached_input": 0.0000015  # $1.50 per million tokens (10% of input)
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
    # Source: https://openai.com/api/pricing
    # Verified: Jan 2025
    "openai:gpt-4o": {
        "input": 0.0000025,  # $2.50 per million tokens
        "output": 0.00001,  # $10.00 per million tokens
        "cached_input": 0.00000025  # $0.25 per million tokens (10% of input)
    },
    "openai:gpt-4o-mini": {
        "input": 0.00000015,  # $0.15 per million tokens
        "output": 0.0000006,  # $0.60 per million tokens
        "cached_input": 0.000000015  # $0.015 per million tokens (10% of input)
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
    
    # Anthropic Claude Models
    # Source: https://www.anthropic.com/pricing
    # Verified: Jan 2025
    # 
    # Key Pricing Notes:
    # - Opus 4.5 introduced significant price drop ($5/$25 vs $15/$75 for Opus 4.0/4.1)
    # - Opus 4.1+ models may charge separately for "thinking tokens" during extended reasoning
    # - Sonnet 4.5 doubles input cost ($6/million) for long-context (>200K tokens)
    # - Prompt caching: Read cache is ~10% of standard input price
    #
    # Claude 4.5 series (Latest - Released Nov 2025)
    "anthropic:claude-opus-4.5": {
        "input": 0.000005,  # $5.00 per million tokens - Latest flagship model (Nov 2025)
        "output": 0.000025,  # $25.00 per million tokens
        "cache_write": 0.00000625,  # $6.25 per million tokens (estimated)
        "cache_read": 0.0000005  # $0.50 per million tokens (~10% of input)
    },
    "anthropic:claude-sonnet-4.5": {
        "input": 0.000003,  # $3.00 per million tokens (≤200K tokens) - Most current Sonnet
        "input_extended": 0.000006,  # $6.00 per million tokens (>200K tokens) - Price doubles for long-context
        "output": 0.000015,  # $15.00 per million tokens (≤200K tokens)
        "output_extended": 0.00002250,  # $22.50 per million tokens (>200K tokens)
        "cache_write": 0.00000375,  # $3.75 per million tokens (≤200K)
        "cache_write_extended": 0.0000075,  # $7.50 per million tokens (>200K)
        "cache_read": 0.0000003,  # $0.30 per million tokens (≤200K) - ~10% of input
        "cache_read_extended": 0.0000006  # $0.60 per million tokens (>200K)
    },
    "anthropic:claude-haiku-4.5": {
        "input": 0.000001,  # $1.00 per million tokens
        "output": 0.000005,  # $5.00 per million tokens
        "cache_write": 0.00000125,  # $1.25 per million tokens
        "cache_read": 0.0000001  # $0.10 per million tokens (~10% of input)
    },
    
    # Claude 4.1 series
    # Note: Opus 4.1 introduced extended thinking tokens (may incur separate charges)
    "anthropic:claude-opus-4.1": {
        "input": 0.000015,  # $15.00 per million tokens - Premium pricing with extended thinking
        "output": 0.000075,  # $75.00 per million tokens
        "cache_write": 0.00001875,  # $18.75 per million tokens
        "cache_read": 0.0000015  # $1.50 per million tokens (~10% of input)
    },
    
    # Claude 4 series (Legacy - May 2025)
    "anthropic:claude-sonnet-4": {
        "input": 0.000003,  # $3.00 per million tokens - Standard mid-tier pricing
        "output": 0.000015,  # $15.00 per million tokens
        "cache_write": 0.00000375,  # $3.75 per million tokens
        "cache_read": 0.0000003  # $0.30 per million tokens (~10% of input)
    },
    "anthropic:claude-opus-4": {
        "input": 0.000015,  # $15.00 per million tokens - Legacy flagship (May 2025)
        "output": 0.000075,  # $75.00 per million tokens
        "cache_write": 0.00001875,  # $18.75 per million tokens
        "cache_read": 0.0000015  # $1.50 per million tokens (~10% of input)
    },
    
    # Claude 3.7 series (Deprecated)
    # Note: Replaced by Sonnet 4 family
    "anthropic:claude-sonnet-3.7": {
        "input": 0.000003,  # $3.00 per million tokens - Deprecated (replaced by Sonnet 4)
        "output": 0.000015,  # $15.00 per million tokens
        "cache_write": 0.00000375,  # $3.75 per million tokens
        "cache_read": 0.0000003  # $0.30 per million tokens (~10% of input)
    },
    
    # Claude 3.5 series
    # Source: https://www.anthropic.com/pricing
    # Verified: Jan 2025 - Claude 3.5 Sonnet: $3/$15 per million tokens
    # Verified: Jan 2025 - Claude 3.5 Haiku: $0.80/$4.00 per million tokens
    "anthropic:claude-haiku-3.5": {
        "input": 0.0000008,  # $0.80 per million tokens
        "output": 0.000004,  # $4.00 per million tokens
        "cache_write": 0.000001,  # $1.00 per million tokens
        "cache_read": 0.00000008  # $0.08 per million tokens
    },
    "anthropic:claude-3-5-sonnet-20241022": {
        "input": 0.000003,  # $3.00 per million tokens
        "output": 0.000015,  # $15.00 per million tokens
        "cache_write": 0.00000375,  # $3.75 per million tokens
        "cache_read": 0.0000003  # $0.30 per million tokens
    },
    
    # Claude 3 series (legacy)
    # Source: https://www.anthropic.com/pricing
    # Verified: Jan 2025
    "anthropic:claude-3-opus": {
        "input": 0.000015,  # $15.00 per million tokens
        "output": 0.000075,  # $75.00 per million tokens
        "cache_write": 0.00001875,  # $18.75 per million tokens
        "cache_read": 0.0000015  # $1.50 per million tokens
    },
    "anthropic:claude-3-sonnet": {
        "input": 0.000003,  # $3.00 per million tokens
        "output": 0.000015,  # $15.00 per million tokens
        "cache_write": 0.00000375,  # $3.75 per million tokens
        "cache_read": 0.0000003  # $0.30 per million tokens
    },
    "anthropic:claude-3-haiku": {
        "input": 0.00000025,  # $0.25 per million tokens
        "output": 0.00000125,  # $1.25 per million tokens
        "cache_write": 0.0000003,  # $0.30 per million tokens
        "cache_read": 0.00000003  # $0.03 per million tokens
    },
    
    # Anthropic Tools
    "anthropic:web-search": {
        "per_search": 0.01  # $10 per 1K searches
    },
    "anthropic:code-execution": {
        "per_hour_per_container": 0.05
    },
    
    # Google Gemini Models
    # Gemini 2.5 Pro
    "google:gemini-2.5-pro": {
        "input": 0.00000125,  # ≤200K context
        "input_extended": 0.0000025,  # >200K context
        "output": 0.00001,  # ≤200K
        "output_extended": 0.000015,  # >200K
        "cache": 0.000000125,  # ≤200K
        "cache_extended": 0.00000025,  # >200K
        "cache_storage_per_hour": 0.0000045
    },
    
    # Gemini 2.5 Flash
    "google:gemini-2.5-flash": {
        "input": 0.0000003,  # text/image/video
        "input_audio": 0.000001,
        "output": 0.0000025,
        "cache": 0.00000003,
        "cache_audio": 0.0000001,
        "cache_storage_per_hour": 0.000001
    },
    "google:gemini-2.5-flash-preview": {
        "input": 0.0000003,
        "input_audio": 0.000001,
        "output": 0.0000025,
        "cache": 0.00000003,
        "cache_audio": 0.0000001,
        "cache_storage_per_hour": 0.000001
    },
    
    # Gemini 2.5 Flash-Lite
    "google:gemini-2.5-flash-lite": {
        "input": 0.0000001,
        "input_audio": 0.0000003,
        "output": 0.0000004,
        "cache": 0.00000001,
        "cache_audio": 0.00000003,
        "cache_storage_per_hour": 0.000001
    },
    "google:gemini-2.5-flash-lite-preview": {
        "input": 0.0000001,
        "input_audio": 0.0000003,
        "output": 0.0000004,
        "cache": 0.00000001,
        "cache_audio": 0.00000003,
        "cache_storage_per_hour": 0.000001
    },
    
    # Gemini 2.5 Flash Native Audio (Live API)
    "google:gemini-2.5-flash-native-audio": {
        "input": 0.0000005,  # text
        "input_audio": 0.000003,  # audio/video
        "output": 0.000002,  # text
        "output_audio": 0.000012  # audio
    },
    
    # Gemini 2.5 Flash Half-Cascade
    "google:gemini-2.5-flash-half-cascade": {
        "input": 0.00000035,
        "input_audio": 0.0000021,
        "output": 0.0000015,
        "output_audio": 0.0000085
    },
    
    # Gemini 2.5 Flash Image
    "google:gemini-2.5-flash-image": {
        "input": 0.0000003,
        "output_per_image": 0.039
    },
    
    # Gemini 2.5 Flash TTS
    "google:gemini-2.5-flash-tts-preview": {
        "input": 0.0000005,
        "output_audio": 0.00001
    },
    "google:gemini-2.5-pro-tts-preview": {
        "input": 0.000001,
        "output_audio": 0.00002
    },
    
    # Gemini 2.0 Flash
    "google:gemini-2.0-flash": {
        "input": 0.0000001,
        "input_audio": 0.0000007,
        "output": 0.0000004,
        "cache": 0.000000025,
        "cache_audio": 0.000000175,
        "cache_storage_per_hour": 0.000001,
        "image_output": 0.039
    },
    "google:gemini-2.0-flash-lite": {
        "input": 0.000000075,
        "output": 0.0000003
    },
    
    # Gemini 2.5 Computer Use
    "google:gemini-2.5-computer-use": {
        "input": 0.00000125,
        "input_extended": 0.0000025,
        "output": 0.00001,
        "output_extended": 0.000015
    },
    
    # Gemini Robotics
    "google:gemini-robotics-er-1.5-preview": {
        "input": 0.0000003,
        "input_audio": 0.000001,
        "output": 0.0000025
    },
    
    # Gemini Embedding
    "google:gemini-embedding": {
        "input": 0.00000015,
        "output": 0.0
    },
    
    # Imagen Models
    "google:imagen-4-fast": {
        "per_image": 0.02
    },
    "google:imagen-4-standard": {
        "per_image": 0.04
    },
    "google:imagen-4-ultra": {
        "per_image": 0.06
    },
    "google:imagen-3": {
        "per_image": 0.03
    },
    
    # Veo Video Models
    "google:veo-3.1-standard": {
        "per_second": 0.40
    },
    "google:veo-3.1-fast": {
        "per_second": 0.15
    },
    "google:veo-3-standard": {
        "per_second": 0.40
    },
    "google:veo-3-fast": {
        "per_second": 0.15
    },
    "google:veo-2": {
        "per_second": 0.35
    },
    
    # Google Tools
    "google:search-grounding": {
        "free_daily": 1500,
        "per_1k_prompts": 35.0
    },
    "google:maps-grounding": {
        "free_daily": 1500,
        "per_1k_prompts": 25.0
    },
    "google:code-execution": {
        "per_call": 0.0  # Free
    },
    "google:file-search": {
        "input": 0.00000015  # Charged as embeddings
    },
    
    # Mistral Models
    # Text Generation - Premium Models
    "mistral:mistral-medium-latest": {
        "input": 0.0000004,
        "output": 0.000002
    },
    "mistral:magistral-medium-latest": {
        "input": 0.000002,
        "output": 0.000005
    },
    "mistral:devstral-medium-2507": {
        "input": 0.0000004,
        "output": 0.000002
    },
    "mistral:mistral-large-latest": {
        "input": 0.000002,
        "output": 0.000006,
        "training": 0.000009,
        "storage_per_month": 4.0
    },
    
    # Text Generation - Small Models
    "mistral:mistral-small-latest": {
        "input": 0.0000001,
        "output": 0.0000003,
        "training": 0.000004,
        "storage_per_month": 2.0
    },
    "mistral:magistral-small-latest": {
        "input": 0.0000005,
        "output": 0.0000015
    },
    "mistral:devstral-small-2507": {
        "input": 0.0000001,
        "output": 0.0000003
    },
    
    # Codestral (Coding Models)
    "mistral:codestral-latest": {
        "input": 0.0000003,
        "output": 0.0000009,
        "training": 0.000003,
        "storage_per_month": 2.0
    },
    "mistral:codestral-fine-tuned": {
        "input": 0.0000002,
        "output": 0.0000006
    },
    
    # Vision Models
    "mistral:pixtral-large-latest": {
        "input": 0.000002,
        "output": 0.000006
    },
    "mistral:pixtral-12b": {
        "input": 0.00000015,
        "output": 0.00000015,
        "training": 0.000002,
        "storage_per_month": 2.0
    },
    
    # Open Source Models
    "mistral:open-mistral-nemo": {
        "input": 0.00000015,
        "output": 0.00000015,
        "training": 0.000001,
        "storage_per_month": 2.0
    },
    "mistral:open-mistral-7b": {
        "input": 0.00000025,
        "output": 0.00000025
    },
    "mistral:open-mixtral-8x7b": {
        "input": 0.0000007,
        "output": 0.0000007
    },
    "mistral:open-mixtral-8x22b": {
        "input": 0.000002,
        "output": 0.000006
    },
    "mistral:ministral-8b-latest": {
        "input": 0.0000001,
        "output": 0.0000001
    },
    "mistral:ministral-3b-latest": {
        "input": 0.00000004,
        "output": 0.00000004
    },
    
    # Audio/Speech Models
    "mistral:voxtral-small-latest": {
        "input": 0.0000001,  # text
        "input_audio_per_minute": 0.004,
        "output": 0.0000003
    },
    "mistral:voxtral-mini-latest": {
        "input": 0.00000004,  # text
        "input_audio_per_minute": 0.001,
        "output": 0.00000004
    },
    "mistral:voxtral-mini-transcribe": {
        "input_audio_per_minute": 0.002
    },
    
    # Document AI
    "mistral:mistral-ocr-latest": {
        "per_1k_pages": 1.0,
        "per_1k_annotations": 3.0
    },
    
    # Embeddings
    "mistral:mistral-embed": {
        "input": 0.0000001,
        "output": 0.0
    },
    "mistral:codestral-embed-2505": {
        "input": 0.00000015,
        "output": 0.0
    },
    
    # Classification & Moderation
    "mistral:classifier-8b": {
        "input": 0.0000001,
        "output": 0.0000001,
        "training": 0.000001,
        "storage_per_month": 2.0
    },
    "mistral:classifier-3b": {
        "input": 0.00000004,
        "output": 0.00000004,
        "training": 0.000001,
        "storage_per_month": 2.0
    },
    "mistral:mistral-moderation-24.11": {
        "input": 0.0000001,
        "output": 0.0
    },
    
    # Mistral Tools
    "mistral:connectors": {
        "per_call": 0.01
    },
    "mistral:enterprise-search-indexing": {
        "input": 0.000006,
        "storage": 0.00000004
    },
    "mistral:code-execution": {
        "per_1k_calls": 30.0
    },
    "mistral:web-search": {
        "per_1k_calls": 30.0
    },
    "mistral:image-generation": {
        "per_1k_images": 100.0
    },
    "mistral:premium-news": {
        "per_1k_calls": 50.0
    },
    "mistral:data-capture": {
        "input": 0.00000004
    },
    
    # Perplexity Models
    # Search API (not token-based, request-based only)
    "perplexity:search-api": {
        "per_1k_requests": 5.0
    },
    
    # Sonar (token cost + request fee by context size)
    "perplexity:sonar": {
        "input": 0.000001,
        "output": 0.000001,
        "request_low_per_1k": 5.0,
        "request_medium_per_1k": 8.0,
        "request_high_per_1k": 12.0
    },
    
    # Sonar Pro
    "perplexity:sonar-pro": {
        "input": 0.000003,
        "output": 0.000015,
        "request_low_per_1k": 6.0,
        "request_medium_per_1k": 10.0,
        "request_high_per_1k": 14.0
    },
    
    # Sonar Reasoning
    "perplexity:sonar-reasoning": {
        "input": 0.000001,
        "output": 0.000005,
        "request_low_per_1k": 5.0,
        "request_medium_per_1k": 8.0,
        "request_high_per_1k": 12.0
    },
    
    # Sonar Reasoning Pro
    "perplexity:sonar-reasoning-pro": {
        "input": 0.000002,
        "output": 0.000008,
        "request_low_per_1k": 6.0,
        "request_medium_per_1k": 10.0,
        "request_high_per_1k": 14.0
    },
    
    # Sonar Deep Research (complex pricing with multiple components)
    "perplexity:sonar-deep-research": {
        "input": 0.000002,
        "output": 0.000008,
        "citation": 0.000002,
        "reasoning": 0.000003,
        "search_queries_per_1k": 5.0
        # Note: No per-request fees for Deep Research
    },
    
    # xAI / Grok Models
    # Source: https://x.ai/api/ (verified Jan 2025)
    # 
    # Key Pricing Notes:
    # - Grok-3 competes directly with Claude Sonnet pricing ($3/$15)
    # - Grok-Code-Fast-1 offers cached input as low as $0.02 per million tokens
    # - Prompt caching available for significant cost savings
    #
    # Language Models
    "xai:grok-code-fast-1": {
        "input": 0.0000002,  # $0.20 per million tokens - Optimized for agentic coding
        "output": 0.0000015,  # $1.50 per million tokens - 256K context window
        "cached_input": 0.00000002  # $0.02 per million tokens - Significant caching discount
    },
    "xai:grok-4-fast-reasoning": {
        "input": 0.0000002,  # $0.20 per million tokens
        "output": 0.0000005  # $0.50 per million tokens
    },
    "xai:grok-4-fast-non-reasoning": {
        "input": 0.0000002,  # $0.20 per million tokens
        "output": 0.0000005  # $0.50 per million tokens
    },
    "xai:grok-4-0709": {
        "input": 0.000003,  # $3.00 per million tokens
        "output": 0.000015  # $15.00 per million tokens
    },
    "xai:grok-4": {
        "input": 0.000003,  # $3.00 per million tokens
        "output": 0.000015  # $15.00 per million tokens
    },
    "xai:grok-3-mini": {
        "input": 0.0000003,  # $0.30 per million tokens - Ultra-low cost reasoning model
        "output": 0.0000005  # $0.50 per million tokens
    },
    "xai:grok-3": {
        "input": 0.000003,  # $3.00 per million tokens - Competes with Claude Sonnet pricing
        "output": 0.000015  # $15.00 per million tokens
    },
    "xai:grok-2-vision": {
        "input": 0.000002,
        "output": 0.00001
    },
    "xai:grok-2-vision-us": {
        "input": 0.000002,
        "output": 0.00001
    },
    "xai:grok-2-vision-eu": {
        "input": 0.000002,
        "output": 0.00001
    },
    
    # Image Generation
    "xai:grok-2-image-1212": {
        "per_image": 0.07
    },
    
    # xAI Tools (effective after Nov 21, 2025)
    "xai:web-search": {
        "per_1k_calls": 10.0
    },
    "xai:x-search": {
        "per_1k_calls": 10.0
    },
    "xai:code-execution": {
        "per_1k_calls": 10.0
    },
    "xai:document-search": {
        "per_1k_calls": 10.0
    },
    "xai:collections-search": {
        "per_1k_calls": 2.5
    },
    # View Image, View X Video, Remote MCP Tools are token-based only (no invocation fee)
    
    # Live Search (deprecated by Dec 15, 2025)
    "xai:live-search": {
        "per_1k_sources": 25.0
    },
    
    # Collections API
    "xai:collections-api": {
        "per_1k_requests": 2.5
    },
    
    # Usage Guidelines Violation Fee
    "xai:violation-fee": {
        "per_request": 0.05
    },
    
    # Cohere Models
    # Command A
    "cohere:command-a": {
        "input": 0.0000025,
        "output": 0.00001
    },
    
    # Command R Series
    "cohere:command-r": {
        "input": 0.00000015,
        "output": 0.0000006
    },
    "cohere:command-r7b": {
        "input": 0.00000003750,
        "output": 0.00000015
    },
    "cohere:command-r-plus": {
        "input": 0.0000025,  # Latest (08-2024)
        "output": 0.00001
    },
    
    # Legacy Command models
    "cohere:command": {
        "input": 0.000001,
        "output": 0.000002
    },
    "cohere:command-light": {
        "input": 0.0000003,
        "output": 0.0000006
    },
    "cohere:command-r-03-2024": {
        "input": 0.0000005,
        "output": 0.0000015
    },
    "cohere:command-r-plus-04-2024": {
        "input": 0.000003,
        "output": 0.000015
    },
    
    # Aya Expanse (Research Models)
    "cohere:aya-expanse-8b": {
        "input": 0.0000005,
        "output": 0.0000015
    },
    "cohere:aya-expanse-32b": {
        "input": 0.0000005,
        "output": 0.0000015
    },
    
    # Embeddings
    "cohere:embed-4": {
        "input": 0.00000012,  # Text
        "output": 0.0
    },
    "cohere:embed-4-image": {
        "input": 0.00000047,  # Image embeddings
        "output": 0.0
    },
    
    # Rerank
    "cohere:rerank-3.5": {
        "per_1k_searches": 2.0
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
    },
    
    # Weaviate Cloud Service (WCS)
    # Pricing by vector dimensions (vectors × dimensions)
    "weaviate:flex-vector-dimensions": {
        "per_million_dims": 0.000745  # Flex plan (pay-as-you-go)
    },
    "weaviate:plus-vector-dimensions": {
        "per_million_dims": 0.000327  # Plus plan (prepaid)
    },
    "weaviate:premium-vector-dimensions": {
        "per_million_dims": 0.000327  # Premium plan (prepaid)
    },
    "weaviate:flex-storage": {
        "per_gib_month": 0.255  # Flex storage
    },
    "weaviate:plus-storage": {
        "per_gib_month": 0.2125  # Plus storage
    },
    "weaviate:premium-storage": {
        "per_gib_month": 0.2125  # Premium storage
    },
    "weaviate:flex-backups": {
        "per_gib": 0.0264  # Flex backups
    },
    "weaviate:plus-backups": {
        "per_gib": 0.022  # Plus backups
    },
    "weaviate:premium-backups": {
        "per_gib": 0.022  # Premium backups
    },
    
    # Qdrant Cloud
    # Resource-based pricing (CPU, memory, disk)
    # Note: Pricing varies by configuration, use calculator for exact costs
    "qdrant:hybrid-cloud": {
        "per_hour": 0.014  # Starting price for small BYOC cluster
    },
    # Qdrant Managed Cloud is resource-based (CPU + memory + storage)
    # Users should use Qdrant's pricing calculator for accurate costs
    
    # Milvus / Zilliz Cloud
    "zilliz:storage-dedicated": {
        "per_gb_month": 99.0  # Dedicated storage
    },
    "zilliz:performance-cluster": {
        "per_million_vectors_month": 65.0  # Performance-optimized (500-1500 QPS)
    },
    "zilliz:capacity-cluster": {
        "per_million_vectors_month": 20.0  # Capacity-optimized
    },
    "zilliz:tiered-storage": {
        "per_million_vectors_month": 7.0  # Tiered storage
    },
    # Note: Zilliz uses vCUs (virtual compute units) for serverless
    # Free tier: 5 GB storage + 2.5M vCUs per month
    
    # Chroma Cloud
    "chroma:write": {
        "per_gib": 2.50  # Ingest/write cost
    },
    "chroma:storage": {
        "per_gib_month": 0.33  # Storage cost
    },
    "chroma:query-scan": {
        "per_tib": 0.0075  # Query scan cost
    },
    "chroma:query-return": {
        "per_gib": 0.09  # Data returned from query
    },
    # Starter plan: $0/mo with $5 free credits
    # Team plan: $250/mo with $100 included usage
    
    # MongoDB Atlas Vector Search
    # Pricing is based on Atlas cluster resources (no separate vector fees)
    "mongodb:m2-shared": {
        "per_month": 9.0  # M2 cluster (2GB)
    },
    "mongodb:m5-shared": {
        "per_month": 25.0  # M5 cluster (5GB)
    },
    "mongodb:m10-dedicated": {
        "per_hour": 0.08  # M10 (10GB, 2GB RAM) on AWS
    },
    # Note: Vector search uses existing Atlas cluster resources
    # Free M0 cluster available (512MB)
    
    # Redis Enterprise Cloud (Vector Search)
    # Pricing by RAM/CPU resources (no separate vector fees)
    "redis:flex-essentials": {
        "per_hour": 0.007  # Shared clusters (~$5/mo)
    },
    "redis:pro": {
        "per_hour": 0.014,  # Dedicated nodes
        "minimum_monthly": 200.0  # $200/mo minimum
    },
    # Free tier: 30 MB RAM included
    
    # Elasticsearch Vector Search
    # Pricing by VCU-hours or GB-hours (no separate vector fees)
    "elasticsearch:ingest-vcu": {
        "per_hour": 0.14  # Example: AWS us-east-1 ingest VCU
    }
    # Note: Elasticsearch is open-source (free to self-host)
    # Elastic Cloud charges by resource usage (VCU-hour or GB-hour)
}


def compute_cost(
    provider: str,
    model: Optional[str],
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
    context_size: Optional[str] = None,
    citation_tokens: int = 0,
    reasoning_tokens: int = 0,
    search_queries: int = 0
) -> float:
    """
    Compute cost for a given operation.
    
    Args:
        provider: Provider name (e.g., "openai", "pinecone")
        model: Model name (e.g., "gpt-5", None for per_call pricing)
        input_tokens: Number of input tokens (non-cached)
        output_tokens: Number of output tokens
        cached_tokens: Number of cached input tokens (OpenAI prompt caching)
        context_size: Context size tier for Perplexity models ("low", "medium", "high")
        citation_tokens: Number of citation tokens (Perplexity Deep Research)
        reasoning_tokens: Number of reasoning tokens (Perplexity Deep Research)
        search_queries: Number of search queries (Perplexity Deep Research)
    
    Returns:
        Cost in USD
    """
    # Build key with fallback for model name variations
    pricing = {}
    if model:
        # Try exact match first
        key = f"{provider}:{model}"
        pricing = PRICING_REGISTRY.get(key, {})
        
        # If not found and model has date suffix (e.g., "claude-3-haiku-20240307"),
        # try without the date suffix (e.g., "claude-3-haiku")
        if not pricing and "-" in model:
            # Try stripping date suffix (format: model-YYYYMMDD)
            import re
            # Match pattern like -20240307 at the end
            base_model = re.sub(r'-\d{8}$', '', model)
            if base_model != model:
                fallback_key = f"{provider}:{base_model}"
                pricing = PRICING_REGISTRY.get(fallback_key, {})
        
        # If still not found, try matching by model family
        if not pricing:
            # Extract model family (e.g., "claude-3-haiku" from "claude-3-haiku-20240307")
            parts = model.split("-")
            if len(parts) >= 3:
                # Try progressively shorter model names
                for i in range(len(parts), 2, -1):  # Start from full name, go down to first 3 parts
                    test_model = "-".join(parts[:i])
                    test_key = f"{provider}:{test_model}"
                    if test_key in PRICING_REGISTRY:
                        pricing = PRICING_REGISTRY[test_key]
                        break
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
    
    # Check for per_1k_searches pricing (Cohere Rerank)
    if "per_1k_searches" in pricing:
        return pricing["per_1k_searches"] / 1000
    
    # Check for per_1k_sources pricing (xAI Live Search)
    if "per_1k_sources" in pricing:
        return pricing["per_1k_sources"] / 1000
    
    # Check for per_image pricing (xAI, Google Imagen)
    if "per_image" in pricing:
        return pricing["per_image"]
    
    # Check for per_request pricing (xAI violation fee)
    if "per_request" in pricing:
        return pricing["per_request"]
    
    # Check for per_1k_pages pricing (Mistral OCR)
    if "per_1k_pages" in pricing:
        return pricing["per_1k_pages"] / 1000
    
    # Check for per_1k_annotations pricing (Mistral OCR)
    if "per_1k_annotations" in pricing:
        return pricing["per_1k_annotations"] / 1000
    
    # Check for per_1k_images pricing (Mistral Image Gen)
    if "per_1k_images" in pricing:
        return pricing["per_1k_images"] / 1000
    
    # Check for input_audio_per_minute pricing (Mistral, Google)
    if "input_audio_per_minute" in pricing:
        return pricing["input_audio_per_minute"]
    
    # Check for per_million_dims pricing (Weaviate vector dimensions)
    if "per_million_dims" in pricing:
        return pricing["per_million_dims"] / 1_000_000
    
    # Check for per_gib_month pricing (Weaviate, Chroma storage)
    if "per_gib_month" in pricing:
        return pricing["per_gib_month"]
    
    # Check for per_gib pricing (Weaviate backups, Chroma writes)
    if "per_gib" in pricing:
        return pricing["per_gib"]
    
    # Check for per_tib pricing (Chroma query scans)
    if "per_tib" in pricing:
        return pricing["per_tib"]
    
    # Check for per_million_vectors_month pricing (Zilliz clusters)
    if "per_million_vectors_month" in pricing:
        return pricing["per_million_vectors_month"] / 1_000_000
    
    # Check for per_month pricing (MongoDB Atlas)
    if "per_month" in pricing:
        return pricing["per_month"] / (30 * 24)  # Convert to hourly equivalent
    
    # Check for per_hour pricing (Qdrant, Redis, Elasticsearch, MongoDB)
    if "per_hour" in pricing:
        return pricing["per_hour"]
    
    # Token-based pricing (default)
    total_cost = 0.0
    
    # Handle cached tokens separately - they cost 10% of regular input (or explicit cached_input rate)
    regular_input_cost = pricing.get("input", 0.0) * input_tokens
    cached_input_cost = pricing.get("cached_input", pricing.get("input", 0.0) * 0.1) * cached_tokens
    output_cost = pricing.get("output", 0.0) * output_tokens
    
    total_cost += regular_input_cost + cached_input_cost + output_cost
    
    # Handle Perplexity-specific pricing
    # 1. Citation tokens (Deep Research)
    if citation_tokens > 0 and "citation" in pricing:
        total_cost += pricing["citation"] * citation_tokens
    
    # 2. Reasoning tokens (Deep Research)
    if reasoning_tokens > 0 and "reasoning" in pricing:
        total_cost += pricing["reasoning"] * reasoning_tokens
    
    # 3. Search queries (Deep Research)
    if search_queries > 0 and "search_queries_per_1k" in pricing:
        total_cost += (pricing["search_queries_per_1k"] / 1000) * search_queries
    
    # 4. Request-based fees (Sonar models with context size)
    if context_size and provider == "perplexity":
        context_key = f"request_{context_size}_per_1k"
        if context_key in pricing:
            total_cost += pricing[context_key] / 1000  # Convert to per-request cost
    
    return total_cost
