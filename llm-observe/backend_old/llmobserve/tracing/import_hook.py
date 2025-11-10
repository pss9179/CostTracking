"""Import hook system for automatic function wrapping."""

import functools
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Callable, Optional

from llmobserve.tracing.function_tracer import should_wrap_function, wrap_function


class FunctionWrapper:
    """Wrapper for intercepting module imports and wrapping functions."""
    
    def __init__(self):
        """Initialize the function wrapper."""
        self._wrapped_modules: set = set()
        self._exclude_patterns: list = []
        self._include_patterns: list = []
        self._enabled = True
        
        # Load exclude patterns from env
        import os
        exclude_str = os.getenv("LLMOBSERVE_EXCLUDE_MODULES", "test,__pycache__")
        self._exclude_patterns = [p.strip() for p in exclude_str.split(",") if p.strip()]
    
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
                
                # Check if it's in the user's project directory
                # This is a heuristic - we assume user code is not in site-packages
                # and is in the current working directory or a subdirectory
                try:
                    cwd = Path.cwd()
                    if not str(file_path).startswith(str(cwd)):
                        # Not in current directory - might be third-party
                        return False
                except Exception:
                    pass
        
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
    
    def install_hook(self) -> None:
        """Install the import hook using sys.meta_path."""
        if not self._enabled:
            return
        
        # Create a custom meta path finder
        class FunctionTracingFinder:
            def __init__(self, wrapper):
                self.wrapper = wrapper
            
            def find_spec(self, name, path, target=None):
                # Let default importers handle the import
                return None
            
            def find_module(self, name, path=None):
                # This is for Python < 3.4 compatibility
                return None
        
        # Add finder to meta path
        finder = FunctionTracingFinder(self)
        if finder not in sys.meta_path:
            sys.meta_path.insert(0, finder)
        
        # Also hook into module loading via importlib
        original_exec_module = importlib.abc.Loader.exec_module
        wrapper_instance = self
        
        def patched_exec_module(loader_self, module):
            # Call original exec_module
            result = original_exec_module(loader_self, module)
            
            # Wrap functions in the module
            if wrapper_instance._enabled:
                try:
                    wrapper_instance.wrap_module_functions(module)
                except Exception:
                    pass
            
            return result
        
        # Patch exec_module (this is a simplified approach)
        # Note: This might not work for all importers, but covers most cases
        importlib.abc.Loader.exec_module = patched_exec_module
    
    def uninstall_hook(self) -> None:
        """Uninstall the import hook."""
        # Disable wrapping
        self._enabled = False


# Global wrapper instance
_function_wrapper = FunctionWrapper()


def enable_function_wrapping():
    """Enable automatic function wrapping via import hook."""
    _function_wrapper.install_hook()


def disable_function_wrapping():
    """Disable automatic function wrapping."""
    _function_wrapper.uninstall_hook()


def wrap_module(module_name: str) -> None:
    """
    Manually wrap functions in a specific module.
    
    Args:
        module_name: Name of the module to wrap
    """
    if module_name in sys.modules:
        module = sys.modules[module_name]
        _function_wrapper.wrap_module_functions(module)

