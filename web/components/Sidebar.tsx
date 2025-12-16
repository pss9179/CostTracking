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
  Settings,
  Cog,
  Activity,
  FileCode2,
  Building2,
  ChevronsUpDown,
  Plus,
  Folder,
  Home,
  Layers,
  Workflow,
  Users,
  Globe,
  Inbox,
  Mail,
  Phone,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  UserButton,
  useUser,
  useOrganization,
  useClerk,
  OrganizationSwitcher,
} from "@clerk/nextjs";
import { useState, useEffect } from "react";

// Navigation organized by feature groups with icon colors
const navigation = [
  // Feature 1: Basic cost tracking (by provider)
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutGrid,
    group: "Analytics",
    iconColor: "text-blue-500",
  },

  // Feature 2: Costs per product feature (semantic buckets)
  {
    name: "Features",
    href: "/features",
    icon: Layers,
    group: "Analytics",
    iconColor: "text-purple-500",
  },

  // Feature 3: Agent tree visualization
  {
    name: "Execution",
    href: "/agents",
    icon: Workflow,
    group: "Analytics",
    iconColor: "text-green-500",
  },

  // Feature 4: Voice AI tracking
  {
    name: "Voice Agents",
    href: "/voice-agents",
    icon: Phone,
    group: "Analytics",
    iconColor: "text-teal-500",
  },

  // Feature 5: Customer/tenant tracking
  {
    name: "Customers",
    href: "/customers",
    icon: Users,
    group: "Tenants",
    iconColor: "text-orange-500",
  },

  // Feature 6: Caps & Alerts
  {
    name: "Caps & Alerts",
    href: "/caps",
    icon: Shield,
    group: "Control",
    iconColor: "text-rose-500",
  },

  // Settings
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
    group: "Settings",
    iconColor: "text-gray-500",
  },

  // Resources
  {
    name: "API Docs",
    href: "/api-docs",
    icon: FileCode2,
    group: "Resources",
    iconColor: "text-cyan-500",
  },
];

