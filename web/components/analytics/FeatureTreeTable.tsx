"use client";

import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { ChevronRight, ChevronDown, Search, X, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatCompactNumber,
  formatDuration,
  formatPercentage,
  parseFeatureSection,
  getFeatureTypeColor,
  getStableColor,
} from "@/lib/format";

// ============================================================================
// TYPES
// ============================================================================

export interface FeatureNode {
  // Core data
  id: string;
  section: string;
  section_path: string | null;
  
  // Metrics
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
  percentage: number;
  
  // Hierarchy
  parent_id?: string | null;
  children?: FeatureNode[];
  depth?: number;
  
  // State
  isExpanded?: boolean;
}

interface FeatureTreeTableProps {
  data: FeatureNode[];
  totalCost: number;
  onRowClick?: (node: FeatureNode) => void;
  onDrillDown?: (node: FeatureNode) => void;
  className?: string;
  maxHeight?: number | string;
  virtualizeThreshold?: number;
}

type SortField = 'name' | 'cost' | 'calls' | 'latency' | 'percentage';
type SortDirection = 'asc' | 'desc';

// ============================================================================
// ROW COMPONENT
// ============================================================================

interface FeatureRowProps {
  node: FeatureNode;
  depth: number;
  isExpanded: boolean;
  hasChildren: boolean;
  totalCost: number;
  onToggle: () => void;
  onClick: () => void;
  style?: React.CSSProperties;
}

