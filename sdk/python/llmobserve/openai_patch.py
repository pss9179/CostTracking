"""
Comprehensive OpenAI SDK monkey-patching for cost tracking.

Handles:
- All billable OpenAI endpoints
- Streaming responses with cancellation tracking
- Prompt caching (cached tokens)
- Proper usage extraction and cost calculation
- Token estimation for cancelled streams (using tiktoken)
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional
from llmobserve import buffer, context, pricing, config
from llmobserve.robustness import (
    check_openai_version,
    detect_patching_conflicts,
    safe_patch,
    get_patch_state,
)

logger = logging.getLogger("llmobserve")

# Try to import tiktoken for token estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    # tiktoken not available - will log warning when needed


def _get_tokenizer(model: str):
    """Get tiktoken tokenizer for a model, with fallback."""
    if not TIKTOKEN_AVAILABLE:
        return None
    
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
        return tiktoken.get_encoding("cl100k_base")


def _estimate_tokens(text: str, model: Optional[str]) -> int:
    """Estimate token count for text using tiktoken."""
    if not TIKTOKEN_AVAILABLE or not text:
        return 0
    
    try:
        encoding = _get_tokenizer(model)
        if encoding:
            return len(encoding.encode(text))
    except Exception as e:
        logger.debug(f"[llmobserve] Failed to estimate tokens: {e}")
    
    return 0


def _estimate_input_tokens_from_messages(messages, model: Optional[str]) -> int:
    """
    Estimate input tokens from chat messages.
    
    OpenAI token counting formula:
    - Each message: 3 tokens (role, content, separator)
    - Plus content length
    - Plus 3 tokens (reply priming)
    """
    if not TIKTOKEN_AVAILABLE or not messages:
        return 0
    
    try:
        encoding = _get_tokenizer(model)
        if not encoding:
            return 0
        
        total_tokens = 3  # Start with reply priming tokens
        
        for message in messages:
            total_tokens += 3  # role, content, separator
            
            # Count role tokens
            if isinstance(message, dict):
                role = message.get("role", "")
                content = message.get("content", "")
            else:
                role = getattr(message, "role", "")
                content = getattr(message, "content", "")
            
            total_tokens += len(encoding.encode(str(role)))
            total_tokens += len(encoding.encode(str(content)))
        
        return total_tokens
    except Exception as e:
        logger.debug(f"[llmobserve] Failed to estimate input tokens: {e}")
        return 0


def _extract_usage(response: Any, method_name: str) -> tuple[int, int, int]:
    """
    Extract input_tokens, output_tokens, and cached_tokens from OpenAI response.
    
    Returns:
        Tuple of (input_tokens, output_tokens, cached_tokens)
    """
    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0
    
    # Standard usage object
    if hasattr(response, "usage") and response.usage:
        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0)
        output_tokens = getattr(usage, "completion_tokens", 0)
        
        # Extract cached tokens (OpenAI prompt caching)
        if hasattr(usage, "prompt_tokens_details"):
            details = usage.prompt_tokens_details
            if details and hasattr(details, "cached_tokens"):
                cached_tokens = getattr(details, "cached_tokens", 0)
                # Subtract cached from total input
                input_tokens = input_tokens - cached_tokens
    
    return input_tokens, output_tokens, cached_tokens


def _track_openai_call(
    method_name: str,
    model: Optional[str],
    start_time: float,
    response: Any,
    error: Optional[Exception] = None,
    is_streaming: bool = False,
    stream_cancelled: bool = False,
    extra_params: Optional[dict] = None
):
    """Track a single OpenAI API call."""
    from llmobserve.retry_tracking import enrich_event_with_retry_metadata, detect_retry_from_section
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Extract usage
    input_tokens, output_tokens, cached_tokens = _extract_usage(response, method_name)
    
    # Calculate cost with cached token support
    cost = pricing.compute_cost(
        provider="openai",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens
    )
    
    # Get hierarchical section information
    section_path = context.get_section_path()
    # Generate a NEW span_id for this LLM call
    span_id = str(uuid.uuid4())
    
    # Get semantic label from semantic map
    try:
        from llmobserve.semantic_mapper import get_semantic_label_from_call_stack
        semantic_label = get_semantic_label_from_call_stack()
    except Exception:
        semantic_label = None
    # The current section's span_id becomes this event's parent
    parent_span_id = context.get_current_span_id()
    
    # Detect 429 rate limiting
    status = "cancelled" if stream_cancelled else ("error" if error else "ok")
    wait_time_ms = 0
    
    if error:
        error_str = str(error).lower()
        if "429" in error_str or "rate" in error_str:
            status = "rate_limited"
            # Try to extract wait time from error
            # (This is a simple heuristic - actual wait time detection would need more logic)
    
    # Create event with hierarchical span tracking
    event = {
        "id": str(uuid.uuid4()),
        "run_id": context.get_run_id(),
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "section": context.get_current_section(),
        "section_path": section_path,
        "span_type": "llm",
        "provider": "openai",
        "endpoint": method_name,
        "model": model,
        "tenant_id": config.get_tenant_id(),
        "customer_id": context.get_customer_id(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "status": status,
        "is_streaming": is_streaming,
        "stream_cancelled": stream_cancelled,
        "event_metadata": extra_params if extra_params else {}
    }
    
    # Enrich with retry metadata (attempt_number, is_retry, operation_id)
    event = enrich_event_with_retry_metadata(event)
    
    # Add semantic label if available
    if semantic_label:
        event["semantic_label"] = semantic_label
    
    buffer.add_event(event)


def _wrap_streaming_response(stream, method_name: str, model: Optional[str], start_time: float, messages=None):
    """
    Wrap a streaming response to track usage and handle cancellation.
    
    Accumulates chunks and emits a single event when stream completes or is cancelled.
    For cancelled streams, estimates both input and output tokens using tiktoken.
    
    Args:
        messages: Original messages/prompt for input token estimation
    """
    accumulated_usage = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}
    accumulated_content = ""  # For token estimation if cancelled
    chunks_received = 0
    cancelled = False
    tokens_estimated = False
    
    try:
        for chunk in stream:
            chunks_received += 1
            
            # Accumulate content for potential estimation
            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    accumulated_content += delta.content
            
            # Try to extract usage from chunk (OpenAI sends it in the last chunk)
            if hasattr(chunk, "usage") and chunk.usage:
                usage = chunk.usage
                accumulated_usage["input_tokens"] = getattr(usage, "prompt_tokens", 0)
                accumulated_usage["output_tokens"] = getattr(usage, "completion_tokens", 0)
                
                # Extract cached tokens
                if hasattr(usage, "prompt_tokens_details"):
                    details = usage.prompt_tokens_details
                    if details and hasattr(details, "cached_tokens"):
                        cached_tokens = getattr(details, "cached_tokens", 0)
                        accumulated_usage["cached_tokens"] = cached_tokens
                        accumulated_usage["input_tokens"] -= cached_tokens
            
            yield chunk
    except GeneratorExit:
        # Stream was cancelled by consumer
        cancelled = True
        
        # Estimate tokens if we don't have usage data
        if accumulated_usage["output_tokens"] == 0 and accumulated_content:
            estimated_output = _estimate_tokens(accumulated_content, model)
            accumulated_usage["output_tokens"] = estimated_output
            tokens_estimated = True
        
        # Estimate input tokens if we don't have usage data and have messages
        if accumulated_usage["input_tokens"] == 0 and messages:
            estimated_input = _estimate_input_tokens_from_messages(messages, model)
            accumulated_usage["input_tokens"] = estimated_input
            tokens_estimated = True
        
        raise
    except Exception as e:
        # Stream error - try to estimate tokens
        if accumulated_usage["output_tokens"] == 0 and accumulated_content:
            estimated_output = _estimate_tokens(accumulated_content, model)
            accumulated_usage["output_tokens"] = estimated_output
            tokens_estimated = True
        
        if accumulated_usage["input_tokens"] == 0 and messages:
            estimated_input = _estimate_input_tokens_from_messages(messages, model)
            accumulated_usage["input_tokens"] = estimated_input
            tokens_estimated = True
        
        _track_openai_call(
            method_name=method_name,
            model=model,
            start_time=start_time,
            response=type('obj', (object,), accumulated_usage)(),
            error=e,
            is_streaming=True,
            stream_cancelled=False,
            extra_params={"tokens_estimated": tokens_estimated}
        )
        raise
    finally:
        # Emit event after stream completes or is cancelled
        if chunks_received > 0:
            # Create a mock response object with accumulated usage
            mock_response = type('obj', (object,), {
                'usage': type('obj', (object,), {
                    'prompt_tokens': accumulated_usage["input_tokens"] + accumulated_usage["cached_tokens"],
                    'completion_tokens': accumulated_usage["output_tokens"],
                    'prompt_tokens_details': type('obj', (object,), {
                        'cached_tokens': accumulated_usage["cached_tokens"]
                    })() if accumulated_usage["cached_tokens"] > 0 else None
                })()
            })()
            
            _track_openai_call(
                method_name=method_name,
                model=model,
                start_time=start_time,
                response=mock_response,
                error=None,
                is_streaming=True,
                stream_cancelled=cancelled,
                extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
            )


def _patch_method(client_class: Any, resource_path: list[str], method_name: str, original_method: Callable):
    """
    Generic method patcher that wraps any OpenAI client method.
    
    Args:
        client_class: The client class to patch (e.g., OpenAI)
        resource_path: Path to the resource (e.g., ["chat", "completions"])
        method_name: Method to wrap (e.g., "create")
        original_method: Original unpatched method
    """
    @functools.wraps(original_method)
    def sync_wrapper(*args, **kwargs):
        # Extract model from kwargs or args
        model = kwargs.get("model", None)
        if not model and len(args) > 0 and hasattr(args[0], "model"):
            model = args[0].model
        
        # Check spending caps before making request (model-specific caps)
        from llmobserve.caps import check_spending_caps, should_check_caps
        from llmobserve import context
        if should_check_caps() and model:
            try:
                check_spending_caps(
                    provider="openai",
                    model=model,
                    customer_id=context.get_customer_id(),
                    agent=context.get_current_section() if context.get_current_section() != "/" else None,
                )
            except Exception as cap_error:
                # Re-raise BudgetExceededError, but catch other errors to fail open
                from llmobserve.caps import BudgetExceededError
                if isinstance(cap_error, BudgetExceededError):
                    raise
                # Log but don't block on other errors
                logger.debug(f"[llmobserve] Cap check error (fail-open): {cap_error}")
        
        # Check if streaming
        is_streaming = kwargs.get("stream", False)
        
        # Extract messages for input token estimation (chat endpoints)
        messages = kwargs.get("messages", None)
        
        start_time = time.time()
        endpoint = ".".join(resource_path + [method_name])
        
        try:
            response = original_method(*args, **kwargs)
            
            # Handle streaming
            if is_streaming and hasattr(response, "__iter__"):
                return _wrap_streaming_response(response, endpoint, model, start_time, messages=messages)
            
            # Non-streaming: track immediately
            _track_openai_call(
                method_name=endpoint,
                model=model,
                start_time=start_time,
                response=response,
                error=None,
                is_streaming=False,
                stream_cancelled=False
            )
            
            return response
        except Exception as e:
            # Track error
            _track_openai_call(
                method_name=endpoint,
                model=model,
                start_time=start_time,
                response=None,
                error=e,
                is_streaming=is_streaming,
                stream_cancelled=False
            )
            raise
    
    @functools.wraps(original_method)
    async def async_wrapper(*args, **kwargs):
        # Extract model
        model = kwargs.get("model", None)
        if not model and len(args) > 0 and hasattr(args[0], "model"):
            model = args[0].model
        
        # Check spending caps before making request (model-specific caps)
        from llmobserve.caps import check_spending_caps, should_check_caps
        from llmobserve import context
        if should_check_caps() and model:
            try:
                check_spending_caps(
                    provider="openai",
                    model=model,
                    customer_id=context.get_customer_id(),
                    agent=context.get_current_section() if context.get_current_section() != "/" else None,
                )
            except Exception as cap_error:
                # Re-raise BudgetExceededError, but catch other errors to fail open
                from llmobserve.caps import BudgetExceededError
                if isinstance(cap_error, BudgetExceededError):
                    raise
                # Log but don't block on other errors
                logger.debug(f"[llmobserve] Cap check error (fail-open): {cap_error}")
        
        # Check if streaming
        is_streaming = kwargs.get("stream", False)
        
        # Extract messages for input token estimation
        messages = kwargs.get("messages", None)
        
        start_time = time.time()
        endpoint = ".".join(resource_path + [method_name])
        
        try:
            response = await original_method(*args, **kwargs)
            
            # Handle async streaming
            if is_streaming and hasattr(response, "__aiter__"):
                # Wrap async stream
                async def async_stream_wrapper():
                    accumulated_usage = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}
                    accumulated_content = ""
                    chunks_received = 0
                    cancelled = False
                    tokens_estimated = False
                    
                    try:
                        async for chunk in response:
                            chunks_received += 1
                            
                            # Accumulate content for potential estimation
                            if hasattr(chunk, "choices") and len(chunk.choices) > 0:
                                delta = chunk.choices[0].delta
                                if hasattr(delta, "content") and delta.content:
                                    accumulated_content += delta.content
                            
                            # Extract usage from chunk
                            if hasattr(chunk, "usage") and chunk.usage:
                                usage = chunk.usage
                                accumulated_usage["input_tokens"] = getattr(usage, "prompt_tokens", 0)
                                accumulated_usage["output_tokens"] = getattr(usage, "completion_tokens", 0)
                                
                                if hasattr(usage, "prompt_tokens_details"):
                                    details = usage.prompt_tokens_details
                                    if details and hasattr(details, "cached_tokens"):
                                        cached_tokens = getattr(details, "cached_tokens", 0)
                                        accumulated_usage["cached_tokens"] = cached_tokens
                                        accumulated_usage["input_tokens"] -= cached_tokens
                            
                            yield chunk
                    except GeneratorExit:
                        cancelled = True
                        
                        # Estimate tokens if we don't have usage data
                        if accumulated_usage["output_tokens"] == 0 and accumulated_content:
                            estimated_output = _estimate_tokens(accumulated_content, model)
                            accumulated_usage["output_tokens"] = estimated_output
                            tokens_estimated = True
                        
                        # Estimate input tokens
                        if accumulated_usage["input_tokens"] == 0 and messages:
                            estimated_input = _estimate_input_tokens_from_messages(messages, model)
                            accumulated_usage["input_tokens"] = estimated_input
                            tokens_estimated = True
                        
                        raise
                    finally:
                        if chunks_received > 0:
                            mock_response = type('obj', (object,), {
                                'usage': type('obj', (object,), {
                                    'prompt_tokens': accumulated_usage["input_tokens"] + accumulated_usage["cached_tokens"],
                                    'completion_tokens': accumulated_usage["output_tokens"],
                                    'prompt_tokens_details': type('obj', (object,), {
                                        'cached_tokens': accumulated_usage["cached_tokens"]
                                    })() if accumulated_usage["cached_tokens"] > 0 else None
                                })()
                            })()
                            
                            _track_openai_call(
                                method_name=endpoint,
                                model=model,
                                start_time=start_time,
                                response=mock_response,
                                error=None,
                                is_streaming=True,
                                stream_cancelled=cancelled,
                                extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
                            )
                
                return async_stream_wrapper()
            
            # Non-streaming async: track immediately
            _track_openai_call(
                method_name=endpoint,
                model=model,
                start_time=start_time,
                response=response,
                error=None,
                is_streaming=False,
                stream_cancelled=False
            )
            
            return response
        except Exception as e:
            _track_openai_call(
                method_name=endpoint,
                model=model,
                start_time=start_time,
                response=None,
                error=e,
                is_streaming=is_streaming,
                stream_cancelled=False
            )
            raise
    
    # Determine if original is async
    import inspect
    if inspect.iscoroutinefunction(original_method):
        return async_wrapper
    else:
        return sync_wrapper


def patch_openai():
    """
    Monkey-patch OpenAI SDK to track all billable endpoints.
    
    Patched endpoints:
    - chat.completions.create (with streaming)
    - completions.create (with streaming)
    - embeddings.create
    - audio.transcriptions.create
    - audio.translations.create
    - audio.speech.create
    - images.generate
    - moderations.create
    - fine_tuning.jobs.create
    - batches.create
    - And more...
    """
    try:
        import openai
        from openai import resources
    except ImportError:
        logger.debug("[llmobserve] OpenAI not installed, skipping OpenAI patching")
        return
    
    # Check if already patched
    if hasattr(resources.chat.Completions, "_llmobserve_patched"):
        logger.debug("[llmobserve] OpenAI already patched, skipping")
        return
    
    # Version compatibility check
    version_status = check_openai_version()
    if version_status == "warning":
        logger.warning(
            f"[llmobserve] OpenAI SDK version {getattr(openai, '__version__', 'unknown')} "
            "may have compatibility issues. Please report any problems."
        )
    
    # Detect conflicts with other libraries
    conflicts = detect_patching_conflicts()
    if conflicts:
        logger.warning(
            f"[llmobserve] Detected potential conflicts with other libraries: {conflicts}. "
            "This may cause tracking issues. Consider using only one observability library."
        )
    
    # List of resources to patch: (resource_class, method_name, endpoint_name)
    endpoints_to_patch = [
        (resources.chat.Completions, "create", "chat.completions"),
        (resources.Completions, "create", "completions"),
        (resources.Embeddings, "create", "embeddings"),
    ]
    
    # Audio endpoints
    try:
        endpoints_to_patch.extend([
            (resources.audio.Transcriptions, "create", "audio.transcriptions"),
            (resources.audio.Translations, "create", "audio.translations"),
            (resources.audio.Speech, "create", "audio.speech"),
        ])
    except AttributeError:
        pass  # Audio resources not available in this OpenAI version
    
    # Images endpoints
    try:
        endpoints_to_patch.extend([
            (resources.Images, "generate", "images.generate"),
            (resources.Images, "create_variation", "images.create_variation"),
            (resources.Images, "edit", "images.edit"),
        ])
    except AttributeError:
        pass  # Images resources not available
    
    # Other endpoints
    try:
        endpoints_to_patch.append((resources.Moderations, "create", "moderations"))
    except AttributeError:
        pass
    
    try:
        endpoints_to_patch.append((resources.fine_tuning.Jobs, "create", "fine_tuning.jobs"))
    except AttributeError:
        pass
    
    try:
        endpoints_to_patch.append((resources.Batches, "create", "batches"))
    except AttributeError:
        pass
    
    patched_count = 0
    failed_count = 0
    
    for resource_class, method_name, endpoint_name in endpoints_to_patch:
        if not hasattr(resource_class, method_name):
            logger.debug(f"[llmobserve] Skipping {endpoint_name}.{method_name} (not found)")
            continue
        
        original_method = getattr(resource_class, method_name)
        
        # Create patch function that wraps the original method
        def patch_wrapper(original):
            return _patch_method(
                resource_class,
                endpoint_name.split("."),
                method_name,
                original
            )
        
        success, error = safe_patch(
            resource_class,
            method_name,
            endpoint_name,
            patch_wrapper,
            original_method
        )
        
        if success:
            patched_count += 1
        else:
            failed_count += 1
            if error:
                logger.error(f"[llmobserve] Failed to patch {endpoint_name}.{method_name}: {error}")
    
    # Mark as patched (only if at least one endpoint was patched)
    if patched_count > 0:
        # Use setattr to avoid type checker issues
        setattr(resources.chat.Completions, "_llmobserve_patched", True)
        logger.info(
            f"[llmobserve] OpenAI SDK patched successfully "
            f"({patched_count} endpoints patched, {failed_count} failed)"
        )
    else:
        logger.warning(
            f"[llmobserve] Failed to patch any OpenAI endpoints. "
            "OpenAI tracking will not work. Check logs for details."
        )
