"""The hardcoded demo episode, and its PROVISIONAL policy.

Slice 1 built the tracer bullet: one mocked endpoint and a stubbed UI, wired end
to end, with no database, no domain layer and no coordinator. Slice 4 keeps the
tracer bullet's four-line contract and adds the policy values PlanBack needs to
have something to compare against.

Everything here is **provisional and hardcoded**. It is not sourced, and at
Slice 5 it stopped trying to be: **Option C was dropped on 1 October 2026** after
the source check cleared no source and found that Option C contradicted Option A
(`03-program-design.md` section 6.2). MOH clause 11 and HealthHub clause 12.1 both
require prior written permission, the UK Open Government Licence route fails
Singapore applicability, and a fixture built from fictional entities cannot be
quoted verbatim from any published guidance at all.

**What makes this honest now is the absence of a claim, not the presence of a
citation.** No value here names a symptom, an urgency, a threshold or a real
facility. **Nothing here may be shown to a participant**, and no value here is a
clinical threshold: there is no reviewer, so none may be authored
(`03-program-design.md` section 8 item 2).

Three rules already hold in this file, because retrofitting them later is how
they get lost:

* **No timer, countdown or auto-advance.** The plan card stays until the patient
  hides it (`PLAN.md` 5.2.1). There is nothing here that hides anything.
* **The simulated label is part of the patient-visible data**, not page chrome.
  An unlabelled simulated receipt is a D11 violation even at Slice 1.
* **The change vocabulary is empty on purpose.** `permitted_change_codes` and
  `authorised_reassessments` carry nothing, so every reassessment fails closed to
  the human path (D7). That is the honest state until a reviewer authorises a
  branch; inventing codes here would make an unauthorised clinical branch look
  approved.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from carerelay.domain.models import (
    Disposition,
    DispositionSource,
    PolicyFixture,
    PolicyText,
)

# Slice 1 placeholder, and still a placeholder at Slice 5: Option C was dropped
# on 1 October 2026, so this wording is authored and carries no clinical claim.
FIXTURE_LABEL = "SIMULATED — RESEARCH DEMONSTRATION. Not clinical advice."
POLICY_VERSION = "fixture-provisional-0"
DEMO_EPISODE_ID = "demo-episode-001"

ACTION_TEXT = "Go to the fictional provider's same-day review."
DEADLINE_DISPLAY = "6pm today"
FALLBACK_ROUTE_TEXT = "the fictional nurse line"

#: Line 2, for a demo episode whose owner is the patient. `domain.rules.patient_lines`
#: owns this rule and renders a third-party owner as "Please act now: you, or
#: [name]."; this fixture has one hardcoded episode, so it carries the self-owner
#: form only. `fixtures/scripted_episode.json` agrees: its `next_owner_id` is
#: `patient`. Reworded 2 October 2026 with the rest of the patient copy.
SELF_OWNER_SENTENCE = "Please act now."


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
    rendered line 2 as "You or *[named person]* must act now." Taken literally with
    a patient owner that produced "You or you must act now.", a malformed
    sentence, caught by inspection of the running app on 28 September 2026, not
    by the test suite.

    The Slice 1 band-aid was `OWNER_DISPLAY = "Myself"`, which rendered "Myself
    must act now." and was itself malformed. **Slice 2 now owns this rule:**
    `domain.rules.patient_lines` composes line 2 by owner, rendering a self owner
    as "Please act now." This fixture mirrors that form, because the demo
    episode's owner is the patient.

    **The divergence from three approved documents was closed on 2 October 2026,
    not carried further.** The wording pass re-approved all three documents to
    the "Please act now." form, so the fixture and `domain.patient_lines` now
    agree with them rather than diverging. Slice 10 still replaces this fixture
    with `domain.patient_lines`; this line is not the authority.
    """
    return PatientLines(
        line_1="No one has agreed to help yet.",
        line_2=SELF_OWNER_SENTENCE,
        line_3=f"Please do it before {DEADLINE_DISPLAY}.",
        line_4=f"If that does not work, call {FALLBACK_ROUTE_TEXT}.",
        simulated=True,
    )


# ---------------------------------------------------------------------------
# The provisional policy
# ---------------------------------------------------------------------------

#: Singapore has had a fixed UTC+8 offset with no DST since 1982, so a fixed
#: offset is exact. Used in preference to `zoneinfo` so no dependency is added:
#: Gate 3 authorises no install beyond the declared test dependencies.
DISPLAY_TZ = timezone(timedelta(hours=8), "SGT")

#: The demo scenario instant: 09:00 SGT, before the 18:00 deadline. Deterministic
#: on purpose, so a walkthrough and a test see the same "today".
SCENARIO_NOW_UTC = datetime(2026, 9, 30, 1, 0, tzinfo=timezone.utc)

ACTION_ID = "attend_same_day_review"
DEADLINE_LOCAL_HHMM = "18:00"
NEXT_OWNER_ID = "patient"
FALLBACK_ROUTE_ID = "nurse_line"

PERMITTED_ROUTE_IDS = frozenset({"fictional_provider", "nurse_line"})
PERMITTED_ACTION_IDS = frozenset(
    {ACTION_ID, "call_nurse_line", "wait_and_monitor"}
)
PERMITTED_OWNER_IDS = frozenset({NEXT_OWNER_ID, "caregiver"})

