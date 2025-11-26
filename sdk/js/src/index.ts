/**
 * LLMObserve - Automatic cost tracking for LLM applications
 *
 * This SDK automatically tracks costs for OpenAI, Anthropic, and other APIs
 * by intercepting HTTP requests and calculating costs based on usage.
 * 
 * @example
 * ```typescript
 * import { observe } from 'llmobserve';
 * 
 * observe({
 *   collectorUrl: 'http://localhost:8000',
 *   apiKey: 'llmo_sk_xxx'
 * });
 * 
 * // Now use OpenAI normally - costs are tracked automatically!
 * import OpenAI from 'openai';
 * const client = new OpenAI();
 * await client.chat.completions.create({...});
 * ```
 */

import { EventBuffer } from './buffer';
import { patchFetch } from './interceptor';
import { getContext, setContext } from './context';

export interface ObserveConfig {
  /** URL of the collector server (e.g., 'http://localhost:8000') */
  collectorUrl: string;
  /** Your API key from the settings page */
  apiKey: string;
  /** Optional tenant ID for multi-tenant setups */
  tenantId?: string;
  /** Optional customer ID for tracking end-user costs */
  customerId?: string;
  /** Flush interval in milliseconds (default: 500) */
  flushIntervalMs?: number;
  /** Enable debug logging */
  debug?: boolean;
}

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

let _initialized = false;
let _buffer: EventBuffer | null = null;

/**
 * Initialize LLMObserve to start tracking API costs.
 *
 * @example
 * ```typescript
 * import { observe } from 'llmobserve';
 *
 * observe({
 *   collectorUrl: 'https://api.llmobserve.com',
 *   apiKey: 'llmo_sk_xxx'
 * });
 *
 * // Now use OpenAI, Anthropic, etc. normally
 * import OpenAI from 'openai';
 * const client = new OpenAI();
 * const response = await client.chat.completions.create({...});
 * // ✅ Costs automatically tracked!
 * ```
 */
export function observe(config: ObserveConfig): void {
  if (_initialized) {
    if (config.debug) {
      console.log('[llmobserve] Already initialized, skipping');
    }
    return;
  }

  // Validate required config
  if (!config.collectorUrl) {
    throw new Error('[llmobserve] collectorUrl is required');
  }
  if (!config.apiKey) {
    throw new Error('[llmobserve] apiKey is required');
  }

  // Set defaults
  const finalConfig = {
    collectorUrl: config.collectorUrl,
    apiKey: config.apiKey,
    tenantId: config.tenantId || process.env.LLMOBSERVE_TENANT_ID || 'default_tenant',
    customerId: config.customerId || process.env.LLMOBSERVE_CUSTOMER_ID || '',
    flushIntervalMs: config.flushIntervalMs || 500,
    debug: config.debug || false,
  };

  // Initialize context
  setContext({
    tenantId: finalConfig.tenantId,
    customerId: finalConfig.customerId,
    agentStack: [],
    runId: generateId(),
  });

  // Initialize event buffer
  _buffer = new EventBuffer(
    finalConfig.collectorUrl,
    finalConfig.apiKey,
    finalConfig.flushIntervalMs,
    finalConfig.debug
  );

  // Patch global fetch
  patchFetch(_buffer, finalConfig);

  _initialized = true;

  if (finalConfig.debug) {
    console.log('[llmobserve] ✅ Initialized successfully');
    console.log(`[llmobserve] Collector URL: ${finalConfig.collectorUrl}`);
    console.log(`[llmobserve] Tenant ID: ${finalConfig.tenantId}`);
  }
}

/**
 * Set the customer ID for tracking end-user costs.
 *
 * @example
 * ```typescript
 * import { setCustomerId } from 'llmobserve';
 *
 * // Track costs per customer
 * setCustomerId('customer_123');
 * ```
 */
export function setCustomerId(customerId: string): void {
  const ctx = getContext();
  ctx.customerId = customerId;
  setContext(ctx);
}

/**
 * Create a named section for grouping related API calls.
 *
 * @example
 * ```typescript
 * import { section } from 'llmobserve';
 *
 * await section('agent:chatbot').run(async () => {
 *   // All API calls here will be tagged with "agent:chatbot"
 *   const response = await client.chat.completions.create({...});
 * });
 * ```
 */
export function section(name: string): { run: <T>(fn: () => Promise<T>) => Promise<T> } {
  return {
    async run<T>(fn: () => Promise<T>): Promise<T> {
      const ctx = getContext();
      ctx.agentStack.push(name);
      setContext(ctx);

      try {
        return await fn();
      } finally {
        const ctx = getContext();
        ctx.agentStack.pop();
        setContext(ctx);
      }
    },
  };
}

/**
 * Manually flush all pending events to the collector.
 * Useful before process exit.
 */
export async function flush(): Promise<void> {
  if (_buffer) {
    await _buffer.flush();
  }
}
