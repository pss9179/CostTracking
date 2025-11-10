"""Bootstrap launcher for auto-instrumentation.

Usage:
    python -m llmobserve.run your_app.py
    python -m llmobserve.run your_app.py arg1 arg2
"""

import os
import runpy
import sys
from pathlib import Path


def main():
    """Bootstrap launcher that enables instrumentation before user code runs."""
    if len(sys.argv) < 2:
        print("Usage: python -m llmobserve.run <script> [args...]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    script_args = sys.argv[2:]
    
    # Set PROJECT_ROOT if not already set
    if "PROJECT_ROOT" not in os.environ:
        script_file = Path(script_path).resolve()
        project_root = script_file.parent
        os.environ["PROJECT_ROOT"] = str(project_root)
    
    # Enable v2 system by default when using bootstrap launcher
    if "LLMOBSERVE_USE_V2_SYSTEM" not in os.environ:
        os.environ["LLMOBSERVE_USE_V2_SYSTEM"] = "true"
    
    # Set up basic tracer provider (console exporter) for plug-and-play
    # This ensures spans are created and exported even without DB
    try:
        from llmobserve.tracing.otel_setup import setup_tracing
        setup_tracing(span_repo=None)  # Basic setup with console exporter only
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to setup tracing: {e}")
    
    # Enable auto-instrumentation and function tracing by importing llmobserve
    # This triggers instrument_all() and enables import hook v2
    try:
        import llmobserve  # This enables API instrumentation and function wrapping
    except Exception as e:
        # Best-effort: don't crash if instrumentation can't be enabled
        import warnings
        warnings.warn(f"Failed to enable auto-instrumentation: {e}")
    
    # Optionally set up DB persistence if configured
    if os.getenv("LLMOBSERVE_ENABLE_DB", "false").lower() == "true":
        try:
            from llmobserve.storage.db import init_db
            from llmobserve.storage.repo import SpanRepository
            from llmobserve.tracing.enrichers import SpanEnricher
            from llmobserve.tracing.instrumentors import instrument_all
            from llmobserve.tracing.otel_setup import setup_tracing
            
            # Initialize database
            init_db()
            
            # Create span repository and enricher
            span_repo = SpanRepository()
            span_enricher = SpanEnricher(span_repo=span_repo)
            
            # Setup tracing with span_repo for DB persistence
            setup_tracing(span_repo=span_repo)
            
            # Re-instrument with span_repo to enable DB persistence
            instrument_all(span_repo=span_repo)
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to enable DB persistence: {e}")
    
    # Run the target script
    # Replace sys.argv with script args so the script sees correct arguments
    original_argv = sys.argv[:]
    sys.argv = [script_path] + script_args
    
    try:
        # Use runpy to execute the script
        runpy.run_path(script_path, run_name="__main__")
    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    main()

