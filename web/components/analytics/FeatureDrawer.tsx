"use client";

import { useMemo } from "react";
import { X, DollarSign, Zap, Clock, BarChart2, TrendingUp, TrendingDown, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatCompactNumber,
  formatDuration,
  formatPercentage,
  formatPercentChange,
  parseFeatureSection,
  getFeatureTypeColor,
  getStableColor,
} from "@/lib/format";
import type { FeatureNode } from "./FeatureTreeTable";

// ============================================================================
// TYPES
// ============================================================================

interface TrendDataPoint {
  date: string;
  cost: number;
  calls: number;
}

interface ProviderBreakdown {
  provider: string;
  cost: number;
  calls: number;
  percentage: number;
}

interface ModelBreakdown {
  model: string;
  cost: number;
  calls: number;
  percentage: number;
}

interface FeatureDrawerProps {
  open: boolean;
  onClose: () => void;
  feature: FeatureNode | null;
  totalCost: number;
  
  // Optional data for detailed view
  trendData?: TrendDataPoint[];
  providerBreakdown?: ProviderBreakdown[];
  modelBreakdown?: ModelBreakdown[];
  
  // Actions
  onProviderClick?: (provider: string) => void;
  onModelClick?: (model: string) => void;
}

// ============================================================================
// STAT CARD
// ============================================================================

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subValue?: string;
  trend?: 'up' | 'down' | 'flat';
}

function StatCard({ icon, label, value, subValue, trend }: StatCardProps) {
  return (
    <div className="bg-slate-50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-slate-400">{icon}</span>
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-bold text-slate-900 tabular-nums">{value}</span>
        {trend && trend !== 'flat' && (
          <span className={cn(
            "text-xs font-medium",
            trend === 'up' ? "text-rose-500" : "text-emerald-500"
          )}>
            {trend === 'up' ? <TrendingUp className="w-3 h-3 inline" /> : <TrendingDown className="w-3 h-3 inline" />}
          </span>
        )}
      </div>
      {subValue && (
        <p className="text-xs text-slate-400 mt-0.5">{subValue}</p>
      )}
    </div>
  );
}

// ============================================================================
// BREAKDOWN LIST
// ============================================================================

interface BreakdownListProps<T> {
  title: string;
  data: T[];
  totalCost: number;
  getName: (item: T) => string;
  getCost: (item: T) => number;
  getCalls: (item: T) => number;
  onItemClick?: (item: T) => void;
  topN?: number;
}

