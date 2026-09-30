# Architecture: CareRelay urgent-advice accessibility

**Gate 2 — APPROVED 25 September 2026 (revision 2).** Approval authorises the Gate A access spike only; it does **not** authorise implementation code. Gates 3 and 4 remain open, and no code may be written before Gate 4. Authority for the gate state is `00-status.md`.

**Revision 2 incorporated the independent adversarial review at `gate2-adversarial-review-thorough.md` (verdict: APPROVE WITH CHANGES).** Every blocking change in that review's §5 was applied or explicitly resolved. §11 is the change log.

Read first: `00-status.md`, `01-product.md` (approved), `PLAN.md` §5–§6, `DESIGN_PRINCIPLES.md`, `03-planback-closure-contract.md`, `research-workarounds.md`.

---

## 0. What exists today

The repository is documentation-only (`9a1f332`). No code, no tests, no services. `PLAN.md` §6 already fixes the responsibility split — application owns state, WorkBuddy coordinates, MCP tools are narrow, adapters are simulated and labelled. That split was approved with Gate 1.

So Gate 2's job is to **pin the decisions `PLAN.md` left open**, in a form Gate 3 can turn into files and signatures.

**Why revision 2 exists.** The round-2 review found three defects that made this document's own headline claims unimplementable as written: an attempt-state transition with nowhere to be written (§4.1), a tool-execution path described five different ways (§3.3), and a baseline arm that structurally could not measure the success metric (§1-D6, §9). Those three are the reason revision 1 was not approvable, and they are the substance of this revision.

---

## 1. Decisions (D1–D12)

