"use client";

import { useState } from "react";
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
  BarChart3,
  HelpCircle
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
                Get Started - $8/month
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
                  <p className="text-sm text-gray-600">Create an account and get your API key ($8/month)</p>
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

        {/* Labeling Costs Section */}
        <section id="labeling" className="mb-16 scroll-mt-20">
          <div className="flex items-center gap-3 mb-6">
            <FileCode className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Labeling Your Costs</h2>
          </div>
          
          <Card className="mb-6 border-2 border-amber-200 bg-amber-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Why Label Costs?</h3>
                  <p className="text-gray-700">
                    LLMObserve automatically tracks <strong>all</strong> your LLM API calls - nothing is hidden. 
                    However, unlabeled costs appear as &quot;Untracked&quot; in your dashboard. By adding labels, 
                    you can organize costs by agent, tool, or workflow to understand exactly where your money is going.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Method 1: @agent Decorator</CardTitle>
                </div>
                <CardDescription>Best for agent functions and entry points</CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`from llmobserve import agent, observe

observe(collector_url="...", api_key="...")

@agent("researcher")
def research_agent(query):
    # All API calls in this function are automatically 
    # labeled as "agent:researcher"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": query}]
    )
    return response

# Dashboard shows costs under "researcher" agent`}
                  id="decorator"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Method 2: section() Context Manager</CardTitle>
                </div>
                <CardDescription>Best for code blocks and nested workflows</CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`from llmobserve import section

# Flat labeling
with section("agent:researcher"):
    response = client.chat.completions.create(...)
    
# Hierarchical labeling (nested)
with section("agent:researcher"):
    with section("tool:web_search"):
        # Labeled as "agent:researcher/tool:web_search"
        search_results = search_api.query(...)
    
    with section("tool:summarize"):
        # Labeled as "agent:researcher/tool:summarize"
        summary = llm.create(...)`}
                  id="section"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Code className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Method 3: wrap_all_tools()</CardTitle>
                </div>
                <CardDescription>Best for LangChain, CrewAI, and other frameworks</CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`from llmobserve import wrap_all_tools
from langchain.agents import AgentExecutor

# Wrap your tools before passing to framework
tools = [search_tool, calculator_tool, weather_tool]
wrapped_tools = wrap_all_tools(tools)

# Each tool call is automatically tracked
agent = AgentExecutor(
    tools=wrapped_tools,
    llm=llm,
    ...
)

# Dashboard shows costs per tool`}
                  id="wrap_tools"
                />
              </CardContent>
            </Card>
          </div>
        </section>

        {/* AI Auto-Instrument Section */}
        <section id="ai-instrument" className="mb-16 scroll-mt-20">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <span className="text-2xl">✨</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900">AI Auto-Instrumentation</h2>
            <Badge className="bg-purple-600 text-white">NEW</Badge>
          </div>

          <Card className="mb-6 border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <span className="text-3xl">🤖</span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Let AI Label Your Code</h3>
                  <p className="text-gray-700 mb-3">
                    Use Claude AI to automatically analyze your Python code and suggest where to add labels. 
                    The AI understands LangChain, CrewAI, AutoGen, and custom agent patterns.
                  </p>
                  <div className="bg-white/50 rounded-lg p-3 text-sm text-gray-700">
                    <strong>How it works:</strong> The AI reads your code, identifies agent functions, tool calls, 
                    and workflows, then suggests the optimal instrumentation strategy using our labeling methods.
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="w-5 h-5" />
                  Installation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Install with AI support
pip install 'llmobserve[ai]'

# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."`}
                  id="ai-install"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Preview Suggestions (No Changes)</CardTitle>
                <CardDescription>See what the AI suggests without modifying your code</CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Analyze a file and preview suggestions
llmobserve preview my_agent.py

