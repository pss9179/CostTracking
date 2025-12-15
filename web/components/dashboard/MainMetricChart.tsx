"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface MainMetricChartProps {
  data: Array<{
    date: string;
    value: number;
  }>;
  title: string;
  metric: string;
  metricValue: string;
  subtext?: string;
  providerStats?: Array<{
    provider: string;
    total_cost: number;
    percentage?: number;
  }>;
}

// Provider color mapping
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10b981",      // emerald-500
  anthropic: "#8b5cf6",   // violet-500
  cohere: "#6366f1",      // indigo-500
  google: "#3b82f6",      // blue-500
  mistral: "#ec4899",     // pink-500
  pinecone: "#f97316",    // orange-500
  stripe: "#a855f7",      // purple-500
  vapi: "#06b6d4",        // cyan-500
  elevenlabs: "#14b8a6", // teal-500
  twilio: "#f59e0b",     // amber-500
  voyage: "#84cc16",     // lime-500
};

export function MainMetricChart({
  data,
  title,
  metric,
  metricValue,
  subtext,
  providerStats = [],
}: MainMetricChartProps) {
  // Calculate max value for better Y-axis scaling
  const maxValue = Math.max(...data.map(d => d.value), 0);
  const yAxisDomain = maxValue > 0 ? [0, maxValue * 1.1] : [0, 0.01];

  // Get unique providers from the data
  const providers = Array.from(
    new Set(
      data.flatMap(d => 
        Object.keys(d).filter(k => k !== 'date' && k !== 'value' && typeof d[k as keyof typeof d] === 'number')
      )
    )
  );

  return (
    <Card className="border-0 shadow-none">
      <CardHeader className="px-0 pt-0 pb-2">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground mb-1">{title}</p>
            <h2 className="text-3xl font-bold tracking-tight">{metricValue}</h2>
          </div>
          <div className="flex items-center gap-2">
            {/* Placeholder for controls if needed */}
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-0 pl-0">
        <div className="w-full" style={{ height: 300 }}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart
              data={data}
              margin={{ top: 10, right: 0, left: -20, bottom: 0 }}
            >
              <defs>
                {providers.map((provider) => {
                  const color = PROVIDER_COLORS[provider] || "#64748b";
                  return (
                    <linearGradient key={provider} id={`color-${provider}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={color} stopOpacity={0.8}/>
                      <stop offset="95%" stopColor={color} stopOpacity={0.3}/>
                    </linearGradient>
                  );
                })}
                {/* Default gradient for fallback */}
                <linearGradient id="color-default" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.3}/>
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
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                dy={10}
                minTickGap={30}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "#94a3b8", fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(4)}`}
                domain={yAxisDomain}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    const total = payload.reduce((sum, p) => sum + (Number(p.value) || 0), 0);
                    return (
                      <div className="rounded-lg border bg-background p-3 shadow-lg">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center justify-between gap-4 pb-2 border-b">
                            <span className="text-xs font-medium text-muted-foreground">
                              {label}
                            </span>
                            <span className="text-sm font-bold">
                              ${total.toFixed(4)}
                            </span>
                          </div>
                          {[...payload].reverse().map((p, i) => (
                            <div key={i} className="flex items-center justify-between gap-4">
                              <div className="flex items-center gap-2">
                                <div 
                                  className="w-3 h-3 rounded-sm" 
                                  style={{ backgroundColor: p.color }}
                                />
                                <span className="text-xs capitalize font-medium">
                                  {p.name}
                                </span>
                              </div>
                              <span className="text-xs font-semibold">
                                ${Number(p.value).toFixed(4)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {/* Render an Area for each provider with stacking */}
              {providers.length > 0 ? (
                providers.map((provider) => (
                  <Area
                    key={provider}
                    type="monotone"
                    dataKey={provider}
                    stackId="1"
                    stroke={PROVIDER_COLORS[provider] || "#64748b"}
                    fill={`url(#color-${provider})`}
                    strokeWidth={2}
                    connectNulls
                    isAnimationActive={false}
                  />
                ))
              ) : (
                /* Fallback: render value if no provider breakdown available */
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#10b981"
                  fill="url(#color-default)"
                  strokeWidth={2}
                  connectNulls
                  isAnimationActive={false}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        </div>
        
        {/* Provider Legend */}
        {providerStats && providerStats.length > 0 && (
          <div className="mt-6 pt-4 border-t">
            <p className="text-xs text-muted-foreground mb-3 font-medium">Providers</p>
            <div className="flex flex-wrap gap-4">
              {providerStats.map((stat) => {
                const color = PROVIDER_COLORS[stat.provider.toLowerCase()] || "#64748b";
                return (
                  <div key={stat.provider} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-sm font-medium capitalize">
                      {stat.provider}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      ${stat.total_cost.toFixed(6)}
                    </span>
                    {stat.percentage !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        ({stat.percentage.toFixed(1)}%)
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
