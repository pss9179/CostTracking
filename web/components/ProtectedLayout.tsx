"use client";

import { Navigation } from "./Navigation";
import { DateRangeProvider } from "@/contexts/DateRangeContext";

/**
 * ProtectedLayout - Wrapper for authenticated pages
 * Note: Actual auth protection is handled by Clerk middleware
 * This component just provides consistent Navigation + layout + date range context
 */
export function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <DateRangeProvider>
      <Navigation />
      <main>{children}</main>
    </DateRangeProvider>
  );
}

