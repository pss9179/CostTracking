"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "no-data-in-dashboard", title: "No data in dashboard" },
  { id: "api-key-not-working", title: "API key not working" },
  { id: "costs-not-matching", title: "Costs not matching" },
  { id: "streaming-not-tracked", title: "Streaming not tracked" },
  { id: "getting-help", title: "Getting help" },
];

export default function TroubleshootingPage() {
  return (
    <DocPage
      title="Troubleshooting"
      description="Solutions to common issues with LLMObserve."
      category="Help"
      toc={toc}
    >
      <h2 id="no-data-in-dashboard">No data appearing in dashboard</h2>

      <p>If you're not seeing LLM calls in your dashboard, check the following:</p>

      <h3>1. Verify observe() is called before LLM calls</h3>

      <p>
        <code>observe()</code> must be called before any LLM API calls. It patches HTTP 
        clients at runtime, so calls made before <code>observe()</code> won't be tracked.
      </p>

      <CodeBlock
        code={`# ✅ Correct - observe() first
from llmobserve import observe
observe(api_key="...")

from openai import OpenAI
client = OpenAI()
client.chat.completions.create(...)  # ✅ Tracked

# ❌ Wrong - LLM calls before observe()
from openai import OpenAI
client = OpenAI()
client.chat.completions.create(...)  # ❌ NOT tracked

from llmobserve import observe
observe(api_key="...")`}
        language="python"
      />

      <h3>2. Check your API key</h3>

      <ul>
        <li>Make sure your API key starts with <code>llmo_sk_</code></li>
        <li>Verify you copied the full key, not just the prefix shown in Settings</li>
        <li>Check for extra whitespace or newlines</li>
      </ul>

      <h3>3. Wait a few seconds</h3>

      <p>
        Events are batched and sent asynchronously. Data typically appears in the dashboard 
        within 10-30 seconds of making an LLM call.
      </p>

      <h3>4. Check for errors in your terminal</h3>

      <p>
        LLMObserve logs errors to stderr. Look for messages starting with <code>[llmobserve]</code>:
      </p>

      <CodeBlock
        code={`# If you see this, your API key is invalid
[llmobserve] ❌ Failed to send events: 401 Unauthorized

# If you see this, network is blocked
[llmobserve] ❌ Failed to send events: Connection refused`}
        language="text"
      />

      <h3>5. Verify your LLM calls are succeeding</h3>

      <p>
        LLMObserve only tracks successful API calls. If your LLM calls are failing 
        (invalid API key, rate limits, etc.), they won't appear in the dashboard.
      </p>

      <h2 id="api-key-not-working">API key not working</h2>

      <p>If you're getting authentication errors:</p>

      <ol>
        <li>Go to <Link href="/settings">Settings</Link> and verify your API key</li>
        <li>Generate a new API key if needed</li>
        <li>Make sure you're using the full key (not just the prefix)</li>
        <li>Check that the key hasn't been revoked</li>
      </ol>

      <Callout type="warning" title="API key format">
        Your API key should look like: <code>llmo_sk_abc123def456...</code> (48+ characters total)
      </Callout>

      <h2 id="costs-not-matching">Costs not matching provider bill</h2>

      <p>
        LLMObserve costs should match your provider bill within 1-2%. If you're seeing 
        larger differences:
      </p>

      <h3>Token counting differences</h3>

      <p>
        Different providers count tokens differently. OpenAI uses tiktoken, Anthropic uses 
        their own tokenizer, etc. Small variations are normal.
      </p>

      <h3>Pricing updates</h3>

      <p>
        We update pricing daily, but there may be a brief lag when providers change prices. 
        If you notice outdated pricing, <a href="mailto:support@llmobserve.com">let us know</a>.
      </p>

      <h3>Missing calls</h3>

      <p>
        If some calls aren't being tracked (see "No data" section above), your totals will 
        be lower than expected.
      </p>

      <h2 id="streaming-not-tracked">Streaming responses not tracked</h2>

      <p>Streaming is fully supported. Common issues:</p>

      <h3>Stream not consumed</h3>

      <p>
        Token counts are captured when the stream <em>completes</em>. If you don't consume 
        the entire stream, the call won't be tracked.
      </p>

      <CodeBlock
        code={`# ✅ Correct - consume entire stream
stream = client.chat.completions.create(..., stream=True)
for chunk in stream:
    print(chunk.choices[0].delta.content)
# Stream completes, cost is tracked

# ❌ Wrong - stream not consumed
stream = client.chat.completions.create(..., stream=True)
first_chunk = next(stream)
# Stream abandoned, cost may not be tracked`}
        language="python"
      />

      <h3>Async streams</h3>

      <p>
        For async streams, make sure you await the entire stream:
      </p>

      <CodeBlock
        code={`async def get_response():
    stream = await client.chat.completions.create(..., stream=True)
    async for chunk in stream:
        print(chunk.choices[0].delta.content)
    # Stream completes, cost is tracked`}
        language="python"
      />

      <h2 id="getting-help">Getting help</h2>

      <p>If you're still stuck:</p>

      <ul>
        <li>
          <strong>Email us:</strong> <a href="mailto:support@llmobserve.com">support@llmobserve.com</a>
        </li>
        <li>
          <strong>Check FAQ:</strong> <Link href="/docs/faq">Frequently Asked Questions</Link>
        </li>
      </ul>

      <Callout type="info" title="Include these details when contacting support">
        <ul className="mt-2 space-y-1">
          <li>• Your Python version</li>
          <li>• LLMObserve SDK version (<code>pip show llmobserve</code>)</li>
          <li>• Which LLM provider you're using</li>
          <li>• Any error messages from your terminal</li>
        </ul>
      </Callout>
    </DocPage>
  );
}

