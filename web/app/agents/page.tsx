"use client";

import { ProtectedLayout } from "@/components/ProtectedLayout";

export default function AgentsPage() {
  return (
    <ProtectedLayout>
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4 max-w-md">
          <h1 className="text-4xl font-bold text-gray-900">Coming Soon!</h1>
          <p className="text-lg text-gray-600">
            Shows execution of all your agents and associated cost with each LLM
            tool call
          </p>
        </div>
      </div>
    </ProtectedLayout>
  );
}
