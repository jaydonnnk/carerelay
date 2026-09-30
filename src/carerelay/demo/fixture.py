"""The hardcoded demo episode — Slice 1 only.

Slice 1 is the tracer bullet: one mocked endpoint and a stubbed UI, wired end to
end. It does almost nothing, but it runs.

Everything here is deliberately **hardcoded**. There is no domain layer, no
database, no coordinator and no policy engine yet — those arrive in Slices 2 and 3.
The four-line shape below is the contract the later slices must keep, so the
tracer bullet fixes it now.

Two rules already hold in this file, because retrofitting them later is how they
get lost:

* **No timer, countdown or auto-advance.** The plan card stays until the patient
  hides it (`PLAN.md` 5.2.1). There is nothing here that hides anything.
* **The simulated label is part of the patient-visible data**, not page chrome.
  An unlabelled simulated receipt is a D11 violation even at Slice 1.
"""

from __future__ import annotations

from dataclasses import dataclass

# Slice 1 placeholder. The judged fixture must be sourced verbatim from
# attributable published guidance (Option C) before any participant sees it.
FIXTURE_LABEL = "SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."
POLICY_VERSION = "fixture-provisional-0"
DEMO_EPISODE_ID = "demo-episode-001"

ACTION_TEXT = "Go to the fictional provider's same-day review."
DEADLINE_DISPLAY = "6pm today"
OWNER_DISPLAY = "Myself"  # named owner; see the note on `demo_lines`
FALLBACK_ROUTE_TEXT = "the fictional nurse line"


@dataclass(frozen=True)
class PatientLines:
    """The four lines the patient sees, and nothing else (`PLAN.md` 6.1).

    Order is part of the contract: line 3 carries the deadline, line 4 names the
    fallback route. The expired rendering (`02-architecture.md` 7) is a different
    set of four lines and arrives with the Closure Contract in Slice 9.
    """

    line_1: str
    line_2: str
    line_3: str
    line_4: str
    simulated: bool

    def as_tuple(self) -> tuple[str, str, str, str]:
        return (self.line_1, self.line_2, self.line_3, self.line_4)


def demo_lines() -> PatientLines:
    """The unresolved rendering: 'we tried and nobody said yes.'

    Hardcoded for Slice 1. Slice 9 derives this from `domain.patient_lines`
    against the two axes, so the wording stops being a literal.

    **Line 2 note.** `PLAN.md` 6.1 and `02-architecture.md` 7 both render line 2
    as "You or *[named person]* must act now.", and `01-product.md` does the
    same. Taken literally with a patient owner that produces "You or you must
    act now." — a malformed sentence, caught by inspection of the running app on
    28 September 2026, not by the test suite. It is corrected here to a straight
    naming of the owner.

    **This is a real divergence from three approved documents and it is flagged,
    not silently absorbed.** The correction belongs in the source documents at
    the next Gate 1 touch. Slice 9 must implement whichever form those documents
    then carry — this line is not the authority.
    """
    return PatientLines(
        line_1="Help is not arranged.",
        line_2=f"{OWNER_DISPLAY} must act now.",
        line_3=f"Before {DEADLINE_DISPLAY}.",
        line_4=f"If this route fails, call {FALLBACK_ROUTE_TEXT}.",
        simulated=True,
    )
