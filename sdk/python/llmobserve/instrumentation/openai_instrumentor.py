"""
OpenAI SDK instrumentor with version guards and fail-open safety.

Provides modular instrumentation for OpenAI SDK with:
- Version compatibility checks
- Fail-open safety (never breaks user code)
- Support for all billable endpoints
"""
import functools
import time
import uuid
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("llmobserve")

# Import shared utilities
from llmobserve import buffer, context, pricing, config
from llmobserve.instrumentation.utils import (
    get_tokenizer,
    estimate_tokens,
    estimate_input_tokens_from_messages,
    extract_openai_usage,
    track_openai_call,
)

# Try to import tiktoken for token estimation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.debug("[llmobserve] tiktoken not installed - cancelled stream costs will be $0")


# Supported OpenAI SDK versions
SUPPORTED_OPENAI_VERSIONS = {
    "1.0": "1.0.0",  # Minimum supported version
    "1.1": "1.1.0",
    "1.2": "1.2.0",
    "1.3": "1.3.0",
    "1.4": "1.4.0",
    "1.5": "1.5.0",
    "1.6": "1.6.0",
    "1.7": "1.7.0",
    "1.8": "1.8.0",
    "1.9": "1.9.0",
    "1.10": "1.10.0",
    "1.11": "1.11.0",
    "1.12": "1.12.0",
}


def check_openai_version() -> tuple[bool, Optional[str]]:
    """
    Check if OpenAI SDK version is supported.
    
    Returns:
        (is_supported: bool, version: Optional[str])
    """
    try:
        import openai
        version = getattr(openai, "__version__", None)
        
        if version is None:
            logger.warning("[llmobserve] OpenAI SDK version unknown - proceeding with caution")
            return True, None  # Fail-open: allow unknown versions
        
        # Check major version
        major_version = version.split(".")[0]
        
        if major_version in SUPPORTED_OPENAI_VERSIONS:
            logger.debug(f"[llmobserve] OpenAI SDK version {version} is supported")
            return True, version
        
        # Check if it's a newer minor version of supported major
        try:
            major_int = int(major_version)
            if major_int >= 1:
                logger.warning(
                    f"[llmobserve] OpenAI SDK version {version} not explicitly tested. "
                    "Proceeding with caution. If you encounter issues, please report them."
                )
                return True, version  # Fail-open: allow newer versions
        except ValueError:
            pass
        
        logger.warning(
            f"[llmobserve] OpenAI SDK version {version} may be incompatible. "
            "Skipping instrumentation to avoid breaking user code."
        )
        return False, version
        
    except ImportError:
        logger.debug("[llmobserve] OpenAI SDK not installed")
        return False, None


