"use client";

import { usePathname, useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

export function UserTypeGuard({ children }: { children: React.ReactNode }) {
    const { isLoaded, isSignedIn } = useUser();
    const router = useRouter();
    const pathname = usePathname();
    const [checked, setChecked] = useState(false);

    useEffect(() => {
        if (!isLoaded) return;

        // Allow public routes without check
        if (!isSignedIn) {
            setChecked(true);
            return;
        }

        const userType = localStorage.getItem("userType");
        const onboardingComplete = localStorage.getItem("onboardingComplete");
        const isOnboarding = pathname === "/onboarding";
        const isWelcome = pathname === "/onboarding/welcome";

        if (!userType && !isOnboarding) {
            // Step 1: No type selected -> Force selection
            router.push("/onboarding");
        } else if (userType && !onboardingComplete && !isWelcome) {
            // Step 2: Type selected but not complete -> Force welcome
            router.push("/onboarding/welcome");
        } else if (userType && onboardingComplete && (isOnboarding || isWelcome)) {
            // Step 3: Complete -> Prevent re-entry
            router.push("/dashboard");
        } else {
            // All good
            setChecked(true);
        }
    }, [isLoaded, isSignedIn, pathname, router]);

    // Optional: Show loading state while checking
    if (!checked) {
        return null; // or a loading spinner
    }

    return <>{children}</>;
}
