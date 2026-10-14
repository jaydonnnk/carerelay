"""Slice 14: authenticated no-plan surfaces, identity and coherent SQLite reads."""
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from carerelay.api import app, get_service
from carerelay.demo import fixture
from carerelay.domain import rules
from carerelay.presentation import journey_surface
from carerelay.state import EpisodeNotFound, open_store
from carerelay.tools import McpTools
from carerelay.simulated_provider import ScriptedProvider
from test_truthfulness import make_service

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def world(tmp_path, monkeypatch):
    token = "synthetic-slice14-test-only"
    monkeypatch.setenv("CARERELAY_API_TOKEN", token)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("CARERELAY_FRONTEND_URL", "http://127.0.0.1:8140/")
    service = make_service(tmp_path / "journey.sqlite")
    service.ensure_episode("fictional-no-plan", "fictional tracer")
    app.dependency_overrides[get_service] = lambda: service
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client, service
    app.dependency_overrides.clear()
    service._store.close()


def assert_no_plan(body, episode="fictional-no-plan"):
    assert body["episode_id"] == episode
    assert body["schema_version"] == "carerelay-journey-v1"
    for key in ("plan", "outcome", "revealed_plan", "question", "disposition_version",
                "policy_version", "closure", "execution", "evidence", "action_owner_id"):
        assert body[key] is None, key
    assert body["care_evidenced"] is False
    assert body["lines"] == body["commands"] == []
    assert body["step"] == "start"
    assert body["plan_redacted"] is False
    assert body["flow"] == dict(stopped=False, stop_reason=None, stopped_disposition_version=None,
        readback_attempt_id=None, latest_restatement_id=None, selected_repair_field=None,
        completed_repairs=0, effective_hint="H1", card_visible=False, interpretation="idle")
    assert body["text"] == fixture.JOURNEY_COPY["start"]
    assert body["simulated"] is True
    assert body["fixture_label"] == fixture.JOURNEY_LABEL


@pytest.mark.parametrize("surface", ["api", "options", "mcp", "root"])
def test_no_plan_surfaces(world, surface):
    client, service = world
    before = service._store.list_events("fictional-no-plan")
    if surface == "api":
        response = client.get("/api/episodes/fictional-no-plan")
        assert response.status_code == 200
        assert_no_plan(response.json())
    elif surface == "options":
        body = client.get("/api/episodes/fictional-no-plan/options").json()
        assert body["routes"] == []
        assert body["disposition_version"] is None
        # Positive control: an assessed record still has the permitted options.
        service.intake("fictional-no-plan", fixture.BOUND_COMPLAINT)
        assert client.get("/api/episodes/fictional-no-plan/options").json()["routes"]
        return
    elif surface == "mcp":
        service.change_consent("fictional-no-plan", granted=True)
        tools = McpTools(service._store, policy=fixture.policy(), provider=ScriptedProvider())
        body = asdict(tools.get_episode("fictional-no-plan", now_utc=fixture.SCENARIO_NOW_UTC))
        assert body["policy_version"] is body["disposition_version"] is body["fallback_route_id"] is None
        assert body["permitted_route_ids"] == ()
        service.intake("fictional-no-plan", fixture.BOUND_COMPLAINT)
        assert tools.get_episode("fictional-no-plan", now_utc=fixture.SCENARIO_NOW_UTC).permitted_route_ids
        return
    else:
        response = client.get("/?redirect=https://attacker.invalid&episode_id=anything", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "http://127.0.0.1:8140/"
        assert response.text == ""
    assert service._store.list_events("fictional-no-plan") == before


@pytest.mark.parametrize("suffix", ["", "/options", "/ledger"])
def test_unknown_and_auth_refusal(world, suffix):
    client, _ = world
    assert client.get("/api/episodes/unknown" + suffix).status_code == 404
    with TestClient(app) as unauthenticated:
        assert unauthenticated.get("/api/episodes/fictional-no-plan" + suffix).status_code == 401


def test_assessed_reads_without_a_stop_or_implicit_expiry(world):
    client, service = world
    service.intake("fictional-no-plan", fixture.BOUND_COMPLAINT)
    before = service._store.list_events("fictional-no-plan")
    response = client.get("/api/episodes/fictional-no-plan")
    assert response.status_code == 200
    assert response.json()["step"] == "plan"
    assert response.json()["plan"]["deadline_utc"] == "2026-09-30T10:00:00+00:00"
    assert response.json()["lines"] == list(fixture.demo_lines().as_tuple())
    assert service._store.list_events("fictional-no-plan") == before
    assert service._store.load_snapshot("fictional-no-plan").flow_stop_reason is None
    assert service.project_patient("fictional-no-plan").lines == fixture.demo_lines().as_tuple()


def test_no_event_identity_after_reopen_and_unknown(world):
    client, service = world
    path = service._store.path
    for episode in ("empty-a", "empty-b"):
        service._store._conn.execute("INSERT INTO episodes(id,persona,created_at) VALUES(?,?,?)",
                                    (episode, "fictional", fixture.SCENARIO_NOW_UTC.isoformat()))
    with open_store(path) as reopened:
        for episode in ("empty-a", "empty-b"):
            bundle = reopened.load_journey_bundle(episode)
            projection = rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC)
            assert projection.episode_id == episode
            assert projection.revision == 0
            response = client.get("/api/episodes/" + episode)
            assert response.status_code == 200
            assert_no_plan(response.json(), episode)
        with pytest.raises(EpisodeNotFound):
            reopened.load_journey_bundle("absent")


