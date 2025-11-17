"use client";

import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { ArrowRight, Zap, BarChart3, Shield, Code, TrendingUp, CheckCircle2, DollarSign } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  const router = useRouter();
  const { isLoaded, isSignedIn } = useUser();

  // Redirect to dashboard if already signed in
  if (isLoaded && isSignedIn) {
    router.push("/dashboard");
    return null;
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
              <span className="text-xl font-bold text-gray-900">LLM Observe</span>
            </div>
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

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {/* Backed by badge */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 rounded-full text-sm text-gray-600">
              <span>Backed by</span>
              <span className="text-orange-500 font-semibold">Y Combinator</span>
            </div>
          </div>

          {/* Main Headline */}
          <div className="text-center max-w-4xl mx-auto mb-12">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6 leading-tight">
              Observability for your AI agents in just{" "}
              <span className="text-indigo-600">10 lines of code</span>
          </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8">
              See exactly what your AI agents are doing, and fix them when they break.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-4">
              <Button
                size="lg"
                onClick={() => router.push("/sign-up")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-lg px-8 py-6 h-auto"
              >
                Start for free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="border-2 border-gray-300 text-gray-900 hover:bg-gray-50 text-lg px-8 py-6 h-auto"
              >
                Book a Demo
              </Button>
            </div>
            <div className="flex gap-8 justify-center text-sm text-gray-500">
              <span>For individual developers</span>
              <span>For teams & companies</span>
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

      {/* Info Banner */}
      <section className="bg-indigo-600 py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <p className="text-white text-center text-sm md:text-base">
            ► New local-first + open-source observability tool for AI SDK on Next.js
          </p>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Your AI agents are failing silently
            </h2>
            <p className="text-xl text-gray-600">
              Standard monitoring misses the failures that matter most. We catch them all.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Bad Tool Calls */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Bad Tool Calls</h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 font-mono text-sm">
                <div className="text-gray-600">get_weather</div>
                <div className="mt-2 space-y-1">
                  <div>location: "tomorrow at 3pm"</div>
                  <div>time: "San Francisco"</div>
                </div>
                <div className="mt-3 bg-red-50 border border-red-200 rounded px-3 py-2 text-red-700 text-xs flex items-center gap-2">
                  <span>!</span>
                  <span>Arguments are swapped</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Wrong arguments, wrong timing, wrong results. Know when your agent calls the wrong tool or passes invalid data.
              </p>
            </div>

            {/* Infinite Loops */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Infinite Loops</h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 space-y-2">
                <div className="font-mono text-sm bg-white rounded p-2">search_database 0.234s</div>
                <div className="font-mono text-sm bg-white rounded p-2">search_database 0.241s</div>
                <div className="font-mono text-sm bg-white rounded p-2">search_database 0.238s</div>
                <div className="bg-yellow-50 border border-yellow-200 rounded px-3 py-2 text-yellow-700 text-xs flex items-center gap-2 mt-2">
                  <span>!</span>
                  <span>Same call repeated 47 times</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Same call, over and over, burning tokens. Detect when your agent gets stuck in repetitive patterns.
              </p>
            </div>

            {/* Hallucinations */}
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Hallucinations</h3>
              <div className="bg-gray-50 rounded-lg p-4 mb-4 font-mono text-sm">
                <div className="text-gray-600">get_order_status</div>
                <div className="mt-2">tracking: "TK9274..."</div>
                <div className="mt-3 bg-white rounded p-2">Output: "It is 79°F in Tampa, FL"</div>
                <div className="mt-3 bg-orange-50 border border-orange-200 rounded px-3 py-2 text-orange-700 text-xs flex items-center gap-2">
                  <span>!</span>
                  <span>Tool returned unrelated data</span>
                </div>
              </div>
              <p className="text-gray-600 text-sm">
                Made-up data that looks legitimate. Track when your LLM invents information instead of using real data.
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
              Tokens, latency, costs – tracked automatically
            </h2>
            <p className="text-xl text-gray-600">
              Stop calculating costs in spreadsheets. We do it for you.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 mb-16">
            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Real-time Tracking</h3>
              <p className="text-gray-600">
                Monitor every LLM call, tool invocation, and API request in real-time with detailed traces.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <DollarSign className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Cost Analytics</h3>
              <p className="text-gray-600">
                Automatic cost calculation across 40+ LLM providers and vector databases with spending caps.
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Shield className="w-8 h-8 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Spending Caps</h3>
              <p className="text-gray-600">
                Set budget limits with email alerts and automatic blocking to prevent cost overruns.
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
              10 Lines of Code to Production
            </h2>
            <p className="text-xl text-gray-600">
              Ship observability in minutes, not days
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
npm install llmobserve

# instrumentation.ts
from llmobserve import observe

observe(
    collector_url="${process.env.NEXT_PUBLIC_COLLECTOR_URL || "https://api.llmobserve.com"}",
    api_key=process.env.LLMOBSERVE_API_KEY
)

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
                    Works directly with your agent framework
                  </h3>
                  <p className="text-gray-600">
                    Seamlessly integrates with OpenAI, Anthropic, LangChain, Vercel AI SDK, and more
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Zap className="w-6 h-6 text-yellow-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Zero code changes to your agent
                  </h3>
                  <p className="text-gray-600">
                    Drop-in observability without modifying your agent logic
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    Start seeing traces in &lt; 1 minute
                  </h3>
                  <p className="text-gray-600">
                    Instant insights into your agent's behavior and performance
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
            Start shipping reliable agents today
          </h2>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              size="lg"
              onClick={() => router.push("/sign-up")}
              className="bg-white text-indigo-600 hover:bg-gray-100 text-lg px-8 py-6 h-auto"
            >
              Start for free
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-2 border-white text-white hover:bg-white/10 text-lg px-8 py-6 h-auto"
            >
              Book a Demo
            </Button>
          </div>
          <p className="text-indigo-100 mt-4 text-sm">
            For individual developers • For teams & companies
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
              <span className="text-lg font-bold text-gray-900">LLM Observe</span>
            </div>
            <div className="flex gap-6 text-sm text-gray-600">
              <Link href="#" className="hover:text-gray-900">Docs</Link>
              <Link href="#" className="hover:text-gray-900">Pricing</Link>
              <Link href="#" className="hover:text-gray-900">Support</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
