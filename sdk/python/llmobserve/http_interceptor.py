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
import json
from typing import Optional, Dict, Any

logger = logging.getLogger("llmobserve")

from llmobserve import context, config
from llmobserve import request_tracker
from llmobserve.caps import check_spending_caps, should_check_caps, BudgetExceededError
from llmobserve.event_creator import extract_model_from_request


def extract_provider_from_url(url: str) -> Optional[str]:
    """Extract provider name from API URL."""
    url_lower = url.lower()
    if "api.openai.com" in url_lower or "openai" in url_lower:
        return "openai"
    elif "api.anthropic.com" in url_lower or "anthropic" in url_lower:
        return "anthropic"
    elif "generativelanguage.googleapis.com" in url_lower or "gemini" in url_lower or "google" in url_lower:
        return "google"
    elif "pinecone.io" in url_lower:
        return "pinecone"
    elif "api.cohere.ai" in url_lower or "cohere" in url_lower:
        return "cohere"
    elif "api.together.xyz" in url_lower or "together" in url_lower:
        return "together"
    elif "api.vapi.ai" in url_lower or "vapi.ai" in url_lower:
        return "vapi"
    elif "openrouter.ai" in url_lower or "openrouter" in url_lower:
        return "openrouter"
    elif "groq.com" in url_lower or "groq" in url_lower:
        return "groq"
    elif "mistral.ai" in url_lower or "mistral" in url_lower:
        return "mistral"
    elif "api.perplexity.ai" in url_lower or "perplexity" in url_lower:
        return "perplexity"
    elif "api.ai21.com" in url_lower or "ai21" in url_lower:
        return "ai21"
    elif "replicate.com" in url_lower or "replicate" in url_lower:
        return "replicate"
    elif "huggingface.co" in url_lower or "huggingface" in url_lower:
        return "huggingface"
    elif "voyageai.com" in url_lower or "voyage" in url_lower:
        return "voyage"
    # Add more providers as needed
    return None


def should_skip_http_fallback(url: str) -> bool:
    """
    Check if HTTP fallback should be skipped for this URL.
    
    Returns True if the provider has a dedicated SDK patch that already
    tracks calls (to avoid duplicate events).
    """
    provider = extract_provider_from_url(url)
    # OpenAI SDK is patched separately, so skip HTTP fallback for OpenAI calls
    if provider == "openai":
        logger.debug(f"[llmobserve] Skipping HTTP fallback for OpenAI (SDK already patched)")
        return True
    return False


