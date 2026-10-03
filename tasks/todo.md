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
- Gate 1, Gate 2 (revision 3), Gate 3 and Gate 4 were all approved by 30 September 2026, so implementation is authorised slice by slice, and each slice still stops for the user's "continue, or re-steer?"

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
- [x] **Option C source check run 1 October 2026: no source clears.** MOH clause 11 and HealthHub clause 12.1 both require prior written permission, and the UK Open Government Licence route fails Singapore applicability. The check also found that Option C **contradicts** Option A, because a fixture of fictional entities cannot be quoted verbatim from any published guidance. The user answered "drop", so `03-program-design.md` section 6.2 now carries Option A alone and **Gate 3 is reopened** pending re-approval. Detail in `00-status.md`.
- [x] **Slice 2 complete**: pure domain core plus an enforcing import boundary; boundary check seen red then green; 240 tests pass after the adversarial review and remediation (30 Sep). Review: `docs/reviews/slice2-adversarial-review.md`
- [x] **Slice 2 adversarial review + remediation** (30 Sep). Verdict: exit contract met with named caveats. Two blockers fixed (a stale deadline rendered to the patient, and a false CRLF claim in `00-status.md`); the boundary scanner's five evasions closed; `project_attempt` now validates every row; the K1 corpus widened with independently-chosen phrasings.
- [x] **Slice 3 complete** (30 Sep): the append-only SQLite record. Thirteen tables, every one refusing UPDATE and DELETE by trigger; the D11 `CHECK` proven independently of the Python guard; the callback representation proven atomic under two concurrent writers and under an injected crash; the `source_ref` mutation gap from the Slice 2 review closed. 69 new tests, 310 pass. Eleven mutations each seen RED and each reverted with an md5 check.
- [x] **Slice 3 remediation** (30 Sep, same day): the review's blocking finding and four more closed before Slice 4 began. `PRAGMA recursive_triggers = ON`, so `INSERT OR REPLACE` is refused on every connection this module opens; five fail-capable tests for the previously untested constraints; the NULL-distinctness assumption proven with its own control; `trim(source_ref) <> ''` added to the D11 `CHECK` and the Python guard widened to match. 22 new tests, 332 pass, eight mutations each RED on exactly its own test. **Committed on `slice-3` and merged into `main`.** O5, O2 and F5 closed at Slice 6 on 3 October 2026; O7 at Slice 5; O8 at Slice 11.

### Open from the Slice 2 review: deferred to the slice where each becomes live

**Standing instruction (user, 30 September 2026):** these are not to be decided now. Each is decided (or put to the user as a question) **at the slice where it first becomes live**, and the decision is recorded in `00-status.md` in that slice's section. Do not silently implement one of these while building an earlier slice.

| # | Open item | Decided at | Why that slice |
|---|---|---|---|
| F4 | **`closed_with_evidence` must render twice over.** It is reachable from real evidence *and* from a recorded human acceptance with no evidence (`care_evidenced = False`). `patient_lines` raises for both today, so the acceptance path that `POST /acceptances` produces has no patient rendering at all. The two cases are not the same fact and must not share a rendering | **Slice 10** | Slice 10 owns the Closure Contract rendering: `derive_closure` complete, `POST /acceptances`, and the four-line unresolved/expired renderings. The acceptance endpoint does not exist before it |
| F5 | **Decide what `simulated` means.** It is currently `not care_evidenced`, conflating "this episode is a simulation" with "care is not evidenced". The code implements the D11 rule as written, so this is a semantics decision, not a bug fix | **CLOSED 3 October 2026** | Decided with the user: **split, always-simulated + `care_evidenced`**. `DEPLOYMENT_SIMULATED = True` in `domain/models.py`; `derive_closure` uses it. Mutation reverts to exactly 2 RED. The ledger still shows `simulated: true` after a documented row, which is the honest fact |
| F6 | **Decide the owner after an escalation.** `action_owner_id` ignores `escalation_id`, so an escalated episode still names the patient. I4 allows "an explicit human service" as the acting party, and the projection cannot express it | **Slice 5**, re-checked at **Slice 10** | Slice 5 records escalations (`POST /escalations`); Slice 10 is where the owner is rendered. Decide when the escalation is first recorded |
| §2.2 | **Amend `03-planback-closure-contract.md` section 2.2.** The `closed_with_evidence` row ("evidence >= documented, **or** an explicit human acceptance is recorded") and the `expired_unresolved` row ("deadline passed with no evidence") overlap on acceptance plus past-deadline. The document states no order; the implementation puts expiry first, for I2 and because the other order is unrenderable | **Slice 10** | The amendment is the documented form of whatever F4 decides. It is a document edit, not code, and it should follow the Slice 10 rendering decision so the two stay consistent |
| `source_ref` | ~~**Record the `source_ref` mutation gap.**~~ **SETTLED at Slice 3, 30 Sep.** `mutated_closure` now carries two named flags, one per half of the D11 guard, and a test requires each half to be independently provable. The new test fails when the flag is reverted to the Slice 2 form. No product code changed | ~~Slice 3~~ done | Closed where the constraint it proves was written |

