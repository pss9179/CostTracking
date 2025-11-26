/**
 * HTTP interceptor for tracking API costs
 */

import { EventBuffer, TraceEvent } from './buffer';
import { getContext, getCurrentAgent } from './context';

interface ObserveConfig {
  collectorUrl: string;
  apiKey: string;
  tenantId: string;
  customerId: string;
  debug: boolean;
}

function generateId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function patchFetch(buffer: EventBuffer, config: ObserveConfig): void {
  const originalFetch = globalThis.fetch;

  globalThis.fetch = async function (
    input: RequestInfo | URL,
    init?: RequestInit
  ): Promise<Response> {
    const url = typeof input === 'string' 
      ? input 
      : input instanceof URL 
        ? input.toString() 
        : (input as Request).url;
    
    const startTime = Date.now();

    // Skip collector requests to avoid infinite loops
    if (url.includes(config.collectorUrl)) {
      return originalFetch(input, init);
    }

    try {
      // Make the actual request
      const response = await originalFetch(input, init);
      const latencyMs = Date.now() - startTime;

      // Clone response to read body
      const clonedResponse = response.clone();

      // Try to parse response body
      let responseBody: any;
      try {
        responseBody = await clonedResponse.json();
      } catch {
        // Not JSON, skip tracking
        return response;
      }

      // Extract event from response
      const ctx = getContext();
      const event = extractEventFromResponse(url, responseBody, latencyMs, ctx);
      if (event) {
        buffer.add(event);
      }

      return response;
    } catch (error) {
      const latencyMs = Date.now() - startTime;

      // Track error
      const provider = extractProviderFromUrl(url);
      if (provider) {
        const ctx = getContext();
        const runId = ctx.runId || generateId();
        const spanId = generateId();
        const section = getCurrentAgent() || 'default';

        buffer.add({
          id: generateId(),
          run_id: runId,
          span_id: spanId,
          parent_span_id: null,
          section: section,
          section_path: section,
          span_type: 'api',
          provider,
          endpoint: 'error',
          model: null,
          tenant_id: ctx.tenantId,
          customer_id: ctx.customerId || null,
          input_tokens: 0,
          output_tokens: 0,
          cached_tokens: 0,
          cost_usd: 0,
          latency_ms: latencyMs,
          status: 'error',
          is_streaming: false,
          stream_cancelled: false,
          event_metadata: {
            error_message: error instanceof Error ? error.message : String(error),
          },
          semantic_label: null,
        });
      }

      throw error;
    }
  };

  if (config.debug) {
    console.log('[llmobserve] ✅ fetch() patched successfully');
  }
}

function extractProviderFromUrl(url: string): string | null {
  const urlLower = url.toLowerCase();
  if (urlLower.includes('api.openai.com')) return 'openai';
  if (urlLower.includes('api.anthropic.com')) return 'anthropic';
  if (urlLower.includes('generativelanguage.googleapis.com')) return 'google';
  if (urlLower.includes('pinecone.io')) return 'pinecone';
  if (urlLower.includes('api.cohere.ai')) return 'cohere';
  if (urlLower.includes('api.together.xyz')) return 'together';
  if (urlLower.includes('api.vapi.ai')) return 'vapi';
  if (urlLower.includes('api.deepgram.com')) return 'deepgram';
  if (urlLower.includes('api.elevenlabs.io')) return 'elevenlabs';
  if (urlLower.includes('api.cartesia.ai')) return 'cartesia';
  return null;
}

