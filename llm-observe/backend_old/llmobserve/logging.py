"""Structured logging with structlog."""

import logging
import sys
from typing import Any, Optional

import structlog
from opentelemetry import trace

from llmobserve.config import settings


def configure_logging() -> None:
    """Configure structlog with JSON output and OpenTelemetry trace context."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_trace_context,
            _redact_secrets,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _add_trace_context(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add OpenTelemetry trace context to log events."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"

    # Add tenant_id from context vars if available
    tenant_id = structlog.contextvars.get_contextvars().get("tenant_id")
    if tenant_id:
        event_dict["tenant_id"] = tenant_id

    return event_dict


def _redact_secrets(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Redact sensitive information from logs."""
    secret_keys = ["api_key", "password", "secret", "token", "authorization"]
    for key in list(event_dict.keys()):
        key_lower = key.lower()
        if any(secret in key_lower for secret in secret_keys):
            event_dict[key] = "[REDACTED]"
    return event_dict


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Initialize logging on import
configure_logging()

