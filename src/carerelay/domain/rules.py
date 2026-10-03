"""Pure domain rules. No I/O, no SDK, no clock.

Every function here is a decision. `02-architecture.md` D2 puts the trust
boundary at the module boundary, and `tests/test_boundaries.py` fails the build
if an I/O, network, database, filesystem or wall-clock import or call appears in
this package.

Time is always an argument, never a lookup. `compare_plan` and `derive_closure`
take `now_utc` because the caller owns the clock (D5); this module never reads
one.

The eight contracted functions are `validate_route`, `validate_change`,
`compare_plan`, `next_repair`, `project_attempt`, `derive_closure`,
`patient_lines` and `reassessment_decision`. `hint_transition` is the ninth and
is here because constraint C8 (no timer, no auto-advance anywhere) is only a
real rule if some code can refuse to hide the card.

Three readings of the approved documents are made explicit rather than silent.
They are listed in `docs/plans/urgent-advice-accessibility/00-status.md` under
the Slice 2 entry so they can be corrected:

1. Closure precedence. `derive_closure` puts expiry above a recorded human
   acceptance. The approved condition for `closed_with_evidence` is "evidence
   >= documented **or** an explicit human acceptance is recorded", and a human
   acceptance is not evidence that care happened. When the deadline has passed
   with no evidence, the honest state is `expired_unresolved`. Choosing the
   other order would let a scripted acceptance report a resolved episode whose
   deadline passed with nothing to show for it, which is invariant I2.
2. Line 2 of the patient plan. The approved rendering is "You or [named person]
   must act now." With a patient owner that is malformed, which Slice 1 found by
   inspection and flagged. Here the sentence is composed by owner: "You must act
   now." when the owner is the patient, and the approved sentence otherwise.
3. No approved wording exists for `closed_with_evidence`. `patient_lines` raises
   rather than render "Help is not arranged." over a resolved episode. Slice 10
   owns the Closure Contract rendering.

The tenth function, `may_score_restatement`, is here for the same reason as
`hint_transition`: Gate 1's transcript-confirmation ordering rule is only a real
rule if some code can refuse to evaluate an unconfirmed transcript.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, tzinfo

from carerelay.domain.models import (
    COMPARISON_FIELDS,
    DEPLOYMENT_SIMULATED,
    MAX_REPAIR_ROUNDS,
    TERMINAL_TRANSITIONS,
    AttemptTransition,
    AuthorisedReassessment,
    ClosureProjection,
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
    PlanComparison,
    PolicyFixture,
    PolicyText,
    ReassessmentOutcome,
    StopOrFixtureDecision,
)

__all__ = [
    "DomainError",
    "PolicyViolation",
    "UnpermittedRouteId",
    "UnpermittedChangeCode",
    "UnpermittedTransition",
    "UnpermittedHintEvent",
    "MissingDisplayText",
    "NoDispositionToRender",
    "NoApprovedPatientWording",
    "normalise",
    "validate_route",
    "validate_change",
    "compare_plan",
    "next_repair",
    "project_attempt",
    "derive_closure",
    "patient_lines",
    "reassessment_decision",
    "may_score_restatement",
    "hint_transition",
]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DomainError(Exception):
    """Base class for a refusal to make a decision."""


class PolicyViolation(DomainError):
    """A value arrived from outside the closed vocabulary the policy permits.

    A policy violation is never a negative finding about the patient. It is a
    stop condition, and the caller routes to the human path (D7, invariant I5).
    """

    def __init__(self, value: object, permitted: Sequence[str] | None = None) -> None:
        self.value = value
        self.permitted = tuple(permitted) if permitted is not None else ()
        detail = f"{value!r} is not in the permitted set"
        if self.permitted:
            detail += f" {sorted(self.permitted)!r}"
        super().__init__(detail)


class UnpermittedRouteId(PolicyViolation):
    """A route id outside `permitted_route_ids`. Hallucinated routes stop here."""


class UnpermittedChangeCode(PolicyViolation):
    """A symptom-change code outside the policy's closed vocabulary."""


class UnpermittedTransition(PolicyViolation):
    """An attempt transition that is not a terminal transition."""


class UnpermittedHintEvent(PolicyViolation):
    """A hint event the vocabulary does not contain, or one for the wrong level."""


class MissingDisplayText(PolicyViolation):
    """A policy id has no approved display string, so it cannot be shown.

    Raised instead of printing an internal identifier to the patient.
    """


class NoDispositionToRender(DomainError):
    """`patient_lines` was called before any plan existed."""


