# CareRelay reframe and accessibility plan

- [x] Re-read the challenge, judging criteria, current PLAN.md, and case-study boundaries.
- [x] Classify every blocker as non-substitutable gate, honest workaround, or scope reduction.
- [x] Confirm official feasibility of Mandarin ASR/TTS and voice integration.
- [x] Define Gate 1 problem, success metric, announcement, and screens.
- [x] Create grayscale HTML wireframes for recommendation, understanding/barrier repair, unresolved handoff, and reassessment/abstention.
- [x] Validate HTML structure and links.
- [x] Obtain Gate 1 (Product) approval — granted 25 September 2026.

## Review

- Gate 1 artifacts render at desktop width and expose all intended headings, controls and bilingual labels.
- Voice remains optional push-to-talk with visible transcript and text fallback.
- No implementation or clinical claim was created before Gate approval.
- **Gate 1 approval was granted on 25 September 2026.** Gate 2 (Architecture) is now active.

## Independent adversarial review

- [x] Extract exact rubric, submission, deadline, and sponsor constraints.
- [x] Audit current claims and mockups against demonstrated evidence.
- [x] Research direct competitors, Singapore services, and simple substitutes.
- [x] Stress-test Mei/Mandarin respiratory and unresolved-handoff stories.
- [x] Compare three directions and fixed baselines.
- [x] Rank three builds, three cuts, and three evidence questions.
- [x] Record final evidence-backed scores and review conclusions.

### Review conclusion

- Reframe around PlanBack plus a narrow Closure Contract; do not lead with the ledger.
- The Mei/Mandarin respiratory story is a convenient feature container, not an evidence-backed best scenario.
- Cut Mandarin voice, broad respiratory intake and patient-facing ledger detail from the judged slice.
- Gate 1 and Gate 2 were approved on 25 September 2026; Gates 3 and 4 remain unapproved, so no implementation is authorised.

## PlanBack and Closure Contract specification

- [x] Define PlanBack precisely: confirmed restatement, deterministic critical-field comparison, bounded repair.
- [x] Identify the wireframe defect where the draft transcript is evaluated before confirmation.
- [x] Define the Closure Contract: two independent axes, immutable deadline, five fault invariants, closure rules.
- [x] Assess feasibility, effort and dependencies for both.
- [x] Record the honest WorkBuddy dependency boundary.
- [x] Propose concrete edits to `PLAN.md` without applying them.
- [x] Add the recall hint ladder (H0–H3) with the level always recorded.
- [x] Apply PlanBack and the Closure Contract to `PLAN.md`.
- [x] Update `01-product.md` and the wireframes; validate all HTML.
- [x] Obtain Gate 1 (Product) approval — 25 September 2026.
- [ ] Run the card-versus-PlanBack baseline comparison before building anything else. **Gate 4 must sequence this first** (round-2 review).

## Four-principle reality check — 2026-09-22

- [x] Inspect the existing design-principles draft, plan pointer, status note and dirty worktree.
- [x] Re-verify organiser requirements, platform surfaces and current competitors from primary sources.
- [x] Correct unsupported exclusivity, novelty, effort and platform claims without changing the unapproved Gate 1 scope.
- [x] Replace the broken inline SVG placeholder with one self-contained HTML audit.
- [x] Validate the HTML, links and documentary consistency; record the result in `PROGRESS.md`.

## Gate 2: Architecture (approved); Gate 3: Program Design (in progress)

