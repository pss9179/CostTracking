"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ChevronRight, ChevronDown } from "lucide-react";

interface TraceEvent {
  id: string;
  span_id: string;
  parent_span_id: string | null;
  section: string;
  section_path: string | null;
  provider: string;
  endpoint: string;
  model: string | null;
  cost_usd: number;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  status: string;
  created_at: string;
}

interface TreeNode {
  event: TraceEvent;
  children: TreeNode[];
  totalCost: number;
  callCount: number;
}

interface HierarchicalTraceProps {
  events: TraceEvent[];
}

function buildTree(events: TraceEvent[]): TreeNode[] {
  // Create a map of span_id to node
  const nodeMap = new Map<string, TreeNode>();
  const rootNodes: TreeNode[] = [];

  // First pass: create all nodes
  events.forEach((event) => {
    nodeMap.set(event.span_id, {
      event,
      children: [],
      totalCost: event.cost_usd,
      callCount: 1,
    });
  });

  // Second pass: build tree structure and calculate costs
  events.forEach((event) => {
    const node = nodeMap.get(event.span_id);
    if (!node) return;

    if (event.parent_span_id && nodeMap.has(event.parent_span_id)) {
      // Add to parent's children
      const parent = nodeMap.get(event.parent_span_id);
      if (parent) {
        parent.children.push(node);
        // Bubble up cost to parent
        let current = parent;
        while (current) {
          current.totalCost += event.cost_usd;
          current.callCount += 1;
          // Find parent of current
          const parentSpanId = current.event.parent_span_id;
          if (!parentSpanId) break;
          current = nodeMap.get(parentSpanId) || null;
        }
      }
    } else {
      // Root node (no parent or parent not found)
      rootNodes.push(node);
    }
  });

  return rootNodes;
}

function TreeNodeComponent({
  node,
  depth = 0,
}: {
  node: TreeNode;
  depth?: number;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = node.children.length > 0;

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString();
  };

  return (
    <div className="border-l-2 border-gray-200 pl-4 py-2">
      <div
        className="flex items-center gap-3 hover:bg-gray-50 p-2 rounded cursor-pointer"
        onClick={() => hasChildren && setIsExpanded(!isExpanded)}
      >
        {/* Expand/Collapse Icon */}
        <div className="w-5 h-5 flex-shrink-0">
          {hasChildren && (
            isExpanded ? (
              <ChevronDown className="w-5 h-5 text-gray-600" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-600" />
            )
          )}
        </div>

        {/* Section Path Badge */}
        <div className="flex-shrink-0">
          <Badge variant="secondary" className="text-xs font-mono">
            {node.event.section_path || node.event.section}
          </Badge>
        </div>

        {/* Provider & Endpoint */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <Badge variant="outline" className="text-xs">
            {node.event.provider}
          </Badge>
          <span className="text-xs text-gray-600">{node.event.endpoint}</span>
        </div>

        {/* Model */}
        {node.event.model && (
          <span className="text-xs text-gray-500 flex-shrink-0">
            {node.event.model}
          </span>
        )}

        {/* Metrics */}
        <div className="ml-auto flex items-center gap-4 text-xs">
          {/* Time */}
          <span className="text-gray-500">{formatDate(node.event.created_at)}</span>

          {/* Latency */}
          <span className="text-gray-600">
            {node.event.latency_ms.toFixed(0)}ms
          </span>

          {/* Tokens */}
          {(node.event.input_tokens > 0 || node.event.output_tokens > 0) && (
            <span className="text-gray-600">
              {node.event.input_tokens} / {node.event.output_tokens} tok
            </span>
          )}

          {/* Cost */}
          <span className="font-semibold text-gray-900 min-w-[80px] text-right">
            ${node.event.cost_usd.toFixed(6)}
          </span>

          {/* Status */}
          <Badge
            variant={node.event.status === "ok" ? "default" : "destructive"}
            className="text-xs"
          >
            {node.event.status}
          </Badge>
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div className="mt-1">
          {node.children.map((child, idx) => (
            <TreeNodeComponent
              key={`${child.event.span_id}-${depth}-${idx}`}
              node={child}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function HierarchicalTrace({ events }: HierarchicalTraceProps) {
  // Check if events have hierarchy (at least one has parent_span_id)
  const hasHierarchy = events.some((e) => e.parent_span_id !== null);

  if (!hasHierarchy) {
    // Fallback to flat list if no hierarchy
    return (
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground mb-4">
          No hierarchical structure detected. Displaying flat event list.
        </p>
        {events.map((event, idx) => (
          <div
            key={`${event.span_id}-${idx}`}
            className="flex items-center gap-3 p-3 border rounded hover:bg-gray-50"
          >
            <Badge variant="secondary" className="text-xs">
              {event.section}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {event.provider}
            </Badge>
            <span className="text-xs text-gray-600">{event.endpoint}</span>
            {event.model && (
              <span className="text-xs text-gray-500">{event.model}</span>
            )}
            <div className="ml-auto flex items-center gap-4 text-xs">
              <span className="text-gray-600">
                {event.latency_ms.toFixed(0)}ms
              </span>
              <span className="font-semibold">${event.cost_usd.toFixed(6)}</span>
              <Badge
                variant={event.status === "ok" ? "default" : "destructive"}
                className="text-xs"
              >
                {event.status}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Build tree from events
  const tree = buildTree(events);

  return (
    <div className="space-y-1">
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
        <p className="text-sm text-blue-900">
          <strong>Hierarchical Trace View:</strong> Expand/collapse sections to
          explore nested agent, tool, and step calls.
        </p>
      </div>
      {tree.map((node, idx) => (
        <TreeNodeComponent key={`${node.event.span_id}-${idx}`} node={node} />
      ))}
    </div>
  );
}

