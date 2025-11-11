import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";
import { Navigation } from "@/components/layout/Navigation";

export const metadata: Metadata = {
  title: "LLM Observe - Cost Observability Dashboard",
  description: "First-class observability for LLM and API costs with hierarchical tracing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body className="min-h-screen bg-background antialiased">
          <Navigation />
          <main>{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}
