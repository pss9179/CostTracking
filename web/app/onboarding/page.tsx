"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check, Copy, ArrowRight } from "lucide-react";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useUser();
  const [step, setStep] = useState(1);
  const [apiKey, setApiKey] = useState("llmo_sk_1234567890abcdef"); // TODO: Generate real key

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const installCommand = `pip install llmobserve`;
  
  const configCode = `import llmobserve

# Initialize with your API key
llmobserve.init(api_key="${apiKey}")

# That's it! All your OpenAI & Pinecone calls are now tracked automatically`;

  const testCode = `import openai
from openai import OpenAI

client = OpenAI()

# This call will be automatically tracked!
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print("✅ Cost tracking active! Check your dashboard.")`;

  const finishOnboarding = () => {
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Welcome to LLM Observe! 🎉</h1>
          <p className="text-muted-foreground text-lg">
            Let's get you set up in 3 simple steps
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4">
          {[1, 2, 3].map((num) => (
            <div key={num} className="flex items-center gap-2">
              <div
                className={`flex items-center justify-center h-10 w-10 rounded-full border-2 font-semibold ${
                  step >= num
                    ? "bg-primary text-primary-foreground border-primary"
                    : "border-muted-foreground text-muted-foreground"
                }`}
              >
                {step > num ? <Check className="h-5 w-5" /> : num}
              </div>
              {num < 3 && (
                <div
                  className={`h-1 w-16 ${
                    step > num ? "bg-primary" : "bg-muted"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Get API Key */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 1: Your API Key</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                We've created an API key for you. Keep this safe - you'll need it to configure the SDK.
              </p>
              
              <div className="p-4 bg-muted rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Your API Key</Label>
                  <Badge>Keep this secret!</Badge>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 p-3 bg-background rounded border text-sm font-mono break-all">
                    {apiKey}
                  </code>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(apiKey)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  💡 You can generate more API keys later in Settings
                </p>
              </div>

              <Button onClick={() => setStep(2)} className="w-full" size="lg">
                Next: Install SDK
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Install SDK */}
        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 2: Install the SDK</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Install our Python SDK to start tracking your LLM costs automatically.
              </p>

              <div className="space-y-2">
                <Label className="text-sm font-medium">Install via pip:</Label>
                <div className="flex items-center gap-2">
                  <code className="flex-1 p-3 bg-muted rounded border text-sm font-mono">
                    {installCommand}
                  </code>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => copyToClipboard(installCommand)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-medium">Configure in your code:</Label>
                <div className="relative">
                  <pre className="p-4 bg-muted rounded border text-xs font-mono overflow-x-auto">
                    {configCode}
                  </pre>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(configCode)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button onClick={() => setStep(3)} className="flex-1" size="lg">
                  Next: Test It Out
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Test */}
        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Step 3: Test Your Setup</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                Run this simple test to make sure everything is working:
              </p>

              <div className="space-y-2">
                <div className="relative">
                  <pre className="p-4 bg-muted rounded border text-xs font-mono overflow-x-auto">
                    {testCode}
                  </pre>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(testCode)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-900">
                  <strong>✨ What happens next:</strong><br />
                  1. The SDK automatically patches OpenAI & Pinecone<br />
                  2. Every API call sends cost data to your dashboard<br />
                  3. You can track costs in real-time!
                </p>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button onClick={finishOnboarding} className="flex-1" size="lg">
                  Go to Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Help Section */}
        <Card className="bg-muted/50">
          <CardContent className="pt-6">
            <p className="text-sm text-center text-muted-foreground">
              Need help? Check out our{" "}
              <a href="/docs" className="text-primary hover:underline">
                documentation
              </a>{" "}
              or reach out to support
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Label({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <label className={`block text-sm font-medium ${className}`}>{children}</label>;
}

