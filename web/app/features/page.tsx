"use client";

import { ProtectedLayout } from "@/components/ProtectedLayout";

export default function FeaturesPage() {
  return (
    <ProtectedLayout>
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4 max-w-md">
          <h1 className="text-4xl font-bold text-gray-900">Coming Soon!</h1>
          <p className="text-lg text-gray-600">
            Shows cost of each feature in your product
          </p>
        </div>
      </div>
    </ProtectedLayout>
  );
}
