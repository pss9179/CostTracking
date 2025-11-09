"""Sampling strategies for OpenTelemetry."""

from typing import Optional

from opentelemetry.sdk.trace.sampling import Decision, Sampler, SamplingResult, SpanKind, Context as TraceContext


class ParentBasedSampler(Sampler):
    """
    Parent-based sampler that respects parent sampling decisions.

    If parent is sampled, sample child. If parent is not sampled, don't sample child.
    If no parent, use root sampler (always sample for demo).
    """

    def __init__(self, root_sampler: Optional[Sampler] = None):
        """Initialize with optional root sampler."""
        self._root_sampler = root_sampler or AlwaysOnSampler()

    def get_description(self) -> str:
        """Return description of the sampler."""
        return "ParentBasedSampler"

    def should_sample(
        self,
        parent_context: Optional[TraceContext],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Optional[dict] = None,
        links: Optional[list] = None,
    ) -> SamplingResult:
        """Determine if span should be sampled."""
        # If parent exists and is sampled, sample child
        if parent_context and parent_context.trace_flags & 0x01:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)

        # If parent exists and is not sampled, don't sample child
        if parent_context:
            return SamplingResult(Decision.DROP)

        # No parent - use root sampler
        return self._root_sampler.should_sample(
            parent_context, trace_id, name, kind, attributes, links
        )


class AlwaysOnSampler(Sampler):
    """Always sample spans."""

    def get_description(self) -> str:
        """Return description of the sampler."""
        return "AlwaysOnSampler"

    def should_sample(
        self,
        parent_context: Optional[TraceContext],
        trace_id: int,
        name: str,
        kind: Optional[SpanKind] = None,
        attributes: Optional[dict] = None,
        links: Optional[list] = None,
    ) -> SamplingResult:
        """Always return RECORD_AND_SAMPLE."""
        return SamplingResult(Decision.RECORD_AND_SAMPLE)

