"""The urgent path, reduced to the ordering property K2 asserts.

`03-program-design.md` §6.1 K2: the fixture's urgent guidance must render before any
PlanBack call is reached, so read-back can never gate or delay it.

Modelled as an event log across episode steps, not as a single function, because the
interesting failure is a *cross-step* ordering violation: read-back happening before
the guidance is shown.
"""

from __future__ import annotations

from . import fixture, planback

GUIDANCE_RENDERED = "urgent_guidance_rendered"
PLANBACK_EXTRACT = "planback_extract"


class RecordingCoordinator:
    """Stands in for the WorkBuddy coordinator. Records when PlanBack is reached."""

    def __init__(self, events: list[str], extracted: planback.ExtractedPlan | None = None):
        self.events = events
        self.extracted = extracted or planback.ExtractedPlan(None, None, None)

    def extract_plan(self, confirmed_text: str, allowed_values=None) -> planback.ExtractedPlan:
        self.events.append(PLANBACK_EXTRACT)
        return self.extracted


def render_urgent_guidance(events: list[str]) -> tuple[str, str, str, str]:
    """The four patient lines. Policy-owned text; no model output reaches the patient."""
    events.append(GUIDANCE_RENDERED)
    return (
        fixture.ACTION_TEXT,
        f"Before {fixture.DEADLINE_LABEL}",
        f"Who: {fixture.OWNER_LABEL}",
        f"If this is not possible: {fixture.FALLBACK_LABEL}",
    )


def intake(events: list[str]) -> tuple[str, str, str, str]:
    """Step 1. Renders the fixture's urgent guidance. Reaches no coordinator."""
    return render_urgent_guidance(events)


def submit_restatement(
    coordinator: RecordingCoordinator, events: list[str], confirmed_text: str
) -> planback.ExtractedPlan:
    """Step 2. Read-back. Legitimately reaches the coordinator — after step 1."""
    return coordinator.extract_plan(confirmed_text)


def intake_planback_first(
    coordinator: RecordingCoordinator, events: list[str], confirmed_text: str
) -> tuple[str, str, str, str]:
    """The deliberate single-branch defect: read-back gates the urgent path.

    Present so the K2 assertion can be shown to fail against a real defect rather
    than merely passing (03-program-design.md §5).
    """
    coordinator.extract_plan(confirmed_text)
    return render_urgent_guidance(events)


def assert_guidance_precedes_planback(events: list[str]) -> None:
    """K2. Raises if guidance was never rendered, or if PlanBack was reached first."""
    if GUIDANCE_RENDERED not in events:
        raise AssertionError(f"urgent guidance was never rendered: {events}")
    first_guidance = events.index(GUIDANCE_RENDERED)
    if PLANBACK_EXTRACT in events:
        first_planback = events.index(PLANBACK_EXTRACT)
        if first_planback < first_guidance:
            raise AssertionError(
                f"read-back was reached before urgent guidance: {events}"
            )
