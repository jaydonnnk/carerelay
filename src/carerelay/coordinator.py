"""The coordinator boundary, and its labelled local simulation.

`02-architecture.md` D8 pins the coordinator's contract: the coordinator
interprets, proposes and returns **structured values only**. It never writes to
the database, never sees credentials, and reaches the world only through the
MCP tool surface. This module owns that contract: the extraction boundary
PlanBack depends on (Slice 4), and the execution boundary the action path
depends on (Slice 6).

**This is not the platform path.** Section 3.3 pins the normative call path: the
coordinator executes the tool through the platform, and the failure event
originates there. No tool is executed through a platform in this build, so both
boundaries here run as a **labelled local simulation** and say so in three
places: the class attribute `simulated`, the `origin` on every execution result,
and every surface that presents one. Nothing here may be shown as a platform
result.

**Gate A, 2 October 2026, and what it did not settle.** The spike passed against
the live ADP endpoint and proved the transport carries a platform-attributable
origin signal. It did not prove tool execution: Q3's failure was a validation
rejection provoked by a malformed body. D8 says ADP may occupy the interpretation
step only and cannot carry the section 3.3 claim. The platform-advantage claim
is therefore weakened and stated as weakened, and `origin` stays `local-sim`.

ADR-0007 (Reading A) is the rule that shapes the extraction boundary: the
coordinator returns **raw spans** and `domain` canonicalises them against the
policy's tables.

**NF5, corrected 3 October 2026.** Earlier drafts of this file claimed the
coordinator "cannot see the expected values". That overclaimed.
`AllowedPlanValues` carries the alias keys **and** the canonical ids for the
action and owner fields, so the expected values are present in the set. The
honest claim is the one the load-bearing half needs: the coordinator cannot
determine **which** candidate is expected, because the sets are unordered and
carry no pairing between a surface form and the disposition's value; and it never
sees the `Disposition` at all, so it cannot read the answer off the plan and echo
it back. Both halves are stated below rather than the flattering one.
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from carerelay.domain import rules
from carerelay.domain.models import ExtractedPlan
from carerelay.tools import McpTools, ToolResult


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

    Built by the service from one `PolicyFixture`: the alias keys **and** the
    canonical ids for the action and owner fields, plus the relative-time forms
    for the deadline field. The canonical ids are included because a restatement
    may legitimately use one verbatim.

    **What this does and does not hide (NF5).** The expected action and owner are
    members of these sets, so this value does not hide them. What it hides is
    the *pairing*: the sets are unordered and carry no link from a form to the
    disposition's value for that field, so a coordinator handed this cannot tell
    which of several recognised spans is the one the plan names. It also never
    receives the `Disposition`, so it cannot read the answer off the plan. It
    can recognise a restatement's words; it cannot determine which candidate is
    expected, and it cannot look the answer up.
    """

    action_forms: frozenset[str]
    owner_forms: frozenset[str]
    deadline_forms: frozenset[str]


@dataclass(frozen=True)
class ToolRequest:
    """Internal action identity and the original process's dispatch permit.

    Patient words and plan values stay outside execution. The permit is never
    serialized into tool JSON or returned to a browser.
    """

    episode_id: str
    route_id: str
    attempt_key: str
    disposition_version: int | None = None
    permit: object | None = None