#: Empty on purpose, and **still empty at the close of Slice 5**. See the module
#: docstring: with no reviewer, no symptom-change code may be permitted, so
#: `domain.rules.reassessment_decision` stops every reassessment at the human
#: path (D7). Dropping Option C did not change this: a sourced fixture would have
#: been evidence that a code is attributable, never authority to act on it. The
#: set is filled only by a reviewer-authorised branch, and no reviewer exists.
PERMITTED_CHANGE_CODES: frozenset[str] = frozenset()

#: Surface phrases the resolver accepts, not clinical content. Carried from the
#: Slice 0 kill-test spike, which is where the K1 corpus was proved.
ACTION_ALIASES = {
    "go to the clinic": ACTION_ID,
    "attend the clinic": ACTION_ID,
    "go down to the clinic": ACTION_ID,
    "see the doctor": ACTION_ID,
    "the polyclinic": ACTION_ID,
    "去诊所": ACTION_ID,
    "看医生": ACTION_ID,
}

OWNER_ALIASES = {
    "you": NEXT_OWNER_ID,
    "me": NEXT_OWNER_ID,
    "myself": NEXT_OWNER_ID,
    "the patient": NEXT_OWNER_ID,
    "我自己": NEXT_OWNER_ID,
}

#: Normalised surface phrase -> (day offset, local HH:MM). The last two resolve to
#: a KNOWN DIFFERENT instant on purpose: a known wrong value must be a mismatch,
#: not an "uncertain". That distinction is the whole point of kill condition K1.
DEADLINE_FORMS = {
    "today before 18:00": (0, "18:00"),
    "today before 6pm": (0, "18:00"),
    "today before six": (0, "18:00"),
    "before six today": (0, "18:00"),
    "by 6 today": (0, "18:00"),
    "今天六点前": (0, "18:00"),
    "today before 8pm": (0, "20:00"),
    "今天八点前": (0, "20:00"),
    "tomorrow before 6pm": (1, "18:00"),
}

#: The one complaint this fixture is bound to. Deliberately non-clinical: it names
#: no symptom, urgency or threshold, because none may be authored before a
#: reviewer exists. Intake accepts **this exact complaint**, normalised for case
#: and whitespace, and stops at the human path for anything else
#: (`03-program-design.md` section 4).
#:
#: **The rule was a substring match until 2 October 2026.** It read "contains this
#: phrase", so a text carrying a red-flag symptom alongside the phrase, such as
#: "help sorting out my appointment, also I have chest pain and cannot breathe",
#: was bound to the demo plan instead of stopping. Finding B3 in the Slice 4
#: adversarial review measured that. The rule is now an exact normalised match,
#: which is what the documents already claimed.
BOUND_COMPLAINT = "help sorting out my appointment"


def policy() -> PolicyFixture:
    """The one provisional policy version. Not sourced; see the module docstring."""
    return PolicyFixture(
        version=POLICY_VERSION,
        permitted_route_ids=PERMITTED_ROUTE_IDS,
        permitted_action_ids=PERMITTED_ACTION_IDS,
        permitted_owner_ids=PERMITTED_OWNER_IDS,
        permitted_change_codes=PERMITTED_CHANGE_CODES,
        action_aliases=ACTION_ALIASES,
        owner_aliases=OWNER_ALIASES,
        deadline_forms=DEADLINE_FORMS,
        authorised_reassessments={},
    )


def policy_text() -> PolicyText:
    """Policy-owned patient wording.

    `deadline_display_by_version` is keyed by disposition version because a
    reassessment inserts a new version with a new deadline, and one fixed string
    would then describe the wrong instant (`domain.models.PolicyText`).
    """
    return PolicyText(
        policy_version=POLICY_VERSION,
        fixture_label=FIXTURE_LABEL,
        deadline_display_by_version={1: DEADLINE_DISPLAY},
        self_owner_id=NEXT_OWNER_ID,
        owner_display_by_id={NEXT_OWNER_ID: "you", "caregiver": "your daughter"},
        route_display_by_id={
            "fictional_provider": "the fictional provider",
            FALLBACK_ROUTE_ID: FALLBACK_ROUTE_TEXT,
        },
        simulated=True,
    )


def deadline_utc(now_utc: datetime) -> datetime:
    """The fixture deadline: 18:00 SGT on the local day `now_utc` falls in."""
    hour, minute = (int(part) for part in DEADLINE_LOCAL_HHMM.split(":"))
    local = now_utc.astimezone(DISPLAY_TZ)
    return local.replace(hour=hour, minute=minute, second=0, microsecond=0).astimezone(
        timezone.utc
    )


def disposition(episode_id: str, now_utc: datetime) -> Disposition:
    """The fixture's one pre-authored plan, anchored to the caller's clock.

    `source` is `fixture`, never `reviewer`: no reviewer has authorised anything.
    """
    return Disposition(
        episode_id=episode_id,
        version=1,
        policy_version=POLICY_VERSION,
        action_id=ACTION_ID,
        clinical_deadline_utc=deadline_utc(now_utc),
        next_owner_id=NEXT_OWNER_ID,
        fallback_route_id=FALLBACK_ROUTE_ID,
        source=DispositionSource.FIXTURE,
    )
