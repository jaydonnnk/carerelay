# Slice 5 adversarial review

**Type:** supporting note. It is authoritative for nothing. `00-status.md` remains the
only authority for gate and slice state, and the approved gate documents remain the
authority for decisions. This note records what an independent adversarial review
observed, and it changes no file it did not create.

**Reviewed:** the working tree of branch `slice-5`, HEAD `ff22ed397835287b649476a27c69e7fe8dcaf7d7`.
**Date:** 1 October 2026.
**Method:** falsify, not confirm. The author's self-report (`00-status.md`) was treated
as a claim document, not as evidence. Every number below was re-derived from the tree.
Labels: **[verified]** observed directly, **[inferred]** follows from observation,
**[hypothesis]** reviewer judgement, **[unknown]** not established.

---

## 1. Verdicts

**D1, Slice 5 implementation: APPROVE WITH CHANGES.** The exit contract is met in
substance: `POST /barriers`, `POST /escalations`, `POST /reassessments`, F6 and O7 are
built, tested with fail-capable tests, and proven live. No blocking defect was found in
the **code**. Three blocking defects were found in the **documentation that the slice
touches**, one of them in an approved gate document. The code may ship once those are
corrected; the slice may not close until they are.

**D2, dropping Option C: UPHOLD.** The reasoning is sound, the contradiction is real,
and no better source exists that the author missed. One nuance the note records rather
than disputes: dropping Option C removes a *sourcing* safeguard, and the Tier 1
classification that replaces it is self-asserted. That makes the fixture's honesty rest
entirely on the claim "this asserts no clinical claim", which is a claim a reader must be
able to check, not a property the code enforces.

---

## 2. Findings

Severity: **BLOCKER** (must be fixed before the slice closes), **SHOULD FIX** (a real
defect, not slice-blocking), **NIT** (cosmetic or a forward note).

