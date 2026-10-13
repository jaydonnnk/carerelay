# Program design: CareRelay urgent-advice accessibility

**Gate 3 amendment: RE-APPROVED 13 October 2026 Singapore time.**
[verified] The user explicitly answered "Yep i approve." Section 9 is the
re-approved program-design amendment against approved Gate 2 revision 4. Sections 1 to 8
remain the prior contract/history, with current upgrade precedence specified in
section 9. Historical approval was last renewed on 1 October 2026, not an
approval of this upgrade. `00-status.md` owns gate state. Gate 1 copy, Gate 2
semantics including section 5.2, and Gate 4 are unchanged. No implementation
is authorised by gate approval. The separate user instruction authorises committing,
publishing, merging and pushing this documentation tree and preparing the Gate 4 handoff.

**Gate 3: APPROVED 30 September 2026 (re-approved).** First approved 26 September 2026. Reopened because Decision **D-1b** moves the clinical screens from server-rendered Python to a Next.js frontend on Vercel, which changed this document's file list (§2) and falsified its statement that no public auth flow is implied. **The reopened change is confined to §1 and §2.** The type contracts, call stacks and test plan in §3 to §8 are unchanged. **Re-approved 30 September 2026.**

Authority: `00-status.md` records Gate 1, Gate 2 revision 3 and Gate 3 as approved.

**Amended at approval (26 September 2026):** §6's blocking clinical dependency is **resolved by decision** — the user selected **Option A + C** from `clinical-review-blocker.md`: a non-clinical comparator (A) with the fixture sourced from attributable published guidance (C). Consequence: **D6's comparator material changes, which is a Gate 2 backtrack** and is recorded as such in `00-status.md`. Two of the three PlanBack kill conditions are lifted out of the study and run immediately with no participants (§6.1, new).

## 1. Scope and stop conditions

- **[verified, approved design]** Python 3.13, FastAPI and SQLite remain the backend default on Render, with the SQLite path supplied by `APP_DATABASE_URL` on a mounted persistent disk. **[REOPENED AND RE-APPROVED 30 September 2026]** The **Node and Next.js reversal is now made**: the clinical frontend is a Next.js app on Vercel calling the Render API as JSON, so server-rendered HTML and vanilla JS are no longer the presentation target (Decision **D-1b**, user instruction 30 September 2026). The original trigger required this decision before the first domain-code commit; Slices 1 to 3 had already shipped, so it is recorded as **made now**, with the reason and the date. A public deployment and a shared bearer token are now implied (§2).
- **[verified, approved design]** One bounded, scripted recommendation fixture, one simulated provider, one caregiver name, one failed action, one interruption. The fixture is labelled as a research demonstration. No arbitrary symptom input may generate a patient-ready disposition without a qualified reviewer and authorised protocol.
- **[verified, approved design]** WorkBuddy is the primary coordinator path. It must execute the MCP tool through the platform, and the ledger must show the platform failure origin. If Gate A fails, use a labelled `local-sim` path and weaken the platform claim. CodeBuddy development history is the recorded usage-proof fallback; its proof is not yet present.
- **[verified, approved design]** The fixed card and the Gate B comparison precede the Closure Contract build in Gate 4. D9 scheduled reassessment, Mandarin voice, real booking, a second adapter, and caregiver messaging are outside this build.
- **[hypothesis]** If the card meets the approved PlanBack cut rule, stop and replan before implementing PlanBack or the Closure Contract. If any contract invariant fails during later slices, stop feature work and repair it.

## 2. Files

The list is the intended implementation footprint, not files authorised by this draft. Exact package names are local choices. Gate 4 may cut a file with the capability it serves, but may not silently move its responsibility across the approved trust boundary.

| File | Responsibility |
|---|---|
| `pyproject.toml` | Pin the Python version, runtime and test dependencies, and focused check commands. **`jinja2` is removed** (declared at line 12, imported nowhere; D-1b leaves no server-side HTML to render). No install is authorised by this document. |
| `src/carerelay/__init__.py` | Package marker only. |
| `src/carerelay/domain/models.py` | Frozen value types and enums for disposition, facts, consent, attempts, evidence, expiry, PlanBack, and closure. No I/O. |
| `src/carerelay/domain/rules.py` | Pure route validation, PlanBack comparison, abstention, transition projection, ownership, closure, and four-line projection rules. No I/O, SDK, or wall clock. |
| `src/carerelay/state.py` | SQLite schema and repositories, including append-only rows, atomic writes, dedupe, and read projections. |
| `src/carerelay/service.py` | Application use cases: intake, restatement, action, callback, consent, expiry, reassessment, and resume. The only layer allowed to coordinate domain, store, coordinator, and clock. |
| `src/carerelay/coordinator.py` | WorkBuddy SDK boundary plus a separately labelled local simulation implementation. Returns structured values only; never writes the database. |
| `src/carerelay/tools.py` | MCP `get_episode`, `submit_simulated_request`, and `record_evidence` handlers. Rechecks authorisation, consent, route, and attempt key server-side. |
| `src/carerelay/simulated_provider.py` | One deterministic, local-only scripted provider port. Every response has `simulated: true`. |
| `src/carerelay/api.py` | FastAPI routes from Gate 2 §3.1, request validation, **the shared bearer-token dependency on every route and on `/ledger`**, CORS locked to the Vercel origin, and HTTP error mapping. No clinical decision logic. |
| `src/carerelay/presentation.py` | **JSON serializers only** (patient, judge, research). Policy-owned text only. Owns no state and, under D-1b, renders no HTML. |
| `src/carerelay/templates/` | **Removed under D-1b.** The clinical screens are Next.js components under `frontend/`. This directory does not exist and is not created. |
| `src/carerelay/static/` | **Removed under D-1b.** Presentation assets live with the Next.js app. |
| `Dockerfile`, `render.yaml` | Backend image and the Render service definition: the paid plan, the **mounted persistent disk**, and the `APP_DATABASE_URL` mount path. |
| `frontend/` (Next.js) | The clinical frontend on Vercel: the one-question patient screen, the four-line unresolved and expired renderings, the hint disclosure control, and the judge ledger view. Calls the Render API as JSON. **No clinical rules**: text comes from the API, never from a component. |
| `frontend/lib/api.ts` | Typed API client and the bearer-token header. No policy logic. |
| `fixtures/scripted_episode.json` | Fictional, explicitly simulated plan and permitted vocabulary. No real facility, ward, clinician, threshold, or reviewed-content claim. |
| `study/fixed-card.html` | Standalone external card to print or export, with the same fixture wording, legitimate options, link, and human route. It is not an in-app condition. |
| `study/protocol.md` | Pre-registration, allocation, consent, scripted failure question, answer key, raw outcome sheet, and cut rule before any participant session. |
| `submission/usage-proof.md` | Private capture checklist and redaction manifest for genuine WorkBuddy or CodeBuddy development history and at least three screenshots; no credentials or chat exports in the public repository. |
| `tests/test_domain.py` | PlanBack, route vocabulary, abstention, ownership, transition, closure, and expiry truth tables. |
| `tests/test_state.py` | SQLite constraints, append-only behaviour, atomicity, callback races, and restart persistence. |
| `tests/test_service.py` | Consent/version race, idempotency, coordinator failure, reassessment authority, and resume. |
| `tests/test_api.py` | Route contracts and serialized patient/ledger projections, including labels, expired copy, and the auth dependency. |
| `tests/test_coordinator.py` | Contract tests for structured outputs and observed origin; SDK availability is not faked as Gate A proof. |
| `tests/test_fault_sequences.py` | Seven deterministic injected sequences from `PLAN.md` §9, with each invariant asserted at the boundary it protects. |
| `tests/test_boundaries.py` | Import rule, forbidden-content scanner with serialized self-tests, and no-model-text-to-patient checks. |
| `tests/test_study.py` | Equal-content card check, response scoring, allocation integrity, and small-sample reporting rules. |

**Amended 30 September 2026 (Gate 3 reopen).** A public auth flow **is** now implied, so the sentence that said none was is corrected rather than left standing. `jinja2` is removed from `pyproject.toml`: it was declared at line 12 and imported nowhere, and under D-1b there is no server-side HTML to render. The approved Gate 2 `/api` routes are all mapped to `api.py`; the three MCP tools are mapped to `tools.py`; the clinical screens are mapped to `frontend/` and are not Python files.

## 3. Types and signatures

Signatures are design contracts, not implementation. All times are timezone-aware instants stored in UTC and rendered in the fixture's named display timezone. The comparison uses a canonical instant or policy-defined time bucket, never an unparsed phrase.

```python
# domain/models.py: immutable values; enum definitions omitted for readability
@dataclass(frozen=True)
class Disposition:
    episode_id: str
    version: int
    policy_version: str
    action_id: str
    clinical_deadline_utc: datetime
    next_owner_id: str
    fallback_route_id: str
    source: Literal["fixture", "reviewer", "reassessment"]

@dataclass(frozen=True)
class ExtractedPlan:
    action_id: str | None
    deadline_utc: datetime | None
    next_owner_id: str | None
    uncertain_fields: frozenset[str]

@dataclass(frozen=True)
class PlanComparison:
    matched: frozenset[str]
    mismatched: frozenset[str]
    uncertain: frozenset[str]
    # Only a known, different canonical value is a mismatch.

@dataclass(frozen=True)
class AttemptCommand:
    episode_id: str
    route_id: str
    purpose_id: str
    consent_version: int

@dataclass(frozen=True)
class AttemptSnapshot:
    attempt_id: str
    idempotency_key: str
    route_id: str
    consent_version: int
    execution: Literal["attempted", "acknowledged", "failed", "superseded"]

@dataclass(frozen=True)
class EvidenceRecord:
    level: Literal["self_reported", "documented"]
    simulated: bool
    provenance: str
    source_ref: str | None

@dataclass(frozen=True)
class EpisodeSnapshot:
    disposition: Disposition | None
    attempt: AttemptSnapshot | None
    evidence: tuple[EvidenceRecord, ...]
    consent_version: int | None
    human_acceptance_id: str | None
    escalation_id: str | None
    expiry_event_id: str | None

@dataclass(frozen=True)
class ClosureProjection:
    execution: str
    evidence: str
    closure: Literal["open", "closed_with_evidence", "escalated_to_human", "expired_unresolved"]
    action_owner_id: str | None
    care_evidenced: bool
    simulated: bool
```

```python
# domain/rules.py: no SDK, network, database, or clock import
def validate_route(route_id: str, permitted_route_ids: frozenset[str]) -> str: ...
def validate_change(value: str | None, permitted_values: frozenset[str]) -> str | None: ...
def compare_plan(expected: Disposition, extracted: ExtractedPlan,
                 action_aliases: Mapping[str, str]) -> PlanComparison: ...
def next_repair(comparison: PlanComparison, completed_rounds: int) -> str | None: ...
def project_attempt(transitions: Sequence["AttemptTransition"]) -> str: ...
def derive_closure(snapshot: EpisodeSnapshot, now_utc: datetime) -> ClosureProjection: ...
def patient_lines(snapshot: EpisodeSnapshot, closure: ClosureProjection,
                  policy_text: "PolicyText") -> tuple[str, str, str, str]: ...
def reassessment_decision(classified_change: str | None,
                          policy: "PolicyFixture") -> "StopOrFixtureDecision": ...
```

`compare_plan` distinguishes `uncertain` from a definite mismatch. Unknown extraction never generates a patient-facing accusation. The patient may correct the input, use constrained choices, reveal the plan, or take the approved human route. A third failed repair round is never offered. H0 to H3 and `dwell_seconds` are recorded, but H2 remains visible until the patient hides it. H3 is `not_recalled`, never a comprehension pass.

```python
# application ports and use cases
class Clock(Protocol):
    def now_utc(self) -> datetime: ...

class CoordinatorPort(Protocol):
    def extract_plan(self, confirmed_text: str, allowed_values: "AllowedPlanValues") -> ExtractedPlan: ...
    def propose_route(self, barrier_code: str, allowed_route_ids: frozenset[str]) -> str | None: ...
    def classify_change(self, confirmed_text: str, allowed_values: frozenset[str]) -> str | None: ...
    def execute_tool(self, scoped_attempt: AttemptSnapshot) -> "ToolResult": ...
    def resume(self, session_ref: str, scoped_snapshot: EpisodeSnapshot) -> str: ...

class EpisodeStore(Protocol):
    def load_snapshot(self, episode_id: str) -> EpisodeSnapshot: ...
    def open_attempt_once(self, command: AttemptCommand, key: str) -> AttemptSnapshot: ...
    def record_callback_once(self, attempt_id: str, callback_key: str,
                             result: "CallbackResult", origin: str) -> bool: ...
    def record_expiry_once(self, episode_id: str, disposition_version: int,
                           now_utc: datetime) -> bool: ...

class EpisodeService:
    def intake(self, episode_id: str, confirmed_text: str) -> "QuestionOrFixture": ...
    def answer_clarification(self, episode_id: str, question_id: str,
                             confirmed_answer: str) -> "QuestionOrFixture": ...
    def confirm_transcript(self, episode_id: str, corrected_text: str) -> str: ...
    def record_hint_event(self, episode_id: str, hint_level: str,
                          event: str) -> None: ...
    def submit_restatement(self, episode_id: str, confirmed_text: str,
                           hint_level: str, transcript_confirmation_id: str | None) -> PlanComparison: ...
    def record_barrier(self, episode_id: str, barrier_code: str) -> str | None: ...
    def change_consent(self, episode_id: str, scope: str, grant: bool) -> int: ...
    def open_action(self, command: AttemptCommand) -> AttemptSnapshot: ...
    def receive_callback(self, episode_id: str, route_id: str,
                         callback_key: str, result: "CallbackResult") -> ClosureProjection: ...
    def project_patient(self, episode_id: str) -> tuple[str, str, str, str]: ...
    def project_ledger(self, episode_id: str) -> "LedgerProjection": ...
    def record_human_acceptance(self, episode_id: str, actor_id: str,
                                accepted_scope: str) -> ClosureProjection: ...
    def escalate(self, episode_id: str, human_path_id: str) -> ClosureProjection: ...
    def reassess(self, episode_id: str, confirmed_change: str) -> "StopOrFixtureDecision": ...
    def resume(self, episode_id: str, session_ref: str) -> EpisodeSnapshot: ...
```

