"""
Universal HTTP client interceptor for llmobserve.

Patches httpx, requests, and aiohttp to inject context headers
and route requests through the proxy for automatic observability.

FEATURES:
- Retry detection (prevents double-counting)
- Failed request handling (only tracks successful calls)
- Rate limit detection (429 responses)
- Batch API support (50% discount for OpenAI batches)
- Clock skew protection
- Graceful degradation
"""
import uuid
import logging
import time
from typing import Optional

logger = logging.getLogger("llmobserve")

from llmobserve import context, config
from llmobserve import request_tracker


def patch_httpx():
    """Patch httpx.Client and httpx.AsyncClient to inject headers."""
    try:
        import httpx
    except ImportError:
        logger.debug("[llmobserve] httpx not installed, skipping patch")
        return False
    
    # Patch sync client
    if hasattr(httpx.Client, "send"):
        if hasattr(httpx.Client.send, "_llmobserve_patched"):
            logger.debug("[llmobserve] httpx.Client already patched")
            return True
        
        original_send = httpx.Client.send
        
        def wrapped_send(self, request, **kwargs):
            if config.is_enabled():
                collector_url = config.get_collector_url()
                proxy_url = config.get_proxy_url()
                request_url_str = str(request.url)
                
                # Skip internal requests (to collector or proxy itself)
                is_internal = False
                if collector_url and request_url_str.startswith(collector_url):
                    is_internal = True
                elif proxy_url and request_url_str.startswith(proxy_url):
                    is_internal = True
                
                if not is_internal:
                    # Generate request ID for retry detection
                    try:
                        request_body = request.content if hasattr(request, 'content') else None
                        request_id = request_tracker.generate_request_id(
                            request.method,
                            request_url_str,
                            request_body
                        )
                        
                        # Check if this is a retry (already tracked)
                        if request_tracker.is_request_tracked(request_id):
                            logger.debug(f"[llmobserve] Skipping retry: {request_id}")
                            return original_send(self, request, **kwargs)
                        
                        # Inject context headers
                        request.headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        request.headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        request.headers["X-LLMObserve-Request-ID"] = request_id
                        parent_span = context.get_current_span_id()
                        request.headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        request.headers["X-LLMObserve-Section"] = context.get_current_section()
                        request.headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        request.headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # Add timestamp for clock skew detection
                        current_timestamp = time.time()
                        if request_tracker.validate_timestamp(current_timestamp):
                            request.headers["X-LLMObserve-Timestamp"] = str(current_timestamp)
                        
                        # Detect batch API usage
                        batch_info = request_tracker.extract_batch_api_info(
                            request_url_str,
                            dict(request.headers)
                        )
                        if batch_info:
                            request.headers["X-LLMObserve-Batch-API"] = "true"
                            request.headers["X-LLMObserve-Discount"] = str(batch_info["discount"])
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            request.headers["X-LLMObserve-Target-URL"] = request_url_str
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                        
                        # Execute request and check response
                        response = original_send(self, request, **kwargs)
                        
                        # Check if we should track this response
                        if request_tracker.should_track_response(response.status_code):
                            # Check for rate limiting
                            rate_limit_info = request_tracker.detect_rate_limit(
                                response.status_code,
                                dict(response.headers)
                            )
                            if rate_limit_info:
                                logger.warning(
                                    f"[llmobserve] Rate limit detected: {rate_limit_info}"
                                )
                            else:
                                # Mark as tracked (successful tracking)
                                request_tracker.mark_request_tracked(request_id)
                        else:
                            logger.debug(
                                f"[llmobserve] Skipping tracking for status {response.status_code}"
                            )
                        
                        return response
                        
                    except Exception as e:
                        # Fail-open: if anything fails, continue anyway
                        logger.debug(f"[llmobserve] Tracking failed: {e}")
                        return original_send(self, request, **kwargs)
            
            return original_send(self, request, **kwargs)
        
        httpx.Client.send = wrapped_send
        wrapped_send._llmobserve_patched = True
        wrapped_send._llmobserve_original = original_send
        
        logger.debug("[llmobserve] Patched httpx.Client.send")
    
    # Patch async client
    if hasattr(httpx.AsyncClient, "send"):
        if hasattr(httpx.AsyncClient.send, "_llmobserve_patched"):
            logger.debug("[llmobserve] httpx.AsyncClient already patched")
            return True
        
        original_async_send = httpx.AsyncClient.send
        
        async def wrapped_async_send(self, request, **kwargs):
            if config.is_enabled():
                collector_url = config.get_collector_url()
                proxy_url = config.get_proxy_url()
                request_url_str = str(request.url)
                
                # Skip internal requests (to collector or proxy itself)
                is_internal = False
                if collector_url and request_url_str.startswith(collector_url):
                    is_internal = True
                elif proxy_url and request_url_str.startswith(proxy_url):
                    is_internal = True
                
                if not is_internal:
                    try:
                        # Generate request ID for retry detection
                        request_body = request.content if hasattr(request, 'content') else None
                        request_id = request_tracker.generate_request_id(
                            request.method,
                            request_url_str,
                            request_body
                        )
                        
                        # Check if this is a retry (already tracked)
                        if request_tracker.is_request_tracked(request_id):
                            logger.debug(f"[llmobserve] Skipping retry: {request_id}")
                            return await original_async_send(self, request, **kwargs)
                        
                        # Inject context headers
                        request.headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        request.headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        request.headers["X-LLMObserve-Request-ID"] = request_id
                        parent_span = context.get_current_span_id()
                        request.headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        request.headers["X-LLMObserve-Section"] = context.get_current_section()
                        request.headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        request.headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # Add timestamp for clock skew detection
                        current_timestamp = time.time()
                        if request_tracker.validate_timestamp(current_timestamp):
                            request.headers["X-LLMObserve-Timestamp"] = str(current_timestamp)
                        
                        # Detect batch API usage
                        batch_info = request_tracker.extract_batch_api_info(
                            request_url_str,
                            dict(request.headers)
                        )
                        if batch_info:
                            request.headers["X-LLMObserve-Batch-API"] = "true"
                            request.headers["X-LLMObserve-Discount"] = str(batch_info["discount"])
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            request.headers["X-LLMObserve-Target-URL"] = request_url_str
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                        
                        # Execute request and check response
                        response = await original_async_send(self, request, **kwargs)
                        
                        # Check if we should track this response
                        if request_tracker.should_track_response(response.status_code):
                            # Check for rate limiting
                            rate_limit_info = request_tracker.detect_rate_limit(
                                response.status_code,
                                dict(response.headers)
                            )
                            if rate_limit_info:
                                logger.warning(
                                    f"[llmobserve] Rate limit detected: {rate_limit_info}"
                                )
                            else:
                                # Mark as tracked (successful tracking)
                                request_tracker.mark_request_tracked(request_id)
                        else:
                            logger.debug(
                                f"[llmobserve] Skipping tracking for status {response.status_code}"
                            )
                        
                        return response
                        
                    except Exception as e:
                        # Fail-open: if anything fails, continue anyway
                        logger.debug(f"[llmobserve] Async tracking failed: {e}")
                        return await original_async_send(self, request, **kwargs)
            
            return await original_async_send(self, request, **kwargs)
        
        httpx.AsyncClient.send = wrapped_async_send
        wrapped_async_send._llmobserve_patched = True
        wrapped_async_send._llmobserve_original = original_async_send
        
        logger.debug("[llmobserve] Patched httpx.AsyncClient.send")
    
    return True


