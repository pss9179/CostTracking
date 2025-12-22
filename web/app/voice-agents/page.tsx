"use client";

import { useState, Suspense } from "react";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Phone, Clock, DollarSign, TrendingUp, Mic, Volume2, MessageSquare, Radio, ArrowRight, Calculator, Zap } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  type VoiceCall,
  type VoiceAlternativeCosts,
} from "@/lib/api";
import { useVoiceAgentsData } from "@/lib/hooks";

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

// Segment labels for alternative costs
const SEGMENT_LABELS: { [key: string]: string } = {
  stt: "Speech-to-Text",
  llm: "Language Model",
  tts: "Text-to-Speech",
};

// Timeline visualization component
function CallTimeline({ call }: { call: VoiceCall }) {
  const segments = call.segments || {};
  const segmentOrder = ['stt', 'llm', 'tts', 'telephony'];
  const orderedSegments = segmentOrder
    .filter(type => segments[type])
    .map(type => ({ type, ...segments[type] }));
  
  const totalLatency = orderedSegments.reduce((sum, seg) => sum + (seg.latency_ms || 0), 0);
  const totalCost = orderedSegments.reduce((sum, seg) => sum + (seg.cost || 0), 0);
  
  // Find bottleneck (segment with highest latency or cost)
  const latencyBottleneck = orderedSegments.length > 0 
    ? orderedSegments.reduce((max, seg) => (seg.latency_ms || 0) > (max.latency_ms || 0) ? seg : max)
    : null;
  const costBottleneck = orderedSegments.length > 0
    ? orderedSegments.reduce((max, seg) => (seg.cost || 0) > (max.cost || 0) ? seg : max)
    : null;
  
  if (orderedSegments.length === 0) return null;
  
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      {/* Pipeline Flow Header */}
      <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
        <Zap className="w-3 h-3" /> Pipeline Flow ({totalLatency.toFixed(0)}ms total)
      </div>
      
      {/* Visual Pipeline */}
      <div className="flex items-center gap-1 mb-3">
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
      
      {/* Waterfall Timeline (if latency data exists) */}
      {totalLatency > 0 && (
        <div className="space-y-1 mb-3">
          {orderedSegments.map((segment, idx) => {
            const startPercent = orderedSegments
              .slice(0, idx)
              .reduce((sum, s) => sum + ((s.latency_ms || 0) / totalLatency) * 100, 0);
            const widthPercent = ((segment.latency_ms || 0) / totalLatency) * 100;
            const isBottleneck = segment.type === latencyBottleneck?.type && widthPercent > 40;
            
            return (
              <div key={segment.type} className="flex items-center gap-2 text-xs">
                <div className="w-12 text-gray-500 uppercase font-medium">{segment.type}</div>
                <div className="flex-1 h-4 bg-gray-100 rounded relative overflow-hidden">
                  <div
                    className="absolute h-full rounded transition-all"
                    style={{
                      left: `${startPercent}%`,
                      width: `${Math.max(widthPercent, 2)}%`,
                      backgroundColor: SEGMENT_COLORS[segment.type] || SEGMENT_COLORS.unknown,
                    }}
                  />
                </div>
                <div className={`w-16 text-right ${isBottleneck ? 'text-red-600 font-bold' : 'text-gray-600'}`}>
                  {segment.latency_ms?.toFixed(0) || 0}ms
                  {isBottleneck && ' ⚠️'}
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      {/* Bottleneck Insights */}
      {(latencyBottleneck || costBottleneck) && (
        <div className="flex flex-wrap gap-2 text-xs">
          {latencyBottleneck && totalLatency > 0 && (latencyBottleneck.latency_ms || 0) / totalLatency > 0.4 && (
            <div className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full border border-amber-200">
              ⏱️ {latencyBottleneck.type.toUpperCase()} is {((latencyBottleneck.latency_ms || 0) / totalLatency * 100).toFixed(0)}% of latency
            </div>
          )}
          {costBottleneck && totalCost > 0 && (costBottleneck.cost || 0) / totalCost > 0.4 && (
            <div className="px-2 py-1 bg-rose-50 text-rose-700 rounded-full border border-rose-200">
              💰 {costBottleneck.type.toUpperCase()} is {((costBottleneck.cost || 0) / totalCost * 100).toFixed(0)}% of cost
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Provider "What If" Calculator - Uses actual usage metrics
function ProviderCalculator({ altCosts }: { altCosts: VoiceAlternativeCosts | null }) {
  const [selectedSegment, setSelectedSegment] = useState<'stt' | 'llm' | 'tts'>('tts');
  
  if (!altCosts || !altCosts.usage) {
    return (
      <div className="py-4 text-center text-gray-400">
        Track voice calls to see provider cost comparisons
      </div>
    );
  }
  
  const { usage, actual_costs, alternatives, best_diy_stack } = altCosts;
  
  // Show usage metrics
  const usageDisplay = {
    stt: `${usage.stt_minutes.toFixed(1)} minutes`,
    llm: `${(usage.llm_input_tokens + usage.llm_output_tokens).toLocaleString()} tokens`,
    tts: `${usage.tts_characters.toLocaleString()} characters`,
  };
  
  const currentAlternatives = alternatives[selectedSegment] || [];
  const currentActual = actual_costs[selectedSegment] || 0;
  
  return (
    <div className="space-y-4">
      {/* Best DIY Stack Summary */}
      {best_diy_stack.total_savings > 0 && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="text-sm font-medium text-green-800">💡 Best DIY Stack</div>
          <div className="text-xs text-green-700 mt-1">
            {best_diy_stack.stt} + {best_diy_stack.llm} + {best_diy_stack.tts}
          </div>
          <div className="text-lg font-bold text-green-600 mt-1">
            Save ${best_diy_stack.total_savings.toFixed(2)} ({best_diy_stack.savings_percent.toFixed(0)}%)
          </div>
        </div>
      )}
      
      {/* Segment Selector */}
      <div className="flex gap-2">
        {(['stt', 'llm', 'tts'] as const).map((seg) => (
          <button
            key={seg}
            onClick={() => setSelectedSegment(seg)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              selectedSegment === seg
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {SEGMENT_LABELS[seg]}
          </button>
        ))}
      </div>
      
      {/* Usage info */}
      <div className="text-sm text-gray-500">
        Based on <span className="font-medium">{usageDisplay[selectedSegment]}</span> of {SEGMENT_LABELS[selectedSegment]}:
      </div>
      
      {/* Alternatives List */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {currentAlternatives.map((provider) => (
          <div
            key={provider.provider}
            className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
              provider.savings > 0 ? 'border-green-200 bg-green-50' :
              provider.savings < 0 ? 'border-red-100 bg-red-50' :
              'border-gray-200 bg-gray-50'
            }`}
          >
            <div>
              <div className="font-medium text-gray-900">{provider.name}</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold">${provider.projected_cost.toFixed(4)}</div>
              {provider.savings !== 0 && (
                <div className={`text-xs font-medium ${provider.savings > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {provider.savings > 0 ? '↓' : '↑'} ${Math.abs(provider.savings).toFixed(4)} ({Math.abs(provider.savings_percent).toFixed(0)}%)
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Current Cost */}
      <div className="text-xs text-gray-400 border-t pt-2">
        Your current {SEGMENT_LABELS[selectedSegment]} cost: ${currentActual.toFixed(4)}
      </div>
    </div>
  );
}

function VoiceAgentsContent() {
  const [timeWindow, setTimeWindow] = useState<string>("24");
  const hours = parseInt(timeWindow);
  
  // Use cached hook - data persists across navigation
  const {
    calls,
    providerStats,
    segmentStats,
    costPerMinute,
    forecast,
    alternativeCosts,
    platformComparison,
    loading,
  } = useVoiceAgentsData(hours);

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
                        label={({ name, percent }: any) => `${name || ''} ${((percent || 0) * 100).toFixed(0)}%`}
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

        {/* Pipeline Insights - Bottleneck Detection */}
        <Card className="border-2 border-dashed border-amber-200 bg-amber-50/30">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Pipeline Insights
            </CardTitle>
            <CardDescription>Bottleneck detection and optimization opportunities</CardDescription>
          </CardHeader>
          <CardContent>
            {segmentStats.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Cost Bottleneck */}
                {(() => {
                  const totalCost = segmentStats.reduce((sum, s) => sum + s.total_cost, 0);
                  const costBottleneck = segmentStats.reduce((max, s) => s.total_cost > max.total_cost ? s : max);
                  const costPercent = totalCost > 0 ? (costBottleneck.total_cost / totalCost) * 100 : 0;
                  
                  return (
                    <div className="p-4 bg-white rounded-lg border">
                      <div className="text-xs text-gray-500 uppercase mb-1">💰 Cost Bottleneck</div>
                      <div className="text-xl font-bold" style={{ color: SEGMENT_COLORS[costBottleneck.segment_type] }}>
                        {costBottleneck.segment_type.toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {costPercent.toFixed(0)}% of total cost (${costBottleneck.total_cost.toFixed(4)})
                      </div>
                      {costPercent > 50 && (
                        <div className="mt-2 text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded">
                          💡 Consider switching {costBottleneck.segment_type.toUpperCase()} provider
                        </div>
                      )}
                    </div>
                  );
                })()}
                
                {/* Latency Bottleneck */}
                {(() => {
                  const totalLatency = segmentStats.reduce((sum, s) => sum + s.avg_latency_ms, 0);
                  const latencyBottleneck = segmentStats.reduce((max, s) => s.avg_latency_ms > max.avg_latency_ms ? s : max);
                  const latencyPercent = totalLatency > 0 ? (latencyBottleneck.avg_latency_ms / totalLatency) * 100 : 0;
                  
                  return (
                    <div className="p-4 bg-white rounded-lg border">
                      <div className="text-xs text-gray-500 uppercase mb-1">⏱️ Latency Bottleneck</div>
                      <div className="text-xl font-bold" style={{ color: SEGMENT_COLORS[latencyBottleneck.segment_type] }}>
                        {latencyBottleneck.segment_type.toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {latencyPercent.toFixed(0)}% of latency ({latencyBottleneck.avg_latency_ms.toFixed(0)}ms avg)
                      </div>
                      {latencyPercent > 50 && latencyBottleneck.segment_type === 'tts' && (
                        <div className="mt-2 text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded">
                          💡 Try streaming TTS or faster provider (Cartesia)
                        </div>
                      )}
                      {latencyPercent > 50 && latencyBottleneck.segment_type === 'llm' && (
                        <div className="mt-2 text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded">
                          💡 Try GPT-4o-mini or Groq for faster responses
                        </div>
                      )}
                    </div>
                  );
                })()}
                
                {/* Quick Stats */}
                <div className="p-4 bg-white rounded-lg border">
                  <div className="text-xs text-gray-500 uppercase mb-1">📊 Pipeline Efficiency</div>
                  <div className="space-y-2">
                    {segmentStats.map(seg => {
                      const totalCost = segmentStats.reduce((sum, s) => sum + s.total_cost, 0);
                      const percent = totalCost > 0 ? (seg.total_cost / totalCost) * 100 : 0;
                      return (
                        <div key={seg.segment_type} className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: SEGMENT_COLORS[seg.segment_type] }}
                          />
                          <div className="text-xs uppercase flex-1">{seg.segment_type}</div>
                          <div className="text-xs font-medium">{percent.toFixed(0)}%</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400">
                Track voice calls to see pipeline insights
              </div>
            )}
          </CardContent>
        </Card>

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
              <ProviderCalculator altCosts={alternativeCosts} />
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

        {/* Cross-Platform Comparison */}
        {platformComparison && platformComparison.platforms.length > 0 && (
          <Card className="border-2 border-emerald-200 bg-gradient-to-r from-emerald-50 to-teal-50">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                🔀 Cross-Platform Comparison
              </CardTitle>
              <CardDescription>Compare costs across Vapi, Retell, DIY, and other platforms</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Platform Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {platformComparison.platforms.map((platform) => (
                    <div 
                      key={platform.platform}
                      className={`p-4 rounded-lg border ${
                        platform.platform === platformComparison.insights.cheapest_platform
                          ? 'border-green-300 bg-green-50'
                          : platform.platform === platformComparison.insights.most_expensive_platform
                          ? 'border-red-200 bg-red-50'
                          : 'border-gray-200 bg-white'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-bold text-lg uppercase">{platform.platform}</span>
                        {platform.platform === platformComparison.insights.cheapest_platform && (
                          <Badge className="bg-green-500">Cheapest</Badge>
                        )}
                      </div>
                      <div className="text-2xl font-bold">${platform.total_cost.toFixed(2)}</div>
                      <div className="text-sm text-gray-600">
                        {platform.call_count} calls • {platform.total_duration_minutes.toFixed(1)} min
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        ${platform.cost_per_minute.toFixed(4)}/min • ${platform.cost_per_call.toFixed(4)}/call
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* Insights */}
                {platformComparison.insights.recommendation && (
                  <div className="p-4 bg-amber-100 border border-amber-300 rounded-lg">
                    <div className="font-medium text-amber-800">💡 Optimization Opportunity</div>
                    <div className="text-sm text-amber-700 mt-1">
                      {platformComparison.insights.recommendation}
                    </div>
                    <div className="text-lg font-bold text-amber-900 mt-2">
                      Potential monthly savings: ${platformComparison.insights.potential_monthly_savings.toFixed(2)}
                    </div>
                  </div>
                )}
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

