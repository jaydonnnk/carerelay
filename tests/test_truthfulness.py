"""Authenticated regression probes. Local SQLite unless explicitly marked otherwise."""
from contextlib import contextmanager
import secrets
import json

import pytest
from fastapi.testclient import TestClient

from carerelay.api import app, get_service
from carerelay.coordinator import LocalSimulationCoordinator
from carerelay.demo import fixture
from carerelay.service import EpisodeService, ScenarioClock
from carerelay.simulated_provider import ScriptedProvider
from carerelay.state import open_store
from carerelay.tools import McpTools

EPISODE = fixture.DEMO_EPISODE_ID
BASE = f"/api/episodes/{EPISODE}"


def make_service(path):
    store = open_store(path, check_same_thread=False)
    tools = McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())
    return EpisodeService(
        store, coordinator=LocalSimulationCoordinator(tools),
        clock=ScenarioClock(fixture.SCENARIO_NOW_UTC), policy=fixture.policy(),
        policy_text=fixture.policy_text(), display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition, bound_complaint=fixture.BOUND_COMPLAINT,
        policy_provenance="test: non-clinical fixture",
    )


@contextmanager
def connected(path, token):
    service = make_service(path)
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()
        service._store.close()


@pytest.fixture
def api(tmp_path, monkeypatch):
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv("CARERELAY_API_TOKEN", token)
    monkeypatch.setenv("APP_ENV", "public")
    path = tmp_path / "truthfulness.sqlite"
    with connected(path, token) as (client, service):
        assert TestClient(app).get(BASE).status_code == 401
        assert client.post("/api/episodes").status_code == 200
        assert client.post(BASE + "/intake", json={"confirmed_text": fixture.BOUND_COMPLAINT}).status_code == 200
        yield client, service, path, token


def surfaces(client):
    patient = client.get(BASE)
    ledger = client.get(BASE + "/ledger")
    alias = client.get(f"/ledger/{EPISODE}")
    # Slice 14 blocks assessed patient HTTP until the complete Slice 15 projection.
    # Retain all old serialized outcome assertions through the unchanged service,
    # plus authenticated HTTP ledger/mutation guards and exact recovery refusal.
    assert patient.status_code == 503, patient.text
    assert patient.json() == {"detail": "journey unavailable"}
    assert ledger.status_code == alias.status_code == 200, (ledger.text, alias.text)
    assert ledger.json() == alias.json()
    service = app.dependency_overrides.get(get_service, get_service)()
    legacy = json.loads(json.dumps(service.project_patient(EPISODE).as_dict()))
    return legacy, ledger.json()


def assert_unresolved(patient, ledger):
    assert patient["simulated"] is ledger["simulated"] is True
    assert patient["fixture_label"] == ledger["fixture_label"] == fixture.FIXTURE_LABEL
    assert patient["closure"] == "open"
    assert patient["lines"] == ["No one has agreed to help yet.", "Please act now.",
                                 "Please do it before 6pm today.",
                                 "If that does not work, call the fictional nurse line."]
    assert patient["care_evidenced"] is False
    assert ledger["axes"]["closure"] == "open"
    assert ledger["axes"]["action_owner_id"] == "patient"
    assert ledger["axes"]["care_evidenced"] is False


class TestFailedHandoff:
    @pytest.mark.parametrize("outcome", ["failed", "attempted", "unknown"])
    def test_unsuccessful_handoff_stays_unresolved(self, api, outcome):
        client, service, path, token = api
        deadline = service._store.load_snapshot(EPISODE).disposition.clinical_deadline_utc
        response = client.post(BASE + "/escalations", json={"human_path": "nurse_line", "outcome": outcome})
        assert response.status_code == 200
        assert service._store.derive_closure(EPISODE, fixture.SCENARIO_NOW_UTC).closure.value == "open"
        patient, ledger = surfaces(client)
        assert_unresolved(patient, ledger)
        assert ledger["escalation"]["outcome"] == outcome
        assert service._store.load_snapshot(EPISODE).disposition.clinical_deadline_utc == deadline
        with connected(path, token) as (restarted, reloaded):
            assert_unresolved(*surfaces(restarted))
            assert reloaded._store.load_snapshot(EPISODE).disposition.clinical_deadline_utc == deadline

    def test_handed_off_keeps_the_approved_successful_rendering(self, api):
        client, _, _, _ = api
        assert client.post(BASE + "/escalations", json={"human_path": "nurse_line", "outcome": "handed_off"}).status_code == 200
        patient, ledger = surfaces(client)
        assert patient["closure"] == "escalated_to_human"
        assert patient["lines"][0] == "We have passed this to the fictional nurse line."
        assert patient["lines"][1] == "You do not need to act now."
        assert ledger["axes"]["action_owner_id"] == "nurse_line"
        assert patient["care_evidenced"] is False


