/** Whole-response validation; clinical values and screen selection come from the server. */
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
export const READBACK_KINDS = ["readback_started", "confirm_words", "score_words", "repair_words",
  "show_plan", "hide_plan", "h3", "supersede_extraction"] as const;
export type ReadbackKind = typeof READBACK_KINDS[number];
export const PERMISSION_KINDS = ["select_barrier", "grant_share", "decline_share", "revoke_share", "request"] as const;
export type PermissionKind = typeof PERMISSION_KINDS[number];
export type CommandOffer = { kind: "select_example" | ReadbackKind | PermissionKind; offer_id: string;
  permitted_choice_ids: string[]; operation_token: string | null };
export type PlanView = { disposition_version: number; policy_version: string; action_id: string;
  action_text: string; deadline_utc: string; deadline_display: string; display_timezone: string;
  original_owner_id: string; original_owner_display: string; current_owner_id: string | null;
  current_owner_display: string | null; fallback_route_id: string; fallback_display: string };
export type OutcomeView = { execution: string; evidence: string; closure: string; care_evidenced: boolean;
  accepted_by: string | null; accepted_scope: string | null; escalation_path: string | null;
  escalation_outcome: string | null; expiry_recorded: boolean };
export type FlowView = { stopped: boolean; stop_reason: string | null; stopped_disposition_version: number | null;
  readback_attempt_id: string | null; latest_restatement_id: string | null; selected_repair_field: string | null;
  completed_repairs: number; effective_hint: string; card_visible: boolean; interpretation: string };
export type Journey = { schema_version: "carerelay-journey-v1"; episode_id: string; revision: number;
  as_of_utc: string; clock_mode: "scenario" | "system"; disposition_version: number | null;
  policy_version: string | null; plan_redacted: boolean; plan: PlanView | null;
  outcome: OutcomeView | null; revealed_plan: PlanView | null; step: string;
  question: { question_id: string; text: string; choices: { choice_id: string; text: string }[] } | null;
  commands: CommandOffer[]; lines: string[]; text: Record<string, string>; flow: FlowView;
  closure: string | null; execution: string | null; evidence: string | null; action_owner_id: string | null;
  care_evidenced: boolean; simulated: true; fixture_label: typeof JOURNEY_LABEL };
export type NoPlanJourney = Journey & { disposition_version: null; policy_version: null; step: "start";
  plan: null; outcome: null; revealed_plan: null; plan_redacted: false; question: null; lines: [] };
export type CommandResult = { receipt: { operation_id: string; state: string; result_ref: string | null;
  scored: boolean; replayed: boolean }; journey: Journey };

const ROOT_KEYS = ["schema_version", "episode_id", "revision", "as_of_utc", "clock_mode",
  "disposition_version", "policy_version", "plan_redacted", "plan", "outcome", "revealed_plan",
  "step", "question", "commands", "lines", "text", "flow", "closure", "execution", "evidence",
  "action_owner_id", "care_evidenced", "simulated", "fixture_label"];
const FLOW_KEYS = ["stopped", "stop_reason", "stopped_disposition_version", "readback_attempt_id",
  "latest_restatement_id", "selected_repair_field", "completed_repairs", "effective_hint", "card_visible", "interpretation"];
const PLAN_KEYS = ["disposition_version", "policy_version", "action_id", "action_text", "deadline_utc",
  "deadline_display", "display_timezone", "original_owner_id", "original_owner_display", "current_owner_id",
  "current_owner_display", "fallback_route_id", "fallback_display"];
const OUTCOME_KEYS = ["execution", "evidence", "closure", "care_evidenced", "accepted_by", "accepted_scope",
  "escalation_path", "escalation_outcome", "expiry_recorded"];