def test_snapshot_race(world):
    _, service = world
    # Commit intake from another connection after the first SELECT establishes
    # the reader snapshot. The current read stays wholly old; next read sees new.
    writer = make_service(service._store.path)
    reader = service._store
    before = reader.load_journey_bundle("fictional-no-plan")
    fired = False
    def concurrent_write(sql):
        nonlocal fired
        if not fired and "SELECT * FROM dispositions" in sql:
            fired = True
            writer.intake("fictional-no-plan", fixture.BOUND_COMPLAINT)
    reader._conn.set_trace_callback(concurrent_write)
    try:
        bundle = reader.load_journey_bundle("fictional-no-plan")
    finally:
        reader._conn.set_trace_callback(None)
        writer._store.close()
    assert fired
    assert bundle.snapshot.disposition is None
    assert bundle.revision == before.revision
    assert bundle.events == before.events
    assert reader.load_journey_bundle("fictional-no-plan").snapshot.disposition is not None
    assert not reader._conn.in_transaction


def test_fresh_process_reads(world):
    _, service = world
    script = '''
import json
from fastapi.testclient import TestClient
from carerelay.api import app
with TestClient(app, headers={"Authorization":"Bearer synthetic-slice14-test-only"}) as c:
    a=c.get("/api/episodes/fictional-no-plan")
    o=c.get("/api/episodes/fictional-no-plan/options")
    l=c.get("/api/episodes/fictional-no-plan/ledger")
    u=c.get("/api/episodes/absent")
    print(json.dumps({"status":[a.status_code,o.status_code,l.status_code,u.status_code],
                      "patient":a.json(),"options":o.json(),"ledger":l.json()}))
'''
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), APP_DATABASE_URL=service._store.path,
               APP_ENV="local", CARERELAY_API_TOKEN="synthetic-slice14-test-only", APP_CLOCK="scenario",
               CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    body = json.loads(result.stdout)
    assert body["status"] == [200, 200, 200, 404]
    assert_no_plan(body["patient"])
    assert body["options"]["routes"] == []
    assert body["ledger"]["disposition_version"] is None


@pytest.mark.parametrize("target", ["", "//attacker.invalid", "javascript:alert(1)",
    "https://user:password@frontend.invalid", "https://frontend.invalid/?redirect=bad",
    "https://frontend.invalid/#bad", "http://remote.invalid"])
def test_root_rejects_untrusted_configuration(world, monkeypatch, target):
    client, _ = world
    monkeypatch.setenv("CARERELAY_FRONTEND_URL", target)
    assert client.get("/", follow_redirects=False).status_code == 503


