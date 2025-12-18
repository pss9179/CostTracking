"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
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
  DialogTrigger,
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
import {
  AlertTriangle,
  Bell,
  Plus,
  Trash2,
  Edit2,
  Shield,
  DollarSign,
  Server,
  Cpu,
  Layers,
  Users,
  Globe,
  Mail,
  Check,
  X,
} from "lucide-react";
import {
  fetchCaps,
  fetchAlerts,
  createCap,
  updateCap,
  deleteCap,
  type Cap,
  type Alert,
  type CapCreate,
} from "@/lib/api";
import { formatSmartCost } from "@/lib/format";

// ============================================================================
// TYPES
// ============================================================================

type CapType = "global" | "provider" | "model" | "feature" | "agent" | "customer";
type Period = "daily" | "weekly" | "monthly";
type Enforcement = "alert" | "hard_block";

interface CapsManagerProps {
  className?: string;
  providers?: string[];
  models?: string[];
  features?: string[];
  onCapChange?: () => void;
}

// ============================================================================
// CAP TYPE ICONS & LABELS
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
  providers?: string[];
  models?: string[];
  features?: string[];
}

function CreateCapDialog({ open, onOpenChange, onSubmit, providers, models, features }: CreateCapDialogProps) {
  const [capType, setCapType] = useState<CapType>("global");
  const [targetName, setTargetName] = useState("");
  const [limitAmount, setLimitAmount] = useState("");
  const [period, setPeriod] = useState<Period>("monthly");
  const [enforcement, setEnforcement] = useState<Enforcement>("alert");
  const [alertThreshold, setAlertThreshold] = useState("80");
  const [alertEmail, setAlertEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetOptions = capType === "provider" ? providers 
    : capType === "model" ? models 
    : capType === "feature" || capType === "agent" ? features
    : [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Map feature to agent for backend compatibility
      const backendCapType = capType === "feature" ? "agent" : capType;
      
      await onSubmit({
        cap_type: backendCapType,
        target_name: capType === "global" ? null : targetName,
        limit_amount: parseFloat(limitAmount),
        period,
        enforcement,
        alert_threshold: parseFloat(alertThreshold) / 100,
        alert_email: alertEmail || null,
      });
      onOpenChange(false);
      // Reset form
      setCapType("global");
      setTargetName("");
      setLimitAmount("");
      setPeriod("monthly");
      setEnforcement("alert");
      setAlertThreshold("80");
      setAlertEmail("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create cap");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
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
                <Label htmlFor="target" className="text-right">Target</Label>
                {targetOptions && targetOptions.length > 0 ? (
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

            {/* Limit Amount */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="limit" className="text-right">Limit ($)</Label>
              <Input
                id="limit"
                type="number"
                step="0.01"
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
                min="0"
                max="100"
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(e.target.value)}
                placeholder="80"
                className="col-span-3"
              />
            </div>

            {/* Alert Email */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right">Alert Email</Label>
              <Input
                id="email"
                type="email"
                value={alertEmail}
                onChange={(e) => setAlertEmail(e.target.value)}
                placeholder="alerts@example.com"
                className="col-span-3"
              />
            </div>

            {error && (
              <div className="col-span-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-sm">
                {error}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
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

  const handleDelete = async (capId: string) => {
    setDeletingId(capId);
    try {
      await onDelete(capId);
    } finally {
      setDeletingId(null);
    }
  };

  if (caps.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-gray-200 rounded-xl">
        <Shield className="w-12 h-12 mx-auto text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-1">No spending caps</h3>
        <p className="text-sm text-gray-500 mb-4">
          Create a cap to monitor and control your LLM spending.
        </p>
      </div>
    );
  }

  return (
    <div className="border rounded-xl overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-gray-50">
            <TableHead className="w-[180px]">Type</TableHead>
            <TableHead>Target</TableHead>
            <TableHead className="text-right">Limit</TableHead>
            <TableHead>Period</TableHead>
            <TableHead>Usage</TableHead>
            <TableHead>Action</TableHead>
            <TableHead className="text-center">Enabled</TableHead>
            <TableHead className="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {caps.map((cap) => {
            // Map agent back to feature for display
            const displayType = cap.cap_type === "agent" ? "feature" : cap.cap_type;
            const config = CAP_TYPE_CONFIG[displayType as CapType] || CAP_TYPE_CONFIG.global;
            const enfConfig = ENFORCEMENT_CONFIG[cap.enforcement as Enforcement] || ENFORCEMENT_CONFIG.alert;
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
                    <span className="font-medium">{config.label}</span>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-sm">
                    {cap.target_name || "—"}
                  </span>
                </TableCell>
                <TableCell className="text-right font-semibold tabular-nums">
                  {formatSmartCost(cap.limit_amount)}
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="capitalize">
                    {cap.period}
                  </Badge>
                </TableCell>
                <TableCell className="min-w-[150px]">
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
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Badge 
                          variant="secondary" 
                          className={cn(
                            "flex items-center gap-1",
                            enfConfig.color === "bg-rose-500" && "bg-rose-100 text-rose-700"
                          )}
                        >
                          {enfConfig.icon}
                          <span className="text-xs">{enfConfig.label}</span>
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        {cap.enforcement === "hard_block" 
                          ? "API calls will be blocked when limit is reached"
                          : "You'll receive an alert when threshold is reached"
                        }
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </TableCell>
                <TableCell className="text-center">
                  <Switch
                    checked={cap.enabled}
                    onCheckedChange={(checked) => onToggle(cap.id, checked)}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(cap.id)}
                    disabled={deletingId === cap.id}
                    className="text-gray-400 hover:text-rose-600"
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
      <div className="text-center py-8 text-gray-500">
        <Bell className="w-8 h-8 mx-auto text-gray-300 mb-2" />
        <p className="text-sm">No alerts yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 max-h-[300px] overflow-y-auto">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={cn(
            "flex items-start gap-3 p-3 rounded-lg border",
            alert.alert_type === "exceeded" ? "bg-rose-50 border-rose-200" : "bg-amber-50 border-amber-200"
          )}
        >
          <AlertTriangle className={cn(
            "w-5 h-5 flex-shrink-0 mt-0.5",
            alert.alert_type === "exceeded" ? "text-rose-500" : "text-amber-500"
          )} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900">
              {alert.alert_type === "exceeded" ? "Limit Exceeded" : "Threshold Warning"}
            </p>
            <p className="text-xs text-gray-600 mt-0.5">
              {alert.target_type}: {alert.target_name || "Global"} — 
              {formatSmartCost(alert.current_spend)} / {formatSmartCost(alert.cap_limit)} 
              ({alert.percentage.toFixed(0)}%)
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {new Date(alert.created_at).toLocaleString()}
            </p>
          </div>
          {alert.email_sent && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger>
                  <Mail className="w-4 h-4 text-gray-400" />
                </TooltipTrigger>
                <TooltipContent>Email sent</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function CapsManager({ className, providers, models, features, onCapChange }: CapsManagerProps) {
  const { getToken } = useAuth();
  const [caps, setCaps] = useState<Cap[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"caps" | "alerts">("caps");

  const loadData = useCallback(async () => {
    try {
      const token = await getToken();
      const [capsData, alertsData] = await Promise.all([
        fetchCaps(token || undefined),
        fetchAlerts(50, token || undefined),
      ]);
      setCaps(capsData);
      setAlerts(alertsData);
    } catch (err) {
      console.error("Failed to load caps/alerts:", err);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateCap = async (capData: CapCreate) => {
    const token = await getToken();
    await createCap(capData, token || undefined);
    await loadData();
    onCapChange?.();
  };

  const handleDeleteCap = async (capId: string) => {
    const token = await getToken();
    await deleteCap(capId, token || undefined);
    await loadData();
    onCapChange?.();
  };

  const handleToggleCap = async (capId: string, enabled: boolean) => {
    const token = await getToken();
    await updateCap(capId, { enabled }, token || undefined);
    await loadData();
    onCapChange?.();
  };

  const alertCount = alerts.filter(a => 
    new Date(a.created_at) > new Date(Date.now() - 24 * 60 * 60 * 1000)
  ).length;

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-500" />
            Spending Caps & Alerts
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Set limits and receive alerts when spending exceeds thresholds.
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          Add Cap
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab("caps")}
          className={cn(
            "px-4 py-2 text-sm font-medium rounded-md transition-colors",
            activeTab === "caps" 
              ? "bg-white text-gray-900 shadow-sm" 
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          Caps ({caps.length})
        </button>
        <button
          onClick={() => setActiveTab("alerts")}
          className={cn(
            "px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2",
            activeTab === "alerts" 
              ? "bg-white text-gray-900 shadow-sm" 
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          Alerts
          {alertCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-amber-100 text-amber-700 rounded-full">
              {alertCount}
            </span>
          )}
        </button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="h-48 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        </div>
      ) : activeTab === "caps" ? (
        <CapsTable caps={caps} onDelete={handleDeleteCap} onToggle={handleToggleCap} />
      ) : (
        <AlertsList alerts={alerts} />
      )}

      {/* Create Dialog */}
      <CreateCapDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreateCap}
        providers={providers}
        models={models}
        features={features}
      />
    </div>
  );
}

export default CapsManager;



