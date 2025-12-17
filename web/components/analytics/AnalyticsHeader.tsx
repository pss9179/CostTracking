"use client";

import { useState, useMemo } from "react";
import { Calendar, ChevronDown, X, RotateCcw, ArrowLeftRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { DateRange } from "@/contexts/AnalyticsContext";

// ============================================================================
// TYPES
// ============================================================================

interface AnalyticsHeaderProps {
  // Date range
  dateRange: DateRange;
  onDateRangeChange: (range: DateRange) => void;
  
  // Provider filter
  providers?: string[];
  availableProviders?: string[];
  onProvidersChange?: (providers: string[]) => void;
  
  // Model filter  
  models?: string[];
  availableModels?: string[];
  onModelsChange?: (models: string[]) => void;
  
  // Feature filter
  features?: string[];
  availableFeatures?: string[];
  onFeaturesChange?: (features: string[]) => void;
  
  // Compare toggle
  compareEnabled?: boolean;
  onCompareToggle?: () => void;
  
  // Group by
  groupBy?: 'provider' | 'model' | 'feature' | null;
  onGroupByChange?: (groupBy: 'provider' | 'model' | 'feature' | null) => void;
  showGroupBy?: boolean;
  
  // Reset
  onReset?: () => void;
  hasActiveFilters?: boolean;
  
  // Title (optional)
  title?: string;
  subtitle?: string;
  
  className?: string;
}

// ============================================================================
// DATE RANGE OPTIONS
// ============================================================================

const DATE_RANGE_OPTIONS: { value: DateRange; label: string; shortLabel: string }[] = [
  { value: "1h", label: "Last 1 hour", shortLabel: "1h" },
  { value: "6h", label: "Last 6 hours", shortLabel: "6h" },
  { value: "24h", label: "Last 24 hours", shortLabel: "24h" },
  { value: "3d", label: "Last 3 days", shortLabel: "3d" },
  { value: "7d", label: "Last 7 days", shortLabel: "7d" },
  { value: "14d", label: "Last 2 weeks", shortLabel: "14d" },
  { value: "30d", label: "Last 30 days", shortLabel: "30d" },
  { value: "90d", label: "Last 3 months", shortLabel: "90d" },
  { value: "180d", label: "Last 6 months", shortLabel: "180d" },
  { value: "365d", label: "Last 1 year", shortLabel: "1y" },
];

// ============================================================================
// MULTI-SELECT FILTER
// ============================================================================

interface MultiSelectFilterProps {
  label: string;
  selected: string[];
  available: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
}

function MultiSelectFilter({
  label,
  selected,
  available,
  onChange,
  placeholder = "All",
}: MultiSelectFilterProps) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  
  const filtered = useMemo(() => {
    if (!search) return available;
    const lower = search.toLowerCase();
    return available.filter(item => item.toLowerCase().includes(lower));
  }, [available, search]);
  
  const toggleItem = (item: string) => {
    if (selected.includes(item)) {
      onChange(selected.filter(i => i !== item));
    } else {
      onChange([...selected, item]);
    }
  };
  
  const clearAll = () => {
    onChange([]);
    setOpen(false);
  };
  
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={cn(
            "h-8 gap-1.5 border-slate-200 bg-white hover:bg-slate-50",
            selected.length > 0 && "border-emerald-300 bg-emerald-50 hover:bg-emerald-100"
          )}
        >
          <span className="text-slate-600 text-xs">{label}</span>
          {selected.length > 0 ? (
            <Badge variant="secondary" className="h-5 px-1.5 bg-emerald-100 text-emerald-700 text-xs">
              {selected.length}
            </Badge>
          ) : (
            <span className="text-slate-400 text-xs">{placeholder}</span>
          )}
          <ChevronDown className="h-3 w-3 text-slate-400" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-0" align="start">
        <div className="p-2 border-b border-slate-100">
          <Input
            placeholder={`Search ${label.toLowerCase()}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 text-sm"
          />
        </div>
        <div className="max-h-64 overflow-y-auto p-1">
          {filtered.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">
              No {label.toLowerCase()} found
            </p>
          ) : (
            filtered.map((item) => (
              <button
                key={item}
                onClick={() => toggleItem(item)}
                className={cn(
                  "w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded-md transition-colors",
                  selected.includes(item)
                    ? "bg-emerald-50 text-emerald-700"
                    : "hover:bg-slate-50 text-slate-700"
                )}
              >
                <div
                  className={cn(
                    "w-4 h-4 rounded border flex items-center justify-center",
                    selected.includes(item)
                      ? "bg-emerald-500 border-emerald-500"
                      : "border-slate-300"
                  )}
                >
                  {selected.includes(item) && (
                    <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                      <path d="M10.28 2.28L4 8.56 1.72 6.28a.75.75 0 00-1.06 1.06l3 3a.75.75 0 001.06 0l7-7a.75.75 0 00-1.06-1.06z" />
                    </svg>
                  )}
                </div>
                <span className="capitalize truncate">{item}</span>
              </button>
            ))
          )}
        </div>
        {selected.length > 0 && (
          <div className="p-2 border-t border-slate-100">
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAll}
              className="w-full h-7 text-xs text-slate-500 hover:text-slate-700"
            >
              Clear selection
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function AnalyticsHeader({
  dateRange,
  onDateRangeChange,
  providers = [],
  availableProviders = [],
  onProvidersChange,
  models = [],
  availableModels = [],
  onModelsChange,
  features = [],
  availableFeatures = [],
  onFeaturesChange,
  compareEnabled = false,
  onCompareToggle,
  groupBy,
  onGroupByChange,
  showGroupBy = false,
  onReset,
  hasActiveFilters = false,
  title,
  subtitle,
  className,
}: AnalyticsHeaderProps) {
  const currentRange = DATE_RANGE_OPTIONS.find(o => o.value === dateRange);
  
  return (
    <div className={cn("space-y-3", className)}>
      {/* Title row (optional) */}
      {(title || subtitle) && (
        <div className="flex items-center justify-between">
          <div>
            {title && (
              <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
            )}
            {subtitle && (
              <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>
            )}
          </div>
        </div>
      )}
      
      {/* Filter bar */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Date range selector */}
        <Select value={dateRange} onValueChange={(v) => onDateRangeChange(v as DateRange)}>
          <SelectTrigger className="w-auto h-8 gap-1.5 text-sm border-slate-200 bg-white hover:bg-slate-50">
            <Calendar className="h-3.5 w-3.5 text-slate-400" />
            <SelectValue>
              <span>{currentRange?.label}</span>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {DATE_RANGE_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {/* Divider */}
        <div className="h-4 w-px bg-slate-200" />
        
        {/* Provider filter */}
        {onProvidersChange && availableProviders.length > 0 && (
          <MultiSelectFilter
            label="Provider"
            selected={providers}
            available={availableProviders}
            onChange={onProvidersChange}
          />
        )}
        
        {/* Model filter */}
        {onModelsChange && availableModels.length > 0 && (
          <MultiSelectFilter
            label="Model"
            selected={models}
            available={availableModels}
            onChange={onModelsChange}
          />
        )}
        
        {/* Feature filter */}
        {onFeaturesChange && availableFeatures.length > 0 && (
          <MultiSelectFilter
            label="Feature"
            selected={features}
            available={availableFeatures}
            onChange={onFeaturesChange}
          />
        )}
        
        {/* Compare toggle */}
        {onCompareToggle && (
          <>
            <div className="h-4 w-px bg-slate-200" />
            <Button
              variant="outline"
              size="sm"
              onClick={onCompareToggle}
              className={cn(
                "h-8 gap-1.5 text-xs",
                compareEnabled
                  ? "border-violet-300 bg-violet-50 text-violet-700 hover:bg-violet-100"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
            >
              <ArrowLeftRight className="h-3.5 w-3.5" />
              Compare
            </Button>
          </>
        )}
        
        {/* Group by selector */}
        {showGroupBy && onGroupByChange && (
          <>
            <div className="h-4 w-px bg-slate-200" />
            <Select
              value={groupBy || "none"}
              onValueChange={(v) => onGroupByChange(v === "none" ? null : v as any)}
            >
              <SelectTrigger className="w-auto h-8 gap-1.5 text-sm border-slate-200 bg-white hover:bg-slate-50">
                <span className="text-slate-400 text-xs">Group:</span>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="provider">Provider</SelectItem>
                <SelectItem value="model">Model</SelectItem>
                <SelectItem value="feature">Feature</SelectItem>
              </SelectContent>
            </Select>
          </>
        )}
        
        {/* Active filter badges */}
        {(providers.length > 0 || models.length > 0 || features.length > 0) && (
          <>
            <div className="h-4 w-px bg-slate-200 ml-1" />
            <div className="flex items-center gap-1.5 flex-wrap">
              {providers.map((p) => (
                <Badge
                  key={p}
                  variant="secondary"
                  className="h-6 gap-1 px-2 bg-slate-100 hover:bg-slate-200 cursor-pointer capitalize"
                  onClick={() => onProvidersChange?.(providers.filter(x => x !== p))}
                >
                  {p}
                  <X className="h-3 w-3" />
                </Badge>
              ))}
              {models.slice(0, 3).map((m) => (
                <Badge
                  key={m}
                  variant="secondary"
                  className="h-6 gap-1 px-2 bg-slate-100 hover:bg-slate-200 cursor-pointer"
                  onClick={() => onModelsChange?.(models.filter(x => x !== m))}
                >
                  {m}
                  <X className="h-3 w-3" />
                </Badge>
              ))}
              {models.length > 3 && (
                <Badge variant="secondary" className="h-6 px-2 bg-slate-100">
                  +{models.length - 3} more
                </Badge>
              )}
            </div>
          </>
        )}
        
        {/* Reset button */}
        {hasActiveFilters && onReset && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="h-8 gap-1.5 text-xs text-slate-500 hover:text-slate-700"
          >
            <RotateCcw className="h-3 w-3" />
            Reset
          </Button>
        )}
      </div>
    </div>
  );
}

