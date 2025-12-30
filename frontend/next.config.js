/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  devIndicators: {
    appIsrStatus: false,
    buildActivity: false,
    buildActivityPosition: "bottom-right",
  },
  // Suppress hydration warnings from browser extensions
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  // Disable static optimization to prevent hydration mismatches
  experimental: {
    optimizePackageImports: [],
  },
};

module.exports = nextConfig;

