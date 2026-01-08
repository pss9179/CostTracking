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
    set_trace_id,
    get_trace_id,
    export as export_context,
    import_context,
    # Voice AI tracking
    voice_call,
    diy_voice_call,
    get_voice_call_id,
    set_voice_call_id,
    get_voice_platform,
    set_voice_platform,
)
from llmobserve.agent_wrapper import agent
from llmobserve.tool_wrapper import tool, wrap_tool
from llmobserve.framework_hooks import wrap_all_tools, try_patch_frameworks
from llmobserve.distributed import export_context as export_distributed_context, import_context as import_distributed_context
from llmobserve.llm_wrappers import wrap_openai_client, wrap_anthropic_client
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
from llmobserve.caps import BudgetExceededError, CapCheckError
from llmobserve.grpc_costs import configure_grpc_cost, clear_grpc_costs
from llmobserve.static_analyzer import preview_agent_tree, analyze_code_file, analyze_code_string
from llmobserve.multi_language_analyzer import (
    preview_multi_language_tree,
    analyze_multi_language_file,
    analyze_multi_language_code,
)

# AI-powered instrumentation (uses LLMObserve backend)
try:
    from llmobserve.ai_instrument import (
        AIInstrumenter,
        preview_instrumentation,
        auto_instrument as ai_auto_instrument,
    )
    _AI_INSTRUMENT_AVAILABLE = True
except ImportError:
    _AI_INSTRUMENT_AVAILABLE = False
    AIInstrumenter = None
    preview_instrumentation = None
    ai_auto_instrument = None

__version__ = "0.3.2"  # Fix HTTP/2 timeout issue with Railway

__all__ = [
    "observe",
    "section",
    "trace",
    # New tool wrapping system
    "agent",
    "tool",
    "wrap_tool",
    "wrap_all_tools",
    # LLM wrappers for tool-calling workflows
    "wrap_openai_client",
    "wrap_anthropic_client",
    "set_run_id",
    "get_run_id",
    "set_customer_id",
    "get_customer_id",
    "set_trace_id",
    "get_trace_id",
    # Context export/import for workers
    "export_context",
    "import_context",
    # Distributed tracing (for background workers)
    "export_distributed_context",
    "import_distributed_context",
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
    # Spending caps
    "BudgetExceededError",
    "CapCheckError",
    # gRPC cost configuration
    "configure_grpc_cost",
    "clear_grpc_costs",
    # Voice AI tracking
    "voice_call",
    "diy_voice_call",
    "get_voice_call_id",
    "set_voice_call_id",
    "get_voice_platform",
    "set_voice_platform",
    # Static analysis (preview before execution)
    "preview_agent_tree",
    "analyze_code_file",
    "analyze_code_string",
    # Multi-language static analysis
    "preview_multi_language_tree",
    "analyze_multi_language_file",
    "analyze_multi_language_code",
    # AI-powered instrumentation (optional)
    "AIInstrumenter",
    "preview_instrumentation",
    "ai_auto_instrument",
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
