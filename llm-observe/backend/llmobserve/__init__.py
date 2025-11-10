"""LLMObserve SDK - Lightweight AI usage and cost tracking."""

from llmobserve.exporter import get_exporter
from llmobserve.tracer import init_tracer, get_tracer, get_current_trace_id, get_current_span_id
from llmobserve.langchain_handler import LLMObserveHandler

__version__ = "0.1.0"

__all__ = [
    "init_tracer",
    "get_tracer",
    "get_current_trace_id",
    "get_current_span_id",
    "LLMObserveHandler",
    "get_exporter",
]


def use_asgi(app):
    """
    Wrap ASGI app to enable middleware.

    Usage:
        from llmobserve import use_asgi
        app = use_asgi(app)
    """
    # Middleware is already added in main.py
    # This is a placeholder for SDK-style usage
    return app

