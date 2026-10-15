# Slice plan: CareRelay urgent-advice accessibility

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

[verified] Narrow Slice 21 frontend scoring-timeout footprint amendment
RE-APPROVED 15 October 2026. The user answered "Approve Gate 4". Slice 21 may
change `frontend/lib/api.ts` only for the score_words/repair_words command
timeout (20 seconds); every other call keeps five seconds. No retry, copy or
other frontend change. `00-status.md` owns the receipt.

**Gate 4 amendment: RE-APPROVED 13 October 2026 Singapore time.**
[verified] The user explicitly answered "Yep i approve" and requested a handoff
for the next agent to start Slice 14 then Slice 15. Section 9 is the approved
upgrade plan. `00-status.md` owns gate/slice state. Gates 1/2/3 contracts remain
unchanged; no proposed slice is started or complete. The new handoff is
`docs/handoffs/patient-experience-slices14-15-2026-10-13.md` (repository root).
Slice 14's Check/continue boundary and an authorised Git handoff into main
precede Slice 15's separate branch. This request supplies no commit, merge,
push, install, credentials, live ADP, production database, deployment or outreach
authority. The drafting/shipping limits below describe their historical checkpoint.

**Historical contract below:** sections 0 to 8 and Slices 0 to 13 are retained
for comparison, including dated forecasts and superseded statements. The
8 October re-approval is recorded in `00-status.md`; the old pending sentence
below describes its drafting checkpoint. Work through Slice 12 and the later
truthfulness repairs shipped; the Slice 9 participant run was cut, and old
Slice 13 was never built. Old Option C, disk/hosting, usage-proof and Gate A
forecasts are not new instructions. Section 9 alone sequences this upgrade;
old Slice 13's intake/classification role and 6 to 10 hours do not cover it.

**Gate 4: RE-APPROVED 30 September 2026.** The plan was approved on 28 September 2026 with the single instruction "continue", reopened on 30 September 2026, and **re-approved the same day**. The restructure is now the plan of record: the tail is renumbered from thirteen slices to fourteen (Slice 0 to Slice 13), one slice is merged, one required slice is added and one conditional slice is added. Authority for gate and slice state is `00-status.md`; this document is the plan, not the state record.

**Gate 4 reopened 8 October 2026: the Gate B run is cut, and re-approval is pending.** Stop condition section 7 item 4 fired (no participant dyad by 5 October) and cut order section 6 item 1 was executed, so the participant run of the study is removed from the plan. The card, the pre-registration and the response-path instrument stay as built work, and the plan makes **no human-centred validation claim**. Slices 10 to 13 no longer wait on a kill-test result. The reopen and its limits are recorded in `00-status.md`.

**Approval authorises:** implementation code, slice by slice, in the order below. **It does not authorise:** installs beyond the declared test dependencies, credentials, recruitment, external calls, deployments, or a push. Each slice still stops for the user's "continue, or re-steer?" before the next one starts. The re-approval question was answered yes on 30 September 2026; the record is in section 8.

Read first: `00-status.md`, `03-program-design.md` (APPROVED 26 Sep, re-approved 30 Sep), `02-architecture.md` (APPROVED 25 Sep revision 2; revision 3 re-approved 30 Sep), `PLAN.md` §7 and §9, `clinical-review-blocker.md`.

---

## 0. What this plan is and is not

