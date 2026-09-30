# Goal

Reframe CareRelay around truthful urgent-advice execution, produce a Gate 1 product specification and HTML wireframes, and determine whether Mandarin Chinese and voice can be included safely.

## Checklist

- [x] Inspect repository state and existing plan evidence.
- [x] Research Mandarin/voice feasibility and blocker workarounds.
- [x] Write Software Factory Gate 1 status and product specification.
- [x] Create plain-HTML Gate 1 wireframes for the core journey.
- [x] Verify the HTML and document review results.
- [x] Obtain explicit Gate 1 approval before architecture or implementation.

## Independent adversarial review — 2026-09-21

- [x] Preserve Gate 1 as pending; this review is not approval.
- [x] Verify every supplied requirement, plan, case study, and HTML mockup.
- [x] Verify current competitors and Singapore substitutes from primary sources.
- [x] Compare at least three materially different directions against fixed baselines.
- [x] Deliver the evidence-backed verdict, score ranges, kill tests, and prioritized cuts.

## Four-principle reality check — 2026-09-22

- [x] Treat the supplied load-bearing/earliness/theme/ambition critique as a Gate 1 review, not approval.
- [x] Verify the organiser-tech audit and 2026 novelty claims against primary sources.
- [x] Repair the design-principles evidence and add a plain-HTML visual audit.
- [x] Re-validate the documentary artifacts and preserve Gate 1 as pending.

## Assumptions and blockers

- The repository has an initial commit and is on `care-relay-adversarial-review`; all current Gate 1 changes remain uncommitted and unrelated changes must be preserved.
- No application code or automated test suite exists; the current work is product planning only.
- Mandarin and voice are proposed as accessibility input/output modes, not new clinical authorities.
- A qualified clinical reviewer and authorised protocol cannot be replaced by tooling. Without them, the prototype must remain a labelled research demonstration using scripted fixtures.
- The user confirmed WorkBuddy is the selected organiser product. WorkBuddy is the primary runtime and usage-proof path; CodeBuddy is not the default plan.

## Run log

- 2026-09-21: Started Gate 1. `git status` failed because the folder has no `.git` repository. Baseline tests are unavailable because the folder contains documentation only.
- 2026-09-21: Started independent adversarial review on branch `care-relay-adversarial-review`. The repository is now initialized but has no commits; all supplied project files are pre-existing and untracked. No application test suite is present, so the baseline is documentary evidence rather than executable tests.
- 2026-09-21: Wrote `docs/plans/urgent-advice-accessibility/03-planback-closure-contract.md` — specification and feasibility for the review's top two ranked changes. Analysis only; no implementation, no edits to `PLAN.md`.
- 2026-09-21: Applied PlanBack and the Closure Contract to `docs/PLAN.md` (§2 claims, §5 demo + §5.1 PlanBack + §5.2 hint ladder, §6 two-axis state model + §6.1 invariants, §7 critical path and effort, §9 Gates B and D, §11 scores). Corrected the single-ladder state model. Updated `01-product.md` with PlanBack, Closure Contract and fixture rules. Fixed the wireframe-2 transcript-ordering defect, added the hint ladder, rewrote wireframe 3 to a four-line patient view plus judge-facing ledger, added `05-planback-repair.html`, updated `mockups/index.html`. All six HTML files validated: well-formed, five internal links resolve.
- 2026-09-21: Reframed the hint ladder as **adaptive scaffolding with fading** at the user's request, after researching the evidence. Cognitive-training claims are now prohibited in `PLAN.md` §2 and §5.3, `01-product.md` and `00-status.md`: meta-analyses show no far transfer, and the FTC fined Lumosity $2m in 2016 for a decline-prevention claim. The mechanism is retained honestly as vanishing cues with errorless learning and spaced retrieval. Longitudinal cognitive monitoring recorded as out-of-scope research. Updated `mockups/02`. Re-validated all HTML.
- 2026-09-22: Resumed on `care-relay-adversarial-review`. Existing uncommitted Gate 1 files were preserved. Assumption: the pasted critique requests documentary incorporation and verification only; it does not approve Gate 1 or authorise architecture/implementation.
- 2026-09-22: Re-verified the four-principle audit. Corrected four overclaims: the nine-surface count is an internal taxonomy; the longitudinal scenarios are examples, not mandated implementations; broad follow-up/cohort monitoring and abstention are not new; and the new scope is not demonstrably effort-neutral. Preserved the fixed-card + NurseFirst kill test. Added `docs/organiser-tech-load-bearing-audit.html`; all seven HTML files parse and all local links resolve. Rendered the audit at the in-app browser's narrow viewport and inspected the header, mapping, decision and sources. Preview: `http://127.0.0.1:8765/docs/organiser-tech-load-bearing-audit.html`.

