/**
 * Event buffer for batching and sending events to the collector
 */

export interface TraceEvent {
  id: string;
  run_id: string;
  span_id: string;
  parent_span_id: string | null;
  section: string;
  section_path: string;
  span_type: string;
  provider: string;
  endpoint: string;
  model: string | null;
  tenant_id: string;
  customer_id: string | null;
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;
  cost_usd: number;
  latency_ms: number;
  status: string;
  is_streaming: boolean;
  stream_cancelled: boolean;
  event_metadata: Record<string, any> | null;
  semantic_label: string | null;
}

export class EventBuffer {
  private buffer: TraceEvent[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private isFlushing = false;

  constructor(
    private collectorUrl: string,
    private apiKey: string,
    private flushIntervalMs: number = 500,
    private debug: boolean = false
  ) {
    this.startFlushTimer();
  }

  add(event: TraceEvent): void {
    this.buffer.push(event);
    if (this.debug) {
      console.log('[llmobserve] Event added:', event);
    }
    // Auto-flush if buffer is large
    if (this.buffer.length >= 10) {
      this.flush();
    }
  }

  private startFlushTimer(): void {
    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.flushIntervalMs);
    
    // Prevent the timer from keeping the process alive
    if (this.flushTimer.unref) {
      this.flushTimer.unref();
    }
  }

  async flush(): Promise<void> {
    if (this.isFlushing || this.buffer.length === 0) {
      return;
    }

    this.isFlushing = true;
    const eventsToSend = [...this.buffer];
    this.buffer = [];

    try {
      // FIX: Use trailing slash and send array directly (not wrapped in object)
      const response = await fetch(`${this.collectorUrl}/events/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(eventsToSend),  // FIX: Send array directly
      });

      if (!response.ok) {
        console.error('[llmobserve] Failed to send events:', response.statusText);
        // Re-add events to buffer on failure
        this.buffer.push(...eventsToSend);
      } else if (this.debug) {
        console.log(`[llmobserve] ✅ Flushed ${eventsToSend.length} events`);
      }
    } catch (error) {
      console.error('[llmobserve] Error sending events:', error);
      // Re-add events to buffer on error
      this.buffer.push(...eventsToSend);
    } finally {
      this.isFlushing = false;
    }
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    this.flush();
  }
}

