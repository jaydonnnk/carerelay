"""Slice 1 API tests. Each assertion must be able to fail (Gate 4 standing rules).

A test that cannot fail tests nothing, so each route contract below is paired
with the failure it is meant to catch: a removed route, a missing label, an
empty line. The `AssertionsHaveTeeth` class proves the two safety-shaped
assertions are not vacuous.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.api import app  # noqa: E402
from carerelay.demo import fixture  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


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
