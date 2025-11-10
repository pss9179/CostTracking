"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Workflow, Trace, fetchTraces, fetchTrace, SpanSummary } from "@/lib/api";
import { cn } from "@/lib/utils";

interface WorkflowStep {
  name: string;
  type: string;
  icon: string;
  color: string;
  children?: WorkflowStep[];
}

function getStepType(spanName: string): { type: string; icon: string; color: string } {
  const name = spanName.toLowerCase();
  
  if (name.includes("workflow.")) {
    return { type: "nested", icon: "🔄", color: "bg-indigo-500" };
  }
  if (name.includes("gpt") || name.includes("llm.request") || name.includes("openai")) {
    return { type: "gpt", icon: "🧠", color: "bg-blue-500" };
  }
  if (name.includes("vapi") || name.includes("call")) {
    return { type: "vapi", icon: "📞", color: "bg-orange-500" };
  }
  if (name.includes("gmail") || name.includes("email")) {
    return { type: "gmail", icon: "📧", color: "bg-green-500" };
  }
  if (name.includes("calendar") || name.includes("gcal")) {
    return { type: "calendar", icon: "📅", color: "bg-purple-500" };
  }
  if (name.includes("pinecone")) {
    return { type: "pinecone", icon: "🔍", color: "bg-emerald-500" };
  }
  if (name.includes("start")) {
    return { type: "start", icon: "▶", color: "bg-purple-500" };
  }
  
  return { type: "other", icon: "⚙️", color: "bg-gray-500" };
}

function buildSpanTree(spans: SpanSummary[]): { root: SpanSummary | null; tree: Map<string, SpanSummary[]> } {
  const tree = new Map<string, SpanSummary[]>();
  let root: SpanSummary | null = null;

  // Find root span (no parent)
  spans.forEach((span) => {
    if (!span.parent_span_id) {
      root = span;
    } else {
      if (!tree.has(span.parent_span_id)) {
        tree.set(span.parent_span_id, []);
      }
      tree.get(span.parent_span_id)!.push(span);
    }
  });

  // Sort children by start_time
  tree.forEach((children) => {
    children.sort((a, b) => a.start_time - b.start_time);
  });

  return { root, tree };
}

function buildWorkflowSteps(
  span: SpanSummary,
  tree: Map<string, SpanSummary[]>,
  visited: Set<string> = new Set()
): WorkflowStep[] {
  if (visited.has(span.span_id)) {
    return []; // Prevent infinite loops
  }
  visited.add(span.span_id);

  const stepType = getStepType(span.name);
  
  // Clean up span name for display
  let displayName = span.name
    .replace("workflow.", "")
    .replace("llm.request", "GPT")
    .replace("openai.chat", "GPT")
    .replace("gmail.", "Gmail ")
    .replace("gcal.", "Calendar ")
    .replace("vapi.", "Vapi ")
    .replace("pinecone.", "Pinecone ");
  
  // Capitalize first letter
  displayName = displayName.charAt(0).toUpperCase() + displayName.slice(1);

  const step: WorkflowStep = {
    name: displayName,
    type: stepType.type,
    icon: stepType.icon,
    color: stepType.color,
  };

  // Get children and sort by start_time
  const children = (tree.get(span.span_id) || []).sort((a, b) => a.start_time - b.start_time);
  
  // For workflow spans, we want to show children inline (not nested)
  // For other spans, we can nest if needed
  if (children.length > 0) {
    step.children = [];
    children.forEach((child) => {
      const childSteps = buildWorkflowSteps(child, tree, visited);
      step.children!.push(...childSteps);
    });
  }

  return [step];
}

interface WorkflowFlowBuilderProps {
  workflows: Workflow[];
  showComplexOnly?: boolean;
}

