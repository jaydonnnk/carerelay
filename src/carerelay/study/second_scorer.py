"""The second scorer's intake. Slice 9, recruitment preparation.

Protocol section 11: a response the scorer cannot classify is recorded verbatim
and resolved by the second scorer, **not by the facilitator who ran the
session**. Section 16: the scorer sees the answer key and the response, does not
see the project hypothesis, and does not run the sessions.

Before this module existed the queue was a dead end. `pending_second_scorer`
named the fields that needed a verdict and nothing could ever supply one, so a
single unclassifiable answer left the cut rule refusing forever: one "maybe"
would have blocked the kill test at any sample size, and the study would have
reported no Gate B result for a reason that had nothing to do with the
mechanism. This is the other half of that queue.

**Why a verdict is refused when it is `unclassified`.** A second scorer who
cannot classify the response has not resolved anything. Recording that as a
verdict would empty the queue without answering the question, which is the one
thing the queue exists to prevent.

**Why the scorer has to be named.** An anonymous verdict cannot be checked
against the facilitator, and section 16 is a rule about a person.

**Why a later decision wins.** The log is append-only, like the outcome sheet, so
a changed mind is a new row rather than an edit. Reading in file order and
letting the last row for a field stand keeps every verdict visible, including
the ones that were superseded.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from carerelay.study.outcomes import (
    ACTION_FIELD,
    DEADLINE_FIELD,
    FALSE_COMPLETION_FIELD,
    RESOLVABLE_FIELDS,
    resolve_all,
)
from carerelay.study.scoring import (
    CORRECT,
    FALSE_COMPLETION,
    INCORRECT,
    NO_FALSE_COMPLETION,
    UNCLASSIFIED,
)

#: The default decision log. Resolved from this file, like the other two.
DEFAULT_DECISIONS_PATH = (
    Path(__file__).resolve().parents[3] / "study" / "second-scorer.jsonl"
)

#: The verdicts each field accepts. The primary outcome is not a recall score,
#: so it takes its own two labels and never `correct` or `incorrect`: a
#: participant who answers "no" has answered correctly, and calling that
#: "incorrect" would read as a scoring error.
FIELD_VERDICTS: dict[str, tuple[str, ...]] = {
    ACTION_FIELD: (CORRECT, INCORRECT),
    DEADLINE_FIELD: (CORRECT, INCORRECT),
    FALSE_COMPLETION_FIELD: (FALSE_COMPLETION, NO_FALSE_COMPLETION),
}


class UnresolvedVerdict(ValueError):
    """A verdict that does not resolve the field it was given.

    Either it is `unclassified`, which is the question rather than the answer,
    or it is a label the field cannot carry, such as calling an action recall
    "false completion".
    """


class NotBlinded(ValueError):
    """The person scoring the response is the person who ran the session.

    Protocol section 16: the facilitator runs the session and does not score it,
    and the scorer does not run the sessions. A verdict from the facilitator is
    the blinding failure the section exists to prevent, and it is refused rather
    than recorded with a note, because a note is not blinding.
    """


@dataclass(frozen=True)
class SecondScorerDecision:
    """One verdict, for one field, on one dyad, by a named scorer."""

    dyad: str
    field: str
    verdict: str
    scorer: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.dyad.strip():
            raise ValueError("a decision names the dyad it resolves")
        if self.field not in RESOLVABLE_FIELDS:
            raise ValueError(
                f"{self.field!r} is not a field the second scorer resolves: "
                f"{', '.join(RESOLVABLE_FIELDS)}"
            )
        allowed = FIELD_VERDICTS[self.field]
        if self.verdict == UNCLASSIFIED or self.verdict not in allowed:
            raise UnresolvedVerdict(
                f"a verdict on {self.field} must be one of "
                f"{', '.join(allowed)}, not {self.verdict!r}: "
                f"'unclassified' is the question, not the answer"
            )
        if not self.scorer.strip():
            raise ValueError(
                "the scorer must be named: section 16 is a rule about a person, "
                "and an anonymous verdict cannot be checked against the "
                "facilitator who ran the session"
            )


def assert_blinded(scorer: str, facilitator: str) -> None:
    """Refuse a verdict from the person who ran the session.

    Protocol section 16. Both names are required: a check that accepted an empty
    facilitator would pass by default on the day it mattered.
    """
    if not scorer.strip():
        raise NotBlinded("the scorer must be named")
    if not facilitator.strip():
        raise NotBlinded(
            "the facilitator who ran the session must be named, or the "
            "blinding check cannot be made"
        )
    if scorer.strip().casefold() == facilitator.strip().casefold():
        raise NotBlinded(
            f"{scorer} ran the session and cannot score it: protocol section 16 "
            f"gives scoring to a second scorer who did not"
        )


def append_decision(decision: SecondScorerDecision, path: Path | None = None) -> Path:
    """Append one verdict. Returns the path written."""
    target = DEFAULT_DECISIONS_PATH if path is None else path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(decision), sort_keys=True, ensure_ascii=False)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
    return target


def read_decisions(path: Path | None = None) -> list[SecondScorerDecision]:
    """Read the decision log back, in the order the verdicts were written."""
    target = DEFAULT_DECISIONS_PATH if path is None else path
    if not target.exists():
        return []
    decisions: list[SecondScorerDecision] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        decisions.append(SecondScorerDecision(**json.loads(line)))
    return decisions


def resolutions_from(decisions: Iterable[SecondScorerDecision]) -> dict[tuple[str, str], str]:
    """The verdicts as `(dyad, field) -> verdict`, later decisions winning.

    A changed mind is a new row, so the last row for a field is the live one and
    the earlier ones stay in the log as evidence.
    """
    resolutions: dict[tuple[str, str], str] = {}
    for decision in decisions:
        resolutions[(decision.dyad, decision.field)] = decision.verdict
    return resolutions


def resolved_rows(
    rows: Sequence[object],
    decisions: Iterable[SecondScorerDecision] | None = None,
) -> list[object]:
    """The rows as the analysis reads them: the verdicts applied.

    Passed to `apply_cut_rule` and `render_result`, which take the rows they are
    given. The sheet is rendered from the **raw** rows, because protocol section
    12 is the raw sheet and the verbatim response is what the second scorer
    scored.
    """
    return resolve_all(rows, resolutions_from(decisions or []))
