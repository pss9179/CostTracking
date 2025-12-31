/**
 * Simple performance instrumentation helpers.
 * Used to diagnose where the 30s delay occurs (Clerk token vs API fetch).
 */

const timers: Record<string, number> = {};

/**
 * Start a timer with a given label.
 */
export function mark(label: string): void {
  timers[label] = performance.now();
  if (process.env.NODE_ENV === 'development') {
    console.log(`[PERF] ${label} started`);
  }
}

/**
 * End a timer and log the duration.
 * @param label - The label for this measurement
 * @param startLabel - Optional: use a different label's start time
 * @returns Duration in milliseconds
 */
export function measure(label: string, startLabel?: string): number {
  const start = startLabel ? timers[startLabel] : timers[label];
  const duration = performance.now() - (start ?? 0);
  if (process.env.NODE_ENV === 'development') {
    console.log(`[PERF] ${label}: ${duration.toFixed(1)}ms`);
  }
  return duration;
}

/**
 * Log cache status for a tab.
 */
export function logCacheStatus(
  tab: string,
  cacheKey: string,
  exists: boolean,
  isStale: boolean
): void {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${tab}] cache`, { cacheKey, exists, isStale });
  }
}

/**
 * Log auth status for a tab.
 */
export function logAuth(
  tab: string,
  isLoaded: boolean,
  isSignedIn: boolean | undefined,
  hasUser: boolean
): void {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${tab}] auth`, { isLoaded, isSignedIn, hasUser });
  }
}

/**
 * Log a fetch result summary.
 */
export function logFetchResult(
  tab: string,
  success: boolean,
  dataCount?: number,
  error?: string
): void {
  if (process.env.NODE_ENV === 'development') {
    if (success) {
      console.log(`[${tab}] fetch success`, { dataCount });
    } else {
      console.log(`[${tab}] fetch failed`, { error });
    }
  }
}

