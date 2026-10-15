"use client";
import { useActionState, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { startExample, selectExample, prepareReadbackWords, submitReadback, prepareBarrierChoice, submitPermission, type ActionResult } from "@/app/actions";
import { ENTRY_COPY, RECOVERY_COPY, JOURNEY_LABEL, reconcileJourney, type Journey, type PlanView, type CommandOffer } from "@/lib/journey";
import { HintCard } from "./HintCard";

type Props = { state: "entry" | "recovery"; creationToken?: string } | { state: "loaded"; journey: Journey };
function PlanRows({ plan, labels }: { plan: PlanView; labels: Record<string, string> }) {
  return <dl className="journey-plan">
    <div><dt>{labels.action_label}</dt><dd>{plan.action_text}</dd></div>
    <div><dt>{labels.deadline_label}</dt><dd>{plan.deadline_display}</dd></div>
    {plan.current_owner_display !== null && <div><dt>{labels.owner_label}</dt><dd>{plan.current_owner_display}</dd></div>}
  </dl>;
}
function ExampleForm({ token, kind, onResult, onPending }: { token: string; kind: "create" | "select_example";
  onResult: (r: ActionResult) => void; onPending: (pending: boolean) => void }) {
  const [result, action, pending] = useActionState(kind === "create" ? startExample : selectExample, null);
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
  async function run(offer: CommandOffer) {
    if (commandPending) return;
    setCommandPending(true);
    try {
      const result = await sendReadback(offer);
      if (result.state === "loaded" && offer.kind === "readback_started") {
        window.location.assign("/"); // A fresh document removes the prior plan's HTML/RSC.
        return;
      }
      if (result.state === "loaded" && offer.kind === "hide_plan" && initialServerAnswers.current) {
        window.location.assign("/?focus=show-plan");
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
  return <div className={`journey${large ? " journey-large" : ""}`}>
    <a className="skip-link" href="#main">Skip to main content</a>
    <header className="journey-header"><span>CareRelay</span>
      <button className="text-control" aria-pressed={large} onClick={() => setLarge(!large)}>{large ? "Smaller text" : "Larger text"}</button>
    </header>
    {/* Focus lands here after a step change; its name says which step and status it is. */}
    <main id="main" className="screen" tabIndex={-1} ref={main} aria-labelledby="journey-heading journey-state">
      <p className="demo-label">{journey?.fixture_label ?? JOURNEY_LABEL}</p>
      <h1 id="journey-heading" tabIndex={-1} ref={heading}>{recovery ? RECOVERY_COPY.heading : copy.heading}</h1>
      {!recovery && copy.status && <p id="journey-state" className="journey-status">{copy.status}</p>}
      {(recovery || copy.description && journey?.step !== "barrier") && <p>{recovery ? RECOVERY_COPY.description : copy.description}</p>}
      {journey?.step === "plan" && journey.plan && <PlanRows plan={journey.plan} labels={copy} />}
      {journey?.lines.map((line, i) => <p className="journey-line" key={i}>{line}</p>)}
      {journey?.question && journey.step !== "barrier" && journey.question.text !== copy.heading && <p className="journey-question">{journey.question.text}</p>}
      {copy.notice && <p className="demo-label">{copy.notice}</p>}
      <p role="status" className="journey-live">{liveStatus}</p>
      {journey && ["readback", "repair"].includes(journey.step) && <ReadbackForm
        key={`${journey.flow.readback_attempt_id}:${journey.flow.latest_restatement_id}`} journey={journey}
        onResult={onResult} onPending={reportPending} prepared={prepared} />}
      {journey?.step === "barrier" && <BarrierForm key={journey.disposition_version} journey={journey} onResult={onResult} onPending={reportPending} />}
      {journey && journey.commands.some(o => ["grant_share", "decline_share", "revoke_share", "request"].includes(o.kind)) &&
        <PermissionControls key={`${journey.disposition_version}:${journey.step}`} journey={journey} onResult={onResult}
          onPending={reportPending} />}
      {readback && <button className="control primary" type="button" aria-disabled={busy(commandPending)} onClick={() => run(readback)}>{copy.readback_label}</button>}
      {show && <button className="control" type="button" ref={showOpener} aria-disabled={busy(commandPending)} onClick={() => run(show)}>{copy.show_label}</button>}
      <HintCard visible={journey?.revealed_plan != null} revision={journey?.revision ?? 0} title={copy.revealed_heading} closeLabel={copy.hide_label}
        opener={showOpener} fallback={main} onHide={() => { if (hide) void run(hide); }}>
        {journey?.revealed_plan && <>
          <p className="demo-label">{copy.reveal_notice}</p>
          <PlanRows plan={journey.revealed_plan} labels={{ action_label: copy.reveal_action_label,
            deadline_label: copy.reveal_deadline_label, owner_label: copy.reveal_owner_label }} />
          <p>{copy.reveal_fallback}</p>
        </>}
      </HintCard>
      {recovery && <a className="control" href="/">{RECOVERY_COPY.retry}</a>}
      {creation && <ExampleForm token={creation} kind="create" onResult={onResult} onPending={reportPending} />}
      {offer?.operation_token && <ExampleForm token={offer.operation_token} kind="select_example" onResult={onResult}
        onPending={reportPending} />}
      {current.state === "entry" && <a className="control primary" href="/example">{ENTRY_COPY.start}</a>}
      {journey && <a className="journey-new-example" href="/example">{ENTRY_COPY.heading}</a>}
    </main>
  </div>;
}
