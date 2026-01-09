"use client";

import { useMemo, useState, useEffect } from "react";
import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import { formatSmartCost, formatAxisCost, formatPercentChange } from "@/lib/format";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

interface ChartDataPoint {
  date: string;
  value: number;
  [key: string]: string | number;
}

type ChartMode = "total" | "lines";

interface CostTrendChartProps {
  data: ChartDataPoint[];
  height?: number;
  className?: string;
  defaultMode?: ChartMode;
  showModeToggle?: boolean;
}

// ============================================================================
// SEMANTIC COLOR SYSTEM
// ============================================================================

// Global, consistent provider color palette - muted categorical
export const PROVIDER_COLORS: Record<string, string> = {
  openai: "#059669",       // emerald-600 (primary provider)
  anthropic: "#7c3aed",    // violet-600
  google: "#2563eb",       // blue-600
  cohere: "#4f46e5",       // indigo-600
  mistral: "#db2777",      // pink-600
  groq: "#ca8a04",         // yellow-600
  perplexity: "#0891b2",   // cyan-600
  together: "#ea580c",     // orange-600
  replicate: "#9333ea",    // purple-600
  huggingface: "#facc15",  // yellow-400
  azure: "#0284c7",        // sky-600
  aws: "#f97316",          // orange-500
  // Voice providers
  vapi: "#0d9488",         // teal-600
  elevenlabs: "#14b8a6",   // teal-500
  deepgram: "#0ea5e9",     // sky-500
  twilio: "#dc2626",       // red-600
  cartesia: "#8b5cf6",     // violet-500
  playht: "#ec4899",       // pink-500
  // Utility providers
  pinecone: "#f97316",     // orange-500
  stripe: "#6366f1",       // indigo-500
  voyage: "#84cc16",       // lime-500
};

const DEFAULT_COLOR = "#64748b"; // slate-500
const TOTAL_COLOR = "#0ea5e9";   // sky-500 (cost = neutral blue)

function getProviderColor(provider: string): string {
  return PROVIDER_COLORS[provider.toLowerCase()] || DEFAULT_COLOR;
}

// ============================================================================
// CHART MODE TOGGLE
// ============================================================================

interface ChartModeToggleProps {
  mode: ChartMode;
  onChange: (mode: ChartMode) => void;
  disabled?: boolean;
}

