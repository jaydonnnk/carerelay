# Slice plan: CareRelay urgent-advice accessibility

**Gate 4 — APPROVED 28 September 2026.** The user approved this plan on 28 September 2026 with the single instruction "continue", following the Gate 4 approval question in `00-status.md`. Authority for gate and slice state is `00-status.md`; this document is the plan, not the state record.

**Approval authorises:** implementation code, slice by slice, in the order below. **It does not authorise:** installs beyond the declared test dependencies, credentials, recruitment, external calls, deployments, or a push. Each slice still stops for the user's "continue, or re-steer?" before the next one starts.

Read first: `00-status.md`, `03-program-design.md` (APPROVED 26 Sep), `02-architecture.md` (APPROVED 25 Sep, revision 2), `PLAN.md` §7 and §9, `clinical-review-blocker.md`.

---

## 0. What this plan is and is not

| | |
|---|---|
| **Scope** | **Full Gate 3 scope.** The user directed on 28 September 2026 that scope is **not** cut to fit the schedule. Every capability in `03-program-design.md` §2 is sequenced. |
| **Capacity** | Solo. No second contributor is recorded. |
| **Honest consequence, stated up front** | Gate 3 §7 estimates **90–150 h** build plus **20–35 h** baseline (110–185 h combined). From 28 September to the 16 October submission is **18 calendar days**. **The full scope does not fit a solo schedule in 18 days.** A solo contributor working 8 h/day has 144 h total — before Gate A, recruitment, the Option C source check, submission assets, or any external delay. This is not a reason to cut scope (the user's instruction), and it is not something this plan will hide. It is the plan's **primary risk**, recorded as R1 in §6 and as the plan-level stop condition in §7. |
| **What the plan does instead of cutting** | It sequences the full scope so that the **highest-risk, highest-value work lands first** and so that a partial build is still a coherent submission. If the schedule fails, it fails with a working demonstration and an honest record, not with six half-built layers. |
| **Not authorised by this draft** | Superseded at approval. Approval authorises implementation code slice by slice. Installs beyond the declared test dependencies, credentials, recruitment, external calls, deployments and pushes remain unauthorised. |

### Approval record — 28 September 2026

The user approved Gate 4 on 28 September 2026 with the instruction **"continue"**, in response to the Gate 4 approval question. Two sub-questions were left open at drafting and are resolved as follows, both under the recommendation given:

| # | Question | Resolution |
|---|---|---|
| 1 | **ADR-0007 — which layer owns canonicalisation?** | **Reading A accepted.** Canonicalisation lives in `domain`; the coordinator returns raw spans. ADR-0007 moves from `proposed` to `accepted`. The Gate 3 `compare_plan` signature is amended accordingly, as recorded in §1.1. |
| 2 | **The Option C source.** | **Scheduling only, not approval.** The source remains unselected and licensing stays unchecked. It blocks Slice 5 and nothing earlier. The check runs inside Slice 0's window; if no source is cleared by 2 October, Option B is the fallback and clinical wording is **not** authored to unblock the schedule. |

**If either resolution is wrong, say so and the document is corrected before the affected slice.** ADR-0007 affects Slices 2 and 4; the Option C source affects Slice 5.

---

## 1. Sequencing constraints this plan must honour

These are carried forward from approved gates. None is negotiable here; changing one reopens the gate that set it.

| # | Constraint | Source |
|---|---|---|
| C1 | **The baseline comparison is sequenced before the Closure Contract build.** | `02-architecture.md` §12; round-2 review; `PLAN.md` §7 currently has the wrong order |
| C2 | **The two §6.1 kill conditions run first**, before any participant work, with no reviewer and no Gate A. | `03-program-design.md` §6.1 |
| C3 | **Slice 1 is the tracer bullet** — hardcoded endpoint plus stubbed UI, wired end to end, runs, and the user can see it. | software-factory Gate 4 rules |
| C4 | **No horizontal building.** No "all the database, then all services, then all the API". | software-factory Gate 4 rules |
| C5 | **The Option C source check precedes use of the fixture wording.** Source selection, licensing and Singapore applicability are unchecked. | `03-program-design.md` §6.2 |
| C6 | **A third repair round is never offered.** `H3` is `not_recalled`, never a comprehension pass. | `PLAN.md` §5.1 |
| C7 | **`domain` imports no SDK, network, database, filesystem or wall clock**, enforced by a fail-capable check. | `02-architecture.md` D2; `03-program-design.md` §5 |
| C8 | **No timer, countdown or auto-advance anywhere.** H2 stays until the patient hides it. | `PLAN.md` §5.2.1 (Gate 1 reopening) |
| C9 | **Every slice ends in a working, testable state** and asks "continue, or re-steer?" | software-factory Gate 4 rules |
| C10 | **Gate 4 must not remove Closure Contract tests to make the schedule look green.** | `03-program-design.md` §7 |

### 1.1 Two readings of the `compare_plan` contract — Gate 4 must resolve this

The spike at `spike/kill_spike/planback.py` exposed an ambiguity the Gate 3 contract leaves open, and it changes what K1 can prove:

| Reading | What the coordinator returns | What K1 can conclude |
|---|---|---|
| **A** — canonicalisation in `domain` | Raw spans (`"today before six"`) | The paraphrase/alias/relative-time/code-switched corpus is testable as **ordinary deterministic code**. K1 is closable offline. |
| **B** — canonicalisation in the model | An already-canonical `action_id` | The corpus only reaches the model. **K1 cannot be closed without a live coordinator.** |

**This plan adopts Reading A** and pins it in **Slice 4** by widening the Gate 3 signature with the resolution tables (`action_aliases`, `deadline_forms`, `owner_aliases`) as explicit policy data. **[hypothesis]** under Reading A the comparator is deterministic and the spike's 15/15 result transfers; under Reading B it does not, and the K1 claim weakens to "the deterministic layer is correct given correct extraction". This is a **Gate 3 contract amendment**, recorded as such, not a silent reinterpretation. It needs the user's acknowledgment at Gate 4 approval.

**`ExtractedPlan.uncertain_fields` must survive the change.** `03-program-design.md` §3 defines `uncertain_fields: frozenset[str]`; the spike's `ExtractedPlan` carries nullable spans instead. The implementation must carry **both** — the raw span *and* the extractor's own uncertainty — because a span the extractor is unsure about is not the same as a span it did not produce. Collapsing them re-creates the "unknown becomes an accusation" defect K1 exists to catch.

---

## 2. The slice plan

Thirteen slices. Each is one shippable, testable state. Dates assume a solo contributor starting 29 September 2026; they are **[hypothesis] planning targets**, not commitments, and the estimate range in `03-program-design.md` §7 is unverified.

### Slice 0 — Baseline proof (no application code)

**Dates:** 29–30 Sep. **Effort:** 4–6 h. **Build order:** first.

| | |
|---|---|
| **Goal** | Close C2 and C5 before a single line of product code exists. The project's cheapest risk reduction, and the largest: if K1 or K2 fails, PlanBack is cut. |
| **Deliverable** | (a) K1 and K2 run reproducibly, output recorded. (b) The Option C source selected, with licence and Singapore applicability checked and written down. |
| **Files** | `spike/` (exists), `study/protocol.md` (first draft of the source provenance section only), `docs/plans/urgent-advice-accessibility/04-slices.md` run log entry |
| **Status on 28 Sep** | **K1 and K2 PASS.** Both ran clean: 15 tests, 0 failures, including the four `AssertionsHaveTeeth` defect-injection tests. Evidence: `spike/tests/test_kill_conditions.py` executed under Python 3.13.14. **This is a spike result, not an implementation result** — it exercises the deterministic layer only and assumes Reading A. |
| **Still open** | The Option C source is **not selected**. Licensing and Singapore applicability are **unchecked**. This blocks the judged fixture — Slice 5 — and nothing earlier. |
| **Stop condition** | **If K1 or K2 fails, stop. PlanBack is cut and this plan is replanned before Slice 1.** If no Option C source can be cleared by 2 October, escalate: Option B (secure one reviewer) is the recorded fallback, not a silent authoring of clinical wording. |
| **Not in this slice** | Any application code. Any participant contact. |

### Slice 0 run log

| Date | Event |
|---|---|
| 2026-09-28 | `spike/tests/test_kill_conditions.py` executed under Python 3.13.14. **15 tests, 0 failures.** Includes the four `AssertionsHaveTeeth` defect-injection tests: the surface-only comparator, the always-uncertain comparator, unknown-treated-as-mismatch, and the two ordering defects (read-back first; guidance never rendered). Each was confirmed to make its assertion fail. |
| 2026-09-28 | Isolated venv created at `~/.workbuddy-ai/binaries/python/envs/default`. **Slice 1's environment check passes:** `fastapi`, `uvicorn`, `pydantic`, `pytest` and `httpx` all install and import into that venv. The intermittent AppControl block on stdlib venv creation recorded in `AGENTS.md` **did not fire**. Nothing was installed into any user-managed environment. |
| — | **Open: Option C source selection.** Licensing and Singapore applicability unchecked. Blocks Slice 5 only. |

**What this run does not prove.** K1 was executed against the deterministic layer with hand-supplied correct spans. The model's own extraction is not reachable offline, and the result depends on Reading A (§1.1). This is a spike result; it is **not** evidence of WorkBuddy access, clinical safety, human learning or patient benefit.

### Slice 1 — Tracer bullet: episode to four lines, hardcoded

**Dates:** 30 Sep – 1 Oct. **Effort:** 5–8 h. **Build order:** second.

| | |
|---|---|
| **Goal** | A running FastAPI app on `127.0.0.1` that serves a hardcoded episode end to end. It does almost nothing. It runs, and the user can see it. |
| **Deliverable** | `POST /api/episodes` returns an id; `GET /api/episodes/{id}` returns the four patient lines from a hardcoded fixture; a plain HTML page renders them. No database, no domain logic, no coordinator. |
| **Files** | `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/templates/patient.html`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json` (hardcoded values only) |
| **Environment check (C-level, must run first)** | **PASSED 28 Sep 2026.** Python 3.13 present; venv created at `~/.workbuddy-ai/binaries/python/envs/default`; FastAPI, uvicorn, pydantic, pytest and httpx installed and verified importable there. The isolated venv was used deliberately so nothing lands in a user-managed environment. `AGENTS.md` records an intermittent AppControl block on stdlib venv creation — **it did not fire.** |
| **Tests** | `tests/test_api.py` — the two routes respond, the four lines are non-empty, and the page renders. Each test must fail against a deliberately removed route before it counts. |
| **Stop condition** | If FastAPI cannot be installed in the isolated venv, or the AppControl block cannot be cleared, stop and escalate. Do **not** silently reorganise the project around the failure — that is exactly where horizontal building starts. |
| **Check** | ✅ curl the endpoint, show the user the JSON and the rendered page. Then ask: continue, or re-steer? |

### Slice 2 — The pure domain core and its enforcing boundary

**Dates:** 1–3 Oct. **Effort:** 8–13 h. **Build order:** third.

| | |
|---|---|
| **Goal** | The decision layer exists and is provably pure. This is C7 — the strongest decision in the approved architecture, and it is a convention with a diagram until a check enforces it. |
| **Deliverable** | `domain/models.py` (frozen types, enums) and `domain/rules.py` (`validate_route`, `validate_change`, `compare_plan`, `next_repair`, `project_attempt`, `derive_closure`, `patient_lines`, `reassessment_decision`) — **no I/O, no SDK, no clock**. |
| **Files** | `src/carerelay/domain/models.py`, `src/carerelay/domain/rules.py`, `tests/test_domain.py`, `tests/test_boundaries.py` |
| **Tests that must be fail-capable** | `test_domain_import_boundary` (adding an SDK/network/db/clock import under `domain/` fails a static check); `test_planback_known_match_mismatch_uncertain` (the K1 corpus, migrated from the spike); `test_closed_vocab_and_missing_is_not_negative`; `test_disposition_deadline_is_append_only`; `test_hint_disclosure_accessibility` (C8: no timer, `dwell_seconds` absent from the patient serialization). |
| **Carries forward** | Slice 0's K1 result, promoted from spike to domain test. The comparator is **not** rewritten from scratch — the spike logic moves in, widened per §1.1. |
| **Stop condition** | If the import boundary cannot be enforced as a failing check, **stop** — D2 is the load-bearing decision, and an unenforced boundary means the architecture is not what the docs claim. |
| **Check** | Run the boundary check once with a deliberate `import socket` added to `rules.py`; show it failing; remove it; show it passing. A green check that was never seen red is not evidence. |

### Slice 3 — State, append-only, with the Closure Contract invariants

**Dates:** 3–6 Oct. **Effort:** 12–20 h. **Build order:** fourth.

| | |
|---|---|
| **Goal** | The clinical record persists, and **I1 (immutable deadline) holds because no retry code path writes a disposition** — stated honestly, as §10 of the architecture requires. |
| **Deliverable** | SQLite (WAL, busy timeout) behind repositories. Tables: `episodes`, `dispositions`, `attempts` (immutable identity, no status column), `attempt_transitions` (append-only, monotonic `seq`), `callbacks` (nullable first-receipt key + `duplicate_of` + `accepted`), `evidence` (D11 `CHECK`), `consents`, `human_acceptances`, `escalations`, `expiry_events`, `restatements`, `events`, `policy_versions`. |
| **Files** | `src/carerelay/state.py`, `tests/test_state.py` |
| **Tests that must be fail-capable** | `test_attempt_open_atomic_and_double_tap`; `test_callback_duplicate_and_reorder` (first-terminal-wins, duplicate recorded and non-winning); `test_consent_revoke_in_flight`; `test_evidence_provenance_constraint` (a simulated or unsourced row cannot be `documented`); `test_expiry_sticky_after_clock_regression`. |
| **Hardest single item** | The callback representation. `callbacks.callback_key` is UNIQUE for the first receipt; duplicates are also written with a **null** unique key (SQLite permits multiple nulls), `duplicate_of` pointing at the first, `accepted = false`. `BEGIN IMMEDIATE` serialises lookup and insert; the transition append is in the same transaction. **[hypothesis]** — prove it under two concurrent writers and a crash, or backtrack Gate 2 rather than losing receipts. |
| **Stop condition** | If the callback representation cannot be made atomic, **stop and backtrack Gate 2** (§8 item 4 of the programme design). Do not ship a representation that silently loses duplicates. |
| **Check** | Show the user a duplicate callback being recorded and the projection not changing. |

### Slice 4 — PlanBack end to end, with the hint ladder and bounded repair

**Dates:** 6–8 Oct. **Effort:** 8–14 h. **Build order:** fifth.

| | |
|---|---|
| **Goal** | The product's headline mechanism, running against real state. |
| **Deliverable** | `POST /restatements`, `POST /restatements/{rid}/repairs`, `POST /hint-events`, `POST /transcript-confirmations`. Coordinator extracts raw spans; **`domain` resolves and compares** (Reading A, pinned here). H0–H3 recorded; H2 stays until the patient hides it; `dwell_seconds` to the ledger only; H3 is `not_recalled`, never a pass; two repairs maximum, third routes to the human path (C6). |
| **Files** | `src/carerelay/service.py` (`submit_restatement`, `record_hint_event`, `confirm_transcript`), `src/carerelay/coordinator.py` (extraction interface — **labelled local simulation at this point**), `src/carerelay/static/app.js`, `tests/test_service.py` |
| **ADRs produced** | ADR-0007 (canonicalisation lives in `domain`, not the model) — see `docs/adr/`. |
| **Stop condition** | If H0–H2 leak a critical field, stop. A hint containing the answer turns a comprehension check into a reading test, and the whole evaluation becomes worthless (`PLAN.md` §5.2). |
| **Check** | Walk the user through a mismatch, one field repaired, then a clean pass — and a third failure routing to the human path. |

### Slice 5 — The judged fixture and the abstention path

**Dates:** 8–9 Oct. **Effort:** 5–8 h. **Build order:** sixth.

| | |
|---|---|
| **Goal** | The fixture is honest and traceable, and the urgent path is provably first. |
| **Deliverable** | `fixtures/scripted_episode.json` carrying the **Slice 0 Option C wording, verbatim, with provenance recorded**; `POST /barriers`; the closed-vocabulary classification → abstention policy → emergency stop; `POST /reassessments` (the only path that may insert disposition v2); `POST /escalations`. `submission/usage-proof.md` skeleton. |
| **Files** | `fixtures/scripted_episode.json`, `src/carerelay/service.py` (`record_barrier`, `escalate`, `reassess`), `src/carerelay/presentation.py`, `tests/test_domain.py` (abstention), `tests/test_api.py` |
| **Tests** | `test_urgent_path_precedes_planback` promoted from the spike (K2, with no coordinator and no reviewer); `test_closed_vocab_and_missing_is_not_negative` — a hallucinated route id, a missing fact and a contradiction all stop at the human path **before** a tool or a disposition. |
| **Gate on this slice** | **Slice 0's source check must be complete.** If the Option C source is not cleared, this slice cannot carry the judged fixture. Do not author clinical wording to unblock it. |
| **Stop condition** | No cleared source by 2 October → escalate per Slice 0. |
| **Check** | The user reads the fixture wording and the provenance record. |

### Slice 6 — The action path, the simulated provider, and the platform call

**Dates:** 9–11 Oct. **Effort:** 10–16 h. **Build order:** seventh.

| | |
|---|---|
| **Goal** | A real tool call happens through the platform, or an honestly labelled local simulation does. |
| **Deliverable** | `POST /actions` (authz + consent + **server-generated idempotency key**, D5); `POST /callbacks/{route_id}`; `src/carerelay/tools.py` with the **three** MCP tools (`get_episode`, `submit_simulated_request`, `record_evidence`), each rechecking authorisation, consent and attempt key server-side; `src/carerelay/simulated_provider.py` (`simulated: true` on every response). |
| **The pinned path** | `02-architecture.md` §3.3, normative: coordinator executes the tool, **the failure event originates in the platform**, and `origin` is recorded and displayed. A local-sim failure is labelled in the same field. |
| **Files** | `src/carerelay/tools.py`, `src/carerelay/simulated_provider.py`, `src/carerelay/service.py` (`open_action`, `receive_callback`), `tests/test_coordinator.py`, `tests/test_api.py` |
| **Gate A decision point — read carefully** | The spike is **overdue and has not run.** Re-verification on 28 September 2026 found: no `WORKBUDDY_API_KEY` or `WORKBUDDY_AGENT_ID` in the environment, no `.env`, and no `workbuddy` or `codebuddy` Python package installed. **On that evidence the platform path is [unknown]-to-unavailable.** This slice therefore builds the coordinator boundary with `CoordinatorPort` having **two labelled implementations**, and the real one is wired only if credentials appear. |
| **If Gate A has not passed by 11 October** | Use the **recorded fallback**: `origin = local-sim`, honest label, §3.3's platform-advantage claim **weakened and stated as weakened**, and the mandatory usage proof carried by genuine CodeBuddy development history. This is the pre-recorded reversal from Gate 2 — it is not a failure of this plan, and it is not to be disguised. |
| **Stop condition** | If neither the platform path nor a labelled local simulation can produce a recorded failure origin, **stop** — the demo's honesty depends on that field. |
| **Check** | Show the user the ledger rendering the origin marker, once for a platform failure and once for a local simulation. They must be distinguishable by inspection. |

### Slice 7 — The baseline instrument: the external card (C1)

**Dates:** It runs **in parallel with Slices 3–6**, and must be **complete before Slice 8**. **Effort:** 5–9 h. **Build order:** eighth, and explicitly **before the Closure Contract build**.

| | |
|---|---|
| **Goal** | Discharge constraint **C1**: the kill test runs before the thing it might kill is finished. This is the whole point of the ordering. |
| **Deliverable** | `study/fixed-card.html` — a **standalone, printable/PDF, non-clinical** content-neutral instruction task of the same shape as the app condition, carrying **no symptom, urgency or disposition content** (the Gate 2 D6 backtrack). Same wording, same legitimate options, a direct link, the approved human route. Delivered **outside the application** — it is not an in-app arm. |
| **Files** | `study/fixed-card.html`, `study/protocol.md` (pre-registration: allocation, consent, scripted post-failure question, answer key, raw outcome sheet, cut rule — **all frozen before the first dyad**), `tests/test_study.py` |
| **Tests** | `test_study_fairness_and_scoring` — card is standalone; wording and options match the fixture; allocation is between-subjects; the scripted question and scoring are fixed before sessions; **raw counts, not percentages, below ten participants**. |
| **Recruitment** | Target 6 per condition; **minimum 3 per condition** or no HCD claim. Debt instrument for R3. |
| **Stop condition** | If the card cannot be made content-neutral while staying a fair comparison, stop and re-read the Gate 2 D6 backtrack. A clinical comparator re-imports the reviewer dependency the whole Option A decision removed. |
| **Check** | The user reads the card and the frozen protocol before any participant sees either. |

### Slice 8 — Gate B: run the comparison

**Dates:** 11–13 Oct. **Effort:** 15–25 h (sessions + analysis). **Build order:** ninth — **before** Slice 9.

| | |
|---|---|
| **Goal** | Run the primary kill test on real dyads. |
| **Deliverable** | Sessions run; raw outcomes recorded; the pre-registered cut rule applied; results written down **including adverse reactions to read-back**. |
| **Primary outcome** | **False completion** — each participant's uncoached yes/no answer to whether care has been arranged after the failed or unconfirmed attempt. |
| **What it measures, stated honestly** | The **mechanism** — does read-back plus truthful status change comprehension, burden and false-completion belief. It does **not** validate clinical advice, and the submission must say so. |
| **Cut rule (pre-registered, from `02-architecture.md` §9)** | PlanBack is cut if the card achieves equal action/deadline recall with **lower burden**; **or** any critical correct statement is flagged as a mismatch; **or** emergency guidance is delayed by read-back. The latter two already passed offline in Slice 0 — this run tests the first. |
| **Blinding** | The scorer sees the answer key and the response, not the project hypothesis. No percentages below n=10. |
| **Stop condition** | **If the card wins on the pre-registered rule, stop. PlanBack is cut and Slices 9–12 are replanned.** That is the plan working as designed, not failing. A simpler card may genuinely win; §6 of the programme design predicts this is the primary kill test for a reason. |
| **Check** | Show the user the raw outcome sheet, not a summary statistic. |

### Slice 9 — The Closure Contract in full (C1 satisfied: it starts after the kill test)

**Dates:** 13–15 Oct. **Effort:** 8–14 h. **Build order:** tenth.

| | |
|---|---|
| **Goal** | The second mechanism, built **only because the baseline did not falsify the first**. |
| **Deliverable** | `derive_closure` complete: two independent axes, `closed_with_evidence` / `escalated_to_human` / `expired_unresolved` / `open`; `POST /acceptances`; the expiry read-path (`record_expiry_once` before projecting, no scheduler); the four-line unresolved and expired renderings from `02-architecture.md` §7, with the five copy rules. |
| **Files** | `src/carerelay/domain/rules.py` (`derive_closure`, `patient_lines`), `src/carerelay/presentation.py`, `src/carerelay/templates/patient.html`, `tests/test_domain.py`, `tests/test_api.py` |
| **Tests that must be fail-capable** | `test_acceptance_is_not_care` (a named acceptance closes the handoff obligation and never sets `care_evidenced`); `test_serialized_patient_and_ledger_labels` (unresolved/expired copy contains the original deadline and the named fallback; the simulated label is **inside** the serialized patient lines); `test_expiry_sticky_after_clock_regression`. |
| **Copy rules (C, do not drift)** | No reproach, no alarm, no false comfort, a named route, the deadline stays visible. The first draft was rejected as too blunt — later edits must not drift back. |
| **Stop condition** | Any invariant violation blocks further feature work (`PLAN.md` §9). |
| **Check** | Show the user the expired screen and the unresolved screen side by side against the approved wording table. |

### Slice 10 — Fault harness and the seven sequences

**Dates:** 15–16 Oct. **Effort:** 8–14 h. **Build order:** eleventh.

| | |
|---|---|
| **Goal** | Prove the contract holds **under fault**, at the boundary each guard protects. |
| **Deliverable** | `tests/test_fault_sequences.py` — timeout, stale availability, duplicate callback, reordered callback, restart mid-episode, clock change, consent revocation. Each asserts I1 deadline, I2 no false completion, I3 idempotency, I4 named owner or visible lack of one, and I5 missing is not negative, at **both** API and serialized patient surfaces. |
| **Hard requirement** | Each sequence must violate **at least one targeted assertion when its guard is independently disabled.** Shared catches do not count as branch coverage. |
| **Also** | `test_scanner_detects_injected_needle` — inject a forbidden facility name, an unlabelled simulated receipt, and a credential into representative serialized HTML/JSON; each is detected, including raw and forward-slash path forms. **A negative scan without this self-test is not evidence.** |
| **Files** | `tests/test_fault_sequences.py`, `tests/test_boundaries.py`, `src/carerelay/state.py` (restart path) |
| **Stop condition** | Any invariant violation blocks feature work. Do not proceed to Slices 11–12 with a red fault sequence. |
| **Check** | Show the user each sequence failing under its disabled guard, then passing. |

### Slice 11 — The judge ledger and the submission surface

**Dates:** 16–17 Oct. **Effort:** 6–10 h. **Build order:** twelfth.

| | |
|---|---|
| **Goal** | The evidence a judge and an engineer can inspect. |
| **Deliverable** | `GET /ledger` — two axes, transitions, expiry, **simulated label**, **failure-event origin**, fault assertions, `dwell_seconds`; `GET /options`; the usage-proof capture. |
| **Files** | `src/carerelay/templates/ledger.html`, `src/carerelay/presentation.py`, `submission/usage-proof.md`, `tests/test_api.py` |
| **Usage-proof obligation** | Genuine WorkBuddy/CodeBuddy development history plus **at least three** redacted chat screenshots. `.gitignore` excludes `.codebuddy/` and `.workbuddy-ai/`, so this is **captured deliberately, from the first session, by a named person, into a named location.** It is the one artefact whose absence blocks scoring entirely (`02-architecture.md` §6.5). |
| **Stop condition** | If the usage proof is absent at this point, the project does not proceed to scoring. Escalate immediately — this is not a last-day item. |
| **Check** | The user inspects the ledger against the declared axes. |

### Slice 12 — Submission assets

**Dates:** 17–18 Oct (and the honest note: this is **past** the 16 Oct deadline unless the earlier slices compress). **Effort:** 8–12 h.

| | |
|---|---|
| **Deliverable** | Project title; sub-ten-word blurb; description; **true 16:9** cover; complete GitHub source; architecture and trust-boundary diagram **with trade-offs**; the demo walkthrough; the honest-claims statement (what the study can and cannot support, the D9 cut, the platform claim at its true strength). |
| **Not** | A live public demo link — declined in `02-architecture.md` §8, because it would expose an unauthenticated clinical-shaped API. Stated as a choice. |
| **Check** | Every claim in the description traceable to a source, a trace, a test, or a clearly labelled hypothesis. |

---

## 3. The critical path

```
Slice 0  K1/K2 (PASS) + Option C source ──┐
                                          │
Slice 1  tracer bullet ───────────────────┼──> Slice 2 domain ──> Slice 3 state
                                          │                          │
                                          │                          ├──> Slice 4 PlanBack
                                          │                          │         │
                                          │                          │         └──> Slice 5 fixture + abstention
                                          │                          │                     │
Slice 7  external card (PARALLEL) ────────┘                          │                     └──> Slice 6 action + platform
                    │                                                 │                                  │
                    └─────> Slice 8 Gate B run ── KILL TEST ──────────┘                                  │
                                        │                                                               │
                    (if not falsified)  v                                                               │
                              Slice 9 Closure Contract <───────────────────────────────────────────────────┘
                                        │
                              Slice 10 fault harness ──> Slice 11 ledger + usage proof ──> Slice 12 assets
```

**The two things that can change this plan:**

1. **Slice 8 falsifies PlanBack.** Then Slices 9–12 are replanned around the surviving mechanism and the submission is smaller and honest. This is designed-in, not failure.
2. **Gate A never passes.** Then Slice 6 takes the recorded fallback: `local-sim`, weakened platform claim, CodeBuddy history as the usage proof.

---

## 4. What "done" means for every slice

Non-negotiable, from the standing rules:

- **Prove it works.** Run it, curl it, or browser-test it, and **show the user the result.** An agent summary is not proof.
- **Check it off in `00-status.md`** — which remains the only authority for slice state.
- **Ask: "Continue to slice N+1, or re-steer?"** If the trajectory is wrong, fix direction before adding code.
- **Real tests only.** Never write a test that passes against the pre-change code. Never comment out, skip or weaken a test to reach green.

---

## 5. Effort summary and the honest arithmetic

| Slice | Effort (h) | Window |
|---|---:|---|
| 0 — kill tests + Option C source | 4–6 | 29–30 Sep |
| 1 — tracer bullet | 5–8 | 30 Sep – 1 Oct |
| 2 — domain core + boundary | 8–13 | 1–3 Oct |
| 3 — state + invariants | 12–20 | 3–6 Oct |
| 4 — PlanBack + ladder | 8–14 | 6–8 Oct |
| 5 — fixture + abstention | 5–8 | 8–9 Oct |
| 6 — action path + platform | 10–16 | 9–11 Oct |
| 7 — external card (parallel) | 5–9 | 3–9 Oct |
| 8 — Gate B run | 15–25 | 11–13 Oct |
| 9 — Closure Contract | 8–14 | 13–15 Oct |
| 10 — fault harness | 8–14 | 15–16 Oct |
| 11 — ledger + usage proof | 6–10 | 16–17 Oct |
| 12 — submission assets | 8–12 | 17–18 Oct |
| **Total** | **102–169** | |

**Compare with the capacity.** Solo, 28 Sep to 16 Oct is **18 days**. At 8 h/day that is **144 h** — and it assumes no lost days, no Gate A retries, no recruitment slippage, no clinical chasing, no submission-form debugging, and no rest. The estimate's central value sits at roughly **135 h**, which means **the plan fits only if almost nothing goes wrong, and does not fit at all in the upper range.**

This paragraph exists because `03-program-design.md` §7 warned that "the upper build range plus the baseline is unlikely to fit a solo schedule" and that Gate 4 "must not silently remove the Closure Contract tests to make the schedule look green". **No Closure Contract test has been removed. Nothing has been cut.** The user's instruction on 28 September 2026 was to keep the full scope, and this plan complies. The arithmetic above is the price of that instruction, recorded rather than hidden.

---

## 6. Risks this plan carries

| # | Risk | Why it is live | Mitigation in this plan | Trigger to change |
|---|---|---|---|---|
| **R1** | **Schedule does not fit.** 102–169 h against 144 h available. | Arithmetic in §5. Solo, full scope, 18 days. | Front-load the kill tests (Slice 0) and the kill test run (Slice 8) so a partial build is still coherent; sequence so Slices 0–6 alone are a demonstrable product with the headline mechanism working. | Any slice overruns its window by more than 50% → replan, and tell the user before cutting anything. |
| **R2** | **Gate A never passes.** Platform path unproven. | The spike is overdue since 26 Sep. Re-verified 28 Sep: no credentials in the environment, no `.env`, no SDK package installed. | Slice 6 builds `CoordinatorPort` with two labelled implementations; the fallback is pre-recorded in Gate 2 §3.3/§6. | No credentials by 11 Oct → take the fallback, weaken the platform claim, state it as weakened. |
| **R3** | **Recruitment fails.** No dyads means no Gate B. | No participant exists. Target 6 per condition, minimum 3. | Slice 7 targets 6 per condition and can run with 3; the protocol is frozen before the first session. | Fewer than 3 per condition → make **no** HCD validation claim, report raw counts only. |
| **R4** | **Option C source cannot be cleared.** Licensing or Singapore applicability fails. | Unchecked. `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope. | Slice 0 front-loads the check; Option B (one reviewer) is the recorded fallback. | No cleared source by 2 Oct → Option B, or escalate. Do not author clinical wording. |
| **R5** | **Reading B is the real contract.** Canonicalisation happens in the model. | The spike's K1 result assumes Reading A. | §1.1 pins Reading A and requires the user's acknowledgment; the residual under B is recorded. | If the coordinator cannot return raw spans → K1 weakens to "the deterministic layer is correct given correct extraction", and the claim is stated at that strength. |
| **R6** | **Callback atomicity fails.** Duplicates lost. | `03-program-design.md` §8 item 4 is an acknowledged hypothesis. | Slice 3 proves it under two concurrent writers and a crash. | Cannot be made atomic → backtrack Gate 2, do not ship a lossy representation. |
| **R7** | **Effort estimate is wrong.** 90–150 h is unverified. | Gate 3 §7 says so explicitly; the user accepted it as achievable, which is not the same as measured. | Slice windows are per-slice stop conditions. | Any slice overrun → R1 trigger. |

---

## 7. Plan-level stop conditions

1. **Slice 0 fails K1 or K2** → PlanBack is cut; replan before Slice 1.
2. **Slice 8 falsifies PlanBack** → cut it; replan Slices 9–12 around the survivor.
3. **Any Closure Contract invariant fails** → stop feature work and repair it (`PLAN.md` §9).
4. **No participant dyad by 13 October** → no HCD validation claim; report raw counts or nothing.
5. **No Gate A by 11 October** → take the recorded local-simulation fallback and weaken the platform claim.
6. **No usage proof at Slice 11** → the project does not proceed to scoring. Escalate, do not paper over it.
7. **R1 fires (any slice >50% over its window)** → tell the user and replan. Do **not** absorb the overrun by quietly dropping tests.

---

## 8. Compacted decisions a fresh session must know

- **Gate 4 is a draft.** No code until the user approves. Approval is the user saying yes in chat, not this document existing.
- **Full scope, no cuts** — user instruction, 28 Sep 2026. The schedule risk is recorded in §5/R1 rather than resolved by cutting.
- **K1 and K2 already pass** (spike, 15/15, Python 3.13.14). That is a deterministic-layer spike result, not an implementation result.
- **C1 is honoured:** the external card (Slice 7) completes before the Closure Contract build (Slice 9), and the kill test (Slice 8) runs between them.
- **Reading A** is adopted for `compare_plan` and pins canonicalisation in `domain`. `ExtractedPlan` must carry the raw span **and** `uncertain_fields`.
- **The Option C source is the only thing blocking the judged fixture.** Everything before Slice 5 can proceed without it.
- **Gate A has not run.** Re-verified 28 Sep: no credentials, no `.env`, no SDK package. Plan for the labelled fallback and take the platform path only if it appears.
- **`00-status.md` is the only authority for slice state.** This document is the plan.
