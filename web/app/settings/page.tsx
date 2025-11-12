"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { loadAuth, getAuthHeaders } from "@/lib/auth";
import { Copy, Check, Trash2, Plus, Key } from "lucide-react";

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const { user: loadedUser } = loadAuth();
    if (!loadedUser) {
      router.push("/login");
      return;
    }
    setUser(loadedUser);
  }, [router]);

  useEffect(() => {
    if (!user) return;
    loadAPIKeys();
  }, [user]);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/me`, {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys);
      }
    } catch (err) {
      console.error("Failed to load API keys:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;

    try {
      setCreatingKey(true);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/api-keys?name=${encodeURIComponent(newKeyName)}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setNewKey(data.key);
        setNewKeyName("");
        await loadAPIKeys();
      }
    } catch (err) {
      console.error("Failed to create API key:", err);
    } finally {
      setCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/api-keys/${keyId}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      if (response.ok) {
        await loadAPIKeys();
      }
    } catch (err) {
      console.error("Failed to revoke API key:", err);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <ProtectedLayout>
      <div className="p-8 space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account and API keys
          </p>
        </div>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>Your account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Name</Label>
              <div className="mt-1 text-sm">{user?.name || "Not set"}</div>
            </div>
            <div>
              <Label>Email</Label>
              <div className="mt-1 text-sm">{user?.email}</div>
            </div>
            <div>
              <Label>Subscription</Label>
              <div className="mt-1">
                <Badge>{user?.subscription_tier || "free"}</Badge>
              </div>
            </div>
            <div>
              <Label>Member Since</Label>
              <div className="mt-1 text-sm">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Unknown"}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Keys
            </CardTitle>
            <CardDescription>
              Use these keys to authenticate the SDK with your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Show newly created key */}
            {newKey && (
              <Alert className="bg-green-50 border-green-200">
                <AlertDescription className="space-y-3">
                  <p className="font-semibold text-green-900">✅ API Key Created Successfully!</p>
                  <p className="text-sm text-green-800">
                    Copy this key now - it won't be shown again:
                  </p>
                  <div className="flex items-center gap-2 p-3 bg-white rounded border">
                    <Input
                      readOnly
                      value={newKey}
                      className="font-mono text-sm"
                    />
                    <Button
                      onClick={() => handleCopy(newKey)}
                      variant="outline"
                      size="icon"
                    >
                      {copied ? <Check className="h-4 w-4 text-green-600" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                  <Button
                    onClick={() => setNewKey(null)}
                    variant="outline"
                    size="sm"
                  >
                    Done
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {/* Create New Key */}
            <div className="space-y-3 p-4 bg-gray-50 rounded-lg border">
              <Label>Create New API Key</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., Production Key"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  disabled={creatingKey}
                />
                <Button
                  onClick={handleCreateKey}
                  disabled={!newKeyName.trim() || creatingKey}
                  className="flex items-center gap-2"
                >
                  <Plus className="h-4 w-4" />
                  {creatingKey ? "Creating..." : "Create"}
                </Button>
              </div>
            </div>

            {/* API Keys Table */}
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading API keys...
              </div>
            ) : apiKeys.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No API keys found
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Key Prefix</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Used</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apiKeys.map((key) => (
                    <TableRow key={key.id}>
                      <TableCell className="font-medium">{key.name}</TableCell>
                      <TableCell className="font-mono text-sm">{key.key_prefix}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(key.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {key.last_used_at
                          ? new Date(key.last_used_at).toLocaleDateString()
                          : "Never"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          onClick={() => handleRevokeKey(key.id)}
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* SDK Setup Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>SDK Setup</CardTitle>
            <CardDescription>
              Add these lines to your code to start tracking
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm space-y-1">
              <div><span className="text-blue-400">import</span> llmobserve</div>
              <div className="mt-2">
                llmobserve.<span className="text-yellow-400">observe</span>(
              </div>
              <div className="pl-4">
                collector_url=<span className="text-green-400">"{typeof window !== "undefined" ? window.location.origin.replace("3000", "8000") : "http://localhost:8000"}"</span>,
              </div>
              <div className="pl-4">
                api_key=<span className="text-green-400">"{apiKeys[0]?.key_prefix || "your-api-key"}..."</span>
              </div>
              <div>)</div>
            </div>
            <Alert>
              <AlertDescription className="text-sm">
                <strong>💡 Pro Tip:</strong> For SaaS applications, use <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">set_customer_id(user.id)</code> to track costs per customer
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