function BreakdownList<T>({
  title,
  data,
  totalCost,
  getName,
  getCost,
  getCalls,
  onItemClick,
  topN = 5,
}: BreakdownListProps<T>) {
  const sorted = useMemo(() => 
    [...data].sort((a, b) => getCost(b) - getCost(a)).slice(0, topN),
    [data, topN]
  );
  
  if (data.length === 0) return null;
  
  return (
    <div>
      <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">{title}</h4>
      <div className="space-y-2">
        {sorted.map((item, i) => {
          const name = getName(item);
          const cost = getCost(item);
          const calls = getCalls(item);
          const percentage = totalCost > 0 ? (cost / totalCost) * 100 : 0;
          const color = getStableColor(name);
          
          return (
            <button
              key={name}
              onClick={() => onItemClick?.(item)}
              className={cn(
                "w-full flex items-center gap-3 p-2 rounded-lg transition-colors",
                onItemClick ? "hover:bg-slate-50 cursor-pointer" : "cursor-default"
              )}
            >
              <div 
                className="w-1.5 h-6 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-medium text-slate-800 capitalize truncate">{name}</p>
                <p className="text-xs text-slate-400">{formatCompactNumber(calls)} calls</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900 tabular-nums">{formatSmartCost(cost)}</p>
                <p className="text-xs text-slate-400 tabular-nums">{formatPercentage(percentage)}</p>
              </div>
            </button>
          );
        })}
        
        {data.length > topN && (
          <p className="text-xs text-slate-400 text-center pt-1">
            +{data.length - topN} more
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function FeatureDrawer({
  open,
  onClose,
  feature,
  totalCost,
  trendData,
  providerBreakdown,
  modelBreakdown,
  onProviderClick,
  onModelClick,
}: FeatureDrawerProps) {
  if (!feature) return null;
  
  const parsed = parseFeatureSection(feature.section);
  const costPerCall = feature.call_count > 0 ? feature.total_cost / feature.call_count : 0;
  const percentage = totalCost > 0 ? (feature.total_cost / totalCost) * 100 : 0;
  const color = getStableColor(feature.section);
  
  // Root handling
  const isRoot = feature.section === 'main' || feature.section === 'default' || feature.section === 'Root';
  const displayName = isRoot ? 'Uncategorized Calls' : parsed.displayName;
  
  return (
    <Sheet open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader className="pb-4 border-b border-slate-100">
          <div className="flex items-start gap-3">
            <div 
              className="w-1.5 h-12 rounded-full flex-shrink-0"
              style={{ backgroundColor: color }}
            />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {!isRoot && (
                  <Badge 
                    variant="secondary" 
                    className={cn("text-xs", getFeatureTypeColor(parsed.type))}
                  >
                    {parsed.type}
                  </Badge>
                )}
              </div>
              <SheetTitle className={cn(
                "text-xl text-left",
                isRoot && "text-slate-500 italic"
              )}>
                {displayName}
              </SheetTitle>
              {feature.section_path && feature.section_path !== feature.section && (
                <p className="text-xs text-slate-400 mt-1 font-mono truncate">
                  {feature.section_path}
                </p>
              )}
            </div>
          </div>
        </SheetHeader>
        
        <div className="py-6 space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 gap-3">
            <StatCard
              icon={<DollarSign className="w-4 h-4" />}
              label="Total Cost"
              value={formatSmartCost(feature.total_cost)}
              subValue={`${formatPercentage(percentage)} of total`}
            />
            <StatCard
              icon={<Zap className="w-4 h-4" />}
              label="API Calls"
              value={formatCompactNumber(feature.call_count)}
            />
            <StatCard
              icon={<Clock className="w-4 h-4" />}
              label="Avg Latency"
              value={formatDuration(feature.avg_latency_ms)}
            />
            <StatCard
              icon={<BarChart2 className="w-4 h-4" />}
              label="Cost/Call"
              value={formatSmartCost(costPerCall)}
            />
          </div>
          
          {/* Trend Chart */}
          {trendData && trendData.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-3">
                Cost Trend
              </h4>
              <div className="h-36 bg-slate-50 rounded-lg p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis 
                      dataKey="date" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: '#94a3b8', fontSize: 10 }}
                      tickFormatter={(v) => formatSmartCost(v)}
                    />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-sm">
                              <p className="font-medium mb-1">{label}</p>
                              <p className="text-xs">
                                Cost: <span className="font-medium">{formatSmartCost(payload[0].value as number)}</span>
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="cost"
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4, strokeWidth: 2, fill: 'white' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          
          {/* Provider Breakdown */}
          {providerBreakdown && providerBreakdown.length > 0 && (
            <BreakdownList
              title="By Provider"
              data={providerBreakdown}
              totalCost={feature.total_cost}
              getName={(p) => p.provider}
              getCost={(p) => p.cost}
              getCalls={(p) => p.calls}
              onItemClick={onProviderClick ? (p) => onProviderClick(p.provider) : undefined}
            />
          )}
          
          {/* Model Breakdown */}
          {modelBreakdown && modelBreakdown.length > 0 && (
            <BreakdownList
              title="By Model"
              data={modelBreakdown}
              totalCost={feature.total_cost}
              getName={(m) => m.model}
              getCost={(m) => m.cost}
              getCalls={(m) => m.calls}
              onItemClick={onModelClick ? (m) => onModelClick(m.model) : undefined}
            />
          )}
          
          {/* No detail data placeholder */}
          {!trendData && !providerBreakdown && !modelBreakdown && (
            <div className="text-center py-8 text-slate-400">
              <Layers className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Detailed breakdown coming soon</p>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

