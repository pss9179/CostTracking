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
        const isOnboarding = pathname === "/onboarding";

        if (!userType && !isOnboarding) {
            // No organization created -> Force organization creation
            router.push("/onboarding");
        } else if (userType && isOnboarding) {
            // Organization created -> Redirect to overview
            router.push("/overview");
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
