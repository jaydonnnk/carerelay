"""Application use cases for PlanBack. Slice 4.

`03-program-design.md` section 2 gives this file its responsibility: intake,
restatement, action, callback, consent, expiry, reassessment and resume, and
makes it "the only layer allowed to coordinate domain, store, coordinator and
clock". Slice 4 implements the PlanBack half of that list: intake, transcript
confirmation, hint events, the restatement round, and the bounded repair.

Nothing here is a clinical decision. Every clinical decision is in `domain`, and
this file is what makes that claim testable: it is the only layer that may call
the coordinator, and it hands the coordinator's output to `domain` without ever
resolving it itself.

**Four decisions this layer owns, and why they are here:**

1. **Whether a restatement may be scored at all.** `domain.may_score_restatement`
   decides. This layer supplies the confirmation and refuses on its behalf, and
   it checks that the confirmation binds to **the very text being scored**, so a
   corrected transcript cannot be swapped for a draft at evaluation time.
2. **Which field is repaired next, and whether a further round exists.**
   `domain.next_repair` decides; this layer carries the round count, which is
   state, not policy.
3. **What the recorded outcome was.** The hint level alone does not settle it. A
   mismatched round achieved no recall, so it records `not_recalled` even at H0;
   and H3 records `not_recalled` even when its comparison is clean, which is the
   rule that revealing the plan is never a comprehension pass (C6).
4. **What happens when the coordinator cannot answer.** The flow stops and
   nothing is written, so no later surface may present the round as scored
   (`02-architecture.md` section 8, degraded states).

**A divergence from the Gate 3 sketch, stated rather than silent.** Gate 3
declares `submit_restatement(...) -> PlanComparison`. Gate 2 section 3.1 gives
the route a `/repairs` child keyed on the restatement id and requires the response
to say whether the patient routes to the human path, so the method returns a
`RestatementOutcome` that carries the `PlanComparison` rather than returning it
bare. The comparison is unchanged; only the envelope grew.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from datetime import tzinfo
from typing import Protocol

from carerelay.coordinator import (
    AllowedPlanValues,
    CoordinatorPort,
    ToolRequest,
)
from carerelay.domain import rules
from carerelay.domain.models import (
    MAX_REPAIR_ROUNDS,
    RECALL_OUTCOME_BY_LEVEL,
    AttemptCommand,
    CallbackResult,
    ClosureProjection,
    ClosureState,
    Disposition,
    ExecutionStatus,
    HintEvent,
    HintEventKind,
    HintLevel,
    HintState,
    InputMode,
    Origin,
    PlanComparison,
    PolicyFixture,
    PolicyText,
    ReassessmentOutcome,
    RecallOutcome,
)
from carerelay.presentation import PatientSurface, patient_surface
from carerelay.state import (
    CLINICAL_SCOPE,
    DEFAULT_KEY_NAMESPACE,
    EpisodeNotFound,
    EpisodeStore,
    RestatementNotFound,
    derive_attempt_key,
)
from carerelay.tools import ToolResult

# Aliased on purpose: `_require_scorable` takes a parameter named
# `transcript_confirmation_id`, which would otherwise shadow the function and
# turn a digest comparison into a call on the parameter itself.
from carerelay.state import (  # noqa: E402
    ReceiptOutcome,
    transcript_confirmation_id as derive_confirmation_id,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ServiceError(Exception):
    """Base class for a use case that refuses to proceed."""


class NoDispositionYet(ServiceError):
    """A restatement before any plan exists. There is nothing to compare against."""


class UnconfirmedTranscript(ServiceError):
    """A voice restatement arrived before its transcript was confirmed.

    The request-layer half of Gate 1's ordering rule. `state.UnconfirmedTranscript`
    is the record-level half; both exist so a defect in either place cannot
    produce a scored round that was evaluated on a draft.
    """


class RepairCapReached(ServiceError):
    """A third repair round was requested. It is never offered (C6)."""


class StaleRestatement(ServiceError):
    """A repair against a restatement that is no longer the latest round.

    Every round is its own row, so repairing an older round would fork the
    ladder: the caller could re-repair round zero forever and the two-repair cap
    would never bite. The repair must be against the most recent round, which is
    the one the previous response named.
    """


class EpisodeAlreadyAssessed(ServiceError):
    """A second intake for an episode that already carries a disposition."""


class IntakeNotRecognised(ServiceError):
    """A complaint this fixture is not bound to. Stops at the human path (D7)."""


class ConsentRequired(ServiceError):
    """An action before any consent was recorded.

    `state.ConsentNotCurrent` covers a consent that exists and has moved. This
    covers the case before it: there is no version to stamp on the attempt at
    all. Distinguishing them matters because the second is "ask", and the first
    is "ask earlier".
    """


class NoAttemptForRoute(ServiceError):
    """A callback for a route this episode never opened an attempt on.

    A callback is a reply to something. Replying to an attempt that does not
    exist would append a transition to nothing, and the ledger would show an
    outcome with no request behind it.
    """


class OriginNotWired(ServiceError):
    """A caller asserted an origin this deployment cannot produce.

    `02-architecture.md` section 3.3 step 6 makes the origin marker the thing
    that keeps the platform claim checkable. A marker the caller can set to any
    value is not checkable: it is a field that says whatever the caller wants.
    This refusal is what stops `origin = platform` being written by a path that
    never reached a platform, which in this build is every path.

    The honest consequence is stated rather than hidden: until a platform really
    executes a tool, `platform` is never a legal value here, and the record says
    so instead of leaving the field empty and unexplained.
    """


# ---------------------------------------------------------------------------
# The clock
# ---------------------------------------------------------------------------


class Clock(Protocol):
    """The only source of time. Injected, so no layer below reads a clock (D5)."""

    def now_utc(self) -> datetime: ...


class SystemClock:
    """The wall clock."""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class ScenarioClock:
    """A fixed instant, so a walkthrough and a test see the same "today".

    The demo default: the fixture's deadline display is "6pm today" and its
    deadline is computed relative to the injected clock, so a wall clock would
    make the displayed deadline drift as the real day changed.
    """

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now_utc(self) -> datetime:
        return self._instant


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RestatementOutcome:
    """What one restatement round produced, for the API to serialise.

    `simulated` travels on the result because the coordinator that produced it
    did: an unlabelled simulated extraction is the same defect D11 forbids for a
    simulated receipt.
    """

    restatement_id: str
    comparison: PlanComparison
    hint_level: HintLevel
    repair_round: int
    outcome: RecallOutcome
    next_repair_field: str | None
    routes_to_human_path: bool
    human_path_route_id: str | None
    simulated: bool

    @property
    def understood(self) -> bool:
        """True only when every critical field resolved **and** agreed.

        Deliberately stricter than "no mismatch": an extractor that answers
        uncertain to everything has zero false mismatches and is useless, because
        read-back would repair nothing and the patient would reach the human path
        every time. K1 must not be passable by refusing to commit.
        """
        return not self.comparison.mismatched and not self.comparison.uncertain


@dataclass(frozen=True)
class BarrierOutcome:
    """What one barrier report produced, for the API to serialise.

    `proposed_route_id` and `permitted_route_id` are both carried because the
    ledger has to be able to show *why* an episode stopped. A proposal outside
    the policy is refused and the refusal is recorded; it is never dropped and
    never silently rewritten to a permitted value.
    """

    barrier_id: str
    episode_id: str
    disposition_version: int
    proposed_route_id: str | None
    permitted_route_id: str | None
    stopped_at_human_path: bool
    human_path_route_id: str | None
    simulated: bool


@dataclass(frozen=True)
class EscalationOutcome:
    """The recorded handoff to a named human path.

    `human_path` is a permitted route id, so the ledger names a service this
    policy can display rather than arbitrary free text.
    """

    escalation_id: str
    episode_id: str
    human_path: str
    outcome: str
    simulated: bool


@dataclass(frozen=True)
class AcceptanceOutcome:
    """The recorded human acceptance, and the closure it produced.

    **Why this carries the id as well as the closure.** Gate 3 pins
    `record_human_acceptance(...) -> ClosureProjection`, and the closure is what
    the caller needs to see the state change. The id is here for the same reason
    `EscalationOutcome` carries `escalation_id`: a response that cannot name the
    record it just wrote cannot be used to check the ledger later. The deviation
    from the pinned signature is stated rather than silent, and it matches the
    precedent `escalate` already set.

    `closure` is derived after the write, so it is the state the acceptance
    produced, not a prediction of it.
    """

    acceptance_id: str
    episode_id: str
    accepted_by: str
    scope: str
    closure: ClosureProjection
    simulated: bool


@dataclass(frozen=True)
class ActionOutcome:
    """One opened attempt, and what the coordinator's tool call returned.

    `tool` is `None` exactly when the attempt was a duplicate: a second request
    on the same `(episode, route, purpose)` reuses the key, must not dispatch
    again (I3), and therefore has nothing new to report. Returning the original
    attempt with no tool result is what makes the double tap a recorded no-op
    rather than a second dispatch.

    `origin` is carried on the outcome, not only on the tool result, so a caller
    that never looks at the tool result still cannot miss where the outcome came
    from.
    """

    episode_id: str
    attempt_id: str
    idempotency_key: str
    route_id: str
    purpose_id: str
    disposition_version: int
    consent_version: int
    execution: ExecutionStatus
    duplicate: bool
    tool: ToolResult | None
    origin: Origin
    simulated: bool


@dataclass(frozen=True)
class CallbackOutcome:
    """What one callback did to the episode.

    `receipt` is the state-layer outcome: applied, duplicate, or refused, and if
    refused, why. Carrying the reason rather than a bool is O5, and it is here
    because the action path is the first consumer that needs to tell "we ignored
    a repeat" from "we refused a success".
    """

    episode_id: str
    route_id: str
    attempt_id: str
    origin: Origin
    receipt: "ReceiptOutcome"
    execution: ExecutionStatus
    simulated: bool

    @property
    def applied(self) -> bool:
        return self.receipt.applied


@dataclass(frozen=True)
class ReassessmentResult:
    """What one reassessment produced.

    `disposition_version` is set only when a reviewer-authorised branch inserted
    a new version. With no reviewer, every input lands on `STOP_AT_HUMAN_PATH`,
    which is the honest state of the judged fixture and is why this slice adds no
    clinical wording.
    """

    episode_id: str
    outcome: ReassessmentOutcome
    reason: str
    disposition_version: int | None
    routes_to_human_path: bool
    human_path_route_id: str | None
    simulated: bool


# ---------------------------------------------------------------------------
# The service
# ---------------------------------------------------------------------------


class EpisodeService:
    """The PlanBack use cases, and the intake that gives them a plan.

    The fixture-shaped values are constructor arguments rather than imports, so
    a test can swap the policy and the disposition without monkeypatching, and so
    Slice 5 can replace the provisional fixture with the sourced one without
    touching this file.
    """

    def __init__(
        self,
        store: EpisodeStore,
        *,
        coordinator: CoordinatorPort,
        clock: Clock,
        policy: PolicyFixture,
        policy_text: PolicyText,
        display_tz: tzinfo,
        disposition_factory: Callable[[str, datetime], Disposition],
        bound_complaint: str,
        policy_provenance: str,
        key_namespace: str = DEFAULT_KEY_NAMESPACE,
    ) -> None:
        self._store = store
        self._coordinator = coordinator
        self._clock = clock
        self._policy = policy
        # Slice 10. The wording half of the same policy. `domain.patient_lines`
        # renders from this value and from nothing else, so the service can
        # project a patient surface without any layer above it composing words.
        self._policy_text = policy_text
        self._display_tz = display_tz
        self._disposition_factory = disposition_factory
        self._bound_complaint = bound_complaint
        self._policy_provenance = policy_provenance
        # D5's server-held secret, folded in at Slice 6 as the Slice 3 review
        # recorded. The key derivation stays in `state`; only the namespace
        # travels, so the signature that makes a double tap provable is unchanged.
        self._key_namespace = key_namespace
        # Read with `getattr`, as `simulated` is below: a test stub implements
        # the port structurally and may omit it, and the safe default is the
        # honest one. A stub that cannot name an origin may not claim `platform`.
        self._origin: Origin = getattr(coordinator, "origin", Origin.LOCAL_SIM)

    @property
    def available_origin(self) -> Origin:
        """The only origin this deployment may record.

        Public because the ledger and the API both have to be able to say which
        origin the wired path can produce, so a refusal can name the alternative
        rather than just refusing.
        """
        return self._origin

    # -- episode ----------------------------------------------------------

    def ensure_episode(self, episode_id: str, persona: str) -> None:
        """Create the episode row if it is absent. Idempotent on purpose.

        `POST /api/episodes` returns one demo episode, and the tracer bullet
        calls it once per session. Making the second call raise would break the
        Slice 1 route contract for no gain. **This writes no disposition**
        (`02-architecture.md` 3.1): assessment does, and only assessment.
        """
        try:
            self._store.load_snapshot(episode_id)
        except EpisodeNotFound:
            self._store.create_episode(
                episode_id, persona, now_utc=self._clock.now_utc()
            )

    def intake(self, episode_id: str, confirmed_text: str) -> Disposition:
        """Assess the fixture-bound complaint and issue the preauthored plan.

        The minimal stand-in for the assessment path, which is scheduled in no
        slice. It is deliberately narrow: the complaint must **be** the one
        phrase this fixture is bound to, and anything else stops at the human
        path (D7). It never composes clinical wording and never derives a
        deadline from free text; the disposition is the fixture's preauthored one.

        **The binding is an exact normalised match, not a substring.** It was a
        substring match until 2 October 2026, when the Slice 4 adversarial review
        raised it as finding B3 and measured the consequence: a text carrying a
        red-flag symptom alongside the bound phrase, such as "help sorting out my
        appointment, also I have chest pain and cannot breathe", contained the
        phrase and therefore **scored 200 and issued the demo plan** instead of
        stopping. An exact match is the rule the documents already claimed and the
        stricter of the two, so it needs no reviewer: making the system refuse
        more inputs is never a clinical claim.

        It also records the policy version first, because the disposition cites
        it and the schema enforces that with a foreign key: a plan that names a
        policy the system never recorded would be unauditable.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is not None:
            raise EpisodeAlreadyAssessed(
                f"episode {episode_id!r} already carries disposition version "
                f"{snapshot.disposition.version}; assessment happens once"
            )
        if rules.normalise(confirmed_text) != self._bound_complaint:
            raise IntakeNotRecognised(
                "the complaint is not the one this fixture is bound to, so no "
                "disposition may be issued: stop at the human path (D7)"
            )

        now_utc = self._clock.now_utc()
        self._store.register_policy_version(
            self._policy.version,
            content=f"provisional fixture policy {self._policy.version}",
            provenance=self._policy_provenance,
            approved_by=None,
            now_utc=now_utc,
        )
        disposition = self._disposition_factory(episode_id, now_utc)
        self._store.insert_disposition(disposition, now_utc=now_utc)
        return disposition

    # -- transcript -------------------------------------------------------

    def confirm_transcript(self, episode_id: str, corrected_text: str) -> str:
        """Record a confirmed or corrected transcript. Returns the confirmation id.

        Gate 1's ordering rule: this happens **before** any evaluation. The id is
        a digest of the text, so a later restatement can be required to be the
        very string that was confirmed.
        """
        self._store.load_snapshot(episode_id)
        return self._store.record_transcript_confirmation(
            episode_id, text=corrected_text, now_utc=self._clock.now_utc()
        )

    # -- hints ------------------------------------------------------------

    def record_hint_event(
        self,
        episode_id: str,
        hint_level: HintLevel | str,
        kind: HintEventKind | str,
        dwell_seconds: float | None = None,
    ) -> HintState:
        """Record one hint event and return the resulting card state.

        The returned state is derived, not stored (D4's sibling rule): the card
        is visible exactly when the recorded event vocabulary says it is, and
        only `patient_hid` can hide it. `dwell_seconds` is recorded for the
        ledger         and is not an input to the derivation (C8).

        The two strings are parsed by `domain` rather than by their enum
        constructors. Until Slice 7 they were constructed directly, so `H9` or
        `auto_hide` raised an uncaught `ValueError` and the route answered 500
        (finding NF2). `PolicyViolation` is the refusal the hint route already
        maps to 422, which is also what makes that branch reachable at last (NF3).
        """
        level = rules.require_hint_level(hint_level)
        event_kind = rules.require_hint_event_kind(kind)
        self._store.load_snapshot(episode_id)
        self._store.record_hint_event(
            episode_id,
            hint_level=level,
            kind=event_kind,
            dwell_seconds=dwell_seconds,
            now_utc=self._clock.now_utc(),
        )
        return self.hint_state(episode_id)

    def hint_state(self, episode_id: str) -> HintState:
        """The current card state, folded from every recorded hint event."""
        self._store.load_snapshot(episode_id)
        state = HintState(level=HintLevel.H0, card_visible=False)
        for record in self._store.list_hint_events(episode_id):
            event = HintEvent(
                level=record.level,
                kind=record.kind,
                dwell_seconds=record.dwell_seconds,
            )
            if event.level is not state.level:
                # A new rung of the ladder starts hidden; only a `shown` event
                # reveals it, and only `patient_hid` removes it.
                state = HintState(level=event.level, card_visible=False)
            state = rules.hint_transition(state, event)
        return state

    # -- restatements -----------------------------------------------------

    def submit_restatement(
        self,
        episode_id: str,
        confirmed_text: str,
        hint_level: HintLevel | str,
        transcript_confirmation_id: str | None = None,
        *,
        input_mode: InputMode | str = InputMode.TEXT,
        dwell_seconds: float | None = None,
    ) -> RestatementOutcome:
        """Score one restatement. Round zero of the ladder.

        Raises `CoordinatorUnavailable` when the coordinator cannot answer, in
        which case nothing is recorded and no outcome exists.
        """
        return self._score(
            episode_id,
            confirmed_text,
            hint_level,
            transcript_confirmation_id,
            input_mode=input_mode,
            dwell_seconds=dwell_seconds,
            repair_round=0,
        )

    def repair_restatement(
        self,
        restatement_id: str,
        confirmed_text: str,
        hint_level: HintLevel | str,
        transcript_confirmation_id: str | None = None,
        *,
        input_mode: InputMode | str = InputMode.TEXT,
        dwell_seconds: float | None = None,
        episode_id: str | None = None,
    ) -> RestatementOutcome:
        """Score one repair round against a recorded restatement.

        The cap is enforced before anything is extracted: a third round is never
        offered (C6), so this refuses rather than scoring a round the product
        says does not exist. A caller that received `routes_to_human_path` has
        already been told where to go.

        `episode_id` is checked against the parent when supplied, so a repair
        cannot be applied to a restatement belonging to another episode. The
        check is here rather than in the route because the route has no business
        reading the record.

        The parent must be the **latest** round. Repairing an older one would
        fork the ladder and let the cap be evaded by re-repairing round zero.
        """
        parent = self._store.get_restatement(restatement_id)
        if episode_id is not None and parent.episode_id != episode_id:
            raise RestatementNotFound(restatement_id)
        rounds = self._store.list_restatements(parent.episode_id)
        latest_id = rounds[-1].restatement_id if rounds else None
        if latest_id != restatement_id:
            raise StaleRestatement(
                f"restatement {restatement_id!r} is not the latest round (the "
                f"latest is {latest_id!r}); repair the round the previous "
                "response named"
            )
        repair_round = parent.repair_round + 1
        if repair_round > MAX_REPAIR_ROUNDS:
            raise RepairCapReached(
                f"restatement {restatement_id!r} is already at repair round "
                f"{parent.repair_round}; two repairs is the maximum and a third "
                "is never offered (C6). Route to the human path."
            )
        return self._score(
            parent.episode_id,
            confirmed_text,
            hint_level,
            transcript_confirmation_id,
            input_mode=input_mode,
            dwell_seconds=dwell_seconds,
            repair_round=repair_round,
        )

    # -- barriers, escalation and reassessment (Slice 5) ------------------

    def record_barrier(
        self,
        episode_id: str,
        barrier_text: str,
        proposed_route_id: str | None = None,
    ) -> BarrierOutcome:
        """Record a practical barrier, and judge any proposed route.

        `domain.validate_route` is the only thing that decides whether a route id
        is permitted, and it is reached through this layer rather than in the
        route function (D2). **A proposal outside the policy is recorded as a
        stop and then refused**: the record keeps the evidence that the episode
        reached the human path, and the caller still gets the refusal. Dropping
        the refusal would lose the one fact the ledger exists to show.

        No route is proposed by the system here. The coordinator proposal the
        architecture names arrives with the coordinator wiring in Slice 6; until
        then a caller may supply one and `domain` judges it.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is no plan "
                "for a barrier to be reported against"
            )
        now_utc = self._clock.now_utc()
        permitted_route_id: str | None = None
        if proposed_route_id is not None:
            try:
                permitted_route_id = rules.validate_route(
                    proposed_route_id, self._policy.permitted_route_ids
                )
            except rules.PolicyViolation:
                self._store.record_barrier(
                    episode_id,
                    disposition_version=snapshot.disposition.version,
                    barrier_text=barrier_text,
                    proposed_route_id=proposed_route_id,
                    permitted_route_id=None,
                    stopped_at_human_path=True,
                    now_utc=now_utc,
                )
                raise
        barrier_id = self._store.record_barrier(
            episode_id,
            disposition_version=snapshot.disposition.version,
            barrier_text=barrier_text,
            proposed_route_id=proposed_route_id,
            permitted_route_id=permitted_route_id,
            stopped_at_human_path=False,
            now_utc=now_utc,
        )
        return BarrierOutcome(
            barrier_id=barrier_id,
            episode_id=episode_id,
            disposition_version=snapshot.disposition.version,
            proposed_route_id=proposed_route_id,
            permitted_route_id=permitted_route_id,
            stopped_at_human_path=False,
            # The route to use when this plan cannot be carried out. It is the
            # disposition's own fallback, so a barrier never invents a route.
            human_path_route_id=snapshot.disposition.fallback_route_id,
            simulated=True,
        )

    def escalate(
        self,
        episode_id: str,
        human_path: str,
        outcome: str = "handed_off",
    ) -> EscalationOutcome:
        """Record the handoff to a named human path.

        The path is validated against the policy's permitted routes, so the
        ledger names a service this product can display rather than free text.

        Escalating twice is allowed, and both records stand. The later one is the
        current handoff (`load_snapshot` takes the latest) and the earlier one
        stays in the record, which is what an append-only history is for. F6
        reads this record: from the moment it exists, the acting party is the
        human path, not the patient.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is no plan "
                "to hand off"
            )
        validated = rules.validate_route(human_path, self._policy.permitted_route_ids)
        escalation_id = self._store.record_escalation(
            episode_id,
            human_path=validated,
            outcome=outcome,
            now_utc=self._clock.now_utc(),
        )
        return EscalationOutcome(
            escalation_id=escalation_id,
            episode_id=episode_id,
            human_path=validated,
            outcome=outcome,
            simulated=True,
        )

    def record_human_acceptance(
        self,
        episode_id: str,
        accepted_by: str,
        accepted_scope: str,
    ) -> AcceptanceOutcome:
        """Record a named human acceptance, then derive the closure it produced.

        The acceptance closes the **handoff obligation**. It is never written to
        `evidence`, so it cannot make `care_evidenced` true, and no surface may
        say care happened because a human accepted a handoff
        (`03-program-design.md` section 3). This is the narrow reading of D4 and
        D11, and it is why the acceptance path and the evidence path are
        separate writes rather than one.

        `accepted_by` is validated against the policy's permitted owner ids, for
        the same reason `escalate` validates the human path: the ledger names a
        party this policy can display, not arbitrary free text. An acceptance by
        an unknown party raises a `PolicyViolation`, which the route maps to 422.

        **The closure is derived after the write, not predicted.** With the
        deadline already passed and no evidence, that derivation is
        `expired_unresolved`, not `closed_with_evidence`: expiry outranks an
        acceptance on purpose (see `rules.derive_closure`), because a promise is
        not evidence. The caller is told so rather than shown a resolved
        episode whose deadline went by with nothing to show for it.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is no "
                "handoff obligation for an acceptance to close"
            )
        validated = rules.validate_owner(accepted_by, self._policy.permitted_owner_ids)
        acceptance_id = self._store.record_human_acceptance(
            episode_id,
            accepted_by=validated,
            scope=accepted_scope,
            now_utc=self._clock.now_utc(),
        )
        closure = self._store.derive_closure(episode_id, self._clock.now_utc())
        return AcceptanceOutcome(
            acceptance_id=acceptance_id,
            episode_id=episode_id,
            accepted_by=validated,
            scope=accepted_scope,
            closure=closure,
            simulated=True,
        )

    def project_patient(self, episode_id: str) -> PatientSurface:
        """The patient's four lines, derived, with the expiry read-path first.

        **The expiry read-path.** The first patient read after an unresolved
        deadline records the expiry event, once, before projecting
        (`03-program-design.md` section 3). There is no scheduler: the read *is*
        the trigger, so nothing urgent waits on a background job, and an episode
        whose deadline passed while nobody looked is still reported honestly the
        moment somebody does.

        **Derive first, then record.** The event is written only when the
        derivation says `expired_unresolved`. That ordering is what keeps a
        resolved episode from recording a spurious expiry: with documented
        evidence the closure is `closed_with_evidence`, so no event is written
        and a later read cannot resurrect one. It also keeps
        `state.record_expiry_once` from raising `PrematureExpiry`, because the
        only remaining branch is "the deadline has passed and no care is
        evidenced".
        """
        now_utc = self._clock.now_utc()
        snapshot = self._store.load_snapshot(episode_id)
        closure = rules.derive_closure(snapshot, now_utc)
        if (
            snapshot.disposition is not None
            and snapshot.expiry_event_id is None
            and closure.closure is ClosureState.EXPIRED_UNRESOLVED
        ):
            self._store.record_expiry_once(
                episode_id, snapshot.disposition.version, now_utc
            )
            snapshot = self._store.load_snapshot(episode_id)
            closure = rules.derive_closure(snapshot, now_utc)
        lines = rules.patient_lines(snapshot, closure, self._policy_text)
        return patient_surface(
            episode_id, lines, closure, self._policy_text.fixture_label
        )

    def reassess(
        self, episode_id: str, confirmed_change_code: str | None
    ) -> ReassessmentResult:
        """Classify a confirmed change, then let `domain` decide what may happen.

        The classification is a closed-vocabulary code supplied by the caller.
        `domain.reassessment_decision` is the only thing that may authorise a
        second disposition version, and with no reviewer every input stops at the
        human path (D7, `03-program-design.md` section 8 item 2). This method
        therefore inserts nothing today: the endpoint and the refusal are what
        this slice owes, not a clinical branch.

        The version number is this layer's to carry when a branch is authorised,
        because it is state rather than policy. `state.insert_disposition` then
        enforces O7: a new version's deadline must be later than the one it
        replaces.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is nothing "
                "to reassess"
            )
        decision = rules.reassessment_decision(confirmed_change_code, self._policy)
        new_version: int | None = None
        if (
            decision.outcome is ReassessmentOutcome.INSERT_DISPOSITION_VERSION
            and decision.disposition is not None
        ):
            authorised = replace(
                decision.disposition,
                episode_id=episode_id,
                version=snapshot.disposition.version + 1,
            )
            self._store.insert_disposition(authorised, now_utc=self._clock.now_utc())
            new_version = authorised.version
        stops = decision.outcome is ReassessmentOutcome.STOP_AT_HUMAN_PATH
        return ReassessmentResult(
            episode_id=episode_id,
            outcome=decision.outcome,
            reason=decision.reason,
            disposition_version=new_version,
            routes_to_human_path=stops,
            human_path_route_id=(
                snapshot.disposition.fallback_route_id if stops else None
            ),
            simulated=True,
        )

    # -- consent ----------------------------------------------------------

    def change_consent(self, episode_id: str, granted: bool) -> int:
        """Append a consent version and return its number.

        The action path is unreachable without one, which is why this lands with
        it rather than in an earlier slice: `open_action` stamps the current
        version on the attempt, `receive_callback` re-checks it, and an attempt
        opened under a consent that is later revoked cannot be recorded as a
        success. Revocation is a new row with a new version, never an edit, so
        the stamped version stays legible forever.
        """
        self._store.load_snapshot(episode_id)
        return self._store.change_consent(
            episode_id,
            CLINICAL_SCOPE,
            granted=granted,
            now_utc=self._clock.now_utc(),
        )

    # -- actions (Slice 6) ------------------------------------------------

    def open_action(
        self, episode_id: str, route_id: str, purpose_id: str
    ) -> ActionOutcome:
        """Open one attempt and execute the tool. `02-architecture.md` section 3.3.

        The order is the normative one and it is not optional:

        1. **authorisation**: `domain.validate_route` is the only thing that may
           say a route is permitted (D2).
        2. **consent**: there must be a current version to stamp.
        3. **the key**: server-generated from `(episode, route, purpose)` under
           the server-held namespace (D5). A client that supplied its own key
           would make a double tap produce two keys, and I3 would never fire.
        4. **open once**: a second request on the same triple returns the
           original attempt and dispatches nothing.
        5. **execute**: the coordinator executes through the MCP tool surface,
           which rechecks all three server-side. The outcome comes back with an
           `origin` saying where it came from.

        This writes **no transition**. Appending the outcome is the callback's
        job, because first-terminal-wins and the duplicate record only mean
        something when the outcome arrives on the path a real platform would use.
        """
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is no plan "
                "with a permitted route to act on"
            )
        route = rules.validate_route(route_id, self._policy.permitted_route_ids)
        if snapshot.consent_version is None:
            raise ConsentRequired(
                f"episode {episode_id!r} has no recorded {CLINICAL_SCOPE} consent, "
                "so no attempt may be opened"
            )

        now_utc = self._clock.now_utc()
        key = derive_attempt_key(
            episode_id, route, purpose_id, namespace=self._key_namespace
        )

        existing = self._store.get_attempt_by_key(key)
        if existing is not None:
            return ActionOutcome(
                episode_id=episode_id,
                attempt_id=existing.attempt_id,
                idempotency_key=key,
                route_id=route,
                purpose_id=purpose_id,
                disposition_version=snapshot.disposition.version,
                consent_version=snapshot.consent_version,
                execution=existing.execution,
                duplicate=True,
                tool=None,
                origin=self._origin,
                simulated=True,
            )

        attempt = self._store.open_attempt_once(
            AttemptCommand(
                episode_id=episode_id,
                route_id=route,
                purpose_id=purpose_id,
                consent_version=snapshot.consent_version,
            ),
            key,
            now_utc=now_utc,
        )
        tool = self._coordinator.execute_tool(
            ToolRequest(
                episode_id=episode_id,
                route_id=route,
                attempt_key=key,
                disposition_version=snapshot.disposition.version,
            ),
            now_utc=now_utc,
        )
        return ActionOutcome(
            episode_id=episode_id,
            attempt_id=attempt.attempt_id,
            idempotency_key=key,
            route_id=route,
            purpose_id=purpose_id,
            disposition_version=snapshot.disposition.version,
            consent_version=attempt.consent_version,
            execution=attempt.execution,
            duplicate=False,
            tool=tool,
            # The origin the tool reports, not the origin the service assumes. If
            # they ever disagree the record follows the tool, because the tool is
            # the thing that actually ran.
            origin=tool.origin,
            simulated=True,
        )

    def receive_callback(
        self,
        episode_id: str,
        route_id: str,
        callback_key: str,
        result: CallbackResult,
        origin: Origin | str,
    ) -> CallbackOutcome:
        """Record one callback against the attempt this route opened.

        **The origin is checked, not trusted.** A caller may assert any value in
        the enum, and `origin = platform` is the one that makes the section 3.3
        claim checkable, so it is precisely the one that must not be settable by
        assertion. This refuses an origin the wired path cannot produce, which
        today means anything other than `local-sim`. See `OriginNotWired`.

        The attempt is the **latest** one opened on that route. Two attempts on
        one route are possible only with two different purpose ids, and the later
        one is the one awaiting an answer.

        **The episode is loaded first, before anything is recorded.** `list_attempts`
        on an episode that does not exist returns nothing, so without this a
        callback for an unknown episode answered 409 "no attempt on this route",
        which is true and misleading: it implies an episode that has been
        contacted. The live run of 3 October 2026 caught it. A missing episode is
        a 404 and says so.
        """
        self._store.load_snapshot(episode_id)
        stated = Origin(origin)
        if stated is not self._origin:
            raise OriginNotWired(
                f"origin {stated.value!r} is not one this deployment can produce; "
                f"the wired path reports {self._origin.value!r}. No tool is "
                "executed through a platform in this build, so recording a "
                "platform origin would state a fact no observation supports."
            )
        attempts = [
            attempt
            for attempt in self._store.list_attempts(episode_id)
            if attempt.route_id == route_id
        ]
        if not attempts:
            raise NoAttemptForRoute(
                f"episode {episode_id!r} opened no attempt on route {route_id!r}, "
                "so a callback for it has nothing to answer"
            )
        attempt = attempts[-1]
        receipt = self._store.record_callback_once(
            attempt.attempt_id,
            callback_key,
            result,
            stated,
            now_utc=self._clock.now_utc(),
        )
        snapshot = self._store.load_snapshot(episode_id)
        execution = (
            snapshot.attempt.execution
            if snapshot.attempt is not None
            else ExecutionStatus.NOT_STARTED
        )
        return CallbackOutcome(
            episode_id=episode_id,
            route_id=route_id,
            attempt_id=attempt.attempt_id,
            origin=stated,
            receipt=receipt,
            execution=execution,
            simulated=True,
        )

    # -- internals --------------------------------------------------------

    def _allowed_values(self) -> AllowedPlanValues:
        """The surface forms the coordinator may recognise, and nothing else.

        The canonical ids are included because a restatement may legitimately
        use one verbatim, and the alias keys because a patient will not. What is
        excluded is anything that would let the coordinator see the expected
        answer (ADR-0007).
        """
        return AllowedPlanValues(
            action_forms=frozenset(self._policy.action_aliases)
            | self._policy.permitted_action_ids,
            owner_forms=frozenset(self._policy.owner_aliases)
            | self._policy.permitted_owner_ids,
            deadline_forms=frozenset(self._policy.deadline_forms),
        )

    def _require_scorable(
        self,
        episode_id: str,
        input_mode: InputMode,
        transcript_confirmation_id: str | None,
        confirmed_text: str,
    ) -> None:
        """Refuse to evaluate a voice restatement before its transcript is confirmed.

        Two checks, because one is not enough: `domain` says whether the mode
        needs a confirmation at all, and the digest check says that the
        confirmation covers **this** string. An id that merely exists would let a
        caller confirm one transcript and score another.
        """
        if not rules.may_score_restatement(input_mode, transcript_confirmation_id):
            raise UnconfirmedTranscript(
                f"an {input_mode.value} restatement may not be scored before its "
                "transcript is confirmed (Gate 1 ordering rule)"
            )
        if input_mode is InputMode.VOICE and transcript_confirmation_id is not None:
            if transcript_confirmation_id != derive_confirmation_id(confirmed_text):
                raise UnconfirmedTranscript(
                    "the confirmation does not match the text being scored; "
                    "confirm this transcript first"
                )
            if not self._store.has_transcript_confirmation(
                episode_id, transcript_confirmation_id
            ):
                raise UnconfirmedTranscript(
                    f"no confirmation {transcript_confirmation_id!r} was recorded "
                    f"for episode {episode_id!r}"
                )

    def _verified_confirmation(
        self,
        episode_id: str,
        transcript_confirmation_id: str | None,
        confirmed_text: str,
    ) -> bool:
        """Whether a confirmation was really recorded **and** covers this text.

        Slice 7 closes NF4. Until now the record carried
        `transcript_confirmation_id is not None`, so a text or chip round that
        named any id at all was recorded as confirmed, and the ledger could
        assert a confirmation that never happened. Only the voice path checked
        the digest and the stored row.

        Two questions, and both must be yes: is this id the digest of the very
        string being scored, and was a confirmation with that id recorded for
        this episode. One alone is not enough: an id that merely exists would
        let a caller confirm one transcript and score another, which is the same
        swap the digest exists to prevent. The test is deliberately the same for
        every input mode, because a false confirmation is a false confirmation
        whichever path it arrived on.

        Whether a mode *needs* a confirmation before scoring stays
        `_require_scorable`'s job. This decides what the record may claim, which
        is a different question and the one NF4 was about.
        """
        if transcript_confirmation_id is None:
            return False
        if transcript_confirmation_id != derive_confirmation_id(confirmed_text):
            return False
        return self._store.has_transcript_confirmation(
            episode_id, transcript_confirmation_id
        )

    def _score(
        self,
        episode_id: str,
        confirmed_text: str,
        hint_level: HintLevel | str,
        transcript_confirmation_id: str | None,
        *,
        input_mode: InputMode | str,
        dwell_seconds: float | None,
        repair_round: int,
    ) -> RestatementOutcome:
        # Parsed by `domain` for the same reason as the hint route: a malformed
        # level or mode is a 422 refusal, not a 500 (NF2).
        level = rules.require_hint_level(hint_level)
        mode = rules.require_input_mode(input_mode)
        snapshot = self._store.load_snapshot(episode_id)
        if snapshot.disposition is None:
            raise NoDispositionYet(
                f"episode {episode_id!r} has no disposition, so there is no "
                "approved plan for a restatement to be compared against"
            )
        self._require_scorable(
            episode_id, mode, transcript_confirmation_id, confirmed_text
        )

        now_utc = self._clock.now_utc()
        # Coordinator extraction may raise `CoordinatorUnavailable`, which is
        # deliberately not caught: the flow stops, and stopping before the store
        # write is what guarantees no row claims a round that never happened.
        extracted = self._coordinator.extract_plan(
            confirmed_text, self._allowed_values()
        )
        comparison = rules.compare_plan(
            snapshot.disposition,
            extracted,
            policy=self._policy,
            now_utc=now_utc,
            display_tz=self._display_tz,
        )

        understood = not comparison.mismatched and not comparison.uncertain
        outcome = (
            RECALL_OUTCOME_BY_LEVEL[level] if understood else RecallOutcome.NOT_RECALLED
        )
        next_field = rules.next_repair(comparison, repair_round)
        routes_to_human_path = not understood and next_field is None

        restatement_id = self._store.record_restatement(
            episode_id,
            disposition_version=snapshot.disposition.version,
            hint_level=level,
            input_mode=mode,
            transcript_confirmed=self._verified_confirmation(
                episode_id, transcript_confirmation_id, confirmed_text
            ),
            extracted=extracted,
            comparison=comparison,
            repair_round=repair_round,
            outcome=outcome,
            dwell_seconds=dwell_seconds,
            now_utc=now_utc,
        )
        return RestatementOutcome(
            restatement_id=restatement_id,
            comparison=comparison,
            hint_level=level,
            repair_round=repair_round,
            outcome=outcome,
            next_repair_field=next_field,
            routes_to_human_path=routes_to_human_path,
            human_path_route_id=(
                snapshot.disposition.fallback_route_id
                if routes_to_human_path
                else None
            ),
            simulated=bool(getattr(self._coordinator, "simulated", False)),
        )


__all__ = [
    "ActionOutcome",
    "BarrierOutcome",
    "CallbackOutcome",
    "Clock",
    "ConsentRequired",
    "EpisodeAlreadyAssessed",
    "EpisodeService",
    "EscalationOutcome",
    "IntakeNotRecognised",
    "NoAttemptForRoute",
    "NoDispositionYet",
    "OriginNotWired",
    "ReassessmentResult",
    "RepairCapReached",
    "RestatementOutcome",
    "ScenarioClock",
    "ServiceError",
    "StaleRestatement",
    "SystemClock",
    "UnconfirmedTranscript",
]
