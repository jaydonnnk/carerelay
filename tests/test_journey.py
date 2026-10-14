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


def s17_understood(service, episode="00000000-0000-4000-8000-000000000017"):
    from test_field_repair import start_readback, confirm
    from carerelay.journey_commands import verify_operation
    start_readback(service, episode)
    confirm(service, episode, "go to the clinic today before six myself")
    offer = next(o for o in service.project_journey(episode).commands if o.kind == "score_words")
    result = service.score_confirmed(verify_operation(offer.operation_token,
        signing_key=service._operation_signing_key()))
    assert result.journey.step == "barrier"
    return episode


def s17_binding(service, episode, kind, choice=None):
    from carerelay.journey_commands import request_digest, verify_operation
    if kind == "select_barrier":
        token = service.prepare_command(episode, kind=kind,
            body_sha256=request_digest(kind, {"choice_id": choice}), parent_id=None)
    else:
        offer = next(o for o in service.project_journey(episode).commands if o.kind == kind)
        token = offer.operation_token
    return verify_operation(token, signing_key=service._operation_signing_key())


def test_s17_permission_dispatch_and_callback_are_separate(tmp_path):
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    service = make_service(tmp_path / "permission.sqlite")
    try:
        ep = s17_understood(service)
        journey = service.project_journey(ep)
        assert any(o.kind == "select_barrier" for o in journey.commands)
        barrier = s17_binding(service, ep, "select_barrier", "booking")
        chosen = service.record_barrier_choice(barrier, choice_id="booking")
        assert chosen.journey.step == "permission"
        assert service._store._conn.execute("SELECT result_kind FROM journey_commands WHERE operation_id = ? AND phase = 'completed'", (barrier.operation_id,)).fetchone()[0] == "barrier"
        assert not any(o.kind == "request" for o in chosen.journey.commands)
        declined = service.change_share_consent(s17_binding(service, ep, "decline_share"), granted=False)
        assert declined.journey.step == "permission" and not service._store.list_attempts(ep)
        granted = service.change_share_consent(s17_binding(service, ep, "grant_share"), granted=True)
        assert any(o.kind == "request" for o in granted.journey.commands)
        assert service._store._conn.execute("SELECT result_kind FROM journey_commands WHERE operation_id = ? AND phase = 'completed'", (granted.receipt.operation_id,)).fetchone()[0] == "consent"
        binding = s17_binding(service, ep, "request")
        requested = service.request_appointment(binding)
        assert requested.receipt.state == "applied" and not requested.receipt.scored
        assert requested.journey.step == "permission"
        assert requested.journey.text["status"] == "No reply yet."
        assert requested.journey.outcome.execution is ExecutionStatus.ATTEMPTED
        assert not any(o.kind == "request" for o in requested.journey.commands)
        assert service.request_appointment(binding).receipt.replayed
        attempts = service._store.list_attempts(ep)
        assert len(attempts) == 1
        assert service._store._conn.execute("SELECT purpose_id FROM attempts").fetchone()[0] == "disposition:1:request_appointment"
        assert len([k for k, _, _ in service._store.list_events(ep) if k == "dispatch_started"]) == 1
        assert len([k for k, _, _ in service._store.list_events(ep) if k == "dispatch_observed"]) == 1
        service.receive_callback(ep, "fictional_provider", "fictional-s17-failure",
            CallbackResult(transition=ExecutionStatus.FAILED), Origin.LOCAL_SIM)
        failed = service.project_journey(ep)
        assert failed.step == "unresolved" and failed.text["heading"] == "The request did not work"
        assert failed.lines == ("No one has agreed to help yet.", "Please act now.",
            "Please do it before 6pm today.", "If that does not work, call the fictional nurse line.")
        assert failed.plan.current_owner_id == "patient"
        assert failed.plan.deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
    finally:
        service._store.close()


@pytest.mark.parametrize("choice", ["transport", "other"])
def test_s17_unsupported_barrier_stops_without_request(tmp_path, choice):
    service = make_service(tmp_path / "unsupported.sqlite")
    try:
        ep = s17_understood(service)
        binding = s17_binding(service, ep, "select_barrier", choice)
        result = service.record_barrier_choice(binding, choice_id=choice)
        assert result.journey.step == "stopped" and result.journey.flow.stopped
        assert result.journey.text["feedback"] == "This example cannot help with that."
        assert not service._store.list_attempts(ep)
        assert service.record_barrier_choice(binding, choice_id=choice).receipt.replayed
    finally:
        service._store.close()


