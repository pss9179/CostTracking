import { API_BASE_URL } from "./utils";

export interface SpanSummary {
  id: number;
  trace_id: string;
  span_id: string;
  parent_span_id: string | null;
  name: string;
  model: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd: number;
  start_time: number;
  duration_ms: number | null;
  tenant_id: string;
  created_at: string;
}

export interface Trace {
  id: number;
  trace_id: string;
  tenant_id: string;
  root_span_name: string | null;
  workflow_name: string | null;
  total_cost_usd: number;
  total_tokens: number;
  span_count: number;
  start_time: number;
  duration_ms: number | null;
  created_at: string;
}

export interface Workflow {
  workflow_name: string;
  total_cost_usd: number;
  total_tokens: number;
  total_runs: number;
  avg_latency_ms: number;
  span_count: number;
  last_run: number;
}

export interface TraceDetail {
  trace: Trace;
  spans: SpanSummary[];
}

export interface Metrics {
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
  cost_by_model: Record<string, number>;
  cost_over_time: Record<string, number>;
}

export async function fetchSpans(traceId?: string, limit = 100): Promise<SpanSummary[]> {
  const url = new URL("/api/proxy/spans", window.location.origin);
  if (traceId) url.searchParams.set("trace_id", traceId);
  url.searchParams.set("limit", limit.toString());
  
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch spans");
  return res.json();
}

export async function fetchTraces(limit = 100): Promise<Trace[]> {
  const url = new URL("/api/proxy/traces", window.location.origin);
  url.searchParams.set("limit", limit.toString());
  
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch traces");
  return res.json();
}

export async function fetchTrace(traceId: string): Promise<TraceDetail> {
  const url = `/api/proxy/traces/${traceId}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch trace");
  return res.json();
}

export async function fetchMetrics(days = 7): Promise<Metrics> {
  const url = new URL("/api/proxy/metrics", window.location.origin);
  url.searchParams.set("days", days.toString());
  
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function runDemo(): Promise<{ status: string; trace_id: string }> {
  const res = await fetch("/api/proxy/demo/run", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run demo");
  return res.json();
}

export async function runFakeApp(): Promise<{ status: string; message: string }> {
  const res = await fetch("/api/proxy/demo/fake_app", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run fake app");
  return res.json();
}

export async function simulateAgent(workflowName?: string): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  tenant_id: string;
  outputs: {
    query: string;
    retrieval_count: number;
    summary: string;
  };
}> {
  const res = await fetch("/api/proxy/demo/simulate-agent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workflow_name: workflowName || null }),
  });
  if (!res.ok) throw new Error("Failed to simulate agent");
  return res.json();
}

export async function fetchWorkflows(limit = 100): Promise<Workflow[]> {
  const url = new URL("/api/proxy/workflows", window.location.origin);
  url.searchParams.set("limit", limit.toString());
  
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch workflows");
  return res.json();
}

export async function updateSpanName(
  spanId: string,
  spanName: string
): Promise<{ status: string; span: SpanSummary }> {
  const res = await fetch(`/api/proxy/spans/${spanId}/name`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ span_name: spanName }),
  });
  if (!res.ok) throw new Error("Failed to update span name");
  return res.json();
}

export async function updateWorkflowName(
  traceId: string,
  workflowName: string
): Promise<{ status: string; trace: Trace }> {
  const res = await fetch(`/api/proxy/traces/${traceId}/workflow-name`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workflow_name: workflowName }),
  });
  if (!res.ok) throw new Error("Failed to update workflow name");
  return res.json();
}

export async function updateWorkflowNameByName(
  workflowName: string,
  newWorkflowName: string
): Promise<{ status: string; updated_count: number }> {
  const res = await fetch(`/api/proxy/workflows/${encodeURIComponent(workflowName)}/name`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ workflow_name: newWorkflowName }),
  });
  if (!res.ok) throw new Error("Failed to update workflow name");
  return res.json();
}

export async function runGmailWorkflow(): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  tenant_id: string;
  result: any;
}> {
  const res = await fetch("/api/proxy/demo/gmail-workflow", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run Gmail workflow");
  return res.json();
}

export async function runCalendarWorkflow(): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  tenant_id: string;
  result: any;
}> {
  const res = await fetch("/api/proxy/demo/calendar-workflow", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run Calendar workflow");
  return res.json();
}

export async function runVapiWorkflow(): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  tenant_id: string;
  result: any;
}> {
  const res = await fetch("/api/proxy/demo/vapi-workflow", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run Vapi workflow");
  return res.json();
}

export async function runAllWorkflows(): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  tenant_id: string;
  result: any;
}> {
  const res = await fetch("/api/proxy/demo/run-all-workflows", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run all workflows");
  return res.json();
}

export async function runComplexWorkflows(): Promise<{
  status: string;
  trace_ids: string[];
  workflow_names: string[];
  tenant_id: string;
  result: any;
}> {
  const res = await fetch("/api/proxy/demo/complex-workflows", { method: "POST" });
  if (!res.ok) throw new Error("Failed to run complex workflows");
  return res.json();
}

export async function runComplexWorkflow(workflowNum: number): Promise<{
  status: string;
  trace_id: string;
  workflow_name: string;
  workflow_description: string;
  tenant_id: string;
  result: any;
}> {
  const res = await fetch(`/api/proxy/demo/complex-workflows/${workflowNum}`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to run complex workflow ${workflowNum}`);
  return res.json();
}

export async function clearAllData(): Promise<{
  status: string;
  message: string;
  spans_deleted: number;
  traces_deleted: number;
  tenant_id: string;
}> {
  const res = await fetch("/api/proxy/demo/clear-data", { method: "POST" });
  if (!res.ok) throw new Error("Failed to clear data");
  return res.json();
}

