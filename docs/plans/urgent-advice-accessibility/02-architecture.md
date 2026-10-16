# Architecture: CareRelay urgent-advice accessibility

[verified] **Gate 2 REOPENED and RE-APPROVED 16 October 2026** for section 14 (judge view and ledger read-back detail). The user answered "Approve Gates 2, 3 and 4 as drafted". Sections 1 to 13 are unchanged. `00-status.md` owns gate state.

[verified user instruction] On 16 October 2026 the user answered "Sure i approve the experiment please finish up slice 21!" to the exact wording-only Gate 2/3/4 proposal and at most one ledger-reserved product call. The narrow amendment is RE-APPROVED. It preserves the v2 schema, published instruction v2, current model/settings, 15-second cap, all byte limits, no retry/fallback, default-off and code authority. Stop after that one live result. No shipping or additional live calls are authorised. `00-status.md` owns the receipt.

[verified] Narrow Slice 21 span-text grounding amendment RE-APPROVED 15 October 2026.
The user answered "Approve Gates 2, 3 and 4 as written in
docs/reviews/slice21-span-text-amendment-proposal.md, including uncertain for
not-found spans and instruction v2." The model returns span text only; code
locates exactly one word-bounded exact occurrence, and none or several stays
uncertain. Wire schema `carerelay-readback-v2`, instruction
`carerelay-readback-instruction-v2`. All other contracts are unchanged.

[verified] Narrow Slice 21 live-budget amendment RE-APPROVED 15 October 2026.
The user explicitly approved the prepared amendments to Gate 2 section 13.6,
Gate 3 section 9.7 and Gate 4 Slice 21: live read-back cap 15 seconds, inherited
fake-profile controls five seconds, complete-answer mode to be observed, and
all input/byte/terminal/no-retry/code-authority/default-off constraints preserved.
This does not authorise deployment or Slice 21 Git publication. Other gate
contracts remain unchanged; `00-status.md` owns the approval receipt.

**Gate 2: RE-APPROVED 13 October 2026 (revision 4).** [verified] The user
explicitly answered "Yep i approve gate 2" and requested a Gate 3 handoff.
Section 13 is approved architecture, not implemented or validated behaviour.
The section 5.2 durable-stop rule remains unchanged and approved.
`00-status.md` owns gate state. Gate 1 remains re-approved; Gates 3 and 4 retain
their prior contracts and do not authorise this upgrade. [hypothesis] labels in
section 13 describe unmeasured design behaviour/benefit, not pending approval.

**Historical approval: APPROVED 30 September 2026 (revision 3).** Revision 2 was approved on 25 September 2026. Revision 3 amends **D1**, amends **D8** and adds **D13**, encoding four user decisions of 30 September 2026 (D-A to D-D) and Decision **D-1b**. **Revision 3 was re-approved on 30 September 2026.** Authority for the gate state is `00-status.md`.

**Revision 2 incorporated the independent adversarial review at `docs/reviews/gate2-adversarial-review-thorough.md` (verdict: APPROVE WITH CHANGES).** Every blocking change in that review's §5 was applied or explicitly resolved. §11 is the change log.

**Revision 3 is driven by `docs/reviews/adp-hosting-stack-review.md`.** Its scope is narrow and named: the hosting split (Render for the backend, Vercel for the clinical frontend), the public deployment and its auth, and ADP as an additive interpretation surface. **D2 to D7 and D9 to D12 are unchanged.** The four decisions, the chosen hosting option and the cost are recorded in §1 (D1, D8, D13), §11 and §12, and in `00-status.md`.

Read first: `00-status.md`, `01-product.md` (approved), `PLAN.md` §5–§6, `DESIGN_PRINCIPLES.md`, `03-planback-closure-contract.md`, `research-workarounds.md`.

---

## 0. What exists today

[verified, source inspection 13 October 2026] The repository contains the
FastAPI application, Next.js frontend, SQLite and Postgres repositories, and
regression tests. Work through Slice 12 and the truthfulness repairs shipped;
Slice 9's participant run was cut, and conditional Slice 13 was never built.
Local and remote `main` matched `aca4594485f3e465daa461bf8139033458b2b81c`
before this documentation branch was created.

[verified] `render.yaml` configures Render's free plan, no disk, and a
Postgres DSN through `APP_DATABASE_URL`; SQLite remains the local test path.
This is configuration evidence, not a fresh deployed-store check. `api.py`
constructs `LocalSimulationCoordinator`; its tool results remain `local-sim`.
The twelve approved HTML screens are prototypes, not the production frontend.
Section 13.1 identifies the current application gaps with source references.

[verified, recorded evidence only] The 12 October shipping record reports
945 passed, 46 Postgres skips, one existing warning, and the repair report
records 39/39 truthfulness mutations RED. No suite or mutation harness has been
rerun for this documentation amendment. [unknown] Postgres runtime proof,
concurrent stop/dispatch ordering, ADP positive extraction and target-user
benefit remain unestablished. Submission assets and usage-proof files exist;
their provenance, redaction and claims still require review.

[verified] Sections 1 to 12 retain the earlier decisions and review history.
Current-state corrections below reconcile shipped storage/auth configuration;
section 13 proposes the new journey decisions. Earlier schedules and study
procedures are historical, not instructions to restart the cut study.

**Why revision 2 exists.** The round-2 review found three defects that made this document's own headline claims unimplementable as written: an attempt-state transition with nowhere to be written (§4.1), a tool-execution path described five different ways (§3.3), and a baseline arm that structurally could not measure the success metric (§1-D6, §9). Those three are the reason revision 1 was not approvable, and they are the substance of this revision.

---

## 1. Decisions (D1 to D13; approved D14 to D18 in section 13)

