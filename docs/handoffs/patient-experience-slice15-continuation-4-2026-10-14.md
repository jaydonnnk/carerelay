# Slice 15: fourth continuation handoff, 14 October 2026

[verified] The user requested a copy-paste handoff prompt near the end of this
session's context. Slice 15's verification battery is COMPLETE locally on dirty
`slice-15-durable-start`. Its authority records are NOT yet written and no commit,
merge or push occurred. `00-status.md` still says Slice 15 is in progress and owns
slice state until the next agent writes the completion section. The three prior
handoffs remain historical evidence.

## What this session completed

All five work items in the assignment were attempted. Four are complete; the fifth
(architecture cleanup) is complete in substance but its record-writing is not.

### Item 1: guard-to-evidence classification and truthfulness replay

- [verified] Full named mutation run: **443 RED, 0 SURVIVED, 0 NOT PROVEN**,
  `all_targets_restored_exact: true`, `exit=0`. This is one clean full run, not a
  combination of two runs. Log: `mutations-full-final.log`.
- [verified] Existing truthfulness harness replayed: **39/39 RED, 0 SURVIVED,
  0 NOT PROVEN**, `exit=0`. Log: `mutations-truthfulness.log`.
- [verified] 45 new named mutations were added to
  `tests/_mutate_patient_experience.py` in `add_classification_mutations`, across
  recorded input, recorded identity, projection/screen copy, canonicalization,
  codec/capability, receipt records and the closure decoder.
- [verified] The harness recognizer was strengthened, not weakened: a mutant that
  makes the product answer with its own typed refusal (`CommandInvalid`,
  `CommandConflict`, `JourneyUnavailable`, `MissingDisplayText`, `DomainError`,
  `StateError`, `EpisodeNotFound`, `InvalidJourneyRecord`, `LockContention`) now
  counts as RED. Interpreter-level breakage stays excluded, so a malformed mutant
  still cannot earn credit.
- [verified] Deliverable: `docs/reviews/slice15-guard-evidence-classification.md`
  (new, untracked). It names the standard applied, the three probe causes, the two
  matcher artifacts, the 45 newly proven independent guards, and a table
  classifying every guard denied independent credit by class: IMPLIED,
  DUPLICATE-LAYER, DUPLICATE-DOWNSTREAM, DUPLICATE-ENGINE, CRASH-CONVERSION,
  STRUCTURAL, UNREACHABLE-FIXTURE, IMPLIED-BOUND, UNPROVEN-NO-CONTROL,
  ENGINE-SLICE-19. Masked guards were classified with empirical evidence rather
  than forced to RED or deleted.
- [verified] Honest limit recorded in that document: guards expressed without an
  `if` are not in the inventory, so the inventory is structural, not exhaustive.

### Item 2: positive scanner controls on five surfaces

- [verified] **50 real serialized surfaces** captured from the production build:
  10 screens (start, plan, stopped, expired, accepted, handoff, documented,
  pending, unavailable, readback) times 5 surfaces (api_json, ssr_html,
  rsc_payload, visible_text, accessibility_text).
- [verified] **1,100 of 1,100 injection controls detected**, `absence_failures: []`,
  `misses: []`. Report: `live/scanner-report.json`; captures under
  `live/scanner/<case>/<surface>.txt`.
- [verified] 25 approved-closure-copy assertions are literal and positive. Five
  scanner needles are also the Gate 1 approved four-line closure copy
  (`01-product.md` lines 177 to 188), so the absence assertion is scoped to
  surfaces where no disposition and outcome are recorded, and the documented,
  accepted and handoff screens carry positive literal-copy assertions instead.
  The scanner was not weakened to accommodate this.
- [verified] The accessibility surface extractor was widened to aria-*, role, alt,
  title, for, `h1` to `h6`, button, anchor, legend, caption, summary, label,
  `.sr-only` spans and meta content, so an accessibility-only leak cannot hide.
- [verified] Cross-surface agreement: **28 trusted stored fixtures over 12
  distinct steps, `failures: []`**. Every API heading and every patient line
  appears literally in the production server render; all labelled simulated and
  fixture; deadlines observed are `2026-09-30T10:00:00+00:00` and `None`, where
  `None` is a screen that carries no deadline. Log: `cross-surface.log`,
  `live/cross-surface-28.json`.

