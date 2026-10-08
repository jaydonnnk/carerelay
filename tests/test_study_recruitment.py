"""Recruitment preparation for Gate B: consent, the second scorer, the script.

Slice 9 built the instrument that scores a response. Before a session can be
run, three things had to exist that did not:

* **consent**, recorded before the task and kept out of the clinical record
  (protocol section 4);
* **a path for the second scorer**, because section 11 sends an unclassifiable
  response to someone who did not run the session and the queue was a dead end;
  one "maybe" would have left the cut rule refusing at any sample size;
* **the facilitator's script**, frozen in section 7 and previously reachable
  only by opening the protocol during a session.

The guards below are chosen for the ways this can lie:

* **A session without consent is refused, and the refusal is the point.** A
  study record that held a session with no consent behind it would be evidence
  that the protocol was broken.
* **A verdict resolves a field without erasing what was said.** The verbatim
  response stays on the sheet; the verdict is carried beside it.
* **The facilitator cannot score their own session.** Section 16 is a rule
  about a person, so the check needs two names and refuses when either is
  missing.

No test here recruits anyone, contacts anyone, or opens a network connection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from carerelay.study.__main__ import (
    POST_FAILURE_QUESTION,
    RECALL_OPTIONS,
    REDIRECT_ANSWER,
    SECONDARY_QUESTIONS,
    STATUS_STATEMENT,
    main,
    render_script,
)
from carerelay.study.consent import (
    CONSENT_VERSION,
    ConsentRecord,
    NoConsentRecorded,
    StaleConsentVersion,
    append_consent,
    consented_dyads,
    read_consents,
    require_consent,
)
from carerelay.study.outcomes import (
    ACTION_FIELD,
    APPLICATION_CONDITION,
    CARD_CONDITION,
    CUT,
    DEADLINE_FIELD,
    FALSE_COMPLETION_FIELD,
    OutcomeRow,
    UnresolvedResponses,
    apply_cut_rule,
    condition_for_position,
    pending_second_scorer,
    render_outcome_sheet,
    resolve_all,
)
from carerelay.study.scoring import (
    CORRECT,
    DEADLINE_OPTIONS,
    FALSE_COMPLETION,
    INCORRECT,
    NO_FALSE_COMPLETION,
    UNCLASSIFIED,
)
from carerelay.study.sheet import append_row
from carerelay.study.second_scorer import (
    NotBlinded,
    SecondScorerDecision,
    UnresolvedVerdict,
    append_decision,
    assert_blinded,
    read_decisions,
    resolutions_from,
    resolved_rows,
)

PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "study" / "protocol.md"
GITIGNORE_PATH = Path(__file__).resolve().parents[1] / ".gitignore"

GOOD_ACTION = "go to the clinic"
GOOD_DEADLINE = "6pm"
UNCLASSIFIABLE = "sometime next week"

#: The closed recall instrument, protocol section 7 as amended on 8 October
#: 2026. `KEYED` is the option the answer key sits at, and `UNRECORDED` is a
#: row where the facilitator recorded no option at all, which is the one recall
#: case the second scorer still resolves.
KEYED = "A"
UNRECORDED = ""

#: The two people section 16 keeps apart.
FACILITATOR = "J. Facilitator"
SCORER = "A. Second"


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
    """One row, condition derived from the frozen position, never chosen."""
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


def _six(burden_a: int = 3, burden_b: int = 1, **kwargs: object) -> list[OutcomeRow]:
    """Three per condition, the protocol minimum, at a burdens the card wins."""
    return [
        _row(1, burden=burden_a),
        _row(3, burden=burden_a),
        _row(5, burden=burden_a),
        _row(2, burden=burden_b),
        _row(4, burden=burden_b),
        _row(6, burden=burden_b, **kwargs),  # type: ignore[arg-type]
    ]


class TestConsentComesBeforeTheTask:
    def test_a_session_without_consent_is_refused(self) -> None:
        with pytest.raises(NoConsentRecorded):
            require_consent("d1", [])

    def test_the_refusal_names_the_dyad(self) -> None:
        """A facilitator has to know which dyad they cannot record."""
        with pytest.raises(NoConsentRecorded, match="d1"):
            require_consent("d1", [])

    def test_a_recorded_consent_authorises_the_session(self) -> None:
        records = [ConsentRecord(dyad="d1", version=CONSENT_VERSION, agreed=True)]
        require_consent("d1", records)

    def test_a_declined_consent_authorises_nothing(self) -> None:
        """Section 4 gives the right to decline; a decline is not a consent."""
        records = [ConsentRecord(dyad="d1", version=CONSENT_VERSION, agreed=False)]
        assert consented_dyads(records) == set()
        with pytest.raises(NoConsentRecorded):
            require_consent("d1", records)

    def test_a_stale_version_authorises_nothing(self) -> None:
        """An agreement to an older wording is not an agreement to this one."""
        with pytest.raises(StaleConsentVersion):
            ConsentRecord(dyad="d1", version="consent-v0", agreed=True)

    def test_consent_for_another_dyad_is_not_consent_for_this_one(self) -> None:
        records = [ConsentRecord(dyad="d2", version=CONSENT_VERSION, agreed=True)]
        with pytest.raises(NoConsentRecorded):
            require_consent("d1", records)


class TestTheConsentRecordIsMinimal:
    def test_the_record_holds_no_participant_detail(self) -> None:
        """Section 4 collects the outcomes, and then says "nothing else".

        A field for a name, a signature or a contact detail would put exactly
        what the section excludes into the study record, so the fields are
        enumerated rather than merely listed in a docstring.
        """
        fields = set(ConsentRecord.__dataclass_fields__)
        assert fields == {"dyad", "version", "agreed", "at"}
        for name in fields:
            assert name not in {"name", "signature", "contact", "email", "phone"}

    def test_a_declined_consent_is_still_written(self, tmp_path: Path) -> None:
        """A refusal is evidence: a log of only agreements could show neither."""
        path = tmp_path / "consent.jsonl"
        append_consent(
            ConsentRecord(dyad="d1", version=CONSENT_VERSION, agreed=False),
            path,
        )
        records = read_consents(path)
        assert len(records) == 1
        assert records[0].agreed is False

    def test_a_missing_log_is_an_empty_study(self, tmp_path: Path) -> None:
        assert read_consents(tmp_path / "nope.jsonl") == []

    def test_the_log_round_trips(self, tmp_path: Path) -> None:
        path = tmp_path / "consent.jsonl"
        append_consent(
            ConsentRecord(dyad="d1", version=CONSENT_VERSION, agreed=True, at="2026-10-08"),
            path,
        )
        assert read_consents(path)[0].at == "2026-10-08"


class TestTheSecondScorerResolvesTheQueue:
    def test_the_queue_is_a_dead_end_without_a_verdict(self) -> None:
        """The gap this module closes: nothing could ever resolve it."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        assert pending_second_scorer(rows) == [("d6", DEADLINE_FIELD, UNCLASSIFIABLE)]
        with pytest.raises(UnresolvedResponses):
            apply_cut_rule(rows)

    def test_a_verdict_resolves_the_field(self) -> None:
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
        )
        resolved = resolve_all(rows, resolutions_from([decision]))
        assert pending_second_scorer(resolved) == []
        assert resolved[5].deadline_label == CORRECT
        assert resolved[5].both_correct == CORRECT

    def test_the_cut_rule_runs_once_the_queue_is_resolved(self) -> None:
        """One "maybe" blocked the kill test at any sample size before this."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
        )
        resolved = resolve_all(rows, resolutions_from([decision]))
        result = apply_cut_rule(resolved)
        assert result.outcome == CUT
        assert result.both_correct == {APPLICATION_CONDITION: 3, CARD_CONDITION: 3}

    def test_a_verdict_can_go_the_other_way(self) -> None:
        """The second scorer is not a rubber stamp for the card."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=INCORRECT, scorer=SCORER
        )
        resolved = resolve_all(rows, resolutions_from([decision]))
        assert apply_cut_rule(resolved).both_correct == {
            APPLICATION_CONDITION: 3,
            CARD_CONDITION: 2,
        }

    def test_the_verbatim_text_survives_the_verdict(self) -> None:
        """The sheet keeps what was said; the verdict is carried beside it."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
        )
        resolved = resolve_all(rows, resolutions_from([decision]))
        assert resolved[5].deadline_recall == UNCLASSIFIABLE
        assert pending_second_scorer(rows) == [("d6", DEADLINE_FIELD, UNCLASSIFIABLE)]

    def test_an_unresolved_field_stays_unresolved(self) -> None:
        """A verdict on one field does not answer another."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=ACTION_FIELD, verdict=CORRECT, scorer=SCORER
        )
        resolved = resolve_all(rows, resolutions_from([decision]))
        assert resolved[5].deadline_label == UNCLASSIFIED
        assert resolved[5].both_correct == UNCLASSIFIED

    def test_the_intake_is_what_the_analysis_reads(self) -> None:
        """`resolved_rows` is the composition the command line hands over."""
        rows = _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE)
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
        )
        assert pending_second_scorer(resolved_rows(rows, [decision])) == []

    def test_a_later_verdict_replaces_an_earlier_one(self) -> None:
        """A changed mind is a new row, and the earlier one stays visible."""
        decisions = [
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
            ),
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=INCORRECT, scorer=SCORER
            ),
        ]
        assert resolutions_from(decisions) == {("d6", DEADLINE_FIELD): INCORRECT}

    def test_the_field_names_are_the_queue_field_names(self) -> None:
        """A verdict filed against a field the queue does not carry is nothing."""
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
        queued = {field for _dyad, field, _text in pending_second_scorer(rows)}
        assert queued == {ACTION_FIELD, DEADLINE_FIELD, FALSE_COMPLETION_FIELD}


