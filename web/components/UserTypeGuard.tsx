"use client";

import { usePathname, useRouter } from "next/navigation";
import { useUser, useOrganizationList } from "@clerk/nextjs";
import { useEffect, useState } from "react";

// Routes that should bypass the guard entirely (auth + public docs)
const PUBLIC_ROUTES = ["/sign-in", "/sign-up", "/sso-callback", "/api-docs", "/docs"];

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

    // Check if current route is a public route - render immediately without waiting
    const isPublicRoute = PUBLIC_ROUTES.some(route => pathname?.startsWith(route));

    useEffect(() => {
        // Public routes bypass all checks - render immediately
        if (isPublicRoute) {
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
    }, [isLoaded, isOrgListLoaded, isSignedIn, user, userMemberships, pathname, router, isPublicRoute]);

    // Public routes render immediately without waiting for Clerk
    if (isPublicRoute) {
        return <>{children}</>;
    }

    // Show loading state while checking (only for non-auth routes)
    if (!checked) {
        return null; // or a loading spinner
    }

    return <>{children}</>;
}