## Result

Gate 1 product specification, workaround audit, five HTML wireframes and one HTML design-principles audit are complete. Mandarin voice is technically feasible as a gated TRTC spike; no account access or clinical accuracy has been demonstrated. **Gate 1 (Product) was approved by the user on 25 September 2026, reopened and re-approved the same day for the timer removal and the expired-screen wording.** **Gate 2 (Architecture) approved 25 September 2026 on revision 2. Gate 3 (Program Design) approved 26 September 2026. Gate 4 (Slice plan) was drafted 28 September 2026 and awaits approval.**

The independent review is recorded in `docs/reviews/gate2-adversarial-review-round1.md`. Verdict: REFRAME CareRelay around closed-loop confirmation of urgent advice; make read-back repair the human-facing mechanism and keep truthful unresolved status as supporting safety infrastructure. Current mandatory organiser-usage proof is absent, so the project risks not being scored; the artifact-only evidence estimate is 39/100, realistic implemented target 73/100, optimistic ceiling 83/100. Gate 1 remains pending.

`03-planback-closure-contract.md` specifies the two ranked mechanisms and checks their feasibility. Findings: PlanBack (deterministic critical-field comparison, bounded repair) is high-feasibility, 18–30 h, no external dependency. The Closure Contract (immutable clinical deadline, two independent execution/evidence axes, five fault invariants) is medium-feasibility, 38–59 h. Combined build 56–89 h; with the baseline comparison, 76–124 h. Key honest finding: neither mechanism requires WorkBuddy — they are application logic. WorkBuddy's genuine dependency is the coordinator, the real tool call, its real failure event, and session resume. Both mechanisms carry pre-registered kill tests. The load-bearing assumption (that a fixed bilingual card does not perform equally) remains untested and should be tested first.

Both mechanisms are now written into `PLAN.md`. The single-ladder state model was replaced with two independent axes, which is a correctness fix, not a preference. A recall hint ladder (H0–H3) was added to PlanBack at the user's request: the prompt escalates so an older user is never stuck at a blank question, but **the level used is always recorded**, because a hint that contains the deadline or action turns a comprehension check into a reading test. Fixture rule added: no asset may name a real healthcare facility.

**Gate status: Gate 1 (Product) APPROVED 25 September 2026** (reopened and re-approved the same day). **Gate 2 (Architecture) APPROVED 25 September 2026** on revision 2. **Gate 3 (Program Design) APPROVED 26 September 2026** with two amendments at approval. Gate 4 (Slice plan) pending. Approval of a gate does not authorise the next one: Gate 2 authorises the Gate A access spike only, and Gate 3 authorises writing the two kill tests and the Gate 4 plan — **no product implementation code until Gate 4 is approved**. See `docs/plans/urgent-advice-accessibility/00-status.md` for the gate doc map — two supporting notes occupy the `02-` and `03-` filenames that Gates 2 and 3 will need.

## Run log — Gate 1 approval

- 2026-09-25: Added `.gitignore` and committed the Gate 1 reframe (`3900cd0`, 15 files, +1499/−62, no co-author trailer). Fast-forward merged `care-relay-adversarial-review` into `main`; both branches at `3900cd0`.
- 2026-09-25: **User approved Gate 1.** Recorded in `00-status.md`, with the unresolved risks carried forward explicitly rather than closed. Gate 2 (Architecture) is now the active gate.