The service generates one idempotency key from `(episode_id, route_id, purpose_id)` under a server-held secret or a collision-resistant server namespace; clients never supply it. A new purpose id is an explicit authorised retry, not a double-tap. `open_attempt_once` writes the attempt and audit event atomically. The tools recheck the current consent version at execution **and** before recording a callback or evidence. Revocation prevents further recording as success.

**Callback representation:** `callbacks.callback_key` is unique for the first receipt. Every duplicate is also written to `callbacks` with a null unique key, `duplicate_of` pointing to the first receipt, and `accepted = false`. The received key is retained only in a redacted or hashed audit field. SQLite permits multiple nulls under a unique constraint. `BEGIN IMMEDIATE` serialises the lookup and insert; the transition append is in the same transaction. This satisfies Gate 2's unique-key and record-every-receipt requirements without dropping duplicate evidence. The first terminal transition in sequence order defines execution; later contradictory transitions remain visible but cannot change it.

**Human acceptance:** a recorded, authorised, named acceptance can close the *handoff obligation*. It is never displayed as evidence that clinical care occurred. `care_evidenced` remains false until non-simulated documented evidence exists. A scripted acceptance remains visibly simulated and cannot make the patient screen say care happened. This is the narrow reading of Gate 2 D4 and D11.

**Expiry:** the first patient or ledger read after an unresolved deadline calls `record_expiry_once` before projecting. No scheduler is implied. Once recorded, a backward clock cannot reopen that disposition. Later evidence can be shown with its own timestamp without erasing the prior expiry event.

**Route mapping:** `/episodes` creates the fixture-bound episode; `/intake`, `/clarifications`, `/transcript-confirmations`, `/restatements`, `/restatements/{rid}/repairs`, `/hint-events`, `/barriers`, `/consents`, `/actions`, `/callbacks/{route_id}`, `/acceptances`, `/escalations`, and `/reassessments` call the correspondingly named service operation. `/episodes/{id}`, `/options`, and `/ledger` are read projections. `/api/study/{session_id}/responses` writes to the separate research response store and never changes a clinical episode. Every write route validates a server-side episode/version or callback binding. **[REOPENED AND RE-APPROVED 30 September 2026]** The demo is no longer local-only: every `/api` route and `/ledger` sit behind the shared bearer-token dependency of Gate 2 D13, with CORS locked to the Vercel origin, so the public deployment is authenticated rather than open.

## 4. Call stacks

| Flow | Top-to-bottom call order and stop |
|---|---|
| Scripted intake | `api` validates input → `service` loads fixture and scoped coordinator session → coordinator returns structured question/fact ids → `domain` validates ids → `state` records confirmed facts → `domain` issues only the preauthored fixture disposition → `presentation` renders policy text. Unknown complaint or missing critical fact stops at the human path. Urgent fixture guidance renders before any PlanBack call. |
| PlanBack | `api` accepts text or confirmed transcript → `service` checks confirmation and hint state → coordinator extracts only canonical fields → `domain.compare_plan` → `state` records level, outcome, and repair count → `presentation` renders the policy-owned next question. Coordinator timeout stops with a text fallback and unchanged deadline. |
| Barrier and action | `api` records barrier → coordinator proposes a route id → `domain.validate_route` → `service` checks consent and opens attempt/key atomically → coordinator executes `submit_simulated_request` through WorkBuddy MCP → tool rechecks authorisation/consent/key → scripted provider responds → platform failure event returns → `state` appends `origin=platform` transition → patient and judge projections refresh. No direct backend-to-provider dispatch on the WorkBuddy path. |
| Callback and resume | Callback route authenticates its local source and binds it to an attempt → `state.record_callback_once` records first or duplicate receipt and applies first-terminal-wins → service reloads app-owned state after WorkBuddy session resume → `domain.derive_closure` → render. A duplicate or restarted session does not advance execution or deadline. |
| Expiry | Patient or judge GET → service reads injected clock → state inserts an expiry event once when overdue and unresolved → domain derives sticky `expired_unresolved` → presentation emits the approved four expired lines. No urgent action waits for this read. |
| Reassessment | Confirmed symptom-change text → coordinator returns one closed-vocabulary value → domain validates it; unknown, conflicting, or unsupported values stop at human route → only a reviewer-authorised policy branch may insert disposition v2. Without that authority, the judged fixture stops; an operational retry never enters this path. |

## 5. Test plan

These are proposed test names and failure assertions, not passing tests. Each test must fail against a deliberate single-branch defect before it counts as proof.

| Test | Assertion that must fail under the named defect |
|---|---|
| `test_domain_import_boundary` | Adding SDK, network, database, filesystem or wall-clock access under `domain/` fails a static import/call check. |
| `test_planback_known_match_mismatch_uncertain` | Correct alias and exact deadline match; a known wrong day flags only deadline; unknown extraction is uncertain, never a claimed error or success. **Kill condition K1:** a fixed adversarial corpus of correct restatements (paraphrase, alias, "today before six", code-switched phrasing) produces zero false mismatches. |
| `test_urgent_path_precedes_planback` | **Kill condition K2:** the fixture's urgent guidance renders before any PlanBack call is reached; read-back can never gate or delay it. Runs with no participants and no clinical review. |
| `test_transcript_order_and_repair_cap` | An unconfirmed voice transcript cannot be scored; two repairs are the maximum; H3 and a plan reveal never count as unaided recall. |
| `test_hint_disclosure_accessibility` | H2 remains until patient action; no timer/auto-advance; `dwell_seconds` stays out of the patient serialization. |
| `test_closed_vocab_and_missing_is_not_negative` | Hallucinated route or symptom code, missing fact and contradiction stop at human path before a tool or disposition. |
| `test_disposition_deadline_is_append_only` | Retry cannot update v1 or create v2; only authorised reassessment creates a new version with provenance. |
| `test_attempt_open_atomic_and_double_tap` | Attempt plus audit event commit together; same `(episode, route, purpose)` yields one attempt and one dispatch. |
| `test_callback_duplicate_and_reorder` | Every receipt is auditable; duplicate makes no transition; a late acknowledgement cannot reverse a prior terminal failure. |
| `test_consent_revoke_in_flight` | A revoked or changed consent version blocks dispatch, callback success, and evidence recording; the failure remains visible. |
| `test_evidence_provenance_constraint` | A simulated or unsourced row cannot be `documented`; a simulated 200 response cannot close care. |
| `test_acceptance_is_not_care` | Named human acceptance may close responsibility transfer but cannot set `care_evidenced` or say care occurred. |
| `test_expiry_sticky_after_clock_regression` | First overdue read persists expiry; moving the clock backward cannot return the disposition to `open`. |
| `test_serialized_patient_and_ledger_labels` | Unresolved/expired copy contains the original deadline and named fallback; simulated label is inside serialized patient lines and ledger; origin is `platform` only with an observed platform event. |
| `test_scanner_detects_injected_needle` | Inject a forbidden facility/clinician name, unlabelled simulated receipt, and credential into representative serialized HTML/JSON; each is detected. Test raw, unescaped and forward-slash path forms. A negative scan without this self-test is not evidence. |
| `test_fault_sequences` | Timeout, stale availability, duplicate callback, reordered callback, restart, clock change, and consent revocation each violate at least one targeted assertion when its guard is independently disabled. Shared catches do not count as branch coverage. |
| `test_study_fairness_and_scoring` | Card remains a standalone artefact; wording/options match the fixture; allocation is between subjects; the scripted post-failure question and scoring are fixed before sessions; raw counts, not percentages, are reported below ten participants. |

The seven fault sequences assert I1 deadline, I2 no false completion, I3 idempotency, I4 named owner or visible lack of one, and I5 missing is not negative at both API and serialized patient surfaces. A successful unit test or static check is not evidence of WorkBuddy access, clinical safety, human learning, or patient benefit.

## 6. Gate B protocol and decision rule

### 6.1 The two kill conditions that need no participants (new, 26 September 2026)

`clinical-review-blocker.md` §4 found that two of the three approved PlanBack cut conditions are **pure system properties**. They were buried inside a study that cannot run. They are lifted out and execute **before any participant work**, with no clinical review required, because no guidance is shown to anyone.

| Cut condition | Test | Kills PlanBack if |
|---|---|---|
| **False mismatch** — a critical correct statement flagged as wrong | `test_planback_known_match_mismatch_uncertain` plus a fixed adversarial corpus of correct restatements (paraphrase, alias, "today before six", code-switched phrasing) | Any critical **correct** statement is flagged as a mismatch |
| **Delayed emergency guidance** — read-back delays the urgent path | `test_urgent_path_precedes_planback` asserts the fixture's urgent guidance renders before any PlanBack call is reached | Emergency guidance is ever placed after, or gated behind, read-back |

**These two run this week and are independent of Gate A, recruitment and review.** If either fails, PlanBack is cut before any further build — which is the single largest risk reduction available to the project right now. **[This is a Gate 3 approval amendment, not a new gate.]**

### 6.2 The participant comparison: Option A, with Option C dropped

**[verified, approved decision]** The user selected **Option A + C** on 26 September 2026. **That selection is superseded for Option C: Option C was dropped on 1 October 2026** (see the paragraph and heading below), so the decision now carries **Option A alone**. The 26 September selection of Option A itself still stands. The card remains a **standalone external artefact**, but the comparison material is **non-clinical**: both conditions administer a content-neutral instruction task of the same shape, carrying **no symptom, urgency or disposition content**. The mechanism under test (read-back improves retention, and a truthful status prevents false completion) is content-independent.

**[verified, approved decision] Option C is dropped, 1 October 2026.** The user answered "drop" to the decision recorded in `00-status.md`. The source check ran the same day and cleared nothing, for two independent reasons:

1. **No source clears.** **[verified]** MOH clause 11 and HealthHub clause 12.1 both require prior written permission to reproduce content, and the Singapore Open Data Licence reaches **Datasets only**, not website content. The UK Open Government Licence route clears the licence but fails **Singapore applicability**: its routes (111, GP) do not exist here.
2. **Option C contradicts Option A.** **[verified]** Option A makes the material content-neutral and names no real service; Option C requires the wording to be quoted **verbatim** from attributable published guidance. No published guidance contains "the fictional provider's same-day review". A fixture built from fictional entities cannot be quoted verbatim from anywhere, so Option C was unsatisfiable as written, and no amount of searching or permission-seeking fixes that.

**What replaces it.** **[verified]** Under Option A the fixture is **Tier 1 non-clinical content** (`clinical-review-blocker.md` section 3): it names no symptom, urgency, threshold or real facility. Its honesty rests on **asserting no clinical claim**, not on quoting one. The fixture therefore keeps its simulated research-demonstration label, keeps `PERMITTED_CHANGE_CODES` empty so every reassessment fails closed to the human path (D7), and is **not** presented as sourced from any authority. Section 8 item 2 still holds in full: no symptom-to-disposition rule is authored, and the reassessment endpoint stops at a human route until a reviewed branch exists.

**[verified] This edit reopens Gate 3** (`AGENTS.md` section 5). It adds no clinical wording and changes no other approved content.

**[hypothesis]** This **changes D6's comparator material**, which is a **Gate 2 backtrack**, recorded in `00-status.md`. The Gate 2 D6 decision (external artefact, between-subjects, scripted post-failure question) is unchanged; only the *content* of the material changes, and with it the claim the study can support.

**What the study can and cannot now claim.** It measures the **mechanism** — does read-back plus truthful status change comprehension, burden and false-completion belief. It does **not** measure whether care advice itself is understood, and the submission must say so plainly. Impact & Relevance loses weight accordingly.

**[hypothesis, prospective operationalisation]** Before the first dyad, freeze the exact wording, answer key, allocation order, five-point burden item, task-time rule, and analysis sheet in `study/protocol.md`. For equal-sized conditions, "equal action/deadline recall" means the card has at least as many dyads with **both** fields correct; "lower burden" means a lower median burden rating, with task time reported separately. A critical correct paraphrase falsely repaired, or emergency guidance delayed, independently triggers the approved PlanBack cut — and §6.1 now tests both before any participant is recruited. Small samples provide a directional decision, not efficacy evidence. With fewer than three target dyads per condition, make no HCD validation claim. Do not report percentages below ten participants.

