"use client";

import { useState } from "react";
import { Workflow, updateWorkflowName } from "@/lib/api";
import { format } from "date-fns";
import { useMutation, useQueryClient } from "@tanstack/react-query";

interface WorkflowTableProps {
  workflows: Workflow[];
  onWorkflowClick?: (workflowName: string) => void;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function WorkflowTable({ workflows, onWorkflowClick }: WorkflowTableProps) {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const updateMutation = useMutation({
    mutationFn: ({ traceId, workflowName }: { traceId: string; workflowName: string }) =>
      updateWorkflowName(traceId, workflowName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["traces"] });
      setEditingId(null);
    },
  });

  const handleEdit = (workflow: Workflow) => {
    setEditingId(workflow.workflow_name);
    setEditValue(workflow.workflow_name);
  };

  const handleSave = (workflow: Workflow) => {
    // For now, we'll need trace_id to update - this is a limitation
    // In a real app, we'd need to track trace_id per workflow or have a different endpoint
    setEditingId(null);
  };

  if (workflows.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        No workflows found. Run a test agent to create one.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Workflow Name
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Total Cost
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Avg Latency
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Runs
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Spans
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Last Run
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {workflows.map((workflow) => (
            <tr
              key={workflow.workflow_name}
              className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
              onClick={() => onWorkflowClick?.(workflow.workflow_name)}
            >
              <td className="px-6 py-4 whitespace-nowrap">
                {editingId === workflow.workflow_name ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => handleSave(workflow)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSave(workflow);
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    autoFocus
                  />
                ) : (
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {workflow.workflow_name}
                  </span>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                ${workflow.total_cost_usd.toFixed(4)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {formatDuration(workflow.avg_latency_ms)}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {workflow.total_runs}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {workflow.span_count}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {format(new Date(workflow.last_run * 1000), "MMM d, HH:mm")}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEdit(workflow);
                  }}
                  className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                >
                  ✏️
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