function OrgSwitcherWrapper() {
  const { organization, isLoaded } = useOrganization();

  if (!isLoaded)
    return (
      <div className="h-12 w-full animate-pulse bg-[#1e293b] rounded-lg" />
    );

  return (
    <div className="w-full relative">
      {/* Custom Trigger UI (Visible) */}
      <div className="absolute inset-0 z-10 pointer-events-none flex items-center">
        <div className="w-full flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-[#1e293b]/20 transition-colors group cursor-pointer pointer-events-auto">
          <Globe className="h-5 w-5 text-white flex-shrink-0" />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="text-sm font-semibold text-white truncate">
              Skyline
            </span>
            <ChevronsUpDown className="h-4 w-4 text-gray-400 group-hover:text-white flex-shrink-0" />
          </div>
        </div>
      </div>

      {/* Actual Switcher (Invisible but clickable) */}
      <div className="relative z-20 opacity-0 w-full">
        <OrganizationSwitcher
          hidePersonal={true}
          afterCreateOrganizationUrl="/dashboard"
          afterLeaveOrganizationUrl="/dashboard"
          afterSelectOrganizationUrl="/dashboard"
          appearance={{
            elements: {
              rootBox: "w-full",
              organizationSwitcherTrigger:
                "w-full min-h-[3.5rem] cursor-pointer",
              organizationSwitcherPopoverCard:
                "bg-white border border-gray-200 shadow-xl rounded-lg p-2 min-w-[280px]",
              organizationSwitcherPopoverActionButton:
                "hover:bg-gray-50 rounded-md transition-colors ml-auto",
              organizationSwitcherPopoverActionButtonText:
                "text-gray-900 font-medium",
              organizationPreview:
                "px-3 py-2 rounded-md hover:bg-gray-50 transition-colors flex items-center gap-3",
              organizationPreviewText: "text-gray-900 font-semibold",
              organizationPreviewSecondaryIdentifier: "text-gray-500 text-xs",
              organizationPreviewAvatarBox: "hidden",
              organizationList: "space-y-1",
              organizationListPreview:
                "px-3 py-2 rounded-md hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-3",
              organizationListPreviewText: "text-gray-900 font-medium",
              organizationListPreviewAvatarBox: "hidden",
              createOrganizationBox:
                "px-3 py-2 rounded-md hover:bg-blue-50 transition-colors cursor-pointer border-t border-gray-100 mt-2 pt-2 flex items-center gap-3",
              createOrganizationButton: "text-blue-800 font-medium",
              footer: "hidden",
            },
            variables: {
              colorPrimary: "#3b82f6",
              colorText: "#111827",
              colorTextSecondary: "#6b7280",
              borderRadius: "0.5rem",
            },
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
  if (pathname?.startsWith("/sign-") || pathname === "/onboarding") {
    return null;
  }

  // Organize navigation by groups
  const overviewNav = {
    name: "Overview",
    href: "/overview",
    icon: Home,
    iconColor: "text-gray-400",
  };

  // Group navigation items
  const analyticsNav = navigation.filter((item) => item.group === "Analytics");
  const tenantsNav = navigation.filter((item) => item.group === "Tenants");
  const controlNav = navigation.filter((item) => item.group === "Control");
  const resourcesNav = navigation.filter((item) => item.group === "Resources");

  // Always show Customers - it's a core feature
  const finalTenantsNav = tenantsNav;

  return (
    <div
      data-sidebar
      className="flex flex-shrink-0 flex-col bg-black h-screen w-60"
      style={{ zIndex: 10 }}
    >
      {/* Organization Switcher with Cloud icon */}
      <div className="flex h-16 items-center flex-shrink-0 w-full border-b border-[#1e293b]/50 px-4">
        <OrgSwitcherWrapper />
      </div>

      {/* Navigation - icons next to text */}
      <nav className="flex-1 space-y-1 px-3 py-4 overflow-y-auto scrollbar-none">
        {/* Home and Inbox Buttons */}
        <div className="flex items-center gap-2 mb-3">
          {/* Overview - Home Button */}
          <Link
            href={overviewNav.href}
            className="group flex items-center justify-center rounded-lg py-3 px-3 transition-all duration-200 flex-1 bg-[#1e293b]/50 hover:bg-[#1e293b] border border-[#334155]/50"
          >
            <overviewNav.icon
              strokeWidth={2}
              className={cn(
                "h-5 w-5 flex-shrink-0 transition-colors",
                overviewNav.iconColor
              )}
            />
          </Link>

          {/* Inbox Button */}
          <Link
            href="/inbox"
            className="group flex items-center justify-center rounded-lg py-3 px-3 transition-all duration-200 flex-1 bg-[#1e293b]/50 hover:bg-[#1e293b] border border-[#334155]/50"
          >
            <Mail
              strokeWidth={2}
              className="h-5 w-5 flex-shrink-0 transition-colors text-gray-400"
            />
          </Link>
        </div>

        {/* Analytics Group */}
        {analyticsNav.length > 0 && (
          <>
            <div className="px-3 py-2 mb-1">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Analytics
              </span>
            </div>
            {analyticsNav.map((item) => {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
                >
                  <item.icon
                    strokeWidth={2}
                    className={cn(
                      "h-5 w-5 flex-shrink-0 transition-colors",
                      item.iconColor || "text-gray-300"
                    )}
                  />
                  <span className="text-sm font-medium leading-tight">
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </>
        )}

        {/* Tenants Group */}
        {finalTenantsNav.length > 0 && (
          <>
            <div className="px-3 py-2 mt-3 mb-1">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Tenants
              </span>
            </div>
            {finalTenantsNav.map((item) => {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
                >
                  <item.icon
                    strokeWidth={2}
                    className={cn(
                      "h-5 w-5 flex-shrink-0 transition-colors",
                      item.iconColor || "text-gray-300"
                    )}
                  />
                  <span className="text-sm font-medium leading-tight">
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </>
        )}

        {/* Control Group */}
        {controlNav.length > 0 && (
          <>
            <div className="px-3 py-2 mt-3 mb-1">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Control
              </span>
            </div>
            {controlNav.map((item) => {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
                >
                  <item.icon
                    strokeWidth={2}
                    className={cn(
                      "h-5 w-5 flex-shrink-0 transition-colors",
                      item.iconColor || "text-gray-300"
                    )}
                  />
                  <span className="text-sm font-medium leading-tight">
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </>
        )}

        {/* Resources Group */}
        {resourcesNav.length > 0 && (
          <>
            <div className="px-3 py-2 mt-3 mb-1">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Resources
              </span>
            </div>
            {resourcesNav.map((item) => {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
                >
                  <item.icon
                    strokeWidth={2}
                    className={cn(
                      "h-5 w-5 flex-shrink-0 transition-colors",
                      item.iconColor || "text-gray-300"
                    )}
                  />
                  <span className="text-sm font-medium leading-tight">
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* Bottom section with Settings and Profile */}
      <div className="py-3 flex-shrink-0 flex flex-col gap-2 relative border-t border-[#1e293b]/50 px-3">
        {/* Settings Link */}
        <Link
          href="/settings"
          className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
        >
          <Cog
            strokeWidth={2}
            className="h-5 w-5 flex-shrink-0 transition-colors text-gray-400"
          />
          <span className="text-sm font-medium leading-tight">Settings</span>
        </Link>

        {isLoaded && user ? (
          <div className="relative flex items-center px-3">
            <UserButton
              afterSignOutUrl="/sign-in"
              appearance={{
                elements: {
                  avatarBox:
                    "h-9 w-9 rounded-lg ring-2 ring-transparent hover:ring-indigo-100 transition-all",
                  userButtonPopoverCard: "shadow-lg",
                },
              }}
            />
          </div>
        ) : (
          <Link
            href="/sign-in"
            className="group flex items-center gap-3 rounded-lg py-2.5 px-3 transition-all duration-200 text-gray-300 hover:bg-[#1e293b] hover:text-white"
          >
            <Cog
              strokeWidth={2}
              className="h-5 w-5 flex-shrink-0 transition-colors text-gray-300 group-hover:text-white"
            />
            <span className="text-sm font-medium leading-tight">Sign In</span>
          </Link>
        )}
      </div>
    </div>
  );
}
