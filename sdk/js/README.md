# LLMObserve

[![npm version](https://badge.fury.io/js/llmobserve.svg)](https://www.npmjs.com/package/llmobserve)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zero-config LLM cost tracking for Node.js. Automatically tracks costs for OpenAI, Anthropic, Google, and 40+ more providers.

**Free forever** - No credit card required, no usage limits.

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
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_xxx'  // Get from Settings at app.llmobserve.com
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

## Get Your API Key

1. Sign up free at [app.llmobserve.com](https://app.llmobserve.com)
2. Go to **Settings** → **API Keys**
3. Create a new API key
4. Use it in your `observe()` call

## Configuration

```typescript
observe({
  // Required
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_xxx',
  
  // Optional
  tenantId: 'my-tenant',        // For multi-tenant apps
  customerId: 'customer-123',   // Track costs per end-user
  flushIntervalMs: 500,         // How often to send events (default: 500ms)
  debug: true,                  // Enable debug logging
  enableCaps: true              // Enable spending cap enforcement (default: true)
});
```

## Features

- **Zero-config**: Just call `observe()` and all LLM calls are tracked automatically
- **40+ Providers**: OpenAI, Anthropic, Google, Cohere, Together AI, and more
- **Multi-tenant**: Track costs per tenant or customer
- **Spending Caps**: Set hard limits and get alerts before exceeding budgets
- **Real-time Dashboard**: View costs instantly at app.llmobserve.com
- **Free Forever**: No credit card, no limits

## Track Costs Per Customer

```typescript
import { observe, setCustomerId } from 'llmobserve';

observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_xxx'
});

// Set customer ID before making API calls
setCustomerId('customer_123');

// Now all API calls will be attributed to customer_123
const response = await openai.chat.completions.create({...});
```

## Sections (Group Related Calls)

```typescript
import { section } from 'llmobserve';

// Group API calls by feature or agent
await section('chatbot').run(async () => {
  const response = await openai.chat.completions.create({...});
  // Tagged with section: "chatbot"
});

await section('summarizer').run(async () => {
  const response = await openai.chat.completions.create({...});
  // Tagged with section: "summarizer"
});
```

## Spending Caps

Caps are enabled by default. When a cap is exceeded, the SDK throws a `BudgetExceededError` before the API call is made:

```typescript
import { observe, BudgetExceededError } from 'llmobserve';

observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_xxx',
  enableCaps: true  // Default: true
});

try {
  const response = await openai.chat.completions.create({...});
} catch (error) {
  if (error instanceof BudgetExceededError) {
    console.error('Budget exceeded!', error.exceededCaps);
    // Handle gracefully - show user a message, etc.
  }
  throw error;
}
```

Set spending caps in your dashboard at [app.llmobserve.com/caps](https://app.llmobserve.com/caps).

## Supported Providers

| Provider | Type | Auto-tracked |
|----------|------|--------------|
| OpenAI | LLM | ✅ |
| Anthropic | LLM | ✅ |
| Google (Gemini) | LLM | ✅ |
| Cohere | LLM | ✅ |
| Together AI | LLM | ✅ |
| Groq | LLM | ✅ |
| Mistral | LLM | ✅ |
| Perplexity | LLM | ✅ |
| Pinecone | Vector DB | ✅ |
| Deepgram | STT | ✅ |
| ElevenLabs | TTS | ✅ |
| Cartesia | TTS | ✅ |
| PlayHT | TTS | ✅ |

## Flush Before Exit

Call `flush()` before process exit to ensure all events are sent:

```typescript
import { flush } from 'llmobserve';

// Before exiting your app
await flush();
process.exit(0);
```

## Environment Variables

You can also configure via environment variables:

```bash
LLMOBSERVE_API_KEY=llmo_sk_xxx
LLMOBSERVE_TENANT_ID=my-tenant
LLMOBSERVE_CUSTOMER_ID=customer-123
```

## Links

- **Dashboard**: [app.llmobserve.com](https://app.llmobserve.com)
- **Documentation**: [llmobserve.com/docs](https://llmobserve.com/docs)
- **GitHub**: [github.com/pss9179/CostTracking](https://github.com/pss9179/CostTracking)
- **Python SDK**: [pypi.org/project/llmobserve](https://pypi.org/project/llmobserve)

## License

MIT © [Skyline](https://llmobserve.com)
