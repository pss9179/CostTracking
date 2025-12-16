"use client";

import { useMemo, useState } from "react";
import { formatSmartCost, getModelFamily } from "@/lib/format";
import { cn } from "@/lib/utils";
import { ChevronRight, ChevronDown, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";

interface ModelStat {
  model: string;
  provider: string;
  total_cost: number;
  call_count: number;
  percentage?: number;
  trend?: number; // Percentage change
}

interface ModelBreakdownProps {
  models: ModelStat[];
  totalCost: number;
  className?: string;
}

// Family color mapping
const FAMILY_COLORS: Record<string, string> = {
  "GPT-4o": "#10b981",
  "GPT-4 Turbo": "#059669",
  "GPT-4": "#047857",
  "GPT-3.5": "#34d399",
  "Claude 3.5 Sonnet": "#8b5cf6",
  "Claude 3.5 Haiku": "#a78bfa",
  "Claude 3 Opus": "#7c3aed",
  "Claude 3 Sonnet": "#8b5cf6",
  "Claude 3 Haiku": "#a78bfa",
  "Claude 2": "#c4b5fd",
  "Claude": "#8b5cf6",
  "Gemini Pro": "#3b82f6",
  "Gemini Flash": "#60a5fa",
  "Gemini": "#3b82f6",
  "Mistral Large": "#ec4899",
  "Mistral Medium": "#f472b6",
  "Mistral Small": "#f9a8d4",
  "Mistral": "#ec4899",
};

const DEFAULT_COLOR = "#64748b";

interface ModelFamily {
  family: string;
  models: ModelStat[];
  totalCost: number;
  totalCalls: number;
  avgCostPerCall: number;
}

export function ModelBreakdown({
  models,
  totalCost,
  className,
}: ModelBreakdownProps) {
  const [expandedFamilies, setExpandedFamilies] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'cost' | 'calls'>('cost');
  
  // Group models by family
  const { families, topSpender, anomaly } = useMemo(() => {
    const familyMap = new Map<string, ModelStat[]>();
    
    models.forEach(model => {
      const family = getModelFamily(model.model);
      const existing = familyMap.get(family) || [];
      existing.push(model);
      familyMap.set(family, existing);
    });
    
    const familyData: ModelFamily[] = Array.from(familyMap.entries()).map(([family, familyModels]) => {
      const famTotalCost = familyModels.reduce((sum, m) => sum + m.total_cost, 0);
      const famTotalCalls = familyModels.reduce((sum, m) => sum + m.call_count, 0);
      
      return {
        family,
        models: familyModels.sort((a, b) => b.total_cost - a.total_cost),
        totalCost: famTotalCost,
        totalCalls: famTotalCalls,
        avgCostPerCall: famTotalCalls > 0 ? famTotalCost / famTotalCalls : 0,
      };
    });
    
    // Sort families
    const sorted = familyData.sort((a, b) => 
      sortBy === 'cost' ? b.totalCost - a.totalCost : b.totalCalls - a.totalCalls
    );
    
    // Find insights
    const topFam = sorted[0];
    
    // Find anomaly: model with unusually high cost per call
    const avgCostPerCall = totalCost / models.reduce((sum, m) => sum + m.call_count, 0) || 0;
    const anomalyModel = models.find(m => {
      const modelAvg = m.call_count > 0 ? m.total_cost / m.call_count : 0;
      return modelAvg > avgCostPerCall * 3 && m.call_count > 5; // 3x average and at least 5 calls
    });
    
    return {
      families: sorted,
      topSpender: topFam,
      anomaly: anomalyModel,
    };
  }, [models, totalCost, sortBy]);

  const toggleFamily = (family: string) => {
    const newExpanded = new Set(expandedFamilies);
    if (newExpanded.has(family)) {
      newExpanded.delete(family);
    } else {
      newExpanded.add(family);
    }
    setExpandedFamilies(newExpanded);
  };

  if (models.length === 0) {
    return (
      <div className={cn("bg-white rounded-xl border border-slate-200/60 p-5", className)}>
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Model Breakdown</h3>
        <p className="text-sm text-slate-400">No model data</p>
      </div>
    );
  }

  return (
    <div className={cn("bg-white rounded-xl border border-slate-200/60 p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-900">Model Breakdown</h3>
        
        {/* Sort toggle */}
        <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
          <button
            onClick={() => setSortBy('cost')}
            className={cn(
              "px-2 py-1 text-xs font-medium rounded-md transition-colors",
              sortBy === 'cost' 
                ? "bg-white text-slate-900 shadow-sm" 
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            Cost
          </button>
          <button
            onClick={() => setSortBy('calls')}
            className={cn(
              "px-2 py-1 text-xs font-medium rounded-md transition-colors",
              sortBy === 'calls' 
                ? "bg-white text-slate-900 shadow-sm" 
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            Calls
          </button>
        </div>
      </div>
      
      {/* Anomaly alert */}
      {anomaly && (
        <div className="mb-4 flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-700">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>
            <span className="font-medium">{anomaly.model}</span> has unusually high cost per call
          </span>
        </div>
      )}
      
      {/* Family list */}
      <div className="space-y-1">
        {families.map((family) => {
          const isExpanded = expandedFamilies.has(family.family);
          const percentage = totalCost > 0 ? (family.totalCost / totalCost) * 100 : 0;
          const color = FAMILY_COLORS[family.family] || DEFAULT_COLOR;
          const hasMultipleModels = family.models.length > 1;
          
          return (
            <div key={family.family}>
              {/* Family row */}
              <button
                onClick={() => hasMultipleModels && toggleFamily(family.family)}
                disabled={!hasMultipleModels}
                className={cn(
                  "w-full flex items-center gap-2 py-2 px-2 -mx-2 rounded-lg transition-colors",
                  hasMultipleModels && "hover:bg-slate-50 cursor-pointer",
                  !hasMultipleModels && "cursor-default"
                )}
              >
                {/* Expand/collapse icon */}
                <div className="w-4 flex-shrink-0">
                  {hasMultipleModels && (
                    isExpanded 
                      ? <ChevronDown className="w-4 h-4 text-slate-400" />
                      : <ChevronRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
                
                {/* Color indicator + bar */}
                <div className="flex-1 flex items-center gap-2 min-w-0">
                  <div 
                    className="w-1.5 h-6 rounded-full flex-shrink-0"
                    style={{ backgroundColor: color }}
                  />
                  
                  {/* Progress bar background */}
                  <div className="flex-1 relative h-6 bg-slate-50 rounded overflow-hidden">
                    <div 
                      className="absolute left-0 top-0 bottom-0 rounded transition-all duration-300"
                      style={{ 
                        width: `${Math.max(percentage, 1)}%`,
                        backgroundColor: color,
                        opacity: 0.15,
                      }}
                    />
                    <div className="relative z-10 h-full flex items-center px-2">
                      <span className="text-sm font-medium text-slate-800 truncate">
                        {family.family}
                      </span>
                      {family.models.length > 1 && (
                        <span className="text-xs text-slate-400 ml-1">
                          ({family.models.length})
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Stats */}
                <div className="flex items-center gap-4 text-right flex-shrink-0">
                  <span className="text-xs text-slate-500 tabular-nums w-10">
                    {family.totalCalls}
                  </span>
                  <span className="text-sm font-semibold text-slate-900 tabular-nums w-16">
                    {formatSmartCost(family.totalCost)}
                  </span>
                  <span className="text-xs text-slate-400 tabular-nums w-10">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              </button>
              
              {/* Expanded model details */}
              {isExpanded && hasMultipleModels && (
                <div className="ml-6 pl-3 border-l-2 border-slate-100 space-y-1 mb-2">
                  {family.models.map((model) => {
                    const modelPercentage = totalCost > 0 ? (model.total_cost / totalCost) * 100 : 0;
                    const costPerCall = model.call_count > 0 ? model.total_cost / model.call_count : 0;
                    
                    return (
                      <div 
                        key={model.model}
                        className="flex items-center gap-2 py-1.5 text-sm"
                      >
                        <span className="flex-1 text-slate-600 truncate font-mono text-xs">
                          {model.model}
                        </span>
                        <span className="text-xs text-slate-400 tabular-nums">
                          {model.call_count} calls
                        </span>
                        <span className="text-xs text-slate-400 tabular-nums">
                          {formatSmartCost(costPerCall)}/call
                        </span>
                        <span className="text-sm font-medium text-slate-700 tabular-nums w-16 text-right">
                          {formatSmartCost(model.total_cost)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Footer insight */}
      <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500">
        {families.length} model families • {models.length} unique models
      </div>
    </div>
  );
}

