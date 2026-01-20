import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Zap,
  BarChart3,
  Shield,
  Code,
  TrendingUp,
  CheckCircle2,
  DollarSign,
} from "lucide-react";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default function LandingPage() {
  const { userId } = auth();
  if (userId) {
    redirect("/dashboard");
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Skyline</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/sign-in"
                className="text-gray-600 hover:text-gray-900 text-sm font-medium"
              >
                Login
              </Link>
              <Button asChild className="bg-indigo-600 hover:bg-indigo-700 text-white">
                <Link href="/sign-up">Get Started - $5/month</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Main Headline */}
          <div className="text-center max-w-4xl mx-auto mb-12">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Track LLM costs in just{" "}
              <span className="text-indigo-600">10 lines of code</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8">
              Monitor spending across all your AI providers. Track costs by
              customer, agent, or model. Set spending caps and never go over
              budget.
            </p>

            {/* CTA Buttons */}
            <div className="flex justify-center items-center mb-4">
              <Button
                size="lg"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-lg px-8 py-6 h-auto"
                asChild
              >
                <Link href="/sign-up">
                  Get Started
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
              </Button>
            </div>
            <div className="flex gap-8 justify-center text-sm text-gray-500">
              <span>For individual developers</span>
              <span>For SaaS founders tracking customer costs</span>
            </div>
          </div>

          {/* Decorative lines */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div className="absolute top-20 left-10 w-32 h-1 bg-yellow-400 transform rotate-12 opacity-60"></div>
            <div className="absolute top-40 right-20 w-24 h-1 bg-blue-400 transform -rotate-12 opacity-60"></div>
            <div className="absolute bottom-20 left-1/4 w-28 h-1 bg-pink-400 transform rotate-45 opacity-60"></div>
            <div className="absolute bottom-40 right-1/3 w-20 h-1 bg-red-400 transform -rotate-45 opacity-60"></div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Stop guessing your LLM costs
            </h2>
            <p className="text-xl text-gray-600">
              Track spending across OpenAI, Anthropic, Google, and 40+
              providers. See costs by customer, agent, or model.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Cost Tracking */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Real-time Cost Tracking
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 font-mono text-sm">
                <div className="text-gray-600">OpenAI: $0.45</div>
                <div className="mt-2 space-y-1">
                  <div>Anthropic: $0.32</div>
                  <div>Pinecone: $0.12</div>
                </div>
                <div className="mt-3 bg-green-50 border border-green-200 rounded px-3 py-2 text-green-700 text-xs flex items-center gap-2">
                  <span>✓</span>
                  <span>All costs tracked automatically</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Every API call is tracked with accurate cost calculation. See
                exactly where your money is going.
              </p>
            </div>

            {/* Customer Cost Tracking */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Track Customer Costs
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-2">
                <div className="font-mono text-sm bg-white rounded p-2">
                  Customer A: $0.89
                </div>
                <div className="font-mono text-sm bg-white rounded p-2">
                  Customer B: $0.45
                </div>
                <div className="font-mono text-sm bg-white rounded p-2">
                  Customer C: $0.23
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded px-3 py-2 text-blue-700 text-xs flex items-center gap-2 mt-2">
                  <span>📊</span>
                  <span>Per-customer breakdown</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Perfect for SaaS founders. Track costs per customer to
                understand profitability and set pricing.
              </p>
            </div>

            {/* Spending Caps */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Spending Caps & Alerts
              </h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 font-mono text-sm">
                <div className="text-gray-600">Daily cap: $100</div>
                <div className="mt-2">Current spend: $87.50</div>
                <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded px-3 py-2 text-yellow-700 text-xs flex items-center gap-2">
                  <span>⚠</span>
                  <span>87.5% of daily cap</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Set budget limits with email alerts. Never go over budget again
                with automatic spending caps.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Automatic cost tracking for all your LLM calls
            </h2>
            <p className="text-xl text-gray-600">
              Stop calculating costs in spreadsheets. We track every API call
              and calculate costs automatically.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Real-time Cost Tracking
              </h3>
              <p className="text-gray-600">
                Monitor every LLM call and API request. See costs update in
                real-time as your agents make calls.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <DollarSign className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Customer Cost Tracking
              </h3>
              <p className="text-gray-600">
                Track costs per customer for your SaaS. See which customers are
                most expensive and optimize pricing.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Spending Caps
              </h3>
              <p className="text-gray-600">
                Set budget limits with email alerts and automatic blocking to
                prevent cost overruns.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Code Example Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              10 Lines of Code to Start Tracking
            </h2>
            <p className="text-xl text-gray-600">
              Start tracking costs in minutes, not days
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Code Block */}
            <div className="bg-gray-900 rounded-xl p-6 shadow-xl">
              <div className="flex gap-2 mb-4">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
              <pre className="text-gray-100 text-sm font-mono overflow-x-auto">
                <code>{`# Install the package
pip install llmobserve

# Your code
from llmobserve import observe

# Just set your API key - collector URL defaults to production!
observe(api_key=os.getenv("LLMOBSERVE_API_KEY"))

# That's it! All your LLM calls
# are now tracked automatically.`}</code>
              </pre>
            </div>

            {/* Features List */}
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Code className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Works with all major LLM providers
                  </h3>
                  <p className="text-gray-600">
                    Seamlessly integrates with OpenAI, Anthropic, Google,
                    Cohere, and 40+ providers
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Zero code changes required
                  </h3>
                  <p className="text-gray-600">
                    Drop-in cost tracking without modifying your application
                    code
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Start seeing costs in &lt; 1 minute
                  </h3>
                  <p className="text-gray-600">
                    Instant cost tracking and analytics for all your LLM calls
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-indigo-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Start tracking your LLM costs today
          </h2>
          <div className="flex justify-center">
            <Button
              size="lg"
              className="bg-white text-indigo-600 hover:bg-gray-100 text-lg px-8 py-6 h-auto"
              asChild
            >
              <Link href="/sign-up">Get Started</Link>
            </Button>
          </div>
          <p className="text-indigo-100 mt-4 text-sm">
            For individual developers • For SaaS founders tracking customer
            costs
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-2 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">Skyline</span>
            </div>
            <div className="flex gap-6 text-sm text-gray-600">
              <Link href="/docs" className="hover:text-gray-900">
                Docs
              </Link>
              <Link href="/pricing" className="hover:text-gray-900">
                Pricing
              </Link>
              <Link href="#" className="hover:text-gray-900">
                Support
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