function record(x: unknown): x is Record<string, unknown> {
  return typeof x === "object" && x !== null && !Array.isArray(x);
}
function exactKeys(x: Record<string, unknown>, keys: string[]): boolean {
  return Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x, k));
}
function bounded(x: unknown, limit = 2048): x is string {
  return typeof x === "string" && x.length > 0 && x.length <= limit;
}
function nullableString(x: unknown): boolean { return x === null || bounded(x, 128); }
function instant(x: unknown): x is string {
  return typeof x === "string" && x.length <= 40 &&
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$/.test(x) &&
    Number.isFinite(Date.parse(x)) && new Date(x).toISOString().slice(0, 19) === x.slice(0, 19);
}
function planView(value: unknown, version: unknown, policy: unknown): value is PlanView {
  if (!record(value) || !exactKeys(value, PLAN_KEYS)) return false;
  if (value.disposition_version !== version || value.policy_version !== policy) return false;
  if (!instant(value.deadline_utc) || value.display_timezone !== "Asia/Singapore") return false;
  for (const key of ["action_id", "action_text", "deadline_display", "original_owner_id",
    "original_owner_display", "fallback_route_id", "fallback_display"]) if (!bounded(value[key])) return false;
  if (!nullableString(value.current_owner_id) || !nullableString(value.current_owner_display)) return false;
  if ((value.current_owner_id === null) !== (value.current_owner_display === null)) return false;
  return true;
}
export function decodeJourney(value: unknown, expectedId: string): Journey | null {
  if (!record(value) || !exactKeys(value, ROOT_KEYS)) return null;
  if (value.schema_version !== "carerelay-journey-v1") return null;
  if (!bounded(value.episode_id, 128) || value.episode_id !== expectedId) return null;
  if (!Number.isSafeInteger(value.revision) || Number(value.revision) < 0) return null;
  if (!instant(value.as_of_utc)) return null;
  if (value.clock_mode !== "scenario" && value.clock_mode !== "system") return null;
  if (value.simulated !== true || value.fixture_label !== JOURNEY_LABEL) return null;
  if (!record(value.flow) || !exactKeys(value.flow, FLOW_KEYS)) return null;
  const flow = value.flow;
  if (typeof flow.stopped !== "boolean" || typeof flow.card_visible !== "boolean") return null;
  for (const key of ["readback_attempt_id", "latest_restatement_id"]) {
    if (!nullableString(flow[key])) return null;
  }
  if (!Number.isInteger(flow.completed_repairs) ||
      Number(flow.completed_repairs) < 0 || Number(flow.completed_repairs) > 2) return null;
  if (!["H0", "H1", "H2", "H3"].includes(flow.effective_hint as string)) return null;
  if (!["idle", "pending", "scored", "unavailable", "uncertain"].includes(flow.interpretation as string)) return null;
  if (flow.selected_repair_field !== null && !["action_id", "deadline_utc", "next_owner_id"].includes(flow.selected_repair_field as string)) return null;
  if (!Array.isArray(value.lines) || !value.lines.every(x => bounded(x))) return null;
  if (!record(value.text) ||
      !Object.values(value.text).every(x => bounded(x))) return null;
  if (!Array.isArray(value.commands)) return null;
  const commandKinds: string[] = [];
  for (const offer of value.commands) {
    if (!record(offer) || !exactKeys(offer, ["kind", "offer_id", "permitted_choice_ids", "operation_token"]) ||
        !bounded(offer.offer_id, 128) ||
        !Array.isArray(offer.permitted_choice_ids) ||
        (offer.operation_token !== null && (!bounded(offer.operation_token, 4096) ||
          !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(offer.operation_token)))) return null;
    if (typeof offer.kind !== "string" || commandKinds.includes(offer.kind)) return null;
    if (!["select_example", ...READBACK_KINDS, ...PERMISSION_KINDS].some(k => k === offer.kind)) return null;
    commandKinds.push(offer.kind);
    if (offer.kind === "select_example" ?
      (offer.permitted_choice_ids.length !== 1 || offer.permitted_choice_ids[0] !== "scripted-appointment") :
      offer.kind === "supersede_extraction" ?
      (offer.permitted_choice_ids.length !== 1 || !bounded(offer.permitted_choice_ids[0], 128)) :
      offer.kind === "select_barrier" ?
      (offer.permitted_choice_ids.length !== 3 || new Set(offer.permitted_choice_ids).size !== 3 ||
       !offer.permitted_choice_ids.every(id => ["booking", "transport", "other"].some(k => k === id)) || offer.operation_token !== null) :
      offer.permitted_choice_ids.length !== 0) return null;
    if (PERMISSION_KINDS.some(k => k === offer.kind) && offer.kind !== "select_barrier" && offer.operation_token === null) return null;
  }
  if (value.disposition_version === null) {
    if (commandKinds.some(k => k !== "select_example")) return null;
    if (flow.interpretation === "pending" && value.commands.length !== 0) return null;
    if (value.step !== "start" || value.plan_redacted !== false) return null;
    for (const key of ["policy_version", "plan", "outcome", "revealed_plan", "question", "closure", "execution", "evidence", "action_owner_id"]) {
      if (value[key] !== null) return null;
    }
    if (value.care_evidenced !== false || value.lines.length !== 0) return null;
    if (!exactKeys(value.text, Object.keys(ENTRY_COPY))) return null;
    for (const [key, copy] of Object.entries(ENTRY_COPY)) if (value.text[key] !== copy) return null;
    if (flow.stopped !== false || flow.card_visible !== false || flow.completed_repairs !== 0 || flow.effective_hint !== "H1") return null;
    if (flow.interpretation !== "idle" && flow.interpretation !== "pending") return null;
    for (const key of ["stop_reason", "stopped_disposition_version", "readback_attempt_id", "latest_restatement_id", "selected_repair_field"]) {
      if (flow[key] !== null) return null;
    }
    return value as NoPlanJourney;
  }
  if (!Number.isSafeInteger(value.disposition_version) || Number(value.disposition_version) < 1) return null;
  if (value.policy_version !== "fixture-provisional-0") return null;
  if (!["plan", "readback", "repair", "barrier", "permission", "unresolved", "stopped", "expired", "accepted", "handoff", "documented"].includes(value.step as string)) return null;
  if (typeof value.plan_redacted !== "boolean" || typeof value.care_evidenced !== "boolean") return null;
  if (!record(value.outcome) || !exactKeys(value.outcome, OUTCOME_KEYS)) return null;
  const outcome = value.outcome;
  if (!["not_started", "attempted", "acknowledged", "failed", "superseded", "expired"].includes(outcome.execution as string)) return null;
  if (!["none", "self_reported", "documented"].includes(outcome.evidence as string)) return null;
  if (typeof outcome.expiry_recorded !== "boolean") return null;
  for (const key of ["accepted_by", "accepted_scope", "escalation_path", "escalation_outcome"]) if (!nullableString(outcome[key])) return null;
  if (value.execution !== outcome.execution || value.evidence !== outcome.evidence || value.closure !== outcome.closure || value.care_evidenced !== outcome.care_evidenced) return null;
  if (flow.stopped ? (flow.stopped_disposition_version !== value.disposition_version || !bounded(flow.stop_reason, 128)) :
      (flow.stopped_disposition_version !== null || flow.stop_reason !== null)) return null;
  if (value.plan_redacted) {
    if (value.step !== "readback" && value.step !== "repair") return null;
    if (value.plan !== null || value.lines.length !== 0 || value.action_owner_id !== null) return null;
  } else {
    if (!planView(value.plan, value.disposition_version, value.policy_version) || value.lines.length !== 4) return null;
    if (value.action_owner_id !== value.plan.current_owner_id) return null;
    if (value.step === "readback" || value.step === "repair") return null;
  }
  if (flow.card_visible) {
    if (!planView(value.revealed_plan, value.disposition_version, value.policy_version) || !["H2", "H3"].includes(flow.effective_hint as string)) return null;
    if (value.plan && !PLAN_KEYS.every(key => (value.plan as Record<string, unknown>)[key] === (value.revealed_plan as Record<string, unknown>)[key])) return null;
  } else if (value.revealed_plan !== null) return null;
  if (value.question !== null) {
    if (!record(value.question) || !exactKeys(value.question, ["question_id", "text", "choices"]) ||
        !bounded(value.question.text) || !Array.isArray(value.question.choices)) return null;
    const choiceIds: unknown[] = [];
    for (const choice of value.question.choices) {
      if (!record(choice) || !exactKeys(choice, ["choice_id", "text"]) ||
          !bounded(choice.text)) return null;
      choiceIds.push(choice.choice_id);
    }
    if (value.question.question_id !== value.step) return null;
    if (value.step === "barrier" ?
      (choiceIds.length !== 3 || new Set(choiceIds).size !== choiceIds.length ||
       !choiceIds.every(id => ["booking", "transport", "other"].some(allowed => id === allowed))) : choiceIds.length !== 0) return null;
  }
  if (value.step === "stopped" && flow.stopped !== true) return null;
  if (flow.stopped && outcome.closure === "open" && value.step !== "stopped") return null;
  if (flow.effective_hint === "H3" && flow.stopped !== true) return null;
  if (outcome.expiry_recorded && value.step !== "expired" && value.step !== "documented") return null;
  if (["plan", "readback", "repair", "barrier", "permission", "stopped", "unresolved"].includes(value.step as string) && outcome.closure !== "open") return null;
  if (value.step === "expired" && outcome.closure !== "expired_unresolved") return null;
  if (value.step === "accepted" && (outcome.closure !== "closed_with_evidence" || outcome.accepted_scope !== "handoff" ||
      !outcome.accepted_by || outcome.accepted_by === (value.plan as PlanView).original_owner_id || value.action_owner_id !== outcome.accepted_by)) return null;
  if (value.step === "handoff" && (outcome.closure !== "escalated_to_human" || !outcome.escalation_path ||
      !["handed_off", "handed_over"].includes(outcome.escalation_outcome as string) || value.action_owner_id !== outcome.escalation_path)) return null;
  if (value.care_evidenced && (outcome.evidence !== "documented" || outcome.closure !== "closed_with_evidence" || value.step !== "documented")) return null;
  if (value.step === "documented" && value.care_evidenced !== true) return null;
  if (value.step === "unresolved" && outcome.execution !== "failed" && outcome.escalation_outcome !== "failed") return null;
  if (value.step === "permission" && !["not_started", "attempted"].includes(outcome.execution as string)) return null;
  if (value.step === "barrier" && outcome.execution !== "not_started") return null;
  if (value.step === "repair" && (flow.selected_repair_field !== "deadline_utc" || Number(flow.completed_repairs) >= 2 ||
      !["H2", "H3"].includes(flow.effective_hint as string))) return null;
  if (outcome.closure === "open" && value.plan && value.plan.current_owner_id !== value.plan.original_owner_id) return null;
  if (value.plan_redacted && (outcome.accepted_by !== null || outcome.escalation_path !== null)) return null;
  if (["readback", "repair"].includes(value.step as string) && flow.readback_attempt_id === null) return null;
  const needsQuestion = flow.interpretation !== "pending" &&
    (["readback", "repair", "barrier"].includes(value.step as string) ||
      (value.step === "permission" && outcome.execution !== "attempted"));
  if (needsQuestion !== (value.question !== null)) return null;
  if (value.step === "plan" && outcome.execution === "failed") return null;
  const allowed: Record<string, string[]> = {
    plan: outcome.execution === "not_started" && outcome.escalation_path === null ? ["readback_started", "show_plan", "hide_plan", "grant_share", "revoke_share"] : ["show_plan", "hide_plan", "revoke_share"],
    readback: ["confirm_words", flow.latest_restatement_id === null ? "score_words" : "repair_words", "show_plan", "hide_plan", "h3"],
    repair: ["confirm_words", "repair_words", "show_plan", "hide_plan", "h3"],
    barrier: ["select_barrier", "show_plan", "hide_plan"],
    permission: outcome.execution === "attempted" ? ["show_plan", "hide_plan", "revoke_share"] :
      ["grant_share", "decline_share", "revoke_share", "request", "show_plan", "hide_plan"],
    stopped: ["show_plan", "hide_plan", "grant_share", "revoke_share"], unresolved: ["show_plan", "hide_plan", "grant_share", "revoke_share"],
    expired: ["revoke_share"], accepted: [], handoff: [], documented: [],
  };
  const allowedKinds = flow.interpretation === "pending" ?
    (value.step === "expired" ? ["revoke_share"] :
      ["permission", "plan", "unresolved", "stopped"].includes(value.step as string) ? ["show_plan", "hide_plan", "revoke_share"] :
      ["readback", "repair"].includes(value.step as string) ? ["show_plan", "hide_plan", "h3", "supersede_extraction"] : []) :
    allowed[value.step as string];
  if (!commandKinds.every(k => allowedKinds.includes(k))) return null;
  const textKeys: Record<string, string[]> = {
    plan: ["heading", "action_label", "deadline_label", "owner_label"],
    readback: ["heading"], repair: ["heading"], barrier: ["heading", "description"],
    permission: outcome.execution === "attempted" ? ["heading", "status", "notice"] : ["heading", "description", "shared"],
    unresolved: ["heading"], stopped: ["heading"], expired: ["heading"],
    accepted: ["heading", "notice"], handoff: ["heading", "notice"], documented: ["heading"],
  };
  const selectedTextKeys = [...textKeys[value.step as string]];
  if (flow.card_visible) selectedTextKeys.push("revealed_heading", "reveal_action_label", "reveal_deadline_label", "reveal_owner_label");
  if (!flow.stopped && outcome.closure === "open" &&
      !(value.step === "permission" && outcome.execution === "attempted") &&
      ["pending", "unavailable", "uncertain"].includes(flow.interpretation as string) ||
      (["readback", "repair"].includes(value.step as string) && flow.latest_restatement_id !== null && value.text.feedback !== undefined)) selectedTextKeys.push("feedback");
  if (value.step === "stopped" && flow.stop_reason === "barrier_stop") selectedTextKeys.push("feedback");
  if (["readback", "repair"].includes(value.step as string)) {
    selectedTextKeys.push("input_label", "input_help", "input_error", "review_label", "preview_label", "answer_label", "confirmation_label", "confirmation_help");
    if (value.step === "repair") selectedTextKeys.push("repair_example_label", "repair_answer", "repair_plan_label", "repair_deadline");
    if (value.text.saved_words !== undefined) selectedTextKeys.push("saved_words", "retry_label", "retry_help");
  } else if (value.text.saved_words !== undefined) return null;
  if (commandKinds.some(k => ["show_plan", "hide_plan"].includes(k))) selectedTextKeys.push("show_label", "hide_label");
  if (commandKinds.includes("readback_started")) selectedTextKeys.push("readback_label");
  if (value.step === "barrier") selectedTextKeys.push("choice_error", "continue_label");
  if (commandKinds.includes("grant_share")) selectedTextKeys.push("consent_label", "consent_error");
  if (value.step === "permission" && value.question !== null) selectedTextKeys.push("request_label");
  if (commandKinds.includes("decline_share") || commandKinds.includes("revoke_share")) selectedTextKeys.push("decline_label");
  if (!exactKeys(value.text, selectedTextKeys)) return null;
  return value as Journey; // The complete bounded projection was checked above.
}

