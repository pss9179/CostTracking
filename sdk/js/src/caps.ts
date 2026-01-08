/**
 * Spending Cap Enforcement for JavaScript SDK
 * 
 * Checks hard spending caps before API calls and throws errors if exceeded.
 */

export interface ExceededCap {
  cap_type: string;
  target_name?: string;
  current: number;
  limit: number;
  period: string;
}

export interface CapCheckResult {
  allowed: boolean;
  exceeded_caps: ExceededCap[];
  message: string;
}

/**
 * Error thrown when a spending cap is exceeded.
 */
export class BudgetExceededError extends Error {
  public exceededCaps: ExceededCap[];

  constructor(message: string, exceededCaps: ExceededCap[]) {
    super(message);
    this.name = 'BudgetExceededError';
    this.exceededCaps = exceededCaps;
  }

  toString(): string {
    let msg = `${this.message}\n\nExceeded Caps:`;
    for (const cap of this.exceededCaps) {
      msg += `\n  - ${cap.cap_type}`;
      if (cap.target_name) {
        msg += ` (${cap.target_name})`;
      }
      msg += `: $${cap.current.toFixed(2)} / $${cap.limit.toFixed(2)} (${cap.period})`;
    }
    return msg;
  }
}

let _capsEnabled = false;
let _collectorUrl = '';
let _apiKey = '';

/**
 * Initialize caps checking with collector configuration.
 */
export function initCaps(collectorUrl: string, apiKey: string): void {
  _collectorUrl = collectorUrl;
  _apiKey = apiKey;
  _capsEnabled = true;
}

/**
 * Check if any spending caps would be exceeded before making an API call.
 * 
 * @param provider - Provider name (e.g., 'openai')
 * @param model - Model ID (e.g., 'gpt-4o')
 * @param customerId - Customer ID for per-customer caps
 * @param agent - Agent/section name for per-agent caps
 * @returns Promise resolving to cap check result
 * @throws BudgetExceededError if a hard cap is exceeded
 */
export async function checkSpendingCaps(options: {
  provider?: string;
  model?: string;
  customerId?: string;
  agent?: string;
}): Promise<CapCheckResult> {
  // If caps not enabled, allow all
  if (!_capsEnabled || !_apiKey) {
    return {
      allowed: true,
      exceeded_caps: [],
      message: 'Caps not configured',
    };
  }

  // Build query params
  const params = new URLSearchParams();
  if (options.provider) params.append('provider', options.provider);
  if (options.model) params.append('model', options.model);
  if (options.customerId) params.append('customer_id', options.customerId);
  if (options.agent) params.append('agent', options.agent);

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

    const response = await fetch(`${_collectorUrl}/caps/check?${params}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${_apiKey}`,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      const result: CapCheckResult = await response.json();

      // If not allowed, throw error
      if (!result.allowed) {
        throw new BudgetExceededError(
          `Spending cap exceeded: ${result.message}`,
          result.exceeded_caps
        );
      }

      return result;
    }

    if (response.status === 401) {
      console.warn('[llmobserve] Invalid API key - caps not checked');
      return {
        allowed: true,
        exceeded_caps: [],
        message: 'Invalid API key',
      };
    }

    // Other errors - fail open
    return {
      allowed: true,
      exceeded_caps: [],
      message: `Cap check failed: ${response.status}`,
    };
  } catch (error) {
    // Network errors or timeouts - fail open
    if (error instanceof BudgetExceededError) {
      throw error; // Re-throw budget errors
    }

    console.warn(`[llmobserve] Cap check failed: ${error}`);
    return {
      allowed: true,
      exceeded_caps: [],
      message: 'Cap check failed - allowing request',
    };
  }
}

/**
 * Check if caps checking is enabled.
 */
export function isCapsEnabled(): boolean {
  return _capsEnabled;
}

