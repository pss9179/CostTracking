"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, ArrowRight, Zap, Sparkles } from "lucide-react";
import Link from "next/link";

export default function PricingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Skyline</span>
            </Link>
            <div className="flex items-center gap-4">
              <Link href="/docs" className="text-gray-600 hover:text-gray-900 text-sm font-medium">
                Docs
              </Link>
              <Link href="/sign-in" className="text-gray-600 hover:text-gray-900 text-sm font-medium">
                Login
              </Link>
              <Button
                onClick={() => router.push("/sign-up")}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                Get Started Free
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            100% Free Forever
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Free for everyone
          </h1>
          <p className="text-xl text-gray-600">
            All features included. No credit card required. No limits.
          </p>
        </div>

        {/* Pricing Card */}
        <Card className="border-2 border-emerald-500 shadow-xl">
          <CardHeader className="text-center pb-8 pt-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 rounded-full mb-4 mx-auto">
              <Sparkles className="w-8 h-8 text-emerald-600" />
            </div>
            <CardTitle className="text-3xl font-bold mb-2">Skyline Free</CardTitle>
            <CardDescription className="text-lg">Everything you need to track LLM costs</CardDescription>
            <div className="mt-6">
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-5xl font-bold text-gray-900">$0</span>
                <span className="text-xl text-gray-600">/forever</span>
              </div>
              <p className="text-sm text-emerald-600 mt-2 font-medium">No credit card required</p>
            </div>
          </CardHeader>
          <CardContent className="pb-12">
            <Button 
              onClick={() => router.push("/sign-up")} 
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mb-8"
              size="lg"
            >
              Get Started Free
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>

            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 mb-4">Everything included:</h3>
              
              {[
                "Unlimited LLM API calls tracked",
                "Real-time cost tracking across 40+ providers",
                "Track costs by customer, agent, or model",
                "Set spending caps with email alerts",
                "Daily, weekly, and monthly cost reports",
                "Export data to CSV/JSON",
                "Agent and workflow tracking",
                "Multi-tenant support for SaaS",
                "Customer cost attribution",
                "Latency monitoring",
                "Error tracking and alerts",
                "Historical cost analysis",
                "Provider comparison insights",
                "Community support"
              ].map((feature, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-emerald-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* FAQ Section */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            Frequently Asked Questions
          </h2>
          
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Is it really free?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! Skyline is completely free with no hidden costs. All features are included at no charge.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Are there any usage limits?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  No limits! Track unlimited API calls, customers, and agents. Everything is included for free.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Which LLM providers do you support?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-2">
                  We support 40+ providers including:
                </p>
                <p className="text-gray-700 font-medium">
                  OpenAI, Anthropic, Google (Gemini), Cohere, Together AI, Replicate, Hugging Face, Perplexity, Groq, Mistral, and many more.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">How accurate is the cost tracking?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  We track token usage in real-time and calculate costs using official provider pricing. Our costs typically match provider bills within 1-2% accuracy.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center mt-20">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to get started?</h2>
          <p className="text-lg text-gray-600 mb-8">
            Start tracking your LLM costs in 2 minutes
          </p>
          <Button 
            onClick={() => router.push("/sign-up")} 
            size="lg"
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            Get Started Free
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
