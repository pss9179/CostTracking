"""Async exporter for cost events to SQLite database."""

import logging
import time
from datetime import datetime
from queue import Queue
from threading import Thread
from typing import Optional, Dict, Any

from llmobserve.models import CostEvent
from llmobserve.db import get_session

# Wrapper function that can be patched in tests
def _get_session():
    """Get database session - can be patched in tests."""
    return get_session()

logger = logging.getLogger(__name__)


class CostEventExporter:
    """Async exporter that batches cost events and writes to SQLite."""

    def __init__(self, batch_size: int = 10, flush_interval: float = 1.0):
        """
        Initialize exporter.

        Args:
            batch_size: Number of events to batch before writing
            flush_interval: Seconds between batch writes
        """
        self._queue: Queue = Queue()
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._running = False
        self._worker_thread: Optional[Thread] = None

    def start(self) -> None:
        """Start background worker thread."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("CostEventExporter started")

    def stop(self) -> None:
        """Stop background worker and flush remaining events."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        self._flush_queue()
        logger.info("CostEventExporter stopped")

    def record_cost(
        self,
        tenant_id: str,
        provider: str,
        cost_usd: float,
        duration_ms: float,
        workflow_id: Optional[str] = None,
        model: Optional[str] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        operation: Optional[str] = None,
    ) -> None:
        """
        Enqueue a cost event for async writing.

        Args:
            tenant_id: Tenant identifier
            provider: Provider name (e.g., "openai", "pinecone")
            cost_usd: Cost in USD
            duration_ms: Duration in milliseconds
            workflow_id: Optional workflow identifier
            model: Optional model name
            trace_id: Optional trace ID for linking
            span_id: Optional span ID
            prompt_tokens: Optional prompt token count
            completion_tokens: Optional completion token count
            total_tokens: Optional total token count
            operation: Optional operation type (e.g., "query", "chat")
        """
        event = {
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "provider": provider,
            "model": model,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow(),
            "trace_id": trace_id,
            "span_id": span_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "operation": operation,
        }
        self._queue.put(event)

    def _worker_loop(self) -> None:
        """Background worker loop that batches and writes events."""
        import time
        batch = []
        last_flush = time.time()

        while self._running:
            try:
                # Try to get event with timeout
                try:
                    event = self._queue.get(timeout=self._flush_interval)
                    batch.append(event)
                except:
                    pass  # Timeout, will flush if batch is ready

                # Flush if batch is full or interval elapsed
                current_time = time.time()
                should_flush = (
                    len(batch) >= self._batch_size or
                    (batch and current_time - last_flush >= self._flush_interval)
                )

                if should_flush and batch:
                    self._write_batch(batch)
                    batch = []
                    last_flush = current_time

            except Exception as e:
                logger.error(f"Error in exporter worker loop: {e}", exc_info=True)

        # Flush remaining events
        if batch:
            self._write_batch(batch)

    def _write_batch(self, batch: list) -> None:
        """Write a batch of events to database."""
        if not batch:
            return

        try:
            session = _get_session()
            try:
                for event_data in batch:
                    event = CostEvent(**event_data)
                    session.add(event)
                session.commit()
            finally:
                session.close()
            logger.debug(f"Wrote {len(batch)} cost events to database")
        except Exception as e:
            logger.error(f"Failed to write cost events batch: {e}", exc_info=True)

    def _flush_queue(self) -> None:
        """Flush all remaining events from queue."""
        batch = []
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                batch.append(event)
            except:
                break

        if batch:
            self._write_batch(batch)


# Global exporter instance
_exporter: Optional[CostEventExporter] = None


def get_exporter() -> CostEventExporter:
    """Get or create global exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = CostEventExporter()
        _exporter.start()
    return _exporter

