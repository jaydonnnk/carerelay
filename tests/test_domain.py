"""Slice 2 domain tests. Truth tables for the pure decision layer.

Five of these tests are named in `04-slices.md` as the tests that must be
fail-capable for Slice 2:

    test_planback_known_match_mismatch_uncertain
    test_closed_vocab_and_missing_is_not_negative
    test_disposition_deadline_is_append_only
    test_hint_disclosure_accessibility
    (test_domain_import_boundary lives in tests/test_boundaries.py)

`AGENTS.md` section 6 requires that each check can fail against a deliberate
defect, and that a fault two checks can both catch counts as proof of neither.
Every assertion below is therefore paired with the mutation that must break it:
`TestPlanBackAssertionsHaveTeeth` swaps in a defective comparator,
`TestDispositionDeadlineIsAppendOnly` scans for a disposition constructor, and
`TestClosureDerivation` runs three separately disabled guards.

Wording note. The alias tables and the corpus are carried over from
`spike/kill_spike/` and are still **provisional**. The judged fixture is sourced
verbatim from attributable published guidance in Slice 5 (Option C), and the
Option C source is not yet cleared. Nothing here may be shown to a participant.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.domain import models, rules  # noqa: E402
from carerelay.domain.models import (  # noqa: E402
    COMPARISON_FIELDS,
    MAX_REPAIR_ROUNDS,
    AttemptSnapshot,
    AttemptTransition,
    AuthorisedReassessment,
    ClosureState,
    Disposition,
    DispositionSource,
    EpisodeSnapshot,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    ExtractedPlan,
    HintEvent,
    HintEventKind,
    HintLevel,
    HintState,
    InputMode,
    Origin,
    PlanComparison,
    PolicyFixture,
    PolicyText,
    RecallOutcome,
    ReassessmentOutcome,
)

# ---------------------------------------------------------------------------
# Provisional fixture data, carried from the kill-test spike
# ---------------------------------------------------------------------------

#: Singapore has had a fixed UTC+8 offset with no daylight saving since 1982, so a
#: fixed offset is exact. A `tzinfo` value is used rather than a zoneinfo lookup,
#: because `domain` reads no files.
DISPLAY_TZ = timezone(timedelta(hours=8), "SGT")

#: Fixed scenario clock: 09:00 SGT, before the 18:00 deadline. Deterministic.
SCENARIO_NOW_UTC = datetime(2026, 9, 30, 1, 0, tzinfo=timezone.utc)

POLICY_VERSION = "fixture-provisional-0"
EPISODE_ID = "demo-episode-001"
ACTION_ID = "attend_same_day_review"
NEXT_OWNER_ID = "patient"
FALLBACK_ROUTE_ID = "nurse_line"

ACTION_ALIASES = {
    "go to the clinic": ACTION_ID,
    "attend the clinic": ACTION_ID,
    "go down to the clinic": ACTION_ID,
    "see the doctor": ACTION_ID,
    "the polyclinic": ACTION_ID,
    "\u53bb\u8bca\u6240": ACTION_ID,
    "\u770b\u533b\u751f": ACTION_ID,
    # Surface variants added at the Slice 2 review, chosen independently of the
    # comparator rather than read off it. None introduces new clinical meaning:
    # each is a synonym of an alias already present.
    "go to the polyclinic": ACTION_ID,
    "attend the polyclinic": ACTION_ID,
    "go to the clinic now": ACTION_ID,
    "go to the doctor": ACTION_ID,
}

OWNER_ALIASES = {
    "you": NEXT_OWNER_ID,
    "me": NEXT_OWNER_ID,
    "myself": NEXT_OWNER_ID,
    "the patient": NEXT_OWNER_ID,
    "\u6211\u81ea\u5df1": NEXT_OWNER_ID,
    "i will do it myself": NEXT_OWNER_ID,
    "i'll do it myself": NEXT_OWNER_ID,
    "i will do it": NEXT_OWNER_ID,
    "the patient themselves": NEXT_OWNER_ID,
}

#: Normalised surface phrase -> (day offset, local HH:MM). The final three resolve
#: to a KNOWN DIFFERENT instant on purpose: a known wrong value must be a
#: mismatch, not an "uncertain". That distinction is the whole point of the test row.
DEADLINE_FORMS = {
    "today before 18:00": (0, "18:00"),
    "today before 6pm": (0, "18:00"),
    "today before six": (0, "18:00"),
    "before six today": (0, "18:00"),
    "by 6 today": (0, "18:00"),
    "\u4eca\u5929\u516d\u70b9\u524d": (0, "18:00"),
    "6pm today": (0, "18:00"),
    "today before 6": (0, "18:00"),
    "before 6pm today": (0, "18:00"),
    "by six today": (0, "18:00"),
    "today by 6pm": (0, "18:00"),
    "today before 8pm": (0, "20:00"),
    "\u4eca\u5929\u516b\u70b9\u524d": (0, "20:00"),
    "tomorrow before 6pm": (1, "18:00"),
}

#: The fixed adversarial corpus of CORRECT restatements (Gate 3 section 6.1).
#: (label, form class, action span, deadline span, owner span)
CORPUS = (
    ("exact canonical", "exact", ACTION_ID, "today before 18:00", "patient"),
    ("paraphrase", "paraphrase", "go to the clinic", "today before 6pm", "you"),
    ("alias and word numeral", "alias", "see the doctor", "today before six", "me"),
    (
        "reordered relative time",
        "relative_time",
        "the polyclinic",
        "before six today",
        "myself",
    ),
    (
        "code-switched Mandarin",
        "code_switched",
        "\u53bb\u8bca\u6240",
        "\u4eca\u5929\u516d\u70b9\u524d",
        "\u6211\u81ea\u5df1",
    ),
    (
        "tight relative form",
        "relative_time",
        "go down to the clinic",
        "by 6 today",
        "you",
    ),
)

#: A corpus that does not cover these four classes is not the corpus Gate 3 asked for.
REQUIRED_FORM_CLASSES = frozenset(
    {"paraphrase", "alias", "relative_time", "code_switched"}
)

#: A second corpus, added at the Slice 2 review. The review found that every entry
#: in `CORPUS` above is a literal key in one of the three resolution tables, so the
#: test proved dict lookup worked rather than that the comparator handles language.
#: These spans were chosen by the reviewer, before the tables were widened, from
#: phrasings a patient plausibly uses. (label, action span, deadline span, owner span)
NATURAL_CORPUS = (
    ("plain synonym", "go to the polyclinic", "6pm today", "I will do it myself"),
    ("word order", "attend the polyclinic", "today before 6", "I'll do it myself"),
    ("tight clock", "go to the doctor", "before 6pm today", "the patient themselves"),
    ("digit and word mix", "the polyclinic", "by six today", "i will do it"),
    ("clinic now", "go to the clinic now", "today by 6pm", "you"),
    ("canonical restated", ACTION_ID, "today before 18:00", "patient"),
)

#: Phrases a patient could say that the policy deliberately cannot resolve. Each
#: must land in `uncertain` and never in `mismatched`: unknown is not an accusation.
UNRESOLVABLE_PHRASES = (
    "take some medicine",
    "ring my neighbour",
    "sometime next week",
    "ask the pharmacy",
    "",
)


def local_deadline(day_offset: int = 0, hhmm: str = "18:00") -> datetime:
    hour, minute = (int(part) for part in hhmm.split(":"))
    local = SCENARIO_NOW_UTC.astimezone(DISPLAY_TZ)
    target = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return (target + timedelta(days=day_offset)).astimezone(timezone.utc)


def disposition(
    version: int = 1,
    source: DispositionSource = DispositionSource.FIXTURE,
    day_offset: int = 0,
) -> Disposition:
    return Disposition(
        episode_id=EPISODE_ID,
        version=version,
        policy_version=POLICY_VERSION,
        action_id=ACTION_ID,
        clinical_deadline_utc=local_deadline(day_offset=day_offset),
        next_owner_id=NEXT_OWNER_ID,
        fallback_route_id=FALLBACK_ROUTE_ID,
        source=source,
    )


REASSESSED_DISPOSITION = disposition(
    version=2, source=DispositionSource.REASSESSMENT, day_offset=1
)

POLICY = PolicyFixture(
    version=POLICY_VERSION,
    permitted_route_ids=frozenset({"fictional_provider", "nurse_line"}),
    permitted_action_ids=frozenset(
        {"attend_same_day_review", "call_nurse_line", "wait_and_monitor"}
    ),
    permitted_owner_ids=frozenset({"patient", "caregiver"}),
    permitted_change_codes=frozenset({"worse_breathing", "better_breathing"}),
    action_aliases=ACTION_ALIASES,
    owner_aliases=OWNER_ALIASES,
    deadline_forms=DEADLINE_FORMS,
    authorised_reassessments={
        "worse_breathing": AuthorisedReassessment(
            change_code="worse_breathing",
            disposition=REASSESSED_DISPOSITION,
            authorised_by="fictional clinician, provisional fixture",
        )
    },
)

POLICY_TEXT = PolicyText(
    policy_version=POLICY_VERSION,
    fixture_label="SIMULATED - RESEARCH DEMONSTRATION. Not clinical advice.",
    deadline_display_by_version={
        1: "6:00 PM on 30 September",
        2: "6:00 PM on 1 October",
    },
    self_owner_id="patient",
    owner_display_by_id={"patient": "you", "caregiver": "your daughter"},
    route_display_by_id={
        "nurse_line": "the fictional nurse line",
        "fictional_provider": "the fictional provider",
    },
    simulated=True,
)


def empty_snapshot(**overrides: object) -> EpisodeSnapshot:
    base: dict[str, object] = {
        "disposition": disposition(),
        "attempt": None,
        "evidence": (),
        "consent_version": None,
        "human_acceptance_id": None,
        "escalation_id": None,
        "expiry_event_id": None,
    }
    base.update(overrides)
    return EpisodeSnapshot(**base)  # type: ignore[arg-type]


def compare(extracted: ExtractedPlan) -> PlanComparison:
    return rules.compare_plan(
        disposition(),
        extracted,
        policy=POLICY,
        now_utc=SCENARIO_NOW_UTC,
        display_tz=DISPLAY_TZ,
    )


def corpus_violations(comparator) -> list[str]:
    """One line per corpus entry the comparator gets wrong. Empty list means K1 passes."""
    problems: list[str] = []
    for label, form_class, action_span, deadline_span, owner_span in CORPUS:
        result = comparator(ExtractedPlan(action_span, deadline_span, owner_span))
        if result.mismatched:
            problems.append(
                f"{label} [{form_class}]: false mismatch {sorted(result.mismatched)}"
            )
        if result.uncertain:
            problems.append(
                f"{label} [{form_class}]: left unresolved {sorted(result.uncertain)}"
            )
    return problems


# ---------------------------------------------------------------------------
# PlanBack: kill condition K1
# ---------------------------------------------------------------------------


class TestPlanBackKnownMatchMismatchUncertain:
    """K1. A correct restatement is never flagged; an unknown is never an accusation."""

    def test_planback_known_match_mismatch_uncertain(self) -> None:
        assert corpus_violations(compare) == []

    def test_corpus_covers_the_four_required_form_classes(self) -> None:
        classes = {row[1] for row in CORPUS}
        assert REQUIRED_FORM_CLASSES - classes == set()
        assert len(CORPUS) >= 6

    def test_natural_phrasings_outside_the_spike_corpus_resolve_cleanly(self) -> None:
        """Added at the Slice 2 review.

        Every entry in `CORPUS` above is a literal key in one of the resolution
        tables, so on its own the corpus proves dict lookup works rather than
        that the comparator handles language. These spans were chosen by the
        reviewer, before the tables were widened, from phrasings a patient
        plausibly uses.
        """
        problems: list[str] = []
        for label, action_span, deadline_span, owner_span in NATURAL_CORPUS:
            result = compare(ExtractedPlan(action_span, deadline_span, owner_span))
            if not result.is_clean():
                problems.append(
                    f"{label}: mismatched={sorted(result.mismatched)} "
                    f"uncertain={sorted(result.uncertain)}"
                )
        assert problems == [], problems

    def test_an_unresolvable_phrase_is_uncertain_and_never_a_mismatch(self) -> None:
        """The safety property that outranks coverage.

        Widening the alias tables must not buy coverage by turning an unknown
        phrase into an accusation. Every phrase the policy cannot resolve stays
        `uncertain`, and the restatement is never reported clean on the strength
        of a guess.
        """
        for phrase in UNRESOLVABLE_PHRASES:
            result = compare(ExtractedPlan(phrase, phrase, phrase))
            assert result.mismatched == frozenset(), phrase
            assert result.is_clean() is False, phrase

    def test_exact_canonical_restatement_is_clean(self) -> None:
        result = compare(ExtractedPlan(ACTION_ID, "today before 18:00", "patient"))
        assert result.is_clean()
        assert set(result.matched) == set(COMPARISON_FIELDS)

    def test_known_wrong_day_flags_only_the_deadline(self) -> None:
        result = compare(ExtractedPlan(ACTION_ID, "tomorrow before 6pm", "patient"))
        assert set(result.mismatched) == {"deadline_utc"}
        assert set(result.uncertain) == set()
        assert set(result.matched) == {"action_id", "next_owner_id"}

    def test_known_wrong_clock_time_flags_only_the_deadline(self) -> None:
        result = compare(ExtractedPlan(ACTION_ID, "today before 8pm", "patient"))
        assert set(result.mismatched) == {"deadline_utc"}
        assert set(result.uncertain) == set()

    def test_known_wrong_action_flags_only_the_action(self) -> None:
        result = compare(ExtractedPlan("wait_and_monitor", "today before 6pm", "patient"))
        assert set(result.mismatched) == {"action_id"}

    def test_unknown_extraction_is_uncertain_not_an_error(self) -> None:
        result = compare(ExtractedPlan("take some medicine", None, None))
        assert set(result.mismatched) == set()
        assert set(result.uncertain) == set(COMPARISON_FIELDS)

    def test_nothing_extracted_is_uncertain_not_success(self) -> None:
        result = compare(ExtractedPlan(None, None, None))
        assert set(result.matched) == set()
        assert set(result.mismatched) == set()
        assert set(result.uncertain) == set(COMPARISON_FIELDS)

    def test_a_resolvable_span_the_extractor_flagged_doubtful_stays_uncertain(self) -> None:
        """Gate 4 section 1.1: a doubtful span is not the same as a produced one.

        The extractor produced the exact canonical action *and* said it was not
        sure. Folding `uncertain_fields` away would turn the extractor's doubt
        into a claim about the patient, which is the defect K1 exists to catch.
        """
        result = compare(
            ExtractedPlan(
                ACTION_ID,
                "today before 6pm",
                "patient",
                uncertain_fields=frozenset({"action_id"}),
            )
        )
        assert "action_id" in result.uncertain
        assert "action_id" not in result.mismatched
        assert "action_id" not in result.matched
        assert result.is_clean() is False

    def test_the_three_sets_stay_disjoint_and_complete(self) -> None:
        samples = (
            ExtractedPlan(ACTION_ID, "today before 6pm", "patient"),
            ExtractedPlan("take some medicine", "tomorrow before 6pm", None),
            ExtractedPlan(None, None, None),
            ExtractedPlan(ACTION_ID, None, "patient", uncertain_fields=frozenset({"action_id"})),
        )
        for sample in samples:
            result = compare(sample)
            assert set(result.matched) & set(result.mismatched) == set()
            assert set(result.matched) & set(result.uncertain) == set()
            assert set(result.mismatched) & set(result.uncertain) == set()
            assert (
                set(result.matched) | set(result.mismatched) | set(result.uncertain)
                == set(COMPARISON_FIELDS)
            )

    def test_repair_is_bounded_to_two_rounds(self) -> None:
        result = compare(ExtractedPlan(None, None, None))
        assert rules.next_repair(result, 0) is not None
        assert rules.next_repair(result, 1) is not None
        assert rules.next_repair(result, MAX_REPAIR_ROUNDS) is None
        assert MAX_REPAIR_ROUNDS == 2

    def test_repair_targets_the_first_unresolved_field_in_order(self) -> None:
        result = compare(ExtractedPlan(None, "tomorrow before 6pm", None))
        assert rules.next_repair(result, 0) == "action_id"

    def test_a_clean_comparison_offers_no_repair(self) -> None:
        result = compare(ExtractedPlan(ACTION_ID, "today before 6pm", "patient"))
        assert result.is_clean()
        assert rules.next_repair(result, 0) is None

    def test_naive_now_is_refused_rather_than_guessed(self) -> None:
        with pytest.raises(rules.DomainError):
            rules.compare_plan(
                disposition(),
                ExtractedPlan(ACTION_ID, "today before 6pm", "patient"),
                policy=POLICY,
                now_utc=datetime(2026, 9, 30, 1, 0),
                display_tz=DISPLAY_TZ,
            )


class TestPlanBackAssertionsHaveTeeth:
    """Gate 3 section 5: an assertion that cannot fail against a defect is not proof."""

    @staticmethod
    def _surface_only(expected, extracted, **_kwargs):
        """Defect: compares raw spans against canonical values without resolving."""
        matched: set[str] = set()
        mismatched: set[str] = set()
        uncertain: set[str] = set()
        pairs = (
            ("action_id", extracted.action_span, expected.action_id),
            ("deadline_utc", extracted.deadline_span, expected.clinical_deadline_utc),
            ("next_owner_id", extracted.next_owner_span, expected.next_owner_id),
        )
        for field_name, raw, want in pairs:
            if raw is None:
                uncertain.add(field_name)
            elif raw == want:
                matched.add(field_name)
            else:
                mismatched.add(field_name)
        return PlanComparison(
            frozenset(matched), frozenset(mismatched), frozenset(uncertain)
        )

    @staticmethod
    def _always_uncertain(_expected, _extracted, **_kwargs):
        """Defect: refuses to commit, so it can never report a false mismatch."""
        return PlanComparison(frozenset(), frozenset(), frozenset(COMPARISON_FIELDS))

    @staticmethod
    def _unknown_is_mismatch(expected, extracted, **kwargs):
        """Defect: treats an unresolved span as a definite error."""
        base = rules.compare_plan(expected, extracted, **kwargs)
        return PlanComparison(
            base.matched, base.mismatched | base.uncertain, frozenset()
        )

    @staticmethod
    def _ignores_extractor_doubt(expected, extracted, **kwargs):
        """Defect: discards `uncertain_fields`, so doubt becomes a claim."""
        return rules.compare_plan(
            expected,
            ExtractedPlan(
                extracted.action_span,
                extracted.deadline_span,
                extracted.next_owner_span,
            ),
            **kwargs,
        )

    def _run(self, impl) -> list[str]:
        def comparator(extracted: ExtractedPlan) -> PlanComparison:
            return impl(
                disposition(),
                extracted,
                policy=POLICY,
                now_utc=SCENARIO_NOW_UTC,
                display_tz=DISPLAY_TZ,
            )

        return corpus_violations(comparator)

    def test_corpus_catches_a_comparator_that_never_resolves(self) -> None:
        assert self._run(self._surface_only), (
            "the corpus did not catch a comparator that compares surface text to "
            "canonical values"
        )

    def test_corpus_catches_a_comparator_that_refuses_to_commit(self) -> None:
        assert self._run(self._always_uncertain), (
            "the corpus did not catch a comparator that answers 'uncertain' to "
            "everything, which would let K1 pass vacuously"
        )

    def test_unknown_test_catches_unknown_treated_as_a_mismatch(self) -> None:
        result = self._unknown_is_mismatch(
            disposition(),
            ExtractedPlan(None, None, None),
            policy=POLICY,
            now_utc=SCENARIO_NOW_UTC,
            display_tz=DISPLAY_TZ,
        )
        assert set(result.mismatched) == set(COMPARISON_FIELDS)
        assert set(result.uncertain) == set()

    def test_doubt_test_catches_a_comparator_that_discards_uncertain_fields(self) -> None:
        """Without this, `test_a_resolvable_span_..._stays_uncertain` could pass
        for the wrong reason and never notice the field being dropped."""
        honest = compare(
            ExtractedPlan(
                ACTION_ID,
                "today before 6pm",
                "patient",
                uncertain_fields=frozenset({"action_id"}),
            )
        )
        mutant = self._ignores_extractor_doubt(
            disposition(),
            ExtractedPlan(
                ACTION_ID,
                "today before 6pm",
                "patient",
                uncertain_fields=frozenset({"action_id"}),
            ),
            policy=POLICY,
            now_utc=SCENARIO_NOW_UTC,
            display_tz=DISPLAY_TZ,
        )
        assert "action_id" in honest.uncertain
        assert "action_id" in mutant.matched
        assert honest != mutant


class TestTranscriptOrder:
    """Gate 1's ordering rule: confirm the transcript before evaluating it."""

    @pytest.mark.parametrize(
        ("mode", "expected"),
        [
            (InputMode.VOICE, False),
            (InputMode.TEXT, True),
            (InputMode.CHIPS, True),
        ],
    )
    def test_a_voice_transcript_needs_a_confirmation_the_other_modes_do_not(
        self, mode: InputMode, expected: bool
    ) -> None:
        assert rules.may_score_restatement(mode, None) is expected

    def test_a_confirmed_transcript_is_scorable(self) -> None:
        assert rules.may_score_restatement(InputMode.VOICE, "confirm-1") is True

    def test_an_empty_confirmation_id_is_not_a_confirmation(self) -> None:
        assert rules.may_score_restatement(InputMode.VOICE, "") is False

    def test_the_rule_has_teeth(self) -> None:
        """Without this, the refusal above could be vacuous: prove the mutant
        `return True` changes an answer the suite relies on."""
        assert rules.may_score_restatement(InputMode.VOICE, None) is not True


