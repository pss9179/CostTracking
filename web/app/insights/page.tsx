"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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

export default function InsightsPage() {
  const searchParams = useSearchParams();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(
    new Set(["section_spike", "model_inefficiency", "token_bloat", "retry_loop"])
  );

  useEffect(() => {
    async function loadInsights() {
      try {
        const data = await fetchInsights();
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
  }, []);

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
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <KPICard
          title="Total Alerts"
          value={stats.total}
          icon={Bell}
          description="Active insights"
        />
        <KPICard
          title="Cost Spikes"
          value={stats.section_spike}
          icon={AlertTriangle}
          description="Sections >2x average"
        />
        <KPICard
          title="Inefficiencies"
          value={stats.model_inefficiency}
          icon={DollarSign}
          description="Expensive model usage"
        />
        <KPICard
          title="Token Bloat"
          value={stats.token_bloat}
          icon={TrendingUp}
          description="Input tokens >1.5x avg"
        />
        <KPICard
          title="Retry Loops"
          value={stats.retry_loop}
          icon={RefreshCw}
          description="Excessive retries detected"
        />
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

