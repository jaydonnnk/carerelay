# ADP and deployment: impact on the approved architecture

**Kind:** supporting note. **Status: DRAFT, authorises nothing.**
**Date:** 30 September 2026.
**Source:** `docs/ADP_Hackathon_Guide_EN.pdf` (9 pages, "Tencent Cloud ADP, Hackathon
Guide", AI CAN DO IT Hackathon Singapore 2026), supplied by the user 30 September 2026.

This note records what the ADP guide changes, what it does not change, and where it
collides with approved documents. It does **not** reopen a gate. A gate is reopened only
by the user, and this note deliberately proposes rather than performs.

Evidence labels follow `AGENTS.md` section 1.

---

## 1. What the guide actually establishes

| Item | Detail | Label |
|---|---|---|
| ADP's status in the handbook | "The Hackathon Handbook lists ADP among the **recommended** Tencent Cloud services" (guide section 7) | **[verified]**: guide section 7, consistent with `CHALLENGE_REQUIREMENTS_JUDGING.md` section 7 |
| The mandatory product requirement | "built on at least one of the products CodeBuddy or WorkBuddy" | **[verified]**: `CHALLENGE_REQUIREMENTS_JUDGING.md` section 8 |
| **ADP does not discharge that requirement** | ADP is a Tencent Cloud service, listed under "Recommended". It is not CodeBuddy or WorkBuddy | **[hypothesis]**: a reading of the two documents, not a statement either makes. Worth confirming with the organiser |
| What ADP provides | "model orchestration, the knowledge base, the workflow and the guardrails all come from the platform" (guide section 7) | **[vendor claim]** |
| Two outputs on publish | **Experience URL** (shareable, for people) and **AppKey** (secret, for software) | **[verified]**: guide section 4 |
| Chat API | `https://wss.lke.tencentcloud.com/adp/v2/chat`, SSE stream | **[verified]**: guide section 6.2 |
| Auth | AppKey alone for HTTP SSE; AppKey **plus** API Secret for WebSocket | **[verified]**: guide section 5 |
| Session model | `ConversationId` per conversation, `VisitorId` per end user | **[verified]**: guide section 6.2 |
| Free allowance | Knowledge-base capacity and DeepSeek tokens on first sign-in; **time-limited** | **[verified]**: guide sections 1 and 8 |
| ADP tool execution | The guide does **not** document it, but `CHALLENGE_REQUIREMENTS_JUDGING.md` section 7 describes ADP as offering "model orchestration, sandboxed runtime environments, **tool-calling frameworks**, and extensible plugin ecosystems". "ADP can execute tools" therefore carries a **vendor claim** in the project's own rubric | **[vendor claim]** for tool-calling in general; **[unknown]** for whether ADP can execute an **MCP** tool |
| ADP platform-originated failure events | **Not mentioned anywhere in the guide**, and not implied by the rubric's tool-calling description | **[unknown]** |
| ADP session resume across a dropped connection | **Not mentioned anywhere in the guide** | **[unknown]** |

---

## 2. The collision: ADP is a chat agent, and the architecture forbids model text reaching the patient

`02-architecture.md` section 8 states, as an approved rule (row "Model-generated text
boundary"):

> "`domain` renders all patient-facing clinical text from policy. **No model-generated
> text reaches the patient.** Coordinator outputs are structured values only, validated
> in `domain`."

The ADP Chat API returns "a stream of SSE events, returned as the answer is generated"
(guide section 6.2). That is free-form model-generated text, by construction.

**This is not a blocker. It is a constraint on where ADP may sit.** ADP is admissible
only on the *interpretation* path, never on the *rendering* path:

```
patient free text  ->  ADP (interpret)  ->  structured values
                                              |
                                              v
                                        domain validates against the permitted set
                                              |
                                              v
                                        domain renders the four lines
```

That is exactly the existing coordinator contract (`02-architecture.md` section 2:
"coordinator proposes -> `domain` validates -> state records"; and D7's closed-vocabulary
classification step). **ADP can occupy the interpretation step inside the coordinator. It
may not occupy the coordinator slot as a whole, and it may not occupy the rendering slot.**
Section 3 explains why the execution half of the coordinator is out of bounds. Any
integration that pipes an ADP SSE answer straight to a patient screen breaks an approved
rule and a Gate 2 decision.

---

## 3. The load-bearing claim: ADP does not replace WorkBuddy as the execution substrate

`02-architecture.md` D8 pins the call path, and section 3.3 is normative:

> "2. Backend sends the coordinator a scoped snapshot containing the permitted route id
> and the attempt key, via the cloud-agent SDK session.
> 3. **The coordinator executes the tool through the platform's tool mechanism.** The
> platform is in the path."

And section 6.6 states the P1 load-bearing answer plainly:

> "The P1 load-bearing answer reverts to **execution substrate**: coordinator, real tool
> call, real failure event, session resume."

ADP's documented capabilities are model orchestration, knowledge base, workflow and
guardrails. The rubric's own description adds "tool-calling frameworks"
(`CHALLENGE_REQUIREMENTS_JUDGING.md` section 7), so "ADP can execute tools" is a
**[vendor claim]** rather than an unknown. What stays **[unknown]** is the part the
load-bearing claim actually rests on: whether ADP can execute **our MCP tool**, emit a
**platform-originated failure event carrying an origin signal**, and **resume a session**
across a dropped connection. None of those three is documented in the guide.

**Therefore:**

- ADP is **not** a drop-in replacement for the WorkBuddy coordinator.
- Substituting ADP for WorkBuddy in section 3.3 would **silently delete the P1
  load-bearing claim** unless ADP is separately proven to execute the MCP tool and
  originate the failure event.
- The correct posture is **additive**: WorkBuddy keeps the execution-substrate role it was
  approved for; ADP adds a second, independent capability on the interpretation path.

This is the same failure mode the Gate 2 round-2 review already caught once, when
revision 1 "described this five different ways" across four sections, which would have
let Gate 3 "wire a direct backend call" while "leaving the demo visually identical and the
platform-failure claim unsupported". **Do not repeat it with ADP.**

---

## 4. What ADP genuinely improves

### 4.1 The Experience URL is the right answer to the demo-link question

The guide section 7 is explicit:

> "use the Experience URL to let judges and teammates try it, and to record the demo video"

This matters more than it looks. `02-architecture.md` section 8 declined the live-link
bonus because exposing the clinical-shaped API publicly was judged unsafe, and stated
that auth is "a precondition, not a follow-up". The Experience URL gives a shareable,
organiser-sanctioned, publicly reachable entry point **to the agent**, without exposing
CareRelay's own clinical API.

**Net effect:** the bonus is reachable through an organiser-sanctioned surface without
exposing CareRelay's own clinical API.

**Corrected 30 September 2026: it relocates the public-surface risk, it does not remove
it.** A published ADP agent is public and shareable, and it will answer clinical questions
unless it is constrained. If that happens on an organiser-sanctioned surface, it is a
deployment claim in substance even when the surrounding page wording is careful.
**Mitigation, and it is a requirement rather than a nicety:** limit the agent's knowledge
base to the **non-clinical fixture** and configure its guardrails to **refuse clinical
advice**, before the Experience URL is shared.

**Corrected 30 September 2026 (later decision):** the local-only choice on the clinical
application **has since been reversed** by D-1b and D-C. A production link is now required,
so the Experience URL is no longer a substitute for one, and the two surfaces carry the
same clinical-claim risk independently.

### 4.2 The AppKey path doubles as usage proof

Guide section 7: "The Handbook asks for proof that the project was built with the tools.
Keeping the key screens and the call results will make that easier."

An AppKey call from `coordinator/` produces a loggable, timestamped request/response pair.
**Corrected 30 September 2026: it is a supplement only.** The mandatory proof under
`CHALLENGE_REQUIREMENTS_JUDGING.md` section 8 is proof of **CodeBuddy or WorkBuddy** usage.
An ADP call log proves **ADP** usage, which is a different product, so it cannot discharge
that requirement on its own. It supplements, and does not replace, the mandatory
CodeBuddy/WorkBuddy development history (section 6.5 of the architecture).

### 4.3 A real second coordinator surface

ADP's knowledge base and guardrails are a defensible home for the D7 closed-vocabulary
classification and the intake clarification loop, the two places the architecture already
routes free text through a model.

---

## 5. Deployment: the requested Vercel + Render split

The user has requested **Vercel for the frontend, Render for the backend.**

### 5.1 The premise does not currently hold

There is no frontend to move. `pyproject.toml` declares FastAPI, uvicorn, pydantic and
jinja2. `src/carerelay/api.py` renders HTML with f-strings inside the route, `jinja2` is
declared but imported nowhere, `src/carerelay/static/style.css` is one file, and **the
product contains no JavaScript at all**. It is one Python process serving its own HTML.

So "Vercel for the frontend" has two possible meanings, and they are not close in cost.

### 5.2 Variant A: static page on Vercel (recommended)

A one-file landing page on Vercel: cover image, sub-10-word blurb, a link to the ADP
Experience URL, a link to the Render demo, and the architecture diagram.

- **Cost:** hours.
- **Risk:** none to the product. It touches no approved code.
- **Rubric effect:** satisfies the optional "Project link" item and helps Demo and
  Storytelling (10 pts).
- **Honest framing:** it is a landing page, not "the frontend". The submission should say
  so.

### 5.3 Variant B: real SPA split (permitted, but expensive)

Next.js or React on Vercel calling FastAPI as a JSON API on Render.

**First, a correction to an argument that would be wrong.** C8 does **not** forbid this.
`04-slices.md` line 47 defines C8 as "**No timer, countdown or auto-advance anywhere.**
H2 stays until the patient hides it." That is a constraint on *behaviour*, not on
technology. The line "no `<script>`" at `00-status.md` line 280 is a Slice 1
**verification observation** offered as evidence that no timer exists. It is not a standing
prohibition on JavaScript. **No approved document forbids a JavaScript frontend.**

What is true:

- **Scope.** `domain/` (1,039 lines: `models.py` plus `rules.py`, excluding the 16-line package marker) and `state.py` (1,323 lines) are untouched. The change
  is the presentation layer: `api.py`'s `HTMLResponse` route and the 94-line `style.css`.
  `GET /api/episodes/{id}` already returns `PatientProjection` as JSON, so the API half
  exists. This is a smaller job than "rewrite the app" suggests.
- **Cost.** A Next.js project, five screens, client routing, data fetching, CORS on
  FastAPI, an API base URL env var, and a Node toolchain in the demo environment.
- **The accessibility dimension.** UX and Accessibility is a scored 10-point dimension and
  the population is community-dwelling older adults. The current screen holds semantic
  HTML, 20px base type, strong contrast, screen-reader compatibility and JS-disabled
  operation **for free**, because it is server-rendered text. A client-rendered app can
  hold all of those, but each becomes work you must do and defend. Precisely: Variant B
  does not damage the dimension, it **adds work required to keep a dimension that is
  currently free.**
- **Two network boundaries in a live demo.** Browser to Vercel to Render to ADP. Section 8
  already names a coordinator stall as "a demo-ending failure". Each added hop is another
  way for the judged walkthrough to fail.
- **Schedule.** Section 5 of this note's source material records the build at 90 to 150
  hours and states it is "not affordable in 21 days". Slices 4 to 13 remain, and the
  deadline is 16 October 2026. A presentation rewrite competes directly with those slices,
  and it is the only one of the two that the rubric does not gate on.

**The decisive objection is schedule and demo risk, not accessibility.** An earlier draft
of this note overstated the accessibility case; this is the corrected reading.

**Middle path.** If the aim is a Next.js-looking submission, Next.js can host the landing
page and a thin demo shell that links to the Render app and the ADP Experience URL. That
gets the requested stack on Vercel without rewriting the clinical screens.


### 5.4 Render: workable, and the free tier is the only thing that breaks it

| Concern | Detail |
|---|---|
| SQLite persistence | `state.py` is a file on disk. Render's free tier has an **ephemeral** filesystem. A paid **persistent disk** plus a mount path is required, or the append-only record does not survive a restart. This is the single hard requirement of the whole split |
| Cold start | The free tier spins down when idle. `02-architecture.md` section 8 already names a coordinator stall as "a demo-ending failure". A cold start plus an ADP SSE stream is exactly that failure |
| Public endpoint | Any Render deployment is public. Section 8: "If a live link is ever added, auth is a precondition, not a follow-up" |
| Secrets | AppKey and API Secret are env vars only (sections 6 and 8). The ADP guide warns twice: do not commit, and check screenshots. Section 8 already says "never in screenshots" |

### 5.5 Reference implementation: laeria.ai, a working Render + Vercel split

`C:\Users\jayd0\OneDrive\Desktop\laeria.ai` is the user's own project and is the strongest
evidence available for this section. Read 30 September 2026.

| Layer | laeria's choice | Evidence |
|---|---|---|
| Frontend | Next.js 14 App Router, Tailwind, on **Vercel** | `README.md` line 126; `https://laeria-ai.vercel.app` appears in **two** files: `extension/content.js` (two refs) and `backend/.auth/storage_state.prod.json` (one ref). `extension/config.js` line 10 holds the **Render backend** URL (`https://laeria-ai-backend.onrender.com`), **not** the Vercel URL |
| Backend | FastAPI in **Docker** on **Render** | `README.md` lines 23 to 24, 127; `backend/Dockerfile` |
| Database | **Supabase Postgres** (pgvector, Auth, RLS) | `README.md` line 129; `infra/supabase/migrations/` |
| Wiring | `NEXT_PUBLIC_API_URL` on Vercel, `CORS_ORIGINS` on FastAPI | `frontend/next.config.js`; `backend/api/main.py` lines 44 to 63 |
| Auth | Bearer token, `allow_credentials=False`, wildcard origin in dev only | `backend/api/main.py` lines 44 to 63 |
| Config | **No `vercel.json`, no `render.yaml`.** Both hosts configured in their dashboards | repository search, 30 Sep 2026 |

**The pattern is proven. So the split is viable, and cheaper than an earlier draft of this
note implied.** That draft was too pessimistic and this is the correction.

**But note why it works there.** laeria's backend is **stateless**: every durable fact
lives in Supabase. Render can restart, cold-start and redeploy freely because there is
nothing on its disk to lose. CareRelay's backend is the opposite. `state.py` is a SQLite
file, and the append-only record is the load-bearing proof of Slice 3.

**laeria also contains a live instance of exactly this trap.** `backend/services/research_cache.py`
line 30 sets `CACHE_DIR = <backend>/.cache/research`, which is inside the container image,
with no mount and no `render.yaml` to declare one. Its own docstring says the cache is on
disk "rather than in memory so it survives a restart". **That claim is false on any
container recreation**, and a redeploy rebuilds the image: the directory is ephemeral and
is wiped. It holds only for an in-place process restart. The cache does not survive a
deployment in production, only in local development.
This is worth fixing in laeria independently of CareRelay, and it is the concrete
precedent for why the persistent disk is not optional here.

**Consequence for CareRelay.** The split is viable on two conditions, and only two:

1. A **paid Render plan with a persistent disk**, mounted, with the SQLite path pointed at
   the mount via an environment variable. Small change. Do this rather than the
   alternative.
2. **Auth**, per section 8, because the endpoint becomes public.

The alternative, moving the store to managed Postgres as laeria did, would rewrite
`state.py`'s 1,323 lines and its trigger-enforced append-only guarantees, which 91 tests
currently prove. Not advisable inside the remaining schedule.

### 5.6 Vercel for the application itself: not viable

Vercel's serverless functions have an ephemeral filesystem outside `/tmp`. SQLite writes
do not persist between invocations, so the append-only record cannot live there. This is
also why laeria put the API on Render and kept Vercel for the Next.js frontend only
(section 5.5). Vercel is fine for Variant A. It is not a host for CareRelay's backend.

---

## 6. Gate implications

Nothing here is authorised. The changes below each require the user to reopen a gate.

| # | Change | Gate | Why it is a gate change |
|---|---|---|---|
| 1 | ADP added as a coordinator implementation | **Gate 2** | D8 and section 3.3 pin **one** normative call path. Adding a second coordinator surface changes an approved decision, not an implementation detail |
| 2 | A public deployment of any kind | **Gate 2** | Section 8 approved **local-only** and declined the live link as "a choice, not an omission". Auth becomes a precondition |
| 3 | Presentation layer split (Variant B only) | **Gate 2 + Gate 3** | Section 2's layout and Gate 3's pinned files both change |
| 4 | ADP Experience URL adopted as the demo entry point | **Gate 1 or Gate 2** | It is a submission-surface decision. Cheapest of the four, and the highest value per unit of risk |

**Not gate changes:** Variant A (a landing page touches no approved code); capturing
AppKey call logs as usage proof (evidence collection, already an obligation under
section 6.5).

---

## 7. Recommended sequence

1. **Do not touch the WorkBuddy coordinator role.** It carries the P1 load-bearing claim.
2. **Register ADP and publish one agent**, purely to obtain an Experience URL and an
   AppKey. This is exploration, not integration.
3. **Adopt the Experience URL** as the judges' and demo-video entry point. This is the
   cheapest real win in this note, and it removes the pressure to expose the clinical API.
4. **Add Variant A** on Vercel as the landing page.
5. **Defer the Render deployment** until the app is worth deploying: after Slice 4 puts
   product behaviour behind a route, and after the fixture wording stops being
   provisional. Deploying the current stub publishes nothing useful and creates a public
   unauthenticated endpoint.
6. **Only then** consider ADP as a second coordinator surface, with the structured-output
   boundary of section 2 written into the design before any code.

---

## 8. Open questions for the organiser

- Does an ADP-based project satisfy "built on at least one of the products CodeBuddy or
  WorkBuddy", or is a separate WorkBuddy/CodeBuddy artefact still required? **[unknown]**
- Does ADP execute MCP tools and emit platform-originated failure events? **[unknown]**.
  This determines whether ADP could ever carry the execution-substrate claim.
- Does the ADP free allowance last through 16 October 2026? **[unknown]**. The guide says
  only that it is time-limited.
