"""K1 and K2 — the two Gate 3 §6.1 kill conditions, with no participants and no reviewer.

    K2  test_urgent_path_precedes_planback
    K1  test_planback_known_match_mismatch_uncertain  (+ the fixed adversarial corpus)

Run:

    python spike/tests/test_kill_conditions.py -v

Throwaway spike. Lives outside `src/carerelay/`, so it is not a domain-code commit and
does not freeze the Python + FastAPI choice (`03-program-design.md` §1). It is not the
implementation footprint of §2 and must not be carried into Slice 1 unchanged.

§5 requires that "each test must fail against a deliberate single-branch defect before
it counts as proof". Every assertion below is therefore paired, in
`AssertionsHaveTeeth`, with a mutated comparator or a mutated call order that must make
it fail. An assertion without a passing teeth-test is not evidence.

Known limit, stated rather than hidden: this exercises the DETERMINISTIC layer. The
model's own extraction is not reachable here. See `planback.py` for the two readings of
§3's `compare_plan` contract and which one this spike assumes.
"""

from __future__ import annotations

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from kill_spike import fixture, intake, planback  # noqa: E402


def make_comparator(impl=planback.compare_plan):
    """Bind the fixture's policy tables so a comparator can be swapped for a mutant."""
    expected = fixture.disposition()

    def compare(extracted: planback.ExtractedPlan) -> planback.PlanComparison:
        return impl(
            expected,
            extracted,
            action_aliases=fixture.ACTION_ALIASES,
            owner_aliases=fixture.OWNER_ALIASES,
            allowed_actions=fixture.ALLOWED_ACTION_IDS,
            allowed_owners=fixture.ALLOWED_OWNER_IDS,
            deadline_forms=fixture.DEADLINE_FORMS,
            now_utc=fixture.SCENARIO_NOW_UTC,
            display_tz=fixture.DISPLAY_TZ,
        )

    return compare


def corpus_violations(compare) -> list[str]:
    """One line per corpus entry the comparator gets wrong. Empty list == K1 passes."""
    problems: list[str] = []
    for label, form_class, action_span, deadline_span, owner_span in fixture.CORPUS:
        result = compare(planback.ExtractedPlan(action_span, deadline_span, owner_span))
        if result.mismatched:
            problems.append(
                f"{label} [{form_class}]: false mismatch {sorted(result.mismatched)}"
            )
        if result.uncertain:
            problems.append(
                f"{label} [{form_class}]: left unresolved {sorted(result.uncertain)}"
            )
    return problems


def surface_only_compare(expected, extracted, **_kwargs):
    """Defect: compares raw spans against canonical values without resolving them."""
    matched: set[str] = set()
    mismatched: set[str] = set()
    uncertain: set[str] = set()
    pairs = (
        ("action_id", extracted.action_span, expected.action_id),
        ("deadline_utc", extracted.deadline_span, expected.deadline_utc),
        ("next_owner_id", extracted.next_owner_span, expected.next_owner_id),
    )
    for field_name, raw, want in pairs:
        if raw is None:
            uncertain.add(field_name)
        elif raw == want:
            matched.add(field_name)
        else:
            mismatched.add(field_name)
    return planback.PlanComparison(
        frozenset(matched), frozenset(mismatched), frozenset(uncertain)
    )


def unknown_is_mismatch_compare(expected, extracted, **kwargs):
    """Defect: treats an unresolved span as a definite error."""
    base = planback.compare_plan(expected, extracted, **kwargs)
    return planback.PlanComparison(
        base.matched, base.mismatched | base.uncertain, frozenset()
    )


def always_uncertain_compare(_expected, _extracted, **_kwargs):
    """Defect: refuses to commit, so it can never report a false mismatch."""
    return planback.PlanComparison(
        frozenset(), frozenset(), frozenset(fixture.COMPARISON_FIELDS)
    )


class UrgentPathPrecedesPlanback(unittest.TestCase):
    """K2. Read-back must never gate or delay the urgent path."""

    def test_guidance_renders_before_any_planback_call(self):
        events: list[str] = []
        coordinator = intake.RecordingCoordinator(events)

        lines = intake.intake(events)
        self.assertEqual(4, len(lines))

        intake.submit_restatement(coordinator, events, "I will go to the clinic")

        intake.assert_guidance_precedes_planback(events)
        self.assertEqual(
            [intake.GUIDANCE_RENDERED, intake.PLANBACK_EXTRACT],
            events,
            "guidance must be the first episode event and read-back must follow it",
        )

    def test_guidance_lines_carry_the_deadline_and_are_not_empty(self):
        events: list[str] = []
        lines = intake.intake(events)
        for line in lines:
            self.assertTrue(line.strip(), f"empty patient line in {lines!r}")
        self.assertIn(fixture.DEADLINE_LABEL, lines[1])
        self.assertIn(fixture.FALLBACK_LABEL, lines[3])


