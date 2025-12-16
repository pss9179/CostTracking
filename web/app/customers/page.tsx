"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  AlertCircle,
  RefreshCw,
  Users,
  Search,
  Download,
  TrendingUp,
  DollarSign,
  Activity,
} from "lucide-react";
import { fetchCustomerStats, type CustomerStats } from "@/lib/api";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

type SortKey = "customer_id" | "total_cost" | "call_count" | "avg_latency_ms";
type SortDir = "asc" | "desc";
type DateRange = "7d" | "30d" | "90d" | "all";

export default function CustomersPage() {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  
  const [customers, setCustomers] = useState<CustomerStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [dateRange, setDateRange] = useState<DateRange>("30d");
  const [sortKey, setSortKey] = useState<SortKey>("total_cost");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const hours = useMemo(() => {
    switch (dateRange) {
      case "7d": return 7 * 24;
      case "30d": return 30 * 24;
      case "90d": return 90 * 24;
      case "all": return 365 * 24;
    }
  }, [dateRange]);

  const loadData = useCallback(async () => {
    if (!isLoaded || !user) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      
      const data = await fetchCustomerStats(hours, null, token);
      setCustomers(data);
    } catch (err) {
      console.error("[Customers] Error:", err);
      setError(err instanceof Error ? err.message : "Failed to load customers");
    } finally {
      setLoading(false);
    }
  }, [isLoaded, user, getToken, hours]);

  useEffect(() => {
    if (isLoaded && user) {
      loadData();
    }
  }, [isLoaded, user, loadData]);

  // Filter and sort
  const filteredCustomers = useMemo(() => {
    let filtered = customers;
    
    if (search) {
      const term = search.toLowerCase();
      filtered = filtered.filter(c => 
        c.customer_id.toLowerCase().includes(term)
      );
    }
    
    return [...filtered].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const cmp = typeof aVal === "string" 
        ? aVal.localeCompare(bVal as string)
        : (aVal as number) - (bVal as number);
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [customers, search, sortKey, sortDir]);

  // Stats
  const totalCost = useMemo(() => 
    customers.reduce((sum, c) => sum + c.total_cost, 0), 
    [customers]
  );
  
  const totalCalls = useMemo(() => 
    customers.reduce((sum, c) => sum + c.call_count, 0), 
    [customers]
  );

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const exportCSV = () => {
    const headers = ["Customer ID", "Total Cost ($)", "API Calls", "Avg Latency (ms)"];
    const rows = filteredCustomers.map(c => [
      c.customer_id,
      c.total_cost.toFixed(6),
      c.call_count,
      c.avg_latency_ms.toFixed(2),
    ]);
    const csv = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `customers-${dateRange}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-6 p-6">
          <Skeleton className="h-10 w-48" />
          <div className="grid grid-cols-3 gap-4">
            {[1, 2, 3].map(i => <Skeleton key={i} className="h-24 rounded-xl" />)}
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
              <Button variant="outline" size="sm" onClick={loadData} className="mt-3">
                <RefreshCw className="w-4 h-4 mr-2" /> Retry
              </Button>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  // Empty state
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
            <div className="bg-gray-900 text-gray-100 rounded-lg p-4 max-w-lg mx-auto text-left font-mono text-sm">
              <div className="text-gray-400"># Python example</div>
              <div><span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> set_customer_id</div>
              <br />
              <div><span className="text-gray-400"># Tag all API calls with this customer</span></div>
              <div>set_customer_id(<span className="text-green-400">"customer_123"</span>)</div>
              <div>response = client.chat.completions.create(...)</div>
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
            <p className="text-gray-500 mt-1">Track costs per customer</p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={dateRange} onValueChange={(v) => setDateRange(v as DateRange)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
                <SelectItem value="90d">Last 90 days</SelectItem>
                <SelectItem value="all">All time</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Customers</p>
                <p className="text-2xl font-bold">{customers.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-50 rounded-lg">
                <DollarSign className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Cost</p>
                <p className="text-2xl font-bold">{formatSmartCost(totalCost)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border p-5">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Activity className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total API Calls</p>
                <p className="text-2xl font-bold">{formatCompactNumber(totalCalls)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border">
          {/* Toolbar */}
          <div className="p-4 border-b flex items-center justify-between gap-4">
            <div className="relative max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search customers..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                {filteredCustomers.length} of {customers.length}
              </span>
              <Button variant="outline" size="sm" onClick={exportCSV}>
                <Download className="w-4 h-4 mr-1" /> Export
              </Button>
            </div>
          </div>

          {/* Table Content */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort("customer_id")}
                >
                  Customer ID
                  {sortKey === "customer_id" && (sortDir === "asc" ? " ↑" : " ↓")}
                </TableHead>
                <TableHead 
                  className="text-right cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort("total_cost")}
                >
                  Total Cost
                  {sortKey === "total_cost" && (sortDir === "asc" ? " ↑" : " ↓")}
                </TableHead>
                <TableHead 
                  className="text-right cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort("call_count")}
                >
                  API Calls
                  {sortKey === "call_count" && (sortDir === "asc" ? " ↑" : " ↓")}
                </TableHead>
                <TableHead 
                  className="text-right cursor-pointer hover:bg-gray-50"
                  onClick={() => handleSort("avg_latency_ms")}
                >
                  Avg Latency
                  {sortKey === "avg_latency_ms" && (sortDir === "asc" ? " ↑" : " ↓")}
                </TableHead>
                <TableHead className="text-right">% of Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCustomers.map((customer, idx) => (
                <TableRow key={customer.customer_id} className="hover:bg-gray-50">
                  <TableCell className="font-medium">
                    {customer.customer_id}
                  </TableCell>
                  <TableCell className="text-right font-semibold tabular-nums">
                    {formatSmartCost(customer.total_cost)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-gray-600">
                    {formatCompactNumber(customer.call_count)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-gray-600">
                    {customer.avg_latency_ms.toFixed(0)}ms
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full"
                          style={{ width: `${Math.min(100, (customer.total_cost / totalCost) * 100)}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-500 tabular-nums w-12">
                        {((customer.total_cost / totalCost) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </ProtectedLayout>
  );
}
