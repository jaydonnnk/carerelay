"""Slice 11: the fault harness. Seven sequences, each proved against its guard.

`04-slices.md` names the seven: timeout, stale availability, duplicate callback,
reordered callback, restart mid-episode, clock change and consent revocation.
Each one drives the running product into a fault through the public API, then
asserts at the serialized surfaces whichever of the five invariants that fault
can falsify. **The coverage is per sequence, not uniform, and is stated rather
than averaged:** I2 and I4 hold in all seven, because the approved tuple below
is asserted by equality; I3 in three (timeout, duplicate, restart); I5 in three
(timeout, stale, consent); and I1's stored-instant half in two (timeout, clock),
its deadline-wording half riding on line 3 of the same tuple. The five are:

* I1, the deadline: the approved line 3 wording carries it, and the stored
  instant is never derived from a later clock read.
* I2, no false completion: the four lines are asserted **equal** to the
  approved rendering for the state the episode is in, so a surface that
  drifted into "Help is arranged." or "It is set for ..." fails by comparison,
  not by a substring check that could be softened.
* I3, idempotency: a repeated delivery is a duplicate, a replayed callback
  after a restart is a duplicate, and no fault path appends a second outcome.
* I4, a named owner or a visible lack of one: the approved unresolved copy
  names the acting party, the expired copy names the route, and the line 1
  statement that no one has agreed yet is part of the exact tuple.
* I5, missing is not negative: a dropped callback leaves the attempt reading
  `attempted`, never `failed`, and a refused callback leaves it exactly as it
  was.

**The hard requirement, and where it is discharged.** Each sequence must
violate at least one targeted assertion when its guard is independently
disabled. `tests/_mutate_slice11.py` performs that: one mutation per sequence,
against the guard named in each class docstring, with the selector pinned to
that class. The Check for this slice is those seven REDs shown to the user
before the suite is declared green.

**The world.** One file-backed store per test, because a restart has to be a
real restart: the crash sequence runs a **child process** that dies inside the
write, and the parent then reads what survived. `MutableClock` is the only
clock; nothing here reads the wall clock.

**A stated limit, not a hidden one.** "Stale availability" is read as the
execution-time recheck that exists in this build: the route permission the
policy carries, re-validated at the tool at the moment of dispatch and
recorded on refusal. The build has no availability table and no observation
age (the Slice 9 review recorded that absence), so this sequence proves what
the code can support, in place of what the phrase might picture. The reading
is repeated in `00-status.md` rather than left to be inferred from the name.

**The mutation map** (sequence, guard, how it is disabled):

1. `TestTimeoutSequence` - `rules.project_attempt`'s empty branch -> returns
   `failed` for no transitions.
2. `TestStaleAvailabilitySequence` - `tools` route recheck -> `validate_route`
   skipped.
3. `TestDuplicateCallbackSequence` - `state` callback-key lookup -> the
   duplicate branch never fires (the `UNIQUE` constraint then fails the insert,
   which is the second line of defence and still a RED).
4. `TestReorderedCallbackSequence` - `project_attempt` ordering -> `ordered[-1]`
   wins instead of `ordered[0]`.
5. `TestRestartMidEpisodeSequence` - the single `BEGIN IMMEDIATE` in
   `record_callback_once` -> the receipt commits in its own transaction before
   the transition.
6. `TestClockChangeSequence` - `derive_closure` expiry stickiness -> the
   `expiry_event_id` clause dropped.
7. `TestConsentRevocationSequence` - `record_callback_once`'s
   `_consent_rejection_reason` call -> the reason is forced to `None`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.api import app, get_service  # noqa: E402
from carerelay.coordinator import LocalSimulationCoordinator  # noqa: E402
from carerelay.demo import fixture  # noqa: E402
from carerelay.domain.models import ExecutionStatus, PolicyFixture  # noqa: E402
from carerelay.service import EpisodeService  # noqa: E402
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.state import SqliteEpisodeStore, open_store  # noqa: E402
from carerelay.tools import McpTools, RouteNotPermitted  # noqa: E402

from test_boundaries import (  # noqa: E402
    scan_for_facility_names,
    scan_for_secrets,
    scan_for_unlabelled_receipts,
)

EPISODE = fixture.DEMO_EPISODE_ID
ROUTE = "fictional_provider"
PURPOSE = "book_transport"
SRC = str(Path(__file__).resolve().parents[1] / "src")

#: The fixture deadline anchored to the scenario instant: 18:00 SGT, 10:00 UTC.
DEADLINE_UTC = fixture.deadline_utc(fixture.SCENARIO_NOW_UTC)

#: The approved rendering while the episode is open and unevidenced.
#: Quoted from `02-architecture.md` section 7. The apostrophes and the period
#: are part of the approved copy; only the evaluator escapes the apostrophe.
UNRESOLVED_LINES = (
    "No one has agreed to help yet.",
    "Please act now.",
    "Please do it before 6pm today.",
    "If that does not work, call the fictional nurse line.",
)

#: The approved rendering after the deadline passed with nothing to show.
EXPIRED_LINES = (
    "No one has agreed to help yet.",
    "You can still do this.",
    "It is past 6pm today. Please go now.",
    "Call the fictional nurse line. They can help from here.",
)

#: Run in a child process, which is what a restart is. The patch dies inside
#: `_append_transition`, after the receipt row has been written but before the
#: transition is, so the only thing that can save the ledger is the fact that
#: both live in one transaction. `flush=True` on the reach marker is what makes
#: "we got there" provable even though the process never returns.
_CRASH_ON_TRANSITION = r"""
import os
import signal
import sys

