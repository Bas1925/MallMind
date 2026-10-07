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

  // Phase 9 (production) will set this to "standalone" for a smaller
  // Docker image. In Phase 0b we use the default build output.
  // output: "standalone",
};

export default nextConfig;
