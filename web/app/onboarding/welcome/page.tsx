"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { BookOpen, Key } from "lucide-react";

export default function WelcomePage() {
    const router = useRouter();

    const handleComplete = (destination: string) => {
        // Mark onboarding as complete
        localStorage.setItem("onboardingComplete", "true");
        router.push(destination);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            <div className="max-w-2xl w-full text-center space-y-8">
                <div className="space-y-4">
                    <h1 className="text-4xl font-bold tracking-tight text-gray-900">
                        Welcome to The Context Company
                    </h1>
                    <p className="text-lg text-gray-600">
                        Analytics will show here once you send your first run.
                    </p>
                </div>

                <div className="flex flex-col gap-4 max-w-md mx-auto">
                    <Button
                        size="lg"
                        className="w-full h-14 text-lg bg-blue-600 hover:bg-blue-700 text-white"
                        onClick={() => handleComplete("/api-docs")}
                    >
                        <BookOpen className="mr-2 h-5 w-5" />
                        View documentation
                    </Button>

                    <Button
                        variant="outline"
                        size="lg"
                        className="w-full h-14 text-lg border-gray-200 hover:bg-gray-50 text-gray-900"
                        onClick={() => handleComplete("/settings")}
                    >
                        <Key className="mr-2 h-5 w-5" />
                        Get your API key
                    </Button>
                </div>

                <div className="pt-12 flex justify-center">
                    {/* Illustration placeholder - using a simple SVG for now to match the vibe */}
                    <svg
                        width="200"
                        height="100"
                        viewBox="0 0 200 100"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        className="text-gray-900"
                    >
                        <path
                            d="M20 80 C 50 80, 50 20, 80 20 S 110 80, 140 80 S 170 20, 200 20"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                        <circle cx="20" cy="80" r="4" fill="currentColor" />
                        <circle cx="80" cy="20" r="4" fill="currentColor" />
                        <circle cx="140" cy="80" r="4" fill="currentColor" />
                        <circle cx="200" cy="20" r="4" fill="currentColor" />
                    </svg>
                </div>
            </div>
        </div>
    );
}
