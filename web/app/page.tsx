"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchRuns, fetchProviderStats, type Run, type ProviderStats } from "@/lib/api";
import { TenantSelector } from "@/components/TenantSelector";
import { formatCost, calculatePercentage } from "@/lib/stats";
import { DollarSign, TrendingUp, Activity, Layers } from "lucide-react";
import { KPICard } from "@/components/layout/KPICard";
import { CustomerCostBreakdown } from "@/components/CustomerCostBreakdown";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const tenantId = searchParams.get("tenant_id") || undefined;
  
  const [runs, setRuns] = useState<Run[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [runsData, providersData] = await Promise.all([
          fetchRuns(1000, tenantId),
          fetchProviderStats(24, tenantId)
        ]);
        setRuns(runsData);
        setProviderStats(providersData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [tenantId]);

  // Calculate stats from runs
  const stats = (() => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    const recentRuns = runs.filter(run => {
      const runDate = new Date(run.started_at);
      return runDate >= yesterday;
    });
    
    const weekRuns = runs.filter(run => {
      const runDate = new Date(run.started_at);
      return runDate >= weekAgo && runDate < yesterday;
    });

    const total_cost = recentRuns.reduce((sum, run) => sum + run.total_cost, 0);
    const total_calls = recentRuns.reduce((sum, run) => sum + run.call_count, 0);
    const week_cost = weekRuns.reduce((sum, run) => sum + run.total_cost, 0) / 7;

    return {
      total_cost_24h: total_cost,
      total_calls_24h: total_calls,
      avg_cost_per_call: total_calls > 0 ? total_cost / total_calls : 0,
      total_runs: recentRuns.length,
      cost_change: week_cost > 0 ? ((total_cost - week_cost) / week_cost) * 100 : 0,
    };
  })();


  if (loading) {
    return (
      <div className="p-8 space-y-8">
        <h1 className="text-3xl font-bold">LLM Cost Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Make sure the collector API is running on http://localhost:8000
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">LLM Cost Dashboard</h1>
        <div className="flex items-center gap-4">
          <TenantSelector />
          <Link
            href="/runs"
            className="text-sm text-blue-600 hover:underline"
          >
            View All Runs →
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Cost (24h)"
          value={formatCost(stats.total_cost_24h)}
          icon={DollarSign}
          change={stats.cost_change}
          changeLabel="vs 7d avg"
          invertColors={true}
        />
        <KPICard
          title="API Calls (24h)"
          value={stats.total_calls_24h.toLocaleString()}
          icon={Activity}
        />
        <KPICard
          title="Avg Cost/Call"
          value={formatCost(stats.avg_cost_per_call)}
          icon={TrendingUp}
        />
        <KPICard
          title="Total Runs"
          value={stats.total_runs}
          icon={Layers}
        />
      </div>

      {/* API Cost Breakdown */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Costs by API Provider (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            {providerStats.length > 0 ? (
              <div className="space-y-3">
                {providerStats.map((provider) => {
                  const percentage = stats.total_cost_24h > 0
                    ? calculatePercentage(provider.total_cost, stats.total_cost_24h)
                    : 0;
                  return (
                    <div key={provider.provider} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{provider.provider}</Badge>
                        <span className="text-sm text-muted-foreground">
                          {provider.call_count} calls
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-32 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${Math.min(percentage, 100)}%` }}
                          />
                        </div>
                        <span className="font-semibold text-sm w-20 text-right">
                          {formatCost(provider.total_cost)}
                        </span>
                        <span className="text-xs text-muted-foreground w-12 text-right">
                          {percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                No API data available
              </p>
            )}
          </CardContent>
        </Card>

        {/* Top Agents/Workflows */}
        <Card>
          <CardHeader>
            <CardTitle>Top Agents & Workflows (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Agent/Tool</TableHead>
                  <TableHead className="text-right">Total Cost</TableHead>
                  <TableHead className="text-right">Calls</TableHead>
                  <TableHead className="text-right">Avg/Call</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(() => {
                  // Aggregate runs by top_section
                  const agentStats = new Map<string, { cost: number; calls: number }>();
                  
                  runs.forEach(run => {
                    if (!run.top_section || run.top_section.includes("retry:") || run.top_section.includes("test:")) {
                      return;
                    }
                    
                    const existing = agentStats.get(run.top_section) || { cost: 0, calls: 0 };
                    existing.cost += run.total_cost;
                    existing.calls += run.call_count;
                    agentStats.set(run.top_section, existing);
                  });
                  
                  const sortedAgents = Array.from(agentStats.entries())
                    .sort((a, b) => b[1].cost - a[1].cost)
                    .slice(0, 8);
                  
                  if (sortedAgents.length === 0) {
                    return (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-muted-foreground">
                          No agent data available
                        </TableCell>
                      </TableRow>
                    );
                  }
                  
                  return sortedAgents.map(([agent, stats]) => (
                    <TableRow key={agent}>
                      <TableCell>
                        <Badge variant="secondary">{agent}</Badge>
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCost(stats.cost)}
                      </TableCell>
                      <TableCell className="text-right">{stats.calls}</TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatCost(stats.cost / stats.calls)}
                      </TableCell>
                    </TableRow>
                  ));
                })()}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Customer Cost Attribution */}
      {tenantId && (
        <Card>
          <CardHeader>
            <CardTitle>Cost by Customer (24h)</CardTitle>
          </CardHeader>
          <CardContent>
            <CustomerCostBreakdown tenantId={tenantId} />
          </CardContent>
        </Card>
      )}

      {/* Recent Runs Preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Runs</CardTitle>
            <Link
              href="/runs"
              className="text-sm text-blue-600 hover:underline"
            >
              View All
            </Link>
        </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {runs.slice(0, 5).map((run) => (
              <Link
                key={run.run_id}
                href={`/runs/${run.run_id}`}
                className="block p-3 rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-muted-foreground">
                        {run.run_id.slice(0, 8)}...
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {run.top_section}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(run.started_at).toLocaleString()} · {run.call_count} calls
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">
                      ${run.total_cost.toFixed(6)}
                    </div>
                  </div>
                </div>
              </Link>
            ))}
            
            {runs.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No runs found. Run the test script to generate sample data.
              </p>
            )}
        </div>
        </CardContent>
      </Card>
    </div>
  );
}
