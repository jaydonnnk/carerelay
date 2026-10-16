"""Slice 23: judge view and ledger read-back detail (Gate 3 sections 10.2 to 10.7).

Backend checks L1 to L6 and S1 run against the real service and SQLite store, seeded through
`_journey_fixtures.seed_journey` or the actual confirm/score command path. Frontend checks
F1, F2, F3 and F5 run the production `frontend/lib/judge.ts` through Node, the same offline
pattern as `test_patient_redesign.py`. No network, no Next.js, no live ADP.
"""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
import subprocess

import pytest

from carerelay.demo import fixture
from carerelay.service import ScenarioClock, _elapsed_ms
from test_truthfulness import make_service
from test_field_repair import start_readback, confirm, score

ROOT = Path(__file__).resolve().parents[1]
NM = ROOT / "frontend/node_modules"
WRONG_TIME = "I will go to the clinic myself today before 8pm"
SEED_CASES = ["start", "plan", "readback", "repair", "uncertain", "unavailable", "pending", "barrier", "permission",
    "declined", "waiting", "acknowledged", "failed", "handoff", "stopped", "accepted", "h3", "documented",
    "expired", "expired_handoff", "expired_stopped"]


def table_counts(path):
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
        return {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in names}


def seeded_service(tmp_path, case):
    from _journey_fixtures import seed_journey
    path = tmp_path / f"s23-{case}.sqlite"
    service = make_service(path)
    episode = "s23-" + case
    seed_journey(service, episode, case)
    return service, episode, path


def wrong_time_then_repair(tmp_path, name="flow"):
    service = make_service(tmp_path / f"{name}.sqlite")
    episode = start_readback(service, episode="s23-" + name)
    first = confirm(service, episode, WRONG_TIME)
    score(service, episode)
    second = confirm(service, episode, "today before 6pm")
    score(service, episode)
    return service, episode, first.receipt.result_ref, second.receipt.result_ref


# ---------------------------------------------------------------------------
# L1: one derivation for the patient read and the ledger
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", SEED_CASES)
def test_l1_ledger_step_equals_the_journey_derivation(tmp_path, case):
    service, episode, _ = seeded_service(tmp_path, case)
    try:
        ledger = service.project_ledger(episode).as_dict()
        journey = service.project_journey(episode)
        assert ledger["journey_step"] == journey.step
        assert ledger["interpretation"] == journey.flow.interpretation
    finally:
        service._store.close()


# ---------------------------------------------------------------------------
# L2: a ledger read writes nothing, including the expiry and missing-H2 edges
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", ["plan", "repair", "expired", "failed", "pending"])
def test_l2_ledger_read_writes_nothing(tmp_path, case):
    service, episode, path = seeded_service(tmp_path, case)
    try:
        before = table_counts(path)
        for _ in range(3):
            service.project_ledger(episode)
        assert table_counts(path) == before
        if case in {"repair", "expired"}:
            # The edge is real: the patient read does write here, so the equality above is not vacuous.
            service.project_journey(episode)
            assert table_counts(path) != before
    finally:
        service._store.close()


# ---------------------------------------------------------------------------
# L3 and L4: the right round's words, and the stored spans and results
# ---------------------------------------------------------------------------

def test_l3_confirmed_words_join_the_matching_round(tmp_path):
    service, episode, first, second = wrong_time_then_repair(tmp_path)
    try:
        rows = service.project_ledger(episode).as_dict()["restatements"]
        assert [r["readback"]["confirmed_words"] for r in rows] == [WRONG_TIME, "today before 6pm"]
        assert [r["extraction_provenance"]["confirmation_id"] for r in rows] == [first, second]
    finally:
        service._store.close()