sys.path.insert(0, sys.argv[1])
from datetime import datetime, timezone

from carerelay import state
from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin


def _die(*_args, **_kwargs):
    print("reached _append_transition", flush=True)
    os.kill(os.getpid(), signal.SIGTERM)


state.SqliteEpisodeStore._append_transition = _die

store = state.open_store(sys.argv[2], check_same_thread=False)
store.record_callback_once(
    sys.argv[3],
    sys.argv[4],
    CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED, payload="crash probe"),
    Origin.LOCAL_SIM,
    now_utc=datetime(2026, 9, 30, 1, 30, tzinfo=timezone.utc),
)
print("completed", flush=True)
"""

#: A fresh interpreter that opens the same file and reports what it can derive.
#: Nothing is passed between the processes but the path and the episode id.
_REOPEN_REPORT = r"""
import json
import sys

sys.path.insert(0, sys.argv[1])
from datetime import timedelta

from carerelay import state

store = state.open_store(sys.argv[2], check_same_thread=False)
episode = sys.argv[3]
snapshot = store.load_snapshot(episode)
attempt = snapshot.attempt
before_the_deadline = snapshot.disposition.clinical_deadline_utc - timedelta(minutes=1)
report = {
    "execution": attempt.execution.value,
    "transitions": len(store.list_transitions(attempt.attempt_id)),
    "callbacks": len(store.list_callbacks(episode)),
    "closure": store.derive_closure(episode, before_the_deadline).closure.value,
}
store.close()
print(json.dumps(report))
"""


class MutableClock:
    """The harness clock. The sequence moves time; nothing else can."""

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now_utc(self) -> datetime:
        return self._instant

    def set(self, instant: datetime) -> None:
        self._instant = instant


@dataclass(frozen=True)
class FaultWorld:
    """One file-backed world, so a restart can actually happen to it."""

    path: Path
    store: SqliteEpisodeStore
    service: EpisodeService
    clock: MutableClock
    client: TestClient


def _install(
    path: Path, *, tools_policy: PolicyFixture | None = None
) -> FaultWorld:
    """Build the store, the tool surface and the service over one file.

    `tools_policy` exists for one sequence only: the stale-availability world
    gives the tools a policy the plan was not made under, which is what the
    execution-time recheck is there to catch. Every other world builds both
    layers from the same fixture.
    """
    store = open_store(path, check_same_thread=False)
    clock = MutableClock(fixture.SCENARIO_NOW_UTC)
    tools = McpTools(
        store,
        policy=tools_policy if tools_policy is not None else fixture.policy(),
        provider=ScriptedProvider(),
    )
    service = EpisodeService(
        store,
        coordinator=LocalSimulationCoordinator(tools),
        clock=clock,
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        policy_provenance="test: provisional",
    )
    app.dependency_overrides[get_service] = lambda: service
    return FaultWorld(
        path=path,
        store=store,
        service=service,
        clock=clock,
        client=TestClient(app),
    )


def _uninstall(world: FaultWorld) -> None:
    app.dependency_overrides.clear()
    world.store.close()


@pytest.fixture()
def world(tmp_path: Path) -> Iterator[FaultWorld]:
    world = _install(tmp_path / "fault.sqlite3")
    try:
        yield world
    finally:
        _uninstall(world)


@pytest.fixture()
def stale_world(tmp_path: Path) -> Iterator[FaultWorld]:
    """A world whose tools no longer permit `ROUTE`.

    The service still plans under the fixture policy, which is the shape of an
    in-flight withdrawal: the plan was made when the route was permitted, and
    the execution-time recheck is the last gate that can still stop it.
    """
    narrow = replace(
        fixture.policy(),
        permitted_route_ids=frozenset({fixture.FALLBACK_ROUTE_ID}),
    )
    world = _install(tmp_path / "stale.sqlite3", tools_policy=narrow)
    try:
        yield world
    finally:
        _uninstall(world)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assess(world: FaultWorld) -> None:
    created = world.client.post("/api/episodes")
    assert created.status_code == 200, created.text
    response = world.client.post(
        f"/api/episodes/{EPISODE}/intake",
        json={"confirmed_text": fixture.BOUND_COMPLAINT},
    )
    assert response.status_code == 200, response.text


def _grant(world: FaultWorld) -> int:
    response = world.client.post(
        f"/api/episodes/{EPISODE}/consents", json={"granted": True}
    )
    assert response.status_code == 200, response.text
    return response.json()["version"]


def _dispatch(world: FaultWorld, route: str = ROUTE, purpose: str = PURPOSE):
    response = world.client.post(
        f"/api/episodes/{EPISODE}/actions",
        json={"route_id": route, "purpose_id": purpose},
    )
    assert response.status_code == 200, response.text
    return response


def _callback(world: FaultWorld, key: str, transition: str):
    response = world.client.post(
        f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
        json={"callback_key": key, "transition": transition, "payload": "fault-probe"},
    )
    assert response.status_code == 200, response.text
    return response


def _run_child(program: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", program, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def _reopen_report(world: FaultWorld) -> dict:
    completed = _run_child(_REOPEN_REPORT, SRC, str(world.path), EPISODE)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _assert_healthy_surface(
    world: FaultWorld,
    expected_lines: tuple[str, ...],
    expected_closure: str,
) -> None:
    """Assert the serialized patient truth at the moment of the fault.

    The lines are asserted **equal** to the approved tuple for the state, so
    I2 is proved by comparison: any rendering that claimed completion would
    not equal these strings. I4 rides on the same tuples (the unresolved copy
    names the acting party; a line 1 that dropped the "no one has agreed yet"
    statement would not match), and I1 rides on line 3, which carries the
    approved deadline wording.

    Both serialized surfaces are scanned with the boundary scanners. The
    scanner self-test lives in `tests/test_boundaries.py`
    (`test_scanner_detects_injected_needle`): a negative scan without it is
    not evidence.

    **Only the JSON projection is content-asserted.** The page at `/` is the
    Slice 1 tracer bullet: it renders `fixture.demo_lines()` and never reads
    its `episode_id`, so it is a constant and the harness asserts `200` plus
    the scanners on it. That limit is recorded in the Slice 11 section of
    `00-status.md` rather than papered over here.
    """
    projected = world.client.get(f"/api/episodes/{EPISODE}")
    assert projected.status_code == 200, projected.text
    body = projected.json()
    assert tuple(body["lines"]) == expected_lines
    assert body["closure"] == expected_closure
    assert body["care_evidenced"] is False
    assert body["simulated"] is True
    assert body["fixture_label"] == fixture.FIXTURE_LABEL

    page = world.client.get("/")
    assert page.status_code == 200

    for scanner in (
        scan_for_secrets,
        scan_for_facility_names,
        scan_for_unlabelled_receipts,
    ):
        assert scanner(projected.text) == [], (
            f"{scanner.__name__} fired on the serialized projection"
        )
        assert scanner(page.text) == [], f"{scanner.__name__} fired on the page"


# ---------------------------------------------------------------------------
# 1. Timeout
# ---------------------------------------------------------------------------


class TestTimeoutSequence:
    """Fault: the outcome never arrives on the callback path.

    Guard under test: `rules.project_attempt`'s empty-transition branch, which
    reports `attempted` for an attempt with no recorded terminal outcome.
    Disabled (returning `failed` from that branch), this class must go red:
    a missing outcome would be reported as a negative one (I5), which is what
    `02-architecture.md` section 4.1 forbids.
    """

    def test_a_dropped_outcome_leaves_the_attempt_in_flight(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        first = _dispatch(world)
        opened = first.json()

        # The tool answered, and the response carries that answer...
        assert opened["outcome"] == "failed"
        assert opened["provider_ref"]
        assert opened["origin"] == "local-sim"
        # ...but no transition was recorded, because the callback never came.
        assert len(world.store.list_transitions(opened["attempt_id"])) == 0

        # I5: the record says in-flight, not failed. A dropped callback is
        # missing information, and missing is not negative.
        assert opened["execution"] == "attempted"
        duplicate = _dispatch(world).json()
        assert duplicate["duplicate"] is True
        assert duplicate["execution"] == "attempted"
        assert duplicate["outcome"] is None

        # The one response that does carry a provider reference also carries
        # the simulated label, so the receipt scanner reads both.
        assert scan_for_unlabelled_receipts(first.text) == []
        assert scan_for_secrets(first.text) == []

        # I2: the patient surface has gained nothing from the silence.
        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")

    def test_the_late_outcome_is_recorded_and_still_resolves_nothing(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        opened = _dispatch(world).json()
        late = _callback(world, "cb-late-1", "failed").json()
        assert late["receipt"] == "applied"
        assert late["execution"] == "failed"

        transitions = world.store.list_transitions(opened["attempt_id"])
        assert len(transitions) == 1
        # I1: a failed action does not move the clinical deadline.
        snapshot = world.store.load_snapshot(EPISODE)
        assert snapshot.disposition.clinical_deadline_utc == DEADLINE_UTC
        # I2: a recorded failure is not completion; the plan stays unresolved
        # with the fallback route named.
        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")


# ---------------------------------------------------------------------------
# 2. Stale availability
# ---------------------------------------------------------------------------


class TestStaleAvailabilitySequence:
    """Fault: the route is permitted when the plan is made, withdrawn at dispatch.

    Guard under test: the execution-time recheck in
    `tools.McpTools.submit_simulated_request`, which re-validates the route
    against the policy at the moment of dispatch and records the refusal
    before raising. Disabled (`validate_route` skipped), the refused dispatch
    silently proceeds and this class must go red: `RouteNotPermitted` is no
    longer raised and the ledger carries no refusal.

    The reading of "stale availability" is stated in the module docstring: the
    thing that can be stale and rechecked in this build is the route
    permission, and the refusal event recorded here is the evidence surface
    the Slice 9 review found missing for this fault.
    """

    def test_a_withdrawn_route_is_refused_at_dispatch_and_recorded(
        self, stale_world: FaultWorld
    ) -> None:
        _assess(stale_world)
        _grant(stale_world)
        with pytest.raises(RouteNotPermitted):
            stale_world.service.open_action(EPISODE, ROUTE, PURPOSE)

        # The attempt was opened before the tool refused: an episode mid-flight.
        attempts = stale_world.store.list_attempts(EPISODE)
        assert len(attempts) == 1
        attempt = attempts[0]
        assert attempt.route_id == ROUTE
        # I5: no outcome arrived, so the attempt reads in-flight, not failed.
        assert attempt.execution is ExecutionStatus.ATTEMPTED
        assert stale_world.store.list_transitions(attempt.attempt_id) == ()

        # A refusal is recorded, not only raised.
        refused = [
            payload
            for kind, payload, _ in stale_world.store.list_events(EPISODE)
            if kind == "refused"
        ]
        assert refused, "the refused dispatch left no evidence in the ledger"
        assert ROUTE in refused[0]
        assert "submit_simulated_request" in refused[0]

        # The provider was never reached, and a callback was never received.
        assert stale_world.store.list_callbacks(EPISODE) == ()
        # I1, I2, I4: the patient surface has gained nothing from the refusal.
        _assert_healthy_surface(stale_world, UNRESOLVED_LINES, "open")

    def test_the_same_world_still_dispatches_a_permitted_route(
        self, stale_world: FaultWorld
    ) -> None:
        """The control: the refusal is about the route, not a broken world."""
        _assess(stale_world)
        _grant(stale_world)
        with pytest.raises(RouteNotPermitted):
            stale_world.service.open_action(EPISODE, ROUTE, PURPOSE)
        # A different purpose id is an explicit authorised retry (D5), so the
        # duplicate suppression does not stand in this dispatch's way.
        control = stale_world.service.open_action(
            EPISODE, fixture.FALLBACK_ROUTE_ID, "call_fallback"
        )
        assert control.duplicate is False
        assert control.tool is not None
        assert control.tool.provider_ref
        assert control.origin.value == "local-sim"


# ---------------------------------------------------------------------------
# 3. Duplicate callback
# ---------------------------------------------------------------------------


class TestDuplicateCallbackSequence:
    """Fault: the same callback is delivered twice.

    Guard under test: the callback-key lookup in
    `state.SqliteEpisodeStore.record_callback_once`. Disabled (the duplicate
    branch never fires), the second delivery is applied again: two
    `callback_applied` events and a receipt that says `applied`, and this
    class goes red on the receipt. The `UNIQUE` constraint on
    `callbacks.callback_key` is the second line of defence under that
    mutation, and its violation is also a RED.
    """

    def test_a_replayed_callback_is_recorded_but_not_reapplied(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        opened = _dispatch(world).json()
        first = _callback(world, "cb-dup-1", "acknowledged").json()
        assert first["receipt"] == "applied"
        assert first["applied"] is True

        again = _callback(world, "cb-dup-1", "acknowledged").json()
        # I3: the second delivery is recorded as a duplicate and applies
        # nothing. "Duplicate, correctly ignored" and "applied" are different
        # facts and must not share a representation (O5).
        assert again["receipt"] == "duplicate"
        assert again["applied"] is False
        assert again["execution"] == "acknowledged"

        transitions = world.store.list_transitions(opened["attempt_id"])
        assert len(transitions) == 1
        receipts = world.store.list_callbacks(EPISODE)
        assert [row.accepted for row in receipts] == [True, False]
        assert receipts[1].duplicate_of == receipts[0].receipt_id
        kinds = [kind for kind, _, _ in world.store.list_events(EPISODE)]
        assert kinds.count("callback_applied") == 1
        assert kinds.count("callback_duplicate") == 1

        # I2: an acknowledgement is a promise, not evidence, so the exact
        # unresolved rendering must still be what the patient sees.
        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")


# ---------------------------------------------------------------------------
# 4. Reordered callback
# ---------------------------------------------------------------------------


class TestReorderedCallbackSequence:
    """Fault: a late acknowledgement arrives after a recorded failure.

    Guard under test: `project_attempt`'s ordering rule, the first terminal
    transition in `seq` order. Disabled (taking `ordered[-1]` instead of
    `ordered[0]`), the late acknowledgement becomes the reported outcome and
    this class goes red on the reordered read. The late row is retained and
    non-winning; absorbing means the failure stands.
    """

    def test_a_late_acknowledgement_cannot_override_a_recorded_failure(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        opened = _dispatch(world).json()
        failed = _callback(world, "cb-fail-1", "failed").json()
        assert failed["receipt"] == "applied"
        assert failed["execution"] == "failed"

        late = _callback(world, "cb-ack-1", "acknowledged").json()
        assert late["receipt"] == "applied"
        # Retained and non-winning: the first terminal in arrival order stands.
        assert late["execution"] == "failed"

        transitions = world.store.list_transitions(opened["attempt_id"])
        assert [row.kind for row in transitions] == [
            ExecutionStatus.FAILED,
            ExecutionStatus.ACKNOWLEDGED,
        ]

        # I2: neither the failure nor the late promise resolves anything.
        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")


# ---------------------------------------------------------------------------
# 5. Restart mid-episode
# ---------------------------------------------------------------------------


class TestRestartMidEpisodeSequence:
    """Fault: the process dies mid-episode.

    Guard under test: the single `BEGIN IMMEDIATE` transaction in
    `record_callback_once`, which holds the receipt row and its transition
    together. Disabled (the receipt commits in its own transaction before the
    transition), a crash between the two leaves a receipt with no transition
    and this class goes red: the ledger would be able to show an outcome that
    was never applied.
    """

    def test_a_crash_between_receipt_and_transition_leaves_neither(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        attempt_id = _dispatch(world).json()["attempt_id"]

        completed = _run_child(
            _CRASH_ON_TRANSITION, SRC, str(world.path), attempt_id, "cb-crash-1"
        )
        # The child reached the dying function, and did not come back.
        assert "reached _append_transition" in completed.stdout, completed.stderr
        assert "completed" not in completed.stdout
        assert completed.returncode != 0

        # A crash between the two writes is not a representable state.
        assert world.store.list_callbacks(EPISODE) == ()
        assert world.store.list_transitions(attempt_id) == ()
        kinds = [kind for kind, _, _ in world.store.list_events(EPISODE)]
        assert "callback_applied" not in kinds

        # I3: the key is not poisoned; the same delivery applies cleanly.
        replay = _callback(world, "cb-crash-1", "acknowledged").json()
        assert replay["receipt"] == "applied"
        assert replay["execution"] == "acknowledged"

    def test_a_committed_callback_survives_a_fresh_process(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        _dispatch(world)
        applied = _callback(world, "cb-restart-2", "acknowledged").json()
        assert applied["receipt"] == "applied"

        report = _reopen_report(world)
        assert report["execution"] == "acknowledged"
        assert report["transitions"] == 1
        assert report["callbacks"] == 1
        # The fresh process derives the same patient truth: an acknowledged
        # request with no evidence is still unresolved (I2).
        assert report["closure"] == "open"

        # I3 across a restart: the redelivered callback is a duplicate, not a
        # second application.
        again = _callback(world, "cb-restart-2", "acknowledged").json()
        assert again["receipt"] == "duplicate"

        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")


# ---------------------------------------------------------------------------
# 6. Clock change
# ---------------------------------------------------------------------------


class TestClockChangeSequence:
    """Fault: the clock moves, in both directions.

    Guard under test: `derive_closure`'s expiry stickiness (the
    `expiry_event_id is not None` clause). Disabled, a backwards clock
    un-expires the episode and this class goes red on the last surface read:
    a deadline that passed with nothing to show is a fact that already
    happened, and I1 means no later clock read can take it back.
    """

    def test_a_backwards_clock_cannot_unexpire_the_episode(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        _grant(world)
        _dispatch(world)
        # I1: the deadline is anchored at assessment, never derived from a
        # later clock read.
        snapshot = world.store.load_snapshot(EPISODE)
        assert snapshot.disposition.clinical_deadline_utc == DEADLINE_UTC

        # Forward: the deadline passes with the attempt unresolved. The first
        # patient read is the trigger and records the expiry.
        world.clock.set(DEADLINE_UTC + timedelta(minutes=30))
        _assert_healthy_surface(world, EXPIRED_LINES, "expired_unresolved")
        first_read = world.store.list_expiry_events(EPISODE)
        assert len(first_read) == 1
        assert first_read[0][0] == 1

        # Once, not per read: a second read writes no second event.
        _assert_healthy_surface(world, EXPIRED_LINES, "expired_unresolved")
        assert len(world.store.list_expiry_events(EPISODE)) == 1

        # Backward: the clock regresses, and the recorded expiry stays.
        world.clock.set(fixture.SCENARIO_NOW_UTC)
        _assert_healthy_surface(world, EXPIRED_LINES, "expired_unresolved")

        # I1 again: no clock movement moved the deadline.
        snapshot = world.store.load_snapshot(EPISODE)
        assert snapshot.disposition.clinical_deadline_utc == DEADLINE_UTC


# ---------------------------------------------------------------------------
# 7. Consent revocation
# ---------------------------------------------------------------------------


class TestConsentRevocationSequence:
    """Fault: consent is revoked while the attempt is in flight.

    Guard under test: the `_consent_rejection_reason` call in
    `record_callback_once`. Disabled (the reason forced to `None`), the
    in-flight success is applied and this class goes red on the receipt:
    a success recorded under a consent that moved is a false-completion path
    (`03-program-design.md` section 3).
    """

    def test_a_success_arriving_after_revocation_is_refused_and_recorded(
        self, world: FaultWorld
    ) -> None:
        _assess(world)
        granted = _grant(world)
        assert granted == 1
        opened = _dispatch(world).json()

        revoked = world.client.post(
            f"/api/episodes/{EPISODE}/consents", json={"granted": False}
        )
        assert revoked.status_code == 200
        assert revoked.json()["version"] == 2

        refused = _callback(world, "cb-revoke-1", "acknowledged").json()
        # I5 of the refusal: "received and refused" is its own state, with the
        # reason, and it is not displayed as an applied outcome (O5).
        assert refused["receipt"] == "refused"
        assert refused["applied"] is False
        assert refused["rejection_reason"]
        assert "consent" in refused["rejection_reason"]
        # The attempt is left exactly as it was: in flight, not acknowledged.
        assert refused["execution"] == "attempted"

        assert world.store.list_transitions(opened["attempt_id"]) == ()
        receipts = world.store.list_callbacks(EPISODE)
        assert len(receipts) == 1
        assert receipts[0].accepted is False
        kinds = [kind for kind, _, _ in world.store.list_events(EPISODE)]
        assert "callback_rejected" in kinds

        # I2: refusing the success keeps the episode unresolved, not complete.
        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")

    def test_regranting_does_not_retroactively_apply_the_refused_success(
        self, world: FaultWorld
    ) -> None:
        """The stamped version is what authorised the attempt, and it moved.

        After a second grant the current consent is granted again, but the
        attempt still carries version 1, so a fresh delivery is refused for
        the version change rather than applied: re-granting does not rewrite
        what the moment of authorisation was.
        """
        _assess(world)
        _grant(world)
        _dispatch(world)
        world.client.post(f"/api/episodes/{EPISODE}/consents", json={"granted": False})
        first = _callback(world, "cb-revoke-2", "acknowledged").json()
        assert first["receipt"] == "refused"

        regranted = world.client.post(
            f"/api/episodes/{EPISODE}/consents", json={"granted": True}
        )
        assert regranted.json()["version"] == 3

        again = _callback(world, "cb-revoke-3", "acknowledged").json()
        assert again["receipt"] == "refused"
        assert "consent" in again["rejection_reason"]
        assert "changed" in again["rejection_reason"]

        _assert_healthy_surface(world, UNRESOLVED_LINES, "open")
