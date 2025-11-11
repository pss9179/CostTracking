"""
LLM Observe SDK - Auto-instrumentation for LLM and API cost tracking.
"""

from llmobserve.observe import observe
from llmobserve.context import section, set_run_id, get_run_id, set_tenant_id, get_tenant_id, set_customer_id, get_customer_id
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

__version__ = "0.2.0"

__all__ = [
    "observe",
    "section",
    "trace",
    "set_run_id",
    "get_run_id",
    "set_tenant_id",
    "get_tenant_id",
    "set_customer_id",
    "get_customer_id",
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
]