The primary false-completion outcome is each participant's uncoached yes/no answer to whether care has been arranged after the failed or unconfirmed attempt. Record raw answers and burden, including adverse reactions to read-back. The scorer sees the answer key and response, not the project hypothesis. No result is claimed yet.

## 7. Effort and risk

**[hypothesis, planning estimate]** Gate 2's review estimated 90–150 person-hours of build plus 20–35 for the baseline. The breakdown below makes that range inspectable; it is not a measured velocity or a promise.

| Work | Person-hours |
|---|---:|
| Environment and application skeleton | 5–8 |
| Pure domain, fixture boundary and PlanBack | 17–28 |
| SQLite state, transactions and Closure Contract | 20–34 |
| API, patient view and judge view | 18–28 |
| WorkBuddy/MCP path and labelled fallback | 12–20 |
| Focused tests, seven faults and serialization checks | 18–32 |
| **Build total** | **90–150** |
| External card, protocol, recruitment, sessions and analysis | **20–35** |
| **Combined, before submission assets and external delays** | **110–185** |

At 26 September, the 16 October submission is about 20 calendar days away. **[hypothesis]** The upper build range plus the baseline is unlikely to fit a solo schedule alongside Gate 4, clinical review, Gate A, and submission assets. The design has already cut D9, voice, Chinese release work, a second adapter, and caregiver messaging. Gate 4 must sequence the baseline first and assign explicit dates and stop conditions; it must not silently remove the Closure Contract tests to make the schedule look green.

## 8. Least confident decisions

1. **[unknown] WorkBuddy tool origin and restart:** Gate A has not proved that the SDK exposes the required failure event or resume semantics. This is the strongest external blocker. Record actual request ids, origin, versions, latency, and failure output during the authorised spike. If absent, label local simulation and weaken the claim.
2. **[unknown] Clinical authority:** No reviewer or authorised protocol exists. The scripted fixture can demonstrate workflow behaviour only. The reassessment endpoint must stop at a human route until a reviewed branch exists. Do not turn the mockup's 995 example into code as if reviewed.
3. **[resolved, 26 September 2026; amended 1 October 2026] Gate B material authority:** The blocking dependency was resolved by decision, and the decision is now **Option A alone** (`clinical-review-blocker.md`). **Option C was dropped on 1 October 2026** (§6.2; the source check ran and cleared no source, and Option C contradicted Option A). The comparator material is **non-clinical** and administers no symptom, urgency or disposition content, so no clinical review is required to run it. The fixture is **authored rather than sourced**, and it asserts **no clinical claim**; no source is claimed for it. The bilingual card and any Chinese participant-facing text stay out of the judged study. This is recorded as a **Gate 2 D6 backtrack**.
4. **[hypothesis] Callback representation:** Nullable first-receipt key plus `duplicate_of` preserves both uniqueness and a row for each duplicate. Prove under two concurrent writers and a crash; if it cannot be made atomic, backtrack Gate 2 rather than silently losing receipts.
5. **[hypothesis] Human acceptance semantics:** Acceptance can close a handoff obligation while care remains unevidenced. Patient copy must make that distinction clear; any projection that reads as care completion fails I2 and requires a Gate 2 backtrack if the approved closure name prevents honest rendering.
6. **[unknown] Baseline advantage and user burden:** No dyad has been observed. A simpler card may win, and a correct paraphrase may be falsely corrected. Gate B is a kill test, not a marketing exercise.
7. **[hypothesis] Schedule:** Even the 110-hour lower bound excludes assets and dependency delays. Gate 4 should cut scope or record a credible staffing plan before authorising code.

**Gate 3 review question:** Are these file and method boundaries, test assertions, callback interpretation, and effort acceptable as the program design? Approval of Gate 3 would authorise drafting Gate 4 only; it would not authorise code, installs, credentials, recruitment, external calls, commits, or a push.

**Resolved at approval (26 September 2026):** approved, subject to the amendments recorded at the top of this document. Gate 4 is now authorised to be drafted.

## 9. Patient-experience and ADP read-back amendment: 13 October 2026

**Gate 3: RE-APPROVED 13 October 2026.** The user answered "approve"
to section 9.12's missing bundle identity correction. Earlier approval that
day was "Yep i approve." This section amends the
existing program design against Gate 2 revision 4, section 13, approved on
13 October Singapore time. It does not replace the historical contract above.
For this upgrade, section 9 takes precedence over obsolete signatures, storage,
platform, expiry-reader, study and effort statements in sections 1 to 8.
`00-status.md` remains the sole gate authority. Gate 1's twelve screens and exact
copy, Gate 2 including section 5.2, and Gate 4 are unchanged.

Including the re-approved identity correction in section 9.12, contracts retain
their **[verified design approval, behaviour remains hypothesis]** status unless
explicitly labelled otherwise. Approval makes them design authority, not passing
evidence. No implementation, tests, migrations, install, credentials, live ADP
call, database mutation, participant contact, deployment, commit or push is
authorised here. The old conditional Slice 13 remains unbuilt and has a different
intake/classification scope. This section supplies no upgrade slice plan.

### 9.1 Current source, preservation and smallest sufficient change

**[verified, source inspection in this session]** At inspection, HEAD is
`aca4594485f3e465daa461bf8139033458b2b81c`. The inherited dirty documentation is
carried into `codex/patient-experience-program-design`. No remote verification
was performed here; the main/remote equality in the handoff is a dated snapshot.
The following are upgrade gaps, not reopened claims about the shipped repairs:

| Current file/symbol | Observed gap | Programming consequence |
|---|---|---|
| `src/carerelay/api.py:create_episode`, `get_episode`, `patient_page` | Shared fixture ID; no-disposition reads and bare `/` return fixture lines | Distinct explicit creation; genuine no-plan projection; retire bare patient renderer |
| `frontend/app/page.tsx:PatientPage`, `frontend/app/actions.ts` | Render creates; hint actions revalidate that render | Render/revalidation must only read the existing locator; no create effect |
| `frontend/lib/api.ts:PatientProjection`, `call` | Type omits existing closure/evidence and trusts JSON by cast | Versioned runtime decoding, including nullable no-plan; no fabricated compatibility lines |
| `service.py:permitted_options`, `project_patient`, `project_ledger` | Options from configured policy without disposition; several separate reads | One coherent bundle and recorded policy version, then domain derivation |
| `service.py:repair_restatement`, `_score` | Latest-parent check exists; repair text is extracted and compared as a new whole plan | Preserve that guard and add explicit same-version field retention |
| `api.py:_DB_LOCK`; both stores' snapshot readers | API lock surrounds extraction; SQLite SELECTs have no encompassing snapshot transaction; Postgres `_read` alone does not promise one MVCC snapshot | Short transaction scopes; no held connection/DB lock over ADP; coherent reads and final rechecks |
| `service.py:open_action`, `tools.py:submit_simulated_request` | Local simulation and current stop/consent guards exist; public purpose is caller-supplied; final checks/invocation are separate | Fixed server purpose; serialize stop/consent versus final local invocation on both engines |
| `coordinator.py:LocalSimulationCoordinator.extract_plan` | Bounded lexical scanner normalises spans; no ADP runtime adapter | Keep labelled simulation separate; ADP requires exact-source spans, not normalised substrings |
| `submission/adp-agent-instruction.md`, `spike/gate_a/probe.py:_reply_text` | Published schema has canonical `action_id`, lacks offsets/uncertainty; spike concatenates text without proving answer-channel separation | New adapter/envelope contract; do not reuse spike text aggregation as production proof |

**[verified]** Source policy is `fixture-provisional-0`; action
`attend_same_day_review`; original owner `patient`; fallback `nurse_line`.
Scenario clock is 30 September 2026 09:00 SGT; stored example deadline is
`2026-09-30T10:00:00+00:00` (18:00 SGT). Fixture timezone is the existing fixed
SGT offset. Wire timezone name is `Asia/Singapore`. Do not replace these with
the browser's date or manufacture a clinically reviewed policy.

**[verified, recorded evidence only]** The 12 October record reports 945 passed,
46 Postgres skips, one existing warning and 39/39 truthfulness mutations RED.
None was rerun here. Slice 9's participant run was cut, not passed. Positive ADP
extraction, Postgres ordering/restarts and benefit over the fixed card remain
**[unknown]**.

The smallest sufficient change extends the current read/API/service/store
boundaries, adds one command table and a separate extraction adapter, and uses
the existing events for navigation, cue provenance, revision and stop. There is
no stored screen, mutable closure, second browser state machine, new scheduler,
identity system, evidence verifier, provider or clinical branch.

### 9.2 Exact future file footprint

Paths below are repository-relative. These are planned changes, not files
created or implemented by this assignment. `.tsx` names below are production
Next.js source contracts; no visualisation file is created as `.tsx`.

| File | Planned responsibility |
|---|---|
| `src/carerelay/domain/models.py` | Immutable journey, command, source-span, retained-field and cue types; retain existing enums and axes |
| `src/carerelay/domain/rules.py` | Pure journey step/command validation, whole-answer doubt checks, canonicalisation/field merge; preserve closure and durable-stop semantics |
| `src/carerelay/state.py` | Protocol, SQLite command schema and transaction-bound readers/writers; episode revision, atomic completion and dispatch reservation |
| `src/carerelay/postgres_schema.py` | Same additive table/constraints/indexes, append-only coverage |
| `src/carerelay/postgres_store.py` | Postgres implementation of the identical protocol and episode lock order |
| `src/carerelay/journey_commands.py` (new) | Canonical request bytes/digest and authenticated operation-token codec; no patient wording or decision rules |
| `src/carerelay/adp_extraction.py` (new) | Separate extraction port, transport/envelope validation, strict JSON/source grounding and labelled offline adapter |
| `src/carerelay/service.py` | Start, prepare/claim/finalize/replay, confirmation, extraction outside transactions, authoritative projection; server-owned action purpose |
| `src/carerelay/presentation.py` | Serialize the domain result, receipts and provenance; no inference or authored copy |
| `src/carerelay/api.py` | Typed amended routes, shared-token auth, phased locking, errors, optional read-only token preparation; retire bare `/` fixture renderer |
| `src/carerelay/tools.py` | Reuse the same episode/consent/version/dispatch guard at MCP invocation and evidence boundaries |
| `src/carerelay/coordinator.py` | Keep action `LocalSimulationCoordinator`; delegate explicitly labelled offline extraction only when configured; no ADP action capability |
| `src/carerelay/demo/fixture.py` | Versioned exact Gate 1 journey-copy data and allowlisted example binding; current policy/aliases and scenario retained |
| `frontend/lib/api.ts` | Server-only API calls and operation preparation; decode bounded unknown JSON, never trust a TypeScript cast |
| `frontend/lib/journey.ts` (new) | Shared wire types/runtime invariant decoder, with no text parsing or clinical derivation |
| `frontend/lib/episode-locator.ts` (new) | Server-only signed opaque locator cookie; start nonce/candidate identity, no words or credentials |
| `frontend/app/example/route.ts` (new) | Read-only browser bootstrap/explicit new-example navigation: set locator cookie, redirect to entry; no FastAPI mutation |
| `frontend/app/page.tsx` | Read locator and current episode; start/recovery without creating on render |
| `frontend/app/actions.ts` | Explicit user actions through server-only client; verify Origin/current locator; retain/reuse operation identity for lost responses |
| `frontend/components/PatientJourney.tsx` (new) | Thin accessible renderer of server-selected step/approved text; draft review stays local/unscored |
| `frontend/components/HintCard.tsx` | Server-recorded reveal before receiving plan payload; native dialog, patient hide/Escape and focus restoration |
| `frontend/app/globals.css` | Approved palette/layout, visible focus, reflow, enlarged text; icons supplement words |
| `frontend/app/ledger/page.tsx` | Judge-only new provenance/receipts and revision, separate from patient navigation |
| `tests/test_journey.py` (new) | Pure step/invariant matrix and serialized API no-plan/screen controls |
| `tests/test_journey_commands.py` (new) | Token binding, replay, same-operation races, lost responses, SQLite crash atomicity |
| `tests/test_field_repair.py` (new) | Retention, latest-parent, confirmation, whole-answer contradiction and cue cases |
| `tests/test_adp_extraction.py` (new) | Offline parser, envelope, grounding, limits, fake transport and timeout counterexamples |
| `tests/test_journey_postgres.py` (new) | Disposable real-engine migration, races, atomicity and fresh-process proof |
| `tests/_mutate_patient_experience.py` (new) | Independent guard mutations with passing controls, actual failures and byte-exact restores |
| `tests/test_api.py`, `tests/test_service.py`, `tests/test_state.py`, `tests/test_postgres_store.py`, `tests/test_boundaries.py`, `tests/test_ledger.py`, `tests/test_truthfulness.py`, `tests/test_truthfulness_postgres.py`, `tests/test_deployment.py` | Reconcile existing contracts and regression/scanner/protocol coverage, preserving shipped repair assertions |
| `docs/reviews/patient-experience-browser-accessibility.md` (future) | Manual browser/assistive-technology observations and limits, not passing placeholder evidence |
| `docs/reviews/adp-readback-observations.md` (future) | Later authorised live extraction/refusal/negation corpus and redacted provenance |
| `docs/plans/urgent-advice-accessibility/00-status.md`, `patient-experience-upgrade.md`; `AGENTS.md`, `docs/PLAN.md`, `docs/DESIGN_PRINCIPLES.md`, `tasks/todo.md`, `PROGRESS.md` | Scope/state/evidence mirrors, updated only as work is actually authorised/proved |