def test_l3_zero_or_two_matching_confirmations_give_null(tmp_path):
    service, episode, first, _ = wrong_time_then_repair(tmp_path)
    try:
        events = [json.loads(p) for k, p, _ in service._store.list_events(episode) if k == "words_confirmed"]
        duplicate = dict(events[0])
        with service._store.journey_transaction(episode, write=True) as tx:
            tx._event("words_confirmed", duplicate, fixture.SCENARIO_NOW_UTC)
        rows = service.project_ledger(episode).as_dict()["restatements"]
        assert rows[0]["readback"]["confirmed_words"] is None, "two matches must not pick one"
        assert rows[1]["readback"]["confirmed_words"] == "today before 6pm"
    finally:
        service._store.close()
    legacy, ep, _ = seeded_service(tmp_path, "repair")
    try:
        row = legacy.project_ledger(ep).as_dict()["restatements"][0]
        assert row["extraction_provenance"] is None and row["readback"]["confirmed_words"] is None
    finally:
        legacy._store.close()


def test_l3_another_episodes_or_versions_words_never_match(tmp_path):
    service, episode, first, _ = wrong_time_then_repair(tmp_path)
    try:
        events = [json.loads(p) for k, p, _ in service._store.list_events(episode) if k == "words_confirmed"]
        with service._store.journey_transaction(episode, write=True) as tx:
            tx._event("words_confirmed", {**events[0], "disposition_version": 2, "text": "other version words"}, fixture.SCENARIO_NOW_UTC)
            tx._event("words_confirmed", {**events[0], "episode_id": "someone-else", "text": "other episode words"}, fixture.SCENARIO_NOW_UTC)
        rows = service.project_ledger(episode).as_dict()["restatements"]
        assert rows[0]["readback"]["confirmed_words"] == WRONG_TIME
    finally:
        service._store.close()


def test_l4_spans_and_fields_equal_the_stored_record(tmp_path):
    service, episode, _, _ = wrong_time_then_repair(tmp_path)
    try:
        stored = service._store.list_restatements(episode)
        rows = service.project_ledger(episode).as_dict()["restatements"]
        assert len(rows) == len(stored) == 2
        for row, record in zip(rows, stored):
            assert row["readback"]["spans"] == {"action_id": record.extracted.action_span,
                "deadline_utc": record.extracted.deadline_span, "next_owner_id": record.extracted.next_owner_span}
            for field, result in row["readback"]["fields"].items():
                assert field in getattr(record.comparison, result)
        assert rows[0]["readback"]["fields"] == {"action_id": "matched", "deadline_utc": "mismatched", "next_owner_id": "matched"}
        assert rows[0]["readback"]["spans"]["deadline_utc"] == "today before 8pm"
        # The repair round keeps the action and owner from round one; its own words hold only the time.
        assert rows[1]["readback"]["spans"]["action_id"] == "go to the clinic"
        assert rows[1]["readback"]["fields"] == {"action_id": "matched", "deadline_utc": "matched", "next_owner_id": "matched"}
    finally:
        service._store.close()


def test_l4_uncertainty_is_preserved(tmp_path):
    service, episode, _ = seeded_service(tmp_path, "uncertain")
    try:
        row = service.project_ledger(episode).as_dict()["restatements"][-1]
        assert set(row["readback"]["fields"].values()) == {"uncertain"}
        assert row["readback"]["spans"] == {"action_id": None, "deadline_utc": None, "next_owner_id": None}
    finally:
        service._store.close()


# ---------------------------------------------------------------------------
# L5: the judge keeps the plan while the patient's copy is folded away
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", ["readback", "repair"])
def test_l5_plan_reference_survives_readback_redaction(tmp_path, case):
    service, episode, _ = seeded_service(tmp_path, case)
    try:
        ledger = service.project_ledger(episode).as_dict()
        journey = service.project_journey(episode)
        assert journey.step == case and journey.plan is None, "the patient's plan is folded away"
        assert ledger["plan_reference"] == {"disposition_version": 1,
            "action_text": "Go to the fictional provider's same-day review.", "deadline_display": "6pm today",
            "owner_display": "You", "fallback_display": "the fictional nurse line"}
    finally:
        service._store.close()