Reminder: the `00-status.md` section for the slice that resolves an item must state the decision and its reason, so a fresh session can see it was made deliberately and not overlooked.

### Open from the Slice 5 build: deferred to the slice where each becomes live

**Same standing instruction (user, 30 September 2026).** Decided, or put to the user as a question, at the slice where each first becomes live, and recorded in `00-status.md` in that slice's section.

| # | Open item | Decided at | Why that slice |
|---|---|---|---|
| F6-render | **`patient_lines` does not follow the escalation.** F6 moved `action_owner_id` to the human path, but line 2 is still composed from `disposition.next_owner_id`, so a derived patient screen would say "You must act now." while the ledger says the nurse line acts. **Latent today:** every HTTP path returns hardcoded fixture lines, so nothing derived is rendered. Fixing it needs approved copy for a human-service owner on line 2, which is a Gate 1 touch | **Slice 10** | Slice 10 owns the Closure Contract rendering and re-checks F6. Authoring the copy now would repeat the `COORDINATOR_FALLBACK_TEXT` situation, which cost a Gate 1 reopen |

### Open from the Slice 4 review: deferred to the slice where each becomes live

**Same standing instruction as above (user, 30 September 2026).** Decided, or put to the user as a question, at the slice where each first becomes live, and recorded in `00-status.md` in that slice's section. No later slice may implement one early and silently. Full note: `docs/reviews/slice4-adversarial-review.md`.