def _wrap_streaming_response(stream, method_name: str, model: Optional[str], start_time: float, messages=None):
    """
    Wrap a streaming response with fail-open safety.
    
    Never breaks user code - always yields chunks even if tracking fails.
    """
    accumulated_usage = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0}
    accumulated_content = ""
    chunks_received = 0
    cancelled = False
    tokens_estimated = False
    
    try:
        for chunk in stream:
            chunks_received += 1
            
            # Accumulate content for potential estimation
            try:
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
            except Exception as e:
                logger.debug(f"[llmobserve] Failed to extract usage from chunk: {e}")
            
            yield chunk
            
    except GeneratorExit:
        cancelled = True
        
        # Estimate tokens if needed (fail-open)
        try:
            if accumulated_usage["output_tokens"] == 0 and accumulated_content:
                accumulated_usage["output_tokens"] = estimate_tokens(accumulated_content, model)
                tokens_estimated = True
            
            if accumulated_usage["input_tokens"] == 0 and messages:
                accumulated_usage["input_tokens"] = estimate_input_tokens_from_messages(messages, model)
                tokens_estimated = True
        except Exception as e:
            logger.debug(f"[llmobserve] Failed to estimate tokens: {e}")
        
        raise
    except Exception as e:
        # Stream error - try to estimate tokens (fail-open)
        try:
            if accumulated_usage["output_tokens"] == 0 and accumulated_content:
                accumulated_usage["output_tokens"] = estimate_tokens(accumulated_content, model)
                tokens_estimated = True
            
            if accumulated_usage["input_tokens"] == 0 and messages:
                accumulated_usage["input_tokens"] = estimate_input_tokens_from_messages(messages, model)
                tokens_estimated = True
        except Exception:
            pass
        
        # Track error (fail-open)
        try:
            track_openai_call(
                method_name=method_name,
                model=model,
                start_time=start_time,
                response=type('obj', (object,), accumulated_usage)(),
                error=e,
                is_streaming=True,
                stream_cancelled=False,
                extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
            )
        except Exception:
            logger.debug(f"[llmobserve] Failed to track error: {e}")
        
        raise
    finally:
        # Emit event after stream completes (fail-open)
        if chunks_received > 0:
            try:
                mock_response = type('obj', (object,), {
                    'usage': type('obj', (object,), {
                        'prompt_tokens': accumulated_usage["input_tokens"] + accumulated_usage["cached_tokens"],
                        'completion_tokens': accumulated_usage["output_tokens"],
                        'prompt_tokens_details': type('obj', (object,), {
                            'cached_tokens': accumulated_usage["cached_tokens"]
                        })() if accumulated_usage["cached_tokens"] > 0 else None
                    })()
                })()
                
                track_openai_call(
                    method_name=method_name,
                    model=model,
                    start_time=start_time,
                    response=mock_response,
                    error=None,
                    is_streaming=True,
                    stream_cancelled=cancelled,
                    extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
                )
            except Exception as e:
                logger.debug(f"[llmobserve] Failed to track stream completion: {e}")


