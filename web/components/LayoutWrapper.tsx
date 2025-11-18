"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/Sidebar";
import { DateRangeProvider } from "@/contexts/DateRangeContext";
import { TopBar } from "@/components/TopBar";

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith('/sign-');
  const isLandingPage = pathname === '/';
  const isOnboardingPage = pathname?.startsWith('/onboarding');
  const isDocsPage = pathname?.startsWith('/docs');

  if (isAuthPage || isLandingPage || isOnboardingPage || isDocsPage) {
    return <>{children}</>;
  }

  return (
    <DateRangeProvider>
      <div className="flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <TopBar />
          <main className="flex-1 overflow-y-auto bg-background px-8 py-6">
            {children}
          </main>
        </div>
      </div>
    </DateRangeProvider>
  );
}