| # | Open item | Decided at | Why that slice |
|---|---|---|---|
| B3 | **The intake recognition rule is a bare substring test.** A complaint that contains the bound phrase is recognised even when it also carries a red-flag symptom, negates the phrase, or asks about someone else. Measured 1 October 2026. No clinical branch is derived from free text and the disposition is the same non-clinical fixture plan in every case, so the demo does not mis-triage; the question is whether the fixture-bound rule should require an exact match, or whether red-flag and negation handling should be built at all | **Slice 5** | Slice 5 is where the judged fixture and the abstention path land. Binding a sourced complaint with a substring test is the same defect at larger size, and red-flag detection is clinical content that needs a reviewer. Do not author it before one exists |
| `COORDINATOR_FALLBACK_TEXT` | **Authored patient-facing copy with no approved source.** `api.py` shows "We could not check that answer just now. Your plan has not changed." when the coordinator cannot answer. The review judged it acceptable for a labelled research demonstration because it names no symptom, urgency, route or deadline and asserts only that the check did not happen. **CLOSED 1 October 2026 by the Gate 1 touch.** `01-product.md` gained an "Approved patient-facing copy" subsection carrying exactly this string. Editing an approved gate document reopens that gate (`AGENTS.md` section 5), so Gate 1 is reopened and awaits re-approval | **Closed at the Gate 1 touch of 1 October 2026** | The fallback is patient-visible and the Gate 1 document owns patient-facing copy. Slice 7 is the public deployment, so it had to be settled before a judge could read it |
| NF1 | **A second episode's intake raises an unhandled `sqlite3.IntegrityError`.** `service.intake` calls `state.register_policy_version` unconditionally and that store method is a plain `INSERT`, so the second episode assessed on one database fails. Latent today: `POST /api/episodes` can only create the demo episode, so no HTTP path reaches it | **Slice 7** | Slice 7 deploys with a persistent disk, and is the first point where the product holds more than one episode |
| NF2 | **Malformed enum values return HTTP 500, not a typed refusal.** `hint_level: "H9"` and `event: "auto_hide"` both reach an uncaught `ValueError`. No row is written, so it is not fail-open | **Slice 7** | Slice 7 adds the auth dependency and the error surface; the refusals should be closed in the same pass |
| NF3 | **The hint route's `PolicyViolation -> 422` branch is unreachable.** `service.hint_state` resets the level before `hint_transition` can refuse it, so the handler never fires | **Slice 7** | Same pass as NF2: either delete the branch or route the enum construction through a domain validator that raises `PolicyViolation` |
| NF4 | **`transcript_confirmed` is recorded true from an unverified confirmation id** on text and chip rounds. Only voice checks the digest and the stored record, so the ledger can assert a confirmation that never happened | **Slice 7** | Slice 7 writes the judge ledger view, so the record's honesty should be settled before it is rendered to a judge |
| NF5 | **The coordinator docstrings overclaim the boundary.** `AllowedPlanValues` carries `permitted_action_ids` and `permitted_owner_ids`, which contain the expected action and owner, so the honest claim is that the coordinator cannot determine **which** candidate is expected. It never sees the `Disposition`, which is the load-bearing half | **CLOSED 3 October 2026** | `coordinator.py` docstrings now state the honest boundary: the expected values are in the sets, and what is hidden is the pairing and the `Disposition`. Pinned by `TestTheExtractionBoundarySaysWhatItHides` |
| NF6 | **"Payloads are redacted from application logs" has nothing to verify against.** There is no logging in `src/`, and `events.payload` does hold raw confirmed patient text | **The slice that first introduces logging** | Build the redaction with the logs, not after them |

Reminder: the `00-status.md` section for the slice that resolves an item must state the decision and its reason, so a fresh session can see it was made deliberately and not overlooked.

## Gate 4: slice plan (APPROVED 2026-09-28; reopened and **RE-APPROVED 2026-09-30**)

**Fourteen slices, Slice 0 to Slice 13**, full Gate 3 scope, in `docs/plans/urgent-advice-accessibility/04-slices.md`. **Renumbered 30 September 2026:** old Slice 7 became 8, old 8 became 9, old 9 became 10, old 10 became 11, and old Slices 11 and 12 merged into Slice 12. **Slice 7 is new** (public deployment, Next.js frontend, auth) and **Slice 13 is new and conditional** (ADP interpretation surface, default do not run). **Gates 2, 3 and 4 are APPROVED in `00-status.md` as of 30 September 2026.**