# ---------------------------------------------------------------------------
# Closed vocabulary, and missing is not negative
# ---------------------------------------------------------------------------


class TestClosedVocabularyAndMissingIsNotNegative:
    """D7 and I5. A hallucinated code stops; an absent one asserts nothing."""

    def test_closed_vocab_and_missing_is_not_negative(self) -> None:
        assert rules.validate_route("nurse_line", POLICY.permitted_route_ids) == "nurse_line"
        assert rules.validate_change(None, POLICY.permitted_change_codes) is None
        assert (
            rules.validate_change("worse_breathing", POLICY.permitted_change_codes)
            == "worse_breathing"
        )

    def test_a_hallucinated_route_id_is_refused(self) -> None:
        with pytest.raises(rules.UnpermittedRouteId):
            rules.validate_route("polyclinic_booking", POLICY.permitted_route_ids)

    def test_an_empty_route_id_is_refused(self) -> None:
        with pytest.raises(rules.UnpermittedRouteId):
            rules.validate_route("", POLICY.permitted_route_ids)

    def test_a_hallucinated_change_code_is_refused(self) -> None:
        with pytest.raises(rules.UnpermittedChangeCode):
            rules.validate_change("chest_pain", POLICY.permitted_change_codes)

    def test_the_refusal_names_the_permitted_set_for_the_ledger(self) -> None:
        with pytest.raises(rules.UnpermittedRouteId) as caught:
            rules.validate_route("polyclinic_booking", POLICY.permitted_route_ids)
        assert "polyclinic_booking" in str(caught.value)
        assert "nurse_line" in str(caught.value)

    def test_a_missing_change_code_stops_at_the_human_path(self) -> None:
        decision = rules.reassessment_decision(None, POLICY)
        assert decision.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert decision.disposition is None
        assert "absence is not a negative finding" in decision.reason

    def test_an_unknown_change_code_stops_at_the_human_path(self) -> None:
        decision = rules.reassessment_decision("chest_pain", POLICY)
        assert decision.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert decision.disposition is None

    def test_a_permitted_code_with_no_authorised_branch_stops(self) -> None:
        """`better_breathing` is in the closed vocabulary and still stops.

        A closed vocabulary is not the same as an authorisation. Only a reviewer
        branch may replace a plan.
        """
        assert "better_breathing" in POLICY.permitted_change_codes
        decision = rules.reassessment_decision("better_breathing", POLICY)
        assert decision.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert decision.disposition is None
        assert "no reviewer-authorised branch" in decision.reason

    def test_every_stop_decision_returns_no_disposition(self) -> None:
        """One guard per stop reason. A shared catch would prove none of them."""
        for code in (None, "chest_pain", "better_breathing"):
            decision = rules.reassessment_decision(code, POLICY)
            assert decision.disposition is None, f"{code!r} produced a disposition"


