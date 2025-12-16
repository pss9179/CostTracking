"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser, useAuth } from "@clerk/nextjs";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  fetchRuns,
  fetchProviderStats,
  fetchModelStats,
  fetchDailyStats,
  type Run,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
} from "@/lib/api";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { CostTrendChart } from "@/components/dashboard/CostTrendChart";
import { ProviderBreakdown } from "@/components/dashboard/ProviderBreakdown";
import { ModelBreakdown } from "@/components/dashboard/ModelBreakdown";
import { AnalyticsHeader } from "@/components/analytics/AnalyticsHeader";
import { MetricCard, MetricCardRow } from "@/components/analytics/MetricCard";
import { StackedBarChart } from "@/components/analytics/CostDistributionChart";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatCompactNumber,
  formatPercentChange,
  getStableColor,
} from "@/lib/format";
import type { DateRange } from "@/contexts/AnalyticsContext";

// ============================================================================
// TYPES
// ============================================================================

interface DashboardStats {
  totalCost24h: number;
  totalCalls24h: number;
  weekCost: number;
  monthCost: number;
  yesterdayCost: number;
  avgCostPerCall: number;
  topProvider: string | null;
  topModel: string | null;
}

// ============================================================================
// HOOKS
// ============================================================================

function useDashboardData(dateRange: DateRange) {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  
  const [runs, setRuns] = useState<Run[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Convert date range to hours/days
  const hours = useMemo(() => {
    switch (dateRange) {
      case "24h": return 24;
      case "7d": return 7 * 24;
      case "30d": return 30 * 24;
      case "90d": return 90 * 24;
    }
  }, [dateRange]);
  
  const days = useMemo(() => Math.ceil(hours / 24), [hours]);
  
  const loadData = useCallback(async (isBackground = false) => {
    if (!isLoaded || !user) return;
    
    if (!isBackground) setLoading(true);
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated. Please sign in again.");
      
      const [runsData, providersData, modelsData, dailyData] = await Promise.all([
        fetchRuns(50, null, token).catch(() => []),
        fetchProviderStats(hours, null, token).catch(() => []),
        fetchModelStats(hours, null, token).catch(() => []),
        fetchDailyStats(days, null, token).catch(() => []),
      ]);
      
      setRuns(runsData || []);
      setProviderStats(providersData || []);
      setModelStats(modelsData || []);
      setDailyStats(dailyData || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("[Dashboard] Error loading data:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, [isLoaded, user, getToken, hours, days]);
  
  // Initial load
  useEffect(() => {
    if (isLoaded && user) {
      loadData();
    }
  }, [isLoaded, user, loadData]);
  
  // Auto-refresh every 30s
  useEffect(() => {
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [loadData]);
  
  return {
    runs,
    providerStats,
    modelStats,
    dailyStats,
    loading,
    error,
    lastRefresh,
    refresh: () => loadData(false),
  };
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

function DashboardPageContent() {
  const searchParams = useSearchParams();
  const [dateRange, setDateRange] = useState<DateRange>(
    (searchParams.get('range') as DateRange) || "7d"
  );
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  
  const {
    runs,
    providerStats,
    modelStats,
    dailyStats,
    loading,
    error,
    lastRefresh,
    refresh,
  } = useDashboardData(dateRange);
  
  // Filter out internal/unknown providers
  const filteredProviderStats = useMemo(() => {
    let filtered = providerStats.filter(
      (stat) => stat.provider !== "internal" && stat.provider !== "unknown"
    );
    
    // Apply provider filter
    if (selectedProviders.length > 0) {
      filtered = filtered.filter(stat => 
        selectedProviders.includes(stat.provider.toLowerCase())
      );
    }
    
    return filtered;
  }, [providerStats, selectedProviders]);
  
  // Filter models
  const filteredModelStats = useMemo(() => {
    let filtered = [...modelStats];
    
    // Apply model filter
    if (selectedModels.length > 0) {
      filtered = filtered.filter(stat =>
        selectedModels.includes(stat.model)
      );
    }
    
    // Apply provider filter
    if (selectedProviders.length > 0) {
      filtered = filtered.filter(stat =>
        selectedProviders.includes(stat.provider.toLowerCase())
      );
    }
    
    return filtered;
  }, [modelStats, selectedProviders, selectedModels]);
  
  // Calculate aggregated stats
  const stats = useMemo<DashboardStats>(() => {
    const totalCost = filteredProviderStats.reduce((sum, stat) => sum + (stat.total_cost || 0), 0);
    const totalCalls = filteredProviderStats.reduce((sum, stat) => sum + (stat.call_count || 0), 0);
    
    // Week cost from daily stats
    const weekCost = dailyStats.slice(-7).reduce((sum, day) => sum + (day.total || 0), 0);
    
    // Month estimate
    const monthCost = dailyStats.reduce((sum, day) => sum + (day.total || 0), 0);
    
    // Yesterday's cost
    const yesterdayCost = dailyStats.length >= 2 
      ? dailyStats[dailyStats.length - 2]?.total || 0 
      : 0;
    
    // Top provider
    const sortedProviders = [...filteredProviderStats].sort((a, b) => b.total_cost - a.total_cost);
    const topProvider = sortedProviders[0]?.provider || null;
    
    // Top model
    const sortedModels = [...filteredModelStats].sort((a, b) => b.total_cost - a.total_cost);
    const topModel = sortedModels[0]?.model || null;
    
    return {
      totalCost24h: totalCost,
      totalCalls24h: totalCalls,
      weekCost,
      monthCost,
      yesterdayCost,
      avgCostPerCall: totalCalls > 0 ? totalCost / totalCalls : 0,
      topProvider,
      topModel,
    };
  }, [filteredProviderStats, filteredModelStats, dailyStats]);
  
  // Prepare chart data
  const chartData = useMemo(() => {
    return dailyStats.map((day) => {
      const providerCosts: Record<string, number> = {};
      if (day.providers && typeof day.providers === 'object') {
        Object.entries(day.providers).forEach(([provider, data]) => {
          // Skip filtered out providers
          if (selectedProviders.length > 0 && !selectedProviders.includes(provider.toLowerCase())) {
            return;
          }
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
  }, [dailyStats, selectedProviders]);
  
  // Available filters
  const availableProviders = useMemo(() => 
    [...new Set(providerStats.map(p => p.provider.toLowerCase()))]
      .filter(p => p !== 'internal' && p !== 'unknown'),
    [providerStats]
  );
  
  const availableModels = useMemo(() =>
    [...new Set(modelStats.map(m => m.model))],
    [modelStats]
  );
  
  // Cost distribution data for stacked bar
  const costDistributionData = useMemo(() => 
    filteredProviderStats.map(p => ({
      name: p.provider,
      cost: p.total_cost,
      calls: p.call_count,
    })),
    [filteredProviderStats]
  );
  
  // Has active filters
  const hasActiveFilters = selectedProviders.length > 0 || selectedModels.length > 0;
  
  // Error state
  if (error) {
    return (
      <ProtectedLayout>
        <div className="p-8">
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-rose-700 font-medium">{error}</p>
              <p className="text-sm text-rose-600 mt-1">
                Check that the collector API is running and accessible.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={refresh}
                className="mt-3 text-rose-600 border-rose-200 hover:bg-rose-100"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-8 w-32" />
          </div>
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
        {/* Header with filters */}
        <AnalyticsHeader
          title="Cost Overview"
          subtitle="Track and optimize your LLM spending"
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          providers={selectedProviders}
          availableProviders={availableProviders}
          onProvidersChange={setSelectedProviders}
          models={selectedModels}
          availableModels={availableModels}
          onModelsChange={setSelectedModels}
          hasActiveFilters={hasActiveFilters}
          onReset={() => {
            setSelectedProviders([]);
            setSelectedModels([]);
          }}
        />
        
        {/* Empty state for new users */}
        {stats.totalCost24h === 0 && stats.weekCost === 0 && stats.monthCost === 0 && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-8 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🚀</span>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                Start tracking your LLM costs
              </h3>
              <p className="text-slate-600 mb-6">
                Add 2 lines of code to your app and see costs appear here automatically.
              </p>
              <div className="bg-slate-900 rounded-lg p-4 text-left font-mono text-sm text-slate-300 mb-6">
                <div><span className="text-purple-400">import</span> llmobserve</div>
                <div className="mt-1">llmobserve.<span className="text-blue-400">observe</span>(api_key=<span className="text-green-400">"your-key"</span>)</div>
              </div>
              <div className="flex gap-3 justify-center">
                <a
                  href="/settings"
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
                >
                  Get your API key
                </a>
                <a
                  href="/api-docs"
                  className="px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 font-medium rounded-lg border border-slate-200 transition-colors"
                >
                  View docs
                </a>
              </div>
            </div>
          </div>
        )}
        
        {/* KPI Cards */}
        <MetricCardRow columns={4}>
          <MetricCard
            title="Today"
            value={stats.totalCost24h}
            previousValue={stats.yesterdayCost}
            deltaLabel="vs yesterday"
            variant="primary"
            icon={<span className="text-emerald-400">$</span>}
          />
          <MetricCard
            title="This Week"
            value={stats.weekCost}
          />
          <MetricCard
            title="This Month"
            value={stats.monthCost}
          />
          <MetricCard
            title="API Calls"
            value={formatCompactNumber(stats.totalCalls24h)}
            formatValue={() => formatCompactNumber(stats.totalCalls24h)}
            tooltipContent={
              <div>
                <p className="font-medium">Total API Calls</p>
                <p className="text-slate-300 tabular-nums">{stats.totalCalls24h.toLocaleString()}</p>
              </div>
            }
          />
        </MetricCardRow>
        
        {/* Spend Distribution (stacked bar) */}
        {costDistributionData.length > 0 && (
          <div className="bg-white rounded-xl border border-slate-200/60 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Spend Distribution</h3>
                <p className="text-xs text-slate-500 mt-0.5">By provider</p>
              </div>
              {stats.topProvider && (
                <div className="text-xs text-slate-500">
                  Top: <span className="font-medium text-slate-700 capitalize">{stats.topProvider}</span>
                </div>
              )}
            </div>
            <StackedBarChart
              data={costDistributionData}
              totalCost={stats.totalCost24h}
              topN={6}
              height={16}
              onClick={(item) => {
                setSelectedProviders([item.name.toLowerCase()]);
              }}
            />
            {/* Legend */}
            <div className="flex flex-wrap gap-3 mt-3">
              {costDistributionData.slice(0, 6).map((item) => (
                <button
                  key={item.name}
                  onClick={() => setSelectedProviders([item.name.toLowerCase()])}
                  className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors"
                >
                  <div 
                    className="w-2.5 h-2.5 rounded-full" 
                    style={{ backgroundColor: getStableColor(item.name) }}
                  />
                  <span className="capitalize">{item.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Spend Trend Chart */}
        <div className="bg-white rounded-xl border border-slate-200/60 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Spend Trend</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {dateRange === "24h" ? "Hourly" : "Daily"} spend over time
              </p>
            </div>
            {chartData.length > 1 && (
              <div className="text-xs text-slate-500">
                Avg: <span className="font-medium text-slate-700">
                  {formatSmartCost(stats.weekCost / Math.max(chartData.length, 1))}/day
                </span>
              </div>
            )}
          </div>
          
          {chartData.length === 0 ? (
            <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
              No data for this period
            </div>
          ) : (
            <CostTrendChart data={chartData} height={200} />
          )}
        </div>
        
        {/* Two-column: Provider + Model breakdowns */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ProviderBreakdown
            providers={filteredProviderStats}
            totalCost={stats.totalCost24h}
          />
          <ModelBreakdown
            models={filteredModelStats.map(m => ({
              ...m,
              percentage: stats.totalCost24h > 0 ? (m.total_cost / stats.totalCost24h) * 100 : 0,
            }))}
            totalCost={stats.totalCost24h}
          />
        </div>
        
        {/* Footer insights */}
        <div className="bg-slate-50 rounded-xl p-4">
          <div className="flex flex-wrap gap-6 text-sm">
            <div>
              <span className="text-slate-500">Avg Cost/Call:</span>
              <span className="ml-2 font-medium text-slate-700">
                {formatSmartCost(stats.avgCostPerCall)}
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
                {filteredModelStats.length}
              </span>
            </div>
            <div className="ml-auto text-xs text-slate-400">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}

// ============================================================================
// PAGE EXPORT
// ============================================================================

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <ProtectedLayout>
          <div className="space-y-6">
            <Skeleton className="h-10 w-48" />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-24 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-56 rounded-xl" />
          </div>
        </ProtectedLayout>
      }
    >
      <DashboardPageContent />
    </Suspense>
  );
}
