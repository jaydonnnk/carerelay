import "server-only";
import { readJourney, readCommand, readConflict, readPrepared, type Journey, type CommandResult, type ReadbackKind, type PermissionKind } from "./journey";
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
export type CommandOutcome = Result<CommandResult> | { ok: false; reason: "conflict"; journey: Journey; detail: string };

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

  if (response.status === 401) {
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
export async function createCommand(episodeId: string, operationToken: string): Promise<CommandOutcome> {
  return command(`/api/episodes`, episodeId, { operation_token: operationToken });
}
export async function selectExampleCommand(episodeId: string, operationToken: string): Promise<CommandOutcome> {
  return command(`/api/episodes/${encodeURIComponent(episodeId)}/intake`, episodeId,
    { operation_token: operationToken, example_id: "scripted-appointment" }, "select_example");
}
// Scoring waits for the approved 15-second live extraction plus two local
// transactions; every other command keeps the five-second bound. Never retried.
const COMMAND_TIMEOUT_MS = 5000;
const SCORING_TIMEOUT_MS = 20000;
async function command(path: string, episodeId: string, body: Record<string, string>, kind: "create" | "select_example" | ReadbackKind | PermissionKind = "create"): Promise<CommandOutcome> {
  try {
    const timeout = kind === "score_words" || kind === "repair_words" ? SCORING_TIMEOUT_MS : COMMAND_TIMEOUT_MS;
    const response = await fetch(`${API_URL}${path}`, { method: "POST", redirect: "error", cache: "no-store",
      signal: AbortSignal.timeout(timeout), headers: { "Content-Type": "application/json", ...(API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {}) },
      body: JSON.stringify(body) });
    if (response.status === 409) {
      const journey = await readConflict(response, episodeId);
      return journey ? { ok: false, reason: "conflict", journey, detail: "command conflict" } :
        { ok: false, reason: "unavailable", detail: "journey unavailable" };
    }
    const value = await readCommand(response, episodeId, kind);
    return value ? { ok: true, value } : { ok: false, reason: "unavailable", detail: "journey unavailable" };
  } catch { return { ok: false, reason: "unavailable", detail: "journey unavailable" }; }
}

export async function prepareWordsCommand(episodeId: string, digest: string, parentId: string | null): Promise<Result<string>> {
  try {
    const query = new URLSearchParams({ prepare_kind: "confirm_words", body_sha256: digest });
    if (parentId !== null) query.set("parent_id", parentId);
    const response = await fetch(`${API_URL}/api/episodes/${encodeURIComponent(episodeId)}?${query}`, {
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(5000),
      headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {},
    });
    const token = await readPrepared(response);
    return token ? { ok: true, value: token } : { ok: false, reason: "unavailable", detail: "journey unavailable" };
  } catch { return { ok: false, reason: "unavailable", detail: "journey unavailable" }; }
}

export async function readbackCommand(episodeId: string, token: string, kind: ReadbackKind,
                                     parentId: string | null, text?: string, oldId?: string): Promise<CommandOutcome> {
  const base = `/api/episodes/${encodeURIComponent(episodeId)}`;
  const body: Record<string, string> = { operation_token: token };
  let path: string;
  if (kind === "confirm_words" && text !== undefined) { path = `${base}/transcript-confirmations`; body.text = text; }
  else if (kind === "score_words") path = `${base}/restatements`;
  else if (kind === "repair_words" && parentId !== null) path = `${base}/restatements/${encodeURIComponent(parentId)}/repairs`;
  else if (["readback_started", "show_plan", "hide_plan", "h3"].includes(kind)) path = `${base}/journey-events`;
  else if (kind === "supersede_extraction" && oldId) path = `${base}/extractions/${encodeURIComponent(oldId)}/supersede`;
  else return { ok: false, reason: "unavailable", detail: "journey unavailable" };
  return command(path, episodeId, body, kind);
}

export async function prepareBarrierCommand(episodeId: string, digest: string): Promise<Result<string>> {
  try {
    const query = new URLSearchParams({ prepare_kind: "select_barrier", body_sha256: digest });
    const response = await fetch(`${API_URL}/api/episodes/${encodeURIComponent(episodeId)}?${query}`, {
      cache: "no-store", redirect: "error", signal: AbortSignal.timeout(5000),
      headers: API_TOKEN ? { Authorization: `Bearer ${API_TOKEN}` } : {},
    });
    const token = await readPrepared(response);
    return token ? { ok: true, value: token } : { ok: false, reason: "unavailable", detail: "journey unavailable" };
  } catch { return { ok: false, reason: "unavailable", detail: "journey unavailable" }; }
}

export async function permissionCommand(episodeId: string, token: string, kind: PermissionKind,
                                      choiceId?: string): Promise<CommandOutcome> {
  const base = `/api/episodes/${encodeURIComponent(episodeId)}`;
  const body: Record<string, string> = { operation_token: token };
  if (kind === "select_barrier") {
    if (!choiceId || !["booking", "transport", "other"].includes(choiceId)) return { ok: false, reason: "unavailable", detail: "journey unavailable" };
    body.choice_id = choiceId;
    return command(`${base}/barriers`, episodeId, body, kind);
  }
  return command(`${base}/${kind === "request" ? "actions" : "consents"}`, episodeId, body, kind);
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
    extraction_provenance: { mode: string; validation: string; confirmation_id: string;
      retained: { field: string; source_restatement_id: string; source_confirmation_id: string }[] } | null;
  }[];
  extractions: {
    operation_id: string;
    terminal_state: string;
    scored: boolean | number;
    interpreter_mode: string;
    instruction_version: string;
    schema_version: string;
    transport_profile: string;
    transport_provenance: string;
    correlation_id: string;
    request_id: string;
    trace_id: string | null;
    model_version: string | null;
    validation: string;
    failure_category: string | null;
    instruction_observation: string;
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
