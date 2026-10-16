/**
 * Slice 23 (Gate 3 sections 10.3 to 10.6): the judge panel's selection logic and copy.
 *
 * Pure and dependency-free, so the same module runs in the server component and in the
 * offline Node checks. Every value it renders comes from the ledger the server derived;
 * nothing here chooses a screen, scores words or reads the patient journey. Copy is the
 * approved inventory in `patient-experience-copy.md`; braces there are ledger values.
 */

export const FIELDS = ["action_id", "deadline_utc", "next_owner_id"] as const;
export type Field = (typeof FIELDS)[number];
export type FieldResult = "matched" | "mismatched" | "uncertain";
export const STEPS = ["start", "plan", "readback", "repair", "barrier", "permission", "unresolved",
  "stopped", "expired", "accepted", "handoff", "documented"] as const;
export type Step = (typeof STEPS)[number];
const INTERPRETATIONS = ["idle", "pending", "scored", "unavailable", "uncertain"] as const;
type Interpretation = (typeof INTERPRETATIONS)[number];
const EXECUTION = ["not_started", "attempted", "acknowledged", "failed"] as const;
type Execution = (typeof EXECUTION)[number];
const EVIDENCE = ["none", "self_reported", "documented"] as const;
const CLOSURE = ["open", "closed_with_evidence", "escalated_to_human", "expired_unresolved"] as const;
type Closure = (typeof CLOSURE)[number];
const TRANSPORT = ["https", "fake-offline", "local-sim"] as const;
export type Transport = (typeof TRANSPORT)[number];
const VALIDATION = ["valid", "invalid", "refused", "timeout", "transport", "disabled", "not_sent"] as const;
type Validation = (typeof VALIDATION)[number];
const MAX = 2048;

export type Readback = {
  confirmed_words: string | null;
  spans: Record<Field, string | null>;
  fields: Record<Field, FieldResult>;
};
export type Extraction = {
  transport: Transport;
  validation: Validation;
  scored: boolean;
  elapsed_ms: number | null;
  request_id: string | null;
  instruction_version: string;
  schema_version: string;
  failure_category: string | null;
};
export type PlanReference = { disposition_version: number; action_text: string; deadline_display: string;
  owner_display: string | null; fallback_display: string };
export type LedgerDetail = {
  journey_step: Step | null;
  interpretation: Interpretation | null;
  plan_reference: PlanReference | null;
  execution: Execution;
  evidence: (typeof EVIDENCE)[number];
  closure: Closure;
  latest: Readback | null;
  lastExtraction: Extraction | null;
  attempts: number;
  provider_reply: "failed" | "accepted" | null;
  origin: string | null;
};

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): v is string => typeof v === "string" && v.length > 0 && v.length <= MAX;
const nullableStr = (v: unknown): v is string | null => v === null || str(v);
const oneOf = <T extends string>(v: unknown, set: readonly T[]): v is T => typeof v === "string" && (set as readonly string[]).includes(v);
const exactKeys = (v: Obj, keys: readonly string[]) => Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v, k));

function decodeReadback(v: unknown): Readback | null {
  if (!isObj(v) || !exactKeys(v, ["confirmed_words", "spans", "fields"])) return null;
  const { confirmed_words: words, spans, fields } = v;
  if (!nullableStr(words) || !isObj(spans) || !isObj(fields)) return null;
  if (!exactKeys(spans, FIELDS) || !exactKeys(fields, FIELDS)) return null;
  for (const f of FIELDS) {
    if (!nullableStr(spans[f]) || !oneOf(fields[f], ["matched", "mismatched", "uncertain"] as const)) return null;
  }
  return { confirmed_words: words, spans: spans as Readback["spans"], fields: fields as Readback["fields"] };
}

function decodeExtraction(v: unknown): Extraction | null {
  if (!isObj(v)) return null;
  const { transport_provenance: transport, validation, scored, elapsed_ms: elapsed, request_id: request,
    instruction_version: instruction, schema_version: schema, failure_category: category } = v;
  if (!oneOf(transport, TRANSPORT) || !oneOf(validation, VALIDATION)) return null;
  if (scored !== true && scored !== false && scored !== 0 && scored !== 1) return null;
  if (elapsed !== null && !(Number.isSafeInteger(elapsed) && (elapsed as number) >= 0)) return null;
  if (!nullableStr(request) || !str(instruction) || !str(schema)) return null;
  if (category !== undefined && !nullableStr(category)) return null;
  return { transport, validation, scored: scored === true || scored === 1, elapsed_ms: elapsed as number | null,
    request_id: request, instruction_version: instruction, schema_version: schema,
    failure_category: (category ?? null) as string | null };
}

