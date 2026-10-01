# Slice 4 adversarial review: PlanBack end to end, the hint ladder, bounded repair

**Supporting note. Authoritative for nothing.** This review is evidence about a
slice. `00-status.md` remains the only authority for gate and slice state.

- **Reviewer:** independent adversarial review, no prior context in this session
  beyond the brief and the read order it names.
- **Date:** 1 October 2026.
- **Branch:** `slice-4` (working tree, uncommitted, three untracked files).
- **Baseline at review time:** `380 passed, 1 warning` (`-o addopts="" -q`).
- **Nothing was committed, pushed, stashed, branched, checked out or deleted.**
  Seventeen mutations were applied and reverted; every one returned to its
  recorded md5 (`RESTORED-CLEAN` on all seventeen). As written, the only file this
  review added to the tree was itself.
- **Remediation followed on the same day,** on the author's instruction to
  continue: the two test gaps are closed and the record is corrected. Four more
  files changed, `tests/test_service.py`, `00-status.md`, `PROGRESS.md` and
  `tasks/todo.md`. Section 10 lists what landed where, so this note and the record
  do not contradict each other.

---

## 1. VERDICT

**APPROVE WITH CHANGES.**

The exit contract is met line by line, and the mechanisms behind it are real
rather than asserted: fifteen of seventeen mutations were detected, each with a
control that stayed green, and the two that were not are exactly B1 and B2
below. Both layered guards (the repair cap, the transcript ordering rule) are
genuinely independent, because removing the service layer leaves the store layer
catching the same defect with its own typed error.
No forbidden area was touched. The status document's claims about test counts,
line endings, em dashes, and "no new table" are all true as written.

Three findings are blocking, and none of them is a broken mechanism. Two are
**unproven claims**: a mutant that records a false recall outcome for a wholly
unrecognised answer survives the entire suite, and the `H1` rung of the ladder has
no test at all, so the contract line "H0 to H3 recorded" is three-quarters
evidenced. The third is that the intake binding rule is a bare substring match
while both its test name and the status record describe it as a general
fail-closed rule.

All three are closeable with tests and one narrowed sentence. Nothing needs to be
rebuilt.

---

## 2. BLOCKING FINDINGS

**Status of these three, as of the remediation that followed this review the same
day: B1 CLOSED, B2 CLOSED, B3 carried as a decision at Slice 5.** The findings are
written below as they stood at review time, which is what a review is for. Section
10 records where each correction landed, and the record carries the detail.

### B1. A mutant that records a false recall pass survives the whole suite

- **File:** `src/carerelay/service.py:510` (the guard), `:511-513` (the outcome
  selection it feeds).
- **Defect.** `_score` computes `understood = not comparison.mismatched and not
  comparison.uncertain`, then records
  `RECALL_OUTCOME_BY_LEVEL[level] if understood else NOT_RECALLED`. Delete the
  `and not comparison.uncertain` half and a restatement the coordinator could not
  recognise at all records `recall_unaided`, `recall_scaffolded` or `recall_cued`
  instead of `not_recalled`.
- **Evidence.** Mutation **M15** applied exactly that edit. **Undetected:** the
  full suite stayed green (`380 passed`). Driven through the real app with the
  mutation in place, the round for the text `"not sure at all"` returned
  `understood: false` alongside `outcome: "recall_unaided"`, and the recorded row
  carried `recall_unaided`. Baseline for the same input is
  `understood: false, outcome: "not_recalled"`.
- **Why it matters.** This is the single most load-bearing outcome mapping in the
  slice. The product exists to distinguish "the patient understood their plan"
  from "they did not", and this mutant writes the first into the clinical record
  for a patient who committed to nothing. It is also internally inconsistent: the
  same response says `understood: false` and `outcome: recall_unaided`.
  `00-status.md:305` cites `test_h3_is_not_recalled_even_when_its_comparison_is_clean`
  as the proof for "H3 is `not_recalled`, never a pass", and that test does prove
  the H3 half. Nothing proves the **uncertain** half, which is the half a
  coordinator that half-heard the answer produces.
- **Smallest fix.** Add one assertion to
  `tests/test_service.py:250` (`test_an_unresolvable_span_is_uncertain_and_never_a_mismatch`):
  `assert outcome.outcome is RecallOutcome.NOT_RECALLED`. Confirm it goes red
  against M15 before accepting it.

### B2. The `H1` rung has no test, so "H0 to H3 recorded" is not proven as stated

- **File:** `src/carerelay/domain/models.py:73` (`HintLevel.H1` mapping);
  `tests/test_service.py:262-269` (the test the record cites);
  `docs/plans/urgent-advice-accessibility/00-status.md:302` (the claim).