### Item 3: bootstrap, key, locator, keyboard and reflow checks

- [verified] Over real HTTP against a production build: bootstrap creates no
  record (303, `Path=/; HttpOnly; SameSite=lax`, no `Secure` because loopback plus
  `CARERELAY_LOOPBACK_TEST=1` is the documented exception; zero rows in episodes,
  dispositions, journey_commands, attempts, restatements, consents; API 404 for
  the bootstrapped id).
- [verified] Durable-start contract: lost create response gives +1 episode, +2
  receipt rows, 0 dispositions, and reload recovers the same episode rather than
  creating a second. Lost intake response gives 0 episodes, +1 disposition, +2
  receipt rows, exactly one disposition version and no v2, and reload renders the
  plan.
- [verified] Persistence: SIGTERM plus a fresh API process returned the identical
  body, revision, deadline and four lines. Two reads of the same candidate were
  byte-identical at revision 115.
- [verified] Refusals: missing locator gives the 200 entry screen and creates
  nothing; a locator signed with a foreign key gives the recovery screen and is not
  adopted; a validly signed locator for a never-bootstrapped episode gives the
  recovery screen, API 404 and zero rows; `encodeLocator` with an empty key throws
  `locator unavailable` and `decodeLocator` returns null.
- [verified] All seven retired patient writes POST to **422 `journey command
  unavailable`** with zero rows created, and unauthenticated POST is 401. The
  nested `/restatements/{id}/repairs` path was used because the flat `/repairs`
  path does not exist (`api.py:778`). An earlier GET-based probe returned 405/404
  and was meaningless; it was redone with POST. Result:
  `live/retired-write-results.json`.
- [verified] Keyboard structure: 3 controls, all native anchor or button, all
  tabbable, zero non-native click handlers, skip link to `#main` present, `main`
  focusable. Text-size control: `aria-pressed` flipped false to true on a real
  click event.
- [blocked] Live keystroke navigation, pointer click, screenshots, 320px reflow and
  enlarged-text measurement are **not** proven. The in-app browser reports
  `viewport=0x0, visible=false, visibilityState=hidden`; `click` and
  `take_screenshot` return `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`, and `press_key`
  reports success while `document.activeElement` stays `BODY`, so keystrokes never
  reach the page. Measuring CSS values alone is explicitly not accepted as
  evidence. Full assistive-technology, zoom and reflow proof is allocated to
  Slice 20 by the approved plan. Two simultaneous tabs are also unavailable (one
  page context), approximated by two sequential reads of the same candidate.

### Item 4: copied previews refreshed

- [verified] Both copied runtimes were rebuilt from current source and verified
  `diff`-clean against the repository before use: `runtime-src` (uvicorn on
  127.0.0.1:8275) and `frontend-preview` (`next start` 15.5.27 on 127.0.0.1:8276).
  A fault-injecting proxy on 127.0.0.1:8277 forwards the browser `Host` verbatim.
  Hashes: `frontend-source-hashes-now.txt`.

### Item 5: architecture cleanup

- [verified] `architect-reviewer` was run in post-slice cleanup mode. Verdict:
  **clean, no deletions recommended**. No orphan `src/carerelay` module; no scratch
  `.log` or `.sqlite` artifact in the tree; no `pytest.mark.skip` or `xfail`; no
  TODO, FIXME or HACK in `src` or `frontend`. `_legacy_service_probes.py` has four
  test consumers, `_journey_fixtures.py` has five. `fixtures/scripted_episode.json`
  has no runtime loader but is cited at `src/carerelay/demo/fixture.py:62` and
  cross-engine compared by `tests/test_postgres_stage2.py:600`: KEEP.
  `frontend/components/HintCard.tsx`: KEEP. No physical repository file was deleted.
