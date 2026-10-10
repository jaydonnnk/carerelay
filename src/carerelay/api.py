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

Slice 7 adds the transport guards the public deployment needs, and nothing else
in this file changes. **Every `/api` route requires a bearer token when auth is
armed**, CORS is locked to the origins the deployment names, and the credentials
flag is off. The two guards are here rather than in `service` because they are
about who may reach the transport, not about what the record may say; `domain`
still owns every clinical decision.

Auth is **fail-closed**: if auth is armed and no token is configured, every
protected route answers 503 rather than serving an open clinical-shaped
endpoint. That is the R9 stop condition expressed in code, and it is why the
local demo and the test suite run disarmed instead of the guard being optional.
"""

from __future__ import annotations

import hmac
import os
import threading
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from carerelay import __version__
from carerelay.coordinator import (
    CoordinatorUnavailable,
    LocalSimulationCoordinator,
)
from carerelay.demo import fixture
from carerelay.domain.rules import (
    NoDispositionToRender,
    PolicyViolation,
    UnpermittedTransition,
)
from carerelay.domain.models import (
    CallbackResult,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    Origin,
)
from carerelay.service import (
    AcceptanceOutcome,
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
    EpisodeStore,
    RestatementNotFound,
    SqliteEpisodeStore,
    StateError,
    is_postgres_target,
    open_store,
)
from carerelay.tools import McpTools

# ---------------------------------------------------------------------------
# Slice 7: who may reach the transport
# ---------------------------------------------------------------------------

#: The prefixes the token guards. `/health` and the fallback patient page stay
#: open on purpose: a health check that needs a credential cannot be used by the
#: platform that is checking it, and the fallback page renders the fixture's
#: static four lines with nothing read from the record.
GUARDED_PREFIXES: tuple[str, ...] = ("/api", "/ledger")

#: The environment names. Slice 7 keeps them to three so the arming rule is
#: legible by inspection rather than by reading the code that reads it.
PUBLIC_ENVS: frozenset[str] = frozenset({"public", "production", "prod"})
TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})

API_TOKEN_ENV = "CARERELAY_API_TOKEN"
REQUIRE_AUTH_ENV = "CARERELAY_REQUIRE_AUTH"
APP_ENV_ENV = "APP_ENV"
CORS_ORIGINS_ENV = "CORS_ORIGINS"


def _env(name: str) -> str:
    return (os.getenv(name) or "").strip()


def auth_is_armed() -> bool:
    """Whether the bearer-token dependency is enforcing.

    Three ways to arm it, because a deployment forgets: `APP_ENV` naming a public
    environment, `CARERELAY_REQUIRE_AUTH` set to yes, or a token being present at
    all. The last is the safety net: configuring a token is an unambiguous
    statement that the service expects one, so treating it as decoration would
    be the one way to publish an open endpoint by mistake.

    Everything else runs disarmed, which is what the local demo and the test
    suite do. Disarmed is a deliberate local state, not a permissive default for
    a deployed service: `APP_ENV=public` is set by `render.yaml`, so the
    deployment is armed without depending on anyone remembering a second flag.
    """
    if _env(APP_ENV_ENV).casefold() in PUBLIC_ENVS:
        return True
    if _env(REQUIRE_AUTH_ENV).casefold() in TRUTHY:
        return True
    return bool(_env(API_TOKEN_ENV))


def configured_token() -> str:
    return _env(API_TOKEN_ENV)


def _unauthorized() -> HTTPException:
    """401 with a `WWW-Authenticate` header, and no hint about the token.

    The detail says what is missing, not what would have been accepted.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="a bearer token is required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _misconfigured() -> HTTPException:
    """503: auth is armed but no token exists.

    This is the fail-closed branch, and it is the one that matters. The
    alternative is to treat a missing token as "no auth needed", which would
    publish a clinical-shaped endpoint to the open internet and would be risk R9
    realised by a typo. A deployment that cannot check a credential must not
    answer, so it answers 503 until someone sets one.
    """
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            f"auth is armed but {API_TOKEN_ENV} is not configured; refusing to "
            "serve a protected route without a credential to check"
        ),
    )