| # | Decision | Why | Reversal |
|---|---|---|---|
| **D1** | **Stack: Python 3.13 + FastAPI + SQLite** (WAL, busy timeout), server-rendered accessible UI (plain HTML/vanilla JS, no framework, no build step) | Matches the mockup style; pydantic models the state; pytest runs the fault harness; fastest solo path | **Trigger: before the first domain-code commit** — not "at the Gate A spike", which cannot answer whether the SDK is better from Node without access. Add an **environment check** (venv, FastAPI + pytest) before Slice 1: `AGENTS.md` records an intermittent AppControl block on stdlib venv creation |
| **D2** | **Trust boundary is a module boundary.** A pure `domain` core owns policy, PlanBack comparison, route-vocabulary validation, closure rules, abstention policy, invariants. It imports **no** network, **no** LLM client, **no** wall clock | "The model interprets. Code decides" must be enforceable by imports, not discipline. Round-2 review calls this the strongest decision here | Not reversible without reopening Gate 1. **Gate 3 must name the enforcing check and make it fail-capable**, or this is a convention with a diagram |
| **D3** | **Append-only clinical record.** Dispositions, attempt transitions, evidence, consents are INSERT-only. The deadline lives on the disposition row; reassessment inserts a new version | I1 (immutable deadline) holds because **no retry code path writes a disposition**. **Restated honestly in §10:** that is a code-review property, not a structural impossibility | Not reversible — this is the Closure Contract |
| **D4** | **Closure is derived, never stored.** A pure function of (attempt projection, evidence axis, deadline, **recorded expiry event**, **human-acceptance record**, now) | Nothing in the system can *write* "resolved". Removes the write path for false completion — a real gain | Not reversible. **Amended:** closure inputs now include `human_acceptances` and `expiry_events`, both of which revision 1 omitted (§4.2) |
| **D5** | **Clock and idempotency are ports, with specified key derivation.** All time via injected `Clock`; **the server generates one idempotency key per (episode, route, attempt-purpose)**; the client never supplies one | Round-2 surface C: if the client generates a key per request, a double-tap produces two keys, I3 never fires, two tool calls dispatch, and the episode holds mixed attempt state. Server-generated keys are what make I3 real | Not reversible after Slice 2 |
| **D6** | **The baseline is an external artefact, not an app arm.** The comparator is a **fixed bilingual card + direct booking link + the approved human route, delivered outside the application** (printed/PDF). Measurement is **between-subjects**. The card condition receives a **scripted post-failure question** so the same false-completion outcome is measurable in both conditions | Revision 1's in-app `arm` flag could not produce the metric: a static card has no failed handoff, so the card arm could never be scored on false completion — the one outcome the reframe rests on. It also erased the card's lowest-burden advantage by wrapping it in app chrome, and within-subject crossover leaked PlanBack comprehension into the card arm. All three defects removed | Reversible. **Pre-registration required** (§9): primary outcome, cut rule and N written before results |
| **D7** | **Abstention is deterministic policy, and the free-text → policy boundary is specified.** Symptom-change input goes through a **closed-vocabulary classification step (coordinator, structured output) whose value is validated against the policy's permitted input set in `domain`**; anything outside the set is *critical uncertainty* → human path | Revision 1 required the urgent path to bypass the coordinator for rendering without saying who classifies free-text symptom change. That gap is the round-2 D7 finding: either a model call (contradicting the bypass) or a keyword rule (contradicting the split). The answer is a closed vocabulary with **fail-to-human as the default** | Not reversible without reopening Gate 1 |
| **D8** | **Coordinator channel, with the tool-execution path pinned (§3.3).** Backend ↔ WorkBuddy managed agent via cloud-agent SDK. **The coordinator executes the tool; the platform emits the failure event.** Our backend is the MCP server enforcing authorisation, consent and idempotency. Coordinator returns structured outputs only and **never** writes to the database | Revision 1 described this five different ways across §2, §3.2, §3.3 and §5.1, so Gate 3 could legitimately wire a direct backend call — leaving the demo visually identical and the platform-failure claim unsupported. §3.3 now states one normative call path, and the **failure-event origin is recorded and shown in the ledger** so the platform path and the fallback are distinguishable by inspection | Reversible to local simulation at the Gate A decision point, with the dependency claim weakened (§6 item 5) |
| **D9** | **DROPPED.** The scheduled-reassessment module is removed from this architecture and recorded as a Gate A / planning question (§6 item 6) | Round-2 review: no scenario, no trigger, no recheck content, no ingress endpoint, no estimate, and an 8-hour cadence that contradicts a same-day deadline — it could not be walked. It was also the only place the P1 load-bearing claim could be proven, which makes it a planning decision, not a module. Keeping it would have let an unestimated, unbuildable module sit inside an approved architecture | Recoverable as a documented future slice **once Gate A passes and it has a scenario and an estimate**. **Cost of the cut stated plainly** (§6 item 6): the P1 answer reverts to "execution substrate" |
| **D10** | **Mandarin voice is an isolated, deferred module.** The text path is complete without it. Voice plugs into the *same* restatement endpoint as a new `input_mode`, behind the transcript-confirmation rule and the zero-silent-critical-fact release gate | TRTC is a gated spike, not a core clinical channel | Cut under schedule pressure (but see the corrected order below) |
| **D11** | **(NEW) Evidence provenance invariant.** `evidence.level = documented` requires a **non-simulated, sourced artefact**, enforced by a `CHECK` constraint — not by convention. Every evidence row carries `simulated`, and **the patient projection serialises the simulated label inside the four-line surface**, not only in page chrome | Round-2 surface B item 6 and the missing fault class "adapter returns 200 with a lie": otherwise D4's `closed_with_evidence` accepts a scripted receipt as proof that care happened | Not reversible — this is what makes "no false completion" hold for *evidence* as well as execution |
| **D12** | **(NEW) Expiry is a recorded event, not a read-time guess.** A persisted `expiry` event is written when the deadline passes unresolved (if not already set), and **expiry is sticky — a backwards clock does not un-expire an episode** | Round-2 surface C: derived-only expiry means a clock regression silently resurrects an expired episode, and nothing runs at the deadline. The event makes "the deadline passed unresolved" auditable rather than inferred | Not reversible |

**Pre-agreed cut order — corrected per round-2 §7:**

1. **D9 — already cut in this revision.** Revision 1 listed voice first, which was decorative: voice was already deferred, so cutting it freed nothing.
2. **Second simulated adapter + `notify_caregiver`.** The caregiver is a named owner *string* on the four-line screen, not a channel. The MCP surface drops to three tools (§3.2).
3. **Chinese UI strings**, if no native reviewer is secured by mid-October. The release gate applies to critical Chinese *strings*, not only voice (`research-workarounds.md`).
4. **TRTC voice.**
5. Anything beyond one route, one adapter, one caregiver name.