- [verified] Stale claims corrected: the now-false comment above
  `NO_PLAN_DETECTORS` in `tests/test_boundaries.py`; two present-tense claims in
  `AGENTS.md` (the "no application code and no automated test suite" baseline
  sentence, and section 8's "Gate A is unrun"); and the `00-status.md` file-map row
  that still said Slices 14 to 21 had not started.
- [verified] 46 skips enumerated with `-rs`: every one carries an explicit
  Postgres-unavailable reason from `tests/test_postgres_store.py` and
  `tests/test_truthfulness_postgres.py`, including the deliberate "this test is
  deliberately not silently green" messages. They are Slice 19 engine skips, not
  silent gaps.

### Suite, build and writing checks

- [verified] Baseline reproduced exactly before any edit: **1,509 passed, 46
  skipped, 1 warning** in 29.21s. Log: `baseline-full.log`.
- [verified] Final full suite after 38 new controls: **1,547 passed, 46 skipped,
  1 warning** in 26.07s, exit 0. Logs: `suite-final.log`, `suite-check.log`.
- [verified] Frontend typecheck exit 0 and production build exit 0.
  Logs: `typecheck-final.log`, `build-final.log`.
- [verified] Writing checks: **0 em dashes** across 3,825 added tracked diff lines
  and across all 12 untracked files. `git diff --check` clean. Every touched file
  is LF, matching this repository (AGENTS.md says preserve current file endings,
  not stale skill defaults).
- [verified] Preservation: `submission/usage-proof/Workbuddy_evidence.mp4` is
  byte-identical at `cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`,
  49,394,082 bytes, still untracked and still excluded. Approved gate documents,
  copy, manifests and config were not modified beyond the three stale-claim
  corrections named above.

## Decisions and traps from this session

- [verified] **`node` must be on PATH or the recorded baseline is unreproducible.**
  The first baseline attempt produced 268 errors, all
  `FileNotFoundError: [Errno 2] No such file or directory: 'node'`. Node lives at
  `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`. This was a
  toolchain gap, not a source regression. Verify the toolchain before believing a
  regression.
- [verified] **A green control batch does not mean the selector touches the
  guard.** `G37 unknown episode has no snapshot` SURVIVED the complete 443-case run
  while looking RED in smaller probes. A manual mutate/probe/restore showed the
  guard is genuinely load-bearing: `store.load_snapshot('never-created')` returns
  an empty snapshot with it removed, and nine legacy patient and ledger reads call
  `load_snapshot` with no bundle read behind it. The existing test only exercised
  the journey path, where `_load_bundle` refuses first. Fix: add a store-level
  control (`test_unknown_episode_has_no_snapshot_at_the_store`), then re-pin.
- [verified] The inventory matcher under-reported coverage twice: it had no
  line-span matching, and no whitespace normalization, so multi-line clauses never
  substring-matched single-line anchors. After adding `mutation_line_spans()` and
  `norm()`/`substring_anchors()`, TypeScript clause gaps fell from 25 to 0.
  `reconcile_sticky_stop` does cover `journey.ts:200`; the matcher had been wrong.
- [verified] Two of my own new test cases were semantically wrong.
  `event_not_dict` and `event_version` were written as refusal cases, but
  `rules.py:922` and `:933` *ignore* foreign events rather than refusing them. They
  were split into `test_derive_journey_ignores_events_it_does_not_own`, asserting
  the observed bundle equals the good one.
- [verified] A `text_not_a_record` decoder case was added and then REMOVED after it
  was observed SURVIVED, masked by `journey.ts:192` `exactKeys(value.text,
  selectedTextKeys)`. `journey_decoder_cases.json` went 74 to 78 cases and is
  byte-identical on a `json.dumps(cases, indent=2, ensure_ascii=False) + "\n"`
  round-trip.
- [verified] **Next.js "Invalid Server Actions request" was my proxy's fault, not a
  product defect.** The proxy stripped and rewrote `Host`, so `x-forwarded-host`
  (8276) did not equal `origin` (8277). Forwarding `Host` verbatim fixed it. That
  rejection is the platform's own protection working.
- [verified] `urllib` followed the 303 and lost the bootstrap `Set-Cookie`; a
  `follow=False` no-redirect opener was required to observe it.
- [verified] HttpOnly locator cookies cannot be set from JavaScript, so the
  `force_cookie` proxy mode injects a chosen locator as a request Cookie header.
- [verified] Non-unique mutation anchors abort the whole probe with
  `NOT PROVEN anchor ... 2 matches` and `SystemExit(2)`. `if episode is None:`
  matched two sites in `state.py`; a three-line anchor including `).fetchone()`
  was needed.
- [verified] Shell word-splitting breaks `--only` labels containing spaces; build
  the argument list as a bash array. `sleep 180` exceeds the 120s Bash timeout
  (exit 143); use 115s or less.

## What is still open

- [verified] **Authority records are NOT written.** Remaining, in order:
  1. Append two entries to `tasks/lessons.md` in its existing flat
     `- 2026-10-14: ...` bullet format with a bolded root cause and a
     **Prevention:** clause. The two lessons are the `node`-on-PATH baseline trap
     and the green-batch/selector trap, both recorded above.
  2. Write the Slice 15 completion and Check record into
     `docs/plans/urgent-advice-accessibility/00-status.md`: a dated section, the
     slice bullet, and the gate line. The blocked viewport items must be disclosed
     there as bounded observations with their blocker, never as a clean pass.
  3. Update the Result section of `PROGRESS.md`. Remember `PROGRESS.md` is
     operational memory and may never record or imply a gate approval.
  4. Update `tasks/todo.md` with the Slice 15 line and any closed open item.
  5. Add the dated 14 October checkpoint to the top of `AGENTS.md`, above the
     third-continuation checkpoint, in the same labelled style.
  6. Optionally write a Slice 15 completion handoff.
  7. Re-run the writing checks after those edits: added-line em-dash count must be
     0, every touched file must stay LF, and `git diff --check` must be clean.
- [verified] **Three preview processes are STILL RUNNING and must be stopped.**
  PIDs are in `$EV/live/{api,frontend,proxy}.pid`. Observed at this checkpoint:
  API pid 80468 listening on 127.0.0.1:8275; `next start` pid 78933 (listener
  78950) on 127.0.0.1:8276; fault proxy pid 80323 on 127.0.0.1:8277.
- [verified] **Shipping has not started.** The authorised sequence is: coherent
  scoped commits on `slice-15-durable-start` excluding the video, verified
  fast-forward into `main`, push `origin/main`, then confirm the live remote with
  `git ls-remote --heads origin`. This sandbox drops local tracking refs after a
  push, which reads like a failed push and is not one.
- [unknown] Whether the Check counts as passed. Every locally runnable Check item
  passes; the viewport-dependent items are blocked by the tool environment and
  their proof is allocated to Slice 20 by the approved plan. The user's shipping
  authorisation is conditioned on "the full approved Check" passing, so whether a
  disclosed environmental blocker satisfies that condition is the user's call, not
  the agent's. Ask before shipping.
- [verified] One guard has no control and is recorded as UNPROVEN-NO-CONTROL for
  Slice 17: `frontend/lib/api.ts:61` (`response.status === 401 ||
  response.status === 503`) has no current test asserting the `reason` distinction
  between the two branches.
- [verified] Real Postgres engine behaviour remains allocated to separately
  authorised Slice 19.

## Evidence

[verified] Evidence root: `/tmp/carerelay-slice15-finish-20261014/`. Temporary
evidence may be transient; regenerate rather than trusting a missing file.

Top level: `baseline-full.log` (1,509), `suite-final.log` and `suite-check.log`
(1,547), `typecheck-final.log`, `build-final.log`, `mutations-full-final.log`
(443/0/0), `mutations-truthfulness.log` (39/39), `mutations-classification.log`
and `mutations-classification-2.log` (probes), `inventory.py`,
`guard-inventory-{python,typescript,summary}.json`, `mutation-map-current.json`,
`classification-observations.json`, `new-labels.txt`, `scanner.py`, `scanner.log`,
`http-faults.py`, `http-faults.log`, `cross-surface.py`, `cross-surface.log`,
`start-live.sh`, `seed.py`, `front-proxy.py`, `frontend-source-hashes-now.txt`,
`video-hash-before.txt`, `video-bytes-before.txt`, `head-before.txt`,
`index-entries-before.txt`, `git-status-before.txt`, `probe-backup/`.

Under `live/`: `live-check-summary.json` (the single best summary of performed and
blocked items), `scanner-report.json`, `scanner/<case>/<surface>.txt` (50 files),
`cross-surface-28.json`, `retired-write-results.json`,
`restart-and-same-candidate.json`, `drop-before.json`, `drop-before-intake.json`,
`http-fault-results.json`, `front-control.json`, `matrix-index.json`,
`requests.jsonl`, `front-requests.jsonl`, `backend.log`, `backend-restart.log`,
`frontend.log`, `front-proxy.log`, `preview.sqlite` plus `-wal`/`-shm`, and the
three `.pid` files.

Note: `http-faults.log` ends with the superseded GET-based retired-write probe
showing 405 and 404. The corrected POST-based result is
`live/retired-write-results.json`, showing 422 for all seven.

## Session source changes

[verified] Modified: `AGENTS.md`, `docs/plans/urgent-advice-accessibility/00-status.md`,
`tests/_mutate_patient_experience.py`, `tests/test_boundaries.py`,
`tests/test_journey_guard_inventory.py`, `tests/journey_decoder_cases.json`, and
the inherited Slice 15 source and test changes listed in the prior handoff.
New and untracked: `docs/reviews/slice15-guard-evidence-classification.md`.

New controls added this session (38 tests): `test_derive_journey_refuses_each_corrupt_recorded_input`
(14 cases), `test_derive_journey_ignores_events_it_does_not_own` (2),
`test_derive_journey_refuses_an_unusable_display_date` (2),
`test_start_refuses_a_capability_it_did_not_issue`,
`test_preparation_requires_kind_and_digest_together`,
`test_each_screen_carries_its_own_recorded_copy_and_cue` (6, reads with `.get()` so
a dropped key is an assertion failure and not a KeyError),
`test_replay_reports_the_recorded_receipt_or_refuses`,
`test_unknown_episode_has_no_snapshot_at_the_store`, and the
`operation_trailing_segment` locator case.

[verified] `service.replay` is dead code in the current path but is a Gate 3
contract method (`03-program-design.md:662`), so it was retained and given a
direct control rather than deleted.

## Copy-paste assignment for the next agent

```text
Finish CareRelay Slice 15 in /Users/jayd0/Desktop/carerelay by writing its
authority records, then stop the preview processes, then publish to main.
Preserve the dirty slice-15-durable-start branch and its inherited changes.

Read AGENTS.md, PROGRESS.md, authoritative 00-status.md, Gate 3 section 9, Gate 4's
Slice 15 contract, and the latest record:
docs/handoffs/patient-experience-slice15-continuation-4-2026-10-14.md.

Completed and shipped: Slices 1 to 12, and Slice 14's read-only no-plan tracer.
Slice 9's participant run was CUT, so no participant validation may be claimed.
Slice 13 is historical and optional, default do not run; its old ADP intake and
classification scope is unbuilt, is not a prerequisite, and must not be built.

Slice 15's verification battery is COMPLETE locally and is not yet recorded.
Verified numbers, all reproduced this session on current source:
1,547 passed, 46 Postgres skips, one existing warning, exit 0; frontend typecheck
and production build exit 0; one clean full mutation run of 443 RED with 0 SURVIVED
and 0 NOT PROVEN and byte-exact restoration; truthfulness 39/39 RED; 50 real
serialized scanner surfaces (10 screens x 5) with 1,100 of 1,100 injection
controls detected and zero unexpected needles; 28 trusted fixtures cross-surface
clean over 12 distinct steps; the live durable-start contract proved over real
HTTP against a production build, including bootstrap-creates-nothing, lost create
and lost intake recovery, restart persistence, byte-identical same-candidate reads,
key rotation, forged identity, missing key, missing locator, and all seven retired
patient writes refusing 422 with zero rows created. Architecture cleanup ran with
verdict clean and no deletions recommended. Writing checks pass: 0 em dashes, all
files LF, git diff --check clean.
Blocked, not passed: live keystroke navigation, pointer click, screenshots, 320px
reflow and enlarged-text measurement, because the in-app browser reports
viewport 0x0, visible false, visibilityState hidden. That proof is allocated to
Slice 20 by the approved plan. Also blocked: two simultaneous tabs. Real Postgres
engine proof is Slice 19. One guard is UNPROVEN-NO-CONTROL for Slice 17:
frontend/lib/api.ts:61 has no test asserting the 401 versus 503 reason
distinction.
Evidence root: /tmp/carerelay-slice15-finish-20261014/, best single summary at
live/live-check-summary.json. Reuse hash-matched evidence; regenerate what is
missing rather than trusting it.

Do these in order:
1. Append two entries to tasks/lessons.md in its existing flat bullet format: the
   node-on-PATH baseline trap (268 FileNotFoundError node errors are a toolchain
   gap, not a regression) and the green-batch trap (G37 unknown episode survived a
   full 443-case run while the guard was genuinely load-bearing, because the only
   existing test reached it through a path where _load_bundle refuses first).
2. Write the Slice 15 completion and Check record into
   docs/plans/urgent-advice-accessibility/00-status.md: a dated section, the slice
   bullet and the gate line. Disclose the blocked viewport items as bounded
   observations with their blocker. Never record them as a clean pass.
3. Update the Result section of PROGRESS.md (operational memory only; it may never
   record or imply a gate approval) and the Slice 15 line in tasks/todo.md.
4. Add the dated 14 October checkpoint to the top of AGENTS.md in the same
   labelled style as the existing checkpoints.
5. Re-run the writing checks on your own added lines: em-dash count 0, LF endings,
   git diff --check clean.
6. Stop the three preview processes. PIDs are in
   /tmp/carerelay-slice15-finish-20261014/live/{api,frontend,proxy}.pid, observed
   as 80468 on 8275, 78933 on 8276 and 80323 on 8277. Verify the ports are free
   afterwards. Name the port before killing anything.
7. Ask the user whether the disclosed environmental blocker satisfies the "full
   approved Check" condition before shipping. The user pre-authorised coherent
   scoped commits, safe integration into main and pushing origin/main only after
   that Check passes, so this is the user's call.
8. If authorised: commit in coherent batches naming what changed and why (never
   one "implement slice 15" commit), fast-forward into main with
   git merge --ff-only, push origin/main, then verify with
   git ls-remote --heads origin. This sandbox drops local tracking refs after a
   push, which reads like a failed push and is not one. Preserve
   submission/usage-proof/Workbuddy_evidence.mp4 byte-for-byte at
   cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106, untracked
   and excluded from every commit. Stage files by name; never git add -A.
9. End with a concise completion report, publication receipt and the remaining
   entry blockers.

Remaining later work, in order: Slice 16 confirmed offline read-back and field
repair; Slice 17 permission and simulated request and failure; Slice 18 strict ADP
adapter with fake transport; Slice 19 separately authorised disposable Postgres
proof; Slice 20 accessibility; Slice 21 separately authorised live ADP.

Do not start Slice 16 before Slice 15 is complete and published. Preserve the later
continuation boundaries and entry blockers: confirmation-copy approval, disposable
database access, and ADP activation, profile and positive extraction proof.
No installation, real configuration or credential change, external runtime call,
manual deployment or participant work is authorised by this assignment. Do not
expand scope, weaken a test, or infer completion from passing totals.
```

## Prompt for handoff review

```text
Review the CareRelay Slice 15 checkpoint in /Users/jayd0/Desktop/carerelay.
Latest record: docs/handoffs/patient-experience-slice15-continuation-4-2026-10-14.md.
Be unbiased, thorough and honest. Assume the work is flawed. Stress-test the actual
dirty diffs and evidence against Gate 3 section 9 and Gate 4's Slice 15 contract.

Claims to attack: 1,547 passed with 46 engine skips and one warning; typecheck and
production build pass; one clean full run of 443 RED with 0 SURVIVED and 0 NOT
PROVEN and byte-exact restoration; truthfulness 39/39 RED; 50 scanner surfaces with
1,100 of 1,100 injection controls; 28 fixtures cross-surface clean over 12 steps;
the live durable-start contract including bootstrap-creates-nothing, lost-response
recovery, restart persistence, rotation, forged identity, missing key and locator,
and seven retired writes refusing 422.

Specific things to check: whether the new TYPED_REFUSAL recognizer in
tests/_mutate_patient_experience.py lets a malformed mutant earn credit; whether
the scoping of five scanner needles to non-approved surfaces hides a real leak;
whether docs/reviews/slice15-guard-evidence-classification.md classifies a genuinely
independent guard as masked; whether any new test is a tautology or asserts helper
output; whether test isolation holds under a reordered suite; whether the blocked
viewport items are honestly disclosed rather than quietly dropped; and whether the
three stale-claim corrections in AGENTS.md, 00-status.md and test_boundaries.py are
accurate and not overreach.

Green output is not completion proof. Do not pass tests for the sake of passing.
All writers must be idle before any safely backed-up single-guard mutation.
No Git operation, installation, real secret, engine, external runtime or deployment
is part of this review. Report PASS, ISSUES FOUND or FAIL with concrete file, line,
test and evidence paths. Deliver your verdict and wait for instructions.
```
