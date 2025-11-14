"use client";

/**
 * ProtectedLayout - Wrapper for authenticated pages
 * Note: Actual auth protection is handled by Clerk middleware
 * Layout is now handled by LayoutWrapper in root layout
 * This component is kept for backwards compatibility but does nothing
 */
export function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

