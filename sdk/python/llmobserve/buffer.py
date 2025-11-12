"""
In-memory event buffer with auto-flush and bounded queue.

Uses a bounded queue (maxsize=10000) with drop-oldest policy when full.
"""
import atexit
import threading
import queue
import logging
from typing import List, Optional
from llmobserve.types import TraceEvent
from llmobserve import config

logger = logging.getLogger("llmobserve")

# Bounded queue for events (maxsize=10000, drop oldest when full)
_event_queue: queue.Queue = queue.Queue(maxsize=10000)
_dropped_count = 0
_dropped_lock = threading.Lock()
_flush_timer: Optional[threading.Timer] = None


def add_event(event: TraceEvent) -> None:
    """
    Add an event to the buffer.
    
    Uses bounded queue with drop-oldest policy when full.
    Logs warning when events are dropped.
    
    Args:
        event: Trace event to buffer
    """
    if not config.is_enabled():
        return
    
    try:
        # Try to add to queue (non-blocking)
        _event_queue.put_nowait(event)
    except queue.Full:
        # Queue is full - drop oldest event
        try:
            _event_queue.get_nowait()  # Remove oldest
            _event_queue.put_nowait(event)  # Add new one
            
            # Track dropped count
            global _dropped_count
            with _dropped_lock:
                _dropped_count += 1
                if _dropped_count % 100 == 0:  # Log every 100 drops
                    logger.warning(
                        f"[llmobserve] Event buffer full - dropped {_dropped_count} events. "
                        "Consider increasing flush frequency or buffer size."
                    )
        except queue.Full:
            # Still full after removing one - log error
            logger.error("[llmobserve] Event buffer full - failed to add event")


def get_and_clear_buffer() -> List[TraceEvent]:
    """
    Get all buffered events and clear the buffer.
    
    Returns:
        List of buffered events
    """
    events = []
    
    # Drain queue (non-blocking)
    while True:
        try:
            event = _event_queue.get_nowait()
            events.append(event)
        except queue.Empty:
            break
    
    # Log dropped count if any
    global _dropped_count
    with _dropped_lock:
        if _dropped_count > 0:
            logger.warning(f"[llmobserve] Dropped {_dropped_count} events due to buffer overflow")
            _dropped_count = 0
    
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