class TestAVerdictHasToResolveSomething:
    def test_an_unclassified_verdict_is_refused(self) -> None:
        """Unclassified is the question, not the answer."""
        with pytest.raises(UnresolvedVerdict):
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=UNCLASSIFIED, scorer=SCORER
            )

    def test_a_verdict_the_field_cannot_carry_is_refused(self) -> None:
        """The primary outcome is not a recall score, so it has its own labels."""
        with pytest.raises(UnresolvedVerdict):
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=FALSE_COMPLETION, scorer=SCORER
            )

    def test_a_recall_field_takes_a_recall_verdict(self) -> None:
        decision = SecondScorerDecision(
            dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
        )
        assert decision.verdict == CORRECT

    def test_the_primary_outcome_takes_its_own_verdict(self) -> None:
        decision = SecondScorerDecision(
            dyad="d1",
            field=FALSE_COMPLETION_FIELD,
            verdict=NO_FALSE_COMPLETION,
            scorer=SCORER,
        )
        assert decision.verdict == NO_FALSE_COMPLETION

    def test_a_field_the_queue_does_not_have_is_refused(self) -> None:
        with pytest.raises(ValueError):
            SecondScorerDecision(
                dyad="d1", field="task time", verdict=CORRECT, scorer=SCORER
            )


