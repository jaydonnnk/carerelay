"""Slice 24, demo B: the simulated provider's scripted failed reply reaches the screen by itself.

The reply is a separate keyed callback (the Slice 17 sequence is kept), origin local-sim,
no evidence, deadline, owner and closure unchanged. A replayed request records a duplicate.
"""
from __future__ import annotations

import pytest

from carerelay.domain.models import ExecutionStatus
from carerelay.service import EpisodeService
from test_journey import s17_binding, s17_understood
from test_truthfulness import make_service


def walk_to_request(service):
    ep = s17_understood(service)
    service.record_barrier_choice(s17_binding(service, ep, "select_barrier", "booking"), choice_id="booking")
    service.change_share_consent(s17_binding(service, ep, "grant_share"), granted=True)
    return ep, s17_binding(service, ep, "request")


def callbacks(service):
    return service._store._conn.execute("SELECT callback_key, result, origin FROM callbacks ORDER BY id").fetchall()


@pytest.fixture
def scripted(tmp_path):
    service = make_service(tmp_path / "scripted.sqlite")
    service._scripted_provider_reply = True
    yield service
    service._store.close()


def test_request_reaches_the_failed_screen_without_any_outside_callback(scripted):
    ep, binding = walk_to_request(scripted)
    before = scripted.project_journey(ep)
    response = scripted.request_appointment(binding)
    assert response.receipt.state == "applied"
    journey = response.journey
    assert journey.step == "unresolved" and journey.text["heading"] == "The request did not work"
    assert journey.outcome.execution is ExecutionStatus.FAILED
    rows = callbacks(scripted)
    assert len(rows) == 1 and rows[0][0].startswith("scripted-reply:")
    assert tuple(rows[0][1:]) == ("failed", "local-sim")
    snapshot = scripted._store.load_snapshot(ep)
    assert snapshot.evidence == ()
    assert snapshot.disposition.clinical_deadline_utc == scripted._store.list_dispositions(ep)[0].clinical_deadline_utc
    assert len(scripted._store.list_dispositions(ep)) == 1
    assert journey.plan == before.plan
    assert scripted.project_ledger(ep).axes["closure"] == "open"


def test_replayed_request_records_a_duplicate_not_a_second_outcome(scripted):
    ep, binding = walk_to_request(scripted)
    scripted.request_appointment(binding)
    again = scripted.request_appointment(binding)
    assert again.receipt.replayed and again.journey.step == "unresolved"
    recorded = scripted._store._conn.execute(
        "SELECT duplicate_of, accepted, rejection_reason, result FROM callbacks ORDER BY id").fetchall()
    assert [tuple(r) for r in recorded] == [(None, 1, None, "failed"), (1, 0, "duplicate", None)]
    assert len(scripted._store.list_attempts(ep)) == 1


def test_the_scripted_reply_can_only_be_failed():
    assert EpisodeService.SCRIPTED_REPLY_TRANSITION is ExecutionStatus.FAILED


def test_off_by_default_keeps_the_separate_callback_wait(tmp_path):
    service = make_service(tmp_path / "off.sqlite")
    try:
        ep, binding = walk_to_request(service)
        journey = service.request_appointment(binding).journey
        assert journey.step == "permission" and journey.text["status"] == "No reply yet."
        assert callbacks(service) == []
    finally:
        service._store.close()


@pytest.mark.parametrize("config,expected", [
    ({}, False), ({"APP_ENV": "local"}, False), ({"APP_ENV": "public"}, True), ({"APP_ENV": " Production "}, True),
    ({"APP_ENV": "public", "APP_SCRIPTED_PROVIDER_REPLY": "off"}, False),
    ({"APP_SCRIPTED_PROVIDER_REPLY": "on"}, True), ({"APP_SCRIPTED_PROVIDER_REPLY": "yes"}, False),
])
def test_wiring_is_on_only_for_public_or_explicit(config, expected):
    from carerelay.api import scripted_provider_reply
    assert scripted_provider_reply(config) is expected
