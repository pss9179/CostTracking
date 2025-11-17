"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { KPICard } from "@/components/layout/KPICard";
import {
  AlertTriangle,
  DollarSign,
  TrendingUp,
  RefreshCw,
  Bell,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchInsights, type Insight } from "@/lib/api";

const INSIGHT_ICONS = {
  section_spike: AlertTriangle,
  model_inefficiency: DollarSign,
  token_bloat: TrendingUp,
  retry_loop: RefreshCw,
  default: Bell,
};

const INSIGHT_COLORS = {
  section_spike: "text-orange-600 bg-orange-50 border-orange-200",
  model_inefficiency: "text-blue-600 bg-blue-50 border-blue-200",
  token_bloat: "text-purple-600 bg-purple-50 border-purple-200",
  retry_loop: "text-red-600 bg-red-50 border-red-200",
};

function InsightsPageContent() {
  const searchParams = useSearchParams();
  const { getToken } = useAuth();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(
    new Set(["section_spike", "model_inefficiency", "token_bloat", "retry_loop"])
  );

  useEffect(() => {
    async function loadInsights() {
      try {
        const token = await getToken({ template: "default" });
        if (!token) {
          setError("Not authenticated. Please sign in.");
          setLoading(false);
          return;
        }
        const data = await fetchInsights(null, token);
        setInsights(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load insights");
      } finally {
        setLoading(false);
      }
    }

    loadInsights();
    const interval = setInterval(loadInsights, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [getToken]);

  const toggleType = (type: string) => {
    const newExpanded = new Set(expandedTypes);
    if (newExpanded.has(type)) {
      newExpanded.delete(type);
    } else {
      newExpanded.add(type);
    }
    setExpandedTypes(newExpanded);
  };

  // Group insights by type
  const groupedInsights = insights.reduce((acc, insight) => {
    const type = insight.type || "other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(insight);
    return acc;
  }, {} as Record<string, Insight[]>);

  // Calculate stats
  const stats = {
    total: insights.length,
    section_spike: insights.filter((i) => i.type === "section_spike").length,
    model_inefficiency: insights.filter((i) => i.type === "model_inefficiency").length,
    token_bloat: insights.filter((i) => i.type === "token_bloat").length,
    retry_loop: insights.filter((i) => i.type === "retry_loop").length,
  };

  if (loading) {
    return (
      <div className="p-8 space-y-8">
        <Skeleton className="h-12 w-64" />
        <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-6">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex-1 min-w-[120px]">
                <Skeleton className="h-4 w-20 mb-2" />
                <Skeleton className="h-8 w-16 mb-1" />
                <Skeleton className="h-3 w-24" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <PageHeader title="Insights & Alerts" />
        <Card className="mt-6">
          <CardContent className="pt-6">
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <PageHeader
        title="Insights & Alerts"
        description="Automated anomaly detection and cost optimization recommendations"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Insights" },
        ]}
      />

      {/* Summary Cards */}
      <div className="rounded-2xl border border-slate-200 bg-white/90 px-5 py-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Total Alerts</div>
            <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
            <p className="text-xs text-gray-500 mt-1">
              Active insights
            </p>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Cost Spikes</div>
            <div className="text-3xl font-bold text-gray-900">{stats.section_spike}</div>
            <p className="text-xs text-gray-500 mt-1">
              Sections &gt;2x average
            </p>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Inefficiencies</div>
            <div className="text-3xl font-bold text-gray-900">{stats.model_inefficiency}</div>
            <p className="text-xs text-gray-500 mt-1">
              Expensive model usage
            </p>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Token Bloat</div>
            <div className="text-3xl font-bold text-gray-900">{stats.token_bloat}</div>
            <p className="text-xs text-gray-500 mt-1">
              Input tokens &gt;1.5x avg
            </p>
          </div>
          <div className="hidden md:block h-10 w-px bg-indigo-200" />
          <div className="flex-1 min-w-[120px]">
            <div className="text-sm font-medium text-gray-600 mb-2">Retry Loops</div>
            <div className="text-3xl font-bold text-gray-900">{stats.retry_loop}</div>
            <p className="text-xs text-gray-500 mt-1">
              Excessive retries detected
            </p>
          </div>
        </div>
      </div>

      {/* Insights by Type */}
      {insights.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-lg font-medium mb-2">No Active Insights</p>
            <p className="text-sm text-muted-foreground">
              Everything looks good! Insights will appear here when anomalies are detected.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {Object.entries(groupedInsights).map(([type, typeInsights]) => {
            const Icon = INSIGHT_ICONS[type as keyof typeof INSIGHT_ICONS] || INSIGHT_ICONS.default;
            const colorClass = INSIGHT_COLORS[type as keyof typeof INSIGHT_COLORS] || "";
            const isExpanded = expandedTypes.has(type);

            return (
              <Card key={type}>
                <CardHeader className="cursor-pointer" onClick={() => toggleType(type)}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${colorClass}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="capitalize">
                          {type.replace(/_/g, " ")}
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">
                          {typeInsights.length} {typeInsights.length === 1 ? "alert" : "alerts"}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      {isExpanded ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </Button>
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="space-y-3">
                    {typeInsights.map((insight, idx) => (
                      <div
                        key={idx}
                        className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="font-medium mb-1">{insight.message}</p>
                            <div className="flex items-center gap-2 flex-wrap">
                              {insight.section && (
                                <Badge variant="secondary" className="text-xs">
                                  {insight.section}
                                </Badge>
                              )}
                              {insight.provider && (
                                <Badge variant="outline" className="text-xs">
                                  {insight.provider}
                                </Badge>
                              )}
                              {insight.endpoint && (
                                <Badge variant="outline" className="text-xs">
                                  {insight.endpoint}
                                </Badge>
                              )}
                              {insight.delta && (
                                <span className="text-xs text-muted-foreground">
                                  {insight.delta > 0 ? "+" : ""}
                                  {insight.delta.toFixed(1)}x
                                </span>
                              )}
                            </div>
                          </div>
                          <Link
                            href="/runs"
                            className="text-xs text-blue-600 hover:underline ml-4 whitespace-nowrap"
                          >
                            View Runs →
                          </Link>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function InsightsPage() {
  return (
    <Suspense fallback={<div className="p-6"><Skeleton className="h-96 w-full" /></div>}>
      <InsightsPageContent />
    </Suspense>
  );
}