---

## 2. Fit

```
Patient / caregiver UI  (server-rendered, text-first, one question at a time
                         — enforced by the projection, not by page layout)
        |
Application API (FastAPI)  — authorisation boundary, server-generated idempotency,
                             consent stamped on the attempt and re-checked at record
        |
        +-- domain/            pure core: policy, PlanBack comparator, route-vocabulary
        |                      validation, closure rules, abstention policy, invariants.
        |                      No I/O, no LLM, no clock.
        +-- state/             append-only repositories (SQLite, WAL), derived projections
        +-- adapters/          ONE scripted simulated clinic/booking adapter (port)
        +-- coordinator/       WorkBuddy session client: scoped snapshots out,
        |                      structured results in. Stateless about clinical facts.
        +-- tools/             MCP server over the application API (authorisation,
        |                      consent, idempotency enforced here)
        +-- harness/           7 seeded fault sequences, fixed-utterance suite, baseline runner
        |
WorkBuddy managed agent (coordinator)  — interprets, clarifies, classifies the
        closed vocabulary, proposes, executes tools, resumes.
        The platform emits the failure events.
```

Boundary rules Gate 3 must not soften:

- `domain` never imports `coordinator`, `adapters`, or an SDK. Flow: **coordinator proposes → `domain` validates → state records.**
- The coordinator **never** writes to the database and **never** sees credentials. It reaches the world only through the MCP tool surface.
- **Every coordinator-proposed route id, and every classified symptom-change value, is validated in `domain` against the policy's permitted set before it can cause an action.** A hallucinated id must not reach the tool layer. Revision 1 had this check only for PlanBack's `action` comparison.
- `adapters` carry `simulated: true` on every response; the flag flows into the evidence row **and** into the patient projection (D11).

---

## 3. Endpoints

### 3.1 UI-facing API (`/api`)

| Route | Verb | Purpose |
|---|---|---|
| `/api/episodes` | POST | Create episode `{persona}`; loads the policy fixture. **Does not write a disposition** — that follows assessment (§5.1) |
| `/api/episodes/{id}/intake` | POST | **NEW.** The patient's initial description. Coordinator clarifies; proposals validated in `domain` before becoming reported facts |
| `/api/episodes/{id}/clarifications` | GET / POST | **NEW.** The current clarifying question and the answer — one question at a time |
| `/api/episodes/{id}/options` | GET | **NEW.** Permitted routes for this disposition, rendered from policy. Revision 1 had this only as an MCP tool, so the UI had nothing to display |
| `/api/episodes/{id}` | GET | Patient projection — four lines (or the expired rendering, §7), with the simulated label serialised in |
| `/api/episodes/{id}/transcript-confirmations` | POST | Confirm/correct a voice transcript **before** any evaluation (Gate 1 ordering rule) |
| `/api/episodes/{id}/restatements` | POST | `{input_mode, text, hint_level}` → coordinator extracts → **`domain` compares** → `{mismatches[]}` or `understanding_confirmed` |
| `/api/episodes/{id}/restatements/{rid}/repairs` | POST | Field-scoped repair, hard-capped at 2; third mismatch routes to the human path |
| `/api/episodes/{id}/hint-events` | POST | Hint escalation and the persistent "show my plan" escape — always records level/outcome |
| `/api/episodes/{id}/barriers` | POST | Report a practical barrier; coordinator proposes a permitted **route id, validated in `domain`** |
| `/api/episodes/{id}/consents` | POST | Grant/revoke clinical scope. **Version stamped on each attempt**, re-checked at record time (§4.1) |
| `/api/episodes/{id}/actions` | POST | Execute: authz + consent + **server-generated idempotency key** → coordinator executes the tool → append `attempt_opened` |
| `/api/episodes/{id}/callbacks/{route_id}` | POST | Platform / adapter callbacks (ack / fail / evidence). Dedupe on `callback_key`; reorder-safe; **origin recorded** (`platform` \| `local-sim`) |
| `/api/episodes/{id}/acceptances` | POST | **NEW.** Records explicit human acceptance — a D4 closure input with no table or endpoint in revision 1 |
| `/api/episodes/{id}/escalations` | POST | **NEW.** Records the handoff to a named human path; gives `escalated_to_human` a recording path and a resume rule |
| `/api/episodes/{id}/reassessments` | POST | Classify (closed vocabulary) → abstention policy → emergency stop **or** insert disposition v2 — the only path that may set a new deadline |
| `/api/episodes/{id}/ledger` | GET | Judge-facing two-axis ledger, event log, **failure-event origin**, fault assertions. Never the patient screen |
| `/api/study/{session_id}/responses` | POST | Baseline outcome questionnaire, including the post-failure question in the card condition |

