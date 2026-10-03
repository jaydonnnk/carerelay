"""FastAPI routes: Slice 1 (tracer bullet) plus Slice 4 (PlanBack).

Slice 1 wired two routes end to end against a hardcoded episode: no database, no
domain logic, no coordinator. Those two routes are untouched here and still serve
the tracer bullet.

Slice 4 adds the PlanBack routes: `/intake`, `/transcript-confirmations`,
`/hint-events`, `/restatements` and `/restatements/{id}/repairs`. **This file
carries no clinical decision.** Every decision is in `domain`, reached through
`service`; the routes validate input, call one use case, and map typed errors to
HTTP. That split is D2's, and it is what lets the route layer be the one file in
the project with no rules in it.

`02-architecture.md` 3.1 lists the full route surface. Later slices add routes in
build order: the API is grown slice by slice, never filled in horizontally.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from carerelay import __version__
from carerelay.coordinator import (
    CoordinatorUnavailable,
    LocalSimulationCoordinator,
)
from carerelay.demo import fixture
from carerelay.domain.rules import PolicyViolation, UnpermittedTransition
from carerelay.domain.models import (
    CallbackResult,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    Origin,
)
from carerelay.service import (
    ActionOutcome,
    BarrierOutcome,
    CallbackOutcome,
    ConsentRequired,
    EpisodeAlreadyAssessed,
    EpisodeService,
    EscalationOutcome,
    IntakeNotRecognised,
    NoAttemptForRoute,
    NoDispositionYet,
    OriginNotWired,
    ReassessmentResult,
    RepairCapReached,
    RestatementOutcome,
    ScenarioClock,
    StaleRestatement,
    SystemClock,
    UnconfirmedTranscript,
)
from carerelay.simulated_provider import ScriptedProvider
from carerelay.state import (
    CLINICAL_SCOPE,
    EpisodeNotFound,
    RestatementNotFound,
    StateError,
    open_store,
)
from carerelay.tools import McpTools

app = FastAPI(
    title="CareRelay",
    version=__version__,
    description=(
        "SIMULATED RESEARCH DEMONSTRATION — not clinical advice, not a medical "
        "device, not validated for patient use."
    ),
)

# Slice 1 renders one patient page that links `/static/style.css`. The file has
# been a declared Slice 1 deliverable since the tracer bullet, but nothing served
# it, so the page rendered unstyled and `GET /static/style.css` answered 404. The
# Slice 6 adversarial review found it. Mounted here so the declared link resolves.
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
    name="static",
)

# Slice 1 only: one in-memory episode, used by the two tracer-bullet routes.
_OPEN_EPISODES: set[str] = set()


# ---------------------------------------------------------------------------
# Slice 4 wiring
# ---------------------------------------------------------------------------


def _clock() -> SystemClock | ScenarioClock:
    """The injected clock. `APP_CLOCK=scenario|system`, scenario by default.

    Scenario is the demo default because the fixture's deadline display is "6pm
    today": under a wall clock it would drift as the real day changed, and the
    walkthrough would stop matching its own fixture.
    """
    if os.getenv("APP_CLOCK", "scenario").strip().casefold() == "system":
        return SystemClock()
    return ScenarioClock(fixture.SCENARIO_NOW_UTC)


def _database_path() -> str:
    """`APP_DATABASE_URL`, or an in-memory database for the local demo.

    Slice 7 sets the mounted persistent disk path on Render. Until then the demo
    runs in memory: the record is still real SQL with real triggers and real
    transactions, but it does not survive a restart, and no claim is made that it
    does.
    """
    return os.getenv("APP_DATABASE_URL") or ":memory:"


#: SQLite has no way to make one connection safe for concurrent use, and FastAPI
#: serves synchronous routes from a thread pool. The store is therefore opened
#: with `check_same_thread=False` and every use case runs under this lock, so a
#: second request waits rather than trying to begin a transaction inside another
#: one. `02-architecture.md` section 4.1's `BEGIN IMMEDIATE` still handles the
#: genuinely concurrent case, which is a *second connection* to the same file.
_DB_LOCK = threading.Lock()

_STORE = open_store(_database_path(), check_same_thread=False)

#: Slice 6. The coordinator reaches the world only through this surface, and the
#: surface reaches the provider, which is a labelled local simulation. The
#: `origin` every action outcome carries comes from here, so it cannot be set
#: per request: see `OriginNotWired` in `service.py`.
_TOOLS = McpTools(_STORE, policy=fixture.policy(), provider=ScriptedProvider())

_SERVICE = EpisodeService(
    _STORE,
    coordinator=LocalSimulationCoordinator(_TOOLS),
    clock=_clock(),
    policy=fixture.policy(),
    display_tz=fixture.DISPLAY_TZ,
    disposition_factory=fixture.disposition,
    bound_complaint=fixture.BOUND_COMPLAINT,
    policy_provenance=(
        "PROVISIONAL: non-clinical placeholder, authored rather than sourced. "
        "Option C was dropped on 1 October 2026 after the source check cleared "
        "no source; the wording names no symptom, urgency, threshold or real "
        "facility and asserts no clinical claim (03-program-design.md 6.2)."
    ),
)


def get_service() -> EpisodeService:
    """The service behind every Slice 4 route.

    A FastAPI dependency rather than a direct module reference, so a test can
    supply a service on a fresh in-memory database. That is not test
    convenience: the clinical record is append-only, so a test suite that shares
    one database cannot be reset, and the second intake would be refused as a
    repeat assessment.
    """
    return _SERVICE

#: The degraded-state message for a coordinator that cannot answer. Not approved
#: clinical copy: none exists for this state, and this is authored so the flow
#: stops with words rather than with a blank screen. It needs a Gate 1 touch.
COORDINATOR_FALLBACK_TEXT = (
    "We could not check that answer just now. Your plan has not changed."
)


class EpisodeCreated(BaseModel):
    episode_id: str
    persona: str
    policy_version: str
    simulated: bool
    fixture_label: str
    note: str


class PatientProjection(BaseModel):
    """The patient's four lines, plus the label the patient must be able to see.

    `simulated` and `fixture_label` are inside the projection on purpose, not in
    page chrome: D11 requires the simulated label to travel with the clinical
    data, because a projection that omits it is a false-completion path.
    """

    episode_id: str
    lines: list[str]
    simulated: bool
    fixture_label: str


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/api/episodes", response_model=EpisodeCreated, tags=["episodes"])
def create_episode(
    service: EpisodeService = Depends(get_service),
) -> EpisodeCreated:
    """Create the demo episode.

    Does **not** write a disposition — that follows assessment (`02-architecture.md`
    3.1, 5.1), which Slice 4 adds at `/intake`. Slice 1 has no assessment, so it
    has no disposition.

    Slice 4 does add the **store** row, because the PlanBack routes need the
    episode to exist as real state. That is idempotent, and it still writes no
    disposition.
    """
    _OPEN_EPISODES.add(fixture.DEMO_EPISODE_ID)
    with _DB_LOCK:
        service.ensure_episode(fixture.DEMO_EPISODE_ID, "fictional older adult")
    return EpisodeCreated(
        episode_id=fixture.DEMO_EPISODE_ID,
        persona=fixture.DEMO_EPISODE_ID and "fictional older adult",
        policy_version=fixture.POLICY_VERSION,
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
        note=(
            "Slice 1 tracer bullet: hardcoded. No disposition is written, no "
            "database exists on this path, and the fixture wording is a "
            "provisional non-clinical placeholder, authored rather than sourced. "
            "Option C was dropped on 1 October 2026; the wording asserts no "
            "clinical claim."
        ),
    )


@app.get(
    "/api/episodes/{episode_id}",
    response_model=PatientProjection,
    tags=["episodes"],
)
def get_episode(episode_id: str) -> PatientProjection:
    """The patient projection — four lines and the simulated label."""
    if episode_id not in _OPEN_EPISODES:
        raise HTTPException(status_code=404, detail="episode not found")
    return PatientProjection(
        episode_id=episode_id,
        lines=list(fixture.demo_lines().as_tuple()),
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def patient_page(episode_id: str = fixture.DEMO_EPISODE_ID) -> HTMLResponse:
    """The patient screen. Server-rendered, text-first, no build step.

    The label is rendered as visible text at the top of the page. Nothing on this
    page hides itself or advances on a timer.
    """
    lines = fixture.demo_lines()
    body = "\n".join(
        f'      <li class="line">{line}</li>' for line in lines.as_tuple()
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CareRelay</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <main class="screen">
    <p class="fixture-label" role="note">{fixture.FIXTURE_LABEL}</p>
    <h1 class="screen-title">Your plan</h1>
    <ul class="lines">
{body}
    </ul>
    <form class="hide-control" method="get" action="/">
      <button type="submit" class="hide-button">Hide the plan</button>
    </form>
  </main>
</body>
</html>"""
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# Slice 4: PlanBack
# ---------------------------------------------------------------------------


