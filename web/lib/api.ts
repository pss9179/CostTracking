"use client";

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
    semantic_label?: string | null;
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
  enforcement: string;
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
  enforcement?: string;
  alert_threshold: number;
  alert_email?: string | null;
}

export interface CapUpdate {
  limit_amount?: number;
  enforcement?: string;
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

export async function fetchProviderTiers(tenantId?: string | null, token?: string): Promise<ProviderTier[]> {
  const headers = await getDashboardAuthHeaders(token);
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
  tenantId?: string | null,
  token?: string
): Promise<ProviderTier> {
  const headers = await getDashboardAuthHeaders(token);
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
  tenantId?: string | null,
  token?: string
): Promise<void> {
  const headers = await getDashboardAuthHeaders(token);
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

// Helper function to get auth headers for dashboard queries (uses Clerk token)
// IMPORTANT: This function REQUIRES a token to be passed. It will NOT include Authorization
// header if no token is provided. All callers must pass a token obtained via getToken()
export async function getDashboardAuthHeaders(token?: string): Promise<HeadersInit> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  // Token MUST be provided - no fallback to window.__clerkToken for reliability
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    // Log warning if no token provided (but don't throw to avoid breaking existing code)
    if (typeof window !== "undefined") {
      console.warn("getDashboardAuthHeaders called without token - Authorization header will be missing");
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
export async function fetchRuns(limit: number = 50, tenantId?: string | null, token?: string): Promise<Run[]> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/runs/latest?limit=${limit}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch runs (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function fetchRunDetail(runId: string, tenantId?: string | null, token?: string): Promise<RunDetail> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/runs/${runId}`;
  if (tenantId) {
    url += `?tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch run detail (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function fetchProviderStats(hours: number = 24, tenantId?: string | null, token?: string): Promise<ProviderStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/stats/by-provider?hours=${hours}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch provider stats (${response.status}): ${errorText}`);
  }

  return response.json();
}

export interface ModelStats {
  model: string;
  provider: string;
  total_cost: number;
  call_count: number;
  input_tokens: number;
  output_tokens: number;
  avg_latency: number;
  percentage: number;
}

export async function fetchModelStats(hours: number = 24, tenantId?: string | null, token?: string): Promise<ModelStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/stats/by-model?hours=${hours}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch model stats (${response.status}): ${errorText}`);
  }

  return response.json();
}

export interface DailyStats {
  date: string;
  total: number;
  providers: Record<string, { cost: number; calls: number }>;
}

export async function fetchDailyStats(days: number = 7, tenantId?: string | null, token?: string): Promise<DailyStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/stats/daily?days=${days}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch daily stats (${response.status}): ${errorText}`);
  }

  return response.json();
}

// Section/Feature Stats
export interface SectionStats {
  section: string;
  section_path: string | null;
  total_cost: number;
  call_count: number;
  avg_latency_ms: number;
  percentage: number;
}

export async function fetchSectionStats(hours: number = 24, tenantId?: string | null, token?: string): Promise<SectionStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  let url = `${COLLECTOR_URL}/stats/by-section?hours=${hours}`;
  if (tenantId) {
    url += `&tenant_id=${encodeURIComponent(tenantId)}`;
  }
  const response = await fetch(url, {
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    throw new Error(`Failed to fetch section stats (${response.status}): ${errorText}`);
  }

  return response.json();
}

export async function fetchInsights(tenantId?: string | null, token?: string): Promise<Insight[]> {
  const headers = await getDashboardAuthHeaders(token);
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

export async function fetchCaps(token?: string): Promise<Cap[]> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/caps/`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch caps: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchAlerts(limit: number = 50, token?: string): Promise<Alert[]> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/caps/alerts/?limit=${limit}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch alerts: ${response.statusText}`);
  }

  return response.json();
}

export async function createCap(cap: CapCreate, token?: string): Promise<Cap> {
  const headers = await getDashboardAuthHeaders(token);
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

export async function updateCap(capId: string, cap: CapUpdate, token?: string): Promise<Cap> {
  const headers = await getDashboardAuthHeaders(token);
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

export async function deleteCap(capId: string, token?: string): Promise<void> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/caps/${capId}`, {
    method: "DELETE",
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to delete cap: ${response.statusText}`);
  }
}

// Voice AI Types
export interface VoiceCall {
  voice_call_id: string;
  customer_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  total_cost: number;
  total_duration_seconds: number;
  total_latency_ms: number;
  cost_per_minute: number;
  segments: {
    [key: string]: {
      cost: number;
      duration_seconds: number;
      latency_ms: number;
      event_count: number;
    };
  };
}

export interface VoiceProviderStats {
  provider: string;
  total_cost: number;
  total_duration_seconds: number;
  total_duration_minutes: number;
  call_count: number;
  event_count: number;
  avg_latency_ms: number;
  cost_per_minute: number;
  percentage: number;
}

export interface VoiceSegmentStats {
  segment_type: string;
  total_cost: number;
  total_duration_seconds: number;
  event_count: number;
  avg_latency_ms: number;
  cost_per_minute: number;
  percentage: number;
}

export interface VoiceCostPerMinute {
  total_cost: number;
  total_duration_seconds: number;
  total_duration_minutes: number;
  total_calls: number;
  total_events: number;
  cost_per_minute: number;
  cost_per_call: number;
  avg_call_duration_seconds: number;
  time_window_hours: number;
}

export interface VoiceForecast {
  last_7_days: {
    total_cost: number;
    total_duration_minutes: number;
    total_calls: number;
  };
  daily_average: {
    cost: number;
    duration_minutes: number;
    calls: number;
  };
  monthly_projection: {
    cost: number;
    duration_minutes: number;
    calls: number;
  };
  note: string;
}

// Voice AI API Functions
export async function fetchVoiceCalls(hours: number = 24, limit: number = 50, token?: string): Promise<VoiceCall[]> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/calls?hours=${hours}&limit=${limit}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice calls: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchVoiceProviderStats(hours: number = 24, token?: string): Promise<VoiceProviderStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/by-provider?hours=${hours}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice provider stats: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchVoiceSegmentStats(hours: number = 24, token?: string): Promise<VoiceSegmentStats[]> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/by-segment?hours=${hours}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice segment stats: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchVoiceCostPerMinute(hours: number = 24, token?: string): Promise<VoiceCostPerMinute> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/cost-per-minute?hours=${hours}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice cost per minute: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchVoiceForecast(token?: string): Promise<VoiceForecast> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/forecast`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice forecast: ${response.statusText}`);
  }

  return response.json();
}

// Cross-Platform Tracking Types
export interface PlatformStats {
  platform: string;
  total_cost: number;
  total_duration_minutes: number;
  call_count: number;
  event_count: number;
  avg_latency_ms: number;
  cost_per_minute: number;
  cost_per_call: number;
  percentage: number;
}

export interface VoicePlatformComparison {
  time_window_hours: number;
  summary: {
    total_cost: number;
    total_calls: number;
    platform_count: number;
  };
  platforms: PlatformStats[];
  insights: {
    cheapest_platform: string | null;
    cheapest_cost_per_minute: number;
    most_expensive_platform: string | null;
    most_expensive_cost_per_minute: number;
    potential_monthly_savings: number;
    recommendation: string | null;
  };
}

export async function fetchVoicePlatformComparison(hours: number = 24, token?: string): Promise<VoicePlatformComparison> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/by-platform?hours=${hours}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice platform comparison: ${response.statusText}`);
  }

