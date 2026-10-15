# CareRelay

**Challenge 1: AI Grandma Knows Best, Intelligent Self-Triage and Care Navigation.**

**Blurb (8 words):** Understand care advice. Find a feasible next step.

**Status of this document.** Every claim below is traceable to a file in this
repository, a test, a live transcript, or is labelled as a hypothesis. Nothing here
is a clinical claim. The companion statement `honest-claims.md` lists what this
project must not be said to have achieved, and it is part of the submission rather
than an appendix to it.

---

## 1. Project overview

**Target scenario.** A community-dwelling older adult, 65 or older, with a family
caregiver who is not in the room (`docs/PLAN.md:166`). They have been given advice,
for example "get this reviewed today". The advice is correct and specific. Nothing
happens next, and the reason is not clinical: the timing was misread, the only route
offered is not one the person can actually use, or a booking or hand-off attempt
failed and nobody was told.

**What CareRelay is.** A patient-facing prototype that treats *follow-through* as the
thing to be engineered, rather than the diagnosis. It does two things a triage tool
usually does not do:

1. **PlanBack.** The patient restates the plan in their own words, and code, not a
   model, checks the critical fields against the approved recommendation
   (`03-planback-closure-contract.md:27`). A mismatch is repaired one field at a
   time, twice at most, and then the episode goes to a named human path
   (`docs/PLAN.md:211-216`).
2. **The Closure Contract.** The episode carries two independent axes, execution and
   evidence, which produce one of four closure states. The record cannot say "done"
   because something was clicked
   (`03-planback-closure-contract.md:135-145`).

**Value proposition.** The patient screen is **four lines and nothing else**
(`docs/PLAN.md:360-364`). It names what must be done, by whom, by when, and which
human route to call if it does not work. When nobody has agreed to help, it says so:

> No one has agreed to help yet.
> Please act now.
> Please do it before 6pm today.
> If that does not work, call the fictional nurse line.

**What the demonstrable build is.** One fictional episode, scripted end to end, with
the single bound complaint "help sorting out my appointment"
(`src/carerelay/demo/fixture.py:203`). The action, deadline, owner and fallback are
all fictional and labelled. Anything outside that bound phrase is refused with HTTP
422 rather than triaged (`00-status.md:157`). That is a deliberate scope decision,
not an unfinished feature: the project asserts no clinical judgement anywhere.

---

## 2. Real-world scenario insights

**Source of the pain point.** The failure CareRelay targets is stated as: "An older
adult may receive the right care advice and still fail to act because the timing was
misunderstood, the next step is impractical, or a booking or handoff attempt failed.
Current interfaces can make a recommendation or click look like progress even when
nobody has accepted responsibility and no care has occurred"
(`01-product.md:5`).

**Target audience.** Community-dwelling adults aged 65 and over, and their remote
family caregivers, in Singapore. English text first; Mandarin is modelled in the
fixture as aliases only and voice was never built (see `honest-claims.md`).

**How strong is the evidence? Labelled, because the labels differ.**

| Claim | Label | Source |
|---|---|---|
| Limited health literacy affects 42.0 per cent and marginal 20.4 per cent of 2,327 Singaporeans aged 65 and over (BRIEF, 2023) | **[verified]**, and it is an instrument classification, **not** a triage error rate | `docs/PLAN.md:105` |
| Human teach-back improved comprehension of discharge instructions (one US emergency department trial, n = 254) | **[verified]**, and it does **not** validate automated comprehension scoring | `docs/PLAN.md:122` |
| How common CareRelay's specific failure is | **[unknown]** | `docs/PLAN.md:108` |
| Which failure dominates: assessment, comprehension, access, or follow-through | **[unknown]** | `docs/PLAN.md:109` |
| Users fail to act after correct advice | **[hypothesis]**. No dyad was ever observed | `AGENTS.md:169-174` |