def guarded_path(path: str) -> bool:
    """Whether this request path carries the record, and so needs a token.

    The prefix test is why the guard can be declared once for the whole app
    instead of 13 times: a route added later under `/api` is covered whether or
    not anyone remembered to annotate it. `tests/test_api.py` walks the real
    route table and fails if a path under a guarded prefix escapes, so the
    blanket cannot quietly stop being one.
    """
    return any(
        path == prefix or path.startswith(prefix + "/") for prefix in GUARDED_PREFIXES
    )


async def require_api_token(request: Request) -> None:
    """The dependency every protected route takes. Slice 7.

    Comparison is `hmac.compare_digest`, not `==`. A token comparison that leaks
    its timing turns a public endpoint into an oracle for the very secret that
    guards it, and the whole point of the guard is that the secret is unguessable.

    The token is read from the environment on every call rather than captured at
    import, so a test can arm auth without reloading the module.
    """
    if not guarded_path(request.url.path):
        return
    if not auth_is_armed():
        return
    token = configured_token()
    if not token:
        raise _misconfigured()
    header = request.headers.get("authorization", "")
    scheme, _, presented = header.partition(" ")
    if scheme.casefold() != "bearer" or not presented.strip():
        raise _unauthorized()
    if not hmac.compare_digest(presented.strip(), token):
        raise _unauthorized()


def permitted_cors_origins() -> list[str]:
    """The allow-list, read from the environment **at request time**.

    Wildcards are refused rather than passed through: an origin of `*` would undo
    the whole guard, so it is dropped and the service then serves no cross-origin
    caller at all, which is the safe direction to fail in.
    """
    raw = _env(CORS_ORIGINS_ENV)
    if not raw:
        return []
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return [origin for origin in origins if origin != "*"]


def _cors_headers_for(request: Request) -> dict[str, str]:
    """The CORS response headers for this request, or none at all.

    The origin is echoed only when it is on the allow-list, so an unnamed origin
    gets no header rather than a permissive one.
    """
    origin = request.headers.get("origin", "").strip()
    if not origin or origin not in permitted_cors_origins():
        return {}
    return {"Access-Control-Allow-Origin": origin, "Vary": "Origin"}


def _install_cors() -> None:
    """Register the CORS middleware. Called after `app` exists, not at import.

    It has to be a function rather than a bare decorator on the module body,
    because the decorator needs `app` and `app` is defined below the guard
    helpers. The first attempt put `@app.middleware` above the `app = FastAPI(...)`
    line and the module failed to import at all.
    """
    app.add_middleware(BaseHTTPMiddleware, dispatch=_cors)


async def _cors(request: Request, call_next):
    """Cross-origin access, decided per request. Slice 7.

    **Why this is not `CORSMiddleware`.** Starlette's middleware takes its
    origins at construction, which happens at import. The first version of this
    guard did that, and the mutation harness caught the consequence: the CORS
    tests set the environment *after* import and passed while proving nothing
    about the configuration, because no middleware existed to be wrong. A guard
    whose tests cannot see it change is not a guard. Reading the environment per
    request costs one split on a short string and buys a test that bites.

    **`Access-Control-Allow-Credentials` is never set**, and there is no switch
    to set it. The token is a bearer credential in a header, so cookie
    credentials are neither needed nor wanted.

    The surface is deliberately narrow: `GET` and `POST`, with `Authorization`
    and `Content-Type`. Nothing else is allowed, because nothing else is used.
    """
    if request.method == "OPTIONS":
        headers = _cors_headers_for(request)
        if not headers:
            return Response(status_code=204)
        return Response(
            status_code=204,
            headers={
                **headers,
                "Access-Control-Allow-Methods": "GET, POST",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
            },
        )
    response = await call_next(request)
    for key, value in _cors_headers_for(request).items():
        response.headers[key] = value
    return response


app = FastAPI(
    title="CareRelay",
    version=__version__,
    description=(
        "SIMULATED RESEARCH DEMONSTRATION — not clinical advice, not a medical "
        "device, not validated for patient use."
    ),
    # Declared once for the whole app, so a route added later cannot be the one
    # that forgot. `require_api_token` decides by path which requests it guards.
    dependencies=[Depends(require_api_token)],
)

