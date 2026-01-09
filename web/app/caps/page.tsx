"use client";

  import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { ProtectedLayout } from "@/components/ProtectedLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  Bell,
  Plus,
  Trash2,
  Shield,
  DollarSign,
  Server,
  Cpu,
  Layers,
  Users,
  Globe,
  Mail,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import {
  fetchCaps,
  fetchAlerts,
  createCap,
  updateCap,
  deleteCap,
  fetchProviderStats,
  fetchModelStats,
  fetchSectionStats,
  fetchCustomerList,
  type Cap,
  type Alert,
  type CapCreate,
} from "@/lib/api";
import { formatSmartCost } from "@/lib/format";
import { cn } from "@/lib/utils";
import { getCached, setCached, getCachedWithMeta } from "@/lib/cache";
import { waitForBackendWarm } from "@/components/BackendWarmer";
import { mark, measure, logCacheStatus, logAuth } from "@/lib/perf";

// ============================================================================
// TYPES
// ============================================================================

type CapType = "global" | "provider" | "model" | "feature" | "agent" | "customer";
type Period = "daily" | "weekly" | "monthly";
type Enforcement = "alert" | "hard_block";

// ============================================================================
// CONFIG
// ============================================================================

const CAP_TYPE_CONFIG: Record<CapType, { icon: React.ReactNode; label: string; color: string }> = {
  global: { icon: <Globe className="w-4 h-4" />, label: "Global", color: "bg-slate-500" },
  provider: { icon: <Server className="w-4 h-4" />, label: "Provider", color: "bg-blue-500" },
  model: { icon: <Cpu className="w-4 h-4" />, label: "Model", color: "bg-purple-500" },
  feature: { icon: <Layers className="w-4 h-4" />, label: "Feature", color: "bg-emerald-500" },
  agent: { icon: <Layers className="w-4 h-4" />, label: "Agent", color: "bg-orange-500" },
  customer: { icon: <Users className="w-4 h-4" />, label: "Customer", color: "bg-pink-500" },
};

const PERIOD_LABELS: Record<Period, string> = {
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

const ENFORCEMENT_CONFIG: Record<Enforcement, { label: string; icon: React.ReactNode; color: string }> = {
  alert: { label: "Alert Only", icon: <Bell className="w-4 h-4" />, color: "bg-amber-500" },
  hard_block: { label: "Hard Block", icon: <Shield className="w-4 h-4" />, color: "bg-rose-500" },
};

// ============================================================================
// CREATE CAP DIALOG
// ============================================================================

interface CreateCapDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (cap: CapCreate) => Promise<void>;
  providers: string[];
  models: string[];
  features: string[];
  customers: string[];
}

type SubScope = "all" | "provider" | "model";

