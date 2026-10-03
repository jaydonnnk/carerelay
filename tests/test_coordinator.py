"""Slice 6: the action path, the simulated provider and the MCP tool surface.

The claims this file exists to hold:

* the provider is deterministic and every response is labelled simulated;
* the three tools recheck authorisation, consent and the attempt key
  **server side**, so a caller that was authorised once is not authorised
  forever;
* a refusal is **recorded** and then raised, so the ledger can say the episode
  stopped rather than leaving a reader to guess;
* the coordinator executes through the tool surface and not around it;
* `origin` is a property of the implementation, so no caller can choose it.

Every guard below is paired with the defect it must catch, and the mutations run
against this file are recorded in `00-status.md`.
"""

from __future__ import annotations

import sys
from dataclasses import fields
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.coordinator import (  # noqa: E402
    AllowedPlanValues,
    LocalSimulationCoordinator,
    ToolRequest,
)
from carerelay.demo import fixture  # noqa: E402
from carerelay.domain.models import (  # noqa: E402
    TERMINAL_TRANSITIONS,
    AttemptCommand,
    Disposition,
    DispositionSource,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    Origin,
)
from carerelay.simulated_provider import (  # noqa: E402
    PROVIDER_REF,
    ScriptedProvider,
)
from carerelay.state import (  # noqa: E402
    CLINICAL_SCOPE,
    ConsentNotCurrent,
    derive_attempt_key,
    open_store,
)
from carerelay.tools import (  # noqa: E402
    McpTools,
    RouteNotPermitted,
    UnknownAttemptKey,
)

EPISODE_ID = "episode-actions"
NOW_UTC = datetime(2026, 10, 1, 4, 0, tzinfo=timezone.utc)
DEADLINE_UTC = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)

#: A permitted route, and one the fixture's policy does not contain.
PERMITTED_ROUTE = "fictional_provider"
ROUTE_NOT_IN_POLICY = "a_route_no_policy_permits"
PURPOSE_ID = "booking"


@pytest.fixture()
def store():
    handle = open_store(":memory:")
    yield handle
    handle.close()


def _seed(store) -> None:
    """One episode with a disposition and granted consent, as the demo has."""
    store.create_episode(EPISODE_ID, "fictional older adult", now_utc=NOW_UTC)
    store.register_policy_version(
        fixture.POLICY_VERSION,
        content="{}",
        provenance="provisional non-clinical placeholder, authored rather than sourced",
        approved_by=None,
        now_utc=NOW_UTC,
    )
    store.insert_disposition(
        Disposition(
            episode_id=EPISODE_ID,
            version=1,
            policy_version=fixture.POLICY_VERSION,
            action_id="attend_same_day_review",
            clinical_deadline_utc=DEADLINE_UTC,
            next_owner_id="patient",
            fallback_route_id="nurse_line",
            source=DispositionSource.FIXTURE,
        ),
        now_utc=NOW_UTC,
    )
    store.change_consent(EPISODE_ID, CLINICAL_SCOPE, granted=True, now_utc=NOW_UTC)


def _tools(store, provider=None) -> McpTools:
    return McpTools(
        store, policy=fixture.policy(), provider=provider or ScriptedProvider()
    )


def _key(route: str, purpose: str) -> str:
    return derive_attempt_key(EPISODE_ID, route, purpose)


def _open(store, route: str = PERMITTED_ROUTE, purpose: str = PURPOSE_ID):
    key = _key(route, purpose)
    attempt = store.open_attempt_once(
        AttemptCommand(EPISODE_ID, route, purpose, 1), key, now_utc=NOW_UTC
    )
    return attempt, key


def _events(store, kind: str) -> tuple[str, ...]:
    return tuple(
        payload for name, payload, _ in store.list_events(EPISODE_ID) if name == kind
    )


# ---------------------------------------------------------------------------
# The provider
# ---------------------------------------------------------------------------


