"""JSON-only presentation of the derived closure.

`02-architecture.md` D2 puts the trust boundary at the module boundary, and this
module sits on the *outside* of it: it turns values `domain` has already decided
into the JSON the API returns. It makes **no** decision of its own, reads no
clock and touches no store, so it has no way to introduce a rule.

**JSON only.** The patient screen's HTML lives with the route that serves it.
Nothing here composes markup, and nothing here composes patient-facing words:
every string arrives from `domain.patient_lines`, which takes them from
`PolicyText`. A presentation layer that could author a sentence would be a
second place for unapproved copy to enter the product, which is exactly what the
copy rules in `02-architecture.md` section 7 forbid.

**The simulated label travels inside the surface.** D11 requires the label to be
serialised with the clinical data rather than only rendered as page chrome,
because a projection that drops it is a false-completion path. `as_dict` keeps
`simulated` and `fixture_label` as siblings of `lines`, and carries `closure` and
`care_evidenced` beside them so a caller can tell a resolved episode from an
unresolved one without re-deriving it.
"""

from __future__ import annotations

from dataclasses import dataclass

from carerelay.domain.models import ClosureProjection

__all__ = [
    "FaultAssertion",
    "LedgerSurface",
    "OptionsSurface",
    "PatientSurface",
    "RouteOption",
    "patient_surface",
]


@dataclass(frozen=True)
class PatientSurface:
    """The patient projection as JSON: four lines, the axes, and the label.

    `lines` is a tuple, not a list, so the value cannot be mutated between the
    decision in `domain` and the serialisation here. `as_dict` converts it at
    the edge, which is the only place a list is correct.
    """

    episode_id: str
    lines: tuple[str, str, str, str]
    closure: str
    care_evidenced: bool
    simulated: bool
    fixture_label: str

    def as_dict(self) -> dict[str, object]:
        """The serialised surface. Order is stable so a test can pin it."""
        return {
            "episode_id": self.episode_id,
            "lines": list(self.lines),
            "closure": self.closure,
            "care_evidenced": self.care_evidenced,
            "simulated": self.simulated,
            "fixture_label": self.fixture_label,
        }


def patient_surface(
    episode_id: str,
    lines: tuple[str, str, str, str],
    closure: ClosureProjection,
    fixture_label: str,
) -> PatientSurface:
    """Assemble the patient projection from values `domain` already decided.

    Every argument is an input: this function chooses none of them. The closure
    axes are copied straight through so the JSON cannot disagree with the rule
    that produced it.
    """
    return PatientSurface(
        episode_id=episode_id,
        lines=lines,
        closure=closure.closure.value,
        care_evidenced=closure.care_evidenced,
        simulated=closure.simulated,
        fixture_label=fixture_label,
    )


# ---------------------------------------------------------------------------
# Slice 12: the judge ledger and the permitted-route projection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RouteOption:
    """One permitted route, as a screen or the ledger may name it.

    `display` comes from `PolicyText.route_display_by_id` and from nothing else,
    so a raw route id cannot reach a surface unnamed. This module composes no
    wording of its own, which is what keeps unapproved copy out of the product.
    """

    route_id: str
    display: str


@dataclass(frozen=True)
class OptionsSurface:
    """`GET /options`: what this episode's current disposition permits.

    The set is `PolicyFixture.permitted_route_ids` and the words are
    `PolicyText.route_display_by_id`. Both are policy data already loaded, so
    this projection decides nothing: it renders what the policy says.
    """

    episode_id: str
    disposition_version: int | None
    routes: tuple[RouteOption, ...]
    available_origin: str
    simulated: bool
    fixture_label: str

    def as_dict(self) -> dict[str, object]:
        """The serialised options. Order is stable so a test can pin it."""
        return {
            "episode_id": self.episode_id,
            "disposition_version": self.disposition_version,
            "routes": [
                {"route_id": r.route_id, "display": r.display} for r in self.routes
            ],
            "available_origin": self.available_origin,
            "simulated": self.simulated,
            "fixture_label": self.fixture_label,
        }


@dataclass(frozen=True)
class FaultAssertion:
    """One invariant, and what the record says about it at this instant.

    **Reporting only, and that is the point.** These values are derived for a
    reader who is meant to check them: no rule in `domain` and no write path
    reads them, so a wrong verdict here cannot move an episode. `evidence`
    carries the raw values the verdict was taken from, so a reader can disagree
    with the verdict rather than only accept it.
    """

    invariant: str
    holds: bool
    evidence: str

    def as_dict(self) -> dict[str, object]:
        return {
            "invariant": self.invariant,
            "holds": self.holds,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class LedgerSurface:
    """`GET /ledger`: the judge-facing read projection for one episode.

    A read of the record and of the derived closure, nothing more. The two axes
    are copied straight through from `ClosureProjection`, so the ledger cannot
    disagree with the rule that produced them, and every row below is a stored
    row rather than a summary: the ledger exists so a judge can check the claim
    instead of taking it.

    **The ledger does not run the expiry read-path.** The patient projection
    does, because a patient read is the trigger that records an expiry. A judge
    opening the ledger is not a clinical event, so this projection never writes:
    reading the evidence must not change it.

    `dwell_seconds` rides on the hint and restatement rows, and nowhere in the
    patient surface (`PLAN.md` 5.2.1, constraint C8).
    """

    episode_id: str
    axes: dict[str, object]
    disposition_version: int | None
    attempts: tuple[dict[str, object], ...]
    callbacks: tuple[dict[str, object], ...]
    evidence: tuple[dict[str, object], ...]
    events: tuple[dict[str, object], ...]
    expiry: tuple[dict[str, object], ...]
    restatements: tuple[dict[str, object], ...]
    hint_events: tuple[dict[str, object], ...]
    barriers: tuple[dict[str, object], ...]
    escalation: dict[str, object] | None
    acceptance: dict[str, object] | None
    #: Every distinct failure-event origin present in this episode. A platform
    #: failure and a local-simulation failure are distinguishable by inspection
    #: here, which is what `02-architecture.md` 3.3 requires.
    origins: tuple[str, ...]
    dwell_seconds_total: float | None
    fault_assertions: tuple[FaultAssertion, ...]
    simulated: bool
    fixture_label: str

    def as_dict(self) -> dict[str, object]:
        """The serialised ledger. Order is stable so a test can pin it."""
        return {
            "episode_id": self.episode_id,
            "axes": self.axes,
            "disposition_version": self.disposition_version,
            "attempts": list(self.attempts),
            "callbacks": list(self.callbacks),
            "evidence": list(self.evidence),
            "events": list(self.events),
            "expiry": list(self.expiry),
            "restatements": list(self.restatements),
            "hint_events": list(self.hint_events),
            "barriers": list(self.barriers),
            "escalation": self.escalation,
            "acceptance": self.acceptance,
            "origins": list(self.origins),
            "dwell_seconds_total": self.dwell_seconds_total,
            "fault_assertions": [a.as_dict() for a in self.fault_assertions],
            "simulated": self.simulated,
            "fixture_label": self.fixture_label,
        }