class IntakeRequest(BaseModel):
    confirmed_text: str


class IntakeResponse(BaseModel):
    episode_id: str
    disposition_version: int
    action_id: str
    deadline_utc: str
    next_owner_id: str
    fallback_route_id: str
    simulated: bool
    fixture_label: str


class TranscriptConfirmationRequest(BaseModel):
    corrected_text: str


class TranscriptConfirmationResponse(BaseModel):
    episode_id: str
    confirmation_id: str


class HintEventRequest(BaseModel):
    hint_level: str
    event: str
    dwell_seconds: float | None = None


class HintEventResponse(BaseModel):
    """The resulting card state, and nothing else.

    There is deliberately no `dwell_seconds` here: it is recorded for the judge
    ledger and must never reach the patient surface (`PLAN.md` 5.2.1, C8).
    """

    episode_id: str
    hint_level: str
    card_visible: bool


class RestatementRequest(BaseModel):
    text: str
    hint_level: str
    input_mode: str = "text"
    transcript_confirmation_id: str | None = None
    dwell_seconds: float | None = None


class RestatementResponse(BaseModel):
    restatement_id: str
    understood: bool
    mismatches: list[str]
    uncertain: list[str]
    outcome: str
    repair_round: int
    next_repair_field: str | None
    routes_to_human_path: bool
    human_path_route_id: str | None
    simulated: bool
    fixture_label: str


