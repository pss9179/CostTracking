"use client";

import Link from "next/link";
import { DocPage, CodeBlock, ParameterTable, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "signature", title: "Signature" },
  { id: "parameters", title: "Parameters" },
  { id: "examples", title: "Examples" },
  { id: "notes", title: "Notes" },
];

export default function ObserveAPIPage() {
  return (
    <DocPage
      title="observe()"
      description="Initialize LLMObserve tracking. Call once at application startup."
      category="API Reference"
      toc={toc}
    >
      <h2 id="signature">Signature</h2>

      <CodeBlock
        code={`def observe(
    api_key: str = None,
    collector_url: str = None,
    customer_id: str = None,
    tenant_id: str = None,
) -> None`}
        language="python"
      />

      <h2 id="parameters">Parameters</h2>

      <ParameterTable
        parameters={[
          {
            name: "api_key",
            type: "str",
            required: true,
            description: "Your LLMObserve API key. Get it from the Settings page. Can also be set via LLMOBSERVE_API_KEY environment variable.",
          },
          {
            name: "collector_url",
            type: "str",
            description: "Custom collector endpoint URL. Only needed for self-hosted or enterprise deployments.",
            default: "Production URL",
          },
          {
            name: "customer_id",
            type: "str",
            description: "Customer identifier for per-customer cost tracking. Useful for SaaS applications.",
          },
          {
            name: "tenant_id",
            type: "str",
            description: "Tenant identifier for multi-tenant applications. Group customers by organization.",
          },
        ]}
      />

      <h2 id="examples">Examples</h2>

      <h3>Basic usage</h3>

      <CodeBlock
        code={`from llmobserve import observe

# Using API key directly
observe(api_key="llmo_sk_your_key_here")

# Or using environment variable (recommended)
# Set LLMOBSERVE_API_KEY in your environment
observe()`}
        language="python"
      />

      <h3>With customer tracking</h3>

      <CodeBlock
        code={`from llmobserve import observe

# Track costs for a specific customer
observe(
    api_key="llmo_sk_...",
    customer_id="cust_123"
)`}
        language="python"
      />

      <h3>Multi-tenant setup</h3>

      <CodeBlock
        code={`from llmobserve import observe

# Track by tenant and customer
observe(
    api_key="llmo_sk_...",
    tenant_id="org_acme",
    customer_id="user_456"
)`}
        language="python"
      />

      <h2 id="notes">Notes</h2>

      <Callout type="warning" title="Call observe() before LLM calls">
        <code>observe()</code> patches HTTP clients at runtime. Any LLM API calls made 
        <em>before</em> calling <code>observe()</code> will not be tracked.
      </Callout>

      <ul>
        <li>Call <code>observe()</code> once at application startup</li>
        <li>Subsequent calls to <code>observe()</code> are ignored</li>
        <li>Use <code>set_customer_id()</code> to change customer ID dynamically</li>
        <li>Set <code>LLMOBSERVE_DISABLED=true</code> to disable tracking in tests</li>
      </ul>

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/quickstart">Quickstart guide</Link></li>
        <li><Link href="/docs/api/agent">@agent decorator</Link></li>
        <li><Link href="/docs/customers">Customer tracking</Link></li>
      </ul>
    </DocPage>
  );
}

