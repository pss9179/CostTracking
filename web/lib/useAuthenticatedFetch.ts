"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { getCached, setCached, getCachedWithMeta } from "./cache";

/**
 * A robust hook for authenticated data fetching that:
 * 1. NEVER makes API calls before auth is ready
 * 2. ALWAYS retries when auth becomes ready
 * 3. NEVER leaves loading state stuck
 * 4. Properly handles cache key changes
 * 5. Provides stable loading/error states
 */

interface UseAuthenticatedFetchOptions<T> {
  cacheKey: string;
  fetcher: (token: string) => Promise<T>;
  // Optional: custom check to determine if cached data is "valid" (has content)
  hasData?: (data: T) => boolean;
  // Optional: stale time in ms (default: 2 minutes)
  staleTime?: number;
}

interface UseAuthenticatedFetchResult<T> {
  data: T | null;
  loading: boolean;
  isRefreshing: boolean;
  error: string | null;
  refetch: () => void;
  lastRefresh: Date | null;
}

export function useAuthenticatedFetch<T>({
  cacheKey,
  fetcher,
  hasData = (d) => d !== null && d !== undefined,
  staleTime = 120000,
}: UseAuthenticatedFetchOptions<T>): UseAuthenticatedFetchResult<T> {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  // Track if a fetch is in progress to prevent duplicates
  const fetchInProgressRef = useRef(false);
  // Track if we've ever successfully fetched for this cache key
  const hasFetchedRef = useRef(false);
  // Track the current cache key to detect changes
  const currentCacheKeyRef = useRef(cacheKey);
  
  // State
  const [data, setData] = useState<T | null>(() => getCached<T>(cacheKey));
  const [loading, setLoading] = useState<boolean>(() => {
    const cached = getCachedWithMeta<T>(cacheKey);
    // Only show loading if: no cache OR cache has no valid data
    return !cached.exists || !hasData(cached.data as T);
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  
  // Reset state when cache key changes
  useEffect(() => {
    if (currentCacheKeyRef.current !== cacheKey) {
      currentCacheKeyRef.current = cacheKey;
      hasFetchedRef.current = false;
      
      // Check if new cache key has data
      const cached = getCachedWithMeta<T>(cacheKey);
      if (cached.exists && hasData(cached.data as T)) {
        setData(cached.data);
        setLoading(false);
      } else {
        setData(null);
        setLoading(true);
      }
      setError(null);
    }
  }, [cacheKey, hasData]);
  
  // The fetch function
  const doFetch = useCallback(async (isBackground: boolean = false) => {
    // CRITICAL: Don't fetch if auth not ready
    if (!isLoaded || !isSignedIn || !user) {
      console.log(`[useAuthenticatedFetch] Auth not ready for ${cacheKey}, will retry when ready`);
      return false; // Return false to indicate fetch didn't happen
    }
    
    // Prevent duplicate fetches
    if (fetchInProgressRef.current) {
      console.log(`[useAuthenticatedFetch] Fetch already in progress for ${cacheKey}`);
      return false;
    }
    
    fetchInProgressRef.current = true;
    
    // Check cache freshness for background refreshes
    const cache = getCachedWithMeta<T>(cacheKey);
    if (isBackground && cache.exists && !cache.isStale) {
      fetchInProgressRef.current = false;
      return false; // Cache is fresh, no need to fetch
    }
    
    // Set loading/refreshing state
    const hasCachedData = cache.exists && hasData(cache.data as T);
    if (hasCachedData) {
      setIsRefreshing(true);
    } else if (!isBackground) {
      setLoading(true);
    }
    setError(null);
    
    try {
      // CRITICAL: Get token and verify it exists
      const token = await getToken();
      
      if (!token) {
        // Token not ready yet - this can happen even when isLoaded/user are truthy
        // Don't set error, just log and allow retry
        console.warn(`[useAuthenticatedFetch] getToken() returned null for ${cacheKey}, will retry`);
        fetchInProgressRef.current = false;
        // DON'T set loading to false here - we'll retry
        return false;
      }
      
      // Make the actual fetch
      const result = await fetcher(token);
      
      // Success! Update state and cache
      setData(result);
      setCached(cacheKey, result);
      setLastRefresh(new Date());
      hasFetchedRef.current = true;
      setError(null);
      
      return true;
    } catch (err) {
      console.error(`[useAuthenticatedFetch] Error fetching ${cacheKey}:`, err);
      
      // Don't overwrite cache on error
      // Only set error if we don't have cached data to show
      const errorMessage = err instanceof Error ? err.message : "Failed to load data";
      
      if (!cache.exists || !hasData(cache.data as T)) {
        setError(errorMessage);
      }
      
      return false;
    } finally {
      // ALWAYS set loading states to false
      setLoading(false);
      setIsRefreshing(false);
      fetchInProgressRef.current = false;
    }
  }, [isLoaded, isSignedIn, user, getToken, cacheKey, fetcher, hasData]);
  
  // Effect to trigger fetch when auth becomes ready or cache key changes
  useEffect(() => {
    // If auth not ready, nothing to do (yet)
    // The effect will re-run when auth state changes
    if (!isLoaded || !isSignedIn || !user) {
      // If we're waiting for auth and have no cached data, ensure loading is true
      const cached = getCachedWithMeta<T>(cacheKey);
      if (!cached.exists || !hasData(cached.data as T)) {
        setLoading(true);
      }
      return;
    }
    
    // Auth is ready - check if we need to fetch
    const cache = getCachedWithMeta<T>(cacheKey);
    const hasCachedData = cache.exists && hasData(cache.data as T);
    
    if (hasCachedData && !cache.isStale) {
      // Fresh cache exists, no need to fetch
      setLoading(false);
      setData(cache.data);
      return;
    }
    
    // Need to fetch (either no cache or stale)
    doFetch(hasCachedData);
  }, [isLoaded, isSignedIn, user, cacheKey, doFetch, hasData]);
  
  // Retry mechanism: if token was null, retry after a short delay
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user) return;
    
    // If we're still loading and haven't fetched yet, retry
    if (loading && !hasFetchedRef.current && !fetchInProgressRef.current) {
      const timer = setTimeout(() => {
        console.log(`[useAuthenticatedFetch] Retrying fetch for ${cacheKey}`);
        doFetch(false);
      }, 500);
      
      return () => clearTimeout(timer);
    }
  }, [loading, isLoaded, isSignedIn, user, cacheKey, doFetch]);
  
  // Manual refetch
  const refetch = useCallback(() => {
    doFetch(false);
  }, [doFetch]);
  
  return {
    data,
    loading,
    isRefreshing,
    error,
    refetch,
    lastRefresh,
  };
}

