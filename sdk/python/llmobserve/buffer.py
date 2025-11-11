"""
In-memory event buffer with auto-flush.
"""
import atexit
import threading
from typing import List, Optional
from llmobserve.types import TraceEvent
from llmobserve import config

# Global event buffer
_buffer: List[TraceEvent] = []
_buffer_lock = threading.Lock()
_flush_timer: Optional[threading.Timer] = None


def add_event(event: TraceEvent) -> None:
    """
    Add an event to the buffer.
    
    Args:
        event: Trace event to buffer
    """
    if not config.is_enabled():
        return
    
    with _buffer_lock:
        _buffer.append(event)


def get_and_clear_buffer() -> List[TraceEvent]:
    """
    Get all buffered events and clear the buffer.
    
    Returns:
        List of buffered events
    """
    with _buffer_lock:
        events = _buffer.copy()
        _buffer.clear()
        return events


def start_flush_timer() -> None:
    """Start periodic flush timer."""
    global _flush_timer
    
    if not config.is_enabled():
        return
    
    # Import here to avoid circular dependency
    from llmobserve.transport import flush_events
    
    def _flush_and_reschedule():
        """Flush events and reschedule the timer."""
        global _flush_timer
        
        flush_events()
        
        # Reschedule
        interval_sec = config.get_flush_interval_ms() / 1000.0
        _flush_timer = threading.Timer(interval_sec, _flush_and_reschedule)
        _flush_timer.daemon = True
        _flush_timer.start()
    
    # Initial schedule
    interval_sec = config.get_flush_interval_ms() / 1000.0
    _flush_timer = threading.Timer(interval_sec, _flush_and_reschedule)
    _flush_timer.daemon = True
    _flush_timer.start()


def stop_flush_timer() -> None:
    """Stop the flush timer."""
    global _flush_timer
    if _flush_timer:
        _flush_timer.cancel()
        _flush_timer = None


# Register cleanup on exit
def _cleanup():
    """Flush remaining events on exit."""
    from llmobserve.transport import flush_events
    stop_flush_timer()
    flush_events()


atexit.register(_cleanup)

