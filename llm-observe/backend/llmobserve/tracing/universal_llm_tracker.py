"""
Universal async cost-tracking wrapper for any LLM provider with streaming support.

This module provides a single function `track_llm_call()` that automatically:
- Detects provider and streaming support
- Tracks tokens and costs for any LLM call
- Handles streaming responses with proper buffering
- Falls back to token estimation when usage data is unavailable
- Guarantees cost logging even on errors or broken streams
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

# Versioned pricing table (updated as needed)
PRICING = {
    "version": "2025-01-15",
    "default": {"prompt": 0.005, "completion": 0.015},  # per 1K tokens
    "openai": {
        "gpt-4o": {"prompt": 0.0025, "completion": 0.010},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4-turbo": {"prompt": 0.010, "completion": 0.030},
        "gpt-4": {"prompt": 0.030, "completion": 0.060},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    },
    "mistral": {
        "mistral-large": {"prompt": 0.002, "completion": 0.006},
        "mistral-medium": {"prompt": 0.0027, "completion": 0.0081},
        "mistral-small": {"prompt": 0.0002, "completion": 0.0006},
    },
    "cohere": {
        "command-r-plus": {"prompt": 0.003, "completion": 0.015},
        "command-r": {"prompt": 0.0005, "completion": 0.0015},
    },
    "gemini": {
        "gemini-1.5-pro": {"prompt": 0.00125, "completion": 0.005},
        "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
    },
    "together": {
        "meta-llama/Llama-2-70b-chat-hf": {"prompt": 0.0007, "completion": 0.0007},
    },
}


def _get_pricing(provider: str, model: str) -> Dict[str, float]:
    """
    Get pricing for a specific provider/model, falling back to defaults.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic")
        model: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet")
    
    Returns:
        Dict with "prompt" and "completion" prices per 1K tokens
    """
    provider_pricing = PRICING.get(provider.lower(), {})
    model_pricing = provider_pricing.get(model, None)
    
    if model_pricing:
        return model_pricing
    
    # Fallback to default pricing
    return PRICING["default"]


def _estimate_tokens_fallback(text: str) -> int:
    """
    Fallback token estimator when tiktoken is unavailable.
    
    Uses a simple word-based approximation: ~1.3 tokens per word.
    This is less accurate than tiktoken but works for any string.
    
    Args:
        text: Input text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Simple word count approximation
    words = len(text.split())
    # Average English: ~1.3 tokens per word
    return int(words * 1.3)


