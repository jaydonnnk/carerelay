"""API and explicit legacy service tests. Each assertion must be able to fail (Gate 4 standing rules).

Actual HTTP checks cover the current wire contract. Retired operations use
explicit EpisodeService probes whose status/body classify service outcomes,
not HTTP responses. Separate authenticated POST checks prove retirement writes
nothing. Original safety selectors remain stable for the mutation harnesses. The `AssertionsHaveTeeth` class proves the two safety-shaped
assertions are not vacuous.
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

from _legacy_service_probes import (
    KEY,
    signed_create,
    signed_intake,
    service_intake,
    service_restatement,
    service_repair,
    service_confirmation,
    service_hint,
    service_consent,
    service_action,
    service_barrier,
)
from carerelay.api import app, get_service, COORDINATOR_FALLBACK_TEXT  # noqa: E402
from carerelay.coordinator import (  # noqa: E402
    AllowedPlanValues,
    CoordinatorUnavailable,
    LocalSimulationCoordinator,
)
from carerelay.demo import fixture  # noqa: E402
from carerelay.domain.models import EvidenceLevel, EvidenceRecord, ExtractedPlan  # noqa: E402
from carerelay.service import EpisodeService, ScenarioClock  # noqa: E402
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.state import open_store  # noqa: E402
from carerelay.tools import McpTools  # noqa: E402

EPISODE = fixture.DEMO_EPISODE_ID

#: A restatement that resolves to exactly the fixture's plan.
CORRECT = "see the doctor today before 6pm myself"
#: A known, different deadline: a mismatch, not an uncertainty (K1).
WRONG_DAY = "see the doctor tomorrow before 6pm myself"


def _tools(store) -> McpTools:
    """The MCP surface one coordinator executes through. Slice 6.

    Built per store, because the tool surface rechecks the attempt key against
    the same database the attempt was opened in.
    """
    return McpTools(store, policy=fixture.policy(), provider=ScriptedProvider(), now=lambda: fixture.SCENARIO_NOW_UTC)


@pytest.fixture()
def client(planback_client) -> TestClient:
    return planback_client


@pytest.fixture()
def planback_client() -> Iterator[TestClient]:
    """A client whose service runs on a fresh in-memory database.

    The clinical record is append-only, so a test cannot reset a shared one: a
    second intake would be refused as a repeat assessment, and a third repair
    would already have been reached by an earlier test.
    """
    store = open_store(":memory:", check_same_thread=False)
    service = EpisodeService(
        store,
        coordinator=LocalSimulationCoordinator(_tools(store)),
        clock=ScenarioClock(fixture.SCENARIO_NOW_UTC),
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        operation_signing_key=lambda: KEY,
        policy_provenance="test: provisional",
    )
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
    store.close()


@pytest.fixture()
def assessed(planback_client: TestClient) -> str:
    signed_create(planback_client)
    response = signed_intake(planback_client)
    assert response.status_code == 200
    return EPISODE


class TestEpisodeContract:
    def test_create_episode_returns_an_id_and_no_disposition(self, client: TestClient):
        response = signed_create(client)
        assert response.status_code == 200
        body = response.json()
        assert body["journey"]["episode_id"] == fixture.DEMO_EPISODE_ID
        assert body["receipt"]["state"] == "applied"
        assert body["journey"]["plan"] is None
        assert body["journey"]["disposition_version"] is None
        # 02-architecture.md 3.1: creating an episode must NOT write a disposition.
        assert "disposition" not in body

    def test_unknown_episode_is_404(self, client: TestClient):
        assert client.get("/api/episodes/does-not-exist").status_code == 404

    def test_no_plan_has_no_fixture_guidance(self, planback_client: TestClient):
        signed_create(planback_client)
        response = planback_client.get(f"/api/episodes/{EPISODE}")
        assert response.status_code == 200
        body = response.json()
        assert body["lines"] == []
        assert body["plan"] is body["outcome"] is body["closure"] is None
        assert body["care_evidenced"] is False
        assert body["text"] == fixture.JOURNEY_COPY["start"]
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.JOURNEY_LABEL

    def test_bare_root_redirects_without_guidance(self, client, monkeypatch):
        monkeypatch.setenv("CARERELAY_FRONTEND_URL", "https://frontend.invalid/")
        response = client.get("/?episode_id=anything&redirect=https://attacker.invalid", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "https://frontend.invalid/"
        assert response.text == ""

    def test_bare_root_without_configuration_refuses(self, client, monkeypatch):
        monkeypatch.delenv("CARERELAY_FRONTEND_URL", raising=False)
        assert client.get("/", follow_redirects=False).status_code == 503

    def test_static_legacy_stylesheet_remains_available(self, client):
        assert client.get("/static/style.css").status_code == 200


def assessed_patient(client):
    """Actual Slice 15 assessed HTTP, retaining the approved safety assertions."""
    response = client.get(f"/api/episodes/{EPISODE}")
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Slice 4: the PlanBack routes
# ---------------------------------------------------------------------------


class DeadCoordinator:
    simulated = True

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        raise CoordinatorUnavailable("no credentials; the Gate A spike is unrun")


def _service_with(store, coordinator) -> EpisodeService:
    return EpisodeService(
        store,
        coordinator=coordinator,
        clock=ScenarioClock(fixture.SCENARIO_NOW_UTC),
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        operation_signing_key=lambda: KEY,
        policy_provenance="test: provisional",
    )


@pytest.fixture()
def dead_client() -> Iterator[TestClient]:
    store = open_store(":memory:", check_same_thread=False)
    service = _service_with(store, DeadCoordinator())
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
    store.close()


class TestPlanBackRouteContracts:
    """Retired PlanBack operations probed explicitly at the service boundary."""
    def test_intake_issues_the_preauthored_plan(self, planback_client: TestClient):
        signed_create(planback_client)
        body = service_intake(planback_client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT}).json()
        assert body["disposition_version"] == 1
        assert body["action_id"] == "attend_same_day_review"
        assert body["fallback_route_id"] == "nurse_line"

    def test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path(
        self, planback_client: TestClient
    ):
        signed_create(planback_client)
        response = service_intake(planback_client, EPISODE, json={"confirmed_text": "something this fixture does not cover"})
        assert response.status_code == 422
        assert response.json()["detail"]["stopped_at"] == "human_path"

    @pytest.mark.parametrize(
        "red_flag_text",
        [
            "help sorting out my appointment, also I have chest pain and cannot breathe",
            "I have crushing chest pain. Also help sorting out my appointment",
            "help sorting out my appointment, I think I am having a stroke",
            "I do not need help sorting out my appointment",
            "does my mother need help sorting out my appointment",
        ],
    )
    def test_a_bound_phrase_inside_a_larger_complaint_stops_at_the_human_path(
        self, planback_client: TestClient, red_flag_text: str
    ):
        """B3, closed 2 October 2026. The binding is an exact match, not a substring.

        These five texts all *contain* the bound phrase, so the old substring rule
        bound them to the demo plan and returned 200. The second one carries
        crushing chest pain and the third a stroke. Every one must now stop at the
        human path, because recognition is "is this the bound complaint", not "does
        it contain the bound phrase".

        The old test submitted only a string with zero token overlap, so it proved
        the disjoint case and nothing else. This parametrisation is what the old
        test name claimed to prove.
        """
        signed_create(planback_client)
        response = service_intake(planback_client, EPISODE, json={"confirmed_text": red_flag_text})
        assert response.status_code == 422, (
            f"{red_flag_text!r} was bound to the demo plan; the binding rule is "
            "a substring match, so a complaint carrying a red flag is accepted"
        )
        assert response.json()["detail"]["stopped_at"] == "human_path"

    def test_the_exact_bound_complaint_still_issues_the_plan(
        self, planback_client: TestClient
    ):
        """The strict rule must not become so strict that nothing binds.

        This is the control for the parametrised test above: the exact bound
        complaint, normalised for case and whitespace, still scores 200.
        """
        signed_create(planback_client)
        response = service_intake(planback_client, EPISODE, json={"confirmed_text": f"  {fixture.BOUND_COMPLAINT.upper()}  "})
        assert response.status_code == 200
        assert response.json()["disposition_version"] == 1

    def test_a_clean_restatement_is_understood(self, planback_client, assessed):
        body = service_restatement(planback_client, assessed, json={"text": CORRECT, "hint_level": "H0"}).json()
        assert body["understood"] is True
        assert body["mismatches"] == []
        assert body["outcome"] == "recall_unaided"

    def test_a_mismatch_names_one_field_to_repair(self, planback_client, assessed):
        body = service_restatement(planback_client, assessed, json={"text": WRONG_DAY, "hint_level": "H0"}).json()
        assert body["mismatches"] == ["deadline_utc"]
        assert body["next_repair_field"] == "deadline_utc"
        assert body["routes_to_human_path"] is False

    def test_two_repairs_then_the_human_path(self, planback_client, assessed):
        first = service_restatement(planback_client, assessed, json={"text": WRONG_DAY, "hint_level": "H0"}).json()
        rid = first["restatement_id"]

        second = service_repair(planback_client, assessed, rid, json={"text": WRONG_DAY, "hint_level": "H0"}).json()
        assert second["repair_round"] == 1

        third = service_repair(planback_client, assessed, second['restatement_id'], json={"text": WRONG_DAY, "hint_level": "H0"}).json()
        assert third["repair_round"] == 2
        assert third["routes_to_human_path"] is True
        assert third["human_path_route_id"] == "nurse_line"

        capped = service_repair(planback_client, assessed, third['restatement_id'], json={"text": WRONG_DAY, "hint_level": "H0"})
        assert capped.status_code == 409

    def test_a_restatement_before_any_plan_is_refused(self, planback_client):
        signed_create(planback_client)
        response = service_restatement(planback_client, EPISODE, json={"text": CORRECT, "hint_level": "H0"})
        assert response.status_code == 409


class TestTranscriptConfirmationRoute:
    def test_an_unconfirmed_voice_restatement_is_refused(
        self, planback_client, assessed
    ):
        response = service_restatement(planback_client, assessed, json={"text": CORRECT, "hint_level": "H0", "input_mode": "voice"})
        assert response.status_code == 409

    def test_a_confirmation_binds_to_the_text_being_scored(
        self, planback_client, assessed
    ):
        confirmation_id = service_confirmation(planback_client, assessed, json={"corrected_text": CORRECT}).json()["confirmation_id"]

        ok = service_restatement(planback_client, assessed, json={
                "text": CORRECT,
                "hint_level": "H0",
                "input_mode": "voice",
                "transcript_confirmation_id": confirmation_id,
            })
        assert ok.status_code == 200
        assert ok.json()["understood"] is True

        swapped = service_restatement(planback_client, assessed, json={
                "text": "a different sentence entirely",
                "hint_level": "H0",
                "input_mode": "voice",
                "transcript_confirmation_id": confirmation_id,
            })
        assert swapped.status_code == 409


class TestPatientSurfaceHasNoDwell:
    """C8 on the serialized surface: `dwell_seconds` is ledger-only."""

    def test_the_restatement_response_carries_no_dwell_marker(
        self, planback_client, assessed
    ):
        body = service_restatement(planback_client, assessed, json={"text": CORRECT, "hint_level": "H0", "dwell_seconds": 4.2}).json()
        assert "dwell_seconds" not in body
        assert "4.2" not in str(body)

    def test_the_hint_event_response_carries_no_dwell_marker(
        self, planback_client, assessed
    ):
        service_hint(planback_client, assessed, json={"hint_level": "H2", "event": "shown", "dwell_seconds": 4.2})
        response = planback_client.get(f"/api/episodes/{assessed}")
        assert response.status_code == 200
        assert response.json()["flow"]["card_visible"] is True
        assert "dwell_seconds" not in response.text
        assert "4.2" not in response.text

    def test_the_dwell_marker_would_be_caught_if_it_were_there(self):
        """A negative scan that has never detected its needle is not evidence."""
        assert "dwell_seconds" in '{"dwell_seconds": 4.2}'


class TestPlanBackCarriesTheSimulatedLabel:
    def test_the_label_is_inside_the_restatement_projection(
        self, planback_client, assessed
    ):
        body = service_restatement(planback_client, assessed, json={"text": CORRECT, "hint_level": "H0"}).json()
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL


class TestCoordinatorUnavailable:
    def test_the_flow_stops_with_a_text_fallback_and_scored_false(
        self, dead_client: TestClient
    ):
        signed_create(dead_client)
        service_intake(dead_client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT})
        service = app.dependency_overrides[get_service]()
        before = service._store.list_restatements(EPISODE)
        with pytest.raises(CoordinatorUnavailable):
            service.submit_restatement(EPISODE, CORRECT, "H0")
        assert service._store.list_restatements(EPISODE) == before == ()
        # Exercise the production fallback serializer, not a helper's mapping.
        from carerelay.api import _coordinator_down
        unavailable = _coordinator_down()
        assert unavailable.status_code == 503
        assert unavailable.detail["scored"] is False
        assert unavailable.detail["text_fallback"] == COORDINATOR_FALLBACK_TEXT
        assert dead_client.get(f"/api/episodes/{EPISODE}").json()["step"] == "plan"

    def test_the_fallback_is_never_a_200_with_empty_mismatches(
        self, dead_client: TestClient
    ):
        """A service success carrying empty mismatches would read as "you understood your
        plan", which is a false completion of exactly the kind I2 forbids."""
        signed_create(dead_client)
        service_intake(dead_client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT})
        response = service_restatement(dead_client, EPISODE, json={"text": CORRECT, "hint_level": "H0"})
        assert response.status_code != 200


