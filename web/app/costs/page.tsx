"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
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
import { CustomerFilter } from "@/components/CustomerFilter";
import { fetchRunDetail, fetchRuns, type Run } from "@/lib/api";
import {
  aggregateByProvider,
  aggregateByModel,
  aggregateByAgent,
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
import { Download, BarChart3, PieChart, TrendingUp, ChevronDown, ChevronRight } from "lucide-react";
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
  LineChart,
  Line,
} from "recharts";

const COLORS = ["#3b82f6", "#a855f7", "#f97316", "#10b981", "#6366f1", "#ec4899"];

// Group models by provider
interface ProviderGroup {
  provider: string;
  totalCost: number;
  totalCalls: number;
  totalTokens: number;
  avgLatency: number;
  models: Array<{
    model: string;
    cost: number;
    calls: number;
    tokens: number;
    avgLatency: number;
  }>;
}

function groupModelsByProvider(events: any[]): ProviderGroup[] {
  const providerMap = new Map<string, ProviderGroup>();

  events.forEach((event) => {
    // Extract provider from model string (e.g., "gpt-4" -> "openai", "claude" -> "anthropic")
    let provider = event.provider || "unknown";
    const model = event.model || "unknown";

    if (!providerMap.has(provider)) {
      providerMap.set(provider, {
        provider,
        totalCost: 0,
        totalCalls: 0,
        totalTokens: 0,
        avgLatency: 0,
        models: [],
      });
    }

    const group = providerMap.get(provider)!;
    group.totalCost += event.cost_usd || 0;
    group.totalCalls += 1;
    group.totalTokens += (event.input_tokens || 0) + (event.output_tokens || 0);
    group.avgLatency += event.latency_ms || 0;

    // Find or create model entry
    let modelEntry = group.models.find((m) => m.model === model);
    if (!modelEntry) {
      modelEntry = {
        model,
        cost: 0,
        calls: 0,
        tokens: 0,
        avgLatency: 0,
      };
      group.models.push(modelEntry);
    }

    modelEntry.cost += event.cost_usd || 0;
    modelEntry.calls += 1;
    modelEntry.tokens += (event.input_tokens || 0) + (event.output_tokens || 0);
    modelEntry.avgLatency += event.latency_ms || 0;
  });

  // Calculate averages
  const results = Array.from(providerMap.values()).map((group) => ({
    ...group,
    avgLatency: group.totalCalls > 0 ? group.avgLatency / group.totalCalls : 0,
    models: group.models.map((m) => ({
      ...m,
      avgLatency: m.calls > 0 ? m.avgLatency / m.calls : 0,
    })).sort((a, b) => b.cost - a.cost),
  }));

  return results.sort((a, b) => b.totalCost - a.totalCost);
}

