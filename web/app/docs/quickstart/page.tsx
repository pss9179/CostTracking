"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout, Steps } from "@/components/docs/DocPage";

const toc = [
  { id: "prerequisites", title: "Prerequisites" },
  { id: "installation", title: "Installation" },
  { id: "get-api-key", title: "Get your API key" },
  { id: "basic-setup", title: "Basic setup" },
  { id: "verify-tracking", title: "Verify tracking" },
  { id: "next-steps", title: "Next steps" },
];

export default function QuickstartPage() {
  return (
    <DocPage
      title="Quickstart"
      description="Get LLMObserve running in under 2 minutes. Start tracking costs with just 2 lines of code."
      category="Getting started"
      toc={toc}
    >
      <Callout type="tip">
        This guide assumes you already have an LLM application using OpenAI, Anthropic, or another provider. 
        LLMObserve works alongside your existing code with zero changes to your LLM calls.
      </Callout>

      <h2 id="prerequisites">Prerequisites</h2>

      <ul>
        <li>Python 3.8 or higher</li>
        <li>An existing LLM application (OpenAI, Anthropic, etc.)</li>
        <li>An LLMObserve account (<Link href="/sign-up">sign up here</Link>)</li>
      </ul>

      <h2 id="installation">Installation</h2>

      <p>Install the llmobserve package using pip:</p>

      <CodeBlock code="pip install llmobserve" language="bash" filename="Terminal" />

      <p>Or if you're using poetry:</p>

      <CodeBlock code="poetry add llmobserve" language="bash" filename="Terminal" />

      <h2 id="get-api-key">Get your API key</h2>

      <Steps
        steps={[
          {
            title: "Sign up or log in",
            description: "Go to app.llmobserve.com and create an account or sign in",
          },
          {
            title: "Navigate to Settings",
            description: "Click Settings in the sidebar navigation",
          },
          {
            title: "Copy your API key",
            description: "Your API key starts with llmo_sk_. Click copy to clipboard.",
          },
        ]}
      />

      <Callout type="warning" title="Keep your API key secret">
        Never commit your API key to version control. Use environment variables instead.
      </Callout>

      <h2 id="basic-setup">Basic setup</h2>

      <p>
        Add llmobserve to your application. You only need to call <code>observe()</code> once, 
        typically at the start of your application.
      </p>

      <CodeBlock
        code={`import os
from llmobserve import observe
from openai import OpenAI

# Initialize LLMObserve - do this once at startup
observe(api_key=os.getenv("LLMOBSERVE_API_KEY"))

# Use OpenAI as normal - all calls are tracked automatically
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello, world!"}]
)

print(response.choices[0].message.content)`}
        language="python"
        filename="main.py"
      />

      <h3>Using environment variables (recommended)</h3>

      <p>Store your API key in a <code>.env</code> file:</p>

      <CodeBlock
        code={`# .env
LLMOBSERVE_API_KEY=llmo_sk_your_key_here`}
        language="bash"
        filename=".env"
      />

      <p>Then load it in your Python code:</p>

      <CodeBlock
        code={`from dotenv import load_dotenv
load_dotenv()

import os
from llmobserve import observe

observe(api_key=os.getenv("LLMOBSERVE_API_KEY"))`}
        language="python"
        filename="main.py"
      />

      <h2 id="verify-tracking">Verify tracking</h2>

      <p>After running your application with LLMObserve:</p>

      <ol>
        <li>Go to your <Link href="/dashboard">Dashboard</Link></li>
        <li>You should see costs appearing within 10-30 seconds</li>
        <li>Click on any call to see details (model, tokens, latency)</li>
      </ol>

      <Callout type="info" title="Not seeing data?">
        <p>If costs aren't appearing, check that:</p>
        <ul className="mt-2 space-y-1">
          <li>• Your API key is correct</li>
          <li>• You called <code>observe()</code> before making LLM API calls</li>
          <li>• Your LLM calls are completing successfully</li>
        </ul>
        <p className="mt-2">
          See <Link href="/docs/troubleshooting" className="underline">Troubleshooting</Link> for more help.
        </p>
      </Callout>

      <h2 id="next-steps">Next steps</h2>

      <p>Now that you're tracking costs, explore these features:</p>

      <ul>
        <li>
          <Link href="/docs/agents"><strong>Agent tracking</strong></Link> — 
          Label costs by agent or workflow to see which parts of your app cost the most
        </li>
        <li>
          <Link href="/docs/customers"><strong>Customer tracking</strong></Link> — 
          Track costs per customer for SaaS applications
        </li>
        <li>
          <Link href="/docs/spending-caps"><strong>Spending caps</strong></Link> — 
          Set budget limits with alerts to prevent cost overruns
        </li>
        <li>
          <Link href="/docs/sdk"><strong>SDK Reference</strong></Link> — 
          Full API documentation for all SDK functions
        </li>
      </ul>
    </DocPage>
  );
}

