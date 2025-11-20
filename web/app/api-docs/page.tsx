"use client";

import { Check, Copy, Terminal } from "lucide-react";
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
        </div>
    );
}

function Card({ title, description }: { title: string; description: string }) {
    return (
        <div className="p-6 rounded-xl border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
            <p className="text-sm text-gray-600 leading-relaxed">{description}</p>
        </div>
    );
}

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <button
            onClick={handleCopy}
            className="p-2 hover:bg-slate-200 rounded-md transition-colors text-slate-500 hover:text-slate-700"
        >
            {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
        </button>
    );
}
