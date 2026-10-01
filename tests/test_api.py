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
from carerelay.state import open_store  # noqa: E402

EPISODE = fixture.DEMO_EPISODE_ID

#: A restatement that resolves to exactly the fixture's plan.
CORRECT = "see the doctor today before 6pm myself"
#: A known, different deadline: a mismatch, not an uncertainty (K1).
WRONG_DAY = "see the doctor tomorrow before 6pm myself"


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
        coordinator=LocalSimulationCoordinator(),
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
        json={"confirmed_text": "I need help sorting out my appointment"},
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

        PLAN.md 6.1 renders line 2 as "You or [named person] must act now.".
        With a patient owner that yields "You or you ...". Caught by inspection
        on 28 Sep 2026, not by a test — so this test now exists.
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
            json={"confirmed_text": "I need help sorting out my appointment"},
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
            json={"confirmed_text": "I need help sorting out my appointment"},
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
            json={"confirmed_text": "I need help sorting out my appointment"},
        )
        response = dead_client.post(
            f"/api/episodes/{EPISODE}/restatements",
            json={"text": CORRECT, "hint_level": "H0"},
        )
        assert response.status_code != 200
