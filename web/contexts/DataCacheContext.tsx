"use client";

import React, { createContext, useContext, useRef, useCallback } from "react";

// Simple in-memory cache that persists across page navigations
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  key: string;
}

interface DataCacheContextType {
  get: <T>(key: string) => T | null;
  set: <T>(key: string, data: T) => void;
  getTimestamp: (key: string) => number | null;
  invalidate: (key: string) => void;
  clear: () => void;
}

const DataCacheContext = createContext<DataCacheContextType | null>(null);

// Cache duration: 5 minutes (data is still shown but marked as stale after this)
const CACHE_DURATION = 5 * 60 * 1000;

export function DataCacheProvider({ children }: { children: React.ReactNode }) {
  // Use ref to persist cache across re-renders without causing re-renders
  const cacheRef = useRef<Map<string, CacheEntry<unknown>>>(new Map());

  const get = useCallback(<T,>(key: string): T | null => {
    const entry = cacheRef.current.get(key);
    if (!entry) return null;
    return entry.data as T;
  }, []);

  const set = useCallback(<T,>(key: string, data: T) => {
    cacheRef.current.set(key, {
      data,
      timestamp: Date.now(),
      key,
    });
  }, []);

  const getTimestamp = useCallback((key: string): number | null => {
    const entry = cacheRef.current.get(key);
    return entry?.timestamp ?? null;
  }, []);

  const invalidate = useCallback((key: string) => {
    cacheRef.current.delete(key);
  }, []);

  const clear = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  return (
    <DataCacheContext.Provider value={{ get, set, getTimestamp, invalidate, clear }}>
      {children}
    </DataCacheContext.Provider>
  );
}

export function useDataCache() {
  const context = useContext(DataCacheContext);
  if (!context) {
    throw new Error("useDataCache must be used within a DataCacheProvider");
  }
  return context;
}

// Hook for cached data fetching with stale-while-revalidate pattern
export function useCachedData<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: {
    staleTime?: number; // How long before data is considered stale (default: 30s)
    enabled?: boolean;  // Whether to enable fetching
  } = {}
) {
  const { staleTime = 30000, enabled = true } = options;
  const cache = useDataCache();
  
  const [data, setData] = React.useState<T | null>(() => cache.get<T>(key));
  const [isLoading, setIsLoading] = React.useState(!data);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const fetchData = useCallback(async (isBackground = false) => {
    if (!enabled) return;
    
    try {
      if (!isBackground) {
        // Only show full loading if we have no cached data
        if (!cache.get(key)) {
          setIsLoading(true);
        } else {
          setIsRefreshing(true);
        }
      } else {
        setIsRefreshing(true);
      }
      
      const result = await fetcher();
      cache.set(key, result);
      setData(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
      // Don't clear data on error - show stale data
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [key, fetcher, enabled, cache]);

  // Check if data is stale
  const timestamp = cache.getTimestamp(key);
  const isStale = timestamp ? Date.now() - timestamp > staleTime : true;

  // Initial fetch or refetch if stale
  React.useEffect(() => {
    if (enabled && isStale) {
      fetchData(!!data); // Background fetch if we have data
    }
  }, [enabled, isStale, fetchData, data]);

  return {
    data,
    isLoading, // True only when no cached data
    isRefreshing, // True when updating in background
    error,
    refetch: () => fetchData(false),
    mutate: (newData: T) => {
      cache.set(key, newData);
      setData(newData);
    },
  };
}



