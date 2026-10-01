"""Frozen domain values for CareRelay. No I/O, no SDK, no clock.

Everything here is an immutable value or a closed vocabulary. Nothing here
reaches a network, a database, a file or the clock, and `tests/test_boundaries.py`
fails the build if that changes.

Three shapes are worth reading before the code:

* **`ExtractedPlan` carries raw spans *and* the extractor's own uncertainty.**
  Gate 4 section 1.1 accepted Reading A of the `compare_plan` contract
  (ADR-0007): canonicalisation lives here, in `domain`, and the coordinator
  returns raw text. A span the extractor is unsure about is not the same as a
  span it did not produce, so both are carried. Collapsing them re-creates the
  "unknown becomes an accusation" defect that kill condition K1 exists to catch.
* **`Disposition` is frozen and versioned.** The clinical deadline is immutable
  to operational code. A new version is inserted; an existing one is never
  updated (D3, invariant I1).
* **Closure is a derived value, never a stored one** (D4). Nothing in this
  package can write "resolved".

Wording note. No patient-facing clinical string is authored here. `PolicyText`
carries the wording and `rules.patient_lines` only composes it, so that no
model-generated text can reach the patient (`02-architecture.md` section 8).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

# ---------------------------------------------------------------------------
# Closed vocabularies
# ---------------------------------------------------------------------------

#: The three critical fields PlanBack compares. Order is the repair order.
COMPARISON_FIELDS: tuple[str, str, str] = (
    "action_id",
    "deadline_utc",
    "next_owner_id",
)

#: PlanBack offers two repair rounds. A third is never offered (C6).
MAX_REPAIR_ROUNDS = 2


class HintLevel(StrEnum):
    """The recall hint ladder (`PLAN.md` section 5.2).

    The level used is always recorded, because a hint that contains the answer
    turns a comprehension check into a reading test.
    """

    H0 = "H0"  # the question alone
    H1 = "H1"  # structural slots only: What / When / Who helps
    H2 = "H2"  # the plan card is shown, and removed only by the patient
    H3 = "H3"  # the plan is shown and the patient confirms it by choosing


class RecallOutcome(StrEnum):
    RECALL_UNAIDED = "recall_unaided"
    RECALL_SCAFFOLDED = "recall_scaffolded"
    RECALL_CUED = "recall_cued"
    NOT_RECALLED = "not_recalled"


#: H3 is an honest result, never a comprehension pass (`PLAN.md` section 5.2).
RECALL_OUTCOME_BY_LEVEL: Mapping[HintLevel, RecallOutcome] = MappingProxyType(
    {
        HintLevel.H0: RecallOutcome.RECALL_UNAIDED,
        HintLevel.H1: RecallOutcome.RECALL_SCAFFOLDED,
        HintLevel.H2: RecallOutcome.RECALL_CUED,
        HintLevel.H3: RecallOutcome.NOT_RECALLED,
    }
)


class HintEventKind(StrEnum):
    """Every hint event the product may emit.

    There is deliberately **no** auto-hide, auto-advance or timeout member.
    `rules.hint_transition` derives card visibility from this set alone, so an
    accessibility rule that no timer may remove the card is enforced by the
    vocabulary rather than by comment. A new member that hides anything without
    a patient action fails `tests/test_domain.py`.
    """

    SHOWN = "shown"
    PATIENT_HID = "patient_hid"


class InputMode(StrEnum):
    """How a restatement arrived.

    `VOICE` is the only mode that carries a machine transcript, so it is the only
    mode whose evaluation may be gated on a confirmation. The constrained `CHIPS`
    path exists so PlanBack can be built and tested with no speech work at all
    (`03-planback-closure-contract.md` section 1.5): a constrained input path is a
    feasibility unlock, not a downgrade.
    """

    TEXT = "text"
    VOICE = "voice"
    CHIPS = "chips"


class ExecutionStatus(StrEnum):
    """Axis A of the Closure Contract: did the request get through?"""

    NOT_STARTED = "not_started"
    ATTEMPTED = "attempted"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"


#: Terminal transitions are absorbing. The **first** one in `seq` order wins.
TERMINAL_TRANSITIONS: frozenset[ExecutionStatus] = frozenset(
    {
        ExecutionStatus.ACKNOWLEDGED,
        ExecutionStatus.FAILED,
        ExecutionStatus.SUPERSEDED,
    }
)


class EvidenceLevel(StrEnum):
    """Axis B of the Closure Contract: do we believe care actually happened?"""

    NONE = "none"
    SELF_REPORTED = "self_reported"
    DOCUMENTED = "documented"


class ClosureState(StrEnum):
    OPEN = "open"
    CLOSED_WITH_EVIDENCE = "closed_with_evidence"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    EXPIRED_UNRESOLVED = "expired_unresolved"


class Origin(StrEnum):
    """Where a failure event came from. The platform path and the local
    simulation must be distinguishable by inspection (`02-architecture.md` 3.3)."""

    PLATFORM = "platform"
    LOCAL_SIM = "local-sim"


class DispositionSource(StrEnum):
    FIXTURE = "fixture"
    REVIEWER = "reviewer"
    REASSESSMENT = "reassessment"


class ReassessmentOutcome(StrEnum):
    STOP_AT_HUMAN_PATH = "stop_at_human_path"
    INSERT_DISPOSITION_VERSION = "insert_disposition_version"


# ---------------------------------------------------------------------------
# PlanBack values
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Disposition:
    """One clinician-governed plan, at one version.

    Frozen on purpose. Invariant I1 says the clinical deadline is immutable to
    operational code: retrying a failed booking is not new clinical information.
    A changed deadline is a new version with a new `source`, inserted, never an
    edit of this object.
    """

    episode_id: str
    version: int
    policy_version: str
    action_id: str
    clinical_deadline_utc: datetime
    next_owner_id: str
    fallback_route_id: str
    source: DispositionSource


@dataclass(frozen=True)
class ExtractedPlan:
    """What a coordinator returns under Reading A (ADR-0007): **raw spans**.

    `None` means the extractor did not commit to a value, and is never evidence
    that the patient is wrong. `uncertain_fields` is the extractor's *own*
    doubt about a field it did produce, and is carried separately for the reason
    given in the module docstring.
    """

    action_span: str | None = None
    deadline_span: str | None = None
    next_owner_span: str | None = None
    uncertain_fields: frozenset[str] = frozenset()


@dataclass(frozen=True)
class PlanComparison:
    """Three disjoint, complete sets over `COMPARISON_FIELDS`.

    Only a known, different canonical value is a mismatch. An unresolved span is
    uncertain: never a claimed error and never a claimed success.
    """

    matched: frozenset[str]
    mismatched: frozenset[str]
    uncertain: frozenset[str]

    def is_clean(self) -> bool:
        """True only when every critical field was resolved **and** agreed.

        Deliberately stricter than "no mismatch". A comparator that answers
        "uncertain" to everything has zero false mismatches and is useless:
        read-back would repair nothing and every patient would be pushed to the
        human path. K1 must not be passable by refusing to commit.
        """
        return not self.mismatched and not self.uncertain


# ---------------------------------------------------------------------------
# Execution and evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AttemptTransition:
    """One append-only row of `attempt_transitions`.

    `seq` is monotonic and assigned on append. An `acknowledged` arriving after
    a `failed` is retained and non-winning: terminal states are absorbing and
    the first terminal transition in `seq` order defines the status.
    """

    seq: int
    kind: ExecutionStatus
    origin: Origin
    recorded_at: datetime
    payload: str = ""


@dataclass(frozen=True)
class AttemptSnapshot:
    attempt_id: str
    idempotency_key: str
    route_id: str
    consent_version: int
    execution: ExecutionStatus


@dataclass(frozen=True)
class AttemptCommand:
    """A request to open one attempt, before the store assigns anything.

    `purpose_id` is part of the identity because D5 derives the idempotency key
    from `(episode, route, attempt-purpose)`. A new purpose id is an explicit
    authorised retry; a double tap reuses the same triple and therefore the same
    key.

    `consent_version` is stamped here and re-checked at record time, so an
    attempt opened under a consent that is later revoked cannot be recorded as
    a success (`03-program-design.md` section 3).
    """

    episode_id: str
    route_id: str
    purpose_id: str
    consent_version: int


@dataclass(frozen=True)
class EvidenceRecord:
    """One row of `evidence`.

    D11: `level = documented` requires a **non-simulated, sourced** artefact.
    That is a `CHECK` constraint in the database (Slice 3) and is also enforced
    here, because a simulated 200 response must never close care.
    """

    level: EvidenceLevel
    simulated: bool
    provenance: str
    source_ref: str | None


@dataclass(frozen=True)
class CallbackResult:
    """What one callback asserts about one attempt.

    `transition` is the terminal execution outcome the callback claims, or
    `None` when the callback carries evidence only. A value outside
    `TERMINAL_TRANSITIONS` is refused by the store rather than folded into
    `attempted`, because a corrupt row must not be able to look like an attempt
    still in flight (`02-architecture.md` section 4.1).
    """

    transition: ExecutionStatus | None = None
    evidence: EvidenceRecord | None = None
    payload: str = ""


@dataclass(frozen=True)
class EpisodeSnapshot:
    """Everything `derive_closure` is allowed to look at.

    This is a projection over app-owned state, not a live object. The expiry
    event and the human-acceptance record are inputs because D4 and D12 require
    them; revision 1 of the architecture omitted both.
    """

    disposition: Disposition | None
    attempt: AttemptSnapshot | None
    evidence: tuple[EvidenceRecord, ...]
    consent_version: int | None
    human_acceptance_id: str | None
    escalation_id: str | None
    expiry_event_id: str | None
    #: The named human path the escalation handed the episode to. Slice 5, F6:
    #: an escalated episode's acting party is that service, not the patient, so
    #: `derive_closure` needs the path itself and not merely the fact that an
    #: escalation exists. `None` whenever `escalation_id` is `None`.
    #: Defaulted, and therefore last, so every existing construction still holds.
    escalated_human_path: str | None = None


@dataclass(frozen=True)
class ClosureProjection:
    """The derived closure. Nothing in the system can write this value."""

    execution: ExecutionStatus
    evidence: EvidenceLevel
    closure: ClosureState
    action_owner_id: str | None
    care_evidenced: bool
    simulated: bool


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyText:
    """Policy-owned patient-facing wording.

    `domain` renders the patient's four lines from this value and from nothing
    else. A raw id that has no display here cannot reach the patient: the
    renderer raises instead of printing an internal identifier.

    `deadline_display_by_version` is keyed by disposition version, not a single
    string. A reassessment inserts a new version with a new deadline, and one
    fixed string would then describe the wrong instant to the patient. A version
    with no entry raises rather than rendering a stale deadline, because the
    deadline is the one fact the product exists to preserve.
    """

    policy_version: str
    fixture_label: str
    deadline_display_by_version: Mapping[int, str]
    #: The owner id that means "the patient themselves". Line 2 is phrased
    #: differently for this owner: "You or [named person] must act now." is a
    #: malformed sentence when the named person is the patient.
    self_owner_id: str
    owner_display_by_id: Mapping[str, str]
    route_display_by_id: Mapping[str, str]
    simulated: bool


@dataclass(frozen=True)
class AuthorisedReassessment:
    """A reviewer-authorised replacement disposition.

    This is the **only** domain route to a second disposition version. It is
    explicit policy data, so the judged fixture has no branch at all until a
    reviewer authorises one.
    """

    change_code: str
    disposition: Disposition
    authorised_by: str


@dataclass(frozen=True)
class PolicyFixture:
    """The resolution tables and closed vocabularies for one policy version.

    Gate 4 section 1.1 widened the Gate 3 `compare_plan` signature "with the
    resolution tables (`action_aliases`, `deadline_forms`, `owner_aliases`) as
    explicit policy data". They are carried here as one value instead of five
    parallel mappings, which keeps a single source of truth for what the policy
    permits and what it can resolve.
    """

    version: str
    permitted_route_ids: frozenset[str]
    permitted_action_ids: frozenset[str]
    permitted_owner_ids: frozenset[str]
    permitted_change_codes: frozenset[str]
    action_aliases: Mapping[str, str]
    owner_aliases: Mapping[str, str]
    #: normalised surface phrase -> (day offset, local HH:MM)
    deadline_forms: Mapping[str, tuple[int, str]]
    authorised_reassessments: Mapping[str, AuthorisedReassessment]


@dataclass(frozen=True)
class StopOrFixtureDecision:
    """The result of a reassessment request.

    `disposition` is non-null only for an authorised insertion. Every other
    outcome stops at the human path, because an operational retry never enters
    this path and a missing or unknown code is not a clinical change.
    """

    outcome: ReassessmentOutcome
    reason: str
    disposition: Disposition | None


# ---------------------------------------------------------------------------
# Hint state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HintState:
    level: HintLevel
    card_visible: bool


@dataclass(frozen=True)
class HintEvent:
    """A hint event, recorded for the judge ledger.

    `dwell_seconds` is evidence-gathering and never a control input. It is
    stored on the `restatements` row, shown in the ledger, never shown to the
    patient, and never changes what the patient may do next (`PLAN.md` 5.2.1).
    """

    level: HintLevel
    kind: HintEventKind
    dwell_seconds: float | None = None
