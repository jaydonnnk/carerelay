"""Isolated Slice 15 guards with valid controls and real production serializers.

MAC tests isolate cryptographic authenticity from the orthogonal shape validator.
SQL controls use existing engine tests that remove only the matching-claim trigger.
No synthetic helper response is mutation evidence here.
"""
import base64
import copy
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from carerelay.demo import fixture
from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import PURPOSES, canonical, issue_operation, request_digest, verify_operation, CommandInvalid
from carerelay.presentation import journey_surface
from test_truthfulness import make_service
from _journey_fixtures import seed_journey

ROOT = Path(__file__).resolve().parents[1]
KEY = b"synthetic-mutation-control"
MAC_BAD = {
    "operation_id": "other-operation", "episode_id": "other-episode",
    "disposition_version": 1, "expected_revision": 1, "kind": "select_example",
    "purpose": "episode:select_example", "body_sha256": "f" * 64,
    "parent_restatement_id": "other-parent", "confirmation_id": "other-confirmation",
    "token_schema": "other-schema",
}


def mac_binding():
    return OperationBinding("mutation-create", "mutation-episode", None, 0, "create",
        PURPOSES["create"], request_digest("create", {}), None, None)


@pytest.mark.parametrize("dimension", MAC_BAD)
def test_mac_dimension_without_shape_overlap(monkeypatch, dimension):
    import carerelay.journey_commands as codec
    binding = mac_binding()
    token = issue_operation(binding, signing_key=KEY)
    # This test measures MAC authenticity alone. Shape has its own tests.
    monkeypatch.setattr(codec, "validate_binding", lambda binding: None)
    assert verify_operation(token, signing_key=KEY) == binding
    encoded, signature = token.split(".")
    body = asdict(binding)
    body[dimension] = MAC_BAD[dimension]
    changed = base64.urlsafe_b64encode(canonical(body)).rstrip(b"=").decode()
    assert changed != encoded
    with pytest.raises(CommandInvalid):
        verify_operation(changed + "." + signature, signing_key=KEY)


# Each tuple contains the trusted screen, one independently malformed wire field,
# and its value. Coupled aliases are updated together when testing a semantic rule.
DECODER_BAD = {
    "root_keys": ("plan", "extra", True),
    "schema": ("plan", "schema_version", "unknown"),
    "identity": ("plan", "episode_id", "other-episode"),
    "revision_negative": ("plan", "revision", -1),
    "revision_unsafe": ("plan", "revision", 9007199254740992),
    "timestamp_format": ("plan", "as_of_utc", "not-time"),
    "timestamp_calendar": ("plan", "as_of_utc", "2026-02-30T00:00:00+00:00"),
    "clock": ("plan", "clock_mode", "browser"),
    "simulation": ("plan", "simulated", False),
    "label": ("plan", "fixture_label", "unknown"),
    "flow_keys": ("plan", "flow.extra", True),
    "stop_type": ("plan", "flow.stopped", 0),
    "visible_type": ("plan", "flow.card_visible", 0),
    "repair_integer": ("plan", "flow.completed_repairs", 1.5),
    "repair_negative": ("plan", "flow.completed_repairs", -1),
    "repair_cap": ("plan", "flow.completed_repairs", 3),
    "hint_enum": ("plan", "flow.effective_hint", "H9"),
    "interpretation_enum": ("plan", "flow.interpretation", "unknown"),
    "repair_field_enum": ("plan", "flow.selected_repair_field", "invented"),
    "execution_enum": ("plan", "outcome.execution", "unknown"),
    "evidence_enum": ("plan", "outcome.evidence", "unknown"),
    "outcome_keys": ("plan", "outcome.extra", True),
    "execution_alias": ("plan", "execution", "failed"),
    "evidence_alias": ("plan", "evidence", "self_reported"),
    "closure_alias": ("plan", "closure", "closed_with_evidence"),
    "care_alias": ("plan", "outcome.care_evidenced", True),
    "stop_version": ("stopped", "flow.stopped_disposition_version", 2),
    "stop_reason": ("stopped", "flow.stop_reason", None),
    "plan_version": ("plan", "plan.disposition_version", 2),
    "plan_policy": ("plan", "plan.policy_version", "unknown"),
    "plan_timezone": ("plan", "plan.display_timezone", "UTC"),
    "plan_deadline": ("plan", "plan.deadline_utc", "not-time"),
    "plan_keys": ("plan", "plan.extra", True),
    "owner_pair": ("plan", "plan.current_owner_display", None),
    "owner_alias": ("plan", "action_owner_id", "caregiver"),
    "question_id": ("readback", "question.question_id", "permission"),
    "question_extra": ("readback", "question.extra", True),
    "question_text": ("readback", "question.text", ""),
    "readback_choice": ("readback", "question.choices", [{"choice_id": "booking", "text": "Booking"}]),
    "barrier_choices": ("barrier", "question.choices", [{"choice_id": "booking", "text": "Booking"}]),
    "missing_question": ("readback", "question", None),
    "redacted_owner": ("readback", "outcome.escalation_path", "nurse_line"),
    "readback_identity": ("readback", "flow.readback_attempt_id", None),
    "stopped_open": ("plan", "flow.stopped", True),
    "h3_stop": ("plan", "flow.effective_hint", "H3"),
    "sticky_expiry": ("plan", "outcome.expiry_recorded", True),
    "open_owner": ("plan", "plan.current_owner_id", "caregiver"),
    "text_keys": ("plan", "text.extra", "unexpected answer"),
    "text_labels": ("plan", "text.deadline_label", None),
    "unresolved_failure": ("plan", "step", "unresolved"),
}
for field in ["action_id", "action_text", "deadline_display", "original_owner_id", "original_owner_display", "fallback_route_id", "fallback_display"]:
    DECODER_BAD["plan_" + field] = ("documented" if field == "original_owner_id" else "plan", "plan." + field, "")
