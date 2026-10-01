"""The coordinator boundary, and its labelled local simulation.

`02-architecture.md` D8 pins the coordinator's contract: the coordinator
interprets, proposes and returns **structured values only**. It never writes to
the database, never sees credentials, and reaches the world only through the
MCP tool surface. This module owns one half of that contract at Slice 4: the
extraction boundary PlanBack depends on.

**This is not the platform path.** Section 3.3 pins the normative call path: the
coordinator executes the tool through the platform, and the failure event
originates there. No credentials exist at this slice (the Gate A spike is still
unrun), so extraction runs as a **labelled local simulation** and says so in two
places: the class attribute `simulated`, and every surface that presents a
result. Nothing here may be shown as a platform result.

ADR-0007 (Reading A) is the rule that shapes the boundary: the coordinator
returns **raw spans** and `domain` canonicalises them against the policy's
tables. It therefore receives only the policy's surface forms, never the
disposition's own values. A coordinator that could see the expected answer could
echo it back and pass the comparison vacuously, which is exactly the failure K1
exists to catch.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from carerelay.domain import rules
from carerelay.domain.models import ExtractedPlan


class CoordinatorError(Exception):
    """Base class for a coordinator that cannot answer."""


class CoordinatorUnavailable(CoordinatorError):
    """The coordinator could not be reached, or did not answer in time.

    `02-architecture.md` section 8 names this degraded state: the flow stops at
    the current question and shows a text fallback, because a coordinator stall
    on the PlanBack critical path is a demo-ending failure. Raising this says
    only that **the comparison did not happen**. The caller decides what "stop"
    renders; no restatement row is written, so nothing may later be presented as
    a scored round.
    """


@dataclass(frozen=True)
class AllowedPlanValues:
    """The surface forms a coordinator may look at, and nothing else.

    Built by the service from one `PolicyFixture`: the alias keys and canonical
    ids for the action and owner fields, and the relative-time forms for the
    deadline field. Carrying the forms separately from the `PolicyFixture`
    itself is what keeps the boundary honest: a coordinator handed this value
    can recognise a restatement's words but cannot see the expected values, so
    it cannot echo the answer.
    """

    action_forms: frozenset[str]
    owner_forms: frozenset[str]
    deadline_forms: frozenset[str]


class CoordinatorPort(Protocol):
    """The extraction boundary, as `03-program-design.md` section 3 fixes it.

    A structural Protocol on purpose: a test stub may implement the shape
    without inheriting, and `LocalSimulationCoordinator` subclasses it anyway
    so the boundary stays named where it matters.
    """

    simulated: bool

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        """Extract the three critical-field spans from a confirmed restatement.

        Returns raw spans only. Canonicalisation is `domain`'s job (ADR-0007),
        so a value returned here is resolved nowhere in this module.
        """
        ...


class LocalSimulationCoordinator(CoordinatorPort):
    """A deterministic, labelled stand-in for the WorkBuddy coordinator.

    It scans the confirmed restatement for the policy's surface forms and
    returns the longest match per critical field, or `None` when the text
    contains no form it recognises. It is a simulation of the recognition a
    model would perform, not a claim about one.

    Two honest limits, stated rather than hidden:

    * **It never flags doubt.** `ExtractedPlan.uncertain_fields` exists for a
      coordinator that half-heard an answer; this one either recognises a form
      or returns `None`, so its `uncertain_fields` is always empty. The field
      stays in the type because the real coordinator is expected to use it.
    * **It recognises only known forms.** A paraphrase outside the policy's
      tables resolves to nothing, and `domain` will call it `uncertain`, never
      a mismatch. That is the correct behaviour for an unknown span, and it is
      why the alias tables, not the matcher, decide what is understood.
    """

    simulated = True

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        text = rules.normalise(confirmed_text)
        return ExtractedPlan(
            action_span=_longest_form(text, allowed_values.action_forms),
            deadline_span=_longest_form(text, allowed_values.deadline_forms),
            next_owner_span=_longest_form(text, allowed_values.owner_forms),
        )


def _longest_form(text: str, forms: frozenset[str]) -> str | None:
    """The longest known form appearing in `text`, or `None`.

    Longest-match resolves overlaps: in "today before 18:00" the forms
    "today before 18:00" and (hypothetically) "today before" would both match,
    and the more specific one is the one a reader would mean.
    """
    best: str | None = None
    for form in forms:
        candidate = rules.normalise(form)
        if candidate and candidate in text:
            if best is None or len(candidate) > len(best):
                best = candidate
    return best