| # | Decision | Why | Reversal |
|---|---|---|---|
| **D1** | **Current stack [verified from source/config, 13 October 2026].** Python 3.13 + FastAPI on Render; Postgres on Supabase through `APP_DATABASE_URL`; SQLite for local checks. Next.js frontend on Vercel. `render.yaml` now specifies `plan: free` and no disk | Slice 7b moved the durable store behind the existing repository interface; the 11 October configuration removed the disk. This corrects the obsolete paid-disk requirement, without proposing another migration | The 30 September D-1b presentation decision remains. No hosting change is proposed by revision 4; deployed persistence still needs proof |
| **D2** | **Trust boundary is a module boundary.** A pure `domain` core owns policy, PlanBack comparison, route-vocabulary validation, closure rules, abstention policy, invariants. It imports **no** network, **no** LLM client, **no** wall clock | "The model interprets. Code decides" must be enforceable by imports, not discipline. Round-2 review calls this the strongest decision here | Not reversible without reopening Gate 1. **Gate 3 must name the enforcing check and make it fail-capable**, or this is a convention with a diagram |
| **D3** | **Append-only clinical record.** Dispositions, attempt transitions, evidence, consents are INSERT-only. The deadline lives on the disposition row; reassessment inserts a new version | I1 (immutable deadline) holds because **no retry code path writes a disposition**. **Restated honestly in §10:** that is a code-review property, not a structural impossibility | Not reversible — this is the Closure Contract |
| **D4** | **Closure is derived, never stored.** A pure function of (attempt projection, evidence axis, deadline, **recorded expiry event**, **human-acceptance record**, now) | Nothing in the system can *write* "resolved". Removes the write path for false completion — a real gain | Not reversible. **Amended:** closure inputs now include `human_acceptances` and `expiry_events`, both of which revision 1 omitted (§4.2) |
| **D5** | **Clock and idempotency are ports, with specified key derivation.** All time via injected `Clock`; **the server generates one idempotency key per (episode, route, attempt-purpose)**; the client never supplies one | Round-2 surface C: if the client generates a key per request, a double-tap produces two keys, I3 never fires, two tool calls dispatch, and the episode holds mixed attempt state. Server-generated keys are what make I3 real | Not reversible after Slice 2 |
| **D6** | **The baseline is an external artefact, not an app arm.** The comparator is a **fixed bilingual card + direct booking link + the approved human route, delivered outside the application** (printed/PDF). Measurement is **between-subjects**. The card condition receives a **scripted post-failure question** so the same false-completion outcome is measurable in both conditions | Revision 1's in-app `arm` flag could not produce the metric: a static card has no failed handoff, so the card arm could never be scored on false completion — the one outcome the reframe rests on. It also erased the card's lowest-burden advantage by wrapping it in app chrome, and within-subject crossover leaked PlanBack comprehension into the card arm. All three defects removed | Reversible. **Pre-registration required** (§9): primary outcome, cut rule and N written before results |
| **D7** | **Abstention is deterministic policy, and the free-text → policy boundary is specified.** Symptom-change input goes through a **closed-vocabulary classification step (coordinator, structured output) whose value is validated against the policy's permitted input set in `domain`**; anything outside the set is *critical uncertainty* → human path | Revision 1 required the urgent path to bypass the coordinator for rendering without saying who classifies free-text symptom change. That gap is the round-2 D7 finding: either a model call (contradicting the bypass) or a keyword rule (contradicting the split). The answer is a closed vocabulary with **fail-to-human as the default** | Not reversible without reopening Gate 1 |
| **D8** | **Coordinator channel, with the tool-execution path pinned (§3.3).** Backend ↔ WorkBuddy managed agent via cloud-agent SDK. **The coordinator executes the tool; the platform emits the failure event.** Our backend is the MCP server enforcing authorisation, consent and idempotency. Coordinator returns structured outputs only and **never** writes to the database. **Amended 30 September 2026 (D-A):** **Historical approved scope: ADP may occupy the interpretation step** (the D7 closed-vocabulary classification and the intake clarification loop) as an **additive second surface**, and **may never occupy the execution path or the rendering path**. §3.3's single normative call path is unchanged | Revision 1 described this five different ways across §2, §3.2, §3.3 and §5.1, so Gate 3 could legitimately wire a direct backend call, leaving the demo visually identical and the platform-failure claim unsupported. §3.3 now states one normative call path, and the **failure-event origin is recorded and shown in the ledger** so the platform path and the fallback are distinguishable by inspection. **The ADP amendment is the same failure mode the Gate 2 round-2 review already caught once**: a second path described loosely enough that the load-bearing claim stops being checkable. ADP is therefore additive and named, not substitutive. The guide does not document ADP tool execution, platform-originated failure events or session resume, so ADP cannot carry the §3.3 claim | Reversible to local simulation at the Gate A decision point, with the dependency claim weakened (§6 item 5) |
| **D9** | **DROPPED.** The scheduled-reassessment module is removed from this architecture and recorded as a Gate A / planning question (§6 item 6) | Round-2 review: no scenario, no trigger, no recheck content, no ingress endpoint, no estimate, and an 8-hour cadence that contradicts a same-day deadline — it could not be walked. It was also the only place the P1 load-bearing claim could be proven, which makes it a planning decision, not a module. Keeping it would have let an unestimated, unbuildable module sit inside an approved architecture | Recoverable as a documented future slice **once Gate A passes and it has a scenario and an estimate**. **Cost of the cut stated plainly** (§6 item 6): the P1 answer reverts to "execution substrate" |
| **D10** | **Mandarin voice is an isolated, deferred module.** The text path is complete without it. Voice plugs into the *same* restatement endpoint as a new `input_mode`, behind the transcript-confirmation rule and the zero-silent-critical-fact release gate | TRTC is a gated spike, not a core clinical channel | Cut under schedule pressure (but see the corrected order below) |
| **D11** | **Evidence provenance.** `documented` requires non-simulated sourced evidence; simulation labels travel with every surface. **[verified, 12 October repair]** External callback/MCP ingestion rejects all caller-labelled real evidence because no artefact verifier exists. Low-level repository fixtures remain trusted | A non-empty reference and a `CHECK` constraint are necessary shape checks, not authentication. Neither an ADP answer nor an acknowledgement proves care | No real ingestion or verifier is added by this amendment |
| **D12** | **(NEW) Expiry is a recorded event, not a read-time guess.** A persisted `expiry` event is written when the deadline passes unresolved (if not already set), and **expiry is sticky — a backwards clock does not un-expire an episode** | Round-2 surface C: derived-only expiry means a clock regression silently resurrects an expired episode, and nothing runs at the deadline. The event makes "the deadline passed unresolved" auditable rather than inferred | Not reversible |
| **D13** | **Public demo boundary [verified from source].** FastAPI guards every `/api` route and `/ledger` using `CARERELAY_API_TOKEN`; Next.js holds that token server-side. CORS stays restricted. The demo has no patient login or verified human identity | Reuse `frontend/lib/api.ts` and server actions. Browser-held episode locators never confer consent or authority | Revision 4 retains this boundary. Real patient access remains outside the shared-token demonstration |

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
- The coordinator/model never writes to the database. Credentials are server-held;
  only the transport client reads them for authentication, never a model prompt,
  session payload, patient projection or tool argument. Actions reach the
  simulated provider only through the MCP tool surface.
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

[verified, current implementation] Postgres and local SQLite sit behind the same
repository interface (`state.py`, `postgres_store.py`, `postgres_schema.py`).
Clinical tables remain INSERT-only. The table outlines below record the earlier
approved design; section 13.5 proposes the narrow additional command record.

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

**Post-stop state, amendment RE-APPROVED 12 October 2026.**
[verified] The former rule conflated stopping the automated flow with completing a
human handoff. The local probes show that no recipient need have accepted anything.
A stop therefore does not establish `escalated_to_human` or transfer responsibility.

- Persist a `flow_stopped` audit event identifying the current disposition version,
  reason and approved fallback route. No new table is required. Existing H3,
  exhausted-repair and barrier-stop records also remain authoritative stop evidence
  on reload, including records written before this repair.
- A two-repair stop, H3, refused barrier route or reassessment abstention stops
  automated restatement scoring, barrier progression and action dispatch for that
  version. A fresh restatement cannot restart an unfinished repair ladder. Guards
  apply at service and MCP entry points and survive process restart.
- Showing or hiding the plan, reading patient/ledger projections, recording consent
  or revocation, and recording a valid human handoff remain available. They do not
  clear the stop. In-flight success/evidence callbacks are recorded as refused and
  cannot progress the stopped plan; failure and duplicate audit records remain.
- Closure and conversational permission are independent. Without a completed
  handoff or qualifying evidence/acceptance, retain the approved unresolved (or
  expired) four lines, the original acting party and original deadline. Only an
  explicit successful handoff outcome transfers responsibility to its named path.
- Reopening requires the existing reviewer-authorised reassessment path to write a
  new disposition version. Earlier stops stay visible in the ledger and cannot
  stop that new version. Old restatements and action keys cannot authorise it.
  The demonstration fixture still has no authorised reassessment branch.

[verified] This amendment changes no patient string, clinical threshold, route,
platform integration or deployment authority. Gate 1 copy is reused. The user
re-approved this amendment on 12 October 2026; its bounded repair is authorised.

### 5.3 Scheduled path

**Removed with D9** (§6 item 6).

---

## 6. External

| External | Role | Env var **names** (never values) |
|---|---|---|
| WorkBuddy managed agent | Coordinator: sessions, streaming, **tool execution**, failure events, resume | `WORKBUDDY_API_KEY`, `WORKBUDDY_AGENT_ID`, `WORKBUDDY_API_BASE` |
| Tencent Cloud ADP (published agent; **additive interpretation surface only**, D8) | Historical intake/classification scope is unbuilt. Section 13 proposes confirmed read-back extraction only. Never execution, rendering or urgency | `ADP_APPKEY`, `ADP_EXPERIENCE_URL`, `ADP_CHAT_ENDPOINT`, `ADP_API_SECRET` (**WebSocket only**) |
| Public deployment (D13) | Judge-facing production link, and the Vercel frontend origin for CORS | `CARERELAY_API_TOKEN`, `CORS_ORIGINS` |
| Simulated clinic/booking adapter (**one**, not two) | Scripted availability + receipts, labelled | `SIM_ADAPTER_MODE=scripted` |
| TRTC (deferred spike, D10) | Push-to-talk Mandarin ASR; TTS reads reviewed text verbatim | `TRTC_SDK_APP_ID`, `TRTC_SECRET_KEY` |
| App config | — | `APP_DATABASE_URL`, `APP_CLOCK=scenario\|system` |

