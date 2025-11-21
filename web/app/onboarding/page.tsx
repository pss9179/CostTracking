"use client";

import { ArrowRight, Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useUser, useOrganizationList } from "@clerk/nextjs";

export default function OnboardingPage() {
  const router = useRouter();
  const { user, isLoaded: isUserLoaded } = useUser();
  const { createOrganization, setActive, userMemberships, isLoaded: isOrgListLoaded } = useOrganizationList({
    userMemberships: {
      infinite: true,
    },
  });
  
  const [orgName, setOrgName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agreed, setAgreed] = useState(false);

  // Redirect if user already has organizations
  useEffect(() => {
    if (isOrgListLoaded && userMemberships.count > 0) {
      // If they have an active org, go to overview, otherwise select the first one and go
      const firstOrg = userMemberships.data[0].organization;
      if (setActive) {
        setActive({ organization: firstOrg.id }).then(() => {
           router.push("/overview");
        });
      } else {
         router.push("/overview");
      }
    }
  }, [isOrgListLoaded, userMemberships, router, setActive]);

  const handleContinue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!orgName.trim() || !user || !createOrganization || !setActive) return;

    setIsLoading(true);

    try {
      const org = await createOrganization({ name: orgName });
      await setActive({ organization: org.id });
      
      // Save organization metadata if needed (optional, as Clerk handles orgs now)
      localStorage.setItem(`user_${user.id}_type`, "multi");
      localStorage.setItem(`user_${user.id}_org_name`, orgName);

      router.push("/overview");
    } catch (err) {
      console.error("Failed to create organization:", err);
      setIsLoading(false);
      // Ideally show an error message to the user
    }
  };

  if (!isUserLoaded || !isOrgListLoaded) {
     return null; // Or a loading spinner
  }

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 relative overflow-hidden bg-white">
      <div className="w-full max-w-lg relative z-10">
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-10 space-y-8 border border-gray-100">
          <div className="text-center space-y-3">
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">
              Plant your flag
            </h1>
            <p className="text-gray-500 text-lg">
              You can invite team members after setting up your organization.
            </p>
          </div>

          <form onSubmit={handleContinue} className="space-y-6">
            <div className="space-y-2">
              <label htmlFor="orgName" className="block text-sm font-medium text-gray-700">
                Organization Name
              </label>
              <div className="relative">
                <input
                  id="orgName"
                  name="orgName"
                  type="text"
                  required
                  className="block w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-gray-900 placeholder:text-gray-400 bg-gray-50"
                  placeholder="Acme Corp"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                />
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
              </div>
              <div className="text-sm">
                <label htmlFor="terms" className="font-medium text-gray-700">
                  I agree to the <a href="#" className="text-blue-600 hover:text-blue-500">Terms of Service</a> and <a href="#" className="text-blue-600 hover:text-blue-500">Privacy Policy</a>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={!orgName.trim() || isLoading}
              className={cn(
                "w-full flex justify-center items-center py-3.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-[0.98]",
                isLoading && "opacity-70 cursor-wait"
              )}
            >
              {isLoading ? (
                "Creating organization..."
              ) : (
                <>
                  Create organization
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-gray-400 text-sm">
            Powered by Skyline Cost Observability
          </p>
        </div>
      </div>
    </div>
  );
}
