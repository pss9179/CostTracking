"""
Semantic mapper - Maps function calls to semantic labels from semantic_map.json
"""
import json
import inspect
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("llmobserve")

_semantic_map: Optional[Dict] = None
_semantic_map_path: Optional[Path] = None


def load_semantic_map(path: Optional[str] = None) -> Dict:
    """
    Load semantic map from .llmobserve/semantic_map.json
    
    Returns empty dict if not found.
    """
    global _semantic_map, _semantic_map_path
    
    # Use cached if already loaded
    if _semantic_map is not None:
        return _semantic_map
    
    # Determine path
    if path:
        map_path = Path(path) / ".llmobserve" / "semantic_map.json"
    else:
        # Try current directory and parent directories
        current = Path.cwd()
        for parent in [current] + list(current.parents)[:5]:  # Check up to 5 levels up
            map_path = parent / ".llmobserve" / "semantic_map.json"
            if map_path.exists():
                break
        else:
            # Not found, return empty
            _semantic_map = {}
            return _semantic_map
    
    _semantic_map_path = map_path
    
    # Load map
    try:
        if map_path.exists():
            with open(map_path, 'r') as f:
                _semantic_map = json.load(f)
                logger.debug(f"[llmobserve] Loaded semantic map from {map_path}")
                return _semantic_map
    except Exception as e:
        logger.warning(f"[llmobserve] Failed to load semantic map: {e}")
    
    _semantic_map = {}
    return _semantic_map


def get_semantic_label_for_function(func_name: str, file_path: Optional[str] = None) -> Optional[str]:
    """
    Get semantic label for a function.
    
    Args:
        func_name: Function name
        file_path: File path (optional, will try to infer from call stack)
    
    Returns:
        Semantic label or None if not found
    """
    semantic_map = load_semantic_map()
    
    if not semantic_map:
        return None
    
    # If file_path provided, use it
    if file_path:
        if file_path in semantic_map:
            # Check for function-specific mapping
            if func_name in semantic_map[file_path]:
                return semantic_map[file_path][func_name]
            # Check for wildcard mapping
            if "*" in semantic_map[file_path]:
                return semantic_map[file_path]["*"]
    
    # Try to infer file_path from call stack
    try:
        frame = inspect.currentframe()
        if frame:
            # Go up call stack to find the calling function
            caller_frame = frame.f_back
            if caller_frame:
                filename = caller_frame.f_code.co_filename
                # Normalize path
                try:
                    file_path = str(Path(filename).resolve())
                except:
                    file_path = filename
                
                if file_path in semantic_map:
                    if func_name in semantic_map[file_path]:
                        return semantic_map[file_path][func_name]
                    if "*" in semantic_map[file_path]:
                        return semantic_map[file_path]["*"]
    except Exception:
        pass
    
    return None


def get_semantic_label_from_call_stack() -> Optional[str]:
    """
    Get semantic label from current call stack.
    
    Tries to find the calling function and map it to a semantic label.
    """
    try:
        frame = inspect.currentframe()
        if not frame:
            return None
        
        # Go up call stack
        caller_frame = frame.f_back
        if not caller_frame:
            return None
        
        func_name = caller_frame.f_code.co_name
        filename = caller_frame.f_code.co_filename
        
        # Normalize path
        try:
            file_path = str(Path(filename).resolve())
        except:
            file_path = filename
        
        return get_semantic_label_for_function(func_name, file_path)
    except Exception:
        return None


def add_semantic_label_to_event(event: Dict) -> Dict:
    """
    Add semantic_label field to event if semantic map exists.
    
    Args:
        event: Event dictionary
    
    Returns:
        Event with semantic_label added (if found)
    """
    semantic_label = get_semantic_label_from_call_stack()
    
    if semantic_label:
        event["semantic_label"] = semantic_label
    
    return event