def patch_httpx():
    """Patch httpx.Client and httpx.AsyncClient to inject headers."""
    try:
        import httpx
    except ImportError:
        logger.debug("[llmobserve] httpx not installed, skipping patch")
        return False
    
    # Patch httpx decoder to handle decompression errors gracefully
    # GZipDecoder.decode catches zlib.error and wraps it in DecodingError
    # We need to catch zlib.error BEFORE it gets wrapped
    try:
        import httpx._decoders as decoders_module
        import zlib
        from httpx import DecodingError
        
        # Patch GZipDecoder.decode - this is the actual implementation that raises the error
        if hasattr(decoders_module, 'GZipDecoder'):
            if not hasattr(decoders_module.GZipDecoder.decode, "_llmobserve_patched"):
                original_gzip_decode = decoders_module.GZipDecoder.decode
                
                def patched_gzip_decode(self, data: bytes) -> bytes:
                    """Handle decompression errors gracefully - catch zlib.error before it's wrapped."""
                    try:
                        return original_gzip_decode(self, data)
                    except zlib.error as e:
                        # zlib.error with "incorrect header check" means content is already decompressed
                        error_str = str(e)
                        if "incorrect header check" in error_str or "-3" in error_str:
                            logger.debug(f"[llmobserve] zlib.error caught - content already decompressed: {error_str}")
                            return data
                        # Re-raise if it's a different zlib error
                        raise
                    except DecodingError as e:
                        # DecodingError wrapping zlib error - check error message
                        error_str = str(e)
                        if "incorrect header check" in error_str or "Error -3" in error_str or "-3" in error_str:
                            logger.debug(f"[llmobserve] DecodingError caught - content already decompressed: {error_str}")
                            return data
                        raise
                
                decoders_module.GZipDecoder.decode = patched_gzip_decode
                decoders_module.GZipDecoder.decode._llmobserve_patched = True
                decoders_module.GZipDecoder.decode._llmobserve_original = original_gzip_decode
                logger.debug("[llmobserve] Patched httpx GZipDecoder.decode to handle proxy responses")
    except (ImportError, AttributeError) as e:
        logger.debug(f"[llmobserve] Could not patch httpx decoder: {e}")
    
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
                        # Get section from context
                        current_section = context.get_current_section()
                        section_path = context.get_section_path()
                        
                        request.headers["X-LLMObserve-Section"] = current_section or ""
                        request.headers["X-LLMObserve-Section-Path"] = section_path or ""
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
                            # CRITICAL: Remove Accept-Encoding to prevent decompression issues
                            if "Accept-Encoding" in request.headers:
                                del request.headers["Accept-Encoding"]
                            if "accept-encoding" in request.headers:
                                del request.headers["accept-encoding"]
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                        
                        # Check spending caps before making request
                        if should_check_caps():
                            provider = extract_provider_from_url(request_url_str)
                            customer_id = context.get_customer_id()
                            agent = context.get_current_section()  # Use section as agent
                            
                            # Extract model from request body for model-specific caps
                            model = None
                            try:
                                if request_body:
                                    # Try to parse request body as JSON
                                    if isinstance(request_body, bytes):
                                        try:
                                            body_dict = json.loads(request_body.decode('utf-8'))
                                            model = extract_model_from_request(body_dict, provider or "")
                                        except (json.JSONDecodeError, UnicodeDecodeError):
                                            pass
                                    elif isinstance(request_body, (str, dict)):
                                        body_dict = request_body if isinstance(request_body, dict) else json.loads(request_body)
                                        model = extract_model_from_request(body_dict, provider or "")
                            except Exception as e:
                                logger.debug(f"[llmobserve] Failed to extract model for cap check: {e}")
                            
                            # This will raise BudgetExceededError if cap exceeded
                            check_spending_caps(
                                provider=provider,
                                model=model,  # Now includes model from request body
                                customer_id=customer_id,
                                agent=agent if agent != "/" else None,
                            )
                        
                        # Track start time for latency calculation
                        start_time = time.time()
                        
                        # Execute request and check response
                        # CRITICAL: If going through proxy, disable decompression by modifying request
                        # before sending
                        if proxy_url and proxy_url in str(request.url):
                            # Ensure Accept-Encoding is not in request
                            if "Accept-Encoding" in request.headers:
                                del request.headers["Accept-Encoding"]
                        
                        response = original_send(self, request, **kwargs)
                        
                        # CRITICAL FIX: If response came from proxy, modify headers IMMEDIATELY
                        # httpx reads headers when response is created, so we must modify before any access
                        if proxy_url and hasattr(response, 'url'):
                            response_url = str(response.url)
                            if proxy_url in response_url:
                                # Remove Content-Encoding from response headers IMMEDIATELY
                                # httpx checks this header when reading content, so we must remove it
                                # before httpx reads the content
                                if hasattr(response, 'headers'):
                                    # httpx uses HeaderList internally - modify _list directly
                                    if hasattr(response.headers, '_list'):
                                        response.headers._list = [
                                            (k, v) for k, v in response.headers._list 
                                            if k.lower() != 'content-encoding'
                                        ]
                                    # Also try direct modification
                                    try:
                                        # Try to get raw headers dict
                                        if hasattr(response.headers, 'raw'):
                                            # Remove from raw headers
                                            raw_headers = response.headers.raw
                                            if isinstance(raw_headers, list):
                                                response.headers.raw = [
                                                    (k, v) for k, v in raw_headers
                                                    if k.lower() != b'content-encoding'
                                                ]
                                    except:
                                        pass
                                    # Force remove via __delitem__
                                    try:
                                        del response.headers["Content-Encoding"]
                                    except:
                                        pass
                                    try:
                                        del response.headers["content-encoding"]
                                    except:
                                        pass
                        
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
                                
                                logger.debug(f"[llmobserve] About to check proxy_url (value: {proxy_url})")
                                # HTTP FALLBACK: Create event if no proxy
                                # Skip if provider SDK is already patched (avoid duplicates)
                                if not proxy_url and not should_skip_http_fallback(request_url_str):
                                    logger.debug(f"[llmobserve] Calling HTTP fallback for {request_url_str}")
                                    from llmobserve.http_fallback import try_create_http_fallback_event
                                    try_create_http_fallback_event(
                                        method=request.method,
                                        url=request_url_str,
                                        status_code=response.status_code,
                                        request_content=getattr(request, 'content', None),
                                        response_content=getattr(response, 'content', None),
                                        start_time=start_time,
                                        request_id=request_id
                                    )
                        else:
                            logger.debug(
                                f"[llmobserve] Skipping tracking for status {response.status_code}"
                            )
                        
                        return response
                    
                    except BudgetExceededError:
                        # CRITICAL: Re-raise budget exceeded errors - don't fail open for hard caps!
                        raise
                        
                    except Exception as e:
                        # Fail-open: if anything else fails, continue anyway
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
                        # Get section from context
                        current_section = context.get_current_section()
                        section_path = context.get_section_path()
                        
                        request.headers["X-LLMObserve-Section"] = current_section or ""
                        request.headers["X-LLMObserve-Section-Path"] = section_path or ""
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
                            # CRITICAL: Remove Accept-Encoding to prevent decompression issues
                            if "Accept-Encoding" in request.headers:
                                del request.headers["Accept-Encoding"]
                            if "accept-encoding" in request.headers:
                                del request.headers["accept-encoding"]
                            request.url = httpx.URL(f"{proxy_url}/proxy")
                        
                        # Check spending caps before making request
                        if should_check_caps():
                            provider = extract_provider_from_url(request_url_str)
                            customer_id = context.get_customer_id()
                            agent = context.get_current_section()  # Use section as agent
                            
                            # Extract model from request body for model-specific caps
                            model = None
                            try:
                                if request_body:
                                    # Try to parse request body as JSON
                                    if isinstance(request_body, bytes):
                                        try:
                                            body_dict = json.loads(request_body.decode('utf-8'))
                                            model = extract_model_from_request(body_dict, provider or "")
                                        except (json.JSONDecodeError, UnicodeDecodeError):
                                            pass
                                    elif isinstance(request_body, (str, dict)):
                                        body_dict = request_body if isinstance(request_body, dict) else json.loads(request_body)
                                        model = extract_model_from_request(body_dict, provider or "")
                            except Exception as e:
                                logger.debug(f"[llmobserve] Failed to extract model for cap check: {e}")
                            
                            # This will raise BudgetExceededError if cap exceeded
                            check_spending_caps(
                                provider=provider,
                                model=model,  # Now includes model from request body
                                customer_id=customer_id,
                                agent=agent if agent != "/" else None,
                            )
                        
                        # Track start time for latency
                        start_time = time.time()
                        
                        # Execute request and check response
                        response = await original_async_send(self, request, **kwargs)
                        
                        # CRITICAL FIX: If response came from proxy, modify headers IMMEDIATELY
                        if proxy_url and hasattr(response, 'url'):
                            response_url = str(response.url)
                            if proxy_url in response_url:
                                # Remove Content-Encoding from response headers IMMEDIATELY
                                if hasattr(response, 'headers'):
                                    # Use _headers dict directly if available (httpx internal)
                                    if hasattr(response.headers, '_list'):
                                        # httpx uses HeaderList internally
                                        response.headers._list = [
                                            (k, v) for k, v in response.headers._list 
                                            if k.lower() != 'content-encoding'
                                        ]
                                    # Also try direct dict access
                                    if isinstance(response.headers, dict):
                                        response.headers.pop("Content-Encoding", None)
                                        response.headers.pop("content-encoding", None)
                                    # Force remove via __delitem__ if possible
                                    try:
                                        del response.headers["Content-Encoding"]
                                    except (KeyError, TypeError):
                                        pass
                                    try:
                                        del response.headers["content-encoding"]
                                    except (KeyError, TypeError):
                                        pass
                        
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
                                
                                logger.debug(f"[llmobserve] About to check proxy_url (value: {proxy_url})")
                                # HTTP FALLBACK: Create event if no proxy
                                # Skip if provider SDK is already patched (avoid duplicates)
                                if not proxy_url and not should_skip_http_fallback(request_url_str):
                                    logger.debug(f"[llmobserve] Calling HTTP fallback for {request_url_str}")
                                    from llmobserve.http_fallback import try_create_http_fallback_event
                                    try_create_http_fallback_event(
                                        method=request.method,
                                        url=request_url_str,
                                        status_code=response.status_code,
                                        request_content=getattr(request, 'content', None),
                                        response_content=getattr(response, 'content', None),
                                        start_time=start_time,
                                        request_id=request_id
                                    )
                        else:
                            logger.debug(
                                f"[llmobserve] Skipping tracking for status {response.status_code}"
                            )
                        
                        return response
                    
                    except BudgetExceededError:
                        # CRITICAL: Re-raise budget exceeded errors - don't fail open for hard caps!
                        raise
                        
                    except Exception as e:
                        # Fail-open: if anything else fails, continue anyway
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
                    try:
                        # Generate request ID
                        request_body = kwargs.get("json") or kwargs.get("data")
                        if isinstance(request_body, dict):
                            import json as json_module
                            request_body_str = json_module.dumps(request_body).encode('utf-8')
                        elif isinstance(request_body, str):
                            request_body_str = request_body.encode('utf-8')
                        elif isinstance(request_body, bytes):
                            request_body_str = request_body
                        else:
                            request_body_str = None
                        
                        request_id = request_tracker.generate_request_id(method, url, request_body_str)
                        
                        # Check retry
                        if request_tracker.is_request_tracked(request_id):
                            logger.debug(f"[llmobserve] Skipping retry (requests): {request_id}")
                            return original_request(self, method, url, **kwargs)
                        
                        # Inject headers
                        headers = kwargs.get("headers", {})
                        if headers is None:
                            headers = {}
                        
                        headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        headers["X-LLMObserve-Request-ID"] = request_id
                        parent_span = context.get_current_span_id()
                        headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        current_section = context.get_current_section()
                        section_path = context.get_section_path()
                        headers["X-LLMObserve-Section"] = current_section or ""
                        headers["X-LLMObserve-Section-Path"] = section_path or ""
                        customer = context.get_customer_id()
                        headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        tenant = context.get_tenant_id()
                        headers["X-LLMObserve-Tenant-ID"] = tenant if tenant else "default_tenant"
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            headers["X-LLMObserve-Target-URL"] = url
                            if "Accept-Encoding" in headers:
                                del headers["Accept-Encoding"]
                            if "accept-encoding" in headers:
                                del headers["accept-encoding"]
                            url = f"{proxy_url}/proxy"
                        
                        kwargs["headers"] = headers
                        
                        # Track start time
                        start_time = time.time()
                        
                        # Make request
                        response = original_request(self, method, url, **kwargs)
                        
                        # HTTP FALLBACK: Create event if no proxy
                        # Skip if provider SDK is already patched (avoid duplicates)
                        if request_tracker.should_track_response(response.status_code):
                            request_tracker.mark_request_tracked(request_id)
                            
                            if not proxy_url and not should_skip_http_fallback(url):
                                from llmobserve.http_fallback import try_create_http_fallback_event
                                try_create_http_fallback_event(
                                    method=method,
                                    url=url,
                                    status_code=response.status_code,
                                    request_content=request_body_str,
                                    response_content=response.content if hasattr(response, 'content') else None,
                                    start_time=start_time,
                                    request_id=request_id
                                )
                        
                        return response
                        
                    except Exception as e:
                        logger.debug(f"[llmobserve] Tracking failed (requests): {e}")
                        return original_request(self, method, url, **kwargs)
            
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
                    try:
                        # Generate request ID
                        request_body = kwargs.get("json") or kwargs.get("data")
                        if isinstance(request_body, dict):
                            import json as json_module
                            request_body_str = json_module.dumps(request_body).encode('utf-8')
                        elif isinstance(request_body, str):
                            request_body_str = request_body.encode('utf-8')
                        elif isinstance(request_body, bytes):
                            request_body_str = request_body
                        else:
                            request_body_str = None
                        
                        request_id = request_tracker.generate_request_id(method, url_str, request_body_str)
                        
                        # Check retry
                        if request_tracker.is_request_tracked(request_id):
                            logger.debug(f"[llmobserve] Skipping retry (aiohttp): {request_id}")
                            return await original_request(self, method, url, **kwargs)
                        
                        # Inject headers
                        headers = kwargs.get("headers", {})
                        if headers is None:
                            headers = {}
                        
                        headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                        headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                        headers["X-LLMObserve-Request-ID"] = request_id
                        parent_span = context.get_current_span_id()
                        headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                        current_section = context.get_current_section()
                        section_path = context.get_section_path()
                        headers["X-LLMObserve-Section"] = current_section or ""
                        headers["X-LLMObserve-Section-Path"] = section_path or ""
                        customer = context.get_customer_id()
                        headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                        tenant = context.get_tenant_id()
                        headers["X-LLMObserve-Tenant-ID"] = tenant if tenant else "default_tenant"
                        
                        # If proxy is configured, route through proxy
                        if proxy_url:
                            headers["X-LLMObserve-Target-URL"] = url_str
                            url = f"{proxy_url}/proxy"
                        
                        kwargs["headers"] = headers
                        
                        # Track start time
                        start_time = time.time()
                        
                        # Make request
                        response = await original_request(self, method, url, **kwargs)
                        
                        # HTTP FALLBACK: Create event if no proxy
                        # Skip if provider SDK is already patched (avoid duplicates)
                        if request_tracker.should_track_response(response.status):
                            request_tracker.mark_request_tracked(request_id)
                            
                            if not proxy_url and not should_skip_http_fallback(url_str):
                                # Read response body
                                response_body = None
                                try:
                                    response_body = await response.read()
                                except:
                                    pass
                                
                                from llmobserve.http_fallback import try_create_http_fallback_event
                                try_create_http_fallback_event(
                                    method=method,
                                    url=url_str,
                                    status_code=response.status,
                                    request_content=request_body_str,
                                    response_content=response_body,
                                    start_time=start_time,
                                    request_id=request_id
                                )
                        
                        return response
                        
                    except Exception as e:
                        logger.debug(f"[llmobserve] Tracking failed (aiohttp): {e}")
                        return await original_request(self, method, url, **kwargs)
            
            return await original_request(self, method, url, **kwargs)
        
        aiohttp.ClientSession._request = wrapped_request
        wrapped_request._llmobserve_patched = True
        wrapped_request._llmobserve_original = original_request
        
        logger.debug("[llmobserve] Patched aiohttp.ClientSession._request")
    
    return True


