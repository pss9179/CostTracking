"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { signup, saveAuth } from "@/lib/auth";
import { Copy, Check, Sparkles } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState<"signup" | "onboarding">("signup");
  
  // Signup form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Onboarding state
  const [apiKey, setApiKey] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signup(email, password, name || undefined);
      saveAuth(result.token, result.user);
      setApiKey(result.api_key.key);
      setStep("onboarding");
    } catch (err: any) {
      setError(err.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleContinue = () => {
    router.push("/dashboard");
  };

  if (step === "onboarding") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="space-y-2">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-green-100 p-3 rounded-full">
                <Sparkles className="h-8 w-8 text-green-600" />
              </div>
            </div>
            <CardTitle className="text-3xl font-bold text-center">Welcome to LLMObserve! 🎉</CardTitle>
            <CardDescription className="text-center text-base">
              Your account is ready. Here's your API key to get started.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* API Key Display */}
            <div className="space-y-3 p-6 bg-gray-50 rounded-lg border-2 border-blue-200">
              <div className="flex items-center justify-between">
                <Label className="text-base font-semibold">Your API Key</Label>
                <span className="text-sm text-red-600 font-medium">⚠️ Save this now!</span>
              </div>
              <div className="flex items-center gap-2">
                <Input
                  readOnly
                  value={apiKey}
                  className="font-mono text-sm bg-white"
                />
                <Button
                  onClick={handleCopy}
                  variant="outline"
                  size="icon"
                >
                  {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                This key will only be shown once. Save it securely!
              </p>
            </div>

            {/* Setup Instructions */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">Quick Setup (30 seconds)</h3>
              
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                    1
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="font-medium">Install the SDK</p>
                    <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm">
                      pip install llmobserve
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                    2
                  </div>
                  <div className="flex-1 space-y-2">
                    <p className="font-medium">Add 2 lines to your code</p>
                    <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm space-y-1">
                      <div><span className="text-blue-400">import</span> llmobserve</div>
                      <div>
                        llmobserve.<span className="text-yellow-400">observe</span>(
                      </div>
                      <div className="pl-4">
                        collector_url=<span className="text-green-400">"{typeof window !== "undefined" ? window.location.origin.replace("3000", "8000") : "http://localhost:8000"}"</span>,
                      </div>
                      <div className="pl-4">
                        api_key=<span className="text-green-400">"{apiKey.substring(0, 20)}..."</span>
                      </div>
                      <div>)</div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                    3
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Track your customers (optional, for SaaS)</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Use <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">set_customer_id(user.id)</code> to attribute costs to your end-users
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <Alert className="bg-blue-50 border-blue-200">
              <AlertDescription className="text-sm">
                <strong>💡 Pro Tip:</strong> Use the same API key across all your services. Each request is automatically tagged so you can filter by customer, agent, or workflow.
              </AlertDescription>
            </Alert>
          </CardContent>

          <CardFooter className="flex flex-col space-y-3">
            <Button
              onClick={handleContinue}
              className="w-full"
              size="lg"
            >
              Go to Dashboard →
            </Button>
            <p className="text-xs text-center text-muted-foreground">
              Your API key is also available in Settings
            </p>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Create Account</CardTitle>
          <CardDescription className="text-center">
            Start tracking your LLM costs in 30 seconds
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="name">Name (optional)</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                minLength={8}
              />
              <p className="text-xs text-muted-foreground">
                At least 8 characters
              </p>
            </div>
          </CardContent>

          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? "Creating account..." : "Create Account"}
            </Button>

            <div className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="text-primary hover:underline font-medium">
                Sign in
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