No dependency, lockfile, hosting, clinical policy, Gate 1 copy/prototype or Gate 4
change is required by this design. Existing `httpx` is the proposed transport;
verify runtime packaging later, and record an unavailable check without installing.
Later operator instruction/runbook revisions belong with authorised ADP enablement,
not with this drafting assignment.

### 9.3 Authoritative values and serialized projection

Signatures/types below have no implementation bodies. Existing frozen
`Disposition`, `ExtractedPlan`, `PlanComparison`, `ClosureProjection`,
`PolicyFixture` and `PolicyText` remain. Existing comparison-field names are
`action_id`, `deadline_utc`, `next_owner_id`; do not mix wire span keys with them.

```python
Field = Literal["action_id", "deadline_utc", "next_owner_id"]
Step = Literal["start", "plan", "readback", "repair", "barrier", "permission",
               "unresolved", "stopped", "expired", "accepted", "handoff",
               "documented", "recovery"]
CommandKind = Literal["create", "select_example", "readback_started", "confirm_words",
    "score_words", "repair_words", "show_plan", "hide_plan", "h3",
    "select_barrier", "grant_share", "decline_share", "revoke_share", "request",
    "supersede_extraction"]

@dataclass(frozen=True)
class PlanView:
    disposition_version: int
    policy_version: str
    action_id: str
    action_text: str
    deadline_utc: datetime
    deadline_display: str
    display_timezone: str
    original_owner_id: str
    original_owner_display: str
    current_owner_id: str | None
    current_owner_display: str | None
    fallback_route_id: str
    fallback_display: str

@dataclass(frozen=True)
class OutcomeView:
    execution: ExecutionStatus
    evidence: EvidenceLevel
    closure: ClosureState
    care_evidenced: bool
    accepted_by: str | None
    accepted_scope: str | None
    escalation_path: str | None
    escalation_outcome: str | None
    expiry_recorded: bool

@dataclass(frozen=True)
class FlowView:
    stopped: bool
    stop_reason: str | None
    stopped_disposition_version: int | None
    readback_attempt_id: str | None
    latest_restatement_id: str | None
    selected_repair_field: Field | None
    completed_repairs: int
    effective_hint: HintLevel
    card_visible: bool
    interpretation: Literal["idle", "pending", "scored", "unavailable", "uncertain"]

@dataclass(frozen=True)
class ChoiceView:
    choice_id: str
    text: str

@dataclass(frozen=True)
class QuestionView:
    question_id: str
    text: str
    choices: tuple[ChoiceView, ...]

@dataclass(frozen=True)
class CommandOffer:
    kind: CommandKind
    offer_id: str
    permitted_choice_ids: tuple[str, ...]
    operation_token: str | None  # absent until the exact request digest is bound

@dataclass(frozen=True)
class JourneyProjection:
    schema_version: Literal["carerelay-journey-v1"]
    episode_id: str
    disposition_version: int | None
    policy_version: str | None
    revision: int
    as_of_utc: datetime
    clock_mode: Literal["scenario", "system"]
    plan_redacted: bool
    plan: PlanView | None
    outcome: OutcomeView | None
    flow: FlowView
    step: Step
    question: QuestionView | None
    commands: tuple[CommandOffer, ...]
    lines: tuple[str, ...]
    text: Mapping[str, str]  # only the selected screen's approved surrounding copy
    revealed_plan: PlanView | None
    simulated: bool
    fixture_label: str
```

Wire keeps existing top-level `closure: str | None` and `care_evidenced: bool`,
plus `execution`, `evidence`, `action_owner_id`, as exact aliases of `outcome`
and `plan.current_owner_id`, not separately calculated fields. No-plan:
`plan=outcome=revealed_plan=question=null`, `disposition_version=policy_version=
closure=execution=evidence=action_owner_id=null`, `care_evidenced=false`,
`lines=[]`, `step=start`, `stopped=false`, repair count 0; no route, deadline,
owner, restatement or action command. Episode identity/revision/simulation label
remain. A recorded-policy row existing elsewhere does not imply a disposition.
No browser episode also renders approved start copy, without a fabricated API
episode. Unknown episode is 404 and renders recovery, never the example.

Entry/recovery transport text must exist when FastAPI cannot answer. Keep a
small exact Gate 1 entry/recovery-copy mirror in `frontend/lib/journey.ts`,
validated for equality against the backend copy catalog. It selects no plan or
clinical sentence. All loaded journey/repair/outcome copy comes from the server
projection. This narrow offline-copy mirror must not grow into browser policy.

`revision` is the highest committed `events.id` for this episode, or 0 when
none. Every new semantic write appends a corresponding event in the same
transaction. Claims/terminal receipts also append lifecycle events. The claim
captures its post-claim revision; finalisation expects that revision, not the
pre-claim token revision. Integer IDs must fit JavaScript's safe range or decode
as invalid; before exceeding it, a separately reviewed wire-version change is
required. Timestamps and process counters are not revision substitutes. Writers
serialize by episode, so sequence assignment and commit order agree for that
episode. A projection is a coherent committed snapshot, not a promise that
nothing will change after the response.

Read by `disposition.policy_version`, resolving a registered policy/text bundle;
never compare/render old records with whichever policy happens to be injected
today. If policy/text is missing or incompatible, return recovery with no
progression commands. Preserve the original record. Missing approved display,
unknown enum/schema, mismatched alias fields, plan with no disposition, stopped
with scoring commands, multiple questions, or ungrounded success is invalid.
Frontend decoder must reject the whole response, not partially render it.

**Unaided disclosure:** the server-internal canonical plan remains available
to derivation. On H0/H1 read-back the browser-visible `plan` contains identity
and axes only via the enclosing projection; the wire `plan` and answer-bearing
`lines`/text are null/empty, using an explicit `plan_redacted=true` flag.
`plan_redacted` is true on that wire/domain branch. Outcome/current
acting owner can stay in internal derivation, but answer-bearing owner/action/
deadline/fallback displays and IDs are omitted from this response. Do not put
them in hidden DOM, input placeholders, HTML/RSC payload, data attributes,
accessible names or a preloaded dialog. This is a presentation redaction for
unaided input, not an authentication claim; previously viewed plan/ledger and
shared-token API access exist. `disposition_version`, `policy_version`, outcome
axes and flow still identify the same plan. A decoder distinguishes this
assessed-redacted branch from genuinely no-plan using the non-null version and
`plan_redacted`. The top-level owner alias is also null while redacted, and
`revealed_plan` is null until a recorded show. Redact hidden readback/repair
plan data at H2 as well; the selected timing-repair sentence is the explicitly
approved answer-bearing exception. Patient-entered draft/confirmed words are
escaped and may repeat the plan; that is not server-supplied answer leakage.
Choosing Show my plan records a cue before returning its data.

Deadline display uses the injected backend clock and stored instant. Scenario
mode permits `6pm today` against 30 September only. System mode may use that
form only on the stored local day; on another day use explicit approved date
formatting, without changing the instant. If a new sentence/template is needed,
Gate 1 approves it first; otherwise recovery/refusal is the honest outcome.
The deployment may remain a scenario demonstration until those strings exist.

### 9.4 Screen and contradiction matrix

Apply existing closure precedence first: trusted documented evidence, expiry
(including sticky recorded expiry), relevant acceptance, actual successful
handoff, open. Apply independent stopped/permission checks to remove automation.
This section does not change that order. Terminal outcomes have no question.
Normal steps have exactly one question; plan/start/outcome/recovery have none.
The local unscored draft review is a subview of readback/repair, not a persisted
screen. A pending command gives no new scoring/request command.

| Gate 1 screen | Derived values and allowed command offers |
|---|---|
| `00-start.html` | Absent episode or true no-plan; approved start text; explicit `create` then `select_example` only, never guidance/options |
| `01-plan.html` | Open, active, unexpired, no `readback_started`; full plan and unresolved status; `readback_started`, show/hide, consent/revoke. Also neutral display for acknowledged/unknown contact without a stronger outcome; no new request |
| `02-readback.html` | Current-version start event, no definite repair pending; one approved read-back question; local review, `confirm_words` then `score_words`, show/hide/H3. Uncertainty and unavailable feedback use the two exact approved messages; no claim of mismatch |
| `03-repair.html` | Latest confirmed comparison has definite `deadline_utc` mismatch, completed repairs less than 2, active; one timing question; confirm then `repair_words`, show/hide/H3. Other fields have no field-specific copy offer until Gate 1 approval |
| `04-barrier.html` | Current-version understood H0/H1/H2 round, no stop/pending repair; choices booking/transport/other. `select_barrier`; booking maps to `fictional_provider`; unsupported choices record stop/refusal with approved wording |
| `05-permission.html` | Current supported barrier, no attempt: grant/decline with unchecked checkbox; `request` only after recorded current grant. Decline leaves permission choice and offers no request. Attempt with no terminal callback: approved No reply yet substate, no redispatch. Acknowledged returns neutral plan, never successful care |
| `06-unresolved.html` | Actual winning failed request or recorded failed human handoff, still open, no stronger closure; approved failed heading plus exact four unresolved lines; show/hide/consent/revoke only. Loading/timeout with unknown action outcome cannot choose this heading |
| `07-stop.html` | Current stop from H3, exhausted repairs, refused barrier or reassessment, unresolved; approved stop heading and four unresolved lines; show/hide/consent/revoke. Operator human transfer remains a separate service/MCP authority, never a patient command |
| `08-recovery.html` | Transport/auth/unknown-ID/invalid projection failure; approved recovery/loading text; Try again reads the same locator only. No guessed episode, plan or mutation |
| `09-expired.html` | `expired_unresolved` wins even if waiting/failed/accepted/stopped; original deadline and approved expired lines; no automated progression. Consent/revoke and legitimate operator human transfer remain recorded actions; transfer cannot erase expiry |
| `10-accepted.html` | Permitted recorded caregiver, scope handoff, current consent checked at recording, before expiry; `closed_with_evidence`, care false, current owner actual recorded caregiver; approved agreement notice and four lines; no question or public acceptance control |
| `11-handoff.html` | `escalated_to_human`, actual `handed_off` or legacy `handed_over`, named policy path; care false, actual path owner, approved simulated notice/lines; no question or public handoff-success control |

Trusted documented-care fixtures use `step=documented` and the separately
approved section 7 lines. No public command/selector/ADP result can create them.
A successful handoff to a path other than `nurse_line` uses approved section 7
templated lines and policy display, not the specific nurse-line heading for a
different target. A missing approved heading yields no new authored heading.

| Conflicting combination/counterexample | Required serialized result |
|---|---|
| Failed/attempted/unknown escalation with an ID | Open, original patient owner, care false; failed heading only for actual failure; no handoff-success wording |
| Acknowledged provider request, no relevant acceptance/evidence | Open, patient owner, neutral plan; acknowledgement retained on execution axis |
| Stop plus relevant acceptance/successful handoff already recorded | True accepted/handoff outcome with `stopped=true`; no questions or automation; stop is not a transfer |
| Stop plus late success/evidence callback | Refused receipt, unchanged outcome/owner/deadline; failure/duplicate audit remains allowed |
| Accepted or handed off but overdue without real documented care | Expired; historical acceptance/path retained for ledger; no revived continuation |
| Prior-version stop plus authorised newer disposition | New version may progress; previous stop remains history; old parent/token/attempt cannot act |
| Current restatement understood but H3 or durable stop exists | No barrier/request offer; H3 is not recalled; cannot reset round zero |
| Missing/corrupt record says success, two questions or active request after stop | Invalid projection/recovery; never pick a plausible screen from sentences |
| Current consent declined/revoked while a request receipt exists | No new dispatch; keep actual attempt/receipt outcome; revocation is not a failure callback |
| Late stale HTTP response after a newer revision in the same episode | Discard lower revision, fetch fresh; never repaint a pre-stop state; same revision may differ only by time-derived expiry/clock display, requiring fresh read |

### 9.5 Start, resume and exact-request replay

```python
@dataclass(frozen=True)
class OperationBinding:
    operation_id: str
    episode_id: str
    disposition_version: int | None
    expected_revision: int
    kind: CommandKind
    purpose: str
    body_sha256: str
    parent_restatement_id: str | None
    confirmation_id: str | None
    token_schema: Literal["carerelay-command-v1"]

@dataclass(frozen=True)
class CommandReceipt:
    operation_id: str
    state: Literal["pending", "applied", "refused", "unavailable", "superseded"]
    result_ref: str | None
    scored: bool
    replayed: bool

@dataclass(frozen=True)
class CommandResponse:
    receipt: CommandReceipt
    journey: JourneyProjection

def request_digest(kind: CommandKind, payload: Mapping[str, object]) -> str: ...
def issue_operation(binding: OperationBinding, *, signing_key: bytes) -> str: ...
def verify_operation(token: str, *, signing_key: bytes) -> OperationBinding: ...

class EpisodeService:
    def start_example(self, binding: OperationBinding) -> CommandResponse: ...
    def prepare_command(self, episode_id: str, *, kind: CommandKind,
                        body_sha256: str, parent_id: str | None) -> str: ...
    def confirm_words(self, binding: OperationBinding, *, text: str) -> CommandResponse: ...
    def score_confirmed(self, binding: OperationBinding) -> CommandResponse: ...
    def replay(self, binding: OperationBinding) -> CommandResponse: ...
    def supersede_extraction(self, binding: OperationBinding,
                             old_operation_id: str) -> CommandResponse: ...
    def project_journey(self, episode_id: str) -> JourneyProjection: ...
```