function WorkflowFlowCard({ 
  workflow, 
  trace 
}: { 
  workflow: Workflow; 
  trace: Trace | null;
}) {
  const [expanded, setExpanded] = useState(true);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);

  // Fetch the LATEST trace for this workflow (not just the one passed)
  const { data: traces = [] } = useQuery({
    queryKey: ["traces"],
    queryFn: () => fetchTraces(100),
  });

  // Find the latest trace for this workflow
  const latestTrace = traces
    .filter((t) => t.workflow_name === workflow.workflow_name)
    .sort((a, b) => (b.start_time || 0) - (a.start_time || 0))[0] || trace;

  // Fetch trace details to get spans
  const { data: traceDetail, isLoading: loadingSpans } = useQuery({
    queryKey: ["trace", latestTrace?.trace_id],
    queryFn: () => fetchTrace(latestTrace!.trace_id),
    enabled: !!latestTrace,
  });

  useEffect(() => {
    if (traceDetail?.spans && traceDetail.spans.length > 0) {
      const { root, tree } = buildSpanTree(traceDetail.spans);
      if (root) {
        // Start building from root's children directly (skip root workflow span)
        const children = tree.get(root.span_id) || [];
        if (children.length > 0) {
          const workflowSteps: WorkflowStep[] = [];
          children.forEach((child) => {
            const childSteps = buildWorkflowSteps(child, tree);
            workflowSteps.push(...childSteps);
          });
          setSteps(workflowSteps);
        } else {
          // If no children, show root as fallback
          const workflowSteps = buildWorkflowSteps(root, tree);
          setSteps(workflowSteps);
        }
      }
    }
  }, [traceDetail]);

  // Flatten steps for display - show nested workflows with their children inline
  const flattenSteps = (steps: WorkflowStep[]): WorkflowStep[] => {
    const result: WorkflowStep[] = [];
    steps.forEach((step) => {
      // For nested workflow spans, show the workflow name, then its children
      if (step.type === "nested" && step.children && step.children.length > 0) {
        result.push({ ...step, children: undefined });
        result.push(...flattenSteps(step.children));
      } else {
        // For regular spans, add them and recursively process children
        result.push({ ...step, children: undefined });
        if (step.children && step.children.length > 0) {
          result.push(...flattenSteps(step.children));
        }
      }
    });
    return result;
  };

  const displaySteps = flattenSteps(steps);

  return (
    <div className="bg-gray-50 dark:bg-gray-900/50 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className={cn(
              "text-xl transition-transform duration-200 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white",
              expanded && "rotate-90"
            )}
            title={expanded ? "Collapse" : "Expand"}
          >
            ▶
          </button>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
            {workflow.workflow_name}
          </h4>
        </div>
        <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1 text-right">
          <div className="font-medium">Runs: {workflow.total_runs}</div>
          <div>Cost: <span className="font-medium">${workflow.total_cost_usd.toFixed(4)}</span></div>
          <div>Spans: {workflow.span_count}</div>
        </div>
      </div>

      {/* Flow Diagram */}
      {expanded && (
        <div className="bg-gray-100 dark:bg-gray-900/50 rounded-lg p-8 border border-gray-200 dark:border-gray-700" style={{
          backgroundImage: 'radial-gradient(circle, #d1d5db 1px, transparent 1px)',
          backgroundSize: '20px 20px',
        }}>
          {loadingSpans ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Loading spans...
            </div>
          ) : displaySteps.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              {latestTrace ? "No spans found in trace" : "No trace data available. Run this workflow first."}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-0 bg-transparent">
              {/* Start node */}
              <div className="flex flex-col items-center w-full">
                <div className="relative w-full max-w-xs">
                  <div className="bg-purple-500 rounded-t-lg px-4 py-3 flex items-center gap-2 shadow-sm">
                    <span className="text-white text-xl">▶</span>
                    <span className="text-white font-semibold text-sm">Start</span>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-b-lg border-x border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm">
                    <p className="text-sm text-gray-900 dark:text-white font-medium">
                      Workflow starts
                    </p>
                  </div>
                </div>
                {displaySteps.length > 0 && (
                  <div className="flex flex-col items-center my-1">
                    <svg className="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                )}
              </div>

              {/* Workflow steps */}
              {displaySteps.map((step, idx) => (
                <WorkflowNode
                  key={`${workflow.workflow_name}-${idx}`}
                  step={step}
                  isLast={idx === displaySteps.length - 1}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function WorkflowNode({ step, isLast }: { step: WorkflowStep; isLast: boolean }) {
  return (
    <div className="flex flex-col items-center w-full">
      {/* Node */}
      <div className="relative w-full max-w-xs">
        {/* Header Bar */}
        <div className={cn("rounded-t-lg px-4 py-3 flex items-center gap-2 shadow-sm", step.color)}>
          <span className="text-white text-xl">{step.icon}</span>
          <span className="text-white font-semibold text-sm truncate">{step.name}</span>
        </div>
        
        {/* Body */}
        <div className="bg-white dark:bg-gray-800 rounded-b-lg border-x border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-900 dark:text-white font-medium break-words">
                {step.name}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
                title="Remove"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <button
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                title="Settings"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Arrow */}
      {!isLast && (
        <div className="flex flex-col items-center my-1">
          <svg className="w-5 h-5 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      )}
    </div>
  );
}

export function WorkflowFlowBuilder({ workflows, showComplexOnly = false }: WorkflowFlowBuilderProps) {
  // Fetch all traces - refetch when workflows change
  const { data: traces = [], isLoading: tracesLoading } = useQuery({
    queryKey: ["traces"],
    queryFn: () => fetchTraces(100),
    refetchOnMount: true,
    refetchOnWindowFocus: true,
  });

  // Filter complex workflows if needed
  const complexWorkflowNames = [
    "gpt_vapi_google_workflow",
    "vapi_google_pinecone_workflow",
    "nested_async_workflow",
    "parallel_workflows_with_nesting",
    "deeply_nested_workflow",
  ];

  const workflowsToShow = showComplexOnly
    ? workflows.filter((w) => complexWorkflowNames.includes(w.workflow_name))
    : workflows;

  // Match workflows with their traces
  const workflowsWithTraces = workflowsToShow.map((workflow) => {
    const trace = traces.find((t) => t.workflow_name === workflow.workflow_name);
    return { workflow, trace };
  });

  if (tracesLoading) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <div className="animate-pulse">Loading traces...</div>
      </div>
    );
  }

  if (workflowsToShow.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <p className="mb-4">
          {showComplexOnly
            ? "No complex workflows found. Click '🔥 Complex Workflows' to run them."
            : "No workflows found. Run workflows to see their flow diagrams."}
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500">
          Workflows will appear here once they have been executed.
        </p>
      </div>
    );
  }

  // Filter to only show workflows that have traces
  const workflowsWithTracesFiltered = workflowsWithTraces.filter(({ trace }) => !!trace);
  
  if (workflowsWithTracesFiltered.length === 0 && workflowsToShow.length > 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <p className="mb-4">Found {workflowsToShow.length} workflow(s), but no trace data yet.</p>
        <p className="text-sm text-gray-400 dark:text-gray-500">
          Traces are being loaded... This may take a few seconds after running workflows.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {workflowsWithTraces
          .filter(({ trace }) => !!trace) // Only show workflows with traces
          .map(({ workflow, trace }) => (
            <WorkflowFlowCard
              key={workflow.workflow_name}
              workflow={workflow}
              trace={trace || null}
            />
          ))}
      </div>
    </div>
  );
}
