import { cookies } from "next/headers";
import Link from "next/link";
import { getLedger } from "@/lib/api";
import { decodeLocator, LOCATOR_COOKIE } from "@/lib/episode-locator";
import { OUTCOME_LANES, PATIENT_HEADING, READBACK_LANES, READ_FAILED, STEP_NAV, actorName, decodeLedgerDetail,
  offlineNote, panelState, stateCopy, stepIndex, trackLegs, type LedgerDetail, type PanelState } from "@/lib/judge";
import { StageFrame } from "@/components/judge/StageFrame";
import { RelayTrack, Icon } from "@/components/judge/RelayTrack";
import { ReadbackLanes } from "@/components/judge/ReadbackLanes";
import { OutcomeLanes } from "@/components/judge/OutcomeLanes";
import "../judge.css";

export const dynamic = "force-dynamic";
export const metadata = { title: "CareRelay | Judge view" };

type Read = { ok: true; detail: LedgerDetail | null } | { ok: false };

/**
 * The judge stage (Gate 2 D19, Gate 3 section 10). This server component reads only the
 * ledger, which never writes, so opening or refreshing the panel records nothing.
 */
async function read(): Promise<Read> {
  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;
  // No locator yet: the frame's first visit issues one, and no episode exists until the press.
  if (!cookie) return { ok: true, detail: null };
  const locator = decodeLocator(cookie, process.env.CARERELAY_API_TOKEN ?? "");
  if (!locator) return { ok: false };
  const result = await getLedger(locator.episode_id);
  if (!result.ok) return result.reason === "not_found" ? { ok: true, detail: null } : { ok: false };
  const detail = decodeLedgerDetail(result.value);
  return detail ? { ok: true, detail } : { ok: false };
}

function decisionNote(state: PanelState, d: LedgerDetail): string {
  const deadline = d.plan_reference?.deadline_display ?? "";
  if (state === "request failed") return `Mei still must act before ${deadline}. The fictional nurse line is her fallback.`;
  if (state === "accepted" || state === "handoff" || state === "documented") return "Chosen by code.";
  return `Chosen by code. The plan, the ${deadline} deadline and who acts are unchanged.`;
}

export default async function StagePage() {
  const result = await read();
  const detail = result.ok ? result.detail : null;
  const state: PanelState | null = result.ok ? (detail ? panelState(detail) : "start") : null;
  const copy = state ? stateCopy(state, detail) : READ_FAILED;
  const actor = actorName(detail);
  const legName = actor === "Tencent ADP" ? actor : actor.charAt(4).toUpperCase() + actor.slice(5);
  const heading = detail?.journey_step ? PATIENT_HEADING[detail.journey_step] : null;
  const lanes = state !== null && detail !== null && (READBACK_LANES.has(state) || OUTCOME_LANES.has(state));
  return (
    <div className="judge">
      <header className="stage-bar">
        <span className="wordmark">CareRelay</span>
        <span className="sim-note">Built for the NTU LKCMedicine challenge.</span>
        <nav aria-label="View">
          <Link href="/demo/stage" aria-current="page">Judge view</Link>
          <Link href="/">Patient only</Link>
        </nav>
      </header>
      <StageFrame>
        <ol className="steps" aria-label="Demo steps">
          {STEP_NAV.map((label, i) => (
            <li key={label} aria-current={state !== null && stepIndex(state) === i ? "step" : undefined}>{label}</li>
          ))}
        </ol>
        <div className="step-head"><h1>{copy.headline}</h1></div>
        <p className="lede">{copy.paragraph}</p>
        {offlineNote(detail) ? <p className="offline-note">{offlineNote(detail)}</p> : null}
        {state ? <RelayTrack legs={trackLegs(state)} readerName={legName} /> : null}
        {lanes && state && detail && READBACK_LANES.has(state) ? <ReadbackLanes detail={detail} /> : null}
        {lanes && state && detail && OUTCOME_LANES.has(state) ? <OutcomeLanes detail={detail} state={state} /> : null}
        {lanes && state && detail && heading ? (
          <div className="decision">
            <span className="arrow"><Icon name="arrow" width={2.4} /></span>
            <p><strong>Next screen: “{heading}”</strong><small>{decisionNote(state, detail)}</small></p>
          </div>
        ) : null}
        <p className="panel-foot"><Link href="/ledger">Open the full ledger</Link></p>
      </StageFrame>
    </div>
  );
}
