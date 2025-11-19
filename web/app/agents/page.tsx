"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRuns, fetchRunDetail } from "@/lib/api";
import { Pie, PieChart, ResponsiveContainer, Cell, Tooltip, Legend } from "recharts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface AgentStats {
  agent: string;
  calls: number;
  tokens: number;
  cost: number;
  avg_latency: number;
  errors: number;
}

// Colors per spec: Agent = slate
const AGENT_COLORS = ["#64748b", "#475569", "#334155", "#1e293b", "#0f172a"];

export default function AgentsPage() {
  const { getToken } = useAuth();
  const [agents, setAgents] = useState<AgentStats[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [treeData, setTreeData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const token = await getToken();
        if (!token) {
          console.error("No Clerk token available");
          return;
        }
        
        const runs = await fetchRuns(500, null, token);
        
        // Aggregate by agent (including untracked)
        const agentMap = new Map<string, AgentStats>();
        let untrackedStats: AgentStats = {
          agent: "untracked",
          calls: 0,
          tokens: 0,
          cost: 0,
          avg_latency: 0,
          errors: 0,
        };
        
        for (const run of runs.slice(0, 50)) {
          try {
            const detail = await fetchRunDetail(run.run_id, null, token);
            const events = detail.events || [];
            
            events.forEach((event: any) => {
              const section = event.section_path || event.section;
              const isAgent = section?.startsWith("agent:");
              const cost = event.cost_usd || 0;
              
              if (isAgent) {
                // Agent event
                const agentName = section.split("/")[0];
                const existing = agentMap.get(agentName) || {
                  agent: agentName,
                  calls: 0,
                  tokens: 0,
                  cost: 0,
                  avg_latency: 0,
                  errors: 0,
                };
                
                existing.calls++;
                existing.tokens += (event.input_tokens || 0) + (event.output_tokens || 0);
                existing.cost += cost;
                existing.avg_latency += event.latency_ms || 0;
                if (event.error_message) existing.errors++;
                
                agentMap.set(agentName, existing);
              } else if (cost > 0) {
                // Untracked event (only if has cost - still show it!)
                untrackedStats.calls++;
                untrackedStats.tokens += (event.input_tokens || 0) + (event.output_tokens || 0);
                untrackedStats.cost += cost;
                untrackedStats.avg_latency += event.latency_ms || 0;
                if (event.error_message) untrackedStats.errors++;
              }
            });
          } catch (err) {
            // Skip failed fetches
          }
        }
        
        // Calculate averages
        const agentList = Array.from(agentMap.values()).map(a => ({
          ...a,
          avg_latency: a.calls > 0 ? a.avg_latency / a.calls : 0,
        })).sort((a, b) => b.cost - a.cost);
        
        // Add untracked to the list if there are untracked costs
        if (untrackedStats.cost > 0) {
          untrackedStats.avg_latency = untrackedStats.calls > 0 ? untrackedStats.avg_latency / untrackedStats.calls : 0;
          agentList.push(untrackedStats);
        }
        
        setAgents(agentList);
      } catch (error) {
        console.error("Failed to load agents:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const totalCost = agents.reduce((sum, a) => sum + a.cost, 0);
  
  // Prepare chart data (filter out zero-cost agents for cleaner viz)
  const chartData = agents
    .filter(a => a.cost > 0)
    .slice(0, 5)
    .map((a, idx) => ({
      name: a.agent.replace("agent:", ""),
      value: parseFloat(a.cost.toFixed(6)),
      percentage: totalCost > 0 ? ((a.cost / totalCost) * 100).toFixed(1) : 0,
    }));

  return (
    <ProtectedLayout>
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Agents & Workflows</h1>
          <p className="text-muted-foreground mt-1">
            Hierarchical agent cost tracking and performance
          </p>
          {agents.some(a => a.agent === "untracked") && (
            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-md text-sm">
              <p className="text-amber-800">
                <strong>⚠️ Note:</strong> Some costs appear as "untracked" because they were not wrapped with agents or tools.
              </p>
              <p className="text-amber-700 text-xs mt-1">
                Use <code className="px-1 py-0.5 bg-amber-100 rounded">@agent("name")</code> and <code className="px-1 py-0.5 bg-amber-100 rounded">wrap_all_tools()</code> for accurate tracking.
              </p>
            </div>
          )}
        </div>

        {/* Split Layout */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Tree View */}
          <Card>
            <CardHeader>
              <CardTitle>Agent Hierarchy</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="h-64 flex items-center justify-center">
                  <p className="text-muted-foreground">Loading...</p>
                </div>
              ) : agents.length === 0 ? (
                <div className="h-64 flex items-center justify-center flex-col gap-2">
                  <p className="text-muted-foreground">No agent data available</p>
                  <p className="text-xs text-muted-foreground">
                    Use <code className="bg-muted px-2 py-1 rounded">with observe.section(&quot;agent:name&quot;)</code> to track agents
                  </p>
                </div>
              ) : (
                <div className="space-y-2 font-mono text-sm">
                  {agents.map((agent, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded cursor-pointer transition-colors ${
                        selectedAgent === agent.agent
                          ? "bg-slate-100 border-2 border-slate-600"
                          : "bg-muted hover:bg-muted/70"
                      }`}
                      onClick={() => setSelectedAgent(agent.agent)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-700">
                          {agent.agent.replace("agent:", "")}
                        </span>
                        <span className="text-green-600 font-semibold">
                          ${agent.cost.toFixed(6)}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {agent.calls} calls · {agent.tokens} tokens · {agent.avg_latency.toFixed(0)}ms avg
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Right: Chart + Table */}
          <div className="space-y-6">
            {/* Donut Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Cost by Agent</CardTitle>
              </CardHeader>
              <CardContent>
                {chartData.length === 0 ? (
                  <div className="h-64 flex items-center justify-center">
                    <p className="text-muted-foreground">No data</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        fill="#8884d8"
                        dataKey="value"
                        label={(entry) => `${entry.name}: $${entry.value.toFixed(6)}`}
                      >
                        {chartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={AGENT_COLORS[index % AGENT_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `$${value.toFixed(4)}`} />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            {/* Agent Table */}
            <Card>
              <CardHeader>
                <CardTitle>Agent Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Agent</TableHead>
                        <TableHead className="text-right">Calls</TableHead>
                        <TableHead className="text-right">Tokens</TableHead>
                        <TableHead className="text-right">Cost</TableHead>
                        <TableHead className="text-right">Avg Latency</TableHead>
                        <TableHead className="text-right">Errors</TableHead>
                        <TableHead className="text-right">% of Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {agents.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={7} className="text-center text-muted-foreground">
                            No agent data available
                          </TableCell>
                        </TableRow>
                      ) : (
                        agents.map((agent, idx) => (
                          <TableRow key={idx} className="hover:bg-muted/50">
                            <TableCell>
                              <Badge variant="secondary">{agent.agent.replace("agent:", "")}</Badge>
                            </TableCell>
                            <TableCell className="text-right">{agent.calls.toLocaleString()}</TableCell>
                            <TableCell className="text-right">{agent.tokens.toLocaleString()}</TableCell>
                            <TableCell className="text-right font-semibold">
                              ${agent.cost.toFixed(6)}
                            </TableCell>
                            <TableCell className="text-right">{agent.avg_latency.toFixed(0)}ms</TableCell>
                            <TableCell className="text-right">{agent.errors}</TableCell>
                            <TableCell className="text-right">
                              {totalCost > 0 ? ((agent.cost / totalCost) * 100).toFixed(1) : 0}%
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
