"""
Spending Cap Enforcement

Checks hard spending caps before API calls and raises exceptions if exceeded.
"""
import logging
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


def check_spending_caps(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Check if any hard spending caps would be exceeded.
    
    Args:
        provider: Provider name (e.g., 'openai')
        model: Model ID (e.g., 'gpt-4o')
        customer_id: Customer ID
        agent: Agent name
    
    Returns:
        Dict with 'allowed', 'exceeded_caps', and 'message' fields
    
    Raises:
        BudgetExceededError: If any hard cap is exceeded
    """
    # If no API key, skip cap checking (not authenticated)
    api_key = config.get_api_key()
    collector_url = config.get_collector_url()
    
    if not api_key:
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
        response = httpx.get(
            f"{collector_url}/caps/check",
            params=params,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=2.0,  # Fast timeout - don't delay user requests
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
            logger.warning("[llmobserve] Cap check failed: Invalid API key")
            # Fail open - don't block user's API calls
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": "Auth failed - allowing request"
            }
        
        else:
            logger.warning(f"[llmobserve] Cap check failed: HTTP {response.status_code}")
            # Fail open
            return {
                "allowed": True,
                "exceeded_caps": [],
                "message": "Check failed - allowing request"
            }
    
    except BudgetExceededError:
        # Re-raise budget errors
        raise
    
    except Exception as e:
        # Fail open - don't break user's application if cap check fails
        logger.debug(f"[llmobserve] Cap check error (fail-open): {e}")
        return {
            "allowed": True,
            "exceeded_caps": [],
            "message": f"Check error - allowing request: {e}"
        }


def should_check_caps() -> bool:
    """Check if cap checking is enabled."""
    return bool(config.get_api_key() and config.get_collector_url())

