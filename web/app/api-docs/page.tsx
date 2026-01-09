"use client";

import { Terminal, Check, Copy, Code2, Layers, Settings, AlertTriangle, Shield, Users, Bell, Zap } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function ApiDocsPage() {
    const [activeTab, setActiveTab] = useState<"python" | "node">("python");

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
                        description="We patch HTTP clients (httpx, requests, aiohttp, fetch) to inject tracking headers. Works with ANY HTTP-based API."
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
                                <span className="text-slate-500"># Step 1: Initialize llmobserve (add at the top of your main file)</span>{"\n"}
                                <span className="text-purple-400">import</span> llmobserve{"\n"}
                                <span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> section, set_customer_id{"\n\n"}
                                llmobserve.<span className="text-blue-400">observe</span>(api_key=<span className="text-green-400">"llmo_sk_your_key_here"</span>)
                                {"\n\n"}
                                <span className="text-slate-500"># Step 2: Use your LLM libraries normally - tracked automatically!</span>{"\n"}
                                <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI{"\n\n"}
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
                                <span className="text-slate-500">// Step 1: Initialize llmobserve (add at the top of your main file)</span>{"\n"}
                                <span className="text-purple-400">import</span> {"{ observe, section, setCustomerId }"} <span className="text-purple-400">from</span> <span className="text-green-400">'llmobserve'</span>;{"\n"}
                                <span className="text-purple-400">import</span> OpenAI <span className="text-purple-400">from</span> <span className="text-green-400">'openai'</span>;{"\n\n"}
                                <span className="text-blue-400">observe</span>({"{\n"}
                                {"  "}collectorUrl: <span className="text-green-400">'https://llmobserve-api-production-d791.up.railway.app'</span>,{"\n"}
                                {"  "}apiKey: <span className="text-green-400">'llmo_sk_your_key_here'</span>{"\n"}
                                {"}"});
                                {"\n\n"}
                                <span className="text-slate-500">// Step 2: Use your LLM libraries normally - tracked automatically!</span>{"\n"}
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
                                    { name: "collector_url", type: "str", optional: true, description: "Collector URL (defaults to production)" },
                                    { name: "tenant_id", type: "str", optional: true, description: "Tenant ID for multi-tenant apps" },
                                    { name: "customer_id", type: "str", optional: true, description: "Default customer ID" },
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
                        </>
                    ) : (
                        <>
                            <ApiMethod
                                name="observe()"
                                description="Initialize LLMObserve tracking. Call this once at the start of your application."
                                params={[
                                    { name: "collectorUrl", type: "string", description: "URL of the collector server" },
                                    { name: "apiKey", type: "string", description: "Your API key from /settings" },
                                    { name: "tenantId", type: "string", optional: true, description: "Tenant ID for multi-tenant apps" },
                                    { name: "customerId", type: "string", optional: true, description: "Default customer ID" },
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
});

// Now you can see "email_summarizer" costs in your Features tab!`}
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

            {/* Spending Caps & Alerts - NEW SECTION */}
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
                        <ul className="text-sm text-gray-600 space-y-1">
                            <li>• Early warning at 80%</li>
                            <li>• Urgent alert at 95%</li>
                            <li>• Cap reached at 100%</li>
                        </ul>
                    </div>

                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <div className="flex items-center gap-2 mb-3">
                            <AlertTriangle className="h-5 w-5 text-red-600" />
                            <h3 className="font-semibold text-gray-900">Hard Caps (Blocking)</h3>
                        </div>
                        <p className="text-sm text-gray-600 mb-3">
                            Block API calls when caps are exceeded. The SDK throws a{" "}
                            <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">BudgetExceededError</code>{" "}
                            before the request is made.
                        </p>
                        <ul className="text-sm text-gray-600 space-y-1">
                            <li>• Prevents overspending</li>
                            <li>• Checked before each API call</li>
                            <li>• Handle gracefully in code</li>
                        </ul>
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
                        <p className="text-xs text-gray-600">Limit spending per provider (OpenAI, Anthropic)</p>
                    </div>
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Model</h4>
                        <p className="text-xs text-gray-600">Limit spending per model (gpt-4o, claude-3)</p>
                    </div>
                    <div className="p-4 rounded-lg border border-gray-200 bg-white">
                        <h4 className="font-medium text-gray-900 mb-1">Customer</h4>
                        <p className="text-xs text-gray-600">Limit spending per customer (for SaaS)</p>
                    </div>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mt-8">Handling Hard Caps in Code</h3>

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
                                <span className="text-purple-400">from</span> llmobserve <span className="text-purple-400">import</span> observe, BudgetExceededError{"\n"}
                                <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI{"\n\n"}
                                observe(api_key=<span className="text-green-400">"llmo_sk_..."</span>){"\n"}
                                client = OpenAI(){"\n\n"}
                                <span className="text-purple-400">try</span>:{"\n"}
                                {"    "}response = client.chat.completions.<span className="text-blue-400">create</span>({"(\n"}
                                {"        "}model=<span className="text-green-400">"gpt-4o"</span>,{"\n"}
                                {"        "}messages=[{"{\"role\": \"user\", \"content\": \"Hello\"}"}]{"\n"}
                                {"    "}){"\n"}
                                <span className="text-purple-400">except</span> BudgetExceededError <span className="text-purple-400">as</span> e:{"\n"}
                                {"    "}<span className="text-slate-500"># Handle cap exceeded - request was blocked!</span>{"\n"}
                                {"    "}<span className="text-blue-400">print</span>(<span className="text-green-400">f"Spending cap exceeded: </span>{"{e}"}<span className="text-green-400">"</span>){"\n"}
                                {"    "}<span className="text-purple-400">for</span> cap <span className="text-purple-400">in</span> e.exceeded_caps:{"\n"}
                                {"        "}<span className="text-blue-400">print</span>(<span className="text-green-400">f"  - </span>{"{cap['cap_type']}"}<span className="text-green-400">: $</span>{"{cap['current']:.2f}"}<span className="text-green-400">/$</span>{"{cap['limit']:.2f}"}<span className="text-green-400">"</span>){"\n"}
                                {"    "}{"\n"}
                                {"    "}<span className="text-slate-500"># Optional: Fall back to a cheaper model</span>{"\n"}
                                {"    "}response = client.chat.completions.<span className="text-blue-400">create</span>({"(\n"}
                                {"        "}model=<span className="text-green-400">"gpt-4o-mini"</span>,  <span className="text-slate-500"># Cheaper alternative</span>{"\n"}
                                {"        "}messages=[{"{\"role\": \"user\", \"content\": \"Hello\"}"}]{"\n"}
                                {"    "})
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
                                <span className="text-purple-400">import</span> {"{ observe, BudgetExceededError }"} <span className="text-purple-400">from</span> <span className="text-green-400">'llmobserve'</span>;{"\n"}
                                <span className="text-purple-400">import</span> OpenAI <span className="text-purple-400">from</span> <span className="text-green-400">'openai'</span>;{"\n\n"}
                                <span className="text-blue-400">observe</span>({"{\n"}
                                {"  "}collectorUrl: <span className="text-green-400">'https://llmobserve-api-production-d791.up.railway.app'</span>,{"\n"}
                                {"  "}apiKey: <span className="text-green-400">'llmo_sk_...'</span>,{"\n"}
                                {"  "}enableCaps: <span className="text-yellow-400">true</span>  <span className="text-slate-500">// Default: true</span>{"\n"}
                                {"}"});{"\n\n"}
                                <span className="text-purple-400">const</span> openai = <span className="text-purple-400">new</span> OpenAI();{"\n\n"}
                                <span className="text-purple-400">try</span> {"{\n"}
                                {"  "}<span className="text-purple-400">const</span> response = <span className="text-purple-400">await</span> openai.chat.completions.<span className="text-blue-400">create</span>({"{\n"}
                                {"    "}model: <span className="text-green-400">'gpt-4o'</span>,{"\n"}
                                {"    "}messages: [{"{ "}role: <span className="text-green-400">'user'</span>, content: <span className="text-green-400">'Hello'</span> {"}"}]{"\n"}
                                {"  "}{"}"});{"\n"}
                                {"}"} <span className="text-purple-400">catch</span> (error) {"{\n"}
                                {"  "}<span className="text-purple-400">if</span> (error <span className="text-purple-400">instanceof</span> BudgetExceededError) {"{\n"}
                                {"    "}<span className="text-slate-500">// Handle cap exceeded - request was blocked!</span>{"\n"}
                                {"    "}console.<span className="text-blue-400">error</span>(<span className="text-green-400">'Budget exceeded!'</span>, error.exceededCaps);{"\n"}
                                {"    "}<span className="text-purple-400">for</span> (<span className="text-purple-400">const</span> cap <span className="text-purple-400">of</span> error.exceededCaps) {"{\n"}
                                {"      "}console.<span className="text-blue-400">log</span>(<span className="text-green-400">`  - ${"${cap.cap_type}"}: $${"${cap.current.toFixed(2)}"}/$$${"${cap.limit.toFixed(2)}"}`</span>);{"\n"}
                                {"    "}{"}\n"}
                                {"  "}{"}\n"}
                                {"  "}<span className="text-purple-400">throw</span> error;{"\n"}
                                {"}"}
                            </pre>
                        </div>
                    </div>
                )}

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                        <strong>💡 Tip:</strong> Hard caps check spending before each API call. If the backend is unreachable, 
                        the SDK "fails open" by default (allows the request). Set <code className="bg-blue-100 px-1 py-0.5 rounded">LLMOBSERVE_STRICT_CAPS=true</code> to 
                        block requests when cap checks fail.
                    </p>
                </div>
            </section>

            {/* Advanced Features */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Advanced Features</h2>
                
                <div className="grid gap-6 md:grid-cols-2">
                    <FeatureCard
                        title="Multi-Tenant Tracking"
                        description="Track costs per customer for SaaS applications"
                        example={activeTab === "python" 
                            ? `from llmobserve import set_customer_id

# In your request handler
set_customer_id(request.user.id)

# All API calls now tagged with customer ID
response = client.chat.completions.create(...)`
                            : `import { setCustomerId } from 'llmobserve';

// In your request handler
setCustomerId(request.user.id);

// All API calls now tagged with customer ID
const response = await openai.chat.completions.create(...);`}
                    />

                    <FeatureCard
                        title="Tag Features"
                        description="Tag LLM calls by feature to see cost breakdown"
                        example={activeTab === "python"
                            ? `with section("feature:email_processing"):
    # All LLM calls here tagged as email_processing
    response = summarize(email)
    
with section("feature:chat_bot"):
    # This one tagged as chat_bot
    response = chat(query)`
                            : `await section('feature:email_processing').run(async () => {
  // All LLM calls here tagged as email_processing
  const response = await summarize(email);
});

await section('feature:chat_bot').run(async () => {
  // This one tagged as chat_bot
  const response = await chat(query);
});`}
                    />

                    <FeatureCard
                        title="Context Export/Import"
                        description="Pass tracking context to background workers"
                        example={activeTab === "python"
                            ? `from llmobserve import export_context, import_context

# In main process
context = export_context()
task.delay(context)

# In worker
import_context(context)
# Tracking continues seamlessly`
                            : `// Context is automatically maintained
// across async operations in Node.js

await section('background_task').run(async () => {
  // All calls in this async context are tracked
  await processInBackground();
});`}
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
                <h2 className="text-2xl font-semibold text-gray-900">Supported Providers</h2>
                
                <div className="grid gap-4 md:grid-cols-3">
                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <h3 className="font-semibold text-gray-900 mb-4">🤖 LLM Providers</h3>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li>• OpenAI (GPT-4o, GPT-4, GPT-3.5)</li>
                            <li>• Anthropic (Claude 3.5, Claude 3)</li>
                            <li>• Google (Gemini Pro, Flash)</li>
                            <li>• Cohere (Command, Embed)</li>
                            <li>• Together AI, Groq, Mistral</li>
                            <li>• Perplexity, Hugging Face</li>
                        </ul>
                    </div>

                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <h3 className="font-semibold text-gray-900 mb-4">🎙️ Voice & Audio</h3>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li>• Deepgram (STT)</li>
                            <li>• ElevenLabs (TTS)</li>
                            <li>• Cartesia (TTS)</li>
                            <li>• PlayHT (TTS)</li>
                            <li>• OpenAI Whisper (STT)</li>
                            <li>• Azure Speech</li>
                        </ul>
                    </div>

                    <div className="p-6 rounded-xl border border-gray-200 bg-white">
                        <h3 className="font-semibold text-gray-900 mb-4">🔧 Infrastructure</h3>
                        <ul className="space-y-2 text-sm text-gray-600">
                            <li>• Pinecone (Vector DB)</li>
                            <li>• Voyage AI (Embeddings)</li>
                            <li>• Vapi, Retell (Voice AI)</li>
                            <li>• Twilio, Telnyx, Vonage</li>
                            <li>• LiveKit, Bland AI</li>
                            <li>• And 40+ more!</li>
                        </ul>
                    </div>
                </div>

                <div className="p-6 rounded-xl border border-gray-200 bg-white">
                    <h3 className="font-semibold text-gray-900 mb-4">📊 Metrics Collected</h3>
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
                            <li>• <strong>Custom labels</strong> - sections & agents</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Environment Variables */}
            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Environment Variables</h2>
                
                <p className="text-gray-600">
                    You can configure the SDK via environment variables instead of code:
                </p>

                <div className="bg-slate-950 rounded-xl overflow-hidden border border-slate-800">
                    <div className="p-6 overflow-x-auto">
                        <pre className="font-mono text-sm leading-relaxed text-slate-300">
                            <span className="text-slate-500"># Required</span>{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_API_KEY</span>=llmo_sk_your_key_here{"\n\n"}
                            <span className="text-slate-500"># Optional</span>{"\n"}
                            <span className="text-blue-400">LLMOBSERVE_COLLECTOR_URL</span>=https://llmobserve-api-production-d791.up.railway.app{"\n"}
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
