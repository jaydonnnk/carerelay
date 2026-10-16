"use client";
import { useActionState, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { startExample, selectExample, prepareReadbackWords, submitReadback, prepareBarrierChoice, submitPermission, type ActionResult } from "@/app/actions";
import { ENTRY_COPY, RECOVERY_COPY, JOURNEY_LABEL, RESTART_LABEL, SLIP_COPY, notifyParent, progressStep, progressLabel, reconcileJourney, startThenSelect,
  QUESTION_ORDER, QUESTIONS, SAFETY_COPY, assessSafety, emergencyLine, uncheckedLine,
  type Journey, type PlanView, type CommandOffer, type SafetyAnswers } from "@/lib/journey";
import { HintCard } from "./HintCard";

/** Slice 22: icons accompany text and never replace it (`patient-experience-copy.md`). */
const PATHS = {
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18M8 14h3M8 17h6" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  person: <><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></>,
  phone: <path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z" />,
  alert: <><circle cx="12" cy="12" r="9" /><path d="M12 7v6M12 16.5v.5" /></>,
  check: <><circle cx="12" cy="12" r="9" /><path d="M8 12l3 3 5-6" /></>,
  folded: <><path d="M3 3l18 18" /><path d="M10.6 6.1A10 10 0 0 1 12 6c5 0 9 6 9 6a17 17 0 0 1-2.7 3.3M6.5 7.5A17 17 0 0 0 3 12s4 6 9 6a9 9 0 0 0 4-1" /></>,
} as const;
type IconName = keyof typeof PATHS;

function Icon({ name }: { name: IconName }) {
  return <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{PATHS[name]}</svg>;
}

/**
 * The guided safety check: one question per screen, then either the emergency
 * screen or `onClear` with what could not be checked. Answers stay in this
 * component; nothing is sent or stored (Gate 2 trade-off, `00-status.md`).
 */
function SafetyCheck({ onClear }: { onClear: (unchecked: string[]) => void }) {
  const [answers, setAnswers] = useState<SafetyAnswers>({});
  const [index, setIndex] = useState(0);
  const [emergency, setEmergency] = useState<string[] | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, [index, emergency]);

  if (emergency) {
    return <>
      <h1 id="journey-heading" tabIndex={-1} ref={heading}>{SAFETY_COPY.emergency_heading}</h1>
      <div className="journey-status-box open safety-emergency" role="alert">
        <Icon name="alert" />
        <div>
          <p className="journey-line"><strong>{SAFETY_COPY.emergency_call}</strong></p>
          <p className="journey-line">{SAFETY_COPY.emergency_wait}</p>
          <p className="journey-line">{emergencyLine(emergency)}</p>
        </div>
      </div>
      <button className="control" type="button" onClick={() => { setEmergency(null); setIndex(0); }}>{SAFETY_COPY.emergency_change}</button>
      <p className="safety-source">{SAFETY_COPY.source}</p>
    </>;
  }

  const id = QUESTION_ORDER[index];
  const question = QUESTIONS[id];
  const chosen = answers[id];
  function next() {
    if (!chosen) return;
    if (index < QUESTION_ORDER.length - 1) { setIndex(index + 1); return; }
    const outcome = assessSafety(answers);
    if (outcome.result === "emergency") setEmergency(outcome.reasons);
    else if (outcome.result === "clear") onClear(outcome.unchecked);
  }
  return <>
    <h1 id="journey-heading" tabIndex={-1} ref={heading}>{SAFETY_COPY.heading}</h1>
    <p>{SAFETY_COPY.intro}</p>
    <form onSubmit={event => { event.preventDefault(); next(); }}>
      <fieldset className="journey-choices">
        <legend className="journey-question">{question.text}</legend>
        {question.options.map(([value, label]) => <label key={value} className="journey-choice">
          <input type="radio" name={id} value={value} checked={chosen === value}
            onChange={() => setAnswers({ ...answers, [id]: value })} />
          <span>{label}</span>
        </label>)}
      </fieldset>
      <button className="control primary" type="submit" aria-disabled={chosen ? undefined : true}>{SAFETY_COPY.next}</button>
      {index > 0 && <button className="control" type="button" onClick={() => setIndex(index - 1)}>{SAFETY_COPY.back}</button>}
    </form>
    <p className="safety-source">{SAFETY_COPY.source}</p>
  </>;
}