## Gate 2 — Architecture (active)

- [x] Re-read all Gate 1 artifacts, PLAN.md, DESIGN_PRINCIPLES.md, research-workarounds.md and project conventions before designing.
- [x] Write `docs/plans/urgent-advice-accessibility/02-architecture.md` revision 1 (decisions D1–D10, module boundaries, endpoints, data model, three flows, external surfaces, Gate A spike questions).
- [x] Update `00-status.md` (Gate 2 in progress; file map; fresh-session notes).
- [x] Independent round-2 adversarial review (`gate2-adversarial-review-thorough.md`) — verdict APPROVE WITH CHANGES.
- [x] **Revision 2**: apply all three blocking defects and the eight secondary blocking changes.
- [x] Fix stale gate mirrors (`DESIGN_PRINCIPLES.md` §12, `03-planback-closure-contract.md`, `tasks/todo.md`, `PROGRESS.md` Result) and mockup numbering (01, 04).
- [x] Obtain explicit Gate 2 approval from the user on revision 2 — **APPROVED 25 September 2026**.
- [x] **Gate 1 reopened and re-approved (25 Sep)** for two amendments: H2's five-second timer removed (card stays until the patient hides it); expired-screen wording approved and softened. Files: `PLAN.md` §5.2/§5.2.1, `01-product.md`, `mockups/02`, `02-architecture.md` §7, `00-status.md`.
- [x] User accepted the 90–150 h effort estimate as achievable; Gate 3 still produces a real estimate.
- [ ] Gate A access spike (due 2026-09-26) — **overdue**. Credential check, one tool executed through the platform with an observed failure-event origin signal, one session resume. Gate 2 approval authorises the spike only, not implementation code.
- [x] **Gate 3 APPROVED 26 September 2026**, with two amendments made at approval: §6.1 adds the two reviewer-free kill conditions (they run first, before any participant work); §6.2 records the Option A + C decision.
- [x] **Clinical-review blocker resolved by decision (26 Sep):** user selected **Option A + C** — non-clinical comparator, fixture sourced verbatim from attributable published guidance.
- [ ] **Gate 2 D6 formally backtracked** — the comparator material loses its clinical content. D6's decision is unchanged; the material and the claim it supports are not.
- [ ] Write and run the two §6.1 kill tests (`test_planback_known_match_mismatch_uncertain` adversarial corpus; `test_urgent_path_precedes_planback`). **These precede all participant work and need no reviewer.**
- [ ] Select the Option C source and check licensing + Singapore applicability. **Precedes use.**
- [ ] Gate 4 — Slice plan. Must sequence the baseline comparison before the Closure Contract build, assign dates and stop conditions, and not remove the Closure Contract tests to make the schedule look green.

### Assumptions and blockers — Gate 2

- Gate A spike remains unrun; the tool-execution path (§3.3) and D8's dependency claim now depend on it.
- Round-2 review estimates 90–150 h for this architecture against the 56–89 h inherited, plus 20–35 h for the baseline. The user has **accepted this as achievable** (25 Sep); it remains unverified and Gate 3 must produce a real estimate.
- Gate 4 must sequence the baseline comparison (Gate B) **before** the Closure Contract build. `PLAN.md` §7 currently schedules it after — wrong order, to be corrected.
- ~~Stack default (Python 3.13 + FastAPI + SQLite) is reversible only **before the first domain-code commit**; environment check required before Slice 1 (AppControl/venv issue recorded in `AGENTS.md`).~~ **Superseded 30 September 2026.** The reversal was decided rather than deferred: the backend stays Python 3.13 + FastAPI + SQLite on **Render**, and the clinical frontend becomes a **Next.js app on Vercel** (`02-architecture.md` revision 3, decision D-1b). The environment check passed on 28 September 2026 and Slices 1 to 3 are committed, so the window this bullet describes has closed.
- D9 (scheduled reassessment) is **dropped**, with the P1 load-bearing cost stated. Not recoverable without Gate A plus a scenario and an estimate.

### Run log — Gate 2

