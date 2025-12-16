"use client";

import { useMemo } from "react";
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

interface ChartDataPoint {
  date: string;
  value: number;
  [key: string]: string | number;
}

interface CostTrendChartProps {
  data: ChartDataPoint[];
  height?: number;
  className?: string;
}

// Provider color mapping - consistent with rest of app
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10b981",      // emerald-500
  anthropic: "#8b5cf6",   // violet-500
  cohere: "#6366f1",      // indigo-500
  google: "#3b82f6",      // blue-500
  mistral: "#ec4899",     // pink-500
  pinecone: "#f97316",    // orange-500
  stripe: "#a855f7",      // purple-500
  vapi: "#06b6d4",        // cyan-500
  elevenlabs: "#14b8a6",  // teal-500
  twilio: "#f59e0b",      // amber-500
  voyage: "#84cc16",      // lime-500
};

const DEFAULT_COLOR = "#10b981";

export function CostTrendChart({
  data,
  height = 220,
  className,
}: CostTrendChartProps) {
  // Calculate stats for the chart
  const { maxValue, avgValue, providers } = useMemo(() => {
    const values = data.map(d => d.value).filter(v => v > 0);
    const max = Math.max(...values, 0);
    const avg = values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
    
    // Get unique providers from data
    const providerKeys = Array.from(
      new Set(
        data.flatMap(d => 
          Object.keys(d).filter(k => 
            k !== 'date' && k !== 'value' && typeof d[k] === 'number'
          )
        )
      )
    );
    
    return { maxValue: max, avgValue: avg, providers: providerKeys };
  }, [data]);

  // Calculate Y-axis domain with some padding
  const yAxisDomain = useMemo(() => {
    if (maxValue === 0) return [0, 0.001];
    const padding = maxValue * 0.1;
    return [0, maxValue + padding];
  }, [maxValue]);

  // Calculate period-over-period change (last point vs first non-zero)
  const trendChange = useMemo(() => {
    const nonZeroData = data.filter(d => d.value > 0);
    if (nonZeroData.length < 2) return null;
    const first = nonZeroData[0].value;
    const last = nonZeroData[nonZeroData.length - 1].value;
    return formatPercentChange(last, first);
  }, [data]);

  if (data.length === 0) {
    return (
      <div className={cn("flex items-center justify-center bg-slate-50 rounded-lg", className)} style={{ height }}>
        <p className="text-sm text-slate-400">No data available</p>
      </div>
    );
  }

  return (
    <div className={cn("relative", className)}>
      {/* Trend indicator badge */}
      {trendChange && trendChange.direction !== 'flat' && (
        <div className="absolute top-0 right-0 z-10">
          <span className={cn(
            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium",
            trendChange.direction === 'up' 
              ? "bg-rose-50 text-rose-600" 
              : "bg-emerald-50 text-emerald-600"
          )}>
            {trendChange.direction === 'up' ? '↑' : '↓'}
            {trendChange.formatted} vs start
          </span>
        </div>
      )}
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 8, right: 8, left: -10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="lineGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="100%" stopColor="#059669" stopOpacity={1}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid
            strokeDasharray="3 3"
            vertical={false}
            stroke="#f1f5f9"
          />
          
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            dy={8}
            minTickGap={50}
            interval="preserveStartEnd"
          />
          
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            tickFormatter={formatAxisCost}
            domain={yAxisDomain}
            width={55}
          />
          
          {/* Average reference line */}
          {avgValue > 0 && (
            <ReferenceLine 
              y={avgValue} 
              stroke="#94a3b8" 
              strokeDasharray="4 4"
              strokeOpacity={0.5}
            />
          )}
          
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const total = payload.reduce((sum, p) => sum + (Number(p.value) || 0), 0);
                const prevIndex = data.findIndex(d => d.date === label) - 1;
                const prevValue = prevIndex >= 0 ? data[prevIndex].value : 0;
                const dayChange = prevValue > 0 ? formatPercentChange(total, prevValue) : null;
                
                return (
                  <div className="bg-slate-900 text-white px-3 py-2 rounded-lg shadow-xl text-sm">
                    <div className="font-medium mb-1">{label}</div>
                    <div className="flex items-center gap-3">
                      <span className="text-lg font-bold">{formatSmartCost(total)}</span>
                      {dayChange && dayChange.direction !== 'flat' && (
                        <span className={cn(
                          "text-xs",
                          dayChange.direction === 'up' ? "text-rose-400" : "text-emerald-400"
                        )}>
                          {dayChange.formatted}
                        </span>
                      )}
                    </div>
                    {/* Provider breakdown if multiple */}
                    {payload.length > 1 && (
                      <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
                        {[...payload].reverse().map((p, i) => (
                          <div key={i} className="flex items-center justify-between gap-4 text-xs">
                            <div className="flex items-center gap-1.5">
                              <div 
                                className="w-2 h-2 rounded-full" 
                                style={{ backgroundColor: p.color }}
                              />
                              <span className="capitalize text-slate-300">{p.name}</span>
                            </div>
                            <span className="font-medium">{formatSmartCost(Number(p.value))}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          
          {/* Render lines for each provider, or fallback to value */}
          {providers.length > 0 ? (
            providers.map((provider) => (
              <Line
                key={provider}
                type="monotone"
                dataKey={provider}
                stroke={PROVIDER_COLORS[provider] || DEFAULT_COLOR}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, fill: "white" }}
                connectNulls
              />
            ))
          ) : (
            <Line
              type="monotone"
              dataKey="value"
              stroke="url(#lineGradient)"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 2, fill: "white", stroke: "#10b981" }}
              connectNulls
            />
          )}
        </LineChart>
      </ResponsiveContainer>
      
      {/* Legend for providers */}
      {providers.length > 1 && (
        <div className="flex flex-wrap gap-4 mt-3 px-2">
          {providers.map((provider) => (
            <div key={provider} className="flex items-center gap-1.5">
              <div 
                className="w-2.5 h-2.5 rounded-full" 
                style={{ backgroundColor: PROVIDER_COLORS[provider] || DEFAULT_COLOR }}
              />
              <span className="text-xs text-slate-500 capitalize">{provider}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