def _create_safe_wrapper(
    resource_class: Any,
    resource_path: list[str],
    method_name: str,
    original_method: Callable
) -> Callable:
    """
    Create a fail-open wrapper for an OpenAI method.
    
    Never breaks user code - always calls original method even if tracking fails.
    """
    @functools.wraps(original_method)
    def sync_wrapper(*args, **kwargs):
        # Extract model (fail-open)
        model = kwargs.get("model", None)
        if not model and len(args) > 0 and hasattr(args[0], "model"):
            try:
                model = args[0].model
            except Exception:
                pass
        
        # Check if streaming
        is_streaming = kwargs.get("stream", False)
        messages = kwargs.get("messages", None)
        
        start_time = time.time()
        endpoint = ".".join(resource_path + [method_name])
        
        try:
            # Call original method (this is the critical path - never fail here)
            response = original_method(*args, **kwargs)
            
            # Handle streaming (fail-open)
            if is_streaming and hasattr(response, "__iter__"):
                try:
                    return _wrap_streaming_response(response, endpoint, model, start_time, messages=messages)
                except Exception as e:
                    logger.debug(f"[llmobserve] Failed to wrap stream: {e}")
                    return response  # Return original stream
            
            # Non-streaming: track immediately (fail-open)
            try:
                track_openai_call(
                    method_name=endpoint,
                    model=model,
                    start_time=start_time,
                    response=response,
                    error=None,
                    is_streaming=False,
                    stream_cancelled=False
                )
            except Exception as e:
                logger.debug(f"[llmobserve] Failed to track call: {e}")
            
            return response
            
        except Exception as e:
            # Track error (fail-open)
            try:
                track_openai_call(
                    method_name=endpoint,
                    model=model,
                    start_time=start_time,
                    response=None,
                    error=e,
                    is_streaming=is_streaming,
                    stream_cancelled=False
                )
            except Exception:
                logger.debug(f"[llmobserve] Failed to track error: {e}")
            
            # Always re-raise original exception
            raise
    
    @functools.wraps(original_method)
    async def async_wrapper(*args, **kwargs):
        # Same logic as sync_wrapper but async
        model = kwargs.get("model", None)
        if not model and len(args) > 0 and hasattr(args[0], "model"):
            try:
                model = args[0].model
            except Exception:
                pass
        
        is_streaming = kwargs.get("stream", False)
        messages = kwargs.get("messages", None)
        
        start_time = time.time()
        endpoint = ".".join(resource_path + [method_name])
        
        try:
            response = await original_method(*args, **kwargs)
            
            if is_streaming and hasattr(response, "__aiter__"):
                # Wrap async stream (full implementation)
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
                            try:
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
                            except Exception as e:
                                logger.debug(f"[llmobserve] Failed to extract usage from chunk: {e}")
                            
                            yield chunk
                    except GeneratorExit:
                        cancelled = True
                        
                        # Estimate tokens if needed (fail-open)
                        try:
                            if accumulated_usage["output_tokens"] == 0 and accumulated_content:
                                accumulated_usage["output_tokens"] = estimate_tokens(accumulated_content, model)
                                tokens_estimated = True
                            
                            if accumulated_usage["input_tokens"] == 0 and messages:
                                accumulated_usage["input_tokens"] = estimate_input_tokens_from_messages(messages, model)
                                tokens_estimated = True
                        except Exception:
                            pass
                        
                        raise
                    except Exception as e:
                        # Stream error - try to estimate tokens (fail-open)
                        try:
                            if accumulated_usage["output_tokens"] == 0 and accumulated_content:
                                accumulated_usage["output_tokens"] = estimate_tokens(accumulated_content, model)
                                tokens_estimated = True
                            
                            if accumulated_usage["input_tokens"] == 0 and messages:
                                accumulated_usage["input_tokens"] = estimate_input_tokens_from_messages(messages, model)
                                tokens_estimated = True
                        except Exception:
                            pass
                        
                        # Track error (fail-open)
                        try:
                            track_openai_call(
                                method_name=method_name,
                                model=model,
                                start_time=start_time,
                                response=type('obj', (object,), accumulated_usage)(),
                                error=e,
                                is_streaming=True,
                                stream_cancelled=False,
                                extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
                            )
                        except Exception:
                            logger.debug(f"[llmobserve] Failed to track error: {e}")
                        
                        raise
                    finally:
                        # Emit event after stream completes (fail-open)
                        if chunks_received > 0:
                            try:
                                mock_response = type('obj', (object,), {
                                    'usage': type('obj', (object,), {
                                        'prompt_tokens': accumulated_usage["input_tokens"] + accumulated_usage["cached_tokens"],
                                        'completion_tokens': accumulated_usage["output_tokens"],
                                        'prompt_tokens_details': type('obj', (object,), {
                                            'cached_tokens': accumulated_usage["cached_tokens"]
                                        })() if accumulated_usage["cached_tokens"] > 0 else None
                                    })()
                                })()
                                
                                track_openai_call(
                                    method_name=method_name,
                                    model=model,
                                    start_time=start_time,
                                    response=mock_response,
                                    error=None,
                                    is_streaming=True,
                                    stream_cancelled=cancelled,
                                    extra_params={"tokens_estimated": tokens_estimated} if tokens_estimated else None
                                )
                            except Exception as e:
                                logger.debug(f"[llmobserve] Failed to track stream completion: {e}")
                
                try:
                    return async_stream_wrapper()
                except Exception as e:
                    logger.debug(f"[llmobserve] Failed to wrap async stream: {e}")
                    return response  # Return original stream
            
            try:
                track_openai_call(
                    method_name=endpoint,
                    model=model,
                    start_time=start_time,
                    response=response,
                    error=None,
                    is_streaming=False,
                    stream_cancelled=False
                )
            except Exception:
                pass
            
            return response
            
        except Exception as e:
            try:
                track_openai_call(
                    method_name=endpoint,
                    model=model,
                    start_time=start_time,
                    response=None,
                    error=e,
                    is_streaming=is_streaming,
                    stream_cancelled=False
                )
            except Exception:
                pass
            raise
    
    # Return appropriate wrapper based on method type
    import inspect
    if inspect.iscoroutinefunction(original_method):
        return async_wrapper
    else:
        return sync_wrapper