/** Changed equal-revision command results require a fresh authoritative read. */
export function reconcileJourney(current: Journey | null, next: Journey, fromRead: boolean): Journey | null {
  if (!current || current.episode_id !== next.episode_id) return next;
  if (next.revision < current.revision) return null;
  if (current.disposition_version === next.disposition_version &&
      ((current.flow.stopped && !next.flow.stopped) ||
       (current.outcome?.expiry_recorded && !next.outcome?.expiry_recorded))) return null;
  if (next.revision === current.revision && !fromRead) {
    const { as_of_utc: previousTime, ...previous } = current;
    const { as_of_utc: nextTime, ...incoming } = next;
    if (JSON.stringify(previous) !== JSON.stringify(incoming)) return null;
  }
  return next;
}

async function boundedJson(response: Response): Promise<unknown> {
  if (![200, 202, 409, 503].includes(response.status) || !response.body) return null;
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
    return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch { return null; }
  finally { reader.releaseLock(); }
}
export async function readJourney(response: Response, expectedId: string): Promise<Journey | null> {
  if (response.status !== 200) return null;
  return decodeJourney(await boundedJson(response), expectedId);
}
export async function readCommand(response: Response, expectedId: string, kind?: CommandOffer["kind"] | "create"): Promise<CommandResult | null> {
  const value = await boundedJson(response);
  if (!record(value) || !exactKeys(value, ["receipt", "journey"]) || !record(value.receipt) ||
      !exactKeys(value.receipt, ["operation_id", "state", "result_ref", "scored", "replayed"])) return null;
  const r = value.receipt;
  if (!bounded(r.operation_id, 128) || !["pending", "applied", "refused", "unavailable", "superseded"].includes(r.state as string) ||
      !nullableString(r.result_ref) || typeof r.scored !== "boolean" || typeof r.replayed !== "boolean") return null;
  if (r.scored && (r.state !== "applied" || !bounded(r.result_ref, 128))) return null;
  const scoring = kind === "score_words" || kind === "repair_words";
  if (r.scored && !scoring) return null;
  if (scoring && r.state === "applied" && !r.scored) return null;
  if ((response.status === 503) !== (r.state === "unavailable")) return null;
  const journey = decodeJourney(value.journey, expectedId);
  if (!journey || (r.state === "pending") !== (response.status === 202)) return null;
  return { receipt: r, journey } as CommandResult;
}

export async function readConflict(response: Response, expectedId: string): Promise<Journey | null> {
  if (response.status !== 409) return null;
  const value = await boundedJson(response);
  return record(value) && exactKeys(value, ["detail", "journey"]) && typeof value.detail === "string" ?
    decodeJourney(value.journey, expectedId) : null;
}

export async function readPrepared(response: Response): Promise<string | null> {
  if (response.status !== 200) return null;
  const value = await boundedJson(response);
  return record(value) && exactKeys(value, ["operation_token"]) && bounded(value.operation_token, 4096) &&
    /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(value.operation_token) ? value.operation_token : null;
}