def s17_ready(service, episode="00000000-0000-4000-8000-000000000017"):
    ep = s17_understood(service, episode)
    service.record_barrier_choice(s17_binding(service, ep, "select_barrier", "booking"), choice_id="booking")
    service.change_share_consent(s17_binding(service, ep, "grant_share"), granted=True)
    return ep, s17_binding(service, ep, "request")


@pytest.mark.parametrize("change", ["stop", "revoke", "deadline", "sticky_expiry"])
def test_s17_final_recheck_refuses_before_invocation(tmp_path, change):
    from datetime import timedelta
    from carerelay.state import CLINICAL_SCOPE
    service = make_service(tmp_path / "recheck.sqlite")
    calls = []
    try:
        ep, binding = s17_ready(service)
        original = service._coordinator.execute_tool
        provider = service._coordinator._tools._provider
        submit = provider.submit_request
        provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
        def change_then_execute(request, *, now_utc):
            now = fixture.SCENARIO_NOW_UTC
            if change == "stop":
                service._store.record_flow_stop(ep, 1, "reassessment_stop", "nurse_line", now_utc=now)
            elif change == "revoke":
                service._store.change_consent(ep, CLINICAL_SCOPE, granted=False, now_utc=now)
            elif change == "deadline":
                service._clock._instant = now + timedelta(hours=10)
            else:
                service._store.record_expiry_once(ep, 1, now + timedelta(hours=10))
            return original(request, now_utc=now_utc)
        service._coordinator.execute_tool = change_then_execute
        result = service.request_appointment(binding)
        assert result.receipt.state == "refused" and not result.receipt.scored
        assert calls == []
        assert not any(k == "dispatch_started" for k, _, _ in service._store.list_events(ep))
        assert len(service._store.list_attempts(ep)) == 1
    finally:
        service._store.close()


def test_s17_forged_reconstructed_and_spent_permits_refuse(tmp_path):
    from dataclasses import replace
    from carerelay.tools import UnknownAttemptKey
    service = make_service(tmp_path / "permits.sqlite")
    calls = []
    try:
        ep, binding = s17_ready(service)
        coordinator = service._coordinator
        original = coordinator.execute_tool
        provider = coordinator._tools._provider
        submit = provider.submit_request
        provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
        def probe(request, *, now_utc):
            for fake in (None, replace(request.permit)):
                with pytest.raises(UnknownAttemptKey):
                    coordinator._tools.submit_simulated_request(ep, request.route_id, request.attempt_key,
                        permit=fake, now_utc=now_utc)
            result = original(request, now_utc=now_utc)
            with pytest.raises(UnknownAttemptKey):
                original(request, now_utc=now_utc)
            return result
        coordinator.execute_tool = probe
        result = service.request_appointment(binding)
        assert result.receipt.state == "applied" and len(calls) == 1
        assert service.request_appointment(binding).receipt.replayed and len(calls) == 1
    finally:
        service._store.close()


