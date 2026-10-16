import { axisValues, type LedgerDetail, type PanelState } from "@/lib/judge";
import { Icon } from "./RelayTrack";

const REFUSALS: ReadonlySet<PanelState> = new Set(["request sent", "request failed", "stopped", "expired"]);

/** The outcome lanes: the simulated provider, the three separate axes, and what CareRelay will not do. */
export function OutcomeLanes({ detail, state }: { detail: LedgerDetail; state: PanelState }) {
  const axes = axisValues(detail);
  const deadline = detail.plan_reference?.deadline_display ?? "";
  const reply = detail.provider_reply;
  return (
    <>
      <section className="lane sim" aria-labelledby="lane-sim">
        <div className="lane-head"><h3 id="lane-sim"><Icon name="provider" />
          {reply ? `The simulated provider replied: ${reply}` : "The simulated provider has not replied"}</h3>
          <span className="lane-note">Simulated, labelled everywhere</span></div>
        <div className="lane-body">
          {detail.attempts > 0 ? <p>Shared with consent: the action and the deadline. No caregiver message was sent.</p> : null}
          <div className="meta">
            {detail.origin ? <span>Origin <b>{detail.origin}</b></span> : null}
            <span>Attempt <b>{detail.attempts}</b></span>
          </div>
        </div>
      </section>

      <section className="lane rules" aria-labelledby="lane-axes">
        <div className="lane-head"><h3 id="lane-axes"><Icon name="rules" />CareRelay recorded what is true, separately</h3>
          <span className="lane-note">Fixed rules, no model</span></div>
        <div className="lane-body">
          <div className="axes">
            <div className={`axis${detail.execution === "failed" ? " bad" : ""}`}><small>Request sent</small><b>{axes.sent}</b></div>
            <div className={`axis${detail.evidence === "none" ? " bad" : ""}`}><small>Proof of care</small><b>{axes.care}</b></div>
            <div className={`axis${detail.closure === "open" || detail.closure === "expired_unresolved" ? " bad" : ""}`}><small>Case</small><b>{axes.caseState}</b></div>
          </div>
          <p className="lane-after">Sending a request and getting care are tracked apart, so a sent request can never be read as care arranged.</p>
        </div>
      </section>

      {REFUSALS.has(state) ? (
        <section className="lane" aria-labelledby="lane-refuse">
          <div className="lane-head"><h3 id="lane-refuse">What CareRelay will not do here</h3></div>
          <div className="lane-body">
            <ul className="refuse">
              <li>Show “booked” or “done”.</li>
              <li>Move or drop the {deadline} deadline.</li>
              <li>Let a model decide anything about her care.</li>
              <li>Stop telling Mei she must act.</li>
            </ul>
          </div>
        </section>
      ) : null}
    </>
  );
}
