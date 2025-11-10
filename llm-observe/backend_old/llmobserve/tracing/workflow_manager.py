"""Workflow manager for lazy workflow span creation and lifecycle management."""

import contextvars
import time
from typing import Optional

from opentelemetry import trace

from llmobserve.tracing.tracer import get_wrapped_tracer


# Context variables for workflow tracking
_current_workflow_span: contextvars.ContextVar[Optional[trace.Span]] = contextvars.ContextVar(
    "current_workflow_span", default=None
)
_workflow_function_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "workflow_function_name", default=None
)
_workflow_start_time: contextvars.ContextVar[Optional[float]] = contextvars.ContextVar(
    "workflow_start_time", default=None
)
_workflow_call_depth: contextvars.ContextVar[dict] = contextvars.ContextVar(
    "workflow_call_depth", default={}
)


class WorkflowState:
    """State tracking for active workflow spans."""
    
    def __init__(self):
        """Initialize workflow state."""
        self.active_span: Optional[trace.Span] = None
        self.function_name: Optional[str] = None
        self.module_name: Optional[str] = None
        self.function_file: Optional[str] = None
        self.start_time: Optional[float] = None
        self.call_depth: dict = {}  # Maps function_key -> depth
        self.function_metadata: dict = {}  # Maps function_key -> {name, module, file}
        self.workflow_stack: list = []  # Stack of workflow spans for nested functions
    
    def begin_function(self, function_key: str, function_name: Optional[str] = None, 
                      module_name: Optional[str] = None, function_file: Optional[str] = None) -> int:
        """
        Track function entry and return recursion depth.
        
        Args:
            function_key: Unique key for the function (e.g., "module.func_name")
            function_name: Optional function name
            module_name: Optional module name
            function_file: Optional function file path
        
        Returns:
            Current recursion depth (0 for outermost call)
        """
        depth = self.call_depth.get(function_key, 0)
        self.call_depth[function_key] = depth + 1
        
        # Store metadata for outermost call of this function
        # For nested functions, we need to preserve parent's metadata on stack
        if depth == 0:
            # Push current metadata onto stack if we have an active workflow span (nested call)
            if self.active_span is not None:
                self.workflow_stack.append({
                    "span": self.active_span,
                    "function_name": self.function_name,
                    "module_name": self.module_name,
                    "function_file": self.function_file,
                    "start_time": self.start_time,
                })
            
            # Store new function's metadata
            if function_name:
                self.function_name = function_name
            if module_name:
                self.module_name = module_name
            if function_file:
                self.function_file = function_file
            
            # Store function start time for accurate workflow span timing
            self.function_start_time = time.time()
            
            # Also store in metadata dict
            self.function_metadata[function_key] = {
                "name": function_name,
                "module": module_name,
                "file": function_file,
            }
        
        return depth
    
    def end_function(self, function_key: str) -> int:
        """
        Track function exit and return remaining depth.
        
        Args:
            function_key: Unique key for the function
        
        Returns:
            Remaining recursion depth (0 when outermost call exits)
        """
        depth = self.call_depth.get(function_key, 0)
        if depth > 0:
            self.call_depth[function_key] = depth - 1
        
        remaining_depth = self.call_depth.get(function_key, 0)
        
        # If this was the outermost call (remaining_depth == 0), restore parent workflow if nested
        if remaining_depth == 0 and self.workflow_stack:
            # Pop parent workflow from stack
            parent = self.workflow_stack.pop()
            self.active_span = parent["span"]
            self.function_name = parent["function_name"]
            self.module_name = parent["module_name"]
            self.function_file = parent["function_file"]
            self.start_time = parent["start_time"]
            # Update context vars
            _current_workflow_span.set(self.active_span)
            _workflow_function_name.set(self.function_name)
            _workflow_start_time.set(self.start_time)
        
        return remaining_depth
    
    def api_call_seen(self) -> bool:
        """
        Check if an API call has been seen (workflow span should exist).
        
        Returns:
            True if workflow span exists, False otherwise
        """
        return self.active_span is not None
    
    def ensure_parent_for_first_api_call(
        self,
        function_name: Optional[str] = None,
        module_name: Optional[str] = None,
        function_file: Optional[str] = None,
    ) -> Optional[trace.Span]:
        """
        Create workflow span lazily on first API call.
        
        Args:
            function_name: Optional name of the function (uses stored if not provided)
            module_name: Optional name of the module (uses stored if not provided)
            function_file: Optional file path (uses stored if not provided)
        
        Returns:
            Created workflow span or None if already exists
        """
        if self.active_span is not None:
            return self.active_span
        
        # Use stored metadata if not provided
        if not function_name:
            function_name = self.function_name
        if not module_name:
            module_name = self.module_name
        if not function_file:
            function_file = self.function_file
        
        if not function_name:
            # Can't create workflow span without function name
            return None
        
        # Create workflow span lazily
        from opentelemetry import trace as otel_trace
        
        tracer = get_wrapped_tracer(__name__)
        workflow_name = f"workflow.{function_name}"
        
        # Start span using OpenTelemetry tracer directly (wrapped tracer's start_span is a context manager)
        otel_tracer = tracer._tracer
        
        # Get function start time if available (for accurate duration tracking)
        function_start_time = getattr(self, 'function_start_time', None)
        api_call_time = time.time()
        
        # Create span (start_time will be when span is created, i.e., first API call)
        # If there's an active workflow span (nested function), it will automatically
        # become the parent due to OpenTelemetry context propagation
        workflow_span = otel_tracer.start_span(workflow_name)
        
        # Set workflow attributes
        workflow_span.set_attribute("function.name", function_name)
        workflow_span.set_attribute("function.module", module_name)
        workflow_span.set_attribute("workflow.type", "auto")
        
        # Store function start time as attribute for accurate duration calculation
        # Note: span.start_time reflects when first API call happened, but we track
        # function start time separately to calculate true function duration
        if function_start_time:
            workflow_span.set_attribute("function.start_time", function_start_time)
            # Calculate pre-API time
            pre_api_time_ms = (api_call_time - function_start_time) * 1000
            if pre_api_time_ms > 0:
                workflow_span.set_attribute("function.pre_api_time_ms", pre_api_time_ms)
        
        if function_file:
            workflow_span.set_attribute("function.file", function_file)
        
        # Set as current span using token
        token = otel_trace.set_span_in_context(workflow_span)
        
        # Store state
        self.active_span = workflow_span
        self.function_name = function_name
        self.start_time = function_start_time or api_call_time  # Use function start time if available
        self._span_token = token  # Store token for cleanup
        
        # Update context vars
        _current_workflow_span.set(workflow_span)
        _workflow_function_name.set(function_name)
        _workflow_start_time.set(self.start_time)
        
        return workflow_span
    
    def end_workflow_span(self, exception: Optional[Exception] = None) -> None:
        """
        End the workflow span.
        
        Args:
            exception: Optional exception that occurred
        """
        if self.active_span is None:
            return
        
        try:
            if exception:
                self.active_span.record_exception(exception)
                self.active_span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
            
            self.active_span.end()
        except Exception:
            # Best-effort: don't crash user app
            pass
        finally:
            # Reset span token if stored
            if hasattr(self, "_span_token"):
                try:
                    from opentelemetry import trace as otel_trace
                    otel_trace.detach(self._span_token)
                except Exception:
                    pass
            
            self.active_span = None
            self.function_name = None
            self.start_time = None
            
            # Clear context vars
            _current_workflow_span.set(None)
            _workflow_function_name.set(None)
            _workflow_start_time.set(None)


