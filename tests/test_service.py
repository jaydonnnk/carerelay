"""Slice 4 service tests. Every guard here must be able to fail.

The four things Slice 4 claims are: a transcript is confirmed before it is
scored, two repairs is the cap, the hint card stays until the patient hides it,
and a coordinator that cannot answer stops the flow without recording a round.
Each of those is a **refusal**, and a refusal that was never seen to bite is a
comment, not a guard. `TestGuardsHaveTeeth` at the bottom disables each one in
turn and requires the paired assertion to change.

Every test gets a fresh in-memory store. That is not convenience: the clinical
record is append-only, so a shared database cannot be reset between tests, and a
second intake would be refused as a repeat assessment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay import service as service_module  # noqa: E402
from carerelay import state as state_module  # noqa: E402
from carerelay.coordinator import (  # noqa: E402
    AllowedPlanValues,
    CoordinatorUnavailable,
    LocalSimulationCoordinator,
)
from carerelay.demo import fixture  # noqa: E402
from carerelay.domain import rules  # noqa: E402
from carerelay.domain.models import (  # noqa: E402
    CallbackResult,
    ClosureState,
    ExecutionStatus,
    ExtractedPlan,
    HintEventKind,
    HintLevel,
    InputMode,
    Origin,
    ReceiptDisposition,
    ReassessmentOutcome,
    RecallOutcome,
)
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.tools import McpTools  # noqa: E402
from carerelay.service import (  # noqa: E402
    ConsentRequired,
    EpisodeAlreadyAssessed,
    EpisodeService,
    IntakeNotRecognised,
    NoAttemptForRoute,
    NoDispositionYet,
    OriginNotWired,
    RepairCapReached,
    ScenarioClock,
    StaleRestatement,
    UnconfirmedTranscript,
)
from carerelay.state import (  # noqa: E402
    RepairRoundOutOfRange,
    UnconfirmedTranscript as StoreUnconfirmedTranscript,
    open_store,
)

EPISODE = "ep-001"

#: A restatement that resolves to exactly the fixture's plan.
CORRECT = "see the doctor today before 6pm myself"
#: A known, different deadline: a mismatch, not an uncertainty (kill condition K1).
WRONG_DAY = "see the doctor tomorrow before 6pm myself"
#: Nothing the policy can resolve.
UNRESOLVABLE = "not sure at all"


@pytest.fixture()
def store():
    handle = open_store(":memory:")
    yield handle
    handle.close()


@pytest.fixture()
def service(store):
    return _build(store)


def _build(store, coordinator=None):
    if coordinator is None:
        # Slice 6: the coordinator reaches the world through the MCP tool
        # surface, so it needs one even in a test that only exercises PlanBack.
        coordinator = LocalSimulationCoordinator(
            McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())
        )
    return EpisodeService(
        store,
        coordinator=coordinator,
        clock=ScenarioClock(fixture.SCENARIO_NOW_UTC),
        policy=fixture.policy(),
        policy_text=fixture.policy_text(),
        display_tz=fixture.DISPLAY_TZ,
        disposition_factory=fixture.disposition,
        bound_complaint=fixture.BOUND_COMPLAINT,
        policy_provenance="test: provisional",
    )


@pytest.fixture()
def assessed(service: EpisodeService) -> str:
    service.ensure_episode(EPISODE, "test persona")
    service.intake(EPISODE, fixture.BOUND_COMPLAINT)
    return EPISODE


class StubCoordinator:
    """A coordinator that returns a fixed plan, so a test controls extraction."""

    simulated = True

    def __init__(self, extracted: ExtractedPlan | None = None) -> None:
        self._extracted = extracted or ExtractedPlan(None, None, None)
        self.calls: list[str] = []

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        self.calls.append(confirmed_text)
        return self._extracted


class DeadCoordinator:
    simulated = True

    def extract_plan(
        self, confirmed_text: str, allowed_values: AllowedPlanValues
    ) -> ExtractedPlan:
        raise CoordinatorUnavailable("no credentials; the Gate A spike is unrun")


# ---------------------------------------------------------------------------
# The transcript ordering rule
# ---------------------------------------------------------------------------


class TestTranscriptOrderAndRepairCap:
    """Gate 3 section 5 names this test. Three claims, each independently."""

    def test_an_unconfirmed_voice_transcript_cannot_be_scored(
        self, service: EpisodeService, assessed: str
    ) -> None:
        with pytest.raises(UnconfirmedTranscript):
            service.submit_restatement(
                assessed, CORRECT, HintLevel.H0, input_mode=InputMode.VOICE
            )

    def test_a_confirmed_voice_transcript_can_be_scored(
        self, service: EpisodeService, assessed: str
    ) -> None:
        confirmation_id = service.confirm_transcript(assessed, CORRECT)
        outcome = service.submit_restatement(
            assessed,
            CORRECT,
            HintLevel.H0,
            confirmation_id,
            input_mode=InputMode.VOICE,
        )
        assert outcome.understood is True
        assert outcome.comparison.mismatched == frozenset()

    def test_a_confirmation_covers_the_text_being_scored(
        self, service: EpisodeService, assessed: str
    ) -> None:
        """Confirm one transcript, score another. The digest must catch it."""
        confirmation_id = service.confirm_transcript(assessed, CORRECT)
        with pytest.raises(UnconfirmedTranscript):
            service.submit_restatement(
                assessed,
                "a completely different sentence",
                HintLevel.H0,
                confirmation_id,
                input_mode=InputMode.VOICE,
            )

    def test_a_text_restatement_needs_no_confirmation(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.submit_restatement(
            assessed, CORRECT, HintLevel.H0, input_mode=InputMode.TEXT
        )
        assert outcome.understood is True

    def test_two_repairs_is_the_maximum(
        self, service: EpisodeService, assessed: str
    ) -> None:
        """Round zero, then two repairs. The third is refused."""
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        assert outcome.repair_round == 0
        assert outcome.next_repair_field == "deadline_utc"
        assert outcome.routes_to_human_path is False

        first = service.repair_restatement(
            outcome.restatement_id, WRONG_DAY, HintLevel.H0
        )
        assert first.repair_round == 1
        assert first.routes_to_human_path is False

        second = service.repair_restatement(
            first.restatement_id, WRONG_DAY, HintLevel.H0
        )
        assert second.repair_round == 2
        # The second repair still mismatches, and no third round exists, so this
        # is the point where the patient is handed to a human.
        assert second.routes_to_human_path is True
        assert second.human_path_route_id == "nurse_line"

        with pytest.raises(RepairCapReached):
            service.repair_restatement(second.restatement_id, WRONG_DAY, HintLevel.H0)

    def test_repairing_an_older_round_cannot_evade_the_cap(
        self, service: EpisodeService, assessed: str
    ) -> None:
        """Every round is its own row, so re-repairing round zero would fork the
        ladder and the cap would never bite."""
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        service.repair_restatement(outcome.restatement_id, WRONG_DAY, HintLevel.H0)
        with pytest.raises(StaleRestatement):
            service.repair_restatement(
                outcome.restatement_id, WRONG_DAY, HintLevel.H0
            )

    def test_a_repair_that_lands_is_a_clean_pass(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        repaired = service.repair_restatement(
            outcome.restatement_id, CORRECT, HintLevel.H0
        )
        assert repaired.understood is True
        assert repaired.routes_to_human_path is False
        assert repaired.outcome is RecallOutcome.RECALL_UNAIDED


# ---------------------------------------------------------------------------
# Recorded outcomes
# ---------------------------------------------------------------------------


class TestRecordedOutcomes:
    def test_an_unaided_match_records_recall_unaided(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.submit_restatement(assessed, CORRECT, HintLevel.H0)
        assert outcome.outcome is RecallOutcome.RECALL_UNAIDED

    def test_h3_is_not_recalled_even_when_its_comparison_is_clean(self, service, assessed):
        """The plan was revealed. That is never a comprehension pass (C6)."""
        outcome = service.submit_restatement(assessed, CORRECT, HintLevel.H3)
        assert outcome.understood is True
        assert outcome.outcome is RecallOutcome.NOT_RECALLED

    def test_a_mismatched_round_records_not_recalled(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        assert outcome.outcome is RecallOutcome.NOT_RECALLED

    def test_an_unresolvable_span_is_uncertain_and_never_a_mismatch(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.submit_restatement(assessed, UNRESOLVABLE, HintLevel.H0)
        assert outcome.comparison.mismatched == frozenset()
        assert set(outcome.comparison.uncertain) == {
            "action_id",
            "deadline_utc",
            "next_owner_id",
        }
        assert outcome.understood is False
        # Slice 4 review B1. An unrecognised answer achieved no recall, so it
        # records `not_recalled` at H0 exactly as a mismatched round does. Without
        # this line a mutant that drops the uncertainty half of `understood`
        # records `recall_unaided` here, which is a false recall pass written into
        # the clinical record, and the whole suite stays green.
        assert outcome.outcome is RecallOutcome.NOT_RECALLED

    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            (HintLevel.H0, RecallOutcome.RECALL_UNAIDED),
            (HintLevel.H1, RecallOutcome.RECALL_SCAFFOLDED),
            (HintLevel.H2, RecallOutcome.RECALL_CUED),
            (HintLevel.H3, RecallOutcome.NOT_RECALLED),
        ],
    )
    def test_the_record_carries_the_hint_level_and_the_round(
        self, service, store, assessed, level, expected
    ):
        """Every rung of the ladder, not just H2. Slice 4 review B2.

        The exit contract says "H0 to H3 recorded". Before this parametrisation
        the cited test exercised H2 only, so changing the `H1` mapping to
        `recall_unaided` broke no test anywhere in the suite. Each case is clean
        (`CORRECT` resolves to the plan), so the recorded outcome is exactly the
        `RECALL_OUTCOME_BY_LEVEL` entry for that rung and the mapping table is
        exercised whole.
        """
        outcome = service.submit_restatement(assessed, CORRECT, level)
        record = store.get_restatement(outcome.restatement_id)
        assert record.hint_level is level
        assert record.repair_round == 0
        assert record.outcome is expected


# ---------------------------------------------------------------------------
# The hint ladder
# ---------------------------------------------------------------------------


class TestHintLadder:
    def test_the_card_stays_visible_until_the_patient_hides_it(
        self, service: EpisodeService, assessed: str
    ) -> None:
        shown = service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.SHOWN, dwell_seconds=4.5
        )
        assert shown.card_visible is True
        hidden = service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.PATIENT_HID, dwell_seconds=9.0
        )
        assert hidden.card_visible is False

    def test_dwell_seconds_is_recorded_for_the_ledger_only(
        self, service, store, assessed
    ):
        service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.SHOWN, dwell_seconds=4.5
        )
        events = store.list_hint_events(assessed)
        assert len(events) == 1
        assert events[0].dwell_seconds == 4.5

    def test_no_event_vocabulary_member_hides_the_card_without_a_patient_action(
        self,
    ) -> None:
        """C8 as a property of the vocabulary, not of a caller."""
        hiding = {
            member.value
            for member in HintEventKind
            if "hid" in member.value or "auto" in member.value
        }
        assert hiding == {"patient_hid"}

    def test_a_dwell_only_difference_changes_nothing(self, service, assessed):
        with_dwell = service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.SHOWN, dwell_seconds=1.0
        )
        service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.PATIENT_HID, dwell_seconds=0.0
        )
        later = service.record_hint_event(
            assessed, HintLevel.H2, HintEventKind.SHOWN, dwell_seconds=600.0
        )
        assert with_dwell.card_visible == later.card_visible


# ---------------------------------------------------------------------------
# The coordinator failing
# ---------------------------------------------------------------------------


class TestCoordinatorFailure:
    def test_a_dead_coordinator_stops_the_flow_without_recording_a_round(
        self, store, assessed: str
    ) -> None:
        dead = _build(store, coordinator=DeadCoordinator())
        with pytest.raises(CoordinatorUnavailable):
            dead.submit_restatement(assessed, CORRECT, HintLevel.H0)
        assert store.list_restatements(assessed) == (), (
            "a round was recorded for a restatement that was never scored"
        )

    def test_a_dead_coordinator_does_not_record_a_repair(
        self, store, assessed: str
    ) -> None:
        """A real round exists, so the refusal is the coordinator and not a
        missing id."""
        live = _build(store)
        outcome = live.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        before = len(store.list_restatements(assessed))

        dead = _build(store, coordinator=DeadCoordinator())
        with pytest.raises(CoordinatorUnavailable):
            dead.repair_restatement(outcome.restatement_id, WRONG_DAY, HintLevel.H0)
        assert len(store.list_restatements(assessed)) == before


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


class TestRefusals:
    def test_a_restatement_before_any_plan_exists_is_refused(self, service) -> None:
        service.ensure_episode(EPISODE, "test persona")
        with pytest.raises(NoDispositionYet):
            service.submit_restatement(EPISODE, CORRECT, HintLevel.H0)

    def test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path(
        self, service
    ) -> None:
        service.ensure_episode(EPISODE, "test persona")
        with pytest.raises(IntakeNotRecognised):
            service.intake(EPISODE, "something this fixture does not cover")

    def test_a_second_intake_is_refused(self, service, assessed: str) -> None:
        with pytest.raises(EpisodeAlreadyAssessed):
            service.intake(assessed, fixture.BOUND_COMPLAINT)

    def test_creating_an_episode_writes_no_disposition(self, service) -> None:
        service.ensure_episode(EPISODE, "test persona")
        assert service._store.load_snapshot(EPISODE).disposition is None

    def test_the_record_refuses_an_unconfirmed_voice_row_on_its_own(
        self, store, assessed: str
    ) -> None:
        """The second layer: bypassing the service guard must not be enough."""
        with pytest.raises(StoreUnconfirmedTranscript):
            store.record_restatement(
                assessed,
                disposition_version=1,
                hint_level=HintLevel.H0,
                input_mode=InputMode.VOICE,
                transcript_confirmed=False,
                extracted=ExtractedPlan("see the doctor", "today before 6pm", "myself"),
                comparison=_empty_comparison(),
                repair_round=0,
                outcome=RecallOutcome.RECALL_UNAIDED,
                dwell_seconds=None,
                now_utc=fixture.SCENARIO_NOW_UTC,
            )

    def test_the_record_refuses_a_third_repair_round_on_its_own(
        self, store, assessed: str
    ) -> None:
        with pytest.raises(RepairRoundOutOfRange):
            store.record_restatement(
                assessed,
                disposition_version=1,
                hint_level=HintLevel.H0,
                input_mode=InputMode.TEXT,
                transcript_confirmed=False,
                extracted=ExtractedPlan(None, None, None),
                comparison=_empty_comparison(),
                repair_round=3,
                outcome=RecallOutcome.NOT_RECALLED,
                dwell_seconds=None,
                now_utc=fixture.SCENARIO_NOW_UTC,
            )


def _empty_comparison():
    from carerelay.domain.models import PlanComparison  # noqa: PLC0415

    return PlanComparison(frozenset(), frozenset(), frozenset())


# ---------------------------------------------------------------------------
# The guards can fail
# ---------------------------------------------------------------------------


class TestGuardsHaveTeeth:
    """Disable each guard; its assertion must change. A green guard that was
    never seen red is not evidence."""

    def test_without_the_transcript_rule_a_voice_restatement_is_scored(
        self, service: EpisodeService, assessed: str, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            rules, "may_score_restatement", lambda mode, cid: True
        )
        try:
            service.submit_restatement(
                assessed, CORRECT, HintLevel.H0, input_mode=InputMode.VOICE
            )
        except StoreUnconfirmedTranscript:
            return  # the record-level guard still refuses, which is the point
        pytest.fail(
            "the transcript rule was bypassed and nothing refused; the guard "
            "is not doing the work"
        )

    def test_without_the_cap_a_third_repair_is_scored(
        self, store, assessed: str, monkeypatch
    ) -> None:
        monkeypatch.setattr(service_module, "MAX_REPAIR_ROUNDS", 5)
        monkeypatch.setattr(state_module, "MAX_REPAIR_ROUNDS", 5)
        service = _build(store)
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        first = service.repair_restatement(outcome.restatement_id, WRONG_DAY, HintLevel.H0)
        second = service.repair_restatement(first.restatement_id, WRONG_DAY, HintLevel.H0)
        third = service.repair_restatement(second.restatement_id, WRONG_DAY, HintLevel.H0)
        assert third.repair_round == 3, (
            "raising the cap did not allow a third round, so the cap was not "
            "what stopped it"
        )

    def test_a_mutant_hint_transition_changes_the_answer(self, service, assessed, monkeypatch):
        """The honest answer is False; a mutant that never hides must make it True.

        Both halves matter: without the first, the assertion could be passing for
        the wrong reason, and without the second the guard would be vacuous.
        """
        service.record_hint_event(assessed, HintLevel.H2, HintEventKind.SHOWN)
        service.record_hint_event(assessed, HintLevel.H2, HintEventKind.PATIENT_HID)
        assert service.hint_state(assessed).card_visible is False

        monkeypatch.setattr(
            rules,
            "hint_transition",
            lambda state, event: type(state)(level=state.level, card_visible=True),
        )
        assert service.hint_state(assessed).card_visible is True

    def test_without_the_stale_check_a_forked_repair_is_accepted(
        self, service: EpisodeService, assessed: str, monkeypatch
    ) -> None:
        outcome = service.submit_restatement(assessed, WRONG_DAY, HintLevel.H0)
        service.repair_restatement(outcome.restatement_id, WRONG_DAY, HintLevel.H0)
        monkeypatch.setattr(
            service._store,
            "list_restatements",
            lambda episode_id: (
                service._store.get_restatement(outcome.restatement_id),
            ),
        )
        again = service.repair_restatement(
            outcome.restatement_id, WRONG_DAY, HintLevel.H0
        )
        assert again.repair_round == 1, (
            "disabling the latest-round check did not re-open round zero, so "
            "the check was not what stopped the fork"
        )


# ---------------------------------------------------------------------------
# Slice 5: barriers, escalation and reassessment
# ---------------------------------------------------------------------------


class TestBarriers:
    """`domain` judges the route; this layer records what it decided.

    Gate 3's named test, first half: **a hallucinated route id stops at the human
    path**. The refusal is recorded as well as raised, because the record is the
    evidence that the episode reached the human path and a caller that only sees
    the exception cannot show it.
    """

    def test_a_permitted_route_is_recorded(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.record_barrier(assessed, "no transport today", "nurse_line")
        assert outcome.permitted_route_id == "nurse_line"
        assert outcome.stopped_at_human_path is False
        assert outcome.human_path_route_id == fixture.FALLBACK_ROUTE_ID
        assert len(service._store.list_barriers(assessed)) == 1

    def test_a_hallucinated_route_is_refused_and_still_recorded(
        self, service: EpisodeService, assessed: str
    ) -> None:
        with pytest.raises(rules.UnpermittedRouteId):
            service.record_barrier(assessed, "no transport", "teleport_clinic")
        rows = service._store.list_barriers(assessed)
        assert len(rows) == 1, (
            "the refusal was raised but not recorded, so the ledger cannot show "
            "that the episode stopped at the human path"
        )
        assert rows[0]["permitted_route_id"] is None
        assert rows[0]["stopped_at_human_path"] == 1

    def test_a_barrier_before_a_plan_is_refused(self, service: EpisodeService) -> None:
        service.ensure_episode(EPISODE, "test persona")
        with pytest.raises(NoDispositionYet):
            service.record_barrier(EPISODE, "no transport", "nurse_line")
        assert service._store.list_barriers(EPISODE) == ()


class TestEscalation:
    def test_a_permitted_human_path_is_recorded(
        self, service: EpisodeService, assessed: str
    ) -> None:
        outcome = service.escalate(assessed, "nurse_line")
        assert outcome.human_path == "nurse_line"
        assert (
            service._store.load_snapshot(assessed).escalation_id
            == outcome.escalation_id
        )

    def test_an_unpermitted_human_path_is_refused(
        self, service: EpisodeService, assessed: str
    ) -> None:
        """A handoff to a path the policy cannot display leaves nothing to show."""
        with pytest.raises(rules.UnpermittedRouteId):
            service.escalate(assessed, "dr-smith-mobile")
        assert service._store.load_snapshot(assessed).escalation_id is None

    def test_the_handoff_moves_the_acting_party(
        self, service: EpisodeService, assessed: str
    ) -> None:
        """F6, end to end, through the real store rather than a hand-built snapshot."""
        before = service._store.derive_closure(assessed, fixture.SCENARIO_NOW_UTC)
        assert before.action_owner_id == fixture.NEXT_OWNER_ID
        service.escalate(assessed, "nurse_line")
        after = service._store.derive_closure(assessed, fixture.SCENARIO_NOW_UTC)
        assert after.closure is ClosureState.ESCALATED_TO_HUMAN
        assert after.action_owner_id == "nurse_line", (
            "the patient is still named as the acting party after the handoff, "
            "which is the defect F6 records"
        )


class TestReassessment:
    """Gate 3's named test, second half: missing is not negative (I5).

    With no reviewer, `permitted_change_codes` is empty and every input stops at
    the human path. The assertion that matters is not the outcome string but that
    **no second disposition version exists**, because a version is the only thing
    that can move a deadline.
    """

    def test_no_code_stops_at_the_human_path(
        self, service: EpisodeService, assessed: str
    ) -> None:
        result = service.reassess(assessed, None)
        assert result.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert result.disposition_version is None
        assert result.routes_to_human_path is True
        assert "absence is not a negative finding" in result.reason
        assert len(service._store.list_dispositions(assessed)) == 1

    def test_an_unknown_code_stops_at_the_human_path(
        self, service: EpisodeService, assessed: str
    ) -> None:
        result = service.reassess(assessed, "chest_pain_now")
        assert result.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert "outside policy" in result.reason
        assert len(service._store.list_dispositions(assessed)) == 1

    def test_nothing_this_fixture_accepts_inserts_a_version(
        self, service: EpisodeService, assessed: str
    ) -> None:
        for code in (None, "", "chest_pain_now", "appointment_changed", "worse"):
            result = service.reassess(assessed, code)
            assert result.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        assert len(service._store.list_dispositions(assessed)) == 1, (
            "a second disposition version exists, so a clinical branch was "
            "authored without a reviewer"
        )

    def test_a_reassessment_before_a_plan_is_refused(
        self, service: EpisodeService
    ) -> None:
        service.ensure_episode(EPISODE, "test persona")
        with pytest.raises(NoDispositionYet):
            service.reassess(EPISODE, None)


class TestPlanPrecedesReadBack:
    """K2, promoted from the spike into the real suite at Slice 5.

    The spike asserted the ordering property against a throwaway module. This
    asserts it against the product, with **no coordinator and no reviewer**: the
    plan is issued and renderable before the coordinator is reached at all, so
    read-back can neither gate nor delay it, and a coordinator failure cannot
    move the deadline.

    The fixture carries no urgent symptom content by design (Option C was dropped
    on 1 October 2026, so nothing here is clinical), so the property this fixture
    can actually prove is the ordering one rather than the clinical one.
    """

    def _assessed_with_a_dead_coordinator(self, store) -> EpisodeService:
        service = _build(store, coordinator=DeadCoordinator())
        service.ensure_episode(EPISODE, "test persona")
        service.intake(EPISODE, fixture.BOUND_COMPLAINT)
        return service

    def test_the_plan_is_issued_without_reaching_the_coordinator(self, store) -> None:
        service = self._assessed_with_a_dead_coordinator(store)
        assert service._store.load_snapshot(EPISODE).disposition.version == 1

    def test_intake_never_reaches_the_coordinator(self, store) -> None:
        """K2's ordering half, as an assertion only this test can catch.

        The two tests above run intake against a coordinator that raises, so a
        defect that made the plan wait on the coordinator also broke
        `TestCoordinatorUnavailable`, and `AGENTS.md` section 6 counts a fault two
        checks both catch as proof of neither. This one runs intake against a
        coordinator that **answers**, so the plan is issued either way and no other
        check moves. The only thing that can fail it is the plan having been made
        to depend on read-back machinery at all, which is the harm K2 names: a
        coordinator that is merely slow, or merely reachable, still delays the
        urgent path.
        """
        coordinator = StubCoordinator()
        service = _build(store, coordinator=coordinator)
        service.ensure_episode(EPISODE, "test persona")
        service.intake(EPISODE, fixture.BOUND_COMPLAINT)
        assert coordinator.calls == [], (
            f"intake asked the coordinator {len(coordinator.calls)} time(s) before "
            "issuing the plan, so the urgent path waits on read-back, which is the "
            "ordering defect K2 exists to catch"
        )

    def test_the_plan_is_renderable_before_any_restatement(self, store) -> None:
        service = self._assessed_with_a_dead_coordinator(store)
        snapshot = service._store.load_snapshot(EPISODE)
        lines = rules.patient_lines(
            snapshot,
            rules.derive_closure(snapshot, fixture.SCENARIO_NOW_UTC),
            fixture.policy_text(),
        )
        assert len(lines) == 4
        assert all(line.strip() for line in lines)

    def test_a_coordinator_failure_cannot_move_the_deadline(self, store) -> None:
        """The degraded state stops the flow and changes nothing (architecture 8)."""
        service = self._assessed_with_a_dead_coordinator(store)
        before = service._store.load_snapshot(EPISODE).disposition
        with pytest.raises(CoordinatorUnavailable):
            service.submit_restatement(EPISODE, CORRECT, HintLevel.H0)
        after = service._store.load_snapshot(EPISODE).disposition
        assert after == before
        assert service._store.list_restatements(EPISODE) == ()


# ---------------------------------------------------------------------------
# Slice 6: the action path, the simulated provider, and the platform call
# ---------------------------------------------------------------------------


class CountingCoordinator:
    """The real coordinator, with a counter on the only door to the world.

    The double-tap claim (I3) is "dispatched nothing", and nothing else in the
    record can show it. A suppressed duplicate writes an audit event, but a
    dispatch that never happened and one that happened and was suppressed leave
    the same rows unless something counts the calls. This is that something.
    """

    def __init__(self, inner) -> None:
        self._inner = inner
        self.executions: list[object] = []

    @property
    def origin(self):
        return self._inner.origin

    def execute_tool(self, request, *, now_utc):
        self.executions.append(request)
        return self._inner.execute_tool(request, now_utc=now_utc)


def _action_service(store):
    """An assessed episode with consent granted, and a counting coordinator."""
    coordinator = CountingCoordinator(
        LocalSimulationCoordinator(
            McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())
        )
    )
    service = _build(store, coordinator=coordinator)
    service.ensure_episode(EPISODE, "test persona")
    service.intake(EPISODE, fixture.BOUND_COMPLAINT)
    service.change_consent(EPISODE, granted=True)
    return service, coordinator


#: A permitted route, and a purpose id. The purpose is free text by design: it
#: is part of the idempotency triple, not part of the clinical vocabulary.
ROUTE = "fictional_provider"
PURPOSE = "book_transport"


class TestActionPath:
    """`02-architecture.md` section 3.3 steps 1 to 4, at the service boundary.

    The three rechecks the tool surface performs are pinned in
    `tests/test_coordinator.py`. What is pinned here is the ordering they sit
    inside: authorisation, then consent, then a key the server generated, then
    exactly one dispatch.
    """

    def test_an_action_before_any_consent_is_refused(self, service, assessed):
        with pytest.raises(ConsentRequired):
            service.open_action(EPISODE, ROUTE, PURPOSE)

    def test_an_action_with_consent_is_opened(self, store):
        service, _ = _action_service(store)
        outcome = service.open_action(EPISODE, ROUTE, PURPOSE)
        assert outcome.duplicate is False
        assert outcome.tool is not None
        assert outcome.consent_version == 1
        assert outcome.disposition_version == 1

    def test_a_route_the_policy_does_not_permit_is_refused_first(self, store):
        """D7. A hallucinated route stops before a tool runs or an attempt exists."""
        service, coordinator = _action_service(store)
        with pytest.raises(rules.UnpermittedRouteId):
            service.open_action(EPISODE, "somewhere_else", PURPOSE)
        assert coordinator.executions == []
        assert service._store.list_attempts(EPISODE) == ()

    def test_a_double_tap_reuses_the_key_and_dispatches_once(self, store):
        """I3. The second request returns the first attempt and runs nothing."""
        service, coordinator = _action_service(store)
        first = service.open_action(EPISODE, ROUTE, PURPOSE)
        second = service.open_action(EPISODE, ROUTE, PURPOSE)
        assert second.attempt_id == first.attempt_id
        assert second.idempotency_key == first.idempotency_key
        assert second.duplicate is True
        assert second.tool is None
        assert len(coordinator.executions) == 1

    def test_a_second_purpose_is_a_second_attempt_and_dispatches(self, store):
        """The control for the test above: not every repeat is a duplicate."""
        service, coordinator = _action_service(store)
        first = service.open_action(EPISODE, ROUTE, "purpose-a")
        second = service.open_action(EPISODE, ROUTE, "purpose-b")
        assert second.attempt_id != first.attempt_id
        assert second.duplicate is False
        assert len(coordinator.executions) == 2

    def test_opening_an_action_writes_no_transition(self, store):
        """The outcome arrives on the callback path, or it does not arrive."""
        service, _ = _action_service(store)
        outcome = service.open_action(EPISODE, ROUTE, PURPOSE)
        assert service._store.list_transitions(outcome.attempt_id) == ()

    def test_the_outcome_origin_is_the_one_the_tool_reports(self, store):
        service, _ = _action_service(store)
        outcome = service.open_action(EPISODE, ROUTE, PURPOSE)
        assert outcome.origin is Origin.LOCAL_SIM
        assert outcome.tool.origin is Origin.LOCAL_SIM


class TestCallbackReceipts:
    """O5. A receipt says applied, duplicate or refused, and says why."""

    def _opened(self, store):
        service, _coordinator = _action_service(store)
        outcome = service.open_action(EPISODE, ROUTE, PURPOSE)
        return service, outcome

    @staticmethod
    def _ack() -> CallbackResult:
        return CallbackResult(transition=ExecutionStatus.ACKNOWLEDGED)

    def test_a_callback_applies_and_moves_the_attempt(self, store):
        service, _ = self._opened(store)
        outcome = service.receive_callback(
            EPISODE, ROUTE, "cb-1", self._ack(), Origin.LOCAL_SIM
        )
        assert outcome.receipt.disposition is ReceiptDisposition.APPLIED
        assert outcome.applied is True
        assert outcome.execution is ExecutionStatus.ACKNOWLEDGED

    def test_a_repeat_callback_is_recorded_as_a_duplicate(self, store):
        service, _ = self._opened(store)
        service.receive_callback(EPISODE, ROUTE, "cb-1", self._ack(), Origin.LOCAL_SIM)
        again = service.receive_callback(
            EPISODE, ROUTE, "cb-1", self._ack(), Origin.LOCAL_SIM
        )
        assert again.receipt.disposition is ReceiptDisposition.DUPLICATE
        assert again.applied is False
        assert again.execution is ExecutionStatus.ACKNOWLEDGED

    def test_a_success_after_revocation_is_refused_and_says_why(self, store):
        service, _ = self._opened(store)
        service.change_consent(EPISODE, granted=False)
        outcome = service.receive_callback(
            EPISODE, ROUTE, "cb-1", self._ack(), Origin.LOCAL_SIM
        )
        assert outcome.receipt.disposition is ReceiptDisposition.REFUSED
        assert outcome.receipt.rejection_reason
        assert outcome.execution is not ExecutionStatus.ACKNOWLEDGED

    def test_a_platform_origin_is_refused_because_no_platform_is_wired(self, store):
        service, _ = self._opened(store)
        with pytest.raises(OriginNotWired):
            service.receive_callback(
                EPISODE, ROUTE, "cb-1", self._ack(), Origin.PLATFORM
            )

    def test_the_platform_refusal_also_fires_on_the_bare_string(self, store):
        """The API passes a string through, so the string must be checked too."""
        service, _ = self._opened(store)
        with pytest.raises(OriginNotWired):
            service.receive_callback(EPISODE, ROUTE, "cb-1", self._ack(), "platform")

    def test_the_refused_platform_origin_wrote_nothing(self, store):
        service, opened = self._opened(store)
        with pytest.raises(OriginNotWired):
            service.receive_callback(
                EPISODE, ROUTE, "cb-1", self._ack(), Origin.PLATFORM
            )
        assert service._store.list_transitions(opened.attempt_id) == ()

    def test_the_wired_origin_is_named_and_is_local_sim(self, store):
        service, _ = self._opened(store)
        assert service.available_origin is Origin.LOCAL_SIM

    def test_a_callback_for_a_route_with_no_attempt_is_refused(self, store):
        service, _ = self._opened(store)
        with pytest.raises(NoAttemptForRoute):
            service.receive_callback(
                EPISODE, "nurse_line", "cb-1", self._ack(), Origin.LOCAL_SIM
            )


# ---------------------------------------------------------------------------
# Slice 7: NF4 -- a recorded confirmation must be a verified fact
# ---------------------------------------------------------------------------


class TestTranscriptConfirmedIsVerified:
    """NF4. Before Slice 7 the record carried `id is not None`.

    A text or chip round could name any string at all and the restatement row
    would assert that the patient confirmed a transcript. Only the voice path
    checked the digest and the stored row, so the ledger could be asked to show a
    confirmation that never happened. The ledger is produced at Slice 12 and it
    is read by a judge, so the record had to be settled before it was rendered.
    """

    def test_a_confirmation_that_was_never_recorded_is_not_claimed(
        self, assessed: str, service: EpisodeService
    ) -> None:
        outcome = service.submit_restatement(
            EPISODE,
            CORRECT,
            "H0",
            "tc-not-a-real-confirmation",
            input_mode="text",
        )
        row = service._store.get_restatement(outcome.restatement_id)
        assert row.transcript_confirmed is False

    def test_a_real_confirmation_of_this_text_is_claimed(
        self, assessed: str, service: EpisodeService
    ) -> None:
        """The control: the fix must not make `transcript_confirmed` unreachable."""
        confirmation_id = service.confirm_transcript(EPISODE, CORRECT)
        outcome = service.submit_restatement(
            EPISODE, CORRECT, "H0", confirmation_id, input_mode="text"
        )
        row = service._store.get_restatement(outcome.restatement_id)
        assert row.transcript_confirmed is True

    def test_a_real_confirmation_of_a_different_text_is_not_claimed(
        self, assessed: str, service: EpisodeService
    ) -> None:
        """The swap the digest exists to prevent: confirm one, score another."""
        confirmation_id = service.confirm_transcript(EPISODE, CORRECT)
        outcome = service.submit_restatement(
            EPISODE, WRONG_DAY, "H0", confirmation_id, input_mode="text"
        )
        row = service._store.get_restatement(outcome.restatement_id)
        assert row.transcript_confirmed is False

    def test_no_confirmation_supplied_is_false_not_unknown(
        self, assessed: str, service: EpisodeService
    ) -> None:
        outcome = service.submit_restatement(EPISODE, CORRECT, "H0")
        row = service._store.get_restatement(outcome.restatement_id)
        assert row.transcript_confirmed is False

    def test_the_voice_path_is_unchanged(
        self, assessed: str, service: EpisodeService
    ) -> None:
        """Voice already checked both halves; it must still pass them."""
        confirmation_id = service.confirm_transcript(EPISODE, CORRECT)
        outcome = service.submit_restatement(
            EPISODE, CORRECT, "H0", confirmation_id, input_mode="voice"
        )
        row = service._store.get_restatement(outcome.restatement_id)
        assert row.transcript_confirmed is True
