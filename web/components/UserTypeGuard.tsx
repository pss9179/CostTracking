"use client";

import { usePathname, useRouter } from "next/navigation";
import { useUser, useOrganizationList } from "@clerk/nextjs";
import { useEffect, useState } from "react";

// Auth routes that should bypass the guard entirely
const AUTH_ROUTES = ["/sign-in", "/sign-up", "/sso-callback"];

export function UserTypeGuard({ children }: { children: React.ReactNode }) {
    const { isLoaded, isSignedIn, user } = useUser();
    const { userMemberships, isLoaded: isOrgListLoaded } = useOrganizationList({
        userMemberships: {
            infinite: true,
        },
    });
    const router = useRouter();
    const pathname = usePathname();
    const [checked, setChecked] = useState(false);

    // Check if current route is an auth route - render immediately without waiting
    const isAuthRoute = AUTH_ROUTES.some(route => pathname?.startsWith(route));

    useEffect(() => {
        // Auth routes bypass all checks - render immediately
        if (isAuthRoute) {
            setChecked(true);
            return;
        }

        if (!isLoaded || !isOrgListLoaded) return;

        // Allow public routes without check
        if (!isSignedIn) {
            setChecked(true);
            return;
        }

        if (!user) return;

        // Check both localStorage AND Clerk organizations
        const userType = localStorage.getItem(`user_${user.id}_type`);
        const hasOrganizations = userMemberships && userMemberships.count > 0;
        const isOnboarding = pathname === "/onboarding";

        // If user has orgs in Clerk but no localStorage entry, fix it
        if (hasOrganizations && !userType) {
            localStorage.setItem(`user_${user.id}_type`, "multi");
        }

        const isOnboarded = userType || hasOrganizations;

        if (!isOnboarded && !isOnboarding) {
            // No organization created -> Force organization creation
            router.push("/onboarding");
        } else if (isOnboarded && isOnboarding) {
            // Organization created -> Redirect to overview
            router.push("/overview");
        } else {
            // All good
            setChecked(true);
        }
    }, [isLoaded, isOrgListLoaded, isSignedIn, user, userMemberships, pathname, router, isAuthRoute]);

    // Auth routes render immediately without waiting for Clerk
    if (isAuthRoute) {
        return <>{children}</>;
    }

    // Show loading state while checking (only for non-auth routes)
    if (!checked) {
        return null; // or a loading spinner
    }

    return <>{children}</>;
}