function FeatureRow({
  node,
  depth,
  isExpanded,
  hasChildren,
  totalCost,
  onToggle,
  onClick,
  style,
}: FeatureRowProps) {
  const parsed = parseFeatureSection(node.section);
  const costPerCall = node.call_count > 0 ? node.total_cost / node.call_count : 0;
  const percentage = totalCost > 0 ? (node.total_cost / totalCost) * 100 : 0;
  const color = getStableColor(node.section);
  
  // Root/uncategorized handling
  const isRoot = node.section === 'main' || node.section === 'default' || node.section === 'Root';
  const displayName = isRoot ? 'Uncategorized' : parsed.displayName;
  
  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors group",
        depth === 0 && "bg-white",
        depth > 0 && "bg-slate-50/50"
      )}
      style={style}
      onClick={onClick}
    >
      {/* Indent + expand/collapse */}
      <div 
        className="flex items-center flex-shrink-0"
        style={{ paddingLeft: depth * 16 }}
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
          className={cn(
            "w-5 h-5 flex items-center justify-center rounded hover:bg-slate-200/60 transition-colors",
            !hasChildren && "invisible"
          )}
        >
          {hasChildren && (
            isExpanded 
              ? <ChevronDown className="w-4 h-4 text-slate-400" />
              : <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </button>
      </div>
      
      {/* Color indicator */}
      <div 
        className="w-1.5 h-6 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      
      {/* Name + type */}
      <div className="flex-1 min-w-0 flex items-center gap-2">
        {!isRoot && (
          <Badge 
            variant="secondary" 
            className={cn("text-[10px] font-medium flex-shrink-0", getFeatureTypeColor(parsed.type))}
          >
            {parsed.type}
          </Badge>
        )}
        <span className={cn(
          "truncate text-sm",
          isRoot ? "text-slate-400 italic" : "text-slate-800 font-medium"
        )}>
          {displayName}
        </span>
        {hasChildren && (
          <span className="text-xs text-slate-400 flex-shrink-0">
            ({node.children?.length || 0})
          </span>
        )}
      </div>
      
      {/* Metrics */}
      <div className="flex items-center gap-4 flex-shrink-0 text-right">
        {/* Calls */}
        <div className="w-16">
          <span className="text-xs text-slate-500 tabular-nums">
            {formatCompactNumber(node.call_count)}
          </span>
        </div>
        
        {/* Latency */}
        <div className="w-16 hidden sm:block">
          <span className="text-xs text-slate-500 tabular-nums">
            {formatDuration(node.avg_latency_ms)}
          </span>
        </div>
        
        {/* Cost per call */}
        <div className="w-20 hidden md:block">
          <span className="text-xs text-slate-500 tabular-nums">
            {formatSmartCost(costPerCall)}/call
          </span>
        </div>
        
        {/* Cost */}
        <div className="w-20">
          <span className="text-sm font-semibold text-slate-900 tabular-nums">
            {formatSmartCost(node.total_cost)}
          </span>
        </div>
        
        {/* Percentage bar */}
        <div className="w-24 hidden lg:flex items-center gap-2">
          <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all"
              style={{ 
                width: `${Math.max(percentage, 1)}%`,
                backgroundColor: color,
              }}
            />
          </div>
          <span className="text-xs text-slate-400 tabular-nums w-10 text-right">
            {formatPercentage(percentage)}
          </span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// HEADER
// ============================================================================

interface HeaderProps {
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

function SortIcon({ field, currentField, direction }: { field: SortField; currentField: SortField; direction: SortDirection }) {
  if (field !== currentField) {
    return <ArrowUpDown className="w-3.5 h-3.5 text-slate-300" />;
  }
  return direction === 'asc' 
    ? <ArrowUp className="w-3.5 h-3.5 text-emerald-500" />
    : <ArrowDown className="w-3.5 h-3.5 text-emerald-500" />;
}

function TableHeader({ sortField, sortDirection, onSort }: HeaderProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-slate-50 border-b border-slate-200 text-xs font-medium text-slate-500 uppercase tracking-wide sticky top-0 z-10">
      {/* Indent placeholder + color */}
      <div className="w-5 flex-shrink-0" />
      <div className="w-1.5 flex-shrink-0" />
      
      {/* Name */}
      <button 
        className="flex-1 min-w-0 flex items-center gap-1 hover:text-slate-700 transition-colors text-left"
        onClick={() => onSort('name')}
      >
        Feature
        <SortIcon field="name" currentField={sortField} direction={sortDirection} />
      </button>
      
      {/* Metrics */}
      <div className="flex items-center gap-4 flex-shrink-0">
        <button 
          className="w-16 flex items-center gap-1 justify-end hover:text-slate-700 transition-colors"
          onClick={() => onSort('calls')}
        >
          Calls
          <SortIcon field="calls" currentField={sortField} direction={sortDirection} />
        </button>
        
        <button 
          className="w-16 hidden sm:flex items-center gap-1 justify-end hover:text-slate-700 transition-colors"
          onClick={() => onSort('latency')}
        >
          Latency
          <SortIcon field="latency" currentField={sortField} direction={sortDirection} />
        </button>
        
        <div className="w-20 hidden md:block text-right">$/Call</div>
        
        <button 
          className="w-20 flex items-center gap-1 justify-end hover:text-slate-700 transition-colors"
          onClick={() => onSort('cost')}
        >
          Cost
          <SortIcon field="cost" currentField={sortField} direction={sortDirection} />
        </button>
        
        <div className="w-24 hidden lg:block text-right">Share</div>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function FeatureTreeTable({
  data,
  totalCost,
  onRowClick,
  onDrillDown,
  className,
  maxHeight = 600,
  virtualizeThreshold = 50,
}: FeatureTreeTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('cost');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Build tree structure from flat data
  const tree = useMemo(() => {
    // For now, treat as flat list (hierarchy comes from section_path parsing)
    return data.map(node => ({
      ...node,
      id: node.section,
      depth: 0,
      children: [],
    }));
  }, [data]);
  
  // Filter by search
  const filteredTree = useMemo(() => {
    if (!searchQuery) return tree;
    
    const lower = searchQuery.toLowerCase();
    return tree.filter(node => {
      const parsed = parseFeatureSection(node.section);
      return (
        node.section.toLowerCase().includes(lower) ||
        parsed.displayName.toLowerCase().includes(lower) ||
        parsed.type.toLowerCase().includes(lower)
      );
    });
  }, [tree, searchQuery]);
  
  // Sort
  const sortedTree = useMemo(() => {
    const sorted = [...filteredTree];
    
    sorted.sort((a, b) => {
      let cmp = 0;
      
      switch (sortField) {
        case 'name':
          cmp = a.section.localeCompare(b.section);
          break;
        case 'cost':
          cmp = a.total_cost - b.total_cost;
          break;
        case 'calls':
          cmp = a.call_count - b.call_count;
          break;
        case 'latency':
          cmp = a.avg_latency_ms - b.avg_latency_ms;
          break;
        case 'percentage':
          cmp = a.percentage - b.percentage;
          break;
      }
      
      return sortDirection === 'asc' ? cmp : -cmp;
    });
    
    // Always put "Root"/"main"/"default" at top
    const rootIndex = sorted.findIndex(n => 
      n.section === 'main' || n.section === 'default' || n.section === 'Root'
    );
    if (rootIndex > 0) {
      const [root] = sorted.splice(rootIndex, 1);
      sorted.unshift(root);
    }
    
    return sorted;
  }, [filteredTree, sortField, sortDirection]);
  
  // Flatten tree for rendering (respecting expanded state)
  const flatList = useMemo(() => {
    const result: (FeatureNode & { depth: number; hasChildren: boolean })[] = [];
    
    function flatten(nodes: FeatureNode[], depth: number) {
      nodes.forEach(node => {
        const hasChildren = (node.children?.length || 0) > 0;
        result.push({ ...node, depth, hasChildren });
        
        if (hasChildren && expandedIds.has(node.id)) {
          flatten(node.children!, depth + 1);
        }
      });
    }
    
    flatten(sortedTree, 0);
    return result;
  }, [sortedTree, expandedIds]);
  
  // Toggle expanded
  const toggleExpanded = useCallback((id: string) => {
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
  
  // Handle sort
  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  }, [sortField]);
  
  // Determine if we should virtualize
  const shouldVirtualize = flatList.length > virtualizeThreshold;
  
  return (
    <div className={cn("bg-white rounded-xl border border-slate-200/60 overflow-hidden", className)}>
      {/* Search bar */}
      <div className="p-3 border-b border-slate-100">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search features, agents, tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 h-9 text-sm border-slate-200"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        {/* Quick stats */}
        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
          <span>{flatList.length} items</span>
          {searchQuery && (
            <span className="text-emerald-600">
              Filtered from {data.length}
            </span>
          )}
        </div>
      </div>
      
      {/* Header */}
      <TableHeader
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
      />
      
      {/* Rows */}
      <div 
        ref={containerRef}
        className="overflow-y-auto"
        style={{ maxHeight }}
      >
        {flatList.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            {searchQuery ? (
              <>
                <p className="text-sm">No features match "{searchQuery}"</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSearchQuery("")}
                  className="mt-2"
                >
                  Clear search
                </Button>
              </>
            ) : (
              <p className="text-sm">No feature data available</p>
            )}
          </div>
        ) : (
          flatList.map((node) => (
            <FeatureRow
              key={node.id}
              node={node}
              depth={node.depth}
              isExpanded={expandedIds.has(node.id)}
              hasChildren={node.hasChildren}
              totalCost={totalCost}
              onToggle={() => toggleExpanded(node.id)}
              onClick={() => {
                onRowClick?.(node);
                if (onDrillDown) {
                  onDrillDown(node);
                }
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}

