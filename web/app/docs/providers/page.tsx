"use client";

import Link from "next/link";
import { DocPage, Callout } from "@/components/docs/DocPage";

const toc = [
  { id: "supported-providers", title: "Supported providers" },
  { id: "openai", title: "OpenAI" },
  { id: "anthropic", title: "Anthropic" },
  { id: "google", title: "Google" },
  { id: "other-providers", title: "Other providers" },
];

const providers = [
  { name: "OpenAI", models: "GPT-4o, GPT-4, GPT-3.5, o1, o3-mini", status: "Full support" },
  { name: "Anthropic", models: "Claude 3.5, Claude 3, Claude 2", status: "Full support" },
  { name: "Google", models: "Gemini Pro, Gemini Flash, PaLM", status: "Full support" },
  { name: "Azure OpenAI", models: "All OpenAI models on Azure", status: "Full support" },
  { name: "Cohere", models: "Command, Embed", status: "Full support" },
  { name: "Mistral", models: "Mistral Large, Medium, Small", status: "Full support" },
  { name: "Groq", models: "Llama, Mixtral, Gemma", status: "Full support" },
  { name: "Together AI", models: "70+ open source models", status: "Full support" },
  { name: "Perplexity", models: "pplx-online, pplx-chat", status: "Full support" },
  { name: "OpenRouter", models: "Routes to 100+ models", status: "Full support" },
  { name: "Replicate", models: "Llama, Stable Diffusion, etc.", status: "Full support" },
  { name: "HuggingFace", models: "Inference API models", status: "Full support" },
  { name: "DeepSeek", models: "DeepSeek Chat, Coder", status: "Full support" },
  { name: "Fireworks", models: "Llama, Mixtral, etc.", status: "Full support" },
  { name: "AI21", models: "Jamba, Jurassic", status: "Full support" },
  { name: "Voyage AI", models: "Embeddings", status: "Full support" },
];

export default function ProvidersPage() {
  return (
    <DocPage
      title="Supported providers"
      description="LLMObserve automatically tracks costs for 40+ LLM providers."
      category="Cost tracking"
      toc={toc}
    >
      <h2 id="supported-providers">Supported providers</h2>

      <p>
        LLMObserve automatically detects and tracks API calls to these providers. 
        No configuration needed — just call <code>observe()</code> and start using your 
        preferred provider.
      </p>

      <div className="overflow-x-auto my-6 not-prose">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-3 pr-4 font-semibold text-slate-900">Provider</th>
              <th className="text-left py-3 pr-4 font-semibold text-slate-900">Models</th>
              <th className="text-left py-3 font-semibold text-slate-900">Status</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={p.name} className="border-b border-slate-100">
                <td className="py-3 pr-4 font-medium text-slate-900">{p.name}</td>
                <td className="py-3 pr-4 text-slate-600">{p.models}</td>
                <td className="py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    {p.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Callout type="info" title="Don't see your provider?">
        LLMObserve works with any provider that uses standard HTTP APIs. If your provider 
        isn't being detected, <a href="mailto:support@llmobserve.com">let us know</a> and 
        we'll add explicit support.
      </Callout>

      <h2 id="openai">OpenAI</h2>

      <p>Full support for all OpenAI models including:</p>

      <ul>
        <li><strong>GPT-4o</strong> — Latest multimodal model</li>
        <li><strong>GPT-4o-mini</strong> — Cost-effective option</li>
        <li><strong>GPT-4 Turbo</strong> — 128K context</li>
        <li><strong>GPT-3.5 Turbo</strong> — Fast and affordable</li>
        <li><strong>o1, o1-mini</strong> — Reasoning models</li>
        <li><strong>Embeddings</strong> — text-embedding-3-small/large</li>
        <li><strong>DALL-E</strong> — Image generation</li>
        <li><strong>Whisper</strong> — Audio transcription</li>
      </ul>

      <h2 id="anthropic">Anthropic</h2>

      <p>Full support for Claude models:</p>

      <ul>
        <li><strong>Claude 3.5 Sonnet</strong> — Best balance of speed and intelligence</li>
        <li><strong>Claude 3 Opus</strong> — Most capable</li>
        <li><strong>Claude 3 Sonnet</strong> — Balanced performance</li>
        <li><strong>Claude 3 Haiku</strong> — Fastest</li>
      </ul>

      <h2 id="google">Google</h2>

      <p>Support for Google AI models:</p>

      <ul>
        <li><strong>Gemini 2.0 Flash</strong> — Latest multimodal</li>
        <li><strong>Gemini 1.5 Pro</strong> — 1M+ context window</li>
        <li><strong>Gemini 1.5 Flash</strong> — Fast and efficient</li>
      </ul>

      <h2 id="other-providers">Other providers</h2>

      <p>
        We support many more providers including Cohere, Mistral, Groq, Together AI, 
        Perplexity, Replicate, HuggingFace, and others. All are automatically detected 
        based on API endpoint patterns.
      </p>

      <h3>OpenRouter</h3>

      <p>
        OpenRouter is a special case — it routes requests to multiple providers. We detect 
        the actual model being called and track costs accordingly.
      </p>

      <hr />

      <h3>See also</h3>

      <ul>
        <li><Link href="/docs/cost-tracking">How cost tracking works</Link></li>
        <li><Link href="/docs/quickstart">Quickstart guide</Link></li>
      </ul>
    </DocPage>
  );
}