class TestTheProviderIsDeterministicAndLabelled:
    def test_every_response_carries_the_simulated_label(self) -> None:
        response = ScriptedProvider().submit_request(PERMITTED_ROUTE, "att-1")
        assert response.simulated is True

    def test_the_same_inputs_give_the_same_response(self) -> None:
        provider = ScriptedProvider()
        assert provider.submit_request(
            PERMITTED_ROUTE, "att-1"
        ) == provider.submit_request(PERMITTED_ROUTE, "att-1")

    def test_the_scripted_outcome_is_a_terminal_failure(self) -> None:
        """Section 5.1 step 6: the adapter fails as scripted.

        A provider that acknowledged would close the episode and leave the
        Closure Contract nothing to show, so this is the script, not a fallback.
        """
        response = ScriptedProvider().submit_request(PERMITTED_ROUTE, "att-1")
        assert response.outcome is ExecutionStatus.FAILED
        assert response.outcome in TERMINAL_TRANSITIONS

    def test_the_provider_reports_local_sim_and_never_platform(self) -> None:
        """The load-bearing honesty claim of this slice.

        Gate A proved ADP's transport carries an origin signal. It did not prove
        tool execution, and D8 says ADP cannot carry the section 3.3 claim. A
        provider that reported `platform` here would be stating a fact no
        observation supports.
        """
        assert ScriptedProvider().origin is Origin.LOCAL_SIM

    def test_a_non_terminal_script_is_refused_at_construction(self) -> None:
        with pytest.raises(ValueError):
            ScriptedProvider({PERMITTED_ROUTE: ExecutionStatus.ATTEMPTED})

    def test_a_script_may_name_an_acknowledgement_without_hiding_the_label(self) -> None:
        provider = ScriptedProvider({PERMITTED_ROUTE: ExecutionStatus.ACKNOWLEDGED})
        response = provider.submit_request(PERMITTED_ROUTE, "att-1")
        assert response.outcome is ExecutionStatus.ACKNOWLEDGED
        assert response.simulated is True
        assert response.provider_ref == PROVIDER_REF


# ---------------------------------------------------------------------------
# The tool surface
# ---------------------------------------------------------------------------


