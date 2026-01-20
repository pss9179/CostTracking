"use client";

import { Suspense } from "react";
import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { DateRangeProvider } from "@/contexts/DateRangeContext";
import { GlobalFiltersProvider } from "@/contexts/GlobalFiltersContext";
import { TopBar } from "@/components/TopBar";
// Removed GlobalFilterBar - each page has its own AnalyticsHeader with filters
// This eliminates the duplicate time filter issue

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith('/sign-');
  const isLandingPage = pathname === '/';
  const isOnboardingPage = pathname?.startsWith('/onboarding');
  const isPublicDocsPage = pathname?.startsWith('/docs'); // Public docs only (not /api-docs)

  if (isAuthPage || isLandingPage || isOnboardingPage || isPublicDocsPage) {
    return <>{children}</>;
  }

  return (
    <DateRangeProvider>
      <Suspense fallback={null}>
        <GlobalFiltersProvider>
          <div className="flex h-screen overflow-hidden bg-black">
            <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 mt-2 mb-4 mr-2 rounded-xl bg-white shadow-lg overflow-hidden">
            <TopBar />
            {/* Filters are now in each page's AnalyticsHeader - no more duplicate */}
            <main className="flex-1 overflow-y-auto bg-background px-6 py-4">
              {children}
            </main>
          </div>
          </div>
        </GlobalFiltersProvider>
      </Suspense>
    </DateRangeProvider>
  );
}

