"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Phone, Clock, DollarSign, TrendingUp, Mic, Volume2, MessageSquare, Radio, ArrowRight, Calculator, Zap } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  fetchVoiceCalls,
  fetchVoiceProviderStats,
  fetchVoiceSegmentStats,
  fetchVoiceCostPerMinute,
  fetchVoiceForecast,
  type VoiceCall,
  type VoiceProviderStats,
  type VoiceSegmentStats,
  type VoiceCostPerMinute,
  type VoiceForecast,
} from "@/lib/api";
import { Suspense } from "react";

// Segment colors for consistent visualization
const SEGMENT_COLORS: { [key: string]: string } = {
  stt: "#3b82f6",      // blue
  llm: "#8b5cf6",      // purple
  tts: "#10b981",      // green
  telephony: "#f59e0b", // amber
  unknown: "#6b7280",   // gray
};

const SEGMENT_ICONS: { [key: string]: any } = {
  stt: Mic,
  llm: MessageSquare,
  tts: Volume2,
  telephony: Phone,
};

// Provider pricing for "What If" calculator
const PROVIDER_PRICING: { [key: string]: { name: string; perMinute: number; description: string } } = {
  vapi: { name: "Vapi", perMinute: 0.05, description: "All-in-one platform" },
  retell: { name: "Retell", perMinute: 0.07, description: "Voice agent platform" },
  bland: { name: "Bland AI", perMinute: 0.09, description: "Enterprise voice" },
  diy_cheap: { name: "DIY (Budget)", perMinute: 0.02, description: "Deepgram + GPT-4o-mini + PlayHT" },
  diy_premium: { name: "DIY (Premium)", perMinute: 0.08, description: "Whisper + GPT-4o + ElevenLabs" },
  openai_realtime: { name: "OpenAI Realtime", perMinute: 0.30, description: "GPT-4o Realtime API" },
};

