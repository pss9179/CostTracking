"""
Request tracking utilities for retry detection and deduplication.
"""
import hashlib
import time
from typing import Set, Dict, Optional
from collections import OrderedDict
import logging

logger = logging.getLogger("llmobserve")

# Global cache for tracking request IDs (bounded LRU)
_tracked_requests: OrderedDict[str, float] = OrderedDict()
_max_cache_size = 10000  # Keep last 10k requests
_cache_ttl_seconds = 3600  # 1 hour TTL


def generate_request_id(method: str, url: str, body: Optional[bytes] = None) -> str:
    """
    Generate deterministic request ID for retry detection.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL
        body: Request body (optional)
    
    Returns:
        SHA256 hash as hex string
    """
    # Create deterministic fingerprint
    fingerprint = f"{method}:{url}"
    if body:
        fingerprint += f":{body.decode('utf-8', errors='ignore')}"
    
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:16]


def is_request_tracked(request_id: str) -> bool:
    """
    Check if request was already tracked (likely a retry).
    
    Args:
        request_id: Request ID from generate_request_id()
    
    Returns:
        True if already tracked (don't track again), False otherwise
    """
    current_time = time.time()
    
    # Clean up expired entries
    expired_keys = [
        rid for rid, timestamp in _tracked_requests.items()
        if current_time - timestamp > _cache_ttl_seconds
    ]
    for key in expired_keys:
        _tracked_requests.pop(key, None)
    
    # Check if already tracked
    if request_id in _tracked_requests:
        logger.debug(f"[llmobserve] Request {request_id} already tracked (retry detected)")
        return True
    
    return False


def mark_request_tracked(request_id: str):
    """
    Mark request as tracked to prevent duplicate tracking on retries.
    
    Args:
        request_id: Request ID from generate_request_id()
    """
    current_time = time.time()
    
    # Add to cache with timestamp
    _tracked_requests[request_id] = current_time
    
    # Enforce size limit (LRU eviction)
    if len(_tracked_requests) > _max_cache_size:
        # Remove oldest entry
        _tracked_requests.popitem(last=False)


def should_track_response(status_code: int) -> bool:
    """
    Determine if response should be tracked based on status code.
    
    Args:
        status_code: HTTP status code
    
    Returns:
        True if should track, False otherwise
    
    RULES:
    - 2xx (success): Track
    - 4xx (client error): Track (user's mistake, but still an API call)
    - 5xx (server error): Don't track (API provider's fault, might not charge)
    - 429 (rate limit): Don't track (no actual work done)
    """
    if 200 <= status_code < 300:
        return True  # Success
    
    if 400 <= status_code < 500:
        # Client errors - most APIs still charge for these
        if status_code == 429:
            return False  # Rate limit - don't track
        return True  # Track other 4xx
    
    if 500 <= status_code < 600:
        return False  # Server errors - don't track
    
    return True  # Default: track


def detect_rate_limit(status_code: int, headers: Dict[str, str]) -> Optional[Dict[str, any]]:
    """
    Detect rate limiting from response.
    
    Args:
        status_code: HTTP status code
        headers: Response headers
    
    Returns:
        Dict with rate limit info if detected, None otherwise
    """
    if status_code != 429:
        return None
    
    # Common rate limit headers
    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    rate_limit_limit = headers.get("X-RateLimit-Limit") or headers.get("x-ratelimit-limit")
    rate_limit_remaining = headers.get("X-RateLimit-Remaining") or headers.get("x-ratelimit-remaining")
    rate_limit_reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
    
    return {
        "rate_limited": True,
        "retry_after": retry_after,
        "limit": rate_limit_limit,
        "remaining": rate_limit_remaining,
        "reset": rate_limit_reset
    }


def validate_timestamp(timestamp: float) -> bool:
    """
    Validate timestamp to detect clock skew.
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
    
    Returns:
        True if timestamp is reasonable, False if likely clock skew
    """
    current_time = time.time()
    
    # Allow 5 minutes of clock skew in either direction
    max_skew = 300  # 5 minutes
    
    if abs(timestamp - current_time) > max_skew:
        logger.warning(
            f"[llmobserve] Clock skew detected: "
            f"timestamp={timestamp}, current={current_time}, "
            f"diff={abs(timestamp - current_time)}s"
        )
        return False
    
    return True


def extract_batch_api_info(url: str, headers: Dict[str, str]) -> Optional[Dict[str, any]]:
    """
    Detect if request is using batch API (OpenAI Batch API gets 50% discount).
    
    Args:
        url: Request URL
        headers: Request headers
    
    Returns:
        Dict with batch info if detected, None otherwise
    """
    # OpenAI Batch API
    if "api.openai.com" in url and "/batches" in url:
        return {
            "is_batch": True,
            "provider": "openai",
            "discount": 0.5  # 50% off
        }
    
    # Anthropic doesn't have batch API yet
    # Cohere doesn't have batch API yet
    # Google Gemini doesn't have batch API yet
    
    return None

