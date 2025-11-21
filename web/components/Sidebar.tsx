"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  LayoutGrid,
  List,
  Cpu,
  Zap,
  Server,
  DollarSign,
  LineChart,
  Settings2,
  Activity,
  FileCode2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { UserButton, useUser, OrganizationSwitcher, useOrganization } from "@clerk/nextjs";
import { useState, useEffect } from "react";
import { Users } from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutGrid },
  // { name: "Runs", href: "/runs", icon: List }, // Removed as per user request
  { name: "Agents", href: "/agents", icon: Cpu },
  // { name: "LLMs", href: "/llms", icon: Zap }, // Removed as per user request
  // { name: "Infrastructure", href: "/infrastructure", icon: Server }, // Removed as per user request
  // { name: "Costs", href: "/costs", icon: DollarSign }, // Removed as per user request
  { name: "Insights", href: "/insights", icon: LineChart },
  // { name: "Settings", href: "/settings", icon: Settings }, // Removed to move to bottom
  { name: "API Docs", href: "/api-docs", icon: FileCode2 },
];

function OrgSwitcherWrapper() {
  const { organization } = useOrganization();
  
  return (
    <div className="w-full px-2 relative" style={{ minHeight: '4rem' }}>
      <div className="absolute inset-0 z-20 pointer-events-none flex flex-col items-center justify-center px-2">
        <div className="flex items-center gap-1.5">
          <span className="text-blue-600 font-bold text-base leading-tight">Skyline</span>
          <svg className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        {organization && (
          <span className="text-gray-900 text-[11px] mt-1 leading-tight">{organization.name}</span>
        )}
      </div>
      
      <div className="relative z-10" style={{ opacity: 0, pointerEvents: 'auto' }}>
        <OrganizationSwitcher 
          hidePersonal={true}
          afterCreateOrganizationUrl="/dashboard"
          afterLeaveOrganizationUrl="/dashboard"
          afterSelectOrganizationUrl="/dashboard"
          appearance={{
            elements: {
              rootBox: "w-full",
              organizationSwitcherTrigger: "w-full min-h-[4rem]"
            }
          }}
        />
      </div>
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoaded, user } = useUser();
  const [userType, setUserType] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded || !user) return;

    // Check user type on mount
    const type = localStorage.getItem(`user_${user.id}_type`);
    setUserType(type);
  }, [isLoaded, user]);

  // Don't show sidebar on auth pages or onboarding
  if (pathname?.startsWith('/sign-') || pathname === '/onboarding') {
    return null;
  }

  // Filter navigation based on user type
  const filteredNavigation = [
    { name: "Overview", href: "/overview", icon: Activity }, // Changed icon to distinguish from Dashboard
    ...navigation
  ];
  
  if (userType === 'multi') {
    // Check if Customers tab is already there to avoid duplicates if re-rendering
    if (!filteredNavigation.find(item => item.name === "Customers")) {
      filteredNavigation.splice(2, 0, { name: "Customers", href: "/customers", icon: Users });
    }
  }

  return (
    <div
      data-sidebar
      className="flex flex-shrink-0 flex-col border-r border-gray-100 bg-gradient-to-b from-blue-50/30 via-white to-white h-screen w-28"
      style={{ zIndex: 10 }}
    >
      {/* Organization Switcher with Skyline branding */}
      <div className="flex h-16 items-center justify-center flex-shrink-0 w-full border-b border-gray-100/50">
        <OrgSwitcherWrapper />
      </div>

      {/* Navigation - icons above text */}
      <nav className="flex-1 space-y-1 px-2 py-3 overflow-y-auto scrollbar-none">
        {filteredNavigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href + "/"));
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200",
                isActive
                  ? "bg-blue-50 text-blue-600"
                  : "text-gray-900 hover:bg-gray-100 hover:text-black"
              )}
            >
              <item.icon 
                strokeWidth={2.5}
                className={cn(
                "h-5 w-5 mb-1 transition-colors",
                isActive ? "text-blue-600" : "text-gray-900 group-hover:text-black"
              )} />
              <span className={cn(
                "text-[10px] font-bold text-center leading-tight",
                isActive ? "text-blue-600" : "text-gray-900 group-hover:text-black"
              )}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom section with Settings and Profile */}
      <div className="py-2 flex-shrink-0 flex flex-col items-center gap-2 relative border-t border-gray-100/50">
        {/* Settings Link */}
        <Link
          href="/settings"
          className={cn(
            "group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200 w-full",
            pathname === "/settings"
              ? "bg-blue-50 text-blue-600"
              : "text-gray-900 hover:bg-gray-100 hover:text-black"
          )}
        >
          <Settings2 
            strokeWidth={2.5}
            className={cn(
            "h-5 w-5 mb-1 transition-colors",
            pathname === "/settings" ? "text-blue-600" : "text-gray-900 group-hover:text-black"
          )} />
          <span className={cn(
            "text-[10px] font-bold text-center leading-tight",
            pathname === "/settings" ? "text-blue-600" : "text-gray-900 group-hover:text-black"
          )}>
            Settings
          </span>
        </Link>

        {isLoaded && user ? (
          <div className="relative flex items-center justify-center">
            <UserButton
              afterSignOutUrl="/sign-in"
              appearance={{
                elements: {
                  avatarBox: "h-9 w-9 rounded-lg ring-2 ring-transparent hover:ring-indigo-100 transition-all",
                  userButtonPopoverCard: "shadow-lg",
                },
              }}
            />
          </div>
        ) : (
          <Link
            href="/sign-in"
            className="group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200 text-gray-900 hover:bg-gray-100 w-full"
          >
            <Settings2 strokeWidth={2.5} className="h-5 w-5 mb-1 transition-colors" />
            <span className="text-[10px] font-bold text-center leading-tight">
              Sign In
            </span>
          </Link>
        )}
      </div>
    </div>
  );
}