// Timeline visualization component
function CallTimeline({ call }: { call: VoiceCall }) {
  const segments = call.segments || {};
  const segmentOrder = ['stt', 'llm', 'tts', 'telephony'];
  const orderedSegments = segmentOrder
    .filter(type => segments[type])
    .map(type => ({ type, ...segments[type] }));
  
  const totalLatency = orderedSegments.reduce((sum, seg) => sum + (seg.latency_ms || 0), 0);
  
  if (orderedSegments.length === 0) return null;
  
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
        <Zap className="w-3 h-3" /> Pipeline Flow ({totalLatency.toFixed(0)}ms total)
      </div>
      <div className="flex items-center gap-1">
        {orderedSegments.map((segment, idx) => {
          const Icon = SEGMENT_ICONS[segment.type] || Radio;
          const widthPercent = totalLatency > 0 ? (segment.latency_ms / totalLatency) * 100 : 25;
          
          return (
            <div key={segment.type} className="flex items-center">
              <div
                className="relative group cursor-pointer"
                style={{ minWidth: `${Math.max(widthPercent, 15)}%` }}
              >
                <div
                  className="flex items-center justify-center gap-1 px-2 py-1.5 rounded-md text-xs font-medium"
                  style={{
                    backgroundColor: SEGMENT_COLORS[segment.type] || SEGMENT_COLORS.unknown,
                    color: 'white',
                  }}
                >
                  <Icon className="w-3 h-3" />
                  <span>{segment.type.toUpperCase()}</span>
                </div>
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {segment.latency_ms?.toFixed(0) || 0}ms • ${segment.cost?.toFixed(4) || '0.0000'}
                </div>
              </div>
              {idx < orderedSegments.length - 1 && (
                <ArrowRight className="w-3 h-3 text-gray-300 mx-1 flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Provider "What If" Calculator
function ProviderCalculator({ totalMinutes, currentCost }: { totalMinutes: number; currentCost: number }) {
  const [selectedProviders, setSelectedProviders] = useState<string[]>(['vapi', 'retell', 'diy_cheap']);
  
  const comparisons = Object.entries(PROVIDER_PRICING).map(([key, provider]) => {
    const projectedCost = totalMinutes * provider.perMinute;
    const savings = currentCost - projectedCost;
    const savingsPercent = currentCost > 0 ? (savings / currentCost) * 100 : 0;
    
    return {
      key,
      ...provider,
      projectedCost,
      savings,
      savingsPercent,
    };
  }).sort((a, b) => a.projectedCost - b.projectedCost);
  
  if (totalMinutes === 0) {
    return (
      <div className="py-4 text-center text-gray-400">
        Track voice calls to see provider cost comparisons
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      <div className="text-sm text-gray-500 mb-3">
        Based on <span className="font-medium">{totalMinutes.toFixed(1)} minutes</span> of voice usage:
      </div>
      {comparisons.map((provider) => (
        <div
          key={provider.key}
          className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
            provider.savings > 0 ? 'border-green-200 bg-green-50' :
            provider.savings < 0 ? 'border-red-100 bg-red-50' :
            'border-gray-200 bg-gray-50'
          }`}
        >
          <div>
            <div className="font-medium text-gray-900">{provider.name}</div>
            <div className="text-xs text-gray-500">{provider.description}</div>
            <div className="text-xs text-gray-400 mt-1">${provider.perMinute.toFixed(3)}/min</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold">${provider.projectedCost.toFixed(2)}</div>
            {provider.savings !== 0 && (
              <div className={`text-xs font-medium ${provider.savings > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {provider.savings > 0 ? '↓' : '↑'} ${Math.abs(provider.savings).toFixed(2)} ({Math.abs(provider.savingsPercent).toFixed(0)}%)
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function VoiceAgentsContent() {
  const { getToken } = useAuth();
  const [calls, setCalls] = useState<VoiceCall[]>([]);
  const [providerStats, setProviderStats] = useState<VoiceProviderStats[]>([]);
  const [segmentStats, setSegmentStats] = useState<VoiceSegmentStats[]>([]);
  const [costPerMinute, setCostPerMinute] = useState<VoiceCostPerMinute | null>(null);
  const [forecast, setForecast] = useState<VoiceForecast | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeWindow, setTimeWindow] = useState<string>("24");

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const token = await getToken();
        if (!token) {
          console.error("No Clerk token available");
          return;
        }

        const hours = parseInt(timeWindow);

        // Fetch all voice stats in parallel
        const [callsData, providersData, segmentsData, cpmData, forecastData] = await Promise.all([
          fetchVoiceCalls(hours, 50, token).catch(() => []),
          fetchVoiceProviderStats(hours, token).catch(() => []),
          fetchVoiceSegmentStats(hours, token).catch(() => []),
          fetchVoiceCostPerMinute(hours, token).catch(() => null),
          fetchVoiceForecast(token).catch(() => null),
        ]);

        setCalls(callsData);
        setProviderStats(providersData);
        setSegmentStats(segmentsData);
        setCostPerMinute(cpmData);
        setForecast(forecastData);
      } catch (error) {
        console.error("Failed to load voice stats:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [getToken, timeWindow]);

  // Calculate totals
  const totalCost = costPerMinute?.total_cost || 0;
  const totalCalls = costPerMinute?.total_calls || 0;
  const totalMinutes = costPerMinute?.total_duration_minutes || 0;
  const avgCostPerMinute = costPerMinute?.cost_per_minute || 0;

  // Prepare segment pie chart data
  const segmentPieData = segmentStats.map(s => ({
    name: s.segment_type.toUpperCase(),
    value: s.total_cost,
    percentage: s.percentage,
    color: SEGMENT_COLORS[s.segment_type] || SEGMENT_COLORS.unknown,
  }));

  // Prepare provider comparison chart data
  const providerChartData = providerStats.slice(0, 10).map(p => ({
    provider: p.provider,
    cost: p.total_cost,
    cost_per_minute: p.cost_per_minute,
    calls: p.call_count,
  }));

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        {/* Header with Time Filter */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Voice Agents</h1>
            <p className="text-sm text-gray-500">Track STT + LLM + TTS costs across your voice pipelines</p>
          </div>
          <Select value={timeWindow} onValueChange={setTimeWindow}>
            <SelectTrigger className="w-40 border-gray-300">
              <SelectValue placeholder="Time window" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last Hour</SelectItem>
              <SelectItem value="24">Last 24 Hours</SelectItem>
              <SelectItem value="168">Last 7 Days</SelectItem>
              <SelectItem value="720">Last 30 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Key Metrics */}
        <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex-1 min-w-[140px]">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-2">
                <DollarSign className="w-4 h-4" />
                Voice Spend
              </div>
              <div className="text-3xl font-bold text-gray-900">${totalCost.toFixed(4)}</div>
              <p className="text-xs text-gray-500 mt-1">
                {totalCalls} calls
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[140px]">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-2">
                <Clock className="w-4 h-4" />
                Total Duration
              </div>
              <div className="text-3xl font-bold text-gray-900">{totalMinutes.toFixed(1)} min</div>
              <p className="text-xs text-gray-500 mt-1">
                {(costPerMinute?.avg_call_duration_seconds || 0).toFixed(0)}s avg/call
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[140px]">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-2">
                <TrendingUp className="w-4 h-4" />
                Cost/Minute
              </div>
              <div className="text-3xl font-bold text-gray-900">${avgCostPerMinute.toFixed(4)}</div>
              <p className="text-xs text-gray-500 mt-1">
                ${(costPerMinute?.cost_per_call || 0).toFixed(4)}/call
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[140px]">
              <div className="flex items-center gap-2 text-sm font-medium text-gray-600 mb-2">
                <Radio className="w-4 h-4" />
                Monthly Forecast
              </div>
              <div className="text-3xl font-bold text-indigo-600">
                ${forecast?.monthly_projection.cost.toFixed(2) || "—"}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                ~{forecast?.monthly_projection.calls || 0} calls projected
              </p>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost by Segment (Pie Chart) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Cost by Segment</CardTitle>
              <CardDescription>Where your voice costs go (STT, LLM, TTS, Telephony)</CardDescription>
            </CardHeader>
            <CardContent>
              {segmentPieData.length > 0 ? (
                <div className="flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                      <Pie
                        data={segmentPieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        label={({ name, percentage }) => `${name} ${percentage.toFixed(0)}%`}
                      >
                        {segmentPieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-[280px] flex items-center justify-center text-gray-400">
                  No voice segment data yet
                </div>
              )}
            </CardContent>
          </Card>

          {/* Latency Breakdown (Bar Chart) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                Latency by Segment
              </CardTitle>
              <CardDescription>Where time goes in your voice pipeline</CardDescription>
            </CardHeader>
            <CardContent>
              {segmentStats.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart 
                    data={segmentStats.map(s => ({
                      segment: s.segment_type.toUpperCase(),
                      latency: s.avg_latency_ms,
                      color: SEGMENT_COLORS[s.segment_type] || SEGMENT_COLORS.unknown,
                    }))}
                    layout="vertical"
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={(v) => `${v.toFixed(0)}ms`} />
                    <YAxis dataKey="segment" type="category" width={80} />
                    <Tooltip
                      formatter={(value: number) => [`${value.toFixed(0)}ms`, "Avg Latency"]}
                    />
                    <Bar dataKey="latency" name="latency">
                      {segmentStats.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={SEGMENT_COLORS[entry.segment_type] || SEGMENT_COLORS.unknown} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[280px] flex items-center justify-center text-gray-400">
                  No latency data yet
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Provider Comparison & Calculator Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Actual Provider Usage (Bar Chart) */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Your Provider Usage</CardTitle>
              <CardDescription>Costs across providers you're currently using</CardDescription>
            </CardHeader>
            <CardContent>
              {providerChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={providerChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(3)}`} />
                    <YAxis dataKey="provider" type="category" width={80} />
                    <Tooltip
                      formatter={(value: number, name: string) => [
                        name === "cost" ? `$${value.toFixed(4)}` : `$${value.toFixed(4)}/min`,
                        name === "cost" ? "Total Cost" : "Cost/Min"
                      ]}
                    />
                    <Bar dataKey="cost" fill="#6366f1" name="cost" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[280px] flex items-center justify-center text-gray-400">
                  No provider data yet
                </div>
              )}
            </CardContent>
          </Card>

          {/* What-If Provider Calculator */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Calculator className="w-4 h-4 text-indigo-500" />
                Provider Cost Calculator
              </CardTitle>
              <CardDescription>What if you switched providers?</CardDescription>
            </CardHeader>
            <CardContent>
              <ProviderCalculator 
                totalMinutes={totalMinutes} 
                currentCost={totalCost} 
              />
            </CardContent>
          </Card>
        </div>

        {/* Segment Details Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Segment Breakdown</CardTitle>
            <CardDescription>Detailed costs and latency by pipeline segment</CardDescription>
          </CardHeader>
          <CardContent>
            {segmentStats.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 font-medium text-gray-600">Segment</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Cost</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Duration</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Events</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">Avg Latency</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">$/min</th>
                      <th className="text-right py-3 px-4 font-medium text-gray-600">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {segmentStats.map((segment) => {
                      const Icon = SEGMENT_ICONS[segment.segment_type] || Radio;
                      return (
                        <tr key={segment.segment_type} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <div
                                className="w-8 h-8 rounded-lg flex items-center justify-center"
                                style={{ backgroundColor: `${SEGMENT_COLORS[segment.segment_type] || SEGMENT_COLORS.unknown}20` }}
                              >
                                <Icon
                                  className="w-4 h-4"
                                  style={{ color: SEGMENT_COLORS[segment.segment_type] || SEGMENT_COLORS.unknown }}
                                />
                              </div>
                              <span className="font-medium">{segment.segment_type.toUpperCase()}</span>
                            </div>
                          </td>
                          <td className="text-right py-3 px-4 font-mono">${segment.total_cost.toFixed(4)}</td>
                          <td className="text-right py-3 px-4">{segment.total_duration_seconds.toFixed(1)}s</td>
                          <td className="text-right py-3 px-4">{segment.event_count}</td>
                          <td className="text-right py-3 px-4">{segment.avg_latency_ms.toFixed(0)}ms</td>
                          <td className="text-right py-3 px-4 font-mono">${segment.cost_per_minute.toFixed(4)}</td>
                          <td className="text-right py-3 px-4">
                            <Badge variant="secondary">{segment.percentage.toFixed(1)}%</Badge>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400">
                No segment data yet. Voice calls will appear here once tracked.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Calls */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Voice Calls</CardTitle>
            <CardDescription>Per-call cost breakdown with segment details</CardDescription>
          </CardHeader>
          <CardContent>
            {calls.length > 0 ? (
              <div className="space-y-3">
                {calls.slice(0, 10).map((call) => (
                  <div
                    key={call.voice_call_id}
                    className="p-4 rounded-lg border border-gray-200 hover:border-indigo-200 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <Phone className="w-4 h-4 text-gray-400" />
                          <span className="font-mono text-sm text-gray-600">
                            {call.voice_call_id.substring(0, 8)}...
                          </span>
                          {call.customer_id && (
                            <Badge variant="outline" className="text-xs">
                              {call.customer_id}
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {call.started_at ? new Date(call.started_at).toLocaleString() : "Unknown time"}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900">
                          ${call.total_cost.toFixed(4)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {call.total_duration_seconds.toFixed(1)}s • ${call.cost_per_minute.toFixed(4)}/min
                        </div>
                      </div>
                    </div>
                    {/* Segment breakdown badges */}
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(call.segments || {}).map(([type, data]) => {
                        const Icon = SEGMENT_ICONS[type] || Radio;
                        return (
                          <div
                            key={type}
                            className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs"
                            style={{
                              backgroundColor: `${SEGMENT_COLORS[type] || SEGMENT_COLORS.unknown}15`,
                              color: SEGMENT_COLORS[type] || SEGMENT_COLORS.unknown,
                            }}
                          >
                            <Icon className="w-3 h-3" />
                            <span className="font-medium">{type.toUpperCase()}</span>
                            <span className="opacity-70">${data.cost?.toFixed(4) || '0.0000'}</span>
                          </div>
                        );
                      })}
                    </div>
                    {/* Timeline visualization */}
                    <CallTimeline call={call} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400">
                No voice calls yet. Use <code className="bg-gray-100 px-1 rounded">voice_call()</code> to track calls.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Forecast Card */}
        {forecast && (
          <Card className="border-indigo-200 bg-gradient-to-r from-indigo-50 to-purple-50">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                Monthly Forecast
              </CardTitle>
              <CardDescription>{forecast.note}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Last 7 Days</div>
                  <div className="text-2xl font-bold">${forecast.last_7_days.total_cost.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">
                    {forecast.last_7_days.total_calls} calls • {forecast.last_7_days.total_duration_minutes.toFixed(0)} min
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Daily Average</div>
                  <div className="text-2xl font-bold">${forecast.daily_average.cost.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">
                    {forecast.daily_average.calls.toFixed(1)} calls/day
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Projected This Month</div>
                  <div className="text-2xl font-bold text-indigo-600">${forecast.monthly_projection.cost.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">
                    ~{forecast.monthly_projection.calls} calls • ~{forecast.monthly_projection.duration_minutes.toFixed(0)} min
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedLayout>
  );
}

export default function VoiceAgentsPage() {
  return (
    <Suspense fallback={
      <ProtectedLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </ProtectedLayout>
    }>
      <VoiceAgentsContent />
    </Suspense>
  );
}