No real healthcare endpoints exist anywhere. Adapter callbacks are local-only. **No fixture, string or receipt names a real facility** (Gate 1 rule).

**Secrets rule (30 September 2026).** Names only are recorded here; **no value appears in any tracked file, log, fixture or screenshot.** The ADP guide warns twice that the AppKey must not be committed and must not appear in a screenshot, and §8 says the same for `CARERELAY_API_TOKEN`. `ADP_CHAT_ENDPOINT` is recorded as a **name** for the same reason: the endpoint itself is not a secret, but keeping the whole ADP surface as names-only means a screenshot cannot leak a value by accident.

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

`01-product.md` fixed four lines whose third is "Before [deadline]", which presumes a future deadline. After expiry that line is false, and revision 1 had no expired rendering anywhere. **The one state the product exists to report had no approved words.**

**Approved by the user 25 September 2026**, on the condition that the wording is not aggressive. The first draft ("The time to go was [deadline]. It has passed." / "Call [route] now") was rejected as too blunt for a frightened older adult. The rendering below is short, warm and forward-looking: it states the situation plainly, keeps the original deadline visible as fact rather than as a reproach, and puts the next step in the present tense.

**Reworded 2 October 2026 for plain human tone.** The user asked for wording that reads like a person rather than an agent. The rewrite is applied against the five copy rules below, which are unchanged, and against the same non-clinical constraint: it names no symptom, urgency, threshold or real facility and asserts no clinical claim. The two substantive changes are that line 1 now names *why* help is not arranged ("no one has agreed") instead of stating a bare negative, and line 2 drops the imperative "must act" for "please act now" while keeping the urgency. No exclamation mark is permitted on this screen: punctuation that alarms is a rule-2 violation.

| Line | Pre-deadline | Expired |
|---|---|---|
| 1 | No one has agreed to help yet. | No one has agreed to help yet. |
| 2 | Please act now: you, or *[named person]*. | You can still do this. |
| 3 | Please do it before *[deadline]*. | It is past *[deadline]*. Please go now. |
| 4 | If that does not work, call *[approved human route]*. | Call *[approved human route]*. They can help from here. |

**What changed on 2 October 2026, line by line.**

| Line | Was | Now | Reason |
|---|---|---|---|
| 1, both | Help is not arranged. / Help still is not arranged. | No one has agreed to help yet. | Names the reason rather than a bare negative. Rule 3 still holds: the facts are unchanged and no comfort is offered. |
| 2, pre-deadline | You or *[named person]* must act now. | Please act now: you, or *[named person]*. | Drops the imperative. "Please" is courtesy, not a softener, so urgency survives. The self-owner form is "Please act now." and the malformed "You or you must act now." stays fixed. |
| 3, pre-deadline | Before *[deadline]*. | Please do it before *[deadline]*. | A fragment became a sentence. The deadline is intact. |
| 4, pre-deadline | If this route fails, call *[approved human route]*. | If that does not work, call *[approved human route]*. | "Route fails" is systems language. Rule 4 still names the route. |
| 3, expired | It is past *[deadline]*, so please go now. | It is past *[deadline]*. Please go now. | Two sentences read calmer than one joined by "so". Rule 5 keeps the deadline. |
| 4, expired | Call *[approved human route]* — they can help from here. | Call *[approved human route]*. They can help from here. | The dash read clipped. Rule 4 still names the route. |

**Copy rules for this screen** (so later edits do not drift back):

- **No reproach.** Never "you did not", "you missed", "too late", "failed", or a bare "now" as an imperative.
- **No alarm.** No red urgency styling on this screen; the emergency path is reached through line 4's route, not through alarm on a missed appointment. **No exclamation marks**, added 2 October 2026: the user proposed "Please act now!!" and it was rejected as a rule-2 violation, because a double exclamation is an alarm rather than a courtesy.
- **No false comfort.** It still says the help is not arranged. The softness is in the tone, not in the facts.
- **Line 4 always names a real route** — 995 remains available, but the screen leads with the ordinary care route rather than the emergency number for a non-emergency expiry.
- **The deadline stays visible.** Removing it would erase the fact the product exists to preserve.
- **No invented capability.** Added 2 October 2026: the copy may not offer an action the system cannot take and has no consent to take. The user proposed adding "I'll contact your emergency contact" to line 1; it was rejected because CareRelay holds no emergency contact, has no channel to reach one and no consent record, so the sentence would promise a dispatch that cannot occur and would create the false completion the product exists to prevent. A question on line 1 ("do you want me to alert...") was rejected for the same reason plus I4: it moves the obligation back to the patient instead of naming the acting party.

**The three closure renderings, approved 8 October 2026.** This section fixed the
unresolved and expired screens. The other two closure states had no approved words:
`domain.patient_lines` refused for `closed_with_evidence`, and `escalated_to_human`
fell through to the unresolved screen with the wrong owner. The approved forms are:

| Line | Resolved, care documented | Resolved, someone agreed | Handed to a human path |
|---|---|---|---|
| 1 | Help is arranged. | Someone has agreed to help. | We have passed this to *[named human path]*. |
| 2 | Nothing more is needed from you. | You do not need to act now. | You do not need to act now. |
| 3 | It is set for *[deadline]*. | It is set for *[deadline]*. | It is set for *[deadline]*. |
| 4 | If that does not happen, call *[approved human route]*. | If that does not happen, call *[approved human route]*. | If that does not work, call *[approved human route]*. |

**The two resolved cases do not share line 1.** A recorded human acceptance is a
promise, not evidence that care happened (Closure Contract section 2.2), so line 1
says "arranged" only when the evidence axis is `documented` and "agreed" when only
an acceptance exists. All three obey the copy rules above: no exclamation mark, no
reproach, no invented capability, a real route on line 4, and the deadline visible
on line 3.

---

## 8. Non-functional surfaces (added — all were absent from revision 1)

| Surface | Decision |
|---|---|
| **Deployment** | **[verified, configuration 13 October 2026]** Render Docker backend, `plan: free`, no disk; durable Postgres via `APP_DATABASE_URL`. Next.js on Vercel calls FastAPI server-side. No deployment is performed here and no redeploy/persistence proof is inferred. The public links are recorded submission surfaces, distinct from ADP extraction |
| **Auth** | **Shared bearer token (D13).** One FastAPI dependency enforces it on **every** `/api` route and on `/ledger`; **CORS is locked to the Vercel origin**; `allow_credentials=False`. No cookie sessions. The reference shape is `laeria.ai` `backend/api/main.py` lines 44 to 63 (bearer rather than cookies, `allow_credentials=False`, wildcard origin in development only). **Auth lands with the deployment slice, never after it** |
| **Secrets** | Server environment only (§6); `.env` gitignored. Next.js holds `CARERELAY_API_TOKEN`; FastAPI holds `APP_DATABASE_URL` and later `ADP_APPKEY`. Never browser bundles, committed files or screenshots |
| **Data retention / PDPA** | **Fixture and dyad data only; no real patient data.** Retention: destroyed 30 days after submission. The old database-file deletion procedure applies only to local SQLite. A disposable Postgres test store needs an authorised teardown; hosted retention/erasure remains an operator dependency, not a verified capability (`PLAN.md` §8). **Added 30 September 2026 (D13):** a public endpoint means the **deployment region and the processor arrangements must be recorded**, and they are currently **[unknown]**. PDPA obligations cover purpose, consent or legal basis, protection, retention limits and overseas transfer, so the Render and Vercel regions and their sub-processor terms fall inside that obligation rather than beside it |
| **Observability & logging** | `events.payload` may contain clinical free text. **Payloads are redacted from application logs**; the ledger reads the table directly. No third-party telemetry |
| **Latency & cost** | Measured and recorded during Gate A — Feasibility is a scored dimension that asks for measured latency. The demo path pre-warms the session and sets explicit timeouts |
| **Degraded states** | **NEW branch:** coordinator unavailable or slow → the flow **stops** at the current question and shows a text fallback, because a coordinator stall on the PlanBack critical path is a demo-ending failure. Adapter timeout → `failed` transition. No permitted route → human path. Deadline passed with no action → expiry event + expired screen |
| **Model-generated text boundary** | `domain` renders all patient-facing clinical text from policy. **No model-generated text reaches the patient.** Coordinator outputs are structured values only, validated in `domain`. Round-2 surface B item 5 noted revision 1 achieved this only by omission; it is now a stated rule |
| **Accessibility: two architectural items** | (a) **One-question-at-a-time is enforced by the patient projection**, not by page layout. (b) **No patient-content timers or automatic wizard advance**; bounded network timeouts do not hide the H2 card, which stays until the patient hides it (Gate 1 §5.2.1, reopened and re-approved 25 Sep). `dwell_seconds` is recorded for the ledger and never shown to the patient |
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

