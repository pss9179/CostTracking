"use client";

import { Terminal, Check, Copy, Code2, Layers, Settings, AlertTriangle, Shield, Bell, ChevronDown, ChevronRight, ArrowRight } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

// Full model list from pricing registry
const SUPPORTED_MODELS = {
  openai: {
    name: "OpenAI",
    models: [
      "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
      "o1-preview", "o1-mini", "o4-mini",
      "text-embedding-3-small", "text-embedding-3-large",
      "whisper-1", "tts-1", "tts-1-hd", "dall-e-3", "dall-e-2",
    ]
  },
  anthropic: {
    name: "Anthropic",
    models: ["claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
  },
  google: {
    name: "Google",
    models: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
  },
  cohere: {
    name: "Cohere",
    models: ["command", "command-light", "command-r", "command-r-plus"]
  },
  mistral: {
    name: "Mistral",
    models: ["mistral-large-latest", "mistral-small-latest", "mistral-7b", "mixtral-8x7b"]
  },
  meta: {
    name: "Meta (Llama)",
    models: ["llama-3.1-405b", "llama-3.1-70b", "llama-3.1-8b", "llama-3.2-3b"]
  },
  groq: {
    name: "Groq",
    models: ["llama-3.1-405b", "llama-3.1-70b", "mixtral-8x7b"]
  },
  deepseek: {
    name: "DeepSeek",
    models: ["deepseek-chat", "deepseek-coder", "deepseek-r1"]
  },
  pinecone: {
    name: "Pinecone",
    models: ["query", "upsert", "llama-text-embed-v2"]
  },
};

export default function PublicDocsPage() {
    const [activeTab, setActiveTab] = useState<"python" | "node">("python");
    const [expandedProviders, setExpandedProviders] = useState<string[]>(["openai", "anthropic"]);

    const toggleProvider = (provider: string) => {
        setExpandedProviders(prev => 
            prev.includes(provider) 
                ? prev.filter(p => p !== provider)
                : [...prev, provider]
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
            {/* Header */}
            <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
                <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
                    <Link href="https://llmobserve.com" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                            <span className="text-white font-bold text-sm">S</span>
                        </div>
                        <span className="font-semibold text-gray-900">Skyline Docs</span>
                    </Link>
                    <div className="flex items-center gap-4">
                        <Link 
                            href="https://app.llmobserve.com/sign-in" 
                            className="text-sm text-gray-600 hover:text-gray-900"
                        >
                            Sign In
                        </Link>
                        <Link 
                            href="https://app.llmobserve.com/sign-up" 
                            className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                        >
                            Get Started Free
                        </Link>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-12 space-y-16">
                {/* Hero */}
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-bold tracking-tight text-gray-900">API Documentation</h1>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers. 
                        Just 2 lines of code.
                    </p>
                </div>

                {/* Language Toggle */}
                <div className="flex justify-center">
                    <div className="flex gap-2 p-1 bg-slate-100 rounded-lg">
                        <button
                            onClick={() => setActiveTab("python")}
                            className={`px-6 py-2.5 rounded-md text-sm font-medium transition-colors ${
                                activeTab === "python" 
                                    ? "bg-white shadow text-gray-900" 
                                    : "text-gray-600 hover:text-gray-900"
                            }`}
                        >
                            Python
                        </button>
                        <button
                            onClick={() => setActiveTab("node")}
                            className={`px-6 py-2.5 rounded-md text-sm font-medium transition-colors ${
                                activeTab === "node" 
                                    ? "bg-white shadow text-gray-900" 
                                    : "text-gray-600 hover:text-gray-900"
                            }`}
                        >
                            Node.js / TypeScript
                        </button>
                    </div>
                </div>

                {/* Quick Start */}
                <section className="space-y-6">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600">
                            <Terminal className="h-5 w-5" />
                        </div>
                        <h2 className="text-2xl font-semibold text-gray-900">Quick Start</h2>
                    </div>

                    {/* Installation */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium text-gray-700">1. Install the SDK</h3>
                        <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-slate-300 flex items-center justify-between">
                            <span>{activeTab === "python" ? "pip install llmobserve" : "npm install llmobserve-sdk"}</span>
                            <CopyButton text={activeTab === "python" ? "pip install llmobserve" : "npm install llmobserve-sdk"} />
                        </div>
                    </div>

                    {/* Code */}
                    <div className="space-y-2">
                        <h3 className="text-sm font-medium text-gray-700">2. Initialize (2 lines!)</h3>
                        {activeTab === "python" ? (
                            <CodeBlock language="python" code={`import llmobserve

llmobserve.observe(api_key="llmo_sk_your_key_here")

# That's it! All LLM calls are now tracked automatically.
# Use OpenAI, Anthropic, etc. as normal - we handle the rest.`} />
                        ) : (
                            <CodeBlock language="typescript" code={`import { observe } from 'llmobserve-sdk';

observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_your_key_here'
});

// That's it! All LLM calls are now tracked automatically.`} />
                        )}
                    </div>
                </section>

                {/* How It Works */}
                <section className="space-y-6">
                    <h2 className="text-2xl font-semibold text-gray-900">How It Works</h2>
                    <div className="grid gap-6 md:grid-cols-3">
                        <Card
                            icon={<Layers className="h-5 w-5" />}
                            title="Zero-Config Tracking"
                            description="We patch HTTP clients to automatically capture API calls. Works with any provider."
                        />
                        <Card
                            icon={<Code2 className="h-5 w-5" />}
                            title="Section Labels"
                            description="Use section() to organize costs by feature, agent, or workflow."
                        />
                        <Card
                            icon={<Settings className="h-5 w-5" />}
                            title="Multi-Language"
                            description="Python and Node.js SDKs. Same API, same dashboard."
                        />
                    </div>
                </section>

                {/* Complete Example */}
                <section className="space-y-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Complete Example</h2>
                    {activeTab === "python" ? (
                        <CodeBlock language="python" code={`import llmobserve
from llmobserve import section, set_customer_id
from openai import OpenAI

# Initialize once at startup
llmobserve.observe(api_key="llmo_sk_your_key_here")

client = OpenAI()

# Optional: Track costs per customer
set_customer_id("customer_123")

# Optional: Tag costs with a feature name
with section("feature:chat_assistant"):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}]
    )

print(response.choices[0].message.content)
# ✅ Costs automatically tracked in your dashboard!`} />
                    ) : (
                        <CodeBlock language="typescript" code={`import { observe, section, setCustomerId } from 'llmobserve-sdk';
import OpenAI from 'openai';

// Initialize once at startup
observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_your_key_here'
});

const openai = new OpenAI();

// Optional: Track costs per customer
setCustomerId('customer_123');

// Optional: Tag costs with a feature name
await section('feature:chat_assistant').run(async () => {
  const response = await openai.chat.completions.create({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello!' }]
  });
  console.log(response.choices[0].message.content);
});
// ✅ Costs automatically tracked in your dashboard!`} />
                    )}
                </section>

                {/* Core API */}
                <section className="space-y-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Core API Reference</h2>
                    
                    <div className="space-y-6">
                        {activeTab === "python" ? (
                            <>
                                <ApiMethod
                                    name="observe(api_key)"
                                    description="Initialize LLMObserve. Call once at app startup."
                                    example={`llmobserve.observe(api_key="llmo_sk_...")`}
                                />
                                <ApiMethod
                                    name="section(name)"
                                    description="Context manager to tag costs with a feature name."
                                    example={`with section("feature:summarizer"):
    response = client.chat.completions.create(...)`}
                                />
                                <ApiMethod
                                    name="set_customer_id(id)"
                                    description="Track costs per customer for multi-tenant apps."
                                    example={`set_customer_id("customer_123")`}
                                />
                            </>
                        ) : (
                            <>
                                <ApiMethod
                                    name="observe({ collectorUrl, apiKey })"
                                    description="Initialize LLMObserve. Call once at app startup."
                                    example={`observe({
  collectorUrl: 'https://...',
  apiKey: 'llmo_sk_...'
});`}
                                />
                                <ApiMethod
                                    name="section(name).run(fn)"
                                    description="Run async function with feature tagging."
                                    example={`await section('feature:summarizer').run(async () => {
  // LLM calls here are tagged
});`}
                                />
                                <ApiMethod
                                    name="setCustomerId(id)"
                                    description="Track costs per customer for multi-tenant apps."
                                    example={`setCustomerId('customer_123');`}
                                />
                                <ApiMethod
                                    name="flush()"
                                    description="Flush pending events before process exit."
                                    example={`await flush();`}
                                />
                            </>
                        )}
                    </div>
                </section>

                {/* Spending Caps */}
                <section className="space-y-6">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-600">
                            <Shield className="h-5 w-5" />
                        </div>
                        <h2 className="text-2xl font-semibold text-gray-900">Spending Caps & Alerts</h2>
                    </div>

                    <p className="text-gray-600">
                        Set budget limits to prevent runaway costs. Configure in your dashboard.
                    </p>

                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="p-6 rounded-xl border border-gray-200 bg-white">
                            <div className="flex items-center gap-2 mb-3">
                                <Bell className="h-5 w-5 text-amber-600" />
                                <h3 className="font-semibold text-gray-900">Soft Caps (Alerts)</h3>
                            </div>
                            <p className="text-sm text-gray-600">
                                Get email notifications at thresholds (80%, 95%, 100%). Calls continue to work.
                            </p>
                        </div>

                        <div className="p-6 rounded-xl border border-gray-200 bg-white">
                            <div className="flex items-center gap-2 mb-3">
                                <AlertTriangle className="h-5 w-5 text-red-600" />
                                <h3 className="font-semibold text-gray-900">Hard Caps (Blocking)</h3>
                            </div>
                            <p className="text-sm text-gray-600">
                                Block calls when exceeded. SDK throws <code className="text-xs bg-gray-100 px-1 rounded">BudgetExceededError</code>.
                            </p>
                        </div>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 pt-4">Handling Hard Caps</h3>
                    {activeTab === "python" ? (
                        <CodeBlock language="python" code={`from llmobserve import observe, BudgetExceededError

observe(api_key="llmo_sk_...")

try:
    response = client.chat.completions.create(...)
except BudgetExceededError as e:
    print(f"Cap exceeded: {e}")
    # Handle gracefully - switch model, queue request, etc.`} />
                    ) : (
                        <CodeBlock language="typescript" code={`import { observe, BudgetExceededError } from 'llmobserve-sdk';

try {
  const response = await openai.chat.completions.create(...);
} catch (error) {
  if (error instanceof BudgetExceededError) {
    console.error('Budget exceeded!', error.exceededCaps);
    // Handle gracefully
  }
}`} />
                    )}
                </section>

                {/* Supported Providers */}
                <section className="space-y-6">
                    <h2 className="text-2xl font-semibold text-gray-900">Supported Providers</h2>
                    
                    <p className="text-gray-600">
                        We track costs for {Object.values(SUPPORTED_MODELS).reduce((acc, p) => acc + p.models.length, 0)}+ models across {Object.keys(SUPPORTED_MODELS).length}+ providers.
                    </p>

                    <div className="space-y-2">
                        {Object.entries(SUPPORTED_MODELS).map(([key, provider]) => (
                            <div key={key} className="border border-gray-200 rounded-lg bg-white overflow-hidden">
                                <button
                                    onClick={() => toggleProvider(key)}
                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        <span className="font-medium text-gray-900">{provider.name}</span>
                                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                                            {provider.models.length} models
                                        </span>
                                    </div>
                                    {expandedProviders.includes(key) ? (
                                        <ChevronDown className="h-4 w-4 text-gray-400" />
                                    ) : (
                                        <ChevronRight className="h-4 w-4 text-gray-400" />
                                    )}
                                </button>
                                {expandedProviders.includes(key) && (
                                    <div className="px-4 pb-4 pt-1 border-t border-gray-100">
                                        <div className="flex flex-wrap gap-2">
                                            {provider.models.map((model) => (
                                                <code 
                                                    key={model} 
                                                    className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded font-mono"
                                                >
                                                    {model}
                                                </code>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </section>

                {/* CTA */}
                <section className="text-center py-12 space-y-6">
                    <h2 className="text-3xl font-bold text-gray-900">Ready to track your LLM costs?</h2>
                    <p className="text-gray-600 max-w-xl mx-auto">
                        Get started in under 2 minutes. Free forever.
                    </p>
                    <Link 
                        href="https://app.llmobserve.com/sign-up" 
                        className="inline-flex items-center gap-2 bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
                    >
                        Get Started Free
                        <ArrowRight className="h-4 w-4" />
                    </Link>
                </section>
            </main>

            {/* Footer */}
            <footer className="border-t border-gray-200 bg-gray-50">
                <div className="max-w-5xl mx-auto px-6 py-8 flex items-center justify-between text-sm text-gray-600">
                    <span>© 2025 Skyline / LLMObserve</span>
                    <div className="flex gap-6">
                        <Link href="https://llmobserve.com" className="hover:text-gray-900">Home</Link>
                        <Link href="https://app.llmobserve.com/pricing" className="hover:text-gray-900">Pricing</Link>
                    </div>
                </div>
            </footer>
        </div>
    );
}

function Card({ title, description, icon }: { title: string; description: string; icon?: React.ReactNode }) {
    return (
        <div className="p-6 rounded-xl border border-gray-200 bg-white">
            <div className="flex items-center gap-2 mb-2">
                {icon && <div className="text-indigo-600">{icon}</div>}
                <h3 className="font-semibold text-gray-900">{title}</h3>
            </div>
            <p className="text-sm text-gray-600">{description}</p>
        </div>
    );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
    return (
        <div className="relative bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-xl">
            <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
                <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/40" />
                    <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/40" />
                </div>
                <span className="text-xs font-medium text-slate-500">{language}</span>
            </div>
            <div className="p-4 overflow-x-auto">
                <pre className="font-mono text-sm leading-relaxed text-slate-300 whitespace-pre">{code}</pre>
            </div>
            <CopyButton text={code} />
        </div>
    );
}

function ApiMethod({ name, description, example }: { name: string; description: string; example: string }) {
    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
            <div className="bg-gray-50 px-5 py-3 border-b border-gray-200">
                <code className="font-mono font-semibold text-indigo-600">{name}</code>
                <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
            <div className="p-4">
                <pre className="bg-slate-950 text-slate-300 rounded-lg p-3 text-sm font-mono overflow-x-auto">{example}</pre>
            </div>
        </div>
    );
}

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const copy = () => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button
            onClick={copy}
            className="absolute top-12 right-3 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 border border-slate-700 transition-all"
            title="Copy to clipboard"
        >
            {copied ? (
                <Check className="h-4 w-4 text-green-400" />
            ) : (
                <Copy className="h-4 w-4 text-slate-400" />
            )}
        </button>
    );
}
