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
3. `closed_with_evidence` had no approved wording until the Gate 1 re-approval
   of 8 October 2026 supplied the closure renderings. `patient_lines` refused
   rather than render "No one has agreed to help yet." over a resolved
   episode, and it now renders all four closure states. The two resolved
   cases do not share line 1: a recorded acceptance is a promise, not
   evidence, so "Someone has agreed to help." is what an acceptance alone
   produces and "Help is arranged." waits for `care_evidenced` (F4).

The tenth function, `may_score_restatement`, is here for the same reason as
`hint_transition`: Gate 1's transcript-confirmation ordering rule is only a real
rule if some code can refuse to evaluate an unconfirmed transcript.

Slice 7 adds three parsers, `require_hint_level`, `require_hint_event_kind` and
`require_input_mode`. A caller-supplied string that is not a member of its closed
vocabulary is a `PolicyViolation`, never a `ValueError`. Before Slice 7 the
service layer called the enum constructors directly, so a malformed value left
`domain` as an uncaught `ValueError` and the API answered 500 (finding NF2). The
rule is the same one `validate_route` already enforces for route ids: an
out-of-vocabulary value stops at the human path, it does not crash.

Slice 10 adds `validate_owner`. It is the same fail-closed check `validate_route`
already applies, aimed at the acting party instead of the route: a recorded human
acceptance names the party that took the handoff on, and I4 requires that party
to be one the policy can display. It lives here rather than in `service` for the
same reason `validate_route` does, because "who is allowed to act" is a safety
decision and D2 keeps safety decisions in the module that cannot do I/O.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta, timezone, tzinfo
import json
import re

from carerelay.domain.models import (
    ReadbackContext,
    RetainedMatch,
    SourceSpan,
    ChoiceView,
    CommandOffer,
    OutcomeView,
    PlanView,
    QuestionView,
    FlowView,
    JourneyBundle,
    JourneyProjection,
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
    RecallOutcome,
    StopOrFixtureDecision,
)

