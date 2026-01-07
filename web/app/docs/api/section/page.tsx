"use client";

import Link from "next/link";
import { DocPage, CodeBlock, ParameterTable, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "signature", title: "Signature" },
  { id: "parameters", title: "Parameters" },
  { id: "examples", title: "Examples" },
  { id: "notes", title: "Notes" },
];

export default function SectionAPIPage() {
  return (
    <DocPage
      title="section() context manager"
      description="Context manager to label a block of code for cost tracking."
      category="API Reference"
      toc={toc}
    >
      <h2 id="signature">Signature</h2>

      <CodeBlock
        code={`@contextmanager
def section(
    name: str,
    metadata: dict = None,
) -> Generator[None, None, None]`}
        language="python"
      />

      <h2 id="parameters">Parameters</h2>

      <ParameterTable
        parameters={[
          {
            name: "name",
            type: "str",
            required: true,
            description: "Section label. Common patterns: 'agent:name', 'tool:name', 'workflow:name'. Can be any string.",
          },
          {
            name: "metadata",
            type: "dict",
            description: "Optional metadata to attach to all events in this section.",
          },
        ]}
      />

      <h2 id="examples">Examples</h2>

      <h3>Basic usage</h3>

      <CodeBlock
        code={`from llmobserve import observe, section
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

# Label a code block
with section("agent:researcher"):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Research AI"}]
    )
    # This call is labeled "agent:researcher"`}
        language="python"
      />

      <h3>Nested sections</h3>

      <CodeBlock
        code={`with section("workflow:research_pipeline"):
    with section("agent:researcher"):
        with section("tool:search"):
            # Labeled "workflow:research_pipeline/agent:researcher/tool:search"
            results = search_api.query("AI news")
        
        with section("tool:analyze"):
            # Labeled "workflow:research_pipeline/agent:researcher/tool:analyze"
            analysis = client.chat.completions.create(...)`}
        language="python"
      />

      <h3>With metadata</h3>

      <CodeBlock
        code={`with section("agent:researcher", metadata={"query_type": "scientific"}):
    response = client.chat.completions.create(...)
    # Metadata attached to all events in this section`}
        language="python"
      />

      <h3>Async usage</h3>

      <CodeBlock
        code={`async def process_request():
    with section("agent:async_processor"):
        # Works in async contexts
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[...]
        )
        return response`}
        language="python"
      />

      <h2 id="notes">Notes</h2>

      <Callout type="tip" title="Naming conventions">
        Use prefixes like <code>agent:</code>, <code>tool:</code>, <code>workflow:</code> to 
        organize your sections. This makes filtering easier in the dashboard.
      </Callout>

      <ul>
        <li>Sections can be nested to any depth</li>
        <li>Nested section names are joined with <code>/</code></li>
        <li>Works in both sync and async code</li>
        <li>LLM calls outside any section appear as "Untracked"</li>
        <li>Sections are thread-safe</li>
      </ul>

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/sections">Sections & workflows guide</Link></li>
        <li><Link href="/docs/api/agent">@agent decorator</Link></li>
        <li><Link href="/docs/agents">Agent tracking</Link></li>
      </ul>
    </DocPage>
  );
}

