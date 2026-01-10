"use client";

import { Terminal, Check, Copy, Code2, Layers, Settings, AlertTriangle, Shield, Bell, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

// Full model list from pricing registry
const SUPPORTED_MODELS = {
  openai: {
    name: "OpenAI",
    models: [
      // Chat models
      "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
      // Reasoning models
      "o1-preview", "o1-mini", "o4-mini",
      // Future models (pricing ready)
      "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
      "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro",
      // Realtime models
      "gpt-realtime", "gpt-realtime-mini", "gpt-realtime-audio", "gpt-realtime-mini-audio",
      // Embeddings
      "text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002",
      // Audio
      "whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe", "gpt-4o-mini-tts", "tts-1", "tts-1-hd",
      // Image
      "dall-e-3", "dall-e-2", "gpt-image-1", "gpt-image-1-mini",
      // Video
      "sora-2", "sora-2-pro-720", "sora-2-pro-1024",
    ]
  },
  anthropic: {
    name: "Anthropic",
    models: [
      "claude-3.5-sonnet", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"
    ]
  },
  google: {
    name: "Google",
    models: [
      "gemini-2.0-flash", "gemini-2.0-flash-live", "gemini-2.5-flash-live",
      "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"
    ]
  },
  cohere: {
    name: "Cohere",
    models: [
      "command", "command-light", "command-r", "command-r-plus", "embed-english-v3.0"
    ]
  },
  mistral: {
    name: "Mistral",
    models: [
      "mistral-large-latest", "mistral-large", "mistral-small-latest", 
      "mistral-tiny", "mistral-7b", "mixtral-8x7b"
    ]
  },
  meta: {
    name: "Meta (Llama)",
    models: [
      "llama-3.1-405b", "llama-3.1-70b", "llama-3.1-8b",
      "llama-3.2-3b", "llama-3.2-1b"
    ]
  },
  groq: {
    name: "Groq",
    models: [
      "llama-3.1-405b", "llama-3.1-70b", "llama-3.1-8b", "mixtral-8x7b"
    ]
  },
  deepseek: {
    name: "DeepSeek",
    models: [
      "deepseek-chat", "deepseek-coder", "deepseek-r1"
    ]
  },
  qwen: {
    name: "Qwen",
    models: [
      "qwen-2.5-72b", "qwen-2.5-7b", "qwen-2.5-3b",
      "qwen-2-72b", "qwen-2-7b"
    ]
  },
  together: {
    name: "Together AI",
    models: [
      "llama-3-70b", "mixtral-8x22b"
    ]
  },
  perplexity: {
    name: "Perplexity",
    models: [
      "pplx-70b-online", "pplx-7b-online"
    ]
  },
  ai21: {
    name: "AI21",
    models: [
      "j2-ultra", "j2-mid"
    ]
  },
  voyage: {
    name: "Voyage AI",
    models: [
      "voyage-2", "voyage-lite-02"
    ]
  },
  pinecone: {
    name: "Pinecone",
    models: [
      "query", "upsert", "delete", "fetch", "list",
      "llama-text-embed-v2", "multilingual-e5-large", "pinecone-sparse-english-v0",
      "pinecone-rerank-v0", "bge-reranker-v2-m3", "cohere-rerank-v3.5"
    ]
  },
  azure_openai: {
    name: "Azure OpenAI",
    models: [
      "gpt-4", "gpt-35-turbo"
    ]
  },
  aws_bedrock: {
    name: "AWS Bedrock",
    models: [
      "claude-3-opus", "claude-3-sonnet", "llama-3-70b"
    ]
  },
};

export default function ApiDocsPage() {
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
        <div className="p-8 max-w-5xl mx-auto space-y-12">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">API Documentation</h1>
                <p className="text-lg text-gray-600">
                    Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers. Just 2 lines of code.
                </p>
            </div>

            {/* Language Toggle */}
            <div className="flex gap-2 p-1 bg-slate-100 rounded-lg w-fit">
                <button
                    onClick={() => setActiveTab("python")}
                    className={cn(
                        "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                        activeTab === "python" 
                            ? "bg-white shadow text-gray-900" 
                            : "text-gray-600 hover:text-gray-900"
                    )}
                >
                    Python
                </button>
                <button
                    onClick={() => setActiveTab("node")}
                    className={cn(
                        "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                        activeTab === "node" 
                            ? "bg-white shadow text-gray-900" 
                            : "text-gray-600 hover:text-gray-900"
                    )}
                >
                    Node.js / TypeScript
                </button>
            </div>

            {/* Quick Start */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                        <Terminal className="h-5 w-5" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900">Quick Start</h2>
                </div>

                {activeTab === "python" ? (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
                        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                            </div>
                            <span className="text-xs font-medium text-slate-500">python</span>
                        </div>
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">import</span> llmobserve{"\n\n"}
                                llmobserve.<span className="text-blue-400">observe</span>({"(\n"}
                                {"    "}api_key=<span className="text-green-400">"llmo_sk_your_key_here"</span> <span className="text-slate-500"># Get from /settings</span>{"\n"}
                                {")"}
                                {"\n\n"}
                                <span className="text-slate-500"># That's it! All LLM calls are now tracked automatically.</span>
                            </pre>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
                        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                            </div>
                            <span className="text-xs font-medium text-slate-500">typescript</span>
                        </div>
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">import</span> {"{ observe }"} <span className="text-purple-400">from</span> <span className="text-green-400">'llmobserve'</span>;{"\n\n"}
                                <span className="text-blue-400">observe</span>({"{\n"}
                                {"  "}collectorUrl: <span className="text-green-400">'https://llmobserve-api-production-d791.up.railway.app'</span>,{"\n"}
                                {"  "}apiKey: <span className="text-green-400">'llmo_sk_your_key_here'</span> <span className="text-slate-500">// Get from /settings</span>{"\n"}
                                {"}"});
                                {"\n\n"}
                                <span className="text-slate-500">// That's it! All LLM calls are now tracked automatically.</span>
                            </pre>
                        </div>
                    </div>
                )}
            </section>

            {/* Installation */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Installation</h2>
                <div className="space-y-4">
                    {activeTab === "python" ? (
                        <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm text-slate-800 border border-slate-200 flex items-center justify-between">
                            <span>pip install llmobserve</span>
                            <CopyButton text="pip install llmobserve" />
                        </div>
                    ) : (
                        <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm text-slate-800 border border-slate-200 flex items-center justify-between">
                            <span>npm install llmobserve</span>
                            <CopyButton text="npm install llmobserve" />
                        </div>
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
                        description="We patch HTTP clients to automatically capture API calls. Works with any provider that uses standard HTTP."
                    />
                    <Card
                        icon={<Code2 className="h-5 w-5" />}
                        title="Section Labels"
                        description="Use section() context managers to organize costs by feature, agent, or workflow."
                    />
                    <Card
                        icon={<Settings className="h-5 w-5" />}
                        title="Multi-Language"
                        description="Available for Python and Node.js. Same API, same dashboard, same powerful tracking."
                    />
                </div>
            </section>

            {/* Complete Example */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Complete Example</h2>
                {activeTab === "python" ? (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
                        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                            </div>
                            <span className="text-xs font-medium text-slate-500">python</span>
                        </div>
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">import</span> llmobserve{"\n"}
                                <span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> section, set_customer_id{"\n"}
                                <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI{"\n\n"}
                                <span className="text-slate-500"># Initialize once at startup</span>{"\n"}
                                llmobserve.<span className="text-blue-400">observe</span>(api_key=<span className="text-green-400">"llmo_sk_your_key_here"</span>){"\n\n"}
                                client = OpenAI(){"\n\n"}
                                <span className="text-slate-500"># Optional: Track costs per customer</span>{"\n"}
                                set_customer_id(<span className="text-green-400">"customer_123"</span>){"\n\n"}
                                <span className="text-slate-500"># Optional: Tag costs with a feature name</span>{"\n"}
                                <span className="text-purple-400">with</span> section(<span className="text-green-400">"feature:chat_assistant"</span>):{"\n"}
                                {"    "}response = client.chat.completions.<span className="text-blue-400">create</span>({"(\n"}
                                {"        "}model=<span className="text-green-400">"gpt-4o-mini"</span>,{"\n"}
                                {"        "}messages=[{"{"}{"\"role\": \"user\", \"content\": \"Hello!\""}{"}"}]{"\n"}
                                {"    "}{")"}
                                {"\n\n"}
                                <span className="text-blue-400">print</span>(response.choices[<span className="text-yellow-400">0</span>].message.content)
                            </pre>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
                        <div className="flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
                            </div>
                            <span className="text-xs font-medium text-slate-500">typescript</span>
                        </div>
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">import</span> {"{ observe, section, setCustomerId }"} <span className="text-purple-400">from</span> <span className="text-green-400">'llmobserve'</span>;{"\n"}
                                <span className="text-purple-400">import</span> OpenAI <span className="text-purple-400">from</span> <span className="text-green-400">'openai'</span>;{"\n\n"}
                                <span className="text-slate-500">// Initialize once at startup</span>{"\n"}
                                <span className="text-blue-400">observe</span>({"{\n"}
                                {"  "}collectorUrl: <span className="text-green-400">'https://llmobserve-api-production-d791.up.railway.app'</span>,{"\n"}
                                {"  "}apiKey: <span className="text-green-400">'llmo_sk_your_key_here'</span>{"\n"}
                                {"}"});{"\n\n"}
                                <span className="text-purple-400">const</span> openai = <span className="text-purple-400">new</span> OpenAI();{"\n\n"}
                                <span className="text-slate-500">// Optional: Track costs per customer</span>{"\n"}
                                <span className="text-blue-400">setCustomerId</span>(<span className="text-green-400">'customer_123'</span>);{"\n\n"}
                                <span className="text-slate-500">// Optional: Tag costs with a feature name</span>{"\n"}
                                <span className="text-purple-400">await</span> <span className="text-blue-400">section</span>(<span className="text-green-400">'feature:chat_assistant'</span>).<span className="text-blue-400">run</span>(<span className="text-purple-400">async</span> () {"=> {\n"}
                                {"  "}<span className="text-purple-400">const</span> response = <span className="text-purple-400">await</span> openai.chat.completions.<span className="text-blue-400">create</span>({"{\n"}
                                {"    "}model: <span className="text-green-400">'gpt-4o-mini'</span>,{"\n"}
                                {"    "}messages: [{"{ "}role: <span className="text-green-400">'user'</span>, content: <span className="text-green-400">'Hello!'</span> {"}"}]{"\n"}
                                {"  "}{"}"});{"\n"}
                                {"  "}console.<span className="text-blue-400">log</span>(response.choices[<span className="text-yellow-400">0</span>].message.content);{"\n"}
                                {"}"});
                            </pre>
                        </div>
                    </div>
                )}
            </section>

            {/* Core API Reference */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Core API Reference</h2>
                
                <div className="space-y-8">
                    {activeTab === "python" ? (
                        <>
                            <ApiMethod
                                name="observe()"
                                description="Initialize LLMObserve tracking. Call this once at the start of your application."
                                params={[
                                    { name: "api_key", type: "str", description: "Your API key from /settings" },
                                ]}
                                example={`import llmobserve

llmobserve.observe(api_key="llmo_sk_your_key_here")`}
                            />

                            <ApiMethod
                                name="section()"
                                description="Context manager to organize costs by feature. All LLM calls inside the block are tagged with the feature name."
                                params={[
                                    { name: "name", type: "str", description: "Feature name (e.g., 'feature:email_summarizer')" },
                                ]}
                                example={`from llmobserve import section

# Tag this cost with the "email_summarizer" feature
with section("feature:email_summarizer"):
    response = client.chat.completions.create(...)
    
# Now you can see "email_summarizer" costs in your Features tab!`}
                            />

                            <ApiMethod
                                name="set_customer_id()"
                                description="Track costs per customer for multi-tenant SaaS applications."
                                params={[
                                    { name: "customer_id", type: "str", description: "Unique identifier for the customer" },
                                ]}
                                example={`from llmobserve import set_customer_id

set_customer_id("customer_123")
# All subsequent API calls are associated with this customer`}
                            />
                        </>
                    ) : (
                        <>
                            <ApiMethod
                                name="observe()"
                                description="Initialize LLMObserve tracking. Call this once at the start of your application."
                                params={[
                                    { name: "collectorUrl", type: "string", description: "URL of the collector server" },
                                    { name: "apiKey", type: "string", description: "Your API key from /settings" },
                                    { name: "enableCaps", type: "boolean", optional: true, description: "Enable spending cap enforcement (default: true)" },
                                ]}
                                example={`import { observe } from 'llmobserve';

observe({
  collectorUrl: 'https://llmobserve-api-production-d791.up.railway.app',
  apiKey: 'llmo_sk_your_key_here'
});`}
                            />

                            <ApiMethod
                                name="section()"
                                description="Create a named section for grouping related API calls. Returns an object with a run() method."
                                params={[
                                    { name: "name", type: "string", description: "Feature name (e.g., 'feature:email_summarizer')" },
                                ]}
                                example={`import { section } from 'llmobserve';

// Tag costs with the "email_summarizer" feature
await section('feature:email_summarizer').run(async () => {
  const response = await openai.chat.completions.create(...);
});`}
                            />

                            <ApiMethod
                                name="setCustomerId()"
                                description="Track costs per customer for multi-tenant SaaS applications."
                                params={[
                                    { name: "customerId", type: "string", description: "Unique identifier for the customer" },
                                ]}
                                example={`import { setCustomerId } from 'llmobserve';

setCustomerId('customer_123');
// All subsequent API calls are associated with this customer`}
                            />

                            <ApiMethod
                                name="flush()"
                                description="Manually flush all pending events to the collector. Call before process exit."
                                params={[]}
                                example={`import { flush } from 'llmobserve';

// Before exiting your app
await flush();
process.exit(0);`}
                            />
                        </>
                    )}
                </div>
            </section>

            {/* Spending Caps & Alerts */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
                        <Shield className="h-5 w-5" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900">Spending Caps & Alerts</h2>
                </div>

                <p className="text-gray-600">
                    Set budget limits to prevent runaway LLM costs. Configure caps in your{" "}
                    <a href="/caps" className="text-indigo-600 hover:underline">Dashboard → Caps</a> page.
                </p>

                <div className="grid gap-6 md:grid-cols-2">
                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <div className="flex items-center gap-2 mb-3">
                            <Bell className="h-5 w-5 text-amber-600" />
                            <h3 className="font-semibold text-gray-900">Soft Caps (Alerts)</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">
                            Get email notifications when spending reaches thresholds (80%, 95%, 100%). 
                            API calls continue to work.
                        </p>
                    </div>

                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <div className="flex items-center gap-2 mb-3">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <h3 className="font-semibold text-gray-900">Hard Caps (Blocking)</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">
                            Block API calls when caps are exceeded. The SDK throws a{" "}
                            <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">BudgetExceededError</code>.
                        </p>
                    </div>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mt-8">Cap Types</h3>
                
                <div className="grid gap-4 md:grid-cols-4">
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Global</h4>
                        <p className="text-xs text-gray-600">Limit total spending across all providers</p>
                    </div>
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Provider</h4>
                        <p className="text-xs text-gray-600">Limit spending per provider</p>
                    </div>
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Model</h4>
                        <p className="text-xs text-gray-600">Limit spending per model</p>
                    </div>
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Customer</h4>
                        <p className="text-xs text-gray-600">Limit spending per customer</p>
                    </div>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mt-8">Handling Hard Caps</h3>

                {activeTab === "python" ? (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> observe, BudgetExceededError{"\n\n"}
                                observe(api_key=<span className="text-green-400">"llmo_sk_..."</span>){"\n\n"}
                                <span className="text-purple-400">try</span>:{"\n"}
                                {"    "}response = client.chat.completions.<span className="text-blue-400">create</span>(...){"\n"}
                                <span className="text-purple-400">except</span> BudgetExceededError <span className="text-purple-400">as</span> e:{"\n"}
                                {"    "}<span className="text-blue-400">print</span>(<span className="text-green-400">f"Cap exceeded: </span>{"{e}"}<span className="text-green-400">"</span>){"\n"}
                                {"    "}<span className="text-slate-500"># Handle gracefully - switch to cheaper model, etc.</span>
                            </pre>
                        </div>
                    </div>
                ) : (
                    <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                        <div className="p-6 overflow-x-auto">
                            <pre className="font-mono text-sm leading-relaxed text-slate-300">
                                <span className="text-purple-400">import</span> {"{ observe, BudgetExceededError }"} <span className="text-purple-400">from</span> <span className="text-green-400">'llmobserve'</span>;{"\n\n"}
                                <span className="text-purple-400">try</span> {"{\n"}
                                {"  "}<span className="text-purple-400">const</span> response = <span className="text-purple-400">await</span> openai.chat.completions.<span className="text-blue-400">create</span>(...);{"\n"}
                                {"}"} <span className="text-purple-400">catch</span> (error) {"{\n"}
                                {"  "}<span className="text-purple-400">if</span> (error <span className="text-purple-400">instanceof</span> BudgetExceededError) {"{\n"}
                                {"    "}console.<span className="text-blue-400">error</span>(<span className="text-green-400">'Budget exceeded!'</span>, error.exceededCaps);{"\n"}
                                {"  "}{"}\n"}
                                {"}"}
                            </pre>
                        </div>
                    </div>
                )}
            </section>

            {/* Supported Providers & Models */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Supported Providers & Models</h2>
                
                <p className="text-gray-600">
                    We track costs for {Object.values(SUPPORTED_MODELS).reduce((acc, p) => acc + p.models.length, 0)}+ models across {Object.keys(SUPPORTED_MODELS).length} providers.
                    Click to expand and see all supported models.
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

                {/* Coming Soon */}
                <div className="mt-8 grid gap-4 md:grid-cols-2">
                    <div className="p-6 rounded-xl border border-dashed border-gray-300 bg-gray-50">
                        <div className="flex items-center gap-2 mb-3">
                            <h3 className="font-semibold text-gray-900">🎙️ Voice & Audio</h3>
                            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-medium">Coming Soon</span>
                        </div>
                        <p className="text-sm text-gray-600">
                            Deepgram, ElevenLabs, Cartesia, PlayHT, Azure Speech, AssemblyAI, and more.
                        </p>
                    </div>

                    <div className="p-6 rounded-xl border border-dashed border-gray-300 bg-gray-50">
                        <div className="flex items-center gap-2 mb-3">
                            <h3 className="font-semibold text-gray-900">🔧 Infrastructure</h3>
                            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-medium">Coming Soon</span>
                        </div>
                        <p className="text-sm text-gray-600">
                            Weaviate, Qdrant, Milvus, Chroma, MongoDB Atlas Vector, and more vector DBs.
                        </p>
                    </div>
                </div>
            </section>

            {/* Metrics Collected */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Metrics Collected</h2>
                
                <div className="p-6 rounded-xl border border-gray-200 bg-white">
                    <div className="grid md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <ul className="space-y-2">
                            <li>• <strong>Cost (USD)</strong> - calculated automatically</li>
                            <li>• <strong>Token usage</strong> - input + output</li>
                        </ul>
                        <ul className="space-y-2">
                            <li>• <strong>Latency</strong> - milliseconds</li>
                            <li>• <strong>Provider & model</strong> - auto-detected</li>
                        </ul>
                        <ul className="space-y-2">
                            <li>• <strong>Status</strong> - success/error/rate-limited</li>
                            <li>• <strong>Section labels</strong> - custom tags</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Environment Variables */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Environment Variables</h2>
                
                <p className="text-gray-600">
                    Configure the SDK via environment variables (Python only):
                </p>

                <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                    <div className="p-6 overflow-x-auto">
                        <pre className="font-mono text-sm leading-relaxed text-slate-300">
                            <span className="text-slate-500"># Required</span>{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_API_KEY</span>=llmo_sk_your_key_here{"\n\n"}
                            <span className="text-slate-500"># Optional</span>{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_TENANT_ID</span>=my-tenant{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_CUSTOMER_ID</span>=customer-123{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_STRICT_CAPS</span>=true  <span className="text-slate-500"># Block requests when cap check fails</span>
                        </pre>
                    </div>
                </div>
            </section>
        </div>
    );
}

function Card({ title, description, icon }: { title: string; description: string; icon?: React.ReactNode }) {
    return (
        <div className="p-6 rounded-xl border border-gray-200 bg-white shadow-sm">
            <div className="flex items-center gap-2 mb-2">
                {icon && <div className="text-indigo-600">{icon}</div>}
                <h3 className="font-semibold text-gray-900">{title}</h3>
            </div>
            <p className="text-sm text-gray-600">{description}</p>
        </div>
    );
}

function ApiMethod({ name, description, params, example }: { 
    name: string; 
    description: string; 
    params: Array<{ name: string; type: string; description: string; optional?: boolean }>; 
    example: string;
}) {
    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <h3 className="font-mono font-semibold text-lg text-gray-900">{name}</h3>
                <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
            <div className="p-6 space-y-4">
                {params.length > 0 && (
                    <div>
                        <h4 className="text-sm font-semibold text-gray-900 mb-2">Parameters:</h4>
                        <div className="space-y-2">
                            {params.map((param, i) => (
                                <div key={i} className="flex gap-3 text-sm flex-wrap">
                                    <code className="font-mono text-indigo-600 font-medium">{param.name}</code>
                                    <span className="text-gray-500">({param.type}{param.optional ? ", optional" : ""})</span>
                                    <span className="text-gray-600">- {param.description}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Example:</h4>
                    <div className="relative">
                        <pre className="bg-slate-950 text-slate-300 rounded-lg p-4 text-sm font-mono overflow-x-auto">
                            {example}
                        </pre>
                        <CopyButton text={example} />
                    </div>
                </div>
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
            className="absolute top-3 right-3 p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700 border border-slate-700 shadow-sm transition-all"
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