def test_l5_no_plan_reference_without_a_plan(tmp_path):
    service, episode, _ = seeded_service(tmp_path, "start")
    try:
        ledger = service.project_ledger(episode).as_dict()
        assert ledger["plan_reference"] is None and ledger["journey_step"] == "start"
    finally:
        service._store.close()


# ---------------------------------------------------------------------------
# L6: server time from stored claim to stored completion
# ---------------------------------------------------------------------------

class SteppingClock:
    """Advances 1.25 s per read, so each stored timestamp differs and the read time differs again."""

    def __init__(self, start):
        self.now = start

    def now_utc(self):
        self.now += timedelta(milliseconds=1250)
        return self.now


def test_l6_elapsed_is_stored_completion_minus_claim(tmp_path):
    service = make_service(tmp_path / "timed.sqlite")
    service._clock = SteppingClock(fixture.SCENARIO_NOW_UTC)
    try:
        episode = start_readback(service, episode="s23-timed")
        confirm(service, episode, WRONG_TIME)
        score(service, episode)
        with service._store.journey_transaction(episode, write=False) as tx:
            claims = [r for r in tx.load_bundle(episode).commands if r["kind"] == "score_words"]
        claimed = next(r["recorded_at"] for r in claims if r["phase"] == "claimed")
        completed = next(r["recorded_at"] for r in claims if r["phase"] == "completed")
        expected = (datetime.fromisoformat(completed) - datetime.fromisoformat(claimed)) // timedelta(milliseconds=1)
        assert expected > 0
        extraction = service.project_ledger(episode).as_dict()["extractions"][-1]
        assert extraction["elapsed_ms"] == expected
    finally:
        service._store.close()


def test_l6_a_fixed_scenario_clock_reports_unknown_not_zero(tmp_path):
    service, episode, _, _ = wrong_time_then_repair(tmp_path)
    try:
        assert isinstance(service._clock, ScenarioClock)
        assert [e["elapsed_ms"] for e in service.project_ledger(episode).as_dict()["extractions"]] == [None, None]
    finally:
        service._store.close()


def test_l6_missing_timestamps_give_null():
    assert _elapsed_ms(None, "2026-09-30T01:00:01+00:00") is None
    assert _elapsed_ms("2026-09-30T01:00:01+00:00", None) is None
    assert _elapsed_ms("2026-09-30T01:00:00+00:00", "2026-09-30T01:00:01.2349+00:00") == 1234


# ---------------------------------------------------------------------------
# Frontend: the production judge module, run offline through Node
# ---------------------------------------------------------------------------

def node(script, data=None):
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps(data), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


TS = f'''import {{readFileSync}} from 'node:fs';
import ts from {json.dumps((NM / "typescript/lib/typescript.js").as_uri())};
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const transpile=s=>ts.transpileModule(s,{{compilerOptions:{{module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}}}).outputText;
const judgeUrl=url(transpile(readFileSync('frontend/lib/judge.ts','utf8')));
const J=await import(judgeUrl);
const input=JSON.parse(readFileSync(0,'utf8'));
'''


def judge(body, data=None):
    return node(TS + body, data)


def ledger_json(service, episode):
    return json.loads(json.dumps(service.project_ledger(episode).as_dict()))


@pytest.fixture
def flow_ledger(tmp_path):
    service, episode, _, _ = wrong_time_then_repair(tmp_path)
    try:
        repaired = ledger_json(service, episode)
    finally:
        service._store.close()
    service = make_service(tmp_path / "check.sqlite")
    try:
        episode = start_readback(service, episode="s23-check")
        confirm(service, episode, WRONG_TIME)
        score(service, episode)
        checked = ledger_json(service, episode)
    finally:
        service._store.close()
    return {"checked": checked, "repaired": repaired}