class TestToolRechecksAuthorisationConsentAndKey:
    def test_a_route_outside_the_policy_is_refused_and_recorded(self, store) -> None:
        _seed(store)
        _open(store)
        with pytest.raises(RouteNotPermitted):
            _tools(store).submit_simulated_request(
                EPISODE_ID,
                ROUTE_NOT_IN_POLICY,
                _key(ROUTE_NOT_IN_POLICY, PURPOSE_ID),
                now_utc=NOW_UTC,
            )
        # The refusal is in the record, not only in the exception. A refusal that
        # is only raised leaves the ledger unable to say the episode stopped.
        assert _events(store, "refused")

    def test_a_key_that_opened_no_attempt_is_refused_and_recorded(self, store) -> None:
        _seed(store)
        with pytest.raises(UnknownAttemptKey):
            _tools(store).submit_simulated_request(
                EPISODE_ID, PERMITTED_ROUTE, "att-never-opened", now_utc=NOW_UTC
            )
        assert _events(store, "refused")

    def test_a_key_belonging_to_another_route_is_refused(self, store) -> None:
        """A caller may not open one attempt and spend it on a different route."""
        _seed(store)
        _open(store, route=PERMITTED_ROUTE)
        other = "nurse_line"
        _open(store, route=other, purpose="other")
        with pytest.raises(UnknownAttemptKey):
            _tools(store).submit_simulated_request(
                EPISODE_ID, PERMITTED_ROUTE, _key(other, "other"), now_utc=NOW_UTC
            )

    def test_revoked_consent_stops_the_dispatch(self, store) -> None:
        _seed(store)
        _attempt, key = _open(store)
        store.change_consent(EPISODE_ID, CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC)
        with pytest.raises(ConsentNotCurrent):
            _tools(store).submit_simulated_request(
                EPISODE_ID, PERMITTED_ROUTE, key, now_utc=NOW_UTC
            )
        assert _events(store, "refused")

    def test_a_permitted_route_with_a_current_key_dispatches(self, store) -> None:
        """The control. Without it every refusal above could pass by refusing all."""
        _seed(store)
        _attempt, key = _open(store)
        result = _tools(store).submit_simulated_request(
            EPISODE_ID, PERMITTED_ROUTE, key, now_utc=NOW_UTC
        )
        assert result.outcome is ExecutionStatus.FAILED
        assert result.origin is Origin.LOCAL_SIM
        assert result.simulated is True
        assert result.attempt_key == key

    def test_get_episode_omits_the_patient_surface(self, store) -> None:
        """An executor gets the route and the key, not the patient's words."""
        _seed(store)
        brief = _tools(store).get_episode(EPISODE_ID, now_utc=NOW_UTC)
        assert brief.episode_id == EPISODE_ID
        assert brief.consent_version == 1
        assert PERMITTED_ROUTE in brief.permitted_route_ids
        assert ROUTE_NOT_IN_POLICY not in brief.permitted_route_ids
        assert brief.simulated is True

    def test_get_episode_is_refused_without_current_consent(self, store) -> None:
        _seed(store)
        store.change_consent(EPISODE_ID, CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC)
        with pytest.raises(ConsentNotCurrent):
            _tools(store).get_episode(EPISODE_ID, now_utc=NOW_UTC)

    def test_record_evidence_rechecks_consent(self, store) -> None:
        _seed(store)
        store.change_consent(EPISODE_ID, CLINICAL_SCOPE, granted=False, now_utc=NOW_UTC)
        with pytest.raises(ConsentNotCurrent):
            _tools(store).record_evidence(
                EPISODE_ID,
                EvidenceRecord(
                    level=EvidenceLevel.SELF_REPORTED,
                    simulated=True,
                    provenance="scripted",
                    source_ref=None,
                ),
                now_utc=NOW_UTC,
            )

    def test_record_evidence_accepts_a_simulated_self_report(self, store) -> None:
        """The control for the refusal above."""
        _seed(store)
        level = _tools(store).record_evidence(
            EPISODE_ID,
            EvidenceRecord(
                level=EvidenceLevel.SELF_REPORTED,
                simulated=True,
                provenance="scripted local provider",
                source_ref=None,
            ),
            now_utc=NOW_UTC,
        )
        assert level is EvidenceLevel.SELF_REPORTED
        assert len(store.list_evidence(EPISODE_ID)) == 1


# ---------------------------------------------------------------------------
# The coordinator executes through the tool surface
# ---------------------------------------------------------------------------


class TestTheCoordinatorExecutesThroughTheToolSurface:
    def test_the_coordinator_reports_the_origin_of_its_tools(self, store) -> None:
        _seed(store)
        assert LocalSimulationCoordinator(_tools(store)).origin is Origin.LOCAL_SIM

    def test_execution_goes_through_the_rechecks(self, store) -> None:
        """A route outside the policy is refused even when the coordinator asks.

        The coordinator is not privileged. If it could reach the provider
        directly it would bypass the only authorisation the product has.
        """
        _seed(store)
        _open(store)
        coordinator = LocalSimulationCoordinator(_tools(store))
        with pytest.raises(RouteNotPermitted):
            coordinator.execute_tool(
                ToolRequest(
                    episode_id=EPISODE_ID,
                    route_id=ROUTE_NOT_IN_POLICY,
                    attempt_key=_key(ROUTE_NOT_IN_POLICY, PURPOSE_ID),
                ),
                now_utc=NOW_UTC,
            )

    def test_execution_returns_the_provider_outcome_and_its_origin(self, store) -> None:
        """The control, and the path the demo walks."""
        _seed(store)
        _attempt, key = _open(store)
        result = LocalSimulationCoordinator(_tools(store)).execute_tool(
            ToolRequest(
                episode_id=EPISODE_ID,
                route_id=PERMITTED_ROUTE,
                attempt_key=key,
                disposition_version=1,
            ),
            now_utc=NOW_UTC,
        )
        assert result.outcome is ExecutionStatus.FAILED
        assert result.origin is Origin.LOCAL_SIM
        assert result.simulated is True

    def test_a_coordinator_without_a_tool_surface_cannot_be_built(self, store) -> None:
        """Failing at wiring time, not at call time.

        An execution boundary with no tool surface is a misconfiguration. If it
        were optional, a wiring mistake would surface later as a refusal that
        looks like a policy decision.
        """
        with pytest.raises(TypeError):
            LocalSimulationCoordinator()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Extraction, and the honest statement of what it hides (NF5)