def test_database_read_failure_is_unavailable_not_clinical_stop(world):
    import sqlite3
    client, service = world
    conn = service._store._conn
    before = service._store.list_events("fictional-no-plan")
    conn.set_authorizer(lambda op, *_: sqlite3.SQLITE_DENY if op == sqlite3.SQLITE_READ else sqlite3.SQLITE_OK)
    try:
        response = client.get("/api/episodes/fictional-no-plan")
    finally:
        conn.set_authorizer(None)
    assert response.status_code == 503
    assert response.json() == {"detail": "journey unavailable"}
    assert service._store.list_events("fictional-no-plan") == before
    assert not conn.in_transaction


def test_reader_annotations_resolve_for_both_engines():
    from typing import get_type_hints
    from carerelay.state import SqliteEpisodeStore
    from carerelay.postgres_store import PostgresEpisodeStore
    from carerelay.domain.models import JourneyBundle
    for store in (SqliteEpisodeStore, PostgresEpisodeStore):
        assert get_type_hints(store.load_journey_bundle)["return"] is JourneyBundle


def test_bundle_preserves_consent_without_exposing_guidance(world):
    client, service = world
    assert service._store.load_journey_bundle("fictional-no-plan").consent_granted is False
    service.change_consent("fictional-no-plan", granted=True)
    assert service._store.load_journey_bundle("fictional-no-plan").consent_granted is True
    assert_no_plan(client.get("/api/episodes/fictional-no-plan").json())
    service.change_consent("fictional-no-plan", granted=False)
    assert service._store.load_journey_bundle("fictional-no-plan").consent_granted is False


def test_reads_call_no_create_model_or_dispatch(world, monkeypatch):
    client, service = world
    called = []
    def forbidden(*args, **kwargs):
        called.append(True)
        raise AssertionError("read attempted work")
    monkeypatch.setattr(service, "ensure_episode", forbidden)
    monkeypatch.setattr(service, "intake", forbidden)
    monkeypatch.setattr(service._coordinator, "extract_plan", forbidden)
    monkeypatch.setattr(service._coordinator, "execute_tool", forbidden)
    monkeypatch.setattr(McpTools, "submit_simulated_request", forbidden)
    for _ in range(3):
        response = client.get("/api/episodes/fictional-no-plan")
        assert response.status_code == 200
        assert_no_plan(response.json())
    assert called == []


def test_expiry_survives_unavailable_date_and_clock_regression(world):
    from datetime import timedelta
    from carerelay.service import ScenarioClock
    client, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    deadline = service._store.load_snapshot(episode).disposition.clinical_deadline_utc
    service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(days=1))
    response = client.get("/api/episodes/" + episode)
    assert response.status_code == 503
    assert response.json() == {"detail": "journey unavailable"}
    assert len(service._store.list_expiry_events(episode)) == 1
    assert service._store.load_snapshot(episode).flow_stop_reason is None
    service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC)
    recovered = client.get("/api/episodes/" + episode)
    assert recovered.status_code == 200
    assert recovered.json()["step"] == "expired"
    assert recovered.json()["outcome"]["expiry_recorded"] is True
    assert recovered.json()["plan"]["deadline_utc"] == deadline.isoformat()
    assert len(service._store.list_expiry_events(episode)) == 1