class NoApprovedPatientWording(DomainError):
    """No approved patient rendering exists for this closure state yet."""


# ---------------------------------------------------------------------------
# Closed-vocabulary validation
# ---------------------------------------------------------------------------


def validate_route(route_id: str, permitted_route_ids: frozenset[str]) -> str:
    """Return `route_id` if the policy permits it, otherwise refuse.

    Fail closed. A route id the policy does not contain is critical uncertainty:
    the caller stops at the human path before a tool is opened or a disposition
    is touched (D7).
    """
    if route_id not in permitted_route_ids:
        raise UnpermittedRouteId(route_id, sorted(permitted_route_ids))
    return route_id


def validate_change(
    value: str | None, permitted_values: frozenset[str]
) -> str | None:
    """Validate one value from the closed symptom-change vocabulary.

    `None` returns `None`. Absent input asserts no change, and absence is never
    a negative finding (I5). A value outside the vocabulary raises, because a
    code the policy has never seen cannot be allowed to pick a clinical branch.
    """
    if value is None:
        return None
    if value not in permitted_values:
        raise UnpermittedChangeCode(value, sorted(permitted_values))
    return value


# ---------------------------------------------------------------------------
# PlanBack
# ---------------------------------------------------------------------------


def normalise(text: str) -> str:
    """Casefold and collapse whitespace, so "By 6 Today" and "by 6 today" agree."""
    return " ".join(text.strip().casefold().split())


def _resolve_id(
    span: str | None, aliases: Mapping[str, str], allowed: frozenset[str]
) -> str | None:
    if span is None:
        return None
    key = normalise(span)
    if key in aliases:
        return aliases[key]
    if key in allowed:
        return key
    return None


def _resolve_deadline(
    span: str | None,
    now_utc: datetime,
    display_tz: tzinfo,
    forms: Mapping[str, tuple[int, str]],
) -> datetime | None:
    """Resolve a relative phrase to a canonical instant.

    Raw text is never compared. "today before six" becomes an instant, so a
    known wrong day resolves to a known different instant and is a mismatch,
    while an unresolvable phrase stays uncertain.
    """
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
    policy: PolicyFixture,
    now_utc: datetime,
    display_tz: tzinfo,
) -> PlanComparison:
    """Compare a restatement against the disposition. Code decides, not a model.

    Reading A (ADR-0007): the coordinator returned raw spans, and resolution
    happens here against the policy's alias and relative-time tables. Gate 4
    section 1.1 widened the Gate 3 signature with exactly these tables; they are
    carried on `PolicyFixture` as one policy value.

    Three outcomes per critical field, and they never collapse:

    * **matched** - a known value that equals the disposition's
    * **mismatched** - a known value that differs. Only a known difference is an
      accusation
    * **uncertain** - the extractor produced nothing, or produced something the
      tables cannot resolve, or flagged the field itself as doubtful

    An `uncertain_fields` entry wins over a resolvable span. A field the
    extractor is unsure about is not the same as a field it did not produce, and
    neither is evidence that the patient is wrong.
    """
    if now_utc.tzinfo is None:
        raise DomainError(
            "now_utc must be timezone-aware; domain never guesses a timezone"
        )

    resolved = (
        (
            "action_id",
            _resolve_id(
                extracted.action_span, policy.action_aliases, policy.permitted_action_ids
            ),
            expected.action_id,
        ),
        (
            "deadline_utc",
            _resolve_deadline(
                extracted.deadline_span, now_utc, display_tz, policy.deadline_forms
            ),
            expected.clinical_deadline_utc,
        ),
        (
            "next_owner_id",
            _resolve_id(
                extracted.next_owner_span, policy.owner_aliases, policy.permitted_owner_ids
            ),
            expected.next_owner_id,
        ),
    )

    matched: set[str] = set()
    mismatched: set[str] = set()
    uncertain: set[str] = set()

    for field_name, got, want in resolved:
        if field_name in extracted.uncertain_fields:
            uncertain.add(field_name)
        elif got is None:
            uncertain.add(field_name)
        elif got == want:
            matched.add(field_name)
        else:
            mismatched.add(field_name)

    return PlanComparison(frozenset(matched), frozenset(mismatched), frozenset(uncertain))


def next_repair(comparison: PlanComparison, completed_rounds: int) -> str | None:
    """The next field to repair, or `None` when no further round is offered.

    Repairs one differing field at a time, in `COMPARISON_FIELDS` order, and is
    bounded: a third round is never offered (C6). An uncertain field is repaired
    like a mismatched one, because the honest repair for "I could not tell what
    you said" is to ask again, not to accuse.
    """
    if completed_rounds >= MAX_REPAIR_ROUNDS:
        return None
    for field_name in COMPARISON_FIELDS:
        if field_name in comparison.mismatched or field_name in comparison.uncertain:
            return field_name
    return None


