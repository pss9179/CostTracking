"use client";

import { useEffect, useState } from "react";
import { useUser, useAuth } from "@clerk/nextjs";
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Copy, Check, Trash2, Plus, Key, Settings as SettingsIcon, Bell, DollarSign, AlertTriangle } from "lucide-react";
import type { Cap, CapCreate, Alert as AlertType, ProviderTier } from "@/lib/api";
import { fetchProviderTiers, setProviderTier, deleteProviderTier } from "@/lib/api";

interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
}

export default function SettingsPage() {
  const { isLoaded, isSignedIn, user: clerkUser } = useUser();
  const { getToken } = useAuth();
  const [user, setUser] = useState<any>(null);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [caps, setCaps] = useState<Cap[]>([]);
  const [alerts, setAlerts] = useState<AlertType[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  
  // Caps form state
  const [showCapForm, setShowCapForm] = useState(false);
  const [capType, setCapType] = useState<string>("global");
  const [targetName, setTargetName] = useState("");
  const [limitAmount, setLimitAmount] = useState<string>("100");
  const [period, setPeriod] = useState<string>("monthly");
  const [enforcement, setEnforcement] = useState<string>("alert");
  const [alertThreshold, setAlertThreshold] = useState<string>("80");
  const [alertEmail, setAlertEmail] = useState("");
  const [creatingCap, setCreatingCap] = useState(false);
  
  // Provider tiers state
  const [providerTiers, setProviderTiers] = useState<ProviderTier[]>([]);
  const [loadingTiers, setLoadingTiers] = useState(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !clerkUser) return;
    
    // Sync user to database first if needed
    async function syncUserIfNeeded() {
      try {
        const collectorUrl = process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        const syncResponse = await fetch(`${collectorUrl}/users/sync`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            id: clerkUser?.id || "",
            email_addresses: clerkUser?.emailAddresses.map(e => ({ email_address: e.emailAddress })) || [],
            first_name: clerkUser?.firstName || "",
            last_name: clerkUser?.lastName || "",
          }),
        });
        
        if (!syncResponse.ok) {
          const errorText = await syncResponse.text();
          console.error("Failed to sync user:", syncResponse.status, errorText);
        } else {
          const syncData = await syncResponse.json();
          console.log("User synced successfully:", syncData);
        }
      } catch (err) {
        console.error("Failed to sync user:", err);
      }
    }
    
    syncUserIfNeeded().then(() => {
      // Wait a bit for sync to complete, then load data
      setTimeout(() => {
        loadAPIKeys();
        loadCaps();
        loadAlerts();
        loadProviderTiers();
      }, 500);
    });
  }, [isLoaded, isSignedIn, clerkUser]);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      // Get Clerk session token
      const session = await getToken();
      if (!session) {
        console.error("No Clerk session token");
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/clerk/api-keys/me`, {
        headers: {
          "Authorization": `Bearer ${session}`,
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setApiKeys(data.api_keys);
      } else {
        const errorText = await response.text();
        console.error("Failed to load API keys:", errorText);
        // If user not found, try syncing again
        if (response.status === 404) {
          console.log("User not found, syncing...");
          // Sync will happen in useEffect
        }
      }
    } catch (err) {
      console.error("Failed to load API keys:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      alert("Please enter a name for your API key");
      return;
    }

    try {
      setCreatingKey(true);
      const session = await getToken();
      if (!session) {
        alert("Please sign in to create an API key");
        setCreatingKey(false);
        return;
      }

      console.log("Creating API key with token:", session.substring(0, 20) + "...");
      
      const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/clerk/api-keys?name=${encodeURIComponent(newKeyName)}`;
      console.log("POST to:", url);

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNewKey(data.key);
        setNewKeyName("");
        await loadAPIKeys();
        alert("API key created successfully! Copy it now - you won't be able to see it again.");
      } else {
        const errorText = await response.text();
        console.error("Failed to create API key:", response.status, errorText);
        console.error("Full response:", response);
        alert(`Failed to create API key: ${response.status} - ${errorText}`);
      }
    } catch (err) {
      console.error("Failed to create API key:", err);
      alert(`Error: ${err instanceof Error ? err.message : "Failed to create API key"}`);
    } finally {
      setCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      return;
    }

    try {
      const session = await getToken();
      if (!session) return;

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/clerk/api-keys/${keyId}`,
        {
          method: "DELETE",
          headers: {
            "Authorization": `Bearer ${session}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        await loadAPIKeys();
      }
    } catch (err) {
      console.error("Failed to revoke API key:", err);
    }
  };

  const loadCaps = async () => {
    try {
      const session = await getToken();
      if (!session) return;

      const { fetchCaps } = await import("@/lib/api");
      const data = await fetchCaps();
      setCaps(data);
    } catch (err) {
      console.error("Failed to load caps:", err);
    }
  };

  const loadAlerts = async () => {
    try {
      const session = await getToken();
      if (!session) return;

      const { fetchAlerts } = await import("@/lib/api");
      const data = await fetchAlerts(20);
      setAlerts(data);
    } catch (err) {
      console.error("Failed to load alerts:", err);
    }
  };

  const handleCreateCap = async () => {
    try {
      setCreatingCap(true);
      const session = await getToken();
      if (!session) return;

      const { createCap } = await import("@/lib/api");
      const capData: CapCreate = {
        cap_type: capType,
        target_name: capType === "global" ? undefined : targetName,
        limit_amount: parseFloat(limitAmount),
        period,
        alert_threshold: parseFloat(alertThreshold) / 100,
        alert_email: alertEmail || user?.email,
      };

      await createCap(capData);
      await loadCaps();
      
      // Reset form
      setShowCapForm(false);
      setCapType("global");
      setTargetName("");
      setLimitAmount("100");
      setPeriod("monthly");
      setAlertThreshold("80");
      setAlertEmail("");
    } catch (err) {
      console.error("Failed to create cap:", err);
      alert(`Failed to create cap: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setCreatingCap(false);
    }
  };

  const handleToggleCap = async (capId: string, enabled: boolean) => {
    try {
      const session = await getToken();
      if (!session) return;

      const { updateCap } = await import("@/lib/api");
      await updateCap(capId, { enabled });
      await loadCaps();
    } catch (err) {
      console.error("Failed to toggle cap:", err);
    }
  };

  const handleDeleteCap = async (capId: string) => {
    if (!confirm("Are you sure you want to delete this spending cap?")) {
      return;
    }

    try {
      const session = await getToken();
      if (!session) return;

      const { deleteCap } = await import("@/lib/api");
      await deleteCap(capId);
      await loadCaps();
    } catch (err) {
      console.error("Failed to delete cap:", err);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadProviderTiers = async () => {
    try {
      setLoadingTiers(true);
      const session = await getToken();
      if (!session) return;
      
      const tenantId = clerkUser?.id;
      const tiers = await fetchProviderTiers(tenantId);
      setProviderTiers(tiers);
    } catch (err) {
      console.error("Failed to load provider tiers:", err);
    } finally {
      setLoadingTiers(false);
    }
  };

  const handleSetProviderTier = async (provider: string, tier: string, planName?: string) => {
    try {
      const session = await getToken();
      if (!session) return;
      
      const tenantId = clerkUser?.id;
      await setProviderTier(provider, tier, planName, tenantId);
      await loadProviderTiers(); // Reload
    } catch (err) {
      console.error("Failed to set provider tier:", err);
      alert("Failed to update provider tier. Please try again.");
    }
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
              <div className="mt-1 text-sm">
                {user?.name || clerkUser?.fullName || clerkUser?.firstName || "Not set"}
              </div>
            </div>
            <div>
              <Label>Email</Label>
              <div className="mt-1 text-sm">
                {user?.email || clerkUser?.emailAddresses?.[0]?.emailAddress || "Not set"}
              </div>
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
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : clerkUser?.createdAt
                  ? new Date(clerkUser.createdAt).toLocaleDateString()
                  : "Unknown"}
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

        {/* Spending Caps & Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Spending Caps & Alerts
            </CardTitle>
            <CardDescription>
              Set spending limits and receive email alerts when you approach your caps
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Create New Cap Button */}
            {!showCapForm && (
              <Button
                onClick={() => {
                  setShowCapForm(true);
                  setAlertEmail(user?.email || "");
                }}
                className="w-full flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Create Spending Cap
              </Button>
            )}

            {/* Cap Creation Form */}
            {showCapForm && (
              <div className="p-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg border-2 border-blue-200 space-y-4">
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-blue-600" />
                  Create New Spending Cap
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Cap Type</Label>
                    <Select value={capType} onValueChange={setCapType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="global">Global (All Services)</SelectItem>
                        <SelectItem value="provider">By Provider (e.g., OpenAI)</SelectItem>
                        <SelectItem value="model">By Model (e.g., gpt-4)</SelectItem>
                        <SelectItem value="agent">By Agent/Workflow</SelectItem>
                        <SelectItem value="customer">By Customer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {capType !== "global" && (
                    <div>
                      <Label>Target Name</Label>
                      <Input
                        placeholder={`e.g., ${
                          capType === "provider" ? "openai" :
                          capType === "model" ? "gpt-4" :
                          capType === "agent" ? "research_assistant" :
                          "customer_123"
                        }`}
                        value={targetName}
                        onChange={(e) => setTargetName(e.target.value)}
                      />
                    </div>
                  )}

                  <div>
                    <Label>Limit Amount ($)</Label>
                    <Input
                      type="number"
                      min="0"
                      step="0.01"
                      value={limitAmount}
                      onChange={(e) => setLimitAmount(e.target.value)}
                    />
                  </div>

                  <div>
                    <Label>Period</Label>
                    <Select value={period} onValueChange={setPeriod}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily</SelectItem>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Alert Threshold (%)</Label>
                    <Input
                      type="number"
                      min="0"
                      max="100"
                      value={alertThreshold}
                      onChange={(e) => setAlertThreshold(e.target.value)}
                      placeholder="80"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Send alert when {alertThreshold}% of cap is reached
                    </p>
                  </div>

                  <div>
                    <Label>Alert Email</Label>
                    <Input
                      type="email"
                      value={alertEmail}
                      onChange={(e) => setAlertEmail(e.target.value)}
                      placeholder={user?.email}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={handleCreateCap}
                    disabled={creatingCap || !limitAmount || (capType !== "global" && !targetName)}
                    className="flex-1"
                  >
                    {creatingCap ? "Creating..." : "Create Cap"}
                  </Button>
                  <Button
                    onClick={() => setShowCapForm(false)}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {/* Active Caps List */}
            {caps.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-medium text-sm text-muted-foreground">Active Caps</h4>
                {caps.map((cap) => (
                  <div
                    key={cap.id}
                    className={`p-4 rounded-lg border ${
                      cap.percentage_used >= 100 ? "bg-red-50 border-red-200" :
                      cap.percentage_used >= cap.alert_threshold * 100 ? "bg-yellow-50 border-yellow-200" :
                      "bg-white border-gray-200"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant={cap.cap_type === "global" ? "default" : "secondary"}>
                            {cap.cap_type}
                          </Badge>
                          {cap.target_name && (
                            <span className="text-sm font-medium">{cap.target_name}</span>
                          )}
                          <Badge variant={cap.enabled ? "default" : "outline"}>
                            {cap.enabled ? "Active" : "Disabled"}
                          </Badge>
                        </div>
                        
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">Spend:</span>
                            <span className="font-semibold">
                              ${cap.current_spend?.toFixed(2) || "0.00"} / ${cap.limit_amount.toFixed(2)}
                            </span>
                            <span className="text-sm text-muted-foreground">
                              ({cap.percentage_used?.toFixed(1) || 0}%)
                            </span>
                          </div>
                          
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                cap.percentage_used >= 100 ? "bg-red-500" :
                                cap.percentage_used >= cap.alert_threshold * 100 ? "bg-yellow-500" :
                                "bg-green-500"
                              }`}
                              style={{ width: `${Math.min(cap.percentage_used || 0, 100)}%` }}
                            />
                          </div>
                          
                          <div className="text-xs text-muted-foreground">
                            {cap.period.charAt(0).toUpperCase() + cap.period.slice(1)} cap • 
                            Alert at {(cap.alert_threshold * 100).toFixed(0)}% • 
                            Email: {cap.alert_email}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 ml-4">
                        <Button
                          onClick={() => handleToggleCap(cap.id, !cap.enabled)}
                          variant="outline"
                          size="sm"
                        >
                          {cap.enabled ? "Disable" : "Enable"}
                        </Button>
                        <Button
                          onClick={() => handleDeleteCap(cap.id)}
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Recent Alerts */}
            {alerts.length > 0 && (
              <div className="space-y-3 border-t pt-6">
                <h4 className="font-medium text-sm text-muted-foreground flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Recent Alerts
                </h4>
                {alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded border-l-4 ${
                      alert.alert_type === "cap_exceeded" 
                        ? "bg-red-50 border-red-500" 
                        : "bg-yellow-50 border-yellow-500"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-sm">
                          {alert.alert_type === "cap_exceeded" ? "🚨 Cap Exceeded" : "⚠️ Threshold Reached"}
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {alert.target_type}: {alert.target_name}
                        </div>
                        <div className="text-sm mt-1">
                          <strong>${alert.current_spend.toFixed(2)}</strong> / ${alert.cap_limit.toFixed(2)} 
                          <span className="text-muted-foreground"> ({alert.percentage.toFixed(1)}%)</span>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(alert.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {caps.length === 0 && !showCapForm && (
              <Alert>
                <AlertDescription>
                  <strong>💡 Tip:</strong> Set up spending caps to avoid surprise bills. 
                  You'll receive email alerts when you reach your thresholds.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Provider API Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              Provider API Keys
            </CardTitle>
            <CardDescription>
              Manage your third-party API keys (OpenAI, Anthropic, Pinecone, etc.)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Alert className="mb-4">
              <AlertDescription>
                <strong>🔒 Coming Soon:</strong> Securely store and manage your API keys for OpenAI, Anthropic, Pinecone, and other providers. 
                For now, use environment variables in your code.
              </AlertDescription>
            </Alert>
            
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-black flex items-center justify-center text-white font-bold">
                    AI
                  </div>
                  <div>
                    <div className="font-medium">OpenAI</div>
                    <div className="text-xs text-muted-foreground">GPT-4, GPT-3.5, Embeddings</div>
                  </div>
                </div>
                <Badge variant="outline">Not configured</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center text-white font-bold">
                    A
                  </div>
                  <div>
                    <div className="font-medium">Anthropic</div>
                    <div className="text-xs text-muted-foreground">Claude models</div>
                  </div>
                </div>
                <Badge variant="outline">Not configured</Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-muted rounded">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-blue-600 flex items-center justify-center text-white font-bold">
                    P
                  </div>
                  <div>
                    <div className="font-medium">Pinecone</div>
                    <div className="text-xs text-muted-foreground">Vector database</div>
                  </div>
                </div>
                <Badge variant="outline">Not configured</Badge>
              </div>
            </div>
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
