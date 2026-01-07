"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout, ParameterTable } from "@/components/docs/DocPage";

const toc = [
  { id: "how-tracking-works", title: "How tracking works" },
  { id: "automatic-detection", title: "Automatic provider detection" },
  { id: "cost-calculation", title: "Cost calculation" },
  { id: "token-counting", title: "Token counting" },
  { id: "latency-tracking", title: "Latency tracking" },
];

export default function CostTrackingPage() {
  return (
    <DocPage
      title="How cost tracking works"
      description="Understand how LLMObserve automatically tracks costs for every LLM API call in your application."
      category="Cost tracking"
      toc={toc}
    >
      <h2 id="how-tracking-works">How tracking works</h2>

      <p>
        When you call <code>observe()</code>, LLMObserve patches the HTTP clients in your Python 
        environment (httpx, requests, aiohttp) to intercept outgoing requests. This allows us to 
        capture LLM API calls without modifying your code.
      </p>

      <p>For each LLM API call, we capture:</p>

      <ul>
        <li><strong>Provider</strong> — OpenAI, Anthropic, Google, etc.</li>
        <li><strong>Model</strong> — gpt-4o, claude-3-sonnet, gemini-pro, etc.</li>
        <li><strong>Input tokens</strong> — Tokens in your prompt/messages</li>
        <li><strong>Output tokens</strong> — Tokens in the response</li>
        <li><strong>Latency</strong> — Time from request to response</li>
        <li><strong>Cost</strong> — Calculated from tokens × pricing</li>
      </ul>

      <Callout type="info" title="Zero changes required">
        You don't need to modify your LLM API calls. Just add <code>observe()</code> once at 
        startup and all calls are tracked automatically.
      </Callout>

      <h2 id="automatic-detection">Automatic provider detection</h2>

      <p>
        LLMObserve automatically detects which provider you're calling based on the API endpoint URL:
      </p>

      <CodeBlock
        code={`# All of these are detected automatically

# OpenAI
client = OpenAI()
client.chat.completions.create(model="gpt-4o", ...)

# Anthropic
client = Anthropic()
client.messages.create(model="claude-3-sonnet", ...)

# Google
client = genai.GenerativeModel("gemini-pro")
client.generate_content(...)

# Azure OpenAI
client = AzureOpenAI(azure_endpoint="...")
client.chat.completions.create(...)

# OpenRouter (routes to multiple providers)
client = OpenAI(base_url="https://openrouter.ai/api/v1")
client.chat.completions.create(model="anthropic/claude-3-opus", ...)`}
        language="python"
      />

      <h3>Supported providers</h3>

      <p>We currently support 40+ providers including:</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 my-4 not-prose">
        {[
          "OpenAI", "Anthropic", "Google", "Azure OpenAI",
          "Cohere", "Mistral", "Perplexity", "Groq",
          "Together AI", "Replicate", "HuggingFace", "DeepSeek",
          "Fireworks", "OpenRouter", "AI21", "Voyage AI"
        ].map((provider) => (
          <div key={provider} className="px-3 py-2 bg-slate-50 rounded-lg text-sm text-slate-700 text-center">
            {provider}
          </div>
        ))}
      </div>

      <p>
        See <Link href="/docs/providers">Supported providers</Link> for the full list with model details.
      </p>

      <h2 id="cost-calculation">Cost calculation</h2>

      <p>
        Costs are calculated using our pricing database, which we update daily to reflect 
        provider pricing changes. The formula is:
      </p>

      <CodeBlock
        code={`cost = (input_tokens × input_price_per_token) + (output_tokens × output_price_per_token)`}
        language="text"
      />

      <Callout type="tip" title="Pricing accuracy">
        Our costs typically match provider bills within 1-2% accuracy. Minor differences can occur 
        due to token counting variations between providers.
      </Callout>

      <h3>Example cost breakdown</h3>

      <p>For a GPT-4o call with 1,000 input tokens and 500 output tokens:</p>

      <CodeBlock
        code={`Model: gpt-4o
Input: 1,000 tokens × $5.00/1M = $0.005
Output: 500 tokens × $15.00/1M = $0.0075
Total: $0.0125`}
        language="text"
      />

      <h2 id="token-counting">Token counting</h2>

      <p>
        Token counts are extracted from the API response when available. For providers that 
        don't return token counts, we estimate using tiktoken or provider-specific tokenizers.
      </p>

      <h3>Streaming responses</h3>

      <p>
        For streaming responses, token counts are captured when the stream completes. The cost 
        is calculated once all tokens have been received.
      </p>

      <CodeBlock
        code={`# Streaming is fully supported
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a story"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")

# Cost is tracked when stream completes`}
        language="python"
      />

      <h2 id="latency-tracking">Latency tracking</h2>

      <p>
        Latency is measured from when the request is sent to when the response is received 
        (or when streaming completes). This includes network latency and provider processing time.
      </p>

      <p>View latency metrics in your dashboard:</p>

      <ul>
        <li><strong>Average latency</strong> — Mean response time across calls</li>
        <li><strong>P50/P95/P99</strong> — Percentile latencies for performance analysis</li>
        <li><strong>Per-model breakdown</strong> — Compare latency across models</li>
      </ul>

      <hr />

      <h3>Next steps</h3>

      <ul>
        <li><Link href="/docs/viewing-costs">Viewing costs in the dashboard</Link></li>
        <li><Link href="/docs/agents">Track costs by agent</Link></li>
        <li><Link href="/docs/providers">Supported providers</Link></li>
      </ul>
    </DocPage>
  );
}