#: The input modes that carry a machine transcript, and therefore require the
#: patient to confirm or correct it before any evaluation (Gate 1 ordering rule).
TRANSCRIPT_INPUT_MODES: frozenset[InputMode] = frozenset({InputMode.VOICE})


def may_score_restatement(
    input_mode: InputMode, transcript_confirmation_id: str | None
) -> bool:
    """Whether a restatement may be evaluated at all.

    Gate 1's ordering rule: a transcript is confirmed **before** it is evaluated.
    Scoring a draft transcript judges a comprehension the patient never agreed to,
    and `03-planback-closure-contract.md` section 1.5 records exactly that defect
    in the current wireframe. A confirmed-and-corrected transcript is a different
    string from the draft, so evaluating the draft is evaluating the wrong input.

    A text or chip restatement carries no transcript and is always scorable.

    This lives in `domain` rather than in the service layer because it is a safety
    decision, and D2 puts safety decisions in the module that cannot do I/O.
    """
    if input_mode in TRANSCRIPT_INPUT_MODES:
        return bool(transcript_confirmation_id)
    return True


# ---------------------------------------------------------------------------
# Execution, evidence and closure
# ---------------------------------------------------------------------------


def project_attempt(transitions: Sequence[AttemptTransition]) -> ExecutionStatus:
    """Derive one attempt's execution status from its append-only transitions.

    `02-architecture.md` section 4.1: the current status is the latest
    transition by `seq`, else `attempted`, and terminal states are absorbing, so
    **the first terminal transition in `seq` order defines the status**. The two
    sentences disagree once a late acknowledgement follows a failure; the
    ordering rule is the correction, and it is the one implemented here.

    A reordered acknowledgement is retained and non-winning. A transition whose
    kind is not terminal is a corrupt row, not an attempt in progress, so it
    raises rather than being folded into `attempted`. **Every** row is checked,
    not only the winning one: a corrupt row anywhere means the ledger cannot be
    trusted, and ignoring the rows after the winner would hide exactly the fault
    this check exists to surface.
    """
    ordered = sorted(transitions, key=lambda row: row.seq)
    for transition in ordered:
        if transition.kind not in TERMINAL_TRANSITIONS:
            raise UnpermittedTransition(
                transition.kind, sorted(member.value for member in TERMINAL_TRANSITIONS)
            )
    if not ordered:
        return ExecutionStatus.ATTEMPTED
    return ordered[0].kind


def _strongest_evidence(records: Sequence[EvidenceRecord]) -> EvidenceLevel:
    """The evidence axis, with D11 enforced here as well as in the database.

    A row claiming `documented` is only documented when it is non-simulated and
    sourced. A simulated or unsourced row is skipped, not upgraded, so a
    scripted 200 response can never close care. Absence of any row is `none`,
    never a negative finding.
    """
    level = EvidenceLevel.NONE
    for record in records:
        if record.level is EvidenceLevel.DOCUMENTED:
            if not record.simulated and record.source_ref:
                return EvidenceLevel.DOCUMENTED
            continue
        if record.level is EvidenceLevel.SELF_REPORTED and level is EvidenceLevel.NONE:
            level = EvidenceLevel.SELF_REPORTED
    return level