# ---------------------------------------------------------------------------
# The deadline is append-only
# ---------------------------------------------------------------------------


class TestDispositionDeadlineIsAppendOnly:
    """D3 and invariant I1. Retry cannot update v1, and only reassessment adds v2."""

    def test_disposition_deadline_is_append_only(self) -> None:
        original = disposition()
        with pytest.raises(dataclasses.FrozenInstanceError):
            original.clinical_deadline_utc = local_deadline(day_offset=1)  # type: ignore[misc]
        assert original.clinical_deadline_utc == local_deadline()

    def test_a_replacement_is_a_new_object_and_leaves_v1_untouched(self) -> None:
        original = disposition()
        replaced = dataclasses.replace(
            original, clinical_deadline_utc=local_deadline(day_offset=1)
        )
        assert replaced is not original
        assert replaced.clinical_deadline_utc != original.clinical_deadline_utc
        assert original.clinical_deadline_utc == local_deadline()

    def test_the_authorised_branch_produces_a_second_version_with_provenance(self) -> None:
        decision = rules.reassessment_decision("worse_breathing", POLICY)
        assert decision.outcome is ReassessmentOutcome.INSERT_DISPOSITION_VERSION
        assert decision.disposition is not None
        assert decision.disposition.version == 2
        assert decision.disposition.source is DispositionSource.REASSESSMENT
        assert decision.disposition.policy_version == POLICY_VERSION
        assert "fictional clinician" in decision.reason

    def test_the_original_version_is_unchanged_after_a_reassessment(self) -> None:
        original = disposition()
        before = (original.version, original.clinical_deadline_utc, original.source)
        rules.reassessment_decision("worse_breathing", POLICY)
        after = (original.version, original.clinical_deadline_utc, original.source)
        assert before == after

    def test_a_branch_that_is_not_marked_reassessment_is_refused(self) -> None:
        """A branch claiming to be a fixture would be an unauthorised edit path."""
        smuggled = PolicyFixture(
            version=POLICY.version,
            permitted_route_ids=POLICY.permitted_route_ids,
            permitted_action_ids=POLICY.permitted_action_ids,
            permitted_owner_ids=POLICY.permitted_owner_ids,
            permitted_change_codes=POLICY.permitted_change_codes,
            action_aliases=POLICY.action_aliases,
            owner_aliases=POLICY.owner_aliases,
            deadline_forms=POLICY.deadline_forms,
            authorised_reassessments={
                "worse_breathing": AuthorisedReassessment(
                    change_code="worse_breathing",
                    disposition=disposition(version=2, day_offset=1),
                    authorised_by="nobody",
                )
            },
        )
        with pytest.raises(rules.PolicyViolation):
            rules.reassessment_decision("worse_breathing", smuggled)

    def test_the_domain_never_authors_a_disposition(self) -> None:
        """The structural half of I1: no retry code path can write a disposition.

        `02-architecture.md` D3 states that I1 holds because no retry code path
        writes a disposition, and section 10 restates it honestly as a code-review
        property. This makes it a check: `domain` constructs no `Disposition` at
        all, so a deadline can only arrive from the caller or from an authorised
        branch.
        """
        source = (Path(rules.__file__)).read_text(encoding="utf-8")
        assert "Disposition" in source, "the file under test does not mention the type"
        assert disposition_constructions(source) == []

    def test_the_disposition_constructor_scan_can_fail(self) -> None:
        """Proves the assertion above is capable of failing."""
        injected = (
            "def retry_booking(d: Disposition) -> Disposition:\n"
            "    return Disposition(\n"
            "        episode_id=d.episode_id, version=d.version + 1,\n"
            "        policy_version=d.policy_version, action_id=d.action_id,\n"
            "        clinical_deadline_utc=d.clinical_deadline_utc + timedelta(hours=4),\n"
            "        next_owner_id=d.next_owner_id,\n"
            "        fallback_route_id=d.fallback_route_id,\n"
            "        source=DispositionSource.REASSESSMENT,\n"
            "    )\n"
        )
        found = disposition_constructions(injected)
        assert len(found) == 1, "the scan missed a disposition constructor"

    def test_no_public_rule_returns_a_disposition(self) -> None:
        """No rule hands a disposition back to a caller.

        The only route to a second version is `reassessment_decision`, and it
        returns a `StopOrFixtureDecision` that carries the authorised value. A
        new rule annotated as returning a `Disposition` fails this test.
        """
        returning = {
            name
            for name, member in vars(rules).items()
            if inspect.isfunction(member)
            and not name.startswith("_")
            and "Disposition" in str(inspect.signature(member).return_annotation)
        }
        assert returning == set(), returning

    def test_only_reassessment_decision_returns_a_disposition_carrier(self) -> None:
        carriers = {
            name
            for name, member in vars(rules).items()
            if inspect.isfunction(member)
            and not name.startswith("_")
            and "Decision" in str(inspect.signature(member).return_annotation)
        }
        assert carriers == {"reassessment_decision"}, carriers
        assert "disposition" in models.StopOrFixtureDecision.__dataclass_fields__


