"use client";

import { useEffect, useState } from "react";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Zap, Activity, Hash, Clock } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchRuns } from "@/lib/api";

interface LLMStats {
  provider: string;
  model_id: string;
  calls: number;
  tokens_prompt: number;
  tokens_completion: number;
  tokens_total: number;
  cost: number;
  avg_latency: number;
  errors: number;
}

export default function LLMsPage() {
  const [stats, setStats] = useState<LLMStats[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const runs = await fetchRuns(1000);
        
        // Aggregate by provider + model
        const aggregated = new Map<string, LLMStats>();
        
        runs.forEach(run => {
          if (!run.provider || run.provider === "internal") return; // Skip internal/agent events
          
          const key = `${run.provider}::${run.model_id || "unknown"}`;
          const existing = aggregated.get(key) || {
            provider: run.provider,
            model_id: run.model_id || "unknown",
            calls: 0,
            tokens_prompt: 0,
            tokens_completion: 0,
            tokens_total: 0,
            cost: 0,
            avg_latency: 0,
            errors: 0,
          };

          existing.calls++;
          existing.tokens_prompt += run.tokens_prompt || 0;
          existing.tokens_completion += run.tokens_completion || 0;
          existing.tokens_total += (run.tokens_prompt || 0) + (run.tokens_completion || 0);
          existing.cost += run.cost || 0;
          existing.avg_latency += run.latency || 0;
          if (run.error_message) existing.errors++;

          aggregated.set(key, existing);
        });

        // Calculate averages
        const result = Array.from(aggregated.values()).map(s => ({
          ...s,
          avg_latency: s.calls > 0 ? s.avg_latency / s.calls : 0,
        }));

        setStats(result.sort((a, b) => b.cost - a.cost));
      } catch (error) {
        console.error("Failed to load LLM stats:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredStats = selectedProvider === "all"
    ? stats
    : stats.filter(s => s.provider.toLowerCase() === selectedProvider.toLowerCase());

  const totalCost = filteredStats.reduce((sum, s) => sum + s.cost, 0);
  const totalCalls = filteredStats.reduce((sum, s) => sum + s.calls, 0);
  const totalTokens = filteredStats.reduce((sum, s) => sum + s.tokens_total, 0);
  const avgLatency = totalCalls > 0
    ? filteredStats.reduce((sum, s) => sum + s.avg_latency * s.calls, 0) / totalCalls
    : 0;

  // Prepare grouped chart data (models grouped under provider)
  const chartData = (() => {
    const providerGroups = new Map<string, LLMStats[]>();
    
    filteredStats.slice(0, 15).forEach(stat => {
      const existing = providerGroups.get(stat.provider) || [];
      existing.push(stat);
      providerGroups.set(stat.provider, existing);
    });
    
    const data: any[] = [];
    providerGroups.forEach((models, provider) => {
      models.forEach((model, idx) => {
        data.push({
          provider: idx === 0 ? provider : '',  // Only show provider name once
          model: model.model_id.substring(0, 20),
          cost: parseFloat(model.cost.toFixed(4)),
          fullLabel: `${provider}/${model.model_id}`,
        });
      });
    });
    
    return data;
  })();

  // Get unique providers for filter
  const providers = Array.from(new Set(stats.map(s => s.provider)));

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        {/* Header with Filter */}
        <div className="flex items-center justify-end">
          <Select value={selectedProvider} onValueChange={setSelectedProvider}>
            <SelectTrigger className="w-48 border-gray-300">
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Providers</SelectItem>
              {providers.map(p => (
                <SelectItem key={p} value={p.toLowerCase()}>
                  {p}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Metrics Cards */}
        <div className="grid gap-5 md:grid-cols-4">
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">LLM Spend</CardTitle>
              <Zap className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">${totalCost.toFixed(2)}</div>
              <p className="text-xs text-gray-500 mt-2">
                {totalCalls} total requests
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Requests</CardTitle>
              <Activity className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{totalCalls.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-2">
                Across {filteredStats.length} models
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Tokens</CardTitle>
              <Hash className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{(totalTokens / 1000).toFixed(1)}K</div>
              <p className="text-xs text-gray-500 mt-2">
                Total processed
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Avg Latency</CardTitle>
              <Clock className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{avgLatency.toFixed(0)}ms</div>
              <p className="text-xs text-gray-500 mt-2">
                Per request
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Chart - Grouped by Provider */}
        <Card className="border-gray-200">
          <CardHeader className="border-b border-gray-100">
            <CardTitle className="text-lg font-semibold text-gray-900">Spend by Model (Grouped by Provider)</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-muted-foreground">Loading...</p>
              </div>
            ) : chartData.length === 0 ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-muted-foreground">No LLM data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData} margin={{ bottom: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="model" 
                    angle={-45} 
                    textAnchor="end" 
                    height={100}
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number, name: any, props: any) => [
                      `$${value.toFixed(4)}`,
                      props.payload.fullLabel
                    ]}
                    labelFormatter={(label) => `Model: ${label}`}
                  />
                  <Legend />
                  <Bar dataKey="cost" fill="#3b82f6" name="Cost ($)" />
                </BarChart>
              </ResponsiveContainer>
            )}
            <div className="mt-4 text-xs text-muted-foreground">
              * Models are grouped by provider. Each bar represents a model&apos;s cost.
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card className="border-gray-200">
          <CardHeader className="border-b border-gray-100">
            <CardTitle className="text-lg font-semibold text-gray-900">Model Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-gray-200">
                  <tr className="text-left">
                    <th className="px-4 py-3 font-semibold text-gray-700">Provider</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Model ID</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Calls</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Prompt Tkn</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Comp Tkn</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Total Tkn</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Cost</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Avg Latency</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Errors</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">% of LLM</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStats.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="px-4 py-8 text-center text-gray-500">
                        No LLM data available
                      </td>
                    </tr>
                  ) : (
                    filteredStats.map((s, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3 font-medium text-gray-900">{s.provider}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-600">{s.model_id}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.calls.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.tokens_prompt.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.tokens_completion.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.tokens_total.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-semibold text-gray-900">${s.cost.toFixed(4)}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.avg_latency.toFixed(0)}ms</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.errors}</td>
                        <td className="px-4 py-3 text-right text-gray-900">
                          {totalCost > 0 ? ((s.cost / totalCost) * 100).toFixed(1) : 0}%
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}

