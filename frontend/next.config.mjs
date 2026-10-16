/** @type {import('next').NextConfig} */
// Slice 7. Deliberately almost empty.
//
// There is no rewrite proxying the API through this app. If the browser could
// reach the Render service through a same-origin path, the bearer token would
// have to be forwarded from somewhere the browser can see, which is the one
// thing the token's whole design is trying to avoid. Every call leaves from the
// server instead: see `lib/api.ts`.
//
// Slice 22 (Gate 2 D19): only this app may frame its pages. The judge stage frames
// the patient route; no other site can.
const nextConfig = {
  reactStrictMode: true,
  async headers() {
    return [{ source: "/:path*", headers: [{ key: "Content-Security-Policy", value: "frame-ancestors 'self'" }] }];
  },
};

export default nextConfig;