### Revision 3 change log (30 September 2026): decision → resolution

| Decision | Resolution | Section |
|---|---|---|
| **D-A**: an ADP-based project goes hand in hand with WorkBuddy; ADP is **additive**, never a replacement for the execution substrate | D8 amended: ADP may occupy the **interpretation step** only. §3.3's single normative call path is unchanged | §1-D8, §2, §3.3 |
| **D-B**: the ADP Experience URL counts as the "project link" bonus | Recorded as a user decision. The Experience URL is one of two public surfaces; the production link is the other | §8, §12 |
| **D-C**: a production link on Vercel is **also** required | D1 and D13: the Next.js frontend on Vercel, and the public Render deployment behind auth | §1-D1, §1-D13, §8 |
| **D-D**: every other recommendation in the ADP hosting review is accepted | The Render paid plan with a mounted persistent disk, the auth shape, the templates decision, and the usage-proof re-prioritisation | §6, §8, §12 |
| **D-1b**: Vercel hosts the clinical screens themselves | D1: the presentation layer moves to Next.js; the "no framework, no build step" clause is retired; the cost is stated in §12 | §1-D1, §8, §12 |

**Every claim in this revision carries a label.** ADP tool execution is a `[vendor claim]` (`CHALLENGE_REQUIREMENTS_JUDGING.md` section 7, "tool-calling frameworks"); the MCP tool, the failure-event origin and session resume are `[unknown]`; the absence of any ADP documentation for those three is `[verified]` as absence. The cost figures in §12 are `[hypothesis]` planning estimates, not measured velocity.

---

## 12. What this architecture still does not decide

- File layout, type definitions, method signatures → **Gate 3**.
- Slice order → **Gate 4**. **Requirement carried forward from round 2: Gate 4 must sequence the baseline comparison (Gate B) *before* the Closure Contract build.** Revision 1 pinned the stack (D1) and the comparison design (D6) before the falsifier had run; that is defensible **only** if the kill test is sequenced first. `PLAN.md` §7 currently schedules sessions for 1–7 October, *after* the state machine — the wrong order, to be corrected at Gate 4.
- **Effort.** Round 2 estimates **90–150 h** for this architecture's build against the 56–89 h it inherited, plus 20–35 h for the baseline. That is **not affordable in 21 days** with Gate 3, Gate 4, recruitment, clinical chasing and submission assets outstanding. **Either the estimate or the scope changes at Gate 3, and this document does not pretend otherwise.** The D9 cut, the MCP reduction and the single adapter are the first tranche.
- **The H2 accessibility hazard is resolved.** Gate 1 was reopened and re-approved on 25 September 2026: the five-second timer is removed and the plan card stays until the patient hides it. **No timer, countdown or auto-advance exists anywhere in the product.** `dwell_seconds` is recorded for the judge ledger only. See `PLAN.md` §5.2.1.
- **The cost of Decision D-1b (added 30 September 2026).** Moving the clinical screens to Next.js on Vercel adds **20 to 34 person-hours [hypothesis]** on top of the 102 to 169 hours the slice plan already carried: a Next.js project, five screens, client routing, data fetching, CORS on FastAPI, an API base URL env var, and a Node toolchain in the demo environment. It also adds **two network boundaries** to the judged walkthrough (browser to Vercel to Render to ADP) where §8 already names a coordinator stall as a demo-ending failure, and it turns the UX and Accessibility position from free (server-rendered semantic HTML) into work that must be done and defended. **The decisive objection is schedule and demo risk, not accessibility**, and the user took the decision knowingly on 30 September 2026. Reversing to D-1a before the frontend slice begins is cheaper than reversing after it.
- **Hosting reconciliation, 13 October 2026 [verified from configuration].** The paid disk requirement was retired after the Postgres move; `render.yaml` now names the free plan. This is no fresh billing or persistence audit. Processor/region/retention arrangements remain a later operator review (§8).
- Whether D9 is revived → after Gate A, with a scenario and an estimate.

**Next action, 13 October 2026:** prepare the separate Gate 3 program-design
amendment against the approved section 13 architecture. The Gate A transport spike ran on 2 October; it did not
prove MCP execution or the positive ADP extraction path. The superseded
"unrun and overdue" instruction is withdrawn. Gate 3 program contracts and
Gate 4 upgrade slices follow separately; no implementation is authorised here.

---

## 13. Revision 4: patient experience and ADP read-back, APPROVED 13 October 2026

Decision summary (approved design; behaviour remains [hypothesis] until proved):

- **D14:** extend the existing patient read into one authoritative journey projection.
- **D15:** map twelve approved screens; retain closure/stop precedence and field-only repair.
- **D16:** explicit start, stable locator and versioned replay/dispatch guards.
- **D17:** ADP extracts confirmed read-back; code canonicalises and compares.
- **D18:** evidence and manual enablement requirements, before separate shipping authority.

### 13.1 Fit and inspected gaps

[verified] Sources inspected on this branch:

- `api.py:create_episode` returns the shared `demo-episode-001` identifier.
  `get_episode` catches `NoDispositionToRender` and returns `fixture.demo_lines()`.
  FastAPI's bare `/` also renders fixture lines without an episode projection.
- `frontend/app/page.tsx` creates the episode on every render, then reads four
  lines. `frontend/lib/api.ts` holds credentials server-side, but its patient
  type omits even the API's existing `closure` and `care_evidenced` fields.
- `presentation.PatientSurface` has no action, deadline, owner, next question,
  stop reason or resume cursor. `/options` lists policy routes even without a
  disposition. Separate reads cannot guarantee a consistent journey snapshot.
- `service.py` and both stores already preserve stop reasons, versions,
  restatements, hint events, barriers, consent, attempts and closure inputs.
  `repair_restatement` currently scores the repair text as another whole plan.
  A timing-only answer therefore needs an explicit field-scoped merge rule.
- `coordinator.py` extracts locally. The published instruction in
  `submission/adp-agent-instruction.md` returns raw spans plus `action_id`,
  lacks field uncertainty and has no measured positive path. It is not a
  drop-in implementation of ADR-0007's raw-span boundary.

### 13.2 D14: one authoritative journey projection

[hypothesis] Extend existing `GET /api/episodes/{id}`; do not add a parallel
patient-state API or store a mutable screen/closure column. Service loads one
consistent, versioned snapshot; domain derives plan, closure, stop and permitted
next step; presentation serialises it. The frontend renders that result.

The projection carries these conceptual groups; exact types belong to Gate 3:

- Identity: episode ID, disposition/policy version, schema version and a durable
  state revision. Revision comes from committed records, not a process counter.
- Plan: nullable action ID and approved action text; absolute UTC deadline,
  server-produced display text/timezone; original plan owner and current acting
  owner separately; approved fallback ID/text. Never parse a patient sentence.
- Outcome: existing closure and care-evidenced fields, execution/evidence axes,
  acceptance actor/scope, escalation outcome and deployment simulation label.
- Flow: stopped flag, reason and stopped disposition version; latest restatement
  reference, repair count, hint visibility and effective cue level. No patient
  dwell-time, score or provider reasoning.
- Next step: one server-selected step, at most one question with approved text,
  permitted choices/route, and allowed commands with version-bound replay tokens.
  Unknown combinations produce recovery/refusal, not a guessed question.
- Copy: approved outcome lines and surrounding Gate 1 text, selected by the
  server. Transport/detail codes stay out of patient wording. Read-back input
  remains the patient's own text and is escaped, never rendered as HTML.

