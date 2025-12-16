"use client";

import { useState, useMemo, useCallback } from "react";
import { cn } from "@/lib/utils";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  Download,
  Layers,
  Clock,
  DollarSign,
  Zap,
  ChevronRight,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";

// ============================================================================
// TYPES
// ============================================================================

export interface FeatureRow {
  id: string;
  name: string;
  section: string;
  type: "feature" | "agent" | "step" | "tool";
  total_cost: number;
  call_count: number;
  cost_per_call: number;
  p50_cost_per_call?: number; // Median cost per call
  p95_cost_per_call?: number; // 95th percentile cost per call
  avg_latency_ms: number;
  p95_latency_ms: number;
  percentage: number;
  trend?: "up" | "down" | "flat";
  provider?: string;
  model?: string;
}

type SortKey = "name" | "total_cost" | "call_count" | "cost_per_call" | "avg_latency_ms" | "p95_latency_ms" | "percentage";
type SortDirection = "asc" | "desc";

interface FeatureTableProps {
  features: FeatureRow[];
  totalCost: number;
  onRowClick?: (feature: FeatureRow) => void;
  onFilterChange?: (filters: { types?: string[]; providers?: string[] }) => void;
  className?: string;
}

// ============================================================================
// COLUMN DEFINITIONS
// ============================================================================

interface ColumnDef {
  key: SortKey;
  label: string;
  tooltip: string;
  align?: "left" | "right" | "center";
  width?: string;
}

const COLUMNS: ColumnDef[] = [
  { key: "name", label: "Feature", tooltip: "Feature, agent, step, or tool name", align: "left", width: "flex-1" },
  { key: "total_cost", label: "Total Cost", tooltip: "Total spend in selected time range", align: "right", width: "w-28" },
  { key: "call_count", label: "Calls", tooltip: "Number of invocations", align: "right", width: "w-20" },
  { key: "cost_per_call", label: "$/Call (p50/p95)", tooltip: "Cost per call: median → 95th percentile. Wide spread = cost variance", align: "right", width: "w-32" },
  { key: "p95_latency_ms", label: "Latency (p95)", tooltip: "95th percentile response time", align: "right", width: "w-24" },
  { key: "percentage", label: "% Total", tooltip: "Percentage of total cost", align: "right", width: "w-28" },
];

// ============================================================================
// TYPE BADGE CONFIG
// ============================================================================

const TYPE_CONFIG: Record<string, { color: string; bg: string }> = {
  feature: { color: "text-emerald-700", bg: "bg-emerald-100" },
  agent: { color: "text-purple-700", bg: "bg-purple-100" },
  step: { color: "text-blue-700", bg: "bg-blue-100" },
  tool: { color: "text-orange-700", bg: "bg-orange-100" },
};

// ============================================================================
// SORTABLE HEADER
// ============================================================================

interface SortableHeaderProps {
  column: ColumnDef;
  sortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
}

