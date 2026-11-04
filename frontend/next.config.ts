import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Tell Next the project root is THIS folder (not the home folder with a stray lockfile)
  turbopack: { root: path.resolve(__dirname) },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }
    ];
  },
};
export default nextConfig;
