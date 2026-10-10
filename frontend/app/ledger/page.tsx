import { createEpisode, getLedger } from "@/lib/api";

/**
 * The judge ledger. Slice 12.
 *
 * **This is not the patient screen and it is not linked from it.** The ledger
 * carries internal ids, the failure-event origin and `dwell_seconds`, and
 * `PLAN.md` 5.2.1 (constraint C8) says dwell is judge-facing evidence that must
 * never reach a patient. Two surfaces, two readers.
 *
 * **Nothing is derived here.** Every value below is a stored row or the
 * server's verdict over stored rows, and the fault assertions are printed with
 * the evidence they were taken from so a reader can disagree with the verdict
 * rather than only accept it.
 *
 * **An empty ledger is never drawn.** If the read fails, the page says so.
 * An empty table reads as "nothing happened", which is a claim no service made.
 */
export default async function LedgerPage() {
  const created = await createEpisode();
  if (!created.ok) {
    return (
      <main className="screen">
        <h1 className="screen-title">Judge ledger</h1>
        <p className="unavailable">
          The service could not be reached, so there is no ledger to show.
        </p>
        <p className="unavailable">
          Reason: {created.detail}. Nothing on this page is a record.
        </p>
      </main>
    );
  }

  const result = await getLedger(created.value.episode_id);
  if (!result.ok) {
    return (
      <main className="screen">
        <h1 className="screen-title">Judge ledger</h1>
        <p className="unavailable">
          The ledger could not be read, so nothing is shown. An empty ledger
          would read as &quot;nothing happened&quot;, which is a claim the
          service did not make.
        </p>
        <p className="unavailable">Reason: {result.detail}</p>
      </main>
    );
  }

  const ledger = result.value;
  const axes = Object.entries(ledger.axes);

  return (
    <main className="screen">
      {/* D11: the label is serialised with the record, so it travels with the
          data rather than sitting in page chrome. */}
      <p className="fixture-label" role="note">
        {ledger.fixture_label}
      </p>
      <h1 className="screen-title">Judge ledger</h1>
      <p className="ledger-note">
        Episode <code>{ledger.episode_id}</code>. This page is a read: it writes
        nothing, so opening it cannot record an expiry or move a deadline. The
        patient screen is the surface that records an expiry, and it is the only
        one.
      </p>

      <h2 className="section-title">The two axes</h2>
      <table className="ledger">
        <tbody>
          {axes.map(([name, value]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              <td>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="section-title">Failure-event origin</h2>
      <p className="ledger-note">
        Every origin present in this episode:{" "}
        <code className="origin">
          {ledger.origins.length ? ledger.origins.join(", ") : "none"}
        </code>
        . A platform failure and a local-simulation failure are distinguishable
        here, which is what the pinned call path requires.
      </p>
      <table className="ledger">
        <thead>
          <tr>
            <th>attempt</th>
            <th>route</th>
            <th>execution</th>
            <th>transitions</th>
          </tr>
        </thead>
        <tbody>
          {ledger.attempts.length === 0 ? (
            <tr>
              <td colSpan={4}>no attempt has been opened</td>
            </tr>
          ) : (
            ledger.attempts.map((attempt) => (
              <tr key={attempt.attempt_id}>
                <td>
                  <code>{attempt.attempt_id.slice(0, 8)}</code>
                </td>
                <td>{attempt.route_id}</td>
                <td>{attempt.execution}</td>
                <td>
                  {attempt.transitions.length === 0 ? (
                    <span>none recorded</span>
                  ) : (
                    attempt.transitions.map((transition) => (
                      <div key={transition.seq}>
                        {transition.seq}. {transition.kind}{" "}
                        <code className="origin">{transition.origin}</code>
                      </div>
                    ))
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>

      <h2 className="section-title">Expiry</h2>
      <p className="ledger-note">
        {ledger.expiry.length === 0
          ? "No expiry event is recorded. This read does not create one."
          : ledger.expiry
              .map(
                (event) =>
                  `disposition v${event.disposition_version} recorded at ${event.recorded_at}`,
              )
              .join("; ")}
      </p>

      <h2 className="section-title">Fault assertions</h2>
      <p className="ledger-note">
        Reporting only. These are verdicts over the rows above and cannot move
        an episode. Each is printed with the values it was taken from.
      </p>
      {ledger.fault_assertions.map((assertion) => (
        <p
          key={assertion.invariant}
          className={assertion.holds ? "holds-true" : "holds-false"}
        >
          <strong>
            {assertion.invariant}: {assertion.holds ? "holds" : "does NOT hold"}
          </strong>
          <br />
          {assertion.evidence}
        </p>
      ))}

      <h2 className="section-title">Dwell time</h2>
      <p className="ledger-note">
        Recorded for this ledger and never shown to a patient.{" "}
        {ledger.dwell_seconds_total === null
          ? "No dwell time is recorded."
          : `Total ${ledger.dwell_seconds_total}s across ${
              ledger.hint_events.length + ledger.restatements.length
            } row(s).`}
      </p>
      <table className="ledger">
        <thead>
          <tr>
            <th>row</th>
            <th>level</th>
            <th>outcome</th>
            <th>dwell_seconds</th>
          </tr>
        </thead>
        <tbody>
          {ledger.hint_events.map((event, index) => (
            <tr key={`hint-${index}`}>
              <td>hint event</td>
              <td>{event.hint_level}</td>
              <td>{event.kind}</td>
              <td>{event.dwell_seconds === null ? "not recorded" : event.dwell_seconds}</td>
            </tr>
          ))}
          {ledger.restatements.map((row, index) => (
            <tr key={`restatement-${index}`}>
              <td>restatement, round {row.repair_round}</td>
              <td>{row.hint_level}</td>
              <td>{row.outcome}</td>
              <td>{row.dwell_seconds === null ? "not recorded" : row.dwell_seconds}</td>
            </tr>
          ))}
          {ledger.hint_events.length === 0 && ledger.restatements.length === 0 ? (
            <tr>
              <td colSpan={4}>no scored row carries a dwell time</td>
            </tr>
          ) : null}
        </tbody>
      </table>

      <h2 className="section-title">Closure inputs</h2>
      <table className="ledger">
        <tbody>
          <tr>
            <th scope="row">disposition version</th>
            <td>{ledger.disposition_version ?? "none"}</td>
          </tr>
          <tr>
            <th scope="row">acceptance</th>
            <td>{ledger.acceptance ? ledger.acceptance.acceptance_id : "none"}</td>
          </tr>
          <tr>
            <th scope="row">escalation</th>
            <td>
              {ledger.escalation
                ? `${ledger.escalation.escalation_id} to ${
                    ledger.escalation.human_path ?? "an unnamed path"
                  }`
                : "none"}
            </td>
          </tr>
          <tr>
            <th scope="row">callbacks</th>
            <td>
              {ledger.callbacks.length === 0
                ? "none"
                : ledger.callbacks
                    .map(
                      (callback) =>
                        `#${callback.receipt_id} ${
                          callback.accepted ? "accepted" : "not applied"
                        } (${callback.origin})`,
                    )
                    .join("; ")}
            </td>
          </tr>
        </tbody>
      </table>
    </main>
  );
}