# ---------------------------------------------------------------------------


class TestTheExtractionBoundarySaysWhatItHides:
    def test_the_expected_values_are_present_so_the_old_claim_was_false(
        self,
    ) -> None:
        """NF5, corrected 3 October 2026.

        Earlier drafts claimed the coordinator "cannot see the expected values".
        It can: the canonical action and owner ids are members of the
        surface-form sets. This test pins the honest half of the claim by first
        pinning that the flattering half is false.
        """
        policy = fixture.policy()
        allowed = AllowedPlanValues(
            action_forms=frozenset(policy.action_aliases)
            | policy.permitted_action_ids,
            owner_forms=frozenset(policy.owner_aliases) | policy.permitted_owner_ids,
            deadline_forms=frozenset(policy.deadline_forms),
        )
        assert set(policy.permitted_action_ids) <= set(allowed.action_forms)
        assert set(policy.permitted_owner_ids) <= set(allowed.owner_forms)

    def test_the_boundary_carries_no_pairing_and_no_disposition(self) -> None:
        """What is genuinely hidden, and the load-bearing half of ADR-0007.

        Three unordered sets and nothing else. There is no field that links a
        surface form to the disposition's value for that field, and there is no
        disposition, so a coordinator handed this can recognise words but cannot
        determine which candidate is expected and cannot look the answer up.
        """
        allowed = AllowedPlanValues(
            action_forms=frozenset({"a"}),
            owner_forms=frozenset({"o"}),
            deadline_forms=frozenset({"d"}),
        )
        assert {field.name for field in fields(allowed)} == {
            "action_forms",
            "owner_forms",
            "deadline_forms",
        }

    def test_extraction_still_resolves_the_fixture_plan(self, store) -> None:
        """The control: the boundary is honest and it still works."""
        _seed(store)
        coordinator = LocalSimulationCoordinator(_tools(store))
        policy = fixture.policy()
        allowed = AllowedPlanValues(
            action_forms=frozenset(policy.action_aliases)
            | policy.permitted_action_ids,
            owner_forms=frozenset(policy.owner_aliases) | policy.permitted_owner_ids,
            deadline_forms=frozenset(policy.deadline_forms),
        )
        extracted = coordinator.extract_plan(
            "see the doctor today before 6pm myself", allowed
        )
        assert extracted.action_span is not None
        assert extracted.deadline_span is not None
        assert extracted.next_owner_span is not None


def test_the_deadline_is_untouched_by_a_failed_dispatch(store) -> None:
    """I1. A failed booking is not new clinical information."""
    _seed(store)
    before = store.load_snapshot(EPISODE_ID).disposition
    _attempt, key = _open(store)
    LocalSimulationCoordinator(_tools(store)).execute_tool(
        ToolRequest(
            episode_id=EPISODE_ID, route_id=PERMITTED_ROUTE, attempt_key=key
        ),
        now_utc=NOW_UTC,
    )
    after = store.load_snapshot(EPISODE_ID).disposition
    assert before == after
    assert after.clinical_deadline_utc == DEADLINE_UTC
    assert after.clinical_deadline_utc - NOW_UTC == timedelta(hours=6)