__all__ = [
    "DomainError",
    "PolicyViolation",
    "UnpermittedRouteId",
    "UnpermittedOwnerId",
    "UnpermittedChangeCode",
    "UnpermittedTransition",
    "UnpermittedHintEvent",
    "MissingDisplayText",
    "NoDispositionToRender",
    "normalise",
    "validate_route",
    "validate_owner",
    "validate_change",
    "compare_plan",
    "next_repair",
    "project_attempt",
    "derive_closure",
    "patient_lines",
    "reassessment_decision",
    "may_score_restatement",
    "hint_transition",
    "require_hint_level",
    "require_hint_event_kind",
    "require_input_mode",
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


class UnpermittedOwnerId(PolicyViolation):
    """An acting party outside `permitted_owner_ids`.

    Slice 10. A recorded human acceptance names the party that took the handoff
    on, and I4 requires that party to be one the policy can display. An
    acceptance by an unknown party would put a name in the ledger that no screen
    can render and no route can reach, so it stops here rather than being stored.
    """


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


def validate_owner(owner_id: str, permitted_owner_ids: frozenset[str]) -> str:
    """Return `owner_id` if the policy permits it, otherwise refuse.

    Slice 10. The same fail-closed rule `validate_route` applies to routes, for
    the party that acts rather than the route that is called. A recorded human
    acceptance is a named party taking the handoff on, and I4 says that party
    must be one the product can name.
    """
    if owner_id not in permitted_owner_ids:
        raise UnpermittedOwnerId(owner_id, sorted(permitted_owner_ids))
    return owner_id


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


def restatement_stops(level: HintLevel, outcome: RecallOutcome, repair_round: int) -> bool:
    """C6: H3 never proves comprehension; an exhausted failed ladder stops."""
    return level is HintLevel.H3 or (
        repair_round >= MAX_REPAIR_ROUNDS and outcome is RecallOutcome.NOT_RECALLED
    )


def source_candidates(text: str, forms: frozenset[str]) -> tuple[SourceSpan, ...]:
    """Recognise supported forms without normalising away source offsets."""
    candidates = set()
    for form in sorted(forms):
        pattern = r"\s+".join(re.escape(part) for part in form.split())
        if form and form[0].isascii() and form[0].isalnum():
            pattern = r"(?<!\w)" + pattern
        if form and form[-1].isascii() and form[-1].isalnum():
            pattern += r"(?!\w)"
        if pattern:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidates.add(SourceSpan(match.group(), match.start(), match.end()))
    return tuple(sorted((span for span in candidates if not any(
        other.start <= span.start and span.end <= other.end and other != span
        for other in candidates)), key=lambda span: (span.start, span.end)))


_READBACK_DOUBT = re.compile(
    r"\b(?:not|no|never|cannot|unsure|uncertain|maybe|perhaps|might|may|could|would|if|or)\b"
    r"|\b\w+n['’]t\b|\?|？|不|没|未", re.IGNORECASE)
_READBACK_BACKWARD = re.compile(
    r"\b(?:actually|forget|instead|won['’]t|can['’]t|don['’]t)\b"
    r"|^\s*(?:no|not|never)\s*[.!?;]?\s*$", re.IGNORECASE)
_READBACK_MENTIONS = {
    "action_id": re.compile(r"\b(?:go to|stay home|visit|wait|call|see the)\b", re.IGNORECASE),
    "deadline_utc": re.compile(r"\b(?:today|tomorrow|before|after|tonight|next day)\b|今天|明天", re.IGNORECASE),
    "next_owner_id": re.compile(r"\b(?:my neighbour|my neighbor|my daughter|my son|someone|she|he|they|we)\b", re.IGNORECASE),
}


def independent_uncertainty(confirmed_text: str, *, policy: PolicyFixture) -> frozenset[str]:
    """Bounded whole-answer check independent of the extractor's assertions."""
    forms = {
        "action_id": frozenset(policy.action_aliases) | policy.permitted_action_ids,
        "deadline_utc": frozenset(policy.deadline_forms),
        "next_owner_id": frozenset(policy.owner_aliases) | policy.permitted_owner_ids,
    }
    uncertain = set()
    for sentence in re.findall(r"[^.!?;]+[.!?;]?", confirmed_text):
        if _READBACK_DOUBT.search(sentence):
            if _READBACK_BACKWARD.search(sentence):
                uncertain.update(COMPARISON_FIELDS)
            for field, values in forms.items():
                if source_candidates(sentence, values):
                    uncertain.add(field)
        elif _READBACK_BACKWARD.search(sentence) and re.search(
            r"\b(?:forget|instead)\b", sentence, re.IGNORECASE):
            uncertain.update(COMPARISON_FIELDS)
        for field, mention in _READBACK_MENTIONS.items():
            grounded = source_candidates(sentence, forms[field])
            if any(not any(span.start <= hit.start() and hit.end() <= span.end
                           for span in grounded) for hit in mention.finditer(sentence)):
                uncertain.add(field)
    for field, values in forms.items():
        spans = source_candidates(confirmed_text, values)
        if field == "deadline_utc":
            resolved = {policy.deadline_forms.get(normalise(span.text)) for span in spans}
        else:
            aliases = policy.action_aliases if field == "action_id" else policy.owner_aliases
            permitted = policy.permitted_action_ids if field == "action_id" else policy.permitted_owner_ids
            resolved = {_resolve_id(span.text, aliases, permitted) for span in spans}
        if len(resolved) > 1:
            uncertain.add(field)
    return frozenset(uncertain)


def merge_field_repair(context: ReadbackContext, extracted: ExtractedPlan, *,
                       whole_answer_doubt: frozenset[str], policy: PolicyFixture,
                       now_utc: datetime, display_tz: tzinfo) -> tuple[ExtractedPlan, tuple[RetainedMatch, ...]]:
    """Borrow only grounded known matches not replaced or contradicted now."""
    if context.policy_version != policy.version:
        raise DomainError("retention policy changed")
    values = {"action_id": extracted.action_span, "deadline_utc": extracted.deadline_span,
              "next_owner_id": extracted.next_owner_span}
    uncertain = set(extracted.uncertain_fields) | set(whole_answer_doubt)
    retained = []
    for source in context.retained:
        if source.field not in COMPARISON_FIELDS:
            raise DomainError("unknown retained field")
        if not source.source_restatement_id or not source.source_confirmation_id:
            raise DomainError("retention has no grounded source")
        if source.field == "action_id":
            value = _resolve_id(source.source_span.text, policy.action_aliases, policy.permitted_action_ids)
        elif source.field == "next_owner_id":
            value = _resolve_id(source.source_span.text, policy.owner_aliases, policy.permitted_owner_ids)
        else:
            value = _resolve_deadline(source.source_span.text, now_utc, display_tz, policy.deadline_forms)
        if value is None or value != source.canonical_value:
            raise DomainError("retention source does not resolve to its value")
        if context.repair_field is None:
            continue
        if source.field == context.repair_field:
            continue
        if values.get(source.field) is not None:
            continue
        if source.field in whole_answer_doubt:
            continue
        values[source.field] = source.source_span.text
        uncertain.discard(source.field)
        retained.append(source)
    return ExtractedPlan(values["action_id"], values["deadline_utc"], values["next_owner_id"],
                         frozenset(uncertain)), tuple(retained)


def readback_confirmation(bundle: JourneyBundle, *, attempt_id: str | None,
                          parent_id: str | None) -> dict[str, object] | None:
    """Only the latest new explicit confirmation can authorise a check."""
    current = None
    for kind, payload, _ in bundle.events:
        if kind != "words_confirmed":
            continue
        try:
            event = json.loads(payload)
        except (ValueError, TypeError):
            raise JourneyUnavailable("invalid words confirmation") from None
        if not isinstance(event, dict) or event.get("schema") != "confirmed-words-v1":
            raise JourneyUnavailable("invalid words confirmation")
        if event.get("disposition_version") != bundle.snapshot.disposition.version or event.get("attempt_id") != attempt_id:
            continue
        if event.get("episode_id") != bundle.episode_id or event.get("policy_version") != bundle.policy.version:
            raise JourneyUnavailable("confirmation policy or episode mismatch")
        if (not isinstance(event.get("text"), str) or not event["text"].strip() or len(event["text"]) > 2048
                or not isinstance(event.get("confirmation_id"), str) or not event["confirmation_id"]):
            raise JourneyUnavailable("invalid confirmed words")
        current = event
    return current if current is not None and current.get("parent_id") == parent_id else None


def readback_context_current(context: ReadbackContext, bundle: JourneyBundle, *, now_utc: datetime) -> bool:
    """Fresh final fence. Time comes from the caller, never a domain clock."""
    disposition = bundle.snapshot.disposition
    if disposition is None or context.episode_id != bundle.episode_id:
        return False
    if context.disposition_version != disposition.version or context.policy_version != disposition.policy_version:
        return False
    if bundle.revision != context.claim_revision:
        return False
    if bundle.snapshot.flow_stop_reason is not None or bundle.snapshot.expiry_event_id is not None:
        return False
    if now_utc >= disposition.clinical_deadline_utc:
        return False
    journey = derive_journey(bundle, now_utc=now_utc)
    if context.attempt_id != journey.flow.readback_attempt_id or context.parent_id != journey.flow.latest_restatement_id:
        return False
    if context.effective_hint != journey.flow.effective_hint or context.effective_hint is HintLevel.H3:
        return False
    if context.completed_repairs != journey.flow.completed_repairs or context.completed_repairs >= MAX_REPAIR_ROUNDS:
        return False
    confirmed = readback_confirmation(bundle, attempt_id=context.attempt_id, parent_id=context.parent_id)
    return confirmed is not None and confirmed["confirmation_id"] == context.confirmation_id and confirmed["text"] == context.confirmed_text


def grounded_parent_matches(bundle: JourneyBundle, *, attempt_id: str,
                            parent_id: str | None) -> tuple[RetainedMatch, ...]:
    """Legacy rows have unknown provenance and supply no retained permission."""
    if parent_id is None:
        return ()
    rows = {row.restatement_id: row for row in bundle.restatements}
    parent = rows.get(parent_id)
    if parent is None or parent.provenance is None:
        return ()
    if parent.disposition_version != bundle.snapshot.disposition.version or parent.provenance.get("attempt_id") != attempt_id:
        raise JourneyUnavailable("retention parent is not this chain")
    ancestors = set()
    node = parent
    while node is not None:
        if node.restatement_id in ancestors:
            raise JourneyUnavailable("cyclic retention chain")
        ancestors.add(node.restatement_id)
        previous = node.provenance.get("parent_id") if node.provenance else None
        node = rows.get(previous) if previous is not None else None
        if previous is not None and node is None:
            raise JourneyUnavailable("missing retention ancestor")
    confirmations = {}
    for kind, payload, _ in bundle.events:
        if kind == "words_confirmed":
            event = json.loads(payload)
            confirmations[event["confirmation_id"]] = event
    result = []
    raw_keys = {"action_id": "action_span", "deadline_utc": "deadline_span", "next_owner_id": "next_owner_span"}
    for field in COMPARISON_FIELDS:
        if field not in parent.comparison.matched:
            continue
        borrowed = next((r for r in parent.provenance.get("retained", []) if r["field"] == field), None)
        source_id = borrowed["source_restatement_id"] if borrowed else parent.restatement_id
        source = rows.get(source_id)
        if source_id not in ancestors or source.provenance is None:
            raise JourneyUnavailable("retention source is not an ancestor")
        meta = source.provenance
        if (source.disposition_version != bundle.snapshot.disposition.version or meta.get("policy_version") != bundle.policy.version
                or meta.get("attempt_id") != attempt_id or field not in source.comparison.matched):
            raise JourneyUnavailable("retention source binding changed")
        confirmation_id = meta.get("confirmation_id")
        event = confirmations.get(confirmation_id)
        if (event is None or event.get("episode_id") != bundle.episode_id or event.get("attempt_id") != attempt_id
                or event.get("disposition_version") != source.disposition_version or event.get("parent_id") != meta.get("parent_id")):
            raise JourneyUnavailable("retention source confirmation changed")
        span_data = meta["raw"][raw_keys[field]]
        if not isinstance(span_data, dict):
            raise JourneyUnavailable("retention has no source span")
        span = SourceSpan(**span_data)
        if (type(span.start) is not int or type(span.end) is not int or not 0 <= span.start < span.end <= len(event["text"])
                or event["text"][span.start:span.end] != span.text):
            raise JourneyUnavailable("retention offsets are not grounded")
        if field == "action_id":
            value = _resolve_id(span.text, bundle.policy.action_aliases, bundle.policy.permitted_action_ids)
        elif field == "next_owner_id":
            value = _resolve_id(span.text, bundle.policy.owner_aliases, bundle.policy.permitted_owner_ids)
        else:
            value = _resolve_deadline(span.text, source.created_at, timezone(timedelta(hours=8)), bundle.policy.deadline_forms)
        if value is None:
            raise JourneyUnavailable("retention value is unknown")
        result.append(RetainedMatch(field, value, source_id, confirmation_id, span))
    return tuple(result)


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


def validate_adapter_evidence(record: EvidenceRecord) -> None:
    """This build has only simulated adapters, with no real artefact verifier.

    A caller's label or source reference cannot establish authenticity. Trusted
    repository fixtures can exercise documented rendering; adapter inputs cannot.
    """
    if not record.simulated:
        raise PolicyViolation("non-simulated evidence has no verified ingestion path")


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


def handoff_is_transfer(accepted_by: str | None, scope: str | None, owner: str) -> bool:
    """An acceptance must cover this handoff and move work off the patient."""
    return scope == "handoff" and bool(accepted_by) and accepted_by not in {"patient", owner}


def _has_handoff_acceptance(snapshot: EpisodeSnapshot) -> bool:
    return (
        snapshot.human_acceptance_id is not None
        and snapshot.disposition is not None
        and handoff_is_transfer(snapshot.accepted_by, snapshot.accepted_scope,
                                snapshot.disposition.next_owner_id)
    )


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
    4. A recorded successful escalation: handed to a named human path, deadline still
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
    elif _has_handoff_acceptance(snapshot):
        closure = ClosureState.CLOSED_WITH_EVIDENCE
    elif snapshot.escalation_id is not None and snapshot.escalation_outcome in {"handed_off", "handed_over"}:
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

    A relevant acceptance names its accepting party. A successful escalation
    moves the obligation to the named human path. Failed or unconfirmed records
    leave the disposition's own `next_owner_id` responsible.
    """
    if _has_handoff_acceptance(snapshot):
        return snapshot.accepted_by
    if snapshot.escalation_id is None or snapshot.escalation_outcome not in {"handed_off", "handed_over"}:
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

    All four closure states have approved renderings in `02-architecture.md`
    section 7: the unresolved and expired screens (re-approved 2 October 2026)
    and the three closure renderings (approved 8 October 2026). The two resolved
    cases do not share line 1: a recorded acceptance is a promise, not evidence
    (F4), so "Help is arranged." waits for `care_evidenced` and an acceptance
    alone says "Someone has agreed to help.".
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
        if closure.care_evidenced:
            # Quoted from `02-architecture.md` section 7, approved 8 October 2026.
            # "Arranged" appears only when the evidence axis is documented.
            return (
                "Help is arranged.",
                "Nothing more is needed from you.",
                f"It is set for {deadline_display}.",
                f"If that does not happen, call {route_display}.",
            )
        # A recorded human acceptance with no documented evidence. Same approval:
        # the acceptance is the promise, so line 1 says "agreed", and only the
        # evidence axis lets a surface say care happened (F4, Closure s2.2).
        return (
            "Someone has agreed to help.",
            "You do not need to act now.",
            f"It is set for {deadline_display}.",
            f"If that does not happen, call {route_display}.",
        )

    if closure.closure is ClosureState.ESCALATED_TO_HUMAN:
        # Quoted from `02-architecture.md` section 7, approved 8 October 2026.
        # F6: line 1 names the human path the handoff went to, which
        # `derive_closure` carries as `action_owner_id`. An id with no approved
        # display refuses rather than printing an internal identifier.
        human_path_display = policy_text.route_display_by_id.get(closure.action_owner_id)
        if human_path_display is None:
            raise MissingDisplayText(closure.action_owner_id)
        return (
            f"We have passed this to {human_path_display}.",
            "You do not need to act now.",
            f"It is set for {deadline_display}.",
            f"If that does not work, call {route_display}.",
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


def _require_member(
    value: str,
    members: Sequence[object],
    error: type[PolicyViolation],
) -> str:
    """One closed-vocabulary lookup, shared by the three parsers below.

    `value` is compared against the members' own `value` strings rather than
    passed to an enum constructor, because the constructor's `ValueError` is the
    defect this exists to remove: a 500 is not a refusal, and a caller cannot
    route to the human path from a traceback.
    """
    permitted = [getattr(member, "value") for member in members]
    if value not in permitted:
        raise error(value, permitted)
    return value


def require_hint_level(value: str) -> HintLevel:
    """A caller-supplied hint level, or a `PolicyViolation`.

    `H9` is not a level, and neither is a level the ladder does not name. The
    permitted set is reported so the refusal is actionable rather than bare.
    """
    return HintLevel(_require_member(value, tuple(HintLevel), UnpermittedHintEvent))


def require_hint_event_kind(value: str) -> HintEventKind:
    """A caller-supplied hint event kind, or a `PolicyViolation`.

    `auto_hide` is the case that matters: it is not in the vocabulary, and it
    must be refused rather than silently accepted (C8). An event kind that hid
    the card without a patient action would be a timer by another name.
    """
    return HintEventKind(
        _require_member(value, tuple(HintEventKind), UnpermittedHintEvent)
    )


def require_input_mode(value: str) -> InputMode:
    """A caller-supplied input mode, or a `PolicyViolation`.

    The mode decides whether a transcript confirmation is required before
    scoring, so a mode outside the vocabulary is a gap in the Gate 1 ordering
    rule and must stop rather than default.
    """
    return InputMode(_require_member(value, tuple(InputMode), PolicyViolation))

class JourneyUnavailable(DomainError):
    """The current reader cannot safely project this stored journey."""


def derive_journey(bundle: JourneyBundle, *, now_utc: datetime) -> JourneyProjection:
    """Select a screen from one stored snapshot; never perform or infer care."""
    if not bundle.episode_id or type(bundle.revision) is not int or not 0 <= bundle.revision <= 9007199254740991:
        raise JourneyUnavailable("invalid journey identity or revision")
    base = JourneyProjection(
        episode_id=bundle.episode_id, revision=bundle.revision,
        as_of_utc=now_utc, flow=FlowView(), text={}, fixture_label="",
    )
    pending = _journey_pending(bundle.commands)
    disposition = bundle.snapshot.disposition
    if disposition is None:
        created = any(r["phase"] == "completed" and r["kind"] == "create" and
                      r["terminal_state"] == "applied" for r in bundle.commands)
        return replace(base, flow=replace(base.flow, interpretation="pending" if pending else "idle"),
                       commands=_journey_offers(("select_example",) if created else (), pending=pending))
    policy, text = bundle.policy, bundle.policy_text
    if policy is None or text is None or policy.version != disposition.policy_version or text.policy_version != disposition.policy_version:
        raise JourneyUnavailable("recorded policy unavailable")
    if disposition.action_id not in policy.permitted_action_ids:
        raise JourneyUnavailable("recorded action is outside its policy")
    validate_owner(disposition.next_owner_id, policy.permitted_owner_ids)
    validate_route(disposition.fallback_route_id, policy.permitted_route_ids)
    # This upgrade has one immutable allowlisted fixture bundle. Unknown bundles
    # refuse; a configured replacement cannot rename a recorded action.
    action = JOURNEY_ACTION_TEXT.get(disposition.policy_version, {}).get(disposition.action_id)
    deadline = text.deadline_display_by_version.get(disposition.version)
    original_owner = text.owner_display_by_id.get(disposition.next_owner_id)
    fallback = text.route_display_by_id.get(disposition.fallback_route_id)
    if not action or not deadline or not original_owner or not fallback:
        raise JourneyUnavailable("approved plan display unavailable")
    # The only approved relative-day display is the stored local day. No new
    # date sentence or shifted deadline is invented on a later-day resume.
    display_tz = timezone(timedelta(hours=8))
    if now_utc.tzinfo is None or disposition.clinical_deadline_utc.astimezone(display_tz).date() != now_utc.astimezone(display_tz).date():
        raise JourneyUnavailable("approved date display unavailable")
    closure = derive_closure(bundle.snapshot, now_utc)
    current_owner = None
    if closure.action_owner_id is not None:
        current_owner = text.owner_display_by_id.get(closure.action_owner_id) or text.route_display_by_id.get(closure.action_owner_id)
        if current_owner is None:
            raise JourneyUnavailable("current owner display unavailable")
    original_owner = "You" if disposition.next_owner_id == text.self_owner_id else original_owner
    current_owner = "You" if closure.action_owner_id == text.self_owner_id else current_owner
    plan = PlanView(disposition.version, disposition.policy_version, disposition.action_id,
        action, disposition.clinical_deadline_utc, deadline, "Asia/Singapore",
        disposition.next_owner_id, original_owner, closure.action_owner_id, current_owner,
        disposition.fallback_route_id, fallback)
    snapshot = bundle.snapshot
    outcome = OutcomeView(closure.execution, closure.evidence, closure.closure,
        closure.care_evidenced, snapshot.accepted_by, snapshot.accepted_scope,
        snapshot.escalated_human_path, snapshot.escalation_outcome, snapshot.expiry_event_id is not None)
    rounds = tuple(r for r in bundle.restatements if r.disposition_version == disposition.version)
    for row in rounds:
        matched, mismatched, uncertain = row.comparison.matched, row.comparison.mismatched, row.comparison.uncertain
        if matched | mismatched | uncertain != frozenset(COMPARISON_FIELDS):
            raise JourneyUnavailable("incomplete comparison partition")
        if matched & mismatched or matched & uncertain or mismatched & uncertain:
            raise JourneyUnavailable("overlapping comparison partition")
        grounded = compare_plan(disposition, row.extracted, policy=policy,
                                now_utc=row.created_at, display_tz=display_tz)
        for field in COMPARISON_FIELDS:
            if field in matched and field not in grounded.matched:
                raise JourneyUnavailable("ungrounded recorded match")
            if field in mismatched and field not in grounded.mismatched:
                raise JourneyUnavailable("ungrounded recorded mismatch")
        recalled = row.outcome in {RecallOutcome.RECALL_UNAIDED, RecallOutcome.RECALL_SCAFFOLDED, RecallOutcome.RECALL_CUED}
        if recalled != (row.comparison.is_clean() and row.hint_level is not HintLevel.H3):
            raise JourneyUnavailable("inconsistent recall outcome")
    latest = rounds[-1] if rounds else None
    started = None
    barrier = False
    hint = HintLevel.H1
    visible = False
    interpretation = "idle"
    for kind, payload, _ in bundle.events:
        if kind not in {"readback_started", "hint_event", "barrier_recorded", "interpretation_unavailable"}:
            continue
        try:
            event = json.loads(payload)
        except (ValueError, TypeError):
            legacy = re.fullmatch(r"version=(\d+) permitted_route=([A-Za-z0-9_-]+) stopped_at_human_path=([01])", payload) if kind == "barrier_recorded" else None
            if legacy is None:
                raise JourneyUnavailable("invalid journey event")
            event = {"disposition_version": int(legacy[1]), "permitted_route_id": legacy[2]}
        if not isinstance(event, dict):
            raise JourneyUnavailable("invalid journey event")
        if event.get("disposition_version", disposition.version) != disposition.version:
            continue
        if kind == "readback_started":
            started = event.get("readback_attempt_id")
            if not isinstance(started, str) or not started:
                raise JourneyUnavailable("invalid readback identity")
        elif kind == "hint_event":
            level = require_hint_level(event.get("hint_level"))
            if "disposition_version" not in event and disposition.version != 1:
                continue
            visible = require_hint_event_kind(event.get("kind")) is HintEventKind.SHOWN
            if level is HintLevel.H3:
                hint = HintLevel.H3
            elif hint is not HintLevel.H3 and (visible or level is HintLevel.H2):
                hint = HintLevel.H2
        elif kind == "barrier_recorded":
            barrier = event.get("permitted_route_id") == "fictional_provider"
        elif kind == "interpretation_unavailable":
            interpretation = "unavailable"
    stopped = snapshot.flow_stop_reason is not None
    repair_field = None
    completed_repairs = latest.repair_round if latest else 0
    if latest is not None:
        if latest.hint_level is HintLevel.H3 or (latest.hint_level is HintLevel.H2 and hint is not HintLevel.H3):
            hint = latest.hint_level
        if interpretation != "unavailable":
            interpretation = "uncertain" if latest.comparison.uncertain else "scored"
        if "deadline_utc" in latest.comparison.mismatched and completed_repairs < MAX_REPAIR_ROUNDS:
            repair_field = "deadline_utc"
    step, question, allowed = "plan", None, ("readback_started", "show_plan", "hide_plan", "grant_share", "revoke_share")
    if closure.care_evidenced:
        step, allowed = "documented", ()
    elif closure.closure is ClosureState.EXPIRED_UNRESOLVED:
        step, allowed = "expired", ("revoke_share",)
    elif closure.closure is ClosureState.CLOSED_WITH_EVIDENCE:
        step, allowed = "accepted", ()
    elif closure.closure is ClosureState.ESCALATED_TO_HUMAN:
        step, allowed = "handoff", ()
    elif stopped:
        step, allowed = "stopped", ("show_plan", "hide_plan", "grant_share", "revoke_share")
    elif closure.execution is ExecutionStatus.FAILED or snapshot.escalation_outcome == "failed":
        step, allowed = "unresolved", ("show_plan", "hide_plan", "grant_share", "revoke_share")
    elif closure.execution is ExecutionStatus.ACKNOWLEDGED or snapshot.escalation_id is not None:
        # Contact/acknowledgement cannot choose a success or failure heading.
        step, allowed = "plan", ("show_plan", "hide_plan", "revoke_share")
    elif closure.execution is ExecutionStatus.ATTEMPTED:
        step, allowed = "permission", ("show_plan", "hide_plan", "revoke_share")
    elif barrier:
        step, allowed = "permission", ("grant_share", "decline_share", "revoke_share", "show_plan", "hide_plan")
        if bundle.consent_granted:
            allowed += ("request",)
        question = QuestionView("permission", "May we share your plan?", ())
    elif latest is not None and latest.comparison.is_clean() and latest.hint_level is not HintLevel.H3:
        step, allowed = "barrier", ("select_barrier", "show_plan", "hide_plan")
        question = QuestionView("barrier", "What makes it difficult?", (
            ChoiceView("booking", "Finding an appointment"), ChoiceView("transport", "Getting there"),
            ChoiceView("other", "Something else")))
    elif started is not None:
        step = "repair" if repair_field else "readback"
        allowed = ("confirm_words", "repair_words" if latest is not None else "score_words", "show_plan", "hide_plan", "h3")
        question = QuestionView(step, "When will you go?" if repair_field else "What will you do, when, and who will act?", ())
    if pending:
        question, allowed, interpretation = None, (), "pending"
    confirmed = readback_confirmation(bundle, attempt_id=started, parent_id=latest.restatement_id if latest else None)
    extraction_pending = any(r["phase"] == "claimed" and r["kind"] in {"score_words", "repair_words"}
        and not any(t["operation_id"] == r["operation_id"] and t["phase"] == "completed" for t in bundle.commands)
        for r in bundle.commands)
    if extraction_pending and closure.closure is ClosureState.OPEN:
        allowed = ("show_plan", "hide_plan") if stopped else ("show_plan", "hide_plan", "h3", "supersede_extraction")
    elif not pending and step in {"readback", "repair"}:
        allowed = tuple(k for k in allowed if k not in {"score_words", "repair_words"} or confirmed is not None)
    flow = FlowView(stopped, snapshot.flow_stop_reason, disposition.version if stopped else None,
        started, latest.restatement_id if latest else None, repair_field, completed_repairs,
        hint, visible, interpretation)
    redacted = step in {"readback", "repair"}
    lines = () if redacted else patient_lines(snapshot, closure, text)
    screen_text = dict(JOURNEY_SCREEN_TEXT[step])
    if step == "permission" and closure.execution is ExecutionStatus.ATTEMPTED:
        screen_text = {"heading": "May we share your plan?", "status": "No reply yet.", "notice": "Simulated request."}
    if step == "handoff" and snapshot.escalated_human_path != "nurse_line":
        screen_text = {"heading": lines[0], "notice": "Simulated handoff. Care is not confirmed."}
    if visible:
        screen_text.update(revealed_heading="Your example plan", reveal_action_label="What to do",
                           reveal_deadline_label="Before", reveal_owner_label="Who acts")
    if not stopped and closure.closure is ClosureState.OPEN:
        if interpretation == "pending":
            screen_text["feedback"] = "Loading. Nothing is confirmed yet."
        elif interpretation == "unavailable":
            screen_text["feedback"] = "We could not check that answer just now. Your plan has not changed."
        elif interpretation == "uncertain":
            screen_text["feedback"] = "We could not confirm that. Try different words, or show your plan."
    if step in {"readback", "repair"}:
        screen_text.update(input_label="Your words", input_help="Demo: use made-up words only.",
            input_error="Add your words, or show your plan.", review_label="Review my answer",
            preview_label="Preview only. Not checked or saved.", answer_label="Your answer",
            confirmation_label="Save and check these words",
            confirmation_help="This saves the words shown above and checks them against your example plan.")
        if latest is not None and not latest.comparison.is_clean() and repair_field is None and interpretation not in {"pending", "unavailable"}:
            screen_text["feedback"] = "We could not confirm that. Try different words, or show your plan."
        if repair_field is not None and hint in {HintLevel.H2, HintLevel.H3}:
            screen_text.update(repair_example_label="Example answer:", repair_answer=latest.extracted.deadline_span or "",
                repair_plan_label="The plan says:", repair_deadline="before " + deadline)
        if confirmed is not None:
            screen_text["saved_words"] = confirmed["text"]
        if extraction_pending:
            screen_text["feedback"] = "Checking your saved words. Your plan has not changed."
        if confirmed is not None:
            screen_text.update(retry_label="Check these words again",
                retry_help="This ends any previous check of these saved words and starts a new check.")
    if any(k in allowed for k in ("show_plan", "hide_plan")):
        screen_text.update(show_label="Show my plan", hide_label="Back to my answer")
    if "readback_started" in allowed:
        screen_text["readback_label"] = "Say it in your words"
    return replace(base, disposition_version=disposition.version, policy_version=disposition.policy_version,
        plan_redacted=redacted, plan=None if redacted else plan, outcome=outcome, flow=flow,
        step=step, question=question, commands=_journey_offers(allowed, pending=pending),
        lines=lines, text=screen_text, revealed_plan=plan if visible else None,
        simulated=text.simulated, fixture_label=text.fixture_label)


# Exact approved fixture wording, pinned to the recorded version. This is a
# closed catalog, not a generated action or a configured-policy fallback.
JOURNEY_ACTION_TEXT = {"fixture-provisional-0": {
    "attend_same_day_review": "Go to the fictional provider's same-day review.",
}}
JOURNEY_SCREEN_TEXT = {
    "plan": {"heading": "Your next step", "action_label": "What to do", "deadline_label": "Before", "owner_label": "Who acts"},
    "readback": {"heading": "What is your plan?"},
    "repair": {"heading": "Let’s check the time"},
    "barrier": {"heading": "What makes it difficult?", "description": "Choose one."},
    "permission": {"heading": "May we share your plan?", "description": "With the fictional provider, to request an appointment.", "shared": "Shared: the action and deadline. No caregiver message."},
    "unresolved": {"heading": "The request did not work"},
    "stopped": {"heading": "Let’s stop the questions"},
    "expired": {"heading": "Your plan still needs action"},
    "accepted": {"heading": "Your daughter agreed", "notice": "Simulated agreement. Care is not confirmed."},
    "handoff": {"heading": "Handed to the nurse line", "notice": "Simulated handoff. Care is not confirmed."},
    "documented": {"heading": "Help is arranged."},
}
IMPLEMENTED_JOURNEY_COMMANDS = frozenset({"select_example", "readback_started", "confirm_words", "score_words",
    "repair_words", "show_plan", "hide_plan", "h3", "supersede_extraction"})


def _journey_pending(rows: tuple[object, ...]) -> bool:
    completed = {r["operation_id"] for r in rows if r["phase"] == "completed"}
    return any(r["phase"] == "claimed" and r["operation_id"] not in completed for r in rows)


def _journey_offers(kinds: tuple[str, ...], *, pending: bool) -> tuple[CommandOffer, ...]:
    if pending and not set(kinds) <= {"show_plan", "hide_plan", "h3", "supersede_extraction"}:
        return ()
    return tuple(CommandOffer(kind, kind, ("scripted-appointment",) if kind == "select_example" else ())
                 for kind in kinds if kind in IMPLEMENTED_JOURNEY_COMMANDS)
