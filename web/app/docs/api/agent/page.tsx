"use client";

import Link from "next/link";
import { DocPage, CodeBlock, ParameterTable, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "signature", title: "Signature" },
  { id: "parameters", title: "Parameters" },
  { id: "examples", title: "Examples" },
  { id: "notes", title: "Notes" },
];

export default function AgentAPIPage() {
  return (
    <DocPage
      title="@agent decorator"
      description="Decorator to label all LLM calls within a function."
      category="API Reference"
      toc={toc}
    >
      <h2 id="signature">Signature</h2>

      <CodeBlock
        code={`def agent(
    name: str,
    metadata: dict = None,
) -> Callable`}
        language="python"
      />

      <h2 id="parameters">Parameters</h2>

      <ParameterTable
        parameters={[
          {
            name: "name",
            type: "str",
            required: true,
            description: "Agent name used as the label in your dashboard. Appears as 'agent:{name}'.",
          },
          {
            name: "metadata",
            type: "dict",
            description: "Optional metadata to attach to all events from this agent. Useful for versioning or additional context.",
          },
        ]}
      />

      <h2 id="examples">Examples</h2>

      <h3>Basic usage</h3>

      <CodeBlock
        code={`from llmobserve import observe, agent
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

@agent("researcher")
def research_topic(topic: str):
    # All LLM calls here are labeled "agent:researcher"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Research: {topic}"}]
    )
    return response.choices[0].message.content

result = research_topic("quantum computing")`}
        language="python"
      />

      <h3>With metadata</h3>

      <CodeBlock
        code={`@agent("researcher", metadata={"version": "2.0", "team": "science"})
def research_topic(topic: str):
    # Metadata is attached to all events
    response = client.chat.completions.create(...)
    return response`}
        language="python"
      />

      <h3>Async functions</h3>

      <CodeBlock
        code={`@agent("async_researcher")
async def async_research(topic: str):
    # Works with async functions too
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Research: {topic}"}]
    )
    return response.choices[0].message.content`}
        language="python"
      />

      <h3>Multiple agents</h3>

      <CodeBlock
        code={`@agent("researcher")
def research_workflow(query):
    return client.chat.completions.create(...)

@agent("writer")
def writing_workflow(content):
    return client.chat.completions.create(...)

@agent("editor")
def editing_workflow(draft):
    return client.chat.completions.create(...)

# Each function's costs tracked separately
research = research_workflow("AI trends")
draft = writing_workflow(research)
final = editing_workflow(draft)`}
        language="python"
      />

      <h2 id="notes">Notes</h2>

      <Callout type="info">
        The <code>@agent</code> decorator is syntactic sugar for wrapping a function in 
        a <code>section()</code> context. Use <code>section()</code> directly for more 
        granular control.
      </Callout>

      <ul>
        <li>Works with both sync and async functions</li>
        <li>Can be combined with <code>section()</code> for nested labeling</li>
        <li>Nested agent calls each get their own label</li>
        <li>Labels appear in the Features page of your dashboard</li>
      </ul>

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/agents">Agent tracking guide</Link></li>
        <li><Link href="/docs/api/section">section() context manager</Link></li>
        <li><Link href="/docs/api/observe">observe()</Link></li>
      </ul>
    </DocPage>
  );
}

