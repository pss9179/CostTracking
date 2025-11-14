"use client";

import { useEffect, useState } from "react";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Server, Database, Zap, Clock } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchRuns } from "@/lib/api";

interface InfraStats {
  category: "vector_db" | "api";
  provider: string;
  service: string;
  calls: number;
  reads: number;
  writes: number;
  cost: number;
  avg_latency: number;
  errors: number;
}

// Categorize providers
const VECTOR_DB_PROVIDERS = ["pinecone", "weaviate", "qdrant", "milvus", "chroma"];
const isVectorDB = (provider: string) => 
  VECTOR_DB_PROVIDERS.some(vdb => provider.toLowerCase().includes(vdb));

export default function InfrastructurePage() {
  const [stats, setStats] = useState<InfraStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const runs = await fetchRuns(1000);
        
        // Aggregate by provider (excluding LLMs)
        const aggregated = new Map<string, InfraStats>();
        
        runs.forEach(run => {
          const provider = run.provider?.toLowerCase() || "unknown";
          
          // Skip internal and LLM providers
          if (provider === "internal" || provider === "openai" || provider === "anthropic" || 
              provider === "google" || provider === "cohere") {
            return;
          }
          
          const category = isVectorDB(provider) ? "vector_db" : "api";
          const key = `${category}::${provider}`;
          
          const existing = aggregated.get(key) || {
            category,
            provider: run.provider || "unknown",
            service: run.endpoint_path || provider,
            calls: 0,
            reads: 0,
            writes: 0,
            cost: 0,
            avg_latency: 0,
            errors: 0,
          };

          existing.calls++;
          existing.cost += run.cost || 0;
          existing.avg_latency += run.latency || 0;
          if (run.error_message) existing.errors++;
          
          // Categorize as read/write based on endpoint
          const endpoint = run.endpoint_path?.toLowerCase() || "";
          if (endpoint.includes("query") || endpoint.includes("search") || endpoint.includes("get") || endpoint.includes("fetch")) {
            existing.reads++;
          } else if (endpoint.includes("insert") || endpoint.includes("upsert") || endpoint.includes("update") || endpoint.includes("delete") || endpoint.includes("create")) {
            existing.writes++;
          }

          aggregated.set(key, existing);
        });

        // Calculate averages
        const result = Array.from(aggregated.values()).map(s => ({
          ...s,
          avg_latency: s.calls > 0 ? s.avg_latency / s.calls : 0,
        }));

        setStats(result.sort((a, b) => b.cost - a.cost));
      } catch (error) {
        console.error("Failed to load infrastructure stats:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const totalCost = stats.reduce((sum, s) => sum + s.cost, 0);
  const totalCalls = stats.reduce((sum, s) => sum + s.calls, 0);
  const totalReads = stats.reduce((sum, s) => sum + s.reads, 0);
  const totalWrites = stats.reduce((sum, s) => sum + s.writes, 0);

  // Chart data
  const chartData = stats.slice(0, 10).map(s => ({
    name: s.provider,
    cost: parseFloat(s.cost.toFixed(4)),
  }));

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        {/* Metrics Cards */}
        <div className="grid gap-5 md:grid-cols-4">
          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Infra Cost</CardTitle>
              <Server className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">${totalCost.toFixed(2)}</div>
              <p className="text-xs text-gray-500 mt-2">
                Total infrastructure spend
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">DB Reads</CardTitle>
              <Database className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{totalReads.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-2">
                Query operations
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">DB Writes</CardTitle>
              <Database className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{totalWrites.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-2">
                Insert/update operations
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">API Calls</CardTitle>
              <Zap className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-3xl font-bold text-gray-900">{totalCalls.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-2">
                Total requests
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Chart */}
        <Card className="border-gray-200">
          <CardHeader className="border-b border-gray-100">
            <CardTitle className="text-lg font-semibold text-gray-900">Cost by Provider</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {loading ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-muted-foreground">Loading...</p>
              </div>
            ) : chartData.length === 0 ? (
              <div className="h-64 flex items-center justify-center">
                <p className="text-muted-foreground">No infrastructure data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip
                    formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
                  />
                  <Legend />
                  <Bar dataKey="cost" fill="#f97316" name="Cost ($)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Table */}
        <Card className="border-gray-200">
          <CardHeader className="border-b border-gray-100">
            <CardTitle className="text-lg font-semibold text-gray-900">Infrastructure Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-gray-200">
                  <tr className="text-left">
                    <th className="px-4 py-3 font-semibold text-gray-700">Category</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Provider</th>
                    <th className="px-4 py-3 font-semibold text-gray-700">Service/API</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Calls</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Reads</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Writes</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Cost</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Avg Latency</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">Errors</th>
                    <th className="px-4 py-3 font-semibold text-gray-700 text-right">% of Infra</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="px-4 py-8 text-center text-gray-500">
                        No infrastructure data available
                      </td>
                    </tr>
                  ) : (
                    stats.map((s, i) => (
                      <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                            {s.category === "vector_db" ? "Vector DB" : "API"}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-medium text-gray-900">{s.provider}</td>
                        <td className="px-4 py-3 font-mono text-xs text-gray-600">{s.service}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.calls.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.reads.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-900">{s.writes.toLocaleString()}</td>
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

