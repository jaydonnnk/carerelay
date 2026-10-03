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

export type PatientProjection = {
  episode_id: string;
  lines: string[];
  simulated: boolean;
  fixture_label: string;
};

export type HintState = {
  episode_id: string;
  hint_level: string;
  card_visible: boolean;
};

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

/** The patient's four lines. Never synthesised when the call fails. */
export async function getEpisode(
  episodeId: string,
): Promise<Result<PatientProjection>> {
  return call<PatientProjection>(`/api/episodes/${encodeURIComponent(episodeId)}`);
}

/**
 * Create the demo episode, so a fresh deployment has something to show. Returns
 * the id the service actually issued, which is the only place that id may come
 * from.
 */
export async function createEpisode(): Promise<Result<{ episode_id: string }>> {
  return call<{ episode_id: string }>("/api/episodes", { method: "POST", body: "{}" });
}

/**
 * Record one hint event. The card is shown and hidden only by a patient action:
 * there is no timer anywhere in this app, and none on the server (constraint C8).
 */
export async function recordHintEvent(
  episodeId: string,
  hintLevel: string,
  event: "shown" | "patient_hid",
): Promise<Result<HintState>> {
  return call<HintState>(
    `/api/episodes/${encodeURIComponent(episodeId)}/hint-events`,
    {
      method: "POST",
      body: JSON.stringify({ hint_level: hintLevel, event }),
    },
  );
}