def patch_urllib3():
    """Patch urllib3 to inject headers and route through proxy.
    
    This is needed for Pinecone SDK which uses urllib3 directly.
    """
    try:
        import urllib3
        from urllib3.poolmanager import PoolManager
        from urllib3.connectionpool import HTTPConnectionPool
    except ImportError:
        logger.debug("[llmobserve] urllib3 not installed, skipping patch")
        return False
    
    # Check if already patched
    if hasattr(PoolManager, "request") and hasattr(PoolManager.request, "_llmobserve_patched"):
        logger.debug("[llmobserve] urllib3.PoolManager already patched")
        return True
    
    # Patch PoolManager.request (used by Pinecone)
    original_request = PoolManager.request
    
    def wrapped_request(self, method, url, **kwargs):
        """Wrapped urllib3 request that injects headers and routes through proxy."""
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
                try:
                    # Generate request ID
                    request_body = kwargs.get("body")
                    if isinstance(request_body, str):
                        request_body_str = request_body.encode('utf-8')
                    elif isinstance(request_body, bytes):
                        request_body_str = request_body
                    else:
                        request_body_str = None
                    
                    request_id = request_tracker.generate_request_id(method, url_str, request_body_str)
                    
                    # Check retry
                    if request_tracker.is_request_tracked(request_id):
                        logger.debug(f"[llmobserve] Skipping retry (urllib3): {request_id}")
                        return original_request(self, method, url, **kwargs)
                    
                    # Inject headers
                    headers = kwargs.get("headers", {})
                    if headers is None:
                        headers = {}
                    
                    # Convert headers to dict if it's a custom object
                    if not isinstance(headers, dict):
                        headers = dict(headers) if hasattr(headers, '__iter__') else {}
                    
                    headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                    headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                    headers["X-LLMObserve-Request-ID"] = request_id
                    parent_span = context.get_current_span_id()
                    headers["X-LLMObserve-Parent-Span-ID"] = parent_span if parent_span else ""
                    headers["X-LLMObserve-Section"] = context.get_current_section()
                    headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                    customer = context.get_customer_id()
                    headers["X-LLMObserve-Customer-ID"] = customer if customer else ""
                    tenant = context.get_tenant_id()
                    headers["X-LLMObserve-Tenant-ID"] = tenant if tenant else "default_tenant"
                    
                    # If proxy is configured, route through proxy
                    if proxy_url:
                        headers["X-LLMObserve-Target-URL"] = url_str
                        headers.pop("Accept-Encoding", None)
                        headers.pop("accept-encoding", None)
                        url = f"{proxy_url}/proxy"
                    
                    kwargs["headers"] = headers
                    
                    # Track start time
                    start_time = time.time()
                    
                    # Make request
                    response = original_request(self, method, url, **kwargs)
                    
                    # HTTP FALLBACK: Create event if no proxy
                    # Skip if provider SDK is already patched (avoid duplicates)
                    if request_tracker.should_track_response(response.status):
                        request_tracker.mark_request_tracked(request_id)
                        
                        if not proxy_url and not should_skip_http_fallback(url_str):
                            from llmobserve.http_fallback import try_create_http_fallback_event
                            try_create_http_fallback_event(
                                method=method,
                                url=url_str,
                                status_code=response.status,
                                request_content=request_body_str,
                                response_content=response.data if hasattr(response, 'data') else None,
                                start_time=start_time,
                                request_id=request_id
                            )
                    
                    return response
                    
                except Exception as e:
                    logger.debug(f"[llmobserve] Tracking failed (urllib3): {e}")
                    return original_request(self, method, url, **kwargs)
        
        return original_request(self, method, url, **kwargs)
    
    PoolManager.request = wrapped_request
    wrapped_request._llmobserve_patched = True
    wrapped_request._llmobserve_original = original_request
    
    logger.debug("[llmobserve] Patched urllib3.PoolManager.request")
    
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
    
    if patch_urllib3():
        patched.append("urllib3")
    else:
        failed.append("urllib3")
    
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

