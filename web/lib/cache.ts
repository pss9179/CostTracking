// Global cache that persists across page navigations
// Using window object to ensure it survives page transitions

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const CACHE_KEY = '__llmobserve_cache__';
const STALE_TIME = 120000; // 2 minutes - increased from 30s to reduce API calls

function getGlobalCache(): Record<string, CacheEntry<unknown>> {
  if (typeof window === 'undefined') return {};
  
  if (!(window as any)[CACHE_KEY]) {
    (window as any)[CACHE_KEY] = {};
  }
  return (window as any)[CACHE_KEY];
}

export function getCached<T>(key: string): T | null {
  const cache = getGlobalCache();
  const entry = cache[key] as CacheEntry<T> | undefined;
  return entry?.data ?? null;
}

export function setCached<T>(key: string, data: T): void {
  const cache = getGlobalCache();
  cache[key] = { data, timestamp: Date.now() };
}

export function isCacheStale(key: string, staleTime: number = STALE_TIME): boolean {
  const cache = getGlobalCache();
  const entry = cache[key];
  if (!entry) return true;
  return Date.now() - entry.timestamp > staleTime;
}

export function getCacheTimestamp(key: string): number | null {
  const cache = getGlobalCache();
  return cache[key]?.timestamp ?? null;
}

export function clearCache(): void {
  if (typeof window !== 'undefined') {
    (window as any)[CACHE_KEY] = {};
  }
}

/**
 * Get cached data with metadata for synchronous state initialization.
 * Returns data, whether it exists, and whether it's stale in a single call.
 * This avoids SSR/hydration issues by returning null data on server.
 */
export interface CacheMeta<T> {
  data: T | null;
  exists: boolean;
  isStale: boolean;
  timestamp: number | null;
}

export function getCachedWithMeta<T>(key: string, staleTime: number = STALE_TIME): CacheMeta<T> {
  // Return empty on server to avoid hydration mismatch
  if (typeof window === 'undefined') {
    return { data: null, exists: false, isStale: true, timestamp: null };
  }
  
  const cache = getGlobalCache();
  const entry = cache[key] as CacheEntry<T> | undefined;
  
  if (!entry) {
    return { data: null, exists: false, isStale: true, timestamp: null };
  }
  
  const isStale = Date.now() - entry.timestamp > staleTime;
  return {
    data: entry.data,
    exists: true,
    isStale,
    timestamp: entry.timestamp,
  };
}

/**
 * Helper to initialize state from cache synchronously.
 * Safe for SSR - returns defaultValue on server.
 */
export function getInitialFromCache<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  const cached = getCached<T>(key);
  return cached ?? defaultValue;
}