type Props = { state: "entry" | "recovery" | "start"; creationToken?: string } | { state: "loaded"; journey: Journey };
function PlanRows({ plan, labels }: { plan: PlanView; labels: Record<string, string> }) {
  return <dl className="journey-plan">
    <div><dt><Icon name="calendar" />{labels.action_label}</dt><dd>{plan.action_text}</dd></div>
    <div><dt><Icon name="clock" />{labels.deadline_label}</dt><dd>{plan.deadline_display}</dd></div>
    {plan.current_owner_display !== null && <div><dt><Icon name="person" />{labels.owner_label}</dt><dd>{plan.current_owner_display}</dd></div>}
  </dl>;
}
/** The plan as a yellow appointment slip (Gate 1, 16 October 2026). */
function PlanSlip({ plan, labels }: { plan: PlanView; labels: Record<string, string> }) {
  return <section className="slip" aria-label={SLIP_COPY.heading}>
    <p className="slip-head"><strong>{SLIP_COPY.heading}</strong></p>
    <PlanRows plan={plan} labels={labels} />
  </section>;
}
/** The server's four lines, unchanged and in order: who has agreed, urgency, deadline, fallback. */
function Lines({ lines, open, children }: { lines: string[]; open: boolean; children?: React.ReactNode }) {
  if (lines.length !== 4) return <>{lines.map((line, i) => <p className="journey-line" key={i}>{line}</p>)}{children}</>;
  return <>
    <div className={`journey-status-box ${open ? "open" : "calm"}`}>
      <Icon name={open ? "alert" : "check"} />
      <div>{lines.slice(0, 3).map((line, i) => <p className="journey-line" key={i}>{line}</p>)}</div>
    </div>
    {children}
    <p className="journey-line journey-fallback"><Icon name="phone" /><span>{lines[3]}</span></p>
  </>;
}
function Progress({ step }: { step: number }) {
  return <div className="journey-progress">
    <span aria-hidden="true" className="bars">{[1, 2, 3, 4].map(n => <b key={n} className={n <= step ? "done" : undefined} />)}</span>
    <span>{progressLabel(step)}</span>
  </div>;
}
async function createThenSelect(previous: ActionResult | null, form: FormData): Promise<ActionResult> {
  return startThenSelect(form, f => startExample(previous, f), f => selectExample(previous, f));
}
function ExampleForm({ token, kind, onResult, onPending }: { token: string; kind: "create" | "select_example";
  onResult: (r: ActionResult) => void; onPending: (pending: boolean) => void }) {
  const [result, action, pending] = useActionState(kind === "create" ? createThenSelect : selectExample, null);
  useReportPending(pending, onPending);
  useEffect(() => { if (result) onResult(result); }, [result, onResult]);
  return <form action={action} onSubmit={event => { if (pending) event.preventDefault(); }}>
    <input type="hidden" name="operation_token" value={token} />
    <button className="control primary" aria-disabled={busy(pending)} type="submit">{ENTRY_COPY.start}</button>
  </form>;
}

/**
 * Report a form's pending command to the page's one status region; unmounting clears it.
 * A live region inserted together with its text is not announced by Safari with VoiceOver.
 */
function useReportPending(pending: boolean, onPending: (pending: boolean) => void) {
  useEffect(() => { onPending(pending); }, [pending, onPending]);
  useEffect(() => () => onPending(false), [onPending]);
}

/**
 * Pending controls stay focusable and say they are busy. A natively disabled control
 * drops keyboard and screen-reader focus to BODY while it holds focus; handlers ignore
 * activation instead, so one command is still sent once.
 */
function busy(pending: boolean): true | undefined {
  return pending || undefined;
}

