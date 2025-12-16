import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { LayoutWrapper } from "@/components/LayoutWrapper";
import { UserTypeGuard } from "@/components/UserTypeGuard";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Skyline - Cost Observability Dashboard",
  description: "First-class observability for LLM and API costs with hierarchical tracing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      signInFallbackRedirectUrl="/dashboard"
      signUpFallbackRedirectUrl="/onboarding"
    >
      <html lang="en" suppressHydrationWarning>
        <body className={`${dmSans.className} min-h-screen bg-background antialiased`}>
          <DataCacheProvider>
            <UserTypeGuard>
              <LayoutWrapper>{children}</LayoutWrapper>
            </UserTypeGuard>
          </DataCacheProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
