# Architecture: CareRelay urgent-advice accessibility

Gate 2 draft — 25 September 2026. **Not approved.** This document authorises no code.
Read first: `00-status.md`, `01-product.md` (approved), `PLAN.md` §5–§6, `DESIGN_PRINCIPLES.md`, `03-planback-closure-contract.md`, `research-workarounds.md`.

## 0. What exists today

The repository is documentation-only (`9a1f332`). No code, no tests, no services. `PLAN.md` §6 already fixes the responsibility split — application owns state, WorkBuddy coordinates, MCP tools are narrow, adapters are simulated and labelled. That split was approved with Gate 1.

So Gate 2 is not a blank-page design. Its job is to **pin the decisions `PLAN.md` deliberately left open**, in a form Gate 3 can turn into files and signatures. Anything `PLAN.md` already settled is referenced, not re-decided.

---

## 1. Decisions (D1–D10)

| # | Decision | Why | Reversal |
|---|---|---|---|
| **D1** | **Stack: Python 3.13 + FastAPI + SQLite**, server-rendered accessible UI (plain HTML/vanilla JS, no frontend framework, no build step) | Matches the throwaway-mockup style; pydantic models the two-axis state; pytest runs the fault harness; fastest solo path | **Trigger: Gate A spike (due 26 Sep).** If the managed-agent SDK works materially better from Node, switch to Node/TypeScript **before Slice 1 code exists**. After that the decision is final. |
| **D2** | **Trust boundary is a module boundary.** A pure `domain` core owns policy, PlanBack comparison, closure rules, abstention policy, invariants. It imports **no** network, **no** LLM client, **no** wall clock | "The model interprets. Code decides" must be enforceable by import rules, not by discipline | Not reversible without reopening Gate 1 |
| **D3** | **Append-only clinical record.** Dispositions, attempts, evidence, consents are INSERT-only. The deadline lives on the disposition row; reassessment inserts a new version and re-points the episode | I1 (immutable deadline) holds **by construction**, not by convention | Not reversible — this is the Closure Contract |
| **D4** | **Closure is derived, never stored.** Closure state is a pure function of (attempts, evidence axis, deadline, now, human acceptance), computed at read time | Nothing in the system can *write* "resolved" — I2 (no false completion) has no code path to violate | Not reversible |
| **D5** | **Clock and idempotency are ports.** All time reads go through an injected `Clock`; every mutating endpoint and tool takes an `idempotency_key` enforced by a unique constraint | The 7 seeded fault sequences (duplicate, reorder, restart, clock change…) are impossible to test honestly otherwise | Not reversible after Slice 2 |
| **D6** | **The baseline arm is first-class.** `episodes.arm ∈ {carerelay, card}`. Same backend, same policy content; the `card` arm serves the fixed bilingual card + booking link + NurseFirst fallback with PlanBack and the ledger disabled | Gate B is the primary kill test and must run on **identical clinical wording** — one codebase, two arms, counterbalanced dyads | Reversible; low cost |
| **D7** | **Abstention is deterministic policy plus a first-class recorded outcome**, in the domain core. Symptom change, missing critical facts, contradictions, out-of-scope input → stop the conversational flow → emergency/human handoff (mockup 04). **The urgent path never passes through the coordinator** — urgent guidance renders synchronously from policy | Urgent guidance must appear before teach-back and must never wait on a model call | Not reversible without reopening Gate 1 |
| **D8** | **Coordinator channel:** backend ↔ WorkBuddy managed agent via the cloud-agent SDK. Backend sends **scoped context snapshots** (current question, confirmed facts — never raw episode history it doesn't need); coordinator returns **structured outputs only** (extracted fields, clarification proposals, tool proposals). MCP tools are executed server-side by our backend with authorisation + consent checked **at execution** | This is the honest WorkBuddy dependency already approved: coordinator, real tool call, real failure event, session resume. Exact wiring is a Gate A spike question (§6) | Reversible to local-simulation fallback at the 26 Sep decision point, with the dependency claim weakened accordingly |
| **D9** | **Conditional scheduled-reassessment module.** Multi-day episode persistence is included (it is free — durable state). The WorkBuddy scheduled recheck loop (`DESIGN_PRINCIPLES.md` §8) is a **defined but inactive** module: activated only if Gate A passes **and** Gate 3 estimates it honestly. Urgent escalation is **never** routed through the managed scheduler (verified 5-minute floor, enterprise-owned) | The P1 audit's candidate load-bearing proof, without betting the submission on unproven access | If Gate A fails: module stays dark, Gate C answer reverts to "execution substrate" |
| **D10** | **Mandarin voice is an isolated, deferred module.** The text path is complete without it. Voice plugs into the *same* restatement endpoint as a new `input_mode`, behind the Gate 1 transcript-confirmation rule and the zero-silent-critical-fact release gate (`research-workarounds.md`) | TRTC is a gated spike, not a core clinical channel | Cut first under schedule pressure |

**Pre-agreed cut order under deadline pressure:** (1) TRTC voice → (2) scheduled-reassessment loop → (3) anything beyond one caregiver channel. Module isolation exists so these cuts are cheap and do not scar the core.

---

## 2. Fit

```
Patient / caregiver UI  (server-rendered, text-first, one question at a time)
        |
Application API (FastAPI)  — authorisation boundary, idempotency, consent at execution
        |
        +-- domain/            pure core: policy, PlanBack comparator, closure rules,
        |                      abstention policy, invariants. No I/O, no LLM, no clock.
        +-- state/             append-only repositories (SQLite), derived projections
        +-- adapters/          simulated clinic/booking + simulated caregiver channel
        |                      (ports; scripted; labelled simulated end-to-end)
        +-- coordinator/       WorkBuddy session client: scoped snapshots out,
        |                      structured results in. Stateless about clinical facts.
        +-- tools/             MCP tool surface over the application API
        +-- harness/           7 seeded fault sequences, fixed-utterance suite, baseline runner
        |
WorkBuddy managed agent (coordinator)  — interprets, clarifies, proposes, resumes
```

Boundary rules that Gate 3 must not soften:

- `domain` never imports `coordinator`, `adapters`, or an SDK. Flow is: coordinator proposes → domain decides → state records.
- The coordinator **never** writes to the database and **never** sees credentials. It reaches the world only through `tools/`.
- `adapters` carry `simulated: true` on every response; that flag flows into evidence records and the UI projection. Nothing can launder a simulated receipt into a real one.

---

## 3. Endpoints

### 3.1 UI-facing API (`/api`)

| Route | Verb | Purpose |
|---|---|---|
| `/api/episodes` | POST | Create episode `{arm, persona}`; loads policy fixture; sets `clinical_deadline` **once**; returns plan card |
| `/api/episodes/{id}` | GET | Patient projection — the four lines + current card state (closure derived at read) |
| `/api/episodes/{id}/transcript-confirmations` | POST | Confirm/correct a voice transcript **before** any evaluation (Gate 1 ordering rule) |
| `/api/episodes/{id}/restatements` | POST | Submit restatement `{input_mode, text, hint_level}` → coordinator extracts → domain compares → `{mismatches[]}` or `understanding_confirmed` |
| `/api/episodes/{id}/restatements/{rid}/repairs` | POST | Field-scoped repair round, hard-capped at 2; third mismatch routes to human path |
| `/api/episodes/{id}/hint-events` | POST | Hint escalation and the persistent "show my plan" escape — always records the level/outcome |
| `/api/episodes/{id}/barriers` | POST | Report a practical barrier; coordinator proposes a permitted alternative route from policy |
| `/api/episodes/{id}/consents` | POST | Grant/revoke scope; checked again **at execution**, revocation honoured mid-episode |
| `/api/episodes/{id}/actions` | POST | Execute chosen route: authz + consent + idempotency key → tool call → append attempt |
| `/api/episodes/{id}/callbacks/{route_id}` | POST | Simulated-adapter callbacks (ack/fail/evidence); dedupe on idempotency key; reorder-safe |
| `/api/episodes/{id}/reassessments` | POST | Symptom change → abstention policy → emergency stop, **or** insert disposition v2 (only path that may set a new deadline) |
| `/api/episodes/{id}/ledger` | GET | Judge-facing two-axis ledger, event log, fault-sequence assertions. Never the patient screen |
| `/api/study/{session_id}/responses` | POST | Baseline-arm outcome questionnaire (Gate B records, incl. hint levels where applicable) |

### 3.2 MCP tool surface (unchanged from `PLAN.md` §6)

`get_episode` · `list_simulated_options` · `propose_action` · `submit_simulated_request` · `notify_caregiver` (simulated) · `record_evidence`

All six: server-side authorisation, consent re-checked at execution, idempotency keys required, responses carry the simulated label.

### 3.3 Coordinator runtime channel

Backend → WorkBuddy managed agent via cloud-agent SDK: create/resume session, send scoped snapshot, stream structured response, receive tool-call requests and **tool-failure events**. The demo's failed booking must be a *real* platform tool-failure event, not a thrown exception we scripted locally — that distinction is the dependency proof.

---

## 4. Data

SQLite behind repository interfaces. All clinical tables INSERT-only; "current" values are latest-row projections or pure derivations.

| Table | Key columns | Notes |
|---|---|---|
| `episodes` | id, **arm**, persona, created_at | No closure column — closure is derived (D4) |
| `dispositions` | id, episode_id, version_no, policy_version, action, **clinical_deadline**, next_owner, fallback_route, source (`fixture`\|`reviewer`\|`reassessment`), created_at | INSERT-only; deadline changes only by inserting a new version (D3) |
| `attempts` | id, episode_id, route_id, **idempotency_key UNIQUE**, started_at, status (`attempted`\|`acknowledged`\|`failed`\|`expired`) | Execution axis; append-only |
| `evidence` | id, episode_id, level (`self_reported`\|`documented`), source, provenance, **simulated**, recorded_at | Evidence axis; absence of a row = `none`, never a negative finding (I5) |
| `consents` | id, episode_id, scope, state, recorded_at | Current = latest row per scope; revocation is a new row |
| `restatements` | id, episode_id, disposition_version, **hint_level**, input_mode, transcript_confirmed, extracted_json, mismatches, repair_round, outcome (`recall_unaided`\|`recall_scaffolded`\|`recall_cued`\|`not_recalled`), created_at | The hint level is non-nullable — without it the evaluation is worthless |
| `events` | id, episode_id, kind, payload, created_at | Audit log; feeds the judge ledger |
| `policy_versions` | id, version, content, provenance, approved_by, created_at | Fixture is labelled `fixture` until a reviewer exists |
| `study_sessions`, `study_responses` | dyad id, arm order, outcomes, task times | Gate B baseline records |

**Queries that will hit them** (all simple; no joins beyond episode scope):

- *Patient projection*: episode + latest disposition + latest evidence level + attempts → the four lines (I4 owner resolution happens here).
- *Closure derivation*: pure function over that projection + `Clock.now()` — `open` / `closed_with_evidence` / `escalated_to_human` / `expired_unresolved`.
- *Dedupe*: `INSERT … ON CONFLICT(idempotency_key) DO NOTHING` → idempotent no-op (I3).
- *Ledger feed*: `events` by episode, ordered.
- *Gate B analysis*: restatements by episode (level × outcome), study responses by arm.

---

## 5. Flow

### 5.1 Main path (the five-minute demo)

1. UI → `POST /api/episodes` → domain loads fixture policy → disposition v1 written with the deadline set once → plan card.
2. **PlanBack**: UI collects restatement (constrained chips or free text; voice later) → if voice, `transcript-confirmations` first → `POST restatements` → coordinator extracts `{action, deadline, next_owner}` → **domain compares** (time-bucket, closed action vocabulary, named owner) → mismatch: one field named, repair ≤2 → every round records its hint level.
3. **Barrier**: `POST barriers` → coordinator proposes a permitted route from policy content only → consent confirmed → `POST actions`.
4. **Execute**: authz + consent + idempotency key → coordinator invokes `submit_simulated_request` → adapter **fails as scripted** → the failure returns through the platform as a real tool-failure event → attempt `failed`, evidence stays `none`, **deadline untouched** → patient screen shows the four lines.
5. **Interrupt/resume**: session dropped; resume = WorkBuddy session restore **+** reload of application-owned state → UI identical, deadline unchanged (demo step 8).
6. **Injected duplicate callback** → dedupe no-op → ledger shows the dedupe, not a state change.
7. `GET /ledger` renders axes, events and fault assertions for judges.

### 5.2 Reassessment / abstention path (mockup 04)

Symptom-change input → **domain abstention policy** (no coordinator in this path) → either the emergency/human stop screen renders synchronously, or a versioned reassessment inserts disposition v2 — the **only** code path allowed to set a new deadline, and it never rewrites v1.

### 5.3 Conditional scheduled path (D9, dark until Gate A passes)

Managed scheduler (≥5-min interval is fine for 8-hour rechecks) → invokes a recheck against the application-owned episode → outcome recorded as a new event/reassessment. **Urgent escalation is never on this path.**

---

## 6. External

| External | Role | Env var **names** (never values) |
|---|---|---|
| WorkBuddy managed agent | Coordinator: sessions, streaming, tool events, resume | `WORKBUDDY_API_KEY`, `WORKBUDDY_AGENT_ID`, `WORKBUDDY_API_BASE` |
| Simulated clinic/booking adapter | Scripted availability + receipts, labelled | `SIM_ADAPTER_MODE=scripted` |
| Simulated caregiver channel | Scripted replies, labelled | (same flag) |
| TRTC (deferred spike, D10) | Push-to-talk Mandarin ASR; TTS reads reviewed text verbatim | `TRTC_SDK_APP_ID`, `TRTC_SECRET_KEY` |
| App config | — | `APP_DATABASE_URL`, `APP_CLOCK=scenario\|system` |

No real healthcare endpoints exist anywhere in the design. Adapter callbacks are local-only. No fixture, string or receipt names a real facility (Gate 1 rule).

**Gate A spike must answer (time-boxed, decision 26 Sep):**

1. Auth scheme — `x-api-key` vs Bearer (the docs conflict); region/quota reality.
2. Session create/stream/resume semantics across a genuine process restart.
3. Tool wiring — hosted MCP server vs SDK-registered tools; how **failure events** actually arrive.
4. Managed scheduler access from a non-enterprise account (for D9 only).
5. If any of 1–3 fails → D8's reversal: local simulation with honest labels, CodeBuddy development history carries the usage-proof requirement, platform-advantage claim weakened. Recorded now so 26 Sep is a decision, not a discovery.

---

## 7. Carried-forward Gate 1 risks → where this architecture handles them

| Risk (from `00-status.md`) | Handled by |
|---|---|
| Organiser-usage proof absent | D8 + Gate A spike questions (§6); CodeBuddy fallback pre-recorded |
| No clinical reviewer / protocol | Fixture-only policy with `provenance=fixture`; abstention stops the flow rather than improvising; no symptom→disposition claim anywhere |
| Load-bearing assumption untested (card may win) | **D6** — the baseline arm is architecture, not an afterthought; Gate B runs before voice/booking work exists |
| Neither mechanism requires WorkBuddy | Honest claim preserved: platform = execution substrate (coordinator, real tool call, real failure event, resume); **D9** is the only deeper candidate and is conditional on Gate A |
| Mandarin voice a gated spike | **D10** — isolated module, text path complete without it |

---

## 8. Explicitly not decided here

- File layout, type definitions, method signatures → **Gate 3**.
- Slice order → **Gate 4** (the build order in `03-planback-closure-contract.md` §6 is the starting hypothesis).
- Whether D9 activates → Gate A result + Gate 3 estimate.
- Any real integration, multi-agent split, or new clinical content authority → out of scope, full stop.

**Next action regardless of approval:** the Gate A access spike is due **tomorrow, 26 Sep** — the pre-recorded decision point. Approval of this document authorises the spike (read-only credential checks and one typed tool call), not implementation code.
