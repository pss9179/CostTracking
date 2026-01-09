"use client";

import { useEffect, useState } from "react";
import { useUser, useAuth } from "@clerk/nextjs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import {
  Copy,
  Check,
  Trash2,
  Plus,
  Key,
  Settings as SettingsIcon,
  Bell,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import type {
  Cap,
  CapCreate,
  Alert as AlertType,
  ProviderTier,
} from "@/lib/api";
import {
  fetchProviderTiers,
  setProviderTier,
  deleteProviderTier,
} from "@/lib/api";

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
        const session = await getToken();
        if (!session) {
          console.error("No Clerk session token for sync");
          return;
        }

        const collectorUrl =
          process.env.NEXT_PUBLIC_COLLECTOR_URL || "http://localhost:8000";
        const syncResponse = await fetch(`${collectorUrl}/users/sync`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            id: clerkUser?.id || "",
            email_addresses:
              clerkUser?.emailAddresses.map((e) => ({
                email_address: e.emailAddress,
              })) || [],
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

      const response = await fetch("/api/api-keys", {
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log("API keys loaded:", data);
        setUser(data.user);
        setApiKeys(data.api_keys || []);
      } else {
        let errorMessage = "Unknown error";
        try {
          const errorData = await response.json();
          errorMessage =
            errorData.error || errorData.detail || JSON.stringify(errorData);
        } catch (e) {
          const errorText = await response.text();
          errorMessage = errorText || `HTTP ${response.status}`;
        }
        console.error(
          "Failed to load API keys:",
          response.status,
          errorMessage
        );
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
    console.log("[Frontend] handleCreateKey called, newKeyName:", newKeyName);

    if (!newKeyName.trim()) {
      alert("Please enter a name for your API key");
      return;
    }

    try {
      setCreatingKey(true);
      console.log("[Frontend] Getting token...");
      const session = await getToken();
      console.log("[Frontend] Token received:", session ? "Yes" : "No");

      if (!session) {
        alert("Please sign in to create an API key");
        setCreatingKey(false);
        return;
      }

      console.log("[Frontend] Creating API key with name:", newKeyName);
      console.log("[Frontend] Making fetch request to /api/api-keys");

      const response = await fetch("/api/api-keys", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newKeyName,
        }),
      });

      console.log(
        "[Frontend] Response status:",
        response.status,
        "ok:",
        response.ok
      );

      if (response.ok) {
        const data = await response.json();
        console.log("[Frontend] API key created successfully:", {
          ...data,
          key: data.key ? `${data.key.substring(0, 10)}...` : "NO KEY",
        });
        if (data.key) {
          setNewKey(data.key);
          setNewKeyName("");
          await loadAPIKeys();
          alert(
            "API key created successfully! Copy it now - you won't be able to see it again."
          );
        } else {
          console.error("[Frontend] No key in response:", data);
          alert(
            "API key created but key not returned. Please check console for details."
          );
        }
      } else {
        let errorMessage = "Unknown error";
        try {
          const errorData = await response.json();
          errorMessage =
            errorData.error || errorData.detail || JSON.stringify(errorData);
          console.error(
            "[Frontend] Failed to create API key - error data:",
            errorData
          );
        } catch (e) {
          const errorText = await response.text();
          errorMessage = errorText || `HTTP ${response.status}`;
          console.error(
            "[Frontend] Failed to create API key - error text:",
            errorText
          );
        }
        console.error(
          "[Frontend] Failed to create API key:",
          response.status,
          errorMessage
        );
        alert(`Failed to create API key: ${response.status} - ${errorMessage}`);
      }
    } catch (err) {
      console.error("Failed to create API key - catch block:", err);
      console.error(
        "Error type:",
        err instanceof Error ? err.constructor.name : typeof err
      );
      console.error(
        "Error message:",
        err instanceof Error ? err.message : String(err)
      );
      console.error(
        "Error stack:",
        err instanceof Error ? err.stack : "No stack"
      );
      alert(
        `Error: ${
          err instanceof Error ? err.message : "Failed to create API key"
        }`
      );
    } finally {
      setCreatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (
      !confirm(
        "Are you sure you want to revoke this API key? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`/api/api-keys?keyId=${keyId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        await loadAPIKeys();
      } else {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Unknown error" }));
        console.error("Failed to revoke API key:", response.status, errorData);
        alert(
          `Failed to revoke API key: ${errorData.error || "Unknown error"}`
        );
      }
    } catch (err) {
      console.error("Failed to revoke API key:", err);
      alert(
        `Error: ${
          err instanceof Error ? err.message : "Failed to revoke API key"
        }`
      );
    }
  };

  const loadCaps = async () => {
    try {
      const session = await getToken();
      if (!session) return;

      const { fetchCaps } = await import("@/lib/api");
      const data = await fetchCaps(session);
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
      const data = await fetchAlerts(20, session);
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

      await createCap(capData, session);
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
      alert(
        `Failed to create cap: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setCreatingCap(false);
    }
  };

  const handleToggleCap = async (capId: string, enabled: boolean) => {
    try {
      const session = await getToken();
      if (!session) return;

      const { updateCap } = await import("@/lib/api");
      await updateCap(capId, { enabled }, session);
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
      await deleteCap(capId, session);
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
      const tiers = await fetchProviderTiers(tenantId, session);
      setProviderTiers(tiers);
    } catch (err) {
      console.error("Failed to load provider tiers:", err);
    } finally {
      setLoadingTiers(false);
    }
  };

  const handleSetProviderTier = async (
    provider: string,
    tier: string,
    planName?: string
  ) => {
    try {
      const session = await getToken();
      if (!session) return;

      const tenantId = clerkUser?.id;
      await setProviderTier(provider, tier, planName, tenantId, session);
      await loadProviderTiers(); // Reload
    } catch (err) {
      console.error("Failed to set provider tier:", err);
      alert("Failed to update provider tier. Please try again.");
    }
  };

  return (
    <ProtectedLayout>
      <div className="space-y-8">
        {/* Account Info */}
        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <h3 className="text-lg font-semibold mb-4">Account Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Name</p>
                <p className="text-base font-medium text-gray-900">
                  {user?.name ||
                    clerkUser?.fullName ||
                    clerkUser?.firstName ||
                    "Not set"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Email</p>
                <p className="text-base font-medium text-gray-900">
                  {user?.email ||
                    clerkUser?.emailAddresses?.[0]?.emailAddress ||
                    "Not set"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Plan
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="bg-emerald-500">
                    Free Forever
                  </Badge>
                </div>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">
                  Member Since
                </p>
                <p className="text-base font-medium text-gray-900">
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString()
                    : clerkUser?.createdAt
                    ? new Date(clerkUser.createdAt).toLocaleDateString()
                    : "Unknown"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card className="border-0 shadow-sm bg-white">
          <CardContent className="pt-6">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-1">API Keys</h3>
                <p className="text-sm text-muted-foreground">
                  Use these keys to authenticate the SDK with your account
                </p>
              </div>
              {/* Show newly created key */}
              {newKey && (
                <Alert className="bg-green-50 border-green-200">
                  <AlertDescription className="space-y-3">
                    <p className="font-semibold text-green-900">
                      ✅ API Key Created Successfully!
                    </p>
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
                        {copied ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
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
              <div className="space-y-3 p-4 bg-gray-50 rounded-lg border border-gray-100">
                <Label className="text-sm font-medium">
                  Create New API Key
                </Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="e.g., Production Key"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    disabled={creatingKey}
                    className="bg-white"
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
                <div className="rounded-lg border border-gray-100 bg-white overflow-hidden">
                  <Table>
                    <TableHeader className="bg-gray-50/50">
                      <TableRow className="border-gray-100 hover:bg-transparent">
                        <TableHead className="font-medium text-gray-500">
                          Name
                        </TableHead>
                        <TableHead className="font-medium text-gray-500">
                          Key Prefix
                        </TableHead>
                        <TableHead className="font-medium text-gray-500">
                          Created
                        </TableHead>
                        <TableHead className="font-medium text-gray-500">
                          Last Used
                        </TableHead>
                        <TableHead className="text-right font-medium text-gray-500">
                          Actions
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {apiKeys.map((key) => (
                        <TableRow
                          key={key.id}
                          className="border-gray-50 hover:bg-gray-50/50"
                        >
                          <TableCell className="font-medium text-gray-900">
                            {key.name}
                          </TableCell>
                          <TableCell className="font-mono text-sm text-gray-600">
                            {key.key_prefix}
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">
                            {new Date(key.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">
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
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
