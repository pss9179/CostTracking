"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import { TrendingUp, TrendingDown, Minus, DollarSign, Zap, Clock, Layers, Server, Cpu } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// ============================================================================
// TYPES
// ============================================================================

interface KPIData {
  totalCost: number;
  costPerRequest: number;
  avgCostPerFeature: number;
  p95CostPerFeature: number;
  p50Latency: number;
  p95Latency: number;
  topProviderPct: { name: string; pct: number } | null;
  topModelPct: { name: string; pct: number } | null;
  totalCalls: number;
  totalFeatures: number;
}

interface KPIGridProps {
  data: KPIData;
  onKPIClick?: (kpiType: string, value?: string) => void;
  className?: string;
}

interface KPICardProps {
  label: string;
  value: string | number;
  subValue?: string;
  tooltip: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "flat";
  onClick?: () => void;
  highlight?: boolean;
}

// ============================================================================
// KPI CARD COMPONENT
// ============================================================================

function KPICard({ 
  label, 
  value, 
  subValue, 
  tooltip, 
  icon, 
  trend, 
  onClick,
  highlight 
}: KPICardProps) {
  const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
  const trendColor = trend === "up" ? "text-rose-500" : trend === "down" ? "text-emerald-500" : "text-gray-400";

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={onClick}
            className={cn(
              "flex flex-col items-start p-4 rounded-xl border transition-all duration-200",
              "hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-sm",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
              highlight ? "bg-slate-900 text-white border-slate-700" : "bg-white border-gray-200",
              onClick && "cursor-pointer"
            )}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className={cn("text-gray-400", highlight && "text-gray-500")}>
                {icon}
              </span>
              <span className={cn(
                "text-xs font-medium uppercase tracking-wider",
                highlight ? "text-gray-400" : "text-gray-500"
              )}>
                {label}
              </span>
            </div>
            
            <div className="flex items-baseline gap-2">
              <span className={cn(
                "text-2xl font-bold tabular-nums",
                highlight ? "text-white" : "text-gray-900"
              )}>
                {typeof value === "number" ? formatSmartCost(value) : value}
              </span>
              {trend && (
                <TrendIcon className={cn("w-4 h-4", trendColor)} />
              )}
            </div>
            
            {subValue && (
              <span className={cn(
                "text-xs mt-1",
                highlight ? "text-gray-400" : "text-gray-500"
              )}>
                {subValue}
              </span>
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs">
          <p className="text-sm">{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================================================
// KPI GRID COMPONENT
// ============================================================================

export function KPIGrid({ data, onKPIClick, className }: KPIGridProps) {
  const handleClick = (type: string, value?: string) => {
    if (onKPIClick) {
      onKPIClick(type, value);
    }
  };

  return (
    <div className={cn("grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-3", className)}>
      {/* Row 1: Cost metrics */}
      <KPICard
        label="Total Cost"
        value={data.totalCost}
        tooltip="Total spend across all providers and models in the selected time range. Click to view cost breakdown."
        icon={<DollarSign className="w-4 h-4" />}
        onClick={() => handleClick("total_cost")}
        highlight
      />
      
      <KPICard
        label="Cost / Request"
        value={formatSmartCost(data.costPerRequest)}
        tooltip="Average cost per API request. Lower is better. Click to see requests by cost."
        icon={<Zap className="w-4 h-4" />}
        onClick={() => handleClick("cost_per_request")}
      />
      
      <KPICard
        label="Avg Cost / Feature"
        value={formatSmartCost(data.avgCostPerFeature)}
        subValue={`p95: ${formatSmartCost(data.p95CostPerFeature)}`}
        tooltip="Average cost per feature invocation. p95 shows the 95th percentile (expensive outliers)."
        icon={<Layers className="w-4 h-4" />}
        onClick={() => handleClick("cost_per_feature")}
      />
      
      <KPICard
        label="Total Requests"
        value={formatCompactNumber(data.totalCalls)}
        subValue={`${data.totalFeatures} features`}
        tooltip="Total API requests in the selected time range across all features."
        icon={<Zap className="w-4 h-4" />}
        onClick={() => handleClick("total_calls")}
      />
      
      {/* Row 2: Latency + Distribution */}
      <KPICard
        label="p50 Latency"
        value={`${data.p50Latency.toFixed(0)}ms`}
        subValue={`p95: ${data.p95Latency.toFixed(0)}ms`}
        tooltip="Median response latency. p95 shows slowest 5% of requests."
        icon={<Clock className="w-4 h-4" />}
        onClick={() => handleClick("latency")}
      />
      
      {data.topProviderPct && (
        <KPICard
          label="Top Provider"
          value={`${data.topProviderPct.pct.toFixed(0)}%`}
          subValue={data.topProviderPct.name}
          tooltip={`${data.topProviderPct.name} accounts for ${data.topProviderPct.pct.toFixed(1)}% of total cost. Click to filter by provider.`}
          icon={<Server className="w-4 h-4" />}
          onClick={() => handleClick("provider", data.topProviderPct?.name)}
        />
      )}
      
      {data.topModelPct && (
        <KPICard
          label="Top Model"
          value={`${data.topModelPct.pct.toFixed(0)}%`}
          subValue={data.topModelPct.name}
          tooltip={`${data.topModelPct.name} accounts for ${data.topModelPct.pct.toFixed(1)}% of total cost. Click to filter by model.`}
          icon={<Cpu className="w-4 h-4" />}
          onClick={() => handleClick("model", data.topModelPct?.name)}
        />
      )}
    </div>
  );
}

// ============================================================================
// HELPER: Calculate KPIs from raw data
// ============================================================================

export function calculateKPIs(
  providerStats: Array<{ provider: string; total_cost: number; call_count: number }>,
  modelStats: Array<{ model: string; total_cost: number; call_count: number }>,
  sectionStats?: Array<{ section: string; total_cost: number; call_count: number; avg_latency_ms: number }>,
): KPIData {
  const totalCost = providerStats.reduce((sum, p) => sum + p.total_cost, 0);
  const totalCalls = providerStats.reduce((sum, p) => sum + p.call_count, 0);
  
  // Cost per request
  const costPerRequest = totalCalls > 0 ? totalCost / totalCalls : 0;
  
  // Feature costs (if available)
  const featureCosts = sectionStats?.map(s => s.total_cost / Math.max(s.call_count, 1)) || [];
  const avgCostPerFeature = featureCosts.length > 0 
    ? featureCosts.reduce((a, b) => a + b, 0) / featureCosts.length 
    : costPerRequest;
  const sortedFeatureCosts = [...featureCosts].sort((a, b) => a - b);
  const p95CostPerFeature = sortedFeatureCosts.length > 0 
    ? sortedFeatureCosts[Math.floor(sortedFeatureCosts.length * 0.95)] || sortedFeatureCosts[sortedFeatureCosts.length - 1]
    : avgCostPerFeature;
  
  // Latencies
  const latencies = sectionStats?.map(s => s.avg_latency_ms) || [];
  const sortedLatencies = [...latencies].sort((a, b) => a - b);
  const p50Latency = sortedLatencies.length > 0 
    ? sortedLatencies[Math.floor(sortedLatencies.length * 0.5)] || 0
    : 0;
  const p95Latency = sortedLatencies.length > 0 
    ? sortedLatencies[Math.floor(sortedLatencies.length * 0.95)] || sortedLatencies[sortedLatencies.length - 1]
    : 0;
  
  // Top provider
  const sortedProviders = [...providerStats].sort((a, b) => b.total_cost - a.total_cost);
  const topProvider = sortedProviders[0];
  const topProviderPct = topProvider && totalCost > 0
    ? { name: topProvider.provider, pct: (topProvider.total_cost / totalCost) * 100 }
    : null;
  
  // Top model
  const sortedModels = [...modelStats].sort((a, b) => b.total_cost - a.total_cost);
  const topModel = sortedModels[0];
  const topModelPct = topModel && totalCost > 0
    ? { name: topModel.model, pct: (topModel.total_cost / totalCost) * 100 }
    : null;
  
  return {
    totalCost,
    costPerRequest,
    avgCostPerFeature,
    p95CostPerFeature,
    p50Latency,
    p95Latency,
    topProviderPct,
    topModelPct,
    totalCalls,
    totalFeatures: sectionStats?.length || 0,
  };
}

export default KPIGrid;