@pytest.mark.parametrize("cut", ["claim", "effect", "receipt"])
def test_s17_action_crash_never_redispatches(tmp_path, cut):
    from dataclasses import asdict, replace
    from carerelay.domain.models import OperationBinding
    from carerelay.journey_commands import CommandConflict, CommandInvalid
    from carerelay.tools import UnknownAttemptKey
    path, marker = tmp_path / "crash.sqlite", tmp_path / "effect.txt"
    service = make_service(path)
    ep, binding = s17_ready(service)
    service._store.close()
    child_source = '''
import os,signal,sys,json
from pathlib import Path
sys.path.insert(0,'tests')
from test_truthfulness import make_service
from carerelay.domain.models import OperationBinding
from carerelay.state import JourneyTransaction
s=make_service(PATH)
def die(*a,**k):
    if CUT=='effect': Path(MARKER).write_text('one local simulated effect')
    os.kill(os.getpid(),signal.SIGKILL)
if CUT=='claim': s._coordinator.execute_tool=die
elif CUT=='effect': s._coordinator._tools._provider.submit_request=die
else:
    provider=s._coordinator._tools._provider
    submit=provider.submit_request
    def effect(*a):
        Path(MARKER).write_text('one local simulated effect')
        return submit(*a)
    provider.submit_request=effect
    JourneyTransaction.complete_once=die
s.request_appointment(OperationBinding(**BINDING))
'''.replace("PATH", repr(str(path))).replace("CUT", repr(cut)).replace("MARKER", repr(str(marker))).replace("BINDING", repr(asdict(binding)))
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), APP_DATABASE_URL=":memory:", APP_ENV="local",
        APP_CLOCK="scenario", CARERELAY_API_TOKEN="", PYTHONDONTWRITEBYTECODE="1",
        CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled")
    child = subprocess.run([sys.executable, "-c", child_source], cwd=ROOT, env=env,
        capture_output=True, text=True)
    assert child.returncode == -9, child.stderr
    service = make_service(path)
    try:
        result = service.request_appointment(binding)
        assert result.receipt.state == "pending" and result.receipt.replayed
        assert result.journey.step == "permission" and result.journey.text["status"] == "No reply yet."
        assert "feedback" not in result.journey.text
        attempts = service._store.list_attempts(ep)
        assert len(attempts) == 1
        assert not any(k in {"dispatch_started", "dispatch_observed"} for k, _, _ in service._store.list_events(ep))
        with pytest.raises(CommandConflict):
            service.request_appointment(replace(binding, operation_id="new-after-crash", expected_revision=result.journey.revision))
        with pytest.raises(CommandInvalid):
            service.open_action(ep, "fictional_provider", "caller-retry")
        with pytest.raises(UnknownAttemptKey):
            service._coordinator._tools.submit_simulated_request(ep, "fictional_provider",
                attempts[0].idempotency_key, now_utc=fixture.SCENARIO_NOW_UTC)
        assert marker.exists() is (cut != "claim")
    finally:
        service._store.close()


def test_s17_nested_claim_cannot_dispatch_before_commit(tmp_path):
    from carerelay.state import StateError
    service = make_service(tmp_path / "nested.sqlite")
    calls = []
    try:
        ep, binding = s17_ready(service)
        provider = service._coordinator._tools._provider
        submit = provider.submit_request
        provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
        with service._store.journey_transaction(ep, write=True):
            with pytest.raises(StateError):
                service.request_appointment(binding)
            assert calls == [] and service._store.list_attempts(ep) == ()
        assert service.request_appointment(binding).receipt.state == "applied"
        assert len(calls) == 1
    finally:
        service._store.close()


def test_s17_invalid_observation_is_unavailable_with_pending_fence(tmp_path, monkeypatch):
    from carerelay.tools import ToolError
    from carerelay.journey_commands import issue_operation
    service = make_service(tmp_path / "unavailable.sqlite")
    try:
        ep, binding = s17_ready(service)
        monkeypatch.setenv("APP_ENV", "local")
        monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-s17-auth")
        def unavailable(*a):
            raise ToolError("synthetic provider detail must not be returned")
        service._coordinator._tools._provider.submit_request = unavailable
        app.dependency_overrides[get_service] = lambda: service
        with TestClient(app, headers={"Authorization": "Bearer synthetic-s17-auth"}, raise_server_exceptions=False) as client:
            token = issue_operation(binding, signing_key=service._operation_signing_key())
            result = client.post(f"/api/episodes/{ep}/actions", json={"operation_token": token})
            assert result.status_code == 503
            assert result.json() == {"detail": "journey unavailable"}
            replay = client.post(f"/api/episodes/{ep}/actions", json={"operation_token": token})
            assert replay.status_code == 202 and replay.json()["receipt"]["state"] == "pending"
            assert len(service._store.list_attempts(ep)) == 1
    finally:
        app.dependency_overrides.clear()
        service._store.close()