def patch_requests():
    """Patch requests.Session to inject headers."""
    try:
        import requests
    except ImportError:
        logger.debug("[llmobserve] requests not installed, skipping patch")
        return False
    
    if hasattr(requests.Session, "request"):
        if hasattr(requests.Session.request, "_llmobserve_patched"):
            logger.debug("[llmobserve] requests.Session already patched")
            return True
        
        original_request = requests.Session.request
        
        def wrapped_request(self, method, url, **kwargs):
            if config.is_enabled():
                collector_url = config.get_collector_url()
                proxy_url = config.get_proxy_url()
                
                # Skip internal requests
                is_internal = False
                if collector_url and url.startswith(collector_url):
                    is_internal = True
                elif proxy_url and url.startswith(proxy_url):
                    is_internal = True
                
                if not is_internal:
                    # ALWAYS inject context headers (for proxy OR direct instrumentation)
                    try:
                        headers = kwargs.get("headers", {})
                        if headers is None:
                            headers = {}
                        
                        headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        parent_span = context.get_current_span_id()
                        headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        headers["X-LLMObserve-Section"] = context.get_current_section()
                        headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            headers["X-LLMObserve-Target-URL"] = url
                            url = f"{proxy_url}/proxy"
                        
                        kwargs["headers"] = headers
                    except Exception as e:
                        # Fail-open: if header injection fails, continue anyway
                        logger.debug(f"[llmobserve] Header injection failed: {e}")
            
            return original_request(self, method, url, **kwargs)
        
        requests.Session.request = wrapped_request
        wrapped_request._llmobserve_patched = True
        wrapped_request._llmobserve_original = original_request
        
        logger.debug("[llmobserve] Patched requests.Session.request")
    
    return True