No disposition means `plan=null`, `closure=null`, `lines=[]`, no deadline,
acting owner, options or restatement/action command, and approved no-plan text.
Assessed responses retain the existing outcome fields/line order while adding
the versioned journey data; legacy no-plan clients must not retain synthetic
guidance as a compatibility fallback. An unknown
ID is 404, not a fixture. Apply this to `/options`, MCP reads and the bare
FastAPI `/` as well: retire/redirect that legacy patient surface or render the
same no-plan/projected state. The ledger remains a separate audience.

Formatting uses the injected backend clock and fixture timezone. The scenario
still refers to 30 September 2026, not the browser's current date. “6pm today”
is allowed only against that scenario day; system-clock operation must derive
relative text from the actual stored instant. No retry resets it. There is no
new scheduler, automatic screen advance or monitoring claim.

### 13.3 D15: map the twelve approved screens without browser rules

[hypothesis] The filenames below are rendering examples, not persisted states.
The server evaluates recorded facts before choosing a step. Closure precedence
stays documented evidence, expiry, relevant acceptance, successful handoff, open.
A durable stop independently removes all automated progression. If an accepted
or handed-off episode is also stopped, show its true outcome with no questions;
never let a stop overwrite a real transfer or imply one.

| Approved screen | Authoritative condition and permitted next behaviour |
|---|---|
| `00-start.html` | No episode or existing episode without disposition. “See the example” explicitly creates/resumes an episode and requests the allowlisted fixture through intake. No symptom assessment or inferred guidance |
| `01-plan.html` | Disposition exists, open, active, before read-back begins. Action/deadline from that version, owner from closure. Display plan before interpretation. Also supplies neutral unresolved rendering for acknowledged/unknown contact without qualifying acceptance; never label it failed |
| `02-readback.html` | Persisted read-back-start event, or a scored round needing uncertainty correction. Draft review is local and unscored; explicit confirmation binds submitted text. Timeout/invalid output keeps this question, with the approved unavailable text |
| `03-repair.html` | Latest comparison has a definite mismatch and a repair remains. Only the selected field is re-asked. Missing/ambiguous fields use the uncertainty wording, never a definite mismatch claim. This screen illustrates timing; other field-specific strings need Gate 1 approval before exposure |
| `04-barrier.html` | Current-version PlanBack confirmation recorded at H0 to H2, no stop, no unresolved repair. Appointment choice maps deterministically to the fictional provider; transport/other have no supported route, show the approved refusal and persist a versioned stop |
| `05-permission.html` | Recorded permitted appointment route, active version and no request yet: unchecked permission. A recorded decline issues no action. A recorded attempt with no response shows waiting; this substate is never successful handoff. An acknowledgement alone returns neutral unresolved wording |
| `06-unresolved.html` | Recorded failed request or failed human handoff, closure open, no stronger state. Preserve owner/deadline and four approved lines. “Did not work” requires an actual failure, never a timeout in loading or an unknown outcome |
| `07-stop.html` | Versioned stop/H3/exhausted repair/refused barrier, still unresolved. No third repair, barrier continuation or dispatch. Plan display, consent/revocation and a valid operator-recorded human transfer stay available |
| `08-recovery.html` | Loading, authentication refusal, unknown episode, malformed projection or transport failure. No new plan or command. Retry is a read of the same locator; after success render its server-selected state, including a stop |
| `09-expired.html` | Derived `expired_unresolved`, including a persisted expiry after clock regression. Overrides waiting, failure, acceptance-without-care and ordinary open steps; preserve deadline and approved expired lines, offer no automated continuation |
| `10-accepted.html` | Relevant permitted caregiver acceptance, with current consent checked at recording, before unresolved expiry. Name the actual recorded caregiver using approved display. `care_evidenced=false`; no booking or completed-care claim. Never offer a public “accept as daughter” control |
| `11-handoff.html` | `escalated_to_human` with actual `handed_off` or legacy `handed_over` outcome and named approved path. Attempted, failed or unknown escalation cannot select it. It stays simulated and care-unconfirmed |

[hypothesis] A trusted documented-care fixture uses the separately approved
section 7 documented-care lines. It is not a thirteenth externally reachable
care capability; real evidence ingestion remains disabled. No preview state
selector, invented receipt or ADP output may produce that state in the app.

Read-back/repair rules: retain previously matched fields only from the latest
confirmed same-version round. Replace the field currently being repaired;
inspect the whole new answer for corrections, negation and contradictions before
carrying anything forward. Never fill a field from the expected plan, a prior
version or an uncertain round. Persist the resulting comparison and provenance.
Two scored repair rounds remain the maximum; H3 remains `not_recalled` and stops.
A successful round at H2, or after revealing the plan during that attempt,
is cued even after hiding/reload; the browser cannot claim H0 or H1 to erase it.
Showing/hiding the plan never clears a stop or consumes a repair.

### 13.4 D16: identity, safe resume and replay

[hypothesis] Keep Next.js server components/actions as the credential boundary.
Allocate an opaque server-generated demo locator/start nonce in an HttpOnly,
Secure, SameSite cookie before a mutating request. It holds no words or secrets
and is not authentication. Explicit start uses that nonce as the creation
operation identity; durable uniqueness returns the same episode if the response
is lost. Each intentional new example gets a new unpredictable episode ID;
never reset the shared fixture episode or create on GET/render/retry.

Reload reads the locator's existing episode. If no locator exists, show start;
if its record is absent, show recovery rather than creating a replacement.
Restoring an ADP conversation is unnecessary: the database owns resume. Drafts
may remain in the current tab, but are unconfirmed and cannot advance state.
No real-patient identity/access-isolation claim follows from the shared token.

The server issues operation tokens for the current allowed commands. Each binds
an episode, disposition version, state revision, purpose and request digest.
Same token/same body reuses its recorded operation result and returns a freshly
projected journey, so replay cannot revive old commands after a later stop or
transfer. Same token/different body or a stale new command refuses and reloads
state. An old receipt never grants current progression authority. New answers use newly issued tokens;
transcript digests alone are not round idempotency. New request tokens must not
create new action attempts: keep D5's key derivation and set its purpose
server-side to the disposition version plus fixed request purpose. Browser
clients may not invent purposes to obtain another dispatch.

Do not hold the global DB lock/transaction during an ADP call. Capture the
revision, perform extraction outside it, then re-read and validate version,
latest parent, cue level, stop, deadline and command token inside the atomic
compare/record boundary. Late output for a stopped/superseded plan is refused.
Apply the same progression guards at service and MCP entry points, not only UI.

[unknown, required later proof] Current process locking is not multi-worker
ordering proof. [hypothesis] SQLite uses its write transaction and Postgres an
episode-row lock for stop, consent/reassessment, scoring and final dispatch
authorisation. The final simulated-provider invocation is serialised with stop writes under
that episode lock, so a stop committed before invocation wins. Record dispatch
start at that boundary; release the lock before any later callback. A dispatch
already begun cannot be undone by a later stop. Record that order
and refuse later success/evidence progression under section 5.2. No exactly-once
external action claim follows. A claimed attempt with an uncertain crash outcome
is never redispatched on reload or by a fresh request token.

### 13.5 Data and endpoint delta

[hypothesis] Reuse dispositions, restatements, barriers, consents, attempts,
transitions, callbacks, acceptances, escalations, expiry and stop events. Derive
screen state; do not create a second journey state machine in the browser.

Add one append-only `journey_commands` record for durable command dedupe. It
holds operation ID, phase (`claimed` or `completed`), episode/version/revision,
command kind, body digest, result reference and interpreter/schema provenance.
Unique operation/phase constraints permit one claim and one terminal receipt,
whose outcome is applied, refused, unavailable or superseded; it cannot be
overwritten by late completion. Both engines enforce append-only writes. Claim
once before work; append the terminal receipt after it. State changes and the
applied receipt commit together. A replayed completed command returns the
referenced result; an in-flight one reports pending, never executes twice.
After a crashed extraction, an explicit retry atomically supersedes the old
claim before issuing a new scoring token; a late result cannot commit.
Ambiguous action claims retain the existing attempt and prohibit redispatch.
This table is necessary because existing restatements, hints, barriers and
consent writes lack general request dedupe. Exact migration/signatures are Gate 3.

