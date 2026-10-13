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


def test_assessed_refuses_without_a_stop_or_implicit_expiry(world):
    client, service = world
    service.intake("fictional-no-plan", fixture.BOUND_COMPLAINT)
    before = service._store.list_events("fictional-no-plan")
    response = client.get("/api/episodes/fictional-no-plan")
    assert response.status_code == 503
    assert response.json() == {"detail": "journey unavailable"}
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