- 2026-09-25: Drafted `02-architecture.md` revision 1 on branch `gate-2-architecture`; committed `1cb05c8`.
- 2026-09-25: User supplied an independent round-2 adversarial review (`gate2-adversarial-review-thorough.md`). Verdict APPROVE WITH CHANGES. Three blocking defects found: (1) §4's INSERT-only `attempts` table could not record a state transition, making acknowledgement writes either an illegal UPDATE or a silently-discarded INSERT — a false *negative* completion — and rendering four of seven fault sequences unwritable; (2) the tool-execution path was described five different ways, leaving the platform-failure claim unverifiable; (3) the D6 in-app card arm structurally could not measure the false-completion metric.
- 2026-09-25: Wrote revision 2 — attempts split into immutable identity + append-only transitions + callbacks with an ordering rule and a transaction boundary; §3.3 pins one normative tool path with a recorded failure-event origin; D6 replaced by an external between-subjects baseline with a pre-registered protocol (§9); added D11 (evidence provenance) and D12 (sticky expiry); added intake/clarification/options/acceptance/escalation endpoints and tables; added §8 non-functional surfaces (deployment, PDPA, logging redaction, degraded states, model-text boundary); added §7 expired-screen rendering flagged for Gate 1 sign-off; §10 restates the safety claims honestly; D9 dropped with its cost stated.
- 2026-09-25: Fixed stale mirrors and mockup numbering; committed `c01a442`.
- 2026-09-25: **Gate 1 reopened (user-instructed)** and re-approved. (a) H2's five-second timer replaced by "the card stays until the patient hides it" — no timers anywhere in the product; `dwell_seconds` recorded for the ledger only. New `PLAN.md` §5.2.1 records the rationale and the rules. (b) Expired-screen wording approved and rewritten after the user rejected the first draft as too blunt; five copy rules added so later edits do not drift back to a reproachful tone. User also accepted the 90–150 h estimate.
- 2026-09-25: Committed `77ea5ed` (Gate 1 reopening + mockup numbering + stale mirrors).
- 2026-09-25: **Gate 2 approved** on revision 2 by the user; committed `6c65f30` with the stale-header fix. **Corrected 30 September 2026:** this entry said `main` was behind `gate-2-architecture` and that the Gate 2 merge had not been pushed to `main` yet. Both are now meaningless: `gate-2-architecture` no longer exists as a branch, its commits are reachable from `main`, and `main` and `slice-3` are both pushed to `origin`.

### Run log — Gate 3 (2026-09-26)

- 2026-09-26: User asked whether Gate 3 was correct. Audit found the Gate 3 file (`03-program-design.md`) was untracked, its header still read "not approved", and it carried an unresolved clinical-review blocker in §8.3 that made the test plan unstartable for a reason unrelated to the software.
- 2026-09-26: Wrote `clinical-review-blocker.md` — a decision paper, not a gate. Finding: `CHALLENGE_REQUIREMENTS_JUDGING.md` §8 requires **no** clinical reviewer, so the blocker is self-imposed. Three tiers identified (mechanism / fixture / symptom→disposition); only Tier 3 is blocked and it was already cut from scope. Two of the three PlanBack kill conditions need **zero participants**: `test_planback_known_match_mismatch_uncertain` (does correct read-back get scored correct?) and `test_urgent_path_precedes_planback` (is the urgent route evaluated before the comprehension check?). These are the project's cheapest risk reduction and are now scheduled **before** any participant-facing work.
- 2026-09-26: Corrected the stale Gate 2 header (`02-architecture.md` now reads APPROVED 25 Sep, revision 2) and recorded the Gate 2 D6 backtrack in `00-status.md`: the comparator loses its clinical content, so D6's *decision* stands but the *material* and the claim it supports do not.
- 2026-09-26: **User selected Option A + C** for the blocker: (A) a non-clinical comparator, so the baseline comparison is licensed without a reviewer; (C) the fixture is sourced verbatim from attributable published guidance, so the content is traceable rather than invented. Option B (secure one reviewer, 48 h time-box) is not taken now and remains available if a fixture cannot be sourced cleanly.
- 2026-09-26: **Gate 3 approved** by the user, with two amendments made at approval: §6.1 adds the two reviewer-free kill conditions and their run order; §6.2 is rewritten for Option A + C. Test plan gained `test_urgent_path_precedes_planback` and a K1 corpus clause on `test_planback_known_match_mismatch_uncertain`. §8.3 marked resolved.
- 2026-09-26: Open items carried forward: the two kill tests are written but **not run**; the Option C source is **not selected**, so licensing and Singapore applicability are unchecked; the Gate A spike is **overdue** (due 25/26 Sep); Gate 4 is not started. Gate 3 approval authorises writing the kill tests and the Gate 4 plan — still no product implementation code.

