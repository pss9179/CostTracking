import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';

interface ObserveOptions {
  collectorUrl?: string;
  apiKey?: string;
  flushIntervalMs?: number;
}

interface TraceEvent {
  id: string;
  run_id: string;
  span_id: string;
  parent_span_id: string;
  section: string;
  section_path: string;
  span_type: string;
  provider: string;
  model: string | null;
  endpoint: string;
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;
  latency_ms: number;
  status: string;
  is_streaming: boolean;
  stream_cancelled: boolean;
  cost_usd: number;
  event_metadata: Record<string, any>;
  customer_id?: string;
  tenant_id?: string;
}

let _config: ObserveOptions = {};
let _buffer: TraceEvent[] = [];
let _flushTimer: NodeJS.Timeout | null = null;

// Generate UUID v4 (simple implementation)
function uuidv4(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function extractProvider(url: string): string {
  const lowerUrl = url.toLowerCase();
  if (lowerUrl.includes('openai.com')) return 'openai';
  if (lowerUrl.includes('anthropic.com')) return 'anthropic';
  if (lowerUrl.includes('cohere.ai')) return 'cohere';
  if (lowerUrl.includes('googleapis.com')) return 'google';
  if (lowerUrl.includes('pinecone.io')) return 'pinecone';
  return 'unknown';
}

function extractModel(body: any): string | null {
  if (!body) return null;
  return body.model || body.model_id || body.engine || null;
}

function extractTokens(body: any, provider: string): { input: number, output: number } {
  if (!body) return { input: 0, output: 0 };
  
  // OpenAI
  if (body.usage) {
    return {
      input: body.usage.prompt_tokens || 0,
      output: body.usage.completion_tokens || 0
    };
  }
  
  // Anthropic
  if (provider === 'anthropic' && body.usage) {
    return {
      input: body.usage.input_tokens || 0,
      output: body.usage.output_tokens || 0
    };
  }
  
  return { input: 0, output: 0 };
}

function flushEvents() {
  if (_buffer.length === 0 || !_config.collectorUrl) return;
  
  const events = [..._buffer];
  _buffer = [];
  
  const url = new URL(`${_config.collectorUrl}/events/`);
  const data = JSON.stringify(events);
  
  const options = {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': data.length,
      'Authorization': _config.apiKey ? `Bearer ${_config.apiKey}` : ''
    }
  };
  
  const req = (url.protocol === 'https:' ? https : http).request(url, options, (res) => {
    // Ignore response
  });
  
  req.on('error', (e) => {
    // Fail silently
  });
  
  req.write(data);
  req.end();
}

export function observe(options: ObserveOptions = {}) {
  _config = {
    collectorUrl: options.collectorUrl || process.env.LLMOBSERVE_COLLECTOR_URL,
    apiKey: options.apiKey || process.env.LLMOBSERVE_API_KEY,
    flushIntervalMs: options.flushIntervalMs || 500
  };
  
  if (!_config.collectorUrl) {
    console.warn('[llmobserve] No collector URL provided. Tracking disabled.');
    return;
  }
  
  // Start flush timer
  if (!_flushTimer) {
    _flushTimer = setInterval(flushEvents, _config.flushIntervalMs);
  }
  
  // Patch global fetch
  const originalFetch = global.fetch;
  
  global.fetch = async function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const startTime = Date.now();
    const url = input.toString();
    const method = init?.method || 'GET';
    
    // Skip collector requests
    if (url.startsWith(_config.collectorUrl!)) {
      return originalFetch(input, init);
    }
    
    let requestBody: any = null;
    if (init?.body && typeof init.body === 'string') {
      try {
        requestBody = JSON.parse(init.body);
      } catch (e) {
        // Ignore parsing errors
      }
    }
    
    try {
      const response = await originalFetch(input, init);
      const latency = Date.now() - startTime;
      
      // Clone response to read body
      const clone = response.clone();
      
      clone.json().then(responseBody => {
        const provider = extractProvider(url);
        const model = extractModel(requestBody);
        const { input: inputTokens, output: outputTokens } = extractTokens(responseBody, provider);
        
        const event: TraceEvent = {
          id: uuidv4(),
          run_id: uuidv4(), // Simple run ID for now
          span_id: uuidv4(),
          parent_span_id: "",
          section: "/",
          section_path: "/",
          span_type: "http_fallback",
          provider: provider,
          model: model,
          endpoint: `${method} ${url}`,
          input_tokens: inputTokens,
          output_tokens: outputTokens,
          cached_tokens: 0,
          latency_ms: latency,
          status: response.ok ? "ok" : "error",
          is_streaming: false,
          stream_cancelled: false,
          cost_usd: 0, // Calculated by collector
          event_metadata: {
            status_code: response.status,
            url: url,
            method: method
          }
        };
        
        _buffer.push(event);
      }).catch(() => {
        // Ignore body reading errors
      });
      
      return response;
    } catch (error) {
      throw error;
    }
  };
  
  console.log('[llmobserve] JS SDK initialized');
}