- [ ] Slice 0: kill tests (**PASS** 28 Sep) + Option C source (**open**)
- [x] **Slice 1: tracer bullet, episode to four lines, hardcoded** (28 Sep)
- [x] **Slice 2: pure domain core + enforcing import boundary** (30 Sep; adversarially reviewed and remediated the same day)
- [x] **Slice 3: append-only state + Closure Contract invariants** (30 Sep; 69 new tests, 310 pass at completion, 332 after the remediation the same day)
- [x] **Slice 4: COMPLETE 1 Oct.** PlanBack end to end, hint ladder, bounded repair. Implemented 30 Sep; adversarially reviewed and remediated 1 Oct (APPROVE WITH CHANGES, 383 pass); **the Check was run live on 1 October 2026 and the user walked through it.** Transcript at `docs/reviews/slice4-walkthrough.md`. **The usage-proof capture starts here and is only half met: see the usage-proof section below**
- [ ] **Slice 5: judged fixture + abstention path. IN PROGRESS 1 Oct 2026.** Unblocked by dropping Option C. Built, tested and proven live: `POST /barriers`, `POST /escalations`, `POST /reassessments`, F6 (the owner moves to the human path on escalation), O7 (a new disposition version must move the deadline later), the `submission/usage-proof.md` skeleton, and K2 promoted from the spike into `tests/test_service.py`. 419 tests pass; nine live curls correct; three mutations each seen RED. **The Check is outstanding.** B3 still needs a clinical reviewer
- [x] **Slice 6 built 3 October 2026 on `slice-6`; adversarially reviewed the same day and two findings fixed in the tree; then a second verification pass the same day; COMMITTED AND PUSHED 3 October 2026 on the user's explicit instruction** (five commits, tip `dc95295`, fast-forwarded into `main`, both branches on `origin`). Action path (`POST /actions`, `POST /callbacks/{route_id}`, `POST /consents`), `simulated_provider.py`, `tools.py` (three MCP tools, three rechecks each), `coordinator.execute_tool`, `OriginNotWired` (origin is checked, not trusted; `origin = local-sim` everywhere because Gate A proved transport, not tool execution, and D8 forbids ADP carrying the section 3.3 claim). F5 split, O2 `LockContention`, O5 `ReceiptOutcome`, NF5 honest boundary claim, all closed. **484 pass** (482 at build, +2 for the review fixes), 11 mutations RED after the harness repair. Live curl proven; **Check run live 3 October 2026, transcript at `docs/reviews/slice6-live-check.md`**. Review at `docs/reviews/slice6-adversarial-review.md`: verdict ISSUES FOUND (not FAIL), the honesty claim upheld, no false claim in the record. **F-1 fixed:** `/static` is now mounted, so `/static/style.css` serves (was 404) and the patient page is styled. **F-2 fixed:** the `refused` receipt now has a fail-capable HTTP test (revoke consent, then post a callback). Both fixes mutation-checked. The Check was walked through on the user's behalf and approved for commit on 3 October 2026.
- [ ] **Slice 7: public deployment, the Next.js clinical frontend and auth (NEW 30 Sep)**
- [ ] Slice 8: baseline instrument, the external card (C1, parallel)
- [ ] Slice 9: Gate B, run the comparison (**kill test**)
- [ ] Slice 10: Closure Contract in full (starts only after the kill test)
- [ ] Slice 11: fault harness + seven sequences
- [ ] Slice 12: judge ledger, submission assets and the usage proof (merge of old 11 and 12; must land before 16 Oct)
- [ ] **Slice 13: ADP interpretation surface (CONDITIONAL, Gate 2 gated, default do not run)**

## Usage proof (OPEN: one half is done, and the missing half blocks scoring)

- [x] **Publish the written development history, done 1 October 2026,** at `docs/session-logs/`. This satisfies `CHALLENGE_REQUIREMENTS_JUDGING.md` line 128, which accepts a written development-process description
- [x] **Three redacted chat screenshots captured 1 October 2026** into `submission/usage-proof/screenshots/`, by Jaydon, and pushed. Redaction checked: no AppKey, token, key or credential in any of the three. Manifest and rules in that folder's `README.md`; the capture log is in `submission/usage-proof.md`, written at Slice 5

### Standing constraints for every slice

- Prove it works — run it, curl it, or browser-test it, and **show the user the result**. An agent summary is not proof.
- Check it off in `00-status.md`, which is the only authority for slice state.
- Ask: "Continue to slice N+1, or re-steer?"
- Real tests only. Never a test that passes against the pre-change code; never weaken a test to reach green.
- **R1:** any slice overrunning its window by more than 50% means telling the user and replanning — not absorbing the overrun by quietly dropping tests.

## Open risks at Gate 4

