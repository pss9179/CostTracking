// Global cache that persists across page navigations
// Using window object to ensure it survives page transitions

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const CACHE_KEY = '__llmobserve_cache__';
const STALE_TIME = 30000; // 30 seconds

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

