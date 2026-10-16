import { NextResponse, type NextRequest } from "next/server";
import { LOCATOR_COOKIE, locatorCookieOptions, locatorToIssue } from "@/lib/episode-locator";

/**
 * Slice 22 (Gate 2 D21): a first visit to the patient route gets a signed locator before the
 * page renders, so the start screen needs one press. This is the `/example` bootstrap moved
 * earlier: no backend call, no episode, no disposition. Any failure passes the request through.
 */
export const config = { matcher: ["/"], runtime: "nodejs" };

export function middleware(request: NextRequest) {
  try {
    const cookie = locatorToIssue(request.cookies.get(LOCATOR_COOKIE)?.value, process.env.CARERELAY_API_TOKEN ?? "");
    if (cookie === null) return NextResponse.next();
    const options = locatorCookieOptions(new URL(request.url), process.env.CARERELAY_LOOPBACK_TEST === "1");
    request.cookies.set(LOCATOR_COOKIE, cookie);
    const response = NextResponse.next({ request: { headers: request.headers } });
    response.cookies.set(LOCATOR_COOKIE, cookie, options);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    return NextResponse.next();
  }
}
