"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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
import { fetchRuns, fetchProviderStats, fetchRunDetail, type Run, type ProviderStats } from "@/lib/api";
import { formatCost, calculatePercentage } from "@/lib/stats";
import { DollarSign, TrendingUp, Activity, Layers } from "lucide-react";
import { KPICard } from "@/components/layout/KPICard";
import { CustomerCostChart } from "@/components/CustomerCostChart";
import { CustomerFilter } from "@/components/CustomerFilter";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { loadAuth } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  
  const [runs, setRuns] = useState<Run[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);

  useEffect(() => {
    // Load user from localStorage
    const { user: loadedUser } = loadAuth();
    if (!loadedUser) {
      router.push("/login");
      return;
    }
    setUser(loadedUser);
  }, [router]);

  useEffect(() => {
    if (!user) return;

    async function loadData() {
      try {
        const [runsData, providersData] = await Promise.all([
          fetchRuns(1000),
          fetchProviderStats(24)
        ]);
        setRuns(runsData);
        setProviderStats(providersData);

        // Fetch events for customer filtering
        const eventPromises = runsData.slice(0, 50).map((run) => 
          fetchRunDetail(run.run_id).then((detail) => detail.events).catch(() => [])
        );
        const eventsArrays = await Promise.all(eventPromises);
        const flatEvents = eventsArrays.flat();
        setAllEvents(flatEvents);
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
  }, [isLoaded, user, selectedCustomer]);

  // Filter events by customer if selected
  const filteredEvents = selectedCustomer
    ? allEvents.filter(e => e.customer_id === selectedCustomer)
    : allEvents;
  
  // Debug: Log filtering results
  if (selectedCustomer) {
    console.log(`[Dashboard] Filtering by customer: ${selectedCustomer}`);
    console.log(`[Dashboard] Total events: ${allEvents.length}, Filtered: ${filteredEvents.length}`);
    console.log(`[Dashboard] Customer IDs in events:`, [...new Set(allEvents.map(e => e.customer_id).filter(Boolean))]);
  }

  // Calculate stats from filtered events
  const stats = (() => {
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    // Filter events by time window
    const recentEvents = filteredEvents.filter(e => {
      const eventDate = new Date(e.created_at);
      return eventDate >= yesterday;
    });
    
    const weekEvents = filteredEvents.filter(e => {
      const eventDate = new Date(e.created_at);
      return eventDate >= weekAgo && eventDate < yesterday;
    });

    const total_cost = recentEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    const total_calls = recentEvents.length;
    const week_cost = weekEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0) / 7;

    // Get unique run IDs
    const uniqueRuns = new Set(recentEvents.map(e => e.run_id));

    return {
      total_cost_24h: total_cost,
      total_calls_24h: total_calls,
      avg_cost_per_call: total_calls > 0 ? total_cost / total_calls : 0,
      total_runs: uniqueRuns.size,
      cost_change: week_cost > 0 ? ((total_cost - week_cost) / week_cost) * 100 : 0,
    };
  })();

  // Filter runs by customer (for display)
  const filteredRuns = selectedCustomer
    ? runs.filter(run => {
        // Check if any event in this run matches the customer
        return allEvents.some(e => e.run_id === run.run_id && e.customer_id === selectedCustomer);
      })
    : runs;

  // Filter provider stats by customer and exclude "internal" provider
  const filteredProviderStats = (selectedCustomer
    ? providerStats.filter(stat => {
        // Recalculate from filtered events
        const customerEvents = filteredEvents.filter(e => e.provider === stat.provider);
        return customerEvents.length > 0;
      }).map(stat => {
        // Recalculate from filtered events
        const customerEvents = filteredEvents.filter(e => e.provider === stat.provider);
        const totalCost = customerEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
        return {
          ...stat,
          total_cost: totalCost,
          call_count: customerEvents.length,
          percentage: stats.total_cost_24h > 0 ? (totalCost / stats.total_cost_24h) * 100 : 0,
        };
      })
    : providerStats
  ).filter(stat => stat.provider !== "internal"); // Exclude internal span events

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

  if (!isLoaded || loading) {
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

  return (
    <ProtectedLayout>
      <div className="p-8 space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">LLM Cost Dashboard</h1>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              {user?.email}
            </div>
          <Link
            href="/settings"
            className="text-sm text-blue-600 hover:underline"
          >
            Settings →
          </Link>
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
            {filteredProviderStats.length > 0 ? (
              <div className="space-y-3">
                {filteredProviderStats.map((provider) => {
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
                {selectedCustomer ? `No data for customer: ${selectedCustomer}` : "No API data available"}
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
                  // Aggregate filtered events by section (only agent: sections)
                  const agentStats = new Map<string, { cost: number; calls: number }>();
                  
                  filteredEvents.forEach(event => {
                    const section = event.section_path || event.section;
                    if (!section || !section.startsWith("agent:")) return;
                    
                    const agentName = section.split("/")[0];
                    const existing = agentStats.get(agentName) || { cost: 0, calls: 0 };
                    existing.cost += event.cost_usd || 0;
                    existing.calls += 1;
                    agentStats.set(agentName, existing);
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
                  
                  return sortedAgents.map(([agent, stats]) => {
                    // Find the most expensive run for this agent
                    const agentEvents = filteredEvents.filter((e) => {
                      const section = e.section_path || e.section;
                      return section && section.startsWith(agent);
                    });
                    
                    const runCosts = new Map<string, number>();
                    agentEvents.forEach((e) => {
                      if (e.run_id) {
                        const current = runCosts.get(e.run_id) || 0;
                        runCosts.set(e.run_id, current + (e.cost_usd || 0));
                      }
                    });
                    
                    const mostExpensiveRun = Array.from(runCosts.entries())
                      .sort((a, b) => b[1] - a[1])[0];
                    
                    const runId = mostExpensiveRun?.[0];
                    
                    return (
                      <TableRow 
                        key={agent}
                        className={runId ? "cursor-pointer hover:bg-muted/50" : ""}
                        onClick={() => {
                          if (runId) {
                            console.log(`[Dashboard] Navigating to run: ${runId}`);
                            router.push(`/runs/${runId}`);
                          }
                        }}
                      >
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
                    );
                  });
                })()}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Customer Cost Chart */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CustomerCostChart />
        
        {/* Customer Filter */}
        <Card>
          <CardHeader>
            <CardTitle>Filter by Customer</CardTitle>
            <p className="text-sm text-muted-foreground">
              View costs segmented by your end-users
            </p>
          </CardHeader>
          <CardContent>
            <CustomerFilter
              selectedCustomer={selectedCustomer}
              onCustomerChange={setSelectedCustomer}
            />
            {selectedCustomer && (
              <div className="mt-4 p-3 bg-blue-50 rounded">
                <p className="text-sm text-blue-900">
                  Filtering by: <strong>{selectedCustomer}</strong>
                </p>
                <p className="text-xs text-blue-700 mt-1">
                  All charts and tables below are filtered to this customer
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

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
            {filteredRuns.slice(0, 5).map((run) => (
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
            
            {filteredRuns.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {selectedCustomer 
                  ? `No runs found for customer: ${selectedCustomer}. Make sure events have customer_id set.`
                  : "No runs found. Run the test script to generate sample data."}
              </p>
            )}
        </div>
        </CardContent>
      </Card>
      </div>
    </ProtectedLayout>
  );
}
