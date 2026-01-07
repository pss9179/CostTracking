"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "overview", title: "Overview" },
  { id: "basic-usage", title: "Basic usage" },
  { id: "nested-sections", title: "Nested sections" },
  { id: "naming-conventions", title: "Naming conventions" },
];

export default function SectionsPage() {
  return (
    <DocPage
      title="Sections & workflows"
      description="Use sections to label and organize costs for complex workflows and pipelines."
      category="Labeling & organization"
      toc={toc}
    >
      <h2 id="overview">Overview</h2>

      <p>
        Sections let you label arbitrary blocks of code. Unlike the <code>@agent</code> decorator 
        (which labels entire functions), sections can wrap any code block and can be nested 
        to create hierarchical labels.
      </p>

      <Callout type="tip">
        Use sections for fine-grained labeling, especially in complex workflows where you 
        want to track costs for individual steps.
      </Callout>

      <h2 id="basic-usage">Basic usage</h2>

      <CodeBlock
        code={`from llmobserve import observe, section
from openai import OpenAI

observe(api_key="...")
client = OpenAI()

# Label a block of code
with section("agent:researcher"):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Research quantum computing"}]
    )
    # This call is labeled "agent:researcher"

# Outside the section, calls are unlabeled
response2 = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
# This call is "Untracked"`}
        language="python"
      />

      <h2 id="nested-sections">Nested sections</h2>

      <p>
        Sections can be nested to create hierarchical labels. This is useful for tracking 
        costs at multiple levels — e.g., by agent AND by tool.
      </p>

      <CodeBlock
        code={`from llmobserve import section

with section("workflow:research_pipeline"):
    # Labeled "workflow:research_pipeline"
    
    with section("agent:researcher"):
        # Labeled "workflow:research_pipeline/agent:researcher"
        
        with section("tool:web_search"):
            # Labeled "workflow:research_pipeline/agent:researcher/tool:web_search"
            search_results = search_api.query("AI news")
        
        with section("tool:summarize"):
            # Labeled "workflow:research_pipeline/agent:researcher/tool:summarize"
            summary = client.chat.completions.create(...)
    
    with section("agent:writer"):
        # Labeled "workflow:research_pipeline/agent:writer"
        article = client.chat.completions.create(...)`}
        language="python"
      />

      <p>
        In your dashboard, you'll see costs broken down at each level:
      </p>

      <ul>
        <li><code>workflow:research_pipeline</code> — Total for the entire pipeline</li>
        <li><code>workflow:research_pipeline/agent:researcher</code> — Just the researcher</li>
        <li><code>workflow:research_pipeline/agent:researcher/tool:web_search</code> — Just web search</li>
      </ul>

      <h2 id="naming-conventions">Naming conventions</h2>

      <p>
        We recommend using prefixes to categorize your sections:
      </p>

      <ul>
        <li><code>agent:</code> — For agent functions (researcher, writer, analyst)</li>
        <li><code>tool:</code> — For individual tools (search, calculator, weather)</li>
        <li><code>workflow:</code> — For multi-step pipelines</li>
        <li><code>step:</code> — For pipeline steps</li>
        <li><code>feature:</code> — For product features (chat, summarize, translate)</li>
      </ul>

      <CodeBlock
        code={`# Good naming
with section("agent:researcher"): ...
with section("tool:web_search"): ...
with section("workflow:onboarding"): ...
with section("feature:document_qa"): ...

# Also fine - just be consistent
with section("researcher"): ...
with section("my_custom_label"): ...`}
        language="python"
      />

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/agents">Agent tracking</Link></li>
        <li><Link href="/docs/api/section">section() API reference</Link></li>
      </ul>
    </DocPage>
  );
}

