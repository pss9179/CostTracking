"""
Spending Cap Enforcement

Checks hard spending caps before API calls and raises exceptions if exceeded.
"""
import logging
import os
from typing import Optional, Dict, Any
import httpx

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
        # Call collector to check caps
        # Force HTTP/1.1 to avoid HTTP/2 issues with Railway edge
        with httpx.Client(http2=False, timeout=5.0) as client:
            response = client.get(
                f"{collector_url}/caps/check",
                params=params,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        
        if response.status_code == 200:
            result = response.json()
            
            # If not allowed, raise exception
            if not result.get("allowed", True):
                exceeded = result.get("exceeded_caps", [])
                raise BudgetExceededError(
                    f"Spending cap exceeded: {result.get('message', 'Unknown')}",
                    exceeded
                )
            
            return result
        
        elif response.status_code == 401:
            # Parse error detail
            try:
                detail = response.json().get("detail", "Invalid API key")
            except:
                detail = "Invalid API key"
            
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
            msg = f"Cap check failed with HTTP {response.status_code}"
            if strict:
                logger.error(f"[llmobserve] {msg}")
                raise CapCheckError(msg, status_code=response.status_code)
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
    
    except httpx.TimeoutException as e:
        msg = f"Cap check timed out: {e}"
        if strict:
            logger.error(f"[llmobserve] {msg}")
            raise CapCheckError(msg)
        else:
            logger.warning(f"[llmobserve] {msg} (failing open)")
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": f"Timeout - allowing request"
            }
    
    except Exception as e:
        msg = f"Cap check error: {type(e).__name__}: {e}"
        if strict:
            logger.error(f"[llmobserve] {msg}")
            raise CapCheckError(msg)
        else:
            logger.debug(f"[llmobserve] {msg} (failing open)")
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": f"Check error - allowing request"
            }


def should_check_caps() -> bool:
    """Check if cap checking is enabled."""
    return bool(config.get_api_key() and config.get_collector_url())