def patch_aiohttp():
    """Patch aiohttp.ClientSession to inject headers."""
    try:
        import aiohttp
    except ImportError:
        logger.debug("[llmobserve] aiohttp not installed, skipping patch")
        return False
    
    if hasattr(aiohttp.ClientSession, "_request"):
        if hasattr(aiohttp.ClientSession._request, "_llmobserve_patched"):
            logger.debug("[llmobserve] aiohttp.ClientSession already patched")
            return True
        
        original_request = aiohttp.ClientSession._request
        
        async def wrapped_request(self, method, url, **kwargs):
            if config.is_enabled():
                collector_url = config.get_collector_url()
                proxy_url = config.get_proxy_url()
                url_str = str(url)
                
                # Skip internal requests
                is_internal = False
                if collector_url and url_str.startswith(collector_url):
                    is_internal = True
                elif proxy_url and url_str.startswith(proxy_url):
                    is_internal = True
                
                if not is_internal:
                    # ALWAYS inject context headers (for proxy OR direct instrumentation)
                    try:
                        headers = kwargs.get("headers", {})
                        if headers is None:
                            headers = {}
                        
                        headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        parent_span = context.get_current_span_id()
                        headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        headers["X-LLMObserve-Section"] = context.get_current_section()
                        headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            headers["X-LLMObserve-Target-URL"] = url_str
                            url = f"{proxy_url}/proxy"
                        
                        kwargs["headers"] = headers
                    except Exception as e:
                        # Fail-open: if header injection fails, continue anyway
                        logger.debug(f"[llmobserve] Header injection failed: {e}")
            
            return await original_request(self, method, url, **kwargs)
        
        aiohttp.ClientSession._request = wrapped_request
        wrapped_request._llmobserve_patched = True
        wrapped_request._llmobserve_original = original_request
        
        logger.debug("[llmobserve] Patched aiohttp.ClientSession._request")
    
    return True


def patch_all_http_clients():
    """
    Patch all HTTP clients for automatic instrumentation.
    
    This replaces per-SDK instrumentors with universal HTTP interception.
    """
    patched = []
    failed = []
    
    if patch_httpx():
        patched.append("httpx")
    else:
        failed.append("httpx")
    
    if patch_requests():
        patched.append("requests")
    else:
        failed.append("requests")
    
    if patch_aiohttp():
        patched.append("aiohttp")
    else:
        failed.append("aiohttp")
    
    if patched:
        logger.info(f"[llmobserve] Successfully patched HTTP clients: {', '.join(patched)}")
    
    if failed:
        logger.debug(f"[llmobserve] Skipped HTTP clients (not installed): {', '.join(failed)}")
    
    return len(patched) > 0


def patch_all_protocols() -> dict:
    """
    Patch HTTP, gRPC, and WebSocket protocols for universal coverage.
    
    Returns:
        dict: Status of each protocol patching attempt.
    """
    from llmobserve.grpc_interceptor import patch_grpc
    from llmobserve.websocket_interceptor import patch_all_websockets
    
    results = {
        "http": patch_all_http_clients(),
        "grpc": patch_grpc(),
        "websocket": patch_all_websockets()
    }
    
    return results

