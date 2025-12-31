"use client";

import { useEffect, useState, useMemo, useCallback, Suspense, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser, useAuth } from "@clerk/nextjs";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  fetchRuns,
  fetchProviderStats,
  fetchModelStats,
  fetchTimeseries,
  fetchDailyStats,
  type Run,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
} from "@/lib/api";
import { getCached, setCached, getCachedWithMeta } from "@/lib/cache";
import { mark, measure, logCacheStatus, logAuth } from "@/lib/perf";
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

// Dashboard cache data shape
interface DashboardCacheData {
  runs: Run[];
  providerStats: ProviderStats[];
  modelStats: ModelStats[];
  dailyStats: DailyStats[];
  prevProviderStats: ProviderStats[];
  prevDailyStats: DailyStats[];
}

function useDashboardData(dateRange: DateRange, compareEnabled: boolean = false) {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  const cacheKey = `dashboard-${dateRange}-${compareEnabled}`;
  
  // SYNC CACHE INIT: Read cache BEFORE first paint (in useState initializers)
  // This eliminates flicker on tab navigation
  const initialCache = typeof window !== 'undefined' 
    ? getCached<DashboardCacheData>(cacheKey) 
    : null;
  const hasValidCache = !!(initialCache?.providerStats?.length);
  
  // Refs to track state across renders without causing re-renders
  const fetchInProgressRef = useRef(false);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const hasLoadedRef = useRef(hasValidCache); // Init from cache
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevCacheKeyRef = useRef(cacheKey); // Track cache key changes
  
  // State - initialized from cache synchronously
  const [runs, setRuns] = useState<Run[]>(() => initialCache?.runs ?? []);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>(() => initialCache?.providerStats ?? []);
  const [modelStats, setModelStats] = useState<ModelStats[]>(() => initialCache?.modelStats ?? []);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>(() => initialCache?.dailyStats ?? []);
  const [dailyAggregates, setDailyAggregates] = useState<DailyStats[]>(() => initialCache?.dailyStats ?? []);
  const [prevProviderStats, setPrevProviderStats] = useState<ProviderStats[]>(() => initialCache?.prevProviderStats ?? []);
  const [prevDailyStats, setPrevDailyStats] = useState<DailyStats[]>(() => initialCache?.prevDailyStats ?? []);
  const [loading, setLoading] = useState(!hasValidCache); // False if cache exists
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Convert date range to hours/days
  const hours = useMemo(() => {
    switch (dateRange) {
      case "1h": return 1;
      case "6h": return 6;
      case "24h": return 24;
      case "3d": return 3 * 24;
      case "7d": return 7 * 24;
      case "14d": return 14 * 24;
      case "30d": return 30 * 24;
      case "90d": return 90 * 24;
      case "180d": return 180 * 24;
      case "365d": return 365 * 24;
      default: return 7 * 24;
    }
  }, [dateRange]);
  
  const days = useMemo(() => Math.ceil(hours / 24), [hours]);
  
  // Handle cacheKey CHANGES only (not initial mount - that's handled by useState)
  useEffect(() => {
    // Skip on initial mount - already initialized via useState
    if (prevCacheKeyRef.current === cacheKey && hasLoadedRef.current) {
      return;
    }
    prevCacheKeyRef.current = cacheKey;
    
    const cached = getCached<DashboardCacheData>(cacheKey);
    logCacheStatus('Dashboard', cacheKey, !!cached, !cached);
    
    if (cached?.providerStats) {
      if (!mountedRef.current) return;
      setRuns(cached.runs || []);
      setProviderStats(cached.providerStats || []);
      setModelStats(cached.modelStats || []);
      setDailyStats(cached.dailyStats || []);
      setDailyAggregates(cached.dailyStats || []);
      setPrevProviderStats(cached.prevProviderStats || []);
      setPrevDailyStats(cached.prevDailyStats || []);
      if (cached.providerStats.length > 0) {
        hasLoadedRef.current = true;
        setLoading(false);
      }
    }
    // NEVER clear state on cache miss - keep existing data
  }, [cacheKey]);
  
  // The fetch function
  const loadData = useCallback(async (isBackground = false): Promise<boolean> => {
    mark('dashboard-loadData');
    
    // CRITICAL: Never fetch without auth
    logAuth('Dashboard', isLoaded, isSignedIn, !!user);
    if (!isLoaded) {
      return false;
    }
    
    if (!isSignedIn || !user) {
      if (!mountedRef.current) return false;
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
    measure('dashboard-auth-ready', 'dashboard-loadData');
    
    // Prevent duplicate fetches
    if (fetchInProgressRef.current) {
      return false;
    }
    
    // Check if cache is fresh for background refreshes
    const cache = getCachedWithMeta<DashboardCacheData>(cacheKey);
    logCacheStatus('Dashboard', cacheKey, cache.exists, cache.isStale);
    if (isBackground && cache.exists && !cache.isStale) {
      return false;
    }
    
    fetchInProgressRef.current = true;
    
    // B) FIX: Only set loading if we haven't loaded yet
    // D) FIX: Background refresh NEVER sets loading
    if (!isBackground && !hasLoadedRef.current) {
      if (mountedRef.current) setLoading(true);
    } else if (!isBackground) {
      if (mountedRef.current) setIsRefreshing(true);
    }
    
    try {
      mark('dashboard-getToken');
      const token = await getToken();
      measure('dashboard-getToken');
      
      // C) FIX: Token retry - don't touch loading in finally if retry scheduled
      if (!token) {
        fetchInProgressRef.current = false;
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) loadData(isBackground);
        }, 500);
        return false; // Return early - don't hit finally's loading reset
      }
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      
      mark('dashboard-fetch');
      const [runsData, providersData, modelsData, timeseriesData, dailyData] = await Promise.all([
        fetchRuns(50, null, token).catch(() => []),
        fetchProviderStats(hours, null, null, token).catch(() => []),
        fetchModelStats(hours, null, null, token).catch(() => []),
        fetchTimeseries(hours, null, null, token).catch(() => []),
        fetchDailyStats(days, null, token).catch(() => []),
      ]);
      measure('dashboard-fetch');
      
      let prevProvidersData: ProviderStats[] = [];
      let prevDailyOnly: DailyStats[] = [];
      
      if (compareEnabled) {
        const prevHours = hours * 2;
        const [prevProviders, , prevDaily] = await Promise.all([
          fetchProviderStats(prevHours, null, null, token).catch(() => []),
          fetchModelStats(prevHours, null, null, token).catch(() => []),
          fetchTimeseries(prevHours, null, null, token).catch(() => []),
        ]);
        
        const halfwayPoint = Math.floor((prevDaily || []).length / 2);
        prevProvidersData = prevProviders || [];
        prevDailyOnly = (prevDaily || []).slice(0, halfwayPoint);
      }
      
      // E) FIX: Check mounted before setState
      if (!mountedRef.current) return false;
      
      setRuns(runsData || []);
      setProviderStats(providersData || []);
      setModelStats(modelsData || []);
      setDailyStats(timeseriesData || []);
      setDailyAggregates(dailyData || []);
      setPrevProviderStats(prevProvidersData);
      setPrevDailyStats(prevDailyOnly);
      setLastRefresh(new Date());
      setError(null);
      
      // B) FIX: Lock loading after first success
      hasLoadedRef.current = true;
      setLoading(false);
      setIsRefreshing(false);
      
      setCached<DashboardCacheData>(cacheKey, {
        runs: runsData || [],
        providerStats: providersData || [],
        modelStats: modelsData || [],
        dailyStats: timeseriesData || [],
        prevProviderStats: prevProvidersData,
        prevDailyStats: prevDailyOnly,
      });
      
      fetchInProgressRef.current = false;
      return true;
    } catch (err) {
      console.error("[Dashboard] Error loading data:", err);
      if (!mountedRef.current) return false;
      // D) FIX: Background refresh failure keeps existing data
      if (!isBackground) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      }
      fetchInProgressRef.current = false;
      setIsRefreshing(false);
      // Only clear loading if we never loaded
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
  }, [isLoaded, isSignedIn, user, getToken, hours, days, compareEnabled, cacheKey]);
  
  // Effect: Trigger fetch when auth becomes ready or cache key changes
  useEffect(() => {
    if (!isLoaded) return;
    
    if (!isSignedIn || !user) {
      if (!hasLoadedRef.current && mountedRef.current) setLoading(false);
      return;
    }
    
    const cache = getCachedWithMeta<DashboardCacheData>(cacheKey);
    const hasFreshCache = cache.exists && !cache.isStale && cache.data?.providerStats?.length;
    
    if (hasFreshCache) {
      hasLoadedRef.current = true;
      if (mountedRef.current) setLoading(false);
      return;
    }
    
    loadData(!!cache.exists);
  }, [isLoaded, isSignedIn, user, cacheKey, loadData]);
  
  // E) FIX: Cleanup on unmount - prevent setState after unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);
  
  // Auto-refresh every 2 minutes (background only, paused when tab is hidden)
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user) return;
    
    const startInterval = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        if (!document.hidden && mountedRef.current) {
          loadData(true); // D) Background refresh - silent
        }
      }, 120000);
    };
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } else {
        const cache = getCachedWithMeta<DashboardCacheData>(cacheKey);
        if (cache.isStale && mountedRef.current) {
          loadData(true);
        }
        startInterval();
      }
    };
    
    startInterval();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isLoaded, isSignedIn, user, cacheKey, loadData]);
  
  return {
    runs,
    providerStats,
    modelStats,
    dailyStats,
    dailyAggregates,
    prevProviderStats,
    prevDailyStats,
    loading,
    isRefreshing,
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
  const [compareEnabled, setCompareEnabled] = useState(false);
  
  const {
    runs,
    providerStats,
    modelStats,
    dailyStats,
    dailyAggregates,
    prevProviderStats,
    prevDailyStats,
    loading,
    isRefreshing,
    error,
    lastRefresh,
    refresh,
  } = useDashboardData(dateRange, compareEnabled);
  
  // Calculate comparison stats
  const comparisonStats = useMemo(() => {
    if (!compareEnabled || prevProviderStats.length === 0) return null;
    
    const currentTotal = providerStats.reduce((sum, p) => sum + p.total_cost, 0);
    const prevTotal = prevProviderStats.reduce((sum, p) => sum + p.total_cost, 0);
    
    // Calculate percent change
    const percentChange = prevTotal > 0 
      ? ((currentTotal - prevTotal) / prevTotal) * 100 
      : currentTotal > 0 ? 100 : 0;
    
    return {
      currentTotal,
      prevTotal,
      percentChange,
      isUp: percentChange > 0,
    };
  }, [compareEnabled, providerStats, prevProviderStats]);
  
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
    
    // Week cost: sum of last 7 days from daily aggregates
    const weekCost = dailyAggregates.slice(-7).reduce((sum, day) => sum + (day.total || 0), 0);
    
    // Month cost: sum of last 30 days from daily aggregates
    const monthCost = dailyAggregates.slice(-30).reduce((sum, day) => sum + (day.total || 0), 0);
    
    // Yesterday's cost from daily aggregates
    const yesterdayCost = dailyAggregates.length >= 2 
      ? dailyAggregates[dailyAggregates.length - 2]?.total || 0 
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
  }, [filteredProviderStats, filteredModelStats, dailyAggregates]);
  
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
      
      // Use the date label directly from the API (already formatted)
      // The timeseries endpoint returns pre-formatted labels like "Dec 17 19:00" for hourly
      // or "Dec 17" for daily. Try to parse, fallback to using as-is.
      let dateLabel = day.date;
      const parsed = new Date(day.date);
      if (!isNaN(parsed.getTime())) {
        // Valid date string, format it nicely
        dateLabel = parsed.toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
        });
      }
      
      return {
        date: dateLabel,
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
  
  // A) FIX: Data presence overrides all other states
  const hasData = providerStats.length > 0;
  
  // Error state - only show if NO data exists
  if (error && !hasData) {
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
  
  // A) FIX: Loading skeleton ONLY if no data AND loading
  // If hasData, ALWAYS render main UI regardless of loading state
  if (!hasData && loading) {
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
          compareEnabled={compareEnabled}
          onCompareToggle={() => setCompareEnabled(!compareEnabled)}
          hasActiveFilters={hasActiveFilters}
          onReset={() => {
            setSelectedProviders([]);
            setSelectedModels([]);
          }}
        />
        
        {/* Subtle refreshing indicator */}
        {isRefreshing && (
          <div className="flex items-center justify-center gap-2 py-1 text-xs text-slate-400">
            <div className="w-3 h-3 border-2 border-slate-300 border-t-slate-500 rounded-full animate-spin" />
            Updating...
          </div>
        )}
        
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
        
        {/* Comparison Banner */}
        {compareEnabled && comparisonStats && (
          <div className={cn(
            "rounded-xl border p-4 flex items-center justify-between",
            comparisonStats.isUp 
              ? "bg-rose-50 border-rose-200" 
              : "bg-emerald-50 border-emerald-200"
          )}>
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center text-lg",
                comparisonStats.isUp ? "bg-rose-100" : "bg-emerald-100"
              )}>
                {comparisonStats.isUp ? "📈" : "📉"}
              </div>
              <div>
                <p className="text-sm font-medium text-slate-700">
                  Comparing to previous {dateRange === "24h" ? "24 hours" : dateRange === "7d" ? "week" : dateRange === "30d" ? "month" : "quarter"}
                </p>
                <p className={cn(
                  "text-lg font-bold",
                  comparisonStats.isUp ? "text-rose-600" : "text-emerald-600"
                )}>
                  {comparisonStats.isUp ? "+" : ""}{comparisonStats.percentChange.toFixed(1)}% 
                  <span className="text-sm font-normal text-slate-500 ml-2">
                    ({formatSmartCost(comparisonStats.prevTotal)} → {formatSmartCost(comparisonStats.currentTotal)})
                  </span>
                </p>
              </div>
            </div>
            <button 
              onClick={() => setCompareEnabled(false)}
              className="text-slate-400 hover:text-slate-600 p-1"
            >
              ✕
            </button>
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
