"""Base instrumentor interface and registry."""

from abc import ABC, abstractmethod
from typing import List


class Instrumentor(ABC):
    """Base class for auto-instrumentation."""

    @abstractmethod
    def instrument(self) -> None:
        """Apply instrumentation to target library."""
        pass

    @abstractmethod
    def uninstrument(self) -> None:
        """Remove instrumentation from target library."""
        pass


class InstrumentorRegistry:
    """Registry for managing instrumentors."""

    def __init__(self):
        """Initialize empty registry."""
        self._instrumentors: List[Instrumentor] = []

    def register(self, instrumentor: Instrumentor) -> None:
        """Register an instrumentor."""
        self._instrumentors.append(instrumentor)

    def instrument_all(self) -> None:
        """Apply all registered instrumentors."""
        for instr in self._instrumentors:
            try:
                instr.instrument()
            except Exception as e:
                import structlog
                logger = structlog.get_logger()
                logger.error("Failed to apply instrumentor", instrumentor=type(instr).__name__, error=str(e))

    def uninstrument_all(self) -> None:
        """Remove all instrumentations."""
        for instr in self._instrumentors:
            try:
                instr.uninstrument()
            except Exception as e:
                import structlog
                logger = structlog.get_logger()
                logger.error("Failed to remove instrumentor", instrumentor=type(instr).__name__, error=str(e))


# Global registry
instrumentor_registry = InstrumentorRegistry()

