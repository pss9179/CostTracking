"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import type { DateRange } from "./AnalyticsContext";

interface GlobalFilters {
  dateRange: DateRange;
  compareEnabled: boolean;
  selectedProviders: string[];
  selectedModels: string[];
  selectedCustomer?: string | null;
}

interface GlobalFiltersContextType {
  filters: GlobalFilters;
  setDateRange: (range: DateRange) => void;
  setCompareEnabled: (enabled: boolean) => void;
  setSelectedProviders: (providers: string[]) => void;
  setSelectedModels: (models: string[]) => void;
  setSelectedCustomer: (customer: string | null) => void;
  clearFilters: () => void;
  applyFilters: (filters: Partial<GlobalFilters>) => void;
}

const defaultFilters: GlobalFilters = {
  dateRange: "7d",
  compareEnabled: false,
  selectedProviders: [],
  selectedModels: [],
  selectedCustomer: null,
};

const GlobalFiltersContext = createContext<GlobalFiltersContextType | undefined>(undefined);

export function GlobalFiltersProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  // Initialize from URL params or defaults
  const [filters, setFilters] = useState<GlobalFilters>(() => {
    const dateRange = (searchParams.get("dateRange") as DateRange) || defaultFilters.dateRange;
    const compareEnabled = searchParams.get("compare") === "true";
    const providers = searchParams.get("providers")?.split(",").filter(Boolean) || [];
    const models = searchParams.get("models")?.split(",").filter(Boolean) || [];
    const customer = searchParams.get("customer") || null;
    
    return {
      dateRange,
      compareEnabled,
      selectedProviders: providers,
      selectedModels: models,
      selectedCustomer: customer,
    };
  });

  // Update URL when filters change
  const updateURL = useCallback((newFilters: GlobalFilters) => {
    const params = new URLSearchParams();
    
    if (newFilters.dateRange !== defaultFilters.dateRange) {
      params.set("dateRange", newFilters.dateRange);
    }
    if (newFilters.compareEnabled) {
      params.set("compare", "true");
    }
    if (newFilters.selectedProviders.length > 0) {
      params.set("providers", newFilters.selectedProviders.join(","));
    }
    if (newFilters.selectedModels.length > 0) {
      params.set("models", newFilters.selectedModels.join(","));
    }
    if (newFilters.selectedCustomer) {
      params.set("customer", newFilters.selectedCustomer);
    }
    
    const queryString = params.toString();
    const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
    router.replace(newUrl, { scroll: false });
  }, [pathname, router]);

  const setDateRange = useCallback((range: DateRange) => {
    setFilters(prev => {
      const newFilters = { ...prev, dateRange: range };
      updateURL(newFilters);
      return newFilters;
    });
  }, [updateURL]);

  const setCompareEnabled = useCallback((enabled: boolean) => {
    setFilters(prev => {
      const newFilters = { ...prev, compareEnabled: enabled };
      updateURL(newFilters);
      return newFilters;
    });
  }, [updateURL]);

  const setSelectedProviders = useCallback((providers: string[]) => {
    setFilters(prev => {
      const newFilters = { ...prev, selectedProviders: providers };
      updateURL(newFilters);
      return newFilters;
    });
  }, [updateURL]);

  const setSelectedModels = useCallback((models: string[]) => {
    setFilters(prev => {
      const newFilters = { ...prev, selectedModels: models };
      updateURL(newFilters);
      return newFilters;
    });
  }, [updateURL]);

  const setSelectedCustomer = useCallback((customer: string | null) => {
    setFilters(prev => {
      const newFilters = { ...prev, selectedCustomer: customer };
      updateURL(newFilters);
      return newFilters;
    });
  }, [updateURL]);

  const clearFilters = useCallback(() => {
    setFilters(defaultFilters);
    router.replace(pathname, { scroll: false });
  }, [pathname, router]);

  const applyFilters = useCallback((newFilters: Partial<GlobalFilters>) => {
    setFilters(prev => {
      const merged = { ...prev, ...newFilters };
      updateURL(merged);
      return merged;
    });
  }, [updateURL]);

  // Sync with URL params on navigation
  useEffect(() => {
    const dateRange = (searchParams.get("dateRange") as DateRange) || defaultFilters.dateRange;
    const compareEnabled = searchParams.get("compare") === "true";
    const providers = searchParams.get("providers")?.split(",").filter(Boolean) || [];
    const models = searchParams.get("models")?.split(",").filter(Boolean) || [];
    const customer = searchParams.get("customer") || null;
    
    setFilters({
      dateRange,
      compareEnabled,
      selectedProviders: providers,
      selectedModels: models,
      selectedCustomer: customer,
    });
  }, [searchParams]);

  return (
    <GlobalFiltersContext.Provider
      value={{
        filters,
        setDateRange,
        setCompareEnabled,
        setSelectedProviders,
        setSelectedModels,
        setSelectedCustomer,
        clearFilters,
        applyFilters,
      }}
    >
      {children}
    </GlobalFiltersContext.Provider>
  );
}

export function useGlobalFilters() {
  const context = useContext(GlobalFiltersContext);
  if (context === undefined) {
    throw new Error("useGlobalFilters must be used within GlobalFiltersProvider");
  }
  return context;
}