for field in ["accepted_by", "accepted_scope", "escalation_path", "escalation_outcome"]:
    DECODER_BAD["outcome_" + field] = ("plan", "outcome." + field, 1)
for field in ["stop_reason", "readback_attempt_id", "latest_restatement_id", "selected_repair_field"]:
    DECODER_BAD["flow_" + field] = ("plan", "flow." + field, 1)


@pytest.mark.parametrize("case", DECODER_BAD)
def test_decoder_independent_invariant(tmp_path, case):
    screen, path, value = DECODER_BAD[case]
    service = make_service(tmp_path / "decoder-mutant.sqlite")
    try:
        seed_journey(service, "mutation-decoder", screen)
        good = journey_surface(service.project_journey("mutation-decoder"))
    finally:
        service._store.close()
    bad = copy.deepcopy(good)
    parts = path.split(".")
    target = bad
    for key in parts[:-1]:
        target = target[key]
    if case == "text_labels":
        del target[parts[-1]]
    else:
        target[parts[-1]] = value
    if case in {"execution_enum", "evidence_enum"}:
        bad[parts[-1]] = value
    if case == "stopped_open":
        bad["flow"].update(stop_reason="fictional-stop", stopped_disposition_version=1)
    if case == "open_owner":
        bad["plan"]["current_owner_display"] = "Caregiver"
        bad["action_owner_id"] = "caregiver"
    if case in {"execution_enum", "unresolved_failure", "outcome_escalation_path"}:
        bad["commands"] = [o for o in bad["commands"] if o["kind"] != "readback_started"]
        bad["text"].pop("readback_label", None)
    if case == "unresolved_failure":
        bad["text"] = {"heading": "That request did not work", "show_label": "Show my plan", "hide_label": "Back to my answer"}
    script = f'''import {{decodeJourney}} from {json.dumps((ROOT / "frontend/lib/journey.ts").as_uri())};
import {{readFileSync}} from "node:fs";
const [good,bad]=JSON.parse(readFileSync(0,"utf8"));
let rejected; try {{ rejected=decodeJourney(bad,good.episode_id)===null; }} catch {{ rejected="threw"; }}
console.log(JSON.stringify([decodeJourney(good,good.episode_id)!==null,rejected]));'''
    child = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps([good, bad]), capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == [True, True]