function decodePlan(v: unknown): PlanReference | null | undefined {
  if (v === null) return null;
  if (!isObj(v) || !exactKeys(v, ["disposition_version", "action_text", "deadline_display", "owner_display", "fallback_display"])) return undefined;
  if (!Number.isSafeInteger(v.disposition_version) || (v.disposition_version as number) < 1) return undefined;
  if (!str(v.action_text) || !str(v.deadline_display) || !nullableStr(v.owner_display) || !str(v.fallback_display)) return undefined;
  return v as PlanReference;
}

/**
 * Decode only what the panel renders. Any failure gives `null` and the panel says it
 * cannot read the episode; a missing or malformed value is never filled with a default.
 */
export function decodeLedgerDetail(value: unknown): LedgerDetail | null {
  if (!isObj(value) || value.simulated !== true) return null;
  for (const key of ["journey_step", "interpretation", "plan_reference", "disposition_version"]) {
    if (!Object.hasOwn(value, key)) return null;
  }
  const step = value.journey_step, interpretation = value.interpretation;
  if (step !== null && !oneOf(step, STEPS)) return null;
  if (interpretation !== null && !oneOf(interpretation, INTERPRETATIONS)) return null;
  const version = value.disposition_version;
  if (version !== null && !(Number.isSafeInteger(version) && (version as number) >= 1)) return null;
  // A stored plan the server could not project is a failed read, never "about to start".
  if (version !== null && (step === null || interpretation === null)) return null;
  const plan = decodePlan(value.plan_reference);
  if (plan === undefined) return null;
  if (step !== null && step !== "start" && (plan === null || plan.disposition_version !== version)) return null;
  const axes = value.axes;
  if (!isObj(axes) || !oneOf(axes.execution, EXECUTION) || !oneOf(axes.evidence, EVIDENCE) || !oneOf(axes.closure, CLOSURE)) return null;
  const { restatements, extractions, attempts, callbacks } = value;
  if (!Array.isArray(restatements) || !Array.isArray(extractions) || !Array.isArray(attempts) || !Array.isArray(callbacks)) return null;
  let latest: Readback | null = null;
  for (const row of restatements) {
    if (!isObj(row)) return null;
    latest = decodeReadback(row.readback);
    if (latest === null) return null;
  }
  let lastExtraction: Extraction | null = null;
  for (const row of extractions) {
    lastExtraction = decodeExtraction(row);
    if (lastExtraction === null) return null;
  }
  let reply: LedgerDetail["provider_reply"] = null;
  let origin: string | null = null;
  for (const row of callbacks) {
    if (!isObj(row) || typeof row.accepted !== "boolean" || !nullableStr(row.result) || !str(row.origin)) return null;
    if (!row.accepted) continue;
    origin = row.origin;
    if (row.result === "failed") reply = "failed";
    else if (row.result === "acknowledged") reply = "accepted";
  }
  return { journey_step: step, interpretation, plan_reference: plan, execution: axes.execution,
    evidence: axes.evidence, closure: axes.closure, latest, lastExtraction, attempts: attempts.length,
    provider_reply: reply, origin };
}

export type PanelState = "start" | "plan" | "readback" | "pending" | "check did not run" | "deadline mismatch"
  | "uncertain" | "other mismatch" | "match" | "permission" | "request sent" | "request failed"
  | "stopped" | "expired" | "accepted" | "handoff" | "documented";

const has = (r: Readback | null, result: FieldResult) => r !== null && FIELDS.some(f => r.fields[f] === result);