Extend `events` for versioned `readback_started` and interpretation failure
provenance. Use existing hint and stop records; no new stop table. Persisting a
review/navigation event never proves understanding, consent, acceptance or care.

| Endpoint | Proposed amendment |
|---|---|
| `POST /api/episodes` | Server-issued creation operation identity; unique episode per intentional example, idempotent lost-response recovery; still no disposition |
| `GET /api/episodes/{id}` | Extended authoritative journey projection, consistent snapshot and existing sticky-expiry read rule; explicit no-plan |
| `POST /api/episodes/{id}/intake` | Allowlisted example selection resolves to the existing non-clinical fixture on the server. Retain exact-match legacy intake and fail closed for other text; idempotent start never writes a second disposition |
| `POST /api/episodes/{id}/journey-events` | Narrow new route for the plan-to-read-back transition (`readback_started`); validated against current state with a replay token. No caller-selected screen or outcome |
| Existing confirmations, restatements, repairs, hints, barriers, consents, actions | Add version/revision/replay guards and return the authoritative current projection. Explicit text confirmation reuses the recorded digest boundary. Server determines cue level, repair field, route and request purpose |
| Existing options, ledger, callbacks, acceptances, escalations, reassessments | No-plan options empty; ledger reads new provenance; retain callback dedupe, consent and durable-stop rules. Keep operator fixture acceptance/handoff distinct from patient controls; no new clinical reassessment branch |

Main call order ([hypothesis]):

1. Browser reaches the Next.js entry and receives a locator; explicit example
   start calls FastAPI create/intake through the server, then reads the journey.
2. The plan renders first. Starting read-back records its versioned event;
   reviewing a draft calls no model. Confirmed submission reaches the backend.
3. Service checks the command/snapshot, calls ADP outside the transaction,
   validates extraction, then rechecks state and atomically records comparison.
4. A matched plan permits barrier selection, then separate provider-sharing
   consent. Server-owned route/purpose reaches the existing action coordinator
   and MCP guards; the local provider executes under the stop ordering rule.
5. Callback/receipt processing retains consent, version, terminal-order and
   simulation guards. A fresh projection supplies the true outcome; reload
   reuses the episode and issues no booking or model call by itself.

### 13.6 D17: ADP extracts confirmed read-back only

[verified user instruction] On 16 October 2026 the user answered "Sure i approve the experiment please finish up slice 21!" to the exact wording-only Gate 2/3/4 proposal and at most one ledger-reserved product call. The narrow amendment is RE-APPROVED. It preserves the v2 schema, published instruction v2, current model/settings, 15-second cap, all byte limits, no retry/fallback, default-off and code authority. Stop after that one live result. No shipping or additional live calls are authorised. `00-status.md` owns the receipt.

[hypothesis] The server instruction explicitly names each v2 output key/type and forbids echoing input metadata. This wording experiment is not evidence of model reliability; each live result remains one observation.

[hypothesis] Choose the role explicitly:
**Confirmed patient words → ADP extraction → deterministic CareRelay comparison.**
This is a new decision, distinct from the old unbuilt Slice 13
intake/classification scope. Do not activate intake clarification, symptom
classification, booking, urgency selection, patient guidance or closure through
ADP. Gates 3 and 4 must design/sequence the read-back integration separately;
the old Slice 13 contract is unchanged and does not authorise it.

Use a backend extraction adapter alongside the existing action coordinator.
ADP has no tool permissions, database access or patient rendering channel.
`LocalSimulationCoordinator` continues to execute simulated actions with
`origin=local-sim`. A real ADP extraction does not convert those into platform
tool failures or satisfy the WorkBuddy runtime claim.

Send only confirmed fictional words, unordered permitted surface vocabularies,
a schema/version and opaque request correlation. Do not send the expected
Disposition, selected answers, owner identity/profile, consent record, booking
receipts or credentials. Stateless calls avoid vendor-memory contamination.
The backend transport adds `ADP_APPKEY`; the model never sees it. Production
processing of real patient words remains outside the demonstration boundary.

The instruction distinguishes a fictional read-back from a request for advice:
repeating the supplied example is eligible for extraction, not automatic refusal.
The strict extraction object has a pinned schema version, nullable raw
`action_span`, `deadline_span`, `next_owner_span`, explicit `uncertain_fields`
and a refusal flag.
[hypothesis, Slice 21 grounding amendment] Each non-null field carries exact span text only.
Code, not the model, locates it: exactly one word-bounded, exact code-point occurrence in the confirmed string becomes the source span.
No occurrence or more than one occurrence leaves that field null and uncertain.
Model-supplied offsets are not accepted.
Every accepted span is still a verbatim slice of the confirmed words, and only domain code canonicalises it.
Reject unknown keys, wrong types, unknown field names,
duplicate JSON keys, multiple objects, markdown/prose, unsupported versions,
truncated streams or overlong output. No model-selected action ID, urgency, timestamp, route, confidence
score, match verdict or patient sentence is accepted. ADR-0007 stays binding:
only domain code canonicalises raw spans against versioned policy tables and
the injected clock/timezone.

Negation and uncertainty are independent checks over the whole confirmed text,
not trust in the model's flags. Carry uncertainty for negation, doubt,
conditionals, alternatives, questions and contradictory later corrections,
including “Actually I won't”. A source-valid positive span inside such a
statement cannot confirm a plan. A missing or unsupported value is uncertain;
only a definite, supported different value is mismatched. A valid but uncertain
comparison follows the bounded correction ladder; malformed/refused/unavailable
responses are unscored. No confidence
threshold turns uncertainty into success. Grounded spans reduce fabrication;
they do not prove general language understanding.

[hypothesis, Slice 21 engineering cap] Use a fifteen-second total live ADP
response budget, no automatic retry, 2,048 input characters and 16 KiB
assembled answer limit. The budget includes the full stream, not just its first
byte. Parse only the final bounded answer channel; never stream reasoning to
the patient. Gate 3 will specify adapter/envelope validation and timeout tests;
any budget change needs recorded justification, not an implied latency result.

[verified diagnostic justification, 15 October 2026] One separately approved
30-second observation produced a source-grounded six-field reply at 11,816 ms,
then exceeded the unchanged 64 KiB wire cap before terminal completion. Five
prior five-second observations did not complete. Fifteen seconds is the approved engineering
cap for the bounded live corpus, not measured worst-case latency or a guarantee.
Preserve the inherited five-second fake-profile controls. Prefer a separately
observed complete-answer profile with Incremental false to reduce stream
overhead; do not raise the 16 KiB answer/frame or 64 KiB wire limits. A missing
terminal, over-limit reply or failed corpus still keeps production ADP disabled.
Urgent guidance remains available before and independently of extraction.

[verified diagnostic justification, 15 October 2026] After an operator model switch, two actual local product calls finished in under 9 seconds, but both returned spans that failed the exact source-offset check.
Code-located offsets keep exact-source grounding while removing the model's offset arithmetic.


Timeout, transport/auth failure, refusal or invalid object: record an unscored
interpretation result, preserve the confirmed draft and current question,
consume no repair round, leave owner/deadline/closure untouched, and show the
approved unavailable/correction text. The patient may revise words, reveal the
plan or use the existing human fallback. A temporary unavailable check is not
section 5.2's durable clinical stop and must not invent a completed handoff.
Do not silently run the lexical simulator after ADP failure or pretend it was
ADP. Any constrained choices that reveal the answer are cued; H3 still stops.

Keep extraction provenance separate from action origin: interpreter mode,
configured instruction/schema version, correlation, validation result and
failure category in the ledger. Mark model-version knowledge unknown if the
provider does not expose it. No raw SSE, reasoning or secrets in general logs.
The published agent's existing schema is incompatible: it must be deliberately
revised, published/activated and probed before enablement, not silently coerced.

### 13.7 D18: evidence required before enabling or shipping

