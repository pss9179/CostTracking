"use client";

import { User, Building2, Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";

import { useUser } from "@clerk/nextjs";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useUser();
  const [selected, setSelected] = useState<"solo" | "multi" | null>(null);

  const handleContinue = () => {
    if (!selected || !user) return;

    // Save selection to localStorage
    localStorage.setItem(`user_${user.id}_type`, selected);

    // Redirect to welcome page
    router.push("/onboarding/welcome");
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-4xl w-full space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-gray-900">Welcome to LLM Observe</h1>
          <p className="text-xl text-gray-600">Tell us a bit about how you plan to use the platform.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mt-12">
          {/* Solo Developer Card */}
          <button
            onClick={() => setSelected("solo")}
            className={cn(
              "relative group p-8 rounded-2xl border-2 transition-all duration-200 text-left hover:shadow-lg bg-white",
              selected === "solo"
                ? "border-indigo-600 ring-4 ring-indigo-50"
                : "border-gray-200 hover:border-indigo-200"
            )}
          >
            <div className={cn(
              "h-14 w-14 rounded-xl flex items-center justify-center mb-6 transition-colors",
              selected === "solo" ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-600 group-hover:bg-indigo-50 group-hover:text-indigo-600"
            )}>
              <User className="h-8 w-8" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Solo Developer</h3>
            <p className="text-gray-600 text-lg">
              Just me building cool stuff. I want to track my own API usage and costs.
            </p>

            {selected === "solo" && (
              <div className="absolute top-6 right-6 h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center text-white animate-in fade-in zoom-in duration-200">
                <Check className="h-5 w-5" />
              </div>
            )}
          </button>

          {/* Multi-tenant Card */}
          <button
            onClick={() => setSelected("multi")}
            className={cn(
              "relative group p-8 rounded-2xl border-2 transition-all duration-200 text-left hover:shadow-lg bg-white",
              selected === "multi"
                ? "border-indigo-600 ring-4 ring-indigo-50"
                : "border-gray-200 hover:border-indigo-200"
            )}
          >
            <div className={cn(
              "h-14 w-14 rounded-xl flex items-center justify-center mb-6 transition-colors",
              selected === "multi" ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-600 group-hover:bg-indigo-50 group-hover:text-indigo-600"
            )}>
              <Building2 className="h-8 w-8" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Software Company</h3>
            <p className="text-gray-600 text-lg">
              I have customers or users. I need to track costs per tenant/customer.
            </p>

            {selected === "multi" && (
              <div className="absolute top-6 right-6 h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center text-white animate-in fade-in zoom-in duration-200">
                <Check className="h-5 w-5" />
              </div>
            )}
          </button>
        </div>

        <div className="flex justify-center pt-8">
          <button
            onClick={handleContinue}
            disabled={!selected}
            className={cn(
              "px-8 py-4 rounded-xl text-lg font-semibold text-white transition-all duration-200 min-w-[200px]",
              selected
                ? "bg-indigo-600 hover:bg-indigo-700 shadow-lg hover:shadow-xl translate-y-0"
                : "bg-gray-300 cursor-not-allowed"
            )}
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
