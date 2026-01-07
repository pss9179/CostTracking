"use client";

import Link from "next/link";
import { DocPage, CodeBlock, Callout, Steps } from "@/components/docs/DocPage";
import { ArrowRight, Zap, Users, Shield, BarChart3 } from "lucide-react";

const toc = [
  { id: "what-is-llmobserve", title: "What is LLMObserve?" },
  { id: "key-features", title: "Key features" },
  { id: "how-it-works", title: "How it works" },
  { id: "getting-started", title: "Getting started" },
];

export default function DocsOverview() {
  return (
    <DocPage
      title="LLMObserve Documentation"
      description="Everything you need to track, understand, and optimize your LLM spending. Get started in under 2 minutes with just 2 lines of code."
      toc={toc}
    >
      {/* Quick Links */}
      <div className="grid md:grid-cols-2 gap-4 not-prose mb-10">
        <Link
          href="/docs/quickstart"
          className="flex items-center gap-4 p-4 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors group"
        >
          <div className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900 group-hover:text-emerald-700">Quickstart</h3>
            <p className="text-sm text-slate-500">Get up and running in 2 minutes</p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600" />
        </Link>
        
        <Link
          href="/docs/sdk"
          className="flex items-center gap-4 p-4 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/50 transition-colors group"
        >
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-slate-900 group-hover:text-emerald-700">API Reference</h3>
            <p className="text-sm text-slate-500">Full SDK documentation</p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600" />
        </Link>
      </div>

      <h2 id="what-is-llmobserve">What is LLMObserve?</h2>
      
      <p>
        LLMObserve is a lightweight cost tracking SDK for LLM applications. It automatically 
        captures every API call to OpenAI, Anthropic, Google, and 40+ other providers, 
        calculating costs in real-time based on token usage.
      </p>

      <p>
        Unlike complex observability platforms, LLMObserve focuses on one thing: <strong>helping you 
        understand and control your LLM spending</strong>. Whether you're a solo developer or running 
        a SaaS with thousands of customers, you get instant visibility into where your money goes.
      </p>

      <h2 id="key-features">Key features</h2>

      <div className="grid md:grid-cols-2 gap-6 not-prose my-6">
        <div className="p-5 rounded-xl border border-slate-200">
          <div className="w-10 h-10 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center mb-3">
            <BarChart3 className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Automatic cost tracking</h3>
          <p className="text-sm text-slate-600">
            Every LLM call is tracked automatically. See costs by provider, model, agent, or customer.
          </p>
        </div>

        <div className="p-5 rounded-xl border border-slate-200">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-lg flex items-center justify-center mb-3">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Customer-level tracking</h3>
          <p className="text-sm text-slate-600">
            Perfect for SaaS. Track costs per customer to understand profitability and set usage limits.
          </p>
        </div>

        <div className="p-5 rounded-xl border border-slate-200">
          <div className="w-10 h-10 bg-amber-100 text-amber-600 rounded-lg flex items-center justify-center mb-3">
            <Shield className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Spending caps</h3>
          <p className="text-sm text-slate-600">
            Set budget limits with alerts. Optionally block API calls when caps are exceeded.
          </p>
        </div>

        <div className="p-5 rounded-xl border border-slate-200">
          <div className="w-10 h-10 bg-purple-100 text-purple-600 rounded-lg flex items-center justify-center mb-3">
            <Zap className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-slate-900 mb-2">Agent tracking</h3>
          <p className="text-sm text-slate-600">
            Label costs by agent, tool, or workflow. Works with LangChain, CrewAI, and custom frameworks.
          </p>
        </div>
      </div>

      <h2 id="how-it-works">How it works</h2>

      <p>
        LLMObserve works by intercepting HTTP requests to LLM providers. When you call 
        <code>observe()</code>, the SDK patches common HTTP libraries (httpx, requests, aiohttp) 
        to capture request/response metadata.
      </p>

      <Callout type="tip" title="Zero performance impact">
        LLMObserve adds minimal overhead. Events are batched and sent asynchronously in the 
        background. Your LLM calls execute exactly as before.
      </Callout>

      <p>Here's what happens when you make an LLM API call:</p>

      <ol>
        <li><strong>You call the LLM API</strong> — OpenAI, Anthropic, etc. as normal</li>
        <li><strong>SDK intercepts the request</strong> — Captures model, tokens, latency</li>
        <li><strong>Cost is calculated</strong> — Using our up-to-date pricing database</li>
        <li><strong>Event is sent</strong> — Asynchronously batched to our collector</li>
        <li><strong>Dashboard updates</strong> — See costs in real-time</li>
      </ol>

      <h2 id="getting-started">Getting started</h2>

      <p>The fastest way to get started is with our 2-minute quickstart:</p>

      <Steps
        steps={[
          {
            title: "Install the SDK",
            description: "Install llmobserve using pip",
            children: <CodeBlock code="pip install llmobserve" language="bash" />
          },
          {
            title: "Get your API key",
            description: "Sign up and copy your API key from the Settings page",
          },
          {
            title: "Add 2 lines of code",
            description: "Initialize llmobserve before making LLM calls",
            children: (
              <CodeBlock
                code={`import llmobserve
llmobserve.observe(api_key="your-api-key")`}
                language="python"
              />
            )
          },
        ]}
      />

      <p>
        That's it! All your LLM API calls are now tracked automatically. 
        See the <Link href="/docs/quickstart" className="text-emerald-600 hover:underline">Quickstart guide</Link> for 
        a complete walkthrough.
      </p>

      <hr />

      <h3>Next steps</h3>
      
      <ul>
        <li><Link href="/docs/quickstart">Quickstart guide</Link> — Full setup walkthrough</li>
        <li><Link href="/docs/agents">Agent tracking</Link> — Label costs by agent or workflow</li>
        <li><Link href="/docs/customers">Customer tracking</Link> — Track costs per customer</li>
        <li><Link href="/docs/spending-caps">Spending caps</Link> — Set budget limits</li>
      </ul>
    </DocPage>
  );
}
