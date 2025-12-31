"use client";

import { useEffect, useState, useMemo, useCallback, Suspense, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { 
  AlertCircle, 
  RefreshCw, 
  Layers, 
} from "lucide-react";
import { 
  fetchSectionStats, 
  fetchProviderStats,
  fetchModelStats,
  type SectionStats,
  type ProviderStats,
  type ModelStats,
} from "@/lib/api";
import { AnalyticsHeader } from "@/components/analytics/AnalyticsHeader";
import { KPIGrid, calculateKPIs } from "@/components/analytics/KPIGrid";
import { FeatureTable, toFeatureRows, type FeatureRow } from "@/components/analytics/FeatureTable";
import { RankedBarChart } from "@/components/analytics/CostDistributionChart";
import { FeatureDrawer } from "@/components/analytics/FeatureDrawer";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatCompactNumber,
  formatDuration,
  getStableColor,
} from "@/lib/format";
import { getCached, setCached, getCachedWithMeta } from "@/lib/cache";
import { mark, measure, logCacheStatus, logAuth } from "@/lib/perf";
import type { DateRange } from "@/contexts/AnalyticsContext";

// ============================================================================
// TYPES
// ============================================================================

interface FilterState {
  types?: string[];
  providers?: string[];
  models?: string[];
}

interface FeaturesCacheData {
  sectionStats: SectionStats[];
  providerStats: ProviderStats[];
  modelStats: ModelStats[];
}

// ============================================================================
// HOOKS
// ============================================================================

