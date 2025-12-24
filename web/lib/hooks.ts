"use client";

import useSWR from "swr";
import { useAuth, useUser } from "@clerk/nextjs";
import { useCallback, useMemo } from "react";
import {
  fetchRuns,
  fetchProviderStats,
  fetchModelStats,
  fetchDailyStats,
  fetchSectionStats,
  fetchInsights,
  fetchCustomerStats,
  fetchCustomerDetail,
  fetchVoiceCalls,
  fetchVoiceProviderStats,
  fetchVoiceSegmentStats,
  fetchVoiceCostPerMinute,
  fetchVoiceForecast,
  fetchVoicePlatformComparison,
  fetchVoiceAlternativeCosts,
  type Run,
  type ProviderStats,
  type ModelStats,
  type DailyStats,
  type SectionStats,
  type Insight,
  type CustomerStats,
  type CustomerDetail,
  type VoiceCall,
  type VoiceProviderStats,
  type VoiceSegmentStats,
  type VoiceCostPerMinute,
  type VoiceForecast,
  type VoicePlatformComparison,
  type VoiceAlternativeCosts,
} from "./api";

// ============================================================================
// SWR Configuration - These make navigation FAST
// ============================================================================

const SWR_CONFIG = {
  // Keep data fresh for 2 minutes before revalidating (increased from 30s)
  dedupingInterval: 120000,
  // Revalidate in background when returning to tab (but throttled)
  revalidateOnFocus: true,
  // Don't refetch if data is less than 2 minutes old
  focusThrottleInterval: 120000,
  // Keep stale data while fetching fresh data
  keepPreviousData: true,
  // Retry on error (reduced from 2 to 1 to avoid excessive retries)
  errorRetryCount: 1,
  // Only revalidate if stale (don't always revalidate on mount)
  revalidateIfStale: true,
  revalidateOnMount: false, // Changed to false - use cached data if available
};

// ============================================================================
// Token-aware fetcher wrapper
// ============================================================================

function useTokenFetcher() {
  const { getToken } = useAuth();
  const { isLoaded, user } = useUser();

  const fetcher = useCallback(
    async <T>(fetchFn: (token: string) => Promise<T>): Promise<T> => {
      if (!isLoaded || !user) {
        throw new Error("Not authenticated");
      }
      const token = await getToken();
      if (!token) {
        throw new Error("No token available");
      }
      return fetchFn(token);
    },
    [getToken, isLoaded, user]
  );

  return { fetcher, isReady: isLoaded && !!user };
}

// ============================================================================
// Dashboard Data Hook - Cached across navigation
// ============================================================================

export function useDashboardData(hours: number) {
  const { fetcher, isReady } = useTokenFetcher();
  const days = Math.ceil(hours / 24);

  // Use SWR for each data type - they'll be cached and deduped
  const {
    data: runs,
    error: runsError,
    isLoading: runsLoading,
    mutate: mutateRuns,
  } = useSWR<Run[]>(
    isReady ? ["runs", 50] : null,
    () => fetcher((token) => fetchRuns(50, null, token)),
    SWR_CONFIG
  );

  const {
    data: providerStats,
    error: providerError,
    isLoading: providerLoading,
    mutate: mutateProviders,
  } = useSWR<ProviderStats[]>(
    isReady ? ["provider-stats", hours] : null,
    () => fetcher((token) => fetchProviderStats(hours, null, token)),
    SWR_CONFIG
  );

  const {
    data: modelStats,
    error: modelError,
    isLoading: modelLoading,
    mutate: mutateModels,
  } = useSWR<ModelStats[]>(
    isReady ? ["model-stats", hours] : null,
    () => fetcher((token) => fetchModelStats(hours, null, token)),
    SWR_CONFIG
  );

  const {
    data: dailyStats,
    error: dailyError,
    isLoading: dailyLoading,
    mutate: mutateDaily,
  } = useSWR<DailyStats[]>(
    isReady ? ["daily-stats", days] : null,
    () => fetcher((token) => fetchDailyStats(days, null, token)),
    SWR_CONFIG
  );

  // Combined loading state - only true on initial load
  const loading = !isReady || (runsLoading && providerLoading && modelLoading && dailyLoading);
  
  // First error we encounter
  const error = runsError || providerError || modelError || dailyError;

  // Refresh all data
  const refresh = useCallback(() => {
    mutateRuns();
    mutateProviders();
    mutateModels();
    mutateDaily();
  }, [mutateRuns, mutateProviders, mutateModels, mutateDaily]);

  return {
    runs: runs || [],
    providerStats: providerStats || [],
    modelStats: modelStats || [],
    dailyStats: dailyStats || [],
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load data") : null,
    refresh,
  };
}

