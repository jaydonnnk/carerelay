/** Runtime decoder for the only currently implemented wire branch: no-plan. */
export const ENTRY_COPY = {
  heading: "Try an example", status: "No plan yet.",
  description: "See what happens when a request fails.", start: "See the example",
} as const;
export const RECOVERY_COPY = {
  heading: "We cannot load your plan", description: "Keep the instructions you already have.",
  retry: "Try again", loading: "Loading. Nothing is confirmed yet.",
} as const;
export const JOURNEY_LABEL = "Demo only · fictional plan · no real care";
export const MAX_JOURNEY_BYTES = 16384;

export type NoPlanJourney = {
  schema_version: "carerelay-journey-v1"; episode_id: string; revision: number;
  as_of_utc: string; clock_mode: "scenario" | "system";
  disposition_version: null; policy_version: null; plan_redacted: false;
  plan: null; outcome: null; revealed_plan: null; step: "start";
  question: null; commands: []; lines: []; text: typeof ENTRY_COPY;
  flow: { stopped: false; stop_reason: null; stopped_disposition_version: null;
    readback_attempt_id: null; latest_restatement_id: null; selected_repair_field: null;
    completed_repairs: 0; effective_hint: "H1"; card_visible: false; interpretation: "idle" };
  closure: null; execution: null; evidence: null; action_owner_id: null;
  care_evidenced: false; simulated: true; fixture_label: typeof JOURNEY_LABEL;
};
function record(x: unknown): x is Record<string, unknown> {
  return typeof x === "object" && x !== null && !Array.isArray(x);
}
function exactKeys(x: Record<string, unknown>, keys: string[]): boolean {
  return Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));
}
export function decodeJourney(value: unknown, expectedId: string): NoPlanJourney | null {
  if (!record(value)) return null;
  if (!exactKeys(value, ["schema_version", "episode_id", "revision", "as_of_utc", "clock_mode",
    "disposition_version", "policy_version", "plan_redacted", "plan", "outcome", "revealed_plan",
    "step", "question", "commands", "lines", "text", "flow", "closure", "execution", "evidence",
    "action_owner_id", "care_evidenced", "simulated", "fixture_label"])) return null;
  if (value.schema_version !== "carerelay-journey-v1") return null;
  if (typeof value.episode_id !== "string" || value.episode_id.length > 128 ||
      !value.episode_id || value.episode_id !== expectedId) return null;
  if (typeof value.revision !== "number" || !Number.isSafeInteger(value.revision) || value.revision < 0) return null;
  if (typeof value.as_of_utc !== "string" || value.as_of_utc.length > 40 ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$/.test(value.as_of_utc) ||
      !Number.isFinite(Date.parse(value.as_of_utc))) return null;
  if (new Date(value.as_of_utc).toISOString().slice(0, 19) !== value.as_of_utc.slice(0, 19)) return null;
  if (value.clock_mode !== "scenario" && value.clock_mode !== "system") return null;
  if (value.step !== "start") return null;
  if (value.plan_redacted !== false) return null;
  for (const key of ["disposition_version", "policy_version", "plan", "outcome", "revealed_plan",
    "question", "closure", "execution", "evidence", "action_owner_id"]) {
    if (value[key] !== null) return null;
  }
  if (value.care_evidenced !== false) return null;
  if (!Array.isArray(value.lines) || value.lines.length !== 0) return null;
  if (!Array.isArray(value.commands) || value.commands.length !== 0) return null;
  if (value.simulated !== true || value.fixture_label !== JOURNEY_LABEL) return null;
  if (!record(value.text) || !exactKeys(value.text, Object.keys(ENTRY_COPY))) return null;
  for (const [key, copy] of Object.entries(ENTRY_COPY)) {
    if (value.text[key] !== copy) return null;
  }
  if (!record(value.flow) || !exactKeys(value.flow, ["stopped", "stop_reason", "stopped_disposition_version",
    "readback_attempt_id", "latest_restatement_id", "selected_repair_field", "completed_repairs",
    "effective_hint", "card_visible", "interpretation"])) return null;
  const flow = value.flow;
  if (flow.stopped !== false) return null;
  for (const key of ["stop_reason", "stopped_disposition_version", "readback_attempt_id",
    "latest_restatement_id", "selected_repair_field"]) {
    if (flow[key] !== null) return null;
  }
  if (flow.completed_repairs !== 0) return null;
  if (flow.effective_hint !== "H1") return null;
  if (flow.card_visible !== false) return null;
  if (flow.interpretation !== "idle") return null;
  return value as NoPlanJourney; // All fields were checked above; never a transport cast.
}

/** Bounded before JSON parsing, including streamed bodies without Content-Length. */
export async function readJourney(response: Response, expectedId: string): Promise<NoPlanJourney | null> {
  if (!response.ok || !response.body) return null;
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let count = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      count += value.byteLength;
      if (count > MAX_JOURNEY_BYTES) { await reader.cancel(); return null; }
      chunks.push(value);
    }
    const bytes = new Uint8Array(count);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    return decodeJourney(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)), expectedId);
  } catch { return null; }
  finally { reader.releaseLock(); }
}