MATRIX = {
    "plan": ("plan", None, "open", "patient", False),
    "readback": ("readback", "readback", "open", None, False),
    "repair": ("repair", "repair", "open", None, False),
    "uncertain": ("readback", "readback", "open", None, False),
    "unavailable": ("readback", "readback", "open", None, False),
    "barrier": ("barrier", "barrier", "open", "patient", False),
    "permission": ("permission", "permission", "open", "patient", False),
    "declined": ("permission", "permission", "open", "patient", False),
    "waiting": ("permission", None, "open", "patient", False),
    "acknowledged": ("plan", None, "open", "patient", False),
    "failed": ("unresolved", None, "open", "patient", False),
    "handoff_failed": ("unresolved", None, "open", "patient", False),
    "handoff_attempted": ("plan", None, "open", "patient", False),
    "handoff_unknown": ("plan", None, "open", "patient", False),
    "stopped": ("stopped", None, "open", "patient", True),
    "h3": ("stopped", None, "open", "patient", True),
    "accepted": ("accepted", None, "closed_with_evidence", "caregiver", False),
    "handoff": ("handoff", None, "escalated_to_human", "nurse_line", False),
    "stopped_accepted": ("accepted", None, "closed_with_evidence", "caregiver", True),
    "stopped_handoff": ("handoff", None, "escalated_to_human", "nurse_line", True),
    "expired": ("expired", None, "expired_unresolved", "patient", False),
    "expired_accepted": ("expired", None, "expired_unresolved", "caregiver", False),
    "expired_handoff": ("expired", None, "expired_unresolved", "nurse_line", False),
    "expired_stopped": ("expired", None, "expired_unresolved", "patient", True),
    "documented": ("documented", None, "closed_with_evidence", "patient", False),
    "expired_documented": ("documented", None, "closed_with_evidence", "patient", False),
    "pending": ("plan", None, "open", "patient", False),
}
OUTCOME_LINES = {
    "open": ["No one has agreed to help yet.", "Please act now.", "Please do it before 6pm today.", "If that does not work, call the fictional nurse line."],
    "accepted": ["Someone has agreed to help.", "You do not need to act now.", "It is set for 6pm today.", "If that does not happen, call the fictional nurse line."],
    "handoff": ["We have passed this to the fictional nurse line.", "You do not need to act now.", "It is set for 6pm today.", "If that does not work, call the fictional nurse line."],
    "expired": ["No one has agreed to help yet.", "You can still do this.", "It is past 6pm today. Please go now.", "Call the fictional nurse line. They can help from here."],
    "documented": ["Help is arranged.", "Nothing more is needed from you.", "It is set for 6pm today.", "If that does not happen, call the fictional nurse line."],
}


@pytest.mark.parametrize("case", MATRIX)
def test_twelve_screens_and_contradictions(world, case):
    from _journey_fixtures import seed_journey
    client, service = world
    episode = "matrix-" + case
    seed_journey(service, episode, case)
    response = client.get("/api/episodes/" + episode)
    assert response.status_code == 200, response.text
    body = response.json()
    step, question, closure, owner, stopped = MATRIX[case]
    assert (body["step"], body["question"]["question_id"] if body["question"] else None,
            body["closure"], body["action_owner_id"], body["flow"]["stopped"]) == MATRIX[case]
    assert body["care_evidenced"] == (step == "documented")
    # Slice 16 adds guarded recall/cue commands. Assert each screen's exact
    # capabilities so a wrong progression offer cannot hide behind a blanket [].
    expected_commands = {
        "plan": ["readback_started", "show_plan", "hide_plan"],
        "readback": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "repair": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "uncertain": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "unavailable": ["confirm_words", "show_plan", "hide_plan", "h3"],
    }
    cues_only = {"barrier", "permission", "declined", "waiting", "acknowledged", "failed",
                 "handoff_failed", "handoff_attempted", "handoff_unknown", "stopped", "h3"}
    expected = expected_commands.get(case, ["show_plan", "hide_plan"] if case in cues_only else [])
    assert [o["kind"] for o in body["commands"]] == expected
    assert body["disposition_version"] == 1
    assert body["policy_version"] == "fixture-provisional-0"
    assert body["simulated"] and body["fixture_label"] == fixture.JOURNEY_LABEL
    ledger = client.get(f"/api/episodes/{episode}/ledger").json()
    assert ledger["axes"]["closure"] == closure
    assert ledger["axes"]["care_evidenced"] == body["care_evidenced"]
    assert body["outcome"]["execution"] == body["execution"] == ledger["axes"]["execution"]
    assert body["outcome"]["evidence"] == body["evidence"] == ledger["axes"]["evidence"]
    if question in {"readback", "repair"}:
        assert body["plan_redacted"] and body["plan"] is body["revealed_plan"] is None
        assert body["lines"] == []
        if question == "repair":
            assert body["flow"]["effective_hint"] == "H2"
            assert body["text"]["repair_deadline"] == "before 6pm today"
        else:
            assert "6pm" not in json.dumps(body)
        assert "attend_same_day_review" not in json.dumps(body)
    else:
        assert body["plan"]["deadline_utc"] == "2026-09-30T10:00:00+00:00"
        assert body["lines"] == OUTCOME_LINES.get(step, OUTCOME_LINES["open"])
    if case == "pending": assert body["flow"]["interpretation"] == "pending"
    if case == "waiting": assert body["text"]["status"] == "No reply yet."
    if case in {"uncertain", "unavailable"}: assert body["flow"]["interpretation"] == case
    with open_store(service._store.path) as reopened:
        assert reopened.load_snapshot(episode).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"