- [x] Write `02-architecture.md` revision 1: D1–D10, module boundaries, endpoints, data, flows, external surfaces, Gate A spike questions.
- [x] Independent round-2 adversarial review (`docs/reviews/gate2-adversarial-review-thorough.md`) — verdict APPROVE WITH CHANGES, three blocking defects.
- [x] Apply all blocking changes as revision 2: attempt transitions, pinned tool path, external between-subjects baseline, missing endpoints/tables, D9 dropped, degraded states, D11/D12 invariants, expired screen, honest claim restatement.
- [x] Fix stale mirrors and mockup numbering.
- [x] **Gate 1 reopened and re-approved (25 Sep):** H2 timer removed (card stays until the patient hides it); expired-screen wording approved and softened.
- [x] User review: **Gate 2 APPROVED 25 September 2026** (revision 2).
- [ ] Run Gate A access spike by 2026-09-26 (spike only, no implementation code).
- [x] Draft Gate 3 program design (files, types, call stacks, test plan), including a build estimate; `03-program-design.md`, 26 September 2026.
- [ ] Review and explicitly approve Gate 3, or revise the draft.
- [ ] Draft Gate 4 only after Gate 3 approval; sequence the card comparison before the Closure Contract build.
- [x] **Gate 3 approved 26 September 2026** — recorded in `00-status.md` with both amendments.
- [x] **Run the two §6.1 kill conditions** — K1 and K2 both PASS, 15 tests, 0 failures (28 Sep).
- [x] Gate A re-verification requested by the user — no credentials, no `.env`, no SDK package; platform path [unknown]-to-unavailable.
- [x] **Slice 1 environment check** — FastAPI stack installs into an isolated venv; AppControl block did not fire.
- [x] Draft Gate 4 (`04-slices.md`): 13 slices, **full scope** per the user's instruction, C1 satisfied.
- [x] Create `docs/adr/` — index plus ADR-0001 to ADR-0008.
- [x] Update `00-status.md`, `PROGRESS.md`, `tasks/todo.md` for the Gate 4 draft.
- [x] **Obtain Gate 4 approval** — granted 28 September 2026 ("continue"). No code before it.
- [x] Resolve ADR-0007 (canonicalisation layer) at Gate 4 approval — **Reading A accepted**, ADR now `accepted`.
- [x] **Slice 1 complete** — tracer bullet runs; 11 tests pass; curl-verified live; documented defect found and fixed.
- [ ] Select the Option C source; check licensing and Singapore applicability. **Precedes Slice 5.**
- [x] **Slice 2 complete**: pure domain core plus an enforcing import boundary; boundary check seen red then green; 240 tests pass after the adversarial review and remediation (30 Sep). Review: `docs/reviews/slice2-adversarial-review.md`
- [x] **Slice 2 adversarial review + remediation** (30 Sep). Verdict: exit contract met with named caveats. Two blockers fixed (a stale deadline rendered to the patient, and a false CRLF claim in `00-status.md`); the boundary scanner's five evasions closed; `project_attempt` now validates every row; the K1 corpus widened with independently-chosen phrasings.
- [x] **Slice 3 complete** (30 Sep): the append-only SQLite record. Thirteen tables, every one refusing UPDATE and DELETE by trigger; the D11 `CHECK` proven independently of the Python guard; the callback representation proven atomic under two concurrent writers and under an injected crash; the `source_ref` mutation gap from the Slice 2 review closed. 69 new tests, 310 pass. Eleven mutations each seen RED and each reverted with an md5 check.

### Open from the Slice 2 review: deferred to the slice where each becomes live

**Standing instruction (user, 30 September 2026):** these are not to be decided now. Each is decided (or put to the user as a question) **at the slice where it first becomes live**, and the decision is recorded in `00-status.md` in that slice's section. Do not silently implement one of these while building an earlier slice.

| # | Open item | Decided at | Why that slice |
|---|---|---|---|
| F4 | **`closed_with_evidence` must render twice over.** It is reachable from real evidence *and* from a recorded human acceptance with no evidence (`care_evidenced = False`). `patient_lines` raises for both today, so the acceptance path that `POST /acceptances` produces has no patient rendering at all. The two cases are not the same fact and must not share a rendering | **Slice 9** | Slice 9 owns the Closure Contract rendering: `derive_closure` complete, `POST /acceptances`, and the four-line unresolved/expired renderings. The acceptance endpoint does not exist before it |
| F5 | **Decide what `simulated` means.** It is currently `not care_evidenced`, conflating "this episode is a simulation" with "care is not evidenced". The code implements the D11 rule as written, so this is a semantics decision, not a bug fix | **Slice 6**, made visible at **Slice 11** | Slice 6 introduces the simulated provider and the `simulated: true` label; Slice 11 shows the simulated label in the judge ledger. Ask the user at Slice 6, before the label is written anywhere a judge will read |
| F6 | **Decide the owner after an escalation.** `action_owner_id` ignores `escalation_id`, so an escalated episode still names the patient. I4 allows "an explicit human service" as the acting party, and the projection cannot express it | **Slice 5**, re-checked at **Slice 9** | Slice 5 records escalations (`POST /escalations`); Slice 9 is where the owner is rendered. Decide when the escalation is first recorded |
| §2.2 | **Amend `03-planback-closure-contract.md` section 2.2.** The `closed_with_evidence` row ("evidence >= documented, **or** an explicit human acceptance is recorded") and the `expired_unresolved` row ("deadline passed with no evidence") overlap on acceptance plus past-deadline. The document states no order; the implementation puts expiry first, for I2 and because the other order is unrenderable | **Slice 9** | The amendment is the documented form of whatever F4 decides. It is a document edit, not code, and it should follow the Slice 9 rendering decision so the two stay consistent |
| `source_ref` | ~~**Record the `source_ref` mutation gap.**~~ **SETTLED at Slice 3, 30 Sep.** `mutated_closure` now carries two named flags, one per half of the D11 guard, and a test requires each half to be independently provable. The new test fails when the flag is reverted to the Slice 2 form. No product code changed | ~~Slice 3~~ done | Closed where the constraint it proves was written |