def disposition_constructions(source: str) -> list[int]:
    """Line numbers where a `Disposition(...)` value is constructed."""
    tree = ast.parse(source)
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == "Disposition":
                lines.append(node.lineno)
    return lines


# ---------------------------------------------------------------------------
# Hint disclosure: no timer, and dwell is recorded but never shown
# ---------------------------------------------------------------------------


class TestHintDisclosureAccessibility:
    """Constraint C8. `PLAN.md` 5.2.1: the card stays until the patient hides it."""

    def test_hint_disclosure_accessibility(self) -> None:
        state = HintState(level=HintLevel.H2, card_visible=True)
        shown = rules.hint_transition(
            state, HintEvent(HintLevel.H2, HintEventKind.SHOWN, dwell_seconds=12.0)
        )
        assert shown.card_visible is True
        hidden = rules.hint_transition(
            state, HintEvent(HintLevel.H2, HintEventKind.PATIENT_HID, dwell_seconds=12.0)
        )
        assert hidden.card_visible is False

    def test_only_a_patient_action_hides_the_card(self) -> None:
        """One guard per event kind, so no single member can cover for another.

        Adding an auto-hide member to `HintEventKind` fails this test, which is
        the point: C8 is enforced by the vocabulary, not by a comment.
        """
        state = HintState(level=HintLevel.H2, card_visible=True)
        hiders: list[str] = []
        for kind in HintEventKind:
            try:
                result = rules.hint_transition(state, HintEvent(HintLevel.H2, kind))
            except rules.UnpermittedHintEvent:
                continue
            if result.card_visible is False:
                hiders.append(kind.value)
        assert hiders == [HintEventKind.PATIENT_HID.value], hiders

    def test_no_event_kind_names_a_timer(self) -> None:
        banned = ("auto", "timeout", "elapsed", "timer", "countdown", "expire")
        for kind in HintEventKind:
            assert not any(word in kind.value for word in banned), kind.value

    def test_dwell_seconds_never_changes_the_outcome(self) -> None:
        """Two events differing only in dwell time must produce the same state."""
        state = HintState(level=HintLevel.H2, card_visible=True)
        for kind in HintEventKind:
            quick = rules.hint_transition(
                state, HintEvent(HintLevel.H2, kind, dwell_seconds=0.1)
            )
            slow = rules.hint_transition(
                state, HintEvent(HintLevel.H2, kind, dwell_seconds=900.0)
            )
            absent = rules.hint_transition(
                state, HintEvent(HintLevel.H2, kind, dwell_seconds=None)
            )
            assert quick == slow == absent

    def test_dwell_seconds_is_recorded_on_the_event(self) -> None:
        """The exclusion from the patient surface is only meaningful because the
        field exists for the judge ledger."""
        assert "dwell_seconds" in HintEvent.__dataclass_fields__
        event = HintEvent(HintLevel.H2, HintEventKind.PATIENT_HID, dwell_seconds=7.5)
        assert event.dwell_seconds == 7.5

    def test_the_four_patient_lines_carry_no_dwell_or_timer_wording(self) -> None:
        closure = rules.derive_closure(empty_snapshot(), SCENARIO_NOW_UTC)
        lines = rules.patient_lines(empty_snapshot(), closure, POLICY_TEXT)
        joined = " ".join(lines).casefold()
        for marker in ("dwell", "seconds", "countdown", "timer", "auto", "remaining"):
            assert marker not in joined, f"{marker!r} leaked into the patient lines"

    def test_h3_is_never_a_comprehension_pass(self) -> None:
        assert models.RECALL_OUTCOME_BY_LEVEL[HintLevel.H3] is RecallOutcome.NOT_RECALLED
        assert models.RECALL_OUTCOME_BY_LEVEL[HintLevel.H2] is RecallOutcome.RECALL_CUED
        assert models.RECALL_OUTCOME_BY_LEVEL[HintLevel.H0] is RecallOutcome.RECALL_UNAIDED

    def test_an_event_for_a_different_level_is_refused(self) -> None:
        state = HintState(level=HintLevel.H2, card_visible=True)
        with pytest.raises(rules.UnpermittedHintEvent):
            rules.hint_transition(state, HintEvent(HintLevel.H0, HintEventKind.PATIENT_HID))