def test_recorded_policy_selected(world, monkeypatch):
    from dataclasses import replace
    client, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    before = client.get("/api/episodes/" + episode).json()
    service._policy = replace(service._policy, version="configured-B", permitted_route_ids=frozenset())
    service._policy_text = replace(service._policy_text, policy_version="configured-B", deadline_display_by_version={1: "invented"})
    monkeypatch.setattr(fixture, "policy", lambda: service._policy)
    monkeypatch.setattr(fixture, "policy_text", lambda: service._policy_text)
    assert client.get("/api/episodes/" + episode).json() == before
    assert len(client.get(f"/api/episodes/{episode}/options").json()["routes"]) == 2


@pytest.mark.parametrize("bad", ["empty", "overlap", "unknown", "wrong_outcome"])
def test_corrupt_comparison_refuses_instead_of_understood(world, bad):
    from dataclasses import replace
    from carerelay.domain.models import PlanComparison, RecallOutcome
    _, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service.submit_restatement(episode, "see the doctor today before 6pm myself", "H1")
    bundle = service._store.load_journey_bundle(episode)
    row = bundle.restatements[-1]
    if bad == "empty": row = replace(row, comparison=PlanComparison(frozenset(), frozenset(), frozenset()))
    if bad == "overlap": row = replace(row, comparison=PlanComparison(frozenset({"action_id", "deadline_utc", "next_owner_id"}), frozenset(), frozenset({"action_id"})), outcome=RecallOutcome.NOT_RECALLED)
    if bad == "unknown": row = replace(row, comparison=PlanComparison(frozenset({"action_id", "deadline_utc"}), frozenset(), frozenset({"bogus"})), outcome=RecallOutcome.NOT_RECALLED)
    if bad == "wrong_outcome": row = replace(row, outcome=RecallOutcome.NOT_RECALLED)
    with pytest.raises(rules.JourneyUnavailable):
        rules.derive_journey(replace(bundle, restatements=(row,)), now_utc=fixture.SCENARIO_NOW_UTC)


@pytest.mark.parametrize("field", ["action_id", "deadline_utc", "next_owner_id"])
@pytest.mark.parametrize("bad", ["absent", "empty", "unknown", "uncertain"])
def test_matched_comparison_requires_recorded_grounded_span(world, field, bad):
    from dataclasses import replace
    _, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service.submit_restatement(episode, "see the doctor today before 6pm myself", "H1")
    bundle = service._store.load_journey_bundle(episode)
    assert rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC).step == "barrier"
    row = bundle.restatements[-1]
    span = {"action_id": "action_span", "deadline_utc": "deadline_span", "next_owner_id": "next_owner_span"}[field]
    change = {"uncertain_fields": frozenset({field})} if bad == "uncertain" else {span: {"absent": None, "empty": "", "unknown": "invented"}[bad]}
    row = replace(row, extracted=replace(row.extracted, **change))
    with pytest.raises(rules.JourneyUnavailable, match="ungrounded"):
        rules.derive_journey(replace(bundle, restatements=(row,)), now_utc=fixture.SCENARIO_NOW_UTC)


@pytest.mark.parametrize("field", ["action_id", "deadline_utc", "next_owner_id"])
@pytest.mark.parametrize("bad", ["absent", "unknown", "uncertain"])
def test_mismatched_comparison_requires_recorded_known_difference(world, field, bad):
    from dataclasses import replace
    from _journey_fixtures import seed_journey
    _, service = world
    episode = "mismatch-integrity"
    seed_journey(service, episode, "repair")
    bundle = service._store.load_journey_bundle(episode)
    assert rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC).step == "repair"
    row = bundle.restatements[-1]
    span = {"action_id": "action_span", "deadline_utc": "deadline_span", "next_owner_id": "next_owner_span"}[field]
    changes = {"uncertain_fields": frozenset({field})} if bad == "uncertain" else {span: None if bad == "absent" else "invented"}
    row = replace(row, extracted=replace(row.extracted, **changes), comparison=replace(row.comparison,
        matched=row.comparison.matched - {field}, mismatched=row.comparison.mismatched | {field}))
    with pytest.raises(rules.JourneyUnavailable, match="ungrounded recorded mismatch"):
        rules.derive_journey(replace(bundle, restatements=(row,)), now_utc=fixture.SCENARIO_NOW_UTC)