def test_s17_terminal_callback_before_invocation_refuses_dispatch(tmp_path):
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    service = make_service(tmp_path / "early-callback.sqlite")
    calls = []
    try:
        ep, binding = s17_ready(service)
        coordinator = service._coordinator
        original = coordinator.execute_tool
        provider = coordinator._tools._provider
        submit = provider.submit_request
        provider.submit_request = lambda *a: (calls.append(a), submit(*a))[1]
        def complete_first(request, *, now_utc):
            service.receive_callback(ep, "fictional_provider", "fictional-first-terminal",
                CallbackResult(transition=ExecutionStatus.FAILED), Origin.LOCAL_SIM)
            return original(request, now_utc=now_utc)
        coordinator.execute_tool = complete_first
        result = service.request_appointment(binding)
        assert result.receipt.state == "refused" and calls == []
        assert result.journey.step == "unresolved"
    finally:
        service._store.close()


@pytest.mark.parametrize("writer_kind", ["stop", "revoke"])
def test_s17_dispatch_holds_serialization_until_atomic_commit(tmp_path, writer_kind):
    import time
    from dataclasses import asdict
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    path = tmp_path / "ordering.sqlite"
    entered, release = tmp_path / "entered", tmp_path / "release"
    writer_ready, writer_done = tmp_path / "writer-ready", tmp_path / "writer-done"
    service = make_service(path)
    ep, binding = s17_ready(service)
    service._store.close()
    setup = f'''import sys,time,json\nfrom pathlib import Path\nsys.path.insert(0,'tests')\nfrom test_truthfulness import make_service\nfrom carerelay.domain.models import OperationBinding\nfrom carerelay.demo import fixture\ns=make_service({str(path)!r})\n'''
    invocation = setup + f'''
provider=s._coordinator._tools._provider
original=provider.submit_request
def paused(*args):
    Path({str(entered)!r}).write_text('one simulated effect')
    until=time.monotonic()+8
    while not Path({str(release)!r}).exists():
        assert time.monotonic()<until, 'provider release missing'
        time.sleep(.01)
    return original(*args)
provider.submit_request=paused
result=s.request_appointment(OperationBinding(**{asdict(binding)!r}))
assert result.receipt.state=='applied'
s._store.close()
'''
    writer = setup + f'''
Path({str(writer_ready)!r}).write_text('ready for same-episode write')
if {writer_kind!r}=='stop':
    s._store.record_flow_stop({ep!r},1,'reassessment_stop','nurse_line',now_utc=fixture.SCENARIO_NOW_UTC)
else:
    s.change_consent({ep!r},False)
Path({str(writer_done)!r}).write_text('committed')
s._store.close()
'''
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), APP_DATABASE_URL=":memory:", APP_ENV="local",
        APP_CLOCK="scenario", CARERELAY_API_TOKEN="", PYTHONDONTWRITEBYTECODE="1",
        CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled")
    children = []
    def wait_file(p):
        until = time.monotonic() + 5
        while not p.exists():
            assert time.monotonic() < until, str(p)
            time.sleep(.01)
    try:
        invoker = subprocess.Popen([sys.executable, "-c", invocation], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        children.append(invoker)
        wait_file(entered)
        waiting = subprocess.Popen([sys.executable, "-c", writer], cwd=ROOT, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        children.append(waiting)
        wait_file(writer_ready)
        time.sleep(.2)
        assert waiting.poll() is None and not writer_done.exists(), "writer passed invocation serialization"
        release.write_text("finish bounded local call")
        for child in children:
            _, error = child.communicate(timeout=8)
            assert child.returncode == 0, error
        assert writer_done.read_text() == "committed"
        service = make_service(path)
        try:
            replay = service.request_appointment(binding)
            assert replay.receipt.state == "applied" and replay.receipt.replayed
            events = [k for k, _, _ in service._store.list_events(ep)]
            assert events.count("dispatch_started") == events.count("dispatch_observed") == 1
            assert len(service._store.list_attempts(ep)) == 1
            callback = service.receive_callback(ep, "fictional_provider", "late-after-" + writer_kind,
                CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED), Origin.LOCAL_SIM)
            assert not callback.applied
            assert service._store.load_snapshot(ep).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
        finally:
            service._store.close()
    finally:
        release.write_text("cleanup")
        for child in children:
            if child.poll() is None:
                child.communicate(timeout=10)


def test_s17_forked_process_cannot_spend_original_permit(tmp_path):
    from carerelay.tools import UnknownAttemptKey
    path = tmp_path / "fork.sqlite"
    service = make_service(path)
    try:
        ep, binding = s17_ready(service)
        coordinator = service._coordinator
        execute = coordinator.execute_tool
        def fork_probe(request, *, now_utc):
            pid = os.fork()
            if pid == 0:
                other = make_service(path)
                try:
                    other._coordinator._tools.submit_simulated_request(ep, request.route_id,
                        request.attempt_key, now_utc=now_utc, permit=request.permit)
                except UnknownAttemptKey:
                    os._exit(0)
                except BaseException:
                    os._exit(2)
                os._exit(1)
            _, status = os.waitpid(pid, 0)
            assert os.waitstatus_to_exitcode(status) == 0
            return execute(request, now_utc=now_utc)
        coordinator.execute_tool = fork_probe
        assert service.request_appointment(binding).receipt.state == "applied"
        assert len([k for k, _, _ in service._store.list_events(ep) if k == "dispatch_started"]) == 1
    finally:
        service._store.close()


@pytest.mark.parametrize("defect,want", [
    ("binding_version", "dispatch disposition changed"),
    ("attempt_absent", "dispatch attempt version changed"),
    ("attempt_version", "dispatch attempt version changed"),
    ("membership", "dispatch attempt membership changed"),
    ("terminal", "dispatch attempt already terminal"),
    ("route", "dispatch route changed"),
    ("attempt_route", "dispatch route changed"),
    ("withdrawn", "dispatch route changed"),
    ("purpose", "dispatch purpose changed"),
    ("attempt_purpose", "dispatch purpose changed"),
    ("stop", "dispatch flow stopped"),
    ("consent", "dispatch consent changed"),
    ("consent_version", "dispatch consent changed"),
    ("expiry", "dispatch deadline expired"),
    ("deadline", "dispatch deadline expired"),
    ("rounds", "dispatch understanding unavailable"),
    ("comparison", "dispatch understanding unavailable"),
    ("h3", "dispatch understanding unavailable"),
    ("policy", "dispatch recorded policy unavailable"),
    ("policy_route", "dispatch recorded policy unavailable"),
    ("barrier", "dispatch supported barrier unavailable"),
    ("closure", "dispatch closure unavailable"),
])
def test_s17_each_final_guard_has_an_isolated_counterexample(tmp_path, defect, want):
    from dataclasses import replace
    from carerelay.domain.models import ExecutionStatus, HintLevel, PlanComparison
    service = make_service(tmp_path / "isolated.sqlite")
    captured = {}
    try:
        ep, binding = s17_ready(service)
        coordinator = service._coordinator
        execute = coordinator.execute_tool
        def capture(request, *, now_utc):
            captured.update(bundle=service._store.load_journey_bundle(ep),
                attempt=service._store.get_attempt_by_key(request.attempt_key))
            return execute(request, now_utc=now_utc)
        coordinator.execute_tool = capture
        assert service.request_appointment(binding).receipt.state == "applied"
        bundle, attempt = captured["bundle"], captured["attempt"]
        now, route, purpose, permitted = fixture.SCENARIO_NOW_UTC, "fictional_provider", binding.purpose, fixture.policy().permitted_route_ids
        assert rules.dispatch_refusal(bundle, binding, attempt, route,
            attempt_purpose=purpose, permitted_routes=permitted, now_utc=now) is None
        if defect == "binding_version": binding = replace(binding, disposition_version=2)
        elif defect == "attempt_absent": attempt = None
        elif defect == "attempt_version": attempt = replace(attempt, disposition_version=2)
        elif defect == "membership": bundle = replace(bundle, snapshot=replace(bundle.snapshot, attempt=replace(attempt, attempt_id="different")))
        elif defect == "terminal": attempt = replace(attempt, execution=ExecutionStatus.FAILED)
        elif defect == "route": route = "nurse_line"; attempt = replace(attempt, route_id=route)
        elif defect == "attempt_route": attempt = replace(attempt, route_id="nurse_line")
        elif defect == "withdrawn": permitted = frozenset()
        elif defect == "purpose": binding = replace(binding, purpose="caller-purpose"); purpose = binding.purpose
        elif defect == "attempt_purpose": purpose = "caller-purpose"
        elif defect == "stop": bundle = replace(bundle, snapshot=replace(bundle.snapshot, flow_stop_reason="reassessment_stop"))
        elif defect == "consent": bundle = replace(bundle, consent_granted=False)
        elif defect == "consent_version": attempt = replace(attempt, consent_version=attempt.consent_version + 1)
        elif defect == "expiry": bundle = replace(bundle, snapshot=replace(bundle.snapshot, expiry_event_id=1))
        elif defect == "deadline": now = bundle.snapshot.disposition.clinical_deadline_utc
        elif defect == "rounds": bundle = replace(bundle, restatements=())
        elif defect == "comparison": bundle = replace(bundle, restatements=(replace(bundle.restatements[-1], comparison=PlanComparison(frozenset(), frozenset(), frozenset({"action_id", "deadline_utc", "next_owner_id"}))),))
        elif defect == "h3": bundle = replace(bundle, restatements=(replace(bundle.restatements[-1], hint_level=HintLevel.H3),))
        elif defect == "policy": bundle = replace(bundle, policy=None)
        elif defect == "policy_route": bundle = replace(bundle, policy=replace(bundle.policy, permitted_route_ids=frozenset()))
        elif defect == "barrier": bundle = replace(bundle, events=tuple(e for e in bundle.events if e[0] != "barrier_recorded"))
        elif defect == "closure": bundle = replace(bundle, snapshot=replace(bundle.snapshot, human_acceptance_id="fictional-accepted", accepted_by="caregiver", accepted_scope="handoff"))
        assert rules.dispatch_refusal(bundle, binding, attempt, route,
            attempt_purpose=purpose, permitted_routes=permitted, now_utc=now) == want
    finally:
        service._store.close()


def test_s17_authenticated_command_routes_and_schema_refusals(tmp_path, monkeypatch):
    from carerelay.journey_commands import issue_operation, request_digest
    service = make_service(tmp_path / "actual-http.sqlite")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-s17-route-auth")
    try:
        ep = s17_understood(service)
        app.dependency_overrides[get_service] = lambda: service
        with TestClient(app, headers={"Authorization": "Bearer synthetic-s17-route-auth"}, raise_server_exceptions=False) as client:
            url = f"/api/episodes/{ep}"
            prepared = client.get(url, params={"prepare_kind": "select_barrier",
                "body_sha256": request_digest("select_barrier", {"choice_id": "booking"})})
            assert prepared.status_code == 200
            token = prepared.json()["operation_token"]
            chosen = client.post(url + "/barriers", json={"operation_token": token, "choice_id": "booking"})
            assert chosen.status_code == 200, chosen.text
            assert chosen.json()["journey"]["step"] == "permission"
            assert client.post(url + "/barriers", json={"operation_token": token, "choice_id": "booking", "route_id": "nurse_line"}).status_code == 422
            assert client.post(url + "/barriers", json={"operation_token": token, "choice_id": "other"}).status_code == 409
            grant = s17_binding(service, ep, "grant_share")
            consent = client.post(url + "/consents", json={"operation_token": issue_operation(grant, signing_key=service._operation_signing_key())})
            assert consent.status_code == 200
            request = s17_binding(service, ep, "request")
            body = {"operation_token": issue_operation(request, signing_key=service._operation_signing_key())}
            assert client.post(url + "/actions", json={**body, "purpose_id": "caller-retry"}).status_code == 422
            applied = client.post(url + "/actions", json=body)
            assert applied.status_code == 200 and applied.json()["receipt"]["replayed"] is False
            replayed = client.post(url + "/actions", json=body)
            assert replayed.status_code == 200 and replayed.json()["receipt"]["replayed"] is True
            assert len(service._store.list_attempts(ep)) == 1
            assert client.post(url + "/actions", json=body, headers={"Authorization": "Bearer wrong"}).status_code == 401
    finally:
        app.dependency_overrides.clear()
        service._store.close()


@pytest.mark.parametrize("transfer", ["accepted", "handoff"])
def test_s17_pending_action_keeps_valid_human_transfer_renderable(tmp_path, transfer):
    from carerelay.coordinator import CoordinatorUnavailable
    service = make_service(tmp_path / "pending-transfer.sqlite")
    try:
        ep, binding = s17_ready(service)
        def unavailable(*a, **k):
            raise CoordinatorUnavailable("original execution lost")
        service._coordinator.execute_tool = unavailable
        with pytest.raises(CoordinatorUnavailable):
            service.request_appointment(binding)
        if transfer == "accepted": service.record_human_acceptance(ep, "caregiver", "handoff")
        else: service.escalate(ep, "nurse_line", "handed_off")
        projection = service.project_journey(ep)
        assert projection.step == transfer
        assert projection.commands == () and projection.question is None
        assert projection.flow.interpretation == "pending"
        body = journey_surface(projection)
        script = '''import {readFileSync} from 'node:fs';
import {decodeJourney} from './frontend/lib/journey.ts';
const v=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(Boolean(decodeJourney(v,v.episode_id))));'''
        node = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
            input=json.dumps(body), text=True, capture_output=True)
        assert node.returncode == 0, node.stderr
        assert json.loads(node.stdout) is True
        assert service.request_appointment(binding).receipt.state == "pending"
    finally:
        service._store.close()


