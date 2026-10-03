/** @type {import('next').NextConfig} */
// Slice 7. Deliberately almost empty.
//
// There is no rewrite proxying the API through this app. If the browser could
// reach the Render service through a same-origin path, the bearer token would
// have to be forwarded from somewhere the browser can see, which is the one
// thing the token's whole design is trying to avoid. Every call leaves from the
// server instead: see `lib/api.ts`.
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