Bootstrap occurs before mutation: an initial request without a locator renders
start and links to the read-only Next.js `/example` handler. That handler
generates a random start nonce, candidate episode ID and creation operation ID,
sets the signed `carerelay_demo_locator` cookie (`HttpOnly`, `Secure` on HTTPS,
`SameSite=Lax`, host-only, path `/`), and redirects back to entry. The browser
therefore holds the locator before See the example can call FastAPI. First-entry
bootstrap must not create an episode or a disposition. Production is HTTPS;
loopback test mode explicitly permits non-Secure cookies and proves no public
access claim. Cookie contains only schema, nonce, candidate ID and operation ID.

Intentional new example navigation, distinct from Try again/reload, allocates a
new nonce/ID. Cookie replacement alone starts nothing. No public reset of
`demo-episode-001`; historic shared episodes remain readable. The server must
not infer a new example from a missing response, 404, remount or validation error.
If a locator exists but its candidate record is absent: show recovery with an
explicit start operation using that same creation identity. An ordinary reload
or Try again makes no POST. A lost creation response is recovered by GET of
the same candidate; if still absent, only the user's explicit same-operation
start replays creation. Same nonce can never map to a second episode.

The API authenticates Next.js with the existing bearer token; locator integrity
and operation MACs use purpose-separated HMAC derivations from the configured
server-held token. Codec receives an injected key; pure domain sees neither key
nor token. No new credential is required. Local offline tests inject a fixture
key explicitly and make no authentication claim. Production without a signing
key fails closed; rotation invalidates old unclaimed capabilities/locators and
goes to recovery, without deleting durable episodes/receipts. Do not pretend a
signed locator authenticates a patient or isolates users under a shared token.

All Next.js actions compare the request Origin/host and cookie-bound episode,
allowlist the command/choice, and forward through the server-only client. The
browser never receives the bearer/AppKey or chooses purpose/route/expected plan.
`select_example` binds a single `scripted-appointment` allowlist entry to the
existing exact-match intake. Create and intake have separate durable receipts;
a loss between them leaves genuine no-plan, and intake replay cannot insert v2.

Token issuance must precede the mutation but follow knowledge of its body.
Fixed-choice offers bind their exact bodies immediately. Free words remain local
until explicit confirmation: after local Review my answer, a server action
computes the exact request digest and asks the existing GET episode route for
read-only `prepare_kind`, `body_sha256`, `parent_id` parameters. This invokes
`prepare_command`, validates current offers and returns an operation token;
it changes no record and sends no words to ADP. Preparation is an extension of
the approved read route, not a new patient-state API. Never log those parameters.
Confirmation POST then binds exact words; it returns a new scoring token bound
to that confirmation and its post-confirm revision. The scoring POST needs the
confirmation reference, not another client text to substitute. Changing draft
words invalidates local prepared tokens; confirmation must happen again.

Digest is SHA-256 over UTF-8 canonical JSON of `{schema, kind, payload}`: fixed
keys, sorted object keys, compact separators, no NaN/floats/unknown keys; preserve
text code points, punctuation and whitespace exactly, with no trimming or Unicode
normalisation. Parent/version/confirmation references and choice are in the
payload; token itself is excluded. Backend independently recomputes it. Unknown
fields/purpose IDs are 422, not ignored. Operation MAC binds episode, version,
revision, parent, fixed purpose, kind and digest. Tokens are capabilities for one
operation, not comprehension, consent or present permission.

Under episode serialization, look for a receipt **before** rejecting the old
revision. Same token/body with completion returns its historical result reference
and a freshly read projection/allowed offers. It never reapplies, calls ADP or
dispatches. Same operation/different digest returns 409 conflict plus fresh
journey, even if stopped; stale unclaimed commands are 409 refused. Invalid MAC
is rejected without writing a claimed identity chosen by the caller. A replay
does not promote its old `understood`/applied fact into current authority.

Claimed-only operations return 202 `pending`, scored false, with fresh journey.
No automatic HTTP, framework, queue or SDK retries; reads can inspect pending.
For extraction, an explicit supersede command atomically appends the old terminal
`superseded` receipt and makes a new allowed scoring offer. This can cancel even
a still-running call: lateness is not evidence of a crash. Only one supersede wins;
late completion must see the terminal receipt and append no score. Input failure,
timeout/refusal/invalid output completes as `unavailable`, records provenance,
consumes no repair and does not set a durable stop. A new scoring operation
requires explicit user action. Server action state retains the same token/body
for a lost response; refresh can read durable pending/completion before asking
for another operation. New operation IDs cannot bypass latest-parent or action
purpose checks.

Request purpose is exactly `disposition:<version>:request_appointment` and route
is the recorded supported barrier's `fictional_provider`. Existing D5 key
derivation stays `(episode, route, server purpose)`. No public explicit retry
purpose is exposed in this upgrade. Multiple newly prepared request tokens
still resolve to that single attempt. Pending/unknown/crashed attempts never
redispatch on reload, replay, new token, direct service or MCP invocation.

### 9.6 Confirmed read-back, field retention and cue honesty

```python
@dataclass(frozen=True)
class SourceSpan:
    text: str
    start: int
    end: int

@dataclass(frozen=True)
class RetainedMatch:
    field: Field
    canonical_value: str | datetime
    source_restatement_id: str
    source_confirmation_id: str
    source_span: SourceSpan

@dataclass(frozen=True)
class ReadbackContext:
    episode_id: str
    disposition_version: int
    policy_version: str
    attempt_id: str
    parent_id: str | None
    confirmation_id: str
    confirmed_text: str
    repair_field: Field | None
    completed_repairs: int
    retained: tuple[RetainedMatch, ...]
    effective_hint: HintLevel
    claim_revision: int

def independent_uncertainty(confirmed_text: str, *, policy: PolicyFixture) -> frozenset[Field]: ...
def compare_plan(expected: Disposition, extracted: ExtractedPlan, *,
                 policy: PolicyFixture, now_utc: datetime,
                 display_tz: tzinfo) -> PlanComparison: ...
def merge_field_repair(context: ReadbackContext, extracted: ExtractedPlan, *,
                      whole_answer_doubt: frozenset[Field],
                      policy: PolicyFixture, now_utc: datetime,
                      display_tz: tzinfo) -> tuple[ExtractedPlan, tuple[RetainedMatch, ...]]: ...
def derive_journey(bundle: "JourneyBundle", *, now_utc: datetime) -> JourneyProjection: ...
```

Every scored mode, including text, needs an explicit confirmation event, exact
digest, episode/version/read-back-attempt/parent binding and a unique confirmation
reference. Existing text-digest-only event IDs are read as historical provenance,
not new scoring permission. Two identical strings in different rounds remain two
different operations. Local Review my answer calls no API/model and keeps the
approved `Preview only. Not checked or saved.` sentence true. Confirmation saves
fictional words; the preview sentence must not remain over a saved/scored answer.

**[verified copy gap, future dependency]** The approved readback/repair prototypes
review a draft but contain no explicit submit-confirmation control. A confirmation
label/help sentence needs Gate 1 approval before that control is exposed. This
is missing implementation copy, not evidence that the approved extraction/closure
architecture is false. No new string is authored or an existing Review label
silently reinterpreted here. API/offline proof can precede exposure; the visible
scoring path stays gated until the exact confirmation wording is approved.

Initial round is round 0 and cannot restart an existing unfinished current-version
ladder. Uncertainty correction and definite-mismatch repair both reference the
latest scored parent. A repair/correction with valid extraction and a comparison
increments completed repairs by one even if it stays uncertain. Two such rounds
maximum; initial failure is not one of the two. Invalid/refused/timed-out output,
confirmation, navigation and reveal/hide consume zero. H3 records `not_recalled`
and stops immediately without interpreting a revealed choice as comprehension.
Still unconfirmed after repair 2 records current-version stop in that same commit.

Field-only repair replaces the selected field with the new answer's grounded
value, including null/uncertain. Other fields may be retained only if known matched
in the immediate latest parent, for this episode/version/policy/read-back attempt
and confirmed chain. Retained provenance may point transitively to the original
grounded match. A mismatch, uncertain field or old-version value is never retained.
Never fill a null from the expected disposition or from unconfirmed draft text.

Inspect the **whole** new text before retention. If it explicitly supplies another
field, compare that new value rather than keep the old one. A definite known
contradictory value replaces the match and becomes a mismatch. Negation, doubt,
conditional language, alternatives, questions, multiple inconsistent candidates
and unsupported corrections make affected fields uncertain. A backward correction
such as `Actually I won't` can invalidate all retained fields even when it repeats
none. Explicit later correction is not silently resolved by picking the last or
longest span. Unsupported phrasing remains uncertain. Preserve the unrelated
aside positive control so the checker does not turn every separate sentence into
global doubt. This is a bounded conservative check, not general semantic proof.

Example: latest parent matched action/owner, definitely mismatched deadline.
Confirmed `today before six` repairs the deadline and retains those two known
matches. The same answer followed by `Actually I won't` cannot retain success.
If owner was uncertain in the parent, timing-only input leaves owner uncertain.
Full-answer correction can replace all three fields; it still consumes only one
repair of the same ladder. Deterministic canonicalisation stays in domain under
ADR-0007 with the same policy version and injected comparison time.

**[verified source limit]** The current `fixture-provisional-0` deadline forms
include `tomorrow before 6pm`, but not bare `tomorrow`. That literal in the Gate 1
illustration is not proven parser coverage. Under this version, bare tomorrow is
uncertain and uses the approved generic correction, while the supported wrong-day
form can select timing repair. Do not silently supply 18:00 from the expected
plan or widen the recorded policy table under its old version. If literal tomorrow
must select a definite mismatch, bring an explicit versioned policy/partial-time
comparison decision back to Gate 2 before implementation; this draft makes no
such change. Timing-only `today before six` is supported and can exercise retention.

Cue level is server-derived for the read-back attempt, monotonically at least
the highest recorded exposure. New plans begin with H1 as already approved;
no new cross-episode fading algorithm is invented. `readback_started` establishes
attempt scope and hides the previously displayed recommendation. A show event
commits H2/cued provenance **before** the response includes the full plan;
failure before return can conservatively mark cued even if the patient never
saw it, and that limitation is recorded. Hide, Escape and reload never erase
exposure. An answer-bearing timing repair also records deadline exposure;
successful repaired recall is cued, never retroactively unaided. H0/H1 clients
cannot lower it by posting `hint_level`; their level is not trusted authority.

Hide can close the dialog immediately for keyboard usability; its durable event
is still required. If that write fails, reload may show the card again, while
cued history remains. Revealing/hiding after stop is permitted and never clears
it. Dwell time is optional judge-only observation, never a timer or control.
Any constrained answer that reveals a value is marked cued; new choices/labels
need Gate 1 approval. Definite timing mismatch uses only approved timing strings
with grounded patient span and server deadline slot. If a different mismatch
needs field-specific words, offer the generic approved correction text/full
answer path with no false timing accusation, and gate specialized copy on Gate 1.

### 9.7 ADP extraction port, strict schema and stream contract

```python
@dataclass(frozen=True)
class ExtractionInput:
    confirmed_text: str
    action_forms: frozenset[str]
    deadline_forms: frozenset[str]
    owner_forms: frozenset[str]
    correlation_id: str
    instruction_version: str
    schema_version: Literal["carerelay-readback-v1"]

@dataclass(frozen=True)
class RawExtraction:
    schema_version: Literal["carerelay-readback-v1"]
    action_span: SourceSpan | None
    deadline_span: SourceSpan | None
    next_owner_span: SourceSpan | None
    uncertain_fields: frozenset[Field]
    refused: bool

@dataclass(frozen=True)
class ExtractionResult:
    mode: Literal["adp", "local-sim"]
    validation: Literal["valid", "invalid", "refused", "timeout", "transport", "disabled"]
    raw: RawExtraction | None
    request_id: str
    trace_id: str | None
    instruction_version: str
    schema_version: str
    model_version: str | None
    failure_category: str | None

class ReadbackExtractor(Protocol):
    def extract(self, request: ExtractionInput, *, budget_seconds: float) -> ExtractionResult: ...

class AdpReadbackExtractor:
    def extract(self, request: ExtractionInput, *, budget_seconds: float = 5.0) -> ExtractionResult: ...

def validate_raw_extraction(answer_utf8: bytes, *, confirmed_text: str) -> RawExtraction: ...
def assemble_answer(frames: Iterable[bytes], *, correlation_id: str,
                    deadline_monotonic: float) -> bytes: ...
```

