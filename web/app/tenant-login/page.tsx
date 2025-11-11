"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function TenantLoginPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Validate API key by calling /auth/me
      const response = await fetch("http://localhost:8000/auth/me", {
        headers: {
          "X-API-Key": apiKey
        }
      });

      if (!response.ok) {
        throw new Error("Invalid API key");
      }

      const tenant = await response.json();

      // Store API key in localStorage
      localStorage.setItem("tenant_api_key", apiKey);
      localStorage.setItem("tenant_id", tenant.tenant_id);
      localStorage.setItem("tenant_name", tenant.name);

      // Redirect to tenant dashboard
      router.push("/tenant-dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Tenant Login</CardTitle>
          <CardDescription>
            Enter your API key to view your customer cost breakdown
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="llmo_..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={loading}
                required
              />
              <p className="text-xs text-muted-foreground">
                Your API key starts with <code>llmo_</code>
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </Button>

            <div className="text-center pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Don't have an API key?{" "}
                <a href="/admin" className="text-blue-600 hover:underline">
                  Contact admin
                </a>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

