"use client";

import { useEffect, useState, useMemo, Suspense } from "react";
import { useRouter } from "next/navigation";
import { useUser, useAuth } from "@clerk/nextjs";
import { Skeleton } from "@/components/ui/skeleton";
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
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { KPICards } from "@/components/dashboard/KPICards";
import { CostTrendChart } from "@/components/dashboard/CostTrendChart";
import { ProviderBreakdown } from "@/components/dashboard/ProviderBreakdown";
import { ModelBreakdown } from "@/components/dashboard/ModelBreakdown";
import { useDateRange } from "@/contexts/DateRangeContext";
import { DateRangeFilter } from "@/components/DateRangeFilter";
import { cn } from "@/lib/utils";
import { formatSmartCost } from "@/lib/format";

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
  const [userType, setUserType] = useState<"solo_dev" | "saas_founder" | null>(null);

  useEffect(() => {
    if (!isLoaded) return;
    if (!user) {
      setLoading(false);
      setError("Not authenticated. Please sign in.");
      return;
    }

    async function loadData(isBackground = false) {
      if (!isBackground) setLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (token && typeof window !== "undefined") {
          (window as any).__clerkToken = token;
        }

        if (!token) {
          throw new Error("Not authenticated. Please sign in again.");
        }

        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

        const [userResponse, runsData, providersData, modelsData, dailyData] = await Promise.all([
          fetch(`${collectorUrl}/clerk/api-keys/me`, {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }).catch(() => ({ ok: false, json: async () => ({}) })),
          fetchRuns(50, null, token).catch(() => []),
          fetchProviderStats(24, null, token).catch(() => []),
          fetchModelStats(24, null, token).catch(() => []),
          fetchDailyStats(7, null, token).catch(() => []),
        ]);

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

        setRuns(runsData || []);
        setProviderStats(providersData || []);
        setModelStats(modelsData || []);
        setDailyStats(dailyData || []);

        if (!isBackground) setLoading(false);

        // Fetch events in background
        if (runsData && runsData.length > 0 && !isBackground) {
          Promise.all(
            runsData.slice(0, 10).map((run) =>
              fetchRunDetail(run.run_id, null, token).then((detail) => detail.events).catch(() => [])
            )
          )
            .then((eventsArrays) => setAllEvents(eventsArrays.flat()))
            .catch(() => {});
        } else {
          setAllEvents([]);
        }
      } catch (err) {
        console.error("[Dashboard] Error loading data:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
        setRuns([]);
        setProviderStats([]);
        setAllEvents([]);
      } finally {
        if (!isBackground) setLoading(false);
      }
    }

    loadData();
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [isLoaded, user, selectedCustomer, getToken]);

  // Filter out internal/unknown providers
  const filteredProviderStats = useMemo(() => {
    return providerStats.filter(
      (stat) => stat.provider !== "internal" && stat.provider !== "unknown"
    );
  }, [providerStats]);

  // Calculate aggregated stats
  const stats = useMemo(() => {
    const totalCost24h = filteredProviderStats.reduce((sum, stat) => sum + (stat.total_cost || 0), 0);
    const totalCalls24h = filteredProviderStats.reduce((sum, stat) => sum + (stat.call_count || 0), 0);
    
    // Calculate week cost from daily stats
    const weekCost = dailyStats.reduce((sum, day) => sum + (day.total || 0), 0);
    
    // Estimate month cost (assuming week data represents typical week)
    const monthCost = weekCost * 4.33;
    
    // Yesterday's cost (second to last day in daily stats)
    const yesterdayCost = dailyStats.length >= 2 ? dailyStats[dailyStats.length - 2]?.total || 0 : 0;
    
    return {
      totalCost24h,
      totalCalls24h,
      weekCost,
      monthCost,
      yesterdayCost,
      avgCostPerCall: totalCalls24h > 0 ? totalCost24h / totalCalls24h : 0,
    };
  }, [filteredProviderStats, dailyStats]);

  // Prepare chart data from daily stats
  const chartData = useMemo(() => {
    return dailyStats.map((day) => {
      const providerCosts: Record<string, number> = {};
      if (day.providers && typeof day.providers === 'object') {
        Object.entries(day.providers).forEach(([provider, data]) => {
          providerCosts[provider.toLowerCase()] = data.cost;
        });
      }
      return {
        date: new Date(day.date).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        }),
        value: day.total || 0,
        ...providerCosts,
      };
    });
  }, [dailyStats]);

  // Prepare model data with percentage
  const modelData = useMemo(() => {
    return modelStats.map((stat) => ({
      ...stat,
      percentage: stats.totalCost24h > 0 ? (stat.total_cost / stats.totalCost24h) * 100 : 0,
    }));
  }, [modelStats, stats.totalCost24h]);

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6">
          <p className="text-rose-700 font-medium">{error}</p>
          <p className="text-sm text-rose-600 mt-2">
            Make sure the collector API is running on{" "}
            {process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000"}
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-56 rounded-xl" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-64 rounded-xl" />
            <Skeleton className="h-64 rounded-xl" />
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6 -mt-2">
        {/* Header with date filter */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Cost Overview</h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Track and optimize your LLM spending
            </p>
          </div>
          <DateRangeFilter value={dateRange} onChange={setDateRange} />
        </div>

        {/* KPI Cards - Primary hierarchy level */}
        <KPICards
          todayCost={stats.totalCost24h}
          weekCost={stats.weekCost}
          monthCost={stats.monthCost}
          previousPeriodCost={stats.yesterdayCost}
          totalCalls={stats.totalCalls24h}
        />

        {/* Trend Chart - Shows "is spend accelerating?" */}
        <div className="bg-white rounded-xl border border-slate-200/60 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Spend Trend</h3>
              <p className="text-xs text-slate-500 mt-0.5">Last 7 days</p>
            </div>
            {/* Quick insight */}
            {chartData.length > 1 && (
              <div className="text-xs text-slate-500">
                Avg: <span className="font-medium text-slate-700">
                  {formatSmartCost(stats.weekCost / 7)}/day
                </span>
              </div>
            )}
          </div>
          <CostTrendChart data={chartData} height={200} />
        </div>

        {/* Two-column layout: Provider + Model breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Provider Breakdown */}
          <ProviderBreakdown
            providers={filteredProviderStats}
            totalCost={stats.totalCost24h}
          />

          {/* Model Breakdown */}
          <ModelBreakdown
            models={modelData}
            totalCost={stats.totalCost24h}
          />
        </div>

        {/* Diagnostics footer */}
        <div className="bg-slate-50 rounded-xl p-4">
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-slate-500">Avg Cost/Call:</span>
              <span className="ml-2 font-medium text-slate-700">
                {formatSmartCost(stats.avgCostPerCall)}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Total Runs:</span>
              <span className="ml-2 font-medium text-slate-700">
                {runs.length}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Active Providers:</span>
              <span className="ml-2 font-medium text-slate-700">
                {filteredProviderStats.length}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Active Models:</span>
              <span className="ml-2 font-medium text-slate-700">
                {modelStats.length}
              </span>
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