Reminder: the `00-status.md` section for the slice that resolves an item must state the decision and its reason, so a fresh session can see it was made deliberately and not overlooked.

## Gate 4 — slice plan (APPROVED 2026-09-28)

Thirteen slices, full Gate 3 scope, in `docs/plans/urgent-advice-accessibility/04-slices.md`.

- [ ] Slice 0 — kill tests (**PASS** 28 Sep) + Option C source (**open**)
- [x] **Slice 1 — tracer bullet: episode to four lines, hardcoded** (28 Sep)
- [x] **Slice 2: pure domain core + enforcing import boundary** (30 Sep; adversarially reviewed and remediated the same day)
- [x] **Slice 3: append-only state + Closure Contract invariants** (30 Sep; 69 new tests, 310 pass)
- [ ] Slice 4 — PlanBack end to end, hint ladder, bounded repair ← **next**
- [ ] Slice 5 — judged fixture + abstention path (blocked on the Option C source)
- [ ] Slice 6 — action path, simulated provider, platform call + Gate A decision
- [ ] Slice 7 — baseline instrument: the external card (C1, parallel)
- [ ] Slice 8 — Gate B: run the comparison (**kill test**)
- [ ] Slice 9 — Closure Contract in full (starts only after the kill test)
- [ ] Slice 10 — fault harness + seven sequences
- [ ] Slice 11 — judge ledger + usage proof
- [ ] Slice 12 — submission assets

### Standing constraints for every slice

- Prove it works — run it, curl it, or browser-test it, and **show the user the result**. An agent summary is not proof.
- Check it off in `00-status.md`, which is the only authority for slice state.
- Ask: "Continue to slice N+1, or re-steer?"
- Real tests only. Never a test that passes against the pre-change code; never weaken a test to reach green.
- **R1:** any slice overrunning its window by more than 50% means telling the user and replanning — not absorbing the overrun by quietly dropping tests.

## Open risks at Gate 4

| # | Risk | Where |
|---|---|---|
| R1 | **Schedule does not fit** — 102–169 h against 144 h available, solo, 18 days | `04-slices.md` §5, §6 |
| R2 | **Gate A never passes** — platform path unproven, spike overdue | `04-slices.md` §6, Slice 6 |
| R3 | **Recruitment fails** — no dyads means no Gate B | `04-slices.md` §6, Slice 7–8 |
| R4 | **Option C source cannot be cleared** | `04-slices.md` §6, Slice 0/5 |
| R5 | **Reading B is the real contract** — K1 weakens | `04-slices.md` §1.1, ADR-0007 |
| R6 | ~~**Callback atomicity fails** — duplicates lost~~ **Resolved at Slice 3, 30 Sep.** `BEGIN IMMEDIATE` plus the busy timeout serialises the lookup and the insert; two connections in two threads on one key yield one applied receipt and one recorded duplicate. Gate 2 was not backtracked | `04-slices.md` §6, Slice 3 |
| R7 | **Effort estimate is wrong** — 90–150 h unverified | `04-slices.md` §6 |

## Review conclusion — round 2

- Revision 1 was not approvable: attempt state was unwritable, the tool path was described five ways, and the baseline arm could not measure the success metric.
- Revision 2 fixes all three; D9 is cut with its cost stated; the survivor set is PlanBack, the Closure Contract, the fault harness, the four-line screen, the ledger and the baseline comparison.
