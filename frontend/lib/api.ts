import "server-only";
import { readJourney, readCommand, type Journey, type CommandResult } from "./journey";
/**
 * The one place the frontend talks to the CareRelay API.
 *
 * **Server-side only.** Every function here reads `CARERELAY_API_TOKEN` from the
 * server process. None of them may be imported from a client component, and the
 * token must never appear in a payload sent to a browser: a bearer token in a
 * client bundle is a published token, and the guard on the Render service is the
 * only thing standing between the record and the open internet (risk R9).
 *
 * **It never invents a plan.** If the API cannot be reached, these functions
 * return an explicit unavailable result rather than fabricated lines. A
 * patient-facing screen that renders four confident lines it made up is the exact
 * false-completion failure CareRelay exists to prevent, and a network error is
 * not a reason to produce one.
 */

const API_URL = process.env.CARERELAY_API_URL ?? "http://127.0.0.1:8000";
const API_TOKEN = process.env.CARERELAY_API_TOKEN ?? "";

/**
 * There is deliberately **no** hardcoded demo episode id here.
 *
 * An earlier draft carried `"demo-episode-1"`. The live service returns
 * `demo-episode-001`, so the page rendered its "could not be reached" state on a
 * perfectly healthy API, and the bug was found by the smoke test rather than by
 * reading the code. The id is whatever the service says it is, and nothing else.
 */

export type PatientProjection = Journey;

/**
 * The three ways a call can end. `unavailable` is a first-class result, not an
 * exception to be swallowed, so a caller has to decide what to render for it.
 */
export type Result<T> =
  | { ok: true; value: T }
  | { ok: false; reason: "unavailable" | "unauthorised" | "not_found"; detail: string };

async function call<T>(
  path: string,
  init: RequestInit = {},
): Promise<Result<T>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  // Only sent when one is configured. The local demo runs with auth disarmed.
  if (API_TOKEN) {
    headers.Authorization = `Bearer ${API_TOKEN}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers, cache: "no-store" });
  } catch {
    return { ok: false, reason: "unavailable", detail: "the service could not be reached" };
  }

  if (response.status === 401 || response.status === 503) {
    return { ok: false, reason: "unauthorised", detail: `the service refused the call (${response.status})` };
  }
  if (response.status === 404) {
    return { ok: false, reason: "not_found", detail: "no such episode" };
  }
  if (!response.ok) {
    return { ok: false, reason: "unavailable", detail: `the service answered ${response.status}` };
  }
  return { ok: true, value: (await response.json()) as T };
}

/** Read-only, bounded and decoded; transport detail never becomes patient copy. */
export async function getEpisode(episodeId: string): Promise<Result<PatientProjection>> {
  try {
    const response = await fetch(`${API_URL}/api/episodes/${encodeURIComponent(episodeId)}`, {
      headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {},
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(5000),
    });
    if (response.status === 404) return { ok: false, reason: "not_found", detail: "journey unavailable" };
    const value = await readJourney(response, episodeId);
    return value ? { ok: true, value } : { ok: false, reason: "unavailable", detail: "journey unavailable" };
  } catch { return { ok: false, reason: "unavailable", detail: "journey unavailable" }; }
}

/** Exact user-selected mutations; response loss is recovered by a separate GET. */
export async function createCommand(episodeId: string, operationToken: string): Promise<Result<CommandResult>> {
  return command(`/api/episodes`, episodeId, { operation_token: operationToken });
}
export async function selectExampleCommand(episodeId: string, operationToken: string): Promise<Result<CommandResult>> {
  return command(`/api/episodes/${encodeURIComponent(episodeId)}/intake`, episodeId,
    { operation_token: operationToken, example_id: "scripted-appointment" });
}
async function command(path: string, episodeId: string, body: Record<string, string>): Promise<Result<CommandResult>> {
  try {
    const response = await fetch(`${API_URL}${path}`, { method: "POST", redirect: "error", cache: "no-store",
      signal: AbortSignal.timeout(5000), headers: { "Content-Type": "application/json", ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}) },
      body: JSON.stringify(body) });
    const value = await readCommand(response, episodeId);
    return value ? { ok: true, value } : { ok: false, reason: "unavailable", detail: "journey unavailable" };
  } catch { return { ok: false, reason: "unavailable", detail: "journey unavailable" }; }
}

/**
 * The judge ledger. A read of the record, and deliberately not the patient
 * screen: it shows the two axes, every transition with its failure-event
 * origin, the expiry rows, the five fault assertions and the dwell times.
 *
 * Nothing here is derived in the browser. `hold` is the server's verdict over
 * stored rows and `evidence` is the values it was taken from, so the page can
 * show both and a reader can disagree with the verdict.
 */
export type FaultAssertion = {
  invariant: string;
  holds: boolean;
  evidence: string;
};

export type LedgerTransition = {
  seq: number;
  kind: string;
  origin: string;
  recorded_at: string;
};

export type LedgerAttempt = {
  attempt_id: string;
  route_id: string;
  consent_version: number;
  execution: string;
  transitions: LedgerTransition[];
};

export type LedgerCallback = {
  receipt_id: number;
  route_id: string;
  accepted: boolean;
  rejection_reason: string | null;
  origin: string;
  result: string | null;
};

export type Ledger = {
  episode_id: string;
  axes: Record<string, string | boolean | null>;
  disposition_version: number | null;
  attempts: LedgerAttempt[];
  callbacks: LedgerCallback[];
  expiry: { disposition_version: number; recorded_at: string }[];
  hint_events: {
    hint_level: string;
    kind: string;
    dwell_seconds: number | null;
  }[];
  restatements: {
    outcome: string;
    repair_round: number;
    hint_level: string;
    dwell_seconds: number | null;
  }[];
  escalation: { escalation_id: string; human_path: string | null } | null;
  acceptance: { acceptance_id: string } | null;
  origins: string[];
  dwell_seconds_total: number | null;
  fault_assertions: FaultAssertion[];
  simulated: boolean;
  fixture_label: string;
};

/**
 * Read the ledger for one episode.
 *
 * If this fails the page says so rather than drawing an empty ledger: an empty
 * table reads as "nothing happened", which is a claim, and one no service made.
 */
export async function getLedger(episodeId: string): Promise<Result<Ledger>> {
  return call<Ledger>(`/api/episodes/${encodeURIComponent(episodeId)}/ledger`);
}