## Gate 4 — Slice plan (drafted 2026-09-28)

- 2026-09-28: Resumed. Verified from `00-status.md` that **Gate 3 was already APPROVED on 26 September 2026** — the user's "start gate 4" was correct and no earlier gate was redone. Gate 4 is the only gate left.
- 2026-09-28: **Ran the two §6.1 kill conditions.** `spike/tests/test_kill_conditions.py` under Python 3.13.14: **15 tests, 0 failures**. Includes four `AssertionsHaveTeeth` defect-injection tests (surface-only comparator, always-uncertain comparator, unknown-as-mismatch, and both ordering defects), each confirmed to make its assertion fail. Result: **K1 and K2 both pass.** This is a deterministic-layer spike result with hand-supplied spans, not an implementation result, and it depends on Reading A.
- 2026-09-28: **Gate A re-verified per the user's instruction.** No `WORKBUDDY_API_KEY` or `WORKBUDDY_AGENT_ID` in the environment, no `.env`, no `workbuddy`/`codebuddy` package installed. Platform path is [unknown]-to-unavailable; Gate A remains overdue.
- 2026-09-28: **Slice 1's environment check passed.** Isolated venv created at `~/.workbuddy-ai/binaries/python/envs/default`; fastapi, uvicorn, pydantic, pytest and httpx installed and verified importable there. The intermittent AppControl block on stdlib venv creation (recorded in `AGENTS.md`) **did not fire**. Nothing installed into a user-managed environment.
- 2026-09-28: Wrote `docs/plans/urgent-advice-accessibility/04-slices.md`: **Gate 4 draft, awaiting approval.** ~~Thirteen slices~~ **Fourteen slices, Slice 0 to Slice 13, as of the 30 September 2026 renumber.** **Full Gate 3 scope** per the user's instruction. Constraint C1 honoured: the external card (old Slice 7, now **Slice 8**) completes before the Closure Contract build (old Slice 9, now **Slice 10**), with the Gate B kill test (old Slice 8, now **Slice 9**) between them. Slice 0 is the kill tests and the Option C source check, front-loaded because it is the largest available risk reduction at the lowest cost.
- 2026-09-28: Surfaced an ambiguity the Gate 3 contract leaves open and that the spike exposed: **which layer owns canonicalisation** in `compare_plan`. Two readings give materially different K1 results. Recorded as **ADR-0007 (proposed)** and pinned to Reading A in `04-slices.md` §1.1. It amends an approved Gate 3 signature and needs acknowledgment at Gate 4 approval.
- 2026-09-28: Recorded the **honest schedule arithmetic**: 102–169 h of planned work against 144 h available (solo, 18 days, 8 h/day, no slack). The plan fits only if almost nothing goes wrong. Written up as R1 rather than resolved by cutting scope — no Closure Contract test was removed, per the `03-program-design.md` §7 rule. If any slice overruns its window by more than 50%, the plan says to tell the user and replan rather than absorb the overrun by dropping tests.
- 2026-09-28: Created **`docs/adr/`** — index plus **ADR-0001 to ADR-0008** covering stack choice, the pure domain core, the append-only record, derived closure, server-generated idempotency keys, the external between-subjects baseline (including its 26 Sep clinical-content backtrack), the canonicalisation question, and the keep-full-scope decision. Populated from the approved gates rather than invented; the gate documents remain authoritative and the index says so.
- 2026-09-28: Updated `00-status.md` (Gate 4 draft state, the thirteen-slice checklist, Gate A re-verification, the two results already in hand) and `tasks/todo.md`.

