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
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">LLMs</h1>
            <p className="text-muted-foreground mt-1">
              Model-level cost and usage breakdown
            </p>
          </div>

          {/* Provider Filter */}
          <Select value={selectedProvider} onValueChange={setSelectedProvider}>
            <SelectTrigger className="w-48">
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
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">LLM Spend</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${totalCost.toFixed(2)}</div>
              <p className="text-xs text-muted-foreground">
                {totalCalls} total requests
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Requests</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalCalls.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                Across {filteredStats.length} models
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tokens</CardTitle>
              <Hash className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(totalTokens / 1000).toFixed(1)}K</div>
              <p className="text-xs text-muted-foreground">
                Total processed
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgLatency.toFixed(0)}ms</div>
              <p className="text-xs text-muted-foreground">
                Per request
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Chart - Grouped by Provider */}
        <Card>
          <CardHeader>
            <CardTitle>Spend by Model (Grouped by Provider)</CardTitle>
          </CardHeader>
          <CardContent>
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
        <Card>
          <CardHeader>
            <CardTitle>Model Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b">
                  <tr className="text-left">
                    <th className="p-2 font-medium">Provider</th>
                    <th className="p-2 font-medium">Model ID</th>
                    <th className="p-2 font-medium text-right">Calls</th>
                    <th className="p-2 font-medium text-right">Prompt Tkn</th>
                    <th className="p-2 font-medium text-right">Comp Tkn</th>
                    <th className="p-2 font-medium text-right">Total Tkn</th>
                    <th className="p-2 font-medium text-right">Cost</th>
                    <th className="p-2 font-medium text-right">Avg Latency</th>
                    <th className="p-2 font-medium text-right">Errors</th>
                    <th className="p-2 font-medium text-right">% of LLM</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStats.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="p-4 text-center text-muted-foreground">
                        No LLM data available
                      </td>
                    </tr>
                  ) : (
                    filteredStats.map((s, i) => (
                      <tr key={i} className="border-b hover:bg-muted/50">
                        <td className="p-2">{s.provider}</td>
                        <td className="p-2 font-mono text-xs">{s.model_id}</td>
                        <td className="p-2 text-right">{s.calls.toLocaleString()}</td>
                        <td className="p-2 text-right">{s.tokens_prompt.toLocaleString()}</td>
                        <td className="p-2 text-right">{s.tokens_completion.toLocaleString()}</td>
                        <td className="p-2 text-right">{s.tokens_total.toLocaleString()}</td>
                        <td className="p-2 text-right font-medium">${s.cost.toFixed(4)}</td>
                        <td className="p-2 text-right">{s.avg_latency.toFixed(0)}ms</td>
                        <td className="p-2 text-right">{s.errors}</td>
                        <td className="p-2 text-right">
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

