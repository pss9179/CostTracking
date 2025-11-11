"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TimeRangeFilter } from "./TimeRangeFilter";
import { SearchInput } from "./SearchInput";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { Card } from "@/components/ui/card";

export interface FilterState {
  tenant?: string;
  provider?: string;
  model?: string;
  sectionPath?: string;
  agent?: string;
  search?: string;
}

interface FilterBarProps {
  tenants?: string[];
  providers?: string[];
  models?: string[];
  showTenant?: boolean;
  showProvider?: boolean;
  showModel?: boolean;
  showSectionSearch?: boolean;
  showAgentSearch?: boolean;
  showGeneralSearch?: boolean;
  searchPlaceholder?: string;
  onFilterChange?: (filters: FilterState) => void;
}

export function FilterBar({
  tenants = [],
  providers = ["openai", "pinecone", "anthropic"],
  models = [],
  showTenant = true,
  showProvider = true,
  showModel = true,
  showSectionSearch = true,
  showAgentSearch = false,
  showGeneralSearch = false,
  searchPlaceholder = "Search...",
  onFilterChange,
}: FilterBarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Get current filter values from URL
  const currentFilters: FilterState = {
    tenant: searchParams.get("tenant") || undefined,
    provider: searchParams.get("provider") || undefined,
    model: searchParams.get("model") || undefined,
    sectionPath: searchParams.get("sectionPath") || undefined,
    agent: searchParams.get("agent") || undefined,
    search: searchParams.get("search") || undefined,
  };

  const updateFilter = (key: keyof FilterState, value: string | undefined) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
    router.push(`?${params.toString()}`);
    
    if (onFilterChange) {
      const newFilters = { ...currentFilters, [key]: value };
      onFilterChange(newFilters);
    }
  };

  const clearAllFilters = () => {
    const params = new URLSearchParams(searchParams.toString());
    // Keep time range params
    const from = params.get("from");
    const to = params.get("to");
    const preset = params.get("preset");
    
    params.delete("tenant");
    params.delete("provider");
    params.delete("model");
    params.delete("sectionPath");
    params.delete("agent");
    params.delete("search");
    
    router.push(`?${params.toString()}`);
    
    if (onFilterChange) {
      onFilterChange({});
    }
  };

  const hasActiveFilters = Object.values(currentFilters).some((v) => v !== undefined);

  return (
    <Card className="p-4 space-y-4">
      {/* Main Filter Row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Time Range */}
        <TimeRangeFilter />

        {/* Tenant Filter */}
        {showTenant && tenants.length > 0 && (
          <Select
            value={currentFilters.tenant || "all"}
            onValueChange={(value) => updateFilter("tenant", value === "all" ? undefined : value)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Tenants" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Tenants</SelectItem>
              {tenants.map((tenant) => (
                <SelectItem key={tenant} value={tenant}>
                  {tenant}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {/* Provider Filter */}
        {showProvider && (
          <Select
            value={currentFilters.provider || "all"}
            onValueChange={(value) => updateFilter("provider", value === "all" ? undefined : value)}
          >
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="All Providers" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Providers</SelectItem>
              {providers.map((provider) => (
                <SelectItem key={provider} value={provider}>
                  {provider}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {/* General Search */}
        {showGeneralSearch && (
          <SearchInput
            placeholder={searchPlaceholder}
            value={currentFilters.search}
            onChange={(value) => updateFilter("search", value)}
            className="w-[250px]"
          />
        )}

        {/* Advanced Filters Toggle */}
        {(showModel || showSectionSearch || showAgentSearch) && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            Advanced
            {showAdvanced ? (
              <ChevronUp className="ml-2 h-4 w-4" />
            ) : (
              <ChevronDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        )}

        {/* Clear All */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            <X className="mr-2 h-4 w-4" />
            Clear all
          </Button>
        )}
      </div>

      {/* Advanced Filters Row */}
      {showAdvanced && (
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t">
          {/* Model Filter */}
          {showModel && models.length > 0 && (
            <Select
              value={currentFilters.model || "all"}
              onValueChange={(value) => updateFilter("model", value === "all" ? undefined : value)}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Models" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Models</SelectItem>
                {models.map((model) => (
                  <SelectItem key={model} value={model}>
                    {model}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {/* Section Path Search */}
          {showSectionSearch && (
            <SearchInput
              placeholder="Filter by section path..."
              value={currentFilters.sectionPath}
              onChange={(value) => updateFilter("sectionPath", value)}
              className="w-[250px]"
            />
          )}

          {/* Agent Search */}
          {showAgentSearch && (
            <SearchInput
              placeholder="Filter by agent..."
              value={currentFilters.agent}
              onChange={(value) => updateFilter("agent", value)}
              className="w-[200px]"
            />
          )}
        </div>
      )}
    </Card>
  );
}