def test_unclaimed_intake_digest_is_not_masked_by_replay(tmp_path):
    from dataclasses import replace
    from carerelay.journey_commands import CommandConflict
    from test_journey_commands import command_service, s15_binding, selected_binding
    service = command_service(tmp_path / "digest.sqlite")
    try:
        service.start_example(s15_binding())
        binding = selected_binding(service)
        before = list(service._store._conn.iterdump())
        with pytest.raises(CommandConflict):
            service.select_example(replace(binding, body_sha256="f" * 64), example_id="scripted-appointment")
        assert list(service._store._conn.iterdump()) == before
        assert service.select_example(binding, example_id="scripted-appointment").receipt.state == "applied"
    finally:
        service._store.close()


@pytest.mark.parametrize("dimension", ["episode_id", "disposition_version", "expected_revision", "kind", "purpose", "body_sha256", "parent_restatement_id", "confirmation_id"])
def test_replayed_binding_dimension(tmp_path, dimension):
    from dataclasses import replace
    from carerelay.journey_commands import CommandConflict
    from test_journey_commands import command_service, s15_binding
    service = command_service(tmp_path / "binding.sqlite")
    binding = s15_binding()
    try:
        service.start_example(binding)
        changed = replace(binding, **{dimension: MAC_BAD[dimension]})
        with service._store.journey_transaction(binding.episode_id, write=False) as tx:
            assert tx.find(binding).state == "applied"
            with pytest.raises(CommandConflict):
                tx.find(changed)
    finally:
        service._store.close()


def test_intake_replay_does_not_reenter_stale_offer_check(tmp_path):
    from carerelay.journey_commands import CommandConflict
    from test_journey_commands import command_service, s15_binding, selected_binding
    service = command_service(tmp_path / "replay.sqlite")
    try:
        create = s15_binding()
        service.start_example(create)
        intake = selected_binding(service)
        first = service.select_example(intake, example_id="scripted-appointment")
        service._store.record_flow_stop(create.episode_id, 1, "reassessment_stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
        error = None
        try:
            replay = service.select_example(intake, example_id="scripted-appointment")
        except CommandConflict as caught:
            error = str(caught)
        assert error is None, f"An exact committed replay was rejected: {error}"
        assert replay.receipt.replayed and replay.journey.flow.stopped
        assert replay.journey.revision > first.journey.revision
    finally:
        service._store.close()


@pytest.mark.parametrize("call", ["load_snapshot", "load_bundle"])
def test_corrupt_reader_error_maps_to_typed_recovery(tmp_path, monkeypatch, call):
    from carerelay.state import InvalidJourneyRecord
    service = make_service(tmp_path / "typed-recovery.sqlite")
    service.ensure_episode("mutation-error", "fictional")
    try:
        with service._store.journey_transaction("mutation-error", write=False) as tx:
            assert tx.load_snapshot("mutation-error").disposition is None
            assert tx.load_bundle("mutation-error").episode_id == "mutation-error"
            def corrupt(*args):
                raise ValueError("controlled malformed stored field")
            monkeypatch.setattr(service._store if call == "load_snapshot" else tx,
                "load_snapshot" if call == "load_snapshot" else "_load_bundle", corrupt)
            observed = None
            try:
                getattr(tx, call)("mutation-error")
            except (ValueError, InvalidJourneyRecord) as caught:
                observed = type(caught)
            assert observed is InvalidJourneyRecord
    finally:
        service._store.close()


@pytest.mark.parametrize("case", ["missing", "duplicate", "foreign"])
def test_event_reference_guard_is_typed_before_order_lookup(case):
    from carerelay.state import _order_by_events, InvalidJourneyRecord
    rows = [{"id": "present"}]
    valid = [("escalation_recorded", json.dumps({"schema": "record-v1", "record_id": "present"}), fixture.SCENARIO_NOW_UTC)]
    assert _order_by_events(rows, valid, "escalation_recorded") == tuple(rows)
    payload = {"schema": "record-v1"}
    if case == "duplicate": payload["record_id"] = "present"
    if case == "foreign": payload["record_id"] = "foreign"
    events = valid + [("escalation_recorded", json.dumps(payload), fixture.SCENARIO_NOW_UTC)]
    observed = None
    try:
        _order_by_events(rows, events, "escalation_recorded")
    except (InvalidJourneyRecord, KeyError) as caught:
        observed = type(caught)
    assert observed is InvalidJourneyRecord


def test_comparison_overlap_with_consistent_recall_outcome(tmp_path):
    from dataclasses import replace
    from carerelay.domain.models import PlanComparison, RecallOutcome
    from carerelay.domain.rules import JourneyUnavailable, derive_journey
    service = make_service(tmp_path / "partition.sqlite")
    try:
        seed_journey(service, "mutation-partition", "barrier")
        bundle = service._store.load_journey_bundle("mutation-partition")
        assert derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC).step == "barrier"
        row = replace(bundle.restatements[-1],
            comparison=PlanComparison(frozenset({"action_id", "deadline_utc", "next_owner_id"}), frozenset(), frozenset({"action_id"})),
            outcome=RecallOutcome.NOT_RECALLED)
        with pytest.raises(JourneyUnavailable, match="overlapping"):
            derive_journey(replace(bundle, restatements=(row,)), now_utc=fixture.SCENARIO_NOW_UTC)
    finally:
        service._store.close()


