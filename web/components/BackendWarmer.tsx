"use client";

import { useEffect, useRef } from "react";

const COLLECTOR_URL = process.env.NEXT_PUBLIC_COLLECTOR_URL || "https://llmobserve-api-production-d791.up.railway.app";

/**
 * BackendWarmer - Immediately pings the backend to wake up Railway container
 * 
 * Railway containers sleep after inactivity. The first real request can take 30+ seconds
 * while the container boots. This component sends a lightweight health check on mount
 * to wake the container BEFORE the user's actual data requests.
 * 
 * This runs in parallel with Clerk auth, so by the time auth is ready and data fetches
 * begin, the container should already be awake.
 */
export function BackendWarmer() {
  const hasWarmed = useRef(false);

  useEffect(() => {
    // Only warm once per page load
    if (hasWarmed.current) return;
    hasWarmed.current = true;

    const warmBackend = async () => {
      const start = performance.now();
      console.log("[BackendWarmer] Warming backend + database...");
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for cold start
        
        // Warm BOTH the container AND the database connection
        // /warm endpoint touches the database with a simple SELECT 1
        const response = await fetch(`${COLLECTOR_URL}/warm`, {
          method: "GET",
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        const elapsed = performance.now() - start;
        
        if (response.ok) {
          const data = await response.json().catch(() => ({}));
          console.log(`[BackendWarmer] Warm complete! Took ${elapsed.toFixed(0)}ms, db_time: ${data.db_time_ms || 'unknown'}ms`);
        } else {
          console.log(`[BackendWarmer] Warm responded ${response.status} in ${elapsed.toFixed(0)}ms`);
        }
      } catch (error) {
        const elapsed = performance.now() - start;
        if (error instanceof Error && error.name === "AbortError") {
          console.log(`[BackendWarmer] Timeout after ${elapsed.toFixed(0)}ms - backend may still be starting`);
        } else {
          console.log(`[BackendWarmer] Warm failed after ${elapsed.toFixed(0)}ms:`, error);
        }
      }
    };

    // Start warming immediately - don't wait for anything
    warmBackend();

    // Also set up a periodic ping every 4 minutes to keep container + DB warm
    // Railway typically sleeps containers after 5 minutes of inactivity
    const intervalId = setInterval(() => {
      fetch(`${COLLECTOR_URL}/warm`, { method: "GET" }).catch(() => {});
    }, 4 * 60 * 1000); // 4 minutes

    return () => clearInterval(intervalId);
  }, []);

  return null; // This component renders nothing
}