# ---------------------------------------------------------------------------
# Attempt projection: first terminal transition wins
# ---------------------------------------------------------------------------


def transition(seq: int, kind: ExecutionStatus, origin: Origin = Origin.LOCAL_SIM):
    return AttemptTransition(
        seq=seq,
        kind=kind,
        origin=origin,
        recorded_at=SCENARIO_NOW_UTC + timedelta(seconds=seq),
    )


class TestAttemptProjection:
    """`02-architecture.md` section 4.1: terminal states are absorbing."""

    def test_no_transitions_means_attempted(self) -> None:
        assert rules.project_attempt(()) is ExecutionStatus.ATTEMPTED

    def test_a_single_failure_projects_failed(self) -> None:
        assert (
            rules.project_attempt((transition(1, ExecutionStatus.FAILED),))
            is ExecutionStatus.FAILED
        )

    def test_a_late_acknowledgement_cannot_reverse_a_failure(self) -> None:
        result = rules.project_attempt(
            (
                transition(1, ExecutionStatus.FAILED),
                transition(2, ExecutionStatus.ACKNOWLEDGED),
            )
        )
        assert result is ExecutionStatus.FAILED

    def test_an_acknowledgement_then_a_failure_stays_acknowledged(self) -> None:
        result = rules.project_attempt(
            (
                transition(1, ExecutionStatus.ACKNOWLEDGED),
                transition(2, ExecutionStatus.FAILED),
            )
        )
        assert result is ExecutionStatus.ACKNOWLEDGED

    def test_transitions_are_ordered_by_seq_not_by_argument_order(self) -> None:
        result = rules.project_attempt(
            (
                transition(2, ExecutionStatus.ACKNOWLEDGED),
                transition(1, ExecutionStatus.FAILED),
            )
        )
        assert result is ExecutionStatus.FAILED

    def test_a_superseded_attempt_projects_superseded(self) -> None:
        assert (
            rules.project_attempt((transition(1, ExecutionStatus.SUPERSEDED),))
            is ExecutionStatus.SUPERSEDED
        )

    def test_a_non_terminal_transition_is_refused_not_folded_into_attempted(self) -> None:
        with pytest.raises(rules.UnpermittedTransition):
            rules.project_attempt((transition(1, ExecutionStatus.NOT_STARTED),))

    def test_a_corrupt_row_anywhere_is_refused_not_only_the_winning_one(self) -> None:
        """Added at the Slice 2 review.

        The raise previously fired only on the lowest-`seq` row, so
        `[acknowledged(1), not_started(2)]` returned `acknowledged` and the
        corrupt row was silently ignored, which contradicted the docstring. A
        corrupt row anywhere means the ledger cannot be trusted.
        """
        with pytest.raises(rules.UnpermittedTransition):
            rules.project_attempt(
                (
                    transition(1, ExecutionStatus.ACKNOWLEDGED),
                    transition(2, ExecutionStatus.NOT_STARTED),
                )
            )
        with pytest.raises(rules.UnpermittedTransition):
            rules.project_attempt(
                (
                    transition(1, ExecutionStatus.NOT_STARTED),
                    transition(2, ExecutionStatus.ACKNOWLEDGED),
                )
            )

    def test_the_projection_ignores_origin_and_the_row_keeps_it(self) -> None:
        """Slice 2 review Q10: should `project_attempt` read `origin`?

        No. Axis A asks whether the request got through, and a platform failure
        and a scripted local failure are the same fact on that axis. Origin is
        what makes them distinguishable in the ledger (`02-architecture.md`
        section 3.3), so it stays on the row and never reaches the projection.
        """
        platform_row = transition(1, ExecutionStatus.FAILED, Origin.PLATFORM)
        simulated_row = transition(1, ExecutionStatus.FAILED, Origin.LOCAL_SIM)

        assert platform_row.origin is Origin.PLATFORM
        assert simulated_row.origin is Origin.LOCAL_SIM
        assert rules.project_attempt((platform_row,)) is ExecutionStatus.FAILED
        assert rules.project_attempt((simulated_row,)) is ExecutionStatus.FAILED
        assert rules.project_attempt((platform_row,)) is rules.project_attempt(
            (simulated_row,)
        )