def _restatement_body(outcome: RestatementOutcome) -> RestatementResponse:
    return RestatementResponse(
        restatement_id=outcome.restatement_id,
        understood=outcome.understood,
        mismatches=sorted(outcome.comparison.mismatched),
        uncertain=sorted(outcome.comparison.uncertain),
        outcome=outcome.outcome.value,
        repair_round=outcome.repair_round,
        next_repair_field=outcome.next_repair_field,
        routes_to_human_path=outcome.routes_to_human_path,
        human_path_route_id=outcome.human_path_route_id,
        simulated=outcome.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )


def _coordinator_down() -> HTTPException:
    """503, with a text fallback and an explicit `scored: False`.

    The flow stops at the current question (`02-architecture.md` section 8). The
    response refuses to look like a scored round, because a 200 carrying empty
    mismatches would read as "you understood your plan" and would be a false
    completion of exactly the kind the product exists to prevent.
    """
    return HTTPException(
        status_code=503,
        detail={
            "detail": "the coordinator could not answer, so nothing was scored",
            "text_fallback": COORDINATOR_FALLBACK_TEXT,
            "scored": False,
        },
    )


@app.post(
    "/api/episodes/{episode_id}/intake",
    response_model=IntakeResponse,
    tags=["planback"],
)
def intake(
    episode_id: str,
    body: IntakeRequest,
    service: EpisodeService = Depends(get_service),
) -> IntakeResponse:
    """The fixture-bound assessment. Issues the preauthored plan, or stops.

    A complaint this fixture is not bound to stops at the human path with 422.
    No disposition is derived from free text, and none is written for an
    unrecognised complaint (D7).
    """
    try:
        with _DB_LOCK:
            disposition = service.intake(episode_id, body.confirmed_text)
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except EpisodeAlreadyAssessed as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except IntakeNotRecognised as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": str(exc),
                "stopped_at": "human_path",
            },
        )
    return IntakeResponse(
        episode_id=episode_id,
        disposition_version=disposition.version,
        action_id=disposition.action_id,
        deadline_utc=disposition.clinical_deadline_utc.isoformat(),
        next_owner_id=disposition.next_owner_id,
        fallback_route_id=disposition.fallback_route_id,
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.post(
    "/api/episodes/{episode_id}/transcript-confirmations",
    response_model=TranscriptConfirmationResponse,
    tags=["planback"],
)
def confirm_transcript(
    episode_id: str,
    body: TranscriptConfirmationRequest,
    service: EpisodeService = Depends(get_service),
) -> TranscriptConfirmationResponse:
    """Confirm or correct a transcript, **before** any evaluation.

    The returned id is a digest of the text, so a restatement can be required to
    be the very string that was confirmed.
    """
    try:
        with _DB_LOCK:
            confirmation_id = service.confirm_transcript(
                episode_id, body.corrected_text
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    return TranscriptConfirmationResponse(
        episode_id=episode_id, confirmation_id=confirmation_id
    )


@app.post(
    "/api/episodes/{episode_id}/hint-events",
    response_model=HintEventResponse,
    tags=["planback"],
)
def record_hint_event(
    episode_id: str,
    body: HintEventRequest,
    service: EpisodeService = Depends(get_service),
) -> HintEventResponse:
    """Record a hint event. The card is hidden only by `patient_hid` (C8)."""
    try:
        with _DB_LOCK:
            state = service.record_hint_event(
                episode_id, body.hint_level, body.event, body.dwell_seconds
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return HintEventResponse(
        episode_id=episode_id,
        hint_level=state.level.value,
        card_visible=state.card_visible,
    )


@app.post(
    "/api/episodes/{episode_id}/restatements",
    response_model=RestatementResponse,
    tags=["planback"],
)
def submit_restatement(
    episode_id: str,
    body: RestatementRequest,
    service: EpisodeService = Depends(get_service),
) -> RestatementResponse:
    """Score one restatement. The coordinator extracts; `domain` decides."""
    try:
        with _DB_LOCK:
            outcome = service.submit_restatement(
                episode_id,
                body.text,
                body.hint_level,
                body.transcript_confirmation_id,
                input_mode=body.input_mode,
                dwell_seconds=body.dwell_seconds,
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except (NoDispositionYet, UnconfirmedTranscript) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except StateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except CoordinatorUnavailable:
        raise _coordinator_down()
    return _restatement_body(outcome)


@app.post(
    "/api/episodes/{episode_id}/restatements/{restatement_id}/repairs",
    response_model=RestatementResponse,
    tags=["planback"],
)
def repair_restatement(
    episode_id: str,
    restatement_id: str,
    body: RestatementRequest,
    service: EpisodeService = Depends(get_service),
) -> RestatementResponse:
    """Score one repair round, capped at two (C6)."""
    try:
        with _DB_LOCK:
            outcome = service.repair_restatement(
                restatement_id,
                body.text,
                body.hint_level,
                body.transcript_confirmation_id,
                input_mode=body.input_mode,
                dwell_seconds=body.dwell_seconds,
                episode_id=episode_id,
            )
    except RestatementNotFound:
        raise HTTPException(
            status_code=404,
            detail=f"restatement {restatement_id!r} not found for episode {episode_id!r}",
        )
    except (
        NoDispositionYet,
        UnconfirmedTranscript,
        RepairCapReached,
        StaleRestatement,
    ) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except StateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except CoordinatorUnavailable:
        raise _coordinator_down()
    return _restatement_body(outcome)


# ---------------------------------------------------------------------------
# Slice 5: barriers, escalation and reassessment
# ---------------------------------------------------------------------------


class BarrierRequest(BaseModel):
    barrier_text: str
    proposed_route_id: str | None = None


class BarrierResponse(BaseModel):
    episode_id: str
    barrier_id: str
    disposition_version: int
    proposed_route_id: str | None
    permitted_route_id: str | None
    stopped_at_human_path: bool
    human_path_route_id: str | None
    simulated: bool
    fixture_label: str


class EscalationRequest(BaseModel):
    human_path: str
    outcome: str = "handed_off"


class EscalationResponse(BaseModel):
    episode_id: str
    escalation_id: str
    human_path: str
    outcome: str
    simulated: bool
    fixture_label: str


class ReassessmentRequest(BaseModel):
    """A closed-vocabulary change code, or nothing.

    Absence is not a negative finding (I5): omitting the code stops at the human
    path exactly as an unknown code does.
    """

    confirmed_change_code: str | None = None


class ReassessmentResponse(BaseModel):
    episode_id: str
    outcome: str
    reason: str
    disposition_version: int | None
    routes_to_human_path: bool
    human_path_route_id: str | None
    simulated: bool
    fixture_label: str


@app.post(
    "/api/episodes/{episode_id}/barriers",
    response_model=BarrierResponse,
    tags=["planback"],
)
def record_barrier(
    episode_id: str,
    body: BarrierRequest,
    service: EpisodeService = Depends(get_service),
) -> BarrierResponse:
    """Report a practical barrier. `domain` judges any proposed route.

    A proposal outside the policy is recorded as a stop **and then** refused with
    422, so the ledger keeps the evidence and the caller still gets the refusal.
    """
    try:
        with _DB_LOCK:
            outcome: BarrierOutcome = service.record_barrier(
                episode_id, body.barrier_text, body.proposed_route_id
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except NoDispositionYet as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PolicyViolation as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": str(exc),
                "stopped_at": "human_path",
                "barrier_recorded": True,
            },
        )
    return BarrierResponse(
        episode_id=episode_id,
        barrier_id=outcome.barrier_id,
        disposition_version=outcome.disposition_version,
        proposed_route_id=outcome.proposed_route_id,
        permitted_route_id=outcome.permitted_route_id,
        stopped_at_human_path=outcome.stopped_at_human_path,
        human_path_route_id=outcome.human_path_route_id,
        simulated=outcome.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.post(
    "/api/episodes/{episode_id}/escalations",
    response_model=EscalationResponse,
    tags=["planback"],
)
def record_escalation(
    episode_id: str,
    body: EscalationRequest,
    service: EpisodeService = Depends(get_service),
) -> EscalationResponse:
    """Hand the episode to a named human path.

    From this record onward the acting party is that path, not the patient (F6).
    """
    try:
        with _DB_LOCK:
            outcome: EscalationOutcome = service.escalate(
                episode_id, body.human_path, body.outcome
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except NoDispositionYet as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return EscalationResponse(
        episode_id=episode_id,
        escalation_id=outcome.escalation_id,
        human_path=outcome.human_path,
        outcome=outcome.outcome,
        simulated=outcome.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.post(
    "/api/episodes/{episode_id}/reassessments",
    response_model=ReassessmentResponse,
    tags=["planback"],
)
def reassess(
    episode_id: str,
    body: ReassessmentRequest,
    service: EpisodeService = Depends(get_service),
) -> ReassessmentResponse:
    """Classify a confirmed change, then stop or insert a new version.

    With no reviewer, `permitted_change_codes` is empty, so every input stops at
    the human path. That is the intended state, not a gap.
    """
    try:
        with _DB_LOCK:
            result: ReassessmentResult = service.reassess(
                episode_id, body.confirmed_change_code
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except NoDispositionYet as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except StateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ReassessmentResponse(
        episode_id=episode_id,
        outcome=result.outcome.value,
        reason=result.reason,
        disposition_version=result.disposition_version,
        routes_to_human_path=result.routes_to_human_path,
        human_path_route_id=result.human_path_route_id,
        simulated=result.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )


# ---------------------------------------------------------------------------
# Slice 6: consent, the action path and the callback
# ---------------------------------------------------------------------------


class ConsentRequest(BaseModel):
    granted: bool


class ConsentResponse(BaseModel):
    episode_id: str
    scope: str
    version: int
    granted: bool
    simulated: bool
    fixture_label: str


class ActionRequest(BaseModel):
    route_id: str
    purpose_id: str


class ActionResponse(BaseModel):
    """One opened attempt, and what the tool call returned.

    `origin` is on the response and not only inside `payload`, because
    `02-architecture.md` section 3.3 step 6 requires the origin marker to be
    displayable, and a marker buried in a payload is not displayable by
    inspection.
    """

    episode_id: str
    attempt_id: str
    idempotency_key: str
    route_id: str
    purpose_id: str
    disposition_version: int
    consent_version: int
    execution: str
    duplicate: bool
    origin: str
    outcome: str | None
    provider_ref: str | None
    payload: str | None
    simulated: bool
    fixture_label: str


class EvidenceBody(BaseModel):
    level: str
    simulated: bool = True
    provenance: str = ""
    source_ref: str | None = None


class CallbackRequest(BaseModel):
    """What the adapter asserts about one attempt.

    `origin` defaults to the value the wired path can produce. A caller may state
    it explicitly and `service.receive_callback` will check it, because a field
    that says whatever the caller wants is not the checkable marker section 3.3
    asks for.
    """

    callback_key: str
    transition: str | None = None
    evidence: EvidenceBody | None = None
    payload: str = ""
    origin: str = Origin.LOCAL_SIM.value


class CallbackResponse(BaseModel):
    episode_id: str
    route_id: str
    attempt_id: str
    origin: str
    receipt: str
    applied: bool
    rejection_reason: str | None
    execution: str
    simulated: bool
    fixture_label: str


@app.post(
    "/api/episodes/{episode_id}/consents",
    response_model=ConsentResponse,
    tags=["actions"],
)
def change_consent(
    episode_id: str,
    body: ConsentRequest,
    service: EpisodeService = Depends(get_service),
) -> ConsentResponse:
    """Grant or revoke clinical scope. Returns the new version number.

    Revocation appends a row rather than editing one, so an attempt stamped with
    an earlier version stays legible and its in-flight callback can be refused.
    """
    try:
        with _DB_LOCK:
            version = service.change_consent(episode_id, body.granted)
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    return ConsentResponse(
        episode_id=episode_id,
        scope=CLINICAL_SCOPE,
        version=version,
        granted=body.granted,
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.post(
    "/api/episodes/{episode_id}/actions",
    response_model=ActionResponse,
    tags=["actions"],
)
def open_action(
    episode_id: str,
    body: ActionRequest,
    service: EpisodeService = Depends(get_service),
) -> ActionResponse:
    """Open one attempt and execute the tool. Section 3.3 steps 1 to 4.

    **This writes no transition.** The outcome arrives on `/callbacks/{route_id}`,
    which is the path a real platform would use and the path that makes the
    duplicate and reordered cases representable.

    A repeat of the same `(episode, route, purpose)` returns the original attempt
    with `duplicate: true` and dispatches nothing (I3).
    """
    try:
        with _DB_LOCK:
            outcome: ActionOutcome = service.open_action(
                episode_id, body.route_id, body.purpose_id
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except (NoDispositionYet, ConsentRequired) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PolicyViolation as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": str(exc),
                "stopped_at": "human_path",
            },
        )
    except StateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return ActionResponse(
        episode_id=episode_id,
        attempt_id=outcome.attempt_id,
        idempotency_key=outcome.idempotency_key,
        route_id=outcome.route_id,
        purpose_id=outcome.purpose_id,
        disposition_version=outcome.disposition_version,
        consent_version=outcome.consent_version,
        execution=outcome.execution.value,
        duplicate=outcome.duplicate,
        origin=outcome.origin.value,
        outcome=outcome.tool.outcome.value if outcome.tool is not None else None,
        provider_ref=outcome.tool.provider_ref if outcome.tool is not None else None,
        payload=outcome.tool.payload if outcome.tool is not None else None,
        simulated=outcome.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )


@app.post(
    "/api/episodes/{episode_id}/callbacks/{route_id}",
    response_model=CallbackResponse,
    tags=["actions"],
)
def receive_callback(
    episode_id: str,
    route_id: str,
    body: CallbackRequest,
    service: EpisodeService = Depends(get_service),
) -> CallbackResponse:
    """Record one callback against the attempt this route opened.

    A duplicate is recorded and returns `receipt: "duplicate"` with
    `applied: false`. A success arriving after revocation is recorded and
    returns `receipt: "refused"` with the reason. Neither is a 200 that looks
    like an applied outcome, which is what O5 was raised for.
    """
    try:
        transition = (
            ExecutionStatus(body.transition) if body.transition is not None else None
        )
        origin = Origin(body.origin)
        evidence = (
            EvidenceRecord(
                level=EvidenceLevel(body.evidence.level),
                simulated=body.evidence.simulated,
                provenance=body.evidence.provenance,
                source_ref=body.evidence.source_ref,
            )
            if body.evidence is not None
            else None
        )
    except ValueError as exc:
        # NF2 is anchored to Slice 7, but this route is new and must not add
        # another instance of the defect it names: an unknown enum value is a
        # typed 422, never a 500.
        raise HTTPException(status_code=422, detail=str(exc))

    result = CallbackResult(
        transition=transition, evidence=evidence, payload=body.payload
    )
    try:
        with _DB_LOCK:
            outcome: CallbackOutcome = service.receive_callback(
                episode_id, route_id, body.callback_key, result, origin
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except (NoAttemptForRoute, ConsentRequired) as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except OriginNotWired as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": str(exc),
                "requested_origin": origin.value,
                "wired_origin": service.available_origin.value,
            },
        )
    except StateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except UnpermittedTransition as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return CallbackResponse(
        episode_id=episode_id,
        route_id=route_id,
        attempt_id=outcome.attempt_id,
        origin=outcome.origin.value,
        receipt=outcome.receipt.disposition.value,
        applied=outcome.receipt.applied,
        rejection_reason=outcome.receipt.rejection_reason,
        execution=outcome.execution.value,
        simulated=outcome.simulated,
        fixture_label=fixture.FIXTURE_LABEL,
    )
