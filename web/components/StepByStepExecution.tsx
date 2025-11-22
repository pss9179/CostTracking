"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatCost } from "@/lib/stats";

interface TraceEvent {
  id: string;
  span_id: string;
  parent_span_id: string | null;
  section: string;
  section_path: string | null;
  provider: string;
  endpoint: string;
  model: string | null;
  cost_usd: number;
  latency_ms: number;
  input_tokens: number | null;
  output_tokens: number | null;
  status: string;
  created_at: string;
  semantic_label?: string | null;
}

interface StepByStepExecutionProps {
  events: TraceEvent[];
}

interface ExecutionStep {
  stepNumber: number;
  section: string;
  sectionPath: string | null;
  semanticLabel: string | null;
  apiCalls: TraceEvent[];
  totalCost: number;
  totalLatency: number;
  startTime: string;
  endTime: string;
}

export function StepByStepExecution({ events }: StepByStepExecutionProps) {
  // Group events by section_path or section to create steps
  const steps: ExecutionStep[] = [];
  const sectionMap = new Map<string, TraceEvent[]>();

  // Group events by section_path (or section if no path)
  events.forEach((event) => {
    const key = event.section_path || event.section || "untracked";
    if (!sectionMap.has(key)) {
      sectionMap.set(key, []);
    }
    sectionMap.get(key)!.push(event);
  });

  // Convert to steps
  let stepNumber = 1;
  sectionMap.forEach((apiCalls, sectionKey) => {
    if (apiCalls.length === 0) return;

    // Sort by timestamp
    const sortedCalls = [...apiCalls].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );

    const totalCost = sortedCalls.reduce((sum, e) => sum + e.cost_usd, 0);
    const totalLatency = sortedCalls.reduce((sum, e) => sum + e.latency_ms, 0);
    const startTime = sortedCalls[0].created_at;
    const endTime = sortedCalls[sortedCalls.length - 1].created_at;

    // Extract semantic label from first event
    const semanticLabel = sortedCalls[0].semantic_label || null;

    steps.push({
      stepNumber: stepNumber++,
      section: sortedCalls[0].section,
      sectionPath: sortedCalls[0].section_path,
      semanticLabel,
      apiCalls: sortedCalls,
      totalCost,
      totalLatency,
      startTime,
      endTime,
    });
  });

  // Sort steps by start time
  steps.sort((a, b) => new Date(a.startTime).getTime() - new Date(b.startTime).getTime());

  // Re-number steps
  steps.forEach((step, index) => {
    step.stepNumber = index + 1;
  });

  const totalRunCost = steps.reduce((sum, s) => sum + s.totalCost, 0);

  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No execution steps found
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card className="border-0 shadow-sm bg-white">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold mb-1">Execution Summary</h3>
              <p className="text-sm text-gray-600">
                {steps.length} step{steps.length !== 1 ? "s" : ""} • Total: {formatCost(totalRunCost)}
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{formatCost(totalRunCost)}</div>
              <div className="text-xs text-gray-500">Total Cost</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step) => (
          <Card key={step.stepNumber} className="border-0 shadow-sm bg-white hover:shadow-md transition-shadow">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-sm">
                      {step.stepNumber}
                    </div>
                    <div>
                      <div className="font-semibold text-gray-900">
                        {step.sectionPath || step.section}
                      </div>
                      {step.semanticLabel && (
                        <Badge variant="secondary" className="mt-1 text-xs">
                          {step.semanticLabel}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-gray-900">{formatCost(step.totalCost)}</div>
                  <div className="text-xs text-gray-500">
                    {step.apiCalls.length} API call{step.apiCalls.length !== 1 ? "s" : ""}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {step.totalLatency.toFixed(0)}ms total
                  </div>
                </div>
              </div>

              {/* API Calls Breakdown */}
              {step.apiCalls.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="space-y-2">
                    {step.apiCalls.map((call, idx) => (
                      <div
                        key={call.id}
                        className="flex items-center justify-between text-sm py-2 px-3 rounded-md bg-gray-50 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <Badge variant="outline" className="text-xs">
                            {call.provider}
                          </Badge>
                          <span className="text-gray-700 font-mono text-xs">
                            {call.endpoint}
                          </span>
                          {call.model && (
                            <span className="text-gray-500 text-xs">
                              {call.model}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs">
                          <span className="text-gray-600">
                            {call.latency_ms.toFixed(0)}ms
                          </span>
                          {(call.input_tokens || call.output_tokens) && (
                            <span className="text-gray-500">
                              {call.input_tokens || 0}/{call.output_tokens || 0} tokens
                            </span>
                          )}
                          <span className="font-semibold text-gray-900">
                            {formatCost(call.cost_usd)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

