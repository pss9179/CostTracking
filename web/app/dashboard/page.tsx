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
  fetchDashboardAll,
  type Run,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
} from "@/lib/api";
import { getCached, setCached, getCachedWithMeta } from "@/lib/cache";
import { mark, measure, logCacheStatus, logAuth } from "@/lib/perf";
import { waitForBackendWarm } from "@/components/BackendWarmer";
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
  todayCost: number;      // Fixed: today's cost
  periodCost: number;     // Variable: selected time range total
  periodCalls: number;    // Variable: selected time range calls
  weekCost: number;       // Fixed: last 7 days
  monthCost: number;      // Fixed: last 30 days
  yesterdayCost: number;  // Fixed: yesterday's cost
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

// TIMING INSTRUMENTATION - measures where delays occur
const PAGE_MOUNT_TIME = typeof window !== 'undefined' ? performance.now() : 0;
if (typeof window !== 'undefined') {
  console.log('[Dashboard] PAGE MOUNT at', PAGE_MOUNT_TIME.toFixed(0), 'ms');
}

function useDashboardData(dateRange: DateRange, compareEnabled: boolean = false) {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  // STABLE USER ID: Use user.id instead of user object to prevent effect re-runs
  // when Clerk refreshes the user object reference
  const userId = user?.id;
  
  // Log Clerk hydration timing
  useEffect(() => {
    if (isLoaded) {
      const now = performance.now();
      console.log('[Dashboard] CLERK HYDRATED at', now.toFixed(0), 'ms (took', (now - PAGE_MOUNT_TIME).toFixed(0), 'ms from mount)');
    }
  }, [isLoaded]);
  
  const cacheKey = `dashboard-${dateRange}-${compareEnabled}`;
  
  // Refs to track state across renders without causing re-renders
  const fetchInProgressRef = useRef(false);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const hasLoadedRef = useRef(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevCacheKeyRef = useRef(cacheKey);
  
  // SYNC CACHE INIT: Read cache INSIDE useState initializers
  // This ensures cache is read at initial mount, not at render time
  const [runs, setRuns] = useState<Run[]>(() => {
    if (typeof window === 'undefined') return [];
    const cached = getCached<DashboardCacheData>(cacheKey);
    console.log('[Dashboard] useState init runs, cached:', !!cached?.runs?.length);
    return cached?.runs ?? [];
  });
  
  const [providerStats, setProviderStats] = useState<ProviderStats[]>(() => {
    if (typeof window === 'undefined') return [];
    const cached = getCached<DashboardCacheData>(cacheKey);
    // FIX: Check if cache exists, not data length (empty [] is valid)
    const hasCachedData = cached !== null && cached !== undefined;
    console.log('[Dashboard] useState init providerStats, hasCachedData:', hasCachedData);
    if (hasCachedData) hasLoadedRef.current = true;
    return cached?.providerStats ?? [];
  });
  
  const [modelStats, setModelStats] = useState<ModelStats[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<DashboardCacheData>(cacheKey)?.modelStats ?? [];
  });
  
  const [dailyStats, setDailyStats] = useState<DailyStats[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<DashboardCacheData>(cacheKey)?.dailyStats ?? [];
  });
  
  const [dailyAggregates, setDailyAggregates] = useState<DailyStats[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<DashboardCacheData>(cacheKey)?.dailyStats ?? [];
  });
  
  const [prevProviderStats, setPrevProviderStats] = useState<ProviderStats[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<DashboardCacheData>(cacheKey)?.prevProviderStats ?? [];
  });
  
  const [prevDailyStats, setPrevDailyStats] = useState<DailyStats[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<DashboardCacheData>(cacheKey)?.prevDailyStats ?? [];
  });
  
  // Loading starts false if we have cached data
  const [loading, setLoading] = useState(() => {
    if (typeof window === 'undefined') return true;
    const cached = getCached<DashboardCacheData>(cacheKey);
    // FIX: Check if cache exists, not data length (empty [] is valid)
    const hasCache = cached !== null && cached !== undefined;
    console.log('[Dashboard] useState init loading, hasCache:', hasCache, '-> loading:', !hasCache);
    return !hasCache;
  });
  
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
  
  // ALWAYS fetch at least 30 days of daily aggregates for KPI cards (TODAY, WEEK, MONTH)
  // This ensures we have accurate data regardless of the selected date range
  const days = useMemo(() => Math.max(30, Math.ceil(hours / 24)), [hours]);
  
  // Handle cacheKey CHANGES only (when dateRange or compareEnabled changes)
  useEffect(() => {
    // Skip if cacheKey hasn't changed
    if (prevCacheKeyRef.current === cacheKey) {
      return;
    }
    
    console.log('[Dashboard] cacheKey changed:', prevCacheKeyRef.current, '->', cacheKey);
    prevCacheKeyRef.current = cacheKey;
    
    const cached = getCached<DashboardCacheData>(cacheKey);
    logCacheStatus('Dashboard', cacheKey, !!cached, !cached);
    
    // FIX: Check if cache exists, not data length (empty [] is valid cached data)
    if (cached !== null && cached !== undefined) {
      if (!mountedRef.current) return;
      setRuns(cached.runs || []);
      setProviderStats(cached.providerStats || []);
      setModelStats(cached.modelStats || []);
      setDailyStats(cached.dailyStats || []);
      setDailyAggregates(cached.dailyStats || []);
      setPrevProviderStats(cached.prevProviderStats || []);
      setPrevDailyStats(cached.prevDailyStats || []);
      hasLoadedRef.current = true;
      setLoading(false);
      console.log('[Dashboard] Hydrated from cache on key change');
    } else {
      // New cache key with no data - need to fetch
      console.log('[Dashboard] No cache for new key, will fetch');
    }
    // NEVER clear state on cache miss - keep existing data
  }, [cacheKey]);
  
  // The fetch function
  const loadData = useCallback(async (isBackground = false): Promise<boolean> => {
    const loadStart = performance.now();
    console.log('[Dashboard] loadData START at', loadStart.toFixed(0), 'ms (', (loadStart - PAGE_MOUNT_TIME).toFixed(0), 'ms since mount)');
    mark('dashboard-loadData');
    
    // CRITICAL: Auth must be ready but should NOT block UI
    logAuth('Dashboard', isLoaded, isSignedIn, !!user);
    if (!isLoaded) {
      console.log('[Dashboard] loadData DEFER: isLoaded=false at', (performance.now() - PAGE_MOUNT_TIME).toFixed(0), 'ms since mount - scheduling retry');
      // Schedule a retry when auth becomes ready - don't block UI
      if (!retryTimeoutRef.current && mountedRef.current) {
        retryTimeoutRef.current = setTimeout(() => {
          retryTimeoutRef.current = null;
          if (mountedRef.current) loadData(isBackground);
        }, 100); // Short retry - Clerk should hydrate quickly
      }
      return false;
    }
    
    if (!isSignedIn || !user) {
      console.log('[Dashboard] loadData ABORT: not signed in');
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
      const tokenStart = Date.now();
      
      // Add timeout to getToken - 2s max (Clerk should be fast when hydrated)
      let token: string | null = null;
    try {
        const tokenPromise = getToken();
        const timeoutPromise = new Promise<null>((_, reject) => 
          setTimeout(() => reject(new Error('getToken timeout after 2s')), 2000)
        );
        token = await Promise.race([tokenPromise, timeoutPromise]);
      } catch (e) {
        console.warn('[Dashboard] getToken timed out after 2s - will retry');
        token = null;
      }
      const tokenDuration = Date.now() - tokenStart;
      const sinceMount = (performance.now() - PAGE_MOUNT_TIME).toFixed(0);
      console.log('[Dashboard] getToken took:', tokenDuration, 'ms, token:', token ? 'present' : 'null', '(', sinceMount, 'ms since mount)');
      measure('dashboard-getToken');
      
      // C) FIX: Token retry - don't touch loading in finally if retry scheduled
      // Limit retries to prevent infinite loop
      const retryCountKey = '__dashboard_retry_count__';
      const retryCount = (window as any)[retryCountKey] || 0;
      
      if (!token) {
        if (retryCount >= 3) {
          console.error('[Dashboard] Max retries (3) reached - giving up on token fetch');
          (window as any)[retryCountKey] = 0;
          fetchInProgressRef.current = false;
          if (!hasLoadedRef.current && mountedRef.current) setLoading(false);
          return false;
        }
        
        (window as any)[retryCountKey] = retryCount + 1;
        console.log('[Dashboard] No token - scheduling retry', retryCount + 1, '/3 in 300ms');
        fetchInProgressRef.current = false;
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          console.log('[Dashboard] Token retry', retryCount + 1, 'executing');
          if (mountedRef.current) loadData(isBackground);
        }, 300);
        return false;
      }
      
      // Reset retry count on successful token
      (window as any)[retryCountKey] = 0;
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      
      // Note: Not awaiting waitForBackendWarm() because it adds unnecessary delay
      // The API requests will wake Railway directly if it's cold
      // The warmer runs in parallel and helps keep the container alive for future requests
      
      mark('dashboard-fetch');
      const fetchStart = Date.now();
      console.log('[Dashboard] Starting fetch with token:', token ? 'present' : 'MISSING');
      
      // Track whether fetch succeeded
      let fetchSucceeded = true;
      
      // Use consolidated endpoint for aggregate stats + timeseries for chart data (with provider breakdown)
      // The timeseries endpoint includes per-provider breakdown needed for stacked/by-provider chart views
      let runsData: Run[] = [];
      let providersData: ProviderStats[] = [];
      let modelsData: ModelStats[] = [];
      let timeseriesData: DailyStats[] = [];
      let dailyData: DailyStats[] = [];
      
      try {
        // OPTIMIZATION: Use Promise.allSettled to prevent one failure from blocking others
        // Also add timeout to prevent hanging on Railway cold starts
        const API_TIMEOUT = 30000; // 30 seconds - covers Railway cold starts
        
        const fetchWithTimeout = <T,>(promise: Promise<T>, timeoutMs: number): Promise<T> => {
          return Promise.race([
            promise,
            new Promise<T>((_, reject) => 
              setTimeout(() => reject(new Error('Request timeout')), timeoutMs)
            )
          ]);
        };
        
        const [runsResult, dashboardResult, timeseriesResult] = await Promise.allSettled([
          fetchWithTimeout(fetchRuns(50, null, token), API_TIMEOUT).catch((e) => {
            console.error('[Dashboard] fetchRuns error:', e.message);
            return [];
          }),
          fetchWithTimeout(fetchDashboardAll(hours, days, token), API_TIMEOUT).catch((e) => {
            console.error('[Dashboard] fetchDashboardAll error:', e.message);
            fetchSucceeded = false;
            return null;
          }),
          // Fetch timeseries separately to get provider breakdown for chart
          fetchWithTimeout(fetchTimeseries(hours, null, null, token), API_TIMEOUT).catch((e) => {
            console.error('[Dashboard] fetchTimeseries error:', e.message);
            return [];
          }),
        ]);
        
        // Extract values from Promise.allSettled results
        runsData = runsResult.status === 'fulfilled' ? runsResult.value : [];
        const dashboardData = dashboardResult.status === 'fulfilled' ? dashboardResult.value : null;
        const timeseriesDataResult = timeseriesResult.status === 'fulfilled' ? timeseriesResult.value : [];
        
        if (dashboardData) {
          // Map consolidated response to existing data structures
          providersData = dashboardData.providers.map(p => ({
            provider: p.provider,
            total_cost: p.total_cost,
            call_count: p.call_count,
            percentage: p.percentage,
          }));
          
          modelsData = dashboardData.models.map(m => ({
            provider: m.provider,
            model: m.model,
            total_cost: m.total_cost,
            call_count: m.call_count,
            input_tokens: m.input_tokens,
            output_tokens: m.output_tokens,
            avg_latency: m.avg_latency,
            percentage: 0, // Will be calculated if needed
          }));
          
          // Use consolidated daily data for aggregates
          dailyData = dashboardData.daily.map(d => ({
            date: d.date,
            total: d.total_cost,
            providers: {}, // Aggregates don't need provider breakdown
          }));
        }
        
        // Use timeseries data for chart (includes provider breakdown for stacked/by-provider modes)
        if (timeseriesDataResult && timeseriesDataResult.length > 0) {
          timeseriesData = timeseriesDataResult;
        } else if (dailyData && dailyData.length > 0) {
          // Fallback to daily data if timeseries failed
          timeseriesData = dailyData;
        }
      } catch (error: any) {
        console.error('[Dashboard] Fetch error:', error.message);
        fetchSucceeded = false;
      }
      
      console.log('[Dashboard] Fetch complete in', Date.now() - fetchStart, 'ms (', (performance.now() - PAGE_MOUNT_TIME).toFixed(0), 'ms since mount):', { 
        fetchSucceeded,
        runs: runsData?.length ?? 0, 
        providers: providersData?.length ?? 0, 
        models: modelsData?.length ?? 0,
        daily: dailyData?.length ?? 0 
      });
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
      
      // CRITICAL FIX: Only update state if we have new data - never clear existing data
      // This prevents the "data disappearing" bug where state gets cleared during loading
      // Always update if we got a response (even empty array), but never set to undefined/null
      if (Array.isArray(runsData)) setRuns(runsData);
      if (Array.isArray(providersData)) setProviderStats(providersData);
      if (Array.isArray(modelsData)) setModelStats(modelsData);
      if (Array.isArray(timeseriesData)) setDailyStats(timeseriesData);
      if (Array.isArray(dailyData)) setDailyAggregates(dailyData);
      if (Array.isArray(prevProvidersData)) setPrevProviderStats(prevProvidersData);
      if (Array.isArray(prevDailyOnly)) setPrevDailyStats(prevDailyOnly);
      setLastRefresh(new Date());
      
      // Only clear error if fetch actually succeeded, otherwise set a generic error
      if (fetchSucceeded) {
        setError(null);
      } else if (!isBackground && !hasLoadedRef.current) {
        // Only set error on initial load failure, not background refresh
        setError("Failed to load data. Check your connection and try again.");
      }
      
      // B) FIX: Lock loading after first success
      hasLoadedRef.current = true;
      setLoading(false);
      setIsRefreshing(false);
      
      // Cache successful responses (even if empty) to prevent refetching on navigation
      // Only skip caching if fetch actually failed (error was caught)
      if (fetchSucceeded) {
      setCached<DashboardCacheData>(cacheKey, {
        runs: runsData || [],
        providerStats: providersData || [],
        modelStats: modelsData || [],
          dailyStats: timeseriesData || [],
        prevProviderStats: prevProvidersData,
        prevDailyStats: prevDailyOnly,
      });
        console.log('[Dashboard] Cache written:', { providers: providersData?.length ?? 0, runs: runsData?.length ?? 0 });
      } else {
        console.log('[Dashboard] NOT caching - fetch failed');
      }
      
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
  }, [isLoaded, isSignedIn, userId, getToken, hours, days, compareEnabled, cacheKey]);
  
  // Effect: Trigger fetch immediately on mount and when deps change
  // loadData now handles auth retry internally - don't wait for isLoaded here
  useEffect(() => {
    const mountTime = (performance.now() - PAGE_MOUNT_TIME).toFixed(0);
    console.log('[Dashboard] Effect running at', mountTime, 'ms since mount:', { isLoaded, isSignedIn, hasUser: !!userId });
    
    const cache = getCachedWithMeta<DashboardCacheData>(cacheKey);
    // FIX: Check cache.exists, NOT data length (empty [] is valid cached data)
    const hasFreshCache = cache.exists && !cache.isStale;
    console.log('[Dashboard] Effect: cache status', { exists: cache.exists, isStale: cache.isStale, hasFreshCache });
    
    if (hasFreshCache) {
      console.log('[Dashboard] Effect: using fresh cache, skipping fetch');
      hasLoadedRef.current = true;
      if (mountedRef.current) setLoading(false);
      return;
    }
    
    // IMMEDIATE LOAD: Call loadData now - it handles auth retry internally
    console.log('[Dashboard] Effect: calling loadData immediately (', mountTime, 'ms since mount)');
    loadData(!!cache.exists);
    // NOTE: Intentionally NOT including loadData in deps - it's stable via useCallback
    // Using userId (string) instead of user (object) to prevent re-runs on Clerk refresh
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, isSignedIn, userId, cacheKey]);
  
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
    if (!isLoaded || !isSignedIn || !userId) return;
    
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, isSignedIn, userId, cacheKey]);
  
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
  
  // Helper: Calculate filtered cost from a day's provider breakdown
  const getFilteredDayCost = useCallback((day: DailyStats): number => {
    // If no filters, return total
    if (selectedProviders.length === 0 && selectedModels.length === 0) {
      return day.total || 0;
    }
    
    // If we have provider breakdown, filter it
    if (day.providers && typeof day.providers === 'object') {
      let sum = 0;
      Object.entries(day.providers).forEach(([provider, data]) => {
        if (selectedProviders.length === 0 || selectedProviders.includes(provider.toLowerCase())) {
          sum += data.cost || 0;
        }
      });
      return sum;
    }
    
    // Fallback to total if no breakdown available
    return day.total || 0;
  }, [selectedProviders, selectedModels]);
  
  // Calculate aggregated stats - use dailyAggregates for time-based KPIs
  // dailyAggregates has actual daily data (not hourly buckets like dailyStats might have for short ranges)
  const stats = useMemo<DashboardStats>(() => {
    // Period stats (for selected time range) - from filteredProviderStats
    const periodCost = filteredProviderStats.reduce((sum, stat) => sum + (stat.total_cost || 0), 0);
    const periodCalls = filteredProviderStats.reduce((sum, stat) => sum + (stat.call_count || 0), 0);
    
    // Helper to get UTC date string in YYYY-MM-DD format (backend uses UTC)
    const getUTCDateStr = (daysAgo: number = 0): string => {
      const date = new Date();
      date.setUTCDate(date.getUTCDate() - daysAgo);
      return date.toISOString().split('T')[0];
    };
    
    // Create a map for quick date lookup from dailyAggregates
    const dailyMap = new Map<string, DailyStats>();
    for (const day of dailyAggregates) {
      // Normalize date string to YYYY-MM-DD (handle various formats)
      const dateKey = day.date?.split('T')[0]?.split(' ')[0] || day.date;
      if (dateKey) {
        dailyMap.set(dateKey, day);
      }
    }
    
    
    // TODAY: Get today's cost from dailyAggregates (UTC)
    const todayStr = getUTCDateStr(0);
    const todayData = dailyMap.get(todayStr);
    const todayCost = todayData ? getFilteredDayCost(todayData) : 0;
    
    // YESTERDAY: Get yesterday's cost (UTC)
    const yesterdayStr = getUTCDateStr(1);
    const yesterdayData = dailyMap.get(yesterdayStr);
    const yesterdayCost = yesterdayData ? getFilteredDayCost(yesterdayData) : 0;
    
    // WEEK: Sum last 7 days from dailyAggregates
    let weekCost = 0;
    for (let i = 0; i < 7; i++) {
      const dateStr = getUTCDateStr(i);
      const dayData = dailyMap.get(dateStr);
      if (dayData) {
        weekCost += getFilteredDayCost(dayData);
      }
    }
    
    // MONTH: Sum last 30 days from dailyAggregates
    let monthCost = 0;
    for (let i = 0; i < 30; i++) {
      const dateStr = getUTCDateStr(i);
      const dayData = dailyMap.get(dateStr);
      if (dayData) {
        monthCost += getFilteredDayCost(dayData);
      }
    }
    
    
    // Top provider
    const sortedProviders = [...filteredProviderStats].sort((a, b) => b.total_cost - a.total_cost);
    const topProvider = sortedProviders[0]?.provider || null;
    
    // Top model
    const sortedModels = [...filteredModelStats].sort((a, b) => b.total_cost - a.total_cost);
    const topModel = sortedModels[0]?.model || null;
    
    return {
      todayCost,
      periodCost,
      periodCalls,
      weekCost,
      monthCost,
      yesterdayCost,
      avgCostPerCall: periodCalls > 0 ? periodCost / periodCalls : 0,
      topProvider,
      topModel,
    };
  }, [filteredProviderStats, filteredModelStats, dailyAggregates, getFilteredDayCost]);
  
  // Prepare chart data - FILTERED by selected provider/model
  const chartData = useMemo(() => {
    return dailyStats.map((day) => {
      const providerCosts: Record<string, number> = {};
      let filteredTotal = 0;
      
      if (day.providers && typeof day.providers === 'object') {
        Object.entries(day.providers).forEach(([provider, data]) => {
          // Skip filtered out providers
          if (selectedProviders.length > 0 && !selectedProviders.includes(provider.toLowerCase())) {
            return;
          }
          const cost = data.cost || 0;
          providerCosts[provider.toLowerCase()] = cost;
          filteredTotal += cost;
        });
      }
      
      // If no filters are active OR no provider breakdown exists, use total
      const hasFilters = selectedProviders.length > 0 || selectedModels.length > 0;
      const chartValue = hasFilters && Object.keys(providerCosts).length > 0 
        ? filteredTotal 
        : (day.total || 0);
      
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
        value: chartValue,
        ...providerCosts,
      };
    });
  }, [dailyStats, selectedProviders, selectedModels]);
  
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
  // hasData: any data in selected period (for charts)
  // hasHistoricalData: any data in past 30 days (for showing KPIs vs onboarding)
  const hasData = providerStats.length > 0;
  const hasHistoricalData = dailyAggregates.length > 0 || stats.monthCost > 0;
  const hasAnySpend = stats.todayCost > 0 || stats.weekCost > 0 || stats.monthCost > 0 || stats.periodCost > 0;
  
  // TIMING: Log first meaningful render
  useEffect(() => {
    const now = performance.now();
    console.log('[Dashboard] FIRST RENDER at', now.toFixed(0), 'ms (', (now - PAGE_MOUNT_TIME).toFixed(0), 'ms from mount)', { hasData, loading });
  }, []); // Only on mount
  
  // DEBUG: Log render state - helps diagnose empty dashboard issue
  console.log('[Dashboard] RENDER:', { 
    hasData, 
    hasAnySpend,
    loading, 
    isRefreshing, 
    providerStatsLen: providerStats.length,
    modelStatsLen: modelStats.length,
    dailyStatsLen: dailyStats.length,
    todayCost: stats.todayCost,
    periodCost: stats.periodCost,
    weekCost: stats.weekCost,
    selectedProviders,
    selectedModels,
  });
  
  // Error state - only show if NO data exists
  if (error && !hasData) {
    return (
      <ProtectedLayout>
        <div>
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
      <div className="space-y-4">
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
        
        {/* Empty state for new users - only show if NO historical data at all */}
        {/* Uses hasHistoricalData (30 days) not hasData (selected period) to avoid false onboarding */}
        {!hasHistoricalData && !loading && !isRefreshing && !error && (
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
        
        {/* No data in selected period (but has historical data) */}
        {hasHistoricalData && !hasData && !loading && !isRefreshing && !hasActiveFilters && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 text-center">
            <div className="max-w-md mx-auto">
              <span className="text-2xl mb-2 block">📊</span>
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                No activity in this period
              </h3>
              <p className="text-slate-600 text-sm">
                No costs recorded in the selected time range. Try expanding the date range to see your data.
              </p>
            </div>
          </div>
        )}
        
        {/* Filter empty state - has data but current filter returns nothing */}
        {hasData && !hasAnySpend && hasActiveFilters && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
            <div className="max-w-md mx-auto">
              <span className="text-2xl mb-2 block">🔍</span>
              <h3 className="text-lg font-medium text-slate-900 mb-2">
                No data matches your filters
              </h3>
              <p className="text-slate-600 text-sm mb-4">
                Try adjusting your provider or model filters to see data.
              </p>
              <button
                onClick={() => {
                  setSelectedProviders([]);
                  setSelectedModels([]);
                }}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-lg transition-colors text-sm"
              >
                Clear filters
              </button>
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
            value={stats.todayCost}
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
            value={formatCompactNumber(stats.periodCalls)}
            formatValue={() => formatCompactNumber(stats.periodCalls)}
            tooltipContent={
              <div>
                <p className="font-medium">Total API Calls</p>
                <p className="text-slate-300 tabular-nums">{stats.periodCalls.toLocaleString()}</p>
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
              totalCost={costDistributionData.reduce((sum, p) => sum + p.cost, 0)}
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
                  {formatSmartCost(stats.periodCost / Math.max(chartData.length, 1))}/day
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
            totalCost={stats.periodCost}
          />
          <ModelBreakdown
            models={filteredModelStats.map(m => ({
              ...m,
              percentage: stats.periodCost > 0 ? (m.total_cost / stats.periodCost) * 100 : 0,
            }))}
            totalCost={stats.periodCost}
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
