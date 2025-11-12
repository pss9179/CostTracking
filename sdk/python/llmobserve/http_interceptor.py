"""
Universal HTTP client interceptor for llmobserve.

Patches httpx, requests, and aiohttp to inject context headers
and route requests through the proxy for automatic observability.
"""
import uuid
import logging
from typing import Optional

logger = logging.getLogger("llmobserve")

from llmobserve import context, config


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
                    # ALWAYS inject context headers (for proxy OR direct instrumentation)
                    try:
                        request.headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        request.headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        parent_span = context.get_current_span_id()
                        request.headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        request.headers["X-LLMObserve-Section"] = context.get_current_section()
                        request.headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        request.headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            request.headers["X-LLMObserve-Target-URL"] = request_url_str
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                    except Exception as e:
                        # Fail-open: if header injection fails, continue anyway
                        logger.debug(f"[llmobserve] Header injection failed: {e}")
            
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
                    # ALWAYS inject context headers (for proxy OR direct instrumentation)
                    try:
                        request.headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        request.headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        parent_span = context.get_current_span_id()
                        request.headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        request.headers["X-LLMObserve-Section"] = context.get_current_section()
                        request.headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                        customer = context.get_customer_id()
                        request.headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            request.headers["X-LLMObserve-Target-URL"] = request_url_str
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                    except Exception as e:
                        # Fail-open: if header injection fails, continue anyway
                        logger.debug(f"[llmobserve] Header injection failed: {e}")
            
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

