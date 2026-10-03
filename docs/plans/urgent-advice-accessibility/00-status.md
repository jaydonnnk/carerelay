# Status: CareRelay urgent-advice accessibility

- Gate 1: Product, **RE-APPROVED 2 October 2026** (re-approved 1 October 2026; approved 25 September 2026). Reopened and re-approved the same day by the plain-human wording pass on the approved patient-facing copy; see the "Patient wording pass" section below
- Gate 2: Architecture, **RE-APPROVED 2 October 2026** (revision 3 re-approved 30 September 2026; revision 2 was approved 25 September 2026). Reopened and re-approved the same day by `02-architecture.md` section 7: the rendering table, a line-by-line change record, and two additions to the copy rules. See the "Patient wording pass" section below
- Gate 3: Program Design, **RE-APPROVED 1 October 2026** (reopened and re-approved the same day; re-approved 30 September 2026; first approved 26 September 2026). The reopen was one paragraph of section 6.2, dropping Option C, and section 8 item 3 was reconciled to the post-drop state in the same pass; see the Gate 3 re-approval below
- Gate 4: Slice plan, **APPROVED** (re-approved 30 September 2026; first approved 28 September 2026)

**All four gates are APPROVED as of 2 October 2026.** Gates 1 and 2 were reopened that day by the patient wording pass and **re-approved the same day** ("I have read and i re approve both gates"), which also completed the re-opened Slice 5 Check. **Slice 5 closes as of 2 October 2026.** Gate 4 was untouched by the pass, so implementation stayed authorised throughout. Nothing is committed and nothing is pushed.

**All three reopened gates were re-approved on 30 September 2026.** Implementation is authorised again, slice by slice, in the order `04-slices.md` gives.

## Gate reopening: 30 September 2026

**Gates 2, 3 and 4 were reopened on the user's instruction of 30 September 2026**, to encode four decisions and one hosting choice. Editing an approved gate document reopens that gate (`AGENTS.md` section 5), so this is a reopen rather than a tidy-up.

| # | Decision | Label |
|---|---|---|
| **D-A** | An ADP-based project goes hand in hand with using WorkBuddy. ADP is **additive**, never a replacement for the WorkBuddy execution substrate | `[verified]` as a user decision |
| **D-B** | The ADP Experience URL **counts as the "project link"** bonus | `[verified]` as a user decision |
| **D-C** | A **production link on Vercel** is also required, in addition to the ADP Experience URL | `[verified]` as a user decision |
| **D-D** | Every other recommendation in `docs/reviews/adp-hosting-stack-review.md` is accepted | `[verified]` as a user decision |
| **D-1b** | **Vercel hosts the clinical screens themselves**, as a Next.js app calling the Render API | `[verified]` as a user decision |

**What D-A does not mean.** It does not authorise ADP on the execution path. The ADP guide does not document ADP tool execution, platform-originated failure events or session resume (`[verified]` as absence). Per `CHALLENGE_REQUIREMENTS_JUDGING.md` section 7, ADP tool-calling is a `[vendor claim]`; the MCP tool, the failure-event origin and session resume are `[unknown]`. The WorkBuddy execution-substrate claim in `02-architecture.md` section 3.3 stays intact.

**Why D-1b reopens Gate 3 as well.** Moving the clinical screens to Next.js changes the Gate 3 file list and falsifies its statement that no public auth flow is implied. Option D-1a would have left Gate 3 closed. The cost of D-1b is recorded in `02-architecture.md` section 12 and in `04-slices.md` section 5.

| Gate | Amended document | What changed |
|---|---|---|
| 2 | `02-architecture.md` revision 3 | D1 replaced, D8 amended, D13 added, section 6 env var names, section 8 four rows, sections 11 and 12 |
| 3 | `03-program-design.md` | Section 1 stack bullet, section 2 file list, section 3 closing line |
| 4 | `04-slices.md` | Renumbered to fourteen slices, one merge, one required slice added, one conditional slice added, effort recomputed, cut order updated, usage proof moved forward, templates drift resolved |

**Committed to `main` and pushed to `origin` on 30 September 2026.** The re-approval question at the end of `04-slices.md` was answered yes on 30 September 2026; the answer and its limits are recorded in the re-approval subsection below.

### Gate re-approval: 30 September 2026

**The user answered the re-approval question with "Yep they look good go ahead and commit the changes to main".** Gate 2 revision 3, Gate 3 and Gate 4 are therefore **APPROVED**, and implementation is authorised again slice by slice in the order `04-slices.md` gives.

**The authorisation limits are unchanged from the original approvals.** No installs beyond the declared test dependencies, no credentials, no recruitment, no deployment, no external calls beyond those the plan names, and no push. The restructure in `04-slices.md` is approved as the plan of record, including Slice 7 (public deployment and auth) and the conditional Slice 13.

## Gate 1 reopen: 1 October 2026

**Gate 1 is reopened because `01-product.md` gained one subsection.** `AGENTS.md` section 5 is explicit: editing an approved gate document reopens that gate. This is the smallest edit that closes the Slice 4 open item, and it changes no other approved content.

| What changed | Why |
|---|---|
| `01-product.md` gained **Approved patient-facing copy**, carrying one string: the coordinator-unavailable fallback, "We could not check that answer just now. Your plan has not changed." | `COORDINATOR_FALLBACK_TEXT` in `api.py` was authored patient-facing copy with no approved source, and Gate 1 owns patient-facing copy. The Slice 4 adversarial review judged the wording acceptable for a labelled research demonstration, because it names no symptom, urgency, route or deadline and asserts only that the check did not happen, on the condition that the touch it needs be tracked rather than left in prose |

### Gate 1 re-approval: 1 October 2026

**The user answered the standing question with "I reapprove gate 1", 1 October 2026.** Gate 1 is therefore **APPROVED** again, and the coordinator-unavailable string "We could not check that answer just now. Your plan has not changed." is approved patient-facing copy in `01-product.md`.

**All four gates are now APPROVED.** The authorisation limits are unchanged: no installs beyond the declared test dependencies, no credentials, no recruitment, no deployment, no external calls beyond those the plan names, and no push. Gate 1's approval does not itself authorise code; Gate 4 authorises implementation slice by slice.

**What this does and does not unblock.** It closes outstanding item 2 of the Slice 4 close-out. It does **not** unblock Slice 5, which is blocked on the Option C source, not on Gate 1. See the source-check section below.

## Option C source check, run 1 October 2026

Requested by the Slice 0 stop condition ("if no Option C source can be cleared by 2 October, escalate") and by Slice 5's gate. **Verdict: no source clears, and the check exposed a contradiction inside the approved decision rather than a missing URL.**

| Candidate | Attributable | Licence | Singapore applicability | Clears |
|---|---|---|---|---|
| **MOH, `moh.gov.sg` content** | Yes | **No.** Clause 11: the Contents "shall not be reproduced, republished, uploaded, posted, transmitted or otherwise distributed in any way, without the prior written permission of the Ministry of Health". Clause 12 makes modification or use for another purpose a violation. The **Singapore Open Data Licence is granted for Datasets only** and does not reach website content (clause 1, and the licence grant itself). Permission route: `moh_qsm@moh.gov.sg`, at MOH's "sole and absolute discretion" | Yes | **No** |
| **HealthHub, `healthhub.sg`** | Yes | **No.** Clause 12.1: materials may not be "modified, copied, used, distributed, framed, reproduced, republished, downloaded, scraped, displayed, posted, transmitted, or sold in any form or by any means, in whole or in part, without our prior written permission. All rights are expressly reserved." Clause 12.2's only carve-out is fair dealings for private study, research, criticism or review. Clause 12.3 also claims IP in AI-generated content; clause 2.4(9) forbids using the interface or outputs to develop a similar interface | Yes | **No** |
| **UK public-sector content under OGL v3, for example NHS** | Yes | Yes, OGL v3 with attribution; the UK framework also carries a "content not licensed for re-use" list **[hypothesis]** as to which specific pages are covered | **No.** UK health-system guidance. Its routes (111, GP) do not exist in Singapore, and quoting it into a Singapore patient-facing surface imports a foreign standard of care | **No** |

All three rows are **[verified]** as read from the primary terms pages on 1 October 2026, except where marked otherwise.

**The finding that matters, and it is not a licensing detail.** `03-program-design.md` section 6.2 approves **Option A and Option C together**, and they cannot both hold:

- **Option A** makes the material **content-neutral** and names **no real service**. The fixture's entities are literally "the fictional provider" and "the fictional nurse line", its complaint is "help sorting out my appointment", and it asserts no symptom, urgency or threshold.
- **Option C** requires the fixture wording to be **sourced verbatim from attributable published guidance**.

**No published guidance contains "the fictional provider's same-day review".** A fixture built from fictional entities cannot be quoted verbatim from anywhere, so Option C is **unsatisfiable as written**, and no amount of searching fixes it. `clinical-review-blocker.md` section 3 already classifies exactly this material as Tier 1 (non-clinical mechanism, "requires no review, not blocked"); the Option C obligation was written for Tier 2 clinical wording that Option A then removed.

**Three ways forward, with the honest cost of each:**

| # | Route | Cost | Effect on Slice 5 |
|---|---|---|---|
| 1 | **Amend section 6.2 to drop Option C** (recommended). Record that under Option A the fixture is Tier 1 content: it carries no symptom, urgency, threshold or real facility, and it is honest because it **asserts no clinical claim**, not because it quotes one | **Gate 3 reopens**, because section 6.2 is approved. Slice 5 is unblocked the same day | **Unblocked today** |
| 2 | **Request written permission from MOH** at `moh_qsm@moh.gov.sg` | MOH has "sole and absolute discretion" and no published timeline; the 2 October trigger is one day away. Permission to quote MOH wording still cannot produce a **fictional** provider, so this does not resolve the contradiction | **Stays blocked** |
| 3 | **Take the recorded fallback, Option B**: secure one qualified reviewer | Unbounded. `clinical-review-blocker.md` records two approaches already made with no response | **Stays blocked** |

**[hypothesis] Recommendation: route 1, with Option B kept as an upside if a reviewer appears.** Route 1 is the only one that resolves the contradiction rather than waiting beside it, and it costs a Gate 3 reopening rather than a schedule. The fixture's honesty does not depend on a quotation: `demo/fixture.py` already carries a simulated research-demonstration label as part of the fixture data itself, and an empty `PERMITTED_CHANGE_CODES`, so every reassessment fails closed to the human path.

**Decision required, and this is Slice 5's gate:** approve the section 6.2 amendment (route 1), or hold for route 2 or 3. **Clinical wording is not authored to unblock the schedule** (the standing instruction of 28 and 30 September 2026), so Slice 5's judged fixture waits on this answer.

**RESOLVED 1 October 2026: route 1.** The user answered **"drop"**. `03-program-design.md` section 6.2 is amended to carry Option A alone, with Option C dropped and both reasons recorded there. **Gate 3 is reopened by that edit** (`AGENTS.md` section 5) and awaits re-approval; Gate 4 is untouched, so implementation stays authorised slice by slice. **Known pending touch:** `04-slices.md` still states Slice 5's gate as "the Option C source must be cleared". That line is superseded by this decision and is corrected at the **next Gate 4 touch**, not now, so that a second reopening is not triggered while a slice is in flight.

**What is not blocked, and can be built now regardless of the answer:** the abstention and barrier path (`POST /barriers`), the escalation and reassessment endpoints (`POST /escalations`, `POST /reassessments`), the F6 owner decision, the O7 deadline constraint, and `submission/usage-proof.md`. None of these carries clinical wording. **These are now being built, at the user's "drop" instruction.**

## Gate 3 reopen: 1 October 2026

**Gate 3 is reopened because `03-program-design.md` section 6.2 was edited** to drop Option C (`AGENTS.md` section 5). One paragraph and one heading changed. The edit adds **no clinical wording**, removes no capability, and changes nothing else in the document.

**Re-approval question: approve the section 6.2 amendment (Option A alone, Option C dropped), or what should change?**

**Gate 4 is untouched**, so implementation remains authorised slice by slice while this question is open, and Slice 5's non-clinical work proceeds. `04-slices.md`'s stale Slice 5 gate line is corrected at the next Gate 4 touch rather than now.

### Gate 3 re-approval: 1 October 2026

**The user answered the standing question with "Yea i approve", 1 October 2026.** Gate 3 (Program Design) is therefore **APPROVED** again, carrying **Option A alone** in section 6.2 and the reconciled section 8 item 3. **All four gates are APPROVED.**

**Two further edits were made in the same completion pass, and both are inside the reopened scope rather than new content:** the Slice 5 adversarial review's finding B1 on section 8 item 3 (which still claimed the fixture was sourced verbatim, contradicting section 6.2), and finding B2 on section 6.2's own first line (which still recorded the 26 September selection of Option A + C with no qualifier). Both are reconciled to the drop. Neither adds a decision; both remove a self-contradiction the review named. Section 6.2's heading already carried the drop.

**The authorisation limits are unchanged.** No installs beyond the declared test dependencies, no credentials, no recruitment, no deployment, no external calls beyond those the plan names, and no push. Gate 3's re-approval does not itself authorise code; Gate 4 authorises implementation slice by slice.

**Blockers closed in the same pass, verified:** B1 and B2 above; B3, the `POST /api/episodes` `note` on the wire, re-run live and confirmed to match `policy_provenance`. Evidence is recorded in the Slice 5 section below.

## Slice 5: judged fixture and abstention path, 1 October 2026

**Built, tested, proven live, reviewed, and its blockers closed. Adversarially reviewed the same day: D1 APPROVE WITH CHANGES, three blocking findings, all documentary or wire-payload, none in the code.** The review is at `docs/reviews/slice5-adversarial-review.md`; its D2 upholds dropping Option C.

| Item | State |
|---|---|
| `POST /barriers` | **Built.** `service.record_barrier` validates any proposed route through `domain.validate_route`. A refused proposal is **recorded as a stop and then refused** with 422, so the ledger keeps the evidence and the caller still gets the refusal |
| `POST /escalations` | **Built.** `service.escalate` validates the human path against the policy's permitted routes, so the record names a service the product can display |
| `POST /reassessments` | **Built.** `service.reassess` calls `domain.reassessment_decision`. With no reviewer, every input stops at the human path and **no second version is inserted** |
| **F6** (the owner after an escalation) | **DECIDED and implemented.** An escalation moves `action_owner_id` to the named human path. `EpisodeSnapshot` gained `escalated_human_path`, and an escalation that names no path is refused rather than falling back to the patient, because a fallback would silently re-impose the obligation the escalation handed away |
| **O7** (deadline monotonicity) | **CLOSED.** `state.insert_disposition` refuses a new version whose deadline is not **later** than the one it replaces (`DeadlineNotMonotonic`). A version 2 at or before version 1 would leave the current version with no expiry event and could return an expired episode to `open` |
| `submission/usage-proof.md` | **Written**, as a skeleton to be completed at Slice 12 |
| The judged fixture wording | **Unblocked and deliberately unchanged.** Option C was dropped, so the non-clinical placeholder stands as authored rather than sourced. `fixtures/scripted_episode.json`, `demo/fixture.py` and the API's `policy_provenance` carry the corrected record |
| **K2, promoted from the spike** | **Done.** `TestPlanPrecedesReadBack` asserts against the product, with no coordinator and no reviewer, that the plan is issued and renderable before the coordinator is reached and that a coordinator failure cannot move the deadline. The fixture carries no urgent clinical content by design, so the ordering property is the one this fixture can actually prove |
| **B3** (the intake recognition rule) | **CLOSED 2 October 2026 without a clinical reviewer, and it turned out not to be a reviewer-gated decision after all.** The rule was a substring match, so a complaint carrying a red-flag symptom alongside the bound phrase was bound to the demo plan. It is now an **exact normalised match**. No red-flag or negation handling is authored, and none is needed: the fix makes the system refuse strictly more inputs, and refusing more is never a clinical claim, so it needs no reviewer. See the B3 section below |
| **F6's rendering half** | **NOT DONE, and deliberately not authored.** `derive_closure` now names the human path, but `patient_lines` still composes line 2 from `disposition.next_owner_id`, so a derived patient screen would say "You must act now." while the ledger says the nurse line acts. That is a real contradiction between the two axes. It is **latent today**: `GET /api/episodes/{id}` returns the hardcoded fixture lines, so no HTTP path renders derived lines, and the same is true of the response bodies of the new endpoints. Fixing it needs approved copy for a human-service owner on line 2, which is a **Gate 1 touch**, so it is not authored here. **Anchored to Slice 10**, which owns the Closure Contract rendering and re-checks F6 |

