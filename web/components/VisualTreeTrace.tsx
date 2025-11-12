"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ChevronRight, ChevronDown, Clock, DollarSign, Zap } from "lucide-react";

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

interface VisualTreeTraceProps {
  events: TraceEvent[];
}

function buildTree(events: TraceEvent[]): TreeNode[] {
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

  // Second pass: build tree structure
  events.forEach((event) => {
    const node = nodeMap.get(event.span_id);
    if (!node) return;

    if (event.parent_span_id && nodeMap.has(event.parent_span_id)) {
      const parent = nodeMap.get(event.parent_span_id);
      if (parent) {
        parent.children.push(node);
      }
    } else {
      rootNodes.push(node);
    }
  });

  // Sort children by cost (descending)
  const sortChildren = (node: TreeNode) => {
    node.children.sort((a, b) => b.totalCost - a.totalCost);
    node.children.forEach(sortChildren);
  };
  rootNodes.forEach(sortChildren);

  return rootNodes;
}

function VisualTreeNode({
  node,
  depth = 0,
  isLast = false,
}: {
  node: TreeNode;
  depth?: number;
  isLast?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(true);
  const hasChildren = node.children.length > 0;
  const { event } = node;

  // Determine node type styling
  const isAgent = event.section.startsWith("agent:");
  const isTool = event.section.startsWith("tool:");
  const isStep = event.section.startsWith("step:");
  const isSpan = event.provider === "internal";

  const getNodeColor = () => {
    if (isAgent) return "border-l-blue-500 bg-blue-50";
    if (isTool) return "border-l-green-500 bg-green-50";
    if (isStep) return "border-l-purple-500 bg-purple-50";
    if (isSpan) return "border-l-gray-400 bg-gray-50";
    return "border-l-orange-500 bg-orange-50";
  };

  const getIconBadgeColor = () => {
    if (isAgent) return "bg-blue-500";
    if (isTool) return "bg-green-500";
    if (isStep) return "bg-purple-500";
    return "bg-gray-500";
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return "$0.00";
    if (cost < 0.000001) return `$${(cost * 1000000).toFixed(2)}µ`;
    if (cost < 0.001) return `$${(cost * 1000).toFixed(2)}m`;
    return `$${cost.toFixed(6)}`;
  };

  const formatLatency = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="relative">
      {/* Connecting Line from Parent */}
      {depth > 0 && (
        <div
          className="absolute left-6 top-0 w-px h-6 bg-gray-300"
          style={{ marginLeft: `${(depth - 1) * 32}px` }}
        />
      )}

      {/* Horizontal Line to Node */}
      {depth > 0 && (
        <div
          className="absolute top-6 left-6 h-px w-6 bg-gray-300"
          style={{ marginLeft: `${(depth - 1) * 32}px` }}
        />
      )}

      {/* Node Card */}
      <div
        className="relative"
        style={{ marginLeft: `${depth * 32}px`, marginBottom: "12px" }}
      >
        <Card
          className={`border-l-4 ${getNodeColor()} transition-all hover:shadow-md cursor-pointer`}
          onClick={() => hasChildren && setIsExpanded(!isExpanded)}
        >
          <div className="p-3">
            <div className="flex items-start gap-3">
              {/* Expand/Collapse Icon */}
              <div className="flex-shrink-0 mt-1">
                {hasChildren ? (
                  isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-gray-600" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-600" />
                  )
                ) : (
                  <div className="w-4 h-4" /> /* Spacer */
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                {/* Header Row */}
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${getIconBadgeColor()}`} />
                  <Badge variant="secondary" className="font-mono text-xs">
                    {event.section_path || event.section}
                  </Badge>
                  {hasChildren && (
                    <Badge variant="outline" className="text-xs">
                      {node.children.length} {node.children.length === 1 ? "child" : "children"}
                    </Badge>
                  )}
                </div>

                {/* API Call Details (skip for internal spans) */}
                {!isSpan && (
                  <div className="flex items-center gap-4 text-xs text-gray-600 mb-2">
                    <div className="flex items-center gap-1">
                      <Badge variant="outline" className="text-xs">
                        {event.provider}
                      </Badge>
                      <span>{event.endpoint}</span>
                    </div>
                    {event.model && (
                      <span className="text-gray-500 font-mono">{event.model}</span>
                    )}
                  </div>
                )}

                {/* Metrics Row */}
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1 text-green-700 font-semibold">
                    <DollarSign className="w-3 h-3" />
                    {formatCost(event.cost_usd)}
                  </div>
                  <div className="flex items-center gap-1 text-gray-600">
                    <Clock className="w-3 h-3" />
                    {formatLatency(event.latency_ms)}
                  </div>
                  {(event.input_tokens > 0 || event.output_tokens > 0) && (
                    <div className="flex items-center gap-1 text-blue-600">
                      <Zap className="w-3 h-3" />
                      {event.input_tokens + event.output_tokens} tok
                      {event.input_tokens > 0 && event.output_tokens > 0 && (
                        <span className="text-gray-500">
                          ({event.input_tokens}↓{event.output_tokens}↑)
                        </span>
                      )}
                    </div>
                  )}
                  <div className={`text-xs ${event.status === "ok" ? "text-green-600" : "text-red-600"}`}>
                    {event.status === "ok" ? "✓" : "✗"} {event.status}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Vertical Line to Children */}
        {hasChildren && isExpanded && node.children.length > 0 && (
          <div
            className="absolute left-6 top-full w-px bg-gray-300"
            style={{
              height: "12px",
              marginLeft: "32px",
            }}
          />
        )}
      </div>

      {/* Children */}
      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child, index) => (
            <VisualTreeNode
              key={child.event.span_id}
              node={child}
              depth={depth + 1}
              isLast={index === node.children.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function VisualTreeTrace({ events }: VisualTreeTraceProps) {
  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No trace events available
      </div>
    );
  }

  const tree = buildTree(events);

  if (tree.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Unable to build trace tree. Check event structure.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-600 pb-4 border-b">
        <span className="font-semibold">Legend:</span>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-blue-500" />
          <span>Agent</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span>Tool</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-purple-500" />
          <span>Step</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-gray-500" />
          <span>Span</span>
        </div>
      </div>

      {/* Tree */}
      <div className="pl-2">
        {tree.map((node) => (
          <VisualTreeNode key={node.event.span_id} node={node} depth={0} />
        ))}
      </div>
    </div>
  );
}