// ============================================================================
// Features Data Hook - Cached across navigation
// ============================================================================

export function useFeaturesData(hours: number) {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: sectionStats,
    error,
    isLoading,
    mutate,
  } = useSWR<SectionStats[]>(
    isReady ? ["section-stats", hours] : null,
    () => fetcher((token) => fetchSectionStats(hours, null, token)),
    SWR_CONFIG
  );

  const loading = !isReady || isLoading;

  return {
    sectionStats: sectionStats || [],
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load feature data") : null,
    refresh: () => mutate(),
  };
}

// ============================================================================
// Voice Agents Data Hook - Cached across navigation
// ============================================================================

export function useVoiceAgentsData(hours: number) {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: calls,
    error: callsError,
    isLoading: callsLoading,
    mutate: mutateCalls,
  } = useSWR<VoiceCall[]>(
    isReady ? ["voice-calls", hours] : null,
    () => fetcher((token) => fetchVoiceCalls(hours, 50, token)),
    SWR_CONFIG
  );

  const {
    data: providerStats,
    error: providerError,
    isLoading: providerLoading,
    mutate: mutateProviders,
  } = useSWR<VoiceProviderStats[]>(
    isReady ? ["voice-provider-stats", hours] : null,
    () => fetcher((token) => fetchVoiceProviderStats(hours, token)),
    SWR_CONFIG
  );

  const {
    data: segmentStats,
    error: segmentError,
    isLoading: segmentLoading,
    mutate: mutateSegments,
  } = useSWR<VoiceSegmentStats[]>(
    isReady ? ["voice-segment-stats", hours] : null,
    () => fetcher((token) => fetchVoiceSegmentStats(hours, token)),
    SWR_CONFIG
  );

  const {
    data: costPerMinute,
    error: costError,
    isLoading: costLoading,
    mutate: mutateCost,
  } = useSWR<VoiceCostPerMinute>(
    isReady ? ["voice-cost-per-minute", hours] : null,
    () => fetcher((token) => fetchVoiceCostPerMinute(hours, token)),
    SWR_CONFIG
  );

  const {
    data: forecast,
    error: forecastError,
    isLoading: forecastLoading,
    mutate: mutateForecast,
  } = useSWR<VoiceForecast>(
    isReady ? ["voice-forecast"] : null,
    () => fetcher((token) => fetchVoiceForecast(token)),
    SWR_CONFIG
  );

  const {
    data: platformComparison,
    error: platformError,
    isLoading: platformLoading,
    mutate: mutatePlatform,
  } = useSWR<VoicePlatformComparison>(
    isReady ? ["voice-platform-comparison", hours] : null,
    () => fetcher((token) => fetchVoicePlatformComparison(hours, token)),
    SWR_CONFIG
  );

  const {
    data: alternativeCosts,
    error: altError,
    isLoading: altLoading,
    mutate: mutateAlt,
  } = useSWR<VoiceAlternativeCosts>(
    isReady ? ["voice-alternative-costs", hours] : null,
    () => fetcher((token) => fetchVoiceAlternativeCosts(hours, token)),
    SWR_CONFIG
  );

  // Combined loading - only true on initial load when we have no data
  const loading = !isReady || (
    callsLoading && providerLoading && segmentLoading && 
    costLoading && forecastLoading && platformLoading && altLoading
  );

  // First error we encounter
  const error = callsError || providerError || segmentError || 
                costError || forecastError || platformError || altError;

  const refresh = useCallback(() => {
    mutateCalls();
    mutateProviders();
    mutateSegments();
    mutateCost();
    mutateForecast();
    mutatePlatform();
    mutateAlt();
  }, [mutateCalls, mutateProviders, mutateSegments, mutateCost, mutateForecast, mutatePlatform, mutateAlt]);

  return {
    calls: calls || [],
    providerStats: providerStats || [],
    segmentStats: segmentStats || [],
    costPerMinute: costPerMinute || null,
    forecast: forecast || null,
    platformComparison: platformComparison || null,
    alternativeCosts: alternativeCosts || null,
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load voice data") : null,
    refresh,
  };
}

