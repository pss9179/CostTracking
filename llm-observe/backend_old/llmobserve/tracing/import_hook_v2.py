"""Import hook v2 for automatic function wrapping at import-time."""

import functools
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from llmobserve.tracing.function_tracer import should_wrap_function, wrap_function


class MetaPathFinder:
    """Meta path finder for import-time function wrapping."""
    
    def __init__(self):
        """Initialize the meta path finder."""
        self._wrapped_modules: set = set()
        self._exclude_patterns: list = []
        self._include_patterns: list = []
        self._enabled = True
        
        # Load exclude patterns from env
        exclude_str = os.getenv("LLMOBSERVE_EXCLUDE_MODULES", "test,__pycache__")
        self._exclude_patterns = [p.strip() for p in exclude_str.split(",") if p.strip()]
        
        # Load include patterns from env (optional)
        include_str = os.getenv("LLMOBSERVE_INCLUDE_MODULES", "")
        self._include_patterns = [p.strip() for p in include_str.split(",") if p.strip() if p.strip()]
        
        # Get PROJECT_ROOT from env
        self._project_root = os.getenv("PROJECT_ROOT")
        if self._project_root:
            self._project_root = Path(self._project_root).resolve()
    
    def should_wrap_module(self, module_name: str) -> bool:
        """
        Determine if a module should be wrapped.
        
        Args:
            module_name: Name of the module
        
        Returns:
            True if module should be wrapped, False otherwise
        """
        # Skip if already wrapped
        if module_name in self._wrapped_modules:
            return False
        
        # Skip stdlib modules
        if module_name.startswith(("_", "sys", "os", "json", "builtins", "typing", "collections")):
            return False
        
        # Skip excluded patterns
        for pattern in self._exclude_patterns:
            if pattern in module_name:
                return False
        
        # Check if module is in site-packages (third-party)
        if module_name in sys.modules:
            mod = sys.modules[module_name]
            if hasattr(mod, "__file__") and mod.__file__:
                file_path = Path(mod.__file__)
                # Check if it's in site-packages
                if "site-packages" in str(file_path):
                    return False
                
                # If PROJECT_ROOT is set, only wrap modules within it
                if self._project_root:
                    try:
                        mod_path = file_path.resolve()
                        if not str(mod_path).startswith(str(self._project_root)):
                            return False
                    except Exception:
                        pass
        
        # Check include patterns if specified
        if self._include_patterns:
            matches_include = False
            for pattern in self._include_patterns:
                if pattern in module_name or module_name.startswith(pattern):
                    matches_include = True
                    break
            if not matches_include:
                return False
        
        return True
    
    def wrap_module_functions(self, module: Any) -> None:
        """
        Wrap all functions in a module.
        
        Args:
            module: Module object to wrap
        """
        module_name = getattr(module, "__name__", "unknown")
        
        if not self.should_wrap_module(module_name):
            return
        
        # Mark as wrapped
        self._wrapped_modules.add(module_name)
        
        # Wrap all functions in the module
        for name, obj in inspect.getmembers(module):
            # Skip private attributes
            if name.startswith("_"):
                continue
            
            # Wrap functions
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                if should_wrap_function(obj, module_name):
                    try:
                        wrapped = wrap_function(obj, module_name)
                        setattr(module, name, wrapped)
                    except Exception:
                        # Skip if wrapping fails (e.g., built-in functions)
                        pass
            
            # Wrap class methods
            elif inspect.isclass(obj):
                self._wrap_class_methods(obj, module_name)
    
    def _wrap_class_methods(self, cls: type, module_name: str) -> None:
        """
        Wrap methods in a class.
        
        Args:
            cls: Class to wrap
            module_name: Name of the module containing the class
        """
        for name, method in inspect.getmembers(cls):
            # Skip private methods (except __call__ and __init__)
            if name.startswith("_") and name not in ("__call__", "__init__"):
                continue
            
            # Wrap methods
            if inspect.isfunction(method) or inspect.ismethod(method):
                if should_wrap_function(method, module_name):
                    try:
                        wrapped = wrap_function(method, module_name)
                        setattr(cls, name, wrapped)
                    except Exception:
                        pass
    
    def find_spec(self, name, path, target=None):
        """Find module spec (let default importers handle it)."""
        return None
    
    def exec_module(self, module):
        """Execute module and wrap functions."""
        # Module is already executed by the time we get here
        # We need to wrap functions after module execution
        if self._enabled:
            try:
                self.wrap_module_functions(module)
            except Exception:
                pass  # Best-effort: don't crash user app


# Global finder instance
_finder: Optional[MetaPathFinder] = None


def enable_import_hook_v2() -> None:
    """Enable the import hook v2 system."""
    global _finder
    
    if _finder is None:
        _finder = MetaPathFinder()
    
    # Add to meta_path if not already there
    if _finder not in sys.meta_path:
        sys.meta_path.insert(0, _finder)
    
    # Also patch importlib's exec_module to wrap functions
    _patch_importlib_exec_module()


_original_exec_module = None


def _patched_exec_module(loader_self, module):
    """Patched exec_module that wraps functions after module execution."""
    # Call original exec_module
    if _original_exec_module:
        result = _original_exec_module(loader_self, module)
    else:
        # Fallback: use default behavior
        import importlib.util
        if hasattr(importlib.util, "exec_module"):
            importlib.util.exec_module(module)
        result = None
    
    # Wrap functions in the module
    if _finder and _finder._enabled:
        try:
            _finder.wrap_module_functions(module)
        except Exception:
            pass  # Best-effort: don't crash user app
    
    return result


def _patch_importlib_exec_module() -> None:
    """Patch importlib's exec_module to wrap functions."""
    global _original_exec_module
    
    if _original_exec_module is None:
        import importlib.abc
        
        if hasattr(importlib.abc, "Loader"):
            _original_exec_module = importlib.abc.Loader.exec_module
            importlib.abc.Loader.exec_module = _patched_exec_module


def disable_import_hook_v2() -> None:
    """Disable the import hook v2 system."""
    global _finder
    
    if _finder:
        _finder._enabled = False
        if _finder in sys.meta_path:
            sys.meta_path.remove(_finder)
    
    # Restore original exec_module
    global _original_exec_module
    if _original_exec_module:
        import importlib.abc
        if hasattr(importlib.abc, "Loader"):
            importlib.abc.Loader.exec_module = _original_exec_module
        _original_exec_module = None


def wrap_module(module_name: str) -> None:
    """
    Manually wrap functions in a specific module.
    
    Args:
        module_name: Name of the module to wrap
    """
    if module_name in sys.modules:
        module = sys.modules[module_name]
        if _finder:
            _finder.wrap_module_functions(module)