[hypothesis] Gate 3 must supply fail-capable tests and Gate 4 small visible
slices for the following obligations; these are acceptance obligations, not new
program contracts, a build schedule, or claims of passing tests:

- Serialized no-plan and every screen condition, contradictory combinations,
  source-grounded action/deadline/owner and one question; API/browser agreement
  with a scanner positive control for every prohibited success phrase.
- Same-episode refresh/lost response/double-tap, separate example IDs, stale
  tabs, repeated hints/consents/repairs, response lost after commit and restart
  between command claim/application. Each guard needs its own mutation proof.
- Field-only repair without expected-answer filling, unaided/cued provenance,
  invalid extraction consuming no round, H3/two-repair stop and authorised
  test-only new-version reopening; all alternate service/MCP paths included.
- ADP positive paraphrases and definite timing mismatch, missing fields,
  negation/corrections, advice/injection probes, refusal, malformed/oversized
  responses and whole-stream timeout. Offline deterministic proof must be
  separated from live ADP observations and their bounded corpus.
- Disposable Postgres concurrency tests for stop/consent versus dispatch,
  late extraction/callbacks, crash/restart and append-only command receipts.
  Re-prove authenticated patient/options/ledger reads after a real restart;
  SQLite skips cannot count as deployed-store evidence.
- Desktop/mobile at 320 CSS pixels, larger text and browser zoom; keyboard,
  focus/dialog restoration, screen-reader questions/errors/status, no answer
  leak on H0/H1 and no timers/automatic wizard advance. A mockup reflow check
  alone is not an accessibility result for the production app.

Manual dependencies, later and separately authorised: configure the existing
backend ADP variables (`ADP_APPKEY`, `ADP_CHAT_ENDPOINT`) and an explicit
`ADP_EXTRACTION_ENABLED` switch only after Gates 3/4 and the live corpus;
operator checks knowledge base/tools, deployed instruction version, positive
extraction and refusal/visible-reasoning behaviour. Use a disposable Postgres
test database with locally configured credentials, never production data or a
pasted secret. Review processor/region/retention arrangements before changing
the data boundary; qualified clinical review/protocol and actual authorised
participant work are still required for clinical readiness or benefit claims.
Existing provider-sharing consent grants no general vendor-processing authority.

No credentials, installation or external call is needed for this amendment.
Correct demo/assets/usage claims only after new evidence; deploy, publish,
commit, push and submit only with separate authority. Remaining sequence:
**Gate 2 approval → Gate 3 program design → Gate 4 upgrade slices → journey and
approved ADP implementation → accessibility/API/Postgres proof → corrected
claims, demo, deployment and submission.** The cut study stays cut.

## 14. Revision 5: judge view and ledger read-back detail, APPROVED 16 October 2026

[verified] Gate 2 was REOPENED and RE-APPROVED 16 October 2026 for this section only.
Gate 1 was re-approved the same day for the redesign and judge view in `design/mocks/redesign/`.
Sections 1 to 13, including the section 5.2 durable-stop rule and D17's ADP boundary, are unchanged.
`00-status.md` owns gate state.

Decision summary (proposed design; behaviour stays [hypothesis] until proved):

- **D19:** two judge surfaces, kept apart from the patient surface. The judge stage shows the unchanged patient route in a same-origin frame beside a panel that reads only the ledger.
- **D20:** the ledger gains read-only read-back detail: confirmed words, code-located spans, per-field comparison, plan reference, current step and server check time.
- **D21:** the Gate 1 patient changes: consent offered only on its own step, the plan visible on the request-failed screen, and a one-press start that closes F7.

### 14.1 Fit and inspected gaps

[verified] Sources inspected on branch `redesign-judge-view` at `be82690`:

- `frontend/app/ledger/page.tsx` is unlinked and prints each extraction as one sentence. A judge sees no confirmed words, no copied phrases and no per-field result.
- `service.ledger` already holds what the panel needs, unexposed: `RestatementRecord.extracted` (stored spans) and `.comparison` (matched, mismatched, uncertain); `words_confirmed` events hold the confirmed text keyed by `confirmation_id`, which restatement provenance carries; each `journey_commands` claim and completion row has `recorded_at`.
- `rules.derive_journey(bundle, now_utc)` is pure. `service.project_journey` is not: it may record expiry and an H2 hint event. A judge panel must therefore never call the patient read.
- `rules.py` offers `grant_share` and `revoke_share` on the plan step, and `grant_share` on the stopped and unresolved steps. That is why the shipped plan screen shows a consent checkbox and "Not now".
- `frontend/app/page.tsx` renders recovery when a valid locator's episode is not found yet. That is the first-visit "We cannot load your plan" (F7), and the cause of the three-click start.
- `frontend/next.config.mjs` sets no framing policy, so any site may frame the patient page today.

### 14.2 D19: judge surfaces separate from the patient surface

[hypothesis] Routes in the existing Next.js app:

| Route | Reader | Reads | Writes |
|---|---|---|---|
| `/` | patient | journey projection (unchanged) | patient commands only |
| `/demo` | judge | nothing; static start page | nothing |
| `/demo/stage` | judge | ledger for the locator's episode | nothing |
| `/ledger` | judge | ledger (unchanged) | nothing |

The stage frames `/` in a same-origin `iframe` inside a phone frame.
The frame keeps the patient document exactly the patient component: no ledger value enters it, and its own navigation keeps working.
The panel is a server-rendered reader of the ledger only, so opening it can never record expiry, a hint event or any other row.

The refresh signal crosses the frame as one message, `{type: "carerelay-journey", revision}`, posted by the patient page only when its parent is the same origin, with the exact origin as target.
The panel accepts it only from its own frame and own origin, then re-renders on the server.
The message carries no plan, words, step or identifier.
A visible "Refresh" control is the fallback if a message is lost.

All routes send `Content-Security-Policy: frame-ancestors 'self'`, which also stops other sites framing the patient page.
The patient page never links to the stage or the ledger.
The judge surfaces show only simulated, fictional data; they never show an AppKey, a raw model reply, a thought channel or a raw stream.

### 14.3 D20: ledger read-back detail

[hypothesis] `GET /api/episodes/{id}/ledger` stays read-only and gains:

| Field | Source | Rule |
|---|---|---|
| `journey_step`, `interpretation` | `rules.derive_journey(bundle, now_utc)` | Same pure function as the patient read, with no writes; null without a plan |
| `plan_reference` | current disposition and recorded policy text | Action, deadline display, owner display, fallback display and version; present during read-back, when the patient's plan is folded away |
| `restatements[].readback.confirmed_words` | `words_confirmed` event matched by `confirmation_id` | Null for legacy rows without provenance; never another round's words |
| `restatements[].readback.spans` | stored `ExtractedPlan` spans | Substrings code located in the confirmed words; not the model's reply text |
| `restatements[].readback.fields` | stored `PlanComparison` | `matched`, `mismatched` or `uncertain` per comparison field |
| `extractions[].elapsed_ms` | claim and completion `recorded_at` | Whole milliseconds on the server; null without both rows |

No table, migration or write is added, and both engines return the same shape.
Under schema v2 a located span equals the model's copied phrase exactly, because code accepts only an exact, word-bounded occurrence; a phrase code could not locate is shown as unclear, never as the model's text.
The confirmed words are fictional demo input and already reach the same judge audience through `/ledger`'s restatement rows; serialized leak scans must cover the new fields.

### 14.4 D21: patient changes approved at Gate 1

[hypothesis] Narrow behaviour changes, each enforced in the layer that owns it:

1. **Offers (domain).** The plan, stopped and unresolved steps stop offering `grant_share`. `revoke_share` is offered only while consent is granted. The permission step is unchanged. This narrows offers; it adds no route, consent or action.
2. **Plan slip on request failure (frontend).** The unresolved step already carries the plan in the projection; the frontend renders it as the slip instead of behind "Show my plan". Redaction during read-back is unchanged.
3. **Start (frontend).** A Node-runtime Next middleware on `/` sets a fresh signed locator only when none is present, using the `/example` codec and cookie options and making no backend call. A valid locator whose episode is not found renders the approved start screen, not recovery. One press runs `create`, then `select_example` with the token the create result offers; each keeps its replay guard. An invalid locator still renders recovery. Real read failures still render recovery.
4. **Presentation (frontend).** Slip, fold, step counter, icons and colour tokens are markup and CSS. The step counter is computed from the server's `journey.step`; no clinical value or screen choice moves to the browser. Fonts are self-hosted by `next/font` at build time, so the browser makes no third-party font request and no dependency is added.

