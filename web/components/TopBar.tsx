"use client";

import { usePathname, useRouter } from "next/navigation";
import { useUser, useClerk } from "@clerk/nextjs";
import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";

export function TopBar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isSignedIn } = useUser();
  const { signOut } = useClerk();

  // Don't show top bar on auth pages or landing page
  if (pathname?.startsWith('/sign-') || pathname === '/') {
    return null;
  }

  const handleSignOut = async () => {
    try {
      await signOut({ redirectUrl: '/' });
      router.push('/');
    } catch (error) {
      console.error('Sign out error:', error);
      // Force redirect even if signOut fails
      router.push('/');
    }
  };

  return (
    <div className="flex items-center justify-between h-16 px-8 border-b bg-background">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">
          {pathname === "/dashboard" && "Dashboard"}
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
      {isSignedIn && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleSignOut}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </Button>
      )}
    </div>
  );
}

