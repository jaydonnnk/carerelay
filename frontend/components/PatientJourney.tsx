"use client";
import { useActionState, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { startExample, selectExample, prepareReadbackWords, submitReadback, type ActionResult } from "@/app/actions";
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
function ExampleForm({ token, kind, onResult }: { token: string; kind: "create" | "select_example"; onResult: (r: ActionResult) => void }) {
  const [result, action, pending] = useActionState(kind === "create" ? startExample : selectExample, null);
  useEffect(() => { if (result) onResult(result); }, [result, onResult]);
  return <form action={action}>
    <input type="hidden" name="operation_token" value={token} />
    <button className="control primary" disabled={pending} type="submit">{ENTRY_COPY.start}</button>
    {pending && <p role="status">{RECOVERY_COPY.loading}</p>}
  </form>;
}

async function sendReadback(offer: CommandOffer, text?: string): Promise<ActionResult> {
  if (!offer.operation_token) return { state: "recovery" };
  const form = new FormData();
  form.set("kind", offer.kind); form.set("operation_token", offer.operation_token);
  if (text !== undefined) form.set("text", text);
  if (offer.kind === "supersede_extraction") form.set("old_operation_id", offer.permitted_choice_ids[0]);
  return submitReadback(form);
}

function ReadbackForm({ journey, onResult, prepared }: { journey: Journey; onResult: (r: ActionResult) => void;
  prepared: { current: { text: string; token: string } | null } }) {
  const copy = journey.text;
  const [draft, setDraft] = useState(copy.saved_words ?? "");
  const [preview, setPreview] = useState(false), [error, setError] = useState(false), [pending, setPending] = useState(false);
  const input = useRef<HTMLTextAreaElement>(null), answer = useRef<HTMLDivElement>(null);
  const canConfirm = journey.commands.some(o => o.kind === "confirm_words");
  const saved = copy.saved_words !== undefined && draft === copy.saved_words;
  function review(event: React.FormEvent) {
    event.preventDefault();
    if (!draft.trim() || Array.from(draft).length > 2048) { setError(true); input.current?.focus(); return; }
    setError(false); setPreview(true); requestAnimationFrame(() => answer.current?.focus());
  }
  async function checkDraft() {
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
      <button className="control" type="submit" disabled={pending}>{copy.review_label}</button>
    </form>}
    {(preview || copy.saved_words !== undefined) && <div tabIndex={-1} ref={answer} className="answer-preview">
      <h2>{copy.answer_label}</h2>
      {preview && !saved && <p>{copy.preview_label}</p>}
      <blockquote>{preview ? draft : copy.saved_words}</blockquote>
      {preview && !saved && canConfirm && <>
        <p>{copy.confirmation_help}</p>
        <button className="control primary" type="button" disabled={pending} onClick={checkDraft}>{copy.confirmation_label}</button>
      </>}
    </div>}
    {saved && (journey.commands.some(o => ["score_words", "repair_words", "supersede_extraction"].includes(o.kind))) && <>
      <p>{copy.retry_help}</p><button className="control primary" type="button" disabled={pending} onClick={retry}>{copy.retry_label}</button>
    </>}
    {pending && <p role="status">{RECOVERY_COPY.loading}</p>}
  </section>;
}
/** Render stored values; lower same-episode revisions never repaint the screen. */
export function PatientJourney(props: Props) {
  const [large, setLarge] = useState(false);
  const [current, setCurrent] = useState<Props>(props);
  const latest = useRef<Journey | null>(props.state === "loaded" ? props.journey : null);
  const main = useRef<HTMLElement>(null);
  const showOpener = useRef<HTMLButtonElement>(null);
  const prepared = useRef<{ text: string; token: string } | null>(null);
  const initialServerAnswers = useRef(props.state === "loaded" && (props.journey.plan !== null || props.journey.revealed_plan !== null));
  const [commandPending, setCommandPending] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined" && window.location.search === "?focus=show-plan") showOpener.current?.focus();
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
  resultHandler.current = r => { accept(r.state === "conflict" ? { state: "loaded", journey: r.journey } : r);
    requestAnimationFrame(() => main.current?.focus()); };
  const [onResult] = useState(() => (r: ActionResult) => resultHandler.current(r));
  const recovery = current.state === "recovery";
  const journey = current.state === "loaded" ? current.journey : null;
  const copy: Record<string, string> = journey?.text ?? ENTRY_COPY;
  const offer = journey?.commands.find(o => o.kind === "select_example" && o.operation_token);
  const creation = current.state !== "loaded" ? current.creationToken : undefined;
  async function run(offer: CommandOffer) {
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
    <main id="main" className="screen" tabIndex={-1} ref={main}>
      <p className="demo-label">{journey?.fixture_label ?? JOURNEY_LABEL}</p>
      <h1>{recovery ? RECOVERY_COPY.heading : copy.heading}</h1>
      {!recovery && copy.status && <p className="journey-status">{copy.status}</p>}
      {(recovery || copy.description) && <p>{recovery ? RECOVERY_COPY.description : copy.description}</p>}
      {journey?.step === "plan" && journey.plan && <PlanRows plan={journey.plan} labels={copy} />}
      {journey?.lines.map((line, i) => <p className="journey-line" key={i}>{line}</p>)}
      {journey?.question && journey.question.text !== copy.heading && <p className="journey-question">{journey.question.text}</p>}
      {copy.notice && <p className="demo-label">{copy.notice}</p>}
      {copy.feedback && <p role="status">{copy.feedback}</p>}
      {journey && ["readback", "repair"].includes(journey.step) && <ReadbackForm
        key={`${journey.flow.readback_attempt_id}:${journey.flow.latest_restatement_id}`} journey={journey}
        onResult={onResult} prepared={prepared} />}
      {readback && <button className="control primary" type="button" disabled={commandPending} onClick={() => run(readback)}>{copy.readback_label}</button>}
      {show && <button className="control" type="button" ref={showOpener} disabled={commandPending} onClick={() => run(show)}>{copy.show_label}</button>}
      <HintCard visible={journey?.revealed_plan != null} revision={journey?.revision ?? 0} title={copy.revealed_heading} closeLabel={copy.hide_label}
        opener={showOpener} fallback={main} onHide={() => { if (hide) void run(hide); }}>
        {journey?.revealed_plan && <PlanRows plan={journey.revealed_plan} labels={{ action_label: copy.reveal_action_label,
          deadline_label: copy.reveal_deadline_label, owner_label: copy.reveal_owner_label }} />}
      </HintCard>
      {recovery && <a className="control" href="/">{RECOVERY_COPY.retry}</a>}
      {creation && <ExampleForm token={creation} kind="create" onResult={onResult} />}
      {offer?.operation_token && <ExampleForm token={offer.operation_token} kind="select_example" onResult={onResult} />}
      {current.state === "entry" && <a className="control primary" href="/example">{ENTRY_COPY.start}</a>}
      {journey && <a className="journey-new-example" href="/example">{ENTRY_COPY.heading}</a>}
    </main>
  </div>;
}