| Evidence | Result |
|---|---|
| `pytest tests/` | **419 passed, 1 warning** (Slice 4 close: 383). Per file: 97 domain, 141 boundaries, 37 api, 100 state, 44 service |
| Live `curl` on `127.0.0.1:8137` | **Nine calls, all correct.** Health 200; create 200; intake 200; barrier with a permitted route 200; barrier with no proposal 200; **hallucinated route 422 carrying `stopped_at: human_path` and `barrier_recorded: true`**; escalation 200; unpermitted human path 422; reassessment with no code 200 `stop_at_human_path`; unknown code 200 `stop_at_human_path`. **Reproducibility, corrected 1 October 2026:** the intake request body field is **`confirmed_text`**, not `text` (`api.py`, `IntakeRequest`). Posting `{"text": ...}` returns 422 and every later call then returns 409 "episode has no disposition". With `{"confirmed_text": ...}` all nine results above reproduce |
| Mutations | **Three, each seen RED on exactly its own test, each reverted.** The O7 check disabled: 2 failed, the later-deadline control passed. F6 reverted to naming the patient: 2 failed. A refused barrier recorded as not-a-stop: 1 failed. The full suite was green again after every revert |

**The review's three blockers, all closed and verified on 1 October 2026.**

| # | Finding | Close and its evidence |
|---|---|---|
| **B1** | `03-program-design.md` section 8 item 3 still claimed, present tense, that the fixture was "sourced verbatim from attributable published guidance" | Rewritten to the post-drop state: Option A alone, the fixture is **authored rather than sourced**, asserts no clinical claim, no source claimed. Label now `[resolved, 26 September 2026; amended 1 October 2026]`. The item is kept, not deleted. `grep 'sourced verbatim'` over the document returns nothing |
| **B2** | Section 6.2's first line still read "The user selected Option A + C on 26 September 2026" under a heading that says Option C is dropped | Qualified: the 26 September selection of Option A stands, and its Option C half is superseded by the drop. History preserved, not rewritten |
| **B3** | `api.py` `POST /api/episodes` `note` still ended "placeholder awaiting the Option C source check", so the wire payload contradicted `policy_provenance` in the same file | Note strings updated to the corrected record. **Re-run live and the body confirmed:** the create response now reads "the fixture wording is a provisional non-clinical placeholder, authored rather than sourced. Option C was dropped on 1 October 2026; the wording asserts no clinical claim." The "Slice 1 tracer bullet: hardcoded" honesty is kept |

**Secondary items closed in the same pass:** `AGENTS.md` section 3 (no longer says Slice 5 is blocked on the source), the `test_domain.py` module docstring, the `test_state.py` provenance literal, and the live-curl evidence above (the `confirmed_text` correction).

**Deliberately not closed, and recorded as such.** `04-slices.md` still states Slice 5's gate as "the Option C source must be cleared". It is corrected at the **next Gate 4 touch** to avoid a second reopening while a slice is in flight. The review's should-fix items are also left: `list_barriers` returning raw `sqlite3.Row` (S1), the 18 `service._store` reaches in tests (S2), and the two NITs. None is slice-blocking.

**Committed, merged and pushed.** Six commits on `slice-5`, base `ff22ed3`, tip `f95cea4` (`6187e51` F6 and O7; `9c331b9` the endpoints and K2; `b7655e6` the corrected fixture record; `6ced793` the Gate 3 amendment and status record; `f6a89f2` the stale-claim sweep; `f95cea4` the review note and the usage-proof skeleton). `slice-5` was fast-forwarded into `main` and `main` pushed to `origin` at `f131ef2` on the user's explicit instruction of 1 October 2026. **The Gate A harness rebuild of 2 October 2026 sits on `main` uncommitted** (see the Gate A section below).

## Slice 5 live check, 2 October 2026

**An independent adversarial review was run against the committed slice. Verdict: PASS WITH CONCERNS, and no blocking finding in the code.** Review at `docs/reviews/slice5-live-check.md`.

| Claim | Result |
|---|---|
| The abstention path is real | **PASS.** No input makes the product guess. Structurally: the only two production `insert_disposition` call sites are `service.intake` and `service.reassess`, both gated, and `permitted_change_codes` and `authorised_reassessments` are both empty, so no HTTP path can write a version 2 |
| The fail-capable tests fail | **PASS, after one fix below.** F6, O7 and K2 are each now independently mutation-proven |

**Two findings, both closed in this pass.**

| # | Finding | Close |
|---|---|---|
| **S1** | The slice checklist row said Slice 5 was "not merged into `main` and not pushed". That was false | Corrected on that row, and re-verified: `origin/main` and `main` both sit at `d5efdc5`, and `f95cea4` is an ancestor of it |
| **S2** | Two of K2's three assertions could not be made to fail alone: the only defect that broke them also broke `TestCoordinatorUnavailable`, and `AGENTS.md` section 6 counts a fault two checks both catch as proof of neither | `tests/test_service.py` gained `test_intake_never_reaches_the_coordinator`. It runs intake against a coordinator that **answers**, so the plan is issued either way and no other check moves. Mutating intake to reach the coordinator tolerantly turns **exactly that one test** red and nothing else: 1 failed, 419 passed |

**Mutations, each seen red and each reverted byte-identical** (harness at `spike/review_mutate.py`): F6 owner reverted to the patient, 4 red; O7 check disabled, 2 red with the later-deadline control green; K2 deadline moved on a coordinator failure, 1 red; K2 intake tolerantly reaching the coordinator, 1 red. `rules.py`, `state.py` and `service.py` all hash back to their pre-mutation values and `loneLF` is 0 on each.

**Test count: 420 passed, 1 warning** (419 at the close of the Slice 5 build, plus the one K2 assertion added here).

**Deliberately not raised, per the review's constraints:** B3, F6's rendering half (anchored to Slice 10), `04-slices.md`'s stale Slice 5 gate line, and Gate A not closing the platform-integration question.

**Carried as notes, none slice-blocking:** O7 is unreachable from any HTTP path today, so it is a store-layer guarantee rather than a product-path one; `barriers` and `escalations` inherit O1's **scoped** append-only guarantee, so `INSERT OR REPLACE` still rewrites a row from a connection that has not set `PRAGMA recursive_triggers`; `rules.validate_change` is defined and unit-tested but called by no production path; `CoordinatorPort.classify_change` is declared and never called, so `03-program-design.md` section 4's classification step lands with the Slice 6 coordinator wiring; the 422 body says `stopped_at` where the 200 body says `stopped_at_human_path`.

**The Check, run 2 October 2026, and its wording has since been superseded.** `04-slices.md` sets it as "the user reads the fixture wording and the provenance record". Both were reproduced verbatim for the user's read at `docs/reviews/slice5-live-check.md` section 7. **The four lines read at that Check were the pre-rewrite forms**: "Help is not arranged.", "You must act now.", "Before 6pm today.", "If this route fails, call the fictional nurse line." The user then asked for a plain-human wording pass, which was applied the same day (see the wording-pass section below). The current lines are "No one has agreed to help yet.", "Please act now.", "Please do it before 6pm today.", "If that does not work, call the fictional nurse line." The stored `policy_versions.provenance` row is unchanged and still reads: "PROVISIONAL: non-clinical placeholder, authored rather than sourced. Option C was dropped on 1 October 2026 after the source check cleared no source; the wording names no symptom, urgency, threshold or real facility and asserts no clinical claim (03-program-design.md 6.2)." `approved_by` is still `NULL`. **Because the wording the user is asked to read has changed, the Check is re-opened: it completes on Jaydon confirming that he has read the reworded lines at `docs/reviews/slice5-live-check.md` section 7, and confirming the reworded forms.**

## Patient wording pass: Gate 1 and Gate 2 reopened, 2 October 2026

**Both gates are reopened by this pass, and neither is re-approved yet.** `AGENTS.md` section 5 is explicit: editing an approved gate document reopens that gate. The pass edits two of them, so two gates reopen.

**What the user asked for.** On 2 October 2026 the user asked for the patient-facing wording across Slices 1 to 7 to "sound like a human, and not a robotic agent", and initially asked for the tone to be sourced from hospitality sources.

**What was declined, and why.** The hospitality sourcing was **not** done, for a reason recorded rather than quietly dropped: a hospitality brand guide is **not a clinical authority**, so it cannot fill a gap the clinical sources already left. MOH clause 11 and HealthHub clause 12.1 both failed on licence on 1 October 2026, and a style guide is a weaker source than either. Citing one would have **weakened** the provenance record by implying an authority that does not exist, and the fixture has been explicitly unsourced since Option C was dropped. The user accepted the alternative: the rewrite is applied against the **five copy rules in `02-architecture.md` section 7**, which are already Gate-approved and were written for exactly this problem. Those rules, not a hotel guide, are the tone authority.

| Gate | Document edited | What changed |
|---|---|---|
| **1** | `01-product.md` | "Approved patient-facing copy" gained the four-line rendering with its current forms, plus two new binding rules: no exclamation marks, and no invented capability. The coordinator-unavailable string is unchanged after review. |
| **2** | `02-architecture.md` section 7 | The rendering table updated; a line-by-line change record added; copy rule 2 gained "no exclamation marks"; copy rule 6 "no invented capability" added. |

**Two rewrites were rejected during the pass, and both rejections are now encoded as rules rather than left in prose.**

| Proposal | Source | Why rejected |
|---|---|---|
| Line 1 becomes a question: "do you want me to alert your emergency contact?" or "I'll contact your emergency contact" | User proposal, 2 October 2026 | **No invented capability.** CareRelay holds no emergency contact, has no channel to reach one, and has no consent record, so the sentence promises a dispatch that cannot occur. That is a **false completion**, which is the exact failure I2 forbids. The question form also breaks **I4**: it moves the obligation back to the patient instead of naming the party who acts. Rejected in full. |
| Line 2 becomes "Please act now!!" | User proposal, 2 October 2026 | **No alarm.** Copy rule 2 already banned alarms because the reviewer killed the first expired draft as too blunt. A double exclamation is an alarm, not a courtesy, and it is sterner than the "You must act now." it replaces, not softer. The user accepted "Please act now." without exclamation marks. |

**Third-party documents carrying the copy were updated for consistency, and none of them is a gate document.** `PLAN.md` section 6.1's patient-facing rule, `03-planback-closure-contract.md` sections 2.5 and 4, and `mockups/03-unresolved-handoff.html` all mirrored the old wording. They were updated in the same pass so the documents stay consistent with the gates that own the copy; only `01-product.md` and `02-architecture.md` reopened anything.

**The fixture remains authored, unsourced and non-clinical.** The rewrite changes tone and nothing else. `PERMITTED_CHANGE_CODES` stays empty, `authorised_reassessments` stays empty, no source is claimed, and `approved_by` stays `NULL`. `fixtures/scripted_episode.json`'s `note` records the reword date and repeats that the wording is still authored and still asserts no clinical claim.

**One pre-existing em dash was carried, not added.** The mockup's line 2 read `<strong>You must act now</strong> — or your daughter, Mei-Ling.` before this pass, and reads `<strong>Please act now</strong> — or wait for your daughter, Mei-Ling.` after it. The em dash is the same construction in the same sentence, so it is not new writing under `AGENTS.md` section 6. Every other added line is em-dash free; the count is verified in the review.

**Verification, 2 October 2026.** Suite **422 passed, 1 warning** (420 before the pass; two new fail-capable copy-rule tests added). The live render was captured from a running `uvicorn` on 127.0.0.1:8145 and matches the approved table exactly. loneLF is 0 on every file touched. **Nothing is committed and nothing is pushed.**

**This pass is not self-approving.** Gates 1 and 2 stay **REOPENED** until the user re-approves them, and the standing question is the one at the end of this section, not an inference from the user having asked for the change.

### The standing re-approval question, 2 October 2026

> Gates 1 and 2 were reopened by the wording pass. The patient copy now reads "No one has agreed to help yet. / Please act now. / Please do it before 6pm today. / If that does not work, call the fictional nurse line." The two new binding rules are no exclamation marks and no invented capability. Gate 1 carries the copy; Gate 2 section 7 carries the table, the change record and the five rules. **Do you re-approve Gate 1 and Gate 2?**

**ANSWERED YES, 2 October 2026.** The user answered: **"I have read and i re approve both gates"**. Gate 1 and Gate 2 are therefore **APPROVED** again, and the reworded patient copy is approved content in `01-product.md` and `02-architecture.md` section 7, carrying both new binding rules (no exclamation marks, no invented capability).

**The same answer closes the re-opened Slice 5 Check.** Slice 5's Check is "the user reads the fixture wording and the provenance record", and it was re-opened because the wording it asks the user to read had changed in this pass. The user has confirmed that read in the same sentence. **Slice 5's Check is COMPLETE**, and Slice 5 closes as of 2 October 2026.

**What this approval does and does not do.**

