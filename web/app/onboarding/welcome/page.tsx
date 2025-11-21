"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { BookOpen, Key, ArrowRight, Activity } from "lucide-react";
import { ProtectedLayout } from "@/components/ProtectedLayout";

export default function WelcomePage() {
    const router = useRouter();

    const handleComplete = (destination: string) => {
        // Mark onboarding as complete
        localStorage.setItem("onboardingComplete", "true");
        router.push(destination);
    };

    return (
        <ProtectedLayout>
            <div className="max-w-4xl mx-auto py-12 px-4">
                <div className="text-center mb-12 space-y-4">
                    <div className="inline-flex items-center justify-center p-3 bg-indigo-100 rounded-full mb-4">
                        <Activity className="h-8 w-8 text-indigo-600" />
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight text-gray-900">
                        Welcome to LLM Observe
                    </h1>
                    <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                        Your dashboard is ready. Connect your first application to start tracking costs, latency, and quality.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                    <Card className="border-2 border-transparent hover:border-indigo-100 transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer group" onClick={() => handleComplete("/api-docs")}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-indigo-600">
                                <BookOpen className="h-5 w-5" />
                                Read the Docs
                            </CardTitle>
                            <CardDescription>
                                Learn how to integrate the SDK in minutes
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-gray-600 mb-6">
                                Follow our quickstart guide to instrument your Python or Node.js application with just a few lines of code.
                            </p>
                            <Button
                                variant="ghost"
                                className="w-full justify-between group-hover:bg-indigo-50 group-hover:text-indigo-700"
                            >
                                View Documentation
                                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                            </Button>
                        </CardContent>
                    </Card>

                    <Card className="border-2 border-transparent hover:border-indigo-100 transition-all duration-200 shadow-sm hover:shadow-md cursor-pointer group" onClick={() => handleComplete("/settings")}>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-indigo-600">
                                <Key className="h-5 w-5" />
                                Get API Key
                            </CardTitle>
                            <CardDescription>
                                Generate your first API key
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-gray-600 mb-6">
                                Create a production or development API key to authenticate your requests and start sending data.
                            </p>
                            <Button
                                variant="ghost"
                                className="w-full justify-between group-hover:bg-indigo-50 group-hover:text-indigo-700"
                            >
                                Go to Settings
                                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
                            </Button>
                        </CardContent>
                    </Card>
                </div>

                <div className="mt-12 text-center">
                    <p className="text-sm text-gray-500">
                        Already integrated? <button onClick={() => handleComplete("/dashboard")} className="text-indigo-600 hover:underline font-medium">Go to Dashboard</button>
                    </p>
                </div>
            </div>
        </ProtectedLayout>
    );
}