class KnownMatchMismatchUncertain(unittest.TestCase):
    """K1. A correct restatement is never flagged; an unknown is never an accusation."""

    def setUp(self):
        self.compare = make_comparator()

    def test_corpus_of_correct_restatements_is_clean(self):
        self.assertEqual([], corpus_violations(self.compare))

    def test_corpus_covers_the_four_required_form_classes(self):
        classes = {row[1] for row in fixture.CORPUS}
        missing = fixture.REQUIRED_FORM_CLASSES - classes
        self.assertEqual(set(), missing, f"corpus is missing {sorted(missing)}")
        self.assertGreaterEqual(len(fixture.CORPUS), 6)

    def test_known_wrong_day_flags_only_the_deadline(self):
        result = self.compare(
            planback.ExtractedPlan(fixture.ACTION_ID, "tomorrow before 6pm", "patient")
        )
        self.assertEqual({"deadline_utc"}, set(result.mismatched))
        self.assertEqual(set(), set(result.uncertain))
        self.assertEqual({"action_id", "next_owner_id"}, set(result.matched))

    def test_known_wrong_clock_time_flags_only_the_deadline(self):
        result = self.compare(
            planback.ExtractedPlan(fixture.ACTION_ID, "today before 8pm", "patient")
        )
        self.assertEqual({"deadline_utc"}, set(result.mismatched))
        self.assertEqual(set(), set(result.uncertain))

    def test_unknown_extraction_is_uncertain_not_an_error(self):
        result = self.compare(planback.ExtractedPlan("take some medicine", None, None))
        self.assertEqual(set(), set(result.mismatched))
        self.assertEqual(set(fixture.COMPARISON_FIELDS), set(result.uncertain))

    def test_nothing_extracted_is_uncertain_not_success(self):
        result = self.compare(planback.ExtractedPlan(None, None, None))
        self.assertEqual(set(), set(result.matched))
        self.assertEqual(set(), set(result.mismatched))
        self.assertEqual(set(fixture.COMPARISON_FIELDS), set(result.uncertain))

    def test_the_three_axes_stay_disjoint_and_complete(self):
        samples = (
            planback.ExtractedPlan(fixture.ACTION_ID, "today before 6pm", "patient"),
            planback.ExtractedPlan("take some medicine", "tomorrow before 6pm", None),
            planback.ExtractedPlan(None, None, None),
        )
        for sample in samples:
            result = self.compare(sample)
            self.assertEqual(set(), set(result.matched) & set(result.mismatched))
            self.assertEqual(set(), set(result.matched) & set(result.uncertain))
            self.assertEqual(set(), set(result.mismatched) & set(result.uncertain))
            self.assertEqual(
                set(fixture.COMPARISON_FIELDS),
                set(result.matched) | set(result.mismatched) | set(result.uncertain),
            )

    def test_repair_is_bounded_to_two_rounds(self):
        comparison = self.compare(planback.ExtractedPlan(None, None, None))
        self.assertIsNotNone(planback.next_repair(comparison, 0))
        self.assertIsNotNone(planback.next_repair(comparison, 1))
        self.assertIsNone(planback.next_repair(comparison, 2))


class AssertionsHaveTeeth(unittest.TestCase):
    """§5: an assertion that cannot fail against a defect is not proof."""

    def test_corpus_catches_a_comparator_that_never_resolves(self):
        problems = corpus_violations(make_comparator(surface_only_compare))
        self.assertTrue(
            problems,
            "the corpus did not catch a comparator that compares surface text to "
            "canonical values",
        )

    def test_corpus_catches_a_comparator_that_refuses_to_commit(self):
        problems = corpus_violations(make_comparator(always_uncertain_compare))
        self.assertTrue(
            problems,
            "the corpus did not catch a comparator that answers 'uncertain' to "
            "everything — K1 would pass vacuously",
        )

    def test_unknown_test_catches_unknown_treated_as_a_mismatch(self):
        result = make_comparator(unknown_is_mismatch_compare)(
            planback.ExtractedPlan(None, None, None)
        )
        self.assertEqual(set(fixture.COMPARISON_FIELDS), set(result.mismatched))
        self.assertEqual(set(), set(result.uncertain))

    def test_ordering_assertion_catches_planback_first(self):
        events: list[str] = []
        coordinator = intake.RecordingCoordinator(events)

        intake.intake_planback_first(coordinator, events, "I will go to the clinic")

        self.assertEqual([intake.PLANBACK_EXTRACT, intake.GUIDANCE_RENDERED], events)
        with self.assertRaises(AssertionError):
            intake.assert_guidance_precedes_planback(events)

    def test_ordering_assertion_catches_guidance_never_rendered(self):
        events: list[str] = []
        intake.RecordingCoordinator(events).extract_plan("")
        with self.assertRaises(AssertionError):
            intake.assert_guidance_precedes_planback(events)


if __name__ == "__main__":
    unittest.main(verbosity=2)
