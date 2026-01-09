"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Sparkles } from "lucide-react";
import { ProtectedLayout } from "@/components/ProtectedLayout";

export default function SubscriptionPage() {
  return (
    <ProtectedLayout>
      <div className="space-y-6 p-8">
        <div>
          <h1 className="text-3xl font-bold">Subscription</h1>
          <p className="text-gray-600 mt-2">Your plan details</p>
        </div>

        <Card className="border-emerald-200 bg-emerald-50/50">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-100 rounded-lg">
                <Sparkles className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <CardTitle className="flex items-center gap-2">
                  Free Forever
                  <Badge variant="default" className="bg-emerald-500">Active</Badge>
                </CardTitle>
                <CardDescription>All features included at no cost</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-gray-600">
                Enjoy unlimited access to all Skyline features. No credit card required, no usage limits.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-4">
                {[
                  "Unlimited LLM API tracking",
                  "All 40+ providers supported",
                  "Customer cost attribution",
                  "Spending caps & alerts",
                  "Feature-level analytics",
                  "Voice agent tracking",
                  "Export to CSV/JSON",
                  "API access",
                ].map((feature, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </ProtectedLayout>
  );
}
