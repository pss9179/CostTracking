"use client";

import React from "react";
import Link from "next/link";

export default function OverviewPage() {
  return (
    <div className="h-full bg-gradient-to-b from-blue-50 via-white to-white flex flex-col items-center p-8 text-center relative overflow-hidden">
      {/* Main Content */}
      <div className="max-w-2xl w-full flex flex-col items-center space-y-8 z-10 pt-24">
        {/* Welcome Text */}
        <div className="space-y-4">
          <h1 className="text-5xl font-bold text-gray-900">
            Welcome to Skyline
          </h1>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row w-full max-w-md gap-3">
          <Link
            href="/settings"
            className="w-full bg-[#2563EB] hover:bg-[#1d4ed8] text-white font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center shadow-lg"
          >
            Get your API key
          </Link>
          <Link
            href="/api-docs"
            className="w-full bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors flex items-center justify-center shadow-sm"
          >
            View documentation
          </Link>
        </div>
      </div>

      {/* City Skyline Illustration */}
      <div className="absolute bottom-0 left-0 right-0 w-full h-64 z-0">
        <svg
          viewBox="0 0 1200 300"
          className="w-full h-full"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Sky gradient */}
          <defs>
            <linearGradient id="skyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop
                offset="0%"
                style={{ stopColor: "#dbeafe", stopOpacity: 0.3 }}
              />
              <stop
                offset="100%"
                style={{ stopColor: "#93c5fd", stopOpacity: 0.1 }}
              />
            </linearGradient>
            <linearGradient
              id="buildingGradient1"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                style={{ stopColor: "#3b82f6", stopOpacity: 0.8 }}
              />
              <stop
                offset="100%"
                style={{ stopColor: "#2563eb", stopOpacity: 0.9 }}
              />
            </linearGradient>
            <linearGradient
              id="buildingGradient2"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                style={{ stopColor: "#2563eb", stopOpacity: 0.7 }}
              />
              <stop
                offset="100%"
                style={{ stopColor: "#1d4ed8", stopOpacity: 0.8 }}
              />
            </linearGradient>
            <linearGradient
              id="buildingGradient3"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop
                offset="0%"
                style={{ stopColor: "#1d4ed8", stopOpacity: 0.6 }}
              />
              <stop
                offset="100%"
                style={{ stopColor: "#1e40af", stopOpacity: 0.7 }}
              />
            </linearGradient>
          </defs>

          {/* Sky background */}
          <rect width="1200" height="300" fill="url(#skyGradient)" />

          {/* Buildings from left to right */}
          {/* Building 1 - Tall */}
          <rect
            x="0"
            y="180"
            width="80"
            height="120"
            fill="url(#buildingGradient1)"
            opacity="0.9"
          />
          <rect
            x="10"
            y="200"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="30"
            y="220"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="55"
            y="200"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 2 - Medium */}
          <rect
            x="100"
            y="220"
            width="70"
            height="80"
            fill="url(#buildingGradient2)"
            opacity="0.85"
          />
          <rect
            x="115"
            y="240"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="140"
            y="240"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 3 - Short */}
          <rect
            x="190"
            y="250"
            width="60"
            height="50"
            fill="url(#buildingGradient3)"
            opacity="0.8"
          />
          <rect
            x="205"
            y="260"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="230"
            y="260"
            width="15"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 4 - Very Tall */}
          <rect
            x="270"
            y="120"
            width="90"
            height="180"
            fill="url(#buildingGradient1)"
            opacity="0.95"
          />
          <rect
            x="290"
            y="150"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="320"
            y="150"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="290"
            y="190"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="320"
            y="190"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="290"
            y="230"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="320"
            y="230"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.5"
          />

          {/* Building 5 - Medium Tall */}
          <rect
            x="380"
            y="160"
            width="75"
            height="140"
            fill="url(#buildingGradient2)"
            opacity="0.9"
          />
          <rect
            x="400"
            y="190"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="430"
            y="190"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="400"
            y="230"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="430"
            y="230"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 6 - Short */}
          <rect
            x="475"
            y="240"
            width="65"
            height="60"
            fill="url(#buildingGradient3)"
            opacity="0.8"
          />
          <rect
            x="495"
            y="250"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="520"
            y="250"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 7 - Tall */}
          <rect
            x="560"
            y="140"
            width="85"
            height="160"
            fill="url(#buildingGradient1)"
            opacity="0.9"
          />
          <rect
            x="580"
            y="170"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="610"
            y="170"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="580"
            y="210"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="610"
            y="210"
            width="20"
            height="25"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 8 - Medium */}
          <rect
            x="665"
            y="200"
            width="70"
            height="100"
            fill="url(#buildingGradient2)"
            opacity="0.85"
          />
          <rect
            x="685"
            y="230"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="710"
            y="230"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 9 - Short Wide */}
          <rect
            x="755"
            y="250"
            width="80"
            height="50"
            fill="url(#buildingGradient3)"
            opacity="0.8"
          />
          <rect
            x="775"
            y="260"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="805"
            y="260"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 10 - Very Tall */}
          <rect
            x="855"
            y="100"
            width="95"
            height="200"
            fill="url(#buildingGradient1)"
            opacity="0.95"
          />
          <rect
            x="880"
            y="130"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="915"
            y="130"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="880"
            y="175"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="915"
            y="175"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="880"
            y="220"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />
          <rect
            x="915"
            y="220"
            width="22"
            height="28"
            fill="#60a5fa"
            opacity="0.5"
          />

          {/* Building 11 - Medium */}
          <rect
            x="970"
            y="180"
            width="75"
            height="120"
            fill="url(#buildingGradient2)"
            opacity="0.9"
          />
          <rect
            x="990"
            y="210"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1020"
            y="210"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="990"
            y="250"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1020"
            y="250"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 12 - Short */}
          <rect
            x="1065"
            y="240"
            width="60"
            height="60"
            fill="url(#buildingGradient3)"
            opacity="0.8"
          />
          <rect
            x="1080"
            y="250"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1105"
            y="250"
            width="18"
            height="20"
            fill="#60a5fa"
            opacity="0.6"
          />

          {/* Building 13 - Tall */}
          <rect
            x="1145"
            y="150"
            width="55"
            height="150"
            fill="url(#buildingGradient1)"
            opacity="0.9"
          />
          <rect
            x="1155"
            y="180"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1175"
            y="180"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1155"
            y="220"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
          <rect
            x="1175"
            y="220"
            width="18"
            height="22"
            fill="#60a5fa"
            opacity="0.6"
          />
        </svg>
      </div>
    </div>
  );
}
