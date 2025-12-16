"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";

// ============================================================================
// TYPES
// ============================================================================

export type DateRange = "24h" | "7d" | "30d" | "90d";

export interface AnalyticsFilters {
  dateRange: DateRange;
  providers: string[];
  models: string[];
  features: string[];
  compareEnabled: boolean;
  groupBy: 'provider' | 'model' | 'feature' | null;
}

export interface AnalyticsContextType {
  // Filters
  filters: AnalyticsFilters;
  setFilters: (filters: Partial<AnalyticsFilters>) => void;
  resetFilters: () => void;
  
  // Convenience setters
  setDateRange: (range: DateRange) => void;
  setProviders: (providers: string[]) => void;
  setModels: (models: string[]) => void;
  setFeatures: (features: string[]) => void;
  toggleCompare: () => void;
  setGroupBy: (groupBy: 'provider' | 'model' | 'feature' | null) => void;
  
  // URL sync
  syncToUrl: () => void;
  
  // Computed values
  dateRangeHours: number;
  dateRangeDays: number;
  hasActiveFilters: boolean;
}

// ============================================================================
// DEFAULT VALUES
// ============================================================================

const DEFAULT_FILTERS: AnalyticsFilters = {
  dateRange: "7d",
  providers: [],
  models: [],
  features: [],
  compareEnabled: false,
  groupBy: null,
};

// ============================================================================
// CONTEXT
// ============================================================================

const AnalyticsContext = createContext<AnalyticsContextType | null>(null);

// ============================================================================
// HELPERS
// ============================================================================

function dateRangeToHours(range: DateRange): number {
  switch (range) {
    case "24h": return 24;
    case "7d": return 7 * 24;
    case "30d": return 30 * 24;
    case "90d": return 90 * 24;
  }
}

function dateRangeToDays(range: DateRange): number {
  switch (range) {
    case "24h": return 1;
    case "7d": return 7;
    case "30d": return 30;
    case "90d": return 90;
  }
}

function parseArrayParam(value: string | null): string[] {
  if (!value) return [];
  return value.split(',').filter(Boolean);
}

function serializeArrayParam(arr: string[]): string | null {
  if (arr.length === 0) return null;
  return arr.join(',');
}

// ============================================================================
// PROVIDER
// ============================================================================

interface AnalyticsProviderProps {
  children: ReactNode;
  defaultFilters?: Partial<AnalyticsFilters>;
}

export function AnalyticsProvider({ children, defaultFilters }: AnalyticsProviderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  
  // Initialize filters from URL or defaults
  const [filters, setFiltersState] = useState<AnalyticsFilters>(() => {
    const initial = { ...DEFAULT_FILTERS, ...defaultFilters };
    
    // Parse from URL if available (client-side only)
    if (typeof window !== 'undefined') {
      const urlRange = searchParams.get('range');
      if (urlRange && ['24h', '7d', '30d', '90d'].includes(urlRange)) {
        initial.dateRange = urlRange as DateRange;
      }
      
      const urlProviders = searchParams.get('providers');
      if (urlProviders) {
        initial.providers = parseArrayParam(urlProviders);
      }
      
      const urlModels = searchParams.get('models');
      if (urlModels) {
        initial.models = parseArrayParam(urlModels);
      }
      
      const urlFeatures = searchParams.get('features');
      if (urlFeatures) {
        initial.features = parseArrayParam(urlFeatures);
      }
      
      const urlCompare = searchParams.get('compare');
      if (urlCompare === 'true') {
        initial.compareEnabled = true;
      }
      
      const urlGroupBy = searchParams.get('groupBy');
      if (urlGroupBy && ['provider', 'model', 'feature'].includes(urlGroupBy)) {
        initial.groupBy = urlGroupBy as 'provider' | 'model' | 'feature';
      }
    }
    
    return initial;
  });
  
  // Sync filters to URL
  const syncToUrl = useCallback(() => {
    if (typeof window === 'undefined') return;
    
    const params = new URLSearchParams();
    
    // Only add non-default values
    if (filters.dateRange !== DEFAULT_FILTERS.dateRange) {
      params.set('range', filters.dateRange);
    }
    
    const providers = serializeArrayParam(filters.providers);
    if (providers) params.set('providers', providers);
    
    const models = serializeArrayParam(filters.models);
    if (models) params.set('models', models);
    
    const features = serializeArrayParam(filters.features);
    if (features) params.set('features', features);
    
    if (filters.compareEnabled) {
      params.set('compare', 'true');
    }
    
    if (filters.groupBy) {
      params.set('groupBy', filters.groupBy);
    }
    
    const queryString = params.toString();
    const newUrl = queryString ? `${pathname}?${queryString}` : pathname;
    
    // Use replaceState to avoid polluting history
    router.replace(newUrl, { scroll: false });
  }, [filters, pathname, router]);
  
  // Auto-sync to URL when filters change
  useEffect(() => {
    const timeout = setTimeout(syncToUrl, 100);
    return () => clearTimeout(timeout);
  }, [syncToUrl]);
  
  // Update filters
  const setFilters = useCallback((newFilters: Partial<AnalyticsFilters>) => {
    setFiltersState(prev => ({ ...prev, ...newFilters }));
  }, []);
  
  // Reset filters
  const resetFilters = useCallback(() => {
    setFiltersState({ ...DEFAULT_FILTERS, ...defaultFilters });
  }, [defaultFilters]);
  
  // Convenience setters
  const setDateRange = useCallback((range: DateRange) => {
    setFilters({ dateRange: range });
  }, [setFilters]);
  
  const setProviders = useCallback((providers: string[]) => {
    setFilters({ providers });
  }, [setFilters]);
  
  const setModels = useCallback((models: string[]) => {
    setFilters({ models });
  }, [setFilters]);
  
  const setFeatures = useCallback((features: string[]) => {
    setFilters({ features });
  }, [setFilters]);
  
  const toggleCompare = useCallback(() => {
    setFilters({ compareEnabled: !filters.compareEnabled });
  }, [filters.compareEnabled, setFilters]);
  
  const setGroupBy = useCallback((groupBy: 'provider' | 'model' | 'feature' | null) => {
    setFilters({ groupBy });
  }, [setFilters]);
  
  // Computed values
  const dateRangeHours = dateRangeToHours(filters.dateRange);
  const dateRangeDays = dateRangeToDays(filters.dateRange);
  const hasActiveFilters = 
    filters.providers.length > 0 ||
    filters.models.length > 0 ||
    filters.features.length > 0;
  
  const value: AnalyticsContextType = {
    filters,
    setFilters,
    resetFilters,
    setDateRange,
    setProviders,
    setModels,
    setFeatures,
    toggleCompare,
    setGroupBy,
    syncToUrl,
    dateRangeHours,
    dateRangeDays,
    hasActiveFilters,
  };
  
  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
}

// ============================================================================
// HOOK
// ============================================================================

export function useAnalytics() {
  const context = useContext(AnalyticsContext);
  if (!context) {
    throw new Error("useAnalytics must be used within AnalyticsProvider");
  }
  return context;
}

// ============================================================================
// LEGACY COMPATIBILITY
// ============================================================================

// Keep backward compatibility with existing useDateRange hook
export function useDateRange() {
  const context = useContext(AnalyticsContext);
  
  // If no AnalyticsProvider, create a standalone state
  const [standaloneRange, setStandaloneRange] = useState<DateRange>("7d");
  
  if (context) {
    return {
      dateRange: context.filters.dateRange,
      setDateRange: context.setDateRange,
    };
  }
  
  return {
    dateRange: standaloneRange,
    setDateRange: setStandaloneRange,
  };
}

