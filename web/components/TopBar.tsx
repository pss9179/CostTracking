"use client";

import { usePathname } from "next/navigation";

export function TopBar() {
  const pathname = usePathname();

  // Don't show top bar on auth pages
  if (pathname?.startsWith('/sign-')) {
    return null;
  }

  return (
    <div className="flex items-center justify-between h-16 px-8 border-b bg-background">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">
          {pathname === "/" && "Dashboard"}
          {pathname === "/runs" && "Runs"}
          {pathname === "/agents" && "Agents"}
          {pathname === "/llms" && "LLMs"}
          {pathname === "/infrastructure" && "Infrastructure"}
          {pathname === "/costs" && "Costs"}
          {pathname === "/insights" && "Insights"}
          {pathname === "/settings" && "Settings"}
          {pathname?.startsWith("/runs/") && "Run Details"}
        </h1>
      </div>
    </div>
  );
}

