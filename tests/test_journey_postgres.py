"""Slice 19 real-engine controls, with explicitly labelled offline query parity."""
from contextlib import contextmanager
from datetime import timedelta
from types import SimpleNamespace

import pytest

from carerelay.demo import fixture
from carerelay.postgres_store import PostgresEpisodeStore
from test_truthfulness import make_service as make_sqlite_service


def make_service(path, *, store=None):
    """Use engine-specific constructor arguments without weakening open_store."""
    from carerelay.state import is_postgres_target
    if not is_postgres_target(path):
        return make_sqlite_service(path)
    from carerelay.coordinator import LocalSimulationCoordinator
    from carerelay.service import EpisodeService, ScenarioClock
    from carerelay.simulated_provider import ScriptedProvider
    from carerelay.tools import McpTools
    from _legacy_service_probes import KEY
    store = store if store is not None else PostgresEpisodeStore(path)
    clock = ScenarioClock(fixture.SCENARIO_NOW_UTC)
    tools = McpTools(store, policy=fixture.policy(), provider=ScriptedProvider(), now=clock.now_utc)
    return EpisodeService(store, coordinator=LocalSimulationCoordinator(tools), clock=clock,
        policy=fixture.policy(), policy_text=fixture.policy_text(), display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition, bound_complaint=fixture.BOUND_COMPLAINT,
        operation_signing_key=lambda: KEY, policy_provenance="test: non-clinical fixture")


class SQLiteCursor:
    """Execute the portable Postgres SELECTs over the same seeded SQLite rows."""
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, args=()):
        self.cursor = self.connection.execute(query.replace("%s", "?"), args)
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]


@pytest.fixture
def pg_readback(request):
    """Only the explicitly supplied disposable DSN may run these engine cases."""
    import psycopg
    from carerelay.postgres_store import probe_dsn
    dsn = probe_dsn()
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            pass
    except psycopg.OperationalError:
        pytest.skip("Postgres unavailable: read-back engine cases unproven until authorised Slice 19")
    # Isolate immutable policy registrations and histories from earlier engine runs.
    request.getfixturevalue("pg_clean_store")
    service = make_service(dsn)
    try:
        yield service, dsn
    finally:
        service._store.close()


def test_postgres_confirmed_repair_and_replay(pg_readback):
    import uuid
    from test_field_repair import start_readback, confirm, score
    service, dsn = pg_readback
    ep = start_readback(service, "fictional-pg16-" + uuid.uuid4().hex)
    confirm(service, ep, "go to the clinic tomorrow before 6pm myself")
    score(service, ep)
    confirm(service, ep, "today before six")
    binding, applied = score(service, ep)
    assert applied.journey.step == "barrier" and applied.journey.flow.completed_repairs == 1
    other = make_service(dsn)
    try:
        replay = other.score_confirmed(binding)
        assert replay.receipt.replayed and replay.receipt.scored
        assert len(other._store.list_restatements(ep)) == 2
        assert other._store.list_restatements(ep)[-1].provenance["mode"] == "local-sim"
    finally:
        other._store.close()


def test_postgres_fake_adp_readback_and_unavailable_contract(pg_readback):
    """Engine proof stays skipped without the separately authorised disposable DSN."""
    import uuid
    from test_adp_extraction import adapter, ScenarioTransport
    from test_field_repair import start_readback, confirm, score
    service, dsn = pg_readback
    for failure in [None, "invalid"]:
        service._readback_extractor = adapter(ScenarioTransport(failure=failure))
        ep = start_readback(service, "fictional-pg18-" + uuid.uuid4().hex)
        confirm(service, ep, "go to the clinic today before six myself")
        binding, result = score(service, ep)
        assert result.receipt.scored is (failure is None)
        assert result.receipt.state == ("applied" if failure is None else "unavailable")
        assert service.project_ledger(ep).as_dict()["extractions"][-1]["transport_provenance"] == "fake-offline"
        assert service._store.list_attempts(ep) == ()
        other = make_service(dsn)
        try:
            replay = other.score_confirmed(binding)
            assert replay.receipt.replayed and replay.receipt.scored is (failure is None)
        finally:
            other._store.close()


def test_postgres_nested_fake_adp_scoring_refuses_before_transport(pg_readback):
    import uuid
    from carerelay.state import StateError
    from test_adp_extraction import adapter, ScenarioTransport
    from test_field_repair import start_readback, confirm, score, KEY, verify_operation
    service, _ = pg_readback
    transport = ScenarioTransport(); service._readback_extractor = adapter(transport)
    ep = start_readback(service, "fictional-pg18-nested-" + uuid.uuid4().hex)
    confirm(service, ep, "go to the clinic today before six myself")
    token = next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words")
    with service._store.journey_transaction(ep, write=True):
        with pytest.raises(StateError): service.score_confirmed(verify_operation(token, signing_key=KEY))
    assert transport.calls == [] and service._store.list_restatements(ep) == ()
    assert score(service, ep)[1].receipt.scored and len(transport.calls) == 1


def test_postgres_permission_request_has_one_atomic_receipt(pg_readback):
    import uuid
    from test_journey import s17_ready
    service, dsn = pg_readback
    ep, binding = s17_ready(service, "fictional-pg17-" + uuid.uuid4().hex)
    result = service.request_appointment(binding)
    assert result.receipt.state == "applied" and not result.receipt.replayed
    assert result.journey.text["status"] == "No reply yet."
    other = make_service(dsn)
    try:
        replay = other.request_appointment(binding)
        assert replay.receipt.replayed and replay.receipt.state == "applied"
        assert len(other._store.list_attempts(ep)) == 1
        events = [kind for kind, _, _ in other._store.list_events(ep)]
        assert events.count("dispatch_started") == events.count("dispatch_observed") == 1
    finally:
        other._store.close()


@pytest.mark.parametrize("stage", ["claim", "dispatch"])
def test_postgres_nested_action_requires_its_own_commit(pg_readback, stage):
    import uuid
    from carerelay.state import StateError
    from test_journey import s17_ready
    service, _ = pg_readback
    ep, binding = s17_ready(service, "fictional-pg17-" + uuid.uuid4().hex)
    if stage == "claim":
        with service._store.journey_transaction(ep, write=True):
            with pytest.raises(StateError):
                service.request_appointment(binding)
        assert not service._store.list_attempts(ep)
    else:
        coordinator = service._coordinator
        execute = coordinator.execute_tool
        def nested(request, *, now_utc):
            with service._store.journey_transaction(ep, write=True):
                return execute(request, now_utc=now_utc)
        coordinator.execute_tool = nested
        with pytest.raises(StateError):
            service.request_appointment(binding)
        assert service.request_appointment(binding).receipt.state == "pending"
        assert not any(k == "dispatch_started" for k, _, _ in service._store.list_events(ep))


