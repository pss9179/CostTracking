"use client";

import Link from "next/link";
import { DocPage, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "general", title: "General" },
  { id: "cost-tracking", title: "Cost tracking" },
  { id: "privacy-security", title: "Privacy & security" },
  { id: "pricing", title: "Pricing" },
];

export default function FAQPage() {
  return (
    <DocPage
      title="Frequently Asked Questions"
      description="Common questions about LLMObserve."
      category="Help"
      toc={toc}
    >
      <h2 id="general">General</h2>

      <h3>What is LLMObserve?</h3>
      <p>
        LLMObserve is a lightweight SDK that automatically tracks costs for your LLM API calls. 
        Add 2 lines of code and see costs broken down by provider, model, agent, or customer.
      </p>

      <h3>Which LLM providers are supported?</h3>
      <p>
        We support 40+ providers including OpenAI, Anthropic, Google, Cohere, Mistral, Groq, 
        Together AI, and many more. See <Link href="/docs/providers">Supported providers</Link> for 
        the full list.
      </p>

      <h3>Does this work with agent frameworks like LangChain?</h3>
      <p>
        Yes! We support LangChain, CrewAI, AutoGen, LlamaIndex, and custom agent frameworks. 
        Use <code>@agent</code> decorators or <code>wrap_all_tools()</code> to track agent costs. 
        See <Link href="/docs/agents">Agent tracking</Link> for details.
      </p>

      <h3>How long does setup take?</h3>
      <p>
        Under 2 minutes. Install the package, add 2 lines of code, and you're tracking costs. 
        See the <Link href="/docs/quickstart">Quickstart guide</Link>.
      </p>

      <h2 id="cost-tracking">Cost tracking</h2>

      <h3>How accurate is the cost tracking?</h3>
      <p>
        Very accurate — typically within 1-2% of your provider bills. We track token usage 
        from API responses and calculate costs using our daily-updated pricing database.
      </p>

      <h3>Does streaming work?</h3>
      <p>
        Yes! Streaming responses are fully supported. Token counts and costs are calculated 
        when the stream completes.
      </p>

      <h3>Why do I see "Untracked" costs in my dashboard?</h3>
      <p>
        "Untracked" means LLM calls were made without a label (agent, section, etc.). The calls 
        are still tracked and counted — they're just not organized by agent. Use <code>@agent</code> 
        or <code>section()</code> to label your code.
      </p>

      <h3>What if costs aren't showing up?</h3>
      <p>
        Check that: (1) You called <code>observe()</code> before making LLM calls, (2) Your API 
        key is correct, (3) Your LLM calls are succeeding. See <Link href="/docs/troubleshooting">Troubleshooting</Link>.
      </p>

      <h2 id="privacy-security">Privacy & security</h2>

      <h3>Do you store my LLM API keys?</h3>
      <p>
        <strong>No.</strong> We never see or store your LLM provider API keys. Your API calls 
        go directly to providers (OpenAI, Anthropic, etc.). We only track metadata like 
        tokens, costs, and latency.
      </p>

      <h3>Do you store my prompts or responses?</h3>
      <p>
        <strong>No.</strong> By default, we only track token counts and metadata. We do not 
        log or store prompt content or LLM responses.
      </p>

      <h3>Where is my data stored?</h3>
      <p>
        Cost and usage data is stored in secure, encrypted databases. We use Railway for 
        hosting with automatic backups.
      </p>

      <h3>Can I self-host?</h3>
      <p>
        The collector is currently hosted only. For enterprise self-hosting options, 
        contact us at enterprise@llmobserve.com.
      </p>

      <h2 id="pricing">Pricing</h2>

      <h3>How much does LLMObserve cost?</h3>
      <p>
        LLMObserve costs $5/month for unlimited tracking. No per-event fees, no hidden costs.
      </p>

      <h3>Is there a free trial?</h3>
      <p>
        Yes! Sign up and track costs free for 7 days. No credit card required for the trial.
      </p>

      <h3>What's included?</h3>
      <p>
        Everything: unlimited API calls tracked, all providers, agent tracking, customer 
        tracking, spending caps, dashboard analytics, and email support.
      </p>

      <hr />

      <Callout type="info" title="Have another question?">
        Email us at <a href="mailto:support@llmobserve.com">support@llmobserve.com</a> and 
        we'll get back to you within 24 hours.
      </Callout>
    </DocPage>
  );
}

