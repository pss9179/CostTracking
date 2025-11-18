"use client";

import { useEffect, useState } from "react";
import { useUser, useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Copy, Check, ArrowRight, Key, Terminal, Code } from "lucide-react";

interface APIKeyInfo {
  id: string;
  name: string;
  key?: string;  // Full key (only on first creation)
  key_prefix: string;
  created_at: string;
}

export default function OnboardingPage() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const router = useRouter();
  const [apiKey, setApiKey] = useState<APIKeyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);

  useEffect(() => {
    if (!isLoaded) return;
    
    if (!user) {
      router.push("/sign-in");
      return;
    }

    // Sync user and get/create API key
    async function syncUserAndGetKey() {
      if (!user) {
        setError("User not found");
        setLoading(false);
        return;
      }

      try {
        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        
        // Get user type from sessionStorage (set during signup)
        const selectedUserType = typeof window !== "undefined" 
          ? sessionStorage.getItem("selectedUserType") 
          : null;
        
        // Get Clerk token for authentication
        const token = await getToken();
        
        // Sync user from Clerk with user type
        const headers: HeadersInit = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        
        const syncResponse = await fetch(`${collectorUrl}/users/sync`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            id: user.id,
            email_addresses: user.emailAddresses.map(e => ({ email_address: e.emailAddress })),
            first_name: user.firstName,
            last_name: user.lastName,
            user_type: selectedUserType || "solo_dev", // Default to solo_dev if not set
          }),
        });
        
        // Clear sessionStorage after use
        if (typeof window !== "undefined") {
          sessionStorage.removeItem("selectedUserType");
        }

        if (!syncResponse.ok) {
          const errorText = await syncResponse.text();
          console.error("[Onboarding] Sync failed:", errorText);
          throw new Error(`Failed to sync user: ${errorText}`);
        }

        const syncData = await syncResponse.json();
        
        // If user already existed and we got their API key
        if (syncData.api_key) {
          setApiKey({
            id: "default",
            name: "Default API Key",
            key: syncData.api_key,
            key_prefix: syncData.api_key_prefix,
            created_at: new Date().toISOString(),
          });
        } else {
          // User already exists, they need to go to settings to view keys
          router.push("/settings");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load API key");
      } finally {
        setLoading(false);
      }
    }

    syncUserAndGetKey();
  }, [user, isLoaded, router]);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isLoaded || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-96 mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-32 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !apiKey) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8">
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle>Setup Error</CardTitle>
            <CardDescription>{error || "No API key available"}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => router.push("/settings")}>
              Go to Settings
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const installCode = `pip install llmobserve`;
  
  const usageCode = `from llmobserve import observe
from openai import OpenAI

# Initialize with your API key
observe(
    collector_url="${process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000"}",
    api_key="${apiKey.key || "YOUR_API_KEY"}"
)

# Use OpenAI as normal - all calls are tracked automatically!
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold">Welcome to LLM Observe! 🎉</h1>
          <p className="text-lg text-muted-foreground">
            Let's get you set up in 3 easy steps
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4">
          {[1, 2, 3].map((step) => (
            <div key={step} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                currentStep >= step ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-600"
              }`}>
                {step}
              </div>
              {step < 3 && (
                <div className={`w-16 h-1 ${
                  currentStep > step ? "bg-blue-600" : "bg-gray-200"
                }`} />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: API Key */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              <CardTitle>Step 1: Your API Key</CardTitle>
            </div>
            <CardDescription>
              Save this key securely - you won't be able to see it again!
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-gray-100 p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <code className="text-sm font-mono">{apiKey.key || apiKey.key_prefix}</code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => copyToClipboard(apiKey.key || "")}
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </Button>
              </div>
            </div>
            
            <Alert>
              <p className="text-sm">
                💡 <strong>Important:</strong> Store this key in your environment variables. 
                You can generate new keys anytime from Settings.
              </p>
            </Alert>

              <div className="space-y-2">
                <Button onClick={() => setCurrentStep(2)} className="w-full">
                  I've saved my API key - Continue <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <div className="text-xs text-gray-600 space-y-1">
                  <p className="text-center">💡 Tip: Save these to your .env file:</p>
                  <div className="bg-gray-50 p-2 rounded text-left font-mono">
                    <div>LLMOBSERVE_API_KEY={apiKey.key || "your-key-here"}</div>
                    <div>LLMOBSERVE_COLLECTOR_URL=https://llmobserve-production.up.railway.app</div>
                  </div>
                </div>
              </div>
          </CardContent>
        </Card>

        {/* Step 2: Install SDK */}
        {currentStep >= 2 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5" />
                <CardTitle>Step 2: Install the SDK</CardTitle>
              </div>
              <CardDescription>
                Install the Python SDK in your project
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-900 text-gray-100 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">Terminal</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(installCode)}
                    className="text-gray-400 hover:text-white"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <code className="text-sm font-mono">{installCode}</code>
              </div>

              <div className="space-y-2">
                <Button onClick={() => setCurrentStep(3)} className="w-full">
                  I've installed the SDK - Continue <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
                <p className="text-xs text-gray-500 text-center">
                  💡 Tip: Run this command in your project directory
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: Usage Example */}
        {currentStep >= 3 && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5" />
                <CardTitle>Step 3: Start Tracking</CardTitle>
              </div>
              <CardDescription>
                Add 2 lines of code to start tracking costs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-400">Python</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(usageCode)}
                    className="text-gray-400 hover:text-white"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  {usageCode}
                </pre>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold">What's tracked automatically:</h4>
                <div className="grid grid-cols-2 gap-2">
                  <Badge variant="secondary">✅ OpenAI API calls</Badge>
                  <Badge variant="secondary">✅ Token usage</Badge>
                  <Badge variant="secondary">✅ Costs (per call)</Badge>
                  <Badge variant="secondary">✅ Latency</Badge>
                  <Badge variant="secondary">✅ Errors</Badge>
                  <Badge variant="secondary">✅ Model info</Badge>
                </div>
              </div>

              <div className="space-y-3">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900 font-medium mb-2">
                    💳 Subscribe to Continue
                  </p>
                  <p className="text-xs text-blue-700 mb-3">
                    LLM Observe Pro is $8/month. Subscribe now to start tracking your costs!
                  </p>
                  <Button 
                    onClick={() => router.push("/settings/subscription")} 
                    className="w-full bg-indigo-600 hover:bg-indigo-700"
                    size="lg"
                  >
                    Subscribe Now - $8/month
                  </Button>
                  <p className="text-xs text-blue-600 text-center mt-2">
                    Have a promo code? Enter it in Settings → Subscription
                  </p>
                </div>
                <Button 
                  onClick={() => router.push("/dashboard")} 
                  variant="outline"
                  className="w-full"
                  size="lg"
                >
                  I'll Subscribe Later
                </Button>
                <p className="text-xs text-gray-500 text-center">
                  Need help? Check out our <Link href="/docs" className="text-indigo-600 hover:underline">documentation</Link>
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Help Section */}
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-4">
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Need Help?</h3>
                <p className="text-sm text-muted-foreground">
                  Check out our documentation or contact support if you run into any issues.
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={() => router.push("/docs")}>
                View Docs
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
