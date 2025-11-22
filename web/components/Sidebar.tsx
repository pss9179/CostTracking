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
  FileCode2,
  Building2,
  ChevronsUpDown,
  Plus,
  Folder,
  Home,
  Layers,
  Workflow,
  Users,
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

// Navigation organized by feature groups
const navigation = [
  // Feature 1: Basic cost tracking (by provider)
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutGrid,
    group: "Analytics",
  },

  // Feature 2: Costs per product feature (semantic buckets)
  { name: "Features", href: "/features", icon: Layers, group: "Analytics" },

  // Feature 3: Agent tree visualization
  { name: "Execution", href: "/agents", icon: Workflow, group: "Analytics" },

  // Feature 4: Customer/tenant tracking
  { name: "Customers", href: "/customers", icon: Users, group: "Tenants" },

  // Resources
  { name: "API Docs", href: "/api-docs", icon: FileCode2, group: "Resources" },
];

function OrgSwitcherWrapper() {
  const { organization, isLoaded } = useOrganization();

  if (!isLoaded)
    return <div className="h-12 w-full animate-pulse bg-gray-100 rounded-lg" />;

  return (
    <div className="w-full relative">
      {/* Custom Trigger UI (Visible) */}
      <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
        <div className="w-full flex flex-col items-center justify-center gap-0.5 p-2 rounded-lg hover:bg-gray-100 transition-colors group cursor-pointer pointer-events-auto">
          <div className="flex items-center gap-1.5">
            <span className="text-blue-600 font-bold text-xl leading-tight">
              Skyline
            </span>
            <ChevronsUpDown className="h-3 w-3 text-gray-400 group-hover:text-gray-600" />
          </div>

          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[10px] font-medium text-gray-500 truncate max-w-[80px] leading-tight">
              {organization?.name || "Select Org"}
            </span>
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
              organizationPreviewAvatarBox: "w-8 h-8 flex-shrink-0",
              organizationList: "space-y-1",
              organizationListPreview:
                "px-3 py-2 rounded-md hover:bg-gray-50 transition-colors cursor-pointer flex items-center gap-3",
              organizationListPreviewText: "text-gray-900 font-medium",
              organizationListPreviewAvatarBox: "w-8 h-8 flex-shrink-0",
              createOrganizationBox:
                "px-3 py-2 rounded-md hover:bg-blue-50 transition-colors cursor-pointer border-t border-gray-100 mt-2 pt-2 flex items-center gap-3",
              createOrganizationButton: "text-blue-600 font-medium",
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
  const overviewNav = { name: "Overview", href: "/overview", icon: Home };

  // Group navigation items
  const analyticsNav = navigation.filter((item) => item.group === "Analytics");
  const tenantsNav = navigation.filter((item) => item.group === "Tenants");
  const resourcesNav = navigation.filter((item) => item.group === "Resources");

  // Always show Customers - it's a core feature
  const finalTenantsNav = tenantsNav;

  return (
    <div
      data-sidebar
      className="flex flex-shrink-0 flex-col border-r border-gray-100 bg-gradient-to-b from-blue-50/30 via-white to-white h-screen w-28"
      style={{ zIndex: 10 }}
    >
      {/* Organization Switcher with Skyline branding */}
      <div className="flex h-20 items-center justify-center flex-shrink-0 w-full border-b border-gray-100/50 px-2">
        <OrgSwitcherWrapper />
      </div>

      {/* Navigation - icons above text */}
      <nav className="flex-1 space-y-1 px-2 py-3 overflow-y-auto scrollbar-none">
        {/* Overview */}
        {(() => {
          const isActive =
            pathname === overviewNav.href ||
            (overviewNav.href !== "/" &&
              pathname?.startsWith(overviewNav.href + "/"));
          return (
            <Link
              key={overviewNav.name}
              href={overviewNav.href}
              className={cn(
                "group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200 mb-2",
                isActive
                  ? "bg-blue-50 text-blue-600"
                  : "text-gray-900 hover:bg-gray-100 hover:text-black"
              )}
            >
              <overviewNav.icon
                strokeWidth={2.5}
                className={cn(
                  "h-5 w-5 mb-1 transition-colors",
                  isActive
                    ? "text-blue-600"
                    : "text-gray-900 group-hover:text-black"
                )}
              />
              <span
                className={cn(
                  "text-[10px] font-bold text-center leading-tight",
                  isActive
                    ? "text-blue-600"
                    : "text-gray-900 group-hover:text-black"
                )}
              >
                {overviewNav.name}
              </span>
            </Link>
          );
        })()}

        {/* Analytics Group */}
        {analyticsNav.length > 0 && (
          <>
            <div className="px-2 py-1 mb-1">
              <span className="text-[8px] font-semibold text-gray-400 uppercase tracking-wider">
                Analytics
              </span>
            </div>
            {analyticsNav.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname?.startsWith(item.href + "/"));
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
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  />
                  <span
                    className={cn(
                      "text-[10px] font-bold text-center leading-tight",
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  >
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
            <div className="px-2 py-1 mt-3 mb-1">
              <span className="text-[8px] font-semibold text-gray-400 uppercase tracking-wider">
                Tenants
              </span>
            </div>
            {finalTenantsNav.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname?.startsWith(item.href + "/"));
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
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  />
                  <span
                    className={cn(
                      "text-[10px] font-bold text-center leading-tight",
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  >
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
            <div className="px-2 py-1 mt-3 mb-1">
              <span className="text-[8px] font-semibold text-gray-400 uppercase tracking-wider">
                Resources
              </span>
            </div>
            {resourcesNav.map((item) => {
              const isActive =
                pathname === item.href ||
                (item.href !== "/" && pathname?.startsWith(item.href + "/"));
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
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  />
                  <span
                    className={cn(
                      "text-[10px] font-bold text-center leading-tight",
                      isActive
                        ? "text-blue-600"
                        : "text-gray-900 group-hover:text-black"
                    )}
                  >
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </>
        )}
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
              pathname === "/settings"
                ? "text-blue-600"
                : "text-gray-900 group-hover:text-black"
            )}
          />
          <span
            className={cn(
              "text-[10px] font-bold text-center leading-tight",
              pathname === "/settings"
                ? "text-blue-600"
                : "text-gray-900 group-hover:text-black"
            )}
          >
            Settings
          </span>
        </Link>

        {isLoaded && user ? (
          <div className="relative flex items-center justify-center">
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
            className="group flex flex-col items-center justify-center rounded-lg py-2 px-1 transition-all duration-200 text-gray-900 hover:bg-gray-100 w-full"
          >
            <Settings2
              strokeWidth={2.5}
              className="h-5 w-5 mb-1 transition-colors"
            />
            <span className="text-[10px] font-bold text-center leading-tight">
              Sign In
            </span>
          </Link>
        )}
      </div>
    </div>
  );
}
