"use client";

import { useEffect, useState } from "react";
import { fetchMetrics, fetchCosts, fetchTenants, fetchWorkflows, CostEvent } from "@/lib/api";
import { TraceTree } from "@/components/trace-tree";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { DollarSign, Zap, Database, TrendingUp, Activity } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from "recharts";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [events, setEvents] = useState<CostEvent[]>([]);
  const [tenants, setTenants] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTenant, setSelectedTenant] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [selectedTenant]);

  const loadData = async () => {
    try {
      const [metricsData, costsData, tenantsData, workflowsData] = await Promise.all([
        fetchMetrics(selectedTenant || undefined),
        fetchCosts({ limit: 1000, tenant_id: selectedTenant || undefined }),
        fetchTenants(),
        fetchWorkflows(selectedTenant || undefined),
      ]);

      setMetrics(metricsData);
      setEvents(costsData.events);
      setTenants(tenantsData.tenants);
      setWorkflows(workflowsData.workflows);
      setLoading(false);
    } catch (error) {
      console.error("Failed to load data:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const costByProviderData = metrics
    ? Object.entries(metrics.cost_by_provider).map(([name, value]) => ({
        name,
        value: Number(value),
      }))
    : [];

  const costOverTimeData = metrics
    ? Object.entries(metrics.cost_over_time)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, cost]) => ({
          date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          cost: Number(cost),
        }))
    : [];

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">LLMObserve Dashboard</h1>
            <p className="text-muted-foreground mt-1">
              Real-time AI workflow tracking and cost monitoring
            </p>
          </div>
          {tenants.length > 0 && (
            <div className="flex gap-2">
              <Badge
                variant={selectedTenant === null ? "default" : "outline"}
                className="cursor-pointer"
                onClick={() => setSelectedTenant(null)}
              >
                All Tenants
              </Badge>
              {tenants.map((tenant) => (
                <Badge
                  key={tenant.tenant_id}
                  variant={selectedTenant === tenant.tenant_id ? "default" : "outline"}
                  className="cursor-pointer"
                  onClick={() => setSelectedTenant(tenant.tenant_id)}
                >
                  {tenant.tenant_id}
                </Badge>
              ))}
            </div>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${metrics?.total_cost_usd.toFixed(4) || "0.0000"}
              </div>
              <p className="text-xs text-muted-foreground">Across all workflows</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.total_requests || 0}</div>
              <p className="text-xs text-muted-foreground">API calls tracked</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.total_tokens.toLocaleString() || "0"}
              </div>
              <p className="text-xs text-muted-foreground">Tokens processed</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{workflows.length}</div>
              <p className="text-xs text-muted-foreground">Unique workflows</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="traces" className="space-y-4">
          <TabsList>
            <TabsTrigger value="traces">Workflow Traces</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="tenants">Tenants</TabsTrigger>
          </TabsList>

          <TabsContent value="traces" className="space-y-4">
            <TraceTree events={events} />
          </TabsContent>

          <TabsContent value="analytics" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Cost by Provider</CardTitle>
                  <CardDescription>Distribution of costs across providers</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={costByProviderData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {costByProviderData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cost Over Time</CardTitle>
                  <CardDescription>Daily cost trends</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={costOverTimeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                      <Line type="monotone" dataKey="cost" stroke="#8884d8" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="tenants" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {tenants.map((tenant) => (
                <Card key={tenant.tenant_id}>
                  <CardHeader>
                    <CardTitle>{tenant.tenant_id}</CardTitle>
                    <CardDescription>Tenant usage statistics</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Total Cost:</span>
                      <span className="font-medium">${tenant.total_cost_usd.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Requests:</span>
                      <span className="font-medium">{tenant.total_requests}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Tokens:</span>
                      <span className="font-medium">{tenant.total_tokens.toLocaleString()}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

