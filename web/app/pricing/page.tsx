"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, ArrowRight, Zap } from "lucide-react";
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
              <span className="text-xl font-bold text-gray-900">LLM Observe</span>
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
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-xl text-gray-600">
            One plan. All features. No hidden fees.
          </p>
        </div>

        {/* Pricing Card */}
        <Card className="border-2 border-indigo-600 shadow-xl">
          <CardHeader className="text-center pb-8 pt-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4 mx-auto">
              <Zap className="w-8 h-8 text-indigo-600" />
            </div>
            <CardTitle className="text-3xl font-bold mb-2">LLM Observe Pro</CardTitle>
            <CardDescription className="text-lg">Everything you need to track LLM costs</CardDescription>
            <div className="mt-6">
              <div className="flex items-baseline justify-center gap-2">
                <span className="text-5xl font-bold text-gray-900">$8</span>
                <span className="text-xl text-gray-600">/month</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">Billed monthly • Cancel anytime</p>
            </div>
          </CardHeader>
          <CardContent className="pb-12">
            <Button 
              onClick={() => router.push("/sign-up")} 
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white mb-8"
              size="lg"
            >
              Get Started Now
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
                "Email support"
              ].map((feature, i) => (
                <div key={i} className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-700">{feature}</span>
                </div>
              ))}
            </div>

            <div className="mt-8 pt-8 border-t border-gray-200">
              <p className="text-sm text-gray-600 text-center">
                Have a promo code? Apply it after signing up in Settings → Subscription
              </p>
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
                <CardTitle className="text-lg">Can I cancel anytime?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes! You can cancel your subscription at any time from the Settings page. No questions asked, no cancellation fees.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">What happens to my data if I cancel?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Your data remains accessible for 30 days after cancellation. You can export all your data to CSV/JSON before canceling. After 30 days, your data is permanently deleted.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Do you offer refunds?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  Yes, we offer a full refund within 7 days of your first payment if you're not satisfied. Just email us at support@llmobserve.com.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Is there a limit on API calls or data?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  No limits! Track unlimited API calls, customers, and agents. The $8/month price covers everything.
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
                <CardTitle className="text-lg">Do you offer enterprise plans?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  For now, we only offer the $8/month plan. If you need enterprise features like SSO, dedicated support, or on-premise deployment, email us at enterprise@llmobserve.com.
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
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            Get Started - $8/month
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