// ============================================================================
// Customers Data Hook - Cached across navigation
// ============================================================================

export function useCustomersData(hours: number = 720) {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: customers,
    error,
    isLoading,
    mutate,
  } = useSWR<CustomerStats[]>(
    isReady ? ["customer-stats", hours] : null,
    () => fetcher((token) => fetchCustomerStats(hours, token)),
    SWR_CONFIG
  );

  const loading = !isReady || isLoading;

  return {
    customers: customers || [],
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load customers") : null,
    refresh: () => mutate(),
  };
}

// ============================================================================
// Customer Detail Hook - Cached across navigation
// ============================================================================

export function useCustomerDetail(customerId: string, days: number = 30) {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: customer,
    error,
    isLoading,
    mutate,
  } = useSWR<CustomerDetail>(
    isReady && customerId ? ["customer-detail", customerId, days] : null,
    () => fetcher((token) => fetchCustomerDetail(customerId, days, token)),
    SWR_CONFIG
  );

  const loading = !isReady || isLoading;

  return {
    customer: customer || null,
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load customer details") : null,
    refresh: () => mutate(),
  };
}

// ============================================================================
// Runs Data Hook - Cached across navigation
// ============================================================================

export function useRunsData(limit: number = 5000) {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: runs,
    error,
    isLoading,
    mutate,
  } = useSWR<Run[]>(
    isReady ? ["runs-list", limit] : null,
    () => fetcher((token) => fetchRuns(limit, null, token)),
    SWR_CONFIG
  );

  const loading = !isReady || isLoading;

  return {
    runs: runs || [],
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load runs") : null,
    refresh: () => mutate(),
  };
}

// ============================================================================
// Insights Data Hook - Cached across navigation
// ============================================================================

export function useInsightsData() {
  const { fetcher, isReady } = useTokenFetcher();

  const {
    data: insights,
    error,
    isLoading,
    mutate,
  } = useSWR<Insight[]>(
    isReady ? ["insights"] : null,
    () => fetcher((token) => fetchInsights(null, token)),
    {
      ...SWR_CONFIG,
      // Insights should refresh more frequently
      refreshInterval: 60000,
    }
  );

  const loading = !isReady || isLoading;

  return {
    insights: insights || [],
    loading,
    error: error ? (error instanceof Error ? error.message : "Failed to load insights") : null,
    refresh: () => mutate(),
  };
}

// ============================================================================
// Prefetch functions - Call these on hover to preload data
// ============================================================================

export function usePrefetch() {
  const { fetcher, isReady } = useTokenFetcher();

  const prefetchDashboard = useCallback(async () => {
    if (!isReady) return;
    // Prefetch by triggering fetches that will populate the SWR cache
    const hours = 168;
    const days = 7;
    try {
      await Promise.all([
        fetcher((token) => fetchRuns(50, null, token)),
        fetcher((token) => fetchProviderStats(hours, null, token)),
        fetcher((token) => fetchModelStats(hours, null, token)),
        fetcher((token) => fetchDailyStats(days, null, token)),
      ]);
    } catch {
      // Silently fail prefetch
    }
  }, [fetcher, isReady]);

  const prefetchFeatures = useCallback(async () => {
    if (!isReady) return;
    const hours = 168; // 7 days
    try {
      await fetcher((token) => fetchSectionStats(hours, null, token));
    } catch {
      // Silently fail prefetch
    }
  }, [fetcher, isReady]);

  return { prefetchDashboard, prefetchFeatures };
}

