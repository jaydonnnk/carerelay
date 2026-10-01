"""PROVISIONAL fixture for the §6.1 kill-test spike. Not sourced. Not reusable.

Superseded 1 October 2026. The paragraph below describes Option C as open. It is
not: the source check ran, no source cleared, and Option C contradicted Option A,
so the user answered "drop" and `03-program-design.md` section 6.2 now carries
Option A alone (see `00-status.md`).

Option C — the fixture wording copied verbatim from attributable published guidance —
is still open: no source selected, licensing and Singapore applicability unchecked
(`03-program-design.md` §6.2). Nothing here may be shown to a participant, and none of
it may be carried into the judged fixture until that check is done.

No real healthcare facility is named. The provider and the fallback route are
explicitly fictional, per the Gate 1 rule.

The wording below is a placeholder chosen only to exercise two properties:
whether the deterministic comparison falsely flags a correct restatement, and whether
the urgent path can ever be reached after read-back. It asserts no clinical threshold.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import planback

# Singapore has had a fixed UTC+8 offset with no DST since 1982, so a fixed offset is
# exact. Used in preference to zoneinfo to avoid an install: no dependency is
# authorised by Gate 3.
DISPLAY_TZ = timezone(timedelta(hours=8), "SGT")

# Fixed scenario clock: 09:00 SGT, before the 18:00 deadline. Deterministic on purpose.
SCENARIO_NOW_UTC = datetime(2026, 9, 26, 1, 0, tzinfo=timezone.utc)

POLICY_VERSION = "spike-provisional-0"
EPISODE_ID = "spike-episode-001"

ACTION_ID = "attend_same_day_review"
DEADLINE_LOCAL_HHMM = "18:00"
NEXT_OWNER_ID = "patient"
FALLBACK_ROUTE_ID = "nurse_line"

ACTION_TEXT = "PROVISIONAL placeholder: attend the fictional provider's same-day review"
DEADLINE_LABEL = "18:00 today"
OWNER_LABEL = "you"
FALLBACK_LABEL = "the fictional nurse line"

ALLOWED_ACTION_IDS = frozenset(
    {"attend_same_day_review", "call_nurse_line", "wait_and_monitor"}
)
ALLOWED_OWNER_IDS = frozenset({"patient", "caregiver"})
PERMITTED_ROUTE_IDS = frozenset({"fictional_provider", "nurse_line"})

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

# Normalised surface phrase -> (day offset, local HH:MM). The last three resolve to a
# KNOWN DIFFERENT instant on purpose: a known wrong value must be a mismatch, not an
# "uncertain". That distinction is the whole point of §5's test row.
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

# The fixed adversarial corpus of CORRECT restatements (03-program-design.md §6.1).
# (label, form class, action span, deadline span, owner span)
CORPUS = (
    ("exact canonical", "exact", ACTION_ID, "today before 18:00", "patient"),
    ("paraphrase", "paraphrase", "go to the clinic", "today before 6pm", "you"),
    ("alias and word numeral", "alias", "see the doctor", "today before six", "me"),
    ("reordered relative time", "relative_time", "the polyclinic", "before six today", "myself"),
    ("code-switched Mandarin", "code_switched", "去诊所", "今天六点前", "我自己"),
    ("tight relative form", "relative_time", "go down to the clinic", "by 6 today", "you"),
)

# A corpus that does not cover these four classes is not the corpus §6.1 asked for.
REQUIRED_FORM_CLASSES = frozenset(
    {"paraphrase", "alias", "relative_time", "code_switched"}
)

COMPARISON_FIELDS = ("action_id", "deadline_utc", "next_owner_id")


def disposition(now_utc: datetime = SCENARIO_NOW_UTC) -> planback.Disposition:
    """The fixture's one pre-authored disposition, anchored to the scenario clock."""
    hour, minute = (int(part) for part in DEADLINE_LOCAL_HHMM.split(":"))
    local = now_utc.astimezone(DISPLAY_TZ)
    deadline_local = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return planback.Disposition(
        action_id=ACTION_ID,
        deadline_utc=deadline_local.astimezone(timezone.utc),
        next_owner_id=NEXT_OWNER_ID,
        fallback_route_id=FALLBACK_ROUTE_ID,
    )
