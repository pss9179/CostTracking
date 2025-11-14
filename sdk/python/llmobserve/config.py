"""
Global configuration for the SDK.
"""
import os
from typing import Optional

# Global configuration state
_config = {
    "enabled": True,
    "collector_url": None,
    "proxy_url": None,
    "api_key": None,
    "flush_interval_ms": 500,
    "tenant_id": None,  # Defaults to "default_tenant" if not set
    "customer_id": None,
    "auto_detect_agents": True,  # Automatically detect agents from call stack
}


def configure(
    collector_url: str,
    api_key: str,
    proxy_url: Optional[str] = None,
    flush_interval_ms: int = 500,
    tenant_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    auto_detect_agents: bool = True
) -> None:
    """
    Configure the SDK.
    
    Args:
        collector_url: URL of the collector API
        api_key: API key for authentication (required)
        proxy_url: URL of the proxy server (optional, for hybrid architecture)
        flush_interval_ms: How often to flush events to collector
        tenant_id: Tenant identifier (defaults to "default_tenant" if not provided)
        customer_id: Optional customer identifier for tracking your end-users
    """
    _config["collector_url"] = collector_url
    _config["proxy_url"] = proxy_url
    _config["api_key"] = api_key
    _config["flush_interval_ms"] = flush_interval_ms
    _config["auto_detect_agents"] = auto_detect_agents
    
    # Set tenant_id: explicit arg > env var > "default_tenant"
    if tenant_id:
        _config["tenant_id"] = tenant_id
    elif os.environ.get("LLMOBSERVE_TENANT_ID"):
        _config["tenant_id"] = os.environ.get("LLMOBSERVE_TENANT_ID")
    else:
        _config["tenant_id"] = "default_tenant"
    
    _config["customer_id"] = customer_id
    
    # Check if disabled via env var
    if os.environ.get("LLMOBSERVE_DISABLED") == "1":
        _config["enabled"] = False


def is_enabled() -> bool:
    """Check if observability is enabled."""
    return _config["enabled"]


def get_collector_url() -> Optional[str]:
    """Get the collector URL."""
    return _config.get("collector_url")


def get_api_key() -> Optional[str]:
    """Get the API key."""
    return _config.get("api_key")


def get_flush_interval_ms() -> int:
    """Get the flush interval in milliseconds."""
    return _config.get("flush_interval_ms", 500)


def get_proxy_url() -> Optional[str]:
    """Get the proxy URL."""
    return _config.get("proxy_url")


def set_proxy_url(proxy_url: str) -> None:
    """Set the proxy URL (used by auto-start)."""
    _config["proxy_url"] = proxy_url


def get_tenant_id() -> str:
    """Get the tenant ID (always returns a value)."""
    return _config.get("tenant_id", "default_tenant")


def get_customer_id() -> Optional[str]:
    """Get the configured customer ID (from config or context)."""
    # Check context first, then config
    from llmobserve import context
    ctx_customer = context.get_customer_id()
    if ctx_customer:
        return ctx_customer
    
    return _config.get("customer_id")


def get_auto_detect_agents() -> bool:
    """Get whether automatic agent detection is enabled."""
    return _config.get("auto_detect_agents", True)