function CreateCapDialog({ open, onOpenChange, onSubmit, providers, models, features, customers }: CreateCapDialogProps) {
  const [capType, setCapType] = useState<CapType>("global");
  const [targetName, setTargetName] = useState("");
  const [subScope, setSubScope] = useState<SubScope>("all");  // For customer caps
  const [subTarget, setSubTarget] = useState("");  // Provider/model for customer caps
  const [limitAmount, setLimitAmount] = useState("100");
  const [period, setPeriod] = useState<Period>("monthly");
  const [enforcement, setEnforcement] = useState<Enforcement>("alert");
  const [alertThreshold, setAlertThreshold] = useState("80");
  const [alertEmail, setAlertEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetOptions = capType === "provider" ? providers 
    : capType === "model" ? models 
    : capType === "feature" || capType === "agent" ? features
    : capType === "customer" ? customers
    : [];

  const subTargetOptions = subScope === "provider" ? providers
    : subScope === "model" ? models
    : [];

  const resetForm = () => {
    setCapType("global");
    setTargetName("");
    setSubScope("all");
    setSubTarget("");
    setLimitAmount("100");
    setPeriod("monthly");
    setEnforcement("alert");
    setAlertThreshold("80");
    setAlertEmail("");
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!limitAmount || parseFloat(limitAmount) <= 0) {
      setError("Please enter a valid limit amount greater than 0");
      return;
    }
    
    if (capType !== "global" && !targetName) {
      setError(`Please select a ${capType}`);
      return;
    }

    // Validate sub_target for customer caps with specific scope
    if (capType === "customer" && subScope !== "all" && !subTarget) {
      setError(`Please select a ${subScope}`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Map feature to agent for backend compatibility
      const backendCapType = capType === "feature" ? "agent" : capType;
      
      const capData: CapCreate = {
        cap_type: backendCapType,
        target_name: capType === "global" ? null : targetName,
        sub_scope: capType === "customer" && subScope !== "all" ? subScope : null,
        sub_target: capType === "customer" && subScope !== "all" ? subTarget : null,
        limit_amount: parseFloat(limitAmount),
        period,
        enforcement,
        alert_threshold: parseFloat(alertThreshold) / 100,
        alert_email: alertEmail || null,
      };
      
      console.log("[CreateCap] Submitting cap:", capData);
      
      await onSubmit(capData);
      resetForm();
      onOpenChange(false);
    } catch (err) {
      console.error("[CreateCap] Error:", err);
      setError(err instanceof Error ? err.message : "Failed to create cap");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      if (!isOpen) resetForm();
      onOpenChange(isOpen);
    }}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-500" />
              Create Spending Cap
            </DialogTitle>
            <DialogDescription>
              Set a spending limit with alerts or hard blocks when exceeded.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Cap Type */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="cap-type" className="text-right">Type</Label>
              <Select value={capType} onValueChange={(v) => { setCapType(v as CapType); setTargetName(""); }}>
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CAP_TYPE_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      <span className="flex items-center gap-2">
                        {config.icon}
                        {config.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Target (if not global) */}
            {capType !== "global" && (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="target" className="text-right">
                  {capType === "customer" ? "Customer" : "Target"}
                </Label>
                {targetOptions.length > 0 ? (
                  <Select value={targetName} onValueChange={setTargetName}>
                    <SelectTrigger className="col-span-3">
                      <SelectValue placeholder={`Select ${capType}...`} />
                    </SelectTrigger>
                    <SelectContent>
                      {targetOptions.map((opt) => (
                        <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id="target"
                    value={targetName}
                    onChange={(e) => setTargetName(e.target.value)}
                    placeholder={`Enter ${capType} name...`}
                    className="col-span-3"
                  />
                )}
              </div>
            )}

            {/* Sub-scope for customer caps */}
            {capType === "customer" && (
              <>
                <div className="grid grid-cols-4 items-center gap-4">
                  <Label htmlFor="sub-scope" className="text-right">Scope</Label>
                  <Select value={subScope} onValueChange={(v) => { setSubScope(v as SubScope); setSubTarget(""); }}>
                    <SelectTrigger className="col-span-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Usage (total for customer)</SelectItem>
                      <SelectItem value="provider">Specific Provider</SelectItem>
                      <SelectItem value="model">Specific Model</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Sub-target (provider/model) for customer caps */}
                {subScope !== "all" && (
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="sub-target" className="text-right">
                      {subScope === "provider" ? "Provider" : "Model"}
                    </Label>
                    {subTargetOptions.length > 0 ? (
                      <Select value={subTarget} onValueChange={setSubTarget}>
                        <SelectTrigger className="col-span-3">
                          <SelectValue placeholder={`Select ${subScope}...`} />
                        </SelectTrigger>
                        <SelectContent>
                          {subTargetOptions.map((opt) => (
                            <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        id="sub-target"
                        value={subTarget}
                        onChange={(e) => setSubTarget(e.target.value)}
                        placeholder={`Enter ${subScope} name...`}
                        className="col-span-3"
                      />
                    )}
                  </div>
                )}
              </>
            )}

            {/* Limit Amount */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="limit" className="text-right">Limit ($)</Label>
              <Input
                id="limit"
                type="number"
                step="any"
                min="0"
                value={limitAmount}
                onChange={(e) => setLimitAmount(e.target.value)}
                placeholder="100.00"
                className="col-span-3"
                required
              />
            </div>

            {/* Period */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="period" className="text-right">Period</Label>
              <Select value={period} onValueChange={(v) => setPeriod(v as Period)}>
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(PERIOD_LABELS).map(([key, label]) => (
                    <SelectItem key={key} value={key}>{label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Enforcement */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="enforcement" className="text-right">Action</Label>
              <Select value={enforcement} onValueChange={(v) => setEnforcement(v as Enforcement)}>
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(ENFORCEMENT_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      <span className="flex items-center gap-2">
                        {config.icon}
                        {config.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Alert Threshold */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="threshold" className="text-right">Alert at %</Label>
              <Input
                id="threshold"
                type="number"
                min="1"
                max="100"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(e.target.value)}
                placeholder="80"
                className="col-span-3"
              />
            </div>

            {/* Send Alerts To (renamed from Alert Email for clarity) */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right text-sm">Send Alerts To</Label>
              <Input
                id="email"
                type="email"
                value={alertEmail}
                onChange={(e) => setAlertEmail(e.target.value)}
                placeholder="your-email@example.com"
                className="col-span-3"
              />
            </div>

            {error && (
              <div className="col-span-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Cap"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ============================================================================
// CAPS TABLE
// ============================================================================

interface CapsTableProps {
  caps: Cap[];
  onDelete: (capId: string) => Promise<void>;
  onToggle: (capId: string, enabled: boolean) => Promise<void>;
}

function CapsTable({ caps, onDelete, onToggle }: CapsTableProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const handleDelete = async (capId: string) => {
    if (!confirm("Are you sure you want to delete this cap?")) return;
    setDeletingId(capId);
    try {
      await onDelete(capId);
    } finally {
      setDeletingId(null);
    }
  };

  const handleToggle = async (capId: string, enabled: boolean) => {
    setTogglingId(capId);
    try {
      await onToggle(capId, enabled);
    } finally {
      setTogglingId(null);
    }
  };

  if (caps.length === 0) {
    return (
      <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl bg-gray-50/50">
        <Shield className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No spending caps</h3>
        <p className="text-gray-500 mb-4 max-w-md mx-auto">
          Create a cap to monitor and control your LLM spending. Get email alerts when you approach your limit.
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-xl overflow-hidden bg-white">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50">
            <TableHead className="w-[140px]">Type</TableHead>
            <TableHead>Target</TableHead>
            <TableHead className="text-right w-[100px]">Limit</TableHead>
            <TableHead className="w-[90px]">Period</TableHead>
            <TableHead className="w-[160px]">Usage</TableHead>
            <TableHead className="w-[120px]">Action</TableHead>
            <TableHead className="text-center w-[80px]">Active</TableHead>
            <TableHead className="w-[60px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {caps.map((cap) => {
            const displayType = cap.cap_type === "agent" ? "feature" : cap.cap_type;
            const config = CAP_TYPE_CONFIG[displayType as CapType] || CAP_TYPE_CONFIG.global;
            const enfConfig = ENFORCEMENT_CONFIG[(cap.enforcement || "alert") as Enforcement] || ENFORCEMENT_CONFIG.alert;
            const usagePercent = Math.min(cap.percentage_used, 100);
            const isOverLimit = cap.percentage_used >= 100;
            const isWarning = cap.percentage_used >= (cap.alert_threshold * 100);

            return (
              <TableRow key={cap.id} className={cn(isOverLimit && "bg-rose-50")}>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className={cn("p-1.5 rounded-md text-white", config.color)}>
                      {config.icon}
                    </span>
                    <span className="font-medium text-sm">{config.label}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="space-y-0.5">
                    <span className="font-mono text-sm text-gray-700">
                      {cap.target_name || "All"}
                    </span>
                    {/* Show sub-scope for customer caps */}
                    {cap.cap_type === "customer" && cap.sub_scope && cap.sub_target && (
                      <div className="text-xs text-gray-500">
                        {cap.sub_scope}: {cap.sub_target}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-semibold tabular-nums">
                  {formatSmartCost(cap.limit_amount)}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="capitalize text-xs">
                    {cap.period}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className={cn(
                        isOverLimit ? "text-rose-600 font-medium" : isWarning ? "text-amber-600" : "text-gray-600"
                      )}>
                        {formatSmartCost(cap.current_spend)}
                      </span>
                      <span className="text-gray-500">
                        {usagePercent.toFixed(0)}%
                      </span>
                    </div>
                    <Progress 
                      value={usagePercent} 
                      className={cn(
                        "h-2",
                        isOverLimit && "[&>div]:bg-rose-500",
                        isWarning && !isOverLimit && "[&>div]:bg-amber-500"
                      )}
                    />
                  </div>
                </TableCell>
                <TableCell>
                  <Badge 
                    variant="secondary" 
                    className={cn(
                      "flex items-center gap-1 w-fit text-xs",
                      (cap.enforcement || "alert") === "hard_block" && "bg-rose-100 text-rose-700"
                    )}
                  >
                    {enfConfig.icon}
                    <span>{enfConfig.label}</span>
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  <Switch
                    checked={cap.enabled}
                    onCheckedChange={(checked) => handleToggle(cap.id, checked)}
                    disabled={togglingId === cap.id}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(cap.id)}
                    disabled={deletingId === cap.id}
                    className="text-gray-400 hover:text-rose-600 h-8 w-8 p-0"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}

// ============================================================================
// ALERTS LIST
// ============================================================================

interface AlertsListProps {
  alerts: Alert[];
}

function AlertsList({ alerts }: AlertsListProps) {
  if (alerts.length === 0) {
    return (
      <div className="text-center py-16 border border-dashed border-gray-200 rounded-xl bg-gray-50/50">
        <Bell className="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 mb-2">No alerts yet</h3>
        <p className="text-gray-500 max-w-md mx-auto">
          Alerts will appear here when your spending approaches or exceeds your caps.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={cn(
            "flex items-start gap-4 p-4 rounded-xl border",
            alert.alert_type === "exceeded" ? "bg-rose-50 border-rose-200" : "bg-amber-50 border-amber-200"
          )}
        >
          <AlertTriangle className={cn(
            "w-6 h-6 flex-shrink-0 mt-0.5",
            alert.alert_type === "exceeded" ? "text-rose-500" : "text-amber-500"
          )} />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900">
              {alert.alert_type === "exceeded" ? "Limit Exceeded" : "Threshold Warning"}
            </p>
            <p className="text-sm text-gray-600 mt-1">
              <span className="font-medium capitalize">{alert.target_type}</span>: {alert.target_name || "Global"} — 
              <span className="font-semibold"> {formatSmartCost(alert.current_spend)}</span> / {formatSmartCost(alert.cap_limit)} 
              <span className="text-gray-500"> ({alert.percentage.toFixed(0)}%)</span>
            </p>
            <p className="text-xs text-gray-400 mt-2">
              {new Date(alert.created_at).toLocaleString()}
            </p>
          </div>
          {alert.email_sent && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <div className="flex items-center gap-1 text-xs text-gray-500 bg-white px-2 py-1 rounded-full border">
                    <Mail className="w-3 h-3" />
                    Sent
                  </div>
                </TooltipTrigger>
                <TooltipContent>Email notification sent</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

interface CapsCacheData {
  caps: Cap[];
  alerts: Alert[];
  providers: string[];
  models: string[];
  features: string[];
  customers: string[];
}

const CAPS_CACHE_KEY = "caps-data";

// TIMING INSTRUMENTATION
const CAPS_MOUNT_TIME = typeof window !== 'undefined' ? performance.now() : 0;
if (typeof window !== 'undefined') {
  console.log('[Caps] PAGE MOUNT at', CAPS_MOUNT_TIME.toFixed(0), 'ms');
}

export default function CapsPage() {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  // STABLE USER ID: Use user.id instead of user object to prevent effect re-runs
  const userId = user?.id;
  
  // Log Clerk hydration timing
  useEffect(() => {
    if (isLoaded) {
      const now = performance.now();
      console.log('[Caps] CLERK HYDRATED at', now.toFixed(0), 'ms (took', (now - CAPS_MOUNT_TIME).toFixed(0), 'ms from mount)');
    }
  }, [isLoaded]);
  
  // Refs for fetch management
  const fetchInProgressRef = useRef(false);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const hasLoadedRef = useRef(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // SYNC CACHE INIT: Read cache INSIDE useState initializers
  // For caps, we check cache existence (caps can be empty legitimately)
  const [caps, setCaps] = useState<Cap[]>(() => {
    if (typeof window === 'undefined') return [];
    const cached = getCached<CapsCacheData>(CAPS_CACHE_KEY);
    console.log('[Caps] useState init caps, cacheExists:', cached !== null);
    if (cached !== null) hasLoadedRef.current = true;
    return cached?.caps ?? [];
  });
  
  const [alerts, setAlerts] = useState<Alert[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<CapsCacheData>(CAPS_CACHE_KEY)?.alerts ?? [];
  });
  
  const [providers, setProviders] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<CapsCacheData>(CAPS_CACHE_KEY)?.providers ?? [];
  });
  
  const [models, setModels] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<CapsCacheData>(CAPS_CACHE_KEY)?.models ?? [];
  });
  
  const [features, setFeatures] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<CapsCacheData>(CAPS_CACHE_KEY)?.features ?? [];
  });
  
  const [customers, setCustomers] = useState<string[]>(() => {
    if (typeof window === 'undefined') return [];
    return getCached<CapsCacheData>(CAPS_CACHE_KEY)?.customers ?? [];
  });
  
  const [loading, setLoading] = useState(() => {
    if (typeof window === 'undefined') return true;
    const cached = getCached<CapsCacheData>(CAPS_CACHE_KEY);
    const hasCache = cached !== null;
    console.log('[Caps] useState init loading, hasCache:', hasCache);
    return !hasCache;
  });
  
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"caps" | "alerts">("caps");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const loadData = useCallback(async (forceRefresh = false): Promise<boolean> => {
    mark('caps-loadData');
    logAuth('Caps', isLoaded, isSignedIn, !!user);
    
    if (!isLoaded) {
      console.log('[Caps] loadData DEFER: isLoaded=false - scheduling retry');
      // Schedule a retry when auth becomes ready - don't block UI
      if (!retryTimeoutRef.current && mountedRef.current) {
        retryTimeoutRef.current = setTimeout(() => {
          retryTimeoutRef.current = null;
          if (mountedRef.current) loadData(forceRefresh);
        }, 100); // Short retry - Clerk should hydrate quickly
      }
      return false;
    }
    
    if (!isSignedIn || !user) {
      console.log('[Caps] loadData ABORT: not signed in');
      if (!mountedRef.current) return false;
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
    measure('caps-auth-ready', 'caps-loadData');
    
    if (fetchInProgressRef.current) return false;
    
    const cache = getCachedWithMeta<CapsCacheData>(CAPS_CACHE_KEY);
    logCacheStatus('Caps', CAPS_CACHE_KEY, cache.exists, cache.isStale);
    if (!forceRefresh && cache.exists && !cache.isStale) {
      hasLoadedRef.current = true;
      if (mountedRef.current) setLoading(false);
      return false;
    }
    
    fetchInProgressRef.current = true;
    
    // B) FIX: Only set loading if we haven't loaded yet
    const isBackground = !forceRefresh && cache.exists;
    if (!isBackground && !hasLoadedRef.current) {
      if (mountedRef.current) setLoading(true);
    } else if (!isBackground) {
      if (mountedRef.current) setIsRefreshing(true);
    }
    
    try {
      mark('caps-getToken');
      const tokenStart = Date.now();
      
      // Add timeout to getToken - 2s max (Clerk should be fast when hydrated)
      let token: string | null = null;
      try {
        const tokenPromise = getToken();
        const timeoutPromise = new Promise<null>((_, reject) => 
          setTimeout(() => reject(new Error('getToken timeout after 2s')), 2000)
        );
        token = await Promise.race([tokenPromise, timeoutPromise]);
      } catch (e) {
        console.warn('[Caps] getToken timed out after 2s - will retry');
        token = null;
      }
      const tokenDuration = Date.now() - tokenStart;
      const sinceMount = (performance.now() - CAPS_MOUNT_TIME).toFixed(0);
      console.log('[Caps] getToken took:', tokenDuration, 'ms, token:', token ? 'present' : 'null', '(', sinceMount, 'ms since mount)');
      measure('caps-getToken');
      
      // Limit retries to prevent infinite loop
      const retryCountKey = '__caps_retry_count__';
      const retryCount = (window as any)[retryCountKey] || 0;
      
      if (!token) {
        if (retryCount >= 3) {
          console.error('[Caps] Max retries (3) reached - giving up');
          (window as any)[retryCountKey] = 0;
          fetchInProgressRef.current = false;
          if (!hasLoadedRef.current && mountedRef.current) setLoading(false);
          return false;
        }
        
        (window as any)[retryCountKey] = retryCount + 1;
        console.log('[Caps] No token - scheduling retry', retryCount + 1, '/3 in 300ms');
        fetchInProgressRef.current = false;
        if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) loadData(forceRefresh);
        }, 300);
        return false;
      }
      
      (window as any)[retryCountKey] = 0;
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }

      // Note: Not awaiting waitForBackendWarm() - API requests wake Railway directly
      
      mark('caps-fetch');
      console.log('[Caps] Starting fetch with token:', token ? 'present' : 'MISSING');
      
      // Track whether each fetch succeeded (200) vs failed (error caught)
      let fetchSucceeded = true;
      const [capsData, alertsData, providersData, modelsData, sectionsData, customersData] = await Promise.all([
        fetchCaps(token).catch((err) => { console.error("[Caps] fetchCaps error:", err.message); fetchSucceeded = false; return []; }),
        fetchAlerts(100, token).catch((err) => { console.error("[Caps] fetchAlerts error:", err.message); fetchSucceeded = false; return []; }),
        fetchProviderStats(24 * 30, null, null, token).catch((e) => { console.error('[Caps] fetchProviderStats error:', e.message); return []; }), // Stats failures are OK
        fetchModelStats(24 * 30, null, null, token).catch((e) => { console.error('[Caps] fetchModelStats error:', e.message); return []; }),
        fetchSectionStats(24 * 30, null, null, token).catch((e) => { console.error('[Caps] fetchSectionStats error:', e.message); return []; }),
        fetchCustomerList(token).catch((e) => { console.error('[Caps] fetchCustomerList error:', e.message); return []; }),
      ]);
      console.log('[Caps] Fetch complete:', { 
        fetchSucceeded,
        caps: capsData?.length ?? 0, 
        alerts: alertsData?.length ?? 0,
        providers: providersData?.length ?? 0,
        models: modelsData?.length ?? 0,
        sections: sectionsData?.length ?? 0,
        customers: customersData?.length ?? 0,
      });
      measure('caps-fetch');
      
      const providersList = [...new Set(providersData.map(p => p.provider))]
        .filter(p => p !== "internal" && p !== "unknown");
      const modelsList = [...new Set(modelsData.map(m => m.model))];
      const featuresList = [...new Set(sectionsData.map(s => s.section))]
        .filter(s => s !== "main" && s !== "default");
      const customersList = customersData.filter(c => c !== null && c !== "");
      
      // E) FIX: Check mounted before setState
      if (!mountedRef.current) return false;
      
      setCaps(capsData);
      setAlerts(alertsData);
      setProviders(providersList);
      setModels(modelsList);
      setFeatures(featuresList);
      setCustomers(customersList);
      setLastRefresh(new Date());
      setError(null);
      
      // B) FIX: Lock loading after first success
      hasLoadedRef.current = true;
      setLoading(false);
      setIsRefreshing(false);
      
      // Cache successful responses (even if empty) to prevent refetching on navigation
      if (fetchSucceeded) {
      setCached<CapsCacheData>(CAPS_CACHE_KEY, {
        caps: capsData,
        alerts: alertsData,
        providers: providersList,
        models: modelsList,
        features: featuresList,
        customers: customersList,
      });
        console.log('[Caps] Cache written:', { caps: capsData.length, alerts: alertsData.length, customers: customersList.length });
      } else {
        console.log('[Caps] NOT caching - fetch failed');
      }
      
      fetchInProgressRef.current = false;
      return true;
    } catch (err) {
      console.error("[CapsPage] Error loading data:", err);
      if (!mountedRef.current) return false;
      setError(err instanceof Error ? err.message : "Failed to load data");
      fetchInProgressRef.current = false;
      setIsRefreshing(false);
      if (!hasLoadedRef.current) setLoading(false);
      return false;
    }
  }, [isLoaded, isSignedIn, userId, getToken]);

  // Effect: Trigger fetch immediately - loadData handles auth retry internally
  useEffect(() => {
    const mountTime = (performance.now() - CAPS_MOUNT_TIME).toFixed(0);
    console.log('[Caps] Effect running at', mountTime, 'ms since mount:', { isLoaded, isSignedIn, hasUser: !!user });
    
    const cache = getCachedWithMeta<CapsCacheData>(CAPS_CACHE_KEY);
    if (cache.exists && !cache.isStale) {
      console.log('[Caps] Effect: using fresh cache, skipping fetch');
      hasLoadedRef.current = true;
      if (mountedRef.current) setLoading(false);
      return;
    }
    
    // IMMEDIATE LOAD: Call loadData now - it handles auth retry internally
    console.log('[Caps] Effect: calling loadData immediately (', mountTime, 'ms since mount)');
    loadData(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, isSignedIn, userId]);
  
  // E) FIX: Cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !userId) return;
    
    const startInterval = () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        if (!document.hidden && mountedRef.current) loadData(false);
      }, 120000);
    };
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
      } else {
        const cache = getCachedWithMeta<CapsCacheData>(CAPS_CACHE_KEY);
        if (cache.isStale && mountedRef.current) loadData(false);
        startInterval();
      }
    };
    
    startInterval();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoaded, isSignedIn, userId]);

  const handleCreateCap = async (capData: CapCreate) => {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    
    console.log("[CapsPage] Creating cap with data:", capData);
    await createCap(capData, token);
    await loadData(true); // Force refresh after mutation
  };

  const handleDeleteCap = async (capId: string) => {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    
    await deleteCap(capId, token);
    await loadData(true);
  };

  const handleToggleCap = async (capId: string, enabled: boolean) => {
    const token = await getToken();
    if (!token) throw new Error("Not authenticated");
    
    await updateCap(capId, { enabled }, token);
    await loadData(true);
  };

  const alertCount24h = alerts.filter(a => 
    new Date(a.created_at) > new Date(Date.now() - 24 * 60 * 60 * 1000)
  ).length;

  // A) FIX: Data presence overrides all other states
  // For caps, we check if we've ever loaded (caps can be empty intentionally)
  const hasLoadedCaps = hasLoadedRef.current;
  
  // TIMING: Log first meaningful render
  useEffect(() => {
    const now = performance.now();
    console.log('[Caps] FIRST RENDER at', now.toFixed(0), 'ms (', (now - CAPS_MOUNT_TIME).toFixed(0), 'ms from mount)', { hasLoadedCaps, loading });
  }, []); // Only on mount
  
  // DEBUG: Log render state
  console.log('[Caps] RENDER:', { hasLoadedCaps, loading, isRefreshing, capsLen: caps.length });
  
  // Error state - only show if never loaded data
  if (error && !hasLoadedCaps) {
    return (
      <ProtectedLayout>
        <div className="p-6">
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-rose-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-rose-700 font-medium">{error}</p>
              <p className="text-sm text-rose-600 mt-1">
                Please try again or check your connection.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadData(true)}
                className="mt-3 text-rose-600 border-rose-200 hover:bg-rose-100"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    );
  }

  // A) FIX: Loading skeleton ONLY if never loaded AND loading
  if (!hasLoadedCaps && loading) {
    return (
      <ProtectedLayout>
        <div className="p-6 space-y-6">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-[400px] rounded-xl" />
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
              <div className="p-2 bg-rose-100 rounded-lg">
                <Shield className="w-6 h-6 text-rose-600" />
              </div>
              Spending Caps & Alerts
            </h1>
            <p className="text-gray-500 mt-1">
              Set spending limits and receive alerts when thresholds are exceeded.
              <span className="text-xs text-gray-400 ml-2">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" onClick={() => loadData(true)} disabled={isRefreshing}>
              <RefreshCw className={cn("w-4 h-4 mr-2", isRefreshing && "animate-spin")} />
              {isRefreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              Add Cap
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <TabsList className="grid w-fit grid-cols-2 h-10">
            <TabsTrigger value="caps" className="gap-2 px-6">
              <Shield className="w-4 h-4" />
              Caps ({caps.length})
            </TabsTrigger>
            <TabsTrigger value="alerts" className="gap-2 px-6">
              <Bell className="w-4 h-4" />
              Alerts
              {alertCount24h > 0 && (
                <span className="px-1.5 py-0.5 text-xs bg-amber-100 text-amber-700 rounded-full ml-1">
                  {alertCount24h}
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="caps" className="mt-6">
            <CapsTable caps={caps} onDelete={handleDeleteCap} onToggle={handleToggleCap} />
          </TabsContent>

          <TabsContent value="alerts" className="mt-6">
            <AlertsList alerts={alerts} />
          </TabsContent>
        </Tabs>

        {/* Help Section */}
        <div className="bg-gray-50 rounded-xl p-6 space-y-4 mt-8">
          <h3 className="font-semibold text-gray-900">How Caps Work</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                <Globe className="w-4 h-4 text-slate-500" />
                Cap Types
              </h4>
              <ul className="space-y-1 text-gray-600">
                <li>• <strong>Global:</strong> All API calls</li>
                <li>• <strong>Provider:</strong> OpenAI, Anthropic, etc.</li>
                <li>• <strong>Model:</strong> gpt-4o, claude-3, etc.</li>
                <li>• <strong>Feature:</strong> Your labeled features</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-500" />
                Alert Only
              </h4>
              <p className="text-gray-600">
                Sends an email notification when spending reaches your threshold. API calls continue to work.
              </p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-500" />
                Hard Block
              </h4>
              <p className="text-gray-600">
                Blocks API calls when limit is exceeded. Requires SDK integration for enforcement.
              </p>
            </div>
          </div>
        </div>

        {/* Create Dialog */}
        <CreateCapDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          onSubmit={handleCreateCap}
          providers={providers}
          models={models}
          features={features}
          customers={customers}
        />
      </div>
    </ProtectedLayout>
  );
}