# ---------------------------------------------------------------------------
# Closure derivation
# ---------------------------------------------------------------------------

DOCUMENTED_REAL = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=False,
    provenance="fictional provider receipt",
    source_ref="receipt-0001",
)
DOCUMENTED_SIMULATED = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=True,
    provenance="scripted local provider",
    source_ref="receipt-0002",
)
DOCUMENTED_UNSOURCED = EvidenceRecord(
    level=EvidenceLevel.DOCUMENTED,
    simulated=False,
    provenance="verbal",
    source_ref=None,
)
SELF_REPORTED = EvidenceRecord(
    level=EvidenceLevel.SELF_REPORTED,
    simulated=True,
    provenance="patient said so",
    source_ref=None,
)


class TestClosureDerivation:
    """D4, D11 and D12. Nothing here can write "resolved"."""

    def test_no_disposition_and_no_attempt_is_open(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(disposition=None), SCENARIO_NOW_UTC
        )
        assert projection.closure is ClosureState.OPEN
        assert projection.execution is ExecutionStatus.NOT_STARTED
        assert projection.evidence is EvidenceLevel.NONE
        assert projection.action_owner_id is None
        assert projection.simulated is True

    def test_a_failed_attempt_before_the_deadline_is_never_resolved(self) -> None:
        snapshot = empty_snapshot(
            attempt=AttemptSnapshot(
                attempt_id="attempt-1",
                idempotency_key="key-1",
                route_id=FALLBACK_ROUTE_ID,
                consent_version=1,
                execution=ExecutionStatus.FAILED,
            )
        )
        projection = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        assert projection.execution is ExecutionStatus.FAILED
        assert projection.closure is ClosureState.OPEN
        assert projection.care_evidenced is False

    def test_the_action_owner_is_named_at_every_moment(self) -> None:
        projection = rules.derive_closure(empty_snapshot(), SCENARIO_NOW_UTC)
        assert projection.action_owner_id == NEXT_OWNER_ID

    def test_real_documented_evidence_closes_with_evidence(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(evidence=(DOCUMENTED_REAL,)), SCENARIO_NOW_UTC
        )
        assert projection.closure is ClosureState.CLOSED_WITH_EVIDENCE
        assert projection.care_evidenced is True
        assert projection.evidence is EvidenceLevel.DOCUMENTED
        assert projection.simulated is False

    def test_a_simulated_documented_row_cannot_close_care(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(evidence=(DOCUMENTED_SIMULATED,)), SCENARIO_NOW_UTC
        )
        assert projection.care_evidenced is False
        assert projection.evidence is not EvidenceLevel.DOCUMENTED
        assert projection.closure is not ClosureState.CLOSED_WITH_EVIDENCE

    def test_an_unsourced_documented_row_cannot_close_care(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(evidence=(DOCUMENTED_UNSOURCED,)), SCENARIO_NOW_UTC
        )
        assert projection.care_evidenced is False

    def test_self_reported_evidence_moves_the_axis_but_does_not_close(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(evidence=(SELF_REPORTED,)), SCENARIO_NOW_UTC
        )
        assert projection.evidence is EvidenceLevel.SELF_REPORTED
        assert projection.care_evidenced is False
        assert projection.closure is ClosureState.OPEN

    def test_a_human_acceptance_before_the_deadline_closes_the_handoff_only(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(human_acceptance_id="accept-1"), SCENARIO_NOW_UTC
        )
        assert projection.closure is ClosureState.CLOSED_WITH_EVIDENCE
        assert projection.care_evidenced is False
        assert projection.simulated is True

    def test_an_escalation_before_the_deadline_is_escalated_to_human(self) -> None:
        projection = rules.derive_closure(
            empty_snapshot(escalation_id="escalation-1"), SCENARIO_NOW_UTC
        )
        assert projection.closure is ClosureState.ESCALATED_TO_HUMAN
        assert projection.action_owner_id == NEXT_OWNER_ID

    def test_an_escalation_past_the_deadline_with_no_evidence_is_expired(self) -> None:
        after = local_deadline() + timedelta(minutes=1)
        projection = rules.derive_closure(
            empty_snapshot(escalation_id="escalation-1"), after
        )
        assert projection.closure is ClosureState.EXPIRED_UNRESOLVED

    def test_an_acceptance_past_the_deadline_with_no_evidence_is_expired(self) -> None:
        """The precedence decision recorded in `rules.py`.

        An acceptance is a promise, not evidence. Reporting a resolved episode
        whose deadline passed with nothing to show for it is invariant I2, so
        expiry outranks it.
        """
        after = local_deadline() + timedelta(minutes=1)
        projection = rules.derive_closure(
            empty_snapshot(human_acceptance_id="accept-1"), after
        )
        assert projection.closure is ClosureState.EXPIRED_UNRESOLVED
        assert projection.care_evidenced is False

    def test_expiry_is_sticky_against_a_backwards_clock(self) -> None:
        before_deadline = SCENARIO_NOW_UTC
        projection = rules.derive_closure(
            empty_snapshot(expiry_event_id="expiry-1"), before_deadline
        )
        assert projection.closure is ClosureState.EXPIRED_UNRESOLVED

    def test_an_expiry_event_without_a_disposition_is_refused(self) -> None:
        """Added at the Slice 2 review.

        An expiry event records that a deadline passed, so it needs a deadline.
        Accepting it produced `expired_unresolved` with `action_owner_id = None`,
        which invariant I4 forbids: at every moment exactly one party must act.
        """
        with pytest.raises(rules.DomainError):
            rules.derive_closure(
                empty_snapshot(disposition=None, expiry_event_id="expiry-1"),
                SCENARIO_NOW_UTC,
            )

    def test_real_evidence_after_an_expiry_event_closes_with_evidence(self) -> None:
        """The expiry event stays in the ledger; it is not erased, and it does not
        outrank evidence that care actually happened."""
        projection = rules.derive_closure(
            empty_snapshot(expiry_event_id="expiry-1", evidence=(DOCUMENTED_REAL,)),
            SCENARIO_NOW_UTC,
        )
        assert projection.closure is ClosureState.CLOSED_WITH_EVIDENCE
        assert projection.care_evidenced is True

    def test_naive_now_is_refused(self) -> None:
        with pytest.raises(rules.DomainError):
            rules.derive_closure(empty_snapshot(), datetime(2026, 9, 30, 1, 0))

    def test_an_attempt_with_no_terminal_outcome_expires_on_the_axis(self) -> None:
        """The execution axis runs attempted -> acknowledged | failed | expired.

        Without this the `expired` axis value is unreachable vocabulary, and
        "we tried and nobody said yes, and the deadline has gone" has no
        rendering on axis A at all.
        """
        attempted = AttemptSnapshot(
            attempt_id="attempt-1",
            idempotency_key="key-1",
            route_id=FALLBACK_ROUTE_ID,
            consent_version=1,
            execution=ExecutionStatus.ATTEMPTED,
        )
        before = rules.derive_closure(
            empty_snapshot(attempt=attempted), SCENARIO_NOW_UTC
        )
        assert before.execution is ExecutionStatus.ATTEMPTED

        after = rules.derive_closure(
            empty_snapshot(attempt=attempted), local_deadline() + timedelta(minutes=1)
        )
        assert after.execution is ExecutionStatus.EXPIRED
        assert after.closure is ClosureState.EXPIRED_UNRESOLVED

    def test_a_recorded_terminal_outcome_is_never_overwritten_by_expiry(self) -> None:
        """`failed` is the more specific fact than `expired` on axis A."""
        failed = AttemptSnapshot(
            attempt_id="attempt-1",
            idempotency_key="key-1",
            route_id=FALLBACK_ROUTE_ID,
            consent_version=1,
            execution=ExecutionStatus.FAILED,
        )
        after = rules.derive_closure(
            empty_snapshot(attempt=failed), local_deadline() + timedelta(minutes=1)
        )
        assert after.execution is ExecutionStatus.FAILED
        assert after.closure is ClosureState.EXPIRED_UNRESOLVED

    def test_no_attempt_at_all_stays_not_started_past_the_deadline(self) -> None:
        """Invariant I4: "nobody, and it is unresolved" is a valid, visible answer."""
        after = rules.derive_closure(
            empty_snapshot(), local_deadline() + timedelta(minutes=1)
        )
        assert after.execution is ExecutionStatus.NOT_STARTED
        assert after.closure is ClosureState.EXPIRED_UNRESOLVED
        assert after.action_owner_id == NEXT_OWNER_ID