@pytest.mark.parametrize("outcome", ["expired", "accepted", "handoff"])
def test_s17_unsupported_barrier_feedback_cannot_corrupt_terminal_screen(tmp_path, outcome):
    from datetime import timedelta
    service = make_service(tmp_path / "barrier-outcome.sqlite")
    try:
        ep = s17_understood(service)
        service.record_barrier_choice(s17_binding(service, ep, "select_barrier", "transport"), choice_id="transport")
        if outcome == "expired": service._clock._instant += timedelta(hours=10)
        elif outcome == "accepted":
            service.change_consent(ep, True)
            service.record_human_acceptance(ep, "caregiver", "handoff")
        else: service.escalate(ep, "nurse_line", "handed_off")
        projection = service.project_journey(ep)
        assert projection.step == outcome and projection.flow.stopped
        assert "feedback" not in projection.text
        body = journey_surface(projection)
        script = '''import {readFileSync} from 'node:fs';
import {decodeJourney} from './frontend/lib/journey.ts';
const v=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(Boolean(decodeJourney(v,v.episode_id))));'''
        node = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
            input=json.dumps(body), text=True, capture_output=True)
        assert node.returncode == 0, node.stderr
        assert json.loads(node.stdout) is True
    finally:
        service._store.close()


def test_s17_command_offers_refuse_unimplemented_kind():
    offers = rules._journey_offers(("select_barrier", "grant_share", "request", "create"), pending=False)
    assert [o.kind for o in offers] == ["select_barrier", "grant_share", "request"]
    assert offers[0].permitted_choice_ids == ("booking", "transport", "other")
    assert rules._journey_offers(("create",), pending=False) == ()

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
        tools = McpTools(service._store, policy=fixture.policy(), provider=ScriptedProvider(), now=lambda: service._clock.now_utc())
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
    # Slice 17 adds permission commands. Assert each screen's exact
    # capabilities so a wrong progression offer cannot hide behind a blanket [].
    expected_commands = {
        "plan": ["readback_started", "show_plan", "hide_plan", "grant_share", "revoke_share"],
        "readback": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "repair": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "uncertain": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "unavailable": ["confirm_words", "show_plan", "hide_plan", "h3"],
        "barrier": ["select_barrier", "show_plan", "hide_plan"],
        "permission": ["grant_share", "decline_share", "revoke_share", "show_plan", "hide_plan"],
        "declined": ["grant_share", "decline_share", "revoke_share", "show_plan", "hide_plan"],
    }
    for neutral in ("waiting", "acknowledged", "handoff_attempted", "handoff_unknown"):
        expected_commands[neutral] = ["show_plan", "hide_plan", "revoke_share"]
    for unresolved in ("failed", "handoff_failed", "stopped", "h3"):
        expected_commands[unresolved] = ["show_plan", "hide_plan", "grant_share", "revoke_share"]
    for expired in ("expired", "expired_accepted", "expired_handoff", "expired_stopped"):
        expected_commands[expired] = ["revoke_share"]
    expected = expected_commands.get(case, [])
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
