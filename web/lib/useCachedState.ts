import { useState, useRef } from 'react';
import { getCached, getCachedWithMeta } from './cache';

interface UseCachedStateResult<T> {
  data: T;
  setData: React.Dispatch<React.SetStateAction<T>>;
  hasEverLoaded: boolean;
  setHasEverLoaded: (val: boolean) => void;
  cacheExists: boolean;
  isStale: boolean;
}

/**
 * Hook that initializes state from cache SYNCHRONOUSLY.
 * This ensures cached data renders on the FIRST paint, avoiding flicker.
 * 
 * @param cacheKey - The key to look up in cache
 * @param defaultValue - Default value if cache is empty
 * @param isValid - Optional predicate to determine if cached data is "real" (e.g., length > 0)
 */
export function useCachedState<T>(
  cacheKey: string,
  defaultValue: T,
  isValid: (data: T) => boolean = () => true
): UseCachedStateResult<T> {
  // Synchronous cache read in useState initializer - runs BEFORE first paint
  const [data, setData] = useState<T>(() => {
    if (typeof window === 'undefined') return defaultValue;
    const cached = getCached<T>(cacheKey);
    return cached ?? defaultValue;
  });
  
  // Get cache metadata for staleness checks
  const cacheMeta = getCachedWithMeta<T>(cacheKey);
  
  const [hasEverLoaded, setHasEverLoaded] = useState<boolean>(
    () => cacheMeta.exists && isValid(cacheMeta.data ?? defaultValue)
  );
  
  return {
    data,
    setData,
    hasEverLoaded,
    setHasEverLoaded,
    cacheExists: cacheMeta.exists,
    isStale: cacheMeta.isStale,
  };
}

/**
 * Helper to sync-initialize multiple related states from a single cache entry.
 * Returns the cached data and whether valid cache exists.
 */
export function getInitialCacheData<T>(
  cacheKey: string,
  isValid: (data: T | null) => boolean = (d) => d !== null
): { cached: T | null; hasCache: boolean; isStale: boolean } {
  if (typeof window === 'undefined') {
    return { cached: null, hasCache: false, isStale: true };
  }
  
  const meta = getCachedWithMeta<T>(cacheKey);
  return {
    cached: meta.data,
    hasCache: meta.exists && isValid(meta.data),
    isStale: meta.isStale,
  };
}