class TestTheFacilitatorDoesNotScore:
    def test_the_facilitator_cannot_score_their_own_session(self) -> None:
        with pytest.raises(NotBlinded):
            assert_blinded(FACILITATOR, FACILITATOR)

    def test_the_check_survives_a_capitalisation_difference(self) -> None:
        with pytest.raises(NotBlinded):
            assert_blinded("j. facilitator", FACILITATOR)

    def test_an_unnamed_facilitator_is_refused(self) -> None:
        """A check that accepted an empty name would pass on the day it mattered."""
        with pytest.raises(NotBlinded):
            assert_blinded(SCORER, "")

    def test_an_anonymous_verdict_is_refused(self) -> None:
        """Section 16 is a rule about a person, so the person has a name."""
        with pytest.raises(ValueError):
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer="  "
            )

    def test_a_blinded_verdict_is_accepted(self, tmp_path: Path) -> None:
        path = tmp_path / "second-scorer.jsonl"
        assert_blinded(SCORER, FACILITATOR)
        append_decision(
            SecondScorerDecision(
                dyad="d6", field=DEADLINE_FIELD, verdict=CORRECT, scorer=SCORER
            ),
            path,
        )
        assert len(read_decisions(path)) == 1

    def test_a_missing_log_is_an_empty_study(self, tmp_path: Path) -> None:
        assert read_decisions(tmp_path / "nope.jsonl") == []