_install_cors()

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

    **Slice 7b: a `postgresql://` value selects the Postgres store** instead of
    SQLite, which is how the deployment reaches Supabase. No other code path
    changes, because both stores implement `EpisodeStore`.
    """
    return os.getenv("APP_DATABASE_URL") or ":memory:"


#: SQLite has no way to make one connection safe for concurrent use, and FastAPI
#: serves synchronous routes from a thread pool. The store is therefore opened
#: with `check_same_thread=False` and every use case runs under this lock, so a
#: second request waits rather than trying to begin a transaction inside another
#: one. `02-architecture.md` section 4.1's `BEGIN IMMEDIATE` still handles the
#: genuinely concurrent case, which is a *second connection* to the same file.
_DB_LOCK = threading.Lock()


def _open_store() -> SqliteEpisodeStore | EpisodeStore:
    """Open whichever engine `APP_DATABASE_URL` names. Slice 7b.

    **Why the two branches are explicit rather than one call with a kwarg.**
    `check_same_thread` is a SQLite connection flag with no Postgres meaning, and
    `open_store` refuses a keyword the chosen engine does not accept rather than
    dropping it. Passing it unconditionally would make a Supabase deployment fail
    at import on an argument that only ever described a local file.

    Either way the store is shared across requests and every use case runs under
    `_DB_LOCK`, so SQLite's own concurrency limit and Postgres's are both handled
    in one place. `02-architecture.md` section 4.1's `BEGIN IMMEDIATE`, and its
    Postgres counterpart `SELECT ... FOR UPDATE`, still handle the genuinely
    concurrent case, which is a *second connection*.
    """
    target = _database_path()
    if is_postgres_target(target):
        return open_store(target)
    return open_store(target, check_same_thread=False)


_STORE = _open_store()

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
    policy_text=fixture.policy_text(),
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

    Slice 10 adds `closure` and `care_evidenced`. The frontend needs the closure
    state to choose which approved rendering to show, and `care_evidenced` is
    carried beside it so a caller can tell a resolved episode from one where a
    human accepted a handoff without re-deriving either. The two are independent
    axes (F5) and neither is inferred from the other here.
    """

    episode_id: str
    lines: list[str]
    closure: str
    care_evidenced: bool
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
def get_episode(
    episode_id: str,
    service: EpisodeService = Depends(get_service),
) -> PatientProjection:
    """The patient projection: four lines and the simulated label.

    Slice 10 derives this from `domain.patient_lines` against the two axes,
    instead of returning a fixed literal, and runs the **expiry read-path**
    first: the first read after an unresolved deadline records the expiry event
    once, so an episode whose deadline passed while nobody looked is reported as
    expired the moment somebody reads it. There is no scheduler behind this.

    **The pre-assessment fallback.** `POST /api/episodes` writes no disposition
    (`02-architecture.md` 3.1), so before assessment there is no plan, no owner,
    no route and no deadline for `domain.patient_lines` to name. The Slice 1
    tracer bullet rendered a fixed four-line placeholder for that case and this
    route keeps it rather than inventing a plan. The literal lives in
    `demo/fixture.py` and is used only here; the moment a disposition exists the
    derivation takes over.

    **Every closure state renders its approved wording.** The three closure
    renderings were approved on 8 October 2026, so `domain.patient_lines` now
    covers all four states the Closure Contract can derive and this route no
    longer needs a refusal branch for a resolved episode.
    """
    if episode_id not in _OPEN_EPISODES:
        raise HTTPException(status_code=404, detail="episode not found")
    with _DB_LOCK:
        try:
            surface = service.project_patient(episode_id)
        except NoDispositionToRender:
            lines = fixture.demo_lines()
            return PatientProjection(
                episode_id=episode_id,
                lines=list(lines.as_tuple()),
                closure="open",
                care_evidenced=False,
                simulated=True,
                fixture_label=fixture.FIXTURE_LABEL,
            )
    return PatientProjection(**surface.as_dict())