### 14.5 Unchanged

ADP stays interpretation only, default-off, schema v2, 15-second cap, one call, no retry or fallback, with code deciding.
Plan, deadline, owner, urgency, closure, sticky expiry and durable-stop rules are unchanged.
`/ledger` semantics are unchanged. No deployment, install, credential or new external service follows from this section.

### 14.6 Least-confident decisions

- **Frame accessibility.** The judge stage is not the patient accessibility surface; `/` remains it. A screen reader inside the frame is not claimed.
- **Node middleware.** Next 15.5 supports Node-runtime middleware. If it fails in the build, the fallback keeps today's `/example` press and still fixes the not-found screen; that costs one extra press.
- **Panel freshness.** It depends on one same-origin message; the Refresh control covers a lost message.
- **Words on a judge surface.** Acceptable only because every input is fictional and labelled. A real-patient deployment would need a separate decision.

## 15. Revision 6: durable reservation guard for hosted ADP, DRAFT 16 October 2026

[verified] Gate 2 is REOPENED 16 October 2026 for this section only, and it is a draft until the user re-approves it.
The user approved hosted ADP in principle ("i approve hosted adp, so mark that down"); that approval does not switch it on, and `00-status.md` owns gate state.
Sections 1 to 14, the section 5.2 durable-stop rule and D17's ADP boundary are unchanged.

Decision summary (proposed design; behaviour stays [hypothesis] until proved):

- **D22:** every live ADP send is reserved in the application database, inside the HTTPS transport, before the socket opens.
- **D23:** three configured ceilings, a durable halt and a single in-flight call bound every send; any missing piece fails closed.
- **D24:** a send the guard refuses is shown to the patient as today's unavailable sentence and to the judge as not sent, never as a live call.

### 15.1 Fit and inspected gaps

[verified] Sources inspected on `main` at `d6ae945`:

- `configured_readback_extractor` (`src/carerelay/adp_extraction.py:831`) returns a live HTTPS extractor as soon as `ADP_EXTRACTION_ENABLED` is `true` or `1`. Nothing meters the calls.
- The only guard that ever ran is the temporary harness `live_guard.py`, which monkeypatches `HttpsReadbackTransport.open` and `AdpReadbackExtractor.extract` and keeps its ledger in a JSON file. It is outside the repository and cannot run on Render. A copy is kept outside the repository at `~/carerelay-evidence-archive/s21-live-guard-20261016/`.
- The code reads three ADP names only: `ADP_EXTRACTION_ENABLED`, `ADP_CHAT_ENDPOINT` and `ADP_APPKEY`. `ADP_EXPERIENCE_URL` and `ADP_API_SECRET` in `.env.example` are read by nothing.
- A transport exception inside `extract` becomes `validation: "transport"` with `transport_provenance: "https"`. The judge panel would then say Tencent ADP "refused, ran out of time or replied in the wrong shape" beside "Live HTTPS call", which is false for a send that never left the server.
- The Docker image runs one uvicorn worker, and the API serialises use cases with an in-process lock. A Render deploy can still overlap two instances, so the guard cannot rely on either.
- The public site needs no sign-in, so anyone who opens the patient page can trigger a check.

### 15.2 D22: reservation before transmission

[hypothesis]

- The guard lives in the transport. A guarded HTTPS transport commits a reservation row in the application database, then opens the socket. No code path reaches the socket without a committed row.
- The row records its sequence number, the ADP `RequestId`, the operation (correlation) ID, its episode, the Singapore calendar day and the time. It holds no words, prompt, AppKey or reply.
- A reservation is accepted only for an operation that has a pending claimed `score_words` or `repair_words` command, which names its episode. Anything else is refused with nothing sent.
- Every reservation is finished exactly once with one outcome: `valid`, `refused`, `invalid`, `timeout`, `transport`, `void` or `lost`.
  - `void` means the payload was never handed to the socket layer. Only code can record it, and only when that is certain.
  - `lost` is an operator record for a reservation whose process died; transmission is unknown, so it counts.
- The finish is written from the extractor's own result, in a `finally`, so a crash leaves the row unfinished and that blocks every later send (D23).
- Tables are append-only, with refusing triggers on SQLite and Postgres like the existing tables. Finishing, halting and clearing are new rows, never updates.

### 15.3 D23: ceilings, halt and fail-closed configuration

[hypothesis] A reservation is refused, with nothing sent, when any of these holds, checked in this order:

| Reason | Condition | Clears when |
|---|---|---|
| `guard_config` | Live extraction is on but a ceiling is missing, not a positive integer, or the database is the in-memory default | Operator sets valid ceilings and a durable database |
| `guard_halted` | The latest halt control is a halt | Operator records a clear, with a reason |
| `guard_unfinished` | Any reservation has no outcome yet | The call finishes, or an operator records it `lost` |
| `guard_episode_ceiling` | This episode's counted reservations reach the per-episode ceiling | Never for that episode |
| `guard_day_ceiling` | Today's (Singapore day) counted reservations reach the per-day ceiling | The next Singapore day |
| `guard_total_ceiling` | All counted reservations reach the total ceiling | Operator raises the ceiling |
| `guard_unbound` | No pending scoring claim matches the operation | Never; it is a code fault |

- Counted means every reservation except `void`. A refusal by the guard is not a reservation and counts nothing.
- An `invalid`, `timeout`, `transport` or `lost` outcome counts and writes a halt in the same transaction. `valid` and `refused` do not halt.
- Ceilings are not failures and never halt.
- The unfinished rule allows one live call at a time across the whole site. A second visitor who submits during that call gets the unavailable sentence. This is the simplest bound that two tabs, two workers or an overlapping deploy cannot exceed.
- Serialisation is enforced by the engine: `BEGIN IMMEDIATE` on SQLite, a transaction-scoped advisory lock on Postgres, and a primary key on the sequence number underneath both, so two writers cannot both take the same next number.
- The guard runs inside the existing 15-second whole-response budget; it does not extend it.
- With `ADP_EXTRACTION_ENABLED` off, nothing changes: the offline extractor runs, no guard is built and ADP is never contacted.

### 15.4 D24: honest rendering of a refused send

[hypothesis]

- The extractor reports a guard refusal as `validation: "not_sent"` with the reason as its failure category, kept apart from `transport`.
- The patient sees the approved sentence "We could not check that answer just now. Your plan has not changed." No new patient string.
- The judge panel labels such a row "Not sent to Tencent ADP" and says Tencent ADP was not contacted, with the reason in plain words. The exact strings are drafted for Gate 1 in `patient-experience-copy.md`.
- No reservation number, count or ceiling reaches the patient surface. The operator command (15.5) is where they are read.

### 15.5 Operator path

[hypothesis] A module command reads `APP_DATABASE_URL` and offers `status`, `clear-halt --reason` and `mark-lost <number> --reason`.
It prints counts, ceilings, the halt state and the latest rows without words, request bodies or secrets.
It is the only way to clear a halt. It runs where the operator holds the database URL; whether Render's free plan offers a shell is [unknown].

### 15.6 Unchanged

The v2 schema, instruction v2, the 15-second cap, every byte limit, one transport call per extraction, no retry, no lexical fallback, code-owned decisions and fictional-only processing are unchanged.
Plan, deadline, owner, urgency, closure and the durable-stop rule are unchanged.
Tencent processing region and retention remain [unknown]; real patient data stays out of scope.

### 15.7 Least-confident decisions

- **Halt on any failure.** Safer, but one timeout from any visitor pauses live checks for everyone until an operator clears it, during judging too.
- **One call at a time.** Two judges checking within the same 6 seconds will see one unavailable result.
- **Operator access.** Clearing a halt needs the production database URL on a trusted machine.
- **Ceiling values.** They are a product decision, recorded in `00-status.md` when the user sets them; ADP pricing per call is [unknown].