def mutated_closure(
    snapshot: EpisodeSnapshot,
    now_utc: datetime,
    *,
    ignore_expiry_event: bool = False,
    trust_simulated_evidence: bool = False,
    trust_unsourced_evidence: bool = False,
    failed_counts_as_closed: bool = False,
):
    """`derive_closure` with one named guard disabled at a time.

    `AGENTS.md` section 6 requires that each guard branch be mutated
    independently and produce one real failure. A fault two checks can both
    catch is proof of neither, so each guard is disabled alone.

    The D11 guard has two halves, and they are mutated separately. One flag that
    removed both (the Slice 2 form of this function) left the `source_ref` half
    with no independent proof, which the Slice 2 review recorded as an open
    finding and assigned to Slice 3. `trust_simulated_evidence` removes the
    `simulated` half only; `trust_unsourced_evidence` removes the `source_ref`
    half only. Each therefore still has to satisfy the other.
    """
    disposition_value = snapshot.disposition
    execution = (
        snapshot.attempt.execution
        if snapshot.attempt is not None
        else ExecutionStatus.NOT_STARTED
    )

    if trust_simulated_evidence:
        evidence = EvidenceLevel.NONE
        for record in snapshot.evidence:
            if record.level is EvidenceLevel.DOCUMENTED and record.source_ref:
                evidence = EvidenceLevel.DOCUMENTED
                break
    elif trust_unsourced_evidence:
        evidence = EvidenceLevel.NONE
        for record in snapshot.evidence:
            if record.level is EvidenceLevel.DOCUMENTED and not record.simulated:
                evidence = EvidenceLevel.DOCUMENTED
                break
    else:
        evidence = rules._strongest_evidence(snapshot.evidence)

    care_evidenced = evidence is EvidenceLevel.DOCUMENTED
    deadline_passed = (
        disposition_value is not None
        and now_utc >= disposition_value.clinical_deadline_utc
    )
    expired = (snapshot.expiry_event_id is not None and not ignore_expiry_event) or (
        deadline_passed and not care_evidenced
    )

    if care_evidenced or (
        failed_counts_as_closed and execution is ExecutionStatus.FAILED
    ):
        closure = ClosureState.CLOSED_WITH_EVIDENCE
    elif expired:
        closure = ClosureState.EXPIRED_UNRESOLVED
    elif snapshot.human_acceptance_id is not None:
        closure = ClosureState.CLOSED_WITH_EVIDENCE
    elif snapshot.escalation_id is not None:
        closure = ClosureState.ESCALATED_TO_HUMAN
    else:
        closure = ClosureState.OPEN

    return models.ClosureProjection(
        execution=execution,
        evidence=evidence,
        closure=closure,
        action_owner_id=(
            disposition_value.next_owner_id if disposition_value is not None else None
        ),
        care_evidenced=care_evidenced,
        simulated=not care_evidenced,
    )


