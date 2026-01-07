"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { BarChart3, ChevronRight } from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  items?: NavItem[];
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navigation: NavSection[] = [
  {
    title: "Getting started",
    items: [
      { title: "Overview", href: "/docs" },
      { title: "Quickstart", href: "/docs/quickstart" },
      { title: "Installation", href: "/docs/installation" },
    ],
  },
  {
    title: "Cost tracking",
    items: [
      { title: "How cost tracking works", href: "/docs/cost-tracking" },
      { title: "Viewing costs in the dashboard", href: "/docs/viewing-costs" },
      { title: "Supported providers", href: "/docs/providers" },
    ],
  },
  {
    title: "Labeling & organization",
    items: [
      { title: "Agent tracking", href: "/docs/agents" },
      { title: "Customer tracking", href: "/docs/customers" },
      { title: "Sections & workflows", href: "/docs/sections" },
    ],
  },
  {
    title: "Spending controls",
    items: [
      { title: "Spending caps", href: "/docs/spending-caps" },
      { title: "Alerts & notifications", href: "/docs/alerts" },
    ],
  },
  {
    title: "API Reference",
    items: [
      { title: "Python SDK", href: "/docs/sdk" },
      { title: "observe()", href: "/docs/api/observe" },
      { title: "@agent decorator", href: "/docs/api/agent" },
      { title: "section() context", href: "/docs/api/section" },
    ],
  },
  {
    title: "Help",
    items: [
      { title: "Troubleshooting", href: "/docs/troubleshooting" },
      { title: "FAQ", href: "/docs/faq" },
    ],
  },
];

function NavLink({ item, pathname }: { item: NavItem; pathname: string }) {
  const isActive = pathname === item.href;
  
  return (
    <Link
      href={item.href}
      className={cn(
        "block py-1.5 px-3 text-sm rounded-md transition-colors",
        isActive
          ? "bg-emerald-50 text-emerald-700 font-medium border-l-2 border-emerald-600 -ml-[2px]"
          : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
      )}
    >
      {item.title}
    </Link>
  );
}

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-white">
      {/* Top Navigation */}
      <nav className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6">
          <div className="flex justify-between items-center h-14">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-semibold text-slate-900">LLMObserve</span>
                <span className="text-slate-400 font-normal">Docs</span>
              </Link>
              
              <div className="hidden md:flex items-center gap-6 text-sm">
                <Link href="/docs" className="text-slate-900 font-medium">Documentation</Link>
                <Link href="/docs/api/observe" className="text-slate-500 hover:text-slate-900">API Reference</Link>
                <Link href="/docs/quickstart" className="text-slate-500 hover:text-slate-900">Quickstart</Link>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <Link 
                href="/dashboard" 
                className="text-sm text-slate-600 hover:text-slate-900"
              >
                Dashboard
              </Link>
              <Link
                href="/sign-up"
                className="text-sm bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-[1600px] mx-auto flex">
        {/* Sidebar */}
        <aside className="w-64 flex-shrink-0 border-r border-slate-200 hidden lg:block">
          <div className="sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto py-6 px-4">
            <nav className="space-y-6">
              {navigation.map((section) => (
                <div key={section.title}>
                  <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2 px-3">
                    {section.title}
                  </h4>
                  <div className="space-y-0.5">
                    {section.items.map((item) => (
                      <NavLink key={item.href} item={item} pathname={pathname} />
                    ))}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}

