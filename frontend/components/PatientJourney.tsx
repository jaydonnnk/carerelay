"use client";
import { useActionState, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { startExample, selectExample, type ActionResult } from "@/app/actions";
import { ENTRY_COPY, RECOVERY_COPY, JOURNEY_LABEL, reconcileJourney, type Journey, type PlanView } from "@/lib/journey";

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
/** Render stored values; lower same-episode revisions never repaint the screen. */
export function PatientJourney(props: Props) {
  const [large, setLarge] = useState(false);
  const [current, setCurrent] = useState<Props>(props);
  const latest = useRef<Journey | null>(props.state === "loaded" ? props.journey : null);
  const main = useRef<HTMLElement>(null);
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
  resultHandler.current = r => { accept(r); requestAnimationFrame(() => main.current?.focus()); };
  const [onResult] = useState(() => (r: ActionResult) => resultHandler.current(r));
  const recovery = current.state === "recovery";
  const journey = current.state === "loaded" ? current.journey : null;
  const copy: Record<string, string> = journey?.text ?? ENTRY_COPY;
  const offer = journey?.commands.find(o => o.kind === "select_example" && o.operation_token);
  const creation = current.state !== "loaded" ? current.creationToken : undefined;
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
      {journey?.flow.interpretation === "pending" && !copy.feedback && <p role="status">{RECOVERY_COPY.loading}</p>}
      {journey?.revealed_plan && <section aria-label={copy.revealed_heading}><h2>{copy.revealed_heading}</h2><PlanRows plan={journey.revealed_plan} labels={{ action_label: copy.reveal_action_label, deadline_label: copy.reveal_deadline_label, owner_label: copy.reveal_owner_label }} /></section>}
      {recovery && <a className="control" href="/">{RECOVERY_COPY.retry}</a>}
      {creation && <ExampleForm token={creation} kind="create" onResult={onResult} />}
      {offer?.operation_token && <ExampleForm token={offer.operation_token} kind="select_example" onResult={onResult} />}
      {current.state === "entry" && <a className="control primary" href="/example">{ENTRY_COPY.start}</a>}
      {journey && <a className="journey-new-example" href="/example">{ENTRY_COPY.heading}</a>}
    </main>
  </div>;
}
