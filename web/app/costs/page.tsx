"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { FilterBar } from "@/components/filters/FilterBar";
import { fetchRunDetail, fetchRuns, type Run } from "@/lib/api";
import {
  aggregateByProvider,
  aggregateByModel,
  aggregateBySectionPath,
  aggregateByDay,
} from "@/lib/aggregations";
import {
  formatCost,
  formatDuration,
  formatTokens,
  calculatePercentage,
} from "@/lib/stats";
import { exportToCSV, exportToJSON } from "@/lib/export";
import { Button } from "@/components/ui/button";
import { Download, BarChart3, PieChart, TrendingUp } from "lucide-react";
import {
  BarChart,
  Bar,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#3b82f6", "#a855f7", "#f97316", "#10b981", "#6366f1", "#ec4899"];

export default function CostsPage() {
  const searchParams = useSearchParams();
  const [runs, setRuns] = useState<Run[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch all runs
        const runsData = await fetchRuns(1000);
        setRuns(runsData);

        // Fetch events for each run (simplified - in production you'd have a better API)
        const eventPromises = runsData.slice(0, 20).map((run) => 
          fetchRunDetail(run.run_id).then((detail) => detail.events)
        );
        const eventsArrays = await Promise.all(eventPromises);
        const flatEvents = eventsArrays.flat();
        setAllEvents(flatEvents);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="p-8 space-y-8">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <PageHeader title="Cost Analysis" />
        <Card className="mt-6">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Aggregate data
  const byProvider = aggregateByProvider(allEvents);
  const byModel = aggregateByModel(allEvents);
  const bySectionPath = aggregateBySectionPath(allEvents);
  const byDay = aggregateByDay(allEvents);

  const totalCost = allEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);

  const handleExportCSV = (data: any[], filename: string) => {
    exportToCSV(data, filename);
  };

  const handleExportJSON = (data: any, filename: string) => {
    exportToJSON(data, filename);
  };

  return (
    <div className="p-8 space-y-8">
      <PageHeader
        title="Cost Analysis"
        description="Comprehensive cost breakdown and trends"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Costs" },
        ]}
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportCSV(allEvents, "cost-events.csv")}
            >
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportJSON({ byProvider, byModel, bySectionPath }, "cost-analysis.json")}
            >
              <Download className="mr-2 h-4 w-4" />
              Export JSON
            </Button>
          </>
        }
      />

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Total Cost</p>
              <p className="text-2xl font-bold">{formatCost(totalCost)}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Total Events</p>
              <p className="text-2xl font-bold">{allEvents.length.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground mb-1">Avg Cost/Event</p>
              <p className="text-2xl font-bold">
                {formatCost(allEvents.length > 0 ? totalCost / allEvents.length : 0)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabbed Cost Analysis */}
      <Tabs defaultValue="provider" className="space-y-6">
        <TabsList>
          <TabsTrigger value="provider">
            <BarChart3 className="mr-2 h-4 w-4" />
            By Provider
          </TabsTrigger>
          <TabsTrigger value="model">
            <PieChart className="mr-2 h-4 w-4" />
            By Model
          </TabsTrigger>
          <TabsTrigger value="section">
            <TrendingUp className="mr-2 h-4 w-4" />
            By Section Path
          </TabsTrigger>
        </TabsList>

        {/* By Provider */}
        <TabsContent value="provider" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Table */}
            <Card>
              <CardHeader>
                <CardTitle>Provider Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead className="text-right">Cost</TableHead>
                      <TableHead className="text-right">Calls</TableHead>
                      <TableHead className="text-right">%</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {byProvider.map((item) => (
                      <TableRow key={item.key}>
                        <TableCell>
                          <Badge variant="secondary">{item.key}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCost(item.cost)}
                        </TableCell>
                        <TableCell className="text-right">{item.count}</TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          {calculatePercentage(item.cost, totalCost).toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {/* Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RechartsPieChart>
                    <Pie
                      data={byProvider}
                      dataKey="cost"
                      nameKey="key"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry) => `${entry.key}: ${formatCost(entry.cost)}`}
                    >
                      {byProvider.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: any) => formatCost(Number(value))}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* By Model */}
        <TabsContent value="model" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Model Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Model</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Calls</TableHead>
                    <TableHead className="text-right">Tokens</TableHead>
                    <TableHead className="text-right">Avg Latency</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {byModel.map((item) => (
                    <TableRow key={item.key}>
                      <TableCell>
                        <Badge variant="outline">{item.key}</Badge>
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCost(item.cost)}
                      </TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                      <TableCell className="text-right">
                        {formatTokens(item.tokens || 0)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatDuration(item.avgLatency || 0)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {calculatePercentage(item.cost, totalCost).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Bar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Cost by Model</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={byModel.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="key" angle={-45} textAnchor="end" height={100} />
                  <YAxis tickFormatter={(value) => formatCost(value)} />
                  <Tooltip formatter={(value: any) => formatCost(Number(value))} />
                  <Bar dataKey="cost" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* By Section Path */}
        <TabsContent value="section" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Section Path Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Section Path</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Calls</TableHead>
                    <TableHead className="text-right">Avg Latency</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bySectionPath.slice(0, 20).map((item) => (
                    <TableRow key={item.key}>
                      <TableCell>
                        <Badge variant="secondary" className="font-mono text-xs">
                          {item.key}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-semibold">
                        {formatCost(item.cost)}
                      </TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                      <TableCell className="text-right">
                        {formatDuration(item.avgLatency || 0)}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {calculatePercentage(item.cost, totalCost).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