def malformed(good):
    cases = {}
    def case(name, edit):
        value = copy.deepcopy(good)
        edit(value)
        cases[name] = value
    case("missing journey_step", lambda v: v.pop("journey_step"))
    case("missing interpretation", lambda v: v.pop("interpretation"))
    case("missing plan_reference", lambda v: v.pop("plan_reference"))
    case("unknown step", lambda v: v.update(journey_step="booked"))
    case("unknown interpretation", lambda v: v.update(interpretation="graded"))
    case("plan without step", lambda v: v.update(journey_step=None))
    case("step without plan", lambda v: v.update(plan_reference=None))
    case("plan version differs", lambda v: v["plan_reference"].update(disposition_version=2))
    case("plan extra key", lambda v: v["plan_reference"].update(urgency="high"))
    case("plan empty action", lambda v: v["plan_reference"].update(action_text=""))
    case("not simulated", lambda v: v.update(simulated=False))
    case("simulated missing", lambda v: v.pop("simulated"))
    case("unknown execution", lambda v: v["axes"].update(execution="booked"))
    case("readback missing", lambda v: v["restatements"][-1].pop("readback"))
    case("fields missing key", lambda v: v["restatements"][-1]["readback"]["fields"].pop("deadline_utc"))
    case("fields extra key", lambda v: v["restatements"][-1]["readback"]["fields"].update(urgency="matched"))
    case("field result unknown", lambda v: v["restatements"][-1]["readback"]["fields"].update(deadline_utc="later"))
    case("spans missing key", lambda v: v["restatements"][-1]["readback"]["spans"].pop("action_id"))
    case("span not string", lambda v: v["restatements"][-1]["readback"]["spans"].update(action_id=7))
    case("words too long", lambda v: v["restatements"][-1]["readback"].update(confirmed_words="x" * 2049))
    case("words empty", lambda v: v["restatements"][-1]["readback"].update(confirmed_words=""))
    case("elapsed negative", lambda v: v["extractions"][-1].update(elapsed_ms=-1))
    case("elapsed fractional", lambda v: v["extractions"][-1].update(elapsed_ms=1.5))
    case("elapsed string", lambda v: v["extractions"][-1].update(elapsed_ms="6011"))
    case("elapsed missing", lambda v: v["extractions"][-1].pop("elapsed_ms"))
    case("transport unknown", lambda v: v["extractions"][-1].update(transport_provenance="unknown"))
    case("validation unknown", lambda v: v["extractions"][-1].update(validation="graded"))
    case("restatements not list", lambda v: v.update(restatements={}))
    return cases


def test_f1_decoder_accepts_the_real_ledger_and_rejects_each_malformed_field(flow_ledger):
    good = flow_ledger["checked"]
    cases = malformed(good)
    out = judge('''console.log(JSON.stringify({good: J.decodeLedgerDetail(input.good),
      bad: Object.fromEntries(Object.entries(input.bad).map(([k, v]) => [k, J.decodeLedgerDetail(v)]))}));''',
      {"good": good, "bad": cases})
    detail = out["good"]
    assert detail is not None
    assert detail["journey_step"] == "repair" and detail["latest"]["confirmed_words"] == WRONG_TIME
    assert detail["lastExtraction"]["transport"] == "local-sim" and detail["lastExtraction"]["elapsed_ms"] is None
    accepted = [name for name, value in out["bad"].items() if value is not None]
    assert accepted == [], f"malformed ledgers decoded: {accepted}"


def test_f1_a_start_ledger_missing_a_key_is_not_a_start(tmp_path):
    service, episode, _ = seeded_service(tmp_path, "start")
    try:
        good = ledger_json(service, episode)
    finally:
        service._store.close()
    out = judge('''console.log(JSON.stringify(input.map(v => J.decodeLedgerDetail(v))));''',
        [good, {k: v for k, v in good.items() if k != "journey_step"}, {k: v for k, v in good.items() if k != "interpretation"}])
    assert out[0] is not None and out[0]["journey_step"] == "start"
    assert out[1:] == [None, None]


