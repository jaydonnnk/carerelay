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
