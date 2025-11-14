"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useUser } from "@clerk/nextjs";
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
import { ProviderCostChart } from "@/components/dashboard/ProviderCostChart";
import { Sparkline } from "@/components/Sparkline";
import { useDateRange } from "@/contexts/DateRangeContext";
import { getDateRangeMs } from "@/components/DateRangeFilter";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const router = useRouter();
  const { isLoaded, user } = useUser();
  const { dateRange } = useDateRange();
  
  const [runs, setRuns] = useState<Run[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !user) return;

    async function loadData() {
      try {
        // For now, don't filter by tenant_id to maintain backward compatibility
        // TODO: Enable tenant filtering once data is properly tagged with tenant_id
        // const tenantId = getTenantId(user.id);
        
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

  // Calculate stats from filtered events (including untracked costs)
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

    // Separate agent vs untracked costs
    const agentEvents = recentEvents.filter(e => e.section?.startsWith("agent:") || e.section_path?.startsWith("agent:"));
    const untrackedEvents = recentEvents.filter(e => !e.section?.startsWith("agent:") && !e.section_path?.startsWith("agent:"));

    const total_cost = recentEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    const agent_cost = agentEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    const untracked_cost = untrackedEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    const total_calls = recentEvents.length;
    const week_cost = weekEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0) / 7;

    // Get unique run IDs from ALL events (not just filtered by customer)
    // This ensures total_runs shows all runs, not just customer-filtered ones
    const allRecentEvents = allEvents.filter(e => {
      const eventDate = new Date(e.created_at);
      return eventDate >= yesterday;
    });
    const uniqueRuns = new Set(allRecentEvents.map(e => e.run_id));

    // Calculate untracked percentage
    const untracked_percentage = total_cost > 0 ? (untracked_cost / total_cost) * 100 : 0;

    return {
      total_cost_24h: total_cost,
      agent_cost_24h: agent_cost,
      untracked_cost_24h: untracked_cost,
      untracked_calls_24h: untrackedEvents.length,
      untracked_percentage,
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
  const filteredProviderStats = (() => {
    const realStats = (selectedCustomer
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
    ).filter(stat => stat.provider !== "internal" && stat.provider !== "unknown"); // Hide "unknown" provider
    
    // Add fake data if no real data
    if (realStats.length === 0) {
      return [
        { provider: 'openai', total_cost: 0.125, call_count: 450, avg_latency: 1234, error_count: 2, percentage: 45.2 },
        { provider: 'anthropic', total_cost: 0.089, call_count: 280, avg_latency: 987, error_count: 1, percentage: 32.1 },
        { provider: 'pinecone', total_cost: 0.032, call_count: 120, avg_latency: 456, error_count: 0, percentage: 11.5 },
        { provider: 'stripe', total_cost: 0.019, call_count: 80, avg_latency: 234, error_count: 0, percentage: 6.8 },
        { provider: 'google', total_cost: 0.014, call_count: 65, avg_latency: 567, error_count: 0, percentage: 5.0 },
      ];
    }
    
    return realStats;
  })();

  // Prepare daily chart data for stacked area chart
  const dailyChartData: Array<{ date: string; [provider: string]: string | number }> = (() => {
    const dateRangeMs = getDateRangeMs(dateRange);
    const startDate = new Date(Date.now() - dateRangeMs);
    const dayMap = new Map<string, Record<string, number>>();
    
    filteredEvents.forEach(event => {
      const eventDate = new Date(event.created_at);
      if (eventDate < startDate || !event.provider || event.provider === "internal") return;
      
      const dateKey = eventDate.toISOString().split('T')[0]; // YYYY-MM-DD
      const dayData = dayMap.get(dateKey) || { date: dateKey } as Record<string, any>;
      const provider = event.provider || 'unknown';
      dayData[provider] = ((dayData[provider] as number) || 0) + (event.cost_usd || 0);
      dayMap.set(dateKey, dayData);
    });
    
    const realData: Array<{ date: string; [provider: string]: string | number }> = Array.from(dayMap.values()).sort((a, b) => {
      const aDate = (a as Record<string, any>).date as string;
      const bDate = (b as Record<string, any>).date as string;
      return aDate.localeCompare(bDate);
    }) as Array<{ date: string; [provider: string]: string | number }>;
    
    // Add fake data if no real data
    if (realData.length === 0) {
      const days = Math.ceil(dateRangeMs / (24 * 60 * 60 * 1000));
      const providers = ['openai', 'anthropic', 'pinecone', 'stripe'];
      return Array.from({ length: Math.min(days, 30) }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (Math.min(days, 30) - 1 - i));
        const dateKey = date.toISOString().split('T')[0];
        const dayData: Record<string, any> = { date: dateKey };
        providers.forEach((provider, idx) => {
          // Create realistic variation
          const baseCost = [0.15, 0.08, 0.03, 0.02][idx];
          const variation = 0.7 + Math.random() * 0.6; // 70% to 130% variation
          dayData[provider] = baseCost * variation * (1 + Math.sin(i * 0.3) * 0.2);
        });
        return dayData as { date: string; [provider: string]: string | number };
      });
    }
    
    return realData;
  })();

  const chartProviders = (() => {
    const realProviders = Array.from(new Set(filteredProviderStats.map(s => s.provider)));
    if (realProviders.length === 0) {
      return ['openai', 'anthropic', 'pinecone', 'stripe'];
    }
    return realProviders;
  })();

  // Calculate 7-day sparklines for each provider
  const providerSparklines = new Map<string, number[]>();
  filteredProviderStats.forEach(stat => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });
    
    const sparklineData = last7Days.map(date => {
      const dayEvents = filteredEvents.filter(e => {
        const eventDate = new Date(e.created_at).toISOString().split('T')[0];
        return eventDate === date && e.provider === stat.provider;
      });
      return dayEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    });
    
    // Add fake sparkline data if all zeros
    if (sparklineData.every(v => v === 0)) {
      const baseCost = stat.total_cost / 7;
      const fakeData = last7Days.map((_, i) => {
        const variation = 0.7 + Math.random() * 0.6;
        const trend = 1 + Math.sin(i * 0.5) * 0.2;
        return baseCost * variation * trend;
      });
      providerSparklines.set(stat.provider, fakeData);
    } else {
      providerSparklines.set(stat.provider, sparklineData);
    }
  });

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

  if (loading) {
    return (
      <div className="space-y-8">
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
      <div className="space-y-6">
        <div className="flex items-center justify-end gap-4">
          <Link
            href="/settings"
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            Settings →
          </Link>
          <Link
            href="/runs"
            className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            View All Runs →
          </Link>
        </div>

      {/* KPI Cards */}
      <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Total Cost (24h)</div>
            <div className="text-3xl font-bold text-gray-900">{formatCost(stats.total_cost_24h)}</div>
            {stats.cost_change !== undefined && (
              <div className={`flex items-center text-xs font-medium mt-1 ${stats.cost_change > 0 ? "text-red-600" : "text-green-600"}`}>
                <span>{stats.cost_change > 0 ? "+" : ""}{stats.cost_change.toFixed(1)}%</span>
                <span className="ml-1.5 text-gray-500 font-normal">vs 7d avg</span>
              </div>
            )}
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">API Calls (24h)</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_calls_24h.toLocaleString()}</div>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Avg Cost/Call</div>
            <div className="text-3xl font-bold text-gray-900">{formatCost(stats.avg_cost_per_call)}</div>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Total Runs</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total_runs}</div>
          </div>
        </div>
      </div>

      {/* Untracked Costs Card (only show if there are untracked costs) */}
      {stats.untracked_cost_24h > 0 && (
        <Card className={`border ${stats.untracked_percentage > 20 ? "border-amber-300 bg-amber-50/50" : "border-gray-200"}`}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <span className="text-amber-600">⚠️</span>
                Untracked / Non-Agent Costs (24h)
              </CardTitle>
              {stats.untracked_percentage > 20 && (
                <Badge variant="destructive" className="bg-amber-600">
                  {stats.untracked_percentage.toFixed(1)}% of total
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <div className="text-sm text-gray-600 mb-1">Untracked Cost</div>
                <div className="text-2xl font-bold text-gray-900">{formatCost(stats.untracked_cost_24h)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">Untracked Calls</div>
                <div className="text-2xl font-bold text-gray-900">{stats.untracked_calls_24h.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">% of Total</div>
                <div className="text-2xl font-bold text-gray-900">{stats.untracked_percentage.toFixed(1)}%</div>
              </div>
            </div>
            <div className="mt-4 text-xs text-gray-600 space-y-1">
              <p>💡 <strong>Tip:</strong> Untracked costs occur when API calls are not wrapped with agents/tools.</p>
              <p className="pl-5">Use <code className="px-1.5 py-0.5 bg-gray-100 rounded">@agent("name")</code> to mark agent entrypoints.</p>
              <p className="pl-5">Use <code className="px-1.5 py-0.5 bg-gray-100 rounded">wrap_all_tools()</code> before passing tools to frameworks.</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stacked Area Chart */}
      <ProviderCostChart 
        data={dailyChartData}
        providers={chartProviders}
      />

      {/* Provider Breakdown Table */}
      <Card className="border-gray-200">
        <CardHeader className="border-b border-gray-100">
          <CardTitle className="text-lg font-semibold text-gray-900">Provider Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200 hover:bg-transparent">
                  <TableHead className="px-4 py-3 font-semibold text-gray-700">Provider</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Calls</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Cost</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Avg Latency</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Errors</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">% of Spend</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Trend (7d)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProviderStats.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      {selectedCustomer ? `No data for customer: ${selectedCustomer}` : "No provider data available"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProviderStats.map((provider) => {
                    // Use percentage from API if available, otherwise calculate from stats
                    // This prevents >100% when using filtered events vs API totals
                    const percentage = provider.percentage !== undefined && provider.percentage !== null
                      ? provider.percentage
                      : (stats.total_cost_24h > 0
                          ? calculatePercentage(provider.total_cost, stats.total_cost_24h)
                          : 0);
                    const sparklineData = providerSparklines.get(provider.provider) || [];
                    
                    return (
                      <TableRow key={provider.provider} className="border-gray-100 hover:bg-gray-50">
                        <TableCell className="px-4 py-3">
                          <Badge variant="outline" className="bg-gray-100 text-gray-700 border-gray-200">{provider.provider}</Badge>
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-900">{provider.call_count.toLocaleString()}</TableCell>
                        <TableCell className="px-4 py-3 text-right font-semibold text-gray-900">
                          {formatCost(provider.total_cost)}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-900">{provider.avg_latency?.toFixed(0) || 0}ms</TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-900">{provider.error_count || 0}</TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-900">{percentage.toFixed(1)}%</TableCell>
                        <TableCell className="px-4 py-3 text-right">
                          <div className="flex justify-end">
                            <Sparkline 
                              data={sparklineData}
                              color="#3b82f6"
                              width={80}
                              height={24}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* API Cost Breakdown - Keep for agent table */}
      <div className="grid gap-4 md:grid-cols-1">

        {/* Top Agents/Workflows */}
        <Card className="border-gray-200">
          <CardHeader className="border-b border-gray-100">
            <CardTitle className="text-lg font-semibold text-gray-900">Top Agents & Workflows (24h)</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200 hover:bg-transparent">
                  <TableHead className="px-4 py-3 font-semibold text-gray-700">Agent/Tool</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Total Cost</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Calls</TableHead>
                  <TableHead className="px-4 py-3 font-semibold text-gray-700 text-right">Avg/Call</TableHead>
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
                        <TableCell colSpan={4} className="px-4 py-8 text-center text-gray-500">
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
                        className={cn("border-gray-100", runId ? "cursor-pointer hover:bg-gray-50" : "")}
                        onClick={() => {
                          if (runId) {
                            console.log(`[Dashboard] Navigating to run: ${runId}`);
                            router.push(`/runs/${runId}`);
                          }
                        }}
                      >
                        <TableCell className="px-4 py-3">
                          <Badge variant="secondary" className="bg-gray-100 text-gray-700 border-gray-200">{agent}</Badge>
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right font-semibold text-gray-900">
                          {formatCost(stats.cost)}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-900">{stats.calls}</TableCell>
                        <TableCell className="px-4 py-3 text-right text-gray-600">
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
                      {formatCost(run.total_cost)}
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