/** Gate 3 section 10.4: a first-match lookup over server-derived values. No clock, no transition. */
export function panelState(d: LedgerDetail): PanelState {
  const step = d.journey_step;
  if (step === null || step === "start") return "start";
  if (step === "plan") return d.execution === "acknowledged" ? "request sent" : "plan";
  if (step === "readback" || step === "repair") {
    if (d.interpretation === "pending") return "pending";
    if (d.interpretation === "unavailable") return "check did not run";
    if (step === "repair") return "deadline mismatch";
    if (has(d.latest, "uncertain")) return "uncertain";
    if (has(d.latest, "mismatched")) return "other mismatch";
    return "readback";
  }
  if (step === "barrier") return "match";
  if (step === "permission") return d.execution === "attempted" ? "request sent" : "permission";
  if (step === "unresolved") return "request failed";
  return step;
}

export const READBACK_LANES: ReadonlySet<PanelState> = new Set(["pending", "check did not run", "deadline mismatch",
  "uncertain", "other mismatch", "match"]);
export const OUTCOME_LANES: ReadonlySet<PanelState> = new Set(["request sent", "request failed", "stopped", "expired",
  "accepted", "handoff", "documented"]);

/**
 * Who did the reading step in this episode. Approved copy names Tencent ADP; when the
 * stored provenance says a local stand-in or a test transport did it, the panel must not
 * imply Tencent ADP was contacted. Before any check runs, the design is described as is.
 */
export function actorName(d: LedgerDetail | null): string {
  const transport = d?.lastExtraction?.transport;
  if (transport === "local-sim") return "The local stand-in";
  if (transport === "fake-offline") return "The offline test transport";
  return "Tencent ADP";
}

/** Shown whenever the last check did not go to Tencent ADP, so the panel never implies it did. */
export function offlineNote(d: LedgerDetail | null): string | null {
  const transport = d?.lastExtraction?.transport;
  if (transport === "local-sim") return "Offline run: a local stand-in did the reading step. Tencent ADP was not contacted for this check.";
  if (transport === "fake-offline") return "Offline run: a test transport did the reading step. Tencent ADP was not contacted for this check.";
  return null;
}

export type Leg = { mark: "active" | "done" | "failed" | null; small: string; tag: boolean };
export type Legs = { mei: Leg; adp: Leg; rules: Leg; provider: Leg; nurse: Leg };

/** Gate 3 section 10.5: ring, tick, red ring or none per leg; the tag moves only on handoff. */
export function trackLegs(state: PanelState, notSent = false): Legs {
  const failed = state === "request failed";
  const legs: Legs = {
    mei: { mark: null, small: failed ? "Still has to act" : "Says her plan back", tag: true },
    adp: { mark: null, small: failed ? "Read her words" : "Copies phrases from her words", tag: false },
    rules: { mark: null, small: failed ? "Checked her answer" : "Compare and decide", tag: false },
    provider: { mark: null, small: failed ? "Simulated booking failed" : "Simulated booking", tag: false },
    nurse: { mark: null, small: failed ? "Her fallback now" : "Fictional fallback", tag: false },
  };
  if (state === "pending") legs.adp.mark = "active";
  if (READBACK_LANES.has(state) && state !== "pending") { legs.adp.mark = notSent ? null : "done"; legs.rules.mark = "active"; }
  if (state === "request sent") { legs.adp.mark = legs.rules.mark = "done"; legs.provider.mark = "active"; }
  if (failed) { legs.adp.mark = legs.rules.mark = "done"; legs.provider.mark = "failed"; }
  if (state === "handoff") { legs.mei.tag = false; legs.nurse.tag = true; legs.nurse.mark = "active"; }
  return legs;
}

const COUNT = ["no", "one", "two", "three"];
/** Phrases this round's reader copied: stored spans that occur in this round's saved words. */
export function copiedCount(r: Readback | null): number {
  if (r === null) return 0;
  return FIELDS.filter(f => {
    const span = r.spans[f];
    return span !== null && (r.confirmed_words === null || r.confirmed_words.includes(span));
  }).length;
}

export const FIELD_LABEL: Record<Field, string> = { action_id: "What to do", deadline_utc: "By when", next_owner_id: "Who acts" };
const FIELD_NOUN: Record<Field, string> = { action_id: "action", deadline_utc: "deadline", next_owner_id: "person who acts" };
export const RESULT_LABEL: Record<FieldResult, string> = { matched: "Same", mismatched: "Different from plan", uncertain: "Unclear" };
export const TRANSPORT_LABEL: Record<Transport, string> = { https: "Live HTTPS call", "fake-offline": "Offline test transport", "local-sim": "Local simulation" };