@pytest.mark.parametrize("change", ["cue", "stop", "expiry", "revision"])
def test_postgres_two_connections_fence_late_readback(pg_readback, change):
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from carerelay.journey_commands import verify_operation
    from carerelay.service import ScenarioClock
    from test_field_repair import start_readback, confirm, PausedExtractor, event, KEY
    service, dsn = pg_readback
    ep = start_readback(service, "fictional-pg16-" + uuid.uuid4().hex)
    confirm(service, ep, "go to the clinic today before six myself")
    offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
    binding = verify_operation(offer.operation_token, signing_key=KEY)
    paused = PausedExtractor()
    service._readback_extractor = paused
    other = make_service(dsn)
    try:
        with ThreadPoolExecutor(1) as worker:
            result = worker.submit(service.score_confirmed, binding)
            assert paused.entered.wait(2)
            try:
                duplicate = other.score_confirmed(binding)
                assert duplicate.receipt.state == "pending" and not duplicate.receipt.scored
                if change == "cue": event(other, ep, "show_plan")
                elif change == "stop": other._store.record_flow_stop(ep, 1, "fixture-stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
                elif change == "expiry": service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(hours=10))
                else:
                    with other._store.journey_transaction(ep, write=True) as tx:
                        tx._event("fixture-audit", {}, fixture.SCENARIO_NOW_UTC)
            finally:
                paused.release.set()
            assert result.result(2).receipt.state == "refused"
        assert other._store.list_restatements(ep) == ()
        assert other._store.load_snapshot(ep).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
    finally:
        paused.release.set()
        other._store.close()


@pytest.mark.parametrize("regression", [False, True])
@pytest.mark.parametrize("record", ["escalation", "acceptance", "restatement", "attempt"])
def test_event_order_survives_equal_or_regressed_clock(tmp_path, monkeypatch, regression, record):
    import carerelay.state as state
    from carerelay.domain.models import HintLevel
    service = make_service(tmp_path / "order.sqlite")
    episode = "event-order"
    service.ensure_episode(episode, "fictional")
    service.intake(episode, fixture.BOUND_COMPLAINT)
    service.change_consent(episode, granted=True)
    ids = iter(["z" * 32, "a" * 32])
    monkeypatch.setattr(state.uuid, "uuid4", lambda: SimpleNamespace(hex=next(ids)))
    first = fixture.SCENARIO_NOW_UTC
    second = first - timedelta(seconds=1) if regression else first
    store = service._store
    if record == "escalation":
        for outcome, now in [("handed_off", first), ("failed", second)]:
            store.record_escalation(episode, human_path="nurse_line", outcome=outcome, now_utc=now)
    elif record == "acceptance":
        for owner, now in [("caregiver", first), ("patient", second)]:
            store.record_human_acceptance(episode, accepted_by=owner, scope="handoff", now_utc=now)
    elif record == "attempt":
        from carerelay.domain.models import AttemptCommand
        for purpose, now in [("one", first), ("two", second)]:
            store.open_attempt_once(AttemptCommand(episode, "fictional_provider", purpose, 1), purpose, now_utc=now)
    else:
        from carerelay.service import ScenarioClock
        service._clock = ScenarioClock(first)
        service.submit_restatement(episode, "see the doctor today before 6pm myself", HintLevel.H1)
        service._clock = ScenarioClock(second)
        service.submit_restatement(episode, "see the doctor tomorrow before 6pm myself", HintLevel.H1)
    pg = PostgresEpisodeStore.__new__(PostgresEpisodeStore)
    @contextmanager
    def read():
        yield SQLiteCursor(store._conn)
    pg._read = read
    if record == "restatement":
        expected = store.list_restatements(episode)
        actual = pg.list_restatements(episode)
        assert [r.restatement_id for r in actual] == [r.restatement_id for r in expected] == ["z" * 32, "a" * 32]
    else:
        expected = store.load_snapshot(episode)
        actual = pg._load_snapshot(SQLiteCursor(store._conn), episode)
        field = {"escalation": "escalation_id", "acceptance": "human_acceptance_id", "attempt": "attempt"}[record]
        a, b = getattr(expected, field), getattr(actual, field)
        if record == "attempt": a, b = a.attempt_id, b.attempt_id
        assert a == b == "a" * 32
    store.close()


def test_postgres_mutex_exists_before_first_transaction(monkeypatch):
    import carerelay.postgres_store as module
    monkeypatch.setattr(module.psycopg, "connect", lambda *a, **k: object())
    monkeypatch.setattr(PostgresEpisodeStore, "init_schema", lambda self: None)
    store = PostgresEpisodeStore("postgresql://offline.invalid/test")
    assert hasattr(store, "_mutex")
    original = store._mutex
    assert original.acquire(blocking=False)
    original.release()
    assert store._mutex is original


def test_postgres_nested_writer_cannot_switch_episode():
    import threading
    from carerelay.state import StateError
    store = PostgresEpisodeStore.__new__(PostgresEpisodeStore)
    store._mutex = threading.RLock()
    store._journey_tx = SimpleNamespace(episode_id="episode-a")
    store._journey_write = True
    store._journey_cursor = object()
    with pytest.raises(StateError, match="episode"):
        with store._write("episode-b"):
            pass


# These tests require actual Postgres. The SQLiteCursor cases above remain offline.
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
import psycopg
from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import request_digest, verify_operation
from _legacy_service_probes import KEY

ROOT = Path(__file__).resolve().parents[1]
NOW = fixture.SCENARIO_NOW_UTC


def fresh_episode():
    return "fictional-s19-" + uuid.uuid4().hex


def child_env(dsn):
    return dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT / "tests"),
        APP_DATABASE_URL=":memory:", APP_ENV="local", APP_CLOCK="scenario",
        CARERELAY_API_TOKEN="", CARERELAY_TEST_DSN=dsn, ADP_EXTRACTION_ENABLED="false",
        PYTHONDONTWRITEBYTECODE="1")