### 3.2 MCP tool surface

**Three tools** — cut from six under the corrected cut order. `notify_caregiver` is removed (the caregiver is a name, not a channel); `list_simulated_options` and `propose_action` are removed as separate tools because they were a UI read and a coordinator proposal, not world-touching operations.

`get_episode` · `submit_simulated_request` · `record_evidence`

All three: server-side authorisation, consent re-checked at record time, server-generated idempotency keys, simulated label on every response.

### 3.3 The tool-execution path — pinned (was round-2 Finding 2)

**One call path. This is normative; Gate 3 must not wire the alternative.**

1. `POST /actions`: authorisation, consent (version stamped), server-generated idempotency key → `attempt_opened` row written.
2. Backend sends the coordinator a scoped snapshot containing the permitted route id and the attempt key, via the cloud-agent SDK session.
3. **The coordinator executes the tool through the platform's tool mechanism.** The platform is in the path.
4. The failure event **originates in the platform** and returns through the SDK to our backend, carrying an origin marker.
5. Backend appends the transition row with `origin = platform`.
6. **The ledger and the judge view display the origin marker.** A platform failure and a local simulation failure are therefore **distinguishable by inspection** — which revision 1 could not guarantee.

**Why normative rather than stylistic:** the submission claims a real platform tool failure occurred. If the backend called the adapter directly, the demo would look identical on screen. The origin marker is what makes the claim checkable, and it is also what keeps the Gate A fallback honest — a local-sim failure is labelled as such in the same field.

---

## 4. Data

SQLite (WAL, busy timeout) behind repository interfaces. Clinical tables INSERT-only.

### 4.1 Attempts — the round-2 Finding 1 fix

**What was broken in revision 1:** `attempts` was declared INSERT-only *and* given a mutable `status` enum, deduped on a `UNIQUE` idempotency key. An acknowledgement had nowhere to go: an UPDATE violated the append-only claim, and an INSERT of a second row was swallowed silently by `ON CONFLICT DO NOTHING`. The acknowledgement would be lost, the patient would see "help is not arranged" while the clinic had accepted — a **false negative completion**, a state the product had no rule for — and four of the seven seeded fault sequences would have been unwritable.

**Resolution — an immutable attempt identity plus append-only transitions:**

| Table | Key columns | Notes |
|---|---|---|
| `attempts` | id, episode_id, route_id, **idempotency_key UNIQUE**, **consent_version**, opened_at | **Immutable identity row.** One per attempt, written once. No status column |
| `attempt_transitions` | id, attempt_id, seq, transition (`acknowledged`\|`failed`\|`superseded`), origin (`platform`\|`local-sim`), payload, recorded_at | **Append-only.** Current status = **latest transition by `seq`, else `attempted`** |
| `callbacks` | id, route_id, **callback_key UNIQUE**, received_at, payload, accepted | Records *every* callback received, including rejected duplicates. Dedupe is asserted over a surface that can hold it |

**Ordering rule (revision 1 had none):** transitions carry a monotonic `seq` assigned on append. An `acknowledged` arriving after a `failed` is **retained and non-winning** — terminal states are absorbing, and the first terminal transition in `seq` order defines the status. The reordered callback is recorded, and the assertion is writable.

**Transaction boundary (revision 1 had none):** the `attempt_opened` row, its initial `events` row, and any `evidence` row created in the same logical step are written **in one transaction**. A crash between them is not a representable state.