def test_phase_enum_without_lifecycle_check(tmp_path, monkeypatch):
    import sqlite3
    import carerelay.state as state
    shape = """CHECK ((phase = 'claimed' AND terminal_state IS NULL AND result_kind IS NULL
            AND result_ref IS NULL AND scored = 0)
        OR (phase = 'completed' AND terminal_state IS NOT NULL)),"""
    assert state._SCHEMA_SQL.count(shape) == 1
    # Phase membership is independent of the lifecycle/terminal shape constraint.
    monkeypatch.setattr(state, "_SCHEMA_SQL", state._SCHEMA_SQL.replace(shape, "CHECK (1),"))
    with state.SqliteEpisodeStore(tmp_path / "phase-enum.sqlite") as store:
        store.create_episode("phase-control", "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        store._conn.execute("DROP TRIGGER journey_commands_claim_binding")
        row = dict(operation_id="phase-operation", episode_id="phase-control", phase="wrong",
            expected_revision=0, claim_revision=0, kind="create", purpose="episode:create",
            body_sha256="a" * 64, scored=0, recorded_at=fixture.SCENARIO_NOW_UTC.isoformat())
        sql = "INSERT INTO journey_commands(" + ",".join(row) + ") VALUES(" + ",".join("?" for _ in row) + ")"
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            store._conn.execute(sql, tuple(row.values()))
        row["phase"] = "claimed"
        store._conn.execute(sql, tuple(row.values()))
        assert store._conn.execute("SELECT phase FROM journey_commands").fetchone()[0] == "claimed"


def test_claim_parent_with_valid_foreign_row(tmp_path):
    from dataclasses import replace
    from carerelay.journey_commands import CommandConflict
    from test_journey_commands import command_service, s15_binding, selected_binding
    service = command_service(tmp_path / "valid-parent.sqlite")
    try:
        service.start_example(s15_binding())
        seed_journey(service, "other-parent-episode", "barrier")
        parent = service._store.list_restatements("other-parent-episode")[-1].restatement_id
        binding = selected_binding(service)
        before = list(service._store._conn.iterdump())
        with pytest.raises(CommandConflict):
            service.select_example(replace(binding, parent_restatement_id=parent), example_id="scripted-appointment")
        assert list(service._store._conn.iterdump()) == before
        assert service.select_example(binding, example_id="scripted-appointment").receipt.state == "applied"
    finally:
        service._store.close()


@pytest.mark.parametrize("case", ["acknowledged", "handoff_unknown"])
def test_neutral_contact_wins_over_understood_round(tmp_path, case):
    service = make_service(tmp_path / "neutral-contact.sqlite")
    try:
        seed_journey(service, "neutral-control", "barrier")
        assert service.project_journey("neutral-control").step == "barrier"
        if case == "acknowledged":
            service.change_consent("neutral-control", True)
            opened = service.open_action("neutral-control", "fictional_provider", "neutral-control")
            from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
            service._store.record_callback_once(opened.attempt_id, "neutral-ack", CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED), Origin.LOCAL_SIM, now_utc=fixture.SCENARIO_NOW_UTC)
        else:
            service.escalate("neutral-control", "nurse_line", "unknown")
        body = journey_surface(service.project_journey("neutral-control"))
        assert body["step"] == "plan"
        assert body["closure"] == "open" and body["action_owner_id"] == "patient"
        assert body["lines"][0] == "No one has agreed to help yet."
        assert body["care_evidenced"] is False
    finally:
        service._store.close()
