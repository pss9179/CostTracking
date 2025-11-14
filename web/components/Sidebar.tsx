"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  LayoutDashboard, 
  List, 
  Bot, 
  Zap, 
  Server, 
  DollarSign, 
  BarChart3, 
  Settings,
  Activity
} from "lucide-react";
import { cn } from "@/lib/utils";
import { UserButton, useUser } from "@clerk/nextjs";
import { useState } from "react";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Runs", href: "/runs", icon: List },
  { name: "Agents", href: "/agents", icon: Bot },
  { name: "LLMs", href: "/llms", icon: Zap },
  { name: "Infrastructure", href: "/infrastructure", icon: Server },
  { name: "Costs", href: "/costs", icon: DollarSign },
  { name: "Insights", href: "/insights", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoaded, user } = useUser();
  const [showDropdown, setShowDropdown] = useState(false);

  // Don't show sidebar on auth pages
  if (pathname?.startsWith('/sign-')) {
    return null;
  }

  return (
    <div 
      data-sidebar 
      className="flex flex-shrink-0 flex-col border-r border-gray-100 bg-background h-screen" 
      style={{ zIndex: 10 }}
    >
      {/* Logo at top */}
      <div className="flex h-16 items-center justify-center flex-shrink-0">
        <Link href="/" className="flex items-center justify-center">
          <Activity className="h-7 w-7 text-indigo-600" strokeWidth={2.5} />
        </Link>
      </div>
      
      {/* Navigation - icons above text */}
      <nav className="flex-1 space-y-1 px-2 py-3 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href + "/"));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200",
                isActive
                  ? "bg-indigo-50 text-indigo-600"
                  : "text-black hover:bg-muted/50"
              )}
            >
              <item.icon className={cn(
                "h-5 w-5 mb-1 transition-colors",
                isActive ? "text-indigo-600" : "text-black"
              )} />
              <span className={cn(
                "text-[10px] font-medium text-center leading-tight",
                isActive ? "text-indigo-600" : "text-black"
              )}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </nav>
      
      {/* Bottom section with profile */}
      <div className="py-2 flex-shrink-0 flex flex-col items-center gap-2 relative">
        {isLoaded && user ? (
          <div className="relative flex items-center justify-center">
            <UserButton 
              afterSignOutUrl="/sign-in"
              appearance={{
                elements: {
                  avatarBox: "h-10 w-10 rounded-lg",
                  userButtonPopoverCard: "shadow-lg",
                },
              }}
            />
          </div>
        ) : (
          <Link
            href="/sign-in"
            className="group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200 text-black hover:bg-muted/50 w-full"
          >
            <Settings className="h-5 w-5 mb-1 transition-colors text-black" />
            <span className="text-[10px] font-medium text-center leading-tight text-black">
              Sign In
            </span>
          </Link>
        )}
      </div>
    </div>
  );
}

