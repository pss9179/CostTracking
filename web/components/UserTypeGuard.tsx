"use client";

import { usePathname, useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

export function UserTypeGuard({ children }: { children: React.ReactNode }) {
    const { isLoaded, isSignedIn, user } = useUser();
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

        if (!user) return;

        const userType = localStorage.getItem(`user_${user.id}_type`);
        const onboardingComplete = localStorage.getItem(`user_${user.id}_onboarding_complete`);
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
    }, [isLoaded, isSignedIn, user, pathname, router]);

    // Optional: Show loading state while checking
    if (!checked) {
        return null; // or a loading spinner
    }

    return <>{children}</>;
}
