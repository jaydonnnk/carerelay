import type { ReactNode } from "react";
import type { Legs } from "@/lib/judge";

/** Inline icons from the approved mockups (`design/mocks/redesign/`). Decorative only. */
const PATHS: Record<string, ReactNode> = {
  person: <><circle cx="12" cy="8" r="4" /><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" /></>,
  adp: <><path d="M7 4H4v16h3M17 4h3v16h-3" /><path d="M8 9h8M8 13h5" /></>,
  rules: <><path d="M12 3v18M6 21h12M4 7h16" /><path d="M7 7l-3 7h6zM17 7l-3 7h6z" /></>,
  provider: <><path d="M4 21V6l8-3 8 3v15" /><path d="M9 21v-5h6v5M9 9h1M14 9h1M9 12h1M14 12h1" /></>,
  phone: <path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z" />,
  words: <><path d="M4 5h16v11H9l-5 4z" /><path d="M8 9h8M8 12h5" /></>,
  yes: <path d="M5 12l5 5 9-10" />,
  no: <path d="M6 6l12 12M18 6L6 18" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18M8 14h3M8 17h6" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
};

export function Icon({ name, width = 2 }: { name: keyof typeof PATHS; width?: number }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={width} strokeLinecap="round"
      strokeLinejoin="round" aria-hidden="true" focusable="false">{PATHS[name]}</svg>
  );
}

const LEGS = [
  { key: "mei", cls: "person", icon: "person", name: "Mei" },
  { key: "adp", cls: "adp", icon: "adp", name: "Tencent ADP" },
  { key: "rules", cls: "rules", icon: "rules", name: "CareRelay rules" },
  { key: "provider", cls: "sim", icon: "provider", name: "Provider" },
  { key: "nurse", cls: "sim", icon: "phone", name: "Nurse line" },
] as const;

const MARK_TEXT = { active: "now", done: "done", failed: "failed" } as const;

/** "Who has the plan": five legs, a mark per leg, and the yellow "Must act" tag. */
export function RelayTrack({ legs, readerName }: { legs: Legs; readerName: string }) {
  return (
    <section className="track-wrap" aria-labelledby="track-h">
      <div className="track-title">
        <h2 id="track-h">Who has the plan</h2>
        <p>The yellow tag shows who must act. It moves only when someone agrees.</p>
      </div>
      <ol className="track">
        {LEGS.map(leg => {
          const state = legs[leg.key];
          const cls = ["leg", leg.cls, state.mark === "failed" ? "failed active" : state.mark ?? ""].join(" ").trim();
          return (
            <li key={leg.key} className={cls}>
              <span className="node"><Icon name={leg.icon} /></span>
              <strong>{leg.key === "adp" ? readerName : leg.name}</strong>
              <small>{state.small}</small>
              {state.mark ? <span className="visually-hidden">({MARK_TEXT[state.mark]})</span> : null}
              {state.tag ? <span className="baton">Must act</span> : null}
            </li>
          );
        })}
      </ol>
      <div className="track-legend">
        <span><i className="key-adp" />Tencent ADP reads words</span>
        <span><i className="key-code" />CareRelay code decides</span>
        <span><i className="key-sim" />Simulated service</span>
        <span><i className="key-plan" />The plan</span>
      </div>
    </section>
  );
}
