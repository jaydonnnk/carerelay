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

Gate 1 product specification, workaround audit, five HTML wireframes and one HTML design-principles audit are complete. Mandarin voice is technically feasible as a gated TRTC spike; no account access or clinical accuracy has been demonstrated. **Gate 1 (Product) was approved by the user on 25 September 2026.** Gate 2 (Architecture) is in progress.

The independent review is recorded in `docs/plans/urgent-advice-accessibility/02-adversarial-review.md`. Verdict: REFRAME CareRelay around closed-loop confirmation of urgent advice; make read-back repair the human-facing mechanism and keep truthful unresolved status as supporting safety infrastructure. Current mandatory organiser-usage proof is absent, so the project risks not being scored; the artifact-only evidence estimate is 39/100, realistic implemented target 73/100, optimistic ceiling 83/100. Gate 1 remains pending.

`03-planback-closure-contract.md` specifies the two ranked mechanisms and checks their feasibility. Findings: PlanBack (deterministic critical-field comparison, bounded repair) is high-feasibility, 18–30 h, no external dependency. The Closure Contract (immutable clinical deadline, two independent execution/evidence axes, five fault invariants) is medium-feasibility, 38–59 h. Combined build 56–89 h; with the baseline comparison, 76–124 h. Key honest finding: neither mechanism requires WorkBuddy — they are application logic. WorkBuddy's genuine dependency is the coordinator, the real tool call, its real failure event, and session resume. Both mechanisms carry pre-registered kill tests. The load-bearing assumption (that a fixed bilingual card does not perform equally) remains untested and should be tested first.

Both mechanisms are now written into `PLAN.md`. The single-ladder state model was replaced with two independent axes, which is a correctness fix, not a preference. A recall hint ladder (H0–H3) was added to PlanBack at the user's request: the prompt escalates so an older user is never stuck at a blank question, but **the level used is always recorded**, because a hint that contains the deadline or action turns a comprehension check into a reading test. Fixture rule added: no asset may name a real healthcare facility.

**Gate status: Gate 1 (Product) is APPROVED as of 25 September 2026.** Gates 2–4 pending. Approval of the product specification does not authorise implementation — Gate 2 must still be approved before any code is written. See `docs/plans/urgent-advice-accessibility/00-status.md` for the gate doc map — two supporting notes occupy the `02-` and `03-` filenames that Gates 2 and 3 will need.

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
- [ ] Obtain explicit Gate 2 approval from the user on revision 2.
- [x] **Gate 1 reopened and re-approved (25 Sep)** for two amendments: H2's five-second timer removed (card stays until the patient hides it); expired-screen wording approved and softened. Files: `PLAN.md` §5.2/§5.2.1, `01-product.md`, `mockups/02`, `02-architecture.md` §7, `00-status.md`.
- [x] User accepted the 90–150 h effort estimate as achievable; Gate 3 still produces a real estimate.
- [ ] Run the Gate A access spike (due 2026-09-26) — credential check, one tool executed through the platform with an observed failure-event origin signal, one session resume. Approval of Gate 2 authorises the spike only, not implementation code.

### Assumptions and blockers — Gate 2

- Gate A spike remains unrun; the tool-execution path (§3.3) and D8's dependency claim now depend on it.
- Round-2 review estimates 90–150 h for this architecture against the 56–89 h inherited, plus 20–35 h for the baseline. The user has **accepted this as achievable** (25 Sep); it remains unverified and Gate 3 must produce a real estimate.
- Gate 4 must sequence the baseline comparison (Gate B) **before** the Closure Contract build. `PLAN.md` §7 currently schedules it after — wrong order, to be corrected.
- Stack default (Python 3.13 + FastAPI + SQLite) is reversible only **before the first domain-code commit**; environment check required before Slice 1 (AppControl/venv issue recorded in `AGENTS.md`).
- D9 (scheduled reassessment) is **dropped**, with the P1 load-bearing cost stated. Not recoverable without Gate A plus a scenario and an estimate.

### Run log — Gate 2

- 2026-09-25: Drafted `02-architecture.md` revision 1 on branch `gate-2-architecture`; committed `1cb05c8`.
- 2026-09-25: User supplied an independent round-2 adversarial review (`gate2-adversarial-review-thorough.md`). Verdict APPROVE WITH CHANGES. Three blocking defects found: (1) §4's INSERT-only `attempts` table could not record a state transition, making acknowledgement writes either an illegal UPDATE or a silently-discarded INSERT — a false *negative* completion — and rendering four of seven fault sequences unwritable; (2) the tool-execution path was described five different ways, leaving the platform-failure claim unverifiable; (3) the D6 in-app card arm structurally could not measure the false-completion metric.
- 2026-09-25: Wrote revision 2 — attempts split into immutable identity + append-only transitions + callbacks with an ordering rule and a transaction boundary; §3.3 pins one normative tool path with a recorded failure-event origin; D6 replaced by an external between-subjects baseline with a pre-registered protocol (§9); added D11 (evidence provenance) and D12 (sticky expiry); added intake/clarification/options/acceptance/escalation endpoints and tables; added §8 non-functional surfaces (deployment, PDPA, logging redaction, degraded states, model-text boundary); added §7 expired-screen rendering flagged for Gate 1 sign-off; §10 restates the safety claims honestly; D9 dropped with its cost stated.
- 2026-09-25: Fixed stale mirrors and mockup numbering; committed `c01a442`.
- 2026-09-25: **Gate 1 reopened (user-instructed)** and re-approved. (a) H2's five-second timer replaced by "the card stays until the patient hides it" — no timers anywhere in the product; `dwell_seconds` recorded for the ledger only. New `PLAN.md` §5.2.1 records the rationale and the rules. (b) Expired-screen wording approved and rewritten after the user rejected the first draft as too blunt; five copy rules added so later edits do not drift back to a reproachful tone. User also accepted the 90–150 h estimate.
