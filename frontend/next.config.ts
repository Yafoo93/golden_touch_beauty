import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Keep the live development compiler isolated from `next build`. Running a
  // production validation while `next dev` is open must not overwrite its
  // manifests and force repeated browser remounts.
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  // The browser uses 127.0.0.1 so Django and Next share one cookie host.
  // Permit that host to access Next's development-only HMR resources.
  allowedDevOrigins: ["127.0.0.1"],
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";

    return [
      {
        source: "/backend-api/:path*",
        // Django/DRF routes use trailing slashes. Add the slash at the
        // destination so Next does not redirect the browser back through the
        // proxy and accidentally request a slashless Django endpoint.
        destination: `${backendUrl}/api/:path*/`,
      },
    ];
  },
};

export default nextConfig;
