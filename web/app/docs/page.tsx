"use client";

import { useState } from "react";
// Docs page for LLM Observe cost tracking
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  BookOpen, 
  Code, 
  Key, 
  Settings, 
  DollarSign, 
  Users, 
  Shield, 
  Zap,
  ChevronRight,
  Copy,
  Check,
  Terminal,
  FileCode,
  BarChart3
} from "lucide-react";

export default function DocsPage() {
  const router = useRouter();
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const CodeBlock = ({ code, language = "python", id }: { code: string; language?: string; id: string }) => (
    <div className="relative bg-gray-900 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400 uppercase">{language}</span>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => copyToClipboard(code, id)}
          className="text-gray-400 hover:text-white h-6 px-2"
        >
          {copied === id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
        </Button>
      </div>
      <pre className="text-sm font-mono text-gray-100 overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">LLM Observe</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/sign-in" className="text-gray-600 hover:text-gray-900 text-sm font-medium">
                Login
              </Link>
              <Button
                onClick={() => router.push("/sign-up")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Sign up for free
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">Documentation</h1>
          <p className="text-xl text-gray-600">
            Everything you need to start tracking LLM costs in minutes
          </p>
        </div>

        {/* Quick Start */}
        <section className="mb-16">
          <Card className="border-2 border-indigo-200 bg-indigo-50">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Zap className="w-6 h-6 text-indigo-600" />
                <CardTitle className="text-2xl">Quick Start</CardTitle>
              </div>
              <CardDescription className="text-base">
                Get started in 3 steps - takes less than 2 minutes
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                    <h3 className="font-semibold">Sign Up</h3>
                  </div>
                  <p className="text-sm text-gray-600">Create a free account and get your API key</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                    <h3 className="font-semibold">Install SDK</h3>
                  </div>
                  <p className="text-sm text-gray-600">Install the Python package with pip</p>
                </div>
                <div className="bg-white rounded-lg p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                    <h3 className="font-semibold">Add Code</h3>
                  </div>
                  <p className="text-sm text-gray-600">Add 2 lines to start tracking</p>
                </div>
              </div>
              <Button onClick={() => router.push("/sign-up")} className="w-full" size="lg">
                Get Started Now
              </Button>
            </CardContent>
          </Card>
        </section>

        {/* Installation */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Terminal className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Installation</h2>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Install the Python SDK</CardTitle>
              <CardDescription>Use pip to install llmobserve</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock 
                code="pip install llmobserve" 
                language="bash"
                id="install"
              />
            </CardContent>
          </Card>
        </section>

        {/* Getting Started */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Code className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Getting Started</h2>
          </div>
          
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Basic Setup</CardTitle>
              <CardDescription>Add cost tracking to your OpenAI code</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock 
                code={`from llmobserve import observe
from openai import OpenAI
import os

# Initialize LLM Observe
observe(
    collector_url="${process.env.NEXT_PUBLIC_COLLECTOR_URL || "https://api.llmobserve.com"}",
    api_key=os.getenv("LLMOBSERVE_API_KEY")
)

# Use OpenAI as normal - all calls are tracked automatically!
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)`}
                id="basic"
              />
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>💡 Tip:</strong> Store your API key in environment variables. Never commit it to version control!
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Environment Variables</CardTitle>
              <CardDescription>Recommended way to store your API key</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock 
                code={`# .env file
LLMOBSERVE_API_KEY=llmo_your_api_key_here

# Load in Python
from dotenv import load_dotenv
load_dotenv()

import os
api_key = os.getenv("LLMOBSERVE_API_KEY")`}
                id="env"
              />
            </CardContent>
          </Card>
        </section>

        {/* Features */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Zap className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Features</h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Automatic Cost Tracking</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Every LLM API call is automatically tracked with accurate cost calculation. 
                  See costs for OpenAI, Anthropic, Google, and 40+ providers.
                </p>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>Real-time cost calculation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>Token usage tracking</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span>Latency monitoring</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Customer Cost Tracking</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Perfect for SaaS founders. Track costs per customer to understand profitability.
                </p>
                <CodeBlock 
                  code={`# Track costs by customer
observe(
    collector_url="...",
    api_key="...",
    customer_id="customer_123"  # Add customer ID
)`}
                  id="customer"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Spending Caps</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Set budget limits with email alerts. Never go over budget again.
                </p>
                <p className="text-sm text-gray-600">
                  Configure spending caps in your dashboard Settings page. Get notified when you're approaching your limit.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Dashboard Analytics</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  View comprehensive analytics in your dashboard:
                </p>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <span>Cost breakdown by provider</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <span>Costs by customer</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <span>Agent and workflow costs</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-indigo-600 mt-0.5 flex-shrink-0" />
                    <span>Historical trends</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Supported Providers */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <FileCode className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Supported Providers</h2>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="grid md:grid-cols-3 gap-4">
                {[
                  "OpenAI", "Anthropic", "Google", "Cohere", "Mistral", "Perplexity",
                  "Pinecone", "Weaviate", "Qdrant", "Chroma", "Supabase", "Stripe"
                ].map((provider) => (
                  <Badge key={provider} variant="outline" className="p-2 text-center">
                    {provider}
                  </Badge>
                ))}
              </div>
              <p className="mt-4 text-sm text-gray-600 text-center">
                And 30+ more providers. See full list in your dashboard.
              </p>
            </CardContent>
          </Card>
        </section>

        {/* API Reference */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Key className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">API Reference</h2>
          </div>

          <Card className="mb-6">
            <CardHeader>
              <CardTitle>observe() Function</CardTitle>
              <CardDescription>Main initialization function</CardDescription>
            </CardHeader>
            <CardContent>
              <CodeBlock 
                code={`observe(
    collector_url: str,  # Your collector API URL
    api_key: str,        # Your API key from dashboard
    customer_id: str = None,  # Optional: Customer ID for tracking
    tenant_id: str = None,   # Optional: Tenant ID for multi-tenancy
)`}
                id="api"
              />
              <div className="mt-4 space-y-2">
                <div className="flex items-start gap-2">
                  <Badge variant="outline" className="mt-1">Required</Badge>
                  <div>
                    <p className="font-semibold">collector_url</p>
                    <p className="text-sm text-gray-600">Your collector API endpoint URL</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Badge variant="outline" className="mt-1">Required</Badge>
                  <div>
                    <p className="font-semibold">api_key</p>
                    <p className="text-sm text-gray-600">Your API key from the Settings page</p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Badge variant="outline" className="mt-1">Optional</Badge>
                  <div>
                    <p className="font-semibold">customer_id</p>
                    <p className="text-sm text-gray-600">Track costs per customer (for SaaS founders)</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Common Use Cases */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <BookOpen className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Common Use Cases</h2>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Track Costs for Individual Projects</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Simple setup for personal projects
observe(
    collector_url="https://api.llmobserve.com",
    api_key=os.getenv("LLMOBSERVE_API_KEY")
)`}
                  id="use-case-1"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Track Costs Per Customer (SaaS)</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Track costs per customer in your SaaS
def handle_customer_request(customer_id: str, user_query: str):
    observe(
        collector_url="https://api.llmobserve.com",
        api_key=os.getenv("LLMOBSERVE_API_KEY"),
        customer_id=customer_id  # Track costs per customer
    )
    
    # Your LLM calls here
    response = client.chat.completions.create(...)
    return response`}
                  id="use-case-2"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Multi-Tenant Applications</CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Track costs per tenant
observe(
    collector_url="https://api.llmobserve.com",
    api_key=os.getenv("LLMOBSERVE_API_KEY"),
    tenant_id=tenant_id,      # Track per tenant
    customer_id=customer_id    # Track per customer within tenant
)`}
                  id="use-case-3"
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Troubleshooting */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <Settings className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Troubleshooting</h2>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>No data showing in dashboard?</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">1.</span>
                    <span>Verify your API key is correct in your code</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">2.</span>
                    <span>Make sure you've made at least one LLM API call after adding observe()</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">3.</span>
                    <span>Check that collector_url points to the correct endpoint</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">4.</span>
                    <span>Wait a few seconds - data may take 10-30 seconds to appear</span>
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>API key not working?</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">1.</span>
                    <span>Go to Settings page and verify your API key</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">2.</span>
                    <span>Generate a new API key if needed</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-indigo-600 font-bold">3.</span>
                    <span>Make sure you're using the full key, not just the prefix</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center py-12 bg-indigo-50 rounded-xl">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to start tracking?</h2>
          <p className="text-lg text-gray-600 mb-6">
            Get started in less than 2 minutes
          </p>
          <Button onClick={() => router.push("/sign-up")} size="lg" className="bg-indigo-600 hover:bg-indigo-700">
            Sign Up for Free
          </Button>
        </section>
      </div>
    </div>
  );
}

