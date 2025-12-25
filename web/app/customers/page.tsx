"use client";

import { useEffect, useState, useMemo, useCallback, Suspense } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { useRouter, useSearchParams } from "next/navigation";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  AlertCircle,
  RefreshCw,
  Users,
  Search,
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Activity,
  ChevronRight,
  X,
  Filter,
  Sparkles,
  Copy,
  ExternalLink,
} from "lucide-react";
import { 
  fetchCustomerStats, 
  fetchProviderStats,
  fetchModelStats,
  fetchTimeseries,
  fetchSectionStats,
  type CustomerStats,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
  type SectionStats,
} from "@/lib/api";
import { CostTrendChart } from "@/components/dashboard/CostTrendChart";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import { getCached, setCached, isCacheStale } from "@/lib/cache";
import { useGlobalFilters } from "@/contexts/GlobalFiltersContext";
import type { DateRange } from "@/contexts/AnalyticsContext";

type SortKey = "customer_id" | "total_cost" | "call_count" | "cost_per_call";

interface CustomerWithDelta extends CustomerStats {
  prevCost?: number;
  costDelta?: number;
  costDeltaPercent?: number;
  primaryProvider?: string;
  primaryModel?: string;
  trend?: "up" | "down" | "stable";
  cost_per_call: number; // Calculated field
}
type SortDir = "asc" | "desc";
type QuickFilter = "all" | "spiking" | "top_spenders" | "high_cost_per_call" | "long_tail";

interface CustomerWithDelta extends CustomerStats {
  prevCost?: number;
  costDelta?: number;
  costDeltaPercent?: number;
  primaryProvider?: string;
  primaryModel?: string;
  trend?: "up" | "down" | "stable";
}

// ============================================================================
// CUSTOMER HEALTH STRIP
// ============================================================================

