"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  AlertCircle, 
  RefreshCw, 
  Layers, 
  Code, 
  Table2,
  GitBranch,
  Shield,
  TrendingUp,
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
import { AgentTree, parseAgentNodes, type AgentNode } from "@/components/analytics/AgentTree";
import { StackedBarChart } from "@/components/analytics/CostDistributionChart";
import { CapsManager } from "@/components/caps/CapsManager";
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

function useFeaturesData(hours: number) {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  
  const [sectionStats, setSectionStats] = useState<SectionStats[]>([]);
  const [providerStats, setProviderStats] = useState<ProviderStats[]>([]);
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
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
      
      const [sections, providers, models] = await Promise.all([
        fetchSectionStats(hours, null, token).catch(() => []),
        fetchProviderStats(hours, null, token).catch(() => []),
        fetchModelStats(hours, null, token).catch(() => []),
      ]);
      
      // Filter out "main" and "default" - these are unlabeled API calls, not real features
      const filteredStats = (sections || []).filter(s => 
        s.section && 
        s.section.toLowerCase() !== "main" && 
        s.section.toLowerCase() !== "default"
      );
      
      setSectionStats(filteredStats);
      setProviderStats(providers || []);
      setModelStats(models || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("[Features] Error loading data:", err);
      setError(err instanceof Error ? err.message : "Failed to load feature data");
      setSectionStats([]);
      setProviderStats([]);
      setModelStats([]);
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
    providerStats,
    modelStats,
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
  const [activeTab, setActiveTab] = useState<"table" | "agents" | "caps">("table");
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
  
  // Convert to agent nodes for tree view
  const agentNodes = useMemo(() => 
    parseAgentNodes(sectionStats),
    [sectionStats]
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
            subtitle="Track costs by feature, agent, and workflow step"
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
              manager to track costs by feature, agent, or workflow step.
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
          subtitle="Track costs by feature, agent, and workflow step"
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
        />
        
        {/* KPI Grid - Numeric first, no charts */}
        <KPIGrid
          data={kpiData}
          onKPIClick={handleKPIClick}
        />
        
        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <TabsList className="grid w-fit grid-cols-3 h-10">
            <TabsTrigger value="table" className="gap-2 px-4">
              <Table2 className="w-4 h-4" />
              Features Table
            </TabsTrigger>
            <TabsTrigger value="agents" className="gap-2 px-4">
              <GitBranch className="w-4 h-4" />
              Agent Hierarchy
            </TabsTrigger>
            <TabsTrigger value="caps" className="gap-2 px-4">
              <Shield className="w-4 h-4" />
              Caps & Alerts
            </TabsTrigger>
          </TabsList>
          
          {/* Features Table Tab - Primary Workhorse */}
          <TabsContent value="table" className="space-y-6 mt-6">
            {/* Cost Distribution Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="bg-white rounded-xl border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-medium text-gray-900">Cost Distribution</h3>
                    <div className="text-xs text-gray-500">Top 5 + Other</div>
                  </div>
                  <StackedBarChart
                    data={chartData}
                    totalCost={totalCost}
                    height={180}
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
                    <span className="text-sm text-gray-500">Agents</span>
                    <span className="font-semibold">
                      {sectionStats.filter(s => s.section.startsWith("agent:")).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Tools</span>
                    <span className="font-semibold">
                      {sectionStats.filter(s => s.section.startsWith("tool:")).length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Steps</span>
                    <span className="font-semibold">
                      {sectionStats.filter(s => s.section.startsWith("step:")).length}
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
          </TabsContent>
          
          {/* Agents Hierarchy Tab */}
          <TabsContent value="agents" className="mt-6">
            <div className="bg-white rounded-xl border p-6">
              <AgentTree
                nodes={agentNodes}
                totalCost={totalCost}
                onNodeClick={(node) => {
                  const feature = featureRows.find(f => f.section === node.section);
                  if (feature) {
                    setSelectedFeature(feature);
                    setDrawerOpen(true);
                  }
                }}
              />
            </div>
          </TabsContent>
          
          {/* Caps & Alerts Tab */}
          <TabsContent value="caps" className="mt-6">
            <CapsManager
              providers={availableProviders}
              models={modelStats.map(m => m.model)}
              features={availableFeatures}
              onCapChange={refresh}
            />
          </TabsContent>
        </Tabs>
        
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