def derive_closure(snapshot: EpisodeSnapshot, now_utc: datetime) -> ClosureProjection:
    """Derive the closure state. Nothing in the system can write "resolved" (D4).

    Precedence, and why:

    1. Non-simulated documented evidence: care happened, so the episode is
       `closed_with_evidence` even if an expiry event was recorded earlier. The
       expiry event stays in the ledger as a fact; it is not erased.
    2. Expiry. Either a recorded expiry event (D12: sticky, so a backwards clock
       cannot un-expire an episode) or a deadline that has passed with no
       evidence. This outranks a human acceptance on purpose: an acceptance is a
       promise, not evidence, and reporting a resolved episode whose deadline
       passed with nothing to show for it is invariant I2.
    3. A recorded human acceptance: closes the handoff obligation.
       `care_evidenced` stays false, so no surface may say care occurred.
    4. A recorded escalation: handed to a named human path, deadline still
       visible.
    5. Otherwise `open`.

    **F6, decided at Slice 5:** the acting party follows the handoff. Once an
    escalation is recorded, `action_owner_id` names the human path it was handed
    to rather than the patient, because I4 requires exactly one party to act at
    every moment and telling a patient to act on a plan that has been handed away
    is the false-responsibility failure this product exists to prevent. An
    escalation that names no human path is refused rather than silently falling
    back to the patient.
    """
    if now_utc.tzinfo is None:
        raise DomainError(
            "now_utc must be timezone-aware; domain never guesses a timezone"
        )

    disposition = snapshot.disposition
    if snapshot.expiry_event_id is not None and disposition is None:
        # An expiry event records that a deadline passed. With no disposition
        # there is no deadline for it to have passed, and the projection would
        # otherwise report `expired_unresolved` while naming no owner, which I4
        # forbids: at every moment exactly one party must act.
        raise DomainError(
            "an expiry event requires a disposition; there is no deadline for it "
            "to have passed"
        )
    execution = (
        snapshot.attempt.execution
        if snapshot.attempt is not None
        else ExecutionStatus.NOT_STARTED
    )
    evidence = _strongest_evidence(snapshot.evidence)
    care_evidenced = evidence is EvidenceLevel.DOCUMENTED
    deadline_passed = (
        disposition is not None and now_utc >= disposition.clinical_deadline_utc
    )
    expired = snapshot.expiry_event_id is not None or (
        deadline_passed and not care_evidenced
    )

    if expired and execution is ExecutionStatus.ATTEMPTED:
        # The execution axis runs attempted -> acknowledged | failed | expired
        # (contract section 2.2). An attempt that recorded no terminal outcome
        # and whose deadline has passed is the one case that reaches `expired`.
        # A recorded acknowledged, failed or superseded outcome is the more
        # specific fact and is never overwritten.
        execution = ExecutionStatus.EXPIRED

    if care_evidenced:
        closure = ClosureState.CLOSED_WITH_EVIDENCE
    elif expired:
        closure = ClosureState.EXPIRED_UNRESOLVED
    elif snapshot.human_acceptance_id is not None:
        closure = ClosureState.CLOSED_WITH_EVIDENCE
    elif snapshot.escalation_id is not None:
        closure = ClosureState.ESCALATED_TO_HUMAN
    else:
        closure = ClosureState.OPEN

    return ClosureProjection(
        execution=execution,
        evidence=evidence,
        closure=closure,
        action_owner_id=_action_owner(snapshot, disposition),
        care_evidenced=care_evidenced,
        # F5, Slice 6: a deployment-level fact, not a function of the evidence.
        # It was `not care_evidenced` until 3 October 2026, which let one
        # documented row imply the episode had stopped being a simulation.
        simulated=DEPLOYMENT_SIMULATED,
    )


def _action_owner(
    snapshot: EpisodeSnapshot, disposition: Disposition | None
) -> str | None:
    """Who must act now. F6, decided at Slice 5; see `derive_closure`.

    An escalation moves the obligation to the named human path. Without an
    escalation the owner is the disposition's own `next_owner_id`, which is the
    pre-Slice-5 behaviour and is unchanged for every non-escalated episode.
    """
    if snapshot.escalation_id is None:
        return disposition.next_owner_id if disposition is not None else None
    if snapshot.escalated_human_path is None:
        raise DomainError(
            f"escalation {snapshot.escalation_id!r} names no human path, so no "
            "party is left to act, which I4 forbids"
        )
    return snapshot.escalated_human_path


# ---------------------------------------------------------------------------
# Patient rendering
# ---------------------------------------------------------------------------


