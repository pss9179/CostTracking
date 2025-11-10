const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CostEvent {
  id: number;
  tenant_id: string;
  workflow_id: string | null;
  provider: string;
  model: string | null;
  cost_usd: number;
  duration_ms: number;
  timestamp: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  operation: string | null;
}

export interface Metrics {
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
  cost_by_provider: Record<string, number>;
  cost_by_model: Record<string, number>;
  cost_over_time: Record<string, number>;
}

export interface Tenant {
  tenant_id: string;
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
}

export interface Workflow {
  workflow_id: string;
  tenant_id: string;
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
}

export async function fetchCosts(params?: {
  tenant_id?: string;
  workflow_id?: string;
  provider?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
}): Promise<{ events: CostEvent[]; total: number }> {
  const queryParams = new URLSearchParams();
  if (params?.tenant_id) queryParams.append('tenant_id', params.tenant_id);
  if (params?.workflow_id) queryParams.append('workflow_id', params.workflow_id);
  if (params?.provider) queryParams.append('provider', params.provider);
  if (params?.start_date) queryParams.append('start_date', params.start_date);
  if (params?.end_date) queryParams.append('end_date', params.end_date);
  if (params?.limit) queryParams.append('limit', params.limit.toString());

  const response = await fetch(`${API_BASE}/api/costs?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch costs');
  return response.json();
}

export async function fetchMetrics(tenant_id?: string, days: number = 7): Promise<Metrics> {
  const queryParams = new URLSearchParams();
  if (tenant_id) queryParams.append('tenant_id', tenant_id);
  queryParams.append('days', days.toString());

  const response = await fetch(`${API_BASE}/api/metrics?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
}

export async function fetchTenants(): Promise<{ tenants: Tenant[] }> {
  const response = await fetch(`${API_BASE}/api/tenants`);
  if (!response.ok) throw new Error('Failed to fetch tenants');
  return response.json();
}

export async function fetchWorkflows(tenant_id?: string): Promise<{ workflows: Workflow[] }> {
  const queryParams = new URLSearchParams();
  if (tenant_id) queryParams.append('tenant_id', tenant_id);

  const response = await fetch(`${API_BASE}/api/workflows?${queryParams}`);
  if (!response.ok) throw new Error('Failed to fetch workflows');
  return response.json();
}