| # | Risk | Where |
|---|---|---|
| R1 | **Schedule does not fit:** **122–203 h** against 128 h available, solo, 16 days, after Decision D-1b added 20–34 h | `04-slices.md` §5, §6 |
| R2 | **Gate A never passes** — platform path unproven, spike overdue | `04-slices.md` §6, Slice 6 |
| R3 | **Recruitment fails:** no dyads means no Gate B | `04-slices.md` §6, Slices 8 and 9 |
| R4 | **Option C source cannot be cleared** | `04-slices.md` §6, Slice 0/5 |
| R5 | **Reading B is the real contract** — K1 weakens | `04-slices.md` §1.1, ADR-0007 |
| R6 | ~~**Callback atomicity fails** — duplicates lost~~ **Resolved at Slice 3, 30 Sep.** `BEGIN IMMEDIATE` plus the busy timeout serialises the lookup and the insert; two connections in two threads on one key yield one applied receipt and one recorded duplicate. Gate 2 was not backtracked | `04-slices.md` §6, Slice 3 |
| R7 | **Effort estimate is wrong** — 90–150 h unverified | `04-slices.md` §6 |
| R8 | **The public deployment breaks the append-only record:** WAL on a mounted disk, or an ephemeral path | `04-slices.md` §6, Slice 7 |
| R9 | **A public surface becomes a clinical claim:** a published agent answers clinical questions with no reviewer | `04-slices.md` §6, Slices 7 and 13 |

## Review conclusion — round 2

- Revision 1 was not approvable: attempt state was unwritable, the tool path was described five ways, and the baseline arm could not measure the success metric.
- Revision 2 fixes all three; D9 is cut with its cost stated; the survivor set is PlanBack, the Closure Contract, the fault harness, the four-line screen, the ledger and the baseline comparison.

## Slice 6 review notes, carried not fixed (3 October 2026)

Three notes from the Slice 6 adversarial review. None blocks; each is recorded here
so it is not lost. A second verification pass the same day added V-1 to V-4 below.

| # | Note | Action |
|---|---|---|
| N-1 | `tools/_fix_status_slice6.py` and `tools/_fix_todo_slice6.py` are one-shot record-editing scripts left in the tree. They are untracked, so a commit by path cannot pick them up, but they are not slice deliverables and they sit beside the real tooling | **Remove before the Slice 6 ship**, or move them out of `tools/`. No later work depends on them |
| N-2 | `docs/reviews/slice6-live-check.md` carries 8 U+2014, all inside quoted HTTP output (the approved fixture label "SIMULATED - RESEARCH DEMONSTRATION..."), none authored and none disclosed | **Resolved:** the file now discloses the count in its section 6. The dashes are imported evidence, which `AGENTS.md` section 6 permits |
| N-3 | `00-status.md`'s Slice 6 section carried no per-file test split and no line-count row, unlike Slices 3 and 4 | **Corrected 3 October 2026** in the Slice 6 section above |

### Verification-check findings, 3 October 2026 (second pass)

| # | Finding | State |
|---|---|---|
| V-1 | `00-status.md` claimed the harness line count was re-stated in the review section; it was never given | **Corrected:** the claim is removed. The harness is 184 lines |
| V-2 | The F-2 mutation anchor in the record named the `version != stamped_version` branch; the test is actually pinned by the `state != "granted"` branch, which fires first | **Corrected** in the Slice 6 section above and to flow into the review note |
| V-3 | `PROGRESS.md` still said "482 pass" after the two fixes took the suite to 484 | **Corrected** in `PROGRESS.md` |
| V-4 | `tests/_mutate_slice6.py` **skips M11** ("anchor not found") and its **own control FAILED**, leaving `state.py` carrying M11's mutation (`if False:  # mutated`) until it was reverted by hand. Cause: `read_text`/`write_text` newline translation converted CRLF files to LF, and the `state.py` anchors were CRLF-unaware. The shipped figure was 10 of 11 RED, not 11 of 11 | **FIXED AND RE-RUN 3 October 2026:** binary I/O, CRLF-normalised anchors, a missing or non-unique anchor is now a hard failure, and the restore is md5-verified. Re-run gives **11 of 11 RED** and a green control with every file byte-exact. **Carried as a note to the ship anyway**, so the fix is reviewed with the slice rather than trusted on sight |
| V-0 | Incident: my own compound mutation left `state.py` short one branch, detected by md5 change and restored to `1dcc54ea...` | Recorded in `docs/reviews/slice6-verification-check.md` section 9 |
