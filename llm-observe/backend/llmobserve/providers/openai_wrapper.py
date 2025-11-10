"""Lightweight wrapper for OpenAI client to track costs."""

import time
from typing import Any, Optional

from opentelemetry import baggage

from llmobserve.exporter import get_exporter
from llmobserve.pricing import pricing_registry
from llmobserve.tracer import get_current_trace_id, get_current_span_id


def openai_client(original_client: Any) -> Any:
    """
    Wrap OpenAI client to track costs.

    Usage:
        from llmobserve.providers import openai_client
        client = openai_client(openai.OpenAI())
    """
    # Create wrapper class
    class TrackedOpenAIClient:
        def __init__(self, client):
            self._client = client
            self._exporter = get_exporter()

        def __getattr__(self, name):
            attr = getattr(self._client, name)
            if name == "chat":
                return TrackedChat(attr, self._exporter)
            elif name == "embeddings":
                return TrackedEmbeddings(attr, self._exporter)
            return attr

    class TrackedChat:
        def __init__(self, chat, exporter):
            self._chat = chat
            self._exporter = exporter

        @property
        def completions(self):
            return TrackedCompletions(self._chat.completions, self._exporter)

    class TrackedCompletions:
        def __init__(self, completions, exporter):
            self._completions = completions
            self._exporter = exporter

        def create(self, *args, **kwargs):
            start_time = time.time()
            model = kwargs.get("model", "gpt-3.5-turbo")
            
            # Call original
            response = self._completions.create(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract usage
            if hasattr(response, "usage"):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens
            else:
                prompt_tokens = completion_tokens = total_tokens = 0
            
            # Calculate cost
            cost_usd = pricing_registry.cost_for(model, prompt_tokens, completion_tokens)
            
            # Get context
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record cost
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider="openai",
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                model=model,
                trace_id=trace_id,
                span_id=span_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                operation="chat",
            )
            
            return response

    class TrackedEmbeddings:
        def __init__(self, embeddings, exporter):
            self._embeddings = embeddings
            self._exporter = exporter

        def create(self, *args, **kwargs):
            start_time = time.time()
            model = kwargs.get("model", "text-embedding-3-small")
            
            # Call original
            response = self._embeddings.create(*args, **kwargs)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract usage
            if hasattr(response, "usage"):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = 0
                total_tokens = response.usage.total_tokens
            else:
                prompt_tokens = total_tokens = 0
                completion_tokens = 0
            
            # Calculate cost
            cost_usd = pricing_registry.cost_for(model, prompt_tokens, completion_tokens)
            
            # Get context
            tenant_id = baggage.get_baggage("tenant_id") or "default"
            workflow_id = baggage.get_baggage("workflow_id")
            trace_id = get_current_trace_id()
            span_id = get_current_span_id()
            
            # Record cost
            self._exporter.record_cost(
                tenant_id=tenant_id,
                provider="openai",
                cost_usd=cost_usd,
                duration_ms=duration_ms,
                workflow_id=workflow_id,
                model=model,
                trace_id=trace_id,
                span_id=span_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                operation="embedding",
            )
            
            return response

    return TrackedOpenAIClient(original_client)

