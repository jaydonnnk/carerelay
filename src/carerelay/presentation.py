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

__all__ = ["PatientSurface", "patient_surface"]


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
