"""The Gate B outcome record, the cut rule and the reporting rules. Slice 9.

This module is the response path `00-status.md` said Slice 9 had to build. It
carries the frozen allocation order, one row per dyad, the pre-registered cut
rule from protocol section 13, and the reporting rules from section 15.

**What it deliberately does not do.** It does not recruit, it does not run a
session, and it does not decide anything a participant said. It scores a response
against the answer key, refuses when it cannot, and writes the result down under
the rules that were frozen before the first dyad.

**The three refusals that matter most.** The cut rule refuses to run while any
row's both-correct field is unclassified, because section 13 reads that field and
a guess there would decide the kill test. It refuses below three analysed dyads per
condition, the floor section 13 gained on 7 October 2026 before the first session,
because section 15 forbids a human-centred claim at that size and a decision should
not rest on evidence that cannot support a claim. And it refuses when the two
conditions are not the same size, because section 13 defines the rule for
equal-sized conditions only and applying it otherwise would be a post-hoc
reinterpretation that section 17 requires to be recorded as one.

**An unknown is never reported as a wrong answer.** The cut rule refuses while
a row is unclassified, and the write-up has to refuse the same way: a count of
the dyads that got both fields right cannot distinguish a dyad that got one
wrong from one nobody has scored yet, so the both-correct section reports all
three labels instead of one. Printing the second as the first is a guess that
looks like a measurement.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from carerelay.study.scoring import (
    CORRECT,
    INCORRECT,
    UNCLASSIFIED,
    classify,
    classify_false_completion,
    score_action_option,
    score_deadline_option,
)

#: The two conditions, protocol section 2. A is CareRelay, B is the fixed card.
APPLICATION_CONDITION = "A"
CARD_CONDITION = "B"
CONDITIONS: tuple[str, ...] = (APPLICATION_CONDITION, CARD_CONDITION)

#: The frozen allocation order, protocol sections 3 and 12. Position 1 takes A,
#: position 2 takes B, and so on to twelve. No participant chooses a condition and
#: no dyad switches after assignment.
ALLOCATION_ORDER: dict[int, str] = {
    position: (APPLICATION_CONDITION if position % 2 == 1 else CARD_CONDITION)
    for position in range(1, 13)
}

#: Hint levels, condition A only. Condition B has no read-back, so it has none.
HINT_LEVELS: tuple[str, ...] = ("H0", "H1", "H2", "H3")

#: The protocol's frozen reporting rule, in code. Section 15: no percentage below
#: ten participants in total, and no human-centred validation claim below three
#: dyads in either condition. `MIN_DYADS_PER_CONDITION` is also the cut rule's
#: minimum sample, added to section 13 on 7 October 2026 before the first session:
#: the same three-dyad floor that stops a claim stops a decision.
MIN_PARTICIPANTS_FOR_PERCENTAGES = 10
MIN_DYADS_PER_CONDITION = 3

#: The recruitment target, protocol section 4, and a different number from the
#: floor above. Section 15 states the result in these terms: six per condition
#: is a directional decision, not efficacy evidence. The directional caveat
#: refers to the target, so a write-up that quoted the three-dyad floor there
#: would understate what was actually aimed for.
TARGET_DYADS_PER_CONDITION = 6

#: The three fields a second scorer may resolve, named once here. The queue
#: below and the intake in `second_scorer.py` both read these, so a verdict can
#: never be filed against a field the queue does not carry, and the queue can
#: never name a field the intake refuses.
ACTION_FIELD = "action recall"
DEADLINE_FIELD = "deadline recall"
FALSE_COMPLETION_FIELD = "false completion"
RESOLVABLE_FIELDS: tuple[str, ...] = (
    ACTION_FIELD,
    DEADLINE_FIELD,
    FALSE_COMPLETION_FIELD,
)

#: The two outcomes of the pre-registered cut rule.
CUT = "cut"
KEEP = "keep"


class NoGateBResult(ValueError):
    """No analysed dyad, so there is no Gate B result.

    Protocol section 18: no dyads means no Gate B result. The run was cut before
    any recruitment was attempted, so this is not a failed recruitment and **not**
    a null result either. A null result would read as evidence that the mechanism
    survived.
    """


class UnequalConditions(ValueError):
    """The two conditions are not the same size.

    Protocol section 13 states the cut rule for equal-sized conditions only.
    Applying it to unequal ones would invent a comparison the protocol does not
    contain, which section 17 requires to be recorded as a post-hoc change.
    """


class UnresolvedResponses(ValueError):
    """A row the second scorer has not resolved yet.

    Protocol section 11 sends an unclassifiable response to the second scorer,
    and section 13 reads the both-correct field. Running the cut rule before the
    second scorer has resolved them decides the kill test on an unanswered row.
    """


class BelowMinimumSample(ValueError):
    """The cut rule's minimum sample is not met.

    Protocol section 13, as amended on 7 October 2026 before the first session:
    the rule is not applied below three dyads per condition. Section 15 forbids a
    human-centred claim at that size, and a decision should not rest on evidence
    that cannot support a claim. A study that stops below the minimum is reported
    as having reached no Gate B result, never as a result that kept PlanBack.
    """


def condition_for_position(position: int) -> str:
    """The condition a frozen position carries."""
    if position not in ALLOCATION_ORDER:
        raise ValueError(
            f"position {position} is not in the frozen allocation order "
            f"(1 to {max(ALLOCATION_ORDER)})"
        )
    return ALLOCATION_ORDER[position]


def next_position(used: Iterable[int]) -> int:
    """The next unused position in the frozen order.

    Protocol section 3: a dyad takes the next unused position, and the
    facilitator records the position used, so a skipped or abandoned session
    leaves a named gap rather than a silent resequencing. A withdrawn dyad keeps
    its position for exactly that reason, which is why `withdrawn` is a flag on
    the row and not a deletion.
    """
    taken = set(used)
    unknown = sorted(taken - set(ALLOCATION_ORDER))
    if unknown:
        raise ValueError(f"positions outside the frozen order: {unknown}")
    for position in sorted(ALLOCATION_ORDER):
        if position not in taken:
            return position
    raise ValueError("all twelve allocation positions are used")


@dataclass(frozen=True)
class OutcomeRow:
    """One dyad's row on the protocol section 12 sheet.

    The three recall fields hold the **verbatim** response, not a score. The
    scores are properties computed from that text, so a row can never carry a
    score that disagrees with what the participant said, and the verbatim text is
    always there for the second scorer.

    The two recall fields are scored from the **option chosen**, recorded in
    `action_option` and `deadline_option` after the amendment of 8 October 2026.
    The words are still kept, because they are what the second scorer reads, but
    they are not what the scorer scores: a closed question needs no vocabulary of
    paraphrases, which is the gap the amendment exists to close.
    """

    dyad: str
    position: int
    condition: str
    task_time_s: int
    action_recall: str
    deadline_recall: str
    false_completion: str
    barrier_recognised: bool | None
    burden: int
    hint_level: str | None = None
    #: The option chosen on the closed recall questions, A to D. Empty means no
    #: option was recorded, which is the one recall case the second scorer still
    #: resolves, so it scores unclassified rather than being guessed.
    action_option: str = ""
    deadline_option: str = ""
    adverse_reaction: str = ""
    notes: str = ""
    withdrawn: bool = False

    def __post_init__(self) -> None:
        if self.condition not in CONDITIONS:
            raise ValueError(f"unknown condition: {self.condition!r}")
        expected = condition_for_position(self.position)
        if self.condition != expected:
            raise ValueError(
                f"position {self.position} carries condition {expected}, "
                f"not {self.condition}: the allocation order is frozen"
            )
        if self.task_time_s < 0:
            raise ValueError(f"task time cannot be negative: {self.task_time_s}")
        if not 1 <= self.burden <= 5:
            raise ValueError(f"burden is a five-point rating, 1 to 5: {self.burden}")
        if self.hint_level is not None and self.condition != APPLICATION_CONDITION:
            raise ValueError(
                f"condition {self.condition} has no read-back, so it has no hint "
                f"level: {self.hint_level!r}"
            )
        if self.hint_level is not None and self.hint_level not in HINT_LEVELS:
            raise ValueError(f"unknown hint level: {self.hint_level!r}")

    @property
    def action_label(self) -> str:
        return classify(score_action_option, self.action_option)

    @property
    def deadline_label(self) -> str:
        return classify(score_deadline_option, self.deadline_option)

    @property
    def false_completion_label(self) -> str:
        return classify_false_completion(self.false_completion)

    @property
    def both_correct(self) -> str:
        """Protocol section 9: the conjunction of the two recall fields.

        An unclassified recall makes the conjunction unclassified, never
        incorrect. Section 13 reads this field to decide whether PlanBack is cut,
        so recording a guess here would kill or save the mechanism on a guess.
        """
        return both_correct_from(self.action_label, self.deadline_label)


def both_correct_from(action_label: str, deadline_label: str) -> str:
    """Protocol section 9: the conjunction of the two recall fields.

    An unclassified recall makes the conjunction unclassified, never incorrect.
    Section 13 reads this field to decide whether PlanBack is cut, so recording
    a guess here would kill or save the mechanism on a guess.

    It is defined once, here, and both the row's own view and the second
    scorer's resolved view read it, so the two cannot disagree about what the
    conjunction means.
    """
    if UNCLASSIFIED in (action_label, deadline_label):
        return UNCLASSIFIED
    if action_label == CORRECT and deadline_label == CORRECT:
        return CORRECT
    return INCORRECT


def analysed(rows: Sequence[OutcomeRow]) -> list[OutcomeRow]:
    """The rows an analysis may read: withdrawn dyads excluded.

    Protocol section 4: a withdrawn dyad's row is marked withdrawn and is
    excluded from the analysis. It is not deleted, so its allocation position
    stays recorded as the gap section 3 asks for.
    """
    return [row for row in rows if not row.withdrawn]


def dyad_counts(rows: Sequence[OutcomeRow]) -> dict[str, int]:
    """Analysed dyads per condition."""
    counts = {condition: 0 for condition in CONDITIONS}
    for row in analysed(rows):
        counts[row.condition] += 1
    return counts


def both_correct_counts(rows: Sequence[OutcomeRow]) -> dict[str, int]:
    """Dyads with both recall fields correct, per condition.

    Protocol section 11: this is the field the cut rule reads.

    **It is not a report of outcomes.** A row that is not `CORRECT` is simply not
    counted, so an unclassified row is absent from this number rather than
    recorded as a failure. That is right for a comparison and wrong for a
    write-up, so `render_result` reports `both_correct_breakdown` and never this.
    """
    counts = {condition: 0 for condition in CONDITIONS}
    for row in analysed(rows):
        if row.both_correct == CORRECT:
            counts[row.condition] += 1
    return counts


def both_correct_breakdown(
    rows: Sequence[OutcomeRow],
) -> dict[str, dict[str, int]]:
    """Both-correct per condition, split by label.

    Three numbers per condition, because one number cannot tell a dyad that got
    the field wrong from a dyad nobody has scored yet, and reporting the second
    as the first is an unknown printed as a wrong answer.
    """
    counts = {
        condition: {CORRECT: 0, INCORRECT: 0, UNCLASSIFIED: 0}
        for condition in CONDITIONS
    }
    for row in analysed(rows):
        counts[row.condition][row.both_correct] += 1
    return counts


def burden_ratings(rows: Sequence[OutcomeRow]) -> dict[str, list[int]]:
    """The raw burden ratings per condition, 1 to 5."""
    ratings: dict[str, list[int]] = {condition: [] for condition in CONDITIONS}
    for row in analysed(rows):
        ratings[row.condition].append(row.burden)
    return ratings


def median_burden(rows: Sequence[OutcomeRow]) -> dict[str, float]:
    """The median burden rating per condition.

    Section 13 compares medians, with task time reported separately and not
    folded into the burden comparison. A condition with no analysed dyad has no
    median, and that raises rather than returning zero: a zero would be the
    lowest burden any card could beat.
    """
    ratings = burden_ratings(rows)
    medians: dict[str, float] = {}
    for condition, values in ratings.items():
        if not values:
            raise NoGateBResult(f"condition {condition} has no analysed dyad")
        medians[condition] = float(statistics.median(values))
    return medians


def pending_second_scorer(rows: Sequence[OutcomeRow]) -> list[tuple[str, str, str]]:
    """The fields a second scorer still has to resolve, as (dyad, field, text).

    Protocol section 11: an unclassifiable response is recorded verbatim and
    resolved by the second scorer, not by the facilitator who ran the session.
    This is the list that makes an unnamed second scorer a visible gap rather
    than a silent one.
    """
    pending: list[tuple[str, str, str]] = []
    for row in analysed(rows):
        if row.action_label == UNCLASSIFIED:
            pending.append((row.dyad, ACTION_FIELD, row.action_recall))
        if row.deadline_label == UNCLASSIFIED:
            pending.append((row.dyad, DEADLINE_FIELD, row.deadline_recall))
        if row.false_completion_label == UNCLASSIFIED:
            pending.append((row.dyad, FALSE_COMPLETION_FIELD, row.false_completion))
    return pending


@dataclass(frozen=True)
class ResolvedRow:
    """One dyad's row as the analysis reads it, with the verdicts applied.

    **Why a wrapper and not a rewrite.** The sheet row keeps the verbatim
    response, because the second scorer scores the words the participant said
    and protocol section 12 is the raw sheet. Substituting a canonical string
    for a resolved field would make the analysis view look exactly like a
    record while quietly no longer holding what was said. So the verdict is
    carried alongside the row and the labels are read through it.

    Every attribute this wrapper does not decide is the row's own value, so it
    can be handed to the cut rule, the counters and the write-up unchanged.
    """

    row: OutcomeRow
    resolutions: Mapping[tuple[str, str], str]

    def __getattr__(self, name: str) -> object:
        """Delegate anything this wrapper does not decide to the row itself."""
        if name == "row":
            raise AttributeError(name)
        return getattr(self.row, name)

    def _label(self, field_name: str, fallback: str) -> str:
        """The second scorer's verdict if there is one, else the scorer's label.

        The fallback is what the *first* scorer could decide. A field with no
        verdict keeps that label, unresolved ones included, so an unanswered
        field cannot quietly become an answer.
        """
        verdict = self.resolutions.get((self.row.dyad, field_name))
        return fallback if verdict is None else verdict

    @property
    def action_label(self) -> str:
        return self._label(ACTION_FIELD, self.row.action_label)

    @property
    def deadline_label(self) -> str:
        return self._label(DEADLINE_FIELD, self.row.deadline_label)

    @property
    def false_completion_label(self) -> str:
        return self._label(FALSE_COMPLETION_FIELD, self.row.false_completion_label)

    @property
    def both_correct(self) -> str:
        return both_correct_from(self.action_label, self.deadline_label)


def resolve_all(
    rows: Sequence[OutcomeRow],
    resolutions: Mapping[tuple[str, str], str] | None = None,
) -> list[ResolvedRow]:
    """Every row as the analysis reads it, with the verdicts applied.

    Pass the result to `apply_cut_rule` and `render_result`. Do **not** pass it
    to `render_outcome_sheet`, which is the raw sheet, and never write it back:
    this is a view for the analysis, not a record.
    """
    given = {} if resolutions is None else dict(resolutions)
    return [ResolvedRow(row=row, resolutions=given) for row in rows]


@dataclass(frozen=True)
class CutDecision:
    """The pre-registered cut rule applied to a set of rows."""

    outcome: str
    reason: str
    both_correct: dict[str, int]
    median_burden: dict[str, float]


def apply_cut_rule(rows: Sequence[OutcomeRow]) -> CutDecision:
    """Apply the pre-registered cut rule, protocol section 13.

    Condition 1 is the only one still live: conditions 2 and 3 are pure system
    properties that passed offline at Slice 0 and are recorded in section 14.

    PlanBack is cut when the card achieves equal action and deadline recall with
    lower burden. "Equal recall" means the card has at least as many dyads with
    both fields correct; "lower burden" means a lower median burden rating. The
    rule is not applied below `MIN_DYADS_PER_CONDITION` dyads per condition.
    """
    live = analysed(rows)
    if not live:
        raise NoGateBResult(
            "no analysed dyad: recruitment failed, so there is no Gate B result"
        )

    sizes = dyad_counts(rows)
    if sizes[APPLICATION_CONDITION] != sizes[CARD_CONDITION]:
        raise UnequalConditions(
            f"the cut rule is defined for equal-sized conditions: "
            f"A has {sizes[APPLICATION_CONDITION]}, B has {sizes[CARD_CONDITION]}"
        )

    if min(sizes.values()) < MIN_DYADS_PER_CONDITION:
        raise BelowMinimumSample(
            f"the cut rule has a minimum sample of {MIN_DYADS_PER_CONDITION} "
            f"dyads per condition, and this study has "
            f"A {sizes[APPLICATION_CONDITION]}, B {sizes[CARD_CONDITION]}: "
            f"no cut or keep decision is available"
        )

    pending = pending_second_scorer(rows)
    if pending:
        raise UnresolvedResponses(
            f"{len(pending)} response(s) await the second scorer, and the cut "
            f"rule reads the field they decide: {pending}"
        )

    counts = both_correct_counts(rows)
    medians = median_burden(rows)
    recall_at_least_equal = counts[CARD_CONDITION] >= counts[APPLICATION_CONDITION]
    lower_burden = medians[CARD_CONDITION] < medians[APPLICATION_CONDITION]

    if recall_at_least_equal and lower_burden:
        return CutDecision(
            outcome=CUT,
            reason=(
                f"the card matched or beat CareRelay on both-correct recall "
                f"(B {counts[CARD_CONDITION]} vs A {counts[APPLICATION_CONDITION]}) "
                f"with a lower median burden "
                f"(B {medians[CARD_CONDITION]} vs A {medians[APPLICATION_CONDITION]})"
            ),
            both_correct=counts,
            median_burden=medians,
        )
    return CutDecision(
        outcome=KEEP,
        reason=(
            f"the card did not meet both halves of the rule: both-correct recall "
            f"B {counts[CARD_CONDITION]} vs A {counts[APPLICATION_CONDITION]}, "
            f"median burden B {medians[CARD_CONDITION]} vs A "
            f"{medians[APPLICATION_CONDITION]}"
        ),
        both_correct=counts,
        median_burden=medians,
    )


def render_outcome_report(counts: Mapping[str, int]) -> list[str]:
    """Render outcome counts under the protocol's frozen reporting rule.

    Raw counts are always reported. A percentage is added only when the total
    reaches `MIN_PARTICIPANTS_FOR_PERCENTAGES`, because a percentage over a
    smaller sample states more than the sample can carry.
    """
    if not counts:
        raise ValueError("no counts to report")
    ordered = sorted(counts.items())
    lines = [f"{condition}: {n} dyads" for condition, n in ordered]
    total = sum(counts.values())
    if total >= MIN_PARTICIPANTS_FOR_PERCENTAGES:
        lines.extend(
            f"{condition}: {n / total:.0%} of {total}" for condition, n in ordered
        )
    return lines


def hcd_claim_supported(counts: Mapping[str, int]) -> bool:
    """Whether a sample supports a human-centred validation claim.

    Protocol section 15: fewer than three dyads in either condition means no such
    claim. An empty condition is a zero, not an exemption.
    """
    if not counts:
        return False
    return min(counts.values()) >= MIN_DYADS_PER_CONDITION


#: The protocol section 12 columns. The two recall columns carry the **option
#: chosen**, A to D, and not the participant's words: section 12 as amended on
#: 8 October 2026, and the score is derived from the option so the sheet cannot
#: disagree with the scorer. The words are rendered into Notes.
SHEET_COLUMNS: tuple[str, ...] = (
    "Dyad",
    "Position",
    "Condition",
    "Task time (s)",
    "Action recall",
    "Deadline recall",
    "Both correct",
    "False completion",
    "Barrier recognised",
    "Burden (1-5)",
    "Hint level (A only)",
    "Adverse reaction",
    "Notes",
)


def _notes_cell(row: OutcomeRow) -> str:
    """The Notes cell: what the facilitator wrote, and the words quoted.

    Protocol section 12 puts the participant's words in Notes, because the two
    recall columns now carry the option. They are rendered here rather than
    dropped, so a printed sheet still shows what was actually said, which is what
    the second scorer has to read. The fields stay separate on the row; only this
    rendering joins them.
    """
    parts: list[str] = []
    if row.notes.strip():
        parts.append(row.notes.strip())
    if row.action_recall.strip():
        parts.append(f'action: "{row.action_recall.strip()}"')
    if row.deadline_recall.strip():
        parts.append(f'deadline: "{row.deadline_recall.strip()}"')
    return "; ".join(parts)


def render_outcome_sheet(rows: Sequence[OutcomeRow]) -> list[str]:
    """The protocol section 12 raw outcome sheet, as markdown.

    Withdrawn rows are rendered but marked, because section 3 wants an abandoned
    session to leave a named gap rather than a silent resequencing.
    """
    header = "| " + " | ".join(SHEET_COLUMNS) + " |"
    divider = "| " + " | ".join("---" for _ in SHEET_COLUMNS) + " |"
    lines = [header, divider]
    for row in rows:
        barrier = "" if row.barrier_recognised is None else (
            "recognised" if row.barrier_recognised else "not recognised"
        )
        condition = row.condition + (" (withdrawn)" if row.withdrawn else "")
        lines.append(
            "| "
            + " | ".join(
                [
                    row.dyad,
                    str(row.position),
                    condition,
                    str(row.task_time_s),
                    row.action_option,
                    row.deadline_option,
                    row.both_correct,
                    row.false_completion_label,
                    barrier,
                    str(row.burden),
                    row.hint_level or "",
                    row.adverse_reaction,
                    _notes_cell(row),
                ]
            )
            + " |"
        )
    return lines


def render_result(rows: Sequence[OutcomeRow]) -> list[str]:
    """Write the result down as protocol section 15 requires.

    Raw counts, the cut decision, adverse reactions, the design limitation and
    the directional-only caveat, in that order. A percentage appears only at ten
    participants.
    """
    lines = [
        "Gate B result. Protocol protocol-v1, card instrument fixed-card-v1.",
        "",
        "Dyads analysed:",
    ]
    lines.extend(f"  {line}" for line in render_outcome_report(dyad_counts(rows)))
    lines.append("")

    if hcd_claim_supported(dyad_counts(rows)):
        lines.append(
            "Human-centred validation claim: supported at the protocol minimum "
            f"of {MIN_DYADS_PER_CONDITION} dyads per condition."
        )
    else:
        lines.append(
            "Human-centred validation claim: NOT made. Fewer than "
            f"{MIN_DYADS_PER_CONDITION} dyads in at least one condition "
            "(protocol section 15)."
        )
    lines.append("")

    lines.append(
        "Both-correct recall (action and deadline): correct, incorrect and "
        "unclassified per condition."
    )
    for condition, labels in both_correct_breakdown(rows).items():
        lines.append(
            f"  {condition}: {labels[CORRECT]} correct, "
            f"{labels[INCORRECT]} incorrect, "
            f"{labels[UNCLASSIFIED]} unclassified"
        )
    lines.append("")

    try:
        decision = apply_cut_rule(rows)
    except (
        BelowMinimumSample,
        NoGateBResult,
        UnequalConditions,
        UnresolvedResponses,
    ) as error:
        lines.append(f"Cut rule: NOT APPLIED. {error}")
    else:
        verdict = "PlanBack is CUT" if decision.outcome == CUT else "PlanBack is kept"
        lines.append(f"Cut rule: {verdict}. {decision.reason}.")
        lines.append(
            f"  median burden: A {decision.median_burden[APPLICATION_CONDITION]}, "
            f"B {decision.median_burden[CARD_CONDITION]}"
        )
    lines.append("")

    pending = pending_second_scorer(rows)
    if pending:
        lines.append("Awaiting the second scorer (protocol section 11):")
        for dyad, field, text in pending:
            lines.append(f"  {dyad}, {field}: {text!r}")
    else:
        lines.append("Awaiting the second scorer: none.")
    lines.append("")

    reactions = [row for row in analysed(rows) if row.adverse_reaction.strip()]
    lines.append("Adverse reactions (protocol section 15):")
    if reactions:
        for row in reactions:
            lines.append(f"  {row.dyad} (condition {row.condition}): {row.adverse_reaction}")
    else:
        lines.append("  none recorded")
    lines.append("")

    lines.extend(
        [
            "Limitations that travel with every result above:",
            "  The study measures the mechanism only. It does not validate "
            "clinical advice (protocol section 1).",
            "  Design limitation (protocol section 2): in condition A the "
            "truthful status arrives on a screen; in condition B the "
            "facilitator speaks it. The content is identical, the channel is "
            "not, and it cannot be.",
            f"  {TARGET_DYADS_PER_CONDITION} per condition is a directional "
            "decision, not efficacy evidence (protocol section 15).",
        ]
    )
    return lines