**Idempotency (D5):** the server generates the key per (episode, route, attempt-purpose). A double-tap produces the *same* key, hits `UNIQUE`, and becomes a no-op that is **recorded** — not silently discarded.

### 4.2 Remaining tables

| Table | Key columns | Notes |
|---|---|---|
| `episodes` | id, persona, created_at | No closure column — derived (D4). The `arm` column is **removed** with D6 |
| `dispositions` | id, episode_id, version_no, policy_version, action, **clinical_deadline**, next_owner, fallback_route, source (`fixture`\|`reviewer`\|`reassessment`), created_at | INSERT-only; the deadline changes only by inserting a version (D3) |
| `evidence` | id, episode_id, level (`self_reported`\|`documented`), **simulated (bool)**, provenance, source_ref, recorded_at | **D11 `CHECK`:** `level = documented` requires `simulated = false` **and** non-null `source_ref`. Absence of a row = `none`, never a negative finding (I5) |
| `consents` | id, episode_id, scope, state, version, recorded_at | Current = latest per scope; revocation is a new row with a new version |
| `human_acceptances` | id, episode_id, accepted_by, scope, recorded_at | **NEW** — a D4 closure input with no home in revision 1 |
| `escalations` | id, episode_id, human_path, outcome, recorded_at | **NEW** — records the handoff; `escalated_to_human` had no recording path |
| `expiry_events` | id, episode_id, disposition_version, occurred_at | **NEW (D12)** — makes expiry sticky under clock regression |
| `restatements` | id, episode_id, disposition_version, **hint_level**, input_mode, transcript_confirmed, extracted_json, mismatches, repair_round, outcome (`recall_unaided`\|`recall_scaffolded`\|`recall_cued`\|`not_recalled`), created_at | `hint_level` is non-nullable — without it the evaluation is worthless |
| `events` | id, episode_id, kind, payload, recorded_at | Audit log; feeds the judge ledger. **`payload` is redacted of clinical free text** (§8) |
| `policy_versions` | id, version, content, provenance, approved_by, created_at | Fixture labelled `fixture` until a reviewer exists |
| `study_sessions`, `study_responses` | dyad id, condition, outcomes, task times | **Research-participant consent tracked separately** from clinical `consents` (§8) |

**Queries that will hit them:**

- *Patient projection*: episode + latest disposition + latest transition per attempt + latest evidence level + expiry event → four lines (or the expired rendering), with the simulated label serialised in.
- *Closure derivation*: pure function over that projection + `Clock.now()` + the recorded expiry event.
- *Invariant assertions*: all seven fault sequences read `attempts` + `attempt_transitions` + `callbacks` + `expiry_events` — all four now exist, which is what makes the harness writable.
- *Gate B analysis*: `study_responses` by condition.

---

## 5. Flow

### 5.1 Main path (the five-minute demo)

1. `POST /episodes` → policy fixture loaded. **No disposition yet.**
2. **Assessment intake (missing entirely from revision 1):** `POST /intake` → coordinator clarifies via `/clarifications`, one question at a time → reported facts recorded with provenance. This is Challenge 1's first listed behaviour, and revision 1's product had no path for it.
3. `domain` writes disposition v1: deadline set **once**; permitted routes available at `/options`.
4. **PlanBack:** restatement (constrained chips or free text; voice later) → if voice, `transcript-confirmations` first → coordinator extracts `{action, deadline, next_owner}` → **`domain` compares** (time bucket, closed action vocabulary, named owner) → mismatch: one field named, repair ≤2 → every round records its hint level.
5. **Barrier:** coordinator proposes a permitted route id → **validated in `domain`** → consent confirmed → `POST /actions` with a server-generated key.
6. **Execute:** the pinned path of §3.3. The coordinator executes the tool; the adapter fails as scripted; **the failure event originates in the platform**; a transition is appended with `origin = platform`; the attempt is `failed`, evidence stays `none`, **the deadline is untouched** → the patient screen shows the four lines.
7. **Interrupt/resume:** the session is dropped; resume = WorkBuddy session restore **+** reload of application-owned state → UI identical, deadline unchanged.
8. **Injected duplicate callback** → recorded in `callbacks`, hits `UNIQUE`, no transition appended → the ledger shows the dedupe, not a state change.
9. `GET /ledger` renders axes, events, **failure-event origin** and fault assertions.

