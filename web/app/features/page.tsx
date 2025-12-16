"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { AlertCircle, RefreshCw, Layers, Code } from "lucide-react";
import { fetchSectionStats, type SectionStats } from "@/lib/api";
import { AnalyticsHeader } from "@/components/analytics/AnalyticsHeader";
import { MetricCard, MetricCardRow } from "@/components/analytics/MetricCard";
import { CostDistributionChart, StackedBarChart } from "@/components/analytics/CostDistributionChart";
import { FeatureTreeTable, type FeatureNode } from "@/components/analytics/FeatureTreeTable";
import { FeatureDrawer } from "@/components/analytics/FeatureDrawer";
import { cn } from "@/lib/utils";
import {
  formatSmartCost,
  formatCompactNumber,
  formatDuration,
  formatPercentage,
  parseFeatureSection,
  getStableColor,
} from "@/lib/format";
import type { DateRange } from "@/contexts/AnalyticsContext";

// ============================================================================
// HOOKS
// ============================================================================

function useFeaturesData(hours: number) {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  
  const [sectionStats, setSectionStats] = useState<SectionStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  
  const loadData = useCallback(async (isBackground = false) => {
    if (!isLoaded || !user) return;
    
    if (!isBackground) setLoading(true);
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated. Please sign in again.");
      
      const stats = await fetchSectionStats(hours, null, token);
      // Filter out "main" and "default" - these are unlabeled API calls, not real features
      const filteredStats = (stats || []).filter(s => 
        s.section && 
        s.section.toLowerCase() !== "main" && 
        s.section.toLowerCase() !== "default"
      );
      setSectionStats(filteredStats);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("[Features] Error loading data:", err);
      setError(err instanceof Error ? err.message : "Failed to load feature data");
      setSectionStats([]);
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, [isLoaded, user, getToken, hours]);
  
  useEffect(() => {
    if (isLoaded && user) {
      loadData();
    }
  }, [isLoaded, user, loadData]);
  
  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(() => loadData(true), 30000);
    return () => clearInterval(interval);
  }, [loadData]);
  
  return {
    sectionStats,
    loading,
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
  const [selectedFeature, setSelectedFeature] = useState<FeatureNode | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  
  // Convert date range to hours
  const hours = useMemo(() => {
    switch (dateRange) {
      case "24h": return 24;
      case "7d": return 7 * 24;
      case "30d": return 30 * 24;
      case "90d": return 90 * 24;
    }
  }, [dateRange]);
  
  const { sectionStats, loading, error, lastRefresh, refresh } = useFeaturesData(hours);
  
  // Calculate totals
  const totals = useMemo(() => {
    const totalCost = sectionStats.reduce((sum, s) => sum + (s.total_cost || 0), 0);
    const totalCalls = sectionStats.reduce((sum, s) => sum + (s.call_count || 0), 0);
    const avgLatency = sectionStats.length > 0
      ? sectionStats.reduce((sum, s) => sum + (s.avg_latency_ms || 0), 0) / sectionStats.length
      : 0;
    
    return { totalCost, totalCalls, avgLatency };
  }, [sectionStats]);
  
  // Convert to FeatureNodes for tree table
  const featureNodes = useMemo<FeatureNode[]>(() => {
    return sectionStats.map(stat => ({
      id: stat.section,
      section: stat.section,
      section_path: stat.section_path,
      total_cost: stat.total_cost,
      call_count: stat.call_count,
      avg_latency_ms: stat.avg_latency_ms,
      percentage: stat.percentage,
    }));
  }, [sectionStats]);
  
  // Chart data
  const chartData = useMemo(() => {
    return sectionStats.map(stat => {
      const parsed = parseFeatureSection(stat.section);
      return {
        name: parsed.displayName,
        cost: stat.total_cost,
        calls: stat.call_count,
        type: parsed.type,
        section: stat.section,
      };
    });
  }, [sectionStats]);
  
  // Available feature types for filtering
  const availableTypes = useMemo(() => {
    const types = new Set<string>();
    sectionStats.forEach(stat => {
      const parsed = parseFeatureSection(stat.section);
      types.add(parsed.type);
    });
    return Array.from(types);
  }, [sectionStats]);
  
  // Handle feature click - open drawer
  const handleFeatureClick = useCallback((node: FeatureNode) => {
    setSelectedFeature(node);
    setDrawerOpen(true);
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
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-52 rounded-xl" />
            <Skeleton className="h-52 rounded-xl" />
          </div>
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }
  
  // Empty state
  if (sectionStats.length === 0) {
    return (
      <ProtectedLayout>
        <div className="space-y-6">
          <AnalyticsHeader
            title="Feature Costs"
            subtitle="Track costs by feature, agent, and workflow step"
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
          />
          
          <div className="bg-white rounded-xl border border-slate-200/60 p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto flex items-center justify-center mb-4">
              <Layers className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No Feature Data Yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto mb-6">
              Start tracking feature costs by using the <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-700">section()</code> context manager in your code.
            </p>
            
            <div className="bg-slate-900 rounded-lg p-4 text-left max-w-lg mx-auto">
              <div className="flex items-center gap-2 mb-2 text-xs text-slate-400">
                <Code className="w-4 h-4" />
                Python
              </div>
              <pre className="text-sm text-slate-300 overflow-x-auto">
{`from llmobserve import section

with section("feature:email_processing"):
    response = openai.chat.completions.create(...)

with section("agent:researcher"):
    with section("tool:web_search"):
        # Nested sections supported
        ...`}
              </pre>
            </div>
            
            <p className="text-xs text-slate-400 mt-6">
              Features will appear here once you start tracking them.
            </p>
          </div>
        </div>
      </ProtectedLayout>
    );
  }
  
  return (
    <ProtectedLayout>
      <div className="space-y-6 -mt-2">
        {/* Header */}
        <AnalyticsHeader
          title="Feature Costs"
          subtitle="Track costs by feature, agent, and workflow step"
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
          features={selectedTypes}
          availableFeatures={availableTypes}
          onFeaturesChange={setSelectedTypes}
          hasActiveFilters={selectedTypes.length > 0}
          onReset={() => setSelectedTypes([])}
        />
        
        {/* KPI Cards */}
        <MetricCardRow columns={4}>
          <MetricCard
            title="Total Feature Cost"
            value={totals.totalCost}
            variant="primary"
            icon={<span className="text-emerald-400">$</span>}
          />
          <MetricCard
            title="Total Calls"
            value={formatCompactNumber(totals.totalCalls)}
            formatValue={() => formatCompactNumber(totals.totalCalls)}
            tooltipContent={
              <div>
                <p className="font-medium">Total API Calls</p>
                <p className="text-slate-300 tabular-nums">{totals.totalCalls.toLocaleString()}</p>
              </div>
            }
          />
          <MetricCard
            title="Features Tracked"
            value={sectionStats.length.toString()}
            formatValue={() => sectionStats.length.toString()}
          />
          <MetricCard
            title="Avg Latency"
            value={formatDuration(totals.avgLatency)}
            formatValue={() => formatDuration(totals.avgLatency)}
          />
        </MetricCardRow>
        
        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Features Bar Chart */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Top Features by Cost</h3>
                <p className="text-xs text-slate-500 mt-0.5">Click to drill down</p>
              </div>
            </div>
            
            {/* Horizontal bar chart using treemap as bars */}
            <div className="space-y-2">
              {chartData
                .sort((a, b) => b.cost - a.cost)
                .slice(0, 8)
                .map((item, i) => {
                  const percentage = totals.totalCost > 0 
                    ? (item.cost / totals.totalCost) * 100 
                    : 0;
                  const color = getStableColor(item.section);
                  
                  return (
                    <button
                      key={item.section}
                      onClick={() => {
                        const node = featureNodes.find(n => n.section === item.section);
                        if (node) handleFeatureClick(node);
                      }}
                      className="w-full flex items-center gap-3 py-1.5 hover:bg-slate-50 rounded transition-colors group"
                    >
                      <div 
                        className="w-1 h-5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span className="text-sm text-slate-700 flex-1 text-left truncate group-hover:text-slate-900">
                        {item.name}
                      </span>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all"
                            style={{ 
                              width: `${Math.max(percentage, 2)}%`,
                              backgroundColor: color,
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-900 tabular-nums w-16 text-right">
                          {formatSmartCost(item.cost)}
                        </span>
                      </div>
                    </button>
                  );
                })}
              
              {chartData.length > 8 && (
                <p className="text-xs text-slate-400 text-center pt-2">
                  +{chartData.length - 8} more in table below
                </p>
              )}
            </div>
          </div>
          
          {/* Cost Distribution Treemap */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Cost Distribution</h3>
                <p className="text-xs text-slate-500 mt-0.5">Proportional view of spend</p>
              </div>
            </div>
            
            <CostDistributionChart
              data={chartData}
              totalCost={totals.totalCost}
              topN={10}
              height={200}
              colorKey="section"
              onClick={(item) => {
                const node = featureNodes.find(n => n.section === (item as any).section);
                if (node) handleFeatureClick(node);
              }}
            />
          </div>
        </div>
        
        {/* Feature Tree Table */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-900">All Features</h3>
            <div className="text-xs text-slate-400">
              Last updated: {lastRefresh.toLocaleTimeString()}
            </div>
          </div>
          
          <FeatureTreeTable
            data={featureNodes}
            totalCost={totals.totalCost}
            onRowClick={handleFeatureClick}
            maxHeight={500}
          />
        </div>
        
        {/* Feature Drawer */}
        <FeatureDrawer
          open={drawerOpen}
          onClose={() => {
            setDrawerOpen(false);
            setSelectedFeature(null);
          }}
          feature={selectedFeature}
          totalCost={totals.totalCost}
        />
      </div>
    </ProtectedLayout>
  );
}

// ============================================================================
// PAGE EXPORT
// ============================================================================

export default function FeaturesPage() {
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
            <Skeleton className="h-64 rounded-xl" />
          </div>
        </ProtectedLayout>
      }
    >
      <FeaturesPageContent />
    </Suspense>
  );
}
