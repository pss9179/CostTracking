"""
OpenAI client wrapper for tool-calling workflows.

Wraps openai.chat.completions.create() to extract tool_calls
and create proper LLM spans with tool_call metadata.
"""
import functools
import time
import uuid
from typing import Any, List, Dict, Optional
import logging

from llmobserve import context, buffer, config

logger = logging.getLogger("llmobserve")


def wrap_openai_client(client: Any) -> Any:
    """
    Wrap OpenAI client's chat.completions.create method.
    
    Extracts tool_calls from responses and creates LLM spans.
    """
    if not hasattr(client, "chat"):
        logger.warning("[llmobserve] OpenAI client has no 'chat' attribute, cannot wrap")
        return client
    
    if not hasattr(client.chat, "completions"):
        logger.warning("[llmobserve] OpenAI client.chat has no 'completions' attribute, cannot wrap")
        return client
    
    # Check if already wrapped
    if getattr(client.chat.completions, "__llmobserve_wrapped__", False):
        return client
    
    # Wrap the create method
    original_create = client.chat.completions.create
    
    @functools.wraps(original_create)
    def wrapped_create(*args, **kwargs):
        return _execute_with_llm_span(original_create, args, kwargs, is_streaming=False)
    
    client.chat.completions.create = wrapped_create
    client.chat.completions.__llmobserve_wrapped__ = True
    
    return client


def _execute_with_llm_span(
    original_func: Any,
    args: tuple,
    kwargs: dict,
    is_streaming: bool
) -> Any:
    """
    Execute OpenAI call within an LLM span context.
    
    Extracts model, tokens, cost, and tool_calls from response.
    """
    # Get section stack
    stack = context._get_section_stack()
    
    # Ensure trace_id is initialized
    trace_id = context.get_trace_id()
    
    # Generate span_id for this LLM call
    span_id = str(uuid.uuid4())
    
    # Get parent_span_id from stack
    parent_span_id = stack[-1]["span_id"] if stack else None
    
    # Extract model from kwargs
    model = kwargs.get("model", "unknown")
    
    # Create section label
    section_label = f"llm:openai"
    
    # Push LLM entry onto stack
    section_entry = {
        "label": section_label,
        "span_id": span_id,
        "parent_span_id": parent_span_id
    }
    stack.append(section_entry)
    
    # Record start time
    start_time = time.time()
    
    # Track state
    error_message = None
    status = "ok"
    response = None
    tool_calls_metadata = []
    input_tokens = 0
    output_tokens = 0
    cost_usd = 0.0
    
    try:
        # Execute the actual OpenAI call
        response = original_func(*args, **kwargs)
        
        # Extract usage and tool_calls from response
        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "prompt_tokens", 0)
            output_tokens = getattr(response.usage, "completion_tokens", 0)
            
            # Calculate cost (use existing pricing registry)
            from llmobserve.pricing import compute_cost
            cost_usd = compute_cost(
                provider="openai",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        # Extract tool_calls from first choice
        if hasattr(response, "choices") and len(response.choices) > 0:
            first_choice = response.choices[0]
            if hasattr(first_choice, "message") and hasattr(first_choice.message, "tool_calls"):
                if first_choice.message.tool_calls:
                    for tc in first_choice.message.tool_calls:
                        tool_calls_metadata.append({
                            "id": getattr(tc, "id", "unknown"),
                            "type": getattr(tc, "type", "function"),
                            "function": {
                                "name": getattr(tc.function, "name", "unknown") if hasattr(tc, "function") else "unknown",
                                "arguments": getattr(tc.function, "arguments", "{}") if hasattr(tc, "function") else "{}"
                            }
                        })
        
        return response
    except Exception as e:
        error_message = str(e)
        status = "error"
        raise  # Re-raise to preserve user's error handling
    finally:
        # Calculate duration
        end_time = time.time()
        latency_ms = max(0.0, (end_time - start_time) * 1000)
        
        # Emit span event
        try:
            if config.is_enabled():
                metadata = {
                    "model": model,
                    "provider": "openai",
                }
                
                # Add tool_calls to metadata (not as spans!)
                if tool_calls_metadata:
                    metadata["tool_calls"] = tool_calls_metadata
                    metadata["tool_calls_count"] = len(tool_calls_metadata)
                
                if error_message:
                    metadata["error"] = error_message
                
                event = {
                    "id": str(uuid.uuid4()),
                    "trace_id": trace_id,
                    "run_id": context.get_run_id(),
                    "span_id": span_id,
                    "parent_span_id": parent_span_id,
                    "section": section_label,
                    "section_path": context.get_section_path(),
                    "span_type": "llm",
                    "provider": "openai",
                    "endpoint": "chat.completions",
                    "model": model,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "status": status,
                    "customer_id": context.get_customer_id(),
                    "event_metadata": metadata,
                    "is_streaming": is_streaming,
                    "stream_cancelled": False,
                    "tenant_id": context.get_tenant_id(),
                }
                buffer.add_event(event)
        except Exception as e:
            logger.debug(f"[llmobserve] Failed to emit LLM span: {e}")
            pass  # Fail silently
        
        # Pop section from stack
        try:
            if stack and len(stack) > 0 and stack[-1].get("span_id") == span_id:
                stack.pop()
        except (IndexError, KeyError):
            pass

