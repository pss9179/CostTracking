"""
WebSocket Interceptor for LLMObserve Context Propagation

Patches websockets and aiohttp WebSocket connections to inject context headers.
"""

import logging
import uuid
from typing import Any, Optional

from llmobserve import config, context

logger = logging.getLogger("llmobserve")

_websockets_patched = False
_aiohttp_ws_patched = False


def patch_websockets() -> bool:
    """
    Patch websockets library to inject LLMObserve context headers.
    
    Returns:
        bool: True if patching succeeded, False otherwise.
    """
    global _websockets_patched
    
    if _websockets_patched:
        logger.debug("[llmobserve] websockets already patched")
        return True
    
    try:
        import websockets
    except ImportError:
        logger.debug("[llmobserve] websockets not installed, skipping WebSocket patching")
        return False
    
    try:
        # Patch websockets.connect
        original_connect = websockets.connect
        
        def patched_connect(uri, **kwargs):
            """Patched connect that injects context headers."""
            if config.is_enabled():
                try:
                    extra_headers = kwargs.get("extra_headers", [])
                    if not isinstance(extra_headers, list):
                        extra_headers = list(extra_headers) if extra_headers else []
                    
                    # Inject LLMObserve context
                    extra_headers.append(("X-LLMObserve-Run-ID", context.get_run_id()))
                    extra_headers.append(("X-LLMObserve-Span-ID", str(uuid.uuid4())))
                    
                    parent_span = context.get_current_span_id()
                    if parent_span:
                        extra_headers.append(("X-LLMObserve-Parent-Span-ID", parent_span))
                    
                    extra_headers.append(("X-LLMObserve-Section", context.get_current_section()))
                    extra_headers.append(("X-LLMObserve-Section-Path", context.get_section_path()))
                    
                    customer = context.get_customer_id()
                    if customer:
                        extra_headers.append(("X-LLMObserve-Customer-ID", customer))
                    
                    kwargs["extra_headers"] = extra_headers
                    logger.debug(f"[llmobserve] Injected context into WebSocket connection: {uri}")
                except Exception as e:
                    # Fail-open: if injection fails, continue anyway
                    logger.debug(f"[llmobserve] WebSocket header injection failed: {e}")
            
            return original_connect(uri, **kwargs)
        
        websockets.connect = patched_connect
        
        _websockets_patched = True
        logger.info("[llmobserve] ✓ websockets library patched (context headers will be injected)")
        return True
        
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to patch websockets: {e}")
        return False


def patch_aiohttp_websocket() -> bool:
    """
    Patch aiohttp WebSocket connections to inject LLMObserve context headers.
    
    Returns:
        bool: True if patching succeeded, False otherwise.
    """
    global _aiohttp_ws_patched
    
    if _aiohttp_ws_patched:
        logger.debug("[llmobserve] aiohttp WebSocket already patched")
        return True
    
    try:
        import aiohttp
    except ImportError:
        logger.debug("[llmobserve] aiohttp not installed, skipping aiohttp WebSocket patching")
        return False
    
    try:
        # Patch ClientSession.ws_connect
        original_ws_connect = aiohttp.ClientSession.ws_connect
        
        async def patched_ws_connect(self, url, **kwargs):
            """Patched ws_connect that injects context headers."""
            if config.is_enabled():
                try:
                    headers = kwargs.get("headers", {})
                    if not isinstance(headers, dict):
                        headers = dict(headers) if headers else {}
                    
                    # Inject LLMObserve context
                    headers["X-LLMObserve-Run-ID"] = context.get_run_id()
                    headers["X-LLMObserve-Span-ID"] = str(uuid.uuid4())
                    
                    parent_span = context.get_current_span_id()
                    if parent_span:
                        headers["X-LLMObserve-Parent-Span-ID"] = parent_span
                    
                    headers["X-LLMObserve-Section"] = context.get_current_section()
                    headers["X-LLMObserve-Section-Path"] = context.get_section_path()
                    
                    customer = context.get_customer_id()
                    if customer:
                        headers["X-LLMObserve-Customer-ID"] = customer
                    
                    kwargs["headers"] = headers
                    logger.debug(f"[llmobserve] Injected context into aiohttp WebSocket: {url}")
                except Exception as e:
                    # Fail-open: if injection fails, continue anyway
                    logger.debug(f"[llmobserve] aiohttp WebSocket header injection failed: {e}")
            
            return await original_ws_connect(self, url, **kwargs)
        
        aiohttp.ClientSession.ws_connect = patched_ws_connect
        
        _aiohttp_ws_patched = True
        logger.info("[llmobserve] ✓ aiohttp WebSocket patched (context headers will be injected)")
        return True
        
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to patch aiohttp WebSocket: {e}")
        return False


def patch_all_websockets() -> bool:
    """
    Patch all WebSocket libraries.
    
    Returns:
        bool: True if at least one library was patched successfully.
    """
    ws_patched = patch_websockets()
    aiohttp_patched = patch_aiohttp_websocket()
    
    return ws_patched or aiohttp_patched


def is_websockets_patched() -> bool:
    """Check if any WebSocket library is patched."""
    return _websockets_patched or _aiohttp_ws_patched