def _estimate_tokens(text: str, model: Optional[str] = None) -> int:
    """
    Estimate token count for text using tiktoken if available, else fallback.
    
    Args:
        text: Input text
        model: Optional model name for tiktoken encoding selection
    
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    
    # Try tiktoken first (most accurate)
    if TIKTOKEN_AVAILABLE:
        try:
            # Map common models to tiktoken encodings
            encoding_map = {
                "gpt-4o": "o200k_base",
                "gpt-4o-mini": "o200k_base",
                "gpt-4-turbo": "cl100k_base",
                "gpt-4": "cl100k_base",
                "gpt-3.5-turbo": "cl100k_base",
            }
            
            encoding_name = encoding_map.get(model, "cl100k_base")
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # If tiktoken fails, fall back to word-based estimation
            pass
    
    # Fallback to word-based estimation
    return _estimate_tokens_fallback(text)


def _extract_usage_from_response(response: Any) -> Optional[Dict[str, int]]:
    """
    Extract token usage from various response formats.
    
    Handles different provider response structures:
    - OpenAI: response.usage.prompt_tokens, response.usage.completion_tokens
    - Anthropic: response.usage.input_tokens, response.usage.output_tokens
    - Generic: response.usage dict or response.token_count dict
    
    Args:
        response: API response object
    
    Returns:
        Dict with "prompt_tokens" and "completion_tokens", or None if unavailable
    """
    if not response:
        return None
    
    usage = None
    
    # Try common usage attribute patterns
    if hasattr(response, "usage"):
        usage = response.usage
    elif hasattr(response, "token_count"):
        usage = response.token_count
    elif isinstance(response, dict):
        usage = response.get("usage") or response.get("token_count")
    
    if not usage:
        return None
    
    # Normalize different provider formats
    prompt_tokens = 0
    completion_tokens = 0
    
    if isinstance(usage, dict):
        # Dict format: check common key names
        prompt_tokens = (
            usage.get("prompt_tokens") or
            usage.get("input_tokens") or
            usage.get("prompt") or
            0
        )
        completion_tokens = (
            usage.get("completion_tokens") or
            usage.get("output_tokens") or
            usage.get("completion") or
            0
        )
    elif hasattr(usage, "prompt_tokens"):
        # Object with prompt_tokens attribute (OpenAI style)
        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
    elif hasattr(usage, "input_tokens"):
        # Object with input_tokens attribute (Anthropic style)
        prompt_tokens = getattr(usage, "input_tokens", 0)
        completion_tokens = getattr(usage, "output_tokens", 0)
    
    if prompt_tokens == 0 and completion_tokens == 0:
        return None
    
    return {
        "prompt_tokens": int(prompt_tokens),
        "completion_tokens": int(completion_tokens),
    }


def _detect_streaming_support(provider: str, client: Any) -> bool:
    """
    Detect if provider supports streaming by checking client methods.
    
    Checks for common streaming patterns:
    - stream=True parameter support
    - .stream() or .create_stream() methods
    - Presence of streaming-related attributes
    
    Args:
        provider: Provider name
        client: Provider client instance
    
    Returns:
        True if streaming appears supported, False otherwise
    """
    if not client:
        return False
    
    # Check for streaming methods
    if hasattr(client, "stream") or hasattr(client, "create_stream"):
        return True
    
    # Check for chat.completions with stream support (OpenAI pattern)
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        if hasattr(client.chat.completions, "create"):
            # Most providers that support streaming accept stream=True
            return True
    
    # Check for messages.create with stream support (Anthropic pattern)
    if hasattr(client, "messages") and hasattr(client.messages, "create"):
        return True
    
    # Default: assume streaming is supported (most modern providers do)
    # The actual call will handle errors gracefully
    return True


async def _call_with_streaming(
    provider: str,
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    **kwargs
) -> Tuple[Any, str]:
    """
    Execute streaming LLM call and buffer all chunks.
    
    Handles different provider streaming patterns:
    - OpenAI: client.chat.completions.create(stream=True)
    - Anthropic: client.messages.create(stream=True)
    - Generic: client.create_stream() or similar
    
    Args:
        provider: Provider name
        client: Provider client instance
        model: Model identifier
        messages: List of message dicts
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Tuple of (response_object, full_output_text)
    """
    full_output = ""
    stream_chunks = []
    
    try:
        # Try OpenAI-style streaming
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        full_output += delta.content
                stream_chunks.append(chunk)
            return stream_chunks, full_output
        
        # Try Anthropic-style streaming
        elif hasattr(client, "messages"):
            stream = await client.messages.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                if hasattr(chunk, "delta") and hasattr(chunk.delta, "text"):
                    full_output += chunk.delta.text
                elif hasattr(chunk, "text"):
                    full_output += chunk.text
                stream_chunks.append(chunk)
            return stream_chunks, full_output
        
        # Try generic stream() method
        elif hasattr(client, "stream"):
            stream = await client.stream(model=model, messages=messages, **kwargs)
            async for chunk in stream:
                if isinstance(chunk, str):
                    full_output += chunk
                elif hasattr(chunk, "content"):
                    full_output += getattr(chunk, "content", "")
                stream_chunks.append(chunk)
            return stream_chunks, full_output
        
        # Fallback: try stream=True in create method
        else:
            # This will likely fail, but we'll catch it
            response = await client.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )
            async for chunk in response:
                if isinstance(chunk, str):
                    full_output += chunk
                stream_chunks.append(chunk)
            return stream_chunks, full_output
            
    except Exception as e:
        # If streaming fails, return what we have so far
        # This ensures partial cost tracking even on broken streams
        return stream_chunks, full_output


async def _call_without_streaming(
    provider: str,
    client: Any,
    model: str,
    messages: List[Dict[str, str]],
    **kwargs
) -> Any:
    """
    Execute non-streaming LLM call.
    
    Handles different provider patterns:
    - OpenAI: client.chat.completions.create()
    - Anthropic: client.messages.create()
    - Generic: client.create() or client.generate()
    
    Args:
        provider: Provider name
        client: Provider client instance
        model: Model identifier
        messages: List of message dicts
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Response object
    """
    # Try OpenAI-style
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return await client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
    
    # Try Anthropic-style
    elif hasattr(client, "messages"):
        return await client.messages.create(
            model=model,
            messages=messages,
            **kwargs
        )
    
    # Try generic create()
    elif hasattr(client, "create"):
        return await client.create(
            model=model,
            messages=messages,
            **kwargs
        )
    
    # Try generate() (Cohere pattern)
    elif hasattr(client, "generate"):
        return await client.generate(
            model=model,
            prompt=messages[-1]["content"] if messages else "",
            **kwargs
        )
    
    else:
        raise ValueError(f"Unsupported provider client pattern: {provider}")


async def track_llm_call(
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    client: Any,
    stream: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Universal async cost-tracking wrapper for any LLM provider with streaming support.
    
    Automatically detects provider capabilities, handles streaming, calculates costs,
    and guarantees cost logging even on errors or broken streams.
    
    Args:
        provider: Provider name (e.g., "openai", "anthropic", "mistral")
        model: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet")
        messages: List of message dicts with "role" and "content"
        client: Provider client instance (e.g., OpenAI(), Anthropic())
        stream: Whether to use streaming (auto-detected if not provided)
        **kwargs: Additional provider-specific arguments
    
    Returns:
        Standardized dict with cost tracking data:
        {
            "provider": str,
            "model": str,
            "pricing_version": str,
            "prompt_tokens": int,
            "completion_tokens": int,
            "total_tokens": int,
            "cost_usd": float,
            "timestamp": str (ISO UTC),
            "error": str | None
        }
    
    Example:
        >>> from openai import AsyncOpenAI
        >>> client = AsyncOpenAI()
        >>> result = await track_llm_call(
        ...     provider="openai",
        ...     model="gpt-4o",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     client=client,
        ...     stream=True
        ... )
        >>> print(result["cost_usd"])
    """
    start_time = time.time()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Initialize tracking variables
    prompt_tokens = 0
    completion_tokens = 0
    cost_usd = 0.0
    error = None
    response = None
    full_output = ""
    
    # Auto-detect streaming support if not explicitly set
    if stream is None:
        stream = _detect_streaming_support(provider, client)
    
    try:
        # Estimate prompt tokens from messages (always available)
        prompt_text = " ".join([msg.get("content", "") for msg in messages])
        prompt_tokens = _estimate_tokens(prompt_text, model)
        
        # Execute API call (streaming or non-streaming)
        if stream:
            # Streaming call: buffer chunks and extract usage if available
            response, full_output = await _call_with_streaming(
                provider=provider,
                client=client,
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Try to extract usage from last chunk or response
            if response:
                # Check last chunk for usage (some providers include it)
                if isinstance(response, list) and response:
                    last_chunk = response[-1]
                    usage = _extract_usage_from_response(last_chunk)
                    if usage:
                        prompt_tokens = usage["prompt_tokens"]
                        completion_tokens = usage["completion_tokens"]
                    else:
                        # Estimate completion tokens from buffered output
                        completion_tokens = _estimate_tokens(full_output, model)
                else:
                    usage = _extract_usage_from_response(response)
                    if usage:
                        prompt_tokens = usage["prompt_tokens"]
                        completion_tokens = usage["completion_tokens"]
                    else:
                        completion_tokens = _estimate_tokens(full_output, model)
            else:
                # No response chunks - estimate from output
                completion_tokens = _estimate_tokens(full_output, model)
        else:
            # Non-streaming call: extract usage directly
            response = await _call_without_streaming(
                provider=provider,
                client=client,
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Extract usage from response
            usage = _extract_usage_from_response(response)
            if usage:
                prompt_tokens = usage["prompt_tokens"]
                completion_tokens = usage["completion_tokens"]
            else:
                # Fallback: estimate tokens from response content
                if hasattr(response, "choices") and response.choices:
                    content = response.choices[0].message.content
                    completion_tokens = _estimate_tokens(content or "", model)
                elif hasattr(response, "content"):
                    completion_tokens = _estimate_tokens(response.content or "", model)
                elif isinstance(response, dict):
                    content = response.get("content") or response.get("text", "")
                    completion_tokens = _estimate_tokens(content, model)
    
    except Exception as e:
        # Error occurred - still track cost with estimated tokens
        error = str(e)
        # If we have partial output from streaming, estimate completion tokens
        if full_output:
            completion_tokens = _estimate_tokens(full_output, model)
        # Otherwise, completion_tokens stays 0 (failed request)
    
    finally:
        # ALWAYS calculate and return cost, even on errors or broken streams
        # This ensures cost tracking is never lost
        
        # Get pricing for this provider/model
        pricing = _get_pricing(provider, model)
        
        # Calculate cost (per 1K tokens)
        prompt_cost = (prompt_tokens / 1000.0) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000.0) * pricing["completion"]
        cost_usd = prompt_cost + completion_cost
        
        # Return standardized payload
        return {
            "provider": provider,
            "model": model,
            "pricing_version": PRICING["version"],
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost_usd": round(cost_usd, 6),  # 6 decimal places for precision
            "timestamp": timestamp,
            "error": error,
        }

