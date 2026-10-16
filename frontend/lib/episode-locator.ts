/** Server-only crypto; the codec receives its key and never stores credentials. */
import { createHash, createHmac, randomUUID, timingSafeEqual } from "node:crypto";
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
/**
 * Slice 22 middleware bootstrap: issue a locator only when the request carries none.
 * An existing cookie, valid or not, is left for the page to judge; nothing reaches the backend.
 */
export function locatorToIssue(existing: string | undefined, key: string): string | null {
  if (existing !== undefined) return null;
  return encodeLocator(newLocator(), key);
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

export type OperationBinding = { operation_id: string; episode_id: string; disposition_version: number | null;
  expected_revision: number; kind: string; purpose: string; body_sha256: string;
  parent_restatement_id: string | null; confirmation_id: string | null; token_schema: "carerelay-command-v1" };
function commandMac(payload: string, key: string): Buffer {
  if (!key.trim()) throw new Error("operation unavailable");
  const separated = createHmac("sha256", key).update("carerelay:command:v1").digest();
  return createHmac("sha256", separated).update(payload).digest();
}
function ordered(value: Record<string, unknown>): string {
  return JSON.stringify(Object.fromEntries(Object.keys(value).sort().map(k => [k, value[k]])));
}
export function creationOperation(locator: EpisodeLocator, key: string): string {
  const digest = createHash("sha256").update(ordered({ kind: "create", payload: {}, schema: "carerelay-command-v1" })).digest("hex");
  const binding: OperationBinding = { operation_id: locator.operation_id, episode_id: locator.episode_id,
    disposition_version: null, expected_revision: 0, kind: "create", purpose: "episode:create",
    body_sha256: digest, parent_restatement_id: null, confirmation_id: null, token_schema: "carerelay-command-v1" };
  const payload = Buffer.from(ordered(binding)).toString("base64url");
  return `${payload}.${commandMac(payload, key).toString("base64url")}`;
}
export function decodeOperation(token: string, key: string): OperationBinding | null {
  try {
    if (token.length > 4096 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(token)) return null;
    const [payload, signature] = token.split(".");
    const actual = Buffer.from(signature, "base64url"), expected = commandMac(payload, key);
    if (actual.length !== expected.length || actual.toString("base64url") !== signature || !timingSafeEqual(actual, expected)) return null;
    const raw = Buffer.from(payload, "base64url");
    if (raw.toString("base64url") !== payload) return null;
    const value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(raw));
    if (!value || typeof value !== "object" || Array.isArray(value) ||
        Object.keys(value).sort().join(",") !== "body_sha256,confirmation_id,disposition_version,episode_id,expected_revision,kind,operation_id,parent_restatement_id,purpose,token_schema") return null;
    if (ordered(value) !== raw.toString("utf8") || value.token_schema !== "carerelay-command-v1" ||
        !Number.isSafeInteger(value.expected_revision) || value.expected_revision < 0 ||
        typeof value.episode_id !== "string" || !UUID.test(value.episode_id) ||
        typeof value.operation_id !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(value.operation_id) ||
        typeof value.body_sha256 !== "string" || !/^[0-9a-f]{64}$/.test(value.body_sha256)) return null;
    if (["create", "select_example"].includes(value.kind)) {
      if (value.disposition_version !== null || value.parent_restatement_id !== null || value.confirmation_id !== null ||
          value.purpose !== `episode:${value.kind}`) return null;
    } else if (["select_barrier", "grant_share", "decline_share", "revoke_share", "request"].includes(value.kind)) {
      if (!Number.isSafeInteger(value.disposition_version) || value.disposition_version < 1 ||
          value.parent_restatement_id !== null || value.confirmation_id !== null ||
          value.purpose !== `disposition:${value.disposition_version}:${value.kind === "request" ? "request_appointment" : value.kind}`) return null;
    } else {
      if (!["readback_started", "confirm_words", "score_words", "repair_words", "show_plan", "hide_plan", "h3", "supersede_extraction"].includes(value.kind) ||
          !Number.isSafeInteger(value.disposition_version) || value.disposition_version < 1) return null;
      for (const ref of [value.parent_restatement_id, value.confirmation_id]) {
        if (ref !== null && (typeof ref !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(ref))) return null;
      }
      const parts = value.purpose.split(":");
      if (parts.length !== 5 || parts[0] !== "disposition" || parts[1] !== String(value.disposition_version) ||
          parts[2] !== "readback" || !/^[A-Za-z0-9_-]{1,128}$/.test(parts[3]) || parts[4] !== value.kind) return null;
      if (value.kind === "readback_started" && parts[3] !== "none") return null;
      if (["confirm_words", "score_words", "repair_words", "h3", "supersede_extraction"].includes(value.kind) && parts[3] === "none") return null;
      if (["readback_started", "show_plan", "hide_plan", "h3"].includes(value.kind) &&
          (value.parent_restatement_id !== null || value.confirmation_id !== null)) return null;
      if (value.kind === "confirm_words" && value.confirmation_id !== null) return null;
      if (["score_words", "repair_words", "supersede_extraction"].includes(value.kind) && value.confirmation_id === null) return null;
      if (value.kind === "score_words" && value.parent_restatement_id !== null) return null;
      if (value.kind === "repair_words" && value.parent_restatement_id === null) return null;
    }
    return value as OperationBinding;
  } catch { return null; }
}

/** Host/Origin and cookie checks happen before any backend call. */
export function allowAction(origin: string | null, host: string | null, cookie: string | undefined,
                            token: string, key: string, kind: string,
                            loopbackTest: boolean): EpisodeLocator | null {
  try {
    const locator = allowPreparation(origin, host, cookie, key, loopbackTest);
    const binding = decodeOperation(token, key);
    if (!locator || !binding || binding.kind !== kind || binding.episode_id !== locator.episode_id) return null;
    if (kind === "create" && (binding.operation_id !== locator.operation_id || binding.expected_revision !== 0)) return null;
    return locator;
  } catch { return null; }
}

export function allowPreparation(origin: string | null, host: string | null, cookie: string | undefined,
                                 key: string, loopbackTest: boolean): EpisodeLocator | null {
  try {
    if (!origin || !host) return null;
    const url = new URL(origin);
    if (url.username || url.password || url.search || url.hash || url.pathname !== "/" ||
        url.host.toLowerCase() !== host.toLowerCase()) return null;
    locatorCookieOptions(url, loopbackTest);
    return cookie ? decodeLocator(cookie, key) : null;
  } catch { return null; }
}

export function confirmedWordsDigest(text: string, parentId: string | null): string {
  return createHash("sha256").update(ordered({ kind: "confirm_words",
    payload: { parent_id: parentId, text }, schema: "carerelay-command-v1" })).digest("hex");
}

export function barrierChoiceDigest(choiceId: string): string {
  return createHash("sha256").update(ordered({ kind: "select_barrier",
    payload: { choice_id: choiceId }, schema: "carerelay-command-v1" })).digest("hex");
}