EXPECTED_PANEL = {"start": "start", "plan": "plan", "readback": "readback", "repair": "deadline mismatch",
    "uncertain": "uncertain", "unavailable": "check did not run", "pending": "plan", "barrier": "match",
    "permission": "permission", "declined": "permission", "waiting": "request sent", "acknowledged": "request sent",
    "failed": "request failed", "handoff": "handoff", "stopped": "stopped", "accepted": "accepted", "h3": "stopped",
    "documented": "documented", "expired": "expired", "expired_handoff": "expired", "expired_stopped": "expired"}


def test_f2_panel_state_follows_the_approved_table_for_every_seeded_ledger(tmp_path):
    ledgers = {}
    for case in SEED_CASES:
        service, episode, _ = seeded_service(tmp_path, case)
        try:
            ledgers[case] = ledger_json(service, episode)
            ledgers[case]["_step"] = service.project_journey(episode).step
        finally:
            service._store.close()
    out = judge('''console.log(JSON.stringify(Object.fromEntries(Object.entries(input).map(([k, v]) => {
      const d = J.decodeLedgerDetail(v); return [k, d === null ? null : J.panelState(d)]; }))));''', ledgers)
    expected = {case: EXPECTED_PANEL[case] for case in SEED_CASES}
    # The table is applied to whatever step the server derived; record it so a fixture drift is visible.
    steps = {case: ledgers[case]["_step"] for case in SEED_CASES}
    assert out == expected, steps


def test_f2_synthetic_rows_cover_the_remaining_table_rows(flow_ledger):
    base = flow_ledger["checked"]
    def variant(step, interpretation, fields=None, execution="not_started"):
        v = copy.deepcopy(base)
        v.update(journey_step=step, interpretation=interpretation)
        v["axes"]["execution"] = execution
        if fields:
            v["restatements"][-1]["readback"]["fields"] = fields
        return v
    cases = {
        "pending": (variant("readback", "pending"), "pending"),
        "repair pending": (variant("repair", "pending"), "pending"),
        "unavailable": (variant("repair", "unavailable"), "check did not run"),
        "repair": (variant("repair", "scored"), "deadline mismatch"),
        "uncertain first": (variant("readback", "uncertain", {"action_id": "mismatched", "deadline_utc": "uncertain", "next_owner_id": "matched"}), "uncertain"),
        "other mismatch": (variant("readback", "scored", {"action_id": "mismatched", "deadline_utc": "matched", "next_owner_id": "matched"}), "other mismatch"),
        "clean readback": (variant("readback", "idle", {"action_id": "matched", "deadline_utc": "matched", "next_owner_id": "matched"}), "readback"),
        "plan acknowledged": (variant("plan", "scored", execution="acknowledged"), "request sent"),
        "permission attempted": (variant("permission", "scored", execution="attempted"), "request sent"),
        "unresolved": (variant("unresolved", "scored", execution="failed"), "request failed"),
    }
    out = judge('''console.log(JSON.stringify(Object.fromEntries(Object.entries(input).map(([k, v]) => {
      const d = J.decodeLedgerDetail(v); return [k, d === null ? null : J.panelState(d)]; }))));''',
      {k: v for k, (v, _) in cases.items()})
    assert out == {k: want for k, (_, want) in cases.items()}