### 5.2 Reassessment / abstention path

Symptom-change input → **closed-vocabulary classification (D7)** → `domain` abstention policy → either the emergency/human stop screen renders synchronously, **or** a versioned reassessment inserts disposition v2 — the only code path that may set a new deadline, never rewriting v1.

**Post-stop state (revision 1 left this unreachable and unexitable):** an emergency stop writes an `escalations` row and leaves the episode `escalated_to_human`. That is **terminal for the conversational flow** — re-opening requires a new reassessment, which writes a new disposition version. There is no silent resume.

### 5.3 Scheduled path

**Removed with D9** (§6 item 6).

---

## 6. External

| External | Role | Env var **names** (never values) |
|---|---|---|
| WorkBuddy managed agent | Coordinator: sessions, streaming, **tool execution**, failure events, resume | `WORKBUDDY_API_KEY`, `WORKBUDDY_AGENT_ID`, `WORKBUDDY_API_BASE` |
| Simulated clinic/booking adapter (**one**, not two) | Scripted availability + receipts, labelled | `SIM_ADAPTER_MODE=scripted` |
| TRTC (deferred spike, D10) | Push-to-talk Mandarin ASR; TTS reads reviewed text verbatim | `TRTC_SDK_APP_ID`, `TRTC_SECRET_KEY` |
| App config | — | `APP_DATABASE_URL`, `APP_CLOCK=scenario\|system` |

No real healthcare endpoints exist anywhere. Adapter callbacks are local-only. **No fixture, string or receipt names a real facility** (Gate 1 rule).

**Gate A spike must answer (time-boxed, decision 26 Sep):**

1. Auth scheme — `x-api-key` vs Bearer (the docs conflict); region/quota reality.
2. Session create / stream / resume across a genuine process restart.
3. **Tool execution through the platform, and whether failure events arrive with a usable origin signal** — now load-bearing for §3.3, not incidental.
4. Managed scheduler access from a non-enterprise account — relevant **only** if D9 is later revived; not blocking this architecture.
5. If 1–3 fail → the §3.3 fallback: local simulation with `origin = local-sim` in the same field, honest label, **CodeBuddy development history carries the usage-proof requirement**, and the platform-advantage claim is weakened and stated as weakened.

**6.5 Usage-proof obligation (new — round-2 finding E2).** The mandatory proof is *development* history plus at least three chat screenshots. `.gitignore` correctly excludes `.codebuddy/` and `.workbuddy-ai/`, so this must be **captured deliberately, from the first CodeBuddy session, by a named person, into a named location, starting now.** It is the one artefact whose absence blocks scoring entirely. Revision 1 mapped this risk to D8, which does not produce it.

