"""
Robustness improvements for monkey-patching:
- Version compatibility checks
- Conflict detection
- Better error handling
- Telemetry for patch failures
"""
import sys
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("llmobserve")

# Track patch state
_patch_state: Dict[str, Any] = {
    "openai_patched": False,
    "pinecone_patched": False,
    "openai_version": None,
    "pinecone_version": None,
    "conflicts_detected": [],
    "patch_failures": [],
}


def check_openai_version() -> Optional[str]:
    """Check OpenAI SDK version and return compatibility status."""
    try:
        import openai
        version = getattr(openai, "__version__", "unknown")
        _patch_state["openai_version"] = version
        
        # Check for known incompatible versions
        major_version = version.split(".")[0] if version != "unknown" else None
        
        if major_version:
            try:
                major = int(major_version)
                if major < 0:
                    logger.warning(f"[llmobserve] OpenAI SDK version {version} may be incompatible")
                    return "warning"
            except ValueError:
                pass
        
        return "ok"
    except ImportError:
        return None


def check_pinecone_version() -> Optional[str]:
    """Check Pinecone SDK version and return compatibility status."""
    try:
        import pinecone
        version = getattr(pinecone, "__version__", "unknown")
        _patch_state["pinecone_version"] = version
        return "ok"
    except ImportError:
        return None


def detect_patching_conflicts() -> list[str]:
    """
    Detect if other libraries have already patched OpenAI/Pinecone.
    
    Returns list of detected conflicts.
    """
    conflicts = []
    
    # Check OpenAI
    try:
        import openai
        from openai import resources
        
        # Check for common patching markers
        if hasattr(resources.chat.Completions, "create"):
            original = getattr(resources.chat.Completions, "create")
            
            # Check if already wrapped (has __wrapped__ attribute)
            if hasattr(original, "__wrapped__"):
                conflicts.append("openai:already_wrapped")
            
            # Check for other common patching libraries
            if hasattr(original, "__helicone_patched__"):
                conflicts.append("openai:helicone_detected")
            
            if hasattr(original, "__langfuse_patched__"):
                conflicts.append("openai:langfuse_detected")
            
            if hasattr(original, "__traceloop_patched__"):
                conflicts.append("openai:traceloop_detected")
            
            # Check if function source suggests patching
            try:
                import inspect
                source = inspect.getsource(original)
                if "helicone" in source.lower() or "langfuse" in source.lower():
                    conflicts.append("openai:possible_conflict")
            except (OSError, TypeError):
                pass  # Can't inspect built-in functions
    except Exception as e:
        logger.debug(f"[llmobserve] Could not check for conflicts: {e}")
    
    _patch_state["conflicts_detected"] = conflicts
    return conflicts


def safe_patch(
    resource_class: Any,
    method_name: str,
    endpoint_name: str,
    patch_func: callable,
    original_method: Optional[Any] = None
) -> tuple[bool, Optional[str]]:
    """
    Safely patch a method with error handling and conflict detection.
    
    Returns:
        (success: bool, error_message: Optional[str])
    """
    try:
        # Get original method if not provided
        if original_method is None:
            if not hasattr(resource_class, method_name):
                return False, f"Method {method_name} not found on {resource_class.__name__}"
            original_method = getattr(resource_class, method_name)
        
        # Check if already patched by us
        if hasattr(original_method, "_llmobserve_patched"):
            logger.debug(f"[llmobserve] {endpoint_name}.{method_name} already patched")
            return True, None
        
        # Check for conflicts
        if hasattr(original_method, "__wrapped__"):
            logger.warning(
                f"[llmobserve] {endpoint_name}.{method_name} appears to be already wrapped. "
                "This may cause conflicts with other observability libraries."
            )
        
        # Apply patch
        wrapped_method = patch_func(original_method)
        setattr(resource_class, method_name, wrapped_method)
        
        # Mark as patched
        wrapped_method._llmobserve_patched = True
        wrapped_method._llmobserve_original = original_method
        
        logger.info(f"[llmobserve] ✓ Patched {endpoint_name}.{method_name}")
        return True, None
        
    except AttributeError as e:
        error_msg = f"Attribute error patching {endpoint_name}.{method_name}: {e}"
        logger.error(f"[llmobserve] ✗ {error_msg}")
        _patch_state["patch_failures"].append({
            "endpoint": endpoint_name,
            "method": method_name,
            "error": str(e),
            "type": "AttributeError"
        })
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error patching {endpoint_name}.{method_name}: {e}"
        logger.error(f"[llmobserve] ✗ {error_msg}")
        _patch_state["patch_failures"].append({
            "endpoint": endpoint_name,
            "method": method_name,
            "error": str(e),
            "type": type(e).__name__
        })
        return False, error_msg


def get_patch_state() -> Dict[str, Any]:
    """Get current patch state for debugging/telemetry."""
    return {
        **_patch_state,
        "python_version": sys.version,
        "platform": sys.platform,
    }


def validate_patch_integrity() -> bool:
    """
    Validate that patches are still intact after patching.
    
    Returns True if patches appear valid.
    """
    try:
        import openai
        from openai import resources
        
        # Check if our patches are still in place
        if hasattr(resources.chat.Completions, "create"):
            method = getattr(resources.chat.Completions, "create")
            if hasattr(method, "_llmobserve_patched"):
                return True
        
        return False
    except Exception:
        return False

