"""
Global configuration for the SDK.
"""
import os
from typing import Optional

# Global configuration state
_config = {
    "enabled": True,
    "collector_url": None,
    "api_key": None,
    "flush_interval_ms": 500,
    "tenant_id": None,
    "customer_id": None,
}


def configure(
    collector_url: str,
    api_key: Optional[str] = None,
    flush_interval_ms: int = 500,
    tenant_id: Optional[str] = None,
    customer_id: Optional[str] = None
) -> None:
    """
    Configure the SDK.
    
    Args:
        collector_url: URL of the collector API
        api_key: Optional API key for authentication
        flush_interval_ms: How often to flush events to collector
        tenant_id: Optional tenant identifier for multi-tenant tracking
        customer_id: Optional customer identifier for per-customer tracking
    """
    _config["collector_url"] = collector_url
    _config["api_key"] = api_key
    _config["flush_interval_ms"] = flush_interval_ms
    _config["tenant_id"] = tenant_id
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


def get_tenant_id() -> Optional[str]:
    """Get the configured tenant ID (from config or env var)."""
    # Check context first, then config, then env var
    from llmobserve import context
    ctx_tenant = context.get_tenant_id()
    if ctx_tenant:
        return ctx_tenant
    
    config_tenant = _config.get("tenant_id")
    if config_tenant:
        return config_tenant
    
    return os.environ.get("LLMOBSERVE_TENANT_ID")


def get_customer_id() -> Optional[str]:
    """Get the configured customer ID (from config or context)."""
    # Check context first, then config
    from llmobserve import context
    ctx_customer = context.get_customer_id()
    if ctx_customer:
        return ctx_customer
    
    return _config.get("customer_id")