### Open at Gate 4 drafting

- ~~**Gate 4 is not approved.**~~ **Approved 28 September 2026** — the user said "continue". Implementation is authorised slice by slice.
- **The Option C source is not selected** — licensing and Singapore applicability unchecked. Blocks Slice 5 only; Slices 1–2 proceed without it.
- **Gate A has not run**, and the plan now treats the labelled local-simulation fallback as the default.
- ~~**ADR-0007 is proposed**~~ **Accepted 28 September 2026** — Reading A: canonicalisation lives in `domain`, and the Gate 3 `compare_plan` signature is amended accordingly.
- **The schedule does not fit** (R1). The user kept the full scope deliberately; the risk is recorded rather than hidden.

## Slice 1 — tracer bullet (complete 2026-09-28)

- 2026-09-28: **Gate 4 approved** by the user with the instruction "continue". Recorded in `00-status.md` and `04-slices.md`. Two open sub-questions resolved under the recommendation given: ADR-0007 moves to `accepted` (canonicalisation lives in `domain`), and the Option C source stays a scheduling item that blocks Slice 5 only.
- 2026-09-28: **Slice 1 built.** `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json`, `tests/test_api.py`. Two routes plus a server-rendered patient page, wired end to end against a hardcoded episode. No database, no domain layer, no coordinator — those are Slices 2 and 3.
- 2026-09-28: **Proved it runs, not just that the tests pass.** `pytest tests/` → **11 passed**. Then `uvicorn` on `127.0.0.1:8137` and `curl` against health, episode creation, the patient projection and an unknown id (404). The four-line projection and the simulated label were read back from the live server.
- 2026-09-28: **Defect found by running it: the tests had missed it.** The first live render produced **"You or you must act now."** `PLAN.md` §6.1, `02-architecture.md` §7 and `01-product.md` all render line 2 as "You or *[named person]* must act now.", which is malformed when the owner is the patient. Fixed to "Myself must act now." with an `OWNER_DISPLAY` constant, and a regression test added. **Flagged as a divergence from three approved documents** rather than silently absorbed: the correction belongs in those documents at the next Gate 1 touch, and Slice 10 must implement whichever form they then carry.
- 2026-09-28: Confirmed C8 holds at Slice 1: no `http-equiv="refresh"`, no `<script>`, no CSS animation, transition or `@keyframes`. Nothing in the product hides itself or advances on a timer.
- 2026-09-28: Confirmed D11 holds at Slice 1: the simulated label is **inside** the serialized patient projection, not only in page chrome.
- 2026-09-28: Confirmed `POST /api/episodes` writes **no disposition**, per `02-architecture.md` §3.1. There is a test for it.
- 2026-09-30: **Corrected.** The line 2 wording recorded above was itself malformed. `demo/fixture.py` now carries `SELF_OWNER_SENTENCE = "You must act now."`, mirroring `domain.rules.patient_lines` for a self owner (Slice 2 owns this rule) and agreeing with `fixtures/scripted_episode.json`, whose `next_owner_id` is `patient`. `OWNER_DISPLAY` is gone. Verified by running the app: line 2 renders "You must act now." on the live page, and all 332 tests pass.

### Next

**Slice 4: PlanBack end to end, with the hint ladder and bounded repair.** `POST /restatements`,
`/restatements/{rid}/repairs`, `/hint-events`, `/transcript-confirmations`; the coordinator
extracts raw spans and `domain` resolves and compares (Reading A, pinned there); H0 to H3 recorded,
H2 stays until the patient hides it, H3 is `not_recalled` and never a pass, two repairs maximum and
a third routes to the human path (C6).

