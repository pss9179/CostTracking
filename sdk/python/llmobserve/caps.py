"""
Spending Cap Enforcement

Checks hard spending caps before API calls and raises exceptions if exceeded.

NOTE: This module uses urllib directly to bypass all SDK patching.
Both httpx and requests are monkey-patched by the SDK, which can cause issues.
"""
import logging
import os
from typing import Optional, Dict, Any

from llmobserve import config

logger = logging.getLogger("llmobserve")


class BudgetExceededError(Exception):
    """
    Raised when a hard spending cap is exceeded.
    
    Contains details about which cap was exceeded and current spending.
    """
    def __init__(self, message: str, exceeded_caps: list):
        super().__init__(message)
        self.exceeded_caps = exceeded_caps
    
    def __str__(self):
        msg = f"{super().__str__()}\n\nExceeded Caps:"
        for cap in self.exceeded_caps:
            msg += f"\n  - {cap['cap_type']}"
            if cap.get('target_name'):
                msg += f" ({cap['target_name']})"
            msg += f": ${cap['current']:.2f} / ${cap['limit']:.2f} ({cap['period']})"
        return msg


class CapCheckError(Exception):
    """
    Raised when cap check fails and strict mode is enabled.
    
    This allows users to handle cap check failures explicitly.
    """
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def check_spending_caps(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent: Optional[str] = None,
    strict: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Check if any hard spending caps would be exceeded.
    
    Args:
        provider: Provider name (e.g., 'openai')
        model: Model ID (e.g., 'gpt-4o')
        customer_id: Customer ID
        agent: Agent name
        strict: If True, raise CapCheckError on auth/connection failures.
                If False (default), fail open and allow requests.
                Can also be set via LLMOBSERVE_STRICT_CAPS=true env var.
    
    Returns:
        Dict with 'allowed', 'exceeded_caps', and 'message' fields
    
    Raises:
        BudgetExceededError: If any hard cap is exceeded
        CapCheckError: If strict mode is enabled and cap check fails
    """
    # Determine strict mode
    if strict is None:
        strict = os.getenv("LLMOBSERVE_STRICT_CAPS", "").lower() in ("true", "1", "yes")
    
    # If no API key, handle based on strict mode
    api_key = config.get_api_key()
    collector_url = config.get_collector_url()
    
    if not api_key:
        msg = "No LLMOBSERVE_API_KEY set - caps cannot be checked. Get your API key from https://app.llmobserve.com"
        if strict:
            logger.error(f"[llmobserve] {msg}")
            raise CapCheckError(msg)
        else:
            logger.warning(f"[llmobserve] {msg}")
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": "No API key - caps not checked"
            }
    
    # Build query params
    params = {}
    if provider:
        params["provider"] = provider
    if model:
        params["model"] = model
    if customer_id:
        params["customer_id"] = customer_id
    if agent:
        params["agent"] = agent
    
    try:
        # Use urllib directly to bypass all SDK patching (requests and httpx are both patched)
        import urllib.request
        import urllib.parse
        import urllib.error
        import ssl
        import json as json_module
        
        # Build URL with params
        url = f"{collector_url}/caps/check"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET"
        )
        
        # Create SSL context with certifi certificates (if available) or default
        ssl_context = ssl.create_default_context()
        try:
            import certifi
            ssl_context.load_verify_locations(certifi.where())
        except ImportError:
            pass  # Use system certificates
        
        try:
            # 15 second timeout - cap check can be slow due to database queries
            with urllib.request.urlopen(req, timeout=15.0, context=ssl_context) as resp:
                response_data = resp.read().decode('utf-8')
                response_json = json_module.loads(response_data)
                status_code = resp.status
        except urllib.error.HTTPError as http_err:
            status_code = http_err.code
            try:
                response_json = json_module.loads(http_err.read().decode('utf-8'))
            except:
                response_json = {"detail": str(http_err)}
        
        if status_code == 200:
            # If not allowed, raise exception
            if not response_json.get("allowed", True):
                exceeded = response_json.get("exceeded_caps", [])
                raise BudgetExceededError(
                    f"Spending cap exceeded: {response_json.get('message', 'Unknown')}",
                    exceeded
                )
            return response_json
        
        elif status_code == 401:
            detail = response_json.get("detail", "Invalid API key")
            msg = f"Cap check auth failed: {detail}. Make sure LLMOBSERVE_API_KEY is a valid key from https://app.llmobserve.com"
            
            if strict:
                logger.error(f"[llmobserve] {msg}")
                raise CapCheckError(msg, status_code=401)
            else:
                logger.warning(f"[llmobserve] {msg} (failing open)")
                return {
                    "allowed": True,
                    "exceeded_caps": [],
                    "message": "Auth failed - allowing request (set LLMOBSERVE_STRICT_CAPS=true to block)"
                }
        
        else:
            msg = f"Cap check failed with HTTP {status_code}"
            if strict:
                logger.error(f"[llmobserve] {msg}")
                raise CapCheckError(msg, status_code=status_code)
            else:
                logger.warning(f"[llmobserve] {msg} (failing open)")
                return {
                    "allowed": True,
                    "exceeded_caps": [],
                    "message": f"Check failed - allowing request"
                }
    
    except BudgetExceededError:
        # Always re-raise budget errors
        raise
    
    except CapCheckError:
        # Re-raise cap check errors in strict mode
        raise
    
    except Exception as e:
        # Handle timeout and connection errors
        error_type = type(e).__name__
        if "Timeout" in error_type or "timeout" in str(e).lower() or "timed out" in str(e).lower():
            msg = f"Cap check timed out: {e}"
        elif "Connection" in error_type or "connection" in str(e).lower():
            msg = f"Cap check connection error: {e}"
        else:
            msg = f"Cap check error: {error_type}: {e}"
        
        if strict:
            logger.error(f"[llmobserve] {msg}")
            raise CapCheckError(msg)
        else:
            logger.warning(f"[llmobserve] {msg} (failing open)")
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": f"Check error - allowing request"
            }


def should_check_caps() -> bool:
    """Check if cap checking is enabled."""
    return bool(config.get_api_key() and config.get_collector_url())
