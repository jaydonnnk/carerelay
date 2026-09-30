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
FALLBACK_ROUTE_TEXT = "the fictional nurse line"

#: Line 2, for a demo episode whose owner is the patient. `domain.rules.patient_lines`
#: owns this rule and renders a third-party owner as "You or [name] must act now.";
#: this fixture has one hardcoded episode, so it carries the self-owner form only.
#: `fixtures/scripted_episode.json` agrees: its `next_owner_id` is `patient`.
SELF_OWNER_SENTENCE = "You must act now."


@dataclass(frozen=True)
class PatientLines:
    """The four lines the patient sees, and nothing else (`PLAN.md` 6.1).

    Order is part of the contract: line 3 carries the deadline, line 4 names the
    fallback route. The expired rendering (`02-architecture.md` 7) is a different
    set of four lines and arrives with the Closure Contract in Slice 10.
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

    Hardcoded for Slice 1. Slice 10 derives this from `domain.patient_lines`
    against the two axes, so the wording stops being a literal.

    **Line 2 note.** `PLAN.md` 6.1, `02-architecture.md` 7 and `01-product.md` all
    render line 2 as "You or *[named person]* must act now." Taken literally with
    a patient owner that produced "You or you must act now.", a malformed
    sentence, caught by inspection of the running app on 28 September 2026, not
    by the test suite.

    The Slice 1 band-aid was `OWNER_DISPLAY = "Myself"`, which rendered "Myself
    must act now." and was itself malformed. **Slice 2 now owns this rule:**
    `domain.rules.patient_lines` composes line 2 by owner, rendering a self owner
    as "You must act now." This fixture mirrors that form, because the demo
    episode's owner is the patient.

    **This remains a real divergence from three approved documents, flagged and
    not silently absorbed.** The correction belongs in those documents at the next
    Gate 1 touch, and `00-status.md` records the reading at the Slice 2 section.
    Slice 10 replaces this fixture with `domain.patient_lines` and implements
    whichever form the documents then carry; this line is not the authority.
    """
    return PatientLines(
        line_1="Help is not arranged.",
        line_2=SELF_OWNER_SENTENCE,
        line_3=f"Before {DEADLINE_DISPLAY}.",
        line_4=f"If this route fails, call {FALLBACK_ROUTE_TEXT}.",
        simulated=True,
    )
