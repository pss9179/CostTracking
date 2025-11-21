import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Disable Turbopack - it doesn't support boolean false in resolveAlias
  // Use webpack instead, which supports false aliases to exclude modules
  // This fixes: "boolean values are invalid in exports field entries"
  // Note: Removing experimental.turbo as it's not a valid key in Next.js 16
  // Webpack will be used automatically when Turbopack is not explicitly enabled
  webpack: (config, { isServer }) => {
    // Exclude server-only Clerk modules from client bundle
    // This prevents 'server-only' and node:async_hooks errors in client bundle
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        '@clerk/nextjs/server': false,
        '@clerk/nextjs/dist/esm/app-router/server': false,
        '@clerk/nextjs/dist/esm/server': false,
      };
    }
    return config;
  },
  turbopack: {},
};

export default nextConfig;
