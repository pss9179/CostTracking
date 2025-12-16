"use client";

import { useEffect, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchSectionStats, type SectionStats } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import { Layers, Clock, TrendingUp, DollarSign, Hash, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

// Format cost with appropriate precision
function formatCost(cost: number | null | undefined): string {
  if (cost === null || cost === undefined || isNaN(cost)) return "$0";
  if (cost === 0) return "$0";

  const absCost = Math.abs(cost);
  const sign = cost < 0 ? "-" : "";

  if (absCost < 0.000001) {
    return `${sign}<$0.000001`;
  } else if (absCost < 0.001) {
    return `${sign}${Math.round(absCost * 1_000_000)}µ$`;
  } else if (absCost < 1) {
    return `${sign}$${absCost.toFixed(4)}`;
  } else if (absCost < 1000) {
    return `${sign}$${absCost.toFixed(2)}`;
  } else if (absCost < 1_000_000) {
    return `${sign}$${(absCost / 1000).toFixed(1)}K`;
  }
  return `${sign}$${(absCost / 1_000_000).toFixed(1)}M`;
}

// Color palette for features
const FEATURE_COLORS = [
  "#10b981", // emerald
  "#8b5cf6", // violet
  "#6366f1", // indigo
  "#3b82f6", // blue
  "#ec4899", // pink
  "#f59e0b", // amber
  "#ef4444", // red
  "#14b8a6", // teal
  "#84cc16", // lime
  "#f97316", // orange
];

// Parse feature type from section name
function parseFeatureType(section: string): { type: string; name: string } {
  if (section.startsWith("feature:")) {
    return { type: "Feature", name: section.replace("feature:", "") };
  } else if (section.startsWith("agent:")) {
    return { type: "Agent", name: section.replace("agent:", "") };
  } else if (section.startsWith("step:")) {
    return { type: "Step", name: section.replace("step:", "") };
  } else if (section.startsWith("tool:")) {
    return { type: "Tool", name: section.replace("tool:", "") };
  }
  return { type: "Section", name: section };
}

// Get badge color based on type
function getTypeColor(type: string): string {
  switch (type) {
    case "Feature":
      return "bg-emerald-100 text-emerald-800";
    case "Agent":
      return "bg-violet-100 text-violet-800";
    case "Step":
      return "bg-blue-100 text-blue-800";
    case "Tool":
      return "bg-amber-100 text-amber-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
}

export default function FeaturesPage() {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();
  const [sectionStats, setSectionStats] = useState<SectionStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(24); // hours
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isLoaded) return;
    if (!user) {
      setLoading(false);
      setError("Not authenticated. Please sign in.");
      return;
    }

    async function loadData() {
      setLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated. Please sign in again.");

        const stats = await fetchSectionStats(timeRange, null, token);
        setSectionStats(stats || []);
      } catch (err) {
        console.error("[Features] Error loading data:", err);
        setError(err instanceof Error ? err.message : "Failed to load feature data");
        setSectionStats([]);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [isLoaded, user, getToken, timeRange]);

  // Calculate totals
  const totalCost = sectionStats.reduce((sum, s) => sum + (s.total_cost || 0), 0);
  const totalCalls = sectionStats.reduce((sum, s) => sum + (s.call_count || 0), 0);
  const avgLatency =
    sectionStats.length > 0
      ? sectionStats.reduce((sum, s) => sum + (s.avg_latency_ms || 0), 0) / sectionStats.length
      : 0;

  // Group by feature type
  const featureGroups = sectionStats.reduce((acc, stat) => {
    const { type } = parseFeatureType(stat.section);
    if (!acc[type]) acc[type] = [];
    acc[type].push(stat);
    return acc;
  }, {} as Record<string, SectionStats[]>);

  // Prepare chart data
  const chartData = sectionStats.slice(0, 10).map((s, i) => ({
    name: parseFeatureType(s.section).name.replace(/_/g, " "),
    cost: s.total_cost || 0,
    calls: s.call_count || 0,
    fill: FEATURE_COLORS[i % FEATURE_COLORS.length],
  }));

  const pieData = sectionStats.slice(0, 8).map((s, i) => ({
    name: parseFeatureType(s.section).name.replace(/_/g, " "),
    value: s.total_cost || 0,
    fill: FEATURE_COLORS[i % FEATURE_COLORS.length],
  }));

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  if (error) {
    return (
      <ProtectedLayout>
        <div className="p-8">
          <Card>
            <CardContent className="pt-6">
              <p className="text-red-600">{error}</p>
              <p className="text-sm text-muted-foreground mt-2">
                Make sure the collector API is running and you have tracked some features.
              </p>
            </CardContent>
          </Card>
        </div>
      </ProtectedLayout>
    );
  }

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="space-y-8 p-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-10 w-32" />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid gap-8 lg:grid-cols-2">
            <Skeleton className="h-80 w-full" />
            <Skeleton className="h-80 w-full" />
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-8 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Feature Costs</h1>
            <p className="text-sm text-muted-foreground">
              Track costs by feature, agent, and workflow step.
            </p>
          </div>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value={24}>Last 24 hours</option>
            <option value={168}>Last 7 days</option>
            <option value={720}>Last 30 days</option>
          </select>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-0 shadow-sm bg-gray-900 text-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-4 w-4 text-gray-400" />
                <p className="text-sm font-medium text-gray-400">Total Feature Cost</p>
              </div>
              <h3 className="text-2xl font-bold tabular-nums">{formatCost(totalCost)}</h3>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Hash className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm font-medium text-muted-foreground">Total Calls</p>
              </div>
              <h3 className="text-2xl font-bold tabular-nums text-gray-900">
                {totalCalls.toLocaleString()}
              </h3>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm font-medium text-muted-foreground">Features Tracked</p>
              </div>
              <h3 className="text-2xl font-bold tabular-nums text-gray-900">
                {sectionStats.length}
              </h3>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-white">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm font-medium text-muted-foreground">Avg Latency</p>
              </div>
              <h3 className="text-2xl font-bold tabular-nums text-gray-900">
                {avgLatency.toFixed(0)}ms
              </h3>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        {sectionStats.length > 0 ? (
          <div className="grid gap-8 lg:grid-cols-2">
            {/* Bar Chart - Top Features by Cost */}
            <Card className="border-0 shadow-sm bg-white">
              <CardHeader>
                <CardTitle className="text-lg">Top Features by Cost</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      layout="vertical"
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                      <XAxis
                        type="number"
                        tickFormatter={(value) => formatCost(value)}
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#6b7280", fontSize: 12 }}
                      />
                      <YAxis
                        dataKey="name"
                        type="category"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: "#374151", fontSize: 12 }}
                        width={120}
                      />
                      <Tooltip
                        cursor={{ fill: "#f3f4f6" }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const p = payload[0].payload;
                            return (
                              <div className="rounded-lg border bg-background p-3 shadow-lg">
                                <p className="text-sm font-medium capitalize">{p.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  Cost: {formatCost(p.cost)}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Calls: {p.calls.toLocaleString()}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="cost" barSize={20} radius={[4, 4, 4, 4]}>
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Pie Chart - Cost Distribution */}
            <Card className="border-0 shadow-sm bg-white">
              <CardHeader>
                <CardTitle className="text-lg">Cost Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }: any) =>
                          `${name} ${(percent * 100).toFixed(0)}%`
                        }
                        labelLine={{ stroke: "#9ca3af", strokeWidth: 1 }}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ active, payload }) => {
                          if (active && payload && payload.length) {
                            const p = payload[0].payload;
                            return (
                              <div className="rounded-lg border bg-background p-3 shadow-lg">
                                <p className="text-sm font-medium capitalize">{p.name}</p>
                                <p className="text-xs text-muted-foreground">
                                  Cost: {formatCost(p.value)}
                                </p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card className="border-0 shadow-sm bg-white">
            <CardContent className="py-12 text-center">
              <Layers className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Feature Data Yet</h3>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Start using the <code className="bg-gray-100 px-1 rounded">section()</code> context
                manager in your code to track feature costs.
              </p>
              <pre className="mt-4 bg-gray-900 text-white p-4 rounded-lg text-left text-sm max-w-md mx-auto">
{`from llmobserve import section

with section("feature:email_processing"):
    response = openai.chat.completions.create(...)
`}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Feature List */}
        {sectionStats.length > 0 && (
          <Card className="border-0 shadow-sm bg-white">
            <CardHeader>
              <CardTitle className="text-lg">All Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sectionStats.map((stat, index) => {
                  const { type, name } = parseFeatureType(stat.section);
                  const isExpanded = expandedSections.has(stat.section);

                  return (
                    <div
                      key={stat.section}
                      className="border border-gray-100 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => toggleSection(stat.section)}
                        className="flex items-center justify-between w-full p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: FEATURE_COLORS[index % FEATURE_COLORS.length] }}
                          />
                          <Badge className={cn("text-xs", getTypeColor(type))}>{type}</Badge>
                          <span className="font-medium text-gray-900 capitalize">
                            {name.replace(/_/g, " ")}
                          </span>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-sm font-semibold tabular-nums">
                              {formatCost(stat.total_cost)}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {stat.percentage.toFixed(1)}% of total
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ChevronDown className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                      </button>

                      {isExpanded && (
                        <div className="px-4 pb-4 pt-2 bg-gray-50 border-t border-gray-100">
                          <div className="grid grid-cols-3 gap-4">
                            <div>
                              <p className="text-xs text-muted-foreground">Calls</p>
                              <p className="text-sm font-semibold">
                                {stat.call_count.toLocaleString()}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Avg Latency</p>
                              <p className="text-sm font-semibold">
                                {stat.avg_latency_ms.toFixed(0)}ms
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Cost/Call</p>
                              <p className="text-sm font-semibold">
                                {formatCost(
                                  stat.call_count > 0 ? stat.total_cost / stat.call_count : 0
                                )}
                              </p>
                            </div>
                          </div>
                          {stat.section_path && stat.section_path !== stat.section && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <p className="text-xs text-muted-foreground">Full Path</p>
                              <code className="text-xs bg-white px-2 py-1 rounded border">
                                {stat.section_path}
                              </code>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ProtectedLayout>
  );
}