def test_f3_track_legs_follow_section_10_5():
    states = ["start", "plan", "readback", "pending", "check did not run", "deadline mismatch", "uncertain",
        "other mismatch", "match", "permission", "request sent", "request failed", "stopped", "expired",
        "accepted", "handoff", "documented"]
    out = judge('''console.log(JSON.stringify(Object.fromEntries(input.map(s => [s, J.trackLegs(s)]))));''', states)
    marks = {s: {leg: v["mark"] for leg, v in legs.items()} for s, legs in out.items()}
    tags = {s: [leg for leg, v in legs.items() if v["tag"]] for s, legs in out.items()}
    none = {"mei": None, "adp": None, "rules": None, "provider": None, "nurse": None}
    assert marks["pending"] == {**none, "adp": "active"}
    for s in ["check did not run", "deadline mismatch", "uncertain", "other mismatch", "match"]:
        assert marks[s] == {**none, "adp": "done", "rules": "active"}, s
    assert marks["request sent"] == {**none, "adp": "done", "rules": "done", "provider": "active"}
    assert marks["request failed"] == {**none, "adp": "done", "rules": "done", "provider": "failed"}
    for s in ["start", "plan", "readback", "permission", "stopped", "expired"]:
        assert marks[s] == none, s
    assert all(tags[s] == ["mei"] for s in states if s != "handoff")
    assert tags["handoff"] == ["nurse"]
    assert out["request failed"]["mei"]["small"] == "Still has to act"


def test_f5_frame_messages_need_own_origin_own_frame_and_exact_shape():
    out = judge('''const frame={}, other={}, own="http://127.0.0.1:8550";
const ok=(e)=>J.acceptFrameMessage(e, own, frame);
const good={type:"carerelay-journey", revision:7};
console.log(JSON.stringify({
 good: ok({origin: own, source: frame, data: good}),
 foreign: ok({origin: "http://evil.example", source: frame, data: good}),
 sibling: ok({origin: own, source: other, data: good}),
 noFrame: J.acceptFrameMessage({origin: own, source: undefined, data: good}, own, undefined),
 extra: ok({origin: own, source: frame, data: {...good, episode_id: "x"}}),
 missing: ok({origin: own, source: frame, data: {type: "carerelay-journey"}}),
 wrongType: ok({origin: own, source: frame, data: {type: "other", revision: 7}}),
 badRevision: ok({origin: own, source: frame, data: {type: "carerelay-journey", revision: "7"}}),
 negative: ok({origin: own, source: frame, data: {type: "carerelay-journey", revision: -1}}),
 string: ok({origin: own, source: frame, data: "carerelay-journey"}),
 array: ok({origin: own, source: frame, data: ["carerelay-journey", 7]}),
}));''')
    assert out == {"good": True, "foreign": False, "sibling": False, "noFrame": False, "extra": False, "missing": False,
        "wrongType": False, "badRevision": False, "negative": False, "string": False, "array": False}


def test_f5_stage_frame_uses_the_guard_and_never_posts():
    source = (ROOT / "frontend/components/judge/StageFrame.tsx").read_text()
    assert "acceptFrameMessage(event, window.location.origin, frame.current?.contentWindow)" in source
    assert "postMessage" not in source
    assert '<iframe ref={frame} src="/"' in source


def test_patient_surface_receives_no_ledger_data():
    """D19: the frame document is the patient page; nothing judge-side flows into it."""
    for path in ["frontend/app/page.tsx", "frontend/components/PatientJourney.tsx", "frontend/lib/journey.ts",
                 "frontend/middleware.ts"]:
        text = (ROOT / path).read_text()
        for needle in ("getLedger", "lib/judge", "components/judge", "/demo", "/ledger"):
            assert needle not in text, f"{path} mentions {needle}"


# ---------------------------------------------------------------------------
# Copy honesty: approved strings, and no implied Tencent ADP call offline
# ---------------------------------------------------------------------------

def test_copy_reads_checked_in_and_different_from_plan(flow_ledger):
    out = judge('''const d=J.decodeLedgerDetail(input);
console.log(JSON.stringify({timing:[J.checkedIn(6011), J.checkedIn(null)], result:J.RESULT_LABEL,
  head:J.stateCopy(J.panelState(d), d).headline, reader:J.readerHeading(d), note:J.offlineNote(d), actor:J.actorName(d)}));''',
        flow_ledger["checked"])
    assert out["timing"] == ["Checked in 6.0 s", None]
    assert out["result"] == {"matched": "Same", "mismatched": "Different from plan", "uncertain": "Unclear"}
    assert out["head"] == "Mei said “today before 8pm”. Her plan says “6pm today”. CareRelay caught it."
    assert out["actor"] == "The local stand-in" and "Tencent ADP" not in out["reader"]
    assert out["note"] == "Offline run: a local stand-in did the reading step. Tencent ADP was not contacted for this check."


