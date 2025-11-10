"""LLM Observability Demo - Auto-instrumentation for LLM calls."""

__version__ = "0.1.0"

# Auto-instrumentation on import (can be disabled via environment variable)
import os

# Check if auto-instrumentation is disabled
_auto_instrument = os.getenv("LLMOBSERVE_AUTO_INSTRUMENT", "true").lower() != "false"

if _auto_instrument:
    try:
        from llmobserve.tracing.instrumentors import instrument_all
        
        # Call instrument_all() without span_repo for now
        # Users can call instrument_all(span_repo=...) manually if they want DB persistence
        instrument_all()
    except Exception:
        # Silently fail if instrumentation can't be enabled
        # This allows the package to be imported even if dependencies are missing
        pass

# Auto-function tracing on import (can be disabled via environment variable)
_auto_function_tracing = os.getenv("LLMOBSERVE_AUTO_FUNCTION_TRACING", "true").lower() != "false"

if _auto_function_tracing:
    try:
        from llmobserve.tracing.context_propagator import enable_context_propagation
        from llmobserve.tracing.import_hook import enable_function_wrapping
        
        # Enable context propagation for threading, async, etc.
        enable_context_propagation()
        
        # Enable automatic function wrapping via import hook
        enable_function_wrapping()
    except Exception:
        # Silently fail if function tracing can't be enabled
        # This allows the package to be imported even if dependencies are missing
        pass