function extractEventFromResponse(
  url: string,
  body: any,
  latencyMs: number,
  ctx: { tenantId: string; customerId: string; runId: string }
): TraceEvent | null {
  const provider = extractProviderFromUrl(url);
  if (!provider) return null;

  const currentAgent = getCurrentAgent();
  const runId = ctx.runId || generateId();
  const spanId = generateId();
  const section = currentAgent || 'default';

  // OpenAI format
  if (provider === 'openai' && body.usage) {
    const model = body.model || 'unknown';
    const inputTokens = body.usage.prompt_tokens || 0;
    const outputTokens = body.usage.completion_tokens || 0;

    // Calculate cost
    const costPer1kInput = getCostPer1kTokens(model, 'input');
    const costPer1kOutput = getCostPer1kTokens(model, 'output');
    const costUsd =
      (inputTokens / 1000) * costPer1kInput +
      (outputTokens / 1000) * costPer1kOutput;

    return {
      id: generateId(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: section,
      section_path: section,
      span_type: 'llm',
      provider,
      endpoint: 'chat',
      model,
      tenant_id: ctx.tenantId,
      customer_id: ctx.customerId || null,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cached_tokens: 0,
      cost_usd: costUsd,
      latency_ms: latencyMs,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: null,
      semantic_label: null,
    };
  }

  // Anthropic format
  if (provider === 'anthropic' && body.usage) {
    const model = body.model || 'unknown';
    const inputTokens = body.usage.input_tokens || 0;
    const outputTokens = body.usage.output_tokens || 0;

    const costPer1kInput = getCostPer1kTokens(model, 'input');
    const costPer1kOutput = getCostPer1kTokens(model, 'output');
    const costUsd =
      (inputTokens / 1000) * costPer1kInput +
      (outputTokens / 1000) * costPer1kOutput;

    return {
      id: generateId(),
      run_id: runId,
      span_id: spanId,
      parent_span_id: null,
      section: section,
      section_path: section,
      span_type: 'llm',
      provider,
      endpoint: 'messages',
      model,
      tenant_id: ctx.tenantId,
      customer_id: ctx.customerId || null,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      cached_tokens: 0,
      cost_usd: costUsd,
      latency_ms: latencyMs,
      status: 'ok',
      is_streaming: false,
      stream_cancelled: false,
      event_metadata: null,
      semantic_label: null,
    };
  }

  // Generic fallback for other providers
  return {
    id: generateId(),
    run_id: runId,
    span_id: spanId,
    parent_span_id: null,
    section: section,
    section_path: section,
    span_type: 'api',
    provider,
    endpoint: 'unknown',
    model: null,
    tenant_id: ctx.tenantId,
    customer_id: ctx.customerId || null,
    input_tokens: 0,
    output_tokens: 0,
    cached_tokens: 0,
    cost_usd: 0,
    latency_ms: latencyMs,
    status: 'ok',
    is_streaming: false,
    stream_cancelled: false,
    event_metadata: null,
    semantic_label: null,
  };
}

// Pricing table for common models
function getCostPer1kTokens(model: string, tokenType: 'input' | 'output'): number {
  const pricing: Record<string, { input: number; output: number }> = {
    // OpenAI
    'gpt-4o': { input: 0.0025, output: 0.01 },
    'gpt-4o-2024-11-20': { input: 0.0025, output: 0.01 },
    'gpt-4o-2024-08-06': { input: 0.0025, output: 0.01 },
    'gpt-4o-mini': { input: 0.00015, output: 0.0006 },
    'gpt-4o-mini-2024-07-18': { input: 0.00015, output: 0.0006 },
    'gpt-4-turbo': { input: 0.01, output: 0.03 },
    'gpt-4-turbo-preview': { input: 0.01, output: 0.03 },
    'gpt-4': { input: 0.03, output: 0.06 },
    'gpt-3.5-turbo': { input: 0.0005, output: 0.0015 },
    'gpt-3.5-turbo-0125': { input: 0.0005, output: 0.0015 },
    // Anthropic
    'claude-3-5-sonnet-20241022': { input: 0.003, output: 0.015 },
    'claude-3-5-sonnet-latest': { input: 0.003, output: 0.015 },
    'claude-3-5-haiku-20241022': { input: 0.0008, output: 0.004 },
    'claude-3-opus-20240229': { input: 0.015, output: 0.075 },
    'claude-3-sonnet-20240229': { input: 0.003, output: 0.015 },
    'claude-3-haiku-20240307': { input: 0.00025, output: 0.00125 },
  };

  const modelPricing = pricing[model] || { input: 0.0001, output: 0.0001 };
  return modelPricing[tokenType];
}