async function sendReadback(offer: CommandOffer, text?: string): Promise<ActionResult> {
  if (!offer.operation_token) return { state: "recovery" };
  const form = new FormData();
  form.set("kind", offer.kind); form.set("operation_token", offer.operation_token);
  if (text !== undefined) form.set("text", text);
  if (offer.kind === "supersede_extraction") form.set("old_operation_id", offer.permitted_choice_ids[0]);
  return submitReadback(form);
}

async function sendPermission(offer: CommandOffer, choiceId?: string): Promise<ActionResult> {
  if (!offer.operation_token) return { state: "recovery" };
  const form = new FormData(); form.set("kind", offer.kind); form.set("operation_token", offer.operation_token);
  if (choiceId !== undefined) form.set("choice_id", choiceId);
  if (offer.kind === "grant_share") form.set("agreed", "yes");
  return submitPermission(form);
}

function BarrierForm({ journey, onResult, onPending }: { journey: Journey; onResult: (r: ActionResult) => void; onPending: (pending: boolean) => void }) {
  const [choice, setChoice] = useState("");
  const [error, setError] = useState(false), [pending, setPending] = useState(false);
  useReportPending(pending, onPending);
  const firstChoice = useRef<HTMLInputElement>(null);
  const prepared = useRef<{ choice: string; token: string } | null>(null);
  const offer = journey.commands.find(o => o.kind === "select_barrier");
  if (!offer || !journey.question) return null;
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (pending) return;
    if (!choice) { setError(true); firstChoice.current?.focus(); return; }
    if (!offer || !offer.permitted_choice_ids.includes(choice)) return;
    setPending(true);
    try {
      if (!prepared.current || prepared.current.choice !== choice) {
        const form = new FormData(); form.set("choice_id", choice);
        const result = await prepareBarrierChoice(form);
        if (!result.ok) { onResult({ state: "recovery" }); return; }
        prepared.current = { choice, token: result.token };
      }
      onResult(await sendPermission({ ...offer, operation_token: prepared.current.token }, choice));
    } catch { onResult({ state: "recovery" }); }
    finally { setPending(false); }
  }
  return <form onSubmit={submit} noValidate>
    <fieldset className="journey-choices" aria-describedby={error ? "barrier-error" : undefined}>
      <legend>{journey.text.description}</legend>
      {journey.question.choices.map((option, index) => <label className="journey-choice" key={option.choice_id}>
        <input ref={index === 0 ? firstChoice : undefined} type="radio" name="choice_id" value={option.choice_id}
          aria-disabled={busy(pending)} checked={choice === option.choice_id}
          onChange={() => { if (pending) return; setChoice(option.choice_id); setError(false); prepared.current = null; }} />
        <span>{option.text}</span>
      </label>)}
    </fieldset>
    {error && <p id="barrier-error" role="alert">{journey.text.choice_error}</p>}
    <button className="control primary" type="submit" aria-disabled={busy(pending)}>{journey.text.continue_label}</button>
  </form>;
}

function PermissionControls({ journey, onResult, onPending }: { journey: Journey; onResult: (r: ActionResult) => void; onPending: (pending: boolean) => void }) {
  const [agreed, setAgreed] = useState(false), [pending, setPending] = useState(false);
  useReportPending(pending, onPending);
  const grant = journey.commands.find(o => o.kind === "grant_share" && o.operation_token);
  const request = journey.commands.find(o => o.kind === "request" && o.operation_token);
  const declineKind = journey.step === "permission" && journey.question && !request ? "decline_share" : "revoke_share";
  const decline = journey.commands.find(o => o.kind === declineKind && o.operation_token);
  async function run(offer: CommandOffer) {
    if (pending) return;
    setPending(true);
    try { onResult(await sendPermission(offer)); }
    catch { onResult({ state: "recovery" }); }
    finally { setPending(false); }
  }
  return <section>
    {journey.text.shared && <p>{journey.text.shared}</p>}
    {grant && <label className="journey-choice" htmlFor="share-plan-consent">
      <input id="share-plan-consent" type="checkbox" checked={agreed} aria-disabled={busy(pending)}
        aria-describedby={!agreed ? "consent-help" : undefined}
        onChange={event => {
          if (pending) return;
          const checked = event.target.checked; setAgreed(checked);
          if (checked) void run(grant);
          else if (decline) void run(decline);
        }} />
      <span>{journey.text.consent_label}</span>
    </label>}
    {grant && !agreed && <p id="consent-help">{journey.text.consent_error}</p>}
    {journey.step === "permission" && journey.question && <button className="control primary" type="button"
      disabled={!request || !agreed} aria-disabled={busy(pending)}
      onClick={() => { if (request && agreed) void run(request); }}>{journey.text.request_label}</button>}
    {decline && <button className="control" type="button" aria-disabled={busy(pending)}
      onClick={() => { if (pending) return; setAgreed(false); void run(decline); }}>{journey.text.decline_label}</button>}
  </section>;
}

