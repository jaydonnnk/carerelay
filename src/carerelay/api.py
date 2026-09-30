"""FastAPI routes — Slice 1 (tracer bullet).

Two routes, wired end to end, against a hardcoded episode. No database, no
domain logic, no coordinator. It runs, and the user can see it.

`02-architecture.md` 3.1 lists the full route surface. This file deliberately
implements two of them and no more. Later slices add routes in build order —
the API is grown slice by slice, never filled in horizontally.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from carerelay import __version__
from carerelay.demo import fixture

app = FastAPI(
    title="CareRelay",
    version=__version__,
    description=(
        "SIMULATED RESEARCH DEMONSTRATION — not clinical advice, not a medical "
        "device, not validated for patient use."
    ),
)

# Slice 1 only: one in-memory episode. Slice 3 built the SQLite record at
# `carerelay.state`, but this route is not wired to it yet: the slice plan gives
# `state.py` its own slice and leaves the API wiring to the slices that add the
# routes. Until then this set is the whole of the API's state.
_OPEN_EPISODES: set[str] = set()


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
def create_episode() -> EpisodeCreated:
    """Create the demo episode.

    Does **not** write a disposition — that follows assessment (`02-architecture.md`
    3.1, 5.1). Slice 1 has no assessment, so it has no disposition.
    """
    _OPEN_EPISODES.add(fixture.DEMO_EPISODE_ID)
    return EpisodeCreated(
        episode_id=fixture.DEMO_EPISODE_ID,
        persona=fixture.DEMO_EPISODE_ID and "fictional older adult",
        policy_version=fixture.POLICY_VERSION,
        simulated=True,
        fixture_label=fixture.FIXTURE_LABEL,
        note=(
            "Slice 1 tracer bullet: hardcoded. No disposition is written, no "
            "database exists, and the fixture wording is a provisional "
            "placeholder awaiting the Option C source check."
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
