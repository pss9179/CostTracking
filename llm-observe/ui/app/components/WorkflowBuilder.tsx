"use client";

import { Workflow } from "@/lib/api";
import { format } from "date-fns";

interface WorkflowBuilderProps {
  workflows: Workflow[];
}

function getWorkflowIcon(name: string): string {
  if (name.includes("gmail") || name.includes("email")) return "📧";
  if (name.includes("calendar") || name.includes("gcal")) return "📅";
  if (name.includes("vapi") || name.includes("call")) return "📞";
  if (name.includes("gpt") || name.includes("llm")) return "🧠";
  if (name.includes("sequence")) return "🔄";
  return "⚙️";
}

function getStepIcon(step: string): string {
  if (step.includes("gmail") || step.includes("email")) return "📧";
  if (step.includes("calendar") || step.includes("gcal")) return "📅";
  if (step.includes("vapi") || step.includes("call")) return "📞";
  if (step.includes("gpt") || step.includes("llm")) return "🧠";
  return "•";
}

export function WorkflowBuilder({ workflows }: WorkflowBuilderProps) {
  // Group workflows by sequence pattern
  const workflowGroups = workflows.reduce((acc, w) => {
    const key = w.workflow_name.includes("sequence_1") ? "sequence_1"
      : w.workflow_name.includes("sequence_2") ? "sequence_2"
      : w.workflow_name.includes("sequence_3") ? "sequence_3"
      : "other";
    
    if (!acc[key]) acc[key] = [];
    acc[key].push(w);
    return acc;
  }, {} as Record<string, Workflow[]>);

  const getSequenceSteps = (workflowName: string): string[] => {
    if (workflowName.includes("sequence_1")) return ["📞 Vapi", "🧠 GPT", "📅 Calendar"];
    if (workflowName.includes("sequence_2")) return ["📅 Calendar", "🧠 GPT", "📞 Vapi"];
    if (workflowName.includes("sequence_3")) return ["📧 Gmail", "🧠 GPT", "📞 Vapi", "📅 Calendar"];
    return [];
  };

  if (workflows.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        No workflows found. Run "Run All" to create multiple workflows.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Workflow Sequences
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Sequence 1 */}
          {workflowGroups.sequence_1 && workflowGroups.sequence_1.length > 0 && (
            <div className="border border-blue-200 dark:border-blue-800 rounded-lg p-4 bg-blue-50 dark:bg-blue-900/20">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">{getWorkflowIcon(workflowGroups.sequence_1[0].workflow_name)}</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">Sequence 1</h4>
              </div>
              <div className="space-y-2 mb-3">
                {getSequenceSteps(workflowGroups.sequence_1[0].workflow_name).map((step, idx) => (
                  <div key={`seq1-${idx}`} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500 dark:text-gray-400">{idx + 1}.</span>
                    <span>{step}</span>
                    {idx < getSequenceSteps(workflowGroups.sequence_1[0].workflow_name).length - 1 && (
                      <span className="text-gray-400">→</span>
                    )}
                  </div>
                ))}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <div>Runs: {workflowGroups.sequence_1[0].total_runs}</div>
                <div>Cost: ${workflowGroups.sequence_1[0].total_cost_usd.toFixed(4)}</div>
                <div>Spans: {workflowGroups.sequence_1[0].span_count}</div>
              </div>
            </div>
          )}

          {/* Sequence 2 */}
          {workflowGroups.sequence_2 && workflowGroups.sequence_2.length > 0 && (
            <div className="border border-purple-200 dark:border-purple-800 rounded-lg p-4 bg-purple-50 dark:bg-purple-900/20">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">{getWorkflowIcon(workflowGroups.sequence_2[0].workflow_name)}</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">Sequence 2</h4>
              </div>
              <div className="space-y-2 mb-3">
                {getSequenceSteps(workflowGroups.sequence_2[0].workflow_name).map((step, idx) => (
                  <div key={`seq2-${idx}`} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500 dark:text-gray-400">{idx + 1}.</span>
                    <span>{step}</span>
                    {idx < getSequenceSteps(workflowGroups.sequence_2[0].workflow_name).length - 1 && (
                      <span className="text-gray-400">→</span>
                    )}
                  </div>
                ))}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <div>Runs: {workflowGroups.sequence_2[0].total_runs}</div>
                <div>Cost: ${workflowGroups.sequence_2[0].total_cost_usd.toFixed(4)}</div>
                <div>Spans: {workflowGroups.sequence_2[0].span_count}</div>
              </div>
            </div>
          )}

          {/* Sequence 3 */}
          {workflowGroups.sequence_3 && workflowGroups.sequence_3.length > 0 && (
            <div className="border border-green-200 dark:border-green-800 rounded-lg p-4 bg-green-50 dark:bg-green-900/20">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-2xl">{getWorkflowIcon(workflowGroups.sequence_3[0].workflow_name)}</span>
                <h4 className="font-semibold text-gray-900 dark:text-white">Sequence 3</h4>
              </div>
              <div className="space-y-2 mb-3">
                {getSequenceSteps(workflowGroups.sequence_3[0].workflow_name).map((step, idx) => (
                  <div key={`seq3-${idx}`} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-500 dark:text-gray-400">{idx + 1}.</span>
                    <span>{step}</span>
                    {idx < getSequenceSteps(workflowGroups.sequence_3[0].workflow_name).length - 1 && (
                      <span className="text-gray-400">→</span>
                    )}
                  </div>
                ))}
              </div>
              <div className="text-xs text-gray-600 dark:text-gray-400">
                <div>Runs: {workflowGroups.sequence_3[0].total_runs}</div>
                <div>Cost: ${workflowGroups.sequence_3[0].total_cost_usd.toFixed(4)}</div>
                <div>Spans: {workflowGroups.sequence_3[0].span_count}</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* All Workflows List */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          All Workflows ({workflows.length})
        </h3>
        <div className="space-y-2">
          {workflows.map((workflow, idx) => (
            <div
              key={`${workflow.workflow_name}-${idx}`}
              className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{getWorkflowIcon(workflow.workflow_name)}</span>
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {workflow.workflow_name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {format(new Date(workflow.last_run * 1000), "MMM d, HH:mm:ss")}
                  </div>
                </div>
              </div>
              <div className="text-right text-sm text-gray-600 dark:text-gray-400">
                <div>${workflow.total_cost_usd.toFixed(4)}</div>
                <div>{workflow.span_count} spans</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

