const COLLECTOR_URL = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";

// Helper function to get tenant_id from Clerk user
// For multi-tenancy: Each Clerk user becomes a tenant (using their user.id)
export function getTenantId(userId: string | null | undefined): string | null {
  if (!userId) return null;
  // Use Clerk user ID as tenant_id for multi-tenant isolation
  return userId;
}

// Types
export interface Run {
  run_id: string;
  started_at: string;
  total_cost: number;
  call_count: number;
  sections: string[];
  top_section: string;
}

export interface RunDetail {
  run_id: string;
  total_cost: number;
  breakdown: {
    by_section: Array<{
      section: string;
      cost: number;
      count: number;
      percentage: number;
    }>;
    by_provider: Array<{
      provider: string;
      cost: number;
      count: number;
      percentage: number;
    }>;
    by_model: Array<{
      model: string;
      cost: number;
      count: number;
      percentage: number;
    }>;
  };
  events: Array<{
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
    customer_id: string | null;
  }>;
}

export interface ProviderStats {
  provider: string;
  total_cost: number;
  call_count: number;
  percentage: number;
  avg_latency?: number;
  error_count?: number;
}

export interface Insight {
  type: string;
  section?: string;
  provider?: string;
  endpoint?: string;
  delta?: number;
  expensive_model?: string;
  cheaper_alternative?: string;
  p95_calls?: number;
  message: string;
}

export interface Cap {
  id: string;
  cap_type: string;
  target_name: string | null;
  limit_amount: number;
  period: string;
  alert_threshold: number;
  alert_email: string | null;
  enabled: boolean;
  current_spend: number;
  percentage_used: number;
  created_at: string;
  updated_at: string;
}

export interface CapCreate {
  cap_type: string;
  target_name?: string | null;
  limit_amount: number;
  period: string;
  alert_threshold: number;
  alert_email?: string | null;
}

export interface CapUpdate {
  limit_amount?: number;
  alert_threshold?: number;
  alert_email?: string | null;
  enabled?: boolean;
}

export interface ProviderTier {
  id: string;
  provider: string;
  tier: string;
  plan_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export async function fetchProviderTiers(tenantId?: string | null): Promise<ProviderTier[]> {
  const headers = await getAuthHeaders();
  let url = `${COLLECTOR_URL}/provider-tiers/`;
  if (tenantId) {
    url += `?tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, { headers });
  if (!response.ok) {
    throw new Error(`Failed to fetch provider tiers: ${response.statusText}`);
  }
  return response.json();
}

export async function setProviderTier(
  provider: string,
  tier: string,
  planName?: string,
  tenantId?: string | null
): Promise<ProviderTier> {
  const headers = await getAuthHeaders();
  let url = `${COLLECTOR_URL}/provider-tiers/?provider=${encodeURIComponent(provider)}&tier=${encodeURIComponent(tier)}`;
  if (planName) {
    url += `&plan_name=${encodeURIComponent(planName)}`;
  }
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    method: "POST",
    headers,
  });
  if (!response.ok) {
    throw new Error(`Failed to set provider tier: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteProviderTier(
  provider: string,
  tenantId?: string | null
): Promise<void> {
  const headers = await getAuthHeaders();
  let url = `${COLLECTOR_URL}/provider-tiers/${encodeURIComponent(provider)}`;
  if (tenantId) {
    url += `?tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    method: "DELETE",
    headers,
  });
  if (!response.ok) {
    throw new Error(`Failed to delete provider tier: ${response.statusText}`);
  }
}

export interface Alert {
  id: string;
  alert_type: string;
  current_spend: number;
  cap_limit: number;
  percentage: number;
  target_type: string;
  target_name: string | null;
  period_start: string;
  period_end: string;
  email_sent: boolean;
  created_at: string;
}

// Helper function to get Clerk token (for dashboard queries)
async function getClerkToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  
  // Dynamic import to avoid SSR issues
  try {
    const { getToken } = await import("@clerk/nextjs/server");
    // For client-side, we need to use the client-side getToken
    // This is a workaround - in production, pass token from page components
    return null;
  } catch {
    return null;
  }
}

// Helper function to get auth headers for dashboard queries (uses Clerk token)
export async function getDashboardAuthHeaders(): Promise<HeadersInit> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Get Clerk token from window (set by page components)
  if (typeof window !== "undefined") {
    const clerkToken = (window as any).__clerkToken;
    if (clerkToken) {
      headers["Authorization"] = `Bearer ${clerkToken}`;
    }
  }

  return headers;
}

// Helper function to get auth headers for SDK calls (uses API key)
async function getAuthHeaders(): Promise<HeadersInit> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Try to get API key from localStorage (set in settings page)
  if (typeof window !== "undefined") {
    const apiKey = localStorage.getItem("api_key");
    if (apiKey) {
      headers["Authorization"] = `Bearer ${apiKey}`;
    }
  }

  return headers;
}

// API Functions
export async function fetchRuns(limit: number = 50, tenantId?: string | null): Promise<Run[]> {
  const headers = await getDashboardAuthHeaders();
  let url = `${COLLECTOR_URL}/runs/latest?limit=${limit}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch runs: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchRunDetail(runId: string, tenantId?: string | null): Promise<RunDetail> {
  const headers = await getDashboardAuthHeaders();
  let url = `${COLLECTOR_URL}/runs/${runId}`;
  if (tenantId) {
    url += `?tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch run detail: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchProviderStats(hours: number = 24, tenantId?: string | null): Promise<ProviderStats[]> {
  const headers = await getDashboardAuthHeaders();
  let url = `${COLLECTOR_URL}/stats/by-provider?hours=${hours}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch provider stats: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchInsights(tenantId?: string | null): Promise<Insight[]> {
  const headers = await getAuthHeaders();
  let url = `${COLLECTOR_URL}/insights/daily`;
  if (tenantId) {
    url += `?tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch insights: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchCaps(): Promise<Cap[]> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${COLLECTOR_URL}/caps/`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch caps: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchAlerts(limit: number = 50): Promise<Alert[]> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${COLLECTOR_URL}/caps/alerts/?limit=${limit}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch alerts: ${response.statusText}`);
  }

  return response.json();
}

export async function createCap(cap: CapCreate): Promise<Cap> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${COLLECTOR_URL}/caps/`, {
    method: "POST",
    headers,
    body: JSON.stringify(cap),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to create cap: ${response.statusText}`);
  }

  return response.json();
}

export async function updateCap(capId: string, cap: CapUpdate): Promise<Cap> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${COLLECTOR_URL}/caps/${capId}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(cap),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Failed to update cap: ${response.statusText}`);
  }

  return response.json();
}

export async function deleteCap(capId: string): Promise<void> {
  const headers = await getAuthHeaders();
  const response = await fetch(`${COLLECTOR_URL}/caps/${capId}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to delete cap: ${response.statusText}`);
  }
}

