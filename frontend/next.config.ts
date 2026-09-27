import type { NextConfig } from "next";

// The demo build (bun run build:demo) is a static site with no backend; see
// src/lib/demo.ts. DEMO_BASE_PATH serves it from a subfolder, e.g. /leasebuddy.
const isDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const nextConfig: NextConfig = isDemo
  ? {
      output: "export",
      basePath: process.env.DEMO_BASE_PATH || "",
      trailingSlash: true,
      devIndicators: false,
    }
  : {
      output: "standalone",
      devIndicators: false,
    };

export default nextConfig;