# Per-execution-context workflow state
_workflow_state: contextvars.ContextVar[WorkflowState] = contextvars.ContextVar(
    "workflow_state", default=WorkflowState()
)


def get_workflow_state() -> WorkflowState:
    """Get the current workflow state for this execution context."""
    try:
        return _workflow_state.get()
    except LookupError:
        state = WorkflowState()
        _workflow_state.set(state)
        return state


def begin_function(function_key: str, function_name: Optional[str] = None,
                  module_name: Optional[str] = None, function_file: Optional[str] = None) -> int:
    """
    Track function entry and return recursion depth.
    
    Args:
        function_key: Unique key for the function
        function_name: Optional function name
        module_name: Optional module name
        function_file: Optional function file path
    
    Returns:
        Current recursion depth (0 for outermost call)
    """
    state = get_workflow_state()
    return state.begin_function(function_key, function_name, module_name, function_file)


def end_function(function_key: str) -> int:
    """
    Track function exit and return remaining depth.
    
    Args:
        function_key: Unique key for the function
    
    Returns:
        Remaining recursion depth (0 when outermost call exits)
    """
    state = get_workflow_state()
    return state.end_function(function_key)


def api_call_seen() -> bool:
    """
    Check if an API call has been seen (workflow span should exist).
    
    Returns:
        True if workflow span exists, False otherwise
    """
    state = get_workflow_state()
    return state.api_call_seen()


def ensure_parent_for_first_api_call(
    function_name: Optional[str] = None,
    module_name: Optional[str] = None,
    function_file: Optional[str] = None,
) -> Optional[trace.Span]:
    """
    Create workflow span lazily on first API call.
    
    Args:
        function_name: Optional name of the function (uses stored if not provided)
        module_name: Optional name of the module (uses stored if not provided)
        function_file: Optional file path (uses stored if not provided)
    
    Returns:
        Created workflow span or None if already exists
    """
    state = get_workflow_state()
    return state.ensure_parent_for_first_api_call(function_name, module_name, function_file)


def get_current_workflow_span() -> Optional[trace.Span]:
    """
    Get the current workflow span from contextvars.
    
    Returns:
        Current workflow span or None
    """
    return _current_workflow_span.get()


def end_workflow_span(exception: Optional[Exception] = None) -> None:
    """
    End the workflow span.
    
    Args:
        exception: Optional exception that occurred
    """
    state = get_workflow_state()
    state.end_workflow_span(exception)

