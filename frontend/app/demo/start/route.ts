import { NextRequest, NextResponse } from "next/server";
import { encodeLocator, newLocator, locatorCookieOptions, LOCATOR_COOKIE } from "@/lib/episode-locator";

/**
 * Slice 24 (demo A): "Start the demo" always issues a fresh locator, so a stale or foreign
 * cookie can never leave a judge on "We cannot load your plan". No backend call, no episode.
 */
export function GET(request: NextRequest) {
  try {
    const options = locatorCookieOptions(new URL(request.url), process.env.CARERELAY_LOOPBACK_TEST === "1");
    const cookie = encodeLocator(newLocator(), process.env.CARERELAY_API_TOKEN ?? "");
    const response = new NextResponse(null, { status: 303, headers: { Location: "/demo/stage" } });
    response.cookies.set(LOCATOR_COOKIE, cookie, options);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return new NextResponse(null, { status: 303, headers: { Location: "/demo/stage", "Cache-Control": "no-store" } });
  }
}
