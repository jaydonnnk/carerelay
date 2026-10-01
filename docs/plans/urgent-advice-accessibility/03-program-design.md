# Program design: CareRelay urgent-advice accessibility

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