def consent(client, granted=True):
    assert client.post(BASE + "/consents", json={"granted": granted}).status_code == 200


def action(client):
    response = client.post(BASE + "/actions", json={"route_id": "fictional_provider", "purpose_id": "handoff-test"})
    assert response.status_code == 200
    return response.json()


class TestEvidenceTrust:
    @pytest.mark.parametrize("provenance", ["", "caller invents a convincing description"])
    def test_caller_labels_cannot_make_real_documentation(self, api, provenance):
        client, _, path, token = api
        consent(client)
        action(client)
        response = client.post(BASE + "/callbacks/fictional_provider", json={
            "callback_key": "invented-document", "evidence": {
                "level": "documented", "simulated": False,
                "source_ref": "not-an-artefact", "provenance": provenance,
            },
        })
        assert response.status_code == 422
        assert_unresolved(*surfaces(client))
        with connected(path, token) as (restarted, _):
            assert_unresolved(*surfaces(restarted))

    def test_mcp_cannot_launder_caller_labelled_real_evidence(self, api):
        from carerelay.domain.models import EvidenceRecord, EvidenceLevel
        from carerelay.domain.rules import PolicyViolation
        client, service, _, _ = api
        consent(client)
        tools = McpTools(service._store, policy=fixture.policy(), provider=ScriptedProvider())
        with pytest.raises(PolicyViolation):
            tools.record_evidence(EPISODE, EvidenceRecord(
                level=EvidenceLevel.DOCUMENTED, simulated=False,
                source_ref="not-an-artefact", provenance="caller-supplied",
            ), now_utc=fixture.SCENARIO_NOW_UTC)
        assert_unresolved(*surfaces(client))

    def test_simulated_report_and_acknowledgement_stay_non_documented(self, api):
        client, _, _, _ = api
        consent(client)
        action(client)
        response = client.post(BASE + "/callbacks/fictional_provider", json={
            "callback_key": "simulated-report", "transition": "acknowledged",
            "evidence": {"level": "self_reported", "simulated": True,
                         "source_ref": "simulation", "provenance": "scripted"},
        })
        assert response.status_code == 200
        assert response.json()["applied"] is True
        patient, ledger = surfaces(client)
        assert_unresolved(patient, ledger)
        assert ledger["axes"]["execution"] == "acknowledged"
        assert ledger["axes"]["evidence"] == "self_reported"


class TestAcceptanceAuthority:
    @pytest.mark.parametrize("actor,scope", [("patient", "unrelated"), ("caregiver", "unrelated"), ("patient", "handoff")])
    def test_only_a_relevant_transfer_can_close(self, api, actor, scope):
        client, _, _, _ = api
        consent(client)
        response = client.post(BASE + "/acceptances", json={"accepted_by": actor, "accepted_scope": scope})
        assert response.status_code == 422
        assert_unresolved(*surfaces(client))

    @pytest.mark.parametrize("revoked", [False, True])
    def test_acceptance_requires_current_permission(self, api, revoked):
        client, _, _, _ = api
        if revoked:
            consent(client)
            consent(client, False)
        response = client.post(BASE + "/acceptances", json={"accepted_by": "caregiver", "accepted_scope": "handoff"})
        assert response.status_code == 409
        assert_unresolved(*surfaces(client))

    def test_valid_acceptance_names_the_new_owner_without_claiming_care(self, api):
        client, service, path, token = api
        consent(client)
        response = client.post(BASE + "/acceptances", json={"accepted_by": "caregiver", "accepted_scope": "handoff"})
        assert response.status_code == 200
        patient, ledger = surfaces(client)
        assert patient["lines"] == ["Someone has agreed to help.", "You do not need to act now.",
                                    "It is set for 6pm today.", "If that does not happen, call the fictional nurse line."]
        assert patient["closure"] == "closed_with_evidence"
        assert patient["care_evidenced"] is False
        assert ledger["axes"]["action_owner_id"] == "caregiver"
        assert ledger["acceptance"]["accepted_by"] == "caregiver"
        assert ledger["acceptance"]["scope"] == "handoff"
        with connected(path, token) as (restarted, _):
            assert surfaces(restarted) == (patient, ledger)

    def test_historical_unrelated_acceptance_cannot_close_on_reload(self, api):
        client, service, path, token = api
        consent(client)
        # Repository fixture models a row stored by the original permissive path.
        service._store.record_human_acceptance(EPISODE, accepted_by="patient", scope="unrelated", now_utc=fixture.SCENARIO_NOW_UTC)
        with connected(path, token) as (restarted, _):
            assert_unresolved(*surfaces(restarted))