Exactly one JSON object, exactly these six keys: `schema_version`, `action_span`,
`deadline_span`, `next_owner_span`, `uncertain_fields`, `refused`. Span is null or
exactly `{text: string, start: integer, end: integer}`. Offset units are Unicode
code points in the **exact** confirmed string, half-open `[start,end)`; no UTF-16
or byte offsets, bool-as-int, negatives, empty span or out-of-range value.
Require `0 <= start < end <= len(text)` and `text[start:end] == span.text`.
Reject duplicate keys at every JSON depth, unknown keys/types/versions, repeated
uncertainty entries, unknown field names, two objects, prose/fences, invalid UTF-8
and non-finite numbers. Refusal must have all spans null and all three fields
uncertain; no provider refusal prose is stored/shown as patient wording.
For eligible extraction, missing spans require the corresponding uncertainty;
uncertainty may also coexist with a non-null grounded span.

Transport sees confirmed fictional words, schema/instruction and independent
surface sets only. It receives no expected Disposition, answer pairing, selected
plan ID, canonical target, caregiver profile, consent record or action receipt.
The vocabulary may contain the expected words because it is the existing closed
set; with one fixture it can reveal likely answers. Exact-source grounding and
independent checks, not a claim that the vocabulary hides the answer, guard that
risk. Empty/missing fields can never be invented. Treat words as data; advice,
prompt injection or role changes cannot widen the output or action boundary.

Each call uses a new ConversationId and RequestId in the observed 32 to 64
alphanumeric/underscore/hyphen format and an anonymous per-call VisitorId.
No vendor conversation/session resume. Reuse only the transport request-body
shape observed by the spike: AppKey supplied by the backend, Contents text,
Stream/Incremental. AppKey is transport auth and must never enter the prompt.
The existing `ADP_CHAT_ENDPOINT` is operator-configured server-side; no browser
endpoint override/redirect credential forwarding. `ADP_API_SECRET` is not used
on this HTTP SSE path.

**[unknown transport detail, enablement blocker]** The current spike proves an
SSE envelope, not a verified final-answer versus reasoning discriminator. The
adapter must pin a transport profile to a later authorised redacted capture:
expected event Type, assistant message ID, final text content ID/channel,
correlation and terminal marker. Only that channel is eligible. Observed lifecycle
names include `request_ack`, `response.created`, `message.added`, `content.added`,
`text.delta`, `message.done`; do not infer success from HTTP 200 or invent
unobserved nested field names. Profile must either positively identify an
incremental final-answer channel plus its completed message or identify one
complete final-answer payload. A changed/unrecognised profile is unavailable,
not a best-effort join. If no discriminator can be established, ADP stays disabled;
this requires Gate 2 reconsideration if extraction is to proceed by another path.

Parse SSE with a bounded incremental UTF-8 decoder, blank-line frame delimiters,
multiline data, checked JSON envelopes and matching message/content/correlation.
Ignore only explicitly profiled lifecycle/heartbeat and reasoning channels;
reasoning bytes are not rendered, logged or persisted. Unknown content/channel,
out-of-order/conflicting IDs, provider `error`, incomplete stream, a terminal
before a required complete answer, or multiple final messages are invalid.
Choose incremental or final mode before assembly; never concatenate both and
double the JSON. Repeated sequence IDs are deduped only if the profiled protocol
provides them and bytes agree; otherwise ambiguous duplicate chunks are invalid.
Completion requires the pinned terminal event; EOF alone and first-byte latency
are not completion.

**[hypothesis, unmeasured limits]** Five seconds covers connection through the
entire assembled answer/terminal stream using a transport monotonic deadline,
not per-chunk timeouts that restart the clock. Domain still receives only injected
UTC time. Maximum input is 2,048 Unicode code points; maximum assembled final
answer is 16 KiB UTF-8 bytes; no automatic retry. For memory protection the
proposed parser also caps an envelope frame at 16 KiB and total wire response at
64 KiB, including ignored channels. These extra engineering limits are unmeasured;
a legitimate envelope exceeding them remains unavailable until a reviewed,
recorded adjustment, never silently accepted. Do not buffer arbitrary reasoning.

After structural/grounding validation, union provider uncertainty with independent
whole-answer doubt/contradiction checks before domain canonicalisation and
comparison. A positive source span inside `I won't go ...`, a question, or a
later `Actually I won't` cannot prove a match. Known definite wrong deadline
can mismatch; missing/unsupported/ambiguous input remains uncertain. These
checks never lexically fill a missing ADP span. No confidence threshold is used.

Timeout, refusal, invalid, disabled or transport/auth failure is unscored with
the approved unavailable sentence, same confirmed answer/current question,
same deadline/owner/closure and zero consumed repairs. A valid uncertain answer
uses the approved correction sentence and the bounded ladder. The separate
`local-sim` extractor may be selected explicitly for an offline demonstration;
it must preserve exact-source provenance or declare unavailable. It is never
invoked as a hidden fallback after an ADP failure. `ADP_EXTRACTION_ENABLED=false`
defaults to disabled ADP; interpreter mode is always visible in the judge record.

Record interpreter mode, configured instruction/schema/profile versions, request
correlation, trace if exposed, validation/failure category and known model version.
Configured instruction version is an operator assertion until independently
observed; absent provider model version is null/unknown. Persist bounded grounded
extraction/confirmed text in the fictional record, never general logs, raw SSE,
reasoning, secrets or unvalidated output. Action origin remains `local-sim`.
ADP cannot select urgency, route, request purpose, book, render patient guidance,
transfer responsibility, write evidence or declare care arranged.

### 9.8 Transactions, permission and call stacks

```python
@dataclass(frozen=True)
class JourneyBundle:
    episode_id: str  # section 9.12: verified stored row identity
    snapshot: EpisodeSnapshot
    revision: int
    policy: PolicyFixture | None
    policy_text: PolicyText | None
    events: tuple["JourneyEvent", ...]
    restatements: tuple["RestatementRecord", ...]
    commands: tuple["JourneyCommandRow", ...]
    consent_granted: bool

class JourneyTransaction(Protocol):
    def load_bundle(self, episode_id: str) -> JourneyBundle: ...
    def claim_once(self, binding: OperationBinding, *, now_utc: datetime) -> "ClaimResult": ...
    def complete_once(self, operation_id: str, *, state: str,
                      result_ref: str | None, scored: bool, now_utc: datetime) -> CommandReceipt: ...
    def append_confirmed_words(self, context: ReadbackContext, *, now_utc: datetime) -> str: ...
    def append_scored_round(self, context: ReadbackContext, extracted: ExtractedPlan,
                            comparison: PlanComparison, *, now_utc: datetime) -> str: ...
    def reserve_dispatch_once(self, attempt_key: str, *, now_utc: datetime) -> bool: ...

@dataclass(frozen=True)
class ClaimResult:
    receipt: CommandReceipt
    newly_claimed: bool
    claim_revision: int

@dataclass(frozen=True)
class DispatchPermit:
    operation_id: str
    attempt_key: str
    claim_revision: int
    # Internal capability held only by the original newly-claiming invocation.
    # Never serialized, reconstructed on restart, or issued on a replay.

class McpTools:
    def __init__(self, store: EpisodeStore, *, policy: PolicyFixture,
                 provider: "ScriptedProvider", now: Callable[[], datetime]) -> None: ...
    def submit_simulated_request(self, episode_id: str, route_id: str,
        attempt_key: str, *, permit: DispatchPermit, now_utc: datetime) -> ToolResult: ...

class EpisodeStore(Protocol):
    def journey_transaction(self, episode_id: str, *, write: bool) -> ContextManager[JourneyTransaction]: ...
    def create_with_claim_once(self, binding: OperationBinding, *, persona: str,
                               now_utc: datetime) -> CommandReceipt: ...
    def load_journey_bundle(self, episode_id: str) -> JourneyBundle: ...

class EpisodeService:
    def select_example(self, binding: OperationBinding, *, example_id: str) -> CommandResponse: ...
    def record_journey_event(self, binding: OperationBinding) -> CommandResponse: ...
    def record_barrier_choice(self, binding: OperationBinding, *, choice_id: str) -> CommandResponse: ...
    def change_share_consent(self, binding: OperationBinding, *, granted: bool) -> CommandResponse: ...
    def request_appointment(self, binding: OperationBinding) -> CommandResponse: ...
```

Transaction facade keeps pure decisions in domain and orchestration in service;
repositories perform inserts/checks with one transaction-bound cursor/connection.
Existing public `record_*` wrappers delegate to transaction-bound helpers, never
open nested transactions or call a Postgres `_read` rollback within a write.
The Python connection mutex may surround a short transaction; it is not
multi-process episode ordering and is never held through ADP.

SQLite: `BEGIN IMMEDIATE` for guard/claim/apply/expiry/stop/consent/dispatch writes;
bounded existing busy timeout; all related SELECTs in that transaction. Pure
ledger/options bundle reads use one explicit read transaction. Patient read may
write sticky expiry, therefore use a short write transaction, load once,
conditionally append expiry and its event, reload in that transaction, project
then commit. Do not read different tables between commits.

Postgres: at READ COMMITTED, every same-episode writer first locks
`episodes ... FOR UPDATE`, then performs its SELECTs **after** obtaining the
lock. Do not reuse a snapshot read before waiting for it. Patient reads take
that lock for expiry consistency. Pure ledger/options reads use a single
REPEATABLE READ READ ONLY transaction and release promptly. Existing long-held
connections remain possible with a per-connection mutex; no pool/dependency is
required for this design. Cross-episode operations use sorted episode IDs, then
attempt rows, then command rows; no reverse lock order. Creating an absent
episode uses candidate PK and operation uniqueness in one transaction, with
unique-conflict replay after rollback, not an absent-row lock that cannot lock.

All entry points that can affect the projection participate: restatement/hints,
barriers, consents, stops, callback, evidence, acceptance, escalation, authorised
reassessment, attempted dispatch and legacy wrappers. Trusted low-level fixtures
also append a revision event when used in the new runtime; old timestamps are
not reconstructed as new event ordering. No public patient control impersonates
an accepting caregiver or records successful handoff. Shared-token operator
fixtures remain simulated, not authenticated receiving-service acceptance.

Extraction phases: short transaction validates current offers and explicit
confirmation, claims once, saves a ReadbackContext and post-claim revision;
release connection/mutex/transaction; call ADP and validate; new short transaction
locks episode and checks terminal receipt, captured revision, current version/
policy, latest parent, exact confirmation, cue provenance, stop and **fresh**
deadline. If any changed, terminal refused/superseded, scored false, no round.
If overdue, persist expiry and refuse; no late answer advances a now-expired
plan. If valid, compare/merge and append score, chain provenance, stop if needed,
revision event and applied terminal receipt atomically. Temporary extraction
failure appends provenance/unavailable receipt atomically without a scored row.
Fresh projection after replay is derived in a separate coherent read if needed;
never return a stale saved screen.

Final action path: service creates/reuses one attempt and command under current
plan/consent checks; coordinator remains the action caller; MCP tool acquires the
same episode serialization, rereads stop/version/consent, fixed purpose/route,
attempt membership and dispatch reservation. It permits invocation only if a
fresh injected clock read under this lock is still before the
deadline and no sticky expiry exists; an old coordinator timestamp is not
execution-time permission. It then inserts the `dispatch_started`
event and invokes the **bounded local synchronous** provider while holding that
serialization, then commits reservation and returned observation. A previously
completed request receipt is read only. For the newly invoked request, its
terminal applied receipt (meaning invocation, not acceptance/care), dispatch
reservation and observation event commit in that same transaction; a refused
invocation writes its refusal and terminal receipt together. Service must not
append the receipt in a later transaction after MCP returns. A previously
committed reservation or a non-owning replay is refused/no-op, never invoked.
Direct MCP callers must have the service-issued attempt binding; guessing keys
or omitting command ownership grants no extra dispatch. Record order separately
from callback progress; the tool observation is not a successful callback.

A stop/revoke committed before invocation wins and yields zero provider calls.
A writer arriving while invocation holds the episode lock waits, then records
its stop/revoke after dispatch-start order. This does not undo begun work and
does not mean consent was absent at invocation. SQLite holds its database write
lock for this small local operation; Postgres holds the episode row lock. This
exception is for the local simulator only, not ADP/network provider calls.

Crash windows are explicit: before claim commit, nothing exists and same-token
retry can claim; after extraction claim before final commit, pending is explicit
and supersede can fence late results; between scored state and terminal receipt,
one transaction rolls both back; after commit before HTTP response, replay reads
the one receipt and current journey. After action attempt/claim commit but before
dispatch, a crash leaves pending/unknown and no automatic resumption. During
provider invocation or after its effect but before reservation/result commit,
the effect may have occurred while the database rolled back. The earlier durable
action claim/attempt must therefore remain a conservative no-redispatch fence;
another worker must not interpret a missing reservation as permission. Only the
process holding the one original claimed execution may attempt that invocation.
`newly_claimed` creates a private DispatchPermit passed through the local
coordinator to MCP; the registered in-process capability is consumed once before
invocation and is not a client-supplied dataclass. Existing attempts and same-token
claims return no permit. An independently constructed permit is refused by MCP.
The coordinator ToolRequest gains this internal permit; it is not exposed in
tool JSON or a public response. A future remote coordinator would need a separately
designed durable dispatch capability and must reopen Gate 2 before replacing this
local boundary. No WorkBuddy path is being enabled by this amendment.
Loss of that process's completion leaves unknown, never a claim of failure or
exactly-once external effects. No lease expiry/restart can reclaim action execution.

