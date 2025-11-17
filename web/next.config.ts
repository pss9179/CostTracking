import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // Disable Turbopack to use webpack (for better control over module resolution)
  // This allows us to exclude server-only Clerk modules from client bundle
  experimental: {
    turbo: {
      resolveAlias: {
        // Exclude server-only Clerk modules from client bundle
        '@clerk/nextjs/server': false,
        '@clerk/nextjs/dist/esm/app-router/server': false,
        '@clerk/nextjs/dist/esm/server': false,
      },
    },
  },
  webpack: (config, { isServer }) => {
    // Exclude server-only Clerk modules from client bundle (fallback for non-Turbopack)
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
};

export default nextConfig;
