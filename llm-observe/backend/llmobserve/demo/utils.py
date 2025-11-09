"""Utility functions for demo workflows."""

import datetime
import inspect
from typing import Optional


def infer_workflow_name() -> str:
    """
    Auto-infer workflow name from caller function name and timestamp.
    
    Returns:
        Workflow name in format: "{caller_function}_{timestamp}"
    """
    # Get the caller function name (2 levels up: caller -> infer_workflow_name -> this function)
    caller_frame = inspect.stack()[2]
    caller_function = caller_frame.function
    
    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    return f"{caller_function}_{timestamp}"

