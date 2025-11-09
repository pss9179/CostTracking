"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchWorkflows,
  fetchMetrics,
  fetchTraces,
  fetchTrace,
  simulateAgent,
} from "@/lib/api";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { WorkflowTable } from "./components/WorkflowTable";
import { TraceTree } from "./components/TraceTree";
import { WorkflowModal } from "./components/WorkflowModal";

const COLORS = {
  gpt: "#3b82f6", // blue
  pinecone: "#10b981", // green
  other: "#f97316", // orange
};

function getProviderColor(name: string): string {
  if (name.includes("gpt") || name.includes("llm")) return COLORS.gpt;
  if (name.includes("pinecone")) return COLORS.pinecone;
  return COLORS.other;
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);

  // Load workflows
  const { data: workflows = [], isLoading: workflowsLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: () => fetchWorkflows(100),
  });

  // Load metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["metrics"],
    queryFn: () => fetchMetrics(7),
  });

  // Load traces for selected workflow
  const { data: traces = [] } = useQuery({
    queryKey: ["traces", selectedWorkflow],
    queryFn: () => fetchTraces(100),
    enabled: !!selectedWorkflow,
  });

  // Load trace detail for tree view
  const { data: traceDetail, refetch: refetchTrace } = useQuery({
    queryKey: ["trace", selectedTraceId],
    queryFn: () => fetchTrace(selectedTraceId!),
    enabled: !!selectedTraceId,
  });

  // Simulate agent mutation
  const simulateMutation = useMutation({
    mutationFn: (workflowName?: string) => simulateAgent(workflowName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
      queryClient.invalidateQueries({ queryKey: ["traces"] });
      setIsModalOpen(false);
    },
  });

  // Prepare chart data
  const costOverTimeData =
    metrics?.cost_over_time
      ? Object.entries(metrics.cost_over_time)
          .map(([date, cost]) => ({
            date,
            cost: Number(cost.toFixed(4)),
          }))
          .sort((a, b) => a.date.localeCompare(b.date))
      : [];

  // Cost per provider (group spans by provider)
  const costByProviderData = workflows.reduce(
    (acc, workflow) => {
      // For now, estimate provider costs from workflow name patterns
      // In production, this would come from span-level provider data
      const provider = workflow.workflow_name.includes("pinecone")
        ? "Pinecone"
        : workflow.workflow_name.includes("gpt") || workflow.workflow_name.includes("llm")
        ? "GPT"
        : "Other";
      acc[provider] = (acc[provider] || 0) + workflow.total_cost_usd;
      return acc;
    },
    {} as Record<string, number>
  );

  const pieData = Object.entries(costByProviderData).map(([name, value]) => ({
    name,
    value: Number(value.toFixed(4)),
  }));

  // Latency per step (from workflows)
  const latencyData = workflows
    .filter((w) => w.avg_latency_ms > 0)
    .slice(0, 10)
    .map((w) => ({
      workflow: w.workflow_name.slice(0, 20),
      latency: w.avg_latency_ms,
    }));

  const handleRunAgent = (workflowName?: string) => {
    simulateMutation.mutate(workflowName);
  };

  const handleWorkflowClick = (workflowName: string) => {
    setSelectedWorkflow(workflowName);
    // Find first trace for this workflow
    const workflowTraces = traces.filter(
      (t) => t.workflow_name === workflowName
    );
    if (workflowTraces.length > 0) {
      setSelectedTraceId(workflowTraces[0].trace_id);
    }
  };

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Workflows
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Monitor AI agent workflows, costs, and performance
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-lg"
          >
            Run Test Agent
          </button>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Total Cost (7d)
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              ${metricsLoading ? "..." : metrics?.total_cost_usd.toFixed(4) || "0.0000"}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Total Tokens (7d)
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {metricsLoading ? "..." : metrics?.total_tokens.toLocaleString() || "0"}
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
              Total Requests (7d)
            </h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">
              {metricsLoading ? "..." : metrics?.total_requests || "0"}
            </p>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Cost Over Time */}
          <div className="lg:col-span-2 bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Cost Over Time
            </h3>
            {costOverTimeData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={costOverTimeData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e7eb",
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    stroke="#3b82f6"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-12">
                No data available
              </p>
            )}
          </div>

          {/* Cost per Provider */}
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Cost per Provider
            </h3>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name}: ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.name === "GPT"
                            ? COLORS.gpt
                            : entry.name === "Pinecone"
                            ? COLORS.pinecone
                            : COLORS.other
                        }
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-12">
                No data available
              </p>
            )}
          </div>
        </div>

        {/* Latency per Step */}
        {latencyData.length > 0 && (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-8">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Latency per Step
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="workflow" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                  }}
                />
                <Legend />
                <Bar dataKey="latency" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Workflows Table */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow mb-8">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Workflows
          </h3>
          {workflowsLoading ? (
            <p className="text-gray-500 dark:text-gray-400">Loading...</p>
          ) : (
            <WorkflowTable
              workflows={workflows}
              onWorkflowClick={handleWorkflowClick}
            />
          )}
        </div>

        {/* Trace Tree */}
        {traceDetail ? (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Trace Tree - {traceDetail.trace.workflow_name || "Untitled Workflow"}
              </h3>
              <button
                onClick={() => setSelectedTraceId(null)}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                ✕ Close
              </button>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Click the ✏️ icon next to any span name to rename it. Expand/collapse spans using ▶/▼.
            </p>
            <TraceTree spans={traceDetail.spans} onUpdate={() => refetchTrace()} />
          </div>
        ) : selectedWorkflow && (
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
            <p className="text-gray-500 dark:text-gray-400">
              Click on a workflow row above to view its trace tree and spans.
            </p>
          </div>
        )}
      </div>

      {/* Workflow Modal */}
      <WorkflowModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleRunAgent}
      />
    </div>
  );
}
