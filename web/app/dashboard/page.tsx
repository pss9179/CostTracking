"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useUser } from "@clerk/nextjs";
import { useAuth } from "@clerk/nextjs";
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
import {
  fetchRuns,
  fetchProviderStats,
  fetchModelStats,
  fetchDailyStats,
  fetchRunDetail,
  type Run,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
} from "@/lib/api";
import { formatCost, calculatePercentage } from "@/lib/stats";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { MainMetricChart } from "@/components/dashboard/MainMetricChart";
import { Sparkline } from "@/components/Sparkline";
import { useDateRange } from "@/contexts/DateRangeContext";
import { getDateRangeMs } from "@/components/DateRangeFilter";
import { cn } from "@/lib/utils";
import { Suspense } from "react";
import { DateRangeFilter } from "@/components/DateRangeFilter";

function DashboardPageContent() {
  const router = useRouter();
  const { isLoaded, user } = useUser();
  const { getToken } = useAuth();
  const { dateRange, setDateRange } = useDateRange();

  const [runs, setRuns] = useState<Run[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);
  const [userType, setUserType] = useState<"solo_dev" | "saas_founder" | null>(
    null
  );

  useEffect(() => {
    // If Clerk isn't loaded yet, wait
    if (!isLoaded) {
      return;
    }

    // If no user, redirect or show error
    if (!user) {
      setLoading(false);
      setError("Not authenticated. Please sign in.");
      return;
    }

    async function loadData(isBackground = false) {
      // Set loading immediately for non-background loads
      if (!isBackground) {
        setLoading(true);
      }
      setError(null);

      try {
        // Get Clerk token and set it for API calls
        const token = await getToken();
        if (token && typeof window !== "undefined") {
          (window as any).__clerkToken = token;
        }

        // Make sure we have a token before making API calls
        if (!token) {
          throw new Error("Not authenticated. Please sign in again.");
        }

        // Fetch user data and main data in parallel
        const collectorUrl =
          process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

        // Fetch user data and main data in parallel - with error handling
        const [userResponse, runsData, providersData, modelsData, dailyData] = await Promise.all([
          fetch(`${collectorUrl}/clerk/api-keys/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }).catch(() => ({ ok: false, json: async () => ({}) })), // Don't fail if user endpoint fails
          fetchRuns(50, null, token).catch((err) => {
            console.warn("[Dashboard] Failed to fetch runs:", err);
            return []; // Return empty array on error
          }),
          fetchProviderStats(24, null, token).catch((err) => {
            console.warn("[Dashboard] Failed to fetch provider stats:", err);
            return []; // Return empty array on error
          }),
          fetchModelStats(24, null, token).then((data) => {
            console.log("[Dashboard] Model stats fetched:", data?.length || 0, "models");
            return data;
          }).catch((err) => {
            console.warn("[Dashboard] Failed to fetch model stats:", err);
            return []; // Return empty array on error
          }),
          fetchDailyStats(7, null, token).then((data) => {
            console.log("[Dashboard] Daily stats fetched:", data?.length || 0, "days");
            return data;
          }).catch((err) => {
            console.warn("[Dashboard] Failed to fetch daily stats:", err);
            return []; // Return empty array on error
          }),
        ]);

        // Handle user data
        if (userResponse && userResponse.ok) {
          try {
            const userData = await userResponse.json();
            if (userData.user?.user_type) {
              setUserType(userData.user.user_type);
            }
          } catch (e) {
            console.warn("[Dashboard] Failed to parse user data:", e);
          }
        }

        // Log for debugging
        console.log(
          `[Dashboard] Fetched ${runsData?.length || 0} runs, ${
            providersData?.length || 0
          } provider stats`
        );

        // Set data immediately - even if empty, show the dashboard
        setRuns(runsData || []);
        setProviderStats(providersData || []);
        setModelStats(modelsData || []);
        setDailyStats(dailyData || []);

        // IMPORTANT: Set loading to false IMMEDIATELY after getting main data
        // Don't wait for events - they load in background
        if (!isBackground) {
          setLoading(false);
        }

        // Fetch events for customer filtering in background - only fetch first 10 runs for speed
        // This is non-blocking so dashboard shows up fast
        if (runsData && runsData.length > 0 && !isBackground) {
          // Fetch events in background without blocking UI
          Promise.all(
            runsData.slice(0, 10).map((run) =>
              fetchRunDetail(run.run_id, null, token)
                .then((detail) => detail.events)
                .catch(() => [])
            )
          )
            .then((eventsArrays) => {
              const flatEvents = eventsArrays.flat();
              console.log(
                `[Dashboard] Fetched ${flatEvents.length} events from ${runsData.length} runs`
              );
              setAllEvents(flatEvents);
            })
            .catch((err) => {
              console.warn(
                "[Dashboard] Failed to fetch some run details:",
                err
              );
              // Don't set error, just log - dashboard still works without events
            });
        } else {
          setAllEvents([]);
        }
      } catch (err) {
        console.error("[Dashboard] Error loading data:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
        // Set empty data so dashboard still shows
        setRuns([]);
        setProviderStats([]);
        setAllEvents([]);
      } finally {
        // Always set loading to false, even on error
        if (!isBackground) {
          setLoading(false);
        }
      }
    }

    loadData();

    // Refresh every 30 seconds
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [isLoaded, user, selectedCustomer, getToken]);

  // Filter events by customer if selected
  const filteredEvents = selectedCustomer
    ? allEvents.filter((e) => e.customer_id === selectedCustomer)
    : allEvents;

  // Filter provider stats by customer and exclude "internal" provider
  // Calculate this FIRST before stats to avoid circular dependency
  const filteredProviderStats = (() => {
    const realStats = (
      selectedCustomer
        ? providerStats
            .filter((stat) => {
              // Recalculate from filtered events
              const customerEvents = filteredEvents.filter(
                (e) => e.provider === stat.provider
              );
              return customerEvents.length > 0;
            })
            .map((stat) => {
              // Recalculate from filtered events
              const customerEvents = filteredEvents.filter(
                (e) => e.provider === stat.provider
              );
              const totalCost = customerEvents.reduce(
                (sum, e) => sum + (e.cost_usd || 0),
                0
              );
              const callCount = customerEvents.length;
              return {
                ...stat,
                total_cost: totalCost,
                call_count: callCount,
                // Percentage will be calculated after total_cost_24h is known
                percentage: 0,
              };
            })
        : providerStats
    ).filter(
      (stat) => stat.provider !== "internal" && stat.provider !== "unknown"
    ); // Hide "unknown" provider

    // Return empty array if no real data - NO FAKE DATA
    return realStats;
  })();

  // Calculate total cost from filtered provider stats (needed for percentage calculation)
  const total_cost_24h_from_providers = filteredProviderStats.reduce(
    (sum, stat) => sum + (stat.total_cost || 0),
    0
  );

  // Update percentages in filteredProviderStats now that we have total
  filteredProviderStats.forEach((stat) => {
    stat.percentage =
      total_cost_24h_from_providers > 0
        ? (stat.total_cost / total_cost_24h_from_providers) * 100
        : 0;
  });

  // Calculate semantic cost breakdown (outside stats function so it's accessible)
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const recentEvents = filteredEvents.filter((e) => {
    const eventDate = new Date(e.created_at);
    return eventDate >= yesterday;
  });

  const semanticCosts = new Map<string, { cost: number; calls: number }>();
  recentEvents.forEach((event) => {
    const semanticLabel = event.semantic_label;
    if (semanticLabel) {
      const existing = semanticCosts.get(semanticLabel) || {
        cost: 0,
        calls: 0,
      };
      existing.cost += event.cost_usd || 0;
      existing.calls += 1;
      semanticCosts.set(semanticLabel, existing);
    }
  });

  // Calculate model breakdown
  const modelCosts = new Map<string, { cost: number; calls: number; provider: string }>();
  recentEvents.forEach((event) => {
    const model = event.model || 'unknown';
    const provider = event.provider || 'unknown';
    if (model && model !== 'unknown') {
      const existing = modelCosts.get(model) || { cost: 0, calls: 0, provider };
      existing.cost += event.cost_usd || 0;
      existing.calls += 1;
      modelCosts.set(model, existing);
    }
  });

  // Use model stats from API (more reliable than calculating from limited events)
  const sortedModelCosts = modelStats
    .map((stat) => ({
      model: stat.model,
      cost: stat.total_cost,
      calls: stat.call_count,
      provider: stat.provider,
      percentage: stat.percentage,
    }))
    .slice(0, 10); // Top 10 models

  // Sort semantic costs by cost descending
  const sortedSemanticCosts = Array.from(semanticCosts.entries())
    .map(([label, stats]) => ({
      label,
      cost: stats.cost,
      calls: stats.calls,
      percentage:
        total_cost_24h_from_providers > 0
          ? (stats.cost / total_cost_24h_from_providers) * 100
          : 0,
    }))
    .sort((a, b) => b.cost - a.cost);

  // Calculate stats from provider stats (more accurate than events)
  const stats = (() => {
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    // Use provider stats for total cost (24h window from backend)
    const total_cost = total_cost_24h_from_providers;
    const total_calls = filteredProviderStats.reduce(
      (sum, stat) => sum + (stat.call_count || 0),
      0
    );

    const weekEvents = filteredEvents.filter((e) => {
      const eventDate = new Date(e.created_at);
      return eventDate >= weekAgo && eventDate < yesterday;
    });

    // Separate agent vs untracked costs
    const agentEvents = recentEvents.filter(
      (e) =>
        e.section?.startsWith("agent:") || e.section_path?.startsWith("agent:")
    );
    const untrackedEvents = recentEvents.filter(
      (e) =>
        !e.section?.startsWith("agent:") &&
        !e.section_path?.startsWith("agent:")
    );

    const agent_cost = agentEvents.reduce(
      (sum, e) => sum + (e.cost_usd || 0),
      0
    );
    const untracked_cost = untrackedEvents.reduce(
      (sum, e) => sum + (e.cost_usd || 0),
      0
    );
    const week_cost =
      weekEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0) / 7;

    // Get unique run IDs from ALL events (not just filtered by customer)
    // This ensures total_runs shows all runs, not just customer-filtered ones
    const allRecentEvents = allEvents.filter((e) => {
      const eventDate = new Date(e.created_at);
      return eventDate >= yesterday;
    });
    const uniqueRuns = new Set(allRecentEvents.map((e) => e.run_id));

    // Calculate untracked percentage
    const untracked_percentage =
      total_cost > 0 ? (untracked_cost / total_cost) * 100 : 0;

    return {
      total_cost_24h: total_cost,
      agent_cost_24h: agent_cost,
      untracked_cost_24h: untracked_cost,
      untracked_calls_24h: untrackedEvents.length,
      untracked_percentage,
      total_calls_24h: total_calls,
      avg_cost_per_call: total_calls > 0 ? total_cost / total_calls : 0,
      total_runs: uniqueRuns.size,
      cost_change:
        week_cost > 0 ? ((total_cost - week_cost) / week_cost) * 100 : 0,
    };
  })();

  // Prepare daily chart data from API (more reliable than calculating from limited events)
  const dailyChartData = dailyStats.map((day) => {
    const providerCosts: Record<string, number> = {};
    Object.entries(day.providers).forEach(([provider, data]) => {
      providerCosts[provider.toLowerCase()] = data.cost;
    });
    return {
      date: new Date(day.date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      value: day.total,
      ...providerCosts,
    };
  });

  // Calculate 7-day sparklines for each provider
  const providerSparklines = new Map<string, number[]>();
  filteredProviderStats.forEach((stat) => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split("T")[0];
    });

    const sparklineData = last7Days.map((date) => {
      const dayEvents = filteredEvents.filter((e) => {
        const eventDate = new Date(e.created_at).toISOString().split("T")[0];
        return eventDate === date && e.provider === stat.provider;
      });
      return dayEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);
    });

    providerSparklines.set(stat.provider, sparklineData);
  });

  if (error) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
            <p className="text-sm text-muted-foreground mt-2">
              Make sure the collector API is running on{" "}
              {process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
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
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6 -mt-4">
        {/* Main Hero Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-3">
            <div className="flex items-center justify-end gap-3 mb-4">
              <DateRangeFilter value={dateRange} onChange={setDateRange} />
            </div>
            <MainMetricChart
              data={dailyChartData}
              title="Total Cost (24h)"
              metric="Cost"
              metricValue={formatCost(stats.total_cost_24h)}
              providerStats={providerStats.map(p => ({
                provider: p.provider,
                total_cost: p.total_cost,
                percentage: calculatePercentage(p.total_cost, stats.total_cost_24h)
              }))}
            />
          </div>
        </div>

        {/* Secondary Metrics Grid */}
        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-1">API Calls</p>
                <h3 className="text-2xl font-bold">
                  {stats.total_calls_24h.toLocaleString()}
                </h3>
              </div>
              <div className="hidden md:block w-px bg-gray-200"></div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-1">
                  Avg Cost/Call
                </p>
                <h3 className="text-2xl font-bold">
                  {formatCost(stats.avg_cost_per_call)}
                </h3>
              </div>
              <div className="hidden md:block w-px bg-gray-200"></div>
              <div className="flex-1">
                <p className="text-sm text-muted-foreground mb-1">Total Runs</p>
                <h3 className="text-2xl font-bold">{stats.total_runs}</h3>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Semantic Cost Breakdown */}
        {sortedSemanticCosts.length > 0 && (
          <Card className="border-0 shadow-sm bg-white">
            <CardContent className="pt-6">
              <h3 className="text-lg font-semibold mb-4">
                Semantic Cost Breakdown
              </h3>
              <div className="rounded-lg border border-gray-100 bg-white overflow-hidden">
                <Table>
                  <TableHeader className="bg-gray-50/50">
                    <TableRow className="border-gray-100 hover:bg-transparent">
                      <TableHead className="font-medium text-gray-500">
                        Semantic Section
                      </TableHead>
                      <TableHead className="text-right font-medium text-gray-500">
                        Cost
                      </TableHead>
                      <TableHead className="text-right font-medium text-gray-500">
                        %
                      </TableHead>
                      <TableHead className="text-right font-medium text-gray-500">
                        Calls
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sortedSemanticCosts.map((semantic) => (
                      <TableRow
                        key={semantic.label}
                        className="border-gray-50 hover:bg-gray-50/50"
                      >
                        <TableCell className="font-medium text-gray-900">
                          {semantic.label}
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {formatCost(semantic.cost)}
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {semantic.percentage.toFixed(1)}%
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {semantic.calls.toLocaleString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Provider Breakdown Table */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Provider Breakdown</h3>
            <div className="rounded-lg border border-gray-100 bg-white overflow-hidden">
              <Table>
                <TableHeader className="bg-gray-50/50">
                  <TableRow className="border-gray-100 hover:bg-transparent">
                    <TableHead className="font-medium text-gray-500">
                      Provider
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      Cost
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      %
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      Trend
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProviderStats.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={4}
                        className="text-center py-8 text-muted-foreground"
                      >
                        No data
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredProviderStats.map((provider) => {
                      const percentage =
                        provider.percentage !== undefined
                          ? provider.percentage
                          : stats.total_cost_24h > 0
                          ? calculatePercentage(
                              provider.total_cost,
                              stats.total_cost_24h
                            )
                          : 0;
                      const sparklineData =
                        providerSparklines.get(provider.provider) || [];

                      return (
                        <TableRow
                          key={provider.provider}
                          className="border-gray-50 hover:bg-gray-50/50"
                        >
                          <TableCell className="font-medium text-gray-900 capitalize">
                            {provider.provider}
                          </TableCell>
                          <TableCell className="text-right text-gray-600">
                            {formatCost(provider.total_cost)}
                          </TableCell>
                          <TableCell className="text-right text-gray-600">
                            {percentage.toFixed(1)}%
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end">
                              <Sparkline
                                data={sparklineData}
                                color="#10b981"
                                width={60}
                                height={20}
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
          </div>

          {/* Model Breakdown Table */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Model Breakdown</h3>
            <div className="rounded-lg border border-gray-100 bg-white overflow-hidden">
              <Table>
                <TableHeader className="bg-gray-50/50">
                  <TableRow className="border-gray-100 hover:bg-transparent">
                    <TableHead className="font-medium text-gray-500">
                      Model
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      Calls
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      Cost
                    </TableHead>
                    <TableHead className="text-right font-medium text-gray-500">
                      %
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedModelCosts.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={4}
                        className="text-center py-8 text-muted-foreground"
                      >
                        No model data
                      </TableCell>
                    </TableRow>
                  ) : (
                    sortedModelCosts.map((model) => (
                      <TableRow
                        key={model.model}
                        className="border-gray-50 hover:bg-gray-50/50"
                      >
                        <TableCell className="font-medium text-gray-900">
                          <div className="flex flex-col">
                            <span className="text-sm">{model.model}</span>
                            <span className="text-xs text-gray-400 capitalize">{model.provider}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {model.calls}
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {formatCost(model.cost)}
                        </TableCell>
                        <TableCell className="text-right text-gray-600">
                          {model.percentage.toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="p-6">
          <Skeleton className="h-96 w-full" />
        </div>
      }
    >
      <DashboardPageContent />
    </Suspense>
  );
}