@pytest.mark.parametrize("case", ["unknown_hint_kind", "malformed_readback", "malformed_hint", "malformed_barrier"])
def test_corrupt_current_journey_event_refuses_http_without_hiding_plan(world, case):
    from _journey_fixtures import seed_journey
    client, service = world
    episode = "corrupt-event-" + case
    seed_journey(service, episode, "readback")
    service.record_hint_event(episode, "H2", "shown")
    assert client.get("/api/episodes/" + episode).json()["flow"]["card_visible"] is True
    kind = {"unknown_hint_kind": "hint_event", "malformed_readback": "readback_started", "malformed_hint": "hint_event", "malformed_barrier": "barrier_recorded"}[case]
    payload = json.dumps({"disposition_version": 1, "hint_level": "H2", "kind": "invented"}) if case == "unknown_hint_kind" else "{bad"
    service._store._conn.execute("INSERT INTO events(episode_id,kind,payload,recorded_at) VALUES(?,?,?,?)", (episode, kind, payload, fixture.SCENARIO_NOW_UTC.isoformat()))
    before = list(service._store._conn.iterdump())
    assert client.get("/api/episodes/" + episode).status_code == 503
    assert list(service._store._conn.iterdump()) == before


@pytest.mark.parametrize("change", ["stop", "consent", "acceptance"])
def test_assessed_snapshot_never_mixes_revisions(world, change):
    from carerelay.presentation import journey_surface
    _, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service.change_consent(episode, granted=True)
    before = service._store.load_journey_bundle(episode)
    writer = make_service(service._store.path)
    fired = False
    def concurrent(sql):
        nonlocal fired
        if not fired and "SELECT * FROM dispositions" in sql:
            fired = True
            if change == "stop": writer._store.record_flow_stop(episode, 1, "reassessment_stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
            if change == "consent": writer.change_consent(episode, granted=False)
            if change == "acceptance": writer.record_human_acceptance(episode, "caregiver", "handoff")
    service._store._conn.set_trace_callback(concurrent)
    try:
        captured = service._store.load_journey_bundle(episode)
    finally:
        service._store._conn.set_trace_callback(None)
        writer._store.close()
    assert fired
    assert captured == before
    after = service._store.load_journey_bundle(episode)
    assert after.revision > captured.revision
    body = journey_surface(rules.derive_journey(captured, now_utc=fixture.SCENARIO_NOW_UTC))
    assert body["step"] == "plan" and not body["flow"]["stopped"]
    if change == "stop": assert after.snapshot.flow_stop_reason == "reassessment_stop"
    if change == "consent": assert after.consent_granted is False
    if change == "acceptance": assert after.snapshot.accepted_by == "caregiver"


@pytest.mark.parametrize("case", ["plan", "stopped", "h3", "accepted", "handoff", "failed", "expired", "documented"])
def test_fresh_interpreter_reads_stored_outcomes(world, case):
    from _journey_fixtures import seed_journey
    _, service = world
    episode = "fresh-" + case
    seed_journey(service, episode, case)
    # Expiry is persisted first; the fresh scenario clock cannot undo it.
    expected = journey_surface(service.project_journey(episode))
    script = '''
import json
from carerelay.api import app
from fastapi.testclient import TestClient
with TestClient(app,headers={'Authorization':'Bearer synthetic-slice14-test-only'}) as c:
 p=c.get('/api/episodes/'+EPISODE)
 o=c.get('/api/episodes/'+EPISODE+'/options')
 l=c.get('/api/episodes/'+EPISODE+'/ledger')
 u=c.get('/api/episodes/absent')
 print(json.dumps({'status':[p.status_code,o.status_code,l.status_code,u.status_code],'patient':p.json(),'ledger':l.json()}))
'''.replace("EPISODE",repr(episode))
    env = dict(os.environ, PYTHONPATH=str(ROOT/"src"), APP_DATABASE_URL=service._store.path,
               APP_ENV="local", APP_CLOCK="scenario", CARERELAY_API_TOKEN="synthetic-slice14-test-only",
               CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled", PYTHONDONTWRITEBYTECODE="1")
    child = subprocess.run([sys.executable,"-c",script],cwd=ROOT,env=env,capture_output=True,text=True)
    assert child.returncode == 0, child.stderr
    result = json.loads(child.stdout)
    assert result["status"] == [200,200,200,404]
    body = result["patient"]
    for key in ["episode_id","step","plan","outcome","flow","lines","revision"]:
        assert body[key] == expected[key], key
    assert result["ledger"]["axes"]["closure"] == body["closure"]


def test_malformed_stored_round_is_recovery_without_mutation(world):
    client, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service._store._conn.execute("INSERT INTO restatements (id,episode_id,disposition_version,hint_level,input_mode,transcript_confirmed,extracted_json,mismatches,repair_round,outcome,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("corrupt-round",episode,1,"H1","text",1,"{}","{}",0,"not_recalled",fixture.SCENARIO_NOW_UTC.isoformat()))
    before = list(service._store._conn.iterdump())
    response = client.get("/api/episodes/" + episode)
    assert response.status_code == 503
    assert response.json() == {"detail": "journey unavailable"}
    assert list(service._store._conn.iterdump()) == before


@pytest.mark.parametrize("event", ["missing", "duplicate", "foreign"])
def test_corrupt_new_record_reference_is_unavailable(world, event):
    client, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    result = service.escalate(episode, "nurse_line", "handed_off")
    payload = {"schema": "record-v1"}
    if event == "duplicate": payload["record_id"] = result.escalation_id
    if event == "foreign": payload["record_id"] = "other-episode-record"
    with service._store.journey_transaction(episode, write=True) as tx:
        tx._event("escalation_recorded", payload, fixture.SCENARIO_NOW_UTC)
    before = list(service._store._conn.iterdump())
    response = client.get("/api/episodes/" + episode)
    assert response.status_code == 503
    assert response.json() == {"detail": "journey unavailable"}
    assert list(service._store._conn.iterdump()) == before


def test_repair_event_records_latest_parent_identity(world):
    _, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    initial = service.submit_restatement(episode, "unsure", "H1")
    repaired = service.repair_restatement(initial.restatement_id, "today before six", "H1")
    events = [json.loads(payload) for kind,payload,_ in service._store.list_events(episode) if kind == "restatement_recorded"]
    assert events[-1]["record_id"] == repaired.restatement_id
    assert events[-1].get("parent_restatement_id") == initial.restatement_id
    assert events[0].get("parent_restatement_id") is None


def test_expiry_survives_corrupt_unrelated_round(world):
    from carerelay.service import ScenarioClock
    from datetime import timedelta
    client, service = world
    episode = "fictional-no-plan"
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service._store._conn.execute("INSERT INTO restatements (id,episode_id,disposition_version,hint_level,input_mode,transcript_confirmed,extracted_json,mismatches,repair_round,outcome,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        ("corrupt-round",episode,1,"H1","text",1,"{}","{}",0,"not_recalled",fixture.SCENARIO_NOW_UTC.isoformat()))
    service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(hours=10))
    assert client.get("/api/episodes/" + episode).status_code == 503
    assert len(service._store.list_expiry_events(episode)) == 1
    service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC)
    assert service._store.load_snapshot(episode).expiry_event_id is not None


def test_naive_stored_deadline_is_unavailable(world):
    client, service = world
    episode = "fictional-no-plan"
    service._store.register_policy_version(fixture.POLICY_VERSION, content="fixture", provenance="fixture", approved_by=None, now_utc=fixture.SCENARIO_NOW_UTC)
    service._store._conn.execute("INSERT INTO dispositions (episode_id,version_no,policy_version,action_id,clinical_deadline_utc,next_owner_id,fallback_route_id,source,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (episode,1,fixture.POLICY_VERSION,fixture.ACTION_ID,"2026-09-30T10:00:00","patient","nurse_line","fixture",fixture.SCENARIO_NOW_UTC.isoformat()))
    before = list(service._store._conn.iterdump())
    response = client.get("/api/episodes/" + episode)
    assert response.status_code == 503
    assert response.json() == {"detail":"journey unavailable"}
    assert list(service._store._conn.iterdump()) == before