| Does | Does not |
|---|---|
| Re-approves Gate 1 and Gate 2 as edited by the wording pass | Authorise a commit or a push; still requires an explicit instruction |
| Fixes the wording it approves, so any later edit reopens the gate again | Make the fixture clinical, reviewed or sourced; `approved_by` stays `NULL` and no source is claimed |
| Closes Slice 5's Check | Close Slice 5's other carried notes (F6's rendering half, O7 reachability, the scoped O1 guarantee, the two dead functions, the 422 field-name mismatch); those stay anchored to their later slices |
| Leaves Gate 4 untouched, so implementation stays authorised | Re-approve Gate 3; it was re-approved on 1 October 2026 and is not touched by this pass |

**The limits are unchanged from the original approvals.** No installs beyond the declared test dependencies, no credentials, no recruitment, no deployment, no external calls beyond those the plan names, and no commit or push.

## Gate A access spike: RUN AND PASSED, 2 October 2026

**Verdict: PASS, exit code 0. All three Gate A questions answered from observation. The answer to the outstanding question "did Gate A ever run?" is yes, and it passed.** The pre-recorded reversal in `AGENTS.md` section 3 (labelled local `local-sim` fallback, weakened platform-advantage claim) **does not apply**.

The spike was built as `spike/gate_a/probe.py` with `spike/gate_a/test_probe.py`, run against the live endpoint `https://wss.lke.tencentcloud.com/adp/v2/chat` with a real ADP AppKey supplied by the user in his own shell.

| # | Question | Result | Evidence |
|---|---|---|---|
| **Q1** | Reachability and a schema-correct request | **PASS** | HTTP 200 carrying `event: request_ack`, then the full chain `response.created`, `response.processing`, `message.added`, `content.added`, `text.delta`, `message.done` |
| **Q2** | Session continuity on a caller-supplied `ConversationId` | **PASS** | Two turns, **issued by two separate client objects sharing only the id** `9aefa047-cd21-4851-9d29-25a024a46ee9`. Turn 2 asked what word it had been asked to remember and answered **"lantern"**, the word turn 1 supplied. The platform reconstructed the prior turn from the id alone, so a process restart holding only the id cannot lose the session |
| **Q3** | Failure-event origin | **PASS** | A malformed body returned HTTP 200 carrying `event: error` with a **numeric** `Code: 400`, an **empty** `RequestId` and a **populated** platform-owned `TraceId` (`960c3a5eaaa236c6c5d988c7e4341a55`) |

**The schema, established against the official ADP reference** (`https://www.tencentcloud.com/document/product/1254/81449`, retrieved 2 October 2026, `[verified]`):

- **Authentication is the `AppKey` request-body field**, not a header. The only documented header is `Content-Type: application/json`. **There is no second secret**, so `ADP_API_SECRET` is not consumed by this API at all. The AppKey is obtained from Application Management, on the running application, via Call, in the Call Information window.
- **`ConversationId` and `RequestId` are caller-supplied** and must match `^[a-zA-Z0-9_-]{32,64}$`. The platform does **not** issue a session id. Q2 is therefore "does ADP honour a caller-supplied id across two calls", which is the property a restart-surviving session actually needs.
- **Failures arrive as HTTP 200 carrying an SSE `event: error` frame**, never as an HTTP 4xx. The reference documents the error event but **not its structure**; the live capture above is the authority for it.
- On the success path the platform echoes the caller's `RequestId` and supplies a `TraceId`. On the malformed-body path `RequestId` is empty and `TraceId` is still supplied. **Both paths carry a platform-attributable identifier.**

**The first draft of the harness was wrong, and the live run exposed it.** It sent the AppKey as an `X-Api-Key` header, expected `ConversationId` to come *back* from the platform, and treated any HTTP 200 as a pass. Its first live run returned PARTIAL because the body was rejected, and its `q1` recorded `ok: true` for a **rejected** call on the strength of the status code alone. **That is the exact softening the gate exists to prevent, and it was in our own harness.** The rebuild requires `request_ack`, reads the error frame as the platform sends it, parses `Code` as numeric, and generates and replays the ids. The stale first-draft `gate_a_result.json` was deleted so it cannot be misread.

| Harness evidence | Result |
|---|---|
| `spike/gate_a/test_probe.py` | **34 passed** (first draft: 17) |
| Mutations | **Three, each seen RED on exactly its own test, each reverted.** M1 header-auth reintroduced; M2 string-only error code; M3 bare-200-as-pass |
| Full suite | **419 passed, 1 warning**, unchanged, so nothing outside the spike moved |
| Redaction | The request body now carries the AppKey, so an echo is the likeliest leak path; a test pins that path shut |

**What this proves and what it does not.** It proves the **transport** carries the section 3.3 claim. It does **not** prove that CareRelay's own code uses the platform; wiring ADP into `src/` is separate, later work. Q3's failure was provoked by an empty `ConversationId`, a validation rejection rather than a **tool-execution** failure, and section 3.3 specifically concerns tool execution. **The origin-signal mechanism is proven; the specific tool-failure case remains `[hypothesis]` until a tool exists to fail, and it is to be stated that way in the submission.**

**Uncommitted.** The rebuilt harness sits in the working tree on `main`. No gate authorises a commit.

## Slices

**Gate 4 is re-approved as of 30 September 2026, so implementation is authorised slice by slice.** Slices proceed one at a time, each ending with a "continue, or re-steer?" check. **Slice 5 is built, reviewed and committed on `slice-5`; Slice 6 is next.** Slice state below is the only authority.

- [x] Slice 0: kill tests (**PASS** 28 Sep) + Option C source (**RESOLVED 1 Oct 2026: no source clears, Option C dropped by user decision**)
- [x] **Slice 1 — COMPLETE 28 Sep.** Tracer bullet runs; 11 tests pass; curl-verified live
- [x] **Slice 2: COMPLETE 30 Sep; adversarially reviewed and remediated the same day.** Pure domain core; boundary check seen red then green; 240 tests pass. Review at `docs/reviews/slice2-adversarial-review.md`
- [x] **Slice 3: COMPLETE 30 Sep; adversarially reviewed the same day, verdict yes with named caveats.** The append-only SQLite record; every table refuses UPDATE and DELETE by trigger; the callback representation proven atomic under two concurrent writers and a crash; 70 new tests (69 in the new `tests/test_state.py`, one added to `tests/test_domain.py`), 310 pass, **332 after the remediation of 30 Sep**. The Slice 2 review's `source_ref` open item is settled here. Review at `docs/reviews/slice3-adversarial-review.md`; eight open items, of which the blocking one and three others were closed by the remediation recorded in the Slice 3 remediation section below
- [x] **Slice 4: COMPLETE 1 Oct.** PlanBack end to end, hint ladder, bounded repair. Implemented 30 September 2026; adversarially reviewed and remediated 1 October 2026 (APPROVE WITH CHANGES, 383 tests pass, two blocking test gaps closed, one intake decision carried); **the Check was run live on 1 October 2026 and the user walked through it: mismatch to one repaired field to a clean pass to a third failure routing to the human path, against a running server, not a summary.** Transcript at `docs/reviews/slice4-walkthrough.md`; review at `docs/reviews/slice4-adversarial-review.md`; see the Slice 4 sections below. **The usage-proof obligation starts here and is only half met: the written history is published, the three chat screenshots are not captured.** See the outstanding-items section below
- [x] **Slice 5: BUILT, REVIEWED, CHECKED AND COMMITTED 2 Oct; the shipped copy was reworded the same day, and B3 was closed without a reviewer.** Judged fixture + abstention path. Unblocked by dropping Option C. Barriers, escalations, reassessments, F6, O7 and the promoted K2 are built and proven live; the adversarial review returned APPROVE WITH CHANGES, its three blocking findings were documentary or wire-payload and are all closed, and **422 tests pass**. Six commits on `slice-5`, **fast-forwarded into `main` and pushed to `origin`** (re-verified 2 October 2026: `origin/main` and `main` both sit at `d5efdc5`, and `f95cea4`, the tip of `slice-5`, is an ancestor of it; the earlier "not merged and not pushed" line on this row was false and is corrected here). **The Check is COMPLETE, 2 October 2026**: it was presented at `docs/reviews/slice5-live-check.md` section 7, re-opened when the wording pass changed the lines it asks the user to read, and confirmed by the user's "I have read and i re approve both gates". **B3 no longer needs a clinical reviewer**; it was a logic defect, and it is closed below

## B3 closed without a clinical reviewer, 2 October 2026

**The premise that B3 needed a reviewer was wrong, and it is worth stating why, because the error was mine.** B3 had been carried since the Slice 4 adversarial review as "a reviewer-gated clinical decision", on the reasoning that handling a red-flag symptom is clinical work. That reasoning is correct for *adding* red-flag handling. It was wrong for *removing a substring match*.

**What B3 actually is.** The intake binding rule read `if self._bound_complaint not in rules.normalise(confirmed_text)`, a substring test. Recognition was therefore "does the bound phrase appear anywhere", not "is this the bound complaint". The Slice 4 review measured the consequence and this record carries the measurements: the text `"help sorting out my appointment, also I have chest pain and cannot breathe"` **scored 200 and issued the demo plan**, as did a text carrying a suspected stroke and a negated text.

**The fix, and why it needs no reviewer.** The rule is now an exact normalised match: `rules.normalise(confirmed_text) != self._bound_complaint`. The system refuses **strictly more** inputs than before. Every input that scored 200 under the old rule and stops under the new one is a *refusal*, and a refusal is never a clinical assertion. No symptom is read, no urgency is inferred, no threshold is authored. The rule the documents already claimed is now the rule the code implements.

**What this does not do.** It does not author a red-flag vocabulary, a negation handler or a third-party-subject handler. Those remain clinical work and remain unauthored. An input that coincidentally equals the bound phrase still binds, which is the accepted limitation of a fixture-bound demo and is unchanged.

**Verification, 2 October 2026.**

| Check | Result |
|---|---|
| Suite | **428 passed, 1 warning** (422 before; five parametrised cases added, plus one control) |
| Mutation: restore the substring rule | **Exactly 5 RED**, all five parametrised cases, nothing else. The control case stayed green, which proves the strict rule did not over-refuse |
| Byte-identical restore | `service.py` sha256 `c44f0db40d4541d9` before and after; loneLF 0 |
| Live, `uvicorn` on 127.0.0.1:8151 | Red flag plus bound phrase **422** with `stopped_at: human_path`; exact bound complaint **200** |

**The misnamed test is corrected.** `test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path` submitted only a zero-overlap string, so it proved the disjoint case and nothing else while carrying a name that claimed the general rule. The general rule now has its own parametrised test, and the original name is kept for the disjoint case it actually covers.

**One test-hygiene fix rode along.** Eight test call sites passed the literal `"i need help sorting out my appointment"` while the fixture binds `"help sorting out my appointment"`. They matched only because the rule was a substring test. They now pass `fixture.BOUND_COMPLAINT`, so the tests cannot silently diverge from the fixture again.

- [ ] Slice 6: action path, simulated provider, platform call + Gate A decision (**Gate A RAN AND PASSED 2 Oct 2026; see the Gate A section above**)
- [ ] **Slice 7: public deployment, the Next.js clinical frontend and auth (NEW 30 Sep, was not in the approved plan)**
- [ ] Slice 8: baseline instrument, the external card (C1, parallel). **Was Slice 7**
- [ ] Slice 9: Gate B, run the comparison (**kill test**). **Was Slice 8**
- [ ] Slice 10: Closure Contract in full (starts only after the kill test). **Was Slice 9**
- [ ] Slice 11: fault harness + seven sequences. **Was Slice 10**
- [ ] Slice 12: judge ledger, submission assets and the usage proof (**merge of old Slices 11 and 12**; must land before 16 October)
- [ ] **Slice 13: ADP interpretation surface (NEW, CONDITIONAL; Gate 2 gated, default do not run)**

**Carried decisions.** Five items from the Slice 2 review were deliberately left undecided. **Slice 3 settled the `source_ref` mutation gap** (see the Slice 3 section below), so four remain. Each is settled (or asked about) at the slice where it becomes live, and recorded there: F4 and the §2.2 amendment at **Slice 10** (Slice 9 before the 30 September 2026 renumber); F5 at **Slice 6**; F6 at **Slice 5**. The full list and the reasons are in the Slice 2 review section below.

## Slice 2 complete, 30 September 2026

**The pure decision layer exists, and constraint C7 is enforced by a check that has been seen to fail.** Branch `slice-2-domain-core`, created from `main` at `6e9be4f` before any edit, per `AGENTS.md` section 6 ("never begin slice work on `main`"). **Committed, merged and pushed on the user's explicit instruction, 30 September 2026.** The range is `6e9be4f..b19b36e`: five commits on `slice-2-domain-core` (domain core and its unit tests; the C7 boundary check; this record and the review note; the writing-convention lessons), fast-forwarded into `main`, then one record-correction commit made on `slice-3` and also fast-forwarded into `main`. `git log --oneline` lists each concern. `main` and `slice-3` sit at `b19b36e`; `slice-2-domain-core` sits at `80245e4`. **Pushed:** at the time, `origin/main` was at `b19b36e` and in sync with local `main` (0 ahead, 0 behind). That hash describes 30 September 2026 and has moved since; the branch tip is not restated as a hash here, because it goes stale on the next push. `AGENTS.md` section 3 records that no gate authorises a commit or push, so this was a user-authorised action rather than a gate authorisation.

| Evidence | Result |
|---|---|
| `pytest tests/` | **240 passed, 1 warning** (Slice 1 baseline: 11 passed; 109 at first completion, before the review added 131 checks) |
| `tests/test_domain.py` | **88 passed** |
| `tests/test_boundaries.py` | **141 passed** |
| `tests/test_api.py` | 11 passed, unchanged |
| **Boundary check seen RED** | `import socket` added to `rules.py` line 40. `test_domain_import_boundary` **FAILED**, naming the file, the line and the module: `rules.py:40: imports forbidden module 'socket'`. Removed; re-run green. `grep -rn "socket\|TEMPORARY" src/carerelay/domain/` returns nothing |
| Injection against the **real** file | `test_scanner_detects_an_injected_import_in_the_real_rules_file` prepends the forbidden import to the actual `rules.py` source and requires detection. A scanner proven only on toy strings proves nothing about the file it polices |
| One detector per forbidden form | `TestScannerHasTeeth` covers module import, `from` import, nested import, wall-clock call after a `from` import, wall-clock call through the module, `time` call, bare `open`, and a model-client import. `TestEveryDetectorIsPairedWithItsInput` iterates the three lists themselves, so **every** entry in `FORBIDDEN_MODULES`, `FORBIDDEN_CALLS` and `FORBIDDEN_CALL_SUFFIXES` now carries an input that must be caught. It also asserts the check is **not** a blanket ban that would forbid the imports `domain` legitimately needs |
| Line endings | New files are CRLF, matching every tracked file (`core.autocrlf=true`). Verified byte-wise: zero lone LF across all five. No line-ending damage |
| Secret and prohibited-content scan | Clean. The only match for "secret" is the stdlib `secrets` module inside the forbidden-import list. No credential-shaped string, no prohibited claim, no real facility or clinician name |

**Files created.** `src/carerelay/domain/__init__.py` (16 lines), `src/carerelay/domain/models.py` (393 lines), `src/carerelay/domain/rules.py` (610 lines), `tests/test_domain.py` (1357 lines), `tests/test_boundaries.py` (507 lines). Line counts are post-remediation.

**The five tests Gate 4 required to be fail-capable.**

| Test | Where | The defect it must catch |
|---|---|---|
| `test_domain_import_boundary` | `test_boundaries.py` | An SDK, network, database, filesystem or wall-clock import or call under `domain/`. Seen failing on a real injected `import socket` |
| `test_planback_known_match_mismatch_uncertain` | `test_domain.py` | **K1.** The six-entry adversarial corpus of correct restatements produces zero false mismatches. `TestPlanBackAssertionsHaveTeeth` swaps in four defective comparators (surface-only, always-uncertain, unknown-as-mismatch, drops-extractor-doubt) and requires the corpus to catch each. **Added at review:** a second, independently-chosen natural-phrasing corpus, because every entry in the original six turned out to be a literal key in one of the resolution tables, plus a test that an unresolvable phrase is `uncertain` and never `mismatched` |
| `test_closed_vocab_and_missing_is_not_negative` | `test_domain.py` | A hallucinated route or change code must stop, and a missing code must assert nothing. Every stop reason is exercised separately |
| `test_disposition_deadline_is_append_only` | `test_domain.py` | A retry that updates v1 or mints v2. Includes a structural scan proving `domain` constructs no `Disposition` at all, with its own teeth test |
| `test_hint_disclosure_accessibility` | `test_domain.py` | **C8.** Card visibility derived from the event vocabulary alone; `dwell_seconds` never changes the outcome; H3 is never a comprehension pass |

**K1 is now a domain test, not a spike result.** The comparator was moved from `spike/kill_spike/planback.py` rather than rewritten: the alias, relative-time and owner tables and the six-entry corpus are carried across, and the resolution logic is the spike's, widened per section 1.1. The spike directory is untouched and remains throwaway.

**Signature amendments carried from Gate 4 section 1.1, made explicit rather than silent.**

| Item | Gate 3 said | Implemented as | Why |
|---|---|---|---|
| `ExtractedPlan` field names | `action_id`, `deadline_utc`, `next_owner_id` | `action_span`, `deadline_span`, `next_owner_span` | Under Reading A the coordinator returns **raw text**, so the old names would have been false. Section 1.1 requires the raw span and the extractor's own uncertainty to be carried separately, and `uncertain_fields` is now a real field that outranks a resolvable span |
| `compare_plan` widening | `(expected, extracted, action_aliases)` | `(expected, extracted, *, policy, now_utc, display_tz)` | Section 1.1 widened the signature with `action_aliases`, `deadline_forms` and `owner_aliases` "as explicit policy data". All three are carried on one `PolicyFixture` value rather than three parallel mappings, so a policy has one source of truth |

**Three readings the approved documents leave open, plus one completion. Each is implemented, documented in `rules.py`, and flagged here so it can be corrected.**

| # | Reading | The alternative | Why this one |
|---|---|---|---|
| 1 | **Closure precedence: expiry outranks a recorded human acceptance.** The approved condition for `closed_with_evidence` is "evidence >= documented **or** an explicit human acceptance is recorded", and a human acceptance is not evidence that care happened. Once the deadline has passed with no evidence, the state is `expired_unresolved` | Put acceptance above expiry, so an accepted handoff stays `closed_with_evidence` past the deadline | The other order lets a scripted acceptance report a resolved episode whose deadline passed with nothing to show for it. That is invariant I2, and it is the product thesis. **This is the one reading most worth an explicit yes or no** |
| 2 | **Line 2 is composed by owner.** "You must act now." when the owner is the patient; the approved "You or [named person] must act now." otherwise | Reproduce the approved literal, which yields the malformed "You or you must act now." that Slice 1 found by inspection | Carries the Slice 1 divergence forward instead of reintroducing the defect. The Slice 1 note still stands: Slice 10 implements whichever form the documents then carry |
| 3 | **`patient_lines` refuses for `closed_with_evidence`.** It raises `NoApprovedPatientWording` | Render the unresolved four lines | No approved rendering exists for a resolved episode. Rendering "Help is not arranged." over an episode where care is evidenced is a false statement to the patient. Slice 10 owns the Closure Contract rendering |
| 4 | **Execution axis completion.** `expired` is set on axis A when an attempt recorded no terminal outcome and the deadline has passed. A recorded `acknowledged`, `failed` or `superseded` outcome is never overwritten, and an episode with no attempt stays `not_started` | Leave `expired` unwired | Contract section 2.2 lists `expired` as an axis value. Left unwired it was unreachable vocabulary, and "we tried and nobody said yes, and the deadline has gone" had no rendering on axis A at all. Found by the post-slice cleanup scan, not by the tests |

**Two defects the post-slice cleanup scan found in this slice's own code, both fixed.** `models.DisplayZone` was defined and never used: removed, along with its now-unused `tzinfo` import. `ExecutionStatus.EXPIRED` was unreachable: reading 4 above wires it, with three tests (the attempt-with-no-outcome case, the recorded-terminal case, and the no-attempt case) each covering a distinct guard.

**The em dash question is settled by measurement, and the original claim was wrong.** The source contains **no** em dash character at all: line 4 of the expired rendering is written as the escape `\u2014`, so the rendered string reproduces the approved copy verbatim while the file stays clean of U+2014. `AGENTS.md` section 6 is therefore not breached and no approved clinical wording has drifted. Verified byte-wise across all five new files: zero U+2014. The first version of this entry said "one em dash is used", which overstated the problem.

**Not in this slice, and deliberately.** No database (Slice 3). No routes, no service, no coordinator. No `presentation.py` or `templates/` (the plan-versus-code drift recorded earlier today is ~~untouched~~ **closed by decision later the same day; see the Gate reopening section at the top of this file**. `04-slices.md` ~~still names~~ **no longer names** `src/carerelay/templates/patient.html`, which does not exist, and `jinja2` is ~~still imported nowhere~~ **to be removed from `pyproject.toml`**). The Option C source is still unselected, so every alias table and every corpus entry here is **provisional** and nothing may be shown to a participant.

**What this evidence does not prove.** A passing static check is not evidence of WorkBuddy access, clinical safety, human learning or patient benefit. K1 remains a deterministic-layer result and depends on Reading A (ADR-0007, risk R5). The 88 domain tests exercise the pure layer only: the model's own extraction is not reachable offline.

## Slice 2 adversarial review and remediation (30 September 2026)

An independent adversarial review with no prior context was run against the branch, from the brief at `04-slices.md` (Slice 2). Full note: **`docs/reviews/slice2-adversarial-review.md`**. Verdict: **the exit contract is met, with named caveats.**

**Two blockers were found and fixed, both real.**

| # | Defect | Fix |
|---|---|---|
| 1 | `patient_lines` rendered `PolicyText.deadline_display` verbatim, decoupled from `disposition.clinical_deadline_utc`. A reassessed disposition (deadline 1 Oct) rendered line 3 as "Before 6:00 PM on 30 September." That is a false statement to the patient, and it breaks approved copy rule 5 in `02-architecture.md` section 7 | `PolicyText.deadline_display` is now `deadline_display_by_version`, keyed by disposition version, mirroring `owner_display_by_id` and `route_display_by_id`. An unworded version raises `MissingDisplayText` instead of printing a stale date |
| 2 | This entry claimed the new files were CRLF and matched every tracked file. They were pure LF | The five new files were normalised to CRLF, which is what the entry intended and what every tracked file uses. Verified byte-wise: zero lone LF |

**The review's highest-ranked risk was confirmed.** The boundary scanner was evadable in five ways, all of which reached a filesystem, a network, a database or the clock without importing a forbidden module: `__builtins__["open"](...)`, `builtins.open(...)`, `builtins.__import__("socket")`, `builtins.__import__("sqlite3")`, and `getattr(datetime, "now")()`. Root cause: `_dotted_name` returned `""` for any call whose `func` was itself a call, a subscript or a lambda, and the scanner skipped those. Fixed by refusing a dynamically produced call target and by adding `builtins` and `sys` to `FORBIDDEN_MODULES`. All five are now caught and each has its own regression test.

**Four further defects fixed.** `project_attempt` raised only on the lowest-`seq` row, so a corrupt row at a higher `seq` was silently ignored, contradicting its own docstring; every row is now validated. `derive_closure` returned `expired_unresolved` with no named owner when an expiry event arrived with no disposition, which I4 forbids; that is now refused. The K1 corpus was found to be self-serving, since all six entries are literal keys in the resolution tables; a second, independently-chosen natural-phrasing corpus was added, together with a test that an unresolvable phrase stays `uncertain` and never becomes a mismatch. Two docstrings claimed full detector coverage that the tests did not provide (deleting `"eval"` and `".today"` from the lists left the suite green); three parametrised tests now iterate the lists themselves.

**Five findings were deliberately left open**, because each needs a product, clinical or documentary decision rather than a code fix.

**They are not decided now. Standing instruction (user, 30 September 2026): each is decided (or put to the user as a question) at the slice where it first becomes live, and the decision is recorded here in that slice's section.** No later slice may silently implement one of these while building an earlier one.

| # | Open question | Decided at |
|---|---|---|
| F4 | `closed_with_evidence` is reachable both from real evidence and from a recorded human acceptance with no evidence, and `patient_lines` raises for both. The acceptance case is a normal product state (`POST /acceptances`) with no patient rendering at all. Slice 10 must render it, and must render the two cases separately | **Slice 10** |
| F5 | `simulated = not care_evidenced` conflates "this episode is a simulation" with "care is not evidenced". The code implements the D11 rule as written, so the meaning is a decision, not a defect | **Slice 6**, visible in the ledger at **Slice 12** |
| F6 | `action_owner_id` ignores `escalation_id` and `human_acceptance_id`, so I4's "explicit human service" owner is inexpressible | **Slice 5**, re-checked at **Slice 10** |
| §2.2 | The `closed_with_evidence` and `expired_unresolved` rows of `03-planback-closure-contract.md` section 2.2 overlap on acceptance plus past-deadline and state no order; the implementation puts expiry first. This is the documentary form of the F4 decision | **Slice 10** |
| `source_ref` | The D11 guard's `simulated` and `source_ref` halves share one mutation flag, so the `source_ref` half has no independent proof | **Slice 3** |

**Evidence.** 240 passed, 1 warning (88 domain, 141 boundaries, 11 api), up from 109. Five mutation checks confirmed the new tests are fail-capable: reverting each fix in turn caused its paired test to fail. Every mutation was reverted with an md5 check, and `git status --short --untracked-files=all` was identical before and after. No commit, branch or push was made **during the review itself**, and no gate was reopened. The work was committed afterwards, the same day, on the user's explicit instruction; see the commit list in the Slice 2 section above.

## Slice 3 complete, 30 September 2026

**The clinical record persists, and ordinary `UPDATE` and `DELETE` have no path through it.** `src/carerelay/state.py` implements the thirteen tables of `02-architecture.md` sections 4.1 and 4.2 behind repository methods, on SQLite with WAL and a busy timeout. Append-only is not a convention here: `BEFORE UPDATE` and `BEFORE DELETE` triggers are generated for **every** table, and the test that proves it opens its own raw connection and issues raw SQL, so this module's own guards are not in the loop. **Amended 30 September 2026 (Slice 3 review F1, closed as O1):** the triggers now refuse `INSERT OR REPLACE` as well, on every connection this module opens, and the claim is scoped to that rather than to "the database has no update path". The distinction is measured, not stylistic: the pragma that makes a `REPLACE` fire the `BEFORE DELETE` trigger is per-connection, so a connection opened outside this module still rewrites a row. See the Slice 3 remediation section below.

**Branch `slice-3`, already the working branch when the slice began. Committed on this branch on the user's explicit instruction, 30 September 2026, and fast-forwarded into `main` the same day, then pushed.** Two new code files, `src/carerelay/state.py` and `tests/test_state.py`; three code files edited, `src/carerelay/domain/models.py`, `tests/test_domain.py` and `src/carerelay/api.py`; the documentation restructured: `AGENTS.md`, `PROGRESS.md`, `00-status.md` and `tasks/todo.md`, plus the new `docs/README.md` and four review files moved into `docs/reviews/`. `slice-3` now has an upstream of its own: it was published to `origin` on the user's instruction of 30 September 2026, so the Slice 3 work reached the remote through `main` and through `slice-3`. Until then it had none, and reached the remote through `main` alone.

**Correction, 30 September 2026 (Slice 3 review, F3).** This row previously asserted that `git status --short --untracked-files=all` "lists exactly ten paths and nothing else", and named `slice-3-review-prompt.md` as the tenth. That file does not exist, and the tree held **nine** paths. This is the second consecutive slice whose version of this row was wrong: the Slice 2 row claimed four paths when the tree held nine. **The count has been removed rather than corrected.** A working-tree count is falsified by the next edit, including an edit made while writing the review, so it is not a durable claim and does not belong in this document. The file lists above are the durable form.

| Evidence | Result |
|---|---|
| `pytest tests/` | **310 passed, 1 warning** at Slice 3 completion, **332** after the remediation below (Slice 2 baseline: 240). Per file after the remediation: **89** domain, **141** boundaries, **11** api, **91** state. The four counts sum to 332, the total. **Corrected 30 September 2026 (Slice 3 review, F2):** this row read 88 domain and asserted the four counts summed to the total, but 88+141+11+69 is 309. The domain figure was Slice 2's stale count; this slice added `test_the_source_ref_half_of_the_guard_is_independently_proven` to `test_domain.py`, taking it to 89 |
| **Every new guard seen RED, one at a time** | Eleven mutations of the guards, each applied alone to one anchor and each reverted with an md5 check. **All eleven made their paired test fail.** `md5 unchanged for every file: True`, and the suite returned to 310 passed afterwards. The mutations: the append-only triggers, the D11 Python guard, the D11 database `CHECK`, the consent re-check, expiry stickiness, the premature-expiry guard, duplicate detection, the attempt idempotency lookup, the transaction rollback, disposition-version monotonicity, and the `source_ref` flag below |
| **The concurrency claim, mutation-proven** | Two further mutations target the concurrency mechanism itself, not the guards. `BEGIN IMMEDIATE` appears once as executable code, inside the shared `_write` helper, so this is one mutation applied to several tests rather than several independent mutations. Changing it to a deferred `BEGIN` turns **both** race tests RED, and a `busy_timeout` of `0` turns **both** race tests RED as well (measured three times on 30 September 2026; this row said the callback race only), while in both cases the single-writer control tests stay GREEN. That control is what makes the result mean something: a mutation that also breaks single-writer writes would prove nothing about concurrency. The failure mode under a deferred `BEGIN` is `[OperationalError('database is locked'), True]`, one writer crashing on the lock upgrade instead of returning the correct duplicate-suppression answer. See the R6 row below |
| Append-only, proven against the schema | Raw `UPDATE` and raw `DELETE` refused on **all thirteen** tables, one parametrised case per table per verb. A row is seeded into every table first, because a `BEFORE UPDATE` trigger fires per row and an update against an empty table would prove nothing |
| The append-only control case | Dropping two triggers lets the same `UPDATE` and `DELETE` succeed, so the refusal is the triggers and not something incidental |
| `INSERT OR REPLACE` refused (O1, added 30 Sep) | Raw `INSERT OR REPLACE` refused on **all thirteen** tables, issued on the store's **own** connection so the test fails if `__init__` stops setting the pragma. The control reproduces the original defect with the pragma off: the same statement rewrites `dispositions.clinical_deadline_utc` to `1999-01-01` |
| The five untested constraints are now fail-capable (O3, added 30 Sep) | One test per constraint, each violating **exactly one** so disabling that constraint is the only way to turn its test red. The three `callbacks` CHECKs overlap, so each violating row is built to satisfy the other two |
| NULL distinctness proven rather than assumed (O4, added 30 Sep) | One key delivered three times writes three receipts, two of them with a null `callback_key`. The control shows the same column refuses a repeated non-null key, so the nulls coexist because they are distinct and not because the constraint is missing |
| D11 `CHECK`, independent of the Python guard | A raw `INSERT` of a simulated or unsourced `documented` row raises `IntegrityError`. A control table that is the same minus the `CHECK` accepts the identical row, and the refused half is now issued inside that same test (Slice 3 review F9) |
| D11 `CHECK` and the Python guard are equivalent (O6, added 30 Sep) | A `NULL`, empty or whitespace-only `source_ref` is refused by both layers. The guard refused `''` but accepted `'   '`, so "enforced twice" was true for a null reference only |
| **R6, two concurrent writers** | Two connections in two threads, one callback key, a `Barrier` so both arrive together. `sorted(outcomes) == [False, True]`: exactly one receipt applied, one recorded as a duplicate of it, one transition appended. The same construction for expiry yields exactly one event. **The mechanism is `BEGIN IMMEDIATE`, and that is now mutation-proven rather than asserted.** With a deferred `BEGIN` the second writer does not produce a wrong duplicate, it crashes with `OperationalError('database is locked')` on the lock upgrade, so the correct idempotent answer is lost. The race tests are what detect this; the single-writer controls are not disturbed, which is why the detection is attributable to concurrency and not to a broken write path |
| Crash atomicity | With the audit write made to raise, the attempt row and its event both roll back and the key is not poisoned. With the transition append made to raise, neither the receipt nor the transition survives |
| The Slice 2 review's `source_ref` gap | **Closed here.** `mutated_closure` now carries two named flags, one per half of the D11 guard, so neither subsumes the other. The new test fails when the flag is reverted to the Slice 2 form |
| Line endings | Both new files normalised to CRLF after writing and verified byte-wise: **zero lone LF**. The three edited code files were already CRLF and the editor preserved them. (This row said "the two edited files"; three code files were edited) |
| Em dashes | **Zero U+2014** in the two new files and in the three edited code files. `src/carerelay/api.py` carries 5 pre-existing U+2014, none added by this slice; across every edited code file the net change in em dash characters is 0. **Corrected 30 September 2026 (Slice 3 review, F12):** this row said "all four files this slice touched" when five code files were touched |
| Secret and prohibited-content scan | Clean. The only match for "secret" is a comment about a server-held secret at Slice 6. No credential, no real facility or clinician name |

**The five tests Gate 4 required to be fail-capable.**

| Test | What it proves |
|---|---|
| `test_attempt_open_atomic_and_double_tap` | One attempt and one audit row for one `(episode, route, purpose)` triple, however many times it is tapped. A crash between the attempt row and its audit row rolls both back and leaves the key usable |
| `test_callback_duplicate_and_reorder` | Every receipt is auditable; a duplicate appends no transition; a late acknowledgement is retained and non-winning because its `seq` is higher |
| `test_consent_revoke_in_flight` | Revocation blocks dispatch, callback success and evidence recording, and the refused receipt is still written with a reason, so the failure is visible rather than absent |
| `test_evidence_provenance_constraint` | A simulated or unsourced row cannot be `documented`, in Python and in the schema, each proven separately |
| `test_expiry_sticky_after_clock_regression` | The first overdue read persists expiry; a backwards clock cannot return the disposition to `open` |

**Files created.** `src/carerelay/state.py`, `tests/test_state.py`. **Files edited.** `src/carerelay/domain/models.py` (the two Gate 3 value types below), `tests/test_domain.py` (the `source_ref` flag), `src/carerelay/api.py` (one comment that this slice made false).

**Two Gate 3 value types were missing and are added here.** `03-program-design.md` section 3 names `AttemptCommand` and `CallbackResult`; Slice 2 did not need either, and the store protocol cannot be written without both. They are frozen values in `domain/models.py`, with no I/O, so nothing about the D2 boundary changes.

**Ten readings the approved documents leave open. Each is implemented, documented in `state.py`, and flagged here so it can be corrected.**

| # | Reading | The alternative | Why this one |
|---|---|---|---|
| 1 | **Every table is insert-only**, not only the four clinical tables D3 names | Enforce on `dispositions`, `attempt_transitions`, `evidence` and `consents` only | Nothing in the product has a legitimate UPDATE or DELETE, and a rule with exceptions is a rule someone finds the exception for. The strongest form is also the easiest to state and to test |
| 2 | **`callback_key_digest` is stored for every receipt; a duplicate's `callback_key` is NULL** | Store the received key in plaintext on the duplicate row as well | `03-program-design.md` section 3 requires the received key to be retained "only in a redacted or hashed audit field". The digest gives the audit trail without a second plaintext copy |
| 3 | **A refused receipt is written with `accepted = 0` and a `rejection_reason`** | Refuse and record nothing, or record a bare `accepted = 0` | "Records every callback received, including rejected duplicates" is in the approved schema. A bare flag leaves "why was this not applied" unanswerable, and the ledger is the artefact that has to answer it. `rejection_reason` is a column the approved column list does not name |
| 4 | **`record_expiry_once` refuses a premature event** | Record whatever the caller asks for | A premature expiry event tells a patient their window is gone while they still have time. That is a false statement of exactly the kind the product exists to prevent, and the store is the narrowest layer that can refuse it |
| 5 | **The existing-event check runs before the overdue check** | Check the deadline first | After a clock regression the deadline is in the future while the event is a fact that already happened. Checking the deadline first would raise `PrematureExpiry` on a sticky episode, which is the opposite of D12 |
| 6 | **The snapshot reports the expiry event for the current disposition version** | Report the latest expiry event for the episode, whatever version it names | An expiry event records that one version's deadline passed. A reassessment inserts a new version with a new deadline, so the earlier event no longer describes the current plan. The row is never deleted and stays in the ledger. Within one version, D12 stickiness is exactly as written. **This is the reading most worth an explicit yes or no** |
| 7 | **`attempts.purpose_id` is a stored column** | Derive the key from `(episode, route)` only | D5 derives the key from `(episode, route, attempt-purpose)`, and an authorised retry is a new purpose. Without the column the triple is not auditable from the record |
| 8 | **`dispositions` versions must be contiguous from 1** | Rely on `UNIQUE (episode_id, version_no)` alone | A gap means a version was rewritten rather than appended, which is the one thing the deadline invariant cannot survive |
| 9 | **The snapshot's attempt is the latest one** | Refuse to project when more than one attempt exists | `EpisodeSnapshot` carries a single attempt and the latest is the one the patient is waiting on. A retry legitimately creates a second |
| 10 | **`state.py` derives the attempt key** (`derive_attempt_key`) | Leave key derivation entirely to the service | D5's double-tap semantics only work if the key is a deterministic function of the triple. The function is small, pure and testable here, and without it the double-tap test would prove nothing about the key. A server-held secret can be folded in at Slice 6 without changing the signature |

**The `source_ref` gap is settled, and this is the decision.** The Slice 2 review recorded that one mutation flag disabled both halves of the D11 guard, so the `source_ref` half had no independent proof. `mutated_closure` in `tests/test_domain.py` now has two flags: `trust_simulated_evidence` removes the `simulated` half only, `trust_unsourced_evidence` removes the `source_ref` half only. The new test requires three things at once: the guard holds as written; removing the `source_ref` half alone lets an unsourced row through; and removing the `simulated` half alone does **not**. No product code changed, and no clinical wording was touched.

**This slice's exit check, run and shown.** A duplicate callback delivered with a contradictory claim (the first receipt says `failed`, the duplicate says `acknowledged`):

```
1. THE ATTEMPT IS OPENED ONCE, HOWEVER MANY TIMES IT IS TAPPED
   first open        attempt 9d3d9d2fd2c0  execution=attempted
   second open       attempt 9d3d9d2fd2c0  execution=attempted
   attempt rows in the record: 1
   audit rows: ['episode_created', 'disposition_recorded', 'consent_changed',
                'attempt_opened', 'attempt_duplicate_suppressed']

2. THE SCRIPTED FAILURE ARRIVES (origin = platform)
   applied: True
     line 1: Help is not arranged.
     line 2: You must act now.
     line 3: Before 6:00 PM on 1 October.
     line 4: If this route fails, call the fictional nurse line.
   closure=open  execution=failed  care_evidenced=False

3. THE SAME CALLBACK IS DELIVERED AGAIN, CLAIMING SUCCESS INSTEAD
   applied: False
   patient screen unchanged: True
   transitions appended: ['failed']

4. BOTH RECEIPTS ARE IN THE RECORD
    id            key dup_of accepted  reason
     1  callback-0001   None     True  None
     2         (null)      1    False  duplicate

5. THE RECORD HAS NO UPDATE PATH AND NO DELETE PATH
   REFUSED  UPDATE attempt_transitions SET transition = 'acknowledged'
             -> attempt_transitions is append-only: UPDATE is refused
   REFUSED  DELETE FROM callbacks
             -> callbacks is append-only: DELETE is refused
   REFUSED  UPDATE dispositions SET clinical_deadline_utc = '1999-01-01T00:00:00+00:00'
             -> dispositions is append-only: UPDATE is refused
```

**Corrected 30 September 2026 (Slice 3 review F1, closed as O1).** Step 5's heading is the script's, and it claimed more than the three statements under it show: all three are `UPDATE` or `DELETE`, and `INSERT OR REPLACE`, which rewrote the same deadline with the triggers in place, was never tried. The remediation section below closes it, and the exit check now has a `REPLACE` case per table with a control that reproduces the original defect.

**Not in this slice, and deliberately.** No routes, no service, no coordinator, no `presentation.py`, no templates, no ledger, no `tools.py`. `restatements` exists as a table with no write path, because the slice plan names it in this slice's deliverable; Slice 4 writes it. `api.py` still serves its Slice 1 in-memory episode and is not wired to the store: wiring the API is not in this slice's file list, and the comment there now says so. The Option C source is still unselected, so every string in the fixture remains provisional.

**What this evidence does not prove.** A green suite is not evidence of WorkBuddy access, clinical safety, human learning or patient benefit. No route, service or coordinator exists, so nothing here has been exercised end to end. The two-writer tests use threads in one process on one machine: they prove `BEGIN IMMEDIATE` plus the busy timeout serialises the lookup and the insert (now mutation-proven, see the concurrency row above), not that the design survives a hostile multi-process load. The append-only triggers refuse `UPDATE` and `DELETE` from any connection, and they refuse `INSERT OR REPLACE` on any connection this module opens; that second half rests on a per-connection pragma, so the claim is scoped in the Slice 3 opening paragraph rather than stated unconditionally. O1 is closed in the remediation section below. They also do not protect against someone who drops a trigger, and the control case in the tests shows exactly that. Separately, a real four-process race on one key yields exactly one applied receipt, and a real process kill mid-transaction is recovered by WAL with `integrity_check` ok, so the concurrency mechanism is stronger than the thread-only tests show while the multi-machine case stays untested.

### Slice 3 adversarial review, 30 September 2026

**Verdict: the slice serves its purpose, with named caveats.** An independent adversarial review with no prior context was run against the branch, from the brief at `04-slices.md` (Slice 3). Full note: `docs/reviews/slice3-adversarial-review.md`. It re-ran five of the thirteen reported guard mutations and confirmed all five were real, went red alone, and reverted with an md5 match. Two of the reviewer's own first attempts were invalid and were re-run, which is recorded because a mutation experiment fails silently when the anchor or the test selection is not asserted.

**What it confirmed.** The raw-SQL append-only proof and its control case; the DELETE-trigger generation attributing exactly 13 `refuses_delete` failures with the 13 `refuses_update` cases green; `BEGIN IMMEDIATE` as load-bearing with green single-writer controls; D11 enforced twice **and independently**, since removing either half alone fails only its own test; the `source_ref` split; 310 passing; 1280 and 1136 lines; 69 state tests; zero lone LF; thirteen tables matching `04-slices.md`; the five Gate 4 named tests; `restatements` with no writer; `api.py` unwired.

**Two blocking findings.** F1, the `INSERT OR REPLACE` gap, is corrected in the opening claim of the Slice 3 section above and carried as O1 below. F2, the per-file split, is corrected in the evidence table above.

**Open items this review raised.** These are defects and test gaps rather than product decisions, so they are recorded here and not in the Slice 2 open-questions table above. No later slice may silently implement one early.

| # | Open item | Status |
|---|---|---|
| O1 | **`INSERT OR REPLACE` rewrites any row, including `dispositions.clinical_deadline_utc`, defeating I1's structural protection.** Fix: `PRAGMA recursive_triggers = ON` in `SqliteEpisodeStore.__init__` plus a `REPLACE` case in the parametrised append-only test | **CLOSED 30 September 2026**, before Slice 4 began. Both halves applied, plus a control that reproduces the original defect and a corrected claim. See the remediation section |
| O2 | Contention past the 5 s busy timeout makes `record_callback_once` raise a raw `sqlite3.OperationalError` and write no receipt, while the docstring at `state.py:437-439` says the losing callback is never lost. Fix: qualify the docstring and make lock contention a typed `StateError`, so a caller can tell "retry" from "refuse" | **PARTLY CLOSED 30 September 2026.** The docstring now states the bound. The typed `StateError` remains, at **Slice 6**, where the action path consumes the return value |
| O3 | Five schema constraints have no fail-capable test: the three `CHECK`s on `callbacks` (`state.py:301`, `:302`, `:303`), the `restatements.hint_level` `CHECK` (`:355`) and `UNIQUE (episode_id, version_no)` on `dispositions` (`:261`). Neutralising each alone left all 69 tests green. The `:303` constraint is the formal statement of the duplicate representation | **CLOSED 30 September 2026.** Five tests, each violating exactly one constraint, each confirmed to go red alone. See the remediation section |
| O4 | The duplicate representation rests on SQLite treating NULLs as distinct in a UNIQUE column. Documented at `state.py:17`, but no test creates more than one NULL-key row, so a suite that would pass under equal-NULL semantics proves nothing about the assumption it rests on | **CLOSED 30 September 2026.** One key delivered three times, with a control proving the column refuses a repeated non-null key |
| O5 | `record_callback_once` returns a bare `bool`, so a duplicate and a consent refusal are indistinguishable without re-reading the record. A bool cannot express "we refused a success because consent was revoked" | **Slice 6**, where the action path consumes it. Untouched here: it is a return-surface decision, not a defect to patch |
| O6 | The D11 `CHECK` is weaker than the Python guard: an empty or whitespace `source_ref` passes the `CHECK` while the guard refuses it, so "enforced twice" is only equivalent for `source_ref IS NULL` | **CLOSED 30 September 2026.** `trim(source_ref) <> ''` added to the `CHECK`, and the guard widened from `not source_ref` to `not source_ref.strip()`, so the two are equivalent for blank as well as null |
| O7 | `insert_disposition` does not require a reassessment to move the deadline later. A version 2 with an earlier deadline than an expired version 1 would make reading 6 report no expiry event and could return the episode to `open` | **Slice 5**, where reassessment is built. Untouched here: there is no reassessment path to constrain yet |
| O8 | The "Crash atomicity" row above tests the in-process rollback path, not a crash. A subprocess kill mid-transaction was verified separately to be recovered by WAL, so the property holds; the row label and the test's reach overstate it | **Slice 11**, the fault harness (Slice 10 before the 30 September 2026 renumber). Untouched here: a subprocess-kill test belongs with the rest of the fault work |

**Note on the exit check.** `04-slices.md`'s Check for this slice, "show the user a duplicate callback being recorded and the projection not changing", was run at the store layer and shown as console output above. It could not be run through the product, because this slice's file list is `state.py` and `test_state.py` only and the routes arrive at Slices 4 to 6. The gap is the plan's, and it is recorded rather than papered over.

### Slice 3 remediation, 30 September 2026

**The blocking finding is closed, and four more with it, before Slice 4 begins.** Applied on the user's instruction of 30 September 2026 to fix what the review left open. Two code files changed, `src/carerelay/state.py` and `tests/test_state.py`, plus four record files (`00-status.md`, `PROGRESS.md`, `tasks/todo.md`, `tasks/lessons.md`). No behaviour changed except two new refusals of statements that should never have been accepted: `INSERT OR REPLACE`, and a blank `source_ref` on a `documented` row.

| Open item | What was done |
|---|---|
| **O1** | `PRAGMA recursive_triggers = ON` in `SqliteEpisodeStore.__init__`, so the implicit delete a `REPLACE` performs now goes through the `BEFORE DELETE` trigger. Thirteen new parametrised cases, one per table, issued on the store's **own** connection so the test fails if the pragma line is removed, plus a control that reproduces the original defect with the pragma off |
| **O3** | Five fail-capable tests, one per constraint. Each violating row is built to break **exactly one** constraint, which the three overlapping `callbacks` CHECKs make non-trivial: a row that broke two would keep the suite green when either was removed |
| **O4** | One key delivered three times writes three receipts, two of them with a null `callback_key`, with a control showing the same column refuses a repeated non-null key |
| **O6** | `trim(source_ref) <> ''` added to the `evidence` CHECK, and the Python guard widened from `not source_ref` to `not source_ref.strip()`. The guard refused `''` but accepted `'   '`, so the two layers were equivalent for a null reference only. The fix widens the guard rather than narrowing the `CHECK`, so both layers refuse the same three forms |
| **O2** | Partly. The class and `_write` docstrings no longer claim the losing callback is never lost; they state that the wait is bounded by `busy_timeout_ms` and that past it the write fails loudly and writes nothing. The typed `StateError` stays at Slice 6 as recorded |
| **F9** (minor) | `test_the_check_is_what_refuses_the_row` now issues the refused `INSERT` itself instead of asserting only that the control table accepts it, so it detects the `CHECK`'s absence rather than claiming to |

**A stronger guard was measured and rejected, not overlooked.** A `BEFORE INSERT` trigger that refuses a colliding insert would close the hole for *any* connection, which the pragma does not. It also refuses `INSERT OR IGNORE`: a `BEFORE INSERT` trigger cannot see the statement's conflict clause, and `RAISE(ABORT)` is not overridden by `OR IGNORE`. Measured 30 September 2026. The false positive would refuse harmless idempotent inserts, including the one this suite's own seeding helper uses, so the pragma plus an honest claim is the correct answer rather than the weaker one. The alternative that does close it per-connection, a `set_authorizer` callback, remains available if a future slice opens the file outside this module.

**Evidence.** 332 passed, 1 warning, split **89** domain, **141** boundaries, **11** api, **91** state; the four counts sum to 332. Eight mutations, each applied alone to an anchor asserted to occur exactly once, each reverted with an md5 match, and each turning exactly its own test red: the pragma (14 red, the thirteen tables plus the control), each of the five constraints (1 red each), the `trim` clause (2 red, one per blank form), and the `callbacks` UNIQUE on `callback_key` (1 red). The suite returned to 332 afterwards. Both edited files are CRLF with zero lone LF and zero U+2014.

**Still open, and deliberately untouched.** O5 (the `bool` return) and O7 (the reassessment deadline ordering) are product decisions for Slices 6 and 5. O8 (the crash-atomicity label) belongs with the **Slice 11** fault harness (Slice 10 before the 30 September 2026 renumber). F4's typed lock error is the half of O2 above. None of these is a false claim left standing.

**Committed on `slice-3` and fast-forwarded into `main`**, in two commits: the code, then this record. `origin` holds both `main` and `slice-3`, each in sync with its local branch. They no longer point at the same commit: `slice-3` was frozen when the slice closed, and `main` has carried later work since. No hash is cited here on purpose: a hash in this file goes stale on the next push, and that correction has already been needed twice.

## Slice 4 COMPLETE, 1 October 2026

**PlanBack runs end to end against real state: coordinator extracts raw spans, `domain` resolves and compares, the record holds every round, and the repair loop is bounded at two.** The slice's Check was run live on 1 October 2026 and the user walked through the result, so the slice is complete. Transcript: `docs/reviews/slice4-walkthrough.md`.

**What the Check showed.** 383 passed, re-verified first. Then over HTTP against uvicorn on 127.0.0.1:8017: an unbound complaint stops at 422 with `stopped_at: human_path`; the bound complaint issues disposition v1; H0 and H2 events leave the card visible through a 900 second dwell and only `patient_hid` hides it; a voice restatement with no confirmation is 409 and with one is scored; round 0 mismatches on `deadline_utc`; repair round 1 fixing the deadline is a clean pass recording `recall_unaided`; a second ladder fails through rounds 0, 1 and 2 and round 2 sets `routes_to_human_path` with `human_path_route_id = nurse_line`; a fourth call is 409; a repair against a superseded round is 409 `StaleRestatement`; and the same clean text records `recall_unaided` at H0 and `not_recalled` at H3. `events.payload` holds `dwell_seconds` 45.5 and 900.0 for the two H2 shown events, and no patient response in the run contains the string `dwell`.

**The stop condition is met structurally, not by demonstration.** No route in this slice returns hint text: `POST /hint-events` answers with the rung and the card's visibility, so there is no surface from which H0 to H2 could leak a critical field. The real hint copy does not exist yet. When it is authored it is Gate 1 content and is checked against this rule.

**Branch `slice-4`, recreated from the tip of `main` on the user's instruction of 30 September 2026.** It had previously been created ahead of the slice at `82df9ee`, which was **nine commits behind `main`**. That is a ship hazard, not a cosmetic one: `git merge-base --is-ancestor main slice-4` failed, so once the slice had commits, `git merge --ff-only` into `main` could not succeed. It was recreated with `git branch -f slice-4 main` after verifying that `git log main..slice-4` was empty (no unique commits to lose) and that `git ls-remote --heads origin slice-4` returned nothing (no remote to orphan). **Lesson for the next slice: do not pre-create a slice branch.** The `AGENTS.md` rule now says to create it from the current tip of `main`, but it does not name this failure mode, and it should.

| Exit contract line | Where it lives | Proof |
|---|---|---|
| `POST /restatements` | `api.py::submit_restatement` | `test_service.py::TestTranscriptOrderAndRepairCap`, `test_api.py::TestPlanBackRouteContracts` |
| `POST /restatements/{rid}/repairs` | `api.py::repair_restatement` | `test_two_repairs_then_the_human_path` (API) and `test_two_repairs_is_the_maximum` (service) |
| `POST /hint-events` | `api.py::record_hint_event` | `TestHintLadder`, plus `test_the_hint_event_response_carries_no_dwell_marker` |
| `POST /transcript-confirmations` | `api.py::confirm_transcript` | `TestTranscriptConfirmationRoute` |
| Coordinator extracts raw spans, `domain` resolves and compares (Reading A) | `coordinator.py::LocalSimulationCoordinator`, `rules.compare_plan` | The coordinator returns spans only and never sees the disposition (`_allowed_values`); ADR-0007 |
| H0 to H3 recorded | `state.py::record_restatement`, `restatements.hint_level` | `test_the_record_carries_the_hint_level_and_the_round`, **parametrised over all four rungs on 1 October 2026**. As implemented on 30 September it exercised H2 only, so the `H1` mapping was unproven and a changed `H1` entry broke no test. Corrected, with the mutation recorded, in the Slice 4 review and remediation section below |
| H2 stays until the patient hides it | `service.hint_state`, folded through `rules.hint_transition` | `test_the_card_stays_visible_until_the_patient_hides_it`, `test_a_dwell_only_difference_changes_nothing` |
| `dwell_seconds` to the ledger only | `events.payload` for `hint_event` rows; absent from every patient response | `TestPatientSurfaceHasNoDwell` (API) and `test_dwell_seconds_is_recorded_for_the_ledger_only` |
| H3 is `not_recalled`, never a pass | `service._score` | `test_h3_is_not_recalled_even_when_its_comparison_is_clean` |
| Two repairs maximum, third routes to the human path (C6) | `service.repair_restatement`, `state.record_restatement` | Cap plus `routes_to_human_path=True` and `human_path_route_id` at round 2; a fourth call is 409 |
| Coordinator unavailable stops the flow | `api.py::_coordinator_down` | `TestCoordinatorUnavailable`: 503 with `scored: False`, and **no row written** |

| Evidence | Result |
|---|---|
| `pytest tests/` | **380 passed, 1 warning**, up from 332. Per file: **95** domain, **141** boundaries, **25** api, **91** state, **28** service. The five counts sum to 380 |
| Line endings | Zero lone LF across the ten touched files, verified byte-wise |
| Em dashes | Zero U+2014 on any added line, verified with `git diff -U0` |
| The Check, a live walkthrough with the user | **Run 1 October 2026 against a running server, and walked through with the user the same day.** A mismatch names `deadline_utc`; repair 1 fixes that field and is a clean pass; a second ladder fails through rounds 0, 1 and 2 and round 2 sets `routes_to_human_path` with `human_path_route_id = nurse_line`; a fourth call is 409. Transcript: `docs/reviews/slice4-walkthrough.md` |

**Two defects found during the build, both fixed, both real.**

| # | Defect | Fix |
|---|---|---|
| 1 | **The repair cap was evadable.** Every round is its own row, so re-repairing round zero forever produced round 1 forever and the two-repair cap never bit | `repair_restatement` now requires the parent to be the **latest** round and raises `StaleRestatement` otherwise. `test_without_the_stale_check_a_forked_repair_is_accepted` proves the check is what stops it |
| 2 | **The confirmation digest was never computed.** `_require_scorable` took a parameter named `transcript_confirmation_id`, which shadowed the imported function of the same name, so the binding check called the string instead. Found because the voice tests failed, not by inspection | The import is aliased to `derive_confirmation_id`, with a comment saying why |

**Five things Slice 4 did that the plan's file list does not name. Each is recorded rather than silent.**

1. **`api.py` gained five routes.** The Slice 4 Files row names only `service.py`, `coordinator.py` and `tests/test_service.py`, but the Deliverable row names four HTTP routes and the Check is a live walkthrough. A route that exists only as a Python method is not `POST /restatements`.
2. **`state.py` gained repository methods.** Slice 3 created `restatements` and wired no writer, so "H0 to H3 recorded" and "`dwell_seconds` to the ledger only" were unreachable. Added `record_restatement`, `list_restatements`, `get_restatement`, `record_hint_event`, `list_hint_events`, `record_transcript_confirmation` and `has_transcript_confirmation`. **No new table was added:** hint events and transcript confirmations live in `events`, which is the table the judge ledger already reads.
3. **`domain` gained `InputMode` and `may_score_restatement`.** The transcript ordering rule is a safety decision, and D2 puts safety decisions in the module that cannot do I/O. It is enforced twice on purpose: once in the service, once in the store, and `test_the_record_refuses_an_unconfirmed_voice_row_on_its_own` proves the second layer is real.
4. **`SqliteEpisodeStore` gained a `check_same_thread` keyword, and `api.py` passes `False` under an explicit lock.** FastAPI serves synchronous routes from a thread pool, so one shared connection raised `sqlite3.ProgrammingError` on every request. SQLite has no way to make one connection safe for concurrent use, so the flag is off **and** every use case runs under `_DB_LOCK`; `BEGIN IMMEDIATE` still handles the genuinely concurrent case, which is a second connection to the same file.
5. **The degraded-state fallback text is authored, not approved.** `COORDINATOR_FALLBACK_TEXT` in `api.py` is new patient-facing copy with no approved source. It exists because the flow has to stop with words rather than a blank screen. **It needs a Gate 1 touch.**

**A Gate 4 gap this slice had to close on its own, and which needs a decision.** **The intake and assessment path is scheduled in no slice.** PlanBack cannot run without a disposition, and Slice 7's own text says the deployed product "already shows intake". Slice 4 therefore implements the minimal version on the route the approved architecture already names (`POST /api/episodes/{id}/intake`, `02-architecture.md` 3.1 and 5.1 step 3): a complaint whose text does not contain the one bound phrase stops at the human path with 422, and one that contains it inserts the preauthored fixture disposition v1. The alternative would have been to write a disposition at episode creation, which `02-architecture.md` 3.1 forbids explicitly. **The full clarification loop is still unowned and unestimated.**

**The recognition rule is a bare substring test, corrected here on 1 October 2026.** The sentence above previously said "a complaint this fixture is not bound to stops at the human path with 422", which reads as a general fail-closed rule and is not what the code does. Measured on 1 October 2026, a complaint that also carries a red-flag symptom ("help sorting out my appointment, also I have chest pain and cannot breathe"), a negated one ("I do not need help sorting out my appointment") and a third-party one ("does my mother need help sorting out my appointment") are all recognised and scored. No clinical branch is derived from the text and the disposition is the same non-clinical plan in every case, so the demo does not mis-triage today; the rule is nonetheless narrower than the sentence implied, and widening it is a reviewer-gated decision carried as an open item in the Slice 4 review and remediation section below.

**Two corrections made while working.** `rules.py` and `test_domain.py` both said the Closure Contract rendering arrives in **Slice 9**. After the 30 September renumbering it is **Slice 10** (Slice 9 is now the Gate B kill test). Both are corrected; `AGENTS.md` section 5 makes a stale mirror a blocking finding.

**Not in this slice, and deliberately.** No disposition is derived from free text: intake issues the fixture's preauthored one or stops. `presentation.py`, `project_patient`, the barrier and action paths, reassessment, expiry projection and the judge ledger are untouched. `GET /api/episodes/{id}` still serves the Slice 1 hardcoded four lines, because re-deriving them is Slice 10's job. The `permitted_change_codes` vocabulary is **empty**, so every reassessment fails closed to the human path: with no reviewer, inventing change codes would make an unauthorised clinical branch look approved.

**Not committed on 30 September 2026.** The working tree held the slice and the earlier `AGENTS.md` amendment. No gate authorises a commit, so neither was committed on the gate's authority. **Superseded 1 October 2026:** the user instructed the ship, and the whole slice is committed and pushed. See the ship section below.

**What this evidence does not prove.** The local simulation coordinator is not the platform path: `02-architecture.md` 3.3's single normative call path still requires the coordinator to execute the tool through the platform with the failure event originating there, and **Gate A has still not run**. Nothing here is evidence of WorkBuddy access, clinical safety, human learning or patient benefit.

### Slice 4 adversarial review and remediation, 1 October 2026

**Verdict APPROVE WITH CHANGES.** An independent adversarial review with no prior context, full note at `docs/reviews/slice4-adversarial-review.md`. It re-ran the suite, mutated seventeen anchors, and checked every claim in the two tables above rather than accepting them.

**What the review verified, and did not have to change.** Every mechanical claim in the Slice 4 section above is true as written: 380 passed at review time with the per-file split summing to it; zero lone LF across all twelve touched files; zero U+2014 on any added line; no `CREATE TABLE` added by this slice; `check_same_thread=False` paired with `_DB_LOCK` on all six store-touching routes; `GET /api/episodes/{id}` still serving the Slice 1 four lines; `permitted_change_codes` empty; no scope creep into the barrier, action, reassessment, expiry, ledger or projection surfaces. Seventeen mutations were applied one at a time, each on an anchor asserted to occur exactly once, each reverted with an md5 match; fifteen were detected, each paired with a control that stayed green, and the two that were not are B1 and B2 below. **The two layered guards were proven independent by reading the failure mode rather than the test colour:** with the service repair cap removed the **store** raises `RepairRoundOutOfRange`, and with the service transcript guard removed the **store** raises `state.UnconfirmedTranscript`.

**Three blocking findings.**

| # | Finding | Disposition |
|---|---|---|
| B1 | `service.py::_score` built `understood` from the mismatch set alone in a mutant and the whole suite stayed green, so an unrecognised answer recorded `recall_unaided` instead of `not_recalled`, contradicting its own `understood: false` in the same response | **CLOSED 1 October 2026.** One assertion added to `test_an_unresolvable_span_is_uncertain_and_never_a_mismatch`. Re-applying the mutant turns exactly that test red |
| B2 | The `H1` entry in `RECALL_OUTCOME_BY_LEVEL` had no test anywhere, so the "H0 to H3 recorded" row above cited a test that exercised H2 only | **CLOSED 1 October 2026.** `test_the_record_carries_the_hint_level_and_the_round` is parametrised over all four rungs, asserting the recorded level and the recorded outcome for each. Changing the `H1` entry now turns exactly that case red |
| B3 | Intake recognition is a bare substring test, while both the test name and the paragraph above described it as a general fail-closed rule | **The claim is corrected above. The rule is deliberately NOT changed:** widening it is a reviewer-gated clinical decision, and it is carried as an open item below |

**Six non-blocking findings, recorded rather than fixed.** None is a false claim left standing.

| # | Finding | Where it is carried |
|---|---|---|
| NF1 | A second episode's intake raises an unhandled `sqlite3.IntegrityError`, because `service.intake` calls `state.register_policy_version` unconditionally and that store method is a plain `INSERT`. **Latent:** `POST /api/episodes` can only create the demo episode, so no HTTP path reaches it today | Open item, **Slice 7**, where the product first holds more than one episode |
| NF2 | Malformed enum values (`hint_level: "H9"`, `event: "auto_hide"`) return HTTP 500 rather than a typed refusal. No row is written in any case, so it is not fail-open | Open item, **Slice 7**, with the error-surface work |
| NF3 | The hint route's `PolicyViolation -> 422` branch is unreachable, because `hint_state` resets the level before `hint_transition` can refuse it | Open item, **Slice 7**, with NF2 |
| NF4 | `transcript_confirmed` is recorded true from an unverified confirmation id on text and chip rounds; only voice is verified | Open item, **Slice 7** |
| NF5 | The coordinator docstrings claim it "cannot see the expected values". It does receive the canonical action and owner ids inside the surface-form sets, so the honest claim is that it cannot determine **which** candidate is expected. The load-bearing claim, that it never sees the `Disposition`, is true | Open item, **Slice 6**, where the real coordinator is wired |
| NF6 | `02-architecture.md` section 8's "payloads are redacted from application logs" has no logging to verify against yet, and `events.payload` does hold raw confirmed patient text | Open item, the slice that first introduces logging |

**One Gate 1 open item this slice created and must not lose.** `COORDINATOR_FALLBACK_TEXT` in `api.py` is authored patient-facing copy with no approved source. The review judged it acceptable for a labelled research demonstration (it names no symptom, urgency, route or deadline, and asserts only that the check did not happen), on the condition that the Gate 1 touch it needs is tracked rather than left in prose. It is now tracked in `tasks/todo.md`.

**Evidence after the remediation.** **383 passed, 1 warning**, split **95** domain, **141** boundaries, **25** api, **91** state, **31** service; the five counts sum to 383. Three tests added, all three by parametrising the hint-level test from one case into four. Three mutations re-applied to check the two fixes: each turned exactly its own new assertion red, and each reverted with an md5 match. `tests/test_service.py` remains CRLF with zero lone LF and zero U+2014.

**Still open, and deliberately untouched.** B3 and NF1 to NF6, each anchored above to the slice where it becomes live, so no later slice implements one early and silently. The exit contract itself was met before the review and is met now; nothing in the remediation changed product behaviour. **Superseded 1 October 2026: the user walked through the live Check, so Slice 4 is complete.**

**Not committed at review time.** No gate authorises a commit, so at that point the review, the two test changes and this record sat in the working tree only. **Superseded 1 October 2026:** all of it is committed and pushed on the user's explicit instruction. See the ship section below.

### Slice 4 ship, 1 October 2026

**User instruction:** "remove the logs from gitignore and include the logs in a separate folder. Other than that slice 4 looks good. Publish the branch and merge and push to main." No gate authorises a commit or a push, so this ship rests on that instruction alone.

**Five commits on `slice-4`, staged by explicit path.** The slice vocabulary in `domain`; the PlanBack loop across `coordinator`, `service`, `state`, `api` and the fixture; the published session logs; this record and the review note; and the `.gitignore` documentation change. `main` was then fast-forwarded to `slice-4` and both branches pushed, so `origin` holds `main` and `slice-4`.

**The session logs are now published, at `docs/session-logs/`.** `docs/CHALLENGE_REQUIREMENTS_JUDGING.md` section 8 lists the CodeBuddy or WorkBuddy conversation history as a **required** submission item and accepts a written development-process description as proof of product usage, and submission is through this repository. The live files stay at `.workbuddy-ai/memory/`, which remains git-ignored, so this folder is a published copy with the refresh rule recorded in its own `README.md`. **Third-party skills are deliberately NOT published:** `.workbuddy-ai/skills/` holds six files copied from a local agents directory with no `license`, `author` or source field, and the challenge requires the project to be original, so unlicensed third-party content does not ship.

**Two disclosed exceptions, not silent ones.** The imported logs carry **136 em dashes**. `AGENTS.md` section 6 bans em dashes in *new writing*; these are imported historical records, so rewriting them would falsify the usage proof, and they are published as written. Their working-tree line endings were normalised to CRLF, which `core.autocrlf=true` normalises back to LF on commit, so no content changed. A content scan before publishing found no tokens, keys, credentials, email addresses or real institution names; the logs do contain the Windows username inside a handful of absolute paths.

## Outstanding items at the close of Slice 4, 1 October 2026

| # | Item | State | Next action |
|---|---|---|---|
| 1 | **Three redacted chat screenshots.** `CHALLENGE_REQUIREMENTS_JUDGING.md` line 164 requires a minimum of three, separately from the written development-process description that line 128 accepts | **CLOSED 1 October 2026.** Three captured by Jaydon into `submission/usage-proof/screenshots/` and pushed. Redaction checked: no AppKey, token, key or credential in any of the three | None. The manifest is in that folder's `README.md` and the capture log is in `submission/usage-proof.md` |
| 2 | **`COORDINATOR_FALLBACK_TEXT`**, the patient-facing copy shown when the coordinator cannot answer | **CLOSED 1 October 2026.** Approved as "We could not check that answer just now. Your plan has not changed." **Gate 1 was re-approved the same day**, so the string now has an approved source | None. This row is closed |
| 3 | **B3, the intake recognition rule.** A bare substring test that also recognises a negated, third-party or red-flag-carrying complaint | **Unchanged and deferred to Slice 5** by the standing instruction of 30 September 2026 | Decided at Slice 5, with a clinical reviewer. No red-flag or negation handling is authored before one exists |
| 4 | **The Option C source.** Unselected; licence and Singapore applicability unchecked | **RESOLVED 1 October 2026.** The check ran, no source cleared, and Option C was found to contradict Option A. The user answered **"drop"**, so `03-program-design.md` section 6.2 now carries Option A alone | **Gate 3 is reopened by that edit** and awaits re-approval. Nothing else waits on it. See the source-check section above |

## Gate 4 approval — 28 September 2026
**Reopened and re-approved on 30 September 2026. See the reopening and re-approval sections at the top of this file.**
The user approved **Gate 4 (Slice plan)** on 28 September 2026 with the instruction **"continue"**, following the approval question in this file. `04-slices.md` now records the approval.

**Approval authorises implementation code, slice by slice, in the planned order.** It does **not** authorise installs beyond the declared test dependencies, credentials, recruitment, external calls, deployment, or a push. Each slice still stops for the user's "continue, or re-steer?" before the next begins.

**Two sub-questions were open at drafting. Both resolved at approval, under the recommendation given:**

| # | Question | Resolution |
|---|---|---|
| 1 | **ADR-0007 — which layer owns canonicalisation?** | **Reading A accepted.** Canonicalisation lives in `domain`; the coordinator returns raw spans. ADR-0007 is now `accepted`, and the Gate 3 `compare_plan` signature is amended. `ExtractedPlan` carries **both** the raw span and `uncertain_fields`. |
| 2 | **The Option C source.** | **Scheduling only.** Still unselected, licensing still unchecked. Blocks Slice 5 and nothing earlier. If no source clears by 2 October → Option B; clinical wording is **not** authored to unblock the schedule. |

**If either resolution is wrong, say so** — ADR-0007 affects Slices 2 and 4, the source affects Slice 5.

## Slice 1 complete — 28 September 2026

**Tracer bullet runs end to end.** `POST /api/episodes` → `GET /api/episodes/{id}` → the four-line patient page, served from `127.0.0.1` with no database, no domain layer and no coordinator.

| Evidence | Result |
|---|---|
| `pytest tests/` | **11 passed** |
| Live `curl` on `127.0.0.1:8137` | health, create, projection and 404 all correct |
| Missing route → 404 | confirmed |
| Simulated label inside the serialized projection | confirmed (D11) |
| No `http-equiv="refresh"`, no `<script>`, no CSS animation/transition | confirmed (C8 — no timer anywhere) |

**Defect found and fixed during this slice — a real one.** The first live render produced **"You or you must act now."** on line 2. `PLAN.md` §6.1, `02-architecture.md` §7 and `01-product.md` all render line 2 as "You or *[named person]* must act now."; with a patient owner that sentence is malformed. **The test suite did not catch it — inspection of the running app did**, which is exactly why Gate 4's standing rule is "run it and show the result" rather than "the tests pass".

- **Fix applied:** line 2 read "Myself must act now.", with `OWNER_DISPLAY` as a named-owner constant. **Corrected 30 September 2026:** that wording was still malformed, and Slice 2 superseded the constant. `demo/fixture.py` now carries `SELF_OWNER_SENTENCE = "You must act now."`, mirroring `domain.rules.patient_lines` for a self owner and agreeing with `fixtures/scripted_episode.json`, whose `next_owner_id` is `patient`.
- **Regression test added:** `test_line_two_does_not_render_a_doubled_owner`.
- **Flagged, not silently absorbed:** this **diverges from three approved documents.** The correction belongs in those documents at the next Gate 1 touch. **Slice 10** (Slice 9 before the 30 September 2026 renumber) must implement whichever form they then carry. The Slice 1 literal is not the authority.

**Files created:** `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`, `src/carerelay/demo/__init__.py`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json`, `tests/test_api.py`.

**Not yet done, and deliberately:** no database (Slice 3), no disposition is written on episode creation (`02-architecture.md` §3.1 — confirmed by `test_create_episode_returns_an_id_and_no_disposition`), and the fixture wording is still a **provisional placeholder** pending the Option C source check.

## Gate 4 draft — 28 September 2026

`04-slices.md` is written and **awaiting explicit approval**. Drafting it authorises no code. ~~Thirteen slices~~ **Fourteen slices as of the 30 September 2026 renumber**, full Gate 3 scope, with constraint C1 satisfied: the external card (old Slice 7, now **Slice 8**) completes before the Closure Contract build (old Slice 9, now **Slice 10**).

**User instructions at drafting (28 September 2026):**

| # | Instruction | Consequence |
|---|---|---|
| 1 | Re-verify Gate A before planning against it | Gate A re-checked. Findings below. |
| 2 | **Keep the full scope** — do not cut to fit the schedule | No capability cut. The schedule risk is recorded as R1 in `04-slices.md` §6/§5 rather than resolved by cutting. |

**Gate A re-verification, 28 September 2026.** No `WORKBUDDY_API_KEY` or `WORKBUDDY_AGENT_ID` in the environment; no `.env`; no `workbuddy` or `codebuddy` Python package installed. **On that evidence the platform path is [unknown]-to-unavailable.** Gate A remains **overdue** since 26 September and has still not run. Slice 6 therefore plans the labelled local-simulation fallback as the default and wires the platform path only if credentials appear. The pre-recorded Gate 2 §3.3 reversal applies if Gate A has not passed by 11 October.

**Two results already in hand, before any product code:**

- **K1 and K2 PASS** — `spike/tests/test_kill_conditions.py`, 15 tests, 0 failures, Python 3.13.14, including four defect-injection tests confirming the assertions can fail. This is a **deterministic-layer spike result**, not an implementation result.
- **Slice 1's environment check passes** — the FastAPI stack installs and imports into an isolated venv; the intermittent AppControl block on stdlib venv creation did not fire.

**Open items at drafting:**

- **The Option C source is not selected.** Licensing and Singapore applicability unchecked. This blocks Slice 5 (the judged fixture) and nothing earlier. If no source can be cleared by 2 October, escalate to Option B — do not author clinical wording to unblock the schedule.
- **ADR-0007 is `proposed`.** It amends the Gate 3 `compare_plan` signature so canonicalisation lives in `domain` (Reading A). It affects what K1 can claim and needs acknowledgment at Gate 4 approval.
- **The schedule does not fit.** 102–169 h against 144 h available, solo, 18 days. Recorded as R1.

**Gate 4 approval question:** Approve Gate 4 as drafted, or what should change?

## Decision records

`docs/adr/` now holds eight Architecture Decision Records capturing the choices that outlive this feature — ADR-0001 to ADR-0008 — plus an index at `docs/adr/README.md`. They summarise decisions already approved at Gates 1–3 and the Gate 4 drafting instructions. **The gate documents remain authoritative**; where an ADR disagrees with them, the gate document wins and the ADR is corrected.


## Gate 3 approval — 26 September 2026
**Reopened and re-approved on 30 September 2026, because Decision D-1b moved the clinical screens to Next.js and changed this gate's file list. See the reopening and re-approval sections at the top of this file.**

The user approved **Gate 3 (Program Design)** on 26 September 2026, on the same day it was drafted, with two amendments made at approval.

Approval covers: the planned file footprint, the type and method contracts, the call stacks, the failure-capable test plan, the callback dedupe representation, the Gate B protocol, and the 90–150 h build plus 20–35 h baseline estimate.

**Gate 3 approval authorises drafting Gate 4 only.** It does **not** authorise code, installs, credentials, recruitment, external calls, or a push. Gate 4 remains pending and no code may be written before Gate 4 is approved.

### Amendments made at approval

| # | Amendment | Where |
|---|---|---|
| 1 | **§6.1 added — the two reviewer-free kill conditions.** Two of the three PlanBack cut conditions (false mismatch on correct restatements; emergency guidance delayed by read-back) are pure system properties. They are lifted out of the stalled study and execute **before any participant work**, requiring no clinical review and no Gate A | `03-program-design.md` §6.1, §5 |
| 2 | **§6.2 rewritten — Option A + C selected.** The comparator is now **non-clinical** (Option A) and the fixture is **sourced verbatim from attributable published guidance** (Option C). The original text said the study "cannot run as specified"; that dependency is resolved by decision | `03-program-design.md` §6.2, §8.3 |

### Gate 2 backtrack — D6 comparator material

**Option A changes D6's comparator content, so Gate 2 D6 is formally backtracked.** The decision itself is unchanged — external artefact, between-subjects, scripted post-failure question, pre-registered cut rule. What changes is the *material*: it now carries no symptom, urgency or disposition content.

| | Before | After |
|---|---|---|
| Comparator content | Bilingual clinical card with the fixture wording | Content-neutral instruction task, same shape, **no clinical content** |
| Review required to run | Clinical + native-speaker + bilingual clinical | **None** — no guidance is administered to anyone |
| What the result supports | Understanding of care advice | Understanding of the **mechanism** only |

**Consequence the submission must state:** the study measures whether read-back plus truthful status changes comprehension, burden and false-completion belief. It does **not** validate clinical advice. Impact & Relevance loses weight accordingly, and no claim may imply otherwise.

### Open at approval

- **Source selection for Option C.** No source chosen; licensing and Singapore applicability unchecked. **This precedes use** and is a Gate 4 task. Note `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope.
- **Option B rejected but not closed.** A reviewer remains valuable for clinical-credibility language, but no longer blocks the study. Not chased on a clock.
- The two §6.1 kill tests have **not been written yet** and must precede participant work.

## Gate 3 draft: 26 September 2026 (superseded by the approval above)

`03-program-design.md` is now **APPROVED** (see the approval record above). It pins planned files, types, call stacks, failure-capable tests, the callback dedupe representation, and a 90–150 person-hour build estimate plus 20–35 hours for the baseline. Gate 4 remains pending and no implementation is authorised. Gate A, participant recruitment and the participant comparison remain unproved.

**The clinical-review blocker has a decision paper: `clinical-review-blocker.md` (26 September 2026).** Headline finding: the hackathon does **not** require a clinical reviewer, and the blocker was narrower than `03-program-design.md` §6 implied — the build, the fixture, the fault harness and the ledger were **not** blocked. Two of the three PlanBack kill conditions (false-mismatch and delayed-emergency-guidance) are **testable with no participants and no reviewer at all**; they are now lifted out of the stalled study as Gate 3 §6.1 and run first. **The user selected Option A + C on 26 September 2026**, which removed the blocking dependency and triggered the Gate 2 D6 backtrack recorded above. Option B (one reviewer) was not chased on a clock but is not closed.

The `02-architecture.md` header previously read "Not approved". Fixed 26 September 2026 — it now records the Gate 2 approval and points to this file for authority.

## Gate 2 approval — 25 September 2026
**Reopened and re-approved on 30 September 2026. Revision 2 was approved on this date; revision 3 is the current approved revision. See the reopening and re-approval sections at the top of this file.**

The user approved **Gate 2 (Architecture) revision 2** on 25 September 2026, following an independent round-2 adversarial review whose verdict was APPROVE WITH CHANGES and whose eleven blocking items were all applied or explicitly resolved.

Approval covers: D1–D12, the module and trust boundaries, the pinned tool-execution path (§3.3), the UI API and the three-tool MCP surface, the attempt/transition/callback schema (§4.1), the three flows, D11 evidence provenance and D12 sticky expiry, the non-functional surfaces (§8), the pre-registered baseline study (§9), the amended expired-screen rendering with its copy rules (§7), and the change log (§11).

**Gate 2 approval authorises the Gate A access spike only.** It does **not** authorise implementation code. Gates 3 and 4 remain pending, and no code may be written before Gate 4.

### Carried into Gate 3

- **A real effort estimate.** The round-2 review's 90–150 h (plus 20–35 h for the baseline) is unverified. The user has accepted it as achievable; Gate 3 must still produce its own estimate.
- **Gate 4 must sequence the baseline comparison (Gate B) before the Closure Contract build.** `PLAN.md` §7 currently schedules the sessions *after* the state machine — wrong order.
- **The Gate A spike is due 26 September.** If it fails, §3.3's fallback applies and the platform-advantage claim is weakened and stated as weakened.
- **D9 (scheduled reassessment) is not deliverable.** The P1 load-bearing answer is "execution substrate". `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is not delivered and must not be implied in the submission.

## Gate 1 reopening — 25 September 2026 (approved)

Gate 1 was **deliberately reopened** after its first approval to resolve the H2 accessibility hazard the round-2 adversarial review identified, and to approve the expired-screen wording. Both changes were approved by the user the same day.

| Change | Decision | Files |
|---|---|---|
| **H2 no longer has a timer** | The plan card at H2 **stays on screen until the patient hides it**. No countdown, no auto-dismiss, no auto-advance anywhere in the product. `dwell_seconds` is recorded for the judge ledger and never shown to the patient. Rationale: a five-second rule is unreadable for older adults, unusable with a screen reader, and un-extendable — it penalised the exact population the product exists for | `PLAN.md` §5.2 + new §5.2.1, `01-product.md`, `mockups/02` |
| **Expired-screen wording** | Approved with **softer, human-centred wording**. The first draft ("The time to go was [deadline]. It has passed." / "Call [route] now") was rejected as too blunt. Final rendering plus five copy rules: no reproach, no alarm, no false comfort, a named route, deadline stays visible | `02-architecture.md` §7 |

**Gate 1 remains APPROVED** with these amendments. Both changes were made openly in the documents, not silently at Gate 3.

## Gate 1 approval — 25 September 2026 (original)

The user explicitly approved Gate 1 on 25 September 2026. This covers the Gate 1
scope below: the reframe, PlanBack, the recall hint ladder, the Closure Contract,
the two-axis state model, the design principles and the five HTML wireframes.

Approval of the product specification does **not** authorise implementation.
Gates 2–4 remain pending and no code may be written until Gate 2 is approved.

### Carried forward as explicit, unresolved Gate 1 risks

These were surfaced by the adversarial review, accepted rather than resolved, and
must be treated as live inputs to Gate 2:

- **Mandatory organiser-usage proof is still absent.** Without it the project does
  not proceed to scoring.
- **No qualified clinical reviewer and no authorised protocol.** The prototype must
  remain a labelled research demonstration using scripted fixtures.
- **The load-bearing assumption is untested:** that a fixed bilingual card does not
  perform equally well. It should be tested before the mechanisms are built.
- **Neither mechanism requires WorkBuddy.** WorkBuddy's genuine dependency is the
  coordinator, the real tool call, its real failure event, and session resume.
- **Mandarin voice is a gated TRTC spike only.** No account access or clinical
  accuracy has been demonstrated.

## Gate 1 scope as of 21 September 2026

Gate 1 was opened with a broader product definition. It has since been narrowed by the independent adversarial review and expanded by two new mechanisms. Both changes were approved on 25 September 2026.

| Change | Where |
|---|---|
| Reframe: closed-loop confirmation of urgent advice, not the ledger | `docs/reviews/gate2-adversarial-review-round1.md` |
| PlanBack — read-back with deterministic critical-field comparison and bounded repair | `03-planback-closure-contract.md`, `PLAN.md` §5.1 |
| Recall hint ladder (H0–H3) with the level always recorded | `PLAN.md` §5.2, `01-product.md`, `mockups/02` |
| Closure Contract — two independent axes and five fault invariants | `03-planback-closure-contract.md`, `PLAN.md` §6.1 |
| Corrected single-ladder state model to two axes | `PLAN.md` §6 |
| Patient sees four lines; the ledger is judge-facing | `PLAN.md` §6.1, `mockups/03` |
| Four design principles adopted; load-bearing audit fails the current scope | `docs/DESIGN_PRINCIPLES.md` |

## Document map

The skill's canonical gate filenames are reserved for Gates 2 to 4. Two supporting documents already occupy those numbers, so a fresh session should read the map below rather than assume by number.

The map spans three folders, reorganised on 30 September 2026 so that a review artefact is not filed beside the record it reviews. Gate documents and their supporting notes stay in this folder. Adversarial reviews and review briefs live in `docs/reviews/`. Decisions that outlive this feature live in `docs/adr/`. The layout is described once, for a reader with no prior context, in `docs/README.md`.

**This folder, `docs/plans/urgent-advice-accessibility/`**

| File | Kind | Purpose |
|---|---|---|
| `00-status.md` | state | this file |
| `01-product.md` | **Gate 1 doc** | problem, success metric, announcement, product rules, screens |
| `02-architecture.md` | **Gate 2 doc** | **revision 3, APPROVED 30 Sep 2026.** Revision 2 was approved 25 Sep. D1 to D13, pinned tool path, attempt-transition schema, external between-subjects baseline, non-functional surfaces, change log |
| `03-program-design.md` | **Gate 3 doc** | **APPROVED 30 Sep 2026.** First approved 26 Sep. Files, types, call stacks, failure-capable tests, effort |
| `04-slices.md` | **Gate 4 doc** | **APPROVED 30 Sep 2026.** First approved 28 Sep. **14 slices, Slice 0 to Slice 13**, full scope, Gate A re-verification, R1 schedule risk |
| `03-planback-closure-contract.md` | supporting note | specification and feasibility for PlanBack and the Closure Contract. Carries the `03-` filename that Gate 3 needed |
| `clinical-review-blocker.md` | supporting note | decision paper, 26 Sep: what the reviewer blocker actually blocks, and three routes through |
| `research-workarounds.md` | supporting note | which blockers are workaroundable and which are hard gates. Listed here for the first time: it was named in `AGENTS.md` section 2 but was missing from this map |
| `adp-and-deployment-impact.md` | supporting note | DRAFT, 30 Sep: what the ADP hackathon guide changes, where ADP collides with the §8 model-generated-text boundary and the D8 execution-substrate claim, and the Vercel/Render deployment assessment. Authorises nothing |
| `mockups/` | Gate 1 assets | five plain-HTML screens, throwaway by design |

**`docs/reviews/`**

| File | Kind | Purpose |
|---|---|---|
| `gate2-adversarial-review-round1.md` | review | independent review, 21 Sep: verdict, competitors, scores, kill dates. Renamed from `02-adversarial-review.md`, which collided with the Gate 2 number and is the documented cause of the file-map trap |
| `gate2-review-prompt-thorough.md` | review brief | the prompt handed to the independent round-2 reviewer |
| `gate2-adversarial-review-thorough.md` | review | independent round-2 review: APPROVE WITH CHANGES, three blocking defects |
| `slice2-adversarial-review.md` | review | independent adversarial review of Slice 2, 30 Sep: verdict, findings, judgement calls, evasion, test quality, and the remediation applied before Slice 3 |
| `slice3-adversarial-review.md` | review | independent adversarial review of Slice 3, 30 Sep: verdict (yes, with named caveats), two blocking findings, five unproven constraints, and the open items it raised |
| `slice4-adversarial-review.md` | review | independent adversarial review of Slice 4, 1 Oct: verdict APPROVE WITH CHANGES, seventeen mutations, three blocking findings, six non-blocking findings, the full edge-case and false-claim audit, and what the evidence does not prove. The two test gaps it found are closed in the Slice 4 review and remediation section above |
| `adp-hosting-stack-review-prompt.md` | review brief | the prompt for an independent reviewer, 30 Sep: the ADP guide, the Vercel/Render request and the laeria reference, against the slice plan. **Not yet run.** Records the author's positions as claims to attack and lists three claims the author already reversed |

**`docs/adr/`**

| File | Kind | Purpose |
|---|---|---|
| `README.md` | index | ADR index |
| `0001` to `0008` | decision records | decisions that outlive this feature. **The gate documents remain authoritative**; where an ADR disagrees with them, the gate document wins and the ADR is corrected |

## Notes for a fresh session

- Product identity: CareRelay must not stop at advice; it checks understanding and feasibility, preserves the clinical deadline, and reports failed or unconfirmed handoffs truthfully.
- **PlanBack:** the patient restates the plan; **code, not a model**, compares `action`, `deadline` and `next_owner`; a mismatch is repaired field by field, bounded to two rounds, then a human path. The model only extracts fields.
- **Hint ladder:** H0 unaided → H1 structural slots → H2 card shown then hidden → H3 plan given. The level used is **always recorded**, because a hint containing the answer turns a comprehension check into a reading test.
- **The ladder fades.** A new plan starts at H1; an unaided success lowers the starting level next time; a failure restores it; changes happen on trends, not single rounds; fading is invisible to the patient. This is **vanishing cues with errorless learning and spaced retrieval** — an established cognitive-rehabilitation technique, cited as prior art.
- **Cognitive claims are prohibited.** No cognitive improvement, “keep your mind sharp,” dementia prevention, screening, risk score or diagnostic output — in the product, submission, video or pitch. Meta-analyses find no far transfer from cognitive training; the FTC fined Lumosity $2 million in 2016 for exactly this claim. The scaffold improves retention of *this plan* and nothing more.
- **Language rule:** never “cognitive rot,” “brain training” or “use it or lose it” in anything user-facing.
- **Longitudinal cognitive signal is research, not a demo claim.** Recorded in `PLAN.md` §5.3 as an out-of-scope hypothesis so the ambition is not lost; it is not presented in the submission.
- **Closure Contract:** execution status and evidence status are two independent axes; the clinical deadline is immutable to operational retries; five invariants are test cases, not slogans.
- **The load-bearing untested assumption:** that a fixed bilingual card plus a direct booking link plus a NurseFirst fallback does *not* perform equally. This is the primary kill test and must run first.
- **Honest dependency boundary:** PlanBack and the Closure Contract are application logic and do not require WorkBuddy. WorkBuddy's genuine contribution is the coordinator, the real tool call, its real failure event and session resume.
- **Open question from `docs/DESIGN_PRINCIPLES.md` (re-verified 22 Sep, resolved 25 Sep):** the P1 load-bearing answer is **"execution substrate"**. The scheduled-reassessment module (D9 in the Gate 2 draft) was dropped after the round-2 adversarial review found it unbuildable as specified — no scenario, no ingress endpoint, no estimate. `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is **not** delivered. The submission must state this rather than imply a capability that is switched off.
- Mandarin and voice are accessibility modes. English text remains the auditable reference until bilingual clinical content is reviewed.
- Provisional persona: Mei, 72, Mandarin-preferring, with remote daughter support. The respiratory-symptom recommendation remains an injected fixture until clinical review.
- **No asset may name a real healthcare facility.** The fixture provider is fictional and labelled.
- No implementation code may be written before Gate 4 approval. **Gate 4 was approved 28 September 2026, reopened on 30 September 2026 and re-approved the same day, so implementation is authorised again slice by slice.**
- **Gate 4 approved 28 Sep, reopened and re-approved 30 September 2026** (see the reopening and re-approval sections at the top of this file). Full scope was kept on the user's explicit instruction; the schedule risk is recorded as R1 in `04-slices.md`, not resolved by cutting. Constraint C1 is honoured: the external card (old Slice 7, now **Slice 8**) completes before the Closure Contract build (old Slice 9, now **Slice 10**), with the Gate B kill test (old Slice 8, now **Slice 9**) between them.
- **ADR-0007 accepted 28 Sep** — canonicalisation lives in `domain` (Reading A). The Gate 3 `compare_plan` signature is amended, and `ExtractedPlan` carries both the raw span and `uncertain_fields`.
- **Gate A has RUN, and PASSED, on 2 October 2026.** Superseded: the 28 September re-verification found no credentials, no `.env` and no SDK package, and on that evidence the platform path was `[unknown]`. The user obtained an ADP AppKey, the rebuilt harness ran against the live endpoint, and all three questions were answered from observation. **The labelled `local-sim` fallback is not needed.** See the Gate A section above for the three findings, the established schema and the limits that still apply.
- **K1 and K2 pass** (spike, 15/15). Deterministic layer only, and dependent on Reading A (ADR-0007).
- **ADR-0007 is accepted, not outstanding. Corrected 30 September 2026.** The line above records the acceptance, and `docs/adr/0007-canonicalisation-lives-in-domain.md` states it in its status line. An earlier note here said “proposed, not accepted” and asked for acknowledgment at Gate 4 approval; that acknowledgment was given, because Gate 4 was approved on 28 September 2026, reopened on 30 September 2026 and re-approved the same day. The amendment to the approved Gate 3 `compare_plan` signature is therefore part of the approved plan, and implementations from Slice 2 onward use the widened signature.
- Gate 2 draft (`02-architecture.md` revision 2) pins D1–D12: Python+FastAPI default (reversible only before the first domain-code commit), pure domain core, append-only attempt transitions, derived closure with sticky expiry, external between-subjects baseline, deterministic abstention with a closed vocabulary, **D9 dropped**, voice deferred and isolated. **The Gate A access spike is due 26 Sep** with a pre-recorded fallback decision. **Superseded 30 September 2026:** revision 3 replaces D1 and adds D13, and the "reversible only before the first domain-code commit" clause no longer applies because the reversal was taken (a Next.js frontend on Vercel, the backend on Render). See the reopening section at the top of this file.
- **Two items that needed a user decision are now both resolved** (25 Sep):
  1. The **H2 timed hide is gone.** The plan card stays until the patient hides it; no timers anywhere in the product; `dwell_seconds` recorded for the ledger only. Gate 1 was reopened deliberately and re-approved.
  2. The **expired patient screen** wording is approved, softened on the user's instruction, with five copy rules in `02-architecture.md` §7.
- Round-2 review effort estimate: **90–150 h** for this architecture plus 20–35 h baseline. The user has reviewed this and **accepted the estimate as achievable** (25 Sep). Gate 3 still produces a real estimate; the acceptance is not a substitute for one.
- Branch and commit state, re-verified 30 September 2026 after the Slice 3 remediation: `main`, `slice-3` and `slice-4` all sit at the tip of the Slice 3 work and its remediation, whose substantive commits are `4841b71` (the store's command and result types), `ad3401a` (the append-only record), `6b831f3` (the documentation restructure) and `27bed4b` (the record), followed by the ship corrections, `71a1e83` (the O1 remediation) and `f17c361` (its record). `slice-2-domain-core` sits at `80245e4`. `gate-2-architecture` and `care-relay-adversarial-review` no longer exist as branches; their commits remain reachable from `main`. `origin` holds `main` and `slice-3`, each in sync with its local branch: the Slice 3 work and its remediation are pushed, and so is everything committed after them, including the Gate 2, 3 and 4 revision-3 amendment. No gate authorises a commit or a push; they were made on the user's explicit instruction of 30 September 2026. The push itself succeeds when it is asked for, so the earlier credential failures no longer apply. **Updated 1 October 2026:** the Slice 4 ship moved `main` forward to the `slice-4` tip, so `origin` now holds `main` and `slice-4`, and `slice-3` stays frozen where its slice closed. **No hash is given for `origin`'s tip, on purpose:** a hash here goes stale on the next push, and that correction has already been needed twice.
- **Slice 3 is complete** (30 September 2026): the append-only record exists at `src/carerelay/state.py`. **Corrected 30 September 2026 by Slice 4:** `restatements` now has a writer (`state.record_restatement`), and `api.py` is wired to the store for the five PlanBack routes. The three tracer-bullet routes from Slice 1 remain hardcoded, because their slice's contract says so. The `source_ref` open item from the Slice 2 review is settled. Ten readings of the approved documents are flagged in the Slice 3 section above; reading 6 (the snapshot reports the expiry event for the current disposition version) is the one most worth an explicit yes or no. The Slice 3 review gives reading 6 an explicit **yes**, with reasoning at section 7 (B4) of the review note; the decision remains the user's. **Reviewed 30 September 2026:** verdict yes with named caveats, two blocking findings corrected above, and eight open items O1 to O8. **Remediated the same day, before Slice 4 began:** O1, O3, O4 and O6 are closed and O2 is half closed, so the `INSERT OR REPLACE` gap no longer blocks the structural claim, which is now scoped rather than absolute. 332 pass. That change is **committed on `slice-3` and fast-forwarded into `main`**, in two commits: the code, then this record. Full note: `docs/reviews/slice3-adversarial-review.md`.
