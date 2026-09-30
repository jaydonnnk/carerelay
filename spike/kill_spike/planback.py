"""Deterministic PlanBack comparison, reduced to what the two kill conditions need.

`03-program-design.md` §3 fixes the real contract as
`compare_plan(expected, extracted, action_aliases)`. This spike widens it with
explicit resolution tables because the spike has to answer a question the contract
leaves open: **which layer owns canonicalisation.**

Two readings are possible and they give different kill-test results:

* Reading A — the coordinator returns RAW SPANS and `compare_plan` resolves them
  against the policy's alias and relative-time tables. The paraphrase / alias /
  "today before six" / code-switched half of the corpus is then testable as ordinary
  deterministic code. This is what the spike implements.
* Reading B — `ExtractedPlan.action_id: str | None` means the coordinator returns an
  already-canonical value, so canonicalisation happens inside the model. The corpus
  then only reaches the model, and K1 cannot be closed without a live coordinator.

The spike result is reported under Reading A and the residual under Reading B is
recorded separately. Gate 4 must pick one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

COMPARISON_FIELDS = ("action_id", "deadline_utc", "next_owner_id")


@dataclass(frozen=True)
class Disposition:
    action_id: str
    deadline_utc: datetime
    next_owner_id: str
    fallback_route_id: str


@dataclass(frozen=True)
class ExtractedPlan:
    """Raw spans, as a correct extractor would return them.

    `None` means the extractor did not commit to a value. `None` is never evidence
    that the patient is wrong.
    """

    action_span: str | None
    deadline_span: str | None
    next_owner_span: str | None


@dataclass(frozen=True)
class PlanComparison:
    matched: frozenset[str]
    mismatched: frozenset[str]
    uncertain: frozenset[str]

    def is_clean(self) -> bool:
        """True only when every critical field was resolved AND agreed.

        Deliberately stricter than "no mismatch". A comparator that answers
        "uncertain" to everything has zero false mismatches and is useless: read-back
        would repair nothing and the patient would be pushed to the human path every
        time. K1 must not be passable by refusing to commit.
        """
        return not self.mismatched and not self.uncertain


def normalise(text: str) -> str:
    return " ".join(text.strip().casefold().split())


def resolve_action(
    span: str | None, aliases: dict[str, str], allowed: frozenset[str]
) -> str | None:
    if span is None:
        return None
    key = normalise(span)
    if key in aliases:
        return aliases[key]
    if key in allowed:
        return key
    return None


def resolve_owner(
    span: str | None, aliases: dict[str, str], allowed: frozenset[str]
) -> str | None:
    if span is None:
        return None
    key = normalise(span)
    if key in aliases:
        return aliases[key]
    if key in allowed:
        return key
    return None


def resolve_deadline(
    span: str | None,
    now_utc: datetime,
    display_tz: tzinfo,
    forms: dict[str, tuple[int, str]],
) -> datetime | None:
    """Resolve a relative phrase to a canonical instant, never compare raw text."""
    if span is None:
        return None
    key = normalise(span)
    if key not in forms:
        return None
    day_offset, hhmm = forms[key]
    hour, minute = (int(part) for part in hhmm.split(":"))
    local = now_utc.astimezone(display_tz)
    target = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    target += timedelta(days=day_offset)
    return target.astimezone(now_utc.tzinfo)


def compare_plan(
    expected: Disposition,
    extracted: ExtractedPlan,
    *,
    action_aliases: dict[str, str],
    owner_aliases: dict[str, str],
    allowed_actions: frozenset[str],
    allowed_owners: frozenset[str],
    deadline_forms: dict[str, tuple[int, str]],
    now_utc: datetime,
    display_tz: tzinfo,
) -> PlanComparison:
    resolved = (
        (
            "action_id",
            resolve_action(extracted.action_span, action_aliases, allowed_actions),
            expected.action_id,
        ),
        (
            "deadline_utc",
            resolve_deadline(extracted.deadline_span, now_utc, display_tz, deadline_forms),
            expected.deadline_utc,
        ),
        (
            "next_owner_id",
            resolve_owner(extracted.next_owner_span, owner_aliases, allowed_owners),
            expected.next_owner_id,
        ),
    )

    matched: set[str] = set()
    mismatched: set[str] = set()
    uncertain: set[str] = set()

    for field_name, got, want in resolved:
        if got is None:
            # Unknown extraction is never a claimed error and never a claimed success.
            uncertain.add(field_name)
        elif got == want:
            matched.add(field_name)
        else:
            # Only a known, different canonical value is a mismatch.
            mismatched.add(field_name)

    return PlanComparison(frozenset(matched), frozenset(mismatched), frozenset(uncertain))


def next_repair(comparison: PlanComparison, completed_rounds: int) -> str | None:
    """Field-by-field repair, bounded. A third round is never offered."""
    if completed_rounds >= 2:
        return None
    for field_name in COMPARISON_FIELDS:
        if field_name in comparison.mismatched or field_name in comparison.uncertain:
            return field_name
    return None
