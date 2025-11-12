"""
LLM Observe SDK - Auto-instrumentation for LLM and API cost tracking.
"""

# Configure logging first
import logging
import sys

# Set up logger with sensible defaults
_logger = logging.getLogger("llmobserve")
if not _logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            '[llmobserve] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    _logger.addHandler(handler)
    _logger.setLevel(logging.WARNING)  # Default to WARNING, can be overridden

from llmobserve.observe import observe
from llmobserve.context import (
    section,
    set_run_id,
    get_run_id,
    set_customer_id,
    get_customer_id,
    export as export_context,
    import_context,
)
from llmobserve.instrumentation import auto_instrument, is_instrumented, is_initialized
from llmobserve.decorators import trace
from llmobserve.celery_support import (
    observe_task,
    get_current_context,
    restore_context,
    with_context,
    patch_celery_task,
    observe_rq_job
)
from llmobserve.retry_tracking import with_retry_tracking, get_retry_metadata
from llmobserve.middleware import (
    ObservabilityMiddleware,
    flask_before_request,
    django_middleware
)
from llmobserve.robustness import get_patch_state, validate_patch_integrity

__version__ = "0.3.0"  # API key-based authentication

__all__ = [
    "observe",
    "section",
    "trace",
    "set_run_id",
    "get_run_id",
    "set_customer_id",
    "get_customer_id",
    # Context export/import for workers
    "export_context",
    "import_context",
    # New modular instrumentation API
    "auto_instrument",
    "is_instrumented",
    "is_initialized",
    # Background worker support
    "observe_task",
    "get_current_context",
    "restore_context",
    "with_context",
    "patch_celery_task",
    "observe_rq_job",
    # Retry tracking
    "with_retry_tracking",
    "get_retry_metadata",
    # Framework middleware
    "ObservabilityMiddleware",
    "flask_before_request",
    "django_middleware",
    # Debugging/robustness
    "get_patch_state",
    "validate_patch_integrity",
]


def set_log_level(level: str):
    """
    Set logging level for llmobserve.
    
    Args:
        level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    _logger.setLevel(numeric_level)
    _logger.info(f"[llmobserve] Log level set to {level}")