/**
 * Hook for fetching multiple resources in parallel with shared auth handling
 */
interface MultiResourceConfig<T> {
  key: string;
  fetcher: (token: string) => Promise<T>;
  hasData?: (data: T) => boolean;
}

export function useMultiAuthenticatedFetch<T extends Record<string, unknown>>(
  cacheKey: string,
  resources: { [K in keyof T]: MultiResourceConfig<T[K]> },
  staleTime: number = 120000
) {
  const { getToken } = useAuth();
  const { isLoaded, isSignedIn, user } = useUser();
  
  const fetchInProgressRef = useRef(false);
  const currentCacheKeyRef = useRef(cacheKey);
  
  // Initialize state from cache
  const [data, setData] = useState<Partial<T>>(() => {
    const cached = getCached<T>(cacheKey);
    return cached || ({} as Partial<T>);
  });
  const [loading, setLoading] = useState<boolean>(() => {
    const cached = getCachedWithMeta<T>(cacheKey);
    return !cached.exists;
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  
  // Reset on cache key change
  useEffect(() => {
    if (currentCacheKeyRef.current !== cacheKey) {
      currentCacheKeyRef.current = cacheKey;
      
      const cached = getCachedWithMeta<T>(cacheKey);
      if (cached.exists) {
        setData(cached.data as T);
        setLoading(false);
      } else {
        setData({} as Partial<T>);
        setLoading(true);
      }
      setError(null);
    }
  }, [cacheKey]);
  
  const doFetch = useCallback(async (isBackground: boolean = false) => {
    if (!isLoaded || !isSignedIn || !user) {
      return false;
    }
    
    if (fetchInProgressRef.current) {
      return false;
    }
    
    fetchInProgressRef.current = true;
    
    const cache = getCachedWithMeta<T>(cacheKey);
    if (isBackground && cache.exists && !cache.isStale) {
      fetchInProgressRef.current = false;
      return false;
    }
    
    if (cache.exists) {
      setIsRefreshing(true);
    } else if (!isBackground) {
      setLoading(true);
    }
    setError(null);
    
    try {
      const token = await getToken();
      
      if (!token) {
        console.warn(`[useMultiAuthenticatedFetch] No token for ${cacheKey}`);
        fetchInProgressRef.current = false;
        return false;
      }
      
      // Fetch all resources in parallel
      const resourceKeys = Object.keys(resources) as Array<keyof T>;
      const results = await Promise.all(
        resourceKeys.map(async (key) => {
          try {
            const result = await resources[key].fetcher(token);
            return { key, result, error: null };
          } catch (err) {
            return { key, result: null, error: err };
          }
        })
      );
      
      // Build the data object
      const newData: Partial<T> = {};
      let hasError = false;
      
      for (const { key, result, error: fetchError } of results) {
        if (fetchError) {
          console.error(`[useMultiAuthenticatedFetch] Error fetching ${String(key)}:`, fetchError);
          hasError = true;
          // Keep existing data for this key
          newData[key] = data[key] as T[typeof key];
        } else {
          newData[key] = result as T[typeof key];
        }
      }
      
      setData(newData);
      
      // Only cache if no errors
      if (!hasError) {
        setCached(cacheKey, newData as T);
      }
      
      setLastRefresh(new Date());
      
      return true;
    } catch (err) {
      console.error(`[useMultiAuthenticatedFetch] Error:`, err);
      setError(err instanceof Error ? err.message : "Failed to load data");
      return false;
    } finally {
      setLoading(false);
      setIsRefreshing(false);
      fetchInProgressRef.current = false;
    }
  }, [isLoaded, isSignedIn, user, getToken, cacheKey, resources, data]);
  
  // Trigger fetch when auth ready
  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user) {
      const cached = getCachedWithMeta<T>(cacheKey);
      if (!cached.exists) {
        setLoading(true);
      }
      return;
    }
    
    const cache = getCachedWithMeta<T>(cacheKey);
    
    if (cache.exists && !cache.isStale) {
      setLoading(false);
      setData(cache.data as T);
      return;
    }
    
    doFetch(!!cache.exists);
  }, [isLoaded, isSignedIn, user, cacheKey, doFetch]);
  
  const refetch = useCallback(() => {
    doFetch(false);
  }, [doFetch]);
  
  return {
    data: data as T,
    loading,
    isRefreshing,
    error,
    refetch,
    lastRefresh,
  };
}