function CustomerHealthStrip({
  customers,
  prevCustomers,
  totalCost,
  prevTotalCost,
}: {
  customers: CustomerWithDelta[];
  prevCustomers: CustomerStats[];
  totalCost: number;
  prevTotalCost: number;
}) {
  const costDelta = totalCost - prevTotalCost;
  const costDeltaPercent = prevTotalCost > 0 ? (costDelta / prevTotalCost) * 100 : 0;
  
  // Calculate concentration
  const top5Cost = customers.slice(0, 5).reduce((sum, c) => sum + c.total_cost, 0);
  const top10Cost = customers.slice(0, 10).reduce((sum, c) => sum + c.total_cost, 0);
  const top5Percent = totalCost > 0 ? (top5Cost / totalCost) * 100 : 0;
  const top10Percent = totalCost > 0 ? (top10Cost / totalCost) * 100 : 0;
  
  // Detect spikes (50%+ increase)
  const spikingCustomers = customers.filter(c => {
    const prev = prevCustomers.find(p => p.customer_id === c.customer_id);
    if (!prev || prev.total_cost === 0) return false;
    const increase = ((c.total_cost - prev.total_cost) / prev.total_cost) * 100;
    return increase >= 50;
  }).length;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {/* Total Spend */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Total Customer Spend</span>
          <DollarSign className="w-4 h-4 text-gray-400" />
        </div>
        <div className="text-2xl font-bold text-gray-900">{formatSmartCost(totalCost)}</div>
        {prevTotalCost > 0 && (
          <div className={cn(
            "text-xs mt-1 flex items-center gap-1",
            costDelta >= 0 ? "text-red-600" : "text-green-600"
          )}>
            {costDelta >= 0 ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            {Math.abs(costDeltaPercent).toFixed(1)}% vs prev period
          </div>
        )}
      </div>
      
      {/* Spend Delta */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Spend Δ</span>
          <Activity className="w-4 h-4 text-gray-400" />
        </div>
        <div className={cn(
          "text-2xl font-bold",
          costDelta >= 0 ? "text-red-600" : "text-green-600"
        )}>
          {costDelta >= 0 ? "+" : ""}{formatSmartCost(costDelta)}
        </div>
        <div className="text-xs text-gray-500 mt-1">vs previous period</div>
      </div>
      
      {/* Spiking Customers */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Spiking Customers</span>
          <AlertCircle className="w-4 h-4 text-amber-500" />
        </div>
        <div className="text-2xl font-bold text-gray-900">{spikingCustomers}</div>
        <div className="text-xs text-gray-500 mt-1">50%+ increase</div>
      </div>
      
      {/* Concentration */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">Spend Concentration</span>
          <Users className="w-4 h-4 text-gray-400" />
        </div>
        <div className="text-2xl font-bold text-gray-900">Top 5: {top5Percent.toFixed(0)}%</div>
        <div className="mt-2 space-y-1">
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-500 rounded-full"
                style={{ width: `${top5Percent}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">Top 5</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-400 rounded-full"
                style={{ width: `${top10Percent}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">Top 10</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// CUSTOMER LEADERBOARD TABLE
// ============================================================================

function CustomerLeaderboard({
  customers,
  totalCost,
  onRowClick,
  sortKey,
  sortDir,
  onSort,
  search,
  onSearch,
  quickFilter,
  onQuickFilter,
  minSpendThreshold,
  onMinSpendChange,
}: {
  customers: CustomerWithDelta[];
  totalCost: number;
  onRowClick: (customer: CustomerWithDelta) => void;
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (key: SortKey) => void;
  search: string;
  onSearch: (value: string) => void;
  quickFilter: QuickFilter;
  onQuickFilter: (filter: QuickFilter) => void;
  minSpendThreshold: number;
  onMinSpendChange: (value: number) => void;
}) {
  const filteredCustomers = useMemo(() => {
    let filtered = customers;
    
    // Search
    if (search) {
      const term = search.toLowerCase();
      filtered = filtered.filter(c => 
        c.customer_id.toLowerCase().includes(term)
      );
    }
    
    // Quick filters
    if (quickFilter === "spiking") {
      filtered = filtered.filter(c => c.trend === "up");
    } else if (quickFilter === "top_spenders") {
      filtered = filtered.slice(0, 10);
    } else if (quickFilter === "high_cost_per_call") {
      const avgCostPerCall = filtered.reduce((sum, c) => {
        const cpc = c.call_count > 0 ? c.total_cost / c.call_count : 0;
        return sum + cpc;
      }, 0) / filtered.length;
      filtered = filtered.filter(c => {
        const cpc = c.call_count > 0 ? c.total_cost / c.call_count : 0;
        return cpc > avgCostPerCall * 2;
      });
    } else if (quickFilter === "long_tail") {
      const top10Cost = filtered.slice(0, 10).reduce((sum, c) => sum + c.total_cost, 0);
      filtered = filtered.slice(10);
    }
    
    // Min spend threshold
    filtered = filtered.filter(c => c.total_cost >= minSpendThreshold);
    
    // Sort
    return [...filtered].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      let cmp = 0;
      
      if (sortKey === "customer_id") {
        cmp = (aVal as string).localeCompare(bVal as string);
      } else {
        cmp = (aVal as number) - (bVal as number);
      }
      
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [customers, search, quickFilter, minSpendThreshold, sortKey, sortDir]);

  const formatCustomerName = (customerId: string) => {
    // Convert customer_startup_io -> Startup IO
    return customerId
      .replace(/^customer_/, "")
      .replace(/_/g, " ")
      .split(" ")
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  return (
    <div className="bg-white rounded-lg border">
      {/* Toolbar */}
      <div className="p-4 border-b space-y-3">
        <div className="flex items-center justify-between gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search customers..."
              value={search}
              onChange={(e) => onSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Select value={quickFilter} onValueChange={(v) => onQuickFilter(v as QuickFilter)}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Customers</SelectItem>
                <SelectItem value="spiking">Spiking</SelectItem>
                <SelectItem value="top_spenders">Top 10</SelectItem>
                <SelectItem value="high_cost_per_call">High Cost/Call</SelectItem>
                <SelectItem value="long_tail">Long Tail</SelectItem>
              </SelectContent>
            </Select>
            
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Filter className="w-4 h-4" />
              <span>Min:</span>
              <Input
                type="number"
                value={minSpendThreshold}
                onChange={(e) => onMinSpendChange(parseFloat(e.target.value) || 0)}
                className="w-24 h-8"
                step="0.01"
                min="0"
              />
            </div>
            
            <Button variant="outline" size="sm" onClick={() => {
              const csv = [
                ["Customer ID", "Total Cost ($)", "Δ vs Prev ($)", "Δ vs Prev (%)", "Calls", "Cost/Call", "Primary Provider", "Primary Model"],
                ...filteredCustomers.map(c => [
                  c.customer_id,
                  c.total_cost.toFixed(6),
                  c.costDelta?.toFixed(6) || "0",
                  c.costDeltaPercent?.toFixed(1) || "0",
                  c.call_count,
                  (c.call_count > 0 ? c.total_cost / c.call_count : 0).toFixed(6),
                  c.primaryProvider || "",
                  c.primaryModel || "",
                ]),
              ].map(r => r.join(",")).join("\n");
              
              const blob = new Blob([csv], { type: "text/csv" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `customers-export.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }}>
              <Download className="w-4 h-4 mr-1" /> Export
            </Button>
          </div>
        </div>
        
        <div className="text-sm text-gray-500">
          Showing {filteredCustomers.length} of {customers.length} customers
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => onSort("customer_id")}
              >
                Customer
                {sortKey === "customer_id" && (sortDir === "asc" ? " ↑" : " ↓")}
              </TableHead>
              <TableHead 
                className="text-right cursor-pointer hover:bg-gray-50"
                onClick={() => onSort("total_cost")}
              >
                Total Cost
                {sortKey === "total_cost" && (sortDir === "asc" ? " ↑" : " ↓")}
              </TableHead>
              <TableHead className="text-right">Δ vs Prev</TableHead>
              <TableHead className="text-right">% of Org</TableHead>
              <TableHead 
                className="text-right cursor-pointer hover:bg-gray-50"
                onClick={() => onSort("call_count")}
              >
                Calls
                {sortKey === "call_count" && (sortDir === "asc" ? " ↑" : " ↓")}
              </TableHead>
              <TableHead 
                className="text-right cursor-pointer hover:bg-gray-50"
                onClick={() => onSort("cost_per_call")}
              >
                Cost/Call
                {sortKey === "cost_per_call" && (sortDir === "asc" ? " ↑" : " ↓")}
              </TableHead>
              <TableHead>Primary Provider</TableHead>
              <TableHead>Primary Model</TableHead>
              <TableHead>Trend</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredCustomers.map((customer) => {
              const costPerCall = customer.call_count > 0 ? customer.total_cost / customer.call_count : 0;
              const percentage = totalCost > 0 ? (customer.total_cost / totalCost) * 100 : 0;
              
              return (
                <TableRow 
                  key={customer.customer_id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onRowClick(customer)}
                >
                  <TableCell className="font-medium">
                    <div>
                      <div className="font-semibold">{formatCustomerName(customer.customer_id)}</div>
                      <div className="text-xs text-gray-400 font-mono">{customer.customer_id}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-semibold tabular-nums">
                    {formatSmartCost(customer.total_cost)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {customer.costDelta !== undefined ? (
                      <div className={cn(
                        "flex items-center justify-end gap-1",
                        customer.costDelta >= 0 ? "text-red-600" : "text-green-600"
                      )}>
                        {customer.costDelta >= 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        <span>{formatSmartCost(Math.abs(customer.costDelta))}</span>
                        {customer.costDeltaPercent !== undefined && (
                          <span className="text-xs">({customer.costDeltaPercent >= 0 ? "+" : ""}{customer.costDeltaPercent.toFixed(1)}%)</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${Math.min(100, percentage)}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 tabular-nums w-12">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-gray-600">
                    {formatCompactNumber(customer.call_count)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-gray-600">
                    {formatSmartCost(costPerCall)}
                  </TableCell>
                  <TableCell>
                    <span className="text-gray-400 text-xs">Click to view</span>
                  </TableCell>
                  <TableCell>
                    <span className="text-gray-400 text-xs">Click to view</span>
                  </TableCell>
                  <TableCell>
                    {customer.trend === "up" ? (
                      <Badge variant="destructive" className="text-xs">Spike</Badge>
                    ) : customer.trend === "down" ? (
                      <Badge variant="secondary" className="text-xs">↓</Badge>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ============================================================================
// CUSTOMER DETAIL PANEL
// ============================================================================

function CustomerDetailPanel({
  customer,
  isOpen,
  onClose,
  hours,
  onViewInDashboard,
}: {
  customer: CustomerWithDelta | null;
  isOpen: boolean;
  onClose: () => void;
  hours: number;
  onViewInDashboard: (customerId: string) => void;
}) {
  const { getToken } = useAuth();
  const [details, setDetails] = useState<{
    providers: ProviderStats[];
    models: ModelStats[];
    timeseries: DailyStats[];
    features: SectionStats[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && customer) {
      setLoading(true);
      getToken().then(token => {
        if (!token) return;
        
        Promise.all([
          fetchProviderStats(hours, null, customer.customer_id, token).catch(() => []),
          fetchModelStats(hours, null, customer.customer_id, token).catch(() => []),
          fetchTimeseries(hours, null, customer.customer_id, token).catch(() => []),
          fetchSectionStats(hours, null, customer.customer_id, token).catch(() => []),
        ]).then(([providers, models, timeseries, features]) => {
          setDetails({
            providers: providers || [],
            models: models || [],
            timeseries: timeseries || [],
            features: features || [],
          });
          setLoading(false);
        });
      });
    }
  }, [isOpen, customer, hours, getToken]);

  if (!customer) return null;

  const costPerCall = customer.call_count > 0 ? customer.total_cost / customer.call_count : 0;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{customer.customer_id}</SheetTitle>
          <SheetDescription>
            Detailed breakdown for this customer
          </SheetDescription>
          <div className="mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                onViewInDashboard(customer.customer_id);
                onClose();
              }}
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              View in Dashboard
            </Button>
          </div>
        </SheetHeader>
        
        {loading ? (
          <div className="mt-6 space-y-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-64" />
          </div>
        ) : details ? (
          <div className="mt-6 space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Total Spend</div>
                <div className="text-xl font-bold">{formatSmartCost(customer.total_cost)}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Calls</div>
                <div className="text-xl font-bold">{formatCompactNumber(customer.call_count)}</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm text-gray-500">Cost/Call</div>
                <div className="text-xl font-bold">{formatSmartCost(costPerCall)}</div>
              </div>
            </div>
            
            {/* Drivers */}
            <div>
              <h3 className="text-sm font-semibold mb-3">Drivers</h3>
              
              <div className="space-y-4">
                {/* Providers */}
                {details.providers.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-2">By Provider</div>
                    <div className="space-y-2">
                      {details.providers.slice(0, 5).map((p) => (
                        <div key={p.provider} className="flex items-center justify-between text-sm">
                          <span>{p.provider}</span>
                          <span className="font-medium">{formatSmartCost(p.total_cost)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Models */}
                {details.models.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-2">By Model</div>
                    <div className="space-y-2">
                      {details.models.slice(0, 5).map((m) => (
                        <div key={`${m.provider}-${m.model}`} className="flex items-center justify-between text-sm">
                          <span>{m.model}</span>
                          <span className="font-medium">{formatSmartCost(m.total_cost)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Features */}
                {details.features.length > 0 && (
                  <div>
                    <div className="text-xs text-gray-500 mb-2">By Feature</div>
                    <div className="space-y-2">
                      {details.features
                        .filter(f => f.section && !f.section.startsWith("step:") && !f.section.startsWith("tool:"))
                        .slice(0, 5)
                        .map((f) => (
                          <div key={f.section} className="flex items-center justify-between text-sm">
                            <span>{f.section.replace("feature:", "")}</span>
                            <span className="font-medium">{formatSmartCost(f.total_cost)}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            {/* Trend Chart */}
            {details.timeseries.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3">Spend Trend</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <CostTrendChart 
                    data={details.timeseries.map((day) => {
                      const providerCosts: Record<string, number> = {};
                      if (day.providers && typeof day.providers === 'object') {
                        Object.entries(day.providers).forEach(([provider, data]) => {
                          providerCosts[provider.toLowerCase()] = data.cost;
                        });
                      }
                      return {
                        date: day.date,
                        value: day.total || 0,
                        ...providerCosts,
                      };
                    })} 
                    height={200} 
                  />
                </div>
              </div>
            )}
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

function CustomersPageContent() {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  const router = useRouter();
  const { filters, setSelectedCustomer: setGlobalCustomer } = useGlobalFilters();
  
  const cacheKey = `customers-${filters.dateRange}`;
  
  // Track hydration state
  const [isHydrated, setIsHydrated] = useState(false);
  
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [prevCustomers, setPrevCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Hydration effect - sync cache to state
  useEffect(() => {
    const cachedData = getCached<{ customers: CustomerStats[], prevCustomers: CustomerStats[] }>(cacheKey);
    if (cachedData && cachedData.customers.length > 0) {
      setCustomers(cachedData.customers);
      setPrevCustomers(cachedData.prevCustomers || []);
      setLoading(false);
    }
    setIsHydrated(true);
  }, []); // Run once on mount
  
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerWithDelta | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("total_cost");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("all");
  const [minSpendThreshold, setMinSpendThreshold] = useState(0);

  const hours = useMemo(() => {
    switch (filters.dateRange) {
      case "1h": return 1;
      case "6h": return 6;
      case "24h": return 24;
      case "3d": return 3 * 24;
      case "7d": return 7 * 24;
      case "2w": return 14 * 24;
      case "30d": return 30 * 24;
      case "3m": return 90 * 24;
      case "6m": return 180 * 24;
      case "1y": return 365 * 24;
      default: return 7 * 24;
    }
  }, [filters.dateRange]);

  const loadData = useCallback(async (isBackground = false) => {
    if (!isLoaded || !user) return;
    
    // Skip if cache is fresh
    if (isBackground && !isCacheStale(cacheKey)) {
      return;
    }
    
    // Show refreshing indicator if we have data, loading only if empty
    const hasData = customers.length > 0;
    if (hasData) {
      setIsRefreshing(true);
    } else if (!isBackground) {
      setLoading(true);
    }
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      
      // Fetch current and previous period
      const [current, previous] = await Promise.all([
        fetchCustomerStats(hours, null, token),
        fetchCustomerStats(hours * 2, null, token), // Previous period
      ]);
      
      // Calculate previous period subset
      const prevCutoff = Math.floor(previous.length / 2);
      const prev = previous.slice(prevCutoff);
      
      setCustomers(current);
      setPrevCustomers(prev);
      
      // Update cache
      setCached(cacheKey, { customers: current, prevCustomers: prev });
    } catch (err) {
      console.error("[Customers] Error:", err);
      setError(err instanceof Error ? err.message : "Failed to load customers");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [isLoaded, user, getToken, hours, cacheKey]);

  useEffect(() => {
    if (!isHydrated) return;
    if (!isLoaded || !user) return;
    
    const cachedData = getCached<{ customers: CustomerStats[], prevCustomers: CustomerStats[] }>(cacheKey);
    const hasCachedData = cachedData && cachedData.customers.length > 0;
    
    if (hasCachedData && !isCacheStale(cacheKey)) {
      return; // Cache is fresh
    }
    
    loadData(!!hasCachedData);
  }, [isHydrated, isLoaded, user, cacheKey, hours]); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Auto-refresh every 2 minutes (paused when tab is hidden)
  useEffect(() => {
    if (!isLoaded || !user) return;
    
    let interval: NodeJS.Timeout | null = null;
    
    const startInterval = () => {
      if (interval) clearInterval(interval);
      interval = setInterval(() => {
        if (!document.hidden) {
          loadData(true);
        }
      }, 120000); // 2 minutes
    };
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) {
          clearInterval(interval);
          interval = null;
        }
      } else {
        startInterval();
      }
    };
    
    startInterval();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      if (interval) clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isLoaded, user, loadData]);


  // Enrich customers with delta and primary provider/model
  const enrichedCustomers = useMemo(() => {
    return customers.map(customer => {
      const prev = prevCustomers.find(p => p.customer_id === customer.customer_id);
      const costDelta = prev ? customer.total_cost - prev.total_cost : undefined;
      const costDeltaPercent = prev && prev.total_cost > 0 
        ? (costDelta! / prev.total_cost) * 100 
        : undefined;
      
      // Calculate cost per call
      const cost_per_call = customer.call_count > 0 
        ? customer.total_cost / customer.call_count 
        : 0;
      
      // Determine trend
      let trend: "up" | "down" | "stable" | undefined;
      if (costDeltaPercent !== undefined) {
        if (costDeltaPercent >= 50) trend = "up";
        else if (costDeltaPercent <= -50) trend = "down";
        else trend = "stable";
      }
      
      return {
        ...customer,
        prevCost: prev?.total_cost,
        costDelta,
        costDeltaPercent,
        trend,
        cost_per_call,
        // Primary provider/model will be fetched on-demand in detail panel
        primaryProvider: undefined,
        primaryModel: undefined,
      } as CustomerWithDelta;
    });
  }, [customers, prevCustomers]);

  const totalCost = useMemo(() => 
    customers.reduce((sum, c) => sum + c.total_cost, 0), 
    [customers]
  );
  
  const prevTotalCost = useMemo(() => 
    prevCustomers.reduce((sum, c) => sum + c.total_cost, 0), 
    [prevCustomers]
  );

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const handleRowClick = (customer: CustomerWithDelta) => {
    setSelectedCustomer(customer);
    setIsDetailOpen(true);
    // Set global filter for cross-linking
    setGlobalCustomer(customer.customer_id);
  };
  
  const handleViewInDashboard = (customerId: string) => {
    setGlobalCustomer(customerId);
    router.push("/dashboard");
  };

  if (loading && customers.length === 0) {
    return (
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
          </div>
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }

  if (error) {
    return (
      <ProtectedLayout>
        <div className="p-8">
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-rose-700 font-medium">{error}</p>
              <Button variant="outline" size="sm" onClick={() => loadData(false)} className="mt-3">
                <RefreshCw className="w-4 h-4 mr-2" /> Retry
              </Button>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  if (customers.length === 0) {
    return (
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
            <p className="text-gray-500 mt-1">Track costs per customer</p>
          </div>
          
          <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl bg-gray-50/50">
            <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No customer data yet
            </h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              Use <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">set_customer_id()</code> in 
              your code to track costs per customer.
            </p>
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
            <p className="text-gray-500 mt-1">Tenant attribution + triage</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => loadData(false)} disabled={loading}>
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </Button>
        </div>

        {/* Health Strip */}
        <CustomerHealthStrip
          customers={enrichedCustomers}
          prevCustomers={prevCustomers}
          totalCost={totalCost}
          prevTotalCost={prevTotalCost}
        />

        {/* Leaderboard */}
        <CustomerLeaderboard
          customers={enrichedCustomers}
          totalCost={totalCost}
          onRowClick={handleRowClick}
          sortKey={sortKey}
          sortDir={sortDir}
          onSort={handleSort}
          search={search}
          onSearch={setSearch}
          quickFilter={quickFilter}
          onQuickFilter={setQuickFilter}
          minSpendThreshold={minSpendThreshold}
          onMinSpendChange={setMinSpendThreshold}
        />

        {/* Detail Panel */}
        <CustomerDetailPanel
          customer={selectedCustomer}
          isOpen={isDetailOpen}
          onClose={() => setIsDetailOpen(false)}
          hours={hours}
          onViewInDashboard={handleViewInDashboard}
        />
      </div>
    </ProtectedLayout>
  );
}

export default function CustomersPage() {
  return (
    <Suspense fallback={
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
          </div>
          <Skeleton className="h-96 rounded-xl" />
        </div>
      </ProtectedLayout>
    }>
      <CustomersPageContent />
    </Suspense>
  );
}