**Carried into Slice 4 and later:** the Option C source (blocks Slice 5), F5 at Slice 6, F6 at
Slice 5, F4 and the §2.2 amendment at Slice 10 (Slice 9 before the 30 September 2026
renumber), and Gate A (still unrun, fallback recorded for
Slice 6). From the Slice 3 review: O2's typed lock error and O5 at Slice 6, O7 at Slice 5, O8 at
Slice 11 (Slice 10 before the renumber). O1, O3, O4 and O6 were closed by the remediation below
and O2's docstring half with them.
Slice 3 is **committed** on branch `slice-3` and fast-forwarded into `main`, as is the
remediation.

- 2026-09-30: **Slice 2 complete and adversarially reviewed**; remediated the same day (two
  blockers, five scanner evasions, a corpus widened against self-serving entries). 240 tests pass.
- 2026-09-30: **Slice 3 complete.** `src/carerelay/state.py` and `tests/test_state.py`. Thirteen
  tables on SQLite with WAL and a busy timeout; every table refuses `UPDATE` and `DELETE` by
  trigger, proven with a separate raw connection and a control case that drops the triggers. The
  D11 `CHECK` proven independently of the Python guard. R6 proven: two connections in two threads
  on one callback key produce exactly one applied receipt, one recorded duplicate and one
  transition, and an injected crash leaves neither a receipt nor a transition. Expiry is sticky
  across a clock regression and a premature event is refused. **70 new tests; 310 pass.** Eleven
  mutations, each applied alone, all eleven RED, every file restored with an md5 check. The Slice 2
  review's `source_ref` gap is closed in `tests/test_domain.py`. Ten readings of the approved
  documents are flagged in `00-status.md`; reading 6 (the snapshot reports the expiry event for the
  current disposition version) wants an explicit yes or no.
- 2026-09-30: **Slice 3 remediation: the blocking review finding is closed.** O1 to O4 and O6 of the
  Slice 3 review, plus the F9 minor finding. `PRAGMA recursive_triggers = ON` in
  `SqliteEpisodeStore.__init__`, which makes `INSERT OR REPLACE` fire the `BEFORE DELETE` triggers
  and closes the hole that rewrote `dispositions.clinical_deadline_utc`; five fail-capable tests for
  the constraints the review found untested; a three-delivery test proving SQLite's NULL-distinctness
  assumption; `trim(source_ref) <> ''` added to the D11 `CHECK` with the Python guard widened to
  match. Two docstrings that claimed more than the mechanism delivers were corrected. **22 new tests;
  332 pass** (89 domain, 141 boundaries, 11 api, 91 state). Eight mutations, each applied alone to an
  anchor asserted to occur exactly once, each RED on exactly its own test and each reverted with an
  md5 check. A schema-level `BEFORE INSERT` guard was measured and rejected because it also refuses
  the harmless `INSERT OR IGNORE`. **Committed on `slice-3` and fast-forwarded into `main`**, in two
  commits: the code, then the record.

## Gate reopening: 2026-09-30

- 2026-09-30: **Gates 2, 3 and 4 reopened on the user's instruction**, to encode Decisions D-A to D-D
  and hosting Decision D-1b, and **re-approved the same day**. **Operational record only:**
  `00-status.md` is the authority for gate state; this entry summarises it and does not replace it.
- **Amended:** `02-architecture.md` (D1, D8, new D13, section 6, section 8 four rows, sections 11 and
  12), `03-program-design.md` (section 1, section 2 file list, section 3 closing line), `04-slices.md`
  (renumbered to fourteen slices, one merge, one required slice, one conditional slice, effort
  recomputed, cut order updated, usage proof moved to Slice 4, templates drift resolved), and
  `adp-and-deployment-impact.md` (the five errors corrected, plus two imprecise claims the review
  named).
- **Mirrors updated:** `AGENTS.md` sections 3 and 8, `docs/PLAN.md` sections 6, 7 and 10,
  `tasks/todo.md`, `00-status.md`.
- **Committed to `main` and pushed to `origin` on 30 September 2026.** Gates 2, 3 and 4 were
  **re-approved** the same day, so implementation is authorised again. The answer is recorded in
  `00-status.md` and at the end of `04-slices.md`.
- **No product code was written.** Slice 4 remains next and remains blocked on the same two items as
  before: the Option C source for Slice 5, and Gate A for Slice 6.