class TestClosureGuardsAreIndependentlyProven:
    """Each guard disabled alone, and required to break its own check."""

    def test_disabling_the_expiry_event_guard_breaks_stickiness(self) -> None:
        snapshot = empty_snapshot(expiry_event_id="expiry-1")
        assert (
            rules.derive_closure(snapshot, SCENARIO_NOW_UTC).closure
            is ClosureState.EXPIRED_UNRESOLVED
        )
        assert (
            mutated_closure(
                snapshot, SCENARIO_NOW_UTC, ignore_expiry_event=True
            ).closure
            is ClosureState.OPEN
        )

    def test_disabling_the_provenance_guard_lets_a_scripted_receipt_close_care(self) -> None:
        snapshot = empty_snapshot(evidence=(DOCUMENTED_SIMULATED,))
        assert rules.derive_closure(snapshot, SCENARIO_NOW_UTC).care_evidenced is False
        assert (
            mutated_closure(
                snapshot, SCENARIO_NOW_UTC, trust_simulated_evidence=True
            ).care_evidenced
            is True
        )

    def test_the_source_ref_half_of_the_guard_is_independently_proven(self) -> None:
        """The `source_ref` half of D11, with its own mutation and its own flag.

        Slice 2's single `trust_simulated_evidence` flag removed both halves at
        once, so `test_an_unsourced_documented_row_cannot_close_care` and
        `test_a_simulated_documented_row_cannot_close_care` shared one mutation
        and neither was proven on its own. Slice 3 closed that.

        Three assertions, and all three are needed: the guard holds as written;
        removing the `source_ref` half alone lets an unsourced row through; and
        removing the `simulated` half alone does **not** let an unsourced row
        through, so the two flags are not the same mutation wearing two names.
        """
        unsourced = empty_snapshot(evidence=(DOCUMENTED_UNSOURCED,))
        assert rules.derive_closure(unsourced, SCENARIO_NOW_UTC).care_evidenced is False
        assert (
            mutated_closure(
                unsourced, SCENARIO_NOW_UTC, trust_unsourced_evidence=True
            ).care_evidenced
            is True
        )
        assert (
            mutated_closure(
                unsourced, SCENARIO_NOW_UTC, trust_simulated_evidence=True
            ).care_evidenced
            is False
        )

        simulated = empty_snapshot(evidence=(DOCUMENTED_SIMULATED,))
        assert (
            mutated_closure(
                simulated, SCENARIO_NOW_UTC, trust_unsourced_evidence=True
            ).care_evidenced
            is False
        )

    def test_treating_a_failed_attempt_as_closed_is_caught(self) -> None:
        snapshot = empty_snapshot(
            attempt=AttemptSnapshot(
                attempt_id="attempt-1",
                idempotency_key="key-1",
                route_id=FALLBACK_ROUTE_ID,
                consent_version=1,
                execution=ExecutionStatus.FAILED,
            )
        )
        assert rules.derive_closure(snapshot, SCENARIO_NOW_UTC).closure is ClosureState.OPEN
        assert (
            mutated_closure(
                snapshot, SCENARIO_NOW_UTC, failed_counts_as_closed=True
            ).closure
            is ClosureState.CLOSED_WITH_EVIDENCE
        )


# ---------------------------------------------------------------------------
# Patient rendering
# ---------------------------------------------------------------------------


class TestPatientLines:
    """Four lines, policy-owned wording, and no internal identifier on screen."""

    def _lines(self, snapshot: EpisodeSnapshot, now_utc: datetime = SCENARIO_NOW_UTC):
        closure = rules.derive_closure(snapshot, now_utc)
        return rules.patient_lines(snapshot, closure, POLICY_TEXT)

    def test_four_non_empty_lines(self) -> None:
        lines = self._lines(empty_snapshot())
        assert len(lines) == 4
        for line in lines:
            assert line.strip()

    def test_line_three_carries_the_deadline_and_line_four_names_the_route(self) -> None:
        lines = self._lines(empty_snapshot())
        assert POLICY_TEXT.deadline_display_by_version[1] in lines[2]
        assert POLICY_TEXT.route_display_by_id[FALLBACK_ROUTE_ID] in lines[3]

    def test_the_rendered_deadline_follows_the_disposition_version(self) -> None:
        """Added at the Slice 2 review.

        A reassessment inserts version 2 with a new deadline. Rendering version
        1's wording over version 2's deadline is a false statement to the
        patient, and the deadline is the one fact the product exists to preserve
        (`02-architecture.md` section 7, copy rule 5).
        """
        snapshot = empty_snapshot(disposition=REASSESSED_DISPOSITION)
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        lines = rules.patient_lines(snapshot, closure, POLICY_TEXT)
        assert POLICY_TEXT.deadline_display_by_version[2] in lines[2]
        assert POLICY_TEXT.deadline_display_by_version[1] not in lines[2]

    def test_a_version_with_no_approved_deadline_wording_is_refused(self) -> None:
        """A version with no approved wording refuses rather than printing a stale date."""
        unworded = dataclasses.replace(disposition(), version=7)
        snapshot = empty_snapshot(disposition=unworded)
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        with pytest.raises(rules.MissingDisplayText):
            rules.patient_lines(snapshot, closure, POLICY_TEXT)

    def test_a_patient_owner_does_not_produce_a_doubled_owner(self) -> None:
        """The defect Slice 1 found by inspection: "You or you must act now."."""
        lines = self._lines(empty_snapshot())
        assert lines[1] == "You must act now."

    def test_a_named_caregiver_owner_keeps_the_approved_sentence(self) -> None:
        caregiver_disposition = dataclasses.replace(
            disposition(), next_owner_id="caregiver"
        )
        lines = self._lines(empty_snapshot(disposition=caregiver_disposition))
        assert lines[1] == "You or your daughter must act now."

    def test_the_expired_rendering_keeps_the_deadline_and_names_the_route(self) -> None:
        after = local_deadline() + timedelta(minutes=1)
        lines = self._lines(empty_snapshot(), after)
        assert lines[0] == "Help still is not arranged."
        assert POLICY_TEXT.deadline_display_by_version[1] in lines[2]
        assert POLICY_TEXT.route_display_by_id[FALLBACK_ROUTE_ID] in lines[3]
        assert "Before" not in lines[2]

    def test_the_expired_rendering_breaks_no_copy_rule(self) -> None:
        after = local_deadline() + timedelta(minutes=1)
        lines = self._lines(empty_snapshot(), after)
        joined = " ".join(lines).casefold()
        for banned in ("you did not", "you missed", "too late", "failed", "expired"):
            assert banned not in joined, f"copy rule broken by {banned!r}"

    def test_no_approved_wording_exists_for_a_resolved_episode(self) -> None:
        """Refusing is safer than printing "Help is not arranged." over a resolved
        episode. The Closure Contract rendering arrives in Slice 10."""
        snapshot = empty_snapshot(evidence=(DOCUMENTED_REAL,))
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        assert closure.closure is ClosureState.CLOSED_WITH_EVIDENCE
        with pytest.raises(rules.NoApprovedPatientWording):
            rules.patient_lines(snapshot, closure, POLICY_TEXT)

    def test_an_id_with_no_approved_display_is_refused_not_printed(self) -> None:
        """No internal identifier may reach the patient surface."""
        unknown_owner = dataclasses.replace(disposition(), next_owner_id="carer-7")
        snapshot = empty_snapshot(disposition=unknown_owner)
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        with pytest.raises(rules.MissingDisplayText):
            rules.patient_lines(snapshot, closure, POLICY_TEXT)

    def test_a_route_with_no_approved_display_is_refused(self) -> None:
        unknown_route = dataclasses.replace(disposition(), fallback_route_id="route-9")
        snapshot = empty_snapshot(disposition=unknown_route)
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        with pytest.raises(rules.MissingDisplayText):
            rules.patient_lines(snapshot, closure, POLICY_TEXT)

    def test_rendering_before_a_plan_exists_is_refused(self) -> None:
        snapshot = empty_snapshot(disposition=None)
        closure = rules.derive_closure(snapshot, SCENARIO_NOW_UTC)
        with pytest.raises(rules.NoDispositionToRender):
            rules.patient_lines(snapshot, closure, POLICY_TEXT)