/** Patient headings, from the approved inventory, for the "Next screen" line. */
export const PATIENT_HEADING: Record<Step, string | null> = { start: null, plan: "Your next step", readback: "What is your plan?",
  repair: "Let’s check the time", barrier: "What makes it difficult?", permission: "May we share your plan?",
  unresolved: "The request did not work", stopped: "Let’s stop the questions", expired: "Your plan still needs action",
  accepted: "Your daughter agreed", handoff: "Handed to the nurse line", documented: "Help is arranged." };

/** Headline and paragraph for each panel state (approved judge copy). */
export function stateCopy(state: PanelState, d: LedgerDetail | null): { headline: string; paragraph: string } {
  const actor = actorName(d);
  const deadline = d?.plan_reference?.deadline_display ?? "";
  const n = copiedCount(d?.latest ?? null);
  switch (state) {
    case "start": return { headline: "Mei is about to get her plan.", paragraph: "Press the button on the phone. CareRelay loads one fictional plan: an action, a deadline and who must act." };
    case "plan": return { headline: "Mei has her plan.", paragraph: "The plan comes from a fixed fictional script, not from a model. Next, Mei says it back in her own words." };
    case "readback": return { headline: "Mei says her plan back from memory.", paragraph: "Her plan is folded away, so her answer is recall, not copying. Nothing goes to Tencent ADP until she saves her words." };
    case "pending": return { headline: `${actor} is reading Mei's words.`, paragraph: "One call, capped at 15 seconds, with no retry. Her plan cannot change while it runs." };
    case "match": return { headline: "Mei got all three right.", paragraph: `${actor} copied out ${COUNT[n]} ${n === 1 ? "phrase" : "phrases"}. CareRelay's code matched each one to the plan.` };
    case "deadline mismatch": {
      const said = d?.latest?.spans.deadline_utc;
      return { headline: said ? `Mei said “${said}”. Her plan says “${deadline}”. CareRelay caught it.` : "Mei's answer does not match her plan.",
        paragraph: `${actor} read Mei's words and copied out ${COUNT[n]} ${n === 1 ? "phrase" : "phrases"}. CareRelay's own code compared them with the stored plan and chose the next screen. The model never judges whether Mei understood.` };
    }
    case "other mismatch": {
      const field = FIELDS.find(f => d?.latest?.fields[f] === "mismatched") ?? "action_id";
      return { headline: "Mei's answer does not match her plan.", paragraph: `Code found a different ${FIELD_NOUN[field]}. Mei is asked to try other words or show her plan.` };
    }
    case "uncertain": return { headline: "CareRelay could not confirm Mei's answer.", paragraph: `${actor} marked part of it as unclear, such as a “won't”, an “or” or a changed mind. Code does not guess, so Mei is asked again.` };
    case "check did not run": if (d?.lastExtraction?.validation === "not_sent") return notSentCopy(d.lastExtraction.failure_category);
      return { headline: "The check did not run, so nothing changed.", paragraph: `${actor} refused, ran out of time or replied in the wrong shape. Mei sees one safe sentence and her plan stays as it was.` };
    case "permission": return { headline: "Mei decides whether to share her plan.", paragraph: "Nothing is shared without her agreement. Only the action and the deadline would go to the simulated provider." };
    case "request sent": return { headline: "The simulated request is out. No reply yet.", paragraph: "A sent request is not care. Mei's case stays open until someone agrees." };
    case "request failed": return { headline: `The booking failed. CareRelay says so, and keeps the ${deadline} deadline.`, paragraph: "Mei agreed to share her plan so the simulated provider could book her in. The provider rejected the request. Nothing in the plan changed, and nobody is shown as helping." };
    case "stopped": return { headline: "CareRelay stopped asking questions.", paragraph: "When the example cannot help, it stops instead of guessing. The deadline and the nurse line stay on Mei's screen." };
    case "expired": return { headline: "The deadline has passed. CareRelay still tells Mei to act.", paragraph: "An expired plan is never hidden or marked done." };
    case "accepted": return { headline: "Someone agreed to help. Care is still not confirmed.", paragraph: "The agreement is simulated and labelled as simulated." };
    case "handoff": return { headline: "Handed to the fictional nurse line.", paragraph: "A human route now holds the plan. CareRelay does not claim care happened." };
    case "documented": return { headline: "Simulated proof of care is recorded.", paragraph: "This is the only state that counts care as evidenced, and here the proof is simulated." };
  }
}

