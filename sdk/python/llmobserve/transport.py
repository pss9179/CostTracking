"""
Transport layer for sending events to collector.

Includes exponential-backoff retry and signal handling.
"""
import json
import time
import signal
import logging
from typing import List
from llmobserve.types import TraceEvent
from llmobserve import config

logger = logging.getLogger("llmobserve")

# Track if shutdown signal received
_shutdown_requested = False


def _handle_signal(signum, frame):
    """Handle SIGTERM/SIGINT to flush events before shutdown."""
    global _shutdown_requested
    _shutdown_requested = True
    logger.info("[llmobserve] Shutdown signal received - flushing events")
    flush_events()


def flush_events() -> None:
    """
    Flush buffered events to the collector with exponential-backoff retry.
    
    Sends a batch POST request to /events endpoint.
    Retries up to 3 times with exponential backoff (1s, 2s, 4s).
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
    
    # Exponential backoff retry (max 3 attempts)
    max_retries = 3
    base_delay = 1.0  # 1 second
    
    for attempt in range(max_retries):
        try:
            # Try to import requests
            try:
                import requests
            except ImportError:
                # Fallback to urllib if requests not available
                import urllib.request
                import urllib.error
                
                url = f"{collector_url}/events/"  # Note: trailing slash required
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
                    return  # Success
                except urllib.error.URLError as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"[llmobserve] ⚠️  Failed to send events, retrying in {delay}s: {e}")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"[llmobserve] ❌ Failed to send events after {max_retries} attempts: {e}")
                        logger.error(f"[llmobserve] Collector URL: {collector_url}")
                        logger.error(f"[llmobserve] Check: 1) URL is correct, 2) Server is running, 3) Network is accessible")
                        return
                return
            
            # Use requests if available
            url = f"{collector_url}/events/"  # Note: trailing slash required
            headers = {"Content-Type": "application/json"}
            
            if config.get_api_key():
                headers["Authorization"] = f"Bearer {config.get_api_key()}"
            
            response = requests.post(
                url,
                json=events,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()  # Raise on HTTP error
            return  # Success
            
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"[llmobserve] ⚠️  Failed to send events, retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"[llmobserve] ❌ Failed to send events after {max_retries} attempts: {e}")
                logger.error(f"[llmobserve] Collector URL: {collector_url}")
                logger.error(f"[llmobserve] Check: 1) URL is correct, 2) Server is running, 3) Network is accessible")
                # Fail-open: don't break user's application
                return


# Register signal handlers for graceful shutdown
try:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
except (ValueError, OSError):
    # Signals not available (e.g., Windows)
    pass

