# LLMObserve

Zero-config LLM cost tracking for Node.js. Automatically tracks costs for OpenAI, Anthropic, and more.

## Installation

```bash
npm install llmobserve
```

## Quick Start

```typescript
import { observe } from 'llmobserve';
import OpenAI from 'openai';

// Initialize LLMObserve (do this once at app startup)
observe({
  collectorUrl: 'http://localhost:8000',  // Or your deployed collector URL
  apiKey: 'llmo_sk_xxx'  // Get from Settings page
});

// Use OpenAI normally - costs are tracked automatically!
const openai = new OpenAI();
const response = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
// ✅ Costs automatically tracked in your dashboard!
```

## Configuration

```typescript
observe({
  // Required
  collectorUrl: 'http://localhost:8000',
  apiKey: 'llmo_sk_xxx',
  
  // Optional
  tenantId: 'my-tenant',        // For multi-tenant apps
  customerId: 'customer-123',   // Track per end-user
  flushIntervalMs: 500,         // How often to send events
  debug: true                   // Enable debug logging
});
```

## Features

- **Zero-config**: Just call `observe()` and all LLM calls are tracked
- **Automatic cost calculation**: Supports GPT-4, Claude, and more
- **Multi-tenant support**: Track costs per tenant/customer
- **Sections**: Group related calls with `section('name').run(async () => ...)`

## Supported Providers

- OpenAI (GPT-4, GPT-4o, GPT-3.5, etc.)
- Anthropic (Claude 3.5, Claude 3, etc.)
- Google (Gemini)
- Cohere
- Together AI
- Pinecone (vector operations)
- Deepgram (STT)
- ElevenLabs (TTS)
- Cartesia (TTS)

## Manual Flush

Call `flush()` before process exit to ensure all events are sent:

```typescript
import { flush } from 'llmobserve';

// Before exiting
await flush();
process.exit(0);
```

## License

MIT

