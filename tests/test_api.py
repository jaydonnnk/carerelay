"""Slice 1 API tests. Each assertion must be able to fail (Gate 4 standing rules).

A test that cannot fail tests nothing, so each route contract below is paired
with the failure it is meant to catch: a removed route, a missing label, an
empty line. The `AssertionsHaveTeeth` class proves the two safety-shaped
assertions are not vacuous.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.api import app, get_service  # noqa: E402
from carerelay.coordinator import (  # noqa: E402
    AllowedPlanValues,
    CoordinatorUnavailable,
    LocalSimulationCoordinator,
)
from carerelay.demo import fixture  # noqa: E402
from carerelay.domain.models import ExtractedPlan  # noqa: E402
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
    return McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


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
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        policy_provenance="test: provisional",
    )
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()
    store.close()


@pytest.fixture()
def assessed(planback_client: TestClient) -> str:
    planback_client.post("/api/episodes")
    response = planback_client.post(
        f"/api/episodes/{EPISODE}/intake",
        json={"confirmed_text": fixture.BOUND_COMPLAINT},
    )
    assert response.status_code == 200
    return EPISODE


class TestEpisodeContract:
    def test_create_episode_returns_an_id_and_no_disposition(self, client: TestClient):
        response = client.post("/api/episodes")
        assert response.status_code == 200
        body = response.json()
        assert body["episode_id"] == fixture.DEMO_EPISODE_ID
        # 02-architecture.md 3.1: creating an episode must NOT write a disposition.
        assert "disposition" not in body

    def test_unknown_episode_is_404(self, client: TestClient):
        assert client.get("/api/episodes/does-not-exist").status_code == 404

    def test_episode_returns_exactly_four_lines(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        assert len(body["lines"]) == 4

    def test_no_line_is_empty(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        for line in body["lines"]:
            assert line.strip(), f"empty patient line in {body['lines']!r}"

    def test_line_three_carries_the_deadline(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        assert fixture.DEADLINE_DISPLAY in body["lines"][2]

    def test_line_four_names_the_fallback_route(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        assert fixture.FALLBACK_ROUTE_TEXT in body["lines"][3]

    def test_line_two_does_not_render_a_doubled_owner(self, client: TestClient):
        """Regression: "You or you must act now." was rendered by the live app.

        The approved copy rendered line 2 as "You or [named person] must act now.".
        With a patient owner that yields "You or you ...". Caught by inspection
        on 28 Sep 2026, not by a test, so this test now exists. The 2 October
        2026 wording pass changed the sentence to "Please act now: you, or
        [named person]." and the doubled-owner defect stays fixed.
        """
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        assert " or you " not in f" {body['lines'][1]} "
        assert "you or you" not in body["lines"][1].lower()


class TestSimulatedLabelTravelsWithTheData:
    """D11: the label must be in the projection, not only in page chrome."""

    def test_label_is_inside_the_serialized_projection(self, client: TestClient):
        client.post("/api/episodes")
        body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL

    def test_label_is_rendered_as_visible_text(self, client: TestClient):
        html = client.get("/").text
        assert fixture.FIXTURE_LABEL in html


class TestNoTimerOrAutoAdvance:
    """C8 / PLAN.md 5.2.1: nothing in the product times out or hides itself."""

    def test_page_contains_no_meta_refresh_or_script(self, client: TestClient):
        html = client.get("/").text.lower()
        assert "http-equiv=\"refresh\"" not in html
        assert "<script" not in html

    def test_stylesheet_has_no_animation_or_auto_hide(self):
        css = (Path(__file__).resolve().parents[1] / "src/carerelay/static/style.css").read_text()
        lowered = css.lower()
        for banned in ("animation:", "transition:", "@keyframes"):
            assert banned not in lowered, f"stylesheet uses {banned!r}"

    def test_the_page_links_a_stylesheet_the_app_actually_serves(
        self, client: TestClient
    ):
        """The Slice 6 review found this: the page linked `/static/style.css`, no
        mount served it, and the CSS test above read the file from disk so it never
        noticed. A 404 on the declared stylesheet means the page renders unstyled.
        """
        html = client.get("/").text
        assert 'href="/static/style.css"' in html
        served = client.get("/static/style.css")
        assert served.status_code == 200, "/static/style.css is linked but not served"
        assert "{" in served.text, "the stylesheet route returned an empty body"


class AssertionsHaveTeeth:
    """A green assertion that was never seen red is not evidence."""

    def test_line_count_assertion_catches_a_dropped_line(self, client: TestClient):
        """Mutate the fixture to three lines; the four-line test must fail."""
        original = fixture.demo_lines

        class ThreeLines:
            def as_tuple(self):
                return original().as_tuple()[:3]

        fixture.demo_lines = ThreeLines  # type: ignore[assignment]
        try:
            client.post("/api/episodes")
            body = client.get(f"/api/episodes/{fixture.DEMO_EPISODE_ID}").json()
            assert len(body["lines"]) != 4, "the four-line assertion is vacuous"
        finally:
            fixture.demo_lines = original  # type: ignore[assignment]

    def test_label_assertion_catches_a_stripped_label(self, client: TestClient):
        """An unlabelled simulated projection must be detectable."""
        original = fixture.FIXTURE_LABEL
        fixture.FIXTURE_LABEL = ""  # type: ignore[misc]
        try:
            response = client.get("/", params={"episode_id": fixture.DEMO_EPISODE_ID})
            assert fixture.FIXTURE_LABEL not in response.text, (
                "the label assertion cannot fail, so it proves nothing"
            )
        finally:
            fixture.FIXTURE_LABEL = original  # type: ignore[misc]


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
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
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
    def test_intake_issues_the_preauthored_plan(self, planback_client: TestClient):
        planback_client.post("/api/episodes")
        body = planback_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT},
        ).json()
        assert body["disposition_version"] == 1
        assert body["action_id"] == "attend_same_day_review"
        assert body["fallback_route_id"] == "nurse_line"

    def test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path(
        self, planback_client: TestClient
    ):
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": "something this fixture does not cover"},
        )
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
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": red_flag_text},
        )
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
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": f"  {fixture.BOUND_COMPLAINT.upper()}  "},
        )
        assert response.status_code == 200
        assert response.json()["disposition_version"] == 1

    def test_a_clean_restatement_is_understood(self, planback_client, assessed):
        body = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        ).json()
        assert body["understood"] is True
        assert body["mismatches"] == []
        assert body["outcome"] == "recall_unaided"

    def test_a_mismatch_names_one_field_to_repair(self, planback_client, assessed):
        body = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        ).json()
        assert body["mismatches"] == ["deadline_utc"]
        assert body["next_repair_field"] == "deadline_utc"
        assert body["routes_to_human_path"] is False

    def test_two_repairs_then_the_human_path(self, planback_client, assessed):
        first = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        ).json()
        rid = first["restatement_id"]

        second = planback_client.post(
            f"/api/episodes/{assessed}/restatements/{rid}/repairs",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        ).json()
        assert second["repair_round"] == 1

        third = planback_client.post(
            f"/api/episodes/{assessed}/restatements/{second['restatement_id']}/repairs",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        ).json()
        assert third["repair_round"] == 2
        assert third["routes_to_human_path"] is True
        assert third["human_path_route_id"] == "nurse_line"

        capped = planback_client.post(
            f"/api/episodes/{assessed}/restatements/{third['restatement_id']}/repairs",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        )
        assert capped.status_code == 409

    def test_a_restatement_before_any_plan_is_refused(self, planback_client):
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        )
        assert response.status_code == 409


class TestTranscriptConfirmationRoute:
    def test_an_unconfirmed_voice_restatement_is_refused(
        self, planback_client, assessed
    ):
        response = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": CORRECT, "hint_level": "H0", "input_mode": "voice"},
        )
        assert response.status_code == 409

    def test_a_confirmation_binds_to_the_text_being_scored(
        self, planback_client, assessed
    ):
        confirmation_id = planback_client.post(
            f"/api/episodes/{assessed}/transcript-confirmations",
            json={"corrected_text": CORRECT},
        ).json()["confirmation_id"]

        ok = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={
                "text": CORRECT,
                "hint_level": "H0",
                "input_mode": "voice",
                "transcript_confirmation_id": confirmation_id,
            },
        )
        assert ok.status_code == 200
        assert ok.json()["understood"] is True

        swapped = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={
                "text": "a different sentence entirely",
                "hint_level": "H0",
                "input_mode": "voice",
                "transcript_confirmation_id": confirmation_id,
            },
        )
        assert swapped.status_code == 409


class TestPatientSurfaceHasNoDwell:
    """C8 on the serialized surface: `dwell_seconds` is ledger-only."""

    def test_the_restatement_response_carries_no_dwell_marker(
        self, planback_client, assessed
    ):
        body = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": CORRECT, "hint_level": "H0", "dwell_seconds": 4.2},
        ).json()
        assert "dwell_seconds" not in body
        assert "4.2" not in str(body)

    def test_the_hint_event_response_carries_no_dwell_marker(
        self, planback_client, assessed
    ):
        body = planback_client.post(
            f"/api/episodes/{assessed}/hint-events",
            json={"hint_level": "H2", "event": "shown", "dwell_seconds": 4.2},
        ).json()
        assert body == {
            "episode_id": assessed,
            "hint_level": "H2",
            "card_visible": True,
        }, f"the hint response leaked a field: {body}"

    def test_the_dwell_marker_would_be_caught_if_it_were_there(self):
        """A negative scan that has never detected its needle is not evidence."""
        assert "dwell_seconds" in '{"dwell_seconds": 4.2}'


class TestPlanBackCarriesTheSimulatedLabel:
    def test_the_label_is_inside_the_restatement_projection(
        self, planback_client, assessed
    ):
        body = planback_client.post(
            f"/api/episodes/{assessed}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        ).json()
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL


class TestCoordinatorUnavailable:
    def test_the_flow_stops_with_a_text_fallback_and_scored_false(
        self, dead_client: TestClient
    ):
        dead_client.post("/api/episodes")
        dead_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT},
        )
        response = dead_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        )
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["scored"] is False
        assert detail["text_fallback"]

    def test_the_fallback_is_never_a_200_with_empty_mismatches(
        self, dead_client: TestClient
    ):
        """A 200 carrying empty mismatches would read as "you understood your
        plan", which is a false completion of exactly the kind I2 forbids."""
        dead_client.post("/api/episodes")
        dead_client.post(
            f"/api/episodes/{EPISODE}/intake",
            json={"confirmed_text": fixture.BOUND_COMPLAINT},
        )
        response = dead_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        )
        assert response.status_code != 200


