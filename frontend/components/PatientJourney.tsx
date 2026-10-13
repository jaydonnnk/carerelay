"use client";
import { useState } from "react";
import { ENTRY_COPY, RECOVERY_COPY, JOURNEY_LABEL, type NoPlanJourney } from "@/lib/journey";

type Props = { state: "entry" | "recovery" } | { state: "loaded"; journey: NoPlanJourney };
/** Thin no-plan renderer. No clinical rules, hidden plan, forms or server actions. */
export function PatientJourney(props: Props) {
  const [large, setLarge] = useState(false);
  const recovery = props.state === "recovery";
  const copy = props.state === "loaded" ? props.journey.text : ENTRY_COPY;
  return (
    <div className={`journey${large ? " journey-large" : ""}`}>
      <a className="skip-link" href="#main">Skip to main content</a>
      <header className="journey-header">
        <span>CareRelay</span>
        <button className="text-control" aria-pressed={large} onClick={() => setLarge(!large)}>
          {large ? "Smaller text" : "Larger text"}
        </button>
      </header>
      <main id="main" className="screen" tabIndex={-1}>
        <p className="demo-label">{props.state === "loaded" ? props.journey.fixture_label : JOURNEY_LABEL}</p>
        <h1>{recovery ? RECOVERY_COPY.heading : copy.heading}</h1>
        {!recovery && <p className="journey-status">{copy.status}</p>}
        <p>{recovery ? RECOVERY_COPY.description : copy.description}</p>
        {recovery && <a className="control primary" href="/">{RECOVERY_COPY.retry}</a>}
        {/* /example only establishes a locator; no start mutation is offered. */}
        {props.state === "entry" && <a className="control primary" href="/example">{copy.start}</a>}
      </main>
    </div>
  );
}