That last row is the honest centre of this project. It is a design thesis with
supporting adjacent literature, not a measured prevalence.

---

## 3. Solution design

### 3.1 Business architecture: what happens in one episode

1. **Intake.** The patient types one complaint. Recognition is an exact normalised
   match against the bound phrase, so free text never produces a disposition
   (`00-status.md:524-528`).
2. **The plan card.** Action, deadline, owner and fallback route, in the policy's own
   words (`src/carerelay/demo/fixture.py:54-56`).
3. **PlanBack.** The restatement is compared on three fields. The deadline compares
   as a time bucket, the action against a closed vocabulary of action ids, the owner
   against the named party (`03-planback-closure-contract.md:65-67`). A hint ladder
   discloses the fields being checked before the patient answers
   (`tests/test_domain.py:819`).
4. **A barrier, if there is one.** The patient reports it; one permitted route is
   dispatched through the tool surface; the simulated provider fails as scripted and
   the attempt is recorded `failed` with the deadline untouched
   (`00-status.md:493`, `:501`).
5. **Closure.** The four-line screen renders the derived state, never a stored one.

### 3.2 The two axes and the four states

- **Execution:** `not_started` to `attempted` to `acknowledged | failed | expired`
- **Evidence:** `none` to `self_reported` to `documented`
- **Closure:** `open`, `closed_with_evidence`, `escalated_to_human`,
  `expired_unresolved` (`03-planback-closure-contract.md:135-145`)

Closure is **derived, never stored** (D4, `02-architecture.md:333`). That removes the
write path for false completion. Its declared cost is that false completion is still
reachable through projection bugs, which is why the fault harness exists.

### 3.3 Technical architecture

| Layer | What it is | Where |
|---|---|---|
| API | FastAPI, the authorisation boundary | `src/carerelay/api.py` |
| Domain | Pure decision logic: no network, no LLM client, no wall clock, enforced by a scanner | `src/carerelay/domain/` |
| Record | Postgres on Supabase, 14 tables and 42 triggers; SQLite for tests | `src/carerelay/postgres_store.py`, `src/carerelay/state.py` |
| Patient and judge surfaces | Next.js on Vercel: four-line patient screen, judge ledger | `frontend/app/` |
| Tool surface | Three MCP tools with three rechecks each | `src/carerelay/tools.py` |
| Development substrate | WorkBuddy and CodeBuddy, which is also the mandatory usage proof | `submission/usage-proof.md` |

**Route surface.** `POST /api/episodes`, `/intake`, `/transcript-confirmations`,
`/hint-events`, `/restatements`, `/restatements/{id}/repairs`, `/barriers`,
`/escalations`, `/acceptances`, `/reassessments`, `/consents`, `/actions`,
`/callbacks/{route_id}`, and the reads `/api/episodes/{id}`, `/options`, `/ledger`
(plus the guarded alias `/ledger/{id}`) (`src/carerelay/api.py:453-1340`).

### 3.4 Trust boundaries

- **One bearer token**, compared with `hmac.compare_digest`, enforced by a single
  dependency on the guarded prefixes `/api` and `/ledger`. If auth is armed and no
  token is configured, a protected route answers **503** rather than serving an open
  endpoint (`src/carerelay/api.py:103`, `:170`, `:189-237`).
- **CORS** is read per request from one allow-list, `https://carerelay-self.vercel.app`.
  Wildcards are refused and credentials are never allowed
  (`src/carerelay/api.py:262-264`; `render.yaml:59-60`).
- **The coordinator is scoped.** It receives permitted surface forms only and returns
  raw spans plus a `ToolRequest` of `episode_id`, `route_id` and `attempt_key`. No
  transcript and no `Disposition` crosses (`src/carerelay/coordinator.py:29-37`,
  `:67-105`).
- **The record is append-only.** UPDATE, DELETE and TRUNCATE are refused by trigger on
  every table (`00-status.md:167`, `:640`).
