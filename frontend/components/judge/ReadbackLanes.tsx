import type { ReactNode } from "react";
import { FIELD_LABEL, FIELDS, RESULT_LABEL, transportLabel, actorName, checkedIn, readerHeading,
  type Field, type LedgerDetail } from "@/lib/judge";
import { Icon } from "./RelayTrack";

const SUP: Record<Field, string> = { action_id: "action", deadline_utc: "when", next_owner_id: "who" };
const ROWS: Field[] = ["action_id", "next_owner_id", "deadline_utc"];

/** Mei's saved words with each stored span underlined where it occurs in those words. */
function marked(words: string, spans: Record<Field, string | null>): ReactNode[] {
  const found = FIELDS.flatMap(f => {
    const span = spans[f];
    const at = span ? words.indexOf(span) : -1;
    return at < 0 || !span ? [] : [{ f, at, end: at + span.length }];
  }).sort((a, b) => a.at - b.at);
  const out: ReactNode[] = [];
  let cursor = 0;
  for (const s of found) {
    if (s.at < cursor) continue;
    out.push(words.slice(cursor, s.at));
    out.push(<span key={s.f} className="span">{words.slice(s.at, s.end)}<sup>{SUP[s.f]}</sup></span>);
    cursor = s.end;
  }
  out.push(words.slice(cursor));
  return out;
}

/** The read-back lanes: Mei's words, the reader's copied phrases, code's comparison. */
export function ReadbackLanes({ detail }: { detail: LedgerDetail }) {
  const latest = detail.latest;
  const extraction = detail.lastExtraction;
  const plan = detail.plan_reference;
  const sent = extraction !== null && extraction.validation !== "not_sent";
  const live = sent && extraction?.transport === "https";
  // A check that did not run has no round of its own; an older round is not shown in its place.
  const ran = extraction !== null && extraction.validation === "valid";
  const planSays: Record<Field, string | null> = { action_id: plan?.action_text ?? null,
    deadline_utc: plan?.deadline_display ?? null, next_owner_id: plan?.owner_display ?? null };
  const timing = checkedIn(extraction?.elapsed_ms ?? null);
  return (
    <>
      {ran && latest?.confirmed_words ? (
        <section className="lane patient-lane" aria-labelledby="lane-words">
          <div className="lane-head"><h3 id="lane-words"><Icon name="words" />Mei saved these words</h3>
            <span className="lane-note">Confirmed by Mei before any AI call</span></div>
          <div className="lane-body"><p className="quote">{latest.confirmed_words}</p></div>
        </section>
      ) : null}

      {extraction ? (
        <section className="lane adp" aria-labelledby="lane-reader">
          <div className="lane-head"><h3 id="lane-reader"><Icon name="adp" />{readerHeading(detail)}</h3>
            {live ? <span className="lane-note">Agent Development Platform</span> : null}</div>
          <div className="lane-body">
            {ran && latest?.confirmed_words ? <p className="quote">{marked(latest.confirmed_words, latest.spans)}</p> : null}
            <div className="meta">
              <span><b>{transportLabel(extraction)}</b></span>
              {sent && timing ? <span>{timing}</span> : null}
              {sent && extraction.request_id ? <span>Request <b className="code">{extraction.request_id.slice(0, 8)}…</b></span> : null}
              {sent ? <span>Instruction <b>{extraction.instruction_version}</b></span> : null}
              {sent ? <span>Schema <b>{extraction.schema_version}</b></span> : null}
              {sent ? <span><b>1</b> call, no retry</span> : <span><b>0</b> calls</span>}
            </div>
            {sent ? <p className="lane-after">{actorName(detail) === "Tencent ADP" ? "ADP" : actorName(detail)} may only copy words that are really there. CareRelay checks every phrase against the saved text before using it.</p> : null}
          </div>
        </section>
      ) : null}

      {ran && latest ? (
        <section className="lane rules" aria-labelledby="lane-rules">
          <div className="lane-head"><h3 id="lane-rules"><Icon name="rules" />CareRelay code compared them with the plan</h3>
            <span className="lane-note">Fixed rules, no model</span></div>
          <div className="lane-body">
            <table className="compare">
              <thead><tr><th scope="col">Field</th><th scope="col">Mei said</th><th scope="col">Plan says</th><th scope="col">Result</th></tr></thead>
              <tbody>
                {ROWS.map(f => {
                  const result = latest.fields[f];
                  return (
                    <tr key={f}>
                      <th scope="row">{FIELD_LABEL[f]}</th>
                      <td>{latest.spans[f] ?? ""}</td>
                      <td>{planSays[f] ?? ""}</td>
                      <td><span className={`verdict ${result === "matched" ? "ok" : result === "mismatched" ? "no" : "unclear"}`}>
                        {result === "uncertain" ? null : <Icon name={result === "matched" ? "yes" : "no"} width={3} />}
                        {RESULT_LABEL[result]}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </>
  );
}