function ChartModeToggle({ mode, onChange, disabled }: ChartModeToggleProps) {
  const options: { value: ChartMode; label: string }[] = [
    { value: "total", label: "Total" },
    { value: "lines", label: "By Provider" },
  ];

  return (
    <div className="flex items-center bg-slate-100 rounded-lg p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          disabled={disabled}
          className={cn(
            "px-3 py-1 text-xs font-medium rounded-md transition-all",
            mode === option.value
              ? "bg-white text-slate-900 shadow-sm"
              : "text-slate-500 hover:text-slate-700",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  mode: ChartMode;
  prevValue: number;
}

function CustomTooltip({ active, payload, label, mode, prevValue }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;

  const total = payload.reduce((sum, p) => sum + (Number(p.value) || 0), 0);
  const dayChange = prevValue > 0 ? formatPercentChange(total, prevValue) : null;

  return (
    <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-sm min-w-[140px]">
      <div className="font-medium text-slate-300 mb-1 text-xs">{label}</div>
      <div className="flex items-center gap-2">
        <span className="text-lg font-bold">{formatSmartCost(total)}</span>
        {dayChange && dayChange.direction !== "flat" && (
          <span
            className={cn(
              "text-xs font-medium",
              dayChange.direction === "up" ? "text-rose-400" : "text-emerald-400"
            )}
          >
            {dayChange.direction === "up" ? "↑" : "↓"} {dayChange.formatted}
          </span>
        )}
      </div>

      {/* Provider breakdown for stacked/lines mode */}
      {mode !== "total" && payload.length > 1 && (
        <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
          {[...payload]
            .filter((p) => Number(p.value) > 0)
            .sort((a, b) => Number(b.value) - Number(a.value))
            .slice(0, 5)
            .map((p, i) => (
              <div
                key={i}
                className="flex items-center justify-between gap-4 text-xs"
              >
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: p.color }}
                  />
                  <span className="capitalize text-slate-300">{p.name}</span>
                </div>
                <span className="font-mono text-slate-100">
                  {formatSmartCost(Number(p.value))}
                </span>
              </div>
            ))}
          {payload.filter((p) => Number(p.value) > 0).length > 5 && (
            <div className="text-xs text-slate-500 text-center pt-1">
              +{payload.filter((p) => Number(p.value) > 0).length - 5} more
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// LEGEND
// ============================================================================

interface LegendProps {
  providers: string[];
  mode: ChartMode;
}

function Legend({ providers, mode }: LegendProps) {
  if (mode === "total" || providers.length <= 1) return null;

  // Show top 8 providers, rest as "+N more"
  const visibleProviders = providers.slice(0, 8);
  const hiddenCount = providers.length - 8;

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 px-1">
      {visibleProviders.map((provider) => (
        <div key={provider} className="flex items-center gap-1.5">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: getProviderColor(provider) }}
          />
          <span className="text-xs text-slate-500 capitalize">{provider}</span>
        </div>
      ))}
      {hiddenCount > 0 && (
        <span className="text-xs text-slate-400">+{hiddenCount} more</span>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function CostTrendChart({
  data,
  height = 200,
  className,
  defaultMode = "total",
  showModeToggle = true,
}: CostTrendChartProps) {
  const [mode, setMode] = useState<ChartMode>(defaultMode);

  // Extract providers and calculate stats
  const { providers, maxValue, avgValue, hasProviderData } = useMemo(() => {
    // Safety check for empty or invalid data
    if (!data || data.length === 0) {
      return { providers: [], maxValue: 0, avgValue: 0, hasProviderData: false };
    }
    
    const providerKeys = Array.from(
      new Set(
        data.flatMap((d) => {
          if (!d) return [];
          return Object.keys(d).filter(
            (k) =>
              k !== "date" &&
              k !== "value" &&
              typeof d[k] === "number" &&
              (d[k] as number) > 0
          );
        })
      )
    );

    // Sort providers by total cost
    const providerTotals = providerKeys.map((p) => ({
      provider: p,
      total: data.reduce((sum, d) => sum + (Number(d?.[p]) || 0), 0),
    }));
    providerTotals.sort((a, b) => b.total - a.total);
    const sortedProviders = providerTotals.map((p) => p.provider);

    const values = data.map((d) => d?.value ?? 0).filter((v) => v > 0);
    const max = values.length > 0 ? Math.max(...values) : 0;
    const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;

    return {
      providers: sortedProviders,
      maxValue: max,
      avgValue: avg,
      hasProviderData: sortedProviders.length > 0,
    };
  }, [data]);

  // Calculate Y-axis domain with padding
  const yAxisDomain = useMemo(() => {
    if (maxValue === 0) return [0, 0.001];
    const padding = maxValue * 0.1;
    return [0, maxValue + padding];
  }, [maxValue]);

  // Calculate trend change
  const trendChange = useMemo(() => {
    if (!data || data.length === 0) return null;
    const nonZeroData = data.filter((d) => d && typeof d.value === 'number' && d.value > 0);
    if (nonZeroData.length < 2) return null;
    const first = nonZeroData[0]?.value ?? 0;
    const last = nonZeroData[nonZeroData.length - 1]?.value ?? 0;
    if (first === 0) return null;
    return formatPercentChange(last, first);
  }, [data]);

  // Get previous value for tooltip delta
  const getPrevValue = (label: string) => {
    if (!data || data.length === 0) return 0;
    const idx = data.findIndex((d) => d?.date === label);
    return idx > 0 ? (data[idx - 1]?.value ?? 0) : 0;
  };

  // Empty state
  if (data.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-slate-50 rounded-lg",
          className
        )}
        style={{ height }}
      >
        <p className="text-sm text-slate-400">No data available</p>
      </div>
    );
  }
  
  // Single data point - show a clear message
  if (data.length === 1) {
    const point = data[0] || { date: '', value: 0 };
    return (
      <div className={cn("relative", className)}>
        <div className="flex items-center justify-between mb-3">
          {showModeToggle && (
            <ChartModeToggle mode={mode} onChange={setMode} disabled={true} />
          )}
        </div>
        <div 
          className="flex flex-col items-center justify-center bg-slate-50 rounded-lg"
          style={{ height }}
        >
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-700 mb-1">
              {formatSmartCost(point.value)}
            </div>
            <div className="text-sm text-slate-500">{point.date}</div>
            <p className="text-xs text-slate-400 mt-3">
              More data points needed to show trends
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Disable stacked/lines mode if no provider data
  const effectiveMode = !hasProviderData && mode !== "total" ? "total" : mode;
  
  // Normalize data for stacked/lines charts - ensure all data points have all provider keys
  const normalizedData = useMemo(() => {
    // Safety check for empty or invalid data
    if (!data || data.length === 0) return [];
    if (effectiveMode === "total" || providers.length === 0) return data;
    
    const normalized = data.map(d => {
      if (!d) return { date: '', value: 0 }; // Safety for undefined items
      const normalizedItem: ChartDataPoint = { 
        date: d.date || '', 
        value: typeof d.value === 'number' ? d.value : 0 
      };
      // Ensure each provider key exists (default to 0 if missing)
      providers.forEach(provider => {
        normalizedItem[provider] = typeof d[provider] === 'number' ? d[provider] : 0;
      });
      return normalizedItem;
    });
    
    // Final safety check - ensure all items have valid structure
    return normalized.filter(d => d && d.date && typeof d.value === 'number');
  }, [data, providers, effectiveMode]);
  
  // Additional guard: don't render lines if no valid normalized data
  const canRenderLines = effectiveMode === "lines" && normalizedData.length > 0 && providers.length > 0;
  
  // Auto-fallback to total mode if user selects lines but data isn't available
  useEffect(() => {
    if (mode === "lines" && !hasProviderData) {
      setMode("total");
    }
  }, [mode, hasProviderData]);

  return (
    <div className={cn("relative", className)}>
      {/* Header with mode toggle and trend indicator */}
      <div className="flex items-center justify-between mb-3">
        {showModeToggle && (
          <ChartModeToggle
            mode={effectiveMode}
            onChange={setMode}
            disabled={!hasProviderData}
          />
        )}
        {!showModeToggle && <div />}

        {trendChange && trendChange.direction !== "flat" && (
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium",
              trendChange.direction === "up"
                ? "bg-rose-50 text-rose-600"
                : "bg-emerald-50 text-emerald-600"
            )}
          >
            {trendChange.direction === "up" ? "↑" : "↓"}
            {trendChange.formatted} vs start
          </span>
        )}
      </div>

      {/* Chart */}
      {effectiveMode === "lines" && !canRenderLines ? (
        <div 
          className="flex items-center justify-center bg-slate-50 rounded-lg"
          style={{ height }}
        >
          <p className="text-sm text-slate-400">
            Provider breakdown data not available. Switch to "Total" view.
          </p>
        </div>
      ) : (
      <ResponsiveContainer width="100%" height={height}>
        {/* Line Chart (Total or By Provider) */}
        <LineChart data={effectiveMode === "lines" ? normalizedData : data} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="totalLineGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor={TOTAL_COLOR} stopOpacity={0.8} />
              <stop offset="100%" stopColor="#0284c7" stopOpacity={1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            dy={8}
            minTickGap={60}
            interval="preserveStartEnd"
            allowDuplicatedCategory={false}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickFormatter={formatAxisCost}
            domain={yAxisDomain}
            width={55}
          />
          {avgValue > 0 && effectiveMode === "total" && (
            <ReferenceLine
              y={avgValue}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              strokeOpacity={0.5}
              label={{
                value: `avg`,
                position: "right",
                fill: "#94a3b8",
                fontSize: 10,
              }}
            />
          )}
          <Tooltip
            content={({ active, payload, label }) => (
              <CustomTooltip
                active={active}
                payload={payload as CustomTooltipProps["payload"]}
                label={String(label ?? "")}
                mode={effectiveMode}
                prevValue={getPrevValue(String(label ?? ""))}
              />
            )}
          />
          {canRenderLines ? (
            // Multiple lines for each provider
            providers.map((provider) => (
              <Line
                key={provider}
                type="monotone"
                dataKey={provider}
                stroke={getProviderColor(provider)}
                strokeWidth={2}
                dot={{ r: 3, fill: getProviderColor(provider), strokeWidth: 0 }}
                activeDot={{ r: 5, strokeWidth: 2, fill: "white" }}
                connectNulls
              />
            ))
          ) : (
            // Single total line
            <Line
              type="monotone"
              dataKey="value"
              stroke="url(#totalLineGrad)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{
                r: 5,
                strokeWidth: 2,
                fill: "white",
                stroke: TOTAL_COLOR,
              }}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
      )}

      {/* Legend */}
      <Legend providers={providers} mode={effectiveMode} />
    </div>
  );
}