function useFeaturesData(hours: number) {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  const cacheKey = `features-${hours}`;
  
  // SYNC CACHE INIT: Read cache BEFORE first paint
  const initialCache = typeof window !== 'undefined' 
    ? getCached<FeaturesCacheData>(cacheKey) 
    : null;
  const hasValidCache = !!(initialCache?.sectionStats?.length);
  
  // Refs to track state across renders
  const fetchInProgressRef = useRef(false);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const hasLoadedRef = useRef(hasValidCache); // Init from cache
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevCacheKeyRef = useRef(cacheKey);
  
  // State - initialized from cache synchronously
  const [sectionStats, setSectionStats] = useState<SectionStats[]>(() => initialCache?.sectionStats ?? []);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>(() => initialCache?.providerStats ?? []);
  const [modelStats, setModelStats] = useState<ModelStats[]>(() => initialCache?.modelStats ?? []);
  const [loading, setLoading] = useState(!hasValidCache); // False if cache exists
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  // Handle cacheKey CHANGES only (not initial mount)
  useEffect(() => {
    if (prevCacheKeyRef.current === cacheKey && hasLoadedRef.current) {
      return;
    }
    prevCacheKeyRef.current = cacheKey;
    
    const cached = getCached<FeaturesCacheData>(cacheKey);
    logCacheStatus('Features', cacheKey, !!cached, !cached);
    
    if (cached?.sectionStats) {
      if (!mountedRef.current) return;
      setSectionStats(cached.sectionStats || []);
      setProviderStats(cached.providerStats || []);
      setModelStats(cached.modelStats || []);
      if (cached.sectionStats.length > 0) {
        hasLoadedRef.current = true;
        setLoading(false);
      }
    }
    // NEVER clear state on cache miss
  }, [cacheKey]);
  
  const loadData = useCallback(async (isBackground = false): Promise<boolean> => {
    mark('features-loadData');
    logAuth('Features', isLoaded, isSignedIn, !!user);
    
    if (!isLoaded) return false;
    
    if (!isSignedIn || !user) {
      if (!mountedRef.current) return false;
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
    measure('features-auth-ready', 'features-loadData');
    
    if (fetchInProgressRef.current) return false;
    
    const cache = getCachedWithMeta<FeaturesCacheData>(cacheKey);
    logCacheStatus('Features', cacheKey, cache.exists, cache.isStale);
    if (isBackground && cache.exists && !cache.isStale) return false;
    
    fetchInProgressRef.current = true;
    
    // B) FIX: Only set loading if we haven't loaded yet
    if (!isBackground && !hasLoadedRef.current) {
      if (mountedRef.current) setLoading(true);
    } else if (!isBackground) {
      if (mountedRef.current) setIsRefreshing(true);
    }
    
    try {
      mark('features-getToken');
      const token = await getToken();
      measure('features-getToken');
      
      // C) FIX: Token retry - return early, don't hit finally
      if (!token) {
        fetchInProgressRef.current = false;
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) loadData(isBackground);
        }, 500);
        return false;
      }
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      
      mark('features-fetch');
      const [sections, providers, models] = await Promise.all([
        fetchSectionStats(hours, null, token).catch(() => []),
        fetchProviderStats(hours, null, token).catch(() => []),
        fetchModelStats(hours, null, token).catch(() => []),
      ]);
      measure('features-fetch');
      
      const filteredStats = (sections || []).filter(s => {
        if (!s.section) return false;
        const lower = s.section.toLowerCase();
        if (lower === "main" || lower === "default") return false;
        if (lower.startsWith("step:") || lower.startsWith("tool:") || lower.startsWith("agent:")) return false;
        return true;
      });
      
      // E) FIX: Check mounted before setState
      if (!mountedRef.current) return false;
      
      setSectionStats(filteredStats);
      setProviderStats(providers || []);
      setModelStats(models || []);
      setLastRefresh(new Date());
      setError(null);
      
      // B) FIX: Lock loading after first success
      hasLoadedRef.current = true;
      setLoading(false);
      setIsRefreshing(false);
      
      setCached<FeaturesCacheData>(cacheKey, {
        sectionStats: filteredStats,
        providerStats: providers || [],
        modelStats: models || [],
      });
      
      fetchInProgressRef.current = false;
      return true;
    } catch (err) {
      console.error("[Features] Error loading data:", err);
      if (!mountedRef.current) return false;
      if (!isBackground) {
        setError(err instanceof Error ? err.message : "Failed to load feature data");
      }
      fetchInProgressRef.current = false;
      setIsRefreshing(false);
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
  }, [isLoaded, isSignedIn, user, getToken, hours, cacheKey]);
  
  // Trigger fetch when auth ready
  useEffect(() => {
    if (!isLoaded) return;
    
    if (!isSignedIn || !user) {
      if (!hasLoadedRef.current && mountedRef.current) setLoading(false);
      return;
    }
    
    const cache = getCachedWithMeta<FeaturesCacheData>(cacheKey);
    if (cache.exists && !cache.isStale && cache.data?.sectionStats?.length) {
      hasLoadedRef.current = true;
      if (mountedRef.current) setLoading(false);
      return;
    }
    
    loadData(!!cache.exists);
  }, [isLoaded, isSignedIn, user, cacheKey, loadData]);
  
  // E) FIX: Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);
  
  // Auto-refresh
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user) return;
    
    const startInterval = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        if (!document.hidden && mountedRef.current) loadData(true);
      }, 120000);
    };
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      } else {
        const cache = getCachedWithMeta<FeaturesCacheData>(cacheKey);
        if (cache.isStale && mountedRef.current) loadData(true);
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
    sectionStats,
    providerStats,
    modelStats,
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

function FeaturesPageContent() {
  const searchParams = useSearchParams();
  const [dateRange, setDateRange] = useState<DateRange>(
    (searchParams.get('range') as DateRange) || "7d"
  );
  const [selectedFeature, setSelectedFeature] = useState<FeatureRow | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filters, setFilters] = useState<FilterState>({});
  
  // Convert date range to hours
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
  
  const { 
    sectionStats, 
    providerStats, 
    modelStats,
    loading, 
    isRefreshing,
    error, 
    lastRefresh, 
    refresh 
  } = useFeaturesData(hours);
  
  // Calculate totals and KPIs
  const totalCost = useMemo(() => 
    sectionStats.reduce((sum, s) => sum + (s.total_cost || 0), 0), 
    [sectionStats]
  );
  
  const kpiData = useMemo(() => 
    calculateKPIs(providerStats, modelStats, sectionStats),
    [providerStats, modelStats, sectionStats]
  );
  
  // Convert to feature rows for table
  const featureRows = useMemo(() => 
    toFeatureRows(sectionStats, totalCost),
    [sectionStats, totalCost]
  );
  
  // Chart data for stacked bar (Top 5 + Other)
  const chartData = useMemo(() => {
    const sorted = [...sectionStats].sort((a, b) => b.total_cost - a.total_cost);
    const top5 = sorted.slice(0, 5);
    const otherCost = sorted.slice(5).reduce((sum, s) => sum + s.total_cost, 0);
    
    const data = top5.map(s => ({
      name: s.section.split(":").pop() || s.section,
      cost: s.total_cost,
      calls: s.call_count,
    }));
    
    if (otherCost > 0) {
      data.push({
        name: "Other",
        cost: otherCost,
        calls: sorted.slice(5).reduce((sum, s) => sum + s.call_count, 0),
      });
    }
    
    return data;
  }, [sectionStats]);
  
  // Available filters
  const availableProviders = useMemo(() => 
    providerStats.map(p => p.provider),
    [providerStats]
  );
  
  const availableFeatures = useMemo(() => 
    sectionStats.map(s => s.section),
    [sectionStats]
  );
  
  // Handle row click
  const handleRowClick = useCallback((feature: FeatureRow) => {
    setSelectedFeature(feature);
    setDrawerOpen(true);
  }, []);
  
  // Handle KPI click (apply filter)
  const handleKPIClick = useCallback((kpiType: string, value?: string) => {
    if (kpiType === "provider" && value) {
      setFilters(prev => ({ ...prev, providers: [value] }));
    } else if (kpiType === "model" && value) {
      setFilters(prev => ({ ...prev, models: [value] }));
    }
  }, []);
  
  // A) FIX: Data presence overrides all other states
  const hasData = sectionStats.length > 0;
  
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
                Make sure you're using the <code className="bg-rose-100 px-1 rounded">section()</code> context manager in your code to track features.
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
  if (!hasData && loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-[400px] rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }
  
  // I) FIX: Empty state for new users - show immediately if not loading
  if (!hasData && !loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <AnalyticsHeader
            title="Feature Costs"
            subtitle="Track costs by feature"
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
          />
          
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl bg-gray-50/50">
            <Layers className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No feature data yet
            </h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Use the <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">section()</code> context 
              manager to track costs by feature.
            </p>
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 max-w-lg mx-auto text-left font-mono text-sm">
              <div className="text-gray-400"># Python example</div>
              <div><span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> section</div>
              <br />
              <div><span className="text-purple-400">with</span> section(<span className="text-green-400">"feature:email_processing"</span>):</div>
              <div className="pl-4 text-gray-400"># Your LLM calls here</div>
              <div className="pl-4">response = client.chat.completions.create(...)</div>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }
  
  return (
    <ProtectedLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <AnalyticsHeader
          title="Feature Costs"
          subtitle="Track costs by feature"
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
        />
        
        {/* Subtle refreshing indicator */}
        {isRefreshing && (
          <div className="flex items-center justify-center gap-2 py-1 text-xs text-slate-400">
            <div className="w-3 h-3 border-2 border-slate-300 border-t-slate-500 rounded-full animate-spin" />
            Updating...
          </div>
        )}
        
        {/* KPI Grid - Numeric first, no charts */}
        <KPIGrid
          data={kpiData}
          onKPIClick={handleKPIClick}
        />
        
        {/* Cost Distribution Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl border p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-900">Cost Distribution</h3>
                <div className="text-xs text-gray-500">Ranked by cost</div>
              </div>
              <RankedBarChart
                data={chartData}
                totalCost={totalCost}
                topN={8}
                height={220}
                showToggle={true}
                showVariance={true}
                onClick={(item) => {
                  const feature = featureRows.find(f => 
                    f.section.endsWith(item.name) || f.section.includes(item.name)
                  );
                  if (feature) handleRowClick(feature);
                }}
              />
            </div>
          </div>
          <div className="bg-white rounded-xl border p-6">
            <h3 className="text-sm font-medium text-gray-900 mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Features</span>
                <span className="font-semibold">{sectionStats.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total API Calls</span>
                <span className="font-semibold">
                  {sectionStats.reduce((sum, s) => sum + s.call_count, 0).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Avg Cost / Call</span>
                <span className="font-semibold">
                  {formatSmartCost(totalCost / Math.max(1, sectionStats.reduce((sum, s) => sum + s.call_count, 0)))}
                </span>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Total Cost</span>
                  <span className="font-bold text-lg">{formatSmartCost(totalCost)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Sortable Table - Source of Truth */}
        <FeatureTable
          features={featureRows}
          totalCost={totalCost}
          onRowClick={handleRowClick}
          onFilterChange={setFilters}
        />
        
        {/* Feature Drawer */}
        {selectedFeature && (
          <FeatureDrawer
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            totalCost={totalCost}
            feature={{
              id: selectedFeature.id,
              section: selectedFeature.section,
              section_path: null,
              total_cost: selectedFeature.total_cost,
              call_count: selectedFeature.call_count,
              avg_latency_ms: selectedFeature.avg_latency_ms,
              percentage: selectedFeature.percentage,
            }}
          />
        )}
      </div>
    </ProtectedLayout>
  );
}

// ============================================================================
// EXPORT
// ============================================================================

export default function FeaturesPage() {
  return (
    <Suspense fallback={
      <ProtectedLayout>
        <div className="p-6">
          <Skeleton className="h-96 w-full rounded-xl" />
        </div>
      </ProtectedLayout>
    }>
      <FeaturesPageContent />
    </Suspense>
  );
}
