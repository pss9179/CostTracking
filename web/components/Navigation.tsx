"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { UserButton, useUser } from "@clerk/nextjs";
import { Activity, BarChart3, Zap, Server, Bot, Settings } from "lucide-react";
import { DateRangeFilter } from "@/components/DateRangeFilter";
import { useDateRange } from "@/contexts/DateRangeContext";

export function Navigation() {
  const pathname = usePathname();
  const { isLoaded, user } = useUser();
  const { dateRange, setDateRange } = useDateRange();

  const isActive = (path: string) => pathname === path;

  if (!isLoaded) {
    return (
      <nav className="border-b bg-white">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <Activity className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-bold">Skyline</span>
            </Link>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="border-b bg-white shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <Activity className="h-6 w-6 text-blue-600" />
            <span className="text-xl font-bold">LLMObserve</span>
          </Link>

          {/* Date Range Filter - Center */}
          <div className="flex-1 flex justify-center">
            <DateRangeFilter value={dateRange} onChange={setDateRange} />
          </div>

          {/* Navigation Links - New UI Spec */}
          <div className="flex items-center space-x-1">
            <Link href="/">
              <Button
                variant={isActive("/") ? "default" : "ghost"}
                size="sm"
                className="flex items-center space-x-2"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Dashboard</span>
              </Button>
            </Link>

            <Link href="/llms">
              <Button
                variant={isActive("/llms") ? "default" : "ghost"}
                size="sm"
                className="flex items-center space-x-2"
              >
                <Zap className="h-4 w-4" />
                <span>LLMs</span>
              </Button>
            </Link>

            <Link href="/infrastructure">
              <Button
                variant={isActive("/infrastructure") ? "default" : "ghost"}
                size="sm"
                className="flex items-center space-x-2"
              >
                <Server className="h-4 w-4" />
                <span>Infrastructure</span>
              </Button>
            </Link>

            <Link href="/agents">
              <Button
                variant={isActive("/agents") ? "default" : "ghost"}
                size="sm"
                className="flex items-center space-x-2"
              >
                <Bot className="h-4 w-4" />
                <span>Agents</span>
              </Button>
            </Link>

            <Link href="/settings">
              <Button
                variant={isActive("/settings") ? "default" : "ghost"}
                size="sm"
                className="flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Button>
            </Link>
          </div>

          {/* Clerk User Button */}
          {user && (
            <div className="flex items-center space-x-3">
              <UserButton
                afterSignOutUrl="/sign-in"
                appearance={{
                  elements: {
                    avatarBox: "h-9 w-9",
                  },
                }}
              />
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

