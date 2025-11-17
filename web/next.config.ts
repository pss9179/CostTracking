import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
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
};

export default nextConfig;
