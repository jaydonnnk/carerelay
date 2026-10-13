/** Server-only crypto; the codec receives its key and never stores credentials. */
import { createHmac, randomUUID, timingSafeEqual } from "node:crypto";
export const LOCATOR_COOKIE = "carerelay_demo_locator";
export type EpisodeLocator = { schema: "carerelay-locator-v1"; nonce: string;
  episode_id: string; operation_id: string };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
function valid(value: unknown): value is EpisodeLocator {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const x = value as Record<string, unknown>;
  return Object.keys(x).sort().join(",") === "episode_id,nonce,operation_id,schema" &&
    x.schema === "carerelay-locator-v1" &&
    [x.nonce, x.episode_id, x.operation_id].every(v => typeof v === "string" && UUID.test(v));
}
function mac(payload: string, key: string): Buffer {
  if (!key.trim()) throw new Error("locator unavailable");
  const separated = createHmac("sha256", key).update("carerelay:locator:v1").digest();
  return createHmac("sha256", separated).update(payload).digest();
}
export function newLocator(): EpisodeLocator {
  return { schema: "carerelay-locator-v1", nonce: randomUUID(), episode_id: randomUUID(), operation_id: randomUUID() };
}
export function encodeLocator(value: EpisodeLocator, key: string): string {
  if (!valid(value)) throw new Error("invalid locator");
  const payload = Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${payload}.${mac(payload, key).toString("base64url")}`;
}
export function decodeLocator(cookie: string, key: string): EpisodeLocator | null {
  try {
    if (cookie.length > 1024 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(cookie)) return null;
    const [payload, signature] = cookie.split(".");
    const bytes = Buffer.from(signature, "base64url");
    const expected = mac(payload, key);
    if (bytes.length !== expected.length || !timingSafeEqual(bytes, expected)) return null;
    if (bytes.toString("base64url") !== signature) return null;
    const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(Buffer.from(payload, "base64url")));
    return valid(value) ? value : null;
  } catch { return null; }
}
export function locatorCookieOptions(url: URL, loopbackTest: boolean) {
  const local = loopbackTest && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
  if (url.protocol !== "https:" && !(url.protocol === "http:" && local)) throw new Error("HTTPS required");
  return { httpOnly: true, secure: url.protocol === "https:", sameSite: "lax" as const, path: "/" };
}