def test_live_provenance_names_tencent_adp(flow_ledger):
    live = copy.deepcopy(flow_ledger["checked"])
    live["extractions"][-1].update(transport_provenance="https", elapsed_ms=6011)
    out = judge('''const d=J.decodeLedgerDetail(input);
console.log(JSON.stringify({reader:J.readerHeading(d), note:J.offlineNote(d)}));''', live)
    assert out == {"reader": "Tencent ADP copied three phrases", "note": None}


# ---------------------------------------------------------------------------
# S1: serialized judge surfaces carry no secret, reasoning or raw stream
# ---------------------------------------------------------------------------

NEEDLES = ("appkey", "app_key", "thought", "reasoning", "[done]", "event: done", "text.delta", "conversationid")


def leaks(serialized):
    from test_boundaries import scan_for_secrets
    lowered = serialized.casefold()
    return sorted({n for n in NEEDLES if n in lowered} | set(scan_for_secrets(serialized)))


def render_panel(ledger):
    """Render the real panel components to static HTML from one ledger value."""
    react = (NM / "react/index.js").as_uri()
    return node(TS + f'''import React from {json.dumps(react)};
import {{renderToStaticMarkup}} from {json.dumps((NM / "react-dom/server.node.js").as_uri())};
const fix=s=>s.replaceAll('"react"',{json.dumps(json.dumps(react))}).replaceAll('"react/jsx-runtime"',{json.dumps(json.dumps((NM / "react/jsx-runtime.js").as_uri()))});
const track=url(fix(transpile(readFileSync('frontend/components/judge/RelayTrack.tsx','utf8'))));
const load=p=>import(url(fix(transpile(readFileSync(p,'utf8').replaceAll('"@/lib/judge"',JSON.stringify(judgeUrl)).replaceAll('"./RelayTrack"',JSON.stringify(track))))));
const R=await import(track), RB=await load('frontend/components/judge/ReadbackLanes.tsx'), OL=await load('frontend/components/judge/OutcomeLanes.tsx');
const d=J.decodeLedgerDetail(input); const s=J.panelState(d);
console.log(JSON.stringify(renderToStaticMarkup(React.createElement(React.Fragment,null,
  React.createElement(R.RelayTrack,{{legs:J.trackLegs(s),readerName:"Tencent ADP"}}),
  React.createElement(RB.ReadbackLanes,{{detail:d}}), React.createElement(OL.OutcomeLanes,{{detail:d,state:s}})))));''', ledger)


def test_s1_ledger_and_panel_carry_no_secret_or_model_channel(flow_ledger):
    for name, ledger in flow_ledger.items():
        assert leaks(json.dumps(ledger, ensure_ascii=False)) == [], name
        html = render_panel(ledger)
        assert WRONG_TIME in html or "today before 6pm" in html, "the panel rendered the stored words"
        assert leaks(html) == [], name


@pytest.mark.parametrize("needle", NEEDLES)
def test_s1_each_planted_needle_is_detected_in_the_new_fields(flow_ledger, needle):
    """A scanner that cannot see the new fields proves nothing about them."""
    planted = copy.deepcopy(flow_ledger["checked"])
    planted["restatements"][-1]["readback"]["confirmed_words"] = f"fictional {needle} words"
    assert needle in leaks(json.dumps(planted, ensure_ascii=False))
    assert needle in leaks(render_panel(planted))
    plan = copy.deepcopy(flow_ledger["checked"])
    plan["plan_reference"]["fallback_display"] = f"the {needle} line"
    assert needle in leaks(json.dumps(plan, ensure_ascii=False))
