"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
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
import type { DateRange } from "@/contexts/AnalyticsContext";

// ============================================================================
// TYPES
// ============================================================================

interface FilterState {
  types?: string[];
  providers?: string[];
  models?: string[];
}

// ============================================================================
// HOOKS
// ============================================================================

// Module-level cache for features data
interface FeaturesCache {
  sectionStats: SectionStats[];
  providerStats: ProviderStats[];
  modelStats: ModelStats[];
  timestamp: number;
}
const featuresCache: { [key: string]: FeaturesCache } = {};
const FEATURES_CACHE_STALE_TIME = 30000; // 30 seconds

function useFeaturesData(hours: number) {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  
  const cacheKey = `features-${hours}`;
  const cached = featuresCache[cacheKey];
  const hasCachedData = cached && cached.sectionStats.length > 0;
  
  const [sectionStats, setSectionStats] = useState<SectionStats[]>(cached?.sectionStats || []);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>(cached?.providerStats || []);
  const [modelStats, setModelStats] = useState<ModelStats[]>(cached?.modelStats || []);
  const [loading, setLoading] = useState(!hasCachedData);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(
    cached ? new Date(cached.timestamp) : new Date()
  );
  
  const loadData = useCallback(async (isBackground = false) => {
    if (!isLoaded || !user) return;
    
    // Check if cache is still fresh
    const cached = featuresCache[cacheKey];
    if (isBackground && cached && Date.now() - cached.timestamp < FEATURES_CACHE_STALE_TIME) {
      return;
    }
    
    if (hasCachedData) {
      setIsRefreshing(true);
    } else if (!isBackground) {
      setLoading(true);
    }
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated. Please sign in again.");
      
      const [sections, providers, models] = await Promise.all([
        fetchSectionStats(hours, null, token).catch(() => []),
        fetchProviderStats(hours, null, token).catch(() => []),
        fetchModelStats(hours, null, token).catch(() => []),
      ]);
      
      // Filter out internal sections - only keep "feature:" prefixed items
      const filteredStats = (sections || []).filter(s => {
        if (!s.section) return false;
        const lower = s.section.toLowerCase();
        if (lower === "main" || lower === "default") return false;
        if (lower.startsWith("step:") || lower.startsWith("tool:") || lower.startsWith("agent:")) return false;
        return true;
      });
      
      setSectionStats(filteredStats);
      setProviderStats(providers || []);
      setModelStats(models || []);
      setLastRefresh(new Date());
      
      // Update cache
      featuresCache[cacheKey] = {
        sectionStats: filteredStats,
        providerStats: providers || [],
        modelStats: models || [],
        timestamp: Date.now(),
      };
    } catch (err) {
      console.error("[Features] Error loading data:", err);
      setError(err instanceof Error ? err.message : "Failed to load feature data");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [isLoaded, user, getToken, hours, cacheKey, hasCachedData]);
  
  useEffect(() => {
    if (isLoaded && user) {
      const cached = featuresCache[cacheKey];
      const isStale = !cached || Date.now() - cached.timestamp > FEATURES_CACHE_STALE_TIME;
      if (isStale) {
        loadData(!!cached);
      }
    }
  }, [isLoaded, user, loadData, cacheKey]);
  
  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [loadData]);
  
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
      case "24h": return 24;
      case "7d": return 7 * 24;
      case "30d": return 30 * 24;
      case "90d": return 90 * 24;
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
  
  // Loading state
  if (loading) {
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
  
  // Empty state
  if (sectionStats.length === 0) {
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