class CoordinatorPort(Protocol):
    """The extraction and execution boundaries.

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

    def execute_tool(self, request: ToolRequest, *, now_utc: datetime) -> ToolResult:
        """Execute one tool for one already-opened attempt.

        `03-program-design.md` section 3 and `02-architecture.md` section 3.3
        both put the coordinator in the execution path: the attempt is opened
        first, the coordinator executes, and the outcome comes back with an
        `origin` that says where it came from.

        The attempt must already exist. A coordinator that could open one would
        also be able to choose the route, which is `domain.validate_route`'s job
        and no one else's.
        """
        ...


class LocalSimulationCoordinator(CoordinatorPort):
    """A deterministic, labelled stand-in for the platform coordinator.

    It scans the confirmed restatement for the policy's surface forms and
    returns the longest match per critical field, or `None` when the text
    contains no form it recognises. It executes through the injected MCP tool
    surface, so the same authorisation, consent and attempt-key rechecks apply
    to it as to any other caller of that surface.

    It is a simulation of the recognition and the dispatch a platform would
    perform, not a claim about one.

    Two honest limits, stated rather than hidden:

    * **Negation and doubt are conservative uncertainty.** Known forms inside
      a negated, conditional, alternative or questioning sentence cannot prove
      understanding. This scanner does not resolve linguistic scope or corrections;
      it marks affected fields uncertain, never a definite patient mistake.
    * **It recognises only known forms.** A paraphrase outside the policy's
      tables resolves to nothing, and `domain` will call it `uncertain`, never
      a mismatch. That is the correct behaviour for an unknown span, and it is
      why the alias tables, not the matcher, decide what is understood.
    """

    simulated = True

    def __init__(self, tools: McpTools) -> None:
        """`tools` is required, not optional.

        An execution boundary with no tool surface wired is a misconfiguration,
        and failing at construction says so where a reader can see it. Defaulting
        it and raising later would turn a wiring mistake into a runtime refusal
        that looks like a policy decision.
        """
        self._tools = tools

    @property
    def origin(self):
        """Every result this coordinator returns carries this origin."""
        return self._tools.origin

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        text = rules.normalise(confirmed_text).replace("’", "'")
        forms = {
            "action_id": allowed_values.action_forms,
            "deadline_utc": allowed_values.deadline_forms,
            "next_owner_id": allowed_values.owner_forms,
        }
        spans = {field: _longest_form(text, values) for field, values in forms.items()}
        uncertain = set()
        # Keep question marks so a question containing the whole answer cannot pass.
        for sentence in re.findall(r"[^.!?;]+[.!?;]?", text):
            if _DOUBT.search(sentence):
                if _PLAN_REFERENCE.search(sentence):
                    uncertain.update(forms)
                for field, values in forms.items():
                    if _longest_form(sentence, values) is not None:
                        uncertain.add(field)
        return ExtractedPlan(
            action_span=spans["action_id"],
            deadline_span=spans["deadline_utc"],
            next_owner_span=spans["next_owner_id"],
            uncertain_fields=frozenset(uncertain),
        )

    def execute_tool(self, request: ToolRequest, *, now_utc: datetime) -> ToolResult:
        """Dispatch through the MCP tool surface.

        The rechecks are the tool's, not this class's: authorisation, consent and
        the attempt key are enforced in `tools`, so a coordinator cannot reach
        past them by calling the provider directly. This method adds nothing to
        that and short-circuits nothing.
        """
        return self._tools.submit_simulated_request(
            request.episode_id,
            request.route_id,
            request.attempt_key,
            now_utc=now_utc,
            permit=request.permit,
        )


# A correction can negate the prior sentence without repeating its fields.
_PLAN_REFERENCE = re.compile(
    r"\b(?:it|that|this|actually|will not|won't|do not|don't|cannot|can't|should not|shouldn't)\b"
    r"|^\s*(?:no|not|never)\s*[.!?;]?\s*$"
)

_DOUBT = re.compile(
    r"\b(?:not|no|never|cannot|unsure|uncertain|maybe|perhaps|might|may|could|would|if|or)\b"
    r"|\b\w+n't\b|\?|不|没|未"
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
        # Latin words must be whole words: "me" inside "appointment" is no owner.
        # Chinese forms have no spaces between words, so retain their literal match.
        pattern = re.escape(candidate)
        if candidate and candidate[0].isascii() and candidate[0].isalnum():
            pattern = r"(?<!\w)" + pattern
        if candidate and candidate[-1].isascii() and candidate[-1].isalnum():
            pattern += r"(?!\w)"
        if candidate and re.search(pattern, text):
            if best is None or len(candidate) > len(best):
                best = candidate
    return best


__all__ = [
    "AllowedPlanValues",
    "CoordinatorError",
    "CoordinatorPort",
    "CoordinatorUnavailable",
    "LocalSimulationCoordinator",
    "ToolRequest",
]