def wait_for_pg_lock(observer, pid, blocker):
    """Wait for the engine's lock graph, never assume a sleep established order."""
    limit = time.monotonic() + 4
    while time.monotonic() < limit:
        row = observer.execute("SELECT wait_event_type, pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s", (pid,)).fetchone()
        if row and row[0] == "Lock" and blocker in row[1]:
            print(json.dumps({"waiter": pid, "blocker": blocker, "wait_event_type": row[0]}))
            return
    assert False, "writer never entered the expected episode lock wait"


@pytest.mark.parametrize("change", ["stop", "consent", "acceptance"])
def test_s19_snapshot_race(pg_readback, monkeypatch, change):
    reader, dsn = pg_readback
    writer = make_service(dsn)
    ep = fresh_episode()
    reader.ensure_episode(ep, "fictional")
    reader.intake(ep, fixture.BOUND_COMPLAINT)
    reader.change_consent(ep, True)
    before = reader._store.load_journey_bundle(ep)
    original = reader._store._load_snapshot
    def pause_between_selects(cur, episode):
        snapshot = original(cur, episode)
        assert cur.execute("SHOW transaction_isolation").fetchone()["transaction_isolation"] == "repeatable read"
        assert cur.execute("SHOW transaction_read_only").fetchone()["transaction_read_only"] == "on"
        if change == "stop": writer._store.record_flow_stop(ep, 1, "reassessment_stop", "nurse_line", now_utc=NOW)
        elif change == "consent": writer.change_consent(ep, False)
        else: writer.record_human_acceptance(ep, "caregiver", "handoff")
        return snapshot
    try:
        print(json.dumps({"reader": reader._store._conn.info.backend_pid, "writer": writer._store._conn.info.backend_pid, "change": change}))
        assert reader._store._conn.info.backend_pid != writer._store._conn.info.backend_pid
        with monkeypatch.context() as patch:
            patch.setattr(reader._store, "_load_snapshot", pause_between_selects)
            captured = reader._store.load_journey_bundle(ep)
        assert captured == before
        after = reader._store.load_journey_bundle(ep)
        assert after.revision > captured.revision
        assert reader._store._conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
        if change == "stop": assert after.snapshot.flow_stop_reason == "reassessment_stop"
        elif change == "consent": assert not after.consent_granted
        else: assert after.snapshot.accepted_by == "caregiver"
    finally:
        writer._store.close()


def test_s19_waited_patient_writer_rereads_committed_stop(pg_readback):
    reader, dsn = pg_readback
    writer = make_service(dsn)
    ep = fresh_episode(); reader.ensure_episode(ep, "fictional"); reader.intake(ep, fixture.BOUND_COMPLAINT)
    try:
        with psycopg.connect(dsn, autocommit=True) as observer, ThreadPoolExecutor(1) as pool:
            with writer._store.journey_transaction(ep, write=True):
                future = pool.submit(reader.project_journey, ep)
                wait_for_pg_lock(observer, reader._store._conn.info.backend_pid, writer._store._conn.info.backend_pid)
                writer._store.record_flow_stop(ep, 1, "reassessment_stop", "nurse_line", now_utc=NOW)
            result = future.result(4)
        assert result.step == "stopped" and result.flow.stopped
        assert not any(o.kind in {"score_words", "request"} for o in result.commands)
    finally:
        writer._store.close()


def test_s19_same_create_and_intake_race_and_lost_response(pg_readback):
    a, dsn = pg_readback; b = make_service(dsn)
    ep = fresh_episode()
    create = OperationBinding("create-" + ep, ep, None, 0, "create", "episode:create", request_digest("create", {}), None, None)
    gate = threading.Barrier(2)
    def together(service, binding, intake):
        gate.wait(4)
        return service.select_example(binding, example_id="scripted-appointment") if intake else service.start_example(binding)
    try:
        with ThreadPoolExecutor(2) as pool:
            responses = [f.result(6) for f in [pool.submit(together, s, create, False) for s in (a,b)]]
            assert sorted(r.receipt.replayed for r in responses) == [False, True]
            token = next(o.operation_token for o in a.project_journey(ep).commands if o.kind == "select_example")
            intake = verify_operation(token, signing_key=KEY)
            responses = [f.result(6) for f in [pool.submit(together, s, intake, True) for s in (a,b)]]
            assert sorted(r.receipt.replayed for r in responses) == [False, True]
        assert len(a._store.list_dispositions(ep)) == 1
        assert b.start_example(create).receipt.replayed and b.select_example(intake, example_id="scripted-appointment").receipt.replayed
        bundle = b._store.load_journey_bundle(ep)
        assert len(bundle.commands) == 4
        from carerelay.journey_commands import CommandConflict
        with pytest.raises(CommandConflict): b.start_example(replace(create, body_sha256="f" * 64))
        assert b._store.load_journey_bundle(ep) == bundle
    finally:
        b._store.close()


@pytest.mark.parametrize("change", ["stop", "revoke", "deadline", "sticky_expiry"])
def test_s19_commit_before_invocation_gives_zero_calls(pg_readback, change):
    from test_journey import s17_ready
    from carerelay.state import CLINICAL_SCOPE
    service, dsn = pg_readback; writer = make_service(dsn)
    ep, binding = s17_ready(service, fresh_episode())
    original = service._coordinator.execute_tool
    provider = service._coordinator._tools._provider
    submit = provider.submit_request; calls = []
    provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
    def committed_then_execute(request, *, now_utc):
        if change == "stop": writer._store.record_flow_stop(ep, 1, "reassessment_stop", "nurse_line", now_utc=NOW)
        elif change == "revoke": writer._store.change_consent(ep, CLINICAL_SCOPE, granted=False, now_utc=NOW)
        elif change == "sticky_expiry": writer._store.record_expiry_once(ep, 1, NOW + timedelta(hours=10))
        else: service._clock._instant = NOW + timedelta(hours=10)
        return original(request, now_utc=now_utc)
    service._coordinator.execute_tool = committed_then_execute
    try:
        result = service.request_appointment(binding)
        assert result.receipt.state == "refused" and not calls
        assert len(writer._store.list_attempts(ep)) == 1
        assert writer._store.load_snapshot(ep).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
        assert not any(k == "dispatch_started" for k, _, _ in writer._store.list_events(ep))
    finally:
        writer._store.close()