class TestReadBackPolarity:
    @pytest.mark.parametrize("text", [
        "I will not see the doctor today before 6pm myself.",
        "I will see the doctor today before 6pm myself. Actually I won't.",
        "I won't see the doctor today before 6pm myself.",
        "I don’t plan to see the doctor today before 6pm myself.",
        "I might see the doctor today before 6pm myself.",
        "Maybe I will see the doctor today before 6pm myself.",
        "I will see the doctor, but not today before 6pm, myself.",
        "I will see the doctor today before 6pm, not myself.",
        "Should I see the doctor today before 6pm myself?",
        "I will see the doctor today before 6pm or tomorrow before 6pm myself.",
    ])
    def test_negated_or_uncertain_answers_are_not_understanding(self, api, text):
        client, _, _, _ = api
        response = client.post(BASE + "/restatements", json={"text": text, "hint_level": "H0"})
        assert response.status_code == 200
        body = response.json()
        assert body["understood"] is False
        assert body["outcome"] == "not_recalled"
        assert body["uncertain"]
        assert body["mismatches"] == []
        patient, ledger = surfaces(client)
        assert_unresolved(patient, ledger)
        assert ledger["restatements"][-1]["outcome"] == "not_recalled"

    @pytest.mark.parametrize("text", [
        "I will see the doctor today before 6pm myself.",
        "Go to the fictional provider's same-day review before 6pm today and you are the owner.",
        "I will go to the clinic today before six myself.",
        "I will see the doctor today before 6pm myself. I am not worried.",
        "I should see the doctor today before 6pm myself.",
    ])
    def test_known_positive_answers_still_match(self, api, text):
        client, _, _, _ = api
        response = client.post(BASE + "/restatements", json={"text": text, "hint_level": "H0"})
        assert response.status_code == 200
        assert response.json()["understood"] is True
        assert response.json()["outcome"] == "recall_unaided"
        assert surfaces(client)[1]["restatements"][-1]["outcome"] == "recall_unaided"

    @pytest.mark.parametrize("owner_text", ["Appointment:", "theme", "myselfish"])
    def test_partial_answer_does_not_invent_an_owner_from_a_substring(self, api, owner_text):
        client, _, _, _ = api
        response = client.post(BASE + "/restatements", json={
            "text": f"{owner_text} see the doctor today before 6pm.", "hint_level": "H0"})
        assert response.status_code == 200
        assert response.json()["understood"] is False
        assert "next_owner_id" in response.json()["uncertain"]


GOOD = "I will see the doctor today before 6pm myself."
BAD = "I will see the doctor tomorrow before 6pm myself."


def readback(client, text=BAD, hint="H0", parent=None):
    suffix = "/restatements" if parent is None else f"/restatements/{parent}/repairs"
    return client.post(BASE + suffix, json={"text": text, "hint_level": hint})


def exhaust_repairs(client):
    response = readback(client)
    assert response.status_code == 200
    for _ in range(2):
        response = readback(client, parent=response.json()["restatement_id"])
        assert response.status_code == 200
    assert response.json()["routes_to_human_path"] is True
    return response.json()["restatement_id"]


