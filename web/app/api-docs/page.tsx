"use client";

import { Terminal, Check, Copy, Bot, Zap, Server } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

export default function ApiDocsPage() {
    return (
        <div className="p-8 max-w-5xl mx-auto space-y-12">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900 mb-4">API Documentation</h1>
                <p className="text-lg text-gray-600">
                    Zero-config cost tracking for OpenAI, Anthropic, Google, and 40+ LLM providers.
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
                            {"    "}collector_url=<span className="text-green-400">"https://llmobserve-production.up.railway.app"</span>,{"\n"}
                            {"    "}api_key=<span className="text-green-400">"your-api-key-here"</span> <span className="text-slate-500"># Get from settings</span>{"\n"}
                            {")"}
                        </pre>
                    </div>
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">Installation</h2>
                <div className="bg-slate-100 rounded-lg p-4 font-mono text-sm text-slate-800 border border-slate-200 flex items-center justify-between">
                    <span>pip install llmobserve</span>
                    <CopyButton text="pip install llmobserve" />
                </div>
            </section>

            <section className="space-y-6">
                <h2 className="text-2xl font-semibold text-gray-900">How It Works</h2>
                <div className="grid gap-6 md:grid-cols-3">
                    <Card
                        title="Zero-Config Tracking"
                        description="We patch Python HTTP clients to inject tracking headers. No SDK-specific code. Works with ANY API."
                    />
                    <Card
                        title="Optional Labeling"
                        description="Add labels to see which agents/tools cost the most using @agent decorators."
                    />
                    <Card
                        title="AI Auto-Instrumentation"
                        description="Let AI add labels for you with a single command: llmobserve instrument --auto-apply"
                    />
                </div>
            </section>
            {/* AI CLI Section */}
            <section className="mb-12">
                <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                    <Terminal className="h-6 w-6 text-indigo-600" />
                    AI Auto-Instrumentation & Review
                </h2>
                <p className="text-gray-600 mb-6">
                    The <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">llmobserve</code> CLI intelligently scans your codebase to detect <strong>hierarchical structures</strong> of agents, tools, and workflows. It proposes changes that you can interactively review before applying.
                </p>

                <div className="grid gap-6 md:grid-cols-3 mb-8">
                    <Card
                        title="1. Scan & Detect"
                        description="Analyzes ASTs to find agents, tools, and LLM calls. Builds a dependency graph to understand your app's hierarchy."
                        code="llmobserve scan ."
                    />
                    <Card
                        title="2. Interactive Review"
                        description="Step through every suggested change. Approve, reject, or modify labels for agents and steps."
                        code="llmobserve review"
                    />
                    <Card
                        title="3. Safe Apply"
                        description="Apply changes with automatic backups. If syntax validation fails, it auto-rolls back."
                        code="llmobserve apply"
                    />
                </div>

                <div className="bg-slate-950 rounded-xl p-6 text-slate-300 font-mono text-sm overflow-x-auto shadow-2xl border border-slate-800">
                    <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-4">
                        <span className="text-slate-400">Interactive Review Session</span>
                        <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-500/20" />
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
                            <div className="w-3 h-3 rounded-full bg-green-500/20" />
                        </div>
                    </div>
                    <div className="space-y-4">
                        <div>
                            <div className="flex gap-2">
                                <span className="text-green-400">$</span>
                                <span>llmobserve review</span>
                            </div>
                            <div className="text-slate-500 mt-1">📋 Reviewing suggested changes...</div>
                        </div>

                        <div className="pl-4 border-l-2 border-slate-800">
                            <div className="text-indigo-400 font-bold">[1/12] research_agent.py</div>
                            <div className="text-slate-400 mt-1">
                                Claude: "Identified main agent loop. Suggesting <span className="text-yellow-400">@agent('researcher')</span> label."
                            </div>

                            <div className="mt-3 bg-slate-900 p-3 rounded border border-slate-800">
                                <div className="text-red-400">- def run_research(query):</div>
                                <div className="text-green-400">+ @agent("researcher")</div>
                                <div className="text-green-400">+ def run_research(query):</div>
                            </div>

                            <div className="mt-2 text-white">
                                Apply this change? [y/n/view/skip]: <span className="animate-pulse">_</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Manual Labeling Section */}
            <section className="mb-12">
                <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                    <Check className="h-6 w-6 text-indigo-600" />
                    Manual Labeling
                </h2>
                <p className="text-gray-600 mb-6">
                    For fine-grained control, use the <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">@trace</code> decorator or <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">section</code> context manager.
                </p>

                <div className="grid gap-8 md:grid-cols-2">
                    <div className="space-y-4">
                        <h3 className="font-medium text-gray-900">Using Decorators</h3>
                        <div className="relative group">
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl opacity-20 blur group-hover:opacity-30 transition duration-200"></div>
                            <div className="relative bg-white rounded-xl border border-gray-200 p-4">
                                <pre className="text-sm font-mono text-gray-800 overflow-x-auto">
                                    {`from llmobserve import trace

@trace(agent="researcher")
def run_research(query):
    # ...

@trace(tool="web_search")
def search(query):
    # ...`}
                                </pre>
                                <CopyButton text={`from llmobserve import trace

@trace(agent="researcher")
def run_research(query):
    # ...

@trace(tool="web_search")
def search(query):
    # ...`} />
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="font-medium text-gray-900">Using Context Managers</h3>
                        <div className="relative group">
                            <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl opacity-20 blur group-hover:opacity-30 transition duration-200"></div>
                            <div className="relative bg-white rounded-xl border border-gray-200 p-4">
                                <pre className="text-sm font-mono text-gray-800 overflow-x-auto">
                                    {`from llmobserve import section

with section("agent:writer"):
    # ...
    
    with section("step:draft"):
        # ...`}
                                </pre>
                                <CopyButton text={`from llmobserve import section

with section("agent:writer"):
    # ...
    
    with section("step:draft"):
        # ...`} />
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

function Card({ title, description, code }: { title: string; description: string; code?: string }) {
    return (
        <div className="p-6 rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
            <p className="text-sm text-gray-600 mb-4">{description}</p>
            {code && (
                <div className="bg-gray-50 rounded-lg p-2 font-mono text-xs text-gray-800 border border-gray-100">
                    {code}
                </div>
            )}
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
