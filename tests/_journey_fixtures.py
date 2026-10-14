"""Trusted local history fixtures. Never routed from patient input."""
from datetime import timedelta
import json

from carerelay.demo import fixture
from carerelay.domain.models import CallbackResult, EvidenceLevel, EvidenceRecord, ExecutionStatus, HintLevel, OperationBinding, Origin
from carerelay.journey_commands import request_digest
from carerelay.service import ScenarioClock

NOW = fixture.SCENARIO_NOW_UTC


def seed_journey(service, episode, case):
    service.ensure_episode(episode, "fictional matrix fixture")
    if case == "start": return
    service.intake(episode, fixture.BOUND_COMPLAINT)
    store = service._store
    if case in {"readback", "repair", "uncertain", "unavailable"}:
        with store.journey_transaction(episode, write=True) as tx:
            tx._event("readback_started", {"disposition_version": 1, "readback_attempt_id": "fixture-attempt"}, NOW)
        if case in {"repair", "uncertain"}:
            words = "see the doctor tomorrow before 6pm myself" if case == "repair" else "unsure"
            service.submit_restatement(episode, words, HintLevel.H1)
        if case == "unavailable":
            with store.journey_transaction(episode, write=True) as tx:
                tx._event("interpretation_unavailable", {"disposition_version": 1}, NOW)
    if case in {"barrier", "permission", "declined"}:
        service.submit_restatement(episode, "see the doctor today before 6pm myself", HintLevel.H1)
        if case != "barrier": service.record_barrier(episode, "booking", "fictional_provider")
        if case == "declined": service.change_consent(episode, granted=False)
    if case in {"waiting", "acknowledged", "failed"}:
        service.change_consent(episode, granted=True)
        action = service.open_action(episode, "fictional_provider", "matrix")
        if case != "waiting":
            status = ExecutionStatus.FAILED if case == "failed" else ExecutionStatus.ACKNOWLEDGED
            store.record_callback_once(action.attempt_id, "matrix-callback", CallbackResult(transition=status), Origin.LOCAL_SIM, now_utc=NOW)
    if case in {"handoff", "stopped_handoff", "expired_handoff"}:
        service.escalate(episode, "nurse_line", "handed_off")
    if case in {"handoff_failed", "handoff_attempted", "handoff_unknown"}:
        service.escalate(episode, "nurse_line", case.removeprefix("handoff_"))
    if case in {"accepted", "stopped_accepted", "expired_accepted"}:
        service.change_consent(episode, granted=True)
        service.record_human_acceptance(episode, "caregiver", "handoff")
    if case in {"stopped", "stopped_accepted", "stopped_handoff", "expired_stopped"}:
        store.record_flow_stop(episode, 1, "reassessment_stop", "nurse_line", now_utc=NOW)
    if case == "h3":
        service.submit_restatement(episode, "see the doctor today before 6pm myself", HintLevel.H3)
    if case in {"documented", "expired_documented"}:
        service.change_consent(episode, granted=True)
        store.record_evidence(episode, EvidenceRecord(EvidenceLevel.DOCUMENTED, False,
            "trusted repository test fixture", "fictional-fixture-receipt"), now_utc=NOW)
    if case.startswith("expired"):
        service._clock = ScenarioClock(NOW + timedelta(hours=10))
    if case == "pending":
        with store.journey_transaction(episode, write=True) as tx:
            revision = tx.load_bundle(episode).revision
            tx.claim_once(OperationBinding("fixture-pending", episode, 1, revision, "readback_started",
                "fixture:pending", request_digest("readback_started", {}), None, None), now_utc=NOW)