function ReadbackForm({ journey, onResult, onPending, prepared }: { journey: Journey; onResult: (r: ActionResult) => void;
  onPending: (pending: boolean) => void; prepared: { current: { text: string; token: string } | null } }) {
  const copy = journey.text;
  const [draft, setDraft] = useState(copy.saved_words ?? "");
  const [preview, setPreview] = useState(false), [error, setError] = useState(false), [pending, setPending] = useState(false);
  useReportPending(pending, onPending);
  const input = useRef<HTMLTextAreaElement>(null), answer = useRef<HTMLDivElement>(null);
  const canConfirm = journey.commands.some(o => o.kind === "confirm_words");
  const saved = copy.saved_words !== undefined && draft === copy.saved_words;
  function review(event: React.FormEvent) {
    event.preventDefault();
    if (pending) return;
    if (!draft.trim() || Array.from(draft).length > 2048) { setError(true); input.current?.focus(); return; }
    setError(false); setPreview(true); requestAnimationFrame(() => answer.current?.focus());
  }
  async function checkDraft() {
    if (pending) return;
    const text = draft;
    setPending(true);
    try {
      if (!prepared.current || prepared.current.text !== text) {
        const form = new FormData(); form.set("text", text); form.set("parent_id", journey.flow.latest_restatement_id ?? "");
        const result = await prepareReadbackWords(form);
        if (!result.ok) { onResult({ state: "recovery" }); return; }
        prepared.current = { text, token: result.token };
      }
      const confirmed = await sendReadback({ kind: "confirm_words", offer_id: "confirm_words", permitted_choice_ids: [],
        operation_token: prepared.current.token }, text);
      onResult(confirmed);
      if (confirmed.state === "loaded") {
        const scoring = confirmed.journey.commands.find(o => o.kind === "score_words" || o.kind === "repair_words");
        if (scoring) onResult(await sendReadback(scoring));
      }
    } catch { onResult({ state: "recovery" }); }
    finally { setPending(false); }
  }
  async function retry() {
    if (pending) return;
    setPending(true);
    try {
      const supersede = journey.commands.find(o => o.kind === "supersede_extraction");
      let current = journey;
      if (supersede) {
        const result = await sendReadback(supersede); onResult(result);
        if (result.state !== "loaded") return;
        current = result.journey;
      }
      const scoring = current.commands.find(o => o.kind === "score_words" || o.kind === "repair_words");
      if (scoring) onResult(await sendReadback(scoring));
    } catch { onResult({ state: "recovery" }); }
    finally { setPending(false); }
  }
  return <section>
    {journey.step === "repair" && <div className="timing-repair">
      <p>{copy.repair_example_label} <q>{copy.repair_answer}</q>.</p>
      <p>{copy.repair_plan_label} <strong>{copy.repair_deadline}</strong>.</p>
    </div>}
    {canConfirm && <form onSubmit={review}>
      <label htmlFor="readback-words">{copy.input_label}</label>
      <p id="readback-help">{copy.input_help}</p>
      <textarea id="readback-words" ref={input} value={draft} disabled={pending} maxLength={4096}
        aria-invalid={error} aria-describedby={error ? "readback-help readback-error" : "readback-help"}
        onChange={event => { setDraft(event.target.value); setPreview(false); setError(false); prepared.current = null; }} />
      {error && <p id="readback-error" role="alert">{copy.input_error}</p>}
      <button className="control" type="submit" aria-disabled={busy(pending)}>{copy.review_label}</button>
    </form>}
    {(preview || copy.saved_words !== undefined) && <div tabIndex={-1} ref={answer} className="answer-preview">
      <h2>{copy.answer_label}</h2>
      {preview && !saved && <p>{copy.preview_label}</p>}
      <blockquote>{preview ? draft : copy.saved_words}</blockquote>
      {preview && !saved && canConfirm && <>
        <p>{copy.confirmation_help}</p>
        <button className="control primary" type="button" aria-disabled={busy(pending)} onClick={checkDraft}>{copy.confirmation_label}</button>
      </>}
    </div>}
    {saved && (journey.commands.some(o => ["score_words", "repair_words", "supersede_extraction"].includes(o.kind))) && <>
      <p>{copy.retry_help}</p><button className="control primary" type="button" aria-disabled={busy(pending)} onClick={retry}>{copy.retry_label}</button>
    </>}
  </section>;
}
/** Render stored values; lower same-episode revisions never repaint the screen. */
export function PatientJourney(props: Props) {
  const [large, setLarge] = useState(false);
  const [current, setCurrent] = useState<Props>(props);
  const latest = useRef<Journey | null>(props.state === "loaded" ? props.journey : null);
  const main = useRef<HTMLElement>(null);
  const showOpener = useRef<HTMLButtonElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const prepared = useRef<{ text: string; token: string } | null>(null);
  const initialServerAnswers = useRef(props.state === "loaded" && (props.journey.plan !== null || props.journey.revealed_plan !== null));
  const [commandPending, setCommandPending] = useState(false);
  // Feedback shown when a command starts belongs to the previous command; fresh server feedback replaces it.
  const [formPending, setFormPending] = useState(false);
  const shownFeedback = useRef<string | undefined>(undefined), staleFeedback = useRef<string | undefined>(undefined);
  const reportPending = useRef((pending: boolean) => {
    if (pending) staleFeedback.current = shownFeedback.current;
    setFormPending(pending);
  }).current;
  useEffect(() => {
    if (typeof window === "undefined" || window.location.search !== "?focus=show-plan") return;
    // After Hide reloads the document, land on the opener, or main if the step no longer offers it.
    (showOpener.current ?? main.current)?.focus();
    window.history.replaceState(window.history.state, "", window.location.pathname);
  }, []);
  const router = useRouter();
  function accept(next: Props, fromRead = false) {
    if (next.state === "loaded") {
      const accepted = reconcileJourney(latest.current, next.journey, fromRead);
      if (!accepted) {
        router.refresh(); // Read once; never retry a mutation or compute clinical state.
        return;
      }
      latest.current = accepted;
    }
    setCurrent(next);
  }
  useEffect(() => { accept(props, true); }, [props]); // A server refresh can change expiry at equal revision.
  useEffect(() => {
    // Slice 22: a same-origin judge stage re-reads its ledger; the message carries only the revision.
    if (typeof window !== "undefined" && current.state === "loaded") notifyParent(window, current.journey.revision);
  }, [current]);
  // Keep a stable callback so an action result is applied once, not after every text-size render.
  const resultHandler = useRef<(r: ActionResult) => void>(() => {});
  const focusAfterResult = useRef<{ step: string | undefined; active: Element | null; recovery: boolean } | null>(null);
  resultHandler.current = r => {
    focusAfterResult.current = { step: latest.current?.step, recovery: r.state === "recovery",
      active: typeof document === "undefined" ? null : document.activeElement };
    accept(r.state === "conflict" ? { state: "loaded", journey: r.journey } : r);
  };
  // Decide after the result is committed: a same-step update (such as the consent checkbox) keeps
  // the control that is still there; a step change, recovery or removed control moves focus to main.
  useLayoutEffect(() => {
    const intent = focusAfterResult.current;
    if (!intent) return;
    focusAfterResult.current = null;
    const { active } = intent;
    const kept = !intent.recovery && intent.step !== undefined && latest.current?.step === intent.step &&
      active instanceof HTMLElement && active !== main.current && active.isConnected && main.current?.contains(active);
    if (kept) { active.focus(); return; }
    // Already on main: VoiceOver ignores refocusing it, so a step change focuses the new heading.
    if (active === main.current && latest.current?.step !== intent.step) heading.current?.focus();
    else main.current?.focus();
  }, [current]);
  const [onResult] = useState(() => (r: ActionResult) => resultHandler.current(r));
  const recovery = current.state === "recovery";
  const journey = current.state === "loaded" ? current.journey : null;
  const copy: Record<string, string> = journey?.text ?? ENTRY_COPY;
  shownFeedback.current = copy.feedback;
  const liveStatus = formPending ? (copy.feedback !== undefined && copy.feedback !== staleFeedback.current ? copy.feedback : RECOVERY_COPY.loading)
    : copy.feedback ?? "";
  const offer = journey?.commands.find(o => o.kind === "select_example" && o.operation_token);
  const creation = current.state !== "loaded" ? current.creationToken : undefined;
  // Quick safety check (Gate 1 to 4, 16 October 2026): it runs before any plan is created.
  const [safety, setSafety] = useState<{ phase: "start" | "check" | "clear"; unchecked: string[] }>({ phase: "start", unchecked: [] });
  const needsCheck = Boolean(creation || offer?.operation_token);
  const checking = needsCheck && safety.phase === "check";
  async function run(offer: CommandOffer) {
    if (commandPending) return;
    setCommandPending(true);
    try {
      const result = await sendReadback(offer);
      if (result.state === "loaded" && offer.kind === "readback_started") {
        window.location.assign("/patient"); // A fresh document removes the prior plan's HTML/RSC.
        return;
      }
      if (result.state === "loaded" && offer.kind === "hide_plan" && initialServerAnswers.current) {
        window.location.assign("/patient?focus=show-plan");
        return;
      }
      if (result.state !== "recovery" && (offer.kind === "show_plan" || offer.kind === "hide_plan")) {
        accept({ state: "loaded", journey: result.journey });
        if (offer.kind === "hide_plan") requestAnimationFrame(() => {
          if (result.journey.step === journey?.step) showOpener.current?.focus();
          else main.current?.focus();
        });
        return;
      }
      onResult(result);
    }
    catch { onResult({ state: "recovery" }); }
    finally { setCommandPending(false); }
  }
  const readback = journey?.commands.find(o => o.kind === "readback_started" && o.operation_token);
  const show = journey?.commands.find(o => o.kind === "show_plan" && o.operation_token);
  const hide = journey?.commands.find(o => o.kind === "hide_plan" && o.operation_token);
  const progress = journey ? progressStep(journey) : null;
  const folded = journey !== null && ["readback", "repair"].includes(journey.step);
  // The slip is open on the plan and request-failed screens; there "Show my plan" would repeat it.
  const slip = journey?.plan && (journey.step === "plan" || journey.step === "unresolved") ? journey.plan : null;
  const open = journey?.closure === "open" || journey?.closure === "expired_unresolved";
  const showButton = show && !slip && <button className="control" type="button" ref={showOpener} aria-disabled={busy(commandPending)} onClick={() => run(show)}>{copy.show_label}</button>;
  return <div className={`journey${large ? " journey-large" : ""}`}>
    <a className="skip-link" href="#main">Skip to main content</a>
    <header className="journey-header"><span className="wordmark">CareRelay</span>
      <button className="text-control" aria-pressed={large} onClick={() => setLarge(!large)}>{large ? "Smaller text" : "Larger text"}</button>
    </header>
    {/* Focus lands here after a step change; its name says which step and status it is. */}
    <main id="main" className="screen" tabIndex={-1} ref={main} aria-labelledby="journey-heading journey-state">
      {checking ? <SafetyCheck onClear={unchecked => setSafety({ phase: "clear", unchecked })} /> : <>
      {progress !== null && <Progress step={progress} />}
      <h1 id="journey-heading" tabIndex={-1} ref={heading}>{recovery ? RECOVERY_COPY.heading : copy.heading}</h1>
      {!recovery && copy.status && <p id="journey-state" className="journey-status">{copy.status}</p>}
      {(recovery || copy.description && journey?.step !== "barrier") && <p>{recovery ? RECOVERY_COPY.description : copy.description}</p>}
      {journey?.step === "plan" && slip && <PlanSlip plan={slip} labels={copy} />}
      {journey && <Lines lines={journey.lines} open={open}>
        {journey.step === "unresolved" && slip && <PlanSlip plan={slip} labels={SLIP_COPY} />}
      </Lines>}
      {journey?.question && journey.step !== "barrier" && journey.question.text !== copy.heading && <p className="journey-question">{journey.question.text}</p>}
      {folded && <section className="slip folded" aria-label={SLIP_COPY.folded}>
        <p className="fold-msg"><Icon name="folded" /><span>{SLIP_COPY.folded}</span></p>
        {showButton}
      </section>}
      {copy.notice && <p className="demo-label">{copy.notice}</p>}
      <p role="status" className="journey-live">{liveStatus}</p>
      {journey && ["readback", "repair"].includes(journey.step) && <ReadbackForm
        key={`${journey.flow.readback_attempt_id}:${journey.flow.latest_restatement_id}`} journey={journey}
        onResult={onResult} onPending={reportPending} prepared={prepared} />}
      {journey?.step === "barrier" && <BarrierForm key={journey.disposition_version} journey={journey} onResult={onResult} onPending={reportPending} />}
      {journey?.step === "permission" && journey.commands.some(o => ["grant_share", "decline_share", "revoke_share", "request"].includes(o.kind)) &&
        <PermissionControls key={`${journey.disposition_version}:${journey.step}`} journey={journey} onResult={onResult}
          onPending={reportPending} />}
      {readback && <button className="control primary" type="button" aria-disabled={busy(commandPending)} onClick={() => run(readback)}>{copy.readback_label}</button>}
      {!folded && showButton}
      <HintCard visible={journey?.revealed_plan != null} revision={journey?.revision ?? 0} title={copy.revealed_heading} closeLabel={copy.hide_label}
        opener={showOpener} fallback={main} onHide={() => { if (hide) void run(hide); }}>
        {journey?.revealed_plan && <>
          <p className="demo-label">{copy.reveal_notice}</p>
          <PlanRows plan={journey.revealed_plan} labels={{ action_label: copy.reveal_action_label,
            deadline_label: copy.reveal_deadline_label, owner_label: copy.reveal_owner_label }} />
          <p>{copy.reveal_fallback}</p>
        </>}
      </HintCard>
      {recovery && <a className="control" href="/patient">{RECOVERY_COPY.retry}</a>}
      {needsCheck && safety.phase === "start" && <button className="control primary" type="button"
        aria-disabled={busy(commandPending || formPending)}
        onClick={() => { if (!commandPending && !formPending) setSafety({ phase: "check", unchecked: [] }); }}>{ENTRY_COPY.start}</button>}
      {needsCheck && safety.phase === "clear" && <div className="journey-status-box calm"><Icon name="check" /><div>
        <p className="journey-line">{SAFETY_COPY.clear}</p>
        {safety.unchecked.length > 0 && <p className="journey-line">{uncheckedLine(safety.unchecked)}</p>}
      </div></div>}
      {safety.phase === "clear" && creation && <ExampleForm token={creation} kind="create" onResult={onResult} onPending={reportPending} />}
      {safety.phase === "clear" && offer?.operation_token && <ExampleForm token={offer.operation_token} kind="select_example" onResult={onResult}
        onPending={reportPending} />}
      {current.state === "entry" && <a className="control primary" href="/example">{ENTRY_COPY.start}</a>}
      {journey && <a className="journey-new-example" href="/example">{RESTART_LABEL}</a>}
      </>}
    </main>
    <footer className="journey-footer">{journey?.fixture_label ?? JOURNEY_LABEL}</footer>
  </div>;
}
