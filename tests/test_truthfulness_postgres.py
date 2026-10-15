"""Engine-gated truthfulness checks. No SQLite result substitutes for this file."""
from dataclasses import replace
from datetime import timedelta
import uuid

import psycopg
import pytest
from carerelay.demo import fixture
from carerelay.domain.models import AttemptCommand, CallbackResult, ExecutionStatus, Origin
from carerelay.postgres_store import PostgresEpisodeStore, probe_dsn
from carerelay.state import CLINICAL_SCOPE, ConsentNotCurrent, FlowStopped


@pytest.fixture
def seeded():
    dsn = probe_dsn()
    try:
        connection = psycopg.connect(dsn, connect_timeout=2)
        connection.close()
    except psycopg.OperationalError:
        pytest.skip("Postgres unavailable: truthfulness restart/transaction checks NOT RUN")
    store = PostgresEpisodeStore(dsn)
    episode = "truthfulness-" + uuid.uuid4().hex
    policy = "test-only-" + uuid.uuid4().hex
    now = fixture.SCENARIO_NOW_UTC
    store.create_episode(episode, "fictional test", now_utc=now)
    store.register_policy_version(policy, content="{}", provenance="test-only", approved_by=None, now_utc=now)
    disposition = replace(fixture.disposition(episode, now), policy_version=policy)
    store.insert_disposition(disposition, now_utc=now)
    try:
        yield store, episode, disposition
    finally:
        store.close()


def test_failed_escalation_survives_postgres_reconnect(seeded):
    store, episode, _ = seeded
    store.record_escalation(episode, human_path="nurse_line", outcome="failed", now_utc=fixture.SCENARIO_NOW_UTC)
    with_store = PostgresEpisodeStore(probe_dsn())
    try:
        state = with_store.derive_closure(episode, fixture.SCENARIO_NOW_UTC)
        assert state.closure.value == "open"
        assert state.action_owner_id == "patient"
    finally:
        with_store.close()


def test_acceptance_permission_and_actor_survive_postgres_transaction(seeded):
    store, episode, _ = seeded
    now = fixture.SCENARIO_NOW_UTC
    with pytest.raises(ConsentNotCurrent):
        store.record_human_acceptance(episode, accepted_by="caregiver", scope="handoff", now_utc=now)
    store.change_consent(episode, CLINICAL_SCOPE, granted=True, now_utc=now)
    store.record_human_acceptance(episode, accepted_by="caregiver", scope="handoff", now_utc=now)
    assert store.load_snapshot(episode).accepted_by == "caregiver"
    assert store.derive_closure(episode, now).action_owner_id == "caregiver"


def test_postgres_stop_refuses_callback_and_new_version_reopens(seeded):
    store, episode, disposition = seeded
    now = fixture.SCENARIO_NOW_UTC
    store.change_consent(episode, CLINICAL_SCOPE, granted=True, now_utc=now)
    attempt = store.open_attempt_once(AttemptCommand(episode, "fictional_provider", "test", 1), uuid.uuid4().hex, now_utc=now)
    assert attempt.disposition_version == 1
    store.record_flow_stop(episode, 1, "reassessment_stop", "nurse_line", now_utc=now)
    with pytest.raises(FlowStopped):
        store.require_active_flow(episode)
    result = store.record_callback_once(attempt.attempt_id, uuid.uuid4().hex, CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED), Origin.LOCAL_SIM, now_utc=now)
    assert result.disposition.value == "refused"
    store.insert_disposition(replace(disposition, version=2, clinical_deadline_utc=disposition.clinical_deadline_utc + timedelta(days=1)), now_utc=now)
    store.require_active_flow(episode)
    assert store.get_attempt_by_key(attempt.idempotency_key).disposition_version == 1


# Reuse the literal behavioral assertions over a real engine, including reconnects.
# The test factory supplies Postgres constructor arguments; no SQLite cursor is used.
import test_truthfulness as legacy
import subprocess
from test_postgres_store import store as pg_clean_store, requires_postgres
from fastapi.testclient import TestClient
from carerelay.api import app, get_service
from _legacy_service_probes import signed_create, signed_intake