| # | Severity | Location | What | Why it matters | Smallest fix |
|---|---|---|---|---|---|
| B1 | **BLOCKER** | `docs/plans/urgent-advice-accessibility/03-program-design.md:290` | Section 8 item 3 still reads, in the present tense, "The fixture **is sourced verbatim** from attributable published guidance; source selection, licensing and Singapore applicability remain unchecked and precede use." | This is an **approved Gate 3 document**, and it now contradicts its own section 6.2 (edited at line 247-256 to drop Option C). A reader of section 8 is told the fixture is sourced; a reader of section 6.2 is told it is not. One of the two is false, and both are in the same approved file | Rewrite item 3 to the post-drop state: "resolved by decision, Option A alone; the fixture is authored, non-clinical, and asserts no clinical claim" |
| B2 | **BLOCKER** | `docs/plans/urgent-advice-accessibility/03-program-design.md:249` | Under the new heading "Option A, **with Option C dropped**", the first line still reads "The user selected **Option A + C** on 26 September 2026" with no qualifier | Same defect, second instance: the heading says one thing, the very next line says the opposite. A gate re-approval is requested against this text | Add "Option C was dropped on 1 October 2026; the 26 September selection is superseded" to line 249, or fold line 249 into the drop paragraph |
| B3 | **BLOCKER** | `src/carerelay/api.py:195-197` | `POST /api/episodes` response `note` still says "placeholder awaiting the Option C source check." | **Reproduced live:** the create call returns this string verbatim (see section 4, command 2). It is a machine-readable API payload that asserts a source check is still pending, when `policy_provenance` three lines away (line 114-120) correctly says Option C was dropped. The same file contradicts itself, and the false half is on the wire | Update the two `note` strings to match the corrected `policy_provenance` |
| S1 | SHOULD FIX | `src/carerelay/state.py:1325` | `list_barriers` returns `tuple[sqlite3.Row, ...]`; every sibling accessor (`list_dispositions:780`, `list_attempts:950`, `list_callbacks:1130`, `list_evidence:1232`, `list_restatements:1543`, `list_hint_events:1590`) returns a typed frozen dataclass | Raw rows leak the SQL schema into every caller. It is the direct enabler of S2: tests then assert on `rows[0]["stopped_at_human_path"]`, binding to a column name | Add a `BarrierRecord` frozen dataclass and return `tuple[BarrierRecord, ...]` |
| S2 | SHOULD FIX | `tests/test_service.py`, `tests/test_api.py` | **18 new `service._store` accesses** added by this slice (3 pre-existed; the total is now 21) | Tests assert against a **private** attribute of the object under test rather than its public surface. Renaming `_store` breaks 21 tests with no product change. It is a coupling defect, and it is why S1 went unnoticed | Route the assertions through public service methods, or accept the store as an explicit test seam rather than reaching through `_` |
| S3 | SHOULD FIX | repo-wide; worst at `docs/plans/urgent-advice-accessibility/04-slices.md:168,171,47,88,91,92,101,414`; `AGENTS.md:86`; `tests/test_domain.py:21-22`; `tests/test_state.py:157`; `PROGRESS.md:80,143,145,149`; `spike/kill_spike/fixture.py:3` | Stale Option C claims survive the drop. `04-slices.md:168` still requires the fixture to carry "the Slice 0 Option C wording, verbatim"; `AGENTS.md:86` still says "Slice 5 is next and is blocked on the Option C source" | The author updated the files they edited and left the rest. `04-slices.md` was deferred **deliberately** and is documented as such (`00-status.md:87`), which is defensible under `AGENTS.md` section 5. `AGENTS.md:86` and the two test-module docstrings are not deferred and are simply stale | Correct `AGENTS.md:86` and the two docstrings now; fold the `04-slices.md` lines into the next Gate 4 touch as already planned |
| N1 | NIT | `src/carerelay/service.py:539,624,747` | `human_path_route_id` is always `disposition.fallback_route_id` | Not decorative (S1's neighbour A9 is **refuted**: it is asserted at `tests/test_service.py:550` and serialised at `api.py:333`). But it carries no information the disposition did not already carry | None required. A comment noting it is deliberately a pass-through would help |
| N2 | NIT | `tests/test_service.py:648-699` | `TestPlanPrecedesReadBack` asserts state (a disposition exists, lines render, deadline unchanged), but the spike test it was promoted from (`spike/tests/test_kill_conditions.py:111-125`) asserted **event order** (`GUIDANCE_RENDERED` before `PLANBACK_EXTRACT`) | The promotion is genuine and the deadline assertion is stronger, but the ordering assertion changed shape. No test now asserts the event *sequence* in the product | Add one assertion on `list_events` order, or state in the docstring that the sequence is proven in the spike and not re-proven here |

**No BLOCKER was found in the implementation code.** B1-B3 are all documentary or
wire-payload. The code itself is correct against its exit contract.

---

## 3. Judgement calls J1-J6

- **J1, is the Option C reasoning sound, and were sources missed?** Sound, and no
  material source was missed. **[verified]** The MOH and HealthHub terms were read and
  both require prior written permission; the Singapore Open Data Licence reaches
  Datasets only, not website content; the UK OGL route fails Singapore applicability
  because routes 111 and GP do not exist here. I found no Singapore government
  clinical-advice source with a permissive content licence that the author overlooked.
  **[inferred]** The decisive point is stronger than licensing: a fixture of *fictional*
  entities cannot be verbatim from *any* source, so Option C was unsatisfiable
  independent of licensing. That is a correct kill of the option.
- **J2, does dropping Option C remove a safeguard?** **Yes, and the author should say
  so more plainly.** Option C's safeguard was *attributability*: a sourced string is one
  a reader can trace and challenge. What replaces it is the Tier 1 classification
  ("asserts no clinical claim"), which is **self-asserted**. The product keeps every
  *behavioural* guard (empty `PERMITTED_CHANGE_CODES`, simulated label, fail-closed
  reassessment). It loses the *evidential* guard, and the honest statement is that the
  fixture is now honest by absence of claim rather than by presence of citation. The
  author's own text at `02-program-design.md:256` and `demo/fixture.py:9-16` says this
  correctly; `00-status.md`'s framing ("honest because it asserts no clinical claim") is
  right but reads as a comfort rather than a trade.
- **J3, F6's acting-party reading versus invariant I4.** **Correct.** I4 requires
  exactly one party to act at every moment. Before F6 an escalated episode named the
  patient as `action_owner_id`, which tells the patient to act on a plan that has been
  handed to a service, a false-responsibility failure. The refusal path (an escalation
  naming no human path raises `DomainError`) closes the only hole. **Verified live:** an
  escalation moves the derived owner to the named path (section 4, A7 probe).
- **J4, O7 "strictly later" versus "not earlier".** **"Strictly later" is the right
  reading and the tests prove it independently.** A version at the *same* deadline is
  also refused (`test_an_equal_deadline_is_refused`), and my mutation M4 (`<=` to `<`)
  failed **that test alone**, demonstrating the equality boundary is separately proven,
  not redundant with the earlier-deadline test. The rationale holds: reading 6 reports an
  expiry event *by version*, so a sideways move would leave the current version with no
  expiry event and could return an expired episode to `open` (I2).
- **J5, recording a refused barrier and then returning 422.** **Correct, and it is the
  right shape.** The refused proposal is written *before* the exception is raised, so the
  ledger keeps the evidence that the episode reached the human path, and the caller still
  gets a typed refusal. The alternative (raise without recording) would lose the one fact
  the ledger exists to show. **Verified live:** the 422 body carries
  `stopped_at: human_path` and `barrier_recorded: true` (section 4, command 6).
- **J6, modifying pre-existing tests.** **Not weakened; correctly re-based.** The two
  modified tests in `test_domain.py:1064-1078` asserted the *old* behaviour that F6
  deliberately changed. The author changed exactly the assertion the behaviour change
  invalidated, **added a control** (`test_a_non_escalated_episode_still_names_the_patient`)
  and a refusal test, and left an explanatory comment. The `test_state.py` deadline change
  is likewise legitimate and commented. This is textbook handling, not weakening.

---

## 4. Evasions and attacks

**Attack that succeeded: A13, the self-contradicting approved gate document.** Two
commands, deterministic, no cleverness required:

```
$ git diff -- docs/plans/urgent-advice-accessibility/03-program-design.md | grep '^[+-]' | grep -i 'option c\|sourced verbatim'
-**[verified, approved decision]** The fixture wording is **sourced verbatim from attributable published guidance** rather than authored (Option C).
+### 6.2 The participant comparison: Option A, with Option C dropped
+**[verified, approved decision] Option C is dropped, 1 October 2026.**
```

and the surviving stale line:

```
$ sed -n '290p' docs/plans/urgent-advice-accessibility/03-program-design.md
3. **[resolved, 26 September 2026] Gate B material authority:** ... The fixture is sourced verbatim from attributable published guidance; **source selection, licensing and Singapore applicability remain unchecked and precede use**
```

The author edited section 6.2 and left section 8 item 3 asserting the opposite, in the
same approved document. That is finding B1.

**Attack that succeeded: B3, the false claim on the wire.** Reproduced live:

```
=== create ===
{"episode_id":"demo-episode-001", ..., "note":"Slice 1 tracer bullet: hardcoded. No disposition is written, no database exists, and the fixture wording is a provisional placeholder awaiting the Option C source check."}
[200]
```

The API asserts a pending source check that the same file says was resolved. Finding B3.

**Attack that partially succeeded: A12, stale references.** 20+ matches for
`Option C` survive outside the files the author updated, including `AGENTS.md:86`
(which still blocks Slice 5 on a source that was dropped) and two test-module
docstrings. Finding S3.

**Attacks that failed (the author's claims held):**

- **A1, all three numbers.** `419 passed, 1 warning` reproduced exactly, and the per-file
  split reproduced exactly: 97 domain, 141 boundaries, 37 api, 100 state, 44 service
  (sum 419). **Four of five `00-status.md` numbers in C1 are verified; the ninth-curl
  claim is verified below.** No false number found.
- **A1, the nine curls.** All nine behaviours reproduced, **but only after correcting the
  intake payload**: the brief's/C1's sequence as written posts `{"text": ...}`, and the API
  requires `{"confirmed_text": ...}` (`api.py:260`). With the brief's payload the intake
  returns 422 and **every subsequent call returns 409** ("episode has no disposition"),
  not the claimed results. With the correct payload all nine are correct: health 200,
  create 200, intake 200, barrier-permitted 200, barrier-no-proposal 200, **hallucinated
  route 422 with `stopped_at: human_path` and `barrier_recorded: true`**, escalation 200,
  unpermitted path 422, reassessment-no-code 200 `stop_at_human_path`, unknown code 200
  `stop_at_human_path`. **[verified]** This is a latent reproducibility defect in the C2
  evidence record, not a false claim about behaviour.
- **A1, CRLF.** All 16 changed/new files are pure CRLF, zero lone-LF. **CLEAN.**
- **A1, the em-dash ban.** Zero em dashes on added lines across 15 tracked files, and
  zero in the new `submission/usage-proof.md`. **CLEAN.**
- **A6, the append-only blind spot.** `barriers` refuses UPDATE and DELETE from a raw
  connection; `INSERT OR REPLACE` is refused only with `recursive_triggers` ON. This is
  exactly the pre-existing, disclosed O1 boundary, extended consistently. The author's
  claim is honest and unchanged by this slice.
- **A7, repeated escalations.** **Latest wins, both rows persist.** Probed directly:
  escalating `nurse_line` then `fictional_provider` leaves both rows in the table
  (oldest first) and derives `action_owner_id == "fictional_provider"`.
- **A9, decorative field.** **Refuted.** `human_path_route_id` is asserted at
  `tests/test_service.py:550` and serialised at `api.py:333`. Load-bearing.
- **A11, import boundary.** `tests/test_boundaries.py` passes, 141 tests; the slice's new
  imports (`dataclasses.replace` in `service.py`) violate nothing. No new leak.
- **A13, gate bookkeeping.** `git status --short -- docs/plans/urgent-advice-accessibility/04-slices.md`
  returns empty: **the Gate 4 document is genuinely untouched.** The claim "Gate 3
  reopened, Gate 4 untouched, implementation still authorised" is **verified correct**.
- **A10, `dataclasses.replace` on policy-authored data.** **Refuted as a live defect.**
  `service.reassess` replaces exactly two *state* fields (`episode_id`, `version`) and
  preserves every *policy* field, which is the correct division. It is additionally
  unreachable today: `PERMITTED_CHANGE_CODES` is empty, so no branch can be returned, and
  the future path is guarded by the `source is not DispositionSource.REASSESSMENT` check
  at `rules.py:631`.
- **A5, the F6 "latent" claim.** **Verified true.** `patient_lines` reads
  `disposition.next_owner_id` (`rules.py:538`) and ignores `closure.action_owner_id`
  entirely, so after an escalation a derived screen would say "You must act now." while
  the ledger names the nurse line. It is latent because nothing rendered over HTTP is
  derived: **confirmed by curl**, `GET /api/episodes/demo-episode-001` returns the
  hardcoded four lines even after an escalation. Deferral to Slice 10 with a Gate 1 copy
  touch is the right call and is disclosed rather than hidden.

---

## 5. Mutation results

Environment: `PYTHONPATH=src C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe -m pytest ... -o addopts="" -q`.
Each mutation: backed up outside the repo with md5, anchor asserted unique, one at a time,
failure mode inspected (not just colour), restored and md5-verified.

| # | Mutation | Target test(s) | Deselected | Result | Actual exception text | Restore |
|---|---|---|---|---|---|---|
| M1 | O7 check disabled (`if False and ... <= previous_deadline`) | `tests/test_state.py -k Monotonicity` | 97 | **2 failed, 1 passed** (the later-deadline control passed) | `Failed: DID NOT RAISE DeadlineNotMonotonic` (x2) | RESTORED CLEAN |
| M2 | F6 reverted to naming the patient (`return disposition.next_owner_id ...`) | `tests/test_{domain,service,api}.py -k "escalat or handoff or acting_party or moves_the_owner"` | 167 | **3 failed, 8 passed** | `AssertionError: assert 'patient' == 'nurse_line'` | RESTORED CLEAN |
| M3 | Refused barrier recorded as not-a-stop (`stopped_at_human_path=True` to `False`) | `tests/test_service.py -k "hallucinated or refused"` | 38 | **1 failed, 5 passed** | `assert 0 == 1` | RESTORED CLEAN |
| M4 | O7 boundary off-by-one (`<=` to `<`) | `tests/test_state.py -k Monotonicity` | 97 | **1 failed, 2 passed** | `Failed: DID NOT RAISE DeadlineNotMonotonic` on `test_an_equal_deadline_is_refused` only | RESTORED CLEAN |
| M5 | F6 no-human-path refusal neutralised | `tests/test_domain.py -k "no_human_path or escalation"` | 94 | **1 failed, 2 passed** | `Failed: DID NOT RAISE DomainError` | RESTORED CLEAN |
| M7 | Barrier event kind renamed (`"barrier_recorded"` to `"barrier_recorded_MUTATED"`) | `tests/test_{state,service}.py -k "Barrier or barrier"` | 135 | **1 failed, 8 passed** | `AssertionError: assert 'barrier_recorded' in ['episode_created', ..., 'barrier_recorded_MUTATED']` | RESTORED CLEAN |

**Author's three mutations, reproduced and reconciled:**

- **O7 disabled → author says "2 failed".** Reproduced: **2 failed**. **Agree.**
- **F6 reverted → author says "2 failed".** Reproduced at **3 failed** with a broad
  selector, and at **2 failed** with `-k "escalation or handoff"` against
  `test_domain.py` + `test_service.py` only (excluding `test_api.py`). The author's
  number is **selector-dependent, not false**; see A3 below. **Agree with a caveat.**
- **Refused barrier not-a-stop → author says "1 failed".** Reproduced: **1 failed**. **Agree.**

**Full suite after every restore: 419 passed, 1 warning.** All three mutation targets
returned to their original md5 (`feadebea...`, `a6df17ef...`, `a491ed8a...`).

**A3, the `-k` deselection trap, demonstrated.** Re-running the F6 mutation:

```
-k "escalation or handoff" on test_domain.py test_service.py  ->  2 failed, 5 passed, 134 deselected
-k "escalat or Escalat or handoff or acting_party or moves_the_owner" on all three files
                                                             ->  3 failed, 8 passed, 167 deselected
```

The reported count is a function of the selector, not of the test suite. The author's
"2 failed" reads as "two tests catch this defect"; three do. Reporting a `-k` count
without the selector and the deselected number understates the blast radius.

**Test quality: no redundant mutations and no test that cannot fail was found.** The
author's three mutations target three different branches (O7 comparison, F6 owner
resolution, barrier stop flag) and each RED-mapped to a distinct branch. My M4 proves the
equality boundary is independently covered, so it is not redundant with the
earlier-deadline test. M7 proves the event emission is covered. Every mutated branch
produced a real failure, not a colour change.

---

## 6. Claims in `00-status.md` that are false or unverifiable

| Line | Claim | Verdict |
|---|---|---|
| 118 | "**419 passed, 1 warning** ... 97 domain, 141 boundaries, 37 api, 100 state, 44 service" | **TRUE.** Reproduced exactly, both total and split |
| 119 | "Nine calls, all correct" (the live curls) | **INCOMPLETE.** All nine *behaviours* are correct, but the sequence is not reproducible as written: the intake payload must be `{"confirmed_text": ...}`, not `{"text": ...}`. With the written payload, the intake 422s and calls 4-10 all return 409 |
| 120 | "Three, each seen RED on exactly its own test" | **IMPRECISE.** True for O7 and barrier. For F6 the blast radius is **three** tests under a broad selector; "exactly its own test" (singular) is a `-k` artefact of the author's narrower selection |
| 110-111 | "fixtures/scripted_episode.json, demo/fixture.py and the API's policy_provenance all carry the corrected record" | **PARTIALLY FALSE.** `demo/fixture.py` and `policy_provenance` (`api.py:114-120`) do. But `api.py:195-197` (the `POST /api/episodes` `note`) still carries the *uncorrected* record, and it is the value that reaches the client. Finding B3 |
| 5, 91-97 | Gate 3 reopened 1 October 2026, Gate 4 untouched | **TRUE.** `04-slices.md` is unmodified in the tree |
| 60-66 | The three-row source-check table | **TRUE as read.** MOH clause 11, HealthHub clause 12.1, the OGL Singapore-applicability failure: all consistent with the primary terms as quoted |
| 105 | "**Latent today:** every HTTP path returns hardcoded fixture lines" | **TRUE.** Confirmed by curl against `GET /api/episodes/{id}` after an escalation |

No claim was found that overstates a *test result*. The false claims are documentary
(stale Option C text) and evidential (the unreproducible curl sequence), not numerical.

---

## 7. Could not verify

- **The Gate 1 "Approved patient-facing copy" subsection in `01-product.md`.** The brief's
  read order does not include `01-product.md`, and it is not in this slice's diff, so the
  claim that `COORDINATOR_FALLBACK_TEXT` now has an approved source was not independently
  checked. **[unknown]** It does not affect D1 or D2.
- **The three chat screenshots' actual contents.** `submission/usage-proof.md` and the
  folder README assert the redaction check was performed; the images were not opened, so
  the "no AppKey, token, key or credential in any of the three" claim is **[vendor-claim]**
  from the author, not verified here. The brief scoped this review to Slice 5 and the
  redaction is a separate concern.
- **`spike/kill_spike/intake.py` behaviour.** Read but not executed; the K2 promotion was
  assessed by reading the spike test and the promoted test side by side, not by running the
  spike.
- **`git log` / commit history for this slice.** Refused by the read-only rule and
  unnecessary: nothing is committed, and the tree was the object of review.

The list is deliberately short but is **not empty**, which is the honest state: the two
items above are genuinely outside what this review was allowed or asked to inspect.