Callbacks serialize on episode before attempt and retain existing unique receipt,
first-terminal-wins, consent-version, evidence-provenance and stop guards. Late
success/evidence after stop/revoke is a refused audit receipt; failure/duplicate
audit remains available. Evidence ingestion still refuses caller-labelled real
evidence, including ADP text/reference. Plan display, consent/revocation and a
valid operator-recorded human transfer remain available under section 5.2.
Only authorised new disposition can reopen; no public demo branch issues one.
Provider-sharing consent is `clinical_share`, not ADP-processing authority.
Fictional words only; processor/region/retention review remains separate.

| Main flow | Exact top-to-bottom call stack |
|---|---|
| Entry/start | `frontend/app/page` read cookie -> `/example` sets locator without backend write -> explicit start server action -> `api.create_episode` -> `service.start_example` -> `store.create_with_claim_once` -> receipt/no-plan -> explicit allowlisted intake operation -> transaction policy/disposition/receipt -> fresh projection |
| Resume/read/recovery | Page or Try again -> server `api.getEpisode` with same locator -> FastAPI `get_episode` -> `service.project_journey` -> coherent bundle/sticky expiry -> `domain.derive_closure` and `derive_journey` -> presentation -> runtime decoder -> PatientJourney; no model/create/dispatch |
| Begin/review/confirm | Plan renders -> explicit journey-events readback_started -> hidden-answer projection -> local draft review -> read-only token preparation -> confirmation POST -> service -> event/receipt atomically -> score token |
| Score/repair | restatements or latest-parent repairs route -> service claim/context -> release DB -> `ReadbackExtractor.extract` -> adapter assemble/validate -> independent whole-answer doubt -> episode rechecks -> `domain.merge_field_repair`/`compare_plan` -> round/provenance/stop/receipt commit -> fresh projection |
| Reveal/hide | HintCard -> server action -> hint route -> episode claim/cue event/receipt commit -> redacted or explicitly revealed projection -> dialog; Hide/Escape never lower highest cue |
| Barrier/permission/request | supported choice -> barrier route/domain validation -> receipt -> separate unchecked consent -> recorded clinical_share grant -> server fixed-purpose request -> action coordinator -> MCP final episode guard/reservation/local provider -> command receipt -> callback separately -> current journey |
| Callback/transfer/reassessment | authenticated existing operator entry -> service/domain permission -> episode transaction, refusal or fact+revision -> preserved closure/stop derivation; no new patient control or ADP role |

HTTP mapping: 200 completed/replayed receipt; 202 pending; 409 stale/body/parent
conflict with fresh projection when authenticated episode is known; 422 schema/
unpermitted input; 404 unknown; 401 auth refusal; 503 transport/lock/unavailable.
ADP unavailable response includes `scored=false`, completed unavailable receipt
and fresh journey if the store is reachable. Database unavailable cannot fabricate
a receipt: recovery and later same-token inspection. Frontend displays approved
messages only, never exceptions/detail codes/provider reasoning. FastAPI `/`
becomes a 303 to the configured trusted frontend entry, with no fixture body and
no user-controlled redirect target; no new auth bypass.

### 9.9 Additive migration and compatibility contract

No migration is executed/written as implementation now. Planned DDL belongs in
the existing SQLite/Postgres schema modules. Preserve all fourteen existing
tables/rows/triggers; add one `journey_commands` table to both append-only lists.
SQLite uses INTEGER primary key and Postgres SERIAL consistent with existing
schemas; timestamps remain existing UTC TEXT format, booleans INTEGER.

| Column/constraint | Exact planned shape |
|---|---|
| `id` | Engine-generated primary key |
| `operation_id`, `phase` | TEXT NOT NULL; phase CHECK claimed/completed; UNIQUE(operation_id, phase) |
| `episode_id` | TEXT NOT NULL REFERENCES episodes(id) |
| `disposition_version` | INTEGER nullable for create/no-plan; composite version existence checked inside transaction |
| `expected_revision`, `claim_revision` | INTEGER NOT NULL, nonnegative; claim revision captured after lifecycle event append |
| `kind`, `purpose`, `body_sha256` | TEXT NOT NULL; kind closed enum; digest exactly 64 lower-case hex characters validated in both store and service |
| `parent_restatement_id`, `confirmation_id` | nullable TEXT, references/binding checked transactionally; parent FK to restatements where non-null |
| `terminal_state` | nullable TEXT CHECK applied/refused/unavailable/superseded |
| `result_kind`, `result_ref` | nullable TEXT; typed allowlist episode/disposition/confirmation/restatement/hint/barrier/consent/attempt/event; no cached projection/patient prose |
| `interpreter_mode`, `instruction_version`, `schema_version`, `transport_profile`, `request_id`, `trace_id`, `model_version`, `validation`, `failure_category` | nullable TEXT, no secrets/raw vendor payload; only extraction operations populate interpreter provenance |
| `scored`, `recorded_at` | INTEGER NOT NULL CHECK 0/1; UTC TEXT NOT NULL |
| Phase shape | Claimed: terminal_state/result/scored absent or 0. Completed: one non-null terminal_state; scored=1 only applied score/repair with restatement result; refused/unavailable/superseded scored=0 |
| Terminal-claim binding | INSERT-only engine trigger requires one matching claim and equality of immutable operation/episode/version/revision/kind/purpose/digest/parent/confirmation columns; service checks too |
| Indexes | (episode_id, id); partial index episode_id WHERE phase=claimed for pending joins; events(episode_id,id), restatements(episode_id,disposition_version,created_at,id) where absent |

Claim and completion are two immutable rows; no UPDATE to change phase. Unique
completion prevents late overwrites. Completion requires a claim; a trigger
failure is not retried as a second operation. Creation inserts the candidate
episode, claim/lifecycle event and terminal receipt atomically, satisfying FK
ordering and lost-response dedupe. Source sequence comes from events IDs, not
the time-based restatement index: new round-recorded events explicitly reference
round/parent, so latest parent is unambiguous under equal timestamps. Indexes
support lookup; they do not decide ordering.

Extend versioned payloads of existing events/extracted_json, not a second stop
table. `readback_started`, `words_confirmed`, `command_claimed`, `command_completed`,
`interpretation_unavailable`, `dispatch_started` and updated `restatement_recorded`
payloads carry episode/disposition/attempt/parent references and typed provenance.
New extracted_json envelope stores raw offsets, merged values, retained source
references, comparison and cue exposure. Legacy flat extracted_json is explicitly
decoded as legacy/local-sim with offsets/provenance unknown; never invent offsets,
confirmation, instruction version or unaided success. Legacy stop derivation from
H3/exhausted/barrier rows is retained. Legacy unfinished rounds need a fresh explicit
confirmation/attempt compatible with their stop rules before new progression;
no historical correct field is silently eligible for retention.

Current legacy write routes cannot remain a bypass. Journey operations require
the new token; operator callbacks/transfers retain existing authenticated fixture
scope and serialize using the same guard. Legacy caller purpose/hint/confirmation
claims cannot authorise a new patient request/score. Existing clients receiving
no-plan must see nullable fields/empty lines and be upgraded together, not a
synthetic fallback. The old hardcoded create contract is superseded explicitly
for this upgrade; no promise that old mutating clients remain wire-compatible.

Later migration proof uses a pre-upgrade disposable database seeded with no-plan,
active, stopped, expired and accepted/handoff histories. Apply twice, reopen in
a fresh process and compare existing row bytes/deadlines/history; verify old
stops and reader compatibility. All new table UPDATE/DELETE and SQLite REPLACE
on repository connections refuse; Postgres UPDATE/DELETE/TRUNCATE/ON CONFLICT
UPDATE refuse. Seed matching rows first, with positive controls that remove just
the tested guard. Table-set/trigger coverage is exact parity, not superset.

Rollout is additive with ADP off; application and migration validation must precede
enablement. Old app rollback is **not** safe after new journey records: it still
creates the shared episode, shows synthetic no-plan and ignores new permission
contracts. Disable new progression and retain upgraded readers/recovery rather
than deploy that old app. Never drop command/event records to roll back. Engine
DDL execution and hosted retention/erasure require later explicit authority.

### 9.10 Fail-capable verification ledger (planned, no passing results)

Each row names a guard, concrete falsifier, serialized observation and independent
mutation. Tests are planned in the files of section 9.2. A mutation counts only
when its pinned collected test produces an actual assertion failure with passing
pre/post controls and byte-exact restoration. Syntax/import/collection errors,
missing anchors, skipped engines and two overlapping catches are NOT PROVEN.
Run each single-guard mutation alone. Expected good cases must also pass so a
blanket refusal is not accepted as proof.

| Guard/test (file prefix) | Counterexample and observable result | Single-guard mutation |
|---|---|---|
| `test_journey.py::test_no_plan_surfaces` | Create without intake: API/options/MCP and bare-root redirect disclose no fixture plan/owner/deadline/options; lines empty; unknown ID 404 | Restore only no-disposition fallback per surface as separate mutations; drop no-plan options/MCP guard independently |
| `::test_recorded_policy_selected` | Persist policy A then configure B: journey action/words/compare remain A or refuse missing A | Replace disposition-version lookup with configured policy |
| `::test_twelve_screens` | Drive each approved condition, assert step/question/commands/exact text plus independent axes and original deadline | Change each screen predicate/command filter separately, not a global always-fail mock |
| `::test_failed_unknown_handoff_not_transfer` | Escalation outcomes failed/attempted/unknown with ID: patient owner/open/no passed wording | Treat escalation ID alone as successful |
| `::test_ack_is_neutral`, `::test_stop_keeps_true_transfer`, `::test_expiry_wins` | Ack alone neutral; stop+valid transfer no question; overdue acceptance expires; documented fixture retains approved precedence | Remove each predicate/precedence/automation filter separately |
| `::test_projection_invariants` | Unknown version, two questions, mismatched aliases, malformed no-plan, missing display, stop+request: decoder renders recovery, zero POST | Remove each runtime invariant independently with only its malformed fixture |
| `test_boundaries.py::test_serialized_detection_controls` | Inject each forbidden success phrase/facility/clinician/credential/unlabelled receipt into representative API JSON, SSR HTML/RSC and visible/accessibility text; detection must fire | Remove each needle detector independently; require its positive control to fail |
| `test_journey.py::test_no_unaided_answer_payload` | H0/H1 readback response/SSR/dialog/accessibility serialization contains no action/deadline/owner answers; Show first records H2 | Restore one answer-bearing field per mutation, including hidden/preloaded dialog payload |
| `test_journey_commands.py::test_cookie_precedes_start` | Network blocks bootstrap response: browser sends zero create; entry render/remount/HintCard revalidation sends zero POST | Move create into render; bypass cookie-established start check separately |
| `::test_distinct_example_and_same_reload` | Two intentional starts distinct IDs; reload same ID/no model/dispatch; locator 404 recovery | Restore shared ID; replace reload with create separately |
| `::test_lost_create_and_intake` | Drop response after each commit, reload then same-operation explicit replay: one episode/one disposition/no v2 | Bypass create uniqueness or completed-intake lookup separately |
| `::test_body_digest_conflict` | Same operation with changed text/choice/parent: 409 conflict, no second fact/consent/round, current journey | Remove digest equality only; companion detects changed stored claim/completion binding |
| `::test_token_bindings` | Swap episode/version/revision/kind/purpose/parent/confirmation or bad MAC: refused with zero work | Remove each named binding check one at a time |
| `::test_pending_and_terminal_replay` | Two workers same claim: one extraction; pending 202, completed replay fresh stopped projection not old success | Remove claim uniqueness; bypass fresh projection independently |
| `::test_supersede_fences_late_result` | Explicit supersede then release old fake ADP answer: one terminal superseded, no scored row/repair | Remove old-terminal fence only |
| `::test_atomic_apply_receipt` | Kill child between comparison write and terminal receipt, restart/replay: both absent or both committed | Split terminal/state transaction at the cut point |
| `::test_fixed_request_purpose` | Fresh tokens/double tap/forged purpose/direct service and MCP: one attempt, at most original invocation | Trust caller purpose; remove dispatch-claim ownership check independently |
| `test_field_repair.py::test_confirmation_exact_and_latest` | Draft, changed confirmed string, identical text from prior version/round: no ADP or scored row | Remove each confirmation dimension/digest check separately |
| `::test_retains_only_latest_known_matches` | Timing-only latest-parent repair succeeds with grounded action/owner retained; uncertain owner stays uncertain; prior-version parent refuses | Disable retention; fill uncertain from expected; disable version/latest-parent check in separate tests |
| `::test_whole_answer_invalidates_retention` | Timing answer + Actually I won't; explicit different action/owner; alternatives/questions/conditional: no understood result; unrelated aside positive control | Remove each independent doubt/correction branch; disable replacement of newly expressed field separately |
| `::test_uncertain_not_definite_mismatch` | Unknown phrase/null versus known wrong day: uncertain correction vs deadline mismatch; unsupported action never timing accusation | Convert unknown to mismatch; choose timing copy for non-timing mismatch separately |
| `::test_two_repairs_h3_and_round_zero` | Valid uncertain rounds 1/2 then stop; H3 no pass; fresh initial POST after failure cannot reset ladder | Remove cap, H3 check, current-stop gate and unfinished-parent gate separately |
| `::test_reveal_hide_reload_cued` | Reveal/hide/reload then posted H0 remains cued; timing repair answer cue persists; hide consumes zero rounds | Trust client hint; clear exposure on hide/reload; omit repair cue event separately |
| `test_adp_extraction.py::test_positive_and_negative_controls` | Grounded positive, known wrong time, missing value and negated whole answer: match/mismatch/uncertain; always-refuse adapter fails positive | Drop extraction use/canonical comparison or independent doubt separately |
| `::test_strict_object[case]` | Extra/missing key, canonical ID, wrong version/type, duplicate key, two objects, prose/fences, repeated/unknown uncertainty, inconsistent refusal/null: unavailable/scored false/no round | Remove only the validator named by each parameter, with otherwise valid object |
| `::test_grounding[case]` | Invented span, wrong offsets, UTF-16 emoji offset, bool int, negative/end-overrun/empty: invalid, no retained/expected answer filling | Disable each bounds/type/source-slice check independently |
| `::test_sse_envelope[case]` | HTTP200 error, reasoning-first, mixed channels/messages, duplicate chunk, truncated/terminal missing, final+delta duplicate: unavailable; one pinned good profile passes | Remove each profile/error/terminal/channel/order/duplication check alone |
| `::test_full_stream_timeout` | First byte within budget then terminal after 5 seconds: timeout, no score/repair, preserved deadline | Replace whole-response deadline with per-chunk/first-byte budget |
| `::test_limits[case]` | 2,049 code points, 16KiB+1 answer, oversized frame/wire: unavailable/refused without score; exact-limit control passes | Raise/remove only each named limit |
| `::test_no_retry_fallback_or_reasoning` | Timeout/refusal/invalid: exactly one ADP call, zero lexical fallback; planted reasoning/secret never in patient or logs | Enable retry; call local extractor after failure; pass reasoning/credential to surface independently |
| `test_journey_postgres.py::test_snapshot_race`, SQLite companion | Pause between snapshot SELECTs, concurrent stop/consent: all fields from one revision, no mixed active/stop commands | Remove read transaction isolation or read across transaction-bound bundle in separate engines |
| `::test_stop_before_dispatch`, `::test_consent_before_dispatch` | Commit stop/revoke before invocation barrier: zero provider calls, refused receipt, current owner/deadline unchanged | Remove final episode serialization/recheck individually per engine |
| `::test_dispatch_before_stop` | Pause bounded local provider while stop waits: one invocation ordered before stop, late success refused; no promise to undo it | Release episode lock before invocation; remove late success stop/consent check separately |
| `::test_late_extraction_rechecks[dimension]` | While fake ADP waits, change stop/version/parent/cue/revision or pass deadline: final unscored/no round/unchanged deadline | Remove each final recheck independently, release exactly that concurrent change |
| `::test_action_crash_never_redispatches` | Kill after claim, before invocation and after simulated effect before commit: restart/new token/direct MCP never re-invokes; pending unknown stays neutral | Reclaim pending action or infer authorization from missing dispatch reservation |
| `::test_schema_migration_and_append_only[case]` | Old histories preserved after twice-applied additive DDL; seeded new receipt refuses update/delete/replace/truncate/upsert | Omit table/trigger or phase/claim binding guard independently |
| `::test_fresh_process_reads` | Fresh authenticated backend reads patient/options/ledger same episode, stop and absolute deadline; unknown still 404 | Reintroduce process-local registry or omit persisted stop read |
| Existing truthfulness service/API/MCP regressions | Evidence forgery, unrelated acceptance, late success, old keys/H3/exhaustion remain refused; simulation labels intact | Each existing repair guard retains its targeted mutation; don't substitute a new shared wrapper catch |

