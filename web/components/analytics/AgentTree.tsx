"use client";

import { useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import {
  ChevronRight,
  ChevronDown,
  Layers,
  Cpu,
  Wrench,
  GitBranch,
  Clock,
  DollarSign,
  MoreHorizontal,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/progress";

// ============================================================================
// TYPES
// ============================================================================

export interface AgentNode {
  id: string;
  name: string;
  type: "agent" | "step" | "tool" | "feature";
  section: string;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
  p95_latency_ms?: number;
  parent_id?: string | null;
  children?: AgentNode[];
  depth?: number;
}

interface AgentTreeProps {
  nodes: AgentNode[];
  totalCost: number;
  onNodeClick?: (node: AgentNode) => void;
  className?: string;
}

interface TreeNodeProps {
  node: AgentNode;
  totalCost: number;
  depth: number;
  expanded: boolean;
  onToggle: () => void;
  onNodeClick?: (node: AgentNode) => void;
}

// ============================================================================
// NODE TYPE CONFIG
// ============================================================================

const NODE_TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  agent: { 
    icon: <Cpu className="w-4 h-4" />, 
    color: "text-purple-600", 
    bg: "bg-purple-100" 
  },
  step: { 
    icon: <GitBranch className="w-4 h-4" />, 
    color: "text-blue-600", 
    bg: "bg-blue-100" 
  },
  tool: { 
    icon: <Wrench className="w-4 h-4" />, 
    color: "text-orange-600", 
    bg: "bg-orange-100" 
  },
  feature: { 
    icon: <Layers className="w-4 h-4" />, 
    color: "text-emerald-600", 
    bg: "bg-emerald-100" 
  },
};

// ============================================================================
// TREE NODE COMPONENT
// ============================================================================

function TreeNode({ node, totalCost, depth, expanded, onToggle, onNodeClick }: TreeNodeProps) {
  const config = NODE_TYPE_CONFIG[node.type] || NODE_TYPE_CONFIG.feature;
  const hasChildren = node.children && node.children.length > 0;
  const percentOfTotal = totalCost > 0 ? (node.total_cost / totalCost) * 100 : 0;
  const costPerCall = node.call_count > 0 ? node.total_cost / node.call_count : 0;

  return (
    <div
      className={cn(
        "group flex items-center gap-2 py-2.5 px-3 rounded-lg transition-all duration-150",
        "hover:bg-gray-50 cursor-pointer",
        depth > 0 && "ml-6 border-l-2 border-gray-100 pl-4"
      )}
      style={{ marginLeft: depth > 0 ? `${depth * 24}px` : 0 }}
      onClick={() => onNodeClick?.(node)}
    >
      {/* Expand/Collapse */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        className={cn(
          "p-0.5 rounded transition-colors",
          hasChildren ? "hover:bg-gray-200" : "invisible"
        )}
      >
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {/* Type Icon */}
      <span className={cn("p-1.5 rounded-md", config.bg, config.color)}>
        {config.icon}
      </span>

      {/* Name & Type */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900 truncate">
            {node.name}
          </span>
          <span className="text-xs text-gray-400 capitalize">
            {node.type}
          </span>
        </div>
        {hasChildren && (
          <span className="text-xs text-gray-400">
            {node.children?.length} sub-item{node.children?.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Metrics */}
      <div className="flex items-center gap-6 text-sm">
        {/* Calls */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="text-gray-500 tabular-nums min-w-[60px] text-right">
                {formatCompactNumber(node.call_count)} calls
              </span>
            </TooltipTrigger>
            <TooltipContent>
              {node.call_count.toLocaleString()} total invocations
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Latency */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="text-gray-500 tabular-nums min-w-[60px] text-right flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {node.avg_latency_ms.toFixed(0)}ms
              </span>
            </TooltipTrigger>
            <TooltipContent>
              Avg latency: {node.avg_latency_ms.toFixed(1)}ms
              {node.p95_latency_ms && (
                <> • p95: {node.p95_latency_ms.toFixed(1)}ms</>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {/* Cost % of parent */}
        <div className="min-w-[100px]">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">{percentOfTotal.toFixed(1)}%</span>
          </div>
          <Progress value={percentOfTotal} className="h-1.5" />
        </div>

        {/* Total Cost */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger>
              <span className="font-semibold text-gray-900 tabular-nums min-w-[80px] text-right">
                {formatSmartCost(node.total_cost)}
              </span>
            </TooltipTrigger>
            <TooltipContent>
              Total: {formatSmartCost(node.total_cost)}
              <br />
              Per call: {formatSmartCost(costPerCall)}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
}

// ============================================================================
// RECURSIVE TREE RENDERER
// ============================================================================

interface TreeRendererProps {
  nodes: AgentNode[];
  totalCost: number;
  expandedIds: Set<string>;
  onToggle: (id: string) => void;
  onNodeClick?: (node: AgentNode) => void;
  depth?: number;
}

function TreeRenderer({ 
  nodes, 
  totalCost, 
  expandedIds, 
  onToggle, 
  onNodeClick,
  depth = 0 
}: TreeRendererProps) {
  return (
    <>
      {nodes.map((node) => {
        const isExpanded = expandedIds.has(node.id);
        const hasChildren = node.children && node.children.length > 0;

        return (
          <div key={node.id}>
            <TreeNode
              node={node}
              totalCost={totalCost}
              depth={depth}
              expanded={isExpanded}
              onToggle={() => onToggle(node.id)}
              onNodeClick={onNodeClick}
            />
            {isExpanded && hasChildren && (
              <TreeRenderer
                nodes={node.children!}
                totalCost={totalCost}
                expandedIds={expandedIds}
                onToggle={onToggle}
                onNodeClick={onNodeClick}
                depth={depth + 1}
              />
            )}
          </div>
        );
      })}
    </>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function AgentTree({ nodes, totalCost, onNodeClick, className }: AgentTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");

  // Build hierarchical tree from flat nodes
  const treeData = useMemo(() => {
    // If already hierarchical, return as-is
    if (nodes.some(n => n.children && n.children.length > 0)) {
      return nodes;
    }

    // Build from flat list using parent_id
    const nodeMap = new Map<string, AgentNode>();
    const roots: AgentNode[] = [];

    // First pass: create map
    nodes.forEach(node => {
      nodeMap.set(node.id, { ...node, children: [] });
    });

    // Second pass: build tree
    nodes.forEach(node => {
      const treeNode = nodeMap.get(node.id)!;
      if (node.parent_id && nodeMap.has(node.parent_id)) {
        const parent = nodeMap.get(node.parent_id)!;
        parent.children = parent.children || [];
        parent.children.push(treeNode);
      } else {
        roots.push(treeNode);
      }
    });

    // Sort by cost descending at each level
    const sortNodes = (nodeList: AgentNode[]) => {
      nodeList.sort((a, b) => b.total_cost - a.total_cost);
      nodeList.forEach(n => {
        if (n.children && n.children.length > 0) {
          sortNodes(n.children);
        }
      });
    };
    sortNodes(roots);

    return roots;
  }, [nodes]);

  // Filter nodes by search
  const filteredNodes = useMemo(() => {
    if (!searchQuery.trim()) return treeData;
    
    const query = searchQuery.toLowerCase();
    const filterTree = (nodeList: AgentNode[]): AgentNode[] => {
      return nodeList
        .map(node => {
          const matchesSelf = node.name.toLowerCase().includes(query) || 
                             node.section.toLowerCase().includes(query);
          const filteredChildren = node.children ? filterTree(node.children) : [];
          
          if (matchesSelf || filteredChildren.length > 0) {
            return { ...node, children: filteredChildren };
          }
          return null;
        })
        .filter(Boolean) as AgentNode[];
    };
    
    return filterTree(treeData);
  }, [treeData, searchQuery]);

  const handleToggle = useCallback((id: string) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleExpandAll = useCallback(() => {
    const getAllIds = (nodeList: AgentNode[]): string[] => {
      return nodeList.flatMap(n => [n.id, ...(n.children ? getAllIds(n.children) : [])]);
    };
    setExpandedIds(new Set(getAllIds(treeData)));
  }, [treeData]);

  const handleCollapseAll = useCallback(() => {
    setExpandedIds(new Set());
  }, []);

  if (nodes.length === 0) {
    return (
      <div className={cn("text-center py-12 border border-dashed border-gray-200 rounded-xl", className)}>
        <Layers className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No agent data</h3>
        <p className="text-sm text-gray-500">
          Use <code className="bg-gray-100 px-1 rounded">section("agent:name")</code> to track agents.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <input
            type="text"
            placeholder="Search agents, steps, tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-64"
          />
        </div>
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={handleExpandAll}
            className="text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
          >
            Expand all
          </button>
          <button
            onClick={handleCollapseAll}
            className="text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
          >
            Collapse all
          </button>
        </div>
      </div>

      {/* Column Headers */}
      <div className="flex items-center gap-2 py-2 px-3 text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
        <div className="flex-1 ml-12">Name</div>
        <div className="min-w-[60px] text-right">Calls</div>
        <div className="min-w-[60px] text-right">Latency</div>
        <div className="min-w-[100px] text-center">% of Total</div>
        <div className="min-w-[80px] text-right">Cost</div>
      </div>

      {/* Tree */}
      <div className="space-y-1">
        <TreeRenderer
          nodes={filteredNodes}
          totalCost={totalCost}
          expandedIds={expandedIds}
          onToggle={handleToggle}
          onNodeClick={onNodeClick}
        />
      </div>

      {/* Summary */}
      <div className="flex items-center justify-between pt-4 border-t text-sm text-gray-500">
        <span>{nodes.length} total items</span>
        <span>Total cost: {formatSmartCost(totalCost)}</span>
      </div>
    </div>
  );
}

// ============================================================================
// HELPER: Parse section stats into agent nodes
// ============================================================================

export function parseAgentNodes(
  sectionStats: Array<{
    section: string;
    section_path?: string | null;
    total_cost: number;
    call_count: number;
    avg_latency_ms: number;
  }>
): AgentNode[] {
  return sectionStats
    .filter(s => s.section && s.section !== "main" && s.section !== "default")
    .map((stat, index) => {
      // Parse section type from name (agent:name, step:name, tool:name, feature:name)
      const [typePrefix, ...nameParts] = stat.section.split(":");
      const name = nameParts.join(":") || stat.section;
      const type = ["agent", "step", "tool", "feature"].includes(typePrefix) 
        ? typePrefix as AgentNode["type"]
        : "feature";

      // Parse parent from section_path if available
      // e.g., "agent:researcher > step:analyze" -> parent is "agent:researcher"
      let parent_id: string | null = null;
      if (stat.section_path && stat.section_path.includes(" > ")) {
        const parts = stat.section_path.split(" > ");
        if (parts.length > 1) {
          parent_id = parts[parts.length - 2]; // Get second to last part
        }
      }

      return {
        id: stat.section,
        name,
        type,
        section: stat.section,
        total_cost: stat.total_cost,
        call_count: stat.call_count,
        avg_latency_ms: stat.avg_latency_ms,
        parent_id,
      };
    });
}

export default AgentTree;