| | |
|---|---|
| **Scope** | **Full Gate 3 scope.** The user directed on 28 September 2026 that scope is **not** cut to fit the schedule. Every capability in `03-program-design.md` §2 is sequenced. |
| **Capacity** | Solo. No second contributor is recorded. |
| **Honest consequence, stated up front** | Gate 3 §7 estimates **90–150 h** build plus **20–35 h** baseline (110–185 h combined). **Revised 30 September 2026.** The plan now carries **122–203 h** across Slices 0 to 12, which is the previously recorded 102–169 h **plus 20–34 h for the new Slice 7** (the public deployment, the Next.js clinical frontend under Decision D-1b, and auth). From 30 September to the 16 October submission is **16 calendar days**: 128 h at 8 h/day, and **96 h at a realistic 6 h/day**. **The remaining Slices 4 to 12 are 93–156 h.** The lower bound fits only at a sustained 8 h/day with zero slack; **the upper bound does not fit at all.** This is not a reason to cut scope (the user's instruction), and it is not something this plan will hide. It is the plan's **primary risk**, recorded as R1 in §6 and as the plan-level stop condition in §7. |
| **Restructured 30 September 2026** | The tail is renumbered to **fourteen entries, Slice 0 to Slice 13**. Old Slice 7 becomes **8**, old 8 becomes **9**, old 9 becomes **10**, old 10 becomes **11**, and old Slices **11 and 12 merge into Slice 12**. **Slice 7 is new** (public deployment, the Next.js frontend and auth) and **Slice 13 is new and conditional** (the ADP interpretation surface, default do not run). Constraint **C1 is amended 8 October 2026**: the external card (Slice 8) is built and the Gate B run (Slice 9) is **cut**, so the Closure Contract build (Slice 10) follows the build directly and no human-centred validation claim is made. |
| **What the plan does instead of cutting** | It sequences the full scope so that the **highest-risk, highest-value work lands first** and so that a partial build is still a coherent submission. If the schedule fails, it fails with a working demonstration and an honest record, not with six half-built layers. |
| **Not authorised by this restructure** | The restructure itself authorises nothing. Approval authorises implementation code slice by slice. Installs beyond the declared test dependencies, credentials, recruitment, external calls, deployments and pushes remain unauthorised. |

### Approval record — 28 September 2026

The user approved Gate 4 on 28 September 2026 with the instruction **"continue"**, in response to the Gate 4 approval question. Two sub-questions were left open at drafting and are resolved as follows, both under the recommendation given:

| # | Question | Resolution |
|---|---|---|
| 1 | **ADR-0007 — which layer owns canonicalisation?** | **Reading A accepted.** Canonicalisation lives in `domain`; the coordinator returns raw spans. ADR-0007 moves from `proposed` to `accepted`. The Gate 3 `compare_plan` signature is amended accordingly, as recorded in §1.1. |
| 2 | **The Option C source.** | **Scheduling only, not approval.** The source remains unselected and licensing stays unchecked. It blocks Slice 5 and nothing earlier. The check runs inside Slice 0's window; if no source is cleared by 2 October, Option B is the fallback and clinical wording is **not** authored to unblock the schedule. |

**If either resolution is wrong, say so and the document is corrected before the affected slice.** ADR-0007 affects Slices 2 and 4; the Option C source affects Slice 5.

**Re-approved 30 September 2026.** The user answered the question at the end of this document with "Yep they look good go ahead and commit the changes to main". Gate 4 is therefore **approved as restructured**, and Slice 4 may begin.

---

## 1. Sequencing constraints this plan must honour

These are carried forward from approved gates. None is negotiable here; changing one reopens the gate that set it.

| # | Constraint | Source |
|---|---|---|
| C1 | **The baseline comparison is sequenced before the Closure Contract build. Amended 8 October 2026:** the comparison's participant run was cut, so the ordering is satisfied by the baseline **instrument** (Slice 8, built) preceding the Closure Contract build (Slice 10), and **no human-centred validation claim is made**. | `02-architecture.md` §12; round-2 review; `PLAN.md` §7 currently has the wrong order |
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

**Fourteen slices, Slice 0 to Slice 13.** Each is one shippable, testable state. Dates assume a solo contributor; they are **[hypothesis] planning targets**, not commitments, and the estimate range in `03-program-design.md` §7 is unverified. **Renumbered 30 September 2026:** old Slice 7 is now Slice 8, old 8 is now 9, old 9 is now 10, old 10 is now 11, and old Slices 11 and 12 are merged into Slice 12. **Slice 7 and Slice 13 are new.**

**Slice 13 is conditional and does not run by default.** It is excluded from every total in §5 unless it is explicitly switched on at Gate 2.

### The templates drift, resolved by decision (30 September 2026)

This document previously named `src/carerelay/templates/patient.html` (Slices 1 and 9 in the old numbering, now 1 and 10) and `src/carerelay/templates/ledger.html` (Slice 11 in the old numbering, now 12). Neither file exists, and `jinja2` is declared at `pyproject.toml:12` and imported nowhere. `AGENTS.md` section 5 makes a stale mirror a **blocking finding**, so the drift is closed by decision rather than left open.

**The decision, under D-1b:** no `templates/` directory is created, and `jinja2` is removed from `pyproject.toml`. `presentation.py` owns **JSON serialization only**. Until the frontend slice lands, the patient view is the Slice 1 tracer-bullet HTML rendered by an f-string inside the route; **Slice 7 replaces it with the Next.js frontend and deletes the f-string renderer.** This is the review's "let `presentation.py` own rendering" option carried to its end state, rather than adopting `jinja2` for files that D-1b would then delete.

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
| **Files** | `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json` (hardcoded values only). **Corrected 30 September 2026:** this row previously named `src/carerelay/templates/patient.html`, which does not exist. The shipped Slice 1 renders the four lines with an f-string inside the route. See the templates decision below. |
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

**Dates:** 30 Sep – 2 Oct. **Effort:** 8–14 h. **Build order:** fifth.

| | |
|---|---|
| **Goal** | The product's headline mechanism, running against real state. |
| **Deliverable** | `POST /restatements`, `POST /restatements/{rid}/repairs`, `POST /hint-events`, `POST /transcript-confirmations`. Coordinator extracts raw spans; **`domain` resolves and compares** (Reading A, pinned here). H0–H3 recorded; H2 stays until the patient hides it; `dwell_seconds` to the ledger only; H3 is `not_recalled`, never a pass; two repairs maximum, third routes to the human path (C6). |
| **Files** | `src/carerelay/service.py` (`submit_restatement`, `record_hint_event`, `confirm_transcript`), `src/carerelay/coordinator.py` (extraction interface, **labelled local simulation at this point**), `tests/test_service.py`. **Amended 30 September 2026:** `src/carerelay/static/app.js` is removed from this row. No JavaScript is introduced before Slice 7, and the hide control stays a plain form. |
| **Usage-proof obligation, moved forward** | **This obligation starts here, not at the last slice.** Genuine WorkBuddy or CodeBuddy development history plus **at least three redacted chat screenshots**, captured deliberately by a named person into a named location. `.gitignore` excludes `.codebuddy/` and `.workbuddy-ai/`, so it cannot be reconstructed later. It is the one artefact whose absence blocks scoring entirely (`02-architecture.md` §6.5), and it now runs from this slice through Slice 12. |
| **ADRs produced** | ADR-0007 (canonicalisation lives in `domain`, not the model). See `docs/adr/`. |
| **Stop condition** | If H0–H2 leak a critical field, stop. A hint containing the answer turns a comprehension check into a reading test, and the whole evaluation becomes worthless (`PLAN.md` §5.2). |
| **Check** | Walk the user through a mismatch, one field repaired, then a clean pass, and a third failure routing to the human path. |

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

### Slice 7: Public deployment, the Next.js clinical frontend and auth (NEW, 30 September 2026)

**Dates:** 5–8 Oct. **Effort:** 20–34 h (**[hypothesis]**; the single largest new block in this plan). **Build order:** eighth, immediately after Slice 6.

| | |
|---|---|
| **Goal** | The product is reachable at a public URL by a judge, and it is not an open clinical-shaped endpoint. This is the slice that satisfies Decision D-C, and it is why the live-link bonus is now taken rather than declined. |
| **Deliverable** | (a) The **Render** deployment: Docker image, a **paid plan with a mounted persistent disk**, and the SQLite path supplied by `APP_DATABASE_URL` on that mount. (b) The **bearer-token dependency** on every `/api` route and on `/ledger`, `CORS_ORIGINS` locked to the Vercel origin, `allow_credentials=False`. (c) The **Next.js clinical frontend on Vercel** (D-1b): the one-question patient screen, the four-line unresolved and expired renderings, the hint disclosure control, and the judge ledger view. (d) Secret handling: env vars only, no value in the repository, a log, a fixture or a screenshot. |
| **Placed after Slice 6 deliberately** | So the deployed product already shows intake, PlanBack, an action and a **labelled failure** before it is public. **Auth lands with the deployment, never after it**: a public endpoint without auth is exactly the risk that section 8 of revision 2 declined the bonus to avoid. |
| **Files** | `Dockerfile`, `render.yaml`, `src/carerelay/api.py` (the auth dependency and CORS), `frontend/` (Next.js app), `frontend/lib/api.ts`, `tests/test_api.py` (auth and CORS assertions), `tests/test_boundaries.py` (a secret-shaped string must be detectable in the serialized surfaces) |
| **Hard requirement** | **The append-only record must survive a restart and a redeploy.** The trigger enforcement from Slice 3 rests on a per-connection pragma and on the file being the same file. Prove the record survives a Render restart and a redeploy, with the thirteen tables and their triggers intact, or the persistence claim is not made. |
| **Stop condition** | If the mounted disk cannot hold the SQLite file with WAL intact, **stop and escalate**. Do not silently fall back to `journal_mode = DELETE` or to an ephemeral path, and do not claim a persistence the deployment does not have. The recorded fallback is `journal_mode = DELETE`, at a throughput cost, and it must be stated as a fallback rather than applied quietly. |
| **Check** | Show the user the public URL, an unauthenticated request being refused, and the append-only record surviving a restart. |

### Slice 8: The baseline instrument: the external card (C1)

**Dates:** It runs **in parallel with Slices 4–6**, and must be **complete before Slice 9**. **Effort:** 5–9 h. **Build order:** ninth, and explicitly **before the Closure Contract build**.

| | |
|---|---|
| **Goal** | Discharge constraint **C1**: the kill test runs before the thing it might kill is finished. This is the whole point of the ordering. |
| **Deliverable** | `study/fixed-card.html` — a **standalone, printable/PDF, non-clinical** content-neutral instruction task of the same shape as the app condition, carrying **no symptom, urgency or disposition content** (the Gate 2 D6 backtrack). Same wording, same legitimate options, a direct link, the approved human route. Delivered **outside the application** — it is not an in-app arm. |
| **Files** | `study/fixed-card.html`, `study/protocol.md` (pre-registration: allocation, consent, scripted post-failure question, answer key, raw outcome sheet, cut rule — **all frozen before the first dyad**), `tests/test_study.py` |
| **Tests** | `test_study_fairness_and_scoring` — card is standalone; wording and options match the fixture; allocation is between-subjects; the scripted question and scoring are fixed before sessions; **raw counts, not percentages, below ten participants**. |
| **Recruitment** | Target 6 per condition; **minimum 3 per condition** or no HCD claim. Debt instrument for R3. |
| **Stop condition** | If the card cannot be made content-neutral while staying a fair comparison, stop and re-read the Gate 2 D6 backtrack. A clinical comparator re-imports the reviewer dependency the whole Option A decision removed. |
| **Check** | The user reads the card and the frozen protocol before any participant sees either. |

### Slice 9: Gate B, the comparison (**CUT 8 October 2026, not run**)

**Was:** 8–10 Oct, 15–25 h (sessions + analysis). **Cut order section 6 item 1; stop condition section 7 item 4.**

| | |
|---|---|
| **Status** | **CUT, not run.** No participant dyad was recruited, so the run is removed from the plan and the project makes **no human-centred validation claim**. This is the plan's own pre-recorded honest cut, not a failure. |
| **What stays built** | `study/fixed-card.html` (Slice 8, shipped), `study/protocol.md` (the pre-registration), and the response-path instrument in `src/carerelay/study/`. They are kept as design evidence; the instrument is not a deliverable. |
| **What was removed** | The participant run, the cut-rule application, and the human-centred claim that depended on them. The pre-registration records a study that was not run, and nothing may imply a Gate B result. |
| **Why** | No dyads and no second scorer, on a fixed hackathon deadline. The cut order names the study as the first and honest cut, and the consequence (no human-centred claim, raw counts or nothing) is pre-recorded in R3. |
| **Check** | None: there is no result to show. The instrument's own suite and its mutation harness are the build evidence. |

### Slice 10: The Closure Contract in full (C1 amended: the kill test was cut, not passed)

**Dates:** 10–12 Oct. **Effort:** 8–14 h. **Build order:** eleventh.

| | |
|---|---|
| **Goal** | The second mechanism. **C1 as originally written is void:** the Gate B run was cut on 8 October 2026, so this slice is built on the plan's default rather than on a surviving baseline, and the project makes no human-centred validation claim. |
| **Deliverable** | `derive_closure` complete: two independent axes, `closed_with_evidence` / `escalated_to_human` / `expired_unresolved` / `open`; `POST /acceptances`; the expiry read-path (`record_expiry_once` before projecting, no scheduler); the four-line unresolved and expired renderings from `02-architecture.md` §7, with the five copy rules. |
| **Files** | `src/carerelay/domain/rules.py` (`derive_closure`, `patient_lines`), `src/carerelay/presentation.py` (JSON only), `tests/test_domain.py`, `tests/test_api.py`. **Corrected 30 September 2026:** `src/carerelay/templates/patient.html` is removed from this row; the screen is a Next.js component from Slice 7. |
| **Tests that must be fail-capable** | `test_acceptance_is_not_care` (a named acceptance closes the handoff obligation and never sets `care_evidenced`); `test_serialized_patient_and_ledger_labels` (unresolved/expired copy contains the original deadline and the named fallback; the simulated label is **inside** the serialized patient lines); `test_expiry_sticky_after_clock_regression`. |
| **Copy rules (C, do not drift)** | No reproach, no alarm, no false comfort, a named route, the deadline stays visible. The first draft was rejected as too blunt — later edits must not drift back. |
| **Stop condition** | Any invariant violation blocks further feature work (`PLAN.md` §9). |
| **Check** | Show the user the expired screen and the unresolved screen side by side against the approved wording table. |

### Slice 11: Fault harness and the seven sequences

**Dates:** 12–14 Oct. **Effort:** 8–14 h. **Build order:** twelfth.

| | |
|---|---|
| **Goal** | Prove the contract holds **under fault**, at the boundary each guard protects. |
| **Deliverable** | `tests/test_fault_sequences.py` — timeout, stale availability, duplicate callback, reordered callback, restart mid-episode, clock change, consent revocation. Each asserts I1 deadline, I2 no false completion, I3 idempotency, I4 named owner or visible lack of one, and I5 missing is not negative, at **both** API and serialized patient surfaces. |
| **Hard requirement** | Each sequence must violate **at least one targeted assertion when its guard is independently disabled.** Shared catches do not count as branch coverage. |
| **Also** | `test_scanner_detects_injected_needle` — inject a forbidden facility name, an unlabelled simulated receipt, and a credential into representative serialized HTML/JSON; each is detected, including raw and forward-slash path forms. **A negative scan without this self-test is not evidence.** |
| **Files** | `tests/test_fault_sequences.py`, `tests/test_boundaries.py`, `src/carerelay/state.py` (restart path) |
| **Stop condition** | Any invariant violation blocks feature work. Do not proceed to Slice 12 with a red fault sequence. |
| **Check** | Show the user each sequence failing under its disabled guard, then passing. |

### Slice 12: Judge ledger, submission assets and the usage proof (merge of old Slices 11 and 12)

**Dates:** 14–16 Oct. **Effort:** 14–22 h. **Build order:** thirteenth. **This slice must land before 16 October.** The old Slice 12 window (17 to 18 October) was **past** the deadline, which is why the two slices are merged rather than merely renumbered.

| | |
|---|---|
| **Goal** | The evidence a judge and an engineer can inspect, and the submission package itself. Merging removes a coordination boundary, not work: the effort is the two old rows added together. |
| **Deliverable** | `GET /ledger` (two axes, transitions, expiry, **simulated label**, **failure-event origin**, fault assertions, `dwell_seconds`); `GET /options`; the ledger view in the Next.js frontend; the **usage-proof capture completed**; project title; sub-ten-word blurb; description; **true 16:9** cover; complete GitHub source; architecture and trust-boundary diagram **with trade-offs**; the demo walkthrough; the honest-claims statement (what the study can and cannot support, the D9 cut, the platform claim at its true strength). |
| **Files** | `src/carerelay/presentation.py` (JSON only), `submission/usage-proof.md`, `tests/test_api.py`, plus the submission assets. **Corrected 30 September 2026:** `src/carerelay/templates/ledger.html` is removed from this row; the ledger is a Next.js view from Slice 7. |
| **ADP submission artefacts (not a code slice)** | Publishing and constraining the ADP agent, capturing the **Experience URL**, and capturing **AppKey call logs**. These are submission artefacts, like the cover image: console work and evidence collection, not repository work, and they authorise no code. The AppKey is a secret and is never committed, logged or screenshotted (`02-architecture.md` §6). |
| **Usage-proof obligation** | Started at Slice 4 and completed here. Genuine WorkBuddy or CodeBuddy development history plus **at least three** redacted chat screenshots, captured by a named person into a named location. `.gitignore` excludes `.codebuddy/` and `.workbuddy-ai/`, so it cannot be reconstructed later. It is the one artefact whose absence blocks scoring entirely (`02-architecture.md` §6.5). An ADP AppKey call log is a **supplement only**: the mandatory proof is CodeBuddy or WorkBuddy usage. |
| **Public link** | **The live-link bonus is now taken**, not declined: the Render product and the Vercel frontend from Slice 7, plus the ADP Experience URL. The earlier "declined as a choice" note is superseded by Decisions D-B and D-C. |
| **Stop condition** | If the usage proof is absent at this point, the project does not proceed to scoring. Escalate immediately: this is not a last-day item, which is why its capture started at Slice 4. |
| **Check** | The user inspects the ledger against the declared axes, and every claim in the description is traceable to a source, a trace, a test, or a clearly labelled hypothesis. |

### Slice 13: ADP interpretation surface (CONDITIONAL, default do not run)

**Dates:** only if switched on. **Effort:** 6–10 h (**[hypothesis]**). **Build order:** last, and **only after a Gate 2 re-approval explicitly enables it**.

| | |
|---|---|
| **Goal** | A second, independent interpretation surface, if and only if time remains after the scored path is complete. |
| **Gate** | **Gate 2 gated.** `02-architecture.md` D8 permits ADP on the **interpretation step only**. Enabling this slice is a Gate 2 decision, not a scheduling decision. |
| **Default** | **Do not run.** It is excluded from every total in §5, from the critical path in §3 and from the cut order in §6. Nothing downstream depends on it. |
| **Deliverable** | An ADP-backed implementation of the intake clarification loop and the D7 closed-vocabulary classification, returning **structured values only**, validated in `domain`. |
| **Hard boundary** | **It must not touch the execution path or the rendering path.** ADP output is converted to structured values and validated in `domain` before it can affect anything, and an ADP SSE answer must never reach the patient surface (`02-architecture.md` §8). |
| **Decision point** | Taken only if Slices 7 to 12 are complete and the usage proof exists. If either is false, this slice does not run and the answer is recorded as "not run", not left silent. |
| **Stop condition** | If ADP cannot return structured values that `domain` can validate, stop. The surface is additive and the product is complete without it. |
| **Check** | Show the user the same episode resolved through the ADP surface and through the local simulation, with identical structured output. |

---

## 3. The critical path

**Amended 8 October 2026: Slice 9 (the Gate B run) is CUT. Read the diagram below with the Gate B run removed: Slice 10 follows the completed build directly and no longer waits on a kill-test result.**

```
Slice 0  K1/K2 (PASS) + Option C source ──┐
                                          │
Slice 1  tracer bullet ───────────────────┼──> Slice 2 domain ──> Slice 3 state
                                          │                          │
                                          │                          ├──> Slice 4 PlanBack
                                          │                          │         │
                                          │                          │         └──> Slice 5 fixture + abstention
                                          │                          │                     │
Slice 8  external card (PARALLEL) ────────┘                          │                     └──> Slice 6 action + platform
                    │                                                 │                                  │
                    │                                                 │                                  v
                    │                                                 │                    Slice 7 PUBLIC DEPLOY + AUTH
                    │                                                 │                                  │
                    └─────> Slice 9 Gate B run ── KILL TEST ──────────┘                                  │
                                        │                                                               │
                    (if not falsified)  v                                                               │
                              Slice 10 Closure Contract <────────────────────────────────────────────────┘
                                        │
                              Slice 11 fault harness ──> Slice 12 ledger + assets + usage proof
                                                                        │
                                              Slice 13 ADP surface (CONDITIONAL, default off)
```

**The two things that can change this plan:**

1. ~~**Slice 9 falsifies PlanBack.**~~ **FIRED 8 October 2026, in its cut form:** no dyad was recruited, so the run was cut rather than falsifying PlanBack. The plan's pre-recorded honest cut (section 6 item 1) executed, and Slices 10 to 13 proceed without a kill-test result.
2. **Gate A never passes.** Then Slice 6 takes the recorded fallback: `local-sim`, weakened platform claim, CodeBuddy history as the usage proof.

**A third, added 30 September 2026.** **Slice 7 is now the largest single block in the plan and it sits on the critical path to a public link.** If it overruns, the honest response is to cut the study (Slices 8 and 9), not to deploy without auth and not to cut the fault harness.

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
| 0: kill tests + Option C source | 4–6 | 29–30 Sep |
| 1: tracer bullet | 5–8 | 30 Sep – 1 Oct |
| 2: domain core + boundary | 8–13 | 1–3 Oct |
| 3: state + invariants | 12–20 | 3–6 Oct |
| 4: PlanBack + ladder + **usage-proof start** | 8–14 | 30 Sep – 2 Oct |
| 5: fixture + abstention | 5–8 | 2–3 Oct |
| 6: action path + platform | 10–16 | 3–5 Oct |
| **7: public deployment + Next.js frontend + auth (NEW)** | **20–34** | 5–8 Oct |
| 8: external card (parallel, was Slice 7) | 5–9 | 3–8 Oct |
| 9: Gate B run (was Slice 8) | **CUT 8 Oct 2026** | not run |
| 10: Closure Contract (was Slice 9) | 8–14 | 10–12 Oct |
| 11: fault harness (was Slice 10) | 8–14 | 12–14 Oct |
| 12: ledger + submission assets + usage proof (**merge of old 11 and 12**) | 14–22 | 14–16 Oct |
| **Total, Slices 0 to 12** | **107–178** | after the 8 October 2026 cut of Slice 9 (15–25 h) |
| *13: ADP interpretation surface (CONDITIONAL, excluded from the total)* | *6–10* | *only if switched on* |

**The arithmetic, recomputed 30 September 2026.** The old total was **102–169 h**. The new total is **122–203 h**, which is the old figure **plus Slice 7's 20–34 h** and nothing else: the merge of old Slices 11 and 12 adds the two old rows together (6–10 plus 8–12 becomes 14–22) rather than saving work, and every other slice keeps its previous estimate.

**Compare with the capacity.** Solo, 30 Sep to 16 Oct is **16 days**. At 8 h/day that is **128 h**; at a realistic 6 h/day it is **96 h**. Neither figure allows for lost days, Gate A retries, recruitment slippage, the Option C source check, submission-form debugging, or rest. **Reduced 8 October 2026:** the cut of Slice 9 (15 to 25 h) takes the plan total to **107 to 178 h**. **The remaining Slices 4 to 12 are 93–156 h.** The lower bound fits only at a sustained 8 h/day with zero slack; **the upper bound does not fit at all.**

This paragraph exists because `03-program-design.md` §7 warned that "the upper build range plus the baseline is unlikely to fit a solo schedule" and that Gate 4 "must not silently remove the Closure Contract tests to make the schedule look green". **No Closure Contract test has been removed and nothing has been cut.** The user's instructions of 28 September 2026 (keep the full scope) and 30 September 2026 (take the Vercel deployment, Decision D-1b) are both complied with, and the arithmetic above is the price of them, recorded rather than hidden.

---

## 6. Risks this plan carries

| # | Risk | Why it is live | Mitigation in this plan | Trigger to change |
|---|---|---|---|---|
| **R1** | **Schedule does not fit.** 122–203 h against 128 h available. | Arithmetic in §5. Solo, full scope, 16 days, and Decision D-1b added 20–34 h on 30 September 2026. | Front-load the kill tests (Slice 0) and the kill test run (Slice 9) so a partial build is still coherent; sequence so Slices 0 to 7 alone are a demonstrable, publicly reachable product with the headline mechanism working. | Any slice overruns its window by more than 50% → replan, and tell the user before cutting anything. |
| **R2** | **Gate A never passes.** Platform path unproven. | The spike has been overdue since 26 Sep. Re-verified 28 Sep: no credentials in the environment, no `.env`, no SDK package installed. | Slice 6 builds `CoordinatorPort` with two labelled implementations; the fallback is pre-recorded in Gate 2 §3.3/§6. | No credentials by 11 Oct → take the fallback, weaken the platform claim, state it as weakened. |
| **R3** | **Recruitment fails.** No dyads means no Gate B. **FIRED 8 October 2026: no dyad, so the run is cut and no human-centred validation claim is made.** | No participant exists. Target 6 per condition, minimum 3. | Slice 8 targets 6 per condition and can run with 3; the protocol is frozen before the first session. | Fewer than 3 per condition → make **no** HCD validation claim, report raw counts only. |
| **R4** | **Option C source cannot be cleared.** Licensing or Singapore applicability fails. | Unchecked. `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope. | Slice 0 front-loads the check; Option B (one reviewer) is the recorded fallback. | No cleared source by 2 Oct → Option B, or escalate. Do not author clinical wording. |
| **R5** | **Reading B is the real contract.** Canonicalisation happens in the model. | The spike's K1 result assumes Reading A. | §1.1 pins Reading A and requires the user's acknowledgment; the residual under B is recorded. | If the coordinator cannot return raw spans → K1 weakens to "the deterministic layer is correct given correct extraction", and the claim is stated at that strength. |
| **R6** | **Callback atomicity fails.** Duplicates lost. | `03-program-design.md` §8 item 4 is an acknowledged hypothesis. | Slice 3 proves it under two concurrent writers and a crash. **Proven 30 September 2026; R6 is closed.** | Cannot be made atomic → backtrack Gate 2, do not ship a lossy representation. |
| **R7** | **Effort estimate is wrong.** 90–150 h is unverified. | Gate 3 §7 says so explicitly; the user accepted it as achievable, which is not the same as measured. | Slice windows are per-slice stop conditions. | Any slice overrun → R1 trigger. |
| **R8 (NEW)** | **The public deployment breaks the append-only record.** A mounted disk that cannot hold WAL, or an ephemeral path, silently loses the Slice 3 guarantee. | The trigger enforcement rests on a per-connection pragma and on the file being the same file. Render's free tier is ephemeral, and WAL needs `-wal` and `-shm` beside the database with mmap support. `[hypothesis]` until measured on the real disk. | Slice 7's hard requirement is to prove the record survives a restart and a redeploy with all thirteen tables and their triggers intact. | The disk cannot hold WAL → stop and escalate; the recorded fallback is `journal_mode = DELETE`, stated as a fallback rather than applied quietly. |
| **R9 (NEW)** | **A public surface becomes a clinical claim.** A published agent or a public endpoint answers clinical questions with no reviewer. | The audit's test is "no deployment claim without an authorised protocol and qualified reviewer". A published ADP agent is public and shareable unless it is constrained. | The ADP agent's knowledge base is limited to the non-clinical fixture and its guardrails refuse clinical advice before the URL is shared; the CareRelay endpoint sits behind the bearer token and carries the research-demonstration label. | Any clinical answer reachable on a public surface → take the surface down and record it. |

**The cut order (updated 30 September 2026), first to last:**

1. ~~**The study, Slices 8 and 9 (20 to 34 h), if no dyad is recruited by about 5 October.**~~ **EXECUTED 8 October 2026.** No dyad was recruited, so the participant run of the study is cut and the plan makes no human-centred validation claim. Slice 8 is built and shipped and the instrument is built; only the run is removed. This is the honest cut the plan pre-recorded.
2. **Never adopt Decision D-1b.** **VOID as of 30 September 2026:** the user took D-1b explicitly, so this line no longer applies and the Next.js frontend is not a cut candidate. It is retained so the supersession is visible rather than silent.
3. **Keep the Closure Contract (Slice 10) and the fault harness (Slice 11).** They carry the demo's honesty and two scored dimensions, and they are not cut candidates.

**Cut candidates not on this list, and why.** Slices 0 to 7 are the demonstrable product, so cutting one removes a capability rather than compressing a schedule. Slice 12 is the submission itself and its window is now inside the deadline. Slice 13 is already conditional and defaults to off.

---

## 7. Plan-level stop conditions

1. **Slice 0 fails K1 or K2** → PlanBack is cut; replan before Slice 1.
2. **Slice 9 falsifies PlanBack** → cut it; replan Slices 10 to 13 around the survivor.
3. **Any Closure Contract invariant fails** → stop feature work and repair it (`PLAN.md` §9).
4. **No participant dyad by 5 October** → cut the study (Slices 8 and 9); make no HCD validation claim; report raw counts or nothing. **FIRED 8 October 2026: the run is cut.**
5. **No Gate A by 11 October** → take the recorded local-simulation fallback and weaken the platform claim.
6. **No usage proof** → the project does not proceed to scoring. Its capture starts at Slice 4 and is checked at every slice, not only at Slice 12. Escalate, do not paper over it.
7. **R1 fires (any slice >50% over its window)** → tell the user and replan. Do **not** absorb the overrun by quietly dropping tests.
8. **R8 fires (the mounted disk cannot hold WAL)** → stop and escalate. Do not deploy an unauthenticated endpoint, and do not claim a persistence the deployment does not have.
9. **R9 fires (a public surface answers a clinical question)** → take the surface down, record it, and do not re-share it until the constraint is proven.

---

## 8. Compacted decisions a fresh session must know

- **Gates 2, 3 and 4 were reopened and re-approved on 30 September 2026.** No code until the user re-approved, which happened the same day. Approval is the user saying yes in chat, not this document existing.
- **Full scope, no cuts** — user instruction, 28 Sep 2026. The schedule risk is recorded in §5/R1 rather than resolved by cutting. **Superseded 8 October 2026:** the plan's pre-recorded cut order fired (no dyad by 5 October), so the study run is cut. This is the plan's own honest cut, not a new scope decision.
- **The stack is Render plus Vercel** (Decision D-1b, 30 Sep 2026): Python and FastAPI on Render behind a shared bearer token, and a Next.js clinical frontend on Vercel. The server-rendered HTML and vanilla JS presentation is retired. This is why **Gate 3 reopened** as well as Gates 2 and 4.
- **ADP is additive only** (Decision D-A): the interpretation step, never the execution path and never the rendering path. **Slice 13 is conditional and defaults to off.**
- **K1 and K2 already pass** (spike, 15/15, Python 3.13.14). That is a deterministic-layer spike result, not an implementation result.
- **C1 is amended 8 October 2026:** the external card (Slice 8) is built, the Gate B run (Slice 9) is **cut and not run**, and the Closure Contract build (Slice 10) follows directly with no human-centred validation claim.
- **Reading A** is adopted for `compare_plan` and pins canonicalisation in `domain`. `ExtractedPlan` must carry the raw span **and** `uncertain_fields`.
- **The Option C source is the only thing blocking the judged fixture.** Everything before Slice 5 can proceed without it.
- **The usage proof starts at Slice 4.** It is the one artefact whose absence blocks scoring, and it cannot be reconstructed once the session logs are gone.
- **Gate A has not run.** Re-verified 28 Sep: no credentials, no `.env`, no SDK package. Plan for the labelled fallback and take the platform path only if it appears.
- **`00-status.md` is the only authority for slice state.** This document is the plan.

**Re-approval question: answered yes on 30 September 2026.** The user approved the amended Gates 2, 3 and 4 and authorised the commit. Recorded in `00-status.md`.

---

## 9. Patient-experience upgrade: proposed vertical slices, 13 October 2026

### 9.1 Authority, inspected gaps and bounded delivery

[verified design authority] Gate 1's twelve screens/copy, Gate 2 revision 4
section 13 and section 5.2, and Gate 3 section 9 are approved. This amendment
sequences them; it does not change their signatures, policy, strings, closure
precedence or proof requirements. Gates 1/2/3 documents remain byte-preserved.

[verified source inspection] `api.py:create_episode/get_episode/patient_page`
still use the shared ID or pre-disposition fixture lines. `PatientPage` creates
on render; `api.ts:call` casts unknown JSON. `permitted_options` exposes configured
routes without a disposition. `repair_restatement/_score` compares repair words
as a whole plan. `_DB_LOCK` surrounds extraction; separate store reads do not
establish one journey snapshot. Action purpose is caller-supplied; MCP rechecks
and local invocation are separate. `LocalSimulationCoordinator` normalises
lexical spans. The published ADP instruction lacks the approved source-offset,
uncertainty and final-answer profile. These are the anticipated upgrade gaps,
not a claim that the shipped truthfulness repairs failed.

[verified historical evidence only] The 12 October record reports 945 passed,
46 Postgres skips, one warning and 39/39 truthfulness mutations RED. No runtime,
browser, live ADP or engine checks are run while drafting this plan. [unknown]
Live extraction, Postgres ordering, production accessibility and card advantage
remain unproved. No new falsifier of an earlier gate is established here.

[hypothesis] The smallest coherent delivery is eight slices, retaining Slice 13
as an unbuilt historical entry. Build order:

1. Slice 14: visible read-only no-plan/recovery tracer.
2. Slice 15: explicit durable start, full stored-plan/outcome reads and resume.
3. Slice 16: explicitly confirmed offline read-back, repair and cue honesty.
4. Slice 17: barrier, permission, bounded simulated dispatch and truthful failure.
5. Slice 18: strict ADP adapter exercised with offline transports.
6. Slice 19: actual disposable Postgres migration, races and restart proof.
7. Slice 20: complete production-browser/accessibility proof and remediation.
8. Slice 21: separately authorised live ADP observations and local enablement.

The grouping follows the visible flow's minimum safety boundary: creation brings
its migration/receipts, scoring brings confirmation/repair/cue guards, and request
brings permission/dispatch fencing. Strict vendor transport stays a separate slice.
Splitting those guards into later layers would expose an unsafe interim mutation.

These are future builds, not permission to start now. After Gate 4 re-approval,
obtain the separately scoped first-slice instruction. Each implementation branch
is created from current main before editing, using the proposed stable names
below; commit/merge/push authority is still separate. If prerequisite slices are
not on main, stop for the authorised handoff rather than silently branch from an
old slice. No horizontal store/service/frontend batch is proposed.

### 9.2 Entry blockers and exposure rules

- **Copy:** Slice 16's patient confirmation/save/check controls are blocked until
  Gate 1 approves the exact confirmation label/help and any new pending/retry
  wording actually needed. `Review my answer` remains a local, unsaved preview.
  Specialized non-timing repair strings remain blocked; use only the approved
  generic full-answer correction. System-date templates remain blocked; the
  scenario stays 30 September 2026, 09:00 SGT, with the stored 18:00 SGT deadline
  (`2026-09-30T10:00:00+00:00`). Missing approved date wording yields recovery.
  Record the separate Gate 1 reopen/re-approval before exposing those strings;
  this Gate 4 draft neither supplies nor approves them.
- **Literal tomorrow:** `fixture-provisional-0` supports `tomorrow before 6pm`,
  not bare `tomorrow`. The latter is uncertain, not definitely wrong. The timing
  story uses supported wrong-day wording, then `today before six`; no expected
  time is filled into an incomplete answer. A different comparison requires a
  separately versioned Gate 2 decision, then reconciliation of dependent plans.
- **Live ADP:** Slices 14 to 20 use disabled ADP or explicitly labelled offline
  extraction. Slice 21 blocks on separate authority for publish AND activation,
  instruction/schema/profile and knowledge-base/tool checks, server-only access,
  fictional-only processing and redacted captures. Existing `clinical_share`
  consent is not ADP-processing authority. No automatic fallback or retry.
- **Postgres:** both engines' code/contracts land with each visible flow. Actual
  engine proof is Slice 19, with explicitly authorised disposable access only.
  Missing access leaves this proof blocked/unproven, not passed. Never use
  production `APP_DATABASE_URL`, install a container or mutate hosted data by
  convenience. Earlier slices can close only their named SQLite/offline scope;
  the whole upgrade cannot close while Slice 19 is blocked.
- **Exposure:** partial builds run locally and offer only implemented, guarded
  commands. A planned control is absent, not an inert success-looking button.
  Until an assessed projection is implemented, return transport unavailable and
  exact recovery text rather than a fabricated partial plan. Replay/stop/version/
  consent boundaries land before each mutation is exposed. Existing legacy
  patient writes must cease being bypasses when command-backed start lands.
  Operator fixture callbacks/transfers remain separate authenticated paths.
- **Release:** local SQLite proof does not permit hosted mutating rollout. Require
  Slice 19 and Slice 20 before that later release decision; live extraction also
  requires Slice 21. Old-app rollback after new records is unsafe: disable new
  progression, retain upgraded readers/recovery and all append-only records.
  Deployment, submission and asset publication require separate authority.

### 9.3 Common exit discipline and exact file conventions

All paths below are repository-relative future file contracts from Gate 3
section 9.2. `.tsx` paths name production Next.js source; this drafting task
creates no implementation or visualisation file. Any later visualisation is HTML.
For every slice, update evidence/scope in `00-status.md`,
`patient-experience-upgrade.md`, `AGENTS.md`, `docs/PLAN.md`,
`docs/DESIGN_PRINCIPLES.md`, `tasks/todo.md` and `PROGRESS.md` only as facts change.

The verification allocation in section 9.5 is part of every exit contract. Each
parameter/guard is independently proved where introduced. Keep the existing
truthfulness service/API/MCP controls and their individual mutations. Include
new pure functions in the real-file SDK/network/store/filesystem/clock scanner;
the domain receives injected time, never reads a clock. Extend secret scans to
all new server/client files and serialized RSC, using synthetic fixture values.

Preserve Gate 3 section 9.8 HTTP mapping: 200 completed/replayed, 202 pending,
409 stale/body/parent conflict with a fresh authenticated known-episode journey,
422 schema/unpermitted input, 404 unknown, 401 auth refusal, 503 transport/lock/
unavailable. Store failure cannot invent a receipt. Decode the whole bounded
projection or use exact recovery text; never display provider/error detail.

Use the existing interpreter/toolchain; no installs. Establish a fresh baseline
for the authorised slice, run focused tests and mutations, then the relevant full
suite and frontend `npm run typecheck`/`npm run build` when touched. An unavailable
tool is recorded, never substituted with a claimed pass. Record collected
selectors, controls, actual assertion failures and byte-exact restoration;
collection/import/syntax errors, missing anchors and skipped engines are NOT
PROVEN. Run one guard mutation at a time, purge its bytecode and back up untracked
targets outside the repo before running. Never kill a live mutation harness.

Capture authenticated API JSON, real browser render, exact local URL/port, engine,
process IDs and relevant revision/deadline. Basic keyboard/focus/reflow checks
accompany each new control; Slice 20 completes the matrix, not the first check.
Show the actual visible result, record bounded completion in `00-status.md`,
invoke `architect-reviewer` in post-slice cleanup mode, then ask the applicable
`Continue to slice N+1, or re-steer?` question. No next slice starts automatically.

### Slice 14: read-only no-plan tracer

**Proposed branch:** `slice-14-journey-tracer`. **Effort:** 4 to 7 h.

- **Goal/visible result:** entry shows approved No plan yet; authenticated GET
  of an existing disposable no-disposition episode yields the real nullable
  projection, which the production renderer displays. A blocked API/unknown
  locator produces recovery. Refresh and HintCard revalidation make zero POSTs.
- **Entry:** Gate 4 approval plus explicit Slice 14 instruction; no new copy,
  credentials or engine access. Existing historical records remain intact.
- **Exact files:** `src/carerelay/domain/models.py`, `src/carerelay/domain/rules.py`,
  `src/carerelay/state.py`, `src/carerelay/postgres_store.py`, `src/carerelay/service.py`, `src/carerelay/presentation.py`, `src/carerelay/api.py`,
  `src/carerelay/tools.py`, `src/carerelay/demo/fixture.py` (all under `src/carerelay/`);
  `frontend/lib/api.ts`, `frontend/lib/journey.ts`, `frontend/lib/episode-locator.ts`,
  `frontend/app/example/route.ts`, `frontend/app/page.tsx`, `frontend/components/PatientJourney.tsx`,
  `frontend/components/HintCard.tsx`, `frontend/app/globals.css` (all under `frontend/`);
  `tests/test_journey.py`, `tests/test_journey_commands.py`, `tests/test_api.py`,
  `tests/test_service.py`, `tests/test_boundaries.py`, `tests/_mutate_patient_experience.py`.
- **Exit:** Gate 3 section 9.3 complete no-plan shape: null plan/outcome/versions/
  aliases, false care, empty lines/options, zero questions/scoring/action offers.
  MCP discloses no no-plan guidance even with consent. Bare FastAPI `/` is 303
  to the configured trusted frontend, without fixture body or caller redirect.
  Page does not create; the read-only bootstrap sets a signed candidate locator
  before any future mutation. No start POST is offered yet. Assessed journeys
  not implemented in this tracer return unavailable/recovery, not synthetic
  guidance. Decoder rejects malformed/bounded unknown data; recovery copy is an
  exact limited Gate 1 mirror. The stores provide the minimal coherent read
  used here; no `journey_commands` migration is introduced without a command.
- **Proof:** G01/G06/G07/G09 and no-plan subset of G31/G37/G38. Independently
  restore each surface's fixture fallback; move creation into render; remove one decoder invariant/detector per malformed input. The bootstrap
  codec has good/bad cookie controls here; the start-precondition mutation is
  proved with actual explicit creation in Slice 15.
  Positive scanner injection must detect each forbidden needle on the serialized
  API, SSR/RSC and visible/accessibility text before an absence claim counts.
  Browser: no-cookie entry, locator 404, blocked bootstrap, blocked API, keyboard
  Try again, 320px/enlarged text; network verifies zero mutation/model/dispatch.
- **Tier/exclusions/stop:** offline authenticated API and disposable SQLite;
  Postgres reader parity is source-only until Slice 19. No intake, scoring,
  hints/consent mutations, requests, live ADP or hosted rollout. Any fabricated
  no-plan guidance or implicit mutation blocks exit; an earlier-contract
  contradiction follows section 9.8's owning-gate stop protocol.

### Slice 15: explicit durable start and coherent stored journey

**Proposed branch:** `slice-15-durable-start`. **Effort:** 14 to 23 h.

- **Goal/visible result:** See the example explicitly creates a distinct episode
  then selects the single allowlisted scripted appointment; a plan appears.
  Dropping either response and reloading reads the same candidate/episode. Stored
  failed, stopped, expired, accepted and successful-handoff fixtures render
  their true outcome with the original deadline and no public actor controls.
- **Entry:** Slice 14 complete; explicit continuation. Scenario copy only.
- **Exact files:** `src/carerelay/domain/models.py`, `src/carerelay/domain/rules.py`,
  `src/carerelay/journey_commands.py`, `src/carerelay/state.py`, `src/carerelay/postgres_schema.py`, `src/carerelay/postgres_store.py`,
  `src/carerelay/service.py`, `src/carerelay/presentation.py`, `src/carerelay/api.py`, `src/carerelay/tools.py`, `src/carerelay/demo/fixture.py`;
  `frontend/lib/api.ts`, `frontend/lib/journey.ts`, `frontend/lib/episode-locator.ts`,
  `frontend/app/example/route.ts`, `frontend/app/page.tsx`, `frontend/app/actions.ts`,
  `frontend/components/PatientJourney.tsx`, `frontend/app/globals.css`, `frontend/app/ledger/page.tsx`;
  `tests/test_journey.py`, `tests/test_journey_commands.py`, `tests/test_journey_postgres.py`,
  `tests/test_state.py`, `tests/test_postgres_store.py`, `tests/test_service.py`, `tests/test_api.py`,
  `tests/test_boundaries.py`, `tests/test_ledger.py`, `tests/test_deployment.py`,
  `tests/_mutate_patient_experience.py`.
- **Exit:** add the exact Gate 3 section 9.9 table, indexes, phase/terminal-claim
  binding and append-only constraints in both engines with create/intake, not
  as a separate database phase. Preserve all fourteen old tables/rows/triggers.
  Apply DDL twice only to disposable SQLite; seed old no-plan/active/stopped/
  expired/accepted/handoff histories and reopen fresh. Revision is committed
  episode `events.id`, safe for JavaScript; every projection-affecting writer,
  including operator/legacy wrappers, appends its event atomically and uses
  episode serialization. Coherent patient/sticky-expiry and ledger/options
  reads use Gate 3 section 9.8 transactions. No nested repository transactions
  or Postgres read rollback inside a write.
- **Exit, browser/command:** signed HttpOnly/host-only/SameSite locator;
  Secure on HTTPS with explicit loopback test exception; purpose-separated
  server HMAC, rotation/missing-key recovery, Origin/host/cookie binding.
  Read-only preparation binds exact canonical UTF-8 JSON/digest, including
  unchanged whitespace/code points. Create and intake each have one claim and
  terminal receipt. Absent-row creation uses PK/operation uniqueness with
  conflict rollback/replay, never an imaginary absent-row lock. Exact replay
  precedes stale-revision refusal and returns a fresh journey; changed body 409;
  pending 202; bad MAC cannot create caller-chosen identity. No auto HTTP/SDK
  retry. Lost create/intake never writes a second episode/disposition/v2.
- **Exit, projection:** recorded policy/text bundle A remains A when configured
  B changes; unknown/missing A refuses. Implement the complete pure twelve-screen
  and contradiction matrix now, while rendering/command offers expose only
  available capabilities. Initial plan precedes read-back; none of the future
  commands are offered. Test every screen predicate with trusted stored fixtures;
  Slices 16/17 subsequently drive their mutations end to end. Documented-care
  is a trusted repository fixture only. Stop is independent of closure;
  acknowledgement/unknown stays neutral; expiry precedence and legacy stops
  survive reload. Lower same-episode revision is discarded and fetched fresh;
  equal revision can still change with clock-derived expiry, never a guessed
  browser clinical calculation. No query selector fabricates an outcome.
- **Proof:** G02 to G07/G09 to G14/G16/G31/G36/G37/G38, with individual token
  dimensions and engine constraints. Network-drop create/intake after commit;
  double taps, two tabs, missing locator, explicit second example, reload,
  rotation, malformed projections and restart. Child crash between state and
  receipt proves both commit or neither. Matched seeded rows make UPDATE/DELETE/
  SQLite REPLACE tests fire. Browser/curl agree on every outcome's exact lines,
  axes/stop/owner/version/deadline; keyboard start/retry and 320px checks.
- **Tier/exclusions/stop:** offline SQLite proof, both-engine implementation,
  real Postgres cases explicitly unproven until Slice 19. No word-confirmation,
  progression, action execution or live ADP. Receipt/legacy-bypass/snapshot or
  preserved-history failure blocks exit. Missing system-date copy keeps scenario
  mode; it does not permit invented dates or a shifted deadline.

### Slice 16: confirmed offline read-back and field repair

**Proposed branch:** `slice-16-confirmed-readback`. **Effort:** 16 to 28 h.

- **Goal/visible result:** from the real plan, start read-back, locally review
  fictional words, explicitly confirm, then score with the labelled offline
  extractor. A supported wrong deadline selects timing repair; timing-only
  `today before six` retains latest known action/owner. Reveal/hide/reload stays
  cued. Two valid uncertain repairs or H3 produce a durable unresolved stop.
- **Entry:** Slice 15 plus continuation; **blocked patient-flow entry** until
  the separate Gate 1 confirmation wording approval in section 9.2. No hidden
  save on Review. Specialized non-timing/date strings remain blocked.
- **Exact files:** `src/carerelay/domain/models.py`, `src/carerelay/domain/rules.py`,
  `src/carerelay/journey_commands.py`, `src/carerelay/adp_extraction.py` (port and explicit offline adapter),
  `src/carerelay/state.py`, `src/carerelay/postgres_store.py`, `src/carerelay/service.py`, `src/carerelay/presentation.py`, `src/carerelay/api.py`,
  `src/carerelay/coordinator.py`, `src/carerelay/demo/fixture.py`; `frontend/lib/api.ts`, `frontend/lib/journey.ts`,
  `frontend/app/actions.ts`, `frontend/components/PatientJourney.tsx`, `frontend/components/HintCard.tsx`,
  `frontend/app/globals.css`, `frontend/app/ledger/page.tsx`; `tests/test_field_repair.py`,
  `tests/test_journey.py`, `tests/test_journey_commands.py`, `tests/test_journey_postgres.py`,
  `tests/test_service.py`, `tests/test_state.py`, `tests/test_postgres_store.py`, `tests/test_api.py`,
  `tests/test_boundaries.py`, `tests/test_truthfulness.py`, `tests/test_truthfulness_postgres.py`,
  `tests/test_ledger.py`, `tests/_mutate_patient_experience.py`.
- **Exit:** all text modes require exact confirmed words bound to episode,
  version, attempt, latest parent and unique confirmation. Draft review calls
  no API/model. Preparation is read-only and words go to extraction only after
  confirmation; changed drafts invalidate prepared tokens. Identical words in
  different rounds are separate operations. Historical digest-only events do
  not grant new permission; legacy offsets/provenance remain unknown.
  Offline adapter supplies exact-source spans or unavailable, never normalized
  substrings pretending to be source offsets. ADP remains disabled.
- **Exit, scoring:** short claim/context commit, release all DB mutexes/locks,
  fake/offline extraction, fresh final transaction rechecks terminal/revision/
  version/policy/parent/confirmation/cue/stop/deadline. Concurrent reveal/stop/
  expiry fences late answers. Applied score/provenance/stop/receipt are atomic;
  pending has no further scoring/request offer. Explicit supersede fences late
  output, with one terminal winner and an explicit fresh scoring offer. Failure
  completes unavailable with no row/repair count; it does not set clinical stop.
  Database failure fabricates neither receipt nor failed-action heading.
- **Exit, repair/cue:** retain only latest same-chain known matches, preserving
  transitive grounded sources. New explicit other-field values replace retention;
  negation/doubt/conditional/alternatives/questions/multiple candidates/backward
  correction invalidate affected matches. Keep unrelated-aside positive control.
  Never fill from expected values or uncertain/old/unconfirmed fields. Valid
  uncertain repairs consume rounds 1 and 2; initial round is 0; invalid/refused/
  timeout/confirm/hide consume zero. No reset via initial POST. H3 never passes.
  Readback response/SSR/RSC/dialog/accessibility text contains no server answers
  in hidden mode; recorded show commits H2 before revealing. Timing repair is
  the approved answer-bearing exception and records a cue. Hide/Escape/reload
  cannot lower it. Dwell stays judge-only, never a timer or automatic advance.
- **Proof:** G08/G12 to G16/G18 to G23/G34/G38; positive/negative offline
  extraction controls. All retention/correction/cue/cap/recheck guards have
  separate mutations and otherwise-valid inputs. Curl changed/old confirmation,
  stale parent, duplicate, pending/supersede and crash; prove one extraction.
  Browser keyboard review/confirm/repair/Show/Escape restores focus; dropped
  responses and refresh preserve state. Draft is escaped, errors approved.
- **Tier/exclusions/stop:** offline deterministic/API/SQLite; Postgres cases
  authored for Slice 19, no live ADP. Barrier/question may be shown when a valid
  match exists but no mutation offered until Slice 17. Missing exact copy,
  scanner-positive control, grounding, cap or stale-result refusal blocks exit;
  literal tomorrow stays uncertain under this policy.

### Slice 17: permission and truthful simulated failure

**Proposed branch:** `slice-17-permission-failure`. **Effort:** 14 to 23 h.

- **Goal/visible result:** understood plan -> booking barrier -> unchecked
  permission -> explicit simulated request -> waiting/real callback failure ->
  exact unresolved lines. Restart retains one attempt and original deadline.
  Transport/other barriers stop honestly; decline/revoke starts no request.
- **Entry:** Slice 16 plus continuation; no new actor/clinical/copy authority.
- **Exact files:** `src/carerelay/domain/models.py`, `src/carerelay/domain/rules.py`,
  `src/carerelay/journey_commands.py`, `src/carerelay/state.py`, `src/carerelay/postgres_store.py`, `src/carerelay/service.py`,
  `src/carerelay/tools.py`, `src/carerelay/coordinator.py`, `src/carerelay/presentation.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`;
  `frontend/lib/api.ts`, `frontend/lib/journey.ts`, `frontend/app/actions.ts`,
  `frontend/components/PatientJourney.tsx`, `frontend/components/HintCard.tsx`, `frontend/app/globals.css`,
  `frontend/app/ledger/page.tsx`; `tests/test_journey.py`, `tests/test_journey_commands.py`,
  `tests/test_journey_postgres.py`, `tests/test_service.py`, `tests/test_api.py`, `tests/test_state.py`,
  `tests/test_postgres_store.py`, `tests/test_truthfulness.py`, `tests/test_truthfulness_postgres.py`,
  `tests/test_ledger.py`, `tests/test_boundaries.py`, `tests/_mutate_patient_experience.py`.
- **Exit:** all barrier/hint/consent/request writes claim/complete atomically,
  current version/understanding/stop/expiry checked. Fixed appointment purpose
  `disposition:<version>:request_appointment` and supported `fictional_provider`
  route are server-owned. New tokens/tabs cannot create a new purpose/attempt.
  Current clinical_share grant is checked under final serialization; the cookie
  never substitutes for auth/consent. Local action coordinator alone calls MCP;
  extraction has no action capability.
- **Exit, invocation:** service commits attempt/claim first; only the original
  newly-claiming process holds a registered, once-consumed DispatchPermit.
  MCP rejects forged/omitted/reconstructed permits and old keys. Under SQLite
  write/Postgres episode-row serialization, reread membership/version/purpose/
  stop/current consent and fresh deadline/sticky expiry, then record dispatch
  start, bounded synchronous local invocation, reservation/observation and
  applied/refused terminal receipt in the same final transaction. No delayed
  service receipt commit. This lock exception is only for the local simulator;
  ADP/network calls hold no lock. Callback is separate; observation is not ack.
- **Exit, races/crashes:** committed stop/revoke first means zero calls;
  invocation first means a later writer waits, then stops/revokes, with late
  success/evidence refused. Begun work cannot be undone. Kill after durable
  claim before invocation, or after effect before final commit: unknown/pending
  survives, reload/replay/new token/direct service/MCP never redispatches.
  Missing reservation is not permission; no lease reclaim/exactly-once claim.
  Failure/duplicates stay auditable, first-terminal and consent/version guards
  remain. Refuse caller-labelled real evidence and unrelated acceptance.
- **Proof:** G03 to G07/G12 to G14/G16/G17/G22/G31 to G35/G37/G38.
  SQLite independent-process barriers and kills, per-guard mutations, direct
  service/MCP bypass probes, double taps and dropped responses. Complete the
  twelve real API/browser states and contradiction cases using authenticated
  operator fixtures for acceptance/handoff; no public success selector.
  Keyboard radio/checkbox/decline/revoke/request/recovery, API failure versus
  unknown observation, refresh, 320px and enlarged text checks.
- **Tier/exclusions/stop:** offline/SQLite and bounded local effects;
  Postgres races unproven until Slice 19. No real provider, message, ADP action,
  clinical branch or patient impersonation of caregiver/human path. Any duplicate
  invocation, receipt split, false success or bypass blocks further feature work.

### Slice 18: strict ADP extraction with offline transports

**Proposed branch:** `slice-18-adp-boundary`. **Effort:** 12 to 21 h.

- **Goal/visible result:** confirmed fictional words travel through the ADP
  adapter with explicitly fake transport; positive spans produce deterministic
  comparison, wrong time produces timing repair, missing/negated input is
  uncertain, invalid/refusal/slow-terminal shows approved unscored unavailable.
  Judge provenance names fake transport and never claims live extraction.
- **Entry:** Slices 16/17 plus continuation; no keys, network or publish.
- **Exact files:** `src/carerelay/adp_extraction.py`, `src/carerelay/domain/rules.py`,
  `src/carerelay/domain/models.py`, `src/carerelay/service.py`, `src/carerelay/coordinator.py`, `src/carerelay/api.py`, `src/carerelay/presentation.py`;
  `frontend/lib/api.ts`, `frontend/lib/journey.ts`, `frontend/components/PatientJourney.tsx`,
  `frontend/app/ledger/page.tsx`; `tests/test_adp_extraction.py`, `tests/test_field_repair.py`,
  `tests/test_journey_commands.py`, `tests/test_journey_postgres.py`, `tests/test_api.py`,
  `tests/test_boundaries.py`, `tests/test_deployment.py`, `tests/_mutate_patient_experience.py`.
- **Exit:** exact Gate 3 section 9.7 six-key `carerelay-readback-v1` object,
  grounded Unicode code-point half-open spans and explicit uncertainty/refusal.
  Strict unknown/duplicate/missing keys, versions, types, null/refusal consistency,
  invalid UTF-8/nonfinite/two-object/prose/fence checks. Union provider flags
  with independent whole-answer checks, then domain canonicalises/compares.
  Missing provider spans are never lexically filled. Only confirmed words,
  independent vocabularies, schema/instruction/correlation enter the model;
  no expected plan, answers, profile, consent, receipt or AppKey in prompt.
- **Exit, transport:** pin fake good profiles for incremental OR complete final
  answer; capture parsing is not live-profile proof. Validate lifecycle/message/
  content/correlation/order/channel/error/terminal, multiline SSE and bounded
  UTF-8 decoding. Reasoning is never buffered/rendered/logged/persisted; ambiguous
  duplicates and delta+final doubling refuse. HTTP 200/EOF/first byte cannot pass.
  Whole-response monotonic budget 5 seconds; input 2,048 code points, final answer
  16 KiB, frame 16 KiB, wire 64 KiB including ignored channels. Exact-limit good
  cases and each over-limit fail; limits remain unmeasured choices. No retries,
  SDK retry or hidden local fallback; failed output consumes no repair/stop.
- **Proof:** G15/G18 to G21/G24 to G30/G34/G38, independent parametrized
  validator/profile/limit mutations, fresh good-case controls, two concurrent
  score workers and superseded/late answers. Planted reasoning/secret must be
  detected on that same surface if leaked. Authenticated curl and production
  browser show same preserved answer/question/owner/deadline and unscored
  failure; one transport call, zero provider calls on extraction. Request body
  asserts fresh stateless IDs, server-only endpoint/auth, no redirects forwarding
  credentials and no expected-answer pairing. Default enable flag is false.
- **Tier/exclusions/stop:** offline fake envelope/API/SQLite only, live profile
  and model correctness unknown. A permissive parser workaround or inability to
  implement the approved discriminator reopens Gate 2; it never enables ADP.

### Slice 19: disposable Postgres end-to-end proof

**Proposed branch:** `slice-19-postgres-proof`. **Effort:** 11 to 18 h.

- **Goal/visible result:** the same real start/read-back/failure/stopped journey
  is read by an authenticated fresh backend process against disposable Postgres.
  Patient/options/ledger retain episode, absolute deadline, stop and receipts;
  browser returns to that episode without extraction/dispatch.
- **Entry:** Slices 15 to 18 complete in their offline scope; continuation and
  separately authorised disposable engine/access. No authorised DSN means blocked.
- **Exact files:** `tests/test_journey_postgres.py`, `tests/test_journey_commands.py`,
  `tests/test_postgres_store.py`, `tests/test_truthfulness_postgres.py`, `tests/test_deployment.py`,
  `tests/test_boundaries.py`, `tests/_mutate_patient_experience.py`; only evidence-led fixes
  in `src/carerelay/state.py`, `src/carerelay/postgres_schema.py`, `src/carerelay/postgres_store.py`,
  `src/carerelay/service.py`, `src/carerelay/tools.py`, `src/carerelay/api.py` within the approved contract.
- **Exit/proof:** real two-connection/process deterministic barriers for G11 to
  G17/G31 to G38: coherent snapshots, same claim, supersede, atomic state/receipt,
  stop/revoke before invocation, invocation before waiting stop, late extraction
  dimension rechecks, callback ordering and every action crash window. Lock
  episode before reading, sorted episode/attempt/command order; pure reads
  REPEATABLE READ READ ONLY, patient expiry reads episode-serialized. Fresh
  read after acquiring a waited lock; prove no lock/mutex remains across fake ADP.
  Migration applies twice to seeded pre-upgrade histories; row bytes/absolute
  deadlines remain, latest parent uses event order with equal timestamps,
  legacy provenance stays unknown. Exact table/trigger parity, seeded matching
  receipt UPDATE/DELETE/TRUNCATE/ON CONFLICT UPDATE and claim/phase binding
  controls each fail independently when only their guard is removed.
- **Browser/API:** run production journey locally with this engine; curl known
  and unknown IDs before/after backend termination; replay committed operation
  after response loss; inspect outcome/commands and no POST on browser refresh.
  Run relevant full suite and engine mutations with zero skipped engine cases
  for the proof claimed, recording actual server/driver versions and failures.
- **Tier/exclusions/stop:** actual disposable Postgres and fresh-process evidence,
  not Supabase/Render deployment or production data. No ADP network, install,
  deployed restart or exactly-once external-effect proof. Any unproved required
  race/trigger, flaky result or inaccessible engine prevents complete engine
  proof; source parity and SQLite passes cannot substitute. New architectural
  falsifiers return to the owning gate.

### Slice 20: production accessibility proof and remediation

**Proposed branch:** `slice-20-accessibility-proof`. **Effort:** 9 to 16 h.

- **Goal/visible result:** the actual production-code journey, served locally,
  is operated through start/confirm/repair/barrier/permission/failure/recovery
  using keyboard and assistive technology, with readable action/deadline/status.
- **Entry:** Slices 14 to 19, confirmation copy approval, explicit continuation;
  a named available assistive-technology/browser pair. If unavailable, record
  that path blocked, complete independent checks, and do not claim full exit.
- **Exact files:** `frontend/components/PatientJourney.tsx`, `frontend/components/HintCard.tsx`,
  `frontend/app/page.tsx`, `frontend/app/actions.ts`, `frontend/app/globals.css`, `frontend/lib/journey.ts`;
  `tests/test_journey.py`, `tests/test_journey_commands.py`, `tests/test_boundaries.py`,
  `tests/_mutate_patient_experience.py`;
  `docs/reviews/patient-experience-browser-accessibility.md`.
- **Exit/proof:** every item in section 9.6, twelve states/substates and
  contradiction agreement at API/SSR/RSC/visible/accessibility surfaces, G03/
  G06/G07/G08/G09/G23/G38. Minimal in-scope fixes rerun affected checks and
  relevant suite/build/typecheck; no new patient wording without Gate 1 approval.
  Evidence states browser/OS/screen-reader versions, viewport/CSS width, zoom,
  steps, expected/observed announcement/focus, failures and limitations. No
  placeholder PASS file, proxy mockup or DOM-only accessibility certificate.
- **Tier/exclusions/stop:** manual production-browser/assistive-technology proof
  locally, with offline extraction and engine proof separate. No target-user
  benefit, clinical safety, general language, outreach or deployment claim.
  Lost action/deadline, focus traps, hidden answers or inaccessible required
  path blocks full exit; repair or owning-gate re-approval comes first.

### Slice 21: authorised live ADP enablement, separate from action execution

[verified user instruction] On 16 October 2026 the user answered "Sure i approve the experiment please finish up slice 21!" to the exact wording-only Gate 2/3/4 proposal and at most one ledger-reserved product call. The narrow amendment is RE-APPROVED. It preserves the v2 schema, published instruction v2, current model/settings, 15-second cap, all byte limits, no retry/fallback, default-off and code authority. Stop after that one live result. No shipping or additional live calls are authorised. `00-status.md` owns the receipt.

Prove the server wording change with failing-first request-content tests, named deletion/substitution mutations and the full offline suite. Run at most one positive local-product call, reserve it first in the existing ledger, then stop on either result. No frontend, dependency, console setting or publication change. The remaining corpus/serialized proof and Check acceptance remain separate.

[hypothesis, narrow engineering amendment] The Slice 21 live response cap is
15 seconds for the whole response, as justified by Gate 2 section 13.6 and
specified in Gate 3 section 9.7. Slice 18's existing five-second fake controls
remain historical/current controls for those profiles. Observe and test the
provider's complete-answer mode with Incremental false before enabling it;
retain 2,048 input code points, 16 KiB final/frame, 64 KiB wire and no retry.
Prove a late terminal is unscored at the new live cap. The one 30-second
diagnostic exception supplies no production-budget pass or general timing claim.


**Proposed branch:** `slice-21-adp-enablement`. **Effort:** 4 to 8 h of engineering
observation/integration, excluding operator/access waiting and publishing work.

- **Goal/visible result:** one confirmed fictional paraphrase is observed through
  the compatible live agent and pinned final-answer profile, then compared by
  code in the local production journey. Negative/invalid/refusal/timeout paths
  remain unscored or uncertain as contracted; action origin stays `local-sim`.
- **Entry:** Slices 18/19/20 complete; continuation plus separately scoped
  operator/live-call authority. Compatible instruction/schema is deliberately
  published AND activated; inspect knowledge base, tools, guardrails and fresh
  stateless sessions. Review fictional processing boundary/server configuration
  before enabling. Credentials configured locally by operator, never pasted.
- **Exact files:** `src/carerelay/adp_extraction.py`, `src/carerelay/api.py`, `src/carerelay/service.py` only
  for observed approved profile/config wiring; `tests/test_adp_extraction.py`,
  `tests/test_boundaries.py`, `tests/test_deployment.py`, `tests/_mutate_patient_experience.py`;
  `docs/reviews/adp-readback-observations.md`; later operator revisions to
  `submission/adp-agent-instruction.md` and `submission/setup-runbook.md`, separately
  authorised as Gate 3 section 9.2 permits. No general asset/claims rewrite here.
  Amended 15 October 2026: `frontend/lib/api.ts` only for the score_words/repair_words
  command timeout (20 seconds, all other calls unchanged at five seconds), and
  `tests/test_journey_commands.py` for its real-module timeout, single-request and
  no-retry proof. No other frontend file, copy or behaviour change.
  Amended 15 October 2026: the model returns span text only, under wire schema `carerelay-readback-v2` and instruction `carerelay-readback-instruction-v2`.
  Code locates exactly one word-bounded exact occurrence; none or several stays uncertain.
  The operator publishes AND activates the revised instruction before any further live call.
  Exact files are unchanged.
- **Exit/proof:** G24 to G30/G34 plus actual positive paraphrase, known wrong
  time, missing values, clinical advice/refusal/injection, negation, alternatives
  and backward correction probes in new sessions. Capture redacted profiled
  Type/message/content/correlation/terminal discrimination and version/request/
  latency/failures. Configured instruction is an operator assertion until
  observed; absent model version remains unknown. Old two refusals are no
  positive control. Regression-check the real captured envelope offline; bounded
  invalid/timeout faults stay deterministic offline, not invented vendor events.
  Use only server-held `ADP_APPKEY`/`ADP_CHAT_ENDPOINT`, default-off
  `ADP_EXTRACTION_ENABLED`, no AppKey prompt/browser/log/SSE persistence.
  Browser/curl verify one explicit call, deterministic result, approved failure
  wording and preserved owner/deadline/closure. No action/tool call follows an
  extraction response by itself.
- **Tier/exclusions/stop:** separately observed live ADP corpus only; no clinical
  safety/general comprehension/WorkBuddy runtime/production deployment/benefit
  claim. Missing positive extraction, incompatible profile, leaked reasoning,
  over-budget legitimate frames or unverifiable activation keep ADP disabled.
  If the approved boundary is impossible, record the counterexample and reopen
  Gate 2 rather than coercing schemas, dropping limits or joining arbitrary Text.

### 9.4 Inspectable effort arithmetic and schedule choice

[hypothesis, unmeasured person-hours] Reallocation of Gate 3 section 9.11's
74 to 126 build/proof hours and 10 to 18 integration allowance. This is a slice
estimate, not measured velocity. Each slice includes its tests/mutations/basic
browser checks; Slice 19 is additional actual-engine proof and Slice 20 the
complete manual matrix. The allowance below is counted once, not again later.

| Slice | Build/proof | Integration allowance | Slice total |
|---|---:|---:|---:|
| 14: no-plan tracer | 4 to 6 | 0 to 1 | 4 to 7 |
| 15: durable start/projection | 12 to 20 | 2 to 3 | 14 to 23 |
| 16: confirmed read-back/repair | 14 to 24 | 2 to 4 | 16 to 28 |
| 17: permission/local failure | 12 to 20 | 2 to 3 | 14 to 23 |
| 18: offline ADP boundary | 10 to 18 | 2 to 3 | 12 to 21 |
| 19: disposable Postgres proof | 10 to 16 | 1 to 2 | 11 to 18 |
| 20: accessibility proof | 8 to 14 | 1 to 2 | 9 to 16 |
| 21: live ADP observations | 4 to 8 | 0 | 4 to 8 |
| **Sum** | **74 to 126** | **10 to 18** | **84 to 144** |

Lower totals: `4+14+16+14+12+11+9+4 = 84`.
Upper totals: `7+23+28+23+21+18+16+8 = 144`.
Tracer only: 4 to 7 h. Through stable start/outcome reads: 18 to 30 h.
Through offline read-back/failure (Slices 14 to 17): 48 to 81 h, still without
ADP/actual-Postgres/full-accessibility proof. Through Slice 20: 80 to 136 h.

Reuses shipped code; excludes Gate 4 drafting, copy/operator publishing/access
delays, processor/region/retention review, clinical review, participant research,
deployment and asset/submission revision. Those exclusions are not zero-cost.
At an assumed 6 productive h/day, full engineering is 14 to 24 working days;
actual availability is unknown. A full-upgrade promise from 13 to 16 October
is unsupported. Current competition cutoff has not been verified here.

The approval choice is the ordered full plan with small stop boundaries, not
automatic execution of all slices. A short schedule can select the tracer or
stable-start milestone and describe only that result; it cannot call the whole
upgrade done or drop guards from an exposed flow. If the user wants narrower
product/ADP scope, record that explicit decision and reopen its owning gate.
Before implementation, confirm available hours/desired milestone separately.
If any slice exceeds its upper effort bound, report actual hours and remaining
obligations and replan at that boundary; preserve proof rather than hide overrun.

### 9.5 Complete Gate 3 guard allocation: planned, no results

The following ledger copies every guard/counterexample/mutation row of approved
Gate 3 section 9.10 and adds its slice allocation. Row IDs are traceability,
not a claimed count of tests or covered branches. Every listed mutation inside
a row is separate. SQLite owners prove locally when introduced; Slice 19
independently repeats applicable store/race/restart guards on real Postgres.
All relevant slices preserve G38. No checkbox/PASS below represents execution.

| ID | Exit owner/proof | Guard/test | Counterexample and observable result | Single-guard mutation |
|---|---|---|---|---|
| G01 | 14; 15/19 restart | `test_journey.py::test_no_plan_surfaces` | Create without intake: API/options/MCP and bare-root redirect disclose no fixture plan/owner/deadline/options; lines empty; unknown ID 404 | Restore only no-disposition fallback per surface as separate mutations; drop no-plan options/MCP guard independently |
| G02 | 15 | `::test_recorded_policy_selected` | Persist policy A then configure B: journey action/words/compare remain A or refuse missing A | Replace disposition-version lookup with configured policy |
| G03 | 15 matrix; 16/17 flows; 20 | `::test_twelve_screens` | Drive each approved condition, assert step/question/commands/exact text plus independent axes and original deadline | Change each screen predicate/command filter separately, not a global always-fail mock |
| G04 | 15/17 | `::test_failed_unknown_handoff_not_transfer` | Escalation outcomes failed/attempted/unknown with ID: patient owner/open/no passed wording | Treat escalation ID alone as successful |
| G05 | 15/17 | `::test_ack_is_neutral`, `::test_stop_keeps_true_transfer`, `::test_expiry_wins` | Ack alone neutral; stop+valid transfer no question; overdue acceptance expires; documented fixture retains approved precedence | Remove each predicate/precedence/automation filter separately |
| G06 | 14 structural; 15/16/17 full; 20 | `::test_projection_invariants` | Unknown version, two questions, mismatched aliases, malformed no-plan, missing display, stop+request: decoder renders recovery, zero POST | Remove each runtime invariant independently with only its malformed fixture |
| G07 | 14 to 20 as surfaces land | `test_boundaries.py::test_serialized_detection_controls` | Inject each forbidden success phrase/facility/clinician/credential/unlabelled receipt into representative API JSON, SSR HTML/RSC and visible/accessibility text; detection must fire | Remove each needle detector independently; require its positive control to fail |
| G08 | 16; 20 | `test_journey.py::test_no_unaided_answer_payload` | H0/H1 readback response/SSR/dialog/accessibility serialization contains no action/deadline/owner answers; Show first records H2 | Restore one answer-bearing field per mutation, including hidden/preloaded dialog payload |
| G09 | 14 bootstrap; 15 start | `test_journey_commands.py::test_cookie_precedes_start` | Network blocks bootstrap response: browser sends zero create; entry render/remount/HintCard revalidation sends zero POST | Move create into render; bypass cookie-established start check separately |
| G10 | 15 | `::test_distinct_example_and_same_reload` | Two intentional starts distinct IDs; reload same ID/no model/dispatch; locator 404 recovery | Restore shared ID; replace reload with create separately |
| G11 | 15; 19 | `::test_lost_create_and_intake` | Drop response after each commit, reload then same-operation explicit replay: one episode/one disposition/no v2 | Bypass create uniqueness or completed-intake lookup separately |
| G12 | 15; extend 16/17; 19 | `::test_body_digest_conflict` | Same operation with changed text/choice/parent: 409 conflict, no second fact/consent/round, current journey | Remove digest equality only; companion detects changed stored claim/completion binding |
| G13 | 15; extend 16/17 | `::test_token_bindings` | Swap episode/version/revision/kind/purpose/parent/confirmation or bad MAC: refused with zero work | Remove each named binding check one at a time |
| G14 | 15 basic; 16 extraction; 19 | `::test_pending_and_terminal_replay` | Two workers same claim: one extraction; pending 202, completed replay fresh stopped projection not old success | Remove claim uniqueness; bypass fresh projection independently |
| G15 | 16; 18; 19 | `::test_supersede_fences_late_result` | Explicit supersede then release old fake ADP answer: one terminal superseded, no scored row/repair | Remove old-terminal fence only |
| G16 | 15 start; 16 score; 17 action; 19 | `::test_atomic_apply_receipt` | Kill child between comparison write and terminal receipt, restart/replay: both absent or both committed | Split terminal/state transaction at the cut point |
| G17 | 17; 19 | `::test_fixed_request_purpose` | Fresh tokens/double tap/forged purpose/direct service and MCP: one attempt, at most original invocation | Trust caller purpose; remove dispatch-claim ownership check independently |
| G18 | 16 | `test_field_repair.py::test_confirmation_exact_and_latest` | Draft, changed confirmed string, identical text from prior version/round: no ADP or scored row | Remove each confirmation dimension/digest check separately |
| G19 | 16 | `::test_retains_only_latest_known_matches` | Timing-only latest-parent repair succeeds with grounded action/owner retained; uncertain owner stays uncertain; prior-version parent refuses | Disable retention; fill uncertain from expected; disable version/latest-parent check in separate tests |
| G20 | 16 | `::test_whole_answer_invalidates_retention` | Timing answer + Actually I won't; explicit different action/owner; alternatives/questions/conditional: no understood result; unrelated aside positive control | Remove each independent doubt/correction branch; disable replacement of newly expressed field separately |
| G21 | 16 | `::test_uncertain_not_definite_mismatch` | Unknown phrase/null versus known wrong day: uncertain correction vs deadline mismatch; unsupported action never timing accusation | Convert unknown to mismatch; choose timing copy for non-timing mismatch separately |
| G22 | 16/17 | `::test_two_repairs_h3_and_round_zero` | Valid uncertain rounds 1/2 then stop; H3 no pass; fresh initial POST after failure cannot reset ladder | Remove cap, H3 check, current-stop gate and unfinished-parent gate separately |
| G23 | 16; 20 | `::test_reveal_hide_reload_cued` | Reveal/hide/reload then posted H0 remains cued; timing repair answer cue persists; hide consumes zero rounds | Trust client hint; clear exposure on hide/reload; omit repair cue event separately |
| G24 | 18 offline; 21 live | `test_adp_extraction.py::test_positive_and_negative_controls` | Grounded positive, known wrong time, missing value and negated whole answer: match/mismatch/uncertain; always-refuse adapter fails positive | Drop extraction use/canonical comparison or independent doubt separately |
| G25 | 18 | `::test_strict_object[case]` | Extra/missing key, canonical ID, wrong version/type, duplicate key, two objects, prose/fences, repeated/unknown uncertainty, inconsistent refusal/null: unavailable/scored false/no round | Remove only the validator named by each parameter, with otherwise valid object |
| G26 | 18 | `::test_grounding[case]` | Invented span, wrong offsets, UTF-16 emoji offset, bool int, negative/end-overrun/empty: invalid, no retained/expected answer filling | Disable each bounds/type/source-slice check independently |
| G27 | 18; 21 observed profile | `::test_sse_envelope[case]` | HTTP200 error, reasoning-first, mixed channels/messages, duplicate chunk, truncated/terminal missing, final+delta duplicate: unavailable; one pinned good profile passes | Remove each profile/error/terminal/channel/order/duplication check alone |
| G28 | 18 | `::test_full_stream_timeout` | First byte within budget then terminal after 5 seconds: timeout, no score/repair, preserved deadline | Replace whole-response deadline with per-chunk/first-byte budget |
| G29 | 18 | `::test_limits[case]` | 2,049 code points, 16KiB+1 answer, oversized frame/wire: unavailable/refused without score; exact-limit control passes | Raise/remove only each named limit |
| G30 | 18; 21 | `::test_no_retry_fallback_or_reasoning` | Timeout/refusal/invalid: exactly one ADP call, zero lexical fallback; planted reasoning/secret never in patient or logs | Enable retry; call local extractor after failure; pass reasoning/credential to surface independently |
| G31 | 15 SQLite; 19 Postgres | `test_journey_postgres.py::test_snapshot_race`, SQLite companion | Pause between snapshot SELECTs, concurrent stop/consent: all fields from one revision, no mixed active/stop commands | Remove read transaction isolation or read across transaction-bound bundle in separate engines |
| G32 | 17 SQLite; 19 Postgres | `::test_stop_before_dispatch`, `::test_consent_before_dispatch` | Commit stop/revoke before invocation barrier: zero provider calls, refused receipt, current owner/deadline unchanged | Remove final episode serialization/recheck individually per engine |
| G33 | 17 SQLite; 19 Postgres | `::test_dispatch_before_stop` | Pause bounded local provider while stop waits: one invocation ordered before stop, late success refused; no promise to undo it | Release episode lock before invocation; remove late success stop/consent check separately |
| G34 | 16/18 SQLite; 19 Postgres | `::test_late_extraction_rechecks[dimension]` | While fake ADP waits, change stop/version/parent/cue/revision or pass deadline: final unscored/no round/unchanged deadline | Remove each final recheck independently, release exactly that concurrent change |
| G35 | 17 SQLite; 19 Postgres | `::test_action_crash_never_redispatches` | Kill after claim, before invocation and after simulated effect before commit: restart/new token/direct MCP never re-invokes; pending unknown stays neutral | Reclaim pending action or infer authorization from missing dispatch reservation |
| G36 | 15 SQLite; 19 Postgres | `::test_schema_migration_and_append_only[case]` | Old histories preserved after twice-applied additive DDL; seeded new receipt refuses update/delete/replace/truncate/upsert | Omit table/trigger or phase/claim binding guard independently |
| G37 | 15/17 SQLite; 19 Postgres | `::test_fresh_process_reads` | Fresh authenticated backend reads patient/options/ledger same episode, stop and absolute deadline; unknown still 404 | Reintroduce process-local registry or omit persisted stop read |
| G38 | Every runtime slice; 19 Postgres | Existing truthfulness service/API/MCP regressions | Evidence forgery, unrelated acceptance, late success, old keys/H3/exhaustion remain refused; simulation labels intact | Each existing repair guard retains its targeted mutation; don't substitute a new shared wrapper catch |

Scanner positive controls include every exact arranged/agreed/passed/no-action-
needed sentence, each facility/clinician/credential needle and an unlabelled
simulated receipt, at API JSON, SSR HTML/RSC and visible/accessibility text.
Require detection on that same surface first, including JSON escaped/raw/
forward-slash path forms. Use fixture needles, not actual secrets; remove only
one detector for its own positive-control mutation. Restore one hidden
answer-bearing field at a time, including preloaded dialog/accessibility data.
Frontend runtime invariants need browser recovery/zero-POST observations under
malformed inputs as well as parser tests; a static scan does not execute a
decoder. The existing Python boundary/deployment tests can orchestrate the
installed Node runtime and real Next.js server without adding a test dependency.

### 9.6 Production-browser and accessibility exit matrix

Apply to actual production code served locally, not Gate 1 mockups. Intended
manual pair: **VoiceOver with Safari on macOS**; record observed versions.
If that pair is unavailable, leave its required path blocked until an available
named pair is explicitly selected and exercised. No install is inferred.

- Desktop plus **320 CSS pixels**, default/enlarged setting; record viewport.
  Check **200% text enlargement**, **200% browser zoom** and **400% browser
  zoom** separately, recording effective CSS viewport. Ordinary content has
  no horizontal scrolling/clipping; action/deadline/status/buttons remain usable.
- Keyboard only: skip link to main, explicit start, review, confirmation, both
  repair rounds, barrier radio group, checkbox, decline/revoke/request, Show,
  Hide/Escape, same-episode Try again. Label inputs/options and associate errors.
  Focus is visible and moves meaningfully after errors and step changes.
- Dialog: focus inside, background inert, no focus escape/trap, Escape restores
  opener or meaningful successor after a step change. API show/hide failure,
  rerender, reload and stopped plan do not strand focus or erase cue history.
- Screen reader: start -> read-back question -> empty input error -> pending
  interpretation -> unavailable/refused or result -> repair -> failed request
  -> recovery. Verify one question, associated error and polite status announced
  once without repeated rerender chatter. No hidden expected answer, provider
  reasoning or raw exception/detail. Local preview label is removed after save.
- All twelve screens and waiting/declined/acknowledged/unknown/documented fixture
  branches: exact approved copy, simulation label, independent stop/outcome,
  original deadline/actual owner. H0/H1 and hidden H2 payloads leak no server
  answer; visible Show is preceded by recorded H2. Icons supplement words.
- No timed hide/countdown/wizard advance, no patient dwell/score/streak. Measure
  DOM/reflow/scanner checks as bounded automated observations; combine with
  manual keyboard, focus and actual announcements. Record failures and fixes.

### 9.7 Honest claim milestones and later manual work

[hypothesis] Slice 14 supports only a read-only no-plan/recovery result. Slice 15
adds local durable start/stored outcome reads. Slices 16/17 add bounded offline
read-back and local simulated request/failure. Slice 18 proves the fake-transport
boundary, not live ADP. Slice 19 proves an actual disposable engine, not hosted
restart. Slice 20 records observed accessibility paths, not target-user suitability
or certification. Slice 21 supports only its observed fictional live corpus.
Approval does not convert any planned result into proof.

The participant run remains cut. Benefit versus a clear instruction card, reduced
burden, clinical safety and general language comprehension remain unknown even
after engineering checks. Shared-token acceptance actors and services remain
simulated. ADP extraction never demonstrates WorkBuddy execution/session resume.

Later separately authorised work: processor/region/retention review before data
boundary changes; qualified clinical review/protocol; participant research only
if explicitly restarted; verification/revision of existing usage-proof, demo,
claims, diagrams and submission assets against actual evidence; deployment/
deployed-restart proof and submission. No current cutoff or score is asserted.
An asset file existing is not a fresh provenance/redaction/claim audit.

### 9.8 Falsifier and approval boundary

Stop further capability work on a failed contract invariant. Record its concrete
input, observed surface/engine and counterexample. Implementation errors within
an authorised contract are repaired and re-proved within that slice. If the
approved contract itself cannot satisfy stop/replay/disclosure/order/ADP limits,
reopen Gate 2; if signatures/migration cannot implement it, reopen Gate 3;
missing or changed strings go through Gate 1. Update the owning gate and all
state mirrors, then stop for explicit re-approval. Gate 4 cannot silently relax
an earlier contract to meet an effort range or pass a test.

This is the safe handoff point: proposed order, exact future files, blocked
entries, all guard allocations and effort/claim limits are on disk. No code,
tests, migrations or live proofs exist from this assignment. Remaining sequence:
Gate 4 approval -> separately authorised visible slices -> API/accessibility/
disposable-Postgres proof -> corrected demo/claims/assets -> separately authorised
deployment/submission. Each slice stops for continue or re-steer.

**Approval recorded:** "Yep i approve", 13 October 2026. Gate 4 is RE-APPROVED.
The user requested an implementation handoff for Slice 14 followed by Slice 15,
with the approved per-slice checkpoint preserved. Neither slice is started here;
Git shipping and later external/manual dependencies still need separate authority.