- **Domain purity is machine-checked**, with one detector per forbidden import, and the
  scanner is itself tested with an injected needle (`tests/test_boundaries.py`).
- **Data**: fixture and dyad data only, no real patient data, destroyed 30 days after
  submission (`02-architecture.md:298`). No fixture names a real facility
  (`01-product.md:146`).

### 3.5 Where the AI sits

[verified local integration] ADP interprets confirmed fictional read-back words. It returns source phrases for the action, deadline and person who acts under the six-key v2 schema. CareRelay validates the reply, locates the exact source phrases and compares them with the stored plan in deterministic domain code. The model cannot choose guidance, change a deadline, grant permission, dispatch an action or close an episode. Patient wording comes from the approved renderer.

[verified observation, 16 October 2026] Call 18 passed through the production Next server action, real local FastAPI and HTTPS ADP adapter. One extraction was valid and scored, all three phrases were located, and the screen advanced to the feasibility question in 5,305 ms from confirmation click. The original plan/deadline/owner remained, execution was not_started and closure stayed open. Earlier slow/invalid replies failed closed. Detailed evidence is in `docs/reviews/adp-readback-observations.md`.

[verified accepted scope] The user accepted this bounded fictional demo with seven further live cases unrun. One positive result does not establish general model reliability, clinical safety or full accessibility. ADP is default-off. An offline review uses the explicitly labelled local-sim extractor and must not be presented as a fresh live ADP call. Slice 21 is published on main and the retained slice branch; `00-status.md` owns its receipt. This local proof is not evidence of the hosted site's behavior.

[verified boundary] Real ADP extraction does not make simulated booking or caregiver actions into platform-originated execution. Action origin stays `local-sim`. ADP tool execution is outside this integration; the earlier transport spike supplies no clinical or action-execution claim.

[verified local artifacts] Development-history records, redacted screenshots and the protected WorkBuddy usage video are retained in the repository. Their presence is evidence of the submitted development process, not an organiser acceptance or scoring result.

### 3.6 Key design trade-offs, as the project records them

| Decision | What it buys | What it costs |
|---|---|---|
| Trust boundary is a module boundary (D2) | The rule is checkable | It has to be machine-enforced, or it is a convention with a diagram (`02-architecture.md:28`) |
| Closure derived, never stored (D4) | No write path to false completion | Projection bugs can still lie (`02-architecture.md:333`) |
| Deterministic comparison, model only on interpretation | No model text reaches a patient | The "AI interaction" claim is weaker than a chat demo, and deliberately so |
| Bounded repair, two rounds, then a human path | No infinite loop with a confused user | Some episodes end at the human path (`docs/PLAN.md:216`) |
| Next.js on Vercel instead of server-rendered HTML (D-1b) | Modern accessible frontend, clean split | 20 to 34 person-hours [hypothesis], two extra network boundaries (`02-architecture.md:374`) |
| Scheduled reassessment dropped (D9) | Honest scope before a deadline | The "monitored episode" is **not** delivered; the load-bearing platform answer reverts to "execution substrate" (`02-architecture.md:35`, `:231`) |
| Fixture authored rather than sourced (Option C dropped) | No licensing or applicability risk | The fixture asserts no clinical claim at all (`03-program-design.md:251-256`) |

---

## 4. Business value and impact

**No clinical or behavioural outcome is claimed, because none was measured.** The
comparison study was cut before a single dyad ran, so there is no human-centred
validation result (`00-status.md:38`). The value below is therefore stated as
engineering evidence and as a defined, falsifiable impact.

**Defined impact.** In any care-navigation interface, the states "action attempted",
"action acknowledged", "someone agreed to help" and "care happened" are currently easy
to conflate. CareRelay makes them four different things with four different renderings,
and the patient sees which one applies. The claim is narrow and testable: *the screen
cannot show help as arranged unless the evidence axis says documented*.

**Quantifiable engineering evidence.**