# ---------------------------------------------------------------------------
# Slice 5: barriers, escalation and reassessment
# ---------------------------------------------------------------------------


class TestBarrierRoute:
    def test_a_permitted_route_returns_200(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/barriers",
            json={"barrier_text": "no transport today", "proposed_route_id": "nurse_line"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["permitted_route_id"] == "nurse_line"
        assert body["simulated"] is True
        assert body["fixture_label"] == fixture.FIXTURE_LABEL

    def test_no_proposal_is_accepted(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """Reporting a barrier without proposing a route is the common case."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/barriers",
            json={"barrier_text": "no transport today"},
        )
        assert response.status_code == 200
        assert response.json()["permitted_route_id"] is None

    def test_a_hallucinated_route_is_422_and_says_it_was_recorded(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/barriers",
            json={"barrier_text": "no transport", "proposed_route_id": "teleport_clinic"},
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["stopped_at"] == "human_path"
        assert detail["barrier_recorded"] is True

    def test_a_barrier_with_no_plan_is_409(self, planback_client: TestClient) -> None:
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/barriers",
            json={"barrier_text": "no transport today"},
        )
        assert response.status_code == 409

    def test_an_unknown_episode_is_404(self, planback_client: TestClient) -> None:
        response = planback_client.post(
            "/api/episodes/nope/barriers", json={"barrier_text": "no transport today"}
        )
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
        planback_client.post("/api/episodes")
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/reassessments", json={}
        )
        assert response.status_code == 409


#: A permitted route, and a purpose id. The purpose is part of the idempotency
#: triple, not part of the clinical vocabulary, so any string is legal here.
ROUTE = "fictional_provider"
PURPOSE = "book_transport"


class TestActionRoutes:
    """The Slice 6 action route.

    Every status code below was also observed against a live server on
    3 October 2026, because a 409 rendered by `TestClient` and a 409 rendered by
    uvicorn are not the same claim.
    """

    @staticmethod
    def _consent(client: TestClient) -> None:
        response = client.post(
            f"/api/episodes/{EPISODE}/consents", json={"granted": True}
        )
        assert response.status_code == 200

    def test_consent_returns_a_version_and_carries_the_label(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/consents", json={"granted": True}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["version"] == 1
        assert body["granted"] is True
        assert body["simulated"] is True

    def test_an_action_without_consent_is_409(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        )
        assert response.status_code == 409

    def test_an_action_opens_an_attempt_and_names_its_origin(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._consent(planback_client)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["duplicate"] is False
        assert body["origin"] == "local-sim"
        assert body["consent_version"] == 1
        assert body["outcome"] is not None
        assert body["provider_ref"]
        assert body["simulated"] is True

    def test_a_double_tap_returns_the_first_attempt_and_no_outcome(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """I3, at the HTTP boundary: the payload says it dispatched nothing."""
        self._consent(planback_client)
        first = planback_client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        ).json()
        second = planback_client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        ).json()
        assert second["attempt_id"] == first["attempt_id"]
        assert second["idempotency_key"] == first["idempotency_key"]
        assert second["duplicate"] is True
        assert second["outcome"] is None
        assert second["provider_ref"] is None

    def test_a_route_the_policy_does_not_permit_is_422_at_the_human_path(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        self._consent(planback_client)
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": "somewhere_else", "purpose_id": PURPOSE},
        )
        assert response.status_code == 422
        assert response.json()["detail"]["stopped_at"] == "human_path"

    def test_an_action_on_an_unknown_episode_is_404(
        self, planback_client: TestClient
    ) -> None:
        response = planback_client.post(
            "/api/episodes/nope/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        )
        assert response.status_code == 404


class TestCallbackRoute:
    """O5 at the HTTP boundary: applied, duplicate and refused are different."""

    def _opened(self, client: TestClient, assessed: str) -> str:
        TestActionRoutes._consent(client)
        response = client.post(
            f"/api/episodes/{EPISODE}/actions",
            json={"route_id": ROUTE, "purpose_id": PURPOSE},
        )
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
        revoked = planback_client.post(
            f"/api/episodes/{EPISODE}/consents", json={"granted": False}
        )
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
        assert planback_client.post("/api/episodes").status_code == 200

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
        response = planback_client.post("/api/episodes")
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    def test_a_wrong_token_is_401(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = planback_client.post(
            "/api/episodes", headers={"Authorization": "Bearer " + "w" * 32}
        )
        assert response.status_code == 401

    def test_the_right_token_passes(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = planback_client.post(
            "/api/episodes", headers={"Authorization": "Bearer " + "t" * 32}
        )
        assert response.status_code == 200

    def test_a_non_bearer_scheme_is_401(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A caller cannot smuggle the token in as a Basic credential."""
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        response = planback_client.post(
            "/api/episodes", headers={"Authorization": "Basic " + "t" * 32}
        )
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
        response = planback_client.post("/api/episodes")
        assert response.status_code == 503

    def test_public_env_is_armed_even_without_the_second_flag(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The deployment arms itself from `APP_ENV` alone."""
        monkeypatch.setenv("APP_ENV", "public")
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        assert planback_client.post("/api/episodes").status_code == 401

    def test_the_patient_fallback_page_is_not_guarded(
        self, planback_client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """It renders the fixture's static four lines and reads no record."""
        monkeypatch.setenv("CARERELAY_API_TOKEN", "t" * 32)
        assert planback_client.get("/").status_code == 200


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
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/hint-events",
            json={"hint_level": "H9", "event": "shown"},
        )
        assert response.status_code == 422

    def test_an_auto_hide_event_is_422_not_500(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """`auto_hide` is not in the vocabulary, because C8 forbids it."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/hint-events",
            json={"hint_level": "H2", "event": "auto_hide"},
        )
        assert response.status_code == 422

    def test_the_permitted_set_is_reported_so_the_refusal_is_actionable(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/hint-events",
            json={"hint_level": "H9", "event": "shown"},
        )
        assert "H3" in response.json()["detail"]

    def test_a_malformed_hint_level_on_a_restatement_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H9"},
        )
        assert response.status_code == 422

    def test_a_malformed_input_mode_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H0", "input_mode": "telepathy"},
        )
        assert response.status_code == 422

    def test_a_malformed_mode_on_a_repair_is_422(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        first = planback_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": WRONG_DAY, "hint_level": "H0"},
        )
        assert first.status_code == 200
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/restatements/"
            f"{first.json()['restatement_id']}/repairs",
            json={"text": CORRECT, "hint_level": "H1", "input_mode": "telepathy"},
        )
        assert response.status_code == 422

    def test_the_control_a_well_formed_event_still_records(
        self, planback_client: TestClient, assessed: str
    ) -> None:
        """Next to every defect case: the feature itself is not broken."""
        response = planback_client.post(
            f"/api/episodes/{EPISODE}/hint-events",
            json={"hint_level": "H2", "event": "shown"},
        )
        assert response.status_code == 200
        assert response.json()["card_visible"] is True