@app.get("/api/episodes/{episode_id}/options", tags=["episodes"])
def get_options(
    episode_id: str,
    service: EpisodeService = Depends(get_service),
) -> dict[str, object]:
    """The routes this episode's disposition permits, in the policy's words.

    `02-architecture.md` 3.1 calls this "permitted routes for this disposition,
    rendered from policy", and it exists because revision 1 held the permitted
    set only as an MCP tool, so a screen had nothing to display. Both halves
    are policy data and neither is decided here: the ids are
    `PolicyFixture.permitted_route_ids` and the words are
    `PolicyText.route_display_by_id`.

    **The route id is never rendered unnamed.** A permitted route with no
    approved display text raises rather than printing its internal identifier,
    which is the same rule `domain.patient_lines` applies to a route name.
    """
    if episode_id not in _OPEN_EPISODES:
        raise HTTPException(status_code=404, detail="episode not found")
    with _DB_LOCK:
        return service.permitted_options(episode_id).as_dict()


@app.get("/api/episodes/{episode_id}/ledger", tags=["episodes"])
def get_ledger(
    episode_id: str,
    service: EpisodeService = Depends(get_service),
) -> dict[str, object]:
    """The judge-facing ledger for one episode.

    This is the surface `04-slices.md` Slice 12 asks for, at the path
    `02-architecture.md` 3.1 names. It carries the two axes, every transition
    with its **failure-event origin**, the expiry rows, the simulated label, the
    five fault assertions as verdicts over stored rows, and `dwell_seconds` on
    the rows that record it.

    **It never writes.** The patient projection runs the expiry read-path
    because a patient read is the trigger that records an expiry; a judge
    reading the evidence is not a clinical event, so this route is read-only by
    design and says so.

    **`dwell_seconds` lives here and only here.** It is judge-facing evidence
    about how long a patient spent with the card, and it must never reach the
    patient surface (`PLAN.md` 5.2.1, constraint C8), which is why the hint
    response above has no such field.
    """
    if episode_id not in _OPEN_EPISODES:
        raise HTTPException(status_code=404, detail="episode not found")
    with _DB_LOCK:
        return service.project_ledger(episode_id).as_dict()


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
    except PolicyViolation as exc:
        # NF2. A malformed `hint_level` or `input_mode` used to leave `domain` as
        # an uncaught `ValueError` and answer 500. `domain` now refuses it, and a
        # refusal is a stop at the human path, not a crash.
        raise HTTPException(status_code=422, detail=str(exc))
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
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))
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


class AcceptanceRequest(BaseModel):
    """A named human acceptance of the handoff, and the scope it covers.

    `accepted_by` is a permitted owner id, validated in `domain`. It is not free
    text: the ledger names a party this policy can display (I4).
    """

    accepted_by: str
    accepted_scope: str = "handoff"


class AcceptanceResponse(BaseModel):
    """The recorded acceptance, and the closure it produced.

    `care_evidenced` is always `false` on this path, and that is the point: an
    acceptance closes the handoff obligation, it is never evidence that care
    happened (`03-program-design.md` section 3). The field is serialised rather
    than omitted so the claim is checkable from the response alone.
    """

    episode_id: str
    acceptance_id: str
    accepted_by: str
    scope: str
    closure: str
    care_evidenced: bool
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
    "/api/episodes/{episode_id}/acceptances",
    response_model=AcceptanceResponse,
    tags=["planback"],
)
def record_acceptance(
    episode_id: str,
    body: AcceptanceRequest,
    service: EpisodeService = Depends(get_service),
) -> AcceptanceResponse:
    """Record a named human acceptance of the handoff. A D4 closure input.

    The acceptance closes the handoff obligation and **never** evidences care:
    it is not written to `evidence`, so `care_evidenced` stays false and no
    surface may say care happened because somebody accepted the case. A 409 when
    the episode has no plan yet, a 422 when the accepting party is not one the
    policy permits, and a 404 when the episode does not exist.
    """
    try:
        with _DB_LOCK:
            outcome: AcceptanceOutcome = service.record_human_acceptance(
                episode_id, body.accepted_by, body.accepted_scope
            )
    except EpisodeNotFound:
        raise HTTPException(status_code=404, detail=f"episode {episode_id!r} not found")
    except NoDispositionYet as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except PolicyViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return AcceptanceResponse(
        episode_id=episode_id,
        acceptance_id=outcome.acceptance_id,
        accepted_by=outcome.accepted_by,
        scope=outcome.scope,
        closure=outcome.closure.closure.value,
        care_evidenced=outcome.closure.care_evidenced,
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