/** Slice 24 (Gate 3 section 11.7): the guard refused, so nothing left the server. */
export const NOT_SENT_LABEL = "Not sent to Tencent ADP";
const NOT_SENT_TAIL = " Tencent ADP was not contacted. Mei sees one safe sentence and her plan stays as it was.";
export function notSentCopy(category: string | null): { headline: string; paragraph: string } {
  const reason = category === "guard_halted" ? "Live checks are paused after an earlier call failed, until an operator reviews it."
    : category === "guard_unfinished" ? "Another live check was still running, and only one runs at a time."
    : category === "guard_episode_ceiling" || category === "guard_day_ceiling" || category === "guard_total_ceiling"
      ? "The live-check limit set for this demo is reached."
    : "Live checks are switched on but not set up safely, so nothing was sent.";
  return { headline: "The check was not sent, so nothing changed.", paragraph: reason + NOT_SENT_TAIL };
}

/** The transport chip: a refused send is never shown as a live call. */
export function transportLabel(e: Extraction): string {
  return e.validation === "not_sent" ? NOT_SENT_LABEL : TRANSPORT_LABEL[e.transport];
}

export const READ_FAILED = { headline: "The judge panel cannot read this episode right now.", paragraph: "Nothing on this panel is a record until the read succeeds." };

/** ADP lane heading from the stored validation and the spans this round's reader copied. */
export function readerHeading(d: LedgerDetail): string {
  const actor = actorName(d);
  const v = d.lastExtraction?.validation;
  if (v === "not_sent") return NOT_SENT_LABEL;
  if (v === "refused") return `${actor} refused`;
  if (v === "timeout") return `${actor} did not answer in time`;
  if (v === "invalid") return `${actor} replied in the wrong shape`;
  const n = copiedCount(d.latest);
  return n === 0 ? `${actor} found nothing it could copy` : `${actor} copied ${COUNT[n]} ${n === 1 ? "phrase" : "phrases"}`;
}

/** "Checked in {s} s": server time from claim to completion, never click-to-screen latency. */
export function checkedIn(ms: number | null): string | null {
  return ms === null ? null : `Checked in ${(ms / 1000).toFixed(1)} s`;
}

export function axisValues(d: LedgerDetail) {
  return {
    sent: { not_started: "Not sent", attempted: "Sent", acknowledged: "Acknowledged", failed: "Failed" }[d.execution],
    care: d.evidence === "none" ? "None" : "Simulated",
    caseState: { open: "Still open", closed_with_evidence: "Closed", escalated_to_human: "Handed to a human", expired_unresolved: "Expired" }[d.closure],
  };
}

/** Panel step indicator (not navigation): which part of the demo the panel is showing. */
export const STEP_NAV = ["Start", "1 Plan", "2 Say it back", "3 Check", "4 Difficulty", "5 Request", "6 Outcome"] as const;
export function stepIndex(state: PanelState): number {
  if (state === "start") return 0;
  if (state === "plan") return 1;
  if (state === "readback") return 2;
  if (state === "match") return 4;
  if (READBACK_LANES.has(state)) return 3;
  if (state === "permission" || state === "request sent") return 5;
  return 6;
}

/**
 * Gate 3 section 10.6: accept a refresh signal only from this page's own frame and own
 * origin, carrying exactly `{type: "carerelay-journey", revision}` and nothing else.
 */
export function acceptFrameMessage(event: { origin: string; source: unknown; data: unknown },
  ownOrigin: string, frameWindow: unknown): boolean {
  if (event.origin !== ownOrigin || frameWindow == null || event.source !== frameWindow) return false;
  const data = event.data;
  if (!isObj(data) || !exactKeys(data, ["type", "revision"])) return false;
  return data.type === "carerelay-journey" && Number.isSafeInteger(data.revision) && (data.revision as number) >= 0;
}
