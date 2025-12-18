"use client";

import { useGlobalFilters } from "@/contexts/GlobalFiltersContext";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { X, Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DateRange } from "@/contexts/AnalyticsContext";

const DATE_RANGE_OPTIONS: { value: DateRange; label: string }[] = [
  { value: "1h", label: "Last 1 hour" },
  { value: "6h", label: "Last 6 hours" },
  { value: "24h", label: "Last 24 hours" },
  { value: "3d", label: "Last 3 days" },
  { value: "7d", label: "Last 7 days" },
  { value: "2w", label: "Last 2 weeks" },
  { value: "30d", label: "Last 30 days" },
  { value: "3m", label: "Last 3 months" },
  { value: "6m", label: "Last 6 months" },
  { value: "1y", label: "Last year" },
];

export function GlobalFilterBar() {
  const { filters, setDateRange, setCompareEnabled, setSelectedProviders, setSelectedModels, setSelectedCustomer, clearFilters } = useGlobalFilters();

  const hasActiveFilters = 
    filters.compareEnabled || 
    filters.selectedProviders.length > 0 || 
    filters.selectedModels.length > 0 || 
    filters.selectedCustomer !== null;

  return (
    <div className="bg-white border-b px-6 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 flex-1">
        <Filter className="w-4 h-4 text-gray-400" />
        
        {/* Date Range */}
        <Select value={filters.dateRange} onValueChange={(v) => setDateRange(v as DateRange)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DATE_RANGE_OPTIONS.map(opt => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Compare Toggle */}
        <Button
          variant={filters.compareEnabled ? "default" : "outline"}
          size="sm"
          onClick={() => setCompareEnabled(!filters.compareEnabled)}
        >
          Compare
        </Button>

        {/* Active Filters */}
        {filters.selectedProviders.length > 0 && (
          <div className="flex items-center gap-1">
            {filters.selectedProviders.map(provider => (
              <Badge key={provider} variant="secondary" className="gap-1">
                {provider}
                <X 
                  className="w-3 h-3 cursor-pointer" 
                  onClick={() => setSelectedProviders(filters.selectedProviders.filter(p => p !== provider))}
                />
              </Badge>
            ))}
          </div>
        )}

        {filters.selectedModels.length > 0 && (
          <div className="flex items-center gap-1">
            {filters.selectedModels.map(model => (
              <Badge key={model} variant="secondary" className="gap-1">
                {model}
                <X 
                  className="w-3 h-3 cursor-pointer" 
                  onClick={() => setSelectedModels(filters.selectedModels.filter(m => m !== model))}
                />
              </Badge>
            ))}
          </div>
        )}

        {filters.selectedCustomer && (
          <Badge variant="secondary" className="gap-1">
            Customer: {filters.selectedCustomer}
            <X 
              className="w-3 h-3 cursor-pointer" 
              onClick={() => setSelectedCustomer(null)}
            />
          </Badge>
        )}
      </div>

      {hasActiveFilters && (
        <Button variant="ghost" size="sm" onClick={clearFilters}>
          Clear Filters
        </Button>
      )}
    </div>
  );
}