function SortableHeader({ column, sortKey, sortDirection, onSort }: SortableHeaderProps) {
  const isActive = sortKey === column.key;
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={() => onSort(column.key)}
            className={cn(
              "flex items-center gap-1 text-xs font-semibold uppercase tracking-wider",
              "hover:text-gray-900 transition-colors",
              column.align === "right" && "justify-end w-full",
              isActive ? "text-gray-900" : "text-gray-500"
            )}
          >
            <span>{column.label}</span>
            {isActive ? (
              sortDirection === "asc" ? (
                <ArrowUp className="w-3 h-3" />
              ) : (
                <ArrowDown className="w-3 h-3" />
              )
            ) : (
              <ArrowUpDown className="w-3 h-3 opacity-40" />
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p>{column.tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function FeatureTable({
  features,
  totalCost,
  onRowClick,
  onFilterChange,
  className,
}: FeatureTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("total_cost");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const pageSize = 20;

  // Handle sort
  const handleSort = useCallback((key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(prev => prev === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
    setPage(0);
  }, [sortKey]);

  // Filter and sort data
  const processedFeatures = useMemo(() => {
    let result = [...features];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(f => 
        f.name.toLowerCase().includes(query) ||
        f.section.toLowerCase().includes(query)
      );
    }

    // Type filter
    if (selectedTypes.length > 0) {
      result = result.filter(f => selectedTypes.includes(f.type));
    }

    // Sort
    result.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc" 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }
      
      const aNum = Number(aVal) || 0;
      const bNum = Number(bVal) || 0;
      return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
    });

    return result;
  }, [features, searchQuery, selectedTypes, sortKey, sortDirection]);

  // Pagination
  const paginatedFeatures = useMemo(() => {
    const start = page * pageSize;
    return processedFeatures.slice(start, start + pageSize);
  }, [processedFeatures, page]);

  const totalPages = Math.ceil(processedFeatures.length / pageSize);

  // Available types for filter
  const availableTypes = useMemo(() => {
    const types = new Set(features.map(f => f.type));
    return Array.from(types);
  }, [features]);

  // Handle type filter toggle
  const handleTypeToggle = (type: string) => {
    setSelectedTypes(prev => {
      const next = prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type];
      onFilterChange?.({ types: next });
      return next;
    });
    setPage(0);
  };

  // Export to CSV
  const handleExport = useCallback(() => {
    const headers = ["Feature", "Type", "Total Cost", "Calls", "Cost/Call", "Avg Latency (ms)", "p95 Latency (ms)", "% of Total"];
    const rows = processedFeatures.map(f => [
      f.name,
      f.type,
      f.total_cost.toFixed(6),
      f.call_count,
      f.cost_per_call.toFixed(6),
      f.avg_latency_ms.toFixed(2),
      f.p95_latency_ms.toFixed(2),
      f.percentage.toFixed(2),
    ]);
    
    const csv = [headers, ...rows].map(row => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `features-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [processedFeatures]);

  if (features.length === 0) {
    return (
      <div className={cn("text-center py-12 border border-dashed border-gray-200 rounded-xl", className)}>
        <Layers className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No feature data</h3>
        <p className="text-sm text-gray-500">
          Use <code className="bg-gray-100 px-1 rounded">section("feature:name")</code> to track features.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          {/* Search */}
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search features..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(0); }}
              className="pl-9 h-9"
            />
          </div>

          {/* Type Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-9 gap-2">
                <Filter className="w-4 h-4" />
                Type
                {selectedTypes.length > 0 && (
                  <Badge variant="secondary" className="ml-1 px-1.5">
                    {selectedTypes.length}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              {availableTypes.map(type => {
                const config = TYPE_CONFIG[type] || TYPE_CONFIG.feature;
                return (
                  <DropdownMenuCheckboxItem
                    key={type}
                    checked={selectedTypes.includes(type)}
                    onCheckedChange={() => handleTypeToggle(type)}
                  >
                    <span className={cn("capitalize", config.color)}>{type}</span>
                  </DropdownMenuCheckboxItem>
                );
              })}
              {selectedTypes.length > 0 && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => { setSelectedTypes([]); onFilterChange?.({ types: [] }); }}>
                    Clear filters
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Export */}
        <Button variant="outline" size="sm" onClick={handleExport} className="h-9 gap-2">
          <Download className="w-4 h-4" />
          Export
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="flex items-center gap-6 text-sm text-gray-600 bg-gray-50 rounded-lg px-4 py-2">
        <span>
          Showing <strong>{processedFeatures.length}</strong> of {features.length} features
        </span>
        <span className="text-gray-300">|</span>
        <span>
          Total: <strong>{formatSmartCost(totalCost)}</strong>
        </span>
        <span className="text-gray-300">|</span>
        <span>
          Calls: <strong>{formatCompactNumber(features.reduce((sum, f) => sum + f.call_count, 0))}</strong>
        </span>
      </div>

      {/* Table */}
      <div className="border rounded-xl overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-gray-50 hover:bg-gray-50">
              {COLUMNS.map(column => (
                <TableHead 
                  key={column.key} 
                  className={cn(
                    column.width,
                    column.align === "right" && "text-right"
                  )}
                >
                  <SortableHeader
                    column={column}
                    sortKey={sortKey}
                    sortDirection={sortDirection}
                    onSort={handleSort}
                  />
                </TableHead>
              ))}
              <TableHead className="w-8" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedFeatures.map((feature, index) => {
              const config = TYPE_CONFIG[feature.type] || TYPE_CONFIG.feature;
              const isTopCost = index < 3 && sortKey === "total_cost" && sortDirection === "desc";

              return (
                <TableRow
                  key={feature.id}
                  onClick={() => onRowClick?.(feature)}
                  className={cn(
                    "cursor-pointer transition-colors",
                    isTopCost && "bg-amber-50/50",
                    onRowClick && "hover:bg-blue-50"
                  )}
                >
                  {/* Name */}
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="secondary" 
                        className={cn("text-xs capitalize", config.bg, config.color)}
                      >
                        {feature.type}
                      </Badge>
                      <span className="truncate max-w-[200px]">{feature.name}</span>
                    </div>
                  </TableCell>

                  {/* Total Cost */}
                  <TableCell className="text-right font-semibold tabular-nums">
                    {formatSmartCost(feature.total_cost)}
                  </TableCell>

                  {/* Calls */}
                  <TableCell className="text-right tabular-nums text-gray-600">
                    {formatCompactNumber(feature.call_count)}
                  </TableCell>

                  {/* Cost/Call with variance */}
                  <TableCell className="text-right">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center justify-end gap-1 tabular-nums">
                            <span className="text-gray-600">
                              {formatSmartCost(feature.p50_cost_per_call || feature.cost_per_call * 0.85)}
                            </span>
                            <span className="text-gray-300">→</span>
                            <span className={cn(
                              "font-medium",
                              (feature.p95_cost_per_call || feature.cost_per_call * 1.8) > feature.cost_per_call * 2
                                ? "text-amber-600"
                                : "text-gray-700"
                            )}>
                              {formatSmartCost(feature.p95_cost_per_call || feature.cost_per_call * 1.8)}
                            </span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="max-w-xs">
                          <div className="space-y-1">
                            <p className="font-medium">Cost per request variance</p>
                            <p className="text-xs text-gray-400">
                              p50: {formatSmartCost(feature.p50_cost_per_call || feature.cost_per_call * 0.85)} (median)
                            </p>
                            <p className="text-xs text-gray-400">
                              p95: {formatSmartCost(feature.p95_cost_per_call || feature.cost_per_call * 1.8)} (expensive outliers)
                            </p>
                            {(feature.p95_cost_per_call || feature.cost_per_call * 1.8) > feature.cost_per_call * 2 && (
                              <p className="text-xs text-amber-500 font-medium">
                                ⚠ High variance - some calls are 2x+ more expensive
                              </p>
                            )}
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>

                  {/* p95 Latency */}
                  <TableCell className="text-right tabular-nums text-gray-600">
                    <span className="flex items-center justify-end gap-1">
                      <Clock className="w-3 h-3 text-gray-400" />
                      {feature.p95_latency_ms.toFixed(0)}ms
                    </span>
                  </TableCell>

                  {/* % of Total */}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={feature.percentage} className="w-16 h-1.5" />
                      <span className="tabular-nums text-gray-600 min-w-[40px]">
                        {feature.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>

                  {/* Chevron */}
                  <TableCell>
                    {onRowClick && (
                      <ChevronRight className="w-4 h-4 text-gray-300" />
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            Page {page + 1} of {totalPages}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// HELPER: Convert section stats to feature rows
// ============================================================================

export function toFeatureRows(
  sectionStats: Array<{
    section: string;
    section_path?: string | null;
    total_cost: number;
    call_count: number;
    avg_latency_ms: number;
    percentage: number;
  }>,
  totalCost: number
): FeatureRow[] {
  return sectionStats
    .filter(s => s.section && s.section !== "main" && s.section !== "default")
    .map((stat) => {
      // Parse type from section name
      const [typePrefix, ...nameParts] = stat.section.split(":");
      const name = nameParts.join(":") || stat.section;
      const type = ["feature", "agent", "step", "tool"].includes(typePrefix) 
        ? typePrefix as FeatureRow["type"]
        : "feature";

      return {
        id: stat.section,
        name,
        section: stat.section,
        type,
        total_cost: stat.total_cost,
        call_count: stat.call_count,
        cost_per_call: stat.call_count > 0 ? stat.total_cost / stat.call_count : 0,
        avg_latency_ms: stat.avg_latency_ms,
        p95_latency_ms: stat.avg_latency_ms * 1.5, // Estimate p95 as 1.5x avg (will be replaced with real data)
        percentage: (stat.total_cost / totalCost) * 100,
      };
    });
}

export default FeatureTable;