@pytest.mark.parametrize("change", ["stop", "revoke"])
def test_s19_invocation_before_waiting_writer_and_late_callback(pg_readback, change):
    from test_journey import s17_ready
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    service, dsn = pg_readback; writer = make_service(dsn)
    ep, binding = s17_ready(service, fresh_episode())
    entered, release = threading.Event(), threading.Event(); calls = []
    provider = service._coordinator._tools._provider; original = provider.submit_request
    def paused(*args):
        calls.append(args); entered.set(); assert release.wait(4)
        return original(*args)
    provider.submit_request = paused
    def write():
        if change == "stop": writer._store.record_flow_stop(ep, 1, "reassessment_stop", "nurse_line", now_utc=NOW)
        else: writer.change_consent(ep, False)
    try:
        with psycopg.connect(dsn, autocommit=True) as observer, ThreadPoolExecutor(2) as pool:
            dispatch = pool.submit(service.request_appointment, binding)
            assert entered.wait(4)
            waiting = pool.submit(write)
            try:
                wait_for_pg_lock(observer, writer._store._conn.info.backend_pid, service._store._conn.info.backend_pid)
                assert not waiting.done()
            finally: release.set()
            assert dispatch.result(4).receipt.state == "applied"
            waiting.result(4)
        assert len(calls) == 1
        callback = writer.receive_callback(ep, "fictional_provider", uuid.uuid4().hex,
            CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED), Origin.LOCAL_SIM)
        assert not callback.applied
        assert service.request_appointment(binding).receipt.replayed and len(calls) == 1
        kinds = [k for k, _, _ in writer._store.list_events(ep)]
        assert kinds.count("dispatch_started") == kinds.count("dispatch_observed") == 1
        events = writer._store.list_events(ep)
        target = next(i for i, (kind, payload, _) in enumerate(events)
            if kind == "flow_stopped" or (kind == "consent_changed" and " revoked " in payload))
        assert kinds.index("dispatch_observed") < target
    finally:
        release.set(); writer._store.close()


@pytest.mark.parametrize("cut", ["claim", "invoke", "effect", "receipt"])
def test_s19_action_crash_never_redispatches(pg_readback, tmp_path, cut):
    from test_journey import s17_ready
    from carerelay.journey_commands import CommandConflict, CommandInvalid
    from carerelay.tools import UnknownAttemptKey
    service, dsn = pg_readback
    ep, binding = s17_ready(service, fresh_episode()); marker = tmp_path / "effect"
    script = f"""
import os,signal
from pathlib import Path
from test_journey_postgres import make_service
from carerelay.domain.models import OperationBinding
from carerelay.state import JourneyTransaction
s=make_service({dsn!r})
def die(*a,**k):
 if {cut!r}=='effect': Path({str(marker)!r}).write_text('one local simulated effect')
 os.kill(os.getpid(),signal.SIGKILL)
if {cut!r}=='claim': s._coordinator.execute_tool=die
elif {cut!r} in ('invoke', 'effect'): s._coordinator._tools._provider.submit_request=die
else:
 provider=s._coordinator._tools._provider; submit=provider.submit_request
 def effect(*a):
  Path({str(marker)!r}).write_text('one local simulated effect')
  return submit(*a)
 provider.submit_request=effect; JourneyTransaction.complete_once=die
s.request_appointment(OperationBinding(**{asdict(binding)!r}))
"""
    child = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=child_env(dsn), capture_output=True, text=True, timeout=10)
    assert child.returncode == -9, child.stderr
    restarted = make_service(dsn)
    try:
        replay = restarted.request_appointment(binding)
        assert replay.receipt.state == "pending" and replay.receipt.replayed
        assert replay.journey.step == "permission" and replay.journey.text["status"] == "No reply yet."
        assert len(restarted._store.list_attempts(ep)) == 1
        assert not any(k in {"dispatch_started", "dispatch_observed"} for k, _, _ in restarted._store.list_events(ep))
        with pytest.raises(CommandConflict): restarted.request_appointment(replace(binding, operation_id=uuid.uuid4().hex, expected_revision=replay.journey.revision))
        with pytest.raises(CommandInvalid): restarted.open_action(ep, "fictional_provider", "caller-retry")
        with pytest.raises(UnknownAttemptKey): restarted._coordinator._tools.submit_simulated_request(ep, "fictional_provider", restarted._store.list_attempts(ep)[0].idempotency_key, now_utc=NOW)
        assert marker.exists() is (cut in {"effect", "receipt"})
    finally:
        restarted._store.close()


@pytest.mark.parametrize("stage", ["create", "intake", "score"])
def test_s19_sigkill_before_terminal_rolls_back_atomic_state(pg_readback, stage):
    from test_field_repair import start_readback, confirm
    service, dsn = pg_readback; ep = fresh_episode()
    binding = OperationBinding("create-" + ep, ep, None, 0, "create", "episode:create", request_digest("create", {}), None, None)
    if stage == "intake":
        service.start_example(binding)
        binding = verify_operation(service.project_journey(ep).commands[0].operation_token, signing_key=KEY)
    elif stage == "score":
        start_readback(service, ep); confirm(service, ep, "go to the clinic today before six myself")
        binding = verify_operation(next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words"), signing_key=KEY)
    script = f"""
import os,signal
from test_journey_postgres import make_service
from carerelay.domain.models import OperationBinding
from carerelay.state import JourneyTransaction
s=make_service({dsn!r})
def die(*a,**k): os.kill(os.getpid(),signal.SIGKILL)
JourneyTransaction.complete_once=die
b=OperationBinding(**{asdict(binding)!r})
if {stage!r}=='create': s.start_example(b)
elif {stage!r}=='intake': s.select_example(b,example_id='scripted-appointment')
else: s.score_confirmed(b)
"""
    child = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=child_env(dsn), capture_output=True, text=True, timeout=10)
    assert child.returncode == -9, child.stderr
    with psycopg.connect(dsn, autocommit=True) as conn:
        if stage == "create":
            assert conn.execute("SELECT count(*) FROM episodes WHERE id=%s", (ep,)).fetchone()[0] == 0
            assert service.start_example(binding).receipt.state == "applied"
        elif stage == "intake":
            assert service._store.list_dispositions(ep) == ()
            assert service.select_example(binding, example_id="scripted-appointment").receipt.state == "applied"
        else:
            assert service._store.list_restatements(ep) == ()
            assert service.score_confirmed(binding).receipt.state == "pending"
            assert conn.execute("SELECT phase FROM journey_commands WHERE operation_id=%s", (binding.operation_id,)).fetchall() == [("claimed",)]


