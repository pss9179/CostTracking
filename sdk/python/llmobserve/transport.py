"""
Transport layer for sending events to collector.
"""
import json
from typing import List
from llmobserve.types import TraceEvent
from llmobserve import config


def flush_events() -> None:
    """
    Flush buffered events to the collector.
    
    Sends a batch POST request to /events endpoint.
    """
    if not config.is_enabled():
        return
    
    # Import here to avoid circular dependency
    from llmobserve.buffer import get_and_clear_buffer
    
    events = get_and_clear_buffer()
    
    if not events:
        return
    
    collector_url = config.get_collector_url()
    if not collector_url:
        return
    
    try:
        # Try to import requests
        try:
            import requests
        except ImportError:
            # Fallback to urllib if requests not available
            import urllib.request
            import urllib.error
            
            url = f"{collector_url}/events"
            data = json.dumps(events).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            if config.get_api_key():
                req.add_header("Authorization", f"Bearer {config.get_api_key()}")
            
            try:
                urllib.request.urlopen(req, timeout=5)
            except urllib.error.URLError:
                pass  # Silently fail
            return
        
        # Use requests if available
        url = f"{collector_url}/events"
        headers = {"Content-Type": "application/json"}
        
        if config.get_api_key():
            headers["Authorization"] = f"Bearer {config.get_api_key()}"
        
        requests.post(
            url,
            json=events,
            headers=headers,
            timeout=5
        )
    except Exception:
        # Silently fail - don't break user's application
        pass

