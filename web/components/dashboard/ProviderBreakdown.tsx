"use client";

import { useMemo, useState } from "react";
import { formatSmartCost, formatPercentChange } from "@/lib/format";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, ChevronDown, ChevronUp } from "lucide-react";

interface ProviderStat {
  provider: string;
  total_cost: number;
  call_count: number;
  percentage?: number;
  trend?: number; // Percentage change from previous period
}

interface ProviderBreakdownProps {
  providers: ProviderStat[];
  totalCost: number;
  className?: string;
}

// Provider color mapping - vibrant, distinctive colors
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10b981",      // emerald
  anthropic: "#8b5cf6",   // violet
  cohere: "#6366f1",      // indigo
  google: "#3b82f6",      // blue
  mistral: "#ec4899",     // pink
  pinecone: "#f97316",    // orange
  stripe: "#a855f7",      // purple
  vapi: "#06b6d4",        // cyan
  elevenlabs: "#14b8a6",  // teal
  twilio: "#f59e0b",      // amber
  voyage: "#84cc16",      // lime
};

const DEFAULT_COLOR = "#64748b"; // slate-500

export function ProviderBreakdown({
  providers,
  totalCost,
  className,
}: ProviderBreakdownProps) {
  const [showAll, setShowAll] = useState(false);
  
  // Sort by cost and split into top 5 + others
  const { topProviders, othersData, topCostDriver, fastestGrowing } = useMemo(() => {
    const sorted = [...providers].sort((a, b) => b.total_cost - a.total_cost);
    const top5 = sorted.slice(0, 5);
    const rest = sorted.slice(5);
    
    // Calculate "Others" aggregate
    const othersTotal = rest.reduce((sum, p) => sum + p.total_cost, 0);
    const othersCalls = rest.reduce((sum, p) => sum + p.call_count, 0);
    
    // Find insights
    const topDriver = sorted[0];
    const growing = sorted.filter(p => p.trend && p.trend > 0).sort((a, b) => (b.trend || 0) - (a.trend || 0))[0];
    
    return {
      topProviders: top5,
      othersData: rest.length > 0 ? { 
        provider: 'others', 
        total_cost: othersTotal, 
        call_count: othersCalls,
        count: rest.length 
      } : null,
      topCostDriver: topDriver,
      fastestGrowing: growing,
    };
  }, [providers]);

  const displayProviders = showAll ? providers : topProviders;

  if (providers.length === 0) {
    return (
      <div className={cn("bg-white rounded-xl border border-slate-200/60 p-5", className)}>
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Provider Breakdown</h3>
        <p className="text-sm text-slate-400">No provider data</p>
      </div>
    );
  }

  return (
    <div className={cn("bg-white rounded-xl border border-slate-200/60 p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-900">Provider Breakdown</h3>
        {/* Quick insights */}
        <div className="flex items-center gap-2 text-xs">
          {topCostDriver && (
            <span className="text-slate-500">
              Top: <span className="font-medium text-slate-700 capitalize">{topCostDriver.provider}</span>
            </span>
          )}
        </div>
      </div>
      
      {/* Stacked horizontal bar */}
      <div className="h-3 rounded-full overflow-hidden flex bg-slate-100 mb-5">
        {displayProviders.map((provider) => {
          const percentage = totalCost > 0 ? (provider.total_cost / totalCost) * 100 : 0;
          if (percentage < 0.5) return null; // Don't show tiny slivers
          
          return (
            <div
              key={provider.provider}
              className="h-full first:rounded-l-full last:rounded-r-full transition-all duration-300"
              style={{ 
                width: `${percentage}%`,
                backgroundColor: PROVIDER_COLORS[provider.provider.toLowerCase()] || DEFAULT_COLOR,
              }}
              title={`${provider.provider}: ${formatSmartCost(provider.total_cost)} (${percentage.toFixed(1)}%)`}
            />
          );
        })}
        {othersData && !showAll && othersData.total_cost > 0 && (
          <div
            className="h-full rounded-r-full bg-slate-300"
            style={{ width: `${(othersData.total_cost / totalCost) * 100}%` }}
            title={`Others: ${formatSmartCost(othersData.total_cost)}`}
          />
        )}
      </div>
      
      {/* Provider list */}
      <div className="space-y-2.5">
        {displayProviders.map((provider) => {
          const percentage = totalCost > 0 ? (provider.total_cost / totalCost) * 100 : 0;
          const color = PROVIDER_COLORS[provider.provider.toLowerCase()] || DEFAULT_COLOR;
          
          return (
            <div key={provider.provider} className="flex items-center gap-3">
              {/* Color dot */}
              <div 
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              
              {/* Provider name */}
              <span className="text-sm font-medium text-slate-700 capitalize flex-1 min-w-0 truncate">
                {provider.provider}
              </span>
              
              {/* Cost */}
              <span className="text-sm font-semibold text-slate-900 tabular-nums">
                {formatSmartCost(provider.total_cost)}
              </span>
              
              {/* Percentage */}
              <span className="text-xs text-slate-400 w-12 text-right tabular-nums">
                {percentage.toFixed(0)}%
              </span>
              
              {/* Trend if available */}
              {provider.trend !== undefined && provider.trend !== 0 && (
                <span className={cn(
                  "flex items-center gap-0.5 text-xs",
                  provider.trend > 0 ? "text-rose-500" : "text-emerald-500"
                )}>
                  {provider.trend > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                </span>
              )}
            </div>
          );
        })}
        
        {/* Others row */}
        {othersData && !showAll && othersData.total_cost > 0 && (
          <div className="flex items-center gap-3 text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full bg-slate-300 flex-shrink-0" />
            <span className="text-sm flex-1">
              +{othersData.count} more
            </span>
            <span className="text-sm font-medium text-slate-500 tabular-nums">
              {formatSmartCost(othersData.total_cost)}
            </span>
            <span className="text-xs w-12 text-right tabular-nums">
              {((othersData.total_cost / totalCost) * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
      
      {/* Expand/collapse button */}
      {providers.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="mt-4 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition-colors"
        >
          {showAll ? (
            <>
              <ChevronUp className="w-3.5 h-3.5" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-3.5 h-3.5" />
              Show all {providers.length} providers
            </>
          )}
        </button>
      )}
    </div>
  );
}

