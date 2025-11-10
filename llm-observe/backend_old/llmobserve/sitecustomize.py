"""Optional auto-load script for automatic instrumentation.

This module can be installed in site-packages or via .pth file to enable
automatic instrumentation without code changes.

Installation:
    1. Copy this file to site-packages/llmobserve/sitecustomize.py
    2. Or create a .pth file pointing to this module
    
Environment variables:
    LLMOBSERVE_AUTO_FUNCTION_TRACING: Enable/disable (default: true)
    LLMOBSERVE_AUTO_INSTRUMENT: Enable/disable (default: true)
"""

import os

# Check if auto-loading is enabled
_auto_load = os.getenv("LLMOBSERVE_AUTO_LOAD", "false").lower() == "true"

if _auto_load:
    try:
        from llmobserve.tracing.import_hook_v2 import enable_import_hook_v2
        from llmobserve.tracing.context_propagator import enable_context_propagation
        
        # Enable import hook v2 if auto function tracing is enabled
        auto_function_tracing = os.getenv("LLMOBSERVE_AUTO_FUNCTION_TRACING", "true").lower() != "false"
        if auto_function_tracing:
            enable_import_hook_v2()
        
        # Enable context propagation
        enable_context_propagation()
    except ImportError:
        # llmobserve not installed - fail silently
        pass
    except Exception:
        # Best-effort: don't crash if instrumentation can't be enabled
        pass