  return response.json();
}

// Alternative Cost Calculation Types
export interface AlternativeProvider {
  provider: string;
  name: string;
  projected_cost: number;
  savings: number;
  savings_percent: number;
}

export interface VoiceAlternativeCosts {
  time_window_hours: number;
  usage: {
    stt_minutes: number;
    llm_input_tokens: number;
    llm_output_tokens: number;
    tts_characters: number;
  };
  actual_costs: {
    stt: number;
    llm: number;
    tts: number;
    total: number;
  };
  alternatives: {
    stt: AlternativeProvider[];
    llm: AlternativeProvider[];
    tts: AlternativeProvider[];
  };
  best_diy_stack: {
    stt: string | null;
    llm: string | null;
    tts: string | null;
    total_cost: number;
    total_savings: number;
    savings_percent: number;
  };
}

export async function fetchVoiceAlternativeCosts(hours: number = 24, token?: string): Promise<VoiceAlternativeCosts> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/stats/voice/alternative-costs?hours=${hours}`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch voice alternative costs: ${response.statusText}`);
  }

  return response.json();
}

// Pricing Settings Types
export interface PricingSettings {
  cartesia_plan: string;
  elevenlabs_tier: string;
  playht_plan: string;
  updated_at: string;
}

export interface PricingOptions {
  [provider: string]: {
    options: string[];
    rates: { [plan: string]: number };
    unit: string;
    description: string;
  };
}

// Fetch user's pricing settings
export async function fetchPricingSettings(token?: string): Promise<PricingSettings> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/settings/pricing`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch pricing settings: ${response.statusText}`);
  }

  return response.json();
}

// Update user's pricing settings
export async function updatePricingSettings(
  settings: Partial<PricingSettings>,
  token?: string
): Promise<PricingSettings> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/settings/pricing`, {
    method: "POST",
    headers: {
      ...headers,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(settings),
  });

  if (!response.ok) {
    throw new Error(`Failed to update pricing settings: ${response.statusText}`);
  }

  return response.json();
}

// Fetch pricing options (plans and rates)
export async function fetchPricingOptions(token?: string): Promise<PricingOptions> {
  const headers = await getDashboardAuthHeaders(token);
  const response = await fetch(`${COLLECTOR_URL}/settings/pricing/options`, {
    headers,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch pricing options: ${response.statusText}`);
  }

  return response.json();
}