# ---------------------------------------------------------------------------
# Slice 5: barriers, escalation and reassessment
# ---------------------------------------------------------------------------


class TestBarrierRoute:
    def test_a_permitted_route_returns_200(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_barrier(planback_client, EPISODE, json={"barrier_text": "no transport today", "proposed_route_id": "nurse_line"})
        assert response.status_code == 200
        body = response.json()
        assert body["permitted_route_id"] == "nurse_line"
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL

    def test_no_proposal_is_accepted(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """Reporting a barrier without proposing a route is the common case."""
        response = service_barrier(planback_client, EPISODE, json={"barrier_text": "no transport today"})
        assert response.status_code == 200
        assert response.json()["permitted_route_id"] is None

    def test_a_hallucinated_route_is_422_and_says_it_was_recorded(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_barrier(planback_client, EPISODE, json={"barrier_text": "no transport", "proposed_route_id": "teleport_clinic"})
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["stopped_at"] == "human_path"
        assert detail["barrier_recorded"] is True

    def test_a_barrier_with_no_plan_is_409(self, planback_client: TestClient) -> None:
        signed_create(planback_client)
        response = service_barrier(planback_client, EPISODE, json={"barrier_text": "no transport today"})
        assert response.status_code == 409

    def test_an_unknown_episode_is_404(self, planback_client: TestClient) -> None:
        response = service_barrier(planback_client, "nope", json={"barrier_text": "no transport today"})
        assert response.status_code == 404


class TestEscalationRoute:
    def test_a_permitted_path_returns_200(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/escalations", json={"human_path": "nurse_line"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["human_path"] == "nurse_line"
        assert body["escalation_id"]

    def test_an_unpermitted_path_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/escalations", json={"human_path": "dr-smith-mobile"}
        )
        assert response.status_code == 422

    def test_the_escalation_moves_the_owner_in_the_derived_state(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """F6 through the HTTP surface, against the service the route uses."""
        service = app.dependency_overrides[get_service]()
        before = service._store.derive_closure(EPISODE, fixture.SCENARIO_NOW_UTC)
        assert before.action_owner_id == fixture.NEXT_OWNER_ID
        planback_client.post(
            f"/api/episodes/{EPISODE}/escalations", json={"human_path": "nurse_line"}
        )
        after = service._store.derive_closure(EPISODE, fixture.SCENARIO_NOW_UTC)
        assert after.action_owner_id == "nurse_line"


class TestReassessmentRoute:
    def test_no_code_stops_at_the_human_path_with_200(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """A stop is a normal outcome, not an error: it is the designed behaviour."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/reassessments", json={}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["outcome"] == "stop_at_human_path"
        assert body["disposition_version"] is None
        assert body["routes_to_human_path"] is True
        assert body["human_path_route_id"] == fixture.FALLBACK_ROUTE_ID

    def test_an_unknown_code_also_stops_with_200(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/reassessments",
            json={"confirmed_change_code": "chest_pain_now"},
        )
        assert response.status_code == 200
        assert response.json()["outcome"] == "stop_at_human_path"

    def test_no_version_is_added_by_any_input(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        service = app.dependency_overrides[get_service]()
        for payload in ({}, {"confirmed_change_code": None}, {"confirmed_change_code": "worse"}):
            planback_client.post(
                f"/api/episodes/{EPISODE}/reassessments", json=payload
            )
        assert len(service._store.list_dispositions(EPISODE)) == 1

    def test_a_reassessment_with_no_plan_is_409(
        self, planback_client: TestClient
    ) -> None:
        signed_create(planback_client)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/reassessments", json={}
        )
        assert response.status_code == 409


#: A permitted route, and a purpose id. The purpose is part of the idempotency
#: triple, not part of the clinical vocabulary, so any string is legal here.
ROUTE = "fictional_provider"
PURPOSE = "book_transport"


class TestActionRoutes:
    """Legacy action safety at EpisodeService; transport is retired in Slice 15.

    Probe status/body classify the service outcome and are not HTTP evidence.
    """

    @staticmethod
    def _consent(client: TestClient) -> None:
        response = service_consent(client, EPISODE, json={"granted": True})
        assert response.status_code == 200

    def test_consent_returns_a_version_and_carries_the_label(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_consent(planback_client, EPISODE, json={"granted": True})
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == 1
        service = app.dependency_overrides[get_service]()
        assert service._store.load_journey_bundle(assessed).consent_granted is True
        patient = planback_client.get(f"/api/episodes/{assessed}")
        assert patient.status_code == 200
        assert patient.json()["simulated"] is True
        assert patient.json()["fixture_label"] == fixture.JOURNEY_LABEL

    def test_an_action_without_consent_is_409(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        from carerelay.service import ConsentRequired
        service = app.dependency_overrides[get_service]()
        with pytest.raises(ConsentRequired):
            service.open_action(EPISODE, ROUTE, PURPOSE)
        assert service._store.list_attempts(EPISODE) == ()

    def test_an_action_opens_an_attempt_and_names_its_origin(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._consent(planback_client)
        response = service_action(planback_client, EPISODE, json={"route_id": ROUTE, "purpose_id": PURPOSE})
        assert response.status_code == 200
        body = response.json()
        assert body["duplicate"] is False
        assert body["purpose_id"] == "disposition:1:request_appointment"
        assert body["origin"] == "local-sim"
        assert body["consent_version"] == 1
        assert body["outcome"] is not None
        assert body["provider_ref"]
        assert body["simulated"] is True

    def test_a_double_tap_returns_the_first_attempt_and_no_outcome(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """I3 at the service boundary: the second call dispatched nothing."""
        self._consent(planback_client)
        first = service_action(planback_client, EPISODE, json={"route_id": ROUTE, "purpose_id": PURPOSE}).json()
        second = service_action(planback_client, EPISODE, json={"route_id": ROUTE, "purpose_id": PURPOSE}).json()
        assert second["attempt_id"] == first["attempt_id"]
        assert second["idempotency_key"] == first["idempotency_key"]
        assert second["duplicate"] is True
        assert second["outcome"] is None
        assert second["provider_ref"] is None

    def test_raw_action_fields_cannot_create_a_request(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        from carerelay.journey_commands import CommandInvalid
        self._consent(planback_client)
        service = app.dependency_overrides[get_service]()
        for purpose in ("purpose-a", "purpose-b", "disposition:1:request_appointment"):
            response = planback_client.post(f"/api/episodes/{EPISODE}/actions",
                json={"route_id": ROUTE, "purpose_id": purpose})
            assert response.status_code == 422
            with pytest.raises(CommandInvalid, match="legacy action requires a journey command"):
                service.open_action(EPISODE, ROUTE, purpose)
        assert service._store.list_attempts(EPISODE) == ()
        assert not any(kind == "dispatch_started" for kind, _, _
                       in service._store.list_events(EPISODE))

    def test_a_route_the_policy_does_not_permit_is_422_at_the_human_path(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._consent(planback_client)
        response = service_action(planback_client, EPISODE, json={"route_id": "somewhere_else", "purpose_id": PURPOSE})
        assert response.status_code == 422
        assert response.json()["detail"]["stopped_at"] == "human_path"

    def test_an_action_on_an_unknown_episode_is_404(
        self, planback_client: TestClient
    ) -> None:
        response = service_action(planback_client, "nope", json={"route_id": ROUTE, "purpose_id": PURPOSE})
        assert response.status_code == 404


class TestCallbackRoute:
    """O5 at the HTTP boundary: applied, duplicate and refused are different."""

    def _opened(self, client: TestClient, assessed: str) -> str:
        TestActionRoutes._consent(client)
        response = service_action(client, EPISODE, json={"route_id": ROUTE, "purpose_id": PURPOSE})
        assert response.status_code == 200
        return response.json()["attempt_id"]

    def test_a_callback_is_applied_and_reports_the_wired_origin(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._opened(planback_client, assessed)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["receipt"] == "applied"
        assert body["applied"] is True
        assert body["origin"] == "local-sim"
        assert body["rejection_reason"] is None

    def test_a_repeat_callback_is_a_duplicate_not_a_second_application(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._opened(planback_client, assessed)
        body = {"callback_key": "cb-1", "transition": "acknowledged"}
        planback_client.post(f"/api/episodes/{EPISODE}/callbacks/{ROUTE}", json=body)
        again = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}", json=body
        )
        assert again.status_code == 200
        assert again.json()["receipt"] == "duplicate"
        assert again.json()["applied"] is False

    def test_a_success_arriving_after_revocation_is_refused_and_says_why(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """O5, third state, at the HTTP boundary.

        The Slice 6 review found this missing: this class covers `applied` and
        `duplicate` but never revoked consent, so the `refused` receipt had no
        fail-capable test on the route even though the class claims all three
        states are different. A refusal is a success that was rejected because
        consent moved, which must not be displayed as "nothing arrived".
        """
        self._opened(planback_client, assessed)
        revoked = service_consent(planback_client, EPISODE, json={"granted": False})
        assert revoked.status_code == 200
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["receipt"] == "refused"
        assert body["applied"] is False
        assert body["rejection_reason"]
        assert body["execution"] != "acknowledged"

    def test_a_platform_origin_is_422_and_names_both_origins(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """The refusal has to name the alternative, or it is just a rejection."""
        self._opened(planback_client, assessed)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={
                "callback_key": "cb-1",
                "transition": "acknowledged",
                "origin": "platform",
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["requested_origin"] == "platform"
        assert detail["wired_origin"] == "local-sim"

    def test_an_unknown_transition_is_a_typed_422_not_a_500(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._opened(planback_client, assessed)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "half_done"},
        )
        assert response.status_code == 422

    def test_a_callback_for_a_route_with_no_attempt_is_409(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._opened(planback_client, assessed)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/callbacks/nurse_line",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        assert response.status_code == 409

    def test_a_callback_for_an_unknown_episode_is_404(
        self, planback_client: TestClient
    ) -> None:
        """Found live on 3 October 2026: this answered 409 before it was fixed.

        `list_attempts` on a missing episode returns nothing, so the route used
        to say "no attempt on this route", which is true of an episode that does
        not exist and implies one that does.
        """
        response = planback_client.post(
            f"/api/episodes/nope/callbacks/{ROUTE}",
            json={"callback_key": "cb-1", "transition": "acknowledged"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Slice 7: the transport guards
# ---------------------------------------------------------------------------


class TestAuthIsFailClosed:
    """The public deployment's guard. Every case here is a way to publish an
    open clinical-shaped endpoint by accident, and each is refused."""

    def test_disarmed_local_demo_still_answers(
        self, planback_client: TestClient
    ) -> None:
        """The control: with nothing configured, the demo is unchanged."""
        assert signed_create(planback_client).status_code == 200

    def test_health_stays_open_when_auth_is_armed(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A health check that needs a token cannot be used by the platform."""
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        assert planback_client.get("/health").status_code == 200

    def test_a_missing_token_is_401(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = signed_create(planback_client)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    def test_a_wrong_token_is_401(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = signed_create(planback_client, headers={"Authorization": "Bearer " + "w" * 32})
        assert response.status_code == 401

    def test_the_right_token_passes(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = signed_create(planback_client, headers={"Authorization": "Bearer " + "t" * 32})
        assert response.status_code == 200

    def test_a_non_bearer_scheme_is_401(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A caller cannot smuggle the token in as a Basic credential."""
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = signed_create(planback_client, headers={"Authorization": "Basic " + "t" * 32})
        assert response.status_code == 401

    def test_armed_with_no_token_configured_is_503_not_open(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The fail-closed branch, and the one that exists for R9.

        `APP_ENV=public` is what `render.yaml` sets. If someone deploys without
        also setting the token, the honest answer is 503. Treating a missing
        token as "no auth needed" would publish the endpoint wide open.
        """
        monkeypatch.setenv("APP_ENV", "public")
        monkeypatch.delenv("CARERELAY_API_TOKEN", raising=False)
        response = signed_create(planback_client)
        assert response.status_code == 503

    def test_public_env_is_armed_even_without_the_second_flag(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The deployment arms itself from `APP_ENV` alone."""
        monkeypatch.setenv("APP_ENV", "public")
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        assert signed_create(planback_client).status_code == 401

    def test_the_patient_fallback_page_is_not_guarded(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The bare-root recovery reads no record."""
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        # The unconfigured bare root now refuses; it never serves guidance.
        assert planback_client.get("/", follow_redirects=False).status_code == 503


class TestEveryApiRouteIsGuarded:
    """A blanket dependency that quietly stops being one is worse than none.

    `api.require_api_token` is declared once on the app and decides by path, so
    a route added later is covered automatically. This walks the real route
    table instead of trusting that, and fails if any path under a guarded prefix
    would escape.
    """

    def test_no_route_under_a_guarded_prefix_is_unguarded(self) -> None:
        from carerelay.api import GUARDED_PREFIXES, app

        guarded = [
            route.path
            for route in app.routes
            if any(
                route.path == prefix or route.path.startswith(prefix + "/")
                for prefix in GUARDED_PREFIXES
            )
        ]
        # The blanket is on the app, so it covers every route; the test's job is
        # to fail if someone splits the app into routers and forgets one.
        assert guarded, "no guarded routes found: the route table changed shape"
        assert len(guarded) >= 10, f"expected the full API surface, saw {guarded}"

    def test_the_guard_decides_by_path_not_by_route(self) -> None:
        from carerelay.api import guarded_path

        assert guarded_path("/api/episodes")
        assert guarded_path("/api/episodes/x/intake")
        assert guarded_path("/ledger")
        assert not guarded_path("/health")
        assert not guarded_path("/")
        # A sibling prefix must not be caught by a string prefix test.
        assert not guarded_path("/apifoo")


class TestCorsIsLocked:
    """Cross-origin access is opt-in, narrow, and never credentialed."""

    def test_no_origins_configured_means_no_cors_header(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
        response = planback_client.get(
            "/health", headers={"Origin": "https://evil.example"}
        )
        assert "access-control-allow-origin" not in response.headers

    def test_a_wildcard_origin_is_dropped_rather_than_honoured(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`*` would undo the whole guard, so it is dropped from the list.

        The drop is asserted on the helper itself, not only on the response,
        because a browser never sends `Origin: *` so an exact-match echo would
        pass while the wildcard remained in the configured list.
        """
        from carerelay.api import permitted_cors_origins

        monkeypatch.setenv("CORS_ORIGINS", "*")
        assert permitted_cors_origins() == []
        response = planback_client.get(
            "/health", headers={"Origin": "https://evil.example"}
        )
        assert "access-control-allow-origin" not in response.headers

    def test_an_unnamed_origin_is_refused(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CORS_ORIGINS", "https://carerelay.vercel.app")
        response = planback_client.get(
            "/health", headers={"Origin": "https://evil.example"}
        )
        assert "access-control-allow-origin" not in response.headers

    def test_a_named_origin_is_allowed(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The positive control, and the test that was missing.

        Every other case in this class asserts the *absence* of a header, which
        a CORS implementation that had never worked at all would also satisfy.
        The mutation harness proved that is exactly what was happening: the
        first version of this guard read the environment at import, so these
        tests passed against no middleware whatsoever. This one cannot pass
        unless the allow-list is genuinely honoured at request time.
        """
        monkeypatch.setenv("CORS_ORIGINS", "https://carerelay.vercel.app")
        response = planback_client.get(
            "/health", headers={"Origin": "https://carerelay.vercel.app"}
        )
        assert response.headers["access-control-allow-origin"] == (
            "https://carerelay.vercel.app"
        )

    def test_credentials_are_never_allowed(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Asserted on a response that *does* carry CORS headers.

        Checking for the header's absence on an arbitrary response would prove
        nothing: it is indistinguishable from CORS being off entirely, which is
        the very confusion that let the first version of this guard pass while
        broken. So the allow-list is configured first, the origin is confirmed
        echoed, and only then is the credentials header required to be missing.

        The token travels in an `Authorization` header as a bearer credential,
        so cookie credentials are neither needed nor wanted, and there is no
        switch that turns them on.
        """
        monkeypatch.setenv("CORS_ORIGINS", "https://carerelay.vercel.app")
        response = planback_client.get(
            "/health", headers={"Origin": "https://carerelay.vercel.app"}
        )
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" not in response.headers
        source = (
            Path(__file__).resolve().parents[1] / "src" / "carerelay" / "api.py"
        ).read_text(encoding="utf-8")
        assert "allow_credentials" not in source


class TestMalformedEnumsAreTypedRefusals:
    """NF2 and NF3. These two inputs answered 500 before Slice 7."""

    def test_an_unknown_hint_level_is_422_not_500(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_hint(planback_client, EPISODE, json={"hint_level": "H9", "event": "shown"})
        assert response.status_code == 422

    def test_an_auto_hide_event_is_422_not_500(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """`auto_hide` is not in the vocabulary, because C8 forbids it."""
        response = service_hint(planback_client, EPISODE, json={"hint_level": "H2", "event": "auto_hide"})
        assert response.status_code == 422

    def test_the_permitted_set_is_reported_so_the_refusal_is_actionable(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_hint(planback_client, EPISODE, json={"hint_level": "H9", "event": "shown"})
        assert "H3" in response.json()["detail"]

    def test_a_malformed_hint_level_on_a_restatement_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_restatement(planback_client, EPISODE, json={"text": CORRECT, "hint_level": "H9"})
        assert response.status_code == 422

    def test_a_malformed_input_mode_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = service_restatement(planback_client, EPISODE, json={"text": CORRECT, "hint_level": "H0", "input_mode": "telepathy"})
        assert response.status_code == 422

    def test_a_malformed_mode_on_a_repair_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        first = service_restatement(planback_client, EPISODE, json={"text": WRONG_DAY, "hint_level": "H0"})
        assert first.status_code == 200
        response = service_repair(planback_client, EPISODE, first.json()['restatement_id'], json={"text": CORRECT, "hint_level": "H1", "input_mode": "telepathy"})
        assert response.status_code == 422

    def test_the_control_a_well_formed_event_still_records(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """Next to every defect case: the feature itself is not broken."""
        response = service_hint(planback_client, EPISODE, json={"hint_level": "H2", "event": "shown"})
        assert response.status_code == 200
        assert response.json()["card_visible"] is True


# ---------------------------------------------------------------------------
# Slice 10: the Closure Contract in full
# ---------------------------------------------------------------------------

#: 19:00 SGT on the scenario day, so the fixture's 18:00 deadline has passed.
#: The fixture derives the deadline from the clock's own local day, so one fixed
#: post-deadline instant is enough to make an assessed episode overdue.
AFTER_DEADLINE_UTC = datetime(2026, 9, 30, 11, 0, tzinfo=timezone.utc)


@pytest.fixture()
def overdue_client() -> Iterator[tuple[TestClient, object]]:
    """A client whose clock is past the fixture's 18:00 SGT deadline.

    The store is yielded alongside the client so a test can count the expiry
    events the read-path wrote. That count is the only way to tell "recorded
    once" from "recorded on every read", and the difference is D12.
    """
    store = open_store(":memory:", check_same_thread=False)
    service = EpisodeService(
        store,
        coordinator=LocalSimulationCoordinator(_tools(store)),
        clock=ScenarioClock(AFTER_DEADLINE_UTC),
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        operation_signing_key=lambda: KEY,
        policy_provenance="test: provisional",
    )
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app), store
    app.dependency_overrides.clear()
    store.close()


class TestExpiryReadPath:
    """The read is the trigger; no scheduler is implied (`03-program-design.md` 3)."""

    def test_the_first_read_after_an_unresolved_deadline_records_expiry_once(
        self, overdue_client: tuple[TestClient, object]
    ) -> None:
        """A patient read is what turns an overdue deadline into a recorded fact."""
        client, store = overdue_client
        signed_create(client)
        service_intake(client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT})
        assert store.list_expiry_events(EPISODE) == (), "nothing has read the episode"

        body = assessed_patient(client)
        assert body["closure"] == "expired_unresolved"
        assert len(store.list_expiry_events(EPISODE)) == 1

        assessed_patient(client)
        assert len(store.list_expiry_events(EPISODE)) == 1, (
            "the second read recorded a second expiry event"
        )

    def test_before_the_deadline_the_read_returns_the_unresolved_screen(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """The control, at the same route: nothing is recorded early."""
        body = assessed_patient(planback_client)
        assert body["closure"] == "open"
        assert "It is past" not in body["lines"][2]

    def test_the_expired_screen_keeps_the_deadline_and_names_the_route(
        self, overdue_client: tuple[TestClient, object]
    ) -> None:
        """Copy rules 4 and 5: the route is named and the deadline stays visible."""
        client, _ = overdue_client
        signed_create(client)
        service_intake(client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT})
        lines = assessed_patient(client)["lines"]
        assert len(lines) == 4
        assert fixture.DEADLINE_DISPLAY in lines[2]
        assert fixture.FALLBACK_ROUTE_TEXT in lines[3]
        assert "It is past" in lines[2]
        assert "!" not in " ".join(lines), "an exclamation mark alarms (copy rule 2)"


class TestSerializedPatientAndLedgerLabels:
    """Gate 4's named Slice 10 test."""

    def test_serialized_patient_and_ledger_labels(
        self, overdue_client: tuple[TestClient, object]
    ) -> None:
        """The expired copy carries the deadline and the named fallback, and the
        simulated label travels **inside** the serialized patient surface rather
        than only in page chrome (D11)."""
        client, _ = overdue_client
        signed_create(client)
        service_intake(client, EPISODE, json={"confirmed_text": fixture.BOUND_COMPLAINT})
        body = assessed_patient(client)

        assert fixture.DEADLINE_DISPLAY in body["lines"][2]
        assert fixture.FALLBACK_ROUTE_TEXT in body["lines"][3]

        # The label is in the same serialized object that carries the four lines.
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.JOURNEY_LABEL
        serialized = json.dumps(body, ensure_ascii=False)
        assert fixture.JOURNEY_LABEL in serialized

    def test_the_label_check_would_catch_a_projection_that_dropped_it(self) -> None:
        """A negative scan that has never detected its needle is not evidence."""
        assert fixture.FIXTURE_LABEL in json.dumps(
            {"simulated": True, "fixture_label": fixture.FIXTURE_LABEL},
            ensure_ascii=False,
        )


class TestAcceptanceClosesTheHandoffAndNeverEvidencesCare:
    """`POST /acceptances`. A D4 closure input that is not evidence."""

    def test_acceptance_is_not_care(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """Gate 4's named Slice 10 test. A named acceptance closes the handoff
        obligation and never sets `care_evidenced`."""
        service_consent(planback_client, EPISODE, json={"granted": True})
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/acceptances",
            json={"accepted_by": "caregiver", "accepted_scope": "handoff"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["closure"] == "closed_with_evidence"
        assert body["care_evidenced"] is False, "an acceptance became evidence"
        assert body["accepted_by"] == "caregiver"
        assert body["simulated"] is True

    def test_the_resolved_screen_renders_the_agreed_lines(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """F4, closed 8 October 2026. The derived screen serves the approved
        resolved rendering, and an acceptance alone says "agreed": it never
        sets `care_evidenced`, so line 1 never claims care happened."""
        service_consent(planback_client, EPISODE, json={"granted": True})
        planback_client.post(
            f"/api/episodes/{EPISODE}/acceptances", json={"accepted_by": "caregiver"}
        )
        body = assessed_patient(planback_client)
        assert body["closure"] == "closed_with_evidence"
        assert body["care_evidenced"] is False
        assert body["lines"][0] == "Someone has agreed to help."
        assert body["lines"][1] == "You do not need to act now."
        assert fixture.DEADLINE_DISPLAY in body["lines"][2]
        assert fixture.FALLBACK_ROUTE_TEXT in body["lines"][3]
        assert "does not happen" in body["lines"][3]
        assert "!" not in " ".join(body["lines"]), "an exclamation mark alarms"

    def test_an_unknown_party_is_refused_not_recorded(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """I4: the ledger names a party the policy can display, not free text."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/acceptances",
            json={"accepted_by": "a stranger"},
        )
        assert response.status_code == 422

    def test_an_acceptance_before_a_plan_is_a_409(
        self, planback_client: TestClient
    ) -> None:
        """There is no handoff obligation to close before there is a plan."""
        signed_create(planback_client)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/acceptances",
            json={"accepted_by": "caregiver"},
        )
        assert response.status_code == 409

    def test_an_unknown_episode_is_a_404(self, planback_client: TestClient) -> None:
        response = planback_client.post(
            "/api/episodes/does-not-exist/acceptances",
            json={"accepted_by": "caregiver"},
        )
        assert response.status_code == 404


class TestClosureRenderingsThroughTheDerivedRoute:
    """The remaining closure renderings, served by `GET /api/episodes/{id}`.

    F4 and F6-render, closed 8 October 2026: the approved wording now exists for
    every closure state, so the resolved and escalated screens render through the
    same derived path the unresolved and expired screens already used. The
    acceptance path ("Someone has agreed to help.") is pinned beside the
    acceptance route, in `TestAcceptanceClosesTheHandoffAndNeverEvidencesCare`.
    """

    def test_documented_evidence_renders_the_care_documented_lines(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """The derived path for documented, non-simulated evidence.

        The demo stack cannot produce this through its tool surface: every
        execution it runs is simulated, and a simulated receipt is never evidence
        (F5). So the row is written to the store directly, the way
        `state.record_callback_once` writes a real one, and the route must serve
        "Help is arranged." from it.
        """
        service_consent(planback_client, EPISODE, json={"granted": True})
        service = app.dependency_overrides[get_service]()
        service._store.record_evidence(
            EPISODE,
            EvidenceRecord(
                level=EvidenceLevel.DOCUMENTED,
                simulated=False,
                provenance="fictional provider receipt",
                source_ref="receipt-0001",
            ),
            now_utc=fixture.SCENARIO_NOW_UTC,
        )
        body = assessed_patient(planback_client)
        assert body["closure"] == "closed_with_evidence"
        assert body["care_evidenced"] is True
        assert body["lines"][0] == "Help is arranged."
        assert body["lines"][1] == "Nothing more is needed from you."
        assert fixture.DEADLINE_DISPLAY in body["lines"][2]
        assert fixture.FALLBACK_ROUTE_TEXT in body["lines"][3]
        assert "does not happen" in body["lines"][3]

    def test_an_escalation_renders_the_handed_to_a_human_lines(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """F6-render through the HTTP surface: the screen names the human path
        the handoff went to, and never tells the patient to act."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/escalations", json={"human_path": "nurse_line"}
        )
        assert response.status_code == 200
        body = assessed_patient(planback_client)
        assert body["closure"] == "escalated_to_human"
        assert body["lines"][0] == (
            f"We have passed this to {fixture.FALLBACK_ROUTE_TEXT}."
        )
        assert body["lines"][1] == "You do not need to act now."
        assert fixture.DEADLINE_DISPLAY in body["lines"][2]
        assert "Please act now" not in " ".join(body["lines"])


class TestRetiredPatientWrites:
    """Real authenticated HTTP must refuse before any persisted change."""

    @pytest.mark.parametrize("suffix,payload", [
        ("transcript-confirmations", {"corrected_text": CORRECT}),
        ("hint-events", {"hint_level": "H2", "event": "shown", "dwell_seconds": 4.2}),
        ("restatements", {"text": CORRECT, "hint_level": "H0"}),
        ("restatements/legacy-parent/repairs", {"text": CORRECT, "hint_level": "H0"}),
        ("barriers", {"barrier_text": "no transport", "proposed_route_id": "fictional_provider"}),
        ("actions", {"route_id": "fictional_provider", "purpose_id": "retired-post"}),
        ("consents", {"granted": True}),
    ])
    def test_retired_post_refuses_without_state_change(self, planback_client, assessed, monkeypatch, suffix, payload):
        monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-retirement-http")
        service = app.dependency_overrides[get_service]()
        before = tuple(service._store._conn.iterdump())
        response = planback_client.post(f"/api/episodes/{assessed}/{suffix}", json=payload,
            headers={"Authorization": "Bearer synthetic-retirement-http"})
        assert response.status_code == 422
        assert response.json() == {"detail": "journey command unavailable"}
        assert tuple(service._store._conn.iterdump()) == before

    def test_unsigned_create_and_free_text_intake_do_not_write(self, planback_client):
        service = app.dependency_overrides[get_service]()
        before = tuple(service._store._conn.iterdump())
        assert planback_client.post("/api/episodes").status_code == 422
        assert tuple(service._store._conn.iterdump()) == before
        assert signed_create(planback_client).status_code == 200
        before = tuple(service._store._conn.iterdump())
        response = planback_client.post(f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT})
        assert response.status_code == 422
        assert tuple(service._store._conn.iterdump()) == before
