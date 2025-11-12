"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { PageHeader } from "@/components/layout/PageHeader";
import { CustomerFilter } from "@/components/CustomerFilter";
import { fetchRuns, fetchRunDetail } from "@/lib/api";
import { formatCost, formatDuration } from "@/lib/stats";
import { 
  Bot, 
  TrendingUp, 
  DollarSign, 
  Activity, 
  Search,
  Download,
  ExternalLink
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from "recharts";

interface AgentStats {
  agentName: string;
  totalRuns: number;
  totalCost: number;
  avgCostPerRun: number;
  minCost: number;
  maxCost: number;
  totalCalls: number;
  avgLatency: number;
  mostExpensiveRunId: string;
  mostExpensiveRunCost: number;
  tools: string[];
  trend: Array<{ date: string; cost: number }>;
}

export default function AgentsPage() {
  const router = useRouter();
  const [agentStats, setAgentStats] = useState<AgentStats[]>([]);
  const [allEvents, setAllEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"cost" | "runs" | "latency">("cost");
  const [selectedCustomer, setSelectedCustomer] = useState<string | null>(null);

  useEffect(() => {
    async function loadAgentData() {
      try {
        // Fetch runs
        const runs = await fetchRuns(500);
        
        // Fetch events for each run
        const runDetails = await Promise.all(
          runs.slice(0, 50).map(r => fetchRunDetail(r.run_id))
        );

        // Aggregate by agent
        const agentMap = new Map<string, {
          runs: Set<string>;
          costs: number[];
          calls: number;
          latencies: number[];
          runCosts: Map<string, number>;
          tools: Set<string>;
          dailyCosts: Map<string, number>;
        }>();

        // Collect all events for customer filtering
        const allEventsList: any[] = [];
        
        runDetails.forEach(detail => {
          detail.events.forEach(event => {
            allEventsList.push(event);
            
            // ONLY PROCESS AGENT SECTIONS (filter out tools, steps, etc.)
            const section = event.section_path || event.section;
            if (!section.startsWith("agent:")) return;
            
            // Skip "internal" provider events (they're section markers, not real API calls)
            if (event.provider === "internal") return;
            
            // Filter by customer if selected
            if (selectedCustomer && event.customer_id !== selectedCustomer) return;

            const agentName = section.split("/")[0];  // Extract "agent:research_assistant"
            
            if (!agentMap.has(agentName)) {
              agentMap.set(agentName, {
                runs: new Set(),
                costs: [],
                calls: 0,
                latencies: [],
                runCosts: new Map(),
                tools: new Set(),
                dailyCosts: new Map(),
              });
            }

            const stats = agentMap.get(agentName)!;
            stats.runs.add(event.run_id);
            stats.costs.push(event.cost_usd);
            stats.calls++;
            stats.latencies.push(event.latency_ms);

            // Track cost per run
            const currentRunCost = stats.runCosts.get(event.run_id) || 0;
            stats.runCosts.set(event.run_id, currentRunCost + event.cost_usd);

            // Extract tools used
            if (section.includes("tool:")) {
              const toolMatch = section.match(/tool:([^\/]+)/);
              if (toolMatch) stats.tools.add(toolMatch[1]);
            }

            // Daily costs
            const day = new Date(event.created_at).toISOString().split("T")[0];
            stats.dailyCosts.set(day, (stats.dailyCosts.get(day) || 0) + event.cost_usd);
          });
        });

        // Convert to stats array
        const statsArray: AgentStats[] = Array.from(agentMap.entries()).map(([name, data]) => {
          const sortedRunCosts = Array.from(data.runCosts.entries())
            .sort((a, b) => b[1] - a[1]);
          
          const sortedDailyCosts = Array.from(data.dailyCosts.entries())
            .sort((a, b) => a[0].localeCompare(b[0]))
            .map(([date, cost]) => ({ date, cost }));

          return {
            agentName: name,
            totalRuns: data.runs.size,
            totalCost: data.costs.reduce((a, b) => a + b, 0),
            avgCostPerRun: data.costs.reduce((a, b) => a + b, 0) / data.runs.size,
            minCost: Math.min(...data.costs),
            maxCost: Math.max(...data.costs),
            totalCalls: data.calls,
            avgLatency: data.latencies.reduce((a, b) => a + b, 0) / data.latencies.length,
            mostExpensiveRunId: sortedRunCosts[0]?.[0] || "",
            mostExpensiveRunCost: sortedRunCosts[0]?.[1] || 0,
            tools: Array.from(data.tools),
            trend: sortedDailyCosts,
          };
        });

        setAgentStats(statsArray);
        setAllEvents(allEventsList);
      } catch (err) {
        console.error("Failed to load agent data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadAgentData();
  }, [selectedCustomer]);

  // Filter and sort
  const filteredAgents = agentStats
    .filter(a => a.agentName.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      switch (sortBy) {
        case "cost": return b.totalCost - a.totalCost;
        case "runs": return b.totalRuns - a.totalRuns;
        case "latency": return b.avgLatency - a.avgLatency;
        default: return 0;
      }
    });

  const totalCost = agentStats.reduce((sum, a) => sum + a.totalCost, 0);
  const totalRuns = agentStats.reduce((sum, a) => sum + a.totalRuns, 0);
  const avgCostPerRun = totalRuns > 0 ? totalCost / totalRuns : 0;

  if (loading) {
    return (
      <div className="p-8 space-y-8">
        <Skeleton className="h-12 w-64" />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-32" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <PageHeader
        title="Agent Analytics"
        description="Monitor your AI agents' costs, performance, and workflows"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Agents" },
        ]}
      />

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agentStats.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCost(totalCost)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Cost/Run</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCost(avgCostPerRun)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalRuns}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters & Search */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search agents..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
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
        <Select value={sortBy} onValueChange={(v: any) => setSortBy(v)}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="cost">Sort by Cost</SelectItem>
            <SelectItem value="runs">Sort by Runs</SelectItem>
            <SelectItem value="latency">Sort by Latency</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" size="sm">
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </div>
      
      {selectedCustomer && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded">
          <p className="text-sm text-blue-900">
            Filtering by: <strong>{selectedCustomer}</strong>
          </p>
        </div>
      )}

      {/* Agent Table */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Breakdown</CardTitle>
          <p className="text-sm text-muted-foreground">
            Click on an agent to view its most expensive run
          </p>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Agent</TableHead>
                <TableHead className="text-right">Total Cost</TableHead>
                <TableHead className="text-right">Runs</TableHead>
                <TableHead className="text-right">Avg Cost/Run</TableHead>
                <TableHead className="text-right">Max Run Cost</TableHead>
                <TableHead className="text-right">Avg Latency</TableHead>
                <TableHead>Tools Used</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAgents.map((agent) => (
                <TableRow 
                  key={agent.agentName}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => {
                    if (agent.mostExpensiveRunId) {
                      router.push(`/runs/${agent.mostExpensiveRunId}`);
                    }
                  }}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-muted-foreground" />
                      <Badge variant="secondary" className="font-mono text-xs">
                        {agent.agentName.replace("agent:", "")}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-semibold">
                    {formatCost(agent.totalCost)}
                  </TableCell>
                  <TableCell className="text-right">{agent.totalRuns}</TableCell>
                  <TableCell className="text-right">
                    {formatCost(agent.avgCostPerRun)}
                  </TableCell>
                  <TableCell className="text-right text-red-600 font-medium">
                    {formatCost(agent.mostExpensiveRunCost)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatDuration(agent.avgLatency)}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {agent.tools.slice(0, 3).map(tool => (
                        <Badge key={tool} variant="outline" className="text-xs">
                          {tool}
                        </Badge>
                      ))}
                      {agent.tools.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{agent.tools.length - 3}
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/runs/${agent.mostExpensiveRunId}`)}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {filteredAgents.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No agents found. Try adjusting your search or filters.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cost Trends */}
      {filteredAgents.length > 0 && filteredAgents[0].trend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Cost Trends (Top Agent)</CardTitle>
            <p className="text-sm text-muted-foreground">
              Daily cost for {filteredAgents[0].agentName}
            </p>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={filteredAgents[0].trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis tickFormatter={(v) => formatCost(v)} />
                <Tooltip formatter={(v: any) => formatCost(v)} />
                <Line type="monotone" dataKey="cost" stroke="#3b82f6" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