- **Defect.** The contract line is "H0 to H3 recorded". The cited proof,
  `test_the_record_carries_the_hint_level_and_the_round`, submits **`H2` only**
  and asserts `RECALL_CUED`. `H0` and `H3` are covered by other tests. `H1` is
  covered by nothing anywhere in `tests/`.
- **Evidence.** Mutation **M13** changed
  `HintLevel.H1: RecallOutcome.RECALL_SCAFFOLDED` to `RECALL_UNAIDED`.
  **Undetected:** `test_service.py` 28 passed, `test_api.py` 25 passed,
  `test_domain.py` 95 passed. The control, **M16**, which broke the `H0` mapping,
  was detected by two tests. So the mapping table is load-bearing and one entry in
  it is untested.
- **Why it matters.** `H1` is the rung the product offers between the bare
  question and showing the plan card, and `recall_scaffolded` is the outcome the
  study's secondary measures read. A wrong mapping there is a silently wrong
  research result, which is the same class of defect as a wrong clinical string.
- **Smallest fix.** Extend `test_the_record_carries_the_hint_level_and_the_round`
  to parametrise over all four levels, asserting the recorded `hint_level` and the
  recorded outcome for each, so `H1 -> recall_scaffolded` is exercised. Confirm it
  goes red against M13.

### B3. The intake binding rule is a substring match, and both the test name and the status record overstate it

- **File:** `src/carerelay/service.py:263` (`if self._bound_complaint not in
  rules.normalise(confirmed_text):`); `tests/test_service.py:366-371`;
  `tests/test_api.py:235-244`;
  `docs/plans/urgent-advice-accessibility/00-status.md:331`.
- **Defect.** Recognition is "the bound phrase appears anywhere in the normalised
  text". It is not "the complaint is the bound complaint". Neither negation nor a
  third-party subject nor an accompanying red flag changes the answer. The status
  record states "a complaint this fixture is not bound to stops at the human path
  with 422"; the test is named
  `test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path` but
  submits only `"something this fixture does not cover"`, a string with zero token
  overlap. So the test proves the disjoint case and nothing else.
- **Evidence.** Driven through `POST /api/episodes/{id}/intake` on a fresh store
  per case. **Scored with 200 and disposition v1:** `"help sorting out my
  appointment, also I have chest pain and cannot breathe"`;
  `"I have crushing chest pain. Also help sorting out my appointment"`;
  `"help sorting out my appointment, I think I am having a stroke"`;
  `"I do not need help sorting out my appointment"` (negated);
  `"does my mother need help sorting out my appointment"` (third party).
  **Stopped with 422:** `""`, `"   "`, `"my appointment"` alone,
  `"my chest hurts"`.
- **Why it matters, stated at its true size.** No clinical branch is derived from
  free text, and the disposition issued is the same non-clinical fixture plan in
  every one of the accepted cases, so there is **no clinical mis-triage in the
  demo today**. The defect is that the one input the whole fail-closed posture
  rests on is not fail-closed: a complaint carrying a red-flag symptom is bound to
  the demo plan rather than stopped, and the documents describe the rule as
  broader than it is. When a sourced fixture arrives at Slice 5 the same substring
  rule would bind a real complaint that also carries a red flag.
- **Smallest fix, and it is a decision, not a code tweak.** Either (a) require the
  normalised complaint to **equal** the bound phrase for the fixture-bound demo,
  which is the honest reading of "the one phrase this fixture is bound to", or
  (b) keep substring binding and correct both the status record and the test name
  to say "a complaint with no recognised phrase stops", with a named open item
  recording that red-flag and negation detection is a reviewer-gated decision that
  no later slice may implement silently. Do not author red-flag detection now: it
  is clinical content and there is no reviewer.

---

## 3. NON-BLOCKING FINDINGS

### NF1. A second episode's intake raises an unhandled `sqlite3.IntegrityError`

- **File:** `src/carerelay/service.py:270-276` calls
  `state.register_policy_version` unconditionally; `src/carerelay/state.py:688-693`
  is a plain `INSERT` with no idempotency guard.
- **Issue.** `register_policy_version` is untouched Slice 3 code
  (`git log -S` puts it in `ad3401a`), but `service.intake` is new in this slice
  and calls it on every assessment. The second episode assessed on one database
  fails: `sqlite3.IntegrityError: UNIQUE constraint failed:
  policy_versions.version`. The API's intake route catches `EpisodeNotFound`,
  `EpisodeAlreadyAssessed` and `IntakeNotRecognised`, so this surfaces as an
  unhandled exception, not a typed refusal.
- **Reachability, stated honestly.** Not reachable through HTTP today, because
  `POST /api/episodes` hardcodes `DEMO_EPISODE_ID` and `intake` 404s for any other
  episode id. I reached it by calling `service.intake` directly and, separately, by
  pre-creating the episode in the store and then hitting the route, which raised.
  So it is latent, not live.
