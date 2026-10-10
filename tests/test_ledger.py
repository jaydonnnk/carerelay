"""Slice 12: the judge ledger and the permitted-route projection.

`04-slices.md` Slice 12 asks for the ledger (two axes, transitions, expiry,
**simulated label**, **failure-event origin**, fault assertions, `dwell_seconds`)
and for `GET /options`. Both are served at the paths `02-architecture.md` 3.1
names, so `/ledger` in the slice row is shorthand for
`/api/episodes/{id}/ledger`; the record says so rather than leaving a reader to
reconcile the two. **Since 10 October 2026 the shorthand is also a real path:**
the same handler is registered at `/ledger/{episode_id}`, which is what makes the
auth row in section 12 true. `/options` has no such twin on purpose.

**Every assertion here must be able to fail**, which is why
`tests/_mutate_slice12.py` exists: one mutation per claim below, each seen RED.
Two of the claims are stated as weaker than they look, and the harness reports
which of the five fault assertions can actually be falsified in today's state
machine rather than averaging them.

**The ledger is a read.** The one non-obvious claim is that reading it changes
nothing, including the expiry read-path the *patient* projection runs. That is
tested with a clock past the deadline, because "it did not write" is only
meaningful where something was there to write.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from carerelay.api import app, get_service  # noqa: E402
from carerelay.coordinator import LocalSimulationCoordinator  # noqa: E402
from carerelay.demo import fixture  # noqa: E402
from carerelay.service import EpisodeService, ScenarioClock  # noqa: E402
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.state import open_store  # noqa: E402
from carerelay.tools import McpTools  # noqa: E402

#: A clock past the fixture deadline, so an expiry is there to be recorded.
#: The deadline is 18:00 SGT on the day the disposition is written, which is
#: 10:00 UTC; this is two hours after it.
AFTER_DEADLINE_UTC = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)

EPISODE = fixture.DEMO_EPISODE_ID
ROUTE = "fictional_provider"
PURPOSE = "book_transport"


def _tools(store) -> McpTools:
    return McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())


def _service(clock_instant: datetime) -> EpisodeService:
    store = open_store(":memory:", check_same_thread=False)
    return EpisodeService(
        store,
        coordinator=LocalSimulationCoordinator(_tools(store)),
        clock=ScenarioClock(clock_instant),
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        policy_provenance="test: provisional",
    )


@pytest.fixture()
def client() -> Iterator[TestClient]:
    service = _service(fixture.SCENARIO_NOW_UTC)
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
    service._store.close()


@pytest.fixture()
def late_client() -> Iterator[TestClient]:
    """A client whose clock is already past the fixture deadline."""
    service = _service(AFTER_DEADLINE_UTC)
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
    service._store.close()


@pytest.fixture()
def assessed(client: TestClient) -> str:
    client.post("/api/episodes")
    response = client.post(
        f"/api/episodes/{EPISODE}/intake",
        json={"confirmed_text": fixture.BOUND_COMPLAINT},
    )
    assert response.status_code == 200
    return EPISODE


def _open_attempt(client: TestClient) -> str:
    client.post(f"/api/episodes/{EPISODE}/consents", json={"granted": True})
    response = client.post(
        f"/api/episodes/{EPISODE}/actions",
        json={"route_id": ROUTE, "purpose_id": PURPOSE},
    )
    assert response.status_code == 200
    return response.json()["attempt_id"]


# ---------------------------------------------------------------------------
# GET /options
# ---------------------------------------------------------------------------


class TestPermittedOptions:
    def test_the_route_set_is_exactly_the_policy_set(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{EPISODE}/options").json()
        assert {r["route_id"] for r in body["routes"]} == set(
            fixture.PERMITTED_ROUTE_IDS
        )

    def test_every_route_carries_the_policy_display_text(self, client: TestClient):
        """A raw route id on a screen is the defect this read exists to prevent."""
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{EPISODE}/options").json()
        display = fixture.policy_text().route_display_by_id
        for route in body["routes"]:
            assert route["display"] == display[route["route_id"]]
            assert route["display"] != route["route_id"]

    def test_the_label_and_the_wired_origin_travel_with_it(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{EPISODE}/options").json()
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL
        assert body["available_origin"] == "local-sim"

    def test_before_assessment_there_is_no_disposition_version(
        self, client: TestClient
    ):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{EPISODE}/options").json()
        assert body["disposition_version"] is None

    def test_after_assessment_the_version_is_named(self, client: TestClient, assessed):
        body = client.get(f"/api/episodes/{assessed}/options").json()
        assert body["disposition_version"] == 1

    def test_an_unknown_episode_is_404(self, client: TestClient):
        assert client.get("/api/episodes/does-not-exist/options").status_code == 404


# ---------------------------------------------------------------------------
# GET /ledger
# ---------------------------------------------------------------------------


class TestLedgerCarriesTheTwoAxes:
    def test_the_three_axis_values_are_present(self, client: TestClient, assessed):
        axes = client.get(f"/api/episodes/{assessed}/ledger").json()["axes"]
        assert axes["execution"] == "not_started"
        assert axes["evidence"] == "none"
        assert axes["closure"] == "open"

    def test_the_simulated_label_is_inside_the_json(self, client: TestClient, assessed):
        """D11: the label has to travel with the data, not only in page chrome."""
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL

    def test_an_unknown_episode_is_404(self, client: TestClient):
        assert client.get("/api/episodes/does-not-exist/ledger").status_code == 404


class TestLedgerCarriesTheFailureEventOrigin:
    """`02-architecture.md` 3.3: platform and local-sim must be distinguishable."""

    def test_a_transition_keeps_its_origin(self, client: TestClient, assessed):
        _open_attempt(client)
        client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        kinds = [
            t["origin"]
            for attempt in body["attempts"]
            for t in attempt["transitions"]
        ]
        assert kinds, "no transition reached the ledger"
        assert set(kinds) == {"local-sim"}

    def test_the_origin_summary_agrees_with_the_rows(self, client: TestClient, assessed):
        _open_attempt(client)
        client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["origins"] == ["local-sim"]

    def test_a_receipt_keeps_why_it_was_not_applied(self, client: TestClient, assessed):
        _open_attempt(client)
        body_json = {"callback_key": "cb-1", "transition": "acknowledged"}
        client.post(f"/api/episodes/{EPISODE}/callbacks/{ROUTE}", json=body_json)
        client.post(f"/api/episodes/{EPISODE}/callbacks/{ROUTE}", json=body_json)
        receipts = client.get(f"/api/episodes/{assessed}/ledger").json()["callbacks"]
        assert len(receipts) == 2
        duplicate = [r for r in receipts if not r["accepted"]]
        assert duplicate, "the duplicate receipt is missing from the ledger"
        assert duplicate[0]["rejection_reason"]


class TestTheLedgerNeverWrites:
    def test_reading_the_ledger_does_not_record_an_expiry(
        self, late_client: TestClient
    ):
        """The claim with teeth: the patient read records it, the ledger read does not.

        A judge opening the evidence is not a clinical event. If this test ever
        passes while `project_ledger` runs the expiry read-path, the ledger has
        become a writer and the evidence is no longer independent of who looked
        at it.
        """
        late_client.post("/api/episodes")
        late_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT},
        )
        first = late_client.get(f"/api/episodes/{EPISODE}/ledger").json()
        assert first["expiry"] == []
        again = late_client.get(f"/api/episodes/{EPISODE}/ledger").json()
        assert again["expiry"] == []

    def test_the_patient_read_does_record_it_and_the_ledger_then_shows_it(
        self, late_client: TestClient
    ):
        """The same clock, the other read. The ledger is not blind: it just writes
        nothing itself."""
        late_client.post("/api/episodes")
        late_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT},
        )
        assert late_client.get(f"/api/episodes/{EPISODE}/ledger").json()["expiry"] == []
        patient = late_client.get(f"/api/episodes/{EPISODE}").json()
        assert patient["closure"] == "expired_unresolved"
        after = late_client.get(f"/api/episodes/{EPISODE}/ledger").json()
        assert len(after["expiry"]) == 1
        assert after["expiry"][0]["disposition_version"] == 1


class TestLedgerCarriesDwellSeconds:
    """`PLAN.md` 5.2.1, C8: judge-facing, never on the patient surface."""

    def test_a_hint_event_keeps_its_dwell_time(self, client: TestClient, assessed):
        client.post(
            f"/api/episodes/{assessed}/hint-events",
            json={"hint_level": "H2", "event": "shown", "dwell_seconds": 12.5},
        )
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["hint_events"][0]["dwell_seconds"] == 12.5
        assert body["dwell_seconds_total"] == 12.5

    def test_with_no_dwell_recorded_the_total_is_absent(self, client: TestClient, assessed):
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["dwell_seconds_total"] is None

    def test_the_hint_response_still_does_not_carry_it_back(
        self, client: TestClient, assessed
    ):
        """C8 at the boundary: the write route never echoes dwell to the patient."""
        response = client.post(
            f"/api/episodes/{assessed}/hint-events",
            json={"hint_level": "H2", "event": "shown", "dwell_seconds": 12.5},
        )
        assert "dwell_seconds" not in response.json()


class TestLedgerCarriesTheClosureInputs:
    def test_an_acceptance_shows_in_the_ledger(self, client: TestClient, assessed):
        client.post(f"/api/episodes/{EPISODE}/acceptances", json={"accepted_by": "caregiver"})
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["acceptance"] is not None
        assert body["axes"]["closure"] == "closed_with_evidence"
        assert body["axes"]["care_evidenced"] is False

    def test_an_escalation_names_the_human_path(self, client: TestClient, assessed):
        client.post(
            f"/api/episodes/{EPISODE}/escalations", json={"human_path": "nurse_line"}
        )
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert body["escalation"] is not None
        assert body["escalation"]["human_path"] == "nurse_line"
        assert body["axes"]["closure"] == "escalated_to_human"


class TestTheFaultAssertions:
    def test_all_five_are_named_and_carry_evidence(self, client: TestClient, assessed):
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        by_id = {a["invariant"]: a for a in body["fault_assertions"]}
        assert sorted(by_id) == ["I1", "I2", "I3", "I4", "I5"]
        for assertion in by_id.values():
            assert isinstance(assertion["holds"], bool)
            assert assertion["evidence"].strip()

    def test_all_five_hold_on_a_clean_unresolved_episode(
        self, client: TestClient, assessed
    ):
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert [a["holds"] for a in body["fault_assertions"]] == [True] * 5

    def test_i3_reports_false_when_two_terminal_transitions_exist(
        self, client: TestClient, assessed
    ):
        """The one assertion of the five that today's state machine can falsify.

        Terminal states are absorbing for the *status*, but the losing row is
        still appended, so an attempt can carry two terminal transitions. I3
        says idempotency means no fault path appends a second outcome, so the
        ledger has to be able to report that it happened. The other four cannot
        be driven false by any sequence this build permits, and the slice record
        says so rather than implying all five are proof.
        """
        _open_attempt(client)
        failed = client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-fail", "transition": "failed"},
        )
        assert failed.status_code == 200
        late = client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-ack", "transition": "acknowledged"},
        )
        assert late.status_code == 200
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        i3 = [a for a in body["fault_assertions"] if a["invariant"] == "I3"][0]
        assert i3["holds"] is False, i3["evidence"]
        assert "=2" in i3["evidence"]


class TestTheLedgerLeaksNothing:
    def test_no_secret_shaped_value_is_serialized(self, client: TestClient, assessed):
        """The ledger is a new JSON surface, so it inherits the secret scan.

        `tests/test_boundaries.py` owns the scanner; this test is the ledger's
        own row in it rather than a second scanner.
        """
        from test_boundaries import scan_for_secrets

        _open_attempt(client)
        client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert scan_for_secrets(json.dumps(body, ensure_ascii=False)) == []

    def test_the_idempotency_key_is_not_published(self, client: TestClient, assessed):
        """D5 derives the key from a server-held secret, so the derivation stays in."""
        _open_attempt(client)
        body = client.get(f"/api/episodes/{assessed}/ledger").json()
        assert "idempotency" not in json.dumps(body).casefold()

    def test_the_ledger_is_json_serializable_every_time(
        self, client: TestClient, assessed
    ):
        _open_attempt(client)
        client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        response = client.get(f"/api/episodes/{assessed}/ledger")
        assert response.status_code == 200
        json.dumps(response.json())


class TestTheLedgerAliasUnderTheGuardedPrefix:
    """The alias that makes the auth row in `02-architecture.md` section 12 true.

    That row says the bearer dependency enforces on every `/api` route **and on
    `/ledger`**, and `/ledger` already sat in `GUARDED_PREFIXES`, so the prefix
    was guarded while no route lived under it: the sentence was aspirational.
    Registering the same handler under `/ledger` is what makes it true, and
    stacking the decorators is what keeps the two paths from drifting.

    Two of the three claims below are about the alias itself, and one is about
    what was deliberately *not* aliased.
    """

    def test_the_alias_serves_the_same_body_as_the_canonical_path(
        self, client: TestClient, assessed
    ):
        """One implementation, two paths. A second copy would be a second thing
        to keep in step, so this asserts they return the same document."""
        canonical = client.get(f"/api/episodes/{assessed}/ledger").json()
        alias = client.get(f"/ledger/{assessed}").json()
        assert alias == canonical

    def test_the_alias_is_guarded_when_auth_is_armed(
        self, client: TestClient, assessed, monkeypatch: pytest.MonkeyPatch
    ):
        """The reason the alias is safe to add at all.

        `/ledger` is a guarded prefix, so the dependency declared once on the app
        covers this route without anyone annotating it. A 200 here with no token
        would mean the blanket has a hole in exactly the place section 12 names.
        """
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        assert client.get(f"/ledger/{assessed}").status_code == 401
        admitted = client.get(
            f"/ledger/{assessed}", headers={"Authorization": "Bearer " + "t" * 32}
        )
        assert admitted.status_code == 200

    def test_the_alias_404s_for_an_unknown_episode(self, client: TestClient):
        assert client.get("/ledger/does-not-exist").status_code == 404

    def test_the_permitted_route_surface_has_no_twin_outside_the_guard(
        self, client: TestClient
    ):
        """The asymmetry is deliberate, so it is asserted rather than explained.

        `/options` is **not** a guarded prefix, so a top-level copy of the
        permitted-route surface would be open. This reads the real route table
        instead of trusting the docstring that says so.
        """
        from carerelay.api import GUARDED_PREFIXES

        assert "/ledger" in GUARDED_PREFIXES
        assert "/options" not in GUARDED_PREFIXES
        assert [r.path for r in app.routes if r.path.startswith("/options")] == []
