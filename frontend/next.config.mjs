import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The default indicator sits on the bottom-left and covers Optimize route.
  devIndicators: false,

  // Pin the workspace root to this frontend directory so Next doesn't
  // walk upwards and get confused by any stray lockfiles higher in the
  // filesystem (common on dev machines with user-level package.json's).
  outputFileTracingRoot: __dirname,
  output: process.env.NEXT_STANDALONE === "1" ? "standalone" : undefined,
  poweredByHeader: false,
  async rewrites() {
    const origin = process.env.API_PROXY_URL ?? "http://127.0.0.1:8000";
    return [{ source: "/api/:path*", destination: `${origin}/api/:path*` }];
  },
};

export default nextConfig;