- **Recommendation.** Make `register_policy_version` idempotent (`INSERT OR
  IGNORE`, or a select-then-insert inside the existing `BEGIN IMMEDIATE`), and add
  a test that assesses two episodes against one store. It will bite the first time
  the product holds more than one episode, which is Slice 7.

### NF2. Malformed enum values return HTTP 500 instead of a typed refusal

- **File:** `src/carerelay/service.py:311-312` (`HintLevel(hint_level)`,
  `HintEventKind(kind)`), `:483-484` (`HintLevel`, `InputMode`);
  `src/carerelay/api.py:434-447`, `:461-479`, `:494-521` (the handlers).
- **Issue.** A bad value raises `ValueError`, which no route catches, so FastAPI
  returns 500 with a stack trace. Measured, with `raise_server_exceptions=False`:
  `restatements` with `hint_level: "H9"` -> 500; `input_mode: "telepathy"` -> 500;
  `hint-events` with `hint_level: "H9"` -> 500; `event: "auto_hide"` -> 500.
  Missing fields are correctly 422 (Pydantic). No row is written in any case, so
  this is not fail-open; it is an unclosed refusal.
- **Recommendation.** Catch `ValueError` in the three routes and map it to 422
  with the same shape as the other refusals, or validate the enum in the Pydantic
  request model so Pydantic does it. Either is a small change.

### NF3. The dead 422 branch on the hint route

- **File:** `src/carerelay/api.py:441-442`.
- **Issue.** The route maps `PolicyViolation` to 422, and the intended source is
  `rules.UnpermittedHintEvent` from `hint_transition`. That exception is
  unreachable from this path: `service.hint_state` (`service.py:333-336`) resets
  the state to the event's level whenever the levels differ, so the level guard in
  `hint_transition` (`rules.py:631-634`) can never fire. A bad event **name** is
  caught earlier by `HintEventKind(kind)`, which raises `ValueError` (NF2). So the
  route's 422 branch is dead code in practice.
- **Recommendation.** Either delete the branch and let NF2's fix carry the case,
  or route the enum construction through a domain validator that raises
  `PolicyViolation`, which is the shape the handler was written for.

### NF4. `transcript_confirmed` is recorded from an unverified id on text and chip rounds

- **File:** `src/carerelay/service.py:458-470` (verification runs only for
  `InputMode.VOICE`) and `:522`
  (`transcript_confirmed=transcript_confirmation_id is not None`).
- **Issue.** A `text` or `chips` restatement carrying any non-null
  `transcript_confirmation_id` is recorded with `transcript_confirmed = 1` even
  though nothing was verified and, measured, even when the id is the digest of a
  sentence nobody confirmed. A random string would do the same. The record then
  asserts that a transcript was confirmed when none was.
- **Recommendation.** Set `transcript_confirmed` only after the confirmation has
  been verified against the store, and treat a supplied id on a mode that carries
  no transcript as a 422 rather than as a claim. Low severity (it can only
  overstate, never understate), but it is a record-integrity claim.

### NF5. The coordinator docstrings overclaim what the boundary hides

