import { NextRequest, NextResponse } from "next/server";
import { encodeLocator, newLocator, locatorCookieOptions, LOCATOR_COOKIE } from "@/lib/episode-locator";

/** Read-only bootstrap: no backend, episode, disposition or action is created. */
export function GET(request: NextRequest) {
  try {
    const options = locatorCookieOptions(new URL(request.url), process.env.CARERELAY_LOOPBACK_TEST === "1");
    const cookie = encodeLocator(newLocator(), process.env.CARERELAY_API_TOKEN ?? "");
    const response = new NextResponse(null, { status: 303, headers: { Location: "/" } });
    response.cookies.set(LOCATOR_COOKIE, cookie, options);
    response.headers.set("Cache-Control", "no-store");
    return response;
  } catch {
    // Never replace a lost/invalid bootstrap with a create or a guessed plan.
    return new NextResponse(null, { status: 303, headers: { Location: "/?recovery=1", "Cache-Control": "no-store" } });
  }
}