@pytest.mark.parametrize("change", ["version", "confirmation", "parent"])
def test_s19_other_final_dimensions_change_while_extraction_waits(pg_readback, change):
    from test_field_repair import start_readback, confirm, PausedExtractor
    from carerelay.domain.models import HintLevel
    service, dsn = pg_readback; writer = make_service(dsn)
    ep = start_readback(service, fresh_episode())
    confirm(service, ep, "go to the clinic today before six myself")
    binding = verify_operation(next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words"), signing_key=KEY)
    paused = PausedExtractor(); service._readback_extractor = paused
    try:
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(service.score_confirmed, binding)
            assert paused.entered.wait(4)
            try:
                assert service._store._conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
                assert service._store._mutex.acquire(blocking=False)
                service._store._mutex.release()
                if change == "version":
                    old = writer._store.load_snapshot(ep).disposition
                    writer._store.insert_disposition(replace(old, version=2, clinical_deadline_utc=old.clinical_deadline_utc+timedelta(days=1)), now_utc=NOW)
                elif change == "parent":
                    # Trusted concurrent history writer, not a public bypass.
                    writer.submit_restatement(ep, "unsure", HintLevel.H1)
                else:
                    bundle = writer._store.load_journey_bundle(ep)
                    confirmed = next(json.loads(p) for k,p,_ in reversed(bundle.events) if k == "words_confirmed")
                    confirmed["confirmation_id"] = "replacement-" + ep
                    with writer._store.journey_transaction(ep, write=True) as tx:
                        tx._event("words_confirmed", confirmed, NOW)
                before = writer._store.list_restatements(ep)
            finally: paused.release.set()
            from carerelay.domain.rules import JourneyUnavailable
            if change == "version":
                # Version 2 has no approved journey display; its fresh read refuses.
                with pytest.raises(JourneyUnavailable, match="approved plan display unavailable"):
                    future.result(4)
                with writer._store.journey_transaction(ep, write=False) as tx:
                    receipt = tx.find(binding)
                assert receipt.state == "refused" and not receipt.scored
            else:
                result = future.result(4)
                assert result.receipt.state == "refused" and not result.receipt.scored
        assert writer._store.list_restatements(ep) == before
        assert len(paused.inputs) == 1
        assert writer._store.list_dispositions(ep)[0].clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
    finally:
        paused.release.set(); writer._store.close()


def test_s19_same_worker_mutex_is_free_and_supersede_fences_late_output(pg_readback, monkeypatch):
    from test_field_repair import start_readback, confirm, PausedExtractor
    from carerelay.domain import rules
    service, dsn = pg_readback; writer = make_service(dsn)
    ep = start_readback(service, fresh_episode()); confirm(service, ep, "go to the clinic today before six myself")
    binding = verify_operation(next(o.operation_token for o in service.project_journey(ep).commands if o.kind == "score_words"), signing_key=KEY)
    paused = PausedExtractor(); service._readback_extractor = paused
    try:
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(service.score_confirmed, binding); assert paused.entered.wait(4)
            try:
                assert service._store._conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
                assert service._store._mutex.acquire(blocking=False)
                service._store._mutex.release()
                same_worker = service.score_confirmed(binding)
                other_worker = writer.score_confirmed(binding)
                assert same_worker.receipt.state == other_worker.receipt.state == "pending"
                assert len(paused.inputs) == 1
                token = next(o.operation_token for o in other_worker.journey.commands if o.kind == "supersede_extraction")
                result = writer.supersede_extraction(verify_operation(token, signing_key=KEY), old_operation_id=binding.operation_id)
                assert result.receipt.state == "applied"
                def no_late_context(*a, **k): raise AssertionError("terminal output evaluated again")
                monkeypatch.setattr(rules, "readback_context_current", no_late_context)
            finally: paused.release.set()
            assert future.result(4).receipt.state == "superseded"
        assert writer._store.list_restatements(ep) == () and len(paused.inputs) == 1
    finally:
        paused.release.set(); writer._store.close()


from test_journey_commands import SCHEMA_CASES
from test_postgres_store import store as pg_clean_store


def insert_command(conn, data):
    from psycopg import sql
    keys = list(data)
    return conn.execute(sql.SQL("INSERT INTO journey_commands ({}) VALUES ({})").format(
        sql.SQL(",").join(map(sql.Identifier, keys)), sql.SQL(",").join(sql.Placeholder() for _ in keys)), tuple(data.values()))


@pytest.mark.parametrize("case", SCHEMA_CASES)
def test_s19_phase_shape_at_engine_first_refusal(pg_readback, pg_clean_store, case):
    store = pg_clean_store; ep = fresh_episode(); store.create_episode(ep, "fictional", now_utc=NOW)
    good = dict(operation_id=ep, episode_id=ep, phase="claimed", expected_revision=0,
        claim_revision=0, kind="create", purpose="episode:create", body_sha256="a"*64,
        scored=0, recorded_at=NOW.isoformat())
    conn = store._conn
    # Isolate CHECKs from the separately tested immutable matching-claim trigger.
    with conn.transaction():
        conn.execute("DROP TRIGGER journey_commands_claim_binding ON journey_commands")
        if case == "phase":
            from psycopg import sql
            shape = conn.execute("SELECT conname FROM pg_constraint WHERE conrelid='journey_commands'::regclass AND contype='c' AND pg_get_constraintdef(oid) LIKE '%terminal_state IS NULL%'").fetchall()
            assert len(shape) == 1
            conn.execute(sql.SQL("ALTER TABLE journey_commands DROP CONSTRAINT {}").format(sql.Identifier(shape[0][0])))
        with pytest.raises(psycopg.errors.CheckViolation):
            with conn.transaction(): insert_command(conn, dict(good, **SCHEMA_CASES[case]))
        insert_command(conn, good)
        assert conn.execute("SELECT count(*) FROM journey_commands WHERE operation_id=%s", (ep,)).fetchone()[0] == 1
        raise_rollback = psycopg.Rollback()
        raise raise_rollback


@pytest.mark.parametrize("field", ["operation_id", "episode_id", "disposition_version", "expected_revision", "claim_revision", "kind", "purpose", "body_sha256", "parent_restatement_id", "confirmation_id"])
def test_s19_completion_binding_is_engine_owned(pg_readback, pg_clean_store, field):
    store = pg_clean_store; ep = fresh_episode(); store.create_episode(ep, "fictional", now_utc=NOW)
    foreign = fresh_episode(); store.create_episode(foreign, "fictional", now_utc=NOW)
    good = dict(operation_id=ep, episode_id=ep, phase="claimed", expected_revision=0,
        claim_revision=0, kind="create", purpose="episode:create", body_sha256="a"*64,
        scored=0, recorded_at=NOW.isoformat())
    # Parent FK must be valid, so a bad FK cannot mask the binding guard.
    from carerelay.domain.models import HintLevel
    helper = make_service(store.dsn)
    try:
        helper.intake(ep, fixture.BOUND_COMPLAINT)
        parent = helper.submit_restatement(ep, "unsure", HintLevel.H1).restatement_id
    finally: helper._store.close()
    bad = dict(good, phase="completed", terminal_state="applied")
    values = dict(operation_id="other-"+ep, episode_id=foreign, disposition_version=1,
        expected_revision=99, claim_revision=99, kind="select_example", purpose="foreign",
        body_sha256="f"*64, parent_restatement_id=parent, confirmation_id="other-confirmation")
    bad[field] = values[field]
    conn = store._conn
    with conn.transaction():
        insert_command(conn, good)
        with pytest.raises(psycopg.errors.RaiseException, match="completion requires matching claim"):
            with conn.transaction(): insert_command(conn, bad)
        insert_command(conn, dict(good, phase="completed", terminal_state="applied"))
        assert conn.execute("SELECT count(*) FROM journey_commands WHERE operation_id=%s", (ep,)).fetchone()[0] == 2
        raise psycopg.Rollback()


@pytest.mark.parametrize("phase", ["claimed", "completed"])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE", "TRUNCATE", "UPSERT"])
def test_s19_matching_receipt_append_only(pg_readback, phase, verb):
    service, dsn = pg_readback; ep = fresh_episode()
    binding = OperationBinding(ep, ep, None, 0, "create", "episode:create", request_digest("create", {}), None, None)
    service.start_example(binding)
    with psycopg.connect(dsn) as conn:
        row = conn.execute("SELECT id FROM journey_commands WHERE operation_id=%s AND phase=%s", (ep,phase)).fetchone(); assert row is not None
        ident = row[0]
        if verb == "UPDATE": statement = "UPDATE journey_commands SET purpose=purpose WHERE id=%s"; args=(ident,)
        elif verb == "DELETE": statement = "DELETE FROM journey_commands WHERE id=%s"; args=(ident,)
        elif verb == "TRUNCATE": statement="TRUNCATE journey_commands"; args=()
        else:
            statement="INSERT INTO journey_commands SELECT * FROM journey_commands WHERE id=%s ON CONFLICT(id) DO UPDATE SET purpose=EXCLUDED.purpose"; args=(ident,)
        with pytest.raises(psycopg.errors.RestrictViolation, match="append-only"):
            with conn.transaction(): conn.execute(statement,args)
        assert conn.execute("SELECT count(*) FROM journey_commands WHERE id=%s", (ident,)).fetchone()[0] == 1
        # This database-only control is rolled back, including its trigger removal.
        with conn.transaction():
            target = "update" if verb == "UPSERT" else verb.lower()
            conn.execute("DROP TRIGGER journey_commands_no_"+target+" ON journey_commands")
            result = conn.execute(statement,args)
            assert result.rowcount == 1 if verb != "TRUNCATE" else conn.execute("SELECT count(*) FROM journey_commands").fetchone()[0] == 0
            raise psycopg.Rollback()
        assert conn.execute("SELECT count(*) FROM journey_commands WHERE id=%s", (ident,)).fetchone()[0] == 1


@pytest.mark.parametrize("first", ["failed", "acknowledged"])
def test_s19_waiting_callback_observes_first_terminal(pg_readback, first):
    from test_journey import s17_ready
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    service, dsn = pg_readback; second = make_service(dsn)
    ep, binding = s17_ready(service, fresh_episode()); service.request_appointment(binding)
    attempt = service._store.list_attempts(ep)[0]
    last = "acknowledged" if first == "failed" else "failed"
    try:
        with psycopg.connect(dsn, autocommit=True) as observer, ThreadPoolExecutor(1) as pool:
            with service._store.journey_transaction(ep, write=True):
                waiting = pool.submit(second._store.record_callback_once, attempt.attempt_id, uuid.uuid4().hex,
                    CallbackResult(transition=ExecutionStatus(last)), Origin.LOCAL_SIM, now_utc=NOW)
                wait_for_pg_lock(observer, second._store._conn.info.backend_pid, service._store._conn.info.backend_pid)
                result = service._store.record_callback_once(attempt.attempt_id, uuid.uuid4().hex,
                    CallbackResult(transition=ExecutionStatus(first)), Origin.LOCAL_SIM, now_utc=NOW)
                assert result.disposition.value == "applied"
            assert waiting.result(4).disposition.value == "applied"
        transitions = second._store.list_transitions(attempt.attempt_id)
        assert [t.kind.value for t in transitions] == [first,last]
        assert second._store.load_snapshot(ep).attempt.execution.value == first
        assert not second.project_journey(ep).outcome.care_evidenced
    finally: second._store.close()


def test_s19_preupgrade_migration_twice_preserves_row_bytes_and_fresh_process(pg_readback, pg_clean_store, tmp_path):
    """Build the old schema from the shipped pre-upgrade commit, not a new-schema seed."""
    import importlib.util
    from carerelay import postgres_schema
    from carerelay.service import ScenarioClock
    from _journey_fixtures import seed_journey
    dsn = pg_clean_store.dsn
    modules = {}
    for name in ["postgres_schema", "postgres_store"]:
        source = subprocess.check_output(["git","show","b91a4ad248fbd22e407b9536f1825d62b52ae8c2:src/carerelay/"+name+".py"],cwd=ROOT)
        path=tmp_path/("old_"+name+".py"); path.write_bytes(source)
        key="carerelay._slice19_old_"+name
        spec=importlib.util.spec_from_file_location(key,path); module=importlib.util.module_from_spec(spec)
        sys.modules[key]=module; spec.loader.exec_module(module); modules[name]=module
    old_schema=modules["postgres_schema"]; old_module=modules["postgres_store"]
    old_module.postgres_schema=old_schema
    assert "journey_commands" not in old_schema.APPEND_ONLY_TABLES
    with psycopg.connect(dsn,autocommit=True) as conn:
        names=conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()
        from psycopg import sql
        conn.execute(sql.SQL("DROP TABLE {} CASCADE").format(sql.SQL(",").join(sql.Identifier(r[0]) for r in names)))
    old=old_module.PostgresEpisodeStore(dsn)
    service=make_service(dsn, store=old)
    cases=["start","plan","stopped","expired","accepted","handoff","h3","failed","barrier"]
    prefix=fresh_episode()+"-"
    for case in cases:
        service._clock=ScenarioClock(NOW)
        seed_journey(service,prefix+case,case)
        if case=="expired": service.project_patient(prefix+case)
    tables=old_schema.APPEND_ONLY_TABLES
    def row_bytes(conn):
        return {table:conn.execute(sql.SQL("SELECT row_to_json(t)::text FROM {} t ORDER BY row_to_json(t)::text").format(sql.Identifier(table))).fetchall() for table in tables}
    with psycopg.connect(dsn,autocommit=True) as conn:
        assert conn.execute("SELECT to_regclass('public.journey_commands')").fetchone()[0] is None
        assert {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")} == set(tables)
        before=row_bytes(conn)
    old.close(); PostgresEpisodeStore.forget_applied_schema(dsn)
    upgraded=PostgresEpisodeStore(dsn)
    try:
        upgraded.init_schema(force=True); upgraded.init_schema(force=True)
        with psycopg.connect(dsn,autocommit=True) as conn:
            assert row_bytes(conn)==before
            actual={r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
            assert actual==set(postgres_schema.APPEND_ONLY_TABLES)==set(tables)|{"journey_commands"}
    finally: upgraded.close()
    script=f"""
import json
from fastapi.testclient import TestClient
from carerelay.api import app,get_service
with TestClient(app,headers={{'Authorization':'Bearer synthetic-s19-migration'}}) as client:
 out={{}}
 for case in {cases!r}:
  ep={prefix!r}+case; response=client.get('/api/episodes/'+ep)
  body=response.json(); out[case]={{'status':response.status_code,'step':body.get('step'),'deadline':(body.get('plan') or {{}}).get('deadline_utc')}}
  ledger=client.get('/api/episodes/'+ep+'/ledger').json()
  assert all(r['extraction_provenance'] is None for r in ledger['restatements'])
 print(json.dumps(out))
"""
    env=child_env(dsn); env.update(APP_DATABASE_URL=dsn,CARERELAY_API_TOKEN="synthetic-s19-migration")
    child=subprocess.run([sys.executable,"-c",script],cwd=ROOT,env=env,capture_output=True,text=True,timeout=12)
    assert child.returncode==0,child.stderr
    output=json.loads(child.stdout)
    expected=dict(start="start",plan="plan",stopped="stopped",expired="expired",accepted="accepted",handoff="handoff",h3="stopped",failed="unresolved",barrier="barrier")
    for case in cases:
        assert output[case]=={'status':200,'step':expected[case],'deadline':None if case=='start' else '2026-09-30T10:00:00+00:00'}
    with psycopg.connect(dsn,autocommit=True) as conn: assert row_bytes(conn)==before


@pytest.mark.parametrize("record", ["restatement", "acceptance", "escalation", "attempt"])
@pytest.mark.parametrize("regression", [False,True])
def test_s19_event_order_equal_timestamps_uses_real_engine(pg_readback, monkeypatch, record, regression):
    import carerelay.postgres_store as pg
    from carerelay.domain.models import AttemptCommand, HintLevel
    from carerelay.service import ScenarioClock
    service,_=pg_readback; ep=fresh_episode(); service.ensure_episode(ep,"fictional"); service.intake(ep,fixture.BOUND_COMPLAINT); service.change_consent(ep,True)
    ids=iter([ep+"z",ep+"a"]); monkeypatch.setattr(pg.uuid,"uuid4",lambda:SimpleNamespace(hex=next(ids)))
    second=NOW-timedelta(seconds=1) if regression else NOW
    if record=="escalation":
        for outcome,now in [("handed_off",NOW),("failed",second)]: service._store.record_escalation(ep,human_path="nurse_line",outcome=outcome,now_utc=now)
        assert service._store.load_snapshot(ep).escalation_id==ep+"a"
    elif record=="acceptance":
        for owner,now in [("caregiver",NOW),("patient",second)]: service._store.record_human_acceptance(ep,accepted_by=owner,scope="handoff",now_utc=now)
        assert service._store.load_snapshot(ep).human_acceptance_id==ep+"a"
    elif record=="attempt":
        for purpose,now in [("one",NOW),("two",second)]: service._store.open_attempt_once(AttemptCommand(ep,"fictional_provider",purpose,1),ep+purpose,now_utc=now)
        assert service._store.load_snapshot(ep).attempt.attempt_id==ep+"a"
    else:
        for text,now in [("see the doctor today before 6pm myself",NOW),("see the doctor tomorrow before 6pm myself",second)]:
            service._clock=ScenarioClock(now); service.submit_restatement(ep,text,HintLevel.H1)
        assert [r.restatement_id for r in service._store.list_restatements(ep)]==[ep+"z",ep+"a"]


@pytest.mark.parametrize("dimension", ["episode", "version", "policy", "revision", "stop", "sticky_expiry", "deadline", "attempt", "parent", "cue", "repair_count", "confirmation", "words", "h3", "cap"])
def test_s19_independent_final_context_guard_with_engine_bundle(pg_readback, tmp_path, monkeypatch, dimension):
    import test_field_repair as controls
    _,dsn=pg_readback
    monkeypatch.setattr(controls,"make_service",lambda path:make_service(dsn))
    # Independent first-refusal guards over the actual stored bundle. Concurrent
    # engine changes are proved separately, because their revision fences overlap.
    start=controls.start_readback
    monkeypatch.setattr(controls,"start_readback",lambda s: start(s,fresh_episode()))
    controls.test_final_context_fences_are_independent(tmp_path,dimension,monkeypatch)


def test_s19_null_parent_score_returns_valid_receipt(pg_readback):
    from test_field_repair import start_readback,confirm,score
    service,_=pg_readback; ep=start_readback(service,fresh_episode())
    confirm(service,ep,"go to the clinic today before six myself")
    outcome=None; failure=None
    try: outcome=score(service,ep)[1]
    except psycopg.Error as error: failure=type(error).__name__
    assert outcome is not None, "Postgres initial scoring failed: " + str(failure)
    assert outcome.receipt.scored and outcome.receipt.state=="applied"
    assert outcome.journey.step=="barrier" and len(service._store.list_restatements(ep))==1


def test_s19_catalog_has_exact_tables_and_all_required_triggers(pg_readback):
    from carerelay import postgres_schema,state
    _,dsn=pg_readback
    with psycopg.connect(dsn,autocommit=True) as conn:
        actual={r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        assert actual==set(state.APPEND_ONLY_TABLES)==set(postgres_schema.APPEND_ONLY_TABLES)
        triggers={r[0] for r in conn.execute("SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND NOT t.tgisinternal AND t.tgenabled='O'")}
        expected={table+"_no_"+verb for table in actual for verb in ["update","delete","truncate"]}|{"journey_commands_claim_binding"}
        assert triggers==expected


@pytest.mark.parametrize("phase", ["claimed", "completed"])
def test_s19_receipt_phase_uniqueness(pg_readback, phase):
    from psycopg.rows import dict_row
    service, dsn = pg_readback; ep = fresh_episode()
    binding = OperationBinding(ep, ep, None, 0, "create", "episode:create", request_digest("create", {}), None, None)
    service.start_example(binding)
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        row = conn.execute("SELECT * FROM journey_commands WHERE operation_id=%s AND phase=%s", (ep, phase)).fetchone()
        row.pop("id")
        with pytest.raises(psycopg.errors.UniqueViolation):
            with conn.transaction(): insert_command(conn, row)
        assert conn.execute("SELECT count(*) AS n FROM journey_commands WHERE operation_id=%s", (ep,)).fetchone()["n"] == 2


@pytest.mark.parametrize("dimension", ["episode_id", "disposition_version", "expected_revision", "kind", "purpose", "body_sha256", "parent_restatement_id", "confirmation_id"])
def test_s19_replayed_binding_first_refusal(pg_readback, dimension):
    from carerelay.journey_commands import CommandConflict
    from test_journey_mutation_controls import MAC_BAD
    service, _ = pg_readback; ep = fresh_episode()
    binding = OperationBinding(ep, ep, None, 0, "create", "episode:create", request_digest("create", {}), None, None)
    service.start_example(binding)
    with service._store.journey_transaction(ep, write=False) as tx:
        assert tx.find(binding).state == "applied"
        with pytest.raises(CommandConflict): tx.find(replace(binding, **{dimension: MAC_BAD[dimension]}))


@pytest.mark.parametrize("case", ["final-score", "forged-permits", "forked-permit", "intake-replay"])
def test_s19_existing_control_over_real_engine(pg_readback, tmp_path, monkeypatch, case):
    import test_journey as journey
    import test_journey_commands as commands
    import test_field_repair as repair
    import test_adp_extraction as extraction
    import test_journey_mutation_controls as controls
    _, dsn = pg_readback
    for module, name in [(journey, "make_service"), (commands, "command_service"), (repair, "make_service")]:
        monkeypatch.setattr(module, name, lambda path: make_service(dsn))
    monkeypatch.setattr(commands, "S15_KEY", KEY)
    tests = {"final-score": extraction.test_final_score_requires_its_own_committing_transaction,
        "forged-permits": journey.test_s17_forged_reconstructed_and_spent_permits_refuse,
        "forked-permit": journey.test_s17_forked_process_cannot_spend_original_permit,
        "intake-replay": controls.test_intake_replay_does_not_reenter_stale_offer_check}
    tests[case](tmp_path)


@pytest.mark.parametrize("defect,want", [
    ("binding_version", "dispatch disposition changed"), ("attempt_absent", "dispatch attempt version changed"),
    ("attempt_version", "dispatch attempt version changed"), ("membership", "dispatch attempt membership changed"),
    ("terminal", "dispatch attempt already terminal"), ("route", "dispatch route changed"),
    ("attempt_route", "dispatch route changed"), ("withdrawn", "dispatch route changed"),
    ("purpose", "dispatch purpose changed"), ("attempt_purpose", "dispatch purpose changed"),
    ("stop", "dispatch flow stopped"), ("consent", "dispatch consent changed"),
    ("consent_version", "dispatch consent changed"), ("expiry", "dispatch deadline expired"),
    ("deadline", "dispatch deadline expired"), ("rounds", "dispatch understanding unavailable"),
    ("comparison", "dispatch understanding unavailable"), ("h3", "dispatch understanding unavailable"),
    ("policy", "dispatch recorded policy unavailable"), ("policy_route", "dispatch recorded policy unavailable"),
    ("barrier", "dispatch supported barrier unavailable"), ("closure", "dispatch closure unavailable"),
])
def test_s19_dispatch_guard_first_refusal_with_engine_bundle(pg_readback, tmp_path, monkeypatch, defect, want):
    import test_journey as controls
    _, dsn = pg_readback
    monkeypatch.setattr(controls, "make_service", lambda path: make_service(dsn))
    controls.test_s17_each_final_guard_has_an_isolated_counterexample(tmp_path, defect, want)


def test_s19_action_crash_before_claim_commit_rolls_back(pg_readback):
    from test_journey import s17_ready
    service, dsn = pg_readback
    ep, binding = s17_ready(service, fresh_episode())
    script = f"""
import os,signal
from test_journey_postgres import make_service
from carerelay.domain.models import OperationBinding
s=make_service({dsn!r})
def die(*a,**k): os.kill(os.getpid(),signal.SIGKILL)
s._store.open_attempt_once=die
s.request_appointment(OperationBinding(**{asdict(binding)!r}))
"""
    child = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=child_env(dsn), capture_output=True, text=True, timeout=10)
    assert child.returncode == -9, child.stderr
    restarted = make_service(dsn)
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            assert conn.execute("SELECT count(*) FROM journey_commands WHERE operation_id=%s", (binding.operation_id,)).fetchone()[0] == 0
        assert restarted._store.list_attempts(ep) == ()
        calls = []; provider = restarted._coordinator._tools._provider; submit = provider.submit_request
        provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
        assert restarted.request_appointment(binding).receipt.state == "applied"
        assert restarted.request_appointment(binding).receipt.replayed
        assert len(calls) == len(restarted._store.list_attempts(ep)) == 1
    finally:
        restarted._store.close()