def instrument_openai() -> bool:
    """
    Instrument OpenAI SDK with fail-open safety and version guards.
    
    Returns:
        True if instrumentation succeeded, False otherwise
    """
    # Check version compatibility
    is_supported, version = check_openai_version()
    if not is_supported:
        logger.warning(f"[llmobserve] Skipping OpenAI instrumentation (version {version} not supported)")
        return False
    
    try:
        import openai
        from openai import resources
    except ImportError:
        logger.debug("[llmobserve] OpenAI not installed, skipping instrumentation")
        return False
    
    # Check if already instrumented
    if hasattr(resources.chat.Completions, "_llmobserve_instrumented"):
        logger.debug("[llmobserve] OpenAI already instrumented, skipping")
        return True
    
    # List of endpoints to instrument
    endpoints_to_patch = [
        (resources.chat.Completions, "create", "chat.completions"),
        (resources.Completions, "create", "completions"),
        (resources.Embeddings, "create", "embeddings"),
    ]
    
    # Audio endpoints (fail-open if not available)
    try:
        endpoints_to_patch.extend([
            (resources.audio.Transcriptions, "create", "audio.transcriptions"),
            (resources.audio.Translations, "create", "audio.translations"),
            (resources.audio.Speech, "create", "audio.speech"),
        ])
    except AttributeError:
        logger.debug("[llmobserve] Audio resources not available in this OpenAI version")
    
    # Images endpoints
    try:
        endpoints_to_patch.extend([
            (resources.Images, "generate", "images.generate"),
            (resources.Images, "create_variation", "images.create_variation"),
            (resources.Images, "edit", "images.edit"),
        ])
    except AttributeError:
        logger.debug("[llmobserve] Images resources not available")
    
    # Other endpoints
    for resource_name, method_name, endpoint_name in [
        ("Moderations", "create", "moderations"),
        ("fine_tuning.Jobs", "create", "fine_tuning.jobs"),
        ("Batches", "create", "batches"),
    ]:
        try:
            resource_class = getattr(resources, resource_name.split(".")[0])
            if "." in resource_name:
                for part in resource_name.split(".")[1:]:
                    resource_class = getattr(resource_class, part)
            endpoints_to_patch.append((resource_class, method_name, endpoint_name))
        except AttributeError:
            logger.debug(f"[llmobserve] {endpoint_name} not available")
    
    patched_count = 0
    failed_count = 0
    
    # Instrument each endpoint (fail-open)
    for resource_class, method_name, endpoint_name in endpoints_to_patch:
        try:
            if not hasattr(resource_class, method_name):
                logger.debug(f"[llmobserve] Skipping {endpoint_name}.{method_name} (not found)")
                continue
            
            original_method = getattr(resource_class, method_name)
            
            # Check if already instrumented
            if hasattr(original_method, "_llmobserve_instrumented"):
                logger.debug(f"[llmobserve] {endpoint_name}.{method_name} already instrumented")
                continue
            
            # Create safe wrapper
            wrapped_method = _create_safe_wrapper(
                resource_class,
                endpoint_name.split("."),
                method_name,
                original_method
            )
            
            # Apply instrumentation (fail-open)
            try:
                setattr(resource_class, method_name, wrapped_method)
                wrapped_method._llmobserve_instrumented = True
                wrapped_method._llmobserve_original = original_method
                patched_count += 1
                logger.debug(f"[llmobserve] ✓ Instrumented {endpoint_name}.{method_name}")
            except Exception as e:
                logger.warning(f"[llmobserve] Failed to instrument {endpoint_name}.{method_name}: {e}")
                failed_count += 1
                
        except Exception as e:
            logger.warning(f"[llmobserve] Error instrumenting {endpoint_name}.{method_name}: {e}")
            failed_count += 1
    
    # Mark as instrumented (only if at least one endpoint succeeded)
    if patched_count > 0:
        try:
            setattr(resources.chat.Completions, "_llmobserve_instrumented", True)
            logger.info(
                f"[llmobserve] OpenAI SDK instrumented successfully "
                f"({patched_count} endpoints, {failed_count} failed)"
            )
            return True
        except Exception:
            pass
    
    if failed_count > 0:
        logger.warning(
            f"[llmobserve] OpenAI instrumentation partially failed "
            f"({patched_count} succeeded, {failed_count} failed)"
        )
        return patched_count > 0
    
    logger.warning("[llmobserve] Failed to instrument any OpenAI endpoints")
    return False

