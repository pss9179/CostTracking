"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SignUp } from "@clerk/nextjs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { User, Building2 } from "lucide-react";

export default function SignUpPage() {
  const router = useRouter();
  const [userType, setUserType] = useState<"solo_dev" | "saas_founder" | null>(null);
  const [showClerkSignUp, setShowClerkSignUp] = useState(false);

  const handleUserTypeSelect = (type: "solo_dev" | "saas_founder") => {
    setUserType(type);
    setShowClerkSignUp(true);
    // Store user type in sessionStorage to use after Clerk signup
    if (typeof window !== "undefined") {
      sessionStorage.setItem("selectedUserType", type);
    }
  };

  if (!showClerkSignUp) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50 px-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-bold text-gray-900 mb-2">
              Choose your account type
            </CardTitle>
            <CardDescription className="text-lg text-gray-600">
              We'll customize your dashboard based on your needs
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <button
              onClick={() => handleUserTypeSelect("solo_dev")}
              className="w-full p-6 border-2 border-gray-200 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:bg-indigo-200 transition-colors">
                  <User className="w-6 h-6 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    Building for myself
                  </h3>
                  <p className="text-gray-600">
                    I'm building AI applications for my own use. I want to track costs and monitor my agents.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Cost tracking</span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Agent monitoring</span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Spending caps</span>
                  </div>
                </div>
              </div>
            </button>

            <button
              onClick={() => handleUserTypeSelect("saas_founder")}
              className="w-full p-6 border-2 border-gray-200 rounded-xl hover:border-indigo-500 hover:bg-indigo-50 transition-all text-left group"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:bg-indigo-200 transition-colors">
                  <Building2 className="w-6 h-6 text-indigo-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">
                    Selling SaaS to multiple customers
                  </h3>
                  <p className="text-gray-600">
                    I'm building a SaaS product and need to track costs per customer and manage multi-tenant observability.
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Multi-tenant</span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Per-customer costs</span>
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">Customer analytics</span>
                  </div>
                </div>
              </div>
            </button>

            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-500 text-center">
                Already have an account?{" "}
                <button
                  onClick={() => router.push("/sign-in")}
                  className="text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Sign in
                </button>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <SignUp
        appearance={{
          elements: {
            rootBox: "mx-auto",
            card: "bg-white border border-gray-200 shadow-lg rounded-2xl",
            headerTitle: "text-gray-900 text-2xl font-bold",
            headerSubtitle: "text-gray-600",
            socialButtonsBlockButton: "bg-white hover:bg-gray-50 border border-gray-200 text-gray-900 transition-all duration-200 shadow-sm",
            socialButtonsBlockButtonText: "text-gray-900 font-medium",
            formButtonPrimary: "bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-sm transition-all duration-200",
            formFieldInput: "bg-white border-gray-200 text-gray-900 placeholder:text-gray-400 focus:border-indigo-500 focus:ring-indigo-500",
            formFieldLabel: "text-gray-700",
            footerActionLink: "text-indigo-600 hover:text-indigo-700",
            identityPreviewText: "text-gray-900",
            identityPreviewEditButton: "text-indigo-600 hover:text-indigo-700",
            dividerLine: "bg-gray-200",
            dividerText: "text-gray-500",
            formResendCodeLink: "text-indigo-600 hover:text-indigo-700",
            alertText: "text-gray-900",
          },
          layout: {
            socialButtonsPlacement: "top",
          },
        }}
        routing="path"
        path="/sign-up"
        signUpFallbackRedirectUrl="/onboarding"
      />
    </div>
  );
}
