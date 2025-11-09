"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchTrace, SpanSummary, Trace } from "@/lib/api";
import { format } from "date-fns";
import { use } from "react";

function buildSpanTree(spans: SpanSummary[]): Map<string, SpanSummary[]> {
  const tree = new Map<string, SpanSummary[]>();
  const rootSpans: SpanSummary[] = [];

  // Build parent-child mapping
  spans.forEach((span) => {
    if (!span.parent_span_id) {
      rootSpans.push(span);
    } else {
      if (!tree.has(span.parent_span_id)) {
        tree.set(span.parent_span_id, []);
      }
      tree.get(span.parent_span_id)!.push(span);
    }
  });

  // Sort children by start_time
  tree.forEach((children) => {
    children.sort((a, b) => a.start_time - b.start_time);
  });

  return tree;
}

function SpanNode({
  span,
  children,
  level,
  minTime,
  maxTime,
  tree,
}: {
  span: SpanSummary;
  children: SpanSummary[];
  level: number;
  minTime: number;
  maxTime: number;
  tree: Map<string, SpanSummary[]>;
}) {
  return (
    <div className="mb-2">
      <div
        className="flex items-center p-2 rounded border-l-2 border-blue-500 bg-gray-50 hover:bg-gray-100"
        style={{ marginLeft: `${level * 20}px` }}
      >
        <div className="flex-1">
          <div className="font-medium text-sm">{span.name}</div>
          <div className="text-xs text-gray-500 mt-1">
            {span.model && <span>Model: {span.model} • </span>}
            Tokens: {span.total_tokens} • Cost: ${span.cost_usd.toFixed(4)}
            {span.duration_ms && ` • Duration: ${span.duration_ms.toFixed(2)}ms`}
          </div>
        </div>
        <div className="text-xs text-gray-400">
          {format(new Date(span.start_time * 1000), "HH:mm:ss.SSS")}
        </div>
      </div>
      {children.map((child) => (
        <SpanNode
          key={child.span_id}
          span={child}
          children={tree.get(child.span_id) || []}
          level={level + 1}
          minTime={minTime}
          maxTime={maxTime}
          tree={tree}
        />
      ))}
    </div>
  );
}

function TimelineBar({ spans, minTime, maxTime }: { spans: SpanSummary[]; minTime: number; maxTime: number }) {
  return (
    <div className="relative h-32 bg-gray-100 rounded p-2">
      {spans.map((span) => {
        const startOffset = ((span.start_time - minTime) / (maxTime - minTime)) * 100;
        const width = Math.max(
          2,
          ((span.duration_ms || 100) / 1000 / (maxTime - minTime)) * 100
        );
        const hue = (span.span_id.charCodeAt(0) * 137.508) % 360;

        return (
          <div
            key={span.span_id}
            className="absolute h-6 rounded"
            style={{
              left: `${startOffset}%`,
              width: `${width}%`,
              backgroundColor: `hsl(${hue}, 70%, 50%)`,
              minWidth: "2px",
            }}
            title={`${span.name} (${span.duration_ms?.toFixed(2)}ms)`}
          />
        );
      })}
    </div>
  );
}

export default function TraceDetailPage({ params }: { params: Promise<{ traceId: string }> }) {
  const { traceId } = use(params);
  const { data, isLoading, error } = useQuery({
    queryKey: ["trace", traceId],
    queryFn: () => fetchTrace(traceId),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-gray-500">Loading trace...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-red-500">Error loading trace: {error instanceof Error ? error.message : "Unknown error"}</p>
        </div>
      </div>
    );
  }

  const { trace, spans } = data;
  const tree = buildSpanTree(spans);
  const rootSpans = spans.filter((s) => !s.parent_span_id);
  
  const minTime = Math.min(...spans.map((s) => s.start_time));
  const maxTime = Math.max(
    ...spans.map((s) => s.start_time + (s.duration_ms || 0) / 1000)
  );

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <a href="/" className="text-blue-600 hover:underline mb-4 inline-block">
            ← Back to Dashboard
          </a>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Trace Details</h1>
          <p className="text-gray-600 font-mono text-sm">{traceId}</p>
        </div>

        {/* Trace Summary */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Trace Summary</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-500">Root Span</div>
              <div className="font-medium">{trace.root_span_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Total Cost</div>
              <div className="font-medium">${trace.total_cost_usd.toFixed(4)}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Total Tokens</div>
              <div className="font-medium">{trace.total_tokens.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Span Count</div>
              <div className="font-medium">{trace.span_count}</div>
            </div>
            {trace.duration_ms && (
              <div>
                <div className="text-sm text-gray-500">Duration</div>
                <div className="font-medium">{trace.duration_ms.toFixed(2)}ms</div>
              </div>
            )}
            <div>
              <div className="text-sm text-gray-500">Start Time</div>
              <div className="font-medium text-sm">
                {format(new Date(trace.start_time * 1000), "MMM d, yyyy HH:mm:ss.SSS")}
              </div>
            </div>
          </div>
        </div>

        {/* Timeline Visualization */}
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">Timeline</h2>
          <TimelineBar spans={spans} minTime={minTime} maxTime={maxTime} />
        </div>

        {/* Span Tree */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Span Tree</h2>
          {rootSpans.length > 0 ? (
            rootSpans.map((rootSpan) => (
              <SpanNode
                key={rootSpan.span_id}
                span={rootSpan}
                children={tree.get(rootSpan.span_id) || []}
                level={0}
                minTime={minTime}
                maxTime={maxTime}
                tree={tree}
              />
            ))
          ) : (
            <p className="text-gray-500">No spans found</p>
          )}
        </div>
      </div>
    </div>
  );
}

