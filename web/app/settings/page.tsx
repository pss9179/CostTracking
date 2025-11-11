"use client";

import { useState, useEffect } from "react";
import { useUser } from "@clerk/nextjs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Copy, Plus, Trash2, Eye, EyeOff } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export default function SettingsPage() {
  const { user, isLoaded } = useUser();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creating, setCreating] = useState(false);
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    if (isLoaded && user) {
      fetchAPIKeys();
    }
  }, [isLoaded, user]);

  const fetchAPIKeys = async () => {
    try {
      // TODO: Replace with actual API endpoint once backend is updated
      const response = await fetch(`${process.env.NEXT_PUBLIC_COLLECTOR_URL || 'http://localhost:8000'}/api-keys`, {
        headers: {
          'Authorization': `Bearer ${user?.id}` // Temporary - will use proper auth
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data);
      } else if (response.status === 404) {
        // Endpoint not implemented yet
        setApiKeys([]);
      }
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      // For now, show empty state
      setApiKeys([]);
    } finally {
      setLoading(false);
    }
  };

  const createAPIKey = async () => {
    if (!newKeyName.trim()) return;
    
    setCreating(true);
    try {
      // TODO: Replace with actual API endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_COLLECTOR_URL || 'http://localhost:8000'}/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user?.id}`
        },
        body: JSON.stringify({ name: newKeyName })
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewlyCreatedKey(data.key);
        setNewKeyName("");
        fetchAPIKeys();
      } else {
        throw new Error('Failed to create API key');
      }
    } catch (error) {
      console.error('Error creating API key:', error);
      alert('Failed to create API key. Backend endpoint not yet implemented.');
    } finally {
      setCreating(false);
    }
  };

  const revokeAPIKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_COLLECTOR_URL || 'http://localhost:8000'}/api-keys/${keyId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${user?.id}`
          }
        }
      );
      
      if (response.ok) {
        fetchAPIKeys();
      }
    } catch (error) {
      console.error('Error revoking API key:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString() + ' ' + new Date(dateString).toLocaleTimeString();
  };

  if (!isLoaded || loading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <PageHeader
        title="Settings"
        description="Manage your API keys and account settings"
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Settings" },
        ]}
      />

      {/* Newly Created Key Alert */}
      {newlyCreatedKey && (
        <Card className="border-green-500 bg-green-50">
          <CardHeader>
            <CardTitle className="text-green-900">API Key Created!</CardTitle>
            <CardDescription className="text-green-800">
              Make sure to copy your API key now. You won't be able to see it again!
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <code className="flex-1 p-3 bg-white rounded border text-sm font-mono">
                {showKey ? newlyCreatedKey : '••••••••••••••••••••••••••••••••'}
              </code>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowKey(!showKey)}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button
                variant="default"
                onClick={() => copyToClipboard(newlyCreatedKey)}
              >
                <Copy className="mr-2 h-4 w-4" />
                Copy
              </Button>
              <Button
                variant="ghost"
                onClick={() => setNewlyCreatedKey(null)}
              >
                Dismiss
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* API Keys Management */}
      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>
            Use API keys to authenticate your SDK and send cost data to LLM Observe.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Create New Key */}
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="keyName">Key Name</Label>
              <Input
                id="keyName"
                placeholder="Production, Development, etc."
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && createAPIKey()}
              />
            </div>
            <div className="pt-6">
              <Button 
                onClick={createAPIKey}
                disabled={!newKeyName.trim() || creating}
              >
                <Plus className="mr-2 h-4 w-4" />
                Create API Key
              </Button>
            </div>
          </div>

          {/* API Keys List */}
          {apiKeys.length === 0 ? (
            <div className="text-center py-12 border rounded-lg bg-muted/10">
              <p className="text-muted-foreground mb-4">No API keys yet</p>
              <p className="text-sm text-muted-foreground">
                Create your first API key to start tracking costs
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {key.key_prefix}...
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(key.created_at)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(key.last_used_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(key.key_prefix)}
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => revokeAPIKey(key.id)}
                          className="text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Account Info */}
      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Email</Label>
            <p className="text-sm text-muted-foreground mt-1">
              {user?.primaryEmailAddress?.emailAddress}
            </p>
          </div>
          <div>
            <Label>User ID</Label>
            <p className="text-sm text-muted-foreground mt-1 font-mono">
              {user?.id}
            </p>
          </div>
          <div>
            <Label>Plan</Label>
            <Badge variant="default" className="mt-1">Free</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