**6.6 The honest cost of dropping D9.** The P1 load-bearing answer reverts to "execution substrate": coordinator, real tool call, real failure event, session resume. `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is not delivered by this architecture. That is the trade, it is deliberate, and the submission states it rather than implying a capability that is switched off.

---

## 7. The expired patient screen (was undefined)

`01-product.md` fixes four lines whose third is "Before [deadline]" — wording that presumes a future deadline. After expiry that line is false, and revision 1 had no expired rendering anywhere. **The one state the product exists to report had no approved words.**

**Approved by the user 25 September 2026**, on the condition that the wording is not aggressive. The first draft ("The time to go was [deadline]. It has passed." / "Call [route] now") was rejected as too blunt for a frightened older adult. The rendering below is short, warm and forward-looking: it states the situation plainly, keeps the original deadline visible as fact rather than as a reproach, and puts the next step in the present tense.

| Line | Pre-deadline | Expired |
|---|---|---|
| 1 | Help is not arranged. | Help still is not arranged. |
| 2 | You or *[named person]* must act now. | You can still do this. |
| 3 | Before *[deadline]*. | It is past *[deadline]*, so please go now. |
| 4 | If this route fails, call *[approved human route]*. | Call *[approved human route]* — they can help from here. |

**Copy rules for this screen** (so later edits do not drift back):

- **No reproach.** Never "you did not", "you missed", "too late", "failed", or a bare "now" as an imperative.
- **No alarm.** No red urgency styling on this screen; the emergency path is reached through line 4's route, not through alarm on a missed appointment.
- **No false comfort.** It still says the help is not arranged. The softness is in the tone, not in the facts.
- **Line 4 always names a real route** — 995 remains available, but the screen leads with the ordinary care route rather than the emergency number for a non-emergency expiry.
- **The deadline stays visible.** Removing it would erase the fact the product exists to preserve.

---

## 8. Non-functional surfaces (added — all were absent from revision 1)

| Surface | Decision |
|---|---|
| **Deployment** | **Local-only demo** (`uvicorn` on `127.0.0.1`) for the judged walkthrough. The optional live-link bonus is **not** taken, because it would turn an unauthenticated clinical-shaped API into a public endpoint. Stated so it is a choice, not an omission |
| **Auth** | No auth on `/api` in the local-only demo; `/ledger` is judge-facing and local. If a live link is ever added, auth is a precondition, not a follow-up |
| **Secrets** | Env vars only (§6); `.env` gitignored. Held in the operator's shell for the demo, never committed, never in screenshots |
| **Data retention / PDPA** | **Fixture and dyad data only; no real patient data.** Retention: destroyed 30 days after submission. Erasure and append-only are reconciled by **deleting the database file**, not by row surgery — recorded explicitly because the tension is real (`PLAN.md` §8) |
| **Observability & logging** | `events.payload` may contain clinical free text. **Payloads are redacted from application logs**; the ledger reads the table directly. No third-party telemetry |
| **Latency & cost** | Measured and recorded during Gate A — Feasibility is a scored dimension that asks for measured latency. The demo path pre-warms the session and sets explicit timeouts |
| **Degraded states** | **NEW branch:** coordinator unavailable or slow → the flow **stops** at the current question and shows a text fallback, because a coordinator stall on the PlanBack critical path is a demo-ending failure. Adapter timeout → `failed` transition. No permitted route → human path. Deadline passed with no action → expiry event + expired screen |
| **Model-generated text boundary** | `domain` renders all patient-facing clinical text from policy. **No model-generated text reaches the patient.** Coordinator outputs are structured values only, validated in `domain`. Round-2 surface B item 5 noted revision 1 achieved this only by omission; it is now a stated rule |
| **Accessibility — two architectural items** | (a) **One-question-at-a-time is enforced by the patient projection**, not by page layout. (b) **No timers anywhere** — the H2 card stays until the patient hides it (Gate 1 §5.2.1, reopened and re-approved 25 Sep). `dwell_seconds` is recorded for the ledger and never shown to the patient |
| **Research-participant consent** | Tracked separately from clinical `consents` |

---

## 9. The baseline study — pre-registration (D6)

**Condition A — CareRelay.** The full assessed flow.
**Condition B — fixed card.** A printed/PDF bilingual card with **identical clinical wording**, the same permitted options, a **direct booking link**, and the approved human route. Delivered **outside the app**.

| Item | Value |
|---|---|
| Design | **Between-subjects**; dyads assigned to one condition |
| N | Target 6 per condition; **minimum 3 per condition** or no HCD claim (`research-workarounds.md`) |
| Primary outcome | **False completion:** proportion who report that care is arranged when it is not |
| Secondary | Action recall, deadline recall, **hint level** per PlanBack outcome, unresolved-barrier recognition, task time, burden |
| Card-condition procedure | Participant receives the card; is told the booking link was tried; is asked whether care is arranged |
| Pre-registered cut rule | **PlanBack is cut if** the card achieves equal action/deadline recall with lower burden; **or** any critical correct statement is flagged as a mismatch; **or** emergency guidance is delayed by read-back |
| Blinding | The scorer does not know the hypothesis. Raw outcomes reported; no percentages below n=10 |

---

## 10. Claims restated at the level they actually hold

Revision 1 claimed more rigour than its mechanisms provided. Corrected:

| Revision 1 claim | Now |
|---|---|
| I1 holds "by construction" | I1 holds because **no retry code path writes to `dispositions`** — enforced by module boundary plus code review. A property to test, not a structural impossibility |
| "Nothing can launder a simulated receipt into a real one" | Enforced by **D11**: a `CHECK` constraint plus a provenance test. Before that constraint existed, the claim was unproven |
| Closure is derived, so false completion is impossible | Closure is derived, so **there is no write path that sets `resolved`**. False completion is still reachable through projection bugs; revision 2 closes the four identified paths — consent/evidence provenance (D11), expiry stickiness (D12), transaction boundary (§4.1), simulated-label serialisation (§8) |
| D9 delivers the P1 load-bearing proof | **D9 is cut.** The honest answer is "execution substrate" (§6 item 6) |

---

## 11. Change log — review finding → resolution

| Round-2 finding | Resolution | Section |
|---|---|---|
| §5.1 Attempt state unrepresentable (§4) | Immutable `attempts` + append-only `attempt_transitions` + `callbacks`; ordering rule; transaction boundary | §4.1 |
| §5.2 Tool execution path unpinned | One normative call path; coordinator executes; origin marker recorded and shown | §3.3, §1-D8 |
| §5.3 D6 cannot measure the metric | External card artefact; between-subjects; scripted post-failure question; pre-registered | §1-D6, §9 |
| §5.4 Missing endpoints and tables | Intake, clarifications, options, acceptances, escalations added | §3.1, §4.2 |
| §5.5 Decide D9 | **Dropped**, with the cost stated | §1-D9, §6.6 |
| §5.6 Degraded branch + text boundary | Degraded states added; "no model text reaches the patient" stated as a rule | §8 |
| §5.7 Two invariants and one rule | D11 evidence provenance, D12 expiry stickiness, consent version stamped on the attempt | §1, §4.1 |
| §5.8 Restate safety claims | §10 restatement table; simulated label serialised into the projection | §10, §8 |
| §5.9 Expired screen has no words | Proposed rendering, flagged for Gate 1 sign-off | §7 |
| §5.10 Stale mirrors, mockup numbering | `DESIGN_PRINCIPLES.md` §12, `03-planback-closure-contract.md`, `tasks/todo.md`, `00-status.md` line 78, mockups 01 and 04 | applied |
| §5.11 H2 timed hide | **RESOLVED 25 Sep** — Gate 1 reopened and re-approved: the timer is gone, the card stays until the patient hides it, no timers anywhere in the product (`PLAN.md` §5.2.1) | §8, §10 |

---

## 12. What this architecture still does not decide

- File layout, type definitions, method signatures → **Gate 3**.
- Slice order → **Gate 4**. **Requirement carried forward from round 2: Gate 4 must sequence the baseline comparison (Gate B) *before* the Closure Contract build.** Revision 1 pinned the stack (D1) and the comparison design (D6) before the falsifier had run; that is defensible **only** if the kill test is sequenced first. `PLAN.md` §7 currently schedules sessions for 1–7 October, *after* the state machine — the wrong order, to be corrected at Gate 4.
- **Effort.** Round 2 estimates **90–150 h** for this architecture's build against the 56–89 h it inherited, plus 20–35 h for the baseline. That is **not affordable in 21 days** with Gate 3, Gate 4, recruitment, clinical chasing and submission assets outstanding. **Either the estimate or the scope changes at Gate 3, and this document does not pretend otherwise.** The D9 cut, the MCP reduction and the single adapter are the first tranche.
- **The H2 accessibility hazard is resolved.** Gate 1 was reopened and re-approved on 25 September 2026: the five-second timer is removed and the plan card stays until the patient hides it. **No timer, countdown or auto-advance exists anywhere in the product.** `dwell_seconds` is recorded for the judge ledger only. See `PLAN.md` §5.2.1.
- Whether D9 is revived → after Gate A, with a scenario and an estimate.

**Next action regardless of approval:** the **Gate A access spike is due tomorrow, 26 Sep** — credential check, session create/resume across a restart, and **one tool executed through the platform whose failure event is observed to carry an origin signal** (now load-bearing for §3.3). Approval of Gate 2 authorises the spike only, not implementation code.