class TestTheFrozenScript:
    def test_the_script_is_the_frozen_protocol_script(self) -> None:
        """Every line is pinned to section 7, so it cannot drift from it.

        The document is hard-wrapped, so a frozen sentence can be broken across
        a line break. Both sides are compared unwrapped.
        """
        protocol = " ".join(PROTOCOL_PATH.read_text(encoding="utf-8").split())
        assert STATUS_STATEMENT in protocol
        assert POST_FAILURE_QUESTION in protocol
        assert REDIRECT_ANSWER in protocol
        for _name, question in SECONDARY_QUESTIONS:
            assert question in protocol, question
        for options in RECALL_OPTIONS.values():
            for option in options:
                assert option in protocol, option

    def test_the_card_condition_carries_the_spoken_statement(self) -> None:
        script = "\n".join(render_script(2))
        assert STATUS_STATEMENT in script
        assert POST_FAILURE_QUESTION in script

    def test_the_application_condition_does_not(self) -> None:
        """Section 5: the screen carries it, and speaking it would add a channel."""
        script = "\n".join(render_script(1))
        assert STATUS_STATEMENT not in script
        assert "Do not speak it" in script

    def test_the_condition_comes_from_the_position(self) -> None:
        """Nobody chooses an arm, so the script cannot be read for the wrong one."""
        assert f"Condition {APPLICATION_CONDITION}." in "\n".join(render_script(1))
        assert f"Condition {CARD_CONDITION}." in "\n".join(render_script(6))

    def test_the_script_carries_all_four_secondary_questions(self) -> None:
        script = "\n".join(render_script(1))
        for _name, question in SECONDARY_QUESTIONS:
            assert question in script, question

    def test_the_script_carries_the_closed_recall_options(self) -> None:
        """The facilitator reads the options aloud, so the script must have them.

        Without this the closed instrument cannot be run from the command line,
        and the amendment of 8 October 2026 does not reach the session.
        """
        script = "\n".join(render_script(1))
        for options in RECALL_OPTIONS.values():
            for index, option in enumerate(options):
                assert f"{chr(ord('A') + index)}. {option}" in script, option

    def test_the_deadline_options_are_the_ones_the_scorer_scores(self) -> None:
        """Read from the scorer, so the script cannot offer an unscoreable one."""
        scored = {option for option in DEADLINE_OPTIONS.values()}
        offered = set(RECALL_OPTIONS["Deadline recall"])
        assert scored <= offered, scored - offered