export default function CostsPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [runs, setRuns] = useState<Run[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        const token = await getToken();
        if (!token) {
          setError("Not authenticated. Please sign in.");
          setLoading(false);
          return;
        }
        
        // Fetch all runs
        const runsData = await fetchRuns(1000, null, token);
        setRuns(runsData);

        // Fetch events for each run (simplified - in production you'd have a better API)
        const eventPromises = runsData.slice(0, 20).map((run) => 
          fetchRunDetail(run.run_id, null, token).then((detail) => detail.events).catch(() => [])
        );
        const eventsArrays = await Promise.all(eventPromises);
        const flatEvents = eventsArrays.flat();
        setAllEvents(flatEvents);
      } catch (err) {
        console.error("[Costs] Error loading data:", err);
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [getToken]);

  const toggleProvider = (provider: string) => {
    const newExpanded = new Set(expandedProviders);
    if (newExpanded.has(provider)) {
      newExpanded.delete(provider);
    } else {
      newExpanded.add(provider);
    }
    setExpandedProviders(newExpanded);
  };

  const handleAgentClick = (agentName: string) => {
    // Find the most expensive run for this agent
    const agentEvents = allEvents.filter((e) => 
      (e.section_path || e.section).includes(agentName)
    );
    
    if (agentEvents.length === 0) return;

    // Group by run_id and find the most expensive
    const runCosts = new Map<string, number>();
    agentEvents.forEach((e) => {
      const current = runCosts.get(e.run_id) || 0;
      runCosts.set(e.run_id, current + (e.cost_usd || 0));
    });

    const mostExpensiveRun = Array.from(runCosts.entries())
      .sort((a, b) => b[1] - a[1])[0];

    if (mostExpensiveRun) {
      router.push(`/runs/${mostExpensiveRun[0]}`);
    }
  };

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

  // Filter events by customer if selected
  const filteredEvents = selectedCustomer
    ? allEvents.filter(e => e.customer_id === selectedCustomer)
    : allEvents;
  
  // Debug: Log filtering results
  if (selectedCustomer) {
    console.log(`[Costs] Filtering by customer: ${selectedCustomer}`);
    console.log(`[Costs] Total events: ${allEvents.length}, Filtered: ${filteredEvents.length}`);
    console.log(`[Costs] Customer IDs in events:`, [...new Set(allEvents.map(e => e.customer_id).filter(Boolean))]);
  }

  // Aggregate data (using filtered events)
  const byProvider = aggregateByProvider(filteredEvents);
  const byAgent = aggregateByAgent(filteredEvents);
  const providerGroups = groupModelsByProvider(filteredEvents);
  const byDay = aggregateByDay(filteredEvents);

  const totalCost = filteredEvents.reduce((sum, e) => sum + (e.cost_usd || 0), 0);

  const handleExportCSV = (data: any[]) => {
    exportToCSV(data);
  };

  const handleExportJSON = (data: any) => {
    exportToJSON(data);
  };

  // Filter events for chart based on selected models
  const chartData = (() => {
    const realData = selectedModels.length > 0
      ? providerGroups.flatMap((pg) =>
          pg.models
            .filter((m) => selectedModels.includes(m.model))
            .map((m) => ({ name: m.model, cost: m.cost }))
        )
      : providerGroups.map((pg) => ({ name: pg.provider, cost: pg.totalCost }));
    
    // Return empty array if no real data - NO FAKE DATA
    return realData;
  })();

  // Show customer filter indicator
  if (selectedCustomer) {
    // Add indicator to page
  }

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
          <div className="flex items-center gap-4">
            <CustomerFilter
              selectedCustomer={selectedCustomer}
              onCustomerChange={setSelectedCustomer}
            />
            {selectedCustomer && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedCustomer(null)}
              >
                Clear Filter
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportCSV(allEvents)}
            >
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExportJSON({ byProvider, byAgent, providerGroups })}
            >
              <Download className="mr-2 h-4 w-4" />
              Export JSON
            </Button>
          </div>
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
          <TabsTrigger value="agent">
            <TrendingUp className="mr-2 h-4 w-4" />
            By Agent
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
                      <TableRow key={item.provider}>
                        <TableCell>
                          <Badge variant="secondary">{item.provider}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCost(item.cost)}
                        </TableCell>
                        <TableCell className="text-right">{item.calls}</TableCell>
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
                      data={byProvider as any}
                      dataKey="cost"
                      nameKey="provider"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry: any) => `${entry.provider}: ${formatCost(entry.cost)}`}
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

        {/* By Model - Grouped by Provider */}
        <TabsContent value="model" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Model Breakdown by Provider</CardTitle>
              <p className="text-sm text-muted-foreground">Click on a provider to expand and see individual models</p>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Provider / Model</TableHead>
                    <TableHead className="text-right">Cost</TableHead>
                    <TableHead className="text-right">Calls</TableHead>
                    <TableHead className="text-right">Tokens</TableHead>
                    <TableHead className="text-right">Avg Latency</TableHead>
                    <TableHead className="text-right">%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {providerGroups.map((group) => (
                    <React.Fragment key={group.provider}>
                      {/* Provider Row */}
                      <TableRow
                        className="cursor-pointer hover:bg-muted/50 font-semibold"
                        onClick={() => toggleProvider(group.provider)}
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {expandedProviders.has(group.provider) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                            <Badge variant="secondary">{group.provider}</Badge>
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-semibold">
                          {formatCost(group.totalCost)}
                        </TableCell>
                        <TableCell className="text-right">{group.totalCalls}</TableCell>
                        <TableCell className="text-right">
                          {formatTokens(group.totalTokens)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatDuration(group.avgLatency)}
                        </TableCell>
                        <TableCell className="text-right text-muted-foreground">
                          {calculatePercentage(group.totalCost, totalCost).toFixed(1)}%
                        </TableCell>
                      </TableRow>

                      {/* Expanded Model Rows */}
                      {expandedProviders.has(group.provider) &&
                        group.models.map((model) => (
                          <TableRow key={`${group.provider}-${model.model}`} className="bg-muted/20">
                            <TableCell className="pl-12">
                              <Badge variant="outline">{model.model}</Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              {formatCost(model.cost)}
                            </TableCell>
                            <TableCell className="text-right">{model.calls}</TableCell>
                            <TableCell className="text-right">
                              {formatTokens(model.tokens)}
                            </TableCell>
                            <TableCell className="text-right">
                              {formatDuration(model.avgLatency)}
                            </TableCell>
                            <TableCell className="text-right text-muted-foreground">
                              {calculatePercentage(model.cost, totalCost).toFixed(1)}%
                            </TableCell>
                          </TableRow>
                        ))}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Bar Chart for Model Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Comparison</CardTitle>
              <p className="text-sm text-muted-foreground">
                {selectedModels.length > 0
                  ? `Comparing selected models`
                  : `Showing provider-level totals (expand providers above to compare individual models)`}
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis tickFormatter={(value) => formatCost(value)} />
                  <Tooltip formatter={(value: any) => formatCost(Number(value))} />
                  <Bar dataKey="cost" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* By Agent */}
        <TabsContent value="agent" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Table */}
            <Card>
              <CardHeader>
                <CardTitle>Agent Breakdown</CardTitle>
                <p className="text-sm text-muted-foreground">Click on an agent to see its most expensive run</p>
              </CardHeader>
              <CardContent>
                {byAgent.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No agent data available.</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Agent</TableHead>
                        <TableHead className="text-right">Cost</TableHead>
                        <TableHead className="text-right">Calls</TableHead>
                        <TableHead className="text-right">%</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {byAgent.map((item) => (
                        <TableRow
                          key={item.agent}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => handleAgentClick(item.agent)}
                        >
                          <TableCell>
                            <Badge variant="secondary">{item.agent}</Badge>
                          </TableCell>
                          <TableCell className="text-right font-semibold">
                            {formatCost(item.cost)}
                          </TableCell>
                          <TableCell className="text-right">{item.calls}</TableCell>
                          <TableCell className="text-right text-muted-foreground">
                            {calculatePercentage(item.cost, totalCost).toFixed(1)}%
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Agent Cost Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Agent Cost Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={byAgent.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="agent" angle={-45} textAnchor="end" height={100} />
                    <YAxis tickFormatter={(value) => formatCost(value)} />
                    <Tooltip
                      formatter={(value: any) => formatCost(Number(value))}
                      labelFormatter={(label) => `Agent: ${label}`}
                    />
                    <Bar dataKey="cost" fill="#10b981" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
