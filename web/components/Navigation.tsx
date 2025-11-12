"use client";

import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Activity, Users, Settings, LogOut, User, BarChart3 } from "lucide-react";
import { loadAuth, clearAuth } from "@/lib/auth";
import { useEffect, useState } from "react";

export function Navigation() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const { user: loadedUser } = loadAuth();
    setUser(loadedUser);
  }, []);

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  const isActive = (path: string) => pathname === path;
  
  const isSaaSFounder = user?.user_type === "saas_founder";

  // Prevent hydration mismatch by only rendering on client
  if (!mounted) {
    return (
      <nav className="border-b bg-white">
        <div className="container mx-auto px-4">
          <div className="flex h-16 items-center justify-between">
            <Link href="/" className="flex items-center space-x-2">
              <Activity className="h-6 w-6 text-blue-600" />
              <span className="text-xl font-bold">LLMObserve</span>
            </Link>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <Activity className="h-6 w-6 text-blue-600" />
            <span className="text-xl font-bold">LLMObserve</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-1">
            <Link href="/">
              <Button
                variant={isActive("/") ? "default" : "ghost"}
                className="flex items-center space-x-2"
              >
                <BarChart3 className="h-4 w-4" />
                <span>Dashboard</span>
              </Button>
            </Link>

            {/* Only show Customers for SaaS founders */}
            {isSaaSFounder && (
              <Link href="/customers">
                <Button
                  variant={isActive("/customers") ? "default" : "ghost"}
                  className="flex items-center space-x-2"
                >
                  <Users className="h-4 w-4" />
                  <span>Customers</span>
                </Button>
              </Link>
            )}

            <Link href="/agents">
              <Button
                variant={isActive("/agents") ? "default" : "ghost"}
                className="flex items-center space-x-2"
              >
                <Activity className="h-4 w-4" />
                <span>Agents</span>
              </Button>
            </Link>
          </div>

          {/* User Menu */}
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
                  <span>{user.email}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user.name || user.email}</p>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push("/settings")}>
                  <Settings className="mr-2 h-4 w-4" />
                  <span>Settings</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Logout</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </div>
    </nav>
  );
}

