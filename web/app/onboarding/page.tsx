"use client";

import { Building2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useUser } from "@clerk/nextjs";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useUser();
  const [orgName, setOrgName] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleContinue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim() || !user) return;

    setIsLoading(true);

    // Simulate API call/processing
    setTimeout(() => {
      // Save selection to localStorage
      localStorage.setItem(`user_${user.id}_type`, "multi");
      localStorage.setItem(`user_${user.id}_org_name`, orgName);

      // Redirect to overview
      router.push("/overview");
    }, 800);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
            Welcome to Skyline
          </h1>
          <p className="text-gray-500">
            Let's set up your organization workspace.
          </p>
        </div>

        <form onSubmit={handleContinue} className="mt-8 space-y-6">
          <div className="space-y-2">
            <label htmlFor="orgName" className="block text-sm font-medium text-gray-700">
              Organization Name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Building2 className="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="orgName"
                name="orgName"
                type="text"
                required
                className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-colors"
                placeholder="Acme Corp"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={!orgName.trim() || isLoading}
            className={cn(
              "w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed",
              isLoading && "opacity-70 cursor-wait"
            )}
          >
            {isLoading ? (
              "Setting up..."
            ) : (
              <>
                Continue to Dashboard
                <ArrowRight className="ml-2 h-4 w-4" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