| Measure | Result | When |
|---|---|---|
| Whole suite on the committed tree | **888 passed, 43 skipped, 0 failed** | 11 October 2026, macOS, Python 3.13.12, no Postgres DSN |
| Same tree on the development machine | 856 passed, 0 skipped | 10 October 2026, Windows, where three modules holding 75 tests do not collect (`00-status.md:468`) |
| Tests collected | 931 | 11 October 2026 |
| Seeded fault sequences | **7 sequences, 11 tests**, each asserting the five invariants at both the API and the patient surface | `tests/test_fault_sequences.py` |
| Mutation harnesses | Slice 6 11/11, Slice 7 10/10, Slice 7b 7/7, Slice 8 26/26, Slice 9 46/46, Slice 10 16/16, Slice 11 7/7, Slice 12 10/10, each with 0 survived and every file restored byte-exact | `00-status.md:544-550` |
| Pre-registered kill conditions K1 and K2 | 15 tests, 0 failures | 28 September 2026, deterministic-layer spike (`00-status.md:945`) |
| Live checks | Slices 4, 5, 6, 10, 11 and 12 each walked through against a running server, transcripts in `docs/reviews/` | |

One measured finding is published rather than averaged away: of the five fault
assertions the judge ledger displays, **one is falsifiable today and four are display
only**, because the states that would falsify them are unreachable in this build
(`00-status.md:474-478`). The harness reports that split instead of counting it as
coverage.

**Feasibility.** The stack is ordinary: FastAPI, Postgres, Next.js, one bearer token,
no bespoke infrastructure, no paid model dependency at runtime. The mechanism is
application logic and does not require any particular AI platform
(`03-planback-closure-contract.md:19`), which is the honest answer to "would this
survive the hackathon".

---

## 5. Traceability

| Claim in this document | Proven by |
|---|---|
| Four-line rendering, five copy rules | `01-product.md:60-89`; `02-architecture.md` section 7; `tests/test_domain.py:1430` |
| PlanBack comparison and bounded repair | `tests/test_domain.py:303`, `:441`; `docs/reviews/slice4-walkthrough.md` |
| Closure derivation and its precedence | `src/carerelay/domain/rules.py:444-529`; `tests/test_domain.py:1031`, `:1344` |
| Append-only, on both engines | `tests/test_state.py`; `tests/test_postgres_store.py`; `tests/test_postgres_stage2.py` |
| Domain purity | `tests/test_boundaries.py`, including the injected-needle self-test |
| Auth, CORS, guarded prefixes | `tests/test_api.py`; `tests/test_deployment.py` |
| Fault behaviour under each guard disabled | `tests/test_fault_sequences.py` with per-sequence mutations |
| Ledger, axes, origin, `dwell_seconds` | `tests/test_ledger.py` (29 tests); `tests/_mutate_slice12.py` |
| No model text reaches the patient | `02-architecture.md:302`; the coordinator contract; `tests/test_boundaries.py` |
| No HCD validation | `00-status.md:38`; the cut is pre-recorded in `04-slices.md` section 7 |

---

## 6. Links

| Item | Value |
|---|---|
| Source | `https://github.com/jaydonnnk/carerelay.git` (public) |
| Live frontend | `https://carerelay-self.vercel.app` |
| Recorded API URL | `https://carerelay-dzt3.onrender.com`. Hosted behavior was not refreshed in this local Slice 21 cleanup. Current code requires server-held auth for protected routes; this row is not a new deployment, uptime or hosting-cost claim |
| ADP Experience URL | `https://adp.tencentcloud.com/webim_exp/#/chat/GkTbUc`. Additive read-back extraction only. Slice 21 is wired and demonstrated through the local product, with bounded acceptance and seven live cases unrun. The older conditional Slice 13 remains unbuilt. The AppKey is server-held and is not recorded here. No hosted Slice 21 deployment is claimed |
| Demo video | Not produced. Optional in the requirements |