- **File:** `src/carerelay/coordinator.py:51-59` ("cannot see the expected
  values, so it cannot echo the answer"); `src/carerelay/service.py:423-430`
  ("What is excluded is anything that would let the coordinator see the expected
  answer").
- **Issue.** By inspection, `extract_plan` receives `AllowedPlanValues`, never a
  `Disposition`, so the load-bearing claim in the brief ("never sees the
  disposition") is **[verified] true**. But `_allowed_values` builds
  `action_forms` from `policy.action_aliases | policy.permitted_action_ids`, and
  `permitted_action_ids` **contains** the expected `action_id`; likewise
  `owner_forms` contains the expected `next_owner_id`. So the coordinator sees a
  set that contains two of the three expected values, and the docstrings say it
  cannot see them. The deadline is genuinely protected: `deadline_forms` are
  surface phrases, never the resolved instant, so the one field K1 turns on is
  not narrowed either.
- **Recommendation.** Keep the mechanism; correct the sentence. The honest
  statement is: the coordinator receives candidate surface forms, including the
  canonical ids, so it can recognise an answer but cannot determine which
  candidate is expected. This is a boundary against accidental echo, not against
  a coordinator that already holds the policy.

### NF6. The payload-redaction claim has no implementation to verify

- **File:** `docs/plans/urgent-advice-accessibility/02-architecture.md`, section 8
  ("Observability & logging"): "Payloads are redacted from application logs".
  `src/carerelay/state.py:1519-1523` relies on it.
- **Issue.** There is no logging in `src/` at all (`grep` for `import logging`,
  `logging.`, `logger` returns nothing). So the claim is vacuous rather than
  false, and `events.payload` genuinely does hold raw confirmed patient text
  (measured: `transcript_confirmed` payload contains the full string).
- **Recommendation.** No change now. Record it as an open item against the slice
  that introduces logging, so the redaction is built with the logs rather than
  after them.

### NF7. Nits

| File:line | Issue | Recommendation |
|---|---|---|
| `src/carerelay/service.py:454-457` | Refusal reads "an voice restatement may not be scored" | Pick the article from the mode value, or drop it: "a restatement in voice mode ..." |
| `src/carerelay/service.py:189` vs `:510` | `understood` is computed twice, once as a property and once as a local | Have `_score` call `comparison.is_clean()` and use it for both, so the two cannot drift |
| `src/carerelay/api.py:343-350` | The 503 body nests `{"detail": {"detail": ...}}` | Rename the inner key, for example `reason`, so the envelope is not self-similar |
| `src/carerelay/state.py:254` | The confirmation id is an unsalted digest of patient text, returned to the client | Acceptable for a demo; note it, because an unsalted digest of short text is a dictionary-recoverable copy of the input |
| `tests/test_service.py:300-309` | `test_no_event_vocabulary_member_hides_the_card_without_a_patient_action` filters member **names** for `"hid"`/`"auto"`, so a hiding member named `dismiss` would evade it | The behavioural enumeration in `tests/test_domain.py:796-811` is the real check; delete this one or replace the name filter with it |
| `tests/test_domain.py:576-579` | `test_the_rule_has_teeth` re-asserts the `(VOICE, None)` case already covered by the parametrised test two lines up | Redundant; the parametrised case is the stronger form |
| `tests/test_api.py:368-370` | `test_the_dwell_marker_would_be_caught_if_it_were_there` asserts a substring against a string literal, scanning no production surface | Honest as a needle-exists control, but M9 already proves the real assertion can fail; consider deleting |
| `src/carerelay/api.py:186` | `persona=fixture.DEMO_EPISODE_ID and "fictional older adult"` is a truthiness expression where a literal was meant | Pre-existing Slice 1 code, not in this diff; fix at the next touch |

---

## 4. MUTATION RESULTS

Seventeen mutations, one at a time. Each anchor was asserted unique in bytes
before use (`data.count(old) == 1`), each target was backed up outside the repo,
and each was restored with an md5 re-check. **All seventeen reported
`RESTORED-CLEAN`**, and a final md5 sweep of the five mutated files confirmed no
drift. Each mutation was paired with a control test that must stay green, so a red
result is attributable to the mechanism rather than to a broken write path. No
`-k` selection was used; whole files were run and the failing test names were read
out of the report, so a silently empty selection was not possible.

| # | File:line | Mutation | Test that went red | Right test? | Control stayed green | Verdict |
|---|---|---|---|---|---|---|
| M1 | `service.py:405` | `if repair_round > MAX_REPAIR_ROUNDS:` -> `> 99:` (service cap neutralised) | `test_two_repairs_is_the_maximum` | yes | `test_a_repair_that_lands_is_a_clean_pass` | **PROVEN** |
| M2 | `state.py:1375` | `if not 0 <= repair_round <= MAX_REPAIR_ROUNDS:` -> `if False:` | `test_the_record_refuses_a_third_repair_round_on_its_own` | yes | `test_two_repairs_is_the_maximum` | **PROVEN** |
| M3 | `service.py:398` | `if latest_id != restatement_id:` -> `if False:` (stale check off) | `test_repairing_an_older_round_cannot_evade_the_cap` | yes | `test_two_repairs_is_the_maximum` | **PROVEN** |
| M4 | `service.py:453` | service `may_score_restatement` call -> `if False:` | `test_an_unconfirmed_voice_transcript_cannot_be_scored` | yes | `test_a_confirmed_voice_transcript_can_be_scored` | **PROVEN** |
| M5 | `state.py:1370` | store voice/confirmed guard -> `if False:` | `test_the_record_refuses_an_unconfirmed_voice_row_on_its_own` | yes | `test_a_text_restatement_needs_no_confirmation` | **PROVEN** |
| M6 | `models.py:75` | `H3 -> NOT_RECALLED` becomes `RECALL_CUED` | `test_h3_is_not_recalled_even_when_its_comparison_is_clean` and `test_h3_is_never_a_comprehension_pass` | yes, both | `test_an_unaided_match_records_recall_unaided` | **PROVEN** |
| M7 | `service.py:459` | `derive_confirmation_id(...)` reverted to the shadowing name | `test_a_confirmed_voice_transcript_can_be_scored` | yes | `test_a_text_restatement_needs_no_confirmation` | **PROVEN** |
| M8 | `service.py:499` | short-circuit the extraction so the coordinator is never called | `test_a_dead_coordinator_stops_the_flow_without_recording_a_round` (service), `test_the_flow_stops_with_a_text_fallback_and_scored_false` (API) | yes, both | `test_the_record_refuses_a_third_repair_round_on_its_own` | **PROVEN** |
| M9 | `api.py:314` | add `dwell_seconds` to `RestatementResponse` | `test_the_restatement_response_carries_no_dwell_marker` | yes | `test_the_hint_event_response_carries_no_dwell_marker` | **PROVEN** |
| M10 | `api.py:344` | `_coordinator_down` `status_code=503` -> `200` | `test_the_flow_stops_with_a_text_fallback_and_scored_false`, `test_the_fallback_is_never_a_200_with_empty_mismatches` | yes, both | `test_the_label_is_inside_the_restatement_projection` | **PROVEN** |
| M11 | `rules.py:316` | `next_repair` cap `>= MAX_REPAIR_ROUNDS` -> `if False:` | `test_two_repairs_is_the_maximum` | yes | `test_a_repair_that_lands_is_a_clean_pass` | **PROVEN** |
| M12 | `rules.py:346` | `may_score_restatement` returns `True` always | `test_an_unconfirmed_voice_transcript_cannot_be_scored` (service), `test_a_voice_transcript_needs_a_confirmation_the_other_modes_do_not` (domain) | yes, both | `test_a_text_restatement_needs_no_confirmation` | **PROVEN** |
| M13 | `models.py:73` | `H1 -> RECALL_SCAFFOLDED` becomes `RECALL_UNAIDED` | **none** | n/a | n/a | **UNDETECTED** (B2) |
| M14 | `service.py:189` | `RestatementOutcome.understood` drops the uncertainty half | `test_an_unresolvable_span_is_uncertain_and_never_a_mismatch` | yes | n/a | **PROVEN** |
| M15 | `service.py:510` | `_score`'s `understood` drops the uncertainty half | **none** | n/a | n/a | **UNDETECTED** (B1) |
| M16 | `models.py:72` | control for M13: `H0 -> RECALL_UNAIDED` becomes `NOT_RECALLED` | `test_an_unaided_match_records_recall_unaided`, `test_a_repair_that_lands_is_a_clean_pass` | yes, both | n/a | **PROVEN** |

An additional order check, **M17**, reversed `COMPARISON_FIELDS` in
`models.py:39-43`. **Detected** by
`test_repair_targets_the_first_unresolved_field_in_order`, so the repair order is
genuinely load-bearing and proven.

**Failure modes read, not just colours.** For the two layered guards the
attribution matters, so the exception was read rather than the test colour:

- **M1** (service cap removed) fails with
  `carerelay.state.RepairRoundOutOfRange: repair_round 3 is outside 0..2`. The
  **store** catches the third round on its own, so the cap is two independent
  mechanisms and the claim at `00-status.md:306` is **[verified] true**.
- **M4** (service transcript guard removed) fails with
  `carerelay.state.UnconfirmedTranscript`. The **store** refuses the unconfirmed
  voice row on its own, so `00-status.md:327`'s "enforced twice on purpose" is
  **[verified] true**.
- **M8**'s red is `DID NOT RAISE`, which is the correct mode: the flow continued
  and wrote a round.

---

## 5. EDGE-CASE RESULTS

Run through `TestClient` against a fresh in-memory store per case, except where a
shared store is named.

| # | Probe | Result | Read |
|---|---|---|---|
| E1 | Voice restatement whose `transcript_confirmation_id` is a **valid digest of different text** | **409**, "the confirmation does not match the text being scored" | Correct. The digest binding works, and this is the API-level confirmation of M7. |
| E2 | Voice restatement with the correct digest of the scored text, but never recorded for this episode | **409**, "no confirmation ... was recorded for episode ..." | Correct. The store-existence half is real. |
| E3 | Text restatement with **no** `transcript_confirmation_id` | **200**, `understood: true` | Correct: text carries no machine transcript. |
| E4 | Voice restatement with **no** `transcript_confirmation_id` | **409** | Correct. Wording nit only ("an voice"). |
| E5 | Repair a restatement belonging to **another episode** | **404**, "not found for episode ..." | Correct, and no existence leak: the id is echoed only because the caller supplied it. |
| E5b | Repair a bogus restatement id | **404** | Correct. |
| E6 | The fourth call overall (round 0, repair 1, repair 2, then a third repair) | **409**, "already at repair round 2; two repairs is the maximum and a third is never offered (C6). Route to the human path." | Correct and honest. Rounds seen were 0, 1, 2, with `routes_to_human_path: true` and `human_path_route_id: "nurse_line"` at round 2. |
| E7 | `dwell_seconds` supplied to the **restatement** route (not a hint route) | Response keys carry no dwell; the `restatements` row stores `42.5`; **zero** `hint_event` rows created | Correct. It is stored ledger-side and absent from the response. Note it lands in `restatements.dwell_seconds`, not in `events.payload`; the contract's "`events.payload` for hint_event rows" is about hint events specifically. |
| E8 | `hint_level: "H3"` with a **clean** comparison | **200**, `understood: true`, `outcome: "not_recalled"` | Correct. H3 is never a pass even when every field resolves and agrees. |
| E9 | Coordinator returns `None` for all three spans | **200**, `understood: false`, `uncertain` = all three fields, `outcome: "not_recalled"`, one row written | Correct: not a false pass. It writes a row because a round genuinely happened; it records no recall. |
| E10 | Malformed enum values | `hint_level: "H9"` -> **500**; `input_mode: "telepathy"` -> **500**; `hint-events` `hint_level: "H9"` -> **500**; `event: "auto_hide"` -> **500**; missing fields -> **422** | Finding NF2. No row written in any case, so not fail-open. |
| E11 | Intake recognition | See B3 | Substring binding. |
| E12 | Does any response echo the confirmed transcript text? | `transcript-confirmations` returns only `episode_id` and `confirmation_id`; the restatement response returns no spans and no text | Correct. The raw spans live only in `restatements.extracted_json`. |
| E13 | `GET /api/episodes/{id}` after a real disposition exists | **200** with the four Slice 1 hardcoded lines, deadline "Before 6pm today." | Correct: still the Slice 1 fixture, not the store. Confirms the "not in this slice" claim. |
| E14 | What one scored round stores | `extracted` = the three raw spans plus an empty `uncertain_fields`; `comparison` = matched all three; the `restatement_recorded` event carries `hint=H0 round=0 outcome=recall_unaided` and **no free text** | Correct, and it matches the docstring's claim that the audit event carries no span. |
| E15 | Where raw patient text lands | `transcript_confirmed` event payload holds the full confirmed string | As designed (section 8 permits it in the clinical record), and it makes NF6 concrete. |
| E16 | Text restatement carrying an **unverified** confirmation id | **200**, row records `transcript_confirmed = True` | Finding NF4. |
| E17 | Chips restatement carrying an unverified confirmation id | **200**, row records `transcript_confirmed = True` | Finding NF4. |
| E18 | Coordinator down, at the API level, with `dwell_seconds` supplied | **503**, `scored: false`, a `text_fallback`, **0 restatement rows, 0 hint_event rows**, events unchanged | Correct, and it is the strongest form of the claim: the absence of a row is measured, not inferred. |
| E19 | Repair in voice mode with the correct digest but no recorded confirmation | **409** | Correct. |
| E20 | Does the restatement response leak the extracted spans? | No spans, no dwell, no text; carries `simulated: true` and `fixture_label` | Correct. |

---

## 6. FALSE-CLAIM AUDIT

Every claim named in the brief, checked rather than accepted.

| Claim | Verdict | Evidence |
|---|---|---|
| "380 passed, 1 warning" | **[verified] true** | Re-ran `pytest tests -o addopts="" -q`: `380 passed, 1 warning in 8.17s`. |
| Per-file split 95 / 141 / 25 / 91 / 28 summing to 380 | **[verified] true** | Measured per file: domain 95, boundaries 141, api 25, state 91, service 28. Sum 380. |
| "up from 332", implying 48 new tests | **[verified] consistent** | `332 + 48 = 380`. The diff adds 18 test defs to tracked files and 28 to the new `test_service.py` = 46 defs; the parametrised transcript test expands one def into three, giving 48. |
| "Zero lone LF across the ten touched files" | **[verified] true**, and understated | Byte-wise: all twelve touched files (nine modified, three new) have `lone_LF = 0`. `coordinator.py`, `service.py` and `test_service.py` are CRLF despite being created by a tool that emits LF, so the normalisation was done. |
| "Zero U+2014 on any added line" | **[verified] true** | `git diff -U0 -- src tests \| grep -c "^+.*<U+2014>"` = 0, where `<U+2014>` is the literal character. Over all tracked files, also 0. |
| "The coordinator returns spans only and never sees the disposition" | **[verified] true**, with a docstring caveat | `extract_plan(confirmed_text, allowed_values)` receives `AllowedPlanValues`; no `Disposition` is reachable from `coordinator.py`. Caveat NF5: the surface-form set contains the canonical action and owner ids, so the docstrings' stronger "cannot see the expected values" is an overclaim. |
| "No new table was added" | **[verified] true** | `git diff -U0 -- src/carerelay/state.py \| grep "^+.*CREATE TABLE"` returns nothing. `hint_event` and `transcript_confirmed` rows live in `events`; `record_hint_event` and `record_transcript_confirmation` call `_append_event` only. |
| "`check_same_thread=False` AND every use case runs under `_DB_LOCK`" | **[verified] true** | `api.py:102` opens with `check_same_thread=False`. All six store-touching routes wrap their single use case in `with _DB_LOCK:` (`:182`, `:370`, `:412`, `:435`, `:462`, `:495`). The three routes that do not take the lock (`/health`, `/`, `GET /api/episodes/{id}`) never touch the store. |
| "The repair cap is enforced at the service layer AND the store layer" | **[verified] true** | M1 and M2, with failure modes read: removing either layer leaves the other catching the defect with its own typed error. |
| "The confirmation digest was never computed; the import is aliased to `derive_confirmation_id`" | **[verified] true** | `service.py:71-76` aliases the import with a comment; M7 reverts it and the voice tests go red. |
| "`GET /api/episodes/{id}` still serves the Slice 1 hardcoded four lines" | **[verified] true** | E13, after a real disposition exists. |
| "`permitted_change_codes` is empty, so every reassessment fails closed" | **[verified] true** | `fixture.py:138` is `frozenset()`; no reassessment route exists (`api.py` declares nine routes, none of them reassessment, barriers, actions, consents, escalations, acceptances, ledger, options or callbacks). |
| "Two defects found during the build, both fixed, both real" | **[verified] true** | Both are now load-bearing: M3 proves the stale check is what stops the forked repair, and M7 proves the digest alias is what makes the binding work. |
| "H0 to H3 recorded" | **[falsified as stated]** | B2. `H1` has no test; M13 survives the suite. |

---

## 7. SCOPE CREEP ASSESSMENT

The status record names five unlisted items and one Gate 4 gap. Assessed on
whether each closes a real gap or should have been a separate slice.

| Item | Assessment |
|---|---|
| 1. `api.py` gained five routes | **Legitimate.** The Deliverable row names four HTTP routes and the Check is a live walkthrough. A use case with no route is not `POST /restatements`. Not creep. |
| 2. `state.py` gained seven repository methods | **Legitimate and unavoidable.** Slice 3 created `restatements` with no writer, so two contract lines ("H0 to H3 recorded", "`dwell_seconds` to the ledger only") were unreachable without them. The claim that no new table was added is **[verified] true**, and reusing `events` rather than adding a `hint_events` table is the smaller change. |
| 3. `domain` gained `InputMode` and `may_score_restatement` | **Legitimate, and correctly placed.** D2 puts safety decisions in the module that cannot do I/O. M4 and M5 show both layers refuse independently. |
| 4. `SqliteEpisodeStore` gained `check_same_thread`, and `api.py` passes `False` under a lock | **Legitimate and necessary.** FastAPI serves synchronous routes from a thread pool, so a shared connection raises `sqlite3.ProgrammingError` without it. The flag is off **and** every store path is locked, which is the safe pairing, not the flag alone. |
| 5. `COORDINATOR_FALLBACK_TEXT` is authored, not approved | **Acceptable for a labelled research demonstration, with one condition.** The copy is `"We could not check that answer just now. Your plan has not changed."` It names no symptom, no urgency, no route and no deadline; it asserts only that the check did not happen, which is the honest statement of the degraded state at `02-architecture.md` section 8. It is not a clinical string, and the whole product carries a visible simulated label. The condition: the slice already records that it "needs a Gate 1 touch", and that must be a tracked open item against the Gate 1 document, not a note that decays. If it is not tracked, it is the same defect class as a clinical string with no source. |
| Gap. The intake and assessment path, scheduled in no slice | **A real gap, closed narrowly and correctly in shape.** PlanBack cannot run without a disposition, and `02-architecture.md` 3.1 forbids writing one at episode creation, so some intake had to exist. The shape is right: the route is the one the approved architecture names, a recognised complaint inserts the preauthored fixture disposition, and nothing is derived from free text. Two things do not clear: the binding rule is a substring match (B3), and a second episode's intake raises an unhandled `IntegrityError` (NF1). The status record is also right that the full clarification loop remains unowned and unestimated; that is the honest description. |

**Forbidden areas, checked and clean.** `presentation.py` does not exist and
`project_patient` is referenced nowhere. There is no barrier, action, consent,
escalation, acceptance, reassessment, expiry-projection, ledger or options route.
`permitted_change_codes` is empty. `GET /api/episodes/{id}` serves the Slice 1
fixture. The `git diff --stat` file list is exactly the nine modified files the
brief names, plus three new files. **No scope creep into any of them.**

---

## 8. WHAT THE EVIDENCE DOES NOT PROVE

An empty list here would be suspicious. These are the things this review, and this
slice, cannot establish.

1. **The local simulation is not the platform path.** `LocalSimulationCoordinator`
   is a deterministic scanner over the policy's surface forms. `02-architecture.md`
   section 3.3's normative path requires the coordinator to execute the tool
   through the platform with the failure event originating there. Nothing in this
   slice exercises that, and the `simulated` flag on every result says so.
2. **Gate A has still not run.** No credentials exist, and no live coordinator
   call was made. The access spike is overdue and its outcome is still
   `[unknown]`. Every "coordinator" statement in this review is about the
   simulation.
3. **K1 is not closed by this slice.** The comparator's behaviour against the
   paraphrase, alias, relative-time and code-switched corpus was proven in the
   Slice 0 spike under Reading A. This slice shows the *wiring* honours Reading A
   (the coordinator returns spans; `domain` resolves and compares), which is what
   makes the spike's result transfer. It does not re-run the corpus through the
   service layer.
4. **No clinical safety is established.** No reviewer exists. The bound complaint
   is deliberately non-clinical, the disposition is the fixture's preauthored
   non-clinical plan, the change vocabulary is empty, and no clinical threshold is
   authored anywhere. Nothing here is evidence that the product is safe, correct
   or appropriate for a real patient.
5. **No patient benefit or human learning is established.** There is no
   participant, no study, no baseline instrument and no measured outcome. The
   baseline card is Slice 8's.
6. **The usage-proof obligation is not discharged.** The capture was meant to
   start at this slice: genuine development history plus at least three redacted
   screenshots into a named location. Nothing in the working tree shows where that
   capture lives, and `.gitignore` excludes `.codebuddy/` and `.workbuddy-ai/`, so
   it cannot be reconstructed later. This is the one artefact whose absence blocks
   scoring entirely, and this review can neither confirm nor deny that it was
   captured. **Ask the named person.**
7. **The persistence and restart claim is not tested.** The demo runs against
   `:memory:` by default (`api.py:91`), so the record does not survive a restart at
   this slice. That is stated, not claimed otherwise, and it is Slice 7's hard
   requirement.
8. **Nothing here proves the second layer would hold under a service-layer defect
   that also bypasses the store API.** The two-layer evidence is that both layers
   refuse the same inputs when the other is removed. A caller that writes raw SQL
   is out of scope of both; the append-only triggers from Slice 3 are what bound
   that case, and they are not re-tested here.
9. **H1's outcome mapping is unproven** (B2), so the ladder's middle rung is
   asserted rather than evidenced.
10. **The uncertain-round outcome mapping is unproven** (B1), so a mutant that
    writes a false recall pass into the clinical record survives the suite.

---

## 9. REPRODUCTION NOTES

- Baseline and per-file counts:
  `pytest tests -o addopts="" -q`, then each file in turn.
- Mutation harness: a script outside the repo that backs up to `%TEMP%`, asserts
  the anchor count is 1, applies one byte-level replacement, runs whole test files
  with `-rA --tb=line`, restores, and re-checks md5. No `-k` selection was used, so
  an empty selection could not be mistaken for a pass.
- Edge probes: scripts outside the repo, loading the app through
  `TestClient(app, raise_server_exceptions=False)` with `get_service` overridden to
  a service on a fresh `:memory:` store per case, and with
  `raise_server_exceptions=False` so the 500s in NF2 are visible as status codes
  rather than tracebacks.
- No production file was left modified. All four probe scripts and every backup
  live in `%TEMP%`, outside the repository.

## 10. THE CORRECTIONS, AND WHERE THEY LANDED

`00-status.md` was not edited at the moment the review was written, because the
brief asked for the review and not a remediation. The author's instruction to
continue was given the same day, so the record was corrected and the two test gaps
were closed. The baseline above (`380 passed`) remains accurate as a statement
about the state at review time; the record now carries `383` as the
post-remediation figure, with the per-file split summing to it.

| What the review required | Where it landed |
|---|---|
| The "H0 to H3 recorded" proof column overstated the test it cited | `00-status.md`, that row of the exit-contract table, corrected; and `test_the_record_carries_the_hint_level_and_the_round` parametrised over all four rungs so the claim is now proven rather than narrowed |
| The uncertain-round outcome case was unproven (B1) | `tests/test_service.py::test_an_unresolvable_span_is_uncertain_and_never_a_mismatch`, one assertion added. Re-applying the mutant now turns exactly that test red |
| The intake paragraph described a general fail-closed rule (B3) | `00-status.md`, the intake paragraph, corrected with the measurements quoted. **The rule was not changed:** widening it is a reviewer-gated decision |
| NF1 and the `COORDINATOR_FALLBACK_TEXT` Gate 1 touch needed tracking, not prose | `tasks/todo.md`, a new "Open from the Slice 4 review" table, every item anchored to the slice where it becomes live |
| This review adds an untracked file, so any fixed `git status` count is falsified by writing it | The record makes no such count for Slice 4. The check was re-run after the last write, not before |

**One arithmetic error in this review was found and corrected while writing the
record.** The header and section 4 originally said fourteen mutations while the
table listed sixteen plus M17. The correct figure is **seventeen applied, fifteen
detected, two undetected**, and the two undetected ones are B1 and B2. It is
recorded here rather than quietly fixed, because the project's rule is that a
review's own arithmetic is checkable and a count that does not match its own table
is exactly the defect this review exists to catch.