class TestTheRecruitmentCommandLine:
    def test_a_session_is_refused_without_consent(self, tmp_path: Path) -> None:
        path = tmp_path / "outcomes.jsonl"
        code = main(
            ["record", "--dyad", "d1", "--position", "1", "--task-time", "10",
             "--action-option", KEYED, "--deadline-option", KEYED,
             "--action", GOOD_ACTION, "--deadline", GOOD_DEADLINE, "--answer",
             "no", "--burden", "2"],
            sheet_path=path,
            consent_path=tmp_path / "consent.jsonl",
        )
        assert code == 2
        assert read_consents(tmp_path / "consent.jsonl") == []
        assert path.exists() is False

    def test_consent_then_record(self, tmp_path: Path) -> None:
        path = tmp_path / "outcomes.jsonl"
        consent = tmp_path / "consent.jsonl"
        assert main(["consent", "--dyad", "d1"], consent_path=consent) == 0
        code = main(
            ["record", "--dyad", "d1", "--position", "1", "--task-time", "10",
             "--action-option", KEYED, "--deadline-option", KEYED,
             "--action", GOOD_ACTION, "--deadline", GOOD_DEADLINE, "--answer",
             "no", "--burden", "2"],
            sheet_path=path,
            consent_path=consent,
        )
        assert code == 0

    def test_a_declined_consent_still_refuses_the_session(self, tmp_path: Path) -> None:
        consent = tmp_path / "consent.jsonl"
        assert main(["consent", "--dyad", "d1", "--declined"], consent_path=consent) == 0
        code = main(
            ["record", "--dyad", "d1", "--position", "1", "--task-time", "10",
             "--action-option", KEYED, "--deadline-option", KEYED,
             "--action", GOOD_ACTION, "--deadline", GOOD_DEADLINE, "--answer",
             "no", "--burden", "2"],
            sheet_path=tmp_path / "outcomes.jsonl",
            consent_path=consent,
        )
        assert code == 2

    def test_a_verdict_from_the_facilitator_is_refused(self, tmp_path: Path) -> None:
        path = tmp_path / "second-scorer.jsonl"
        code = main(
            ["resolve", "--dyad", "d6", "--field", DEADLINE_FIELD,
             "--verdict", CORRECT, "--scorer", FACILITATOR,
             "--facilitator", FACILITATOR],
            decisions_path=path,
        )
        assert code == 2
        assert read_decisions(path) == []

    def test_a_blinded_verdict_is_recorded(self, tmp_path: Path) -> None:
        path = tmp_path / "second-scorer.jsonl"
        code = main(
            ["resolve", "--dyad", "d6", "--field", DEADLINE_FIELD,
             "--verdict", CORRECT, "--scorer", SCORER,
             "--facilitator", FACILITATOR],
            decisions_path=path,
        )
        assert code == 0
        assert read_decisions(path)[0].scorer == SCORER

    def test_report_applies_the_verdict(self, tmp_path: Path, capsys) -> None:
        """The cut rule refuses while the queue holds anything; resolved, it runs."""
        sheet = tmp_path / "outcomes.jsonl"
        decisions = tmp_path / "second-scorer.jsonl"
        for row in _six(deadline_option=UNRECORDED, deadline=UNCLASSIFIABLE):
            append_row(row, sheet)
        assert main(["report"], sheet_path=sheet, decisions_path=decisions) == 0
        assert "NOT APPLIED" in capsys.readouterr().out

        main(
            ["resolve", "--dyad", "d6", "--field", DEADLINE_FIELD,
             "--verdict", CORRECT, "--scorer", SCORER,
             "--facilitator", FACILITATOR],
            decisions_path=decisions,
        )
        assert main(["report"], sheet_path=sheet, decisions_path=decisions) == 0
        assert "PlanBack is CUT" in capsys.readouterr().out

    def test_script_takes_the_next_unused_position(self, tmp_path: Path, capsys) -> None:
        sheet = tmp_path / "outcomes.jsonl"
        append_row(_row(1), sheet)
        assert main(["script"], sheet_path=sheet) == 0
        assert "Position 2" in capsys.readouterr().out


class TestStudyDataNeverReachesTheRepository:
    def test_every_study_data_file_is_git_ignored(self) -> None:
        """Participant data is destroyed 30 days after submission, not committed."""
        ignored = GITIGNORE_PATH.read_text(encoding="utf-8")
        for name in ("study/outcomes.jsonl", "study/consent.jsonl",
                     "study/second-scorer.jsonl"):
            assert name in ignored, name