# Output:
# 🔍 Analysis of my_agent.py
# 
# Found 3 suggestions:
# 
# 1. Line 15 - decorator
#    Label: research_agent
#    Function: research_workflow
#    Reason: Main agent orchestration function making LLM calls
#    Before: def research_workflow(query):
#    After:  @agent("research_agent")
#            def research_workflow(query):
# 
# 2. Line 42 - wrap_tools
#    ...`}
                  id="ai-preview"
                  language="bash"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Auto-Apply Changes</CardTitle>
                <CardDescription>Let AI modify your code (creates .bak backup)</CardDescription>
              </CardHeader>
              <CardContent>
                <CodeBlock 
                  code={`# Apply AI suggestions automatically
llmobserve instrument my_agent.py --auto-apply

# Output:
# ✅ Applied 3 changes to my_agent.py
#    Backup created: my_agent.py.bak
#
# Changes:
#   1. Added @agent("research_agent") decorator
#   2. Added @agent("writer_agent") decorator
#   3. Wrapped tools with wrap_all_tools()

# Your original file is backed up as .bak`}
                  id="ai-apply"
                  language="bash"
                />
              </CardContent>
            </Card>

            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="pt-6">
                <div className="space-y-3 text-sm text-gray-700">
                  <div className="flex items-start gap-2">
                    <span>💰</span>
                    <p><strong>Cost:</strong> Uses Claude API (~$0.01 per file analyzed). We don&apos;t charge extra.</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span>🔒</span>
                    <p><strong>Privacy:</strong> Your code is sent to Anthropic&apos;s API for analysis. Not stored by us.</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span>📝</span>
                    <p><strong>Safety:</strong> Always creates .bak backup before modifying files.</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <span>🎯</span>
                    <p><strong>Accuracy:</strong> AI is conservative - only suggests where it clearly makes sense.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
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
                  <Zap className="w-5 h-5 text-indigo-600" />
                  <CardTitle>Agent & Workflow Tracking</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4">
                  Track costs for individual agents and complex workflows. See which agents cost the most.
                </p>
                <CodeBlock 
                  code={`from llmobserve import observe, section

observe(collector_url="...", api_key="...")

# Method 1: Use @agent decorator
from llmobserve import agent

@agent("research_agent")
def research_workflow():
    # All LLM calls here are tracked under "agent:research_agent"
    response = client.chat.completions.create(...)
    return response

# Method 2: Use section context manager
with section("agent:data_analyst"):
    # All calls in this block tracked under this agent
    response = client.chat.completions.create(...)
    
# Method 3: Wrap tools (for LangChain/CrewAI)
from llmobserve import wrap_all_tools

tools = [search_tool, calculator_tool]
wrapped_tools = wrap_all_tools(tools)

# Pass wrapped tools to your agent framework
agent = Agent(tools=wrapped_tools, ...)`}
                  id="agents"
                />
                <p className="text-sm text-gray-600 mt-4">
                  <strong>Dashboard view:</strong> Your dashboard will show a breakdown of costs by agent, including total spend and number of calls per agent. Untracked calls are grouped under "untracked".
                </p>
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

        {/* FAQ Section */}
        <section className="mb-16">
          <div className="flex items-center gap-3 mb-6">
            <HelpCircle className="w-8 h-8 text-indigo-600" />
            <h2 className="text-3xl font-bold text-gray-900">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How accurate is the cost tracking?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  We track token usage in real-time and calculate costs using official provider pricing tables. 
                  Our costs typically match provider bills within 1-2% accuracy. We update pricing daily to reflect 
                  any provider changes.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Which LLM providers are supported?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-2">
                  We support 40+ providers including:
                </p>
                <p className="text-gray-700 font-medium">
                  OpenAI (GPT-4, GPT-3.5, o1, o3), Anthropic (Claude), Google (Gemini), Cohere, 
                  Together AI, Replicate, Hugging Face, Perplexity, Groq, Mistral, DeepSeek, Fireworks, 
                  Anyscale, and many more.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Do you support agent frameworks like LangChain and CrewAI?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! We support all major agent frameworks including LangChain, CrewAI, AutoGen, and LlamaIndex. 
                  Use our <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">@agent</code> decorator or <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">wrap_all_tools()</code> function 
                  to track agent costs automatically.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I track costs by customer for my SaaS?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Absolutely! Pass a <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">customer_id</code> when calling <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">observe()</code> or 
                  use <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">set_customer_id()</code> dynamically. Your dashboard will show a breakdown of costs 
                  by customer, helping you understand profitability.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How do spending caps work?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Set a monthly spending limit in Settings → Spending Caps. You'll receive email alerts at 80% and 95% of your cap. 
                  You can optionally block API calls when the cap is reached to prevent overages.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I export my data?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! Export your cost data, runs, and traces to CSV or JSON format from any page. 
                  Perfect for creating custom reports or importing into your own analytics tools.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Does this work with streaming responses?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! We automatically track streaming responses from OpenAI, Anthropic, and other providers. 
                  Token usage and costs are calculated once the stream completes.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What if I see costs as "untracked" in my dashboard?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  "Untracked" means LLM calls were made without an explicit agent or section label. To fix this, 
                  use the <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">@agent</code> decorator, <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">section()</code> context manager, 
                  or <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">wrap_all_tools()</code> to label your workflows.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Do you store my API keys?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  No! We never see or store your LLM provider API keys. All API calls go directly from your code 
                  to the provider. We only track metadata (tokens, costs, latency) via HTTP headers.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Can I self-host the collector?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  The collector is currently hosted only. For enterprise self-hosting options, 
                  email us at enterprise@llmobserve.com.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What if costs aren't showing up?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Check that: (1) You've called <code className="bg-gray-100 px-1 py-0.5 rounded text-sm">observe()</code> before making LLM calls, 
                  (2) Your API key is correct, (3) You're using httpx, requests, or aiohttp for HTTP calls. 
                  If issues persist, check the Troubleshooting section above or email support@llmobserve.com.
                </p>
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
            Get Started - $8/month
          </Button>
        </section>
      </div>
    </div>
  );
}

