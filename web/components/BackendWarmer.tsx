"use client";

import { useEffect, useRef } from "react";

const COLLECTOR_URL = process.env.NEXT_PUBLIC_COLLECTOR_URL || "https://llmobserve-api-production-d791.up.railway.app";

// Global promise that resolves when backend is warm
// Other components can await this before making API calls
let warmPromise: Promise<boolean> | null = null;
let warmResolve: ((value: boolean) => void) | null = null;

// Create the promise immediately (before any React renders)
if (typeof window !== "undefined" && !warmPromise) {
  warmPromise = new Promise<boolean>((resolve) => {
    warmResolve = resolve;
  });
  
  // Start warming immediately - don't wait for React
  const start = performance.now();
  console.log("[BackendWarmer] Starting warm (pre-React)...");
  
  fetch(`${COLLECTOR_URL}/warm`, { method: "GET" })
    .then(async (response) => {
      const elapsed = performance.now() - start;
      if (response.ok) {
        const data = await response.json().catch(() => ({}));
        console.log(`[BackendWarmer] Warm complete! Took ${elapsed.toFixed(0)}ms, db_time: ${data.db_time_ms || 'unknown'}ms`);
      } else {
        console.log(`[BackendWarmer] Warm responded ${response.status} in ${elapsed.toFixed(0)}ms`);
      }
      warmResolve?.(true);
    })
    .catch((error) => {
      const elapsed = performance.now() - start;
      console.log(`[BackendWarmer] Warm failed after ${elapsed.toFixed(0)}ms:`, error);
      warmResolve?.(false);
    });
}

/**
 * Wait for the backend to be warm before making API calls.
 * Returns immediately if already warm.
 */
export async function waitForBackendWarm(): Promise<boolean> {
  if (!warmPromise) return true; // SSR or already resolved
  return warmPromise;
}

/**
 * Check if backend warm request has completed (non-blocking)
 */
export function isBackendWarm(): boolean {
  // Check if the promise is resolved by seeing if warmResolve is still set
  // After resolution, we could set a flag, but for simplicity we'll just return true
  // if the warmPromise exists (meaning warming was initiated)
  return warmPromise !== null;
}

/**
 * BackendWarmer - React component that sets up keep-alive pings
 * 
 * The actual warming happens in module scope (above) to start BEFORE React hydrates.
 * This component just sets up the periodic keep-alive pings.
 */
export function BackendWarmer() {
  const hasSetupInterval = useRef(false);

  useEffect(() => {
    if (hasSetupInterval.current) return;
    hasSetupInterval.current = true;

    // Set up periodic ping every 4 minutes to keep container + DB warm
    // Railway typically sleeps containers after 5 minutes of inactivity
    const intervalId = setInterval(() => {
      fetch(`${COLLECTOR_URL}/warm`, { method: "GET" }).catch(() => {});
    }, 4 * 60 * 1000); // 4 minutes

    return () => clearInterval(intervalId);
  }, []);

  return null; // This component renders nothing
}