class TestDurableStops:
    def test_fresh_restatement_cannot_reset_an_exhausted_ladder(self, api):
        client, _, path, token = api
        exhaust_repairs(client)
        with connected(path, token) as (restarted, _):
            response = readback(restarted, GOOD)
            assert response.status_code == 409
            assert_unresolved(*surfaces(restarted))

    def test_reassessment_stop_blocks_actions_after_reload(self, api):
        client, _, path, token = api
        consent(client)
        response = client.post(BASE + "/reassessments", json={})
        assert response.status_code == 200
        assert response.json()["outcome"] == "stop_at_human_path"
        with connected(path, token) as (restarted, _):
            response = restarted.post(BASE + "/actions", json={"route_id": "fictional_provider", "purpose_id": "after-stop"})
            assert response.status_code == 409
            assert_unresolved(*surfaces(restarted))

    def test_h3_never_reports_understanding_or_offers_repair(self, api):
        client, _, _, _ = api
        response = readback(client, GOOD, hint="H3")
        assert response.status_code == 200
        body = response.json()
        assert body["understood"] is False
        assert body["outcome"] == "not_recalled"
        assert body["routes_to_human_path"] is True
        assert body["next_repair_field"] is None
        assert surfaces(client)[1]["restatements"][-1]["outcome"] == "not_recalled"

    def test_direct_mcp_dispatch_cannot_bypass_reassessment_stop(self, api):
        from carerelay.state import StateError
        client, service, _, _ = api
        consent(client)
        opened = action(client)
        client.post(BASE + "/reassessments", json={})
        tools = McpTools(service._store, policy=fixture.policy(), provider=ScriptedProvider())
        with pytest.raises(StateError):
            tools.submit_simulated_request(EPISODE, "fictional_provider", opened["idempotency_key"], now_utc=fixture.SCENARIO_NOW_UTC)
        assert_unresolved(*surfaces(client))


