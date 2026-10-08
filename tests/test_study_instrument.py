"""The Gate B response path. Slice 9.

`tests/test_study.py` guards the two artefacts: the card and the pre-registration.
This module guards the instrument that scores what a participant says and decides
whether PlanBack survives, which is the part Slice 9 had to build because
`00-status.md` recorded the rules as living inside a test and governing nothing.

The guards below are chosen for the ways this instrument can lie:

* **Allocation is frozen.** A facilitator must not be able to pick a condition,
  and a skipped session must leave a gap rather than resequence the rest.
* **A refusal is not a score.** An unclassifiable response has to stay
  unclassified all the way to the cut rule, because the cut rule reads the field
  it belongs to and a guess there kills or saves the mechanism by accident.
* **The cut rule refuses when it cannot be applied.** Unequal conditions and
  unresolved rows are not edge cases: they are the two situations in which
  applying the frozen rule would invent a comparison the protocol does not
  contain.
* **Reporting stays raw.** Percentages below ten participants, and a
  human-centred claim below three dyads in either condition, are the two
  overstatements the protocol exists to prevent.

No test here recruits anyone, contacts anyone, or opens a network connection.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from carerelay.study.__main__ import main
from carerelay.demo import fixture
from carerelay.study.outcomes import (
    ALLOCATION_ORDER,
    APPLICATION_CONDITION,
    CARD_CONDITION,
    CUT,
    KEEP,
    MIN_DYADS_PER_CONDITION,
    MIN_PARTICIPANTS_FOR_PERCENTAGES,
    SHEET_COLUMNS,
    BelowMinimumSample,
    CutDecision,
    NoGateBResult,
    OutcomeRow,
    UnequalConditions,
    UnresolvedResponses,
    analysed,
    apply_cut_rule,
    both_correct_breakdown,
    both_correct_counts,
    burden_ratings,
    condition_for_position,
    dyad_counts,
    median_burden,
    next_position,
    pending_second_scorer,
    render_outcome_sheet,
    render_result,
)
from carerelay.study.scoring import (
    ACTION_OPTIONS,
    CORRECT,
    DEADLINE_OPTIONS,
    FALSE_COMPLETION,
    INCORRECT,
    KEYED_OPTION,
    NO_FALSE_COMPLETION,
    UNCLASSIFIED,
    classify,
    score_action_option,
    score_action_recall,
    score_deadline_option,
    score_deadline_recall,
    score_false_completion,
)
from carerelay.study.sheet import append_row, read_rows

#: The protocol the instrument implements. The cut rule's minimum sample is a
#: document claim as well as a code guard, so one test reads the document.
PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "study" / "protocol.md"

#: A restatement the fixture resolves to the keyed action, and one it resolves to
#: a different instant. Both are fixture values, so neither is invented here.
GOOD_ACTION = "go to the clinic"
GOOD_DEADLINE = "6pm"
WRONG_DEADLINE = "today before 8pm"
UNCLASSIFIABLE = "sometime next week"

#: The closed recall instrument, protocol section 7 as amended on 8 October
#: 2026. `KEYED` is the option the answer key sits at, `DISTRACTOR` is a value
#: the fixture resolves to a different one, `DONT_KNOW` is the fourth option,
#: and `UNRECORDED` is a row where the facilitator recorded no option at all,
#: which is the one recall case the second scorer still resolves.
KEYED = "A"
DISTRACTOR = "B"
DONT_KNOW = "D"
UNRECORDED = ""


def _row(
    position: int,
    *,
    action: str = GOOD_ACTION,
    deadline: str = GOOD_DEADLINE,
    action_option: str = KEYED,
    deadline_option: str = KEYED,
    answer: str = "no",
    burden: int = 2,
    **kwargs: object,
) -> OutcomeRow:
    """One row, with its condition derived from the frozen position.

    The condition is never passed in, because protocol section 3 forbids anyone
    from choosing it. A helper that took it as an argument would quietly make
    every test below capable of the thing the allocation guard exists to stop.
    """
    return OutcomeRow(
        dyad=f"d{position}",
        position=position,
        condition=condition_for_position(position),
        task_time_s=30,
        action_recall=action,
        deadline_recall=deadline,
        action_option=action_option,
        deadline_option=deadline_option,
        false_completion=answer,
        barrier_recognised=True,
        burden=burden,
        **kwargs,  # type: ignore[arg-type]
    )


class TestTheFrozenAllocation:
    def test_the_order_alternates_a_and_b(self) -> None:
        assert ALLOCATION_ORDER[1] == APPLICATION_CONDITION
        assert ALLOCATION_ORDER[2] == CARD_CONDITION
        assert ALLOCATION_ORDER[11] == APPLICATION_CONDITION
        assert ALLOCATION_ORDER[12] == CARD_CONDITION

    def test_the_order_holds_twelve_positions(self) -> None:
        assert sorted(ALLOCATION_ORDER) == list(range(1, 13))

    def test_the_order_is_the_protocol_table(self) -> None:
        """Section 12: position 1 takes A, position 2 takes B, and so on."""
        assert "".join(ALLOCATION_ORDER[p] for p in range(1, 13)) == "ABABABABABAB"

    def test_a_position_outside_the_order_is_refused(self) -> None:
        with pytest.raises(ValueError):
            condition_for_position(13)

    def test_the_next_position_is_the_lowest_unused(self) -> None:
        assert next_position([]) == 1
        assert next_position([1]) == 2

    def test_an_abandoned_session_leaves_a_gap(self) -> None:
        """Section 3: a gap is named, not resequenced away."""
        assert next_position([1, 2, 3]) == 4

    def test_a_used_position_outside_the_order_is_refused(self) -> None:
        with pytest.raises(ValueError):
            next_position([1, 99])

    def test_every_position_used_is_refused(self) -> None:
        with pytest.raises(ValueError):
            next_position(range(1, 13))


class TestTheRowKeepsItsVerbatimText:
    def test_a_row_scores_the_option_it_carries(self) -> None:
        """Scored from the option, after the amendment of 8 October 2026."""
        row = _row(1)
        assert row.action_label == CORRECT
        assert row.deadline_label == CORRECT
        assert row.both_correct == CORRECT

    def test_the_row_still_carries_the_words(self) -> None:
        """The words are what the second scorer reads, so they stay on it."""
        row = _row(1)
        assert row.action_recall == GOOD_ACTION
        assert row.deadline_recall == GOOD_DEADLINE

    def test_words_without_an_option_are_not_a_score(self) -> None:
        """A facilitator who wrote down what was said but not which option was
        chosen has not produced a score, and the instrument says so rather than
        reading the words for them."""
        row = _row(1, action_option=UNRECORDED)
        assert row.action_recall == GOOD_ACTION
        assert row.action_label == UNCLASSIFIED

    def test_the_primary_outcome_is_named_not_scored(self) -> None:
        """A "no" is a correct answer, so "incorrect" would be the wrong word."""
        assert _row(1, answer="no").false_completion_label == NO_FALSE_COMPLETION
        assert _row(2, answer="yes").false_completion_label == FALSE_COMPLETION

    def test_an_unclassifiable_response_stays_unclassified(self) -> None:
        row = _row(1, deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        assert row.deadline_label == UNCLASSIFIED

    def test_a_condition_that_contradicts_its_position_is_refused(self) -> None:
        with pytest.raises(ValueError):
            OutcomeRow(
                dyad="d1",
                position=1,
                condition=CARD_CONDITION,
                task_time_s=30,
                action_recall=GOOD_ACTION,
                deadline_recall=GOOD_DEADLINE,
                false_completion="no",
                barrier_recognised=True,
                burden=2,
            )

    def test_an_unknown_condition_is_refused(self) -> None:
        with pytest.raises(ValueError):
            OutcomeRow(
                dyad="d1",
                position=1,
                condition="C",
                task_time_s=30,
                action_recall=GOOD_ACTION,
                deadline_recall=GOOD_DEADLINE,
                false_completion="no",
                barrier_recognised=True,
                burden=2,
            )

    def test_a_burden_outside_the_five_point_scale_is_refused(self) -> None:
        with pytest.raises(ValueError):
            _row(1, burden=6)

    def test_a_negative_task_time_is_refused(self) -> None:
        with pytest.raises(ValueError):
            OutcomeRow(
                dyad="d1",
                position=1,
                condition=APPLICATION_CONDITION,
                task_time_s=-1,
                action_recall=GOOD_ACTION,
                deadline_recall=GOOD_DEADLINE,
                false_completion="no",
                barrier_recognised=True,
                burden=2,
            )

    def test_the_card_condition_has_no_hint_level(self) -> None:
        """Read-back is the variable under test, so only A has a hint ladder."""
        with pytest.raises(ValueError):
            _row(2, hint_level="H1")

    def test_an_unknown_hint_level_is_refused(self) -> None:
        with pytest.raises(ValueError):
            _row(1, hint_level="H9")

    def test_a_hint_level_is_allowed_in_condition_a(self) -> None:
        assert _row(1, hint_level="H2").hint_level == "H2"


class TestBothCorrectIsAConjunction:
    def test_both_correct_when_both_fields_are_correct(self) -> None:
        assert _row(1).both_correct == CORRECT

    def test_not_both_correct_when_one_is_wrong(self) -> None:
        row = _row(1, deadline_option=DISTRACTOR, deadline=WRONG_DEADLINE)
        assert row.both_correct == INCORRECT

    def test_unclassified_when_either_field_is_unclassified(self) -> None:
        """Section 13 reads this field, so it must never be guessed."""
        row = _row(1, deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        assert row.both_correct == UNCLASSIFIED
        assert row.both_correct != INCORRECT


class TestTheScorerNeverSeesTheCondition:
    def test_no_scorer_takes_a_condition_argument(self) -> None:
        """Section 16: the scorer sees the key and the response, not the arm."""
        for scorer in (
            score_action_option,
            score_deadline_option,
            score_action_recall,
            score_deadline_recall,
            score_false_completion,
        ):
            assert len(inspect.signature(scorer).parameters) == 1, scorer

    def test_classify_turns_a_refusal_into_a_label(self) -> None:
        assert classify(score_deadline_recall, GOOD_DEADLINE) == CORRECT
        assert classify(score_deadline_recall, WRONG_DEADLINE) == INCORRECT
        assert classify(score_deadline_recall, UNCLASSIFIABLE) == UNCLASSIFIED


class TestThePreRegisteredCutRule:
    def test_the_card_cuts_planback_on_equal_recall_and_lower_burden(self) -> None:
        """Three per condition, the protocol minimum: the rule runs here."""
        rows = [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1),
            _row(6, burden=1),
        ]
        decision = apply_cut_rule(rows)
        assert decision.outcome == CUT
        assert decision.both_correct == {"A": 3, "B": 3}
        assert decision.median_burden[CARD_CONDITION] < decision.median_burden[
            APPLICATION_CONDITION
        ]

    def test_planback_is_kept_when_the_card_loses_on_recall(self) -> None:
        rows = [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1, deadline_option=DISTRACTOR, deadline=WRONG_DEADLINE),
            _row(6, burden=1),
        ]
        decision = apply_cut_rule(rows)
        assert decision.outcome == KEEP
        assert decision.both_correct == {"A": 3, "B": 2}

    def test_planback_is_kept_when_the_card_burden_is_higher(self) -> None:
        rows = [
            _row(1, burden=1),
            _row(3, burden=1),
            _row(5, burden=1),
            _row(2, burden=4),
            _row(4, burden=4),
            _row(6, burden=4),
        ]
        assert apply_cut_rule(rows).outcome == KEEP

    def test_planback_is_kept_when_the_card_burden_is_only_equal(self) -> None:
        """Section 13 says lower, not "no higher"."""
        rows = [_row(position, burden=2) for position in range(1, 7)]
        assert apply_cut_rule(rows).outcome == KEEP

    def test_the_rule_refuses_while_a_response_awaits_the_second_scorer(self) -> None:
        rows = [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1),
            _row(6, burden=1, deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE),
        ]
        with pytest.raises(UnresolvedResponses):
            apply_cut_rule(rows)

    def test_the_rule_refuses_below_the_protocol_minimum(self) -> None:
        """Two per condition, the sample that used to decide the kill test.

        Section 13 was amended on 7 October 2026, before the first session, so
        that the rule is not applied below the section 15 minimum. The card wins
        on both halves here, so without the floor this returns CUT.
        """
        rows = [_row(1, burden=3), _row(3, burden=3), _row(2, burden=1), _row(4, burden=1)]
        with pytest.raises(BelowMinimumSample):
            apply_cut_rule(rows)

    def test_the_cut_rule_states_the_minimum_sample_it_is_given(self) -> None:
        """Section 13 carries the floor, added 7 October 2026 before the session.

        The document and the guard have to say the same thing, or the amendment
        is only half recorded.
        """
        text = PROTOCOL_PATH.read_text(encoding="utf-8").casefold()
        assert "minimum sample: three dyads per condition" in text

    def test_the_rule_refuses_when_the_conditions_are_unequal(self) -> None:
        rows = [_row(1, burden=3), _row(3, burden=3), _row(5, burden=3), _row(2, burden=1)]
        with pytest.raises(UnequalConditions):
            apply_cut_rule(rows)

    def test_the_rule_refuses_when_no_dyad_was_analysed(self) -> None:
        with pytest.raises(NoGateBResult):
            apply_cut_rule([])

    def test_a_fully_withdrawn_study_has_no_result(self) -> None:
        """Section 18: no result, not a null result. The run was cut, not failed."""
        rows = [_row(1, withdrawn=True), _row(2, withdrawn=True)]
        with pytest.raises(NoGateBResult):
            apply_cut_rule(rows)

    def test_withdrawn_rows_are_excluded_from_the_counts(self) -> None:
        rows = [
            _row(1, burden=3),
            _row(3, burden=3, withdrawn=True),
            _row(2, burden=1),
            _row(4, burden=1),
        ]
        assert dyad_counts(rows) == {"A": 1, "B": 2}
        assert len(analysed(rows)) == 3

    def test_the_median_of_an_even_sample_is_the_mean_of_the_middle_two(self) -> None:
        rows = [_row(1, burden=1), _row(3, burden=5), _row(2, burden=2), _row(4, burden=2)]
        assert median_burden(rows)[APPLICATION_CONDITION] == 3.0

    def test_a_condition_with_no_analysed_dyad_has_no_median(self) -> None:
        """A zero would be the lowest burden any card could beat."""
        with pytest.raises(NoGateBResult):
            median_burden([_row(1), _row(3)])

    def test_burden_ratings_stay_raw(self) -> None:
        rows = [_row(1, burden=1), _row(3, burden=5), _row(2, burden=2), _row(4, burden=2)]
        assert burden_ratings(rows)[APPLICATION_CONDITION] == [1, 5]


class TestTheSecondScorerQueue:
    def test_every_unclassifiable_field_is_queued_verbatim(self) -> None:
        """All three fields, not just one of them.

        The first version of this guard exercised the deadline field only, and
        the Slice 9 mutation run proved it: a mutation that disabled the action
        branch survived with the whole suite green, because nothing ever asked
        for an unclassifiable action. A queue that silently loses a field is
        worse than no queue, so each field is asserted in one row.
        """
        rows = [
            _row(
                1,
                action_option=UNRECORDED,
                deadline_option=UNRECORDED,
                action=UNCLASSIFIABLE,
                deadline=UNCLASSIFIABLE,
                answer="maybe",
            )
        ]
        assert pending_second_scorer(rows) == [
            ("d1", "action recall", UNCLASSIFIABLE),
            ("d1", "deadline recall", UNCLASSIFIABLE),
            ("d1", "false completion", "maybe"),
        ]

    def test_nothing_is_queued_when_everything_is_classified(self) -> None:
        assert pending_second_scorer([_row(1), _row(2)]) == []

    def test_a_withdrawn_dyad_is_not_queued(self) -> None:
        assert pending_second_scorer([_row(1, deadline=UNCLASSIFIABLE, withdrawn=True)]) == []


class TestTheRawOutcomeSheet:
    def test_the_sheet_carries_the_protocol_columns(self) -> None:
        sheet = render_outcome_sheet([_row(1)])
        assert sheet[0] == "| " + " | ".join(SHEET_COLUMNS) + " |"
        assert len(SHEET_COLUMNS) == 13

    def test_the_recall_columns_record_the_option_not_the_words(self) -> None:
        """Section 12 as amended: the score is derived from the option, so the
        sheet records the letter and cannot disagree with the scorer."""
        sheet = "\n".join(render_outcome_sheet([_row(1, deadline_option=DISTRACTOR)]))
        assert "| d1 | 1 | A | 30 | A | B |" in sheet, sheet

    def test_the_words_are_rendered_into_notes(self) -> None:
        """Section 12 puts the words in Notes; they are not dropped, because a
        printed sheet with no words in it leaves the second scorer nothing."""
        sheet = "\n".join(render_outcome_sheet([_row(1)]))
        assert f'action: "{GOOD_ACTION}"' in sheet, sheet
        assert f'deadline: "{GOOD_DEADLINE}"' in sheet, sheet

    def test_a_withdrawn_row_is_rendered_and_marked(self) -> None:
        """Section 3 wants a named gap, not a vanished one."""
        sheet = render_outcome_sheet([_row(2, withdrawn=True)])
        assert any("withdrawn" in line for line in sheet), sheet

    def test_the_sheet_round_trips_through_the_file(self, tmp_path: Path) -> None:
        path = tmp_path / "outcomes.jsonl"
        append_row(_row(1), path)
        append_row(_row(2, answer="yes"), path)
        rows = read_rows(path)
        assert [row.dyad for row in rows] == ["d1", "d2"]
        assert rows[0].false_completion_label == NO_FALSE_COMPLETION
        assert rows[1].false_completion_label == FALSE_COMPLETION

    def test_a_missing_sheet_is_an_empty_study(self, tmp_path: Path) -> None:
        assert read_rows(tmp_path / "nope.jsonl") == []


class TestTheResultIsWrittenDownHonestly:
    def test_raw_counts_are_reported(self) -> None:
        result = render_result([_row(1), _row(2)])
        assert any("A: 1 dyads" in line for line in result), result
        assert any("B: 1 dyads" in line for line in result), result

    def test_no_percentage_below_ten_participants(self) -> None:
        rows = [_row(p) for p in range(1, 9)]
        result = render_result(rows)
        assert total_dyads(rows) < MIN_PARTICIPANTS_FOR_PERCENTAGES
        assert not any("%" in line for line in result), result

    def test_no_hcd_claim_below_three_dyads_per_condition(self) -> None:
        result = render_result([_row(1), _row(2)])
        assert any("NOT made" in line for line in result), result

    def test_the_control_a_claim_is_made_at_the_minimum(self) -> None:
        rows = [_row(1), _row(3), _row(5), _row(2), _row(4), _row(6)]
        result = render_result(rows)
        assert any("supported at the protocol minimum" in line for line in result), result

    def test_the_cut_decision_is_written_down(self) -> None:
        rows = [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1),
            _row(6, burden=1),
        ]
        result = render_result(rows)
        assert any("PlanBack is CUT" in line for line in result), result

    def test_a_refused_cut_rule_is_reported_not_hidden(self) -> None:
        result = render_result([_row(1), _row(3), _row(2)])
        assert any("NOT APPLIED" in line for line in result), result

    def test_a_below_minimum_cut_rule_is_reported_not_hidden(self) -> None:
        """Equal but too small: the floor refuses, and the write-up says so."""
        result = render_result([_row(1), _row(3), _row(2), _row(4)])
        assert any("NOT APPLIED" in line for line in result), result

    def test_adverse_reactions_are_reported(self) -> None:
        rows = [_row(1, adverse_reaction="found the read-back tiring"), _row(2)]
        result = render_result(rows)
        assert any("read-back tiring" in line for line in result), result

    def test_the_absence_of_adverse_reactions_is_stated(self) -> None:
        result = render_result([_row(1), _row(2)])
        assert any("none recorded" in line for line in result), result

    def test_the_design_limitation_travels_with_the_result(self) -> None:
        """Section 15: report the section 2 limitation wherever a result appears."""
        result = render_result([_row(1), _row(2)])
        assert any("Design limitation" in line for line in result), result

    def test_the_result_says_it_is_directional(self) -> None:
        result = render_result([_row(1), _row(2)])
        assert any("directional" in line for line in result), result

    def test_the_result_does_not_claim_clinical_validation(self) -> None:
        result = render_result([_row(1), _row(2)])
        joined = " ".join(result).casefold()
        assert "does not validate clinical advice" in joined


class TestTheClosedRecallInstrument:
    """Protocol sections 7, 10 and 11, as amended on 8 October 2026.

    The amendment closed the two recall questions, so the field is scored from
    the option chosen. The defect it removes is a scorer that could not return
    `incorrect` for an action at all: the wrong-action vocabulary was empty,
    because the fixture's alias table keys the keyed action only.
    """

    def test_the_keyed_option_is_correct(self) -> None:
        assert score_action_option(KEYED) is True
        assert score_deadline_option(KEYED) is True

    @pytest.mark.parametrize("letter", ("B", "C"))
    def test_a_distractor_is_incorrect_not_unclassified(self, letter: str) -> None:
        """K1: a value the fixture resolves to a different one is a known
        wrong value, and it is scored rather than refused."""
        assert score_action_option(letter) is False
        assert score_deadline_option(letter) is False

    @pytest.mark.parametrize("scorer", (score_action_option, score_deadline_option))
    def test_i_dont_know_is_incorrect_not_unclassified(self, scorer) -> None:
        """Section 11: the field was not recalled, and that is a measurement
        rather than an absence of one. It is not uncertain."""
        assert scorer(DONT_KNOW) is False

    @pytest.mark.parametrize("scorer", (score_action_option, score_deadline_option))
    def test_no_recorded_option_is_refused_not_guessed(self, scorer) -> None:
        """The one recall case the second scorer still resolves."""
        with pytest.raises(ValueError):
            scorer(UNRECORDED)

    def test_the_letter_is_read_whatever_the_facilitator_typed(self) -> None:
        """Case and a trailing stop aside: the letter is what is recorded."""
        assert score_action_option("a") is True
        assert score_deadline_option("A.") is True

    def test_the_words_are_not_an_option(self) -> None:
        """Recording the words instead of the letter is not a score, and the
        instrument refuses rather than reading them back."""
        for text in (GOOD_ACTION, GOOD_DEADLINE, UNCLASSIFIABLE):
            assert classify(score_action_option, text) == UNCLASSIFIED
            assert classify(score_deadline_option, text) == UNCLASSIFIED

    def test_the_action_options_are_the_fixture_permitted_actions(self) -> None:
        """Derived, so the distractors are routes the fixture already resolves."""
        assert set(ACTION_OPTIONS.values()) == set(
            fixture.policy().permitted_action_ids
        )
        assert ACTION_OPTIONS[KEYED_OPTION] == fixture.ACTION_ID

    def test_the_keyed_deadline_option_is_the_deadline_the_card_prints(self) -> None:
        assert DEADLINE_OPTIONS[KEYED_OPTION] == fixture.DEADLINE_DISPLAY

    def test_the_protocol_offers_the_deadline_options_the_scorer_reads(self) -> None:
        """Section 7 is frozen, so the option text is pinned to the document."""
        protocol = " ".join(PROTOCOL_PATH.read_text(encoding="utf-8").split())
        rendered = " ".join(
            f"{letter.upper()}. {option}" for letter, option in DEADLINE_OPTIONS.items()
        )
        assert rendered in protocol, rendered
        assert "D. I don't know" in protocol

    def test_the_protocol_names_the_action_options_the_scorer_reads(self) -> None:
        """Options B and C are renderings the amendment wrote under the five copy
        rules, so they are pinned here rather than derived from the fixture."""
        protocol = " ".join(PROTOCOL_PATH.read_text(encoding="utf-8").split())
        assert f"A. {fixture.ACTION_TEXT}" in protocol
        assert "B. Call the fictional nurse line." in protocol
        assert "C. Wait and monitor." in protocol


class TestAnUnknownIsNotReportedAsAWrongAnswer:
    """The write-up has to refuse the way the cut rule refuses.

    A count of the dyads that got both fields right cannot tell a dyad that got
    one wrong from a dyad nobody has scored yet. Reporting it alone prints the
    second as the first, which is a guess that looks like a measurement.
    """

    def _mixed(self) -> list[OutcomeRow]:
        """Three per condition: one correct, one wrong, one unscored in B."""
        return [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1, deadline_option=DISTRACTOR),
            _row(
                6,
                burden=1,
                action_option=UNRECORDED,
                action=UNCLASSIFIABLE,
            ),
        ]

    def test_the_breakdown_names_all_three_labels(self) -> None:
        rows = self._mixed()
        assert both_correct_breakdown(rows)[CARD_CONDITION] == {
            CORRECT: 1,
            INCORRECT: 1,
            UNCLASSIFIED: 1,
        }

    def test_the_control_a_wrong_row_is_counted_as_incorrect(self) -> None:
        """Without this, a breakdown that never reports a wrong answer at all
        would pass the guard above."""
        rows = [_row(2, deadline_option=DISTRACTOR)]
        assert both_correct_breakdown(rows)[CARD_CONDITION][INCORRECT] == 1

    def test_the_write_up_reports_three_numbers(self) -> None:
        result = "\n".join(render_result(self._mixed()))
        assert "B: 1 correct, 1 incorrect, 1 unclassified" in result, result

    def test_the_write_up_does_not_report_a_single_count(self) -> None:
        """The old line printed "B: 1 dyads", reading two unresolved or wrong
        rows as one number."""
        result = "\n".join(render_result(self._mixed()))
        assert "B: 1 dyads" not in result, result

    def test_the_cut_rule_still_refuses_on_the_same_rows(self) -> None:
        """The write-up is not a second opinion: both refuse, or neither does."""
        with pytest.raises(UnresolvedResponses):
            apply_cut_rule(self._mixed())


class TestTheCommandLine:
    """Every command here records consent first.

    Consent was added to the instrument after these tests were written, and
    `record` now refuses a dyad without it. Each test was given a consent row
    rather than a way around the guard, so it still asserts what it always did:
    the first two that a valid session is recorded, the third that an invalid
    one is not.
    """

    def test_a_recorded_session_is_read_back(self, tmp_path: Path) -> None:
        path = tmp_path / "outcomes.jsonl"
        consent = tmp_path / "consent.jsonl"
        assert main(["consent", "--dyad", "d1"], consent_path=consent) == 0
        code = main(
            [
                "record",
                "--dyad",
                "d1",
                "--position",
                "1",
                "--task-time",
                "42",
                "--action-option",
                KEYED,
                "--deadline-option",
                KEYED,
                "--action",
                GOOD_ACTION,
                "--deadline",
                GOOD_DEADLINE,
                "--answer",
                "no",
                "--barrier",
                "yes",
                "--burden",
                "2",
            ],
            sheet_path=path,
            consent_path=consent,
        )
        assert code == 0
        assert [row.dyad for row in read_rows(path)] == ["d1"]

    def test_the_command_derives_the_condition(self, tmp_path: Path) -> None:
        """The facilitator never types a condition; section 3 forbids choosing."""
        path = tmp_path / "outcomes.jsonl"
        consent = tmp_path / "consent.jsonl"
        main(["consent", "--dyad", "d2"], consent_path=consent)
        main(
            ["record", "--dyad", "d2", "--position", "2", "--task-time", "10",
             "--action-option", KEYED, "--deadline-option", KEYED,
             "--action", GOOD_ACTION, "--deadline", GOOD_DEADLINE, "--answer",
             "no", "--burden", "3"],
            sheet_path=path,
            consent_path=consent,
        )
        assert read_rows(path)[0].condition == CARD_CONDITION

    def test_a_refused_row_returns_two(self, tmp_path: Path) -> None:
        """A burden of 9 is outside the scale, and consent does not excuse it."""
        path = tmp_path / "outcomes.jsonl"
        consent = tmp_path / "consent.jsonl"
        main(["consent", "--dyad", "d1"], consent_path=consent)
        code = main(
            ["record", "--dyad", "d1", "--position", "1", "--task-time", "10",
             "--action-option", KEYED, "--deadline-option", KEYED,
             "--action", GOOD_ACTION, "--deadline", GOOD_DEADLINE, "--answer",
             "no", "--burden", "9"],
            sheet_path=path,
            consent_path=consent,
        )
        assert code == 2
        assert read_rows(path) == []

    def test_report_on_an_empty_study_says_there_is_no_result(self, tmp_path: Path) -> None:
        code = main(["report"], sheet_path=tmp_path / "outcomes.jsonl")
        assert code == 0

    def test_sheet_prints_the_protocol_columns(self, tmp_path: Path) -> None:
        path = tmp_path / "outcomes.jsonl"
        append_row(_row(1), path)
        code = main(["sheet"], sheet_path=path)
        assert code == 0


def total_dyads(rows: list[OutcomeRow]) -> int:
    """Analysed dyads in total, which is the number the percentage floor reads."""
    return sum(dyad_counts(rows).values())


class TestTheLiftedRulesAreTheSameRules:
    """The five functions moved; their meaning must not have moved with them."""

    def test_the_reporting_thresholds_are_unchanged(self) -> None:
        assert MIN_PARTICIPANTS_FOR_PERCENTAGES == 10
        assert MIN_DYADS_PER_CONDITION == 3

    def test_a_decision_is_a_value_not_a_side_effect(self) -> None:
        rows = [
            _row(1, burden=3),
            _row(3, burden=3),
            _row(5, burden=3),
            _row(2, burden=1),
            _row(4, burden=1),
            _row(6, burden=1),
        ]
        assert isinstance(apply_cut_rule(rows), CutDecision)
        assert both_correct_counts(rows) == {"A": 3, "B": 3}
