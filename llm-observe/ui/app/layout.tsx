import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { TopNav } from "./components/TopNav";
import { Sidebar } from "./components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LLM Observe",
  description: "OpenTelemetry-based LLM observability dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <TopNav />
          <Sidebar />
          <main className="ml-64 pt-16 min-h-screen bg-gray-50 dark:bg-gray-950">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}