Scanner absence checks must first show detection on that **same serialized
surface**, including JSON escaped/raw/forward-slash path forms. Success needles
include each exact approved arranged/agreed/passed/no-action-needed phrase,
not just one generic word. Test only fixture values, never actual secret bytes.
Domain import scanner includes the new pure functions and independently detects
real-file network/SDK/store/clock injection. Frontend secret scanner covers all
new server/client files and RSC payloads, not a stale hand-picked inventory.

Proof tiers are separate:

1. **Offline deterministic:** fake ADP transports, pure domain and serialized
   authenticated API, SQLite race/crash tests; no claim about live extraction or
   deployed database. Run meaningful focused tests/mutations, then relevant full
   suite after implementation; preserve existing truthfulness controls.
2. **Live ADP, later authorised:** compatible instruction publish **and activate**,
   knowledge-base/tool checks and new stateless sessions; positive paraphrase,
   definite wrong time, missing fields, refusal/advice/injection, negation and
   backward correction probes. Capture redacted profile/version/request/latency
   and failures; two old refusal observations cannot prove the positive path.
3. **Actual disposable Postgres, later authorised:** two independent connections
   or processes with deterministic barriers, process termination/restart, matching
   rows for trigger controls and migrated legacy histories. Local SQLite or
   Postgres code/signature parity is not engine proof. Missing authorised DSN means
   skip/unproven, never use APP_DATABASE_URL or a production run by convenience.
4. **Browser/accessibility:** inspect actual production journey locally, not just
   prototypes. Desktop and 320 CSS pixels; enlarged text setting, 200% text/zoom
   and 400% browser zoom reflow with recorded viewport; no lost action/deadline
   or horizontal scroll for ordinary content. Keyboard-only start/review/confirm/
   repair/barrier/checkbox/recovery; visible focus, skip link, labelled fields,
   grouped radio options, error focus, no timer/auto-advance. Dialog focus moves
   inside, Escape/back restores opener or meaningful successor if step changed,
   background inert; failure does not strand focus. Screen reader reads one
   question, associated validation error and polite pending/result status once;
   no provider reasoning, hidden-answer text or raw detail codes. Check at least
   one named screen reader/browser pair and report exactly what was observed;
   automated DOM/reflow scans do not certify accessibility.

Engineering checks do not prove participant benefit, older-adult suitability,
clinical safety, general language comprehension, genuine provider acceptance or
WorkBuddy execution. Correct demo/claims/usage assets only after actual evidence;
the cut study remains cut.

### 9.11 Least-confident decisions, effort and approval boundary

1. **[unknown] Final-answer channel:** observed ADP transport lacks production
   discriminator proof. Enablement blocks on a pinned captured profile; if unavailable,
   reopen Gate 2 rather than accept arbitrary Text frames or reasoning.
2. **[hypothesis] Conservative language checks:** grounding does not establish
   intent/negation scope. Stress positive and contradictory corpus together;
   missing coverage stays uncertain, never a falsely definite mismatch/pass.
3. **[verified gap / unknown approval] Copy:** explicit confirmation control,
   non-timing field repair and out-of-scenario date strings need Gate 1 decisions
   before exposure. Current copy is preserved. Do not call review/save/check the
   same action or silently promise a complete scoring UI before that approval.
4. **[hypothesis] Action fence versus availability:** conservative unknown
   dispatch sacrifices retry after a crash. This follows the approved no-redispatch
   boundary; a retry/lease/provider-idempotency scheme is another Gate 2 decision,
   not an implementation convenience. Holding SQLite's writer lock during the
   bounded local provider is acceptable only for this scripted demonstration.
5. **[hypothesis] Signed capabilities and read preparation:** purpose-separated
   use of the existing server token avoids another credential but couples rotation
   to locator recovery. Shared-token operators/users still have no verified identity
   isolation. Two tabs can conflict; fresh projection and refusal are intentional.
6. **[unknown] Frozen policy payload/legacy provenance:** current registry content
   is only a provisional label, not a complete reconstructible policy bundle.
   Resolve the recorded fixture version through an immutable allowlisted bundle
   and refuse unknown versions; don't fabricate history or migrate by relabelling.
7. **[unknown] Benefit and schedule:** no participant result and no measured
   upgrade velocity. More steps may add burden; approval cannot establish that
   ADP or read-back beats the card.

**[hypothesis, incremental effort, person-hours]** Estimate is for this amendment's
future implementation/proof, reusing shipped code; it is neither historical
whole-project effort nor the old 6 to 10 hour conditional Slice 13 estimate.

| Work package, not a slice sequence | Hours |
|---|---:|
| Coherent projection, copy selection, policy/revision and screen matrix | 8 to 14 |
| Locator, confirmation/replay capabilities, command table and both engines | 14 to 22 |
| Field-only repair, whole-answer and cue provenance | 8 to 14 |
| ADP transport/envelope/strict boundary and offline corpus | 10 to 18 |
| Thin twelve-screen production renderer and keyboard/dialog behaviour | 12 to 20 |
| Independent guard mutations, serialized API/scanners, Postgres races/restarts | 14 to 24 |
| Browser/assistive-technology checks, remediation and evidence records | 8 to 14 |
| **Incremental build/proof subtotal** | **74 to 126** |
| Integration/debugging allowance, unmeasured | 10 to 18 |
| **Planning range** | **84 to 144** |

No measured throughput supports this range. It excludes Gate 4 drafting,
operator publishing/access delays, processor/retention review, clinical review,
participant research, deployment and submission-asset revisions. At an assumed
6 productive hours/day it is 14 to 24 working days; availability is unconfirmed.
It is not credible to promise this full scope before a 16 October target from
13 October. Current cutoff is not independently checked. Gate 4 must decide a
small visible plan/claim scope without silently dropping guards or representing
old study/ADP evidence as new proof.

**Gate falsifier protocol:** no new contradiction invalidating Gate 1/2 was
established by this source inspection; the observed app gaps are the ones Gate 2
already designs to change. Copy omissions and unproved envelope/ordering are
explicit exposure/enablement dependencies. If later programming evidence cannot
implement the approved stop/replay/disclosure/ADP boundary, record the concrete
counterexample, reopen the owning gate in `00-status.md` and stop for its approval.
Do not repair architecture silently within a Gate 3 implementation.

After approval the next authorised design step is a separate Gate 4 amendment.
Then separately authorised small journey/ADP slices, API/accessibility/disposable
Postgres proof, corrected assets/claims, and explicit deployment/submission
authority. This is a safe handoff boundary: contracts, counterexamples and
dependencies are on disk; no important permission exists only in chat.

**Approval recorded:** the user explicitly answered "Yep i approve." on
13 October 2026. Gate 3 is RE-APPROVED. The same message separately authorises
committing the working tree, publishing the branch, merging and pushing to main,
and an actionable prompt for the next agent to prepare Gate 4. This is no
Gate 4 approval or authority to implement the upgrade.

## 9.12 Identity correction: Gate 3 re-approved, 13 October 2026

**Status: RE-APPROVED.** The user answered "approve" on 13 October 2026. The earlier section 9 approval remains
history. This narrow correction is proposed after Slice 14 preflight, under
Gate 4 section 9.8's signature-falsifier rule. No implementation was written.

[verified] `JourneyProjection.episode_id` is required by section 9.3, including
for true no-plan. That section explicitly permits revision 0 when no events
exist. The section 9.8 bundle had no identity field, and the current
`EpisodeSnapshot` has none. For two valid no-plan rows without events, all
approved bundle fields can be equal while the required response IDs differ.
A disposable SQLite probe seeded `fictional-empty-a` and `fictional-empty-b`,
closed/reopened the store, compared those fields and verified integrity and
foreign keys. This counterexample does not claim the unbuilt projector ran.

**Approved signature delta:** the section 9.8 `JourneyBundle` now shows required
`episode_id: str` before `snapshot`. Both `load_bundle(episode_id)` and
`load_journey_bundle(episode_id)` must populate it from the verified stored
`episodes.id` row in the same coherent transaction as the remaining fields.
An absent row still raises `EpisodeNotFound` and maps to 404; merely echoing
an unverified request ID is not sufficient. `derive_journey` copies this identity
for no-plan and assessed projections; no event/disposition/process lookup or
shared demo ID may substitute for it. Its signature stays pure and unchanged.

**Required future regression, within existing G01/G31/G37 scope:** seed two
no-plan episodes with no events in disposable SQLite, reopen, read both through
authenticated GET and assert their distinct exact IDs with revision 0, null
plan/outcome/aliases and empty commands/lines/options. Unknown ID stays 404.
Include ordinary eventful no-plan controls. Independently remove bundle identity
propagation or substitute the shared ID and require real assertion failure;
retain the existing per-surface no-plan and fresh-process obligations. Store
reader parity remains source-only until the authorised Slice 19 engine proof.

This adds no wire field (identity is already required), public endpoint, table,
command, policy, copy or clinical behavior. Gates 1/2 and the approved Gate 4 plan
are unchanged. Slice 14 implementation may resume after this explicit re-approval. Its later visible Check/cleanup/continuation and authorised main
handoff remain prerequisites for Slice 15.

**Re-approval recorded:** "approve", 13 October 2026.
