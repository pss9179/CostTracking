"use client";

import { useState, useEffect, useRef } from "react";
import { Badge } from "@/components/ui/badge";

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
  x: number;
  y: number;
  id: string;
}

interface GraphTreeVisualizationProps {
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
      x: 0,
      y: 0,
      id: event.span_id,
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

  return rootNodes;
}

// Calculate tree layout positions
function calculateLayout(nodes: TreeNode[], startX: number = 400, startY: number = 60, levelHeight: number = 150) {
  const calculateSubtreeWidth = (node: TreeNode): number => {
    if (node.children.length === 0) return 180;
    const childrenWidth = node.children.reduce((sum, child) => sum + calculateSubtreeWidth(child), 0);
    return Math.max(180, childrenWidth);
  };

  const positionNode = (node: TreeNode, x: number, y: number, width: number) => {
    node.x = x + width / 2;
    node.y = y;

    if (node.children.length > 0) {
      let currentX = x;
      node.children.forEach((child) => {
        const childWidth = calculateSubtreeWidth(child);
        positionNode(child, currentX, y + levelHeight, childWidth);
        currentX += childWidth;
      });
    }
  };

  let currentX = 0;
  nodes.forEach((node) => {
    const nodeWidth = calculateSubtreeWidth(node);
    positionNode(node, currentX, startY, nodeWidth);
    currentX += nodeWidth + 100;
  });

  return nodes;
}

function getNodeColor(event: TraceEvent) {
  if (event.section.startsWith("agent:")) return { bg: "#3b82f6", border: "#1d4ed8", text: "#fff", shadow: "#93c5fd" }; // blue
  if (event.section.startsWith("tool:")) return { bg: "#10b981", border: "#047857", text: "#fff", shadow: "#6ee7b7" }; // green
  if (event.section.startsWith("step:")) return { bg: "#8b5cf6", border: "#6d28d9", text: "#fff", shadow: "#c4b5fd" }; // purple
  if (event.provider === "internal") return { bg: "#64748b", border: "#475569", text: "#fff", shadow: "#cbd5e1" }; // gray
  return { bg: "#f59e0b", border: "#b45309", text: "#fff", shadow: "#fcd34d" }; // orange
}

function GraphNode({ node, onClick }: { node: TreeNode; onClick: () => void }) {
  const colors = getNodeColor(node.event);
  const isSpan = node.event.provider === "internal";
  
  const label = node.event.section.split(":")[1] || node.event.section;
  const cost = node.event.cost_usd;
  const costDisplay = cost === 0 ? "$0" : cost < 0.000001 ? `$${(cost * 1000000).toFixed(1)}µ` : `$${cost.toFixed(6)}`;

  return (
    <g
      transform={`translate(${node.x}, ${node.y})`}
      onClick={onClick}
      style={{ cursor: "pointer" }}
      className="node-hover"
    >
      {/* Outer glow on hover */}
      <circle
        r={isSpan ? 40 : 52}
        fill={colors.shadow}
        opacity="0"
        className="node-glow"
      />
      
      {/* Node Circle with better shadow */}
      <circle
        r={isSpan ? 35 : 48}
        fill={colors.bg}
        stroke={colors.border}
        strokeWidth={4}
        filter="url(#shadow)"
      />
      
      {/* Label with better readability */}
      <text
        y={isSpan ? 0 : -5}
        textAnchor="middle"
        fill={colors.text}
        fontSize="14"
        fontWeight="700"
        fontFamily="system-ui, -apple-system, sans-serif"
        style={{ pointerEvents: "none" }}
      >
        {label.length > 10 ? label.substring(0, 9) + "..." : label}
      </text>
      
      {/* Cost with better styling */}
      {!isSpan && (
        <text
          y={15}
          textAnchor="middle"
          fill={colors.text}
          fontSize="12"
          fontWeight="600"
          fontFamily="ui-monospace, monospace"
          style={{ pointerEvents: "none" }}
        >
          {costDisplay}
        </text>
      )}
      
      {/* Provider badge for non-spans */}
      {!isSpan && node.event.provider && (
        <text
          y={30}
          textAnchor="middle"
          fill={colors.text}
          fontSize="9"
          fontWeight="500"
          opacity="0.9"
          fontFamily="system-ui, -apple-system, sans-serif"
          style={{ pointerEvents: "none" }}
        >
          {node.event.provider}
        </text>
      )}
    </g>
  );
}

function GraphEdge({ from, to, label }: { from: TreeNode; to: TreeNode; label?: string }) {
  const midX = (from.x + to.x) / 2;
  const midY = (from.y + to.y) / 2;

  return (
    <g>
      {/* Edge line with gradient */}
      <line
        x1={from.x}
        y1={from.y + 48}
        x2={to.x}
        y2={to.y - 48}
        stroke="#64748b"
        strokeWidth={3}
        strokeOpacity="0.6"
        markerEnd="url(#arrowhead)"
      />
      
      {/* Edge label */}
      {label && (
        <text
          x={midX}
          y={midY}
          textAnchor="middle"
          fill="#475569"
          fontSize="11"
          fontWeight="500"
          fontFamily="system-ui, -apple-system, sans-serif"
          style={{ pointerEvents: "none" }}
        >
          {label}
        </text>
      )}
    </g>
  );
}