@pytest.fixture
def api(pg_clean_store, monkeypatch):
    from test_journey_postgres import make_service
    token = "synthetic-s19-truthfulness-only"
    monkeypatch.setenv("CARERELAY_API_TOKEN", token)
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setattr(legacy, "make_service", make_service)
    # The original fresh-interpreter assertion needs the engine-aware factory too.
    run = subprocess.run
    def engine_child(args, *a, **kw):
        if isinstance(args, list) and len(args)>2 and args[1]=="-c" and "from test_truthfulness import connected" in args[2]:
            args = list(args)
            args[2] = "import test_truthfulness\nfrom test_journey_postgres import make_service\ntest_truthfulness.make_service=make_service\n" + args[2]
        return run(args, *a, **kw)
    monkeypatch.setattr(subprocess, "run", engine_child)
    service = make_service(pg_clean_store.dsn)
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app, headers={"Authorization":"Bearer " + token}) as client:
            assert TestClient(app).get(legacy.BASE).status_code == 401
            assert signed_create(client).status_code == signed_intake(client).status_code == 200
            yield client, service, pg_clean_store.dsn, token
    finally:
        app.dependency_overrides.clear(); service._store.close()


@requires_postgres
class TestFailedHandoff(legacy.TestFailedHandoff):
    pass


@requires_postgres
class TestEvidenceTrust(legacy.TestEvidenceTrust):
    pass


@requires_postgres
class TestAcceptanceAuthority(legacy.TestAcceptanceAuthority):
    pass


@requires_postgres
class TestReadBackPolarity(legacy.TestReadBackPolarity):
    pass


@requires_postgres
class TestDurableStops(legacy.TestDurableStops):
    pass


@requires_postgres
class TestStopAlternatesAndRecovery(legacy.TestStopAlternatesAndRecovery):
    pass


@requires_postgres
class TestStopRecordGuards(legacy.TestStopRecordGuards):
    @pytest.mark.parametrize("hint,round_no", [("H3",0),("H0",2)])
    def test_legacy_stop_rows_are_still_binding(self, api, hint, round_no):
        from carerelay.domain.models import HintLevel, InputMode, ExtractedPlan, PlanComparison, RecallOutcome
        _, service, _, _ = api
        original = service._store._append_event
        def legacy_event(cur, episode, kind, payload, now):
            if kind != "flow_stopped": original(cur, episode, kind, payload, now)
        service._store._append_event = legacy_event
        service._store.record_restatement(legacy.EPISODE, disposition_version=1, hint_level=HintLevel(hint),
            input_mode=InputMode.TEXT, transcript_confirmed=True, extracted=ExtractedPlan(None,None,None),
            comparison=PlanComparison(frozenset(),frozenset(),frozenset({"action_id","deadline_utc","next_owner_id"})),
            repair_round=round_no, outcome=RecallOutcome.NOT_RECALLED, dwell_seconds=None, now_utc=fixture.SCENARIO_NOW_UTC)
        service._store._append_event = original
        assert service._store.load_snapshot(legacy.EPISODE).flow_stop_reason == "planback_stop"
        assert legacy.readback(api[0], legacy.GOOD).status_code == 409

    def test_h3_stop_event_is_atomic_with_its_restatement(self, api):
        client, service, _, _ = api
        original = service._store._append_event
        def broken_audit(cur, episode, kind, payload, now):
            if kind == "flow_stopped": raise RuntimeError("injected stop audit failure")
            return original(cur,episode,kind,payload,now)
        service._store._append_event = broken_audit
        try:
            with pytest.raises(RuntimeError,match="injected stop audit failure"):
                legacy.readback(client,legacy.GOOD,hint="H3")
        finally: service._store._append_event = original
        assert service._store.list_restatements(legacy.EPISODE) == ()
        assert service._store.load_snapshot(legacy.EPISODE).flow_stop_reason is None
