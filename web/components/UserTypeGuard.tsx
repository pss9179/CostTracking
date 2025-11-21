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
        const isOnboarding = pathname === "/onboarding";

        if (!userType && !isOnboarding) {
            // No type selected, force onboarding
            router.push("/onboarding");
        } else if (userType && isOnboarding) {
            // Already selected, prevent re-onboarding
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