class TestStopAlternatesAndRecovery:
    @pytest.mark.parametrize("cause", ["repairs", "h3", "reassessment", "barrier"])
    def test_stop_blocks_alternate_endpoints_in_a_fresh_process(self, api, cause):
        import json
        import os
        import subprocess
        import sys
        client, _, path, token = api
        consent(client)
        opened = action(client)
        parent = readback(client, GOOD).json()["restatement_id"]
        if cause == "repairs":
            parent = exhaust_repairs(client)
        elif cause == "h3":
            parent = readback(client, GOOD, hint="H3").json()["restatement_id"]
        elif cause == "reassessment":
            client.post(BASE + "/reassessments", json={})
        else:
            assert client.post(BASE + "/barriers", json={"barrier_text": "no route", "proposed_route_id": "invented"}).status_code == 422
        script = '''
import json, os, sys
from test_truthfulness import connected, BASE, GOOD, surfaces
with connected(sys.argv[1], os.environ["CARERELAY_API_TOKEN"]) as (client, service):
    answers = {}
    answers["hint"] = client.post(BASE + "/hint-events", json={"hint_level": "H2", "event": "shown"}).status_code
    answers["consent"] = client.post(BASE + "/consents", json={"granted": True}).status_code
    answers["restatement"] = client.post(BASE + "/restatements", json={"text": GOOD, "hint_level": "H0"}).status_code
    answers["repair"] = client.post(BASE + "/restatements/" + sys.argv[2] + "/repairs", json={"text": GOOD, "hint_level": "H0"}).status_code
    answers["action"] = client.post(BASE + "/actions", json={"route_id": "fictional_provider", "purpose_id": "handoff-test"}).status_code
    answers["new_action"] = client.post(BASE + "/actions", json={"route_id": "nurse_line", "purpose_id": "alternate"}).status_code
    answers["barrier"] = client.post(BASE + "/barriers", json={"barrier_text": "retry", "proposed_route_id": "nurse_line"}).status_code
    patient, ledger = surfaces(client)
    print(json.dumps({"answers": answers, "patient": patient, "ledger": ledger}))
'''
        result = subprocess.run([sys.executable, "-c", script, str(path), parent],
                                env=dict(os.environ, PYTHONPATH="src:tests", PYTHONDONTWRITEBYTECODE="1"),
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["answers"] == {"hint": 200, "consent": 200, "restatement": 409,
                                   "repair": 409, "action": 409, "new_action": 409, "barrier": 409}
        assert_unresolved(data["patient"], data["ledger"])
        assert data["ledger"]["axes"]["flow_stopped"] is True
        assert len(data["ledger"]["attempts"]) == 1

    @pytest.mark.parametrize("kind", ["acknowledged", "evidence"])
    def test_inflight_success_is_a_refused_receipt_after_stop(self, api, kind):
        client, _, _, _ = api
        consent(client)
        action(client)
        client.post(BASE + "/reassessments", json={})
        body = {"callback_key": "late-success"}
        if kind == "evidence":
            body["evidence"] = {"level": "self_reported", "simulated": True}
        else:
            body["transition"] = kind
        response = client.post(BASE + "/callbacks/fictional_provider", json=body)
        assert response.status_code == 200
        assert response.json()["receipt"] == "refused"
        assert response.json()["applied"] is False
        patient, ledger = surfaces(client)
        assert_unresolved(patient, ledger)
        assert ledger["callbacks"][-1]["accepted"] is False
        assert "flow stopped" in ledger["callbacks"][-1]["rejection_reason"]
        assert ledger["axes"]["evidence"] == "none"
        assert ledger["attempts"][-1]["transitions"] == []
        assert client.post(BASE + "/callbacks/fictional_provider", json=body).json()["receipt"] == "duplicate"

    def test_failure_audit_and_valid_human_transfer_remain_available(self, api):
        client, _, _, _ = api
        consent(client)
        action(client)
        client.post(BASE + "/reassessments", json={})
        response = client.post(BASE + "/callbacks/fictional_provider", json={"callback_key": "late-failure", "transition": "failed"})
        assert response.json()["receipt"] == "applied"
        assert_unresolved(*surfaces(client))
        assert client.post(BASE + "/acceptances", json={"accepted_by": "caregiver"}).status_code == 200
        patient, ledger = surfaces(client)
        assert patient["lines"][0] == "Someone has agreed to help."
        assert ledger["axes"]["flow_stopped"] is True
        assert readback(client, GOOD).status_code == 409

    def test_mcp_evidence_cannot_progress_a_stopped_plan(self, api):
        from carerelay.domain.models import EvidenceRecord, EvidenceLevel
        from carerelay.state import FlowStopped
        client, service, _, _ = api
        consent(client)
        client.post(BASE + "/reassessments", json={})
        tools = McpTools(service._store, policy=fixture.policy(), provider=ScriptedProvider())
        with pytest.raises(FlowStopped):
            tools.record_evidence(EPISODE, EvidenceRecord(EvidenceLevel.SELF_REPORTED, True, "scripted", None), now_utc=fixture.SCENARIO_NOW_UTC)
        assert surfaces(client)[1]["axes"]["evidence"] == "none"

    def test_round_zero_cannot_reset_an_unfinished_ladder(self, api):
        client, _, _, _ = api
        first = readback(client).json()
        assert readback(client, GOOD).status_code == 409
        assert readback(client, GOOD, parent=first["restatement_id"]).json()["understood"] is True
        assert surfaces(client)[1]["axes"]["flow_stopped"] is False

    def test_correct_second_repair_does_not_stop(self, api):
        client, _, _, _ = api
        first = readback(client).json()
        second = readback(client, parent=first["restatement_id"]).json()
        third = readback(client, GOOD, parent=second["restatement_id"]).json()
        assert third["understood"] is True
        assert third["routes_to_human_path"] is False
        assert surfaces(client)[1]["axes"]["flow_stopped"] is False
        consent(client)
        action(client)

    def test_authorised_new_version_reopens_without_reusing_old_keys(self, api):
        from dataclasses import replace
        from datetime import timedelta
        from carerelay.domain.models import AuthorisedReassessment, DispositionSource
        from carerelay.tools import UnknownAttemptKey
        client, service, path, token = api
        consent(client)
        opened = action(client)
        old_round = readback(client, GOOD).json()["restatement_id"]
        client.post(BASE + "/reassessments", json={})
        original = service._store.load_snapshot(EPISODE).disposition
        # Test-only authorisation, no clinical content or production branch added.
        replacement = replace(original, version=2, source=DispositionSource.REASSESSMENT,
                              clinical_deadline_utc=original.clinical_deadline_utc + timedelta(days=1))
        policy = replace(fixture.policy(), permitted_change_codes=frozenset({"test-only"}),
                         authorised_reassessments={"test-only": AuthorisedReassessment("test-only", replacement, "test-only authority")})
        service._policy = policy
        text = replace(fixture.policy_text(), deadline_display_by_version={1: "6pm today", 2: "6pm tomorrow"})
        service._policy_text = text
        response = client.post(BASE + "/reassessments", json={"confirmed_change_code": "test-only"})
        assert response.status_code == 200
        assert response.json()["disposition_version"] == 2
        with connected(path, token) as (restarted, reloaded):
            reloaded._policy = policy
            reloaded._policy_text = text
            patient, ledger = surfaces(restarted)
            assert ledger["axes"]["flow_stopped"] is False
            assert ledger["disposition_version"] == 2
            assert patient["lines"][2] == "Please do it before 6pm tomorrow."
            assert len([e for e in ledger["events"] if e["kind"] == "flow_stopped"]) == 1
            assert readback(restarted, GOOD, parent=old_round).status_code == 409
            assert restarted.post(BASE + "/actions", json={"route_id": "fictional_provider", "purpose_id": "handoff-test"}).status_code == 409
            tools = McpTools(reloaded._store, policy=policy, provider=ScriptedProvider())
            with pytest.raises(UnknownAttemptKey):
                tools.submit_simulated_request(EPISODE, "fictional_provider", opened["idempotency_key"], now_utc=fixture.SCENARIO_NOW_UTC)
            assert restarted.post(BASE + "/actions", json={"route_id": "fictional_provider", "purpose_id": "new-version-purpose"}).status_code == 200
            assert reloaded._store.list_dispositions(EPISODE)[0] == original


class TestStopRecordGuards:
    @pytest.mark.parametrize("hint,round_no", [("H3", 0), ("H0", 2)])
    def test_legacy_stop_rows_are_still_binding(self, api, hint, round_no):
        from carerelay.domain.models import HintLevel, InputMode, ExtractedPlan, PlanComparison, RecallOutcome
        client, service, _, _ = api
        # Suppress only the new audit event to model the old persisted row shape.
        original = service._store._append_event
        def legacy_event(episode, kind, payload, now):
            if kind != "flow_stopped":
                original(episode, kind, payload, now)
        service._store._append_event = legacy_event
        service._store.record_restatement(EPISODE, disposition_version=1,
            hint_level=HintLevel(hint), input_mode=InputMode.TEXT, transcript_confirmed=False,
            extracted=ExtractedPlan(None, None, None),
            comparison=PlanComparison(frozenset(), frozenset(), frozenset({"action_id"})),
            repair_round=round_no, outcome=RecallOutcome.NOT_RECALLED,
            dwell_seconds=None, now_utc=fixture.SCENARIO_NOW_UTC)
        service._store._append_event = original
        assert service._store.load_snapshot(EPISODE).flow_stop_reason == "planback_stop"
        assert readback(client, GOOD).status_code == 409

    def test_h3_stop_event_is_atomic_with_its_restatement(self, api):
        client, service, _, _ = api
        original = service._store._append_event
        def broken_audit(episode, kind, payload, now):
            if kind == "flow_stopped":
                raise RuntimeError("injected stop audit failure")
            return original(episode, kind, payload, now)
        service._store._append_event = broken_audit
        with pytest.raises(RuntimeError, match="injected stop audit failure"):
            readback(client, GOOD, hint="H3")
        service._store._append_event = original
        assert service._store.list_restatements(EPISODE) == ()
        assert service._store.load_snapshot(EPISODE).flow_stop_reason is None

    def test_reassessment_stop_is_recorded_with_version_and_fallback(self, api):
        import json
        client, _, _, _ = api
        client.post(BASE + "/reassessments", json={})
        patient, ledger = surfaces(client)
        assert_unresolved(patient, ledger)
        events = [json.loads(e["payload"]) for e in ledger["events"] if e["kind"] == "flow_stopped"]
        assert events == [{"disposition_version": 1, "reason": "reassessment_stop", "human_path": "nurse_line"}]

    def test_reassessment_stop_blocks_repair_without_rescoring(self, api):
        client, _, _, _ = api
        first = readback(client, GOOD).json()
        client.post(BASE + "/reassessments", json={})
        assert readback(client, GOOD, parent=first["restatement_id"]).status_code == 409
        assert len(surfaces(client)[1]["restatements"]) == 1

    def test_h3_mismatch_still_routes_to_human_without_a_repair_offer(self, api):
        client, _, _, _ = api
        body = readback(client, BAD, hint="H3").json()
        assert body["understood"] is False
        assert body["routes_to_human_path"] is True
        assert body["next_repair_field"] is None
