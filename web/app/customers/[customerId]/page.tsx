"use client";

import { useState, useMemo, Suspense } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  DollarSign,
  Activity,
  Zap,
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { useCustomerDetail, useDashboardData } from "@/lib/hooks";
import { formatSmartCost, formatCompactNumber } from "@/lib/format";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area,
} from "recharts";

// Provider colors
const PROVIDER_COLORS: Record<string, string> = {
  openai: "#10a37f",
  anthropic: "#d97757",
  google: "#4285f4",
  azure: "#0078d4",
  mistral: "#ff7000",
  cohere: "#d4a574",
  default: "#64748b",
};

function CustomerDetailContent() {
  const params = useParams();
  const router = useRouter();
  const customerId = params.customerId as string;

  const [activeTab, setActiveTab] = useState<"providers" | "models" | "features">("providers");

  // Fetch customer detail - 30 days
  const { customer, loading, error, refresh } = useCustomerDetail(
    decodeURIComponent(customerId),
    30
  );

  // Also get org-wide totals for comparison (30 days = 720 hours)
  const { providerStats, loading: dashLoading } = useDashboardData(720);

  const orgTotalCost = useMemo(() => {
    return providerStats.reduce((sum, p) => sum + (p.total_cost || 0), 0);
  }, [providerStats]);

  // Calculate metrics
  const metrics = useMemo(() => {
    if (!customer) return null;
    const days = customer.period_days || 30;
    return {
      totalCost: customer.total_cost,
      avgPerDay: customer.total_cost / days,
      costPerRequest: customer.call_count > 0 ? customer.total_cost / customer.call_count : 0,
      apiCalls: customer.call_count,
      percentOfOrg: orgTotalCost > 0 ? (customer.total_cost / orgTotalCost) * 100 : 0,
      avgLatency: customer.avg_latency_ms,
    };
  }, [customer, orgTotalCost]);

  // Error state
  if (error) {
    return (
      <ProtectedLayout>
        <div className="p-8">
          <div className="mb-6">
            <Link href="/customers">
              <Button variant="ghost" size="sm">
                <ChevronLeft className="w-4 h-4 mr-1" />
                Back to Customers
              </Button>
            </Link>
          </div>
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 flex items-start gap-4">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-rose-700 font-medium">{error}</p>
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
  if (loading || !customer) {
    return (
      <ProtectedLayout>
        <div className="space-y-6">
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-20 w-full" />
          <div className="grid grid-cols-5 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-24 rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-80 rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }

  // Calculate provider chart data
  const providerChartData = customer.by_provider.slice(0, 10).map((p) => ({
    name: p.provider,
    cost: p.cost,
    calls: p.calls,
    fill: PROVIDER_COLORS[p.provider.toLowerCase()] || PROVIDER_COLORS.default,
  }));

  // Calculate model chart data
  const modelChartData = customer.top_models.slice(0, 10).map((m) => ({
    name: m.model,
    cost: m.cost,
    calls: m.calls,
  }));

  return (
    <ProtectedLayout>
      <div className="space-y-6 -mt-2">
        {/* Back button and header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/customers">
              <Button variant="ghost" size="sm" className="text-slate-500 hover:text-slate-700">
                <ChevronLeft className="w-4 h-4 mr-1" />
                Customers
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {decodeURIComponent(customerId)}
              </h1>
              <p className="text-sm text-slate-500">
                Last {customer.period_days} days
              </p>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={refresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* KPI Cards - Reusing dashboard-style layout */}
        <div className="grid grid-cols-5 gap-4">
          {/* Total Cost */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-md bg-emerald-100">
                <DollarSign className="w-4 h-4 text-emerald-600" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Total Cost
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {formatSmartCost(metrics?.totalCost || 0)}
            </p>
          </div>

          {/* Avg/Day */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-md bg-blue-100">
                <Activity className="w-4 h-4 text-blue-600" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Avg $/Day
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {formatSmartCost(metrics?.avgPerDay || 0)}
            </p>
          </div>

          {/* Cost/Request */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-md bg-amber-100">
                <Zap className="w-4 h-4 text-amber-600" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Cost/Request
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {formatSmartCost(metrics?.costPerRequest || 0)}
            </p>
          </div>

          {/* API Calls */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-md bg-violet-100">
                <Activity className="w-4 h-4 text-violet-600" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                API Calls
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {formatCompactNumber(metrics?.apiCalls || 0)}
            </p>
          </div>

          {/* % of Org */}
          <div className="bg-white rounded-xl border border-slate-200/60 p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="p-1.5 rounded-md bg-rose-100">
                <Users className="w-4 h-4 text-rose-600" />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                % of Org
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {(metrics?.percentOfOrg || 0).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Cost Drivers Section */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold">Cost Drivers</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
              <TabsList className="mb-6">
                <TabsTrigger value="providers">By Provider</TabsTrigger>
                <TabsTrigger value="models">By Model</TabsTrigger>
              </TabsList>

              <TabsContent value="providers" className="mt-0">
                {providerChartData.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={providerChartData}
                        layout="vertical"
                        margin={{ top: 0, right: 30, left: 80, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal vertical={false} />
                        <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(2)}`} stroke="#94a3b8" fontSize={12} />
                        <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={12} width={70} />
                        <Tooltip
                          formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
                          contentStyle={{
                            backgroundColor: "#fff",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                          }}
                        />
                        <Bar dataKey="cost" radius={[0, 4, 4, 0]}>
                          {providerChartData.map((entry, index) => (
                            <Bar key={index} dataKey="cost" fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex items-center justify-center text-slate-400">
                    No provider data available
                  </div>
                )}

                {/* Provider details table */}
                {providerChartData.length > 0 && (
                  <div className="mt-6 border-t pt-4">
                    <div className="grid grid-cols-3 gap-4 text-sm font-medium text-slate-500 mb-2 px-2">
                      <div>Provider</div>
                      <div className="text-right">Cost</div>
                      <div className="text-right">Calls</div>
                    </div>
                    {customer.by_provider.slice(0, 5).map((p) => (
                      <div
                        key={p.provider}
                        className="grid grid-cols-3 gap-4 px-2 py-2 border-b border-slate-100 text-sm"
                      >
                        <div className="font-medium text-slate-900">{p.provider}</div>
                        <div className="text-right text-slate-700">
                          {formatSmartCost(p.cost)}
                        </div>
                        <div className="text-right text-slate-600">
                          {formatCompactNumber(p.calls)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="models" className="mt-0">
                {modelChartData.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={modelChartData}
                        layout="vertical"
                        margin={{ top: 0, right: 30, left: 120, bottom: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal vertical={false} />
                        <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(2)}`} stroke="#94a3b8" fontSize={12} />
                        <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={11} width={110} />
                        <Tooltip
                          formatter={(value: number) => [`$${value.toFixed(4)}`, "Cost"]}
                          contentStyle={{
                            backgroundColor: "#fff",
                            border: "1px solid #e2e8f0",
                            borderRadius: "8px",
                          }}
                        />
                        <Bar dataKey="cost" fill="#6366f1" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex items-center justify-center text-slate-400">
                    No model data available
                  </div>
                )}

                {/* Model details table */}
                {modelChartData.length > 0 && (
                  <div className="mt-6 border-t pt-4">
                    <div className="grid grid-cols-3 gap-4 text-sm font-medium text-slate-500 mb-2 px-2">
                      <div>Model</div>
                      <div className="text-right">Cost</div>
                      <div className="text-right">Calls</div>
                    </div>
                    {customer.top_models.slice(0, 5).map((m) => (
                      <div
                        key={m.model}
                        className="grid grid-cols-3 gap-4 px-2 py-2 border-b border-slate-100 text-sm"
                      >
                        <div className="font-medium text-slate-900 truncate" title={m.model}>
                          {m.model}
                        </div>
                        <div className="text-right text-slate-700">
                          {formatSmartCost(m.cost)}
                        </div>
                        <div className="text-right text-slate-600">
                          {formatCompactNumber(m.calls)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Customer Health Panel */}
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold">Customer Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-6">
              {/* Cost Trend */}
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-center mb-2">
                  <div className="p-2 rounded-full bg-emerald-100">
                    <TrendingUp className="w-5 h-5 text-emerald-600" />
                  </div>
                </div>
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                  Cost Trend
                </p>
                <Badge variant="secondary" className="bg-emerald-100 text-emerald-700">
                  Stable
                </Badge>
              </div>

              {/* P95 Latency */}
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-center mb-2">
                  <div className="p-2 rounded-full bg-blue-100">
                    <Clock className="w-5 h-5 text-blue-600" />
                  </div>
                </div>
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                  Avg Latency
                </p>
                <p className="text-lg font-semibold text-slate-900">
                  {customer.avg_latency_ms.toFixed(0)}ms
                </p>
              </div>

              {/* Error Rate - Mock */}
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-center mb-2">
                  <div className="p-2 rounded-full bg-amber-100">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  </div>
                </div>
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                  Error Rate
                </p>
                <p className="text-lg font-semibold text-slate-900">{"<1%"}</p>
              </div>

              {/* Budget Status - Mock */}
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <div className="flex justify-center mb-2">
                  <div className="p-2 rounded-full bg-violet-100">
                    <DollarSign className="w-5 h-5 text-violet-600" />
                  </div>
                </div>
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">
                  Budget Status
                </p>
                <Badge variant="secondary" className="bg-violet-100 text-violet-700">
                  On Track
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}

export default function CustomerDetailPage() {
  return (
    <Suspense
      fallback={
        <ProtectedLayout>
          <div className="space-y-6">
            <Skeleton className="h-10 w-32" />
            <div className="grid grid-cols-5 gap-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-24 rounded-xl" />
              ))}
            </div>
            <Skeleton className="h-80 rounded-xl" />
          </div>
        </ProtectedLayout>
      }
    >
      <CustomerDetailContent />
    </Suspense>
  );
}

