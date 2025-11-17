"use client";

import { useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";

interface TenantCreated {
  tenant_id: string;
  name: string;
  api_key: string;
  message: string;
}

export default function AdminPage() {
  const { getToken } = useAuth();
  const [tenantId, setTenantId] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [creating, setCreating] = useState(false);
  const [created, setCreated] = useState<TenantCreated | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError(null);
    setCreated(null);

    try {
      const token = await getToken({ template: "default" });
      if (!token) {
        setError("Not authenticated. Please sign in.");
        setCreating(false);
        return;
      }
      
      const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
      const response = await fetch(`${collectorUrl}/auth/tenants`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          tenant_id: tenantId,
          name: tenantName
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create tenant");
      }

      const data = await response.json();
      setCreated(data);
      setTenantId("");
      setTenantName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create tenant");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Admin Panel</h1>
          <p className="text-muted-foreground">
            Create and manage tenant accounts
          </p>
        </div>

        {/* Create Tenant Form */}
        <Card>
          <CardHeader>
            <CardTitle>Create New Tenant</CardTitle>
            <CardDescription>
              Generate an API key for a new customer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateTenant} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="tenant_id">Tenant ID</Label>
                <Input
                  id="tenant_id"
                  placeholder="acme-corp"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  disabled={creating}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Lowercase, alphanumeric, hyphens allowed (e.g., "acme-corp")
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tenant_name">Display Name</Label>
                <Input
                  id="tenant_name"
                  placeholder="ACME Corporation"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                  disabled={creating}
                  required
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              <Button type="submit" disabled={creating}>
                {creating ? "Creating..." : "Create Tenant"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Success Message */}
        {created && (
          <Card className="border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-900">
                ✅ Tenant Created Successfully
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-green-900">Tenant ID</Label>
                <Input
                  value={created.tenant_id}
                  readOnly
                  className="bg-white"
                />
              </div>

              <div>
                <Label className="text-green-900">Display Name</Label>
                <Input
                  value={created.name}
                  readOnly
                  className="bg-white"
                />
              </div>

              <div>
                <Label className="text-green-900">API Key</Label>
                <Input
                  value={created.api_key}
                  readOnly
                  className="bg-white font-mono text-sm"
                />
                <p className="text-xs text-green-800 mt-1">
                  ⚠️ Copy this key now! It won't be shown again.
                </p>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    navigator.clipboard.writeText(created.api_key);
                    alert("API key copied to clipboard!");
                  }}
                  variant="outline"
                >
                  Copy API Key
                </Button>
                <Button
                  onClick={() => {
                    const message = `Tenant Created:\n\nTenant ID: ${created.tenant_id}\nName: ${created.name}\nAPI Key: ${created.api_key}\n\nLogin at: http://localhost:3000/tenant-login`;
                    navigator.clipboard.writeText(message);
                    alert("Full details copied to clipboard!");
                  }}
                  variant="outline"
                >
                  Copy All Details
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>How to Use</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">1. Create a Tenant</h3>
              <p className="text-sm text-muted-foreground">
                Use the form above to create a tenant account. Save the API key.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">2. Give API Key to Customer</h3>
              <p className="text-sm text-muted-foreground">
                Share the API key with your customer securely. They'll use it to log in.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">3. Customer Logs In</h3>
              <p className="text-sm text-muted-foreground">
                Customer visits{" "}
                <Link href="/tenant-login" className="text-blue-600 hover:underline">
                  /tenant-login
                </Link>{" "}
                and enters their API key.
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-2">4. View Customer Breakdown</h3>
              <p className="text-sm text-muted-foreground">
                Customer sees their dashboard with per-user cost breakdown.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Links */}
        <div className="flex gap-4">
          <Link href="/">
            <Button variant="outline">Main Dashboard</Button>
          </Link>
          <Link href="/tenants">
            <Button variant="outline">All Tenants</Button>
          </Link>
          <Link href="/tenant-login">
            <Button variant="outline">Tenant Login</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

