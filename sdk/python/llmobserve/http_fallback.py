"""
HTTP Fallback Event Creation

When no proxy is available, intercept HTTP responses and create events directly.
This provides universal API coverage without per-SDK patching.
"""
import time
import json
import logging
from typing import Optional, Dict, Any
from llmobserve import buffer
from llmobserve.event_creator import create_event_from_http_response, should_create_event

logger = logging.getLogger("llmobserve")


def try_create_http_fallback_event(
    method: str,
    url: str,
    status_code: int,
    request_content: Optional[bytes],
    response_content: Optional[bytes],
    start_time: float,
    request_id: Optional[str] = None
) -> bool:
    """
    Attempt to create an event from HTTP request/response.
    
    Returns True if event was created, False otherwise.
    Fails silently - never breaks the user's application.
    """
    logger.debug(f"[llmobserve] try_create_http_fallback_event called for {method} {url} (status {status_code})")
    try:
        if not should_create_event(url, status_code):
            return False
        
        # Calculate latency
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Parse bodies
        request_body = None
        response_body = None
        
        try:
            if request_content:
                request_body = json.loads(request_content.decode('utf-8'))
        except:
            pass
        
        try:
            if response_content:
                response_body = json.loads(response_content.decode('utf-8'))
        except:
            pass
        
        # Create event
        event = create_event_from_http_response(
            method=method,
            url=url,
            status_code=status_code,
            request_body=request_body,
            response_body=response_body,
            latency_ms=latency_ms,
            request_id=request_id
        )
        
        if event:
            buffer.add_event(event)
            logger.debug(f"[llmobserve] HTTP fallback: created event for {url}")
            return True
        
        return False
        
    except Exception as e:
        logger.debug(f"[llmobserve] HTTP fallback failed (non-critical): {e}")
        return False

