"use client";

import { Terminal, Check, Copy, Code2, Layers, Settings } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function ApiDocsPage() {
    return (
        <div className="p-8 max-w-5xl mx-auto space-y-12">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">API Documentation</h1>
                <p className="text-lg text-gray-600">
                    Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers. Just 2 lines of code.
                </p>
            </div>

            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
                        <Terminal className="h-5 w-5" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900">Quick Start</h2>
                </div>

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
                            {"    "}collector_url=<span className="text-green-400">"http://localhost:8000"</span>,{"\n"}
                            {"    "}api_key=<span className="text-green-400">"your-api-key-here"</span> <span className="text-slate-500"># Get from /settings</span>{"\n"}
                            {")"}
                            {"\n\n"}
                            <span className="text-slate-500"># That's it! All LLM calls are now tracked automatically.</span>
                        </pre>
                    </div>
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Installation</h2>
                <div className="space-y-4">
                    <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm text-slate-800 border border-slate-200 flex items-center justify-between">
                        <span>pip install llmobserve</span>
                        <CopyButton text="pip install llmobserve" />
                    </div>
                    <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm text-slate-800 border border-slate-200 flex items-center justify-between">
                        <span>npm install llmobserve</span>
                        <CopyButton text="npm install llmobserve" />
                    </div>
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">How It Works</h2>
                <div className="grid gap-6 md:grid-cols-3">
                    <Card
                        icon={<Layers className="h-5 w-5" />}
                        title="Zero-Config Tracking"
                        description="We patch Python HTTP clients (httpx, requests, aiohttp) to inject tracking headers. Works with ANY HTTP-based API."
                    />
                    <Card
                        icon={<Code2 className="h-5 w-5" />}
                        title="Optional Labeling"
                        description="Use section() context managers or @trace decorators to organize costs by feature, agent, or customer."
                    />
                    <Card
                        icon={<Settings className="h-5 w-5" />}
                        title="Multi-Language Support"
                        description="Available for Python and Node.js/TypeScript. Same API, same dashboard, same powerful tracking."
                    />
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Complete Example</h2>
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
                            <span className="text-slate-500"># Step 1: Initialize llmobserve (add at the top of your main file)</span>{"\n"}
                            <span className="text-purple-400">import</span> llmobserve{"\n\n"}
                            llmobserve.<span className="text-blue-400">observe</span>({"(\n"}
                            {"    "}collector_url=<span className="text-green-400">"http://localhost:8000"</span>,{"\n"}
                            {"    "}api_key=<span className="text-green-400">"llmo_sk_your_key_here"</span>{"\n"}
                            {")"}
                            {"\n\n"}
                            <span className="text-slate-500"># Step 2: Use your LLM libraries normally - tracked automatically!</span>{"\n"}
                            <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI{"\n\n"}
                            client = OpenAI(api_key=<span className="text-green-400">"your-openai-key"</span>){"\n\n"}
                            <span className="text-slate-500"># This call is automatically tracked - no changes needed!</span>{"\n"}
                            response = client.chat.completions.<span className="text-blue-400">create</span>({"(\n"}
                            {"    "}model=<span className="text-green-400">"gpt-4o-mini"</span>,{"\n"}
                            {"    "}messages=[{"{"}{"\"role\": \"user\", \"content\": \"Hello!\""}{"}"}]{"\n"}
                            {")"}
                            {"\n\n"}
                            <span className="text-blue-400">print</span>(response.choices[<span className="text-yellow-400">0</span>].message.content)
                        </pre>
                    </div>
                </div>
            </section>

            {/* Core API Reference */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Core API Reference</h2>
                
                <div className="space-y-8">
                    <ApiMethod
                        name="observe()"
                        description="Initialize LLMObserve tracking. Call this once at the start of your application."
                        params={[
                            { name: "collector_url", type: "str", description: "URL of the collector API (e.g., http://localhost:8000)" },
                            { name: "api_key", type: "str", description: "Your API key from /settings" },
                        ]}
                        example={`import llmobserve

llmobserve.observe(
    collector_url="http://localhost:8000",
    api_key="llmo_sk_your_key_here"
)`}
                    />

                    <ApiMethod
                        name="section()"
                        description="Context manager to organize costs by feature, agent, or workflow section."
                        params={[
                            { name: "name", type: "str", description: "Name of the section (e.g., 'user_query', 'agent:researcher')" },
                        ]}
                        example={`from llmobserve import section

with section("user_query"):
    response = client.chat.completions.create(...)
    
with section("agent:researcher"):
    with section("tool:web_search"):
        # Nested sections work too!
        search_results = search_api(...)`}
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

                    <ApiMethod
                        name="set_run_id()"
                        description="Group related API calls into a single execution run."
                        params={[
                            { name: "run_id", type: "str", description: "Unique identifier for this run (e.g., UUID)" },
                        ]}
                        example={`from llmobserve import set_run_id
import uuid

set_run_id(str(uuid.uuid4()))
# All API calls in this execution are grouped together`}
                    />

                    <ApiMethod
                        name="@trace()"
                        description="Decorator to automatically track function calls with custom labels."
                        params={[
                            { name: "agent", type: "str", optional: true, description: "Label this function as an agent" },
                            { name: "tool", type: "str", optional: true, description: "Label this function as a tool" },
                            { name: "step", type: "str", optional: true, description: "Label this function as a step" },
                        ]}
                        example={`from llmobserve import trace

@trace(agent="researcher")
def run_research(query):
    return client.chat.completions.create(...)

@trace(tool="web_search")
def search_web(query):
    return search_api.query(query)`}
                    />
                </div>
            </section>

            {/* Advanced Features */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Advanced Features</h2>
                
                <div className="grid gap-6 md:grid-cols-2">
                    <FeatureCard
                        title="Multi-Tenant Tracking"
                        description="Track costs per customer for SaaS applications"
                        example={`from llmobserve import set_customer_id

# In your request handler
set_customer_id(request.user.id)

# All API calls now tagged with customer ID
response = client.chat.completions.create(...)`}
                    />

                    <FeatureCard
                        title="Hierarchical Sections"
                        description="Nest sections to track complex workflows"
                        example={`with section("agent:researcher"):
    with section("tool:web_search"):
        results = search(...)
    
    with section("tool:summarize"):
        summary = summarize(results)`}
                    />

                    <FeatureCard
                        title="Context Export/Import"
                        description="Pass tracking context to background workers"
                        example={`from llmobserve import export_context, import_context

# In main process
context = export_context()
task.delay(context)

# In worker
import_context(context)
# Tracking continues seamlessly`}
                    />

                    <FeatureCard
                        title="Framework Integration"
                        description="Works with all major AI frameworks"
                        example={`# Works automatically with:
# - LangChain
# - CrewAI  
# - AutoGen
# - LlamaIndex
# - Any HTTP-based API`}
                    />
                </div>
            </section>

            {/* What Gets Tracked */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">What Gets Tracked</h2>
                
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <h3 className="font-semibold text-gray-900 mb-4">✅ Supported Providers</h3>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li>• OpenAI (GPT-4, GPT-4o, GPT-3.5, etc.)</li>
                            <li>• Anthropic (Claude)</li>
                            <li>• Google (Gemini)</li>
                            <li>• Cohere, Together AI, Groq</li>
                            <li>• Mistral, Perplexity, Hugging Face</li>
                            <li>• And 40+ more providers!</li>
                        </ul>
                    </div>

                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <h3 className="font-semibold text-gray-900 mb-4">📊 Metrics Collected</h3>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li>• Cost (USD) - calculated automatically</li>
                            <li>• Token usage (input + output)</li>
                            <li>• Latency (milliseconds)</li>
                            <li>• Provider & model name</li>
                            <li>• Status (success/error/rate-limited)</li>
                            <li>• Custom labels & sections</li>
                        </ul>
                    </div>
                </div>
            </section>
        </div>
    );
}

function Card({ title, description, code, icon }: { title: string; description: string; code?: string; icon?: React.ReactNode }) {
    return (
        <div className="p-6 rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-2">
                {icon && <div className="text-indigo-600">{icon}</div>}
                <h3 className="font-semibold text-gray-900">{title}</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">{description}</p>
            {code && (
                <div className="bg-gray-50 rounded-lg p-2 font-mono text-xs text-gray-800 border border-gray-100">
                    {code}
                </div>
            )}
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
                <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Parameters:</h4>
                    <div className="space-y-2">
                        {params.map((param, i) => (
                            <div key={i} className="flex gap-3 text-sm">
                                <code className="font-mono text-indigo-600 font-medium">{param.name}</code>
                                <span className="text-gray-500">({param.type}{param.optional ? ", optional" : ""})</span>
                                <span className="text-gray-600">- {param.description}</span>
                            </div>
                        ))}
                    </div>
                </div>
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

function FeatureCard({ title, description, example }: { title: string; description: string; example: string }) {
    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
            <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">{title}</h3>
                <p className="text-sm text-gray-600 mt-1">{description}</p>
            </div>
            <div className="p-4">
                <pre className="bg-slate-950 text-slate-300 rounded-lg p-4 text-xs font-mono overflow-x-auto">
                    {example}
                </pre>
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
            className="absolute top-3 right-3 p-2 rounded-lg bg-white/80 hover:bg-white border border-gray-200 shadow-sm transition-all"
            title="Copy to clipboard"
        >
            {copied ? (
                <Check className="h-4 w-4 text-green-500" />
            ) : (
                <Copy className="h-4 w-4 text-gray-500" />
            )}
        </button>
    );
}
