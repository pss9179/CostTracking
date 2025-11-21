"use client";

import React from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

export default function OverviewPage() {
  return (
    <div className="h-full bg-white flex flex-col items-center justify-start p-8 pt-32 text-center">
      <div className="max-w-2xl w-full flex flex-col items-center space-y-8">
        
        {/* Welcome Text */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome to Skyline
          </h1>
          <p className="text-gray-500">
            Analytics will show in Dashboard after your first run.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col w-full max-w-md space-y-3">
          <Link
            href="/docs"
            className="w-full bg-[#2563EB] hover:bg-[#1d4ed8] text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center"
          >
            View documentation
          </Link>
          <button
            className="w-full bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center"
            onClick={() => alert("API Key generation coming soon!")}
          >
            Get your API key
          </button>
        </div>

      </div>
    </div>
  );
}
