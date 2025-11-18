"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
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
  const { getToken } = useAuth();
  const [stats, setStats] = useState<InfraStats[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const token = await getToken();
        if (!token) {
          console.error("No Clerk token available");
          return;
        }
        const runs = await fetchRuns(1000, null, token);
        
        // Aggregate by provider (excluding LLMs)
        const aggregated = new Map<string, InfraStats>();
        
        // Note: Run type doesn't have provider info - would need to fetch RunDetail for each run
        // For now, return empty stats since infrastructure data requires event-level details
        // TODO: Implement proper infrastructure aggregation by fetching run details
        
        // Return empty array for now - infrastructure stats require event-level data
        setStats([]);
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

  // Chart data - NO FAKE DATA
  const chartData = stats.slice(0, 10).map(s => ({
    name: s.provider,
    cost: parseFloat(s.cost.toFixed(4)),
  }));

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        {/* Metrics Cards */}
        <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">Infra Cost</div>
              <div className="text-3xl font-bold text-gray-900">${totalCost.toFixed(2)}</div>
              <p className="text-xs text-gray-500 mt-1">
                Total infrastructure spend
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">DB Reads</div>
              <div className="text-3xl font-bold text-gray-900">{totalReads.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-1">
                Query operations
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">DB Writes</div>
              <div className="text-3xl font-bold text-gray-900">{totalWrites.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-1">
                Insert/update operations
              </p>
            </div>
            <div className="hidden md:block h-10 w-px bg-indigo-200" />
            <div className="flex-1 min-w-[120px]">
              <div className="text-sm font-medium text-gray-600 mb-2">API Calls</div>
              <div className="text-3xl font-bold text-gray-900">{totalCalls.toLocaleString()}</div>
              <p className="text-xs text-gray-500 mt-1">
                Total requests
              </p>
            </div>
          </div>
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