export function GraphTreeVisualization({ events }: GraphTreeVisualizationProps) {
  const [selectedNode, setSelectedNode] = useState<TreeNode | null>(null);
  const [tree, setTree] = useState<TreeNode[]>([]);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (events.length > 0) {
      const builtTree = buildTree(events);
      const layoutTree = calculateLayout(builtTree);
      setTree(layoutTree);
    }
  }, [events]);

  if (events.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No trace events available
      </div>
    );
  }

  // Calculate SVG dimensions
  const allNodes: TreeNode[] = [];
  const collectNodes = (nodes: TreeNode[]) => {
    nodes.forEach((node) => {
      allNodes.push(node);
      collectNodes(node.children);
    });
  };
  collectNodes(tree);

  const minX = Math.min(...allNodes.map((n) => n.x)) - 100;
  const maxX = Math.max(...allNodes.map((n) => n.x)) + 100;
  const minY = Math.min(...allNodes.map((n) => n.y)) - 80;
  const maxY = Math.max(...allNodes.map((n) => n.y)) + 80;
  const width = maxX - minX;
  const height = maxY - minY;

  const renderEdges = (nodes: TreeNode[]) => {
    const edges: JSX.Element[] = [];
    nodes.forEach((node) => {
      node.children.forEach((child) => {
        edges.push(
          <GraphEdge
            key={`edge-${node.id}-${child.id}`}
            from={node}
            to={child}
          />
        );
      });
      edges.push(...renderEdges(node.children));
    });
    return edges;
  };

  const renderNodes = (nodes: TreeNode[]) => {
    const nodeElements: JSX.Element[] = [];
    nodes.forEach((node) => {
      nodeElements.push(
        <GraphNode
          key={node.id}
          node={node}
          onClick={() => setSelectedNode(node)}
        />
      );
      nodeElements.push(...renderNodes(node.children));
    });
    return nodeElements;
  };

  return (
    <div className="space-y-4">
      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-600 pb-4 border-b flex-wrap">
        <span className="font-semibold">Legend:</span>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span>Agent</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>Tool</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-purple-500" />
          <span>Step</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-gray-400" />
          <span>Span</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-orange-500" />
          <span>API Call</span>
        </div>
      </div>

      {/* Graph Visualization */}
      <div className="border rounded-lg bg-gradient-to-br from-gray-50 to-white overflow-auto" style={{ maxHeight: "700px" }}>
        <style>{`
          .node-hover:hover .node-glow {
            opacity: 0.3;
            transition: opacity 0.2s ease;
          }
          .node-hover {
            transition: transform 0.2s ease;
          }
          .node-hover:hover {
            transform: scale(1.05);
          }
        `}</style>
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`${minX} ${minY} ${width} ${height}`}
          style={{ minWidth: "100%", minHeight: "500px" }}
        >
          {/* Definitions */}
          <defs>
            {/* Shadow filter */}
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
              <feOffset dx="2" dy="2" result="offsetblur" />
              <feComponentTransfer>
                <feFuncA type="linear" slope="0.3" />
              </feComponentTransfer>
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            
            {/* Arrowhead marker */}
            <marker
              id="arrowhead"
              markerWidth="12"
              markerHeight="12"
              refX="11"
              refY="6"
              orient="auto"
              markerUnits="strokeWidth"
            >
              <path d="M0,0 L0,12 L12,6 z" fill="#64748b" opacity="0.6" />
            </marker>
          </defs>

          {/* Render edges first (behind nodes) */}
          {renderEdges(tree)}

          {/* Render nodes */}
          {renderNodes(tree)}
        </svg>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div className="border rounded-lg p-4 bg-blue-50">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-lg">Node Details</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-600">Section:</span>
              <div className="font-mono font-semibold">{selectedNode.event.section_path || selectedNode.event.section}</div>
            </div>
            
            {selectedNode.event.provider !== "internal" && (
              <>
                <div>
                  <span className="text-gray-600">Provider:</span>
                  <div><Badge variant="outline">{selectedNode.event.provider}</Badge></div>
                </div>
                
                <div>
                  <span className="text-gray-600">Endpoint:</span>
                  <div className="font-mono text-xs">{selectedNode.event.endpoint}</div>
                </div>
                
                {selectedNode.event.model && (
                  <div>
                    <span className="text-gray-600">Model:</span>
                    <div className="font-mono text-xs">{selectedNode.event.model}</div>
                  </div>
                )}
                
                <div>
                  <span className="text-gray-600">Cost:</span>
                  <div className="font-semibold text-green-700">${selectedNode.event.cost_usd.toFixed(6)}</div>
                </div>
                
                <div>
                  <span className="text-gray-600">Latency:</span>
                  <div className="font-semibold">{selectedNode.event.latency_ms.toFixed(0)}ms</div>
                </div>
                
                {(selectedNode.event.input_tokens > 0 || selectedNode.event.output_tokens > 0) && (
                  <div>
                    <span className="text-gray-600">Tokens:</span>
                    <div className="font-mono text-xs">
                      {selectedNode.event.input_tokens}↓ {selectedNode.event.output_tokens}↑ 
                      ({selectedNode.event.input_tokens + selectedNode.event.output_tokens} total)
                    </div>
                  </div>
                )}
              </>
            )}
            
            <div>
              <span className="text-gray-600">Children:</span>
              <div className="font-semibold">{selectedNode.children.length}</div>
            </div>
            
            <div>
              <span className="text-gray-600">Status:</span>
              <div>
                <Badge variant={selectedNode.event.status === "ok" ? "default" : "destructive"}>
                  {selectedNode.event.status}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