def patient_lines(
    snapshot: EpisodeSnapshot,
    closure: ClosureProjection,
    policy_text: PolicyText,
) -> tuple[str, str, str, str]:
    """The four lines the patient sees, and nothing else.

    Every word comes from `policy_text` or from the approved copy. No model
    output can reach this surface: an owner or route id with no approved display
    raises rather than printing an internal identifier.

    The deadline wording is looked up by **disposition version**. A reassessment
    inserts a new version with a new deadline, so a single fixed string would
    describe the wrong instant; a version with no approved wording raises rather
    than printing a stale deadline.

    `02-architecture.md` section 7 fixes two approved renderings, the unresolved
    one and the expired one. There is no approved rendering for a resolved
    episode, so this refuses instead of printing "No one has agreed to help yet."
    over an episode where care is evidenced.
    """
    disposition = snapshot.disposition
    if disposition is None:
        raise NoDispositionToRender(
            "no disposition exists, so there are no approved patient lines to render"
        )

    owner_display = policy_text.owner_display_by_id.get(disposition.next_owner_id)
    if owner_display is None:
        raise MissingDisplayText(disposition.next_owner_id)
    route_display = policy_text.route_display_by_id.get(disposition.fallback_route_id)
    if route_display is None:
        raise MissingDisplayText(disposition.fallback_route_id)

    deadline_display = policy_text.deadline_display_by_version.get(disposition.version)
    if deadline_display is None:
        raise MissingDisplayText(
            f"no approved deadline wording for disposition version {disposition.version}"
        )

    if closure.closure is ClosureState.EXPIRED_UNRESOLVED:
        # Quoted from `02-architecture.md` section 7, re-approved 2 October 2026.
        # The punctuation is part of the approved copy, not new prose. Line 3
        # carries the deadline and is a real sentence rather than a fragment;
        # line 4 lost its em dash, which read clipped to a frightened reader.
        return (
            "No one has agreed to help yet.",
            "You can still do this.",
            f"It is past {deadline_display}. Please go now.",
            f"Call {route_display}. They can help from here.",
        )

    if closure.closure is ClosureState.CLOSED_WITH_EVIDENCE:
        raise NoApprovedPatientWording(
            "no approved patient rendering exists for closed_with_evidence; "
            "the Closure Contract rendering arrives in Slice 10"
        )

    if disposition.next_owner_id == policy_text.self_owner_id:
        owner_sentence = "Please act now."
    else:
        owner_sentence = f"Please act now: you, or {owner_display}."

    return (
        "No one has agreed to help yet.",
        owner_sentence,
        f"Please do it before {deadline_display}.",
        f"If that does not work, call {route_display}.",
    )


# ---------------------------------------------------------------------------
# Reassessment
# ---------------------------------------------------------------------------


def reassessment_decision(
    classified_change: str | None, policy: PolicyFixture
) -> StopOrFixtureDecision:
    """Decide whether a confirmed symptom change may replace the plan.

    Only a reviewer-authorised branch may insert a second disposition version.
    Everything else stops at the human path, and the reasons are distinct on
    purpose so the ledger shows why:

    * no confirmed code: absence asserts no change (I5)
    * a code outside the closed vocabulary: fail closed (D7)
    * a permitted code with no authorised branch: the judged fixture stops

    An operational retry never reaches this function. Retrying a failed booking
    is not new clinical information (I1).
    """
    if classified_change is None:
        return StopOrFixtureDecision(
            outcome=ReassessmentOutcome.STOP_AT_HUMAN_PATH,
            reason="no confirmed change code: absence is not a negative finding (I5)",
            disposition=None,
        )

    if classified_change not in policy.permitted_change_codes:
        return StopOrFixtureDecision(
            outcome=ReassessmentOutcome.STOP_AT_HUMAN_PATH,
            reason=(
                f"change code {classified_change!r} is outside policy "
                f"{policy.version}: fail closed to the human path (D7)"
            ),
            disposition=None,
        )

    branch: AuthorisedReassessment | None = policy.authorised_reassessments.get(
        classified_change
    )
    if branch is None:
        return StopOrFixtureDecision(
            outcome=ReassessmentOutcome.STOP_AT_HUMAN_PATH,
            reason=(
                f"policy {policy.version} has no reviewer-authorised branch for "
                f"change code {classified_change!r}"
            ),
            disposition=None,
        )

    if branch.disposition.source is not DispositionSource.REASSESSMENT:
        raise PolicyViolation(
            branch.disposition.source,
            [DispositionSource.REASSESSMENT.value],
        )

    return StopOrFixtureDecision(
        outcome=ReassessmentOutcome.INSERT_DISPOSITION_VERSION,
        reason=f"authorised by {branch.authorised_by}",
        disposition=branch.disposition,
    )


# ---------------------------------------------------------------------------
# Hint disclosure
# ---------------------------------------------------------------------------


def hint_transition(state: HintState, event: HintEvent) -> HintState:
    """Apply one hint event to the card's visibility.

    The card is hidden **only** by `HintEventKind.PATIENT_HID`. Nothing in this
    function reads `dwell_seconds`, so no elapsed time can remove the card: two
    events differing only in dwell time produce the same state. That is
    constraint C8, and it is the reason the event vocabulary has no auto-hide
    member.
    """
    if event.level is not state.level:
        raise UnpermittedHintEvent(
            event.level, [member.value for member in HintLevel]
        )

    if event.kind is HintEventKind.PATIENT_HID:
        return HintState(level=state.level, card_visible=False)
    if event.kind is HintEventKind.SHOWN:
        return HintState(level=state.level, card_visible=True)
    raise UnpermittedHintEvent(
        event.kind, [member.value for member in HintEventKind]
    )
