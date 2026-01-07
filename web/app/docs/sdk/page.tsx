"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout, ParameterTable } from "@/components/docs/DocPage";

const toc = [
  { id: "installation", title: "Installation" },
  { id: "observe", title: "observe()" },
  { id: "agent", title: "@agent decorator" },
  { id: "section", title: "section()" },
  { id: "wrap-all-tools", title: "wrap_all_tools()" },
  { id: "set-customer-id", title: "set_customer_id()" },
  { id: "environment-variables", title: "Environment variables" },
];

export default function SDKPage() {
  return (
    <DocPage
      title="Python SDK Reference"
      description="Complete API reference for the llmobserve Python SDK."
      category="API Reference"
      toc={toc}
    >
      <h2 id="installation">Installation</h2>

      <CodeBlock code="pip install llmobserve" language="bash" />

      <p>Requirements:</p>
      <ul>
        <li>Python 3.8+</li>
        <li>Works with: httpx, requests, aiohttp</li>
      </ul>

      <h2 id="observe">observe()</h2>

      <p>
        Initialize LLMObserve tracking. Call this once at application startup, before making 
        any LLM API calls.
      </p>

      <CodeBlock
        code={`from llmobserve import observe

observe(
    api_key="llmo_sk_...",
    customer_id="cust_123",      # Optional
    tenant_id="tenant_456",      # Optional
)`}
        language="python"
      />

      <ParameterTable
        parameters={[
          {
            name: "api_key",
            type: "str",
            required: true,
            description: "Your LLMObserve API key from the Settings page. Can also be set via LLMOBSERVE_API_KEY env var.",
          },
          {
            name: "collector_url",
            type: "str",
            description: "Collector endpoint URL. Defaults to production.",
            default: "https://llmobserve-api-production-d791.up.railway.app",
          },
          {
            name: "customer_id",
            type: "str",
            description: "Customer identifier for per-customer cost tracking. Useful for SaaS applications.",
          },
          {
            name: "tenant_id",
            type: "str",
            description: "Tenant identifier for multi-tenant applications.",
          },
        ]}
      />

      <Callout type="tip">
        You can also set <code>LLMOBSERVE_API_KEY</code> as an environment variable. 
        If set, you can call <code>observe()</code> with no arguments.
      </Callout>

      <h2 id="agent">@agent decorator</h2>

      <p>
        Decorator to label all LLM calls within a function. The label appears in your 
        dashboard for cost breakdown by agent.
      </p>

      <CodeBlock
        code={`from llmobserve import agent

@agent("researcher")
def research_workflow(query: str):
    # All LLM calls here are labeled "agent:researcher"
    response = client.chat.completions.create(...)
    return response

@agent("writer", metadata={"version": "2.0"})
def writing_workflow(topic: str):
    # Additional metadata is attached to events
    response = client.chat.completions.create(...)
    return response`}
        language="python"
      />

      <ParameterTable
        parameters={[
          {
            name: "name",
            type: "str",
            required: true,
            description: "Agent name. Used as the label in your dashboard.",
          },
          {
            name: "metadata",
            type: "dict",
            description: "Optional metadata to attach to all events from this agent.",
          },
        ]}
      />

      <h2 id="section">section()</h2>

      <p>
        Context manager for labeling a block of code. Can be nested to create hierarchical labels.
      </p>

      <CodeBlock
        code={`from llmobserve import section

# Simple label
with section("agent:researcher"):
    response = client.chat.completions.create(...)

# Nested labels (creates "agent:researcher/tool:search")
with section("agent:researcher"):
    with section("tool:search"):
        results = search_api.query(...)
    
    with section("tool:summarize"):
        summary = client.chat.completions.create(...)`}
        language="python"
      />

      <ParameterTable
        parameters={[
          {
            name: "name",
            type: "str",
            required: true,
            description: "Section label. Common patterns: 'agent:name', 'tool:name', 'workflow:name'.",
          },
          {
            name: "metadata",
            type: "dict",
            description: "Optional metadata to attach to events in this section.",
          },
        ]}
      />

      <h2 id="wrap-all-tools">wrap_all_tools()</h2>

      <p>
        Wrap a list of tools to automatically label each tool's LLM calls. 
        Designed for agent frameworks like LangChain and CrewAI.
      </p>

      <CodeBlock
        code={`from llmobserve import wrap_all_tools

# Your tools
tools = [search_tool, calculator_tool, weather_tool]

# Wrap them
wrapped = wrap_all_tools(tools)

# Each tool's calls are now labeled "tool:{tool_name}"
agent = AgentExecutor(tools=wrapped, ...)`}
        language="python"
      />

      <ParameterTable
        parameters={[
          {
            name: "tools",
            type: "List[Tool]",
            required: true,
            description: "List of tool objects. Each tool should have a 'name' attribute.",
          },
        ]}
      />

      <h2 id="set-customer-id">set_customer_id()</h2>

      <p>
        Dynamically set the customer ID for subsequent LLM calls. Useful when the customer 
        changes during a request (e.g., in a web server).
      </p>

      <CodeBlock
        code={`from llmobserve import observe, set_customer_id

observe(api_key="...")

def handle_request(request):
    # Set customer for this request
    set_customer_id(request.user.customer_id)
    
    # All subsequent LLM calls are tracked for this customer
    response = client.chat.completions.create(...)
    
    return response`}
        language="python"
      />

      <ParameterTable
        parameters={[
          {
            name: "customer_id",
            type: "str",
            required: true,
            description: "Customer identifier. Pass None to clear.",
          },
        ]}
      />

      <h2 id="environment-variables">Environment variables</h2>

      <p>LLMObserve reads these environment variables:</p>

      <ParameterTable
        parameters={[
          {
            name: "LLMOBSERVE_API_KEY",
            type: "string",
            description: "Your API key. If set, you can call observe() without arguments.",
          },
          {
            name: "LLMOBSERVE_COLLECTOR_URL",
            type: "string",
            description: "Custom collector URL. Defaults to production if not set.",
          },
          {
            name: "LLMOBSERVE_DISABLED",
            type: "bool",
            description: "Set to 'true' to disable tracking entirely. Useful for testing.",
            default: "false",
          },
        ]}
      />

      <CodeBlock
        code={`# .env
LLMOBSERVE_API_KEY=llmo_sk_your_key_here

# Optional
LLMOBSERVE_DISABLED=false`}
        language="bash"
        filename=".env"
      />

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/quickstart">Quickstart guide</Link></li>
        <li><Link href="/docs/agents">Agent tracking</Link></li>
        <li><Link href="/docs/customers">Customer tracking</Link></li>
      </ul>
    </DocPage>
  );
}

