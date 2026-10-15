# CareRelay: Slice 20 handoff, 15 October 2026

`00-status.md` owns gate and slice state. This supporting handoff follows the
same eleven-part prompt structure as the Slice 19 handoff. The user accepted
Slice 19 and requested main publication followed by this prompt. Publication
is recorded separately; query current live refs before branching.

This shipping session does not start Slice 20 or create its branch. Submitting
the prompt below continues Slice 20 only. Slice 21 requires separate authority.

## Copy-paste prompt for the next agent

You are continuing CareRelay in `/Users/jayd0/Desktop/carerelay` on macOS.
Start with Slice 20 only. Read this complete handoff and its controlling
documents before editing. Reverify Git, evidence, tools and actual browser
capabilities. Use `carerelay-slice-build` and `carerelay-slice-review`; perform
`architect-reviewer` cleanup after the slice. The numbered structure matches
the Slice 19 prompt. No other project's account or database permissions transfer.

### 1. Project in brief

[verified design] CareRelay is a labelled research demonstration for an older
adult and caregiver using fictional advice. Preserve the critical action,
absolute deadline and actual owner across read-back, retry, restart and failed
handoff. Code decides urgency, guidance, comparison, permissions and closure.
A model may extract confirmed words only. Provider reasoning, credentials and
hidden expected answers do not belong in patient responses. Actions and
receiving-service actors remain simulated. An invocation is not a booking,
accepted handoff or evidence of care.

[verified approval] Gate 1's five confirmation/help and pending/retry strings
were narrowly re-approved on 14 October. Gate 2 revision 4 and Gates 3/4 section
9 are re-approved; Gate 3 includes section 9.12's episode identity amendment.
Their receipts remain in `00-status.md`. Design approval is not runtime proof.
Exact copy remains controlling. Specialized non-timing/system-date wording is
blocked; bare `tomorrow` remains uncertain in `fixture-provisional-0`.

### 2. Where work sits

[verified] Slices 14 to 18 are accepted and shipped. Slice 19's bounded local
real-engine Check was accepted on 15 October. Its authorised publication is
recorded in `00-status.md`; verify its completed receipt and live main before
starting Slice 20. Slice 19's branch is `slice-19-postgres-proof`, originally
created from `a392b97abb24fe277e158c1926b1b808320088e4`. That is a historical
base, not the next branch point. Query the final current main tip afresh.

[verified] Slices 20/21 remain unstarted in this handoff session. The remaining
order is production accessibility, then separately authorised live ADP.
Each stops for its own bounded Check acceptance. Commit/merge/push and later
continuation require explicit instructions. Slice 13 is conditional and
unbuilt, not a prerequisite; Slice 9's participant run remains cut.

### 3. Completed Slice 19 and exact evidence

[verified in the Slice 19 proof session] PostgreSQL 17.11 with psycopg 3.3.6
executed the full suite: **2,261 passed, zero skips, one existing Starlette
warning**. All 232 Postgres-gated cases executed. The corresponding offline
run was **2,029 passed, 232 Postgres skips, one warning**. Offline skips and
source parity were not substituted for actual engine execution.

[verified] One complete current engine mutation run has **156 named RED over
141 distinct edits**, zero survivor/unproven, 153 green control cases and exact
restores. The separate current offline run has **824 named RED over 805 edits**,
zero survivor/unproven, 821 controls and exact restores. Truthfulness is
**39/39 RED**, with seven exact target backups. A supplemental request-specific
pending-state mutant has its own meaningful assertion failure and green
before/after controls; it is not added to those totals. Shipping audits the
current fingerprints and results; it does not claim to rerun these corpora.

[verified] Actual independent connection/process barriers proved coherent
read-only snapshots, waited-lock fresh reads, duplicate create/intake and
lost-response replay, supersede and late extraction dimensions, stop/revoke
ordering, first terminal callbacks, action/score crash windows and no automatic
redispatch. Genuine pre-upgrade histories survived additive migration and two
forced reapplications, with old row bytes/deadlines/history exact and legacy
provenance unknown. Actual catalog: 15 tables and 46 enabled user triggers.
Seeded phase, unique claim, immutable completion binding and matching receipt
UPDATE/DELETE/TRUNCATE/upsert refusals have isolated fail-capable controls.

[verified] Authenticated HTTP proved wrong-time scoring, grounded repair,
simulated request/failure, durable stop, lost-response replay and changed-body
conflict. Actual backend SIGKILL and PostgreSQL immediate shutdown/WAL recovery
preserved serialized rows and patient/options/ledger. Known/unknown curl stayed
200/404; exact confirmation replay was 200 and changed body 409. Production
browser refresh returned to the same stopped episode with identical text/rows
and zero POST/extraction/dispatch deltas. The ledger retained failed execution,
open closure, patient owner, no care evidence and original absolute deadline
`2026-09-30T10:00:00+00:00`. It labelled synthetic extraction and unknown model
identity. The observed viewport was 544 by 797; this was not accessibility proof.

[verified] 249 same-captured-string scanner controls over five patient and five
ledger API/SSR/RSC/visible/AX captures plus process logs passed. Actual RSC
content types were checked. Typecheck/build passed on frozen production files.
The sole functional production repair is a shared SQL null-parameter text cast
in `src/carerelay/state.py`; PostgreSQL could not infer the original null type.
`postgres_store.py` edits clarify documentation. Fixture constructor/receipt
shape/policy isolation and old-schema test setup were repaired without relaxing
production guards. Earlier failing/preparatory runs are preserved as history.

Review: `docs/reviews/slice19-local-check-2026-10-15.md`. Evidence locations:

- `/tmp/carerelay-s19-resume-20261015/`: `post-mutation-engine.xml/.log`,
  `current-offline.xml/.log`, `proof-audit.json`, current engine/offline corpus
  folders with controls, backups, results, coverage and per-case JUnit/logs.
  `current-truthfulness.log` identifies the truthfulness backup directory.
- Its `live/` folder: frozen production files, actual HTTP/curl/recovery,
  browser screenshots/observations, scanner controls, supplemental mutation,
  typecheck/build and preview cleanup. `catalog-final.json`,
  `architecture-cleanup.json` and `preservation-final.json` bound other claims.
- `/tmp/carerelay-s19-preflight/`: original 231-file tree/index/video snapshot,
  offline baseline, branch preservation and exact engine authority receipt.
- `/tmp/carerelay-s19-shipping-20261015/`: shipping snapshot of 232 existing
  files/index/video, current proof audit, fresh offline suite and frontend checks.

[verified] The approved dedicated cluster `/tmp/carerelay-s19-postgres-17.11`,
database `carerelay_slice19_disposable`, role `carerelay_s19`, loopback 55419,
was stopped and removed after proof. `cluster-cleanup.json` and compressed
server log remain. No hosted database was accessed. Temporary evidence may
disappear; unavailable evidence must be regenerated under appropriate authority
or marked unavailable. A committed review does not substitute for actual proof.

### 4. User decisions and unresolved findings

[verified] Acceptance/publication request on 15 October:
"I accept. Push to main and then the handoff prompt for slice 20. Please follow
the prompt structure for slice 19 thanks". This accepts Slice 19's disclosed
bounded Check and authorises its scoped commits, safe main integration, main
push and this handoff. This shipping session does not implement Slice 20.
Submitting this prompt provides the separate Slice 20 continuation instruction.

[verified failure] Native Escape closed the plan dialog but focus ended at
BODY rather than the opener in the existing `PatientJourney` component. This
was disclosed at Slice 18 acceptance and preserved through Slice 19, whose
frontend bytes were unchanged. It was not retested in Slice 19. Slice 20 must
reproduce, fix and prove the required focus behavior. Do not relabel it a pass.

[unknown] Actual VoiceOver/Safari announcements, full keyboard matrix,
200%/400% browser zoom and full accessibility remain unproved. Earlier Slice
15 viewport blockers were never retroactively passed. Slice 19's browser refresh
and ledger captures prove their narrow observations only. No clinical safety,
target-user benefit, hosted persistence or live ADP claim follows.

### 5. Slice 20 entry, branch and exact contract

Owner: `04-slices.md` section 9.3, **Slice 20**, and complete section 9.6.
Related approved guards: G03/G06/G07/G08/G09/G23/G38. Proposed branch:
**`slice-20-accessibility-proof`**. The 9 to 16 person-hour estimate is unmeasured,
not a deadline. Confirm Slices 14 to 19 acceptance/publication and exact copy
approval from current records. Snapshot all tree files, logical/raw index and
protected tracked video outside the repo. Reverify main against live origin/main
and establish a fresh safe offline baseline. Create the branch from that
verified current main before its first edit. Preserve unrelated dirty work.

Intended actual manual pair: **VoiceOver with Safari on macOS**. Record observed
OS/browser/reader versions and controls available. If unavailable, leave the
required path blocked until an available named pair is explicitly selected and
exercised. Finish independent checks, disclose the limitation and do not claim
full exit. No installation is inferred.

Exact implementation/test footprint:
`frontend/components/PatientJourney.tsx`, `frontend/components/HintCard.tsx`,
`frontend/app/page.tsx`, `frontend/app/actions.ts`, `frontend/app/globals.css`,
`frontend/lib/journey.ts`; `tests/test_journey.py`,
`tests/test_journey_commands.py`, `tests/test_boundaries.py`,
`tests/_mutate_patient_experience.py`;
`docs/reviews/patient-experience-browser-accessibility.md`.
Make minimal evidence-led fixes inside approved behavior. No speculative backend
or ADP rewrite. No new patient wording without narrow owning Gate 1 approval.

Operate actual production code served locally through the complete matrix:

- Desktop and **320 CSS pixels**, default/enlarged setting. Separately check
  **200% text enlargement, 200% browser zoom and 400% browser zoom**. Record
  effective CSS viewport/zoom; ordinary content must not scroll horizontally or
  clip. Critical action/deadline/status/buttons remain readable and usable.
- Keyboard only: skip to main, explicit start, review, confirm, both repairs,
  barrier radio group, checkbox, decline/revoke/request, Show, Hide/Escape and
  same-episode Try again. Inputs/options have labels; errors are associated.
  Focus is visible and moves meaningfully after errors and step changes.
- Dialog: focus inside, background inert, no escape or trapping; Escape returns
  to the opener or a meaningful successor after a step change. Exercise API
  show/hide failure, rerender, reload and stopped plan. Retain cue history and
  usable focus. Prove the known BODY-focus fix by failing pre-change behavior.
- Actual screen reader: start, read-back question, empty error, pending
  interpretation, unavailable/refused/result, repair, failed request and recovery.
  Record expected and observed announcements. One question, associated error
  and polite status announce once without rerender chatter. No hidden expected
  answer, provider reasoning or raw exception/detail. Preview label disappears
  after save. DOM attributes alone do not prove announcements.
- All twelve screens in the approved copy inventory, plus waiting, declined,
  acknowledged, unknown and documented fixture branches. Preserve exact copy,
  simulation label, independent stop/outcome, original deadline and actual owner.
  H0/H1 and hidden H2 responses leak no server answer; visible Show follows a
  recorded H2. Icons supplement words. No timed hide/countdown/advance or patient
  dwell, score or streak.
- Compare API, SSR, actual RSC, visible and accessibility representations for
  contradictions and leaks, including G03/G06 to G09/G23/G38. Record RSC content
  types. Every absence assertion needs a positive injection control against the
  same captured serialized string, including escaped forms. Preserve truthful
  failed/unresolved behavior and the original action/deadline/owner after reload.

Evidence must name case, fixture/episode, versions, viewport, text/zoom settings,
steps, expected/observed focus and announcements, failures, fixes and limits.
A proxy mockup, standalone HTML PASS file or DOM-only report cannot replace
operating the actual production journey with the actual named reader/browser.

### 6. Later work after the Slice 20 boundary

[verified design] Slice 20 ends at its own visible Check and acceptance request.
This prompt does not authorise committing, merging or pushing Slice 20, nor
starting Slice 21. Later authorised shipping must complete and verify main
publication before a subsequent slice branches from fresh main. A blocked
required accessibility path prevents full Slice 20 exit regardless of test totals.

### 7. Later Slice 21: separate live authority required

Branch `slice-21-adp-enablement` requires completed Slices 18/19/20, explicit
continuation and separately scoped operator/live-call authority. Gate 2 sections
13.6/13.7, Gate 3 sections 9.2/9.7 and Gate 4's Slice 21 contract control.
Review fictional processing/region/retention before enabling. Provider-sharing
consent is not general vendor-processing permission. Operator configures
credentials locally. Publishing and activating compatible instructions/schema
and inspecting tools/knowledge base/guardrails need that separate scope.

Observe positive grounded paraphrase and the required negative/refusal corpus
in fresh stateless fictional sessions. Pin the actually observed channel,
correlation and terminal profile with redacted captures; configured instruction
version remains an assertion until observed and absent model identity unknown.
Synthetic envelopes and old refusals prove no positive vendor extraction.
Use default-off `ADP_EXTRACTION_ENABLED` and server-held configuration only.
No retries, fallback, leaked reasoning/credentials or action call from extraction.
Missing positive proof, incompatible profile or unverifiable activation keeps
ADP disabled. Do not weaken approved parsing/limits to make a provider pass.

### 8. Authority and out of scope

This prompt continues **Slice 20 only**. Slice 19's publication authority is
exhausted after its verified receipt. No Slice 20 commit/merge/push, Slice 21,
install, real configuration/credential change, live vendor call, hosted database,
manual deployment, participant contact or revival of the cut study is implied.
No main publication follows from Check acceptance alone. A push may trigger
configured automation; it does not prove deployed behavior.

Apply in-scope reversible offline fixes autonomously. Do not ask again for
scope already explicitly granted. If a required action lacks authority, name
the concrete action and exact controlling rule. The removed Slice 19 target is
not a reachable current database. If further real-engine work becomes necessary,
identify and obtain applicable explicit named disposable-target authority before
connection/DDL/writes/cleanup. Never use an inherited DSN or production server.
If an approved invariant or copy is impossible, preserve the counterexample and
reopen its owning gate instead of silently changing the contract to pass.

### 9. Tooling, preservation and traps

[verified in this session] Existing Python:
`/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`.
Node bin: `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`.
Frontend dependencies are installed. Recheck tools without installing. Run tests
from repository cwd with `PYTHONPATH=src`, because subprocess paths are relative.

For a safe offline baseline explicitly set `APP_DATABASE_URL=:memory:`,
`APP_CLOCK=scenario`, `APP_ENV=local`, `CARERELAY_API_TOKEN=''`,
`ADP_EXTRACTION_ENABLED=false`, `PYTHONDONTWRITEBYTECODE=1`,
`CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled` and
`PYTHONPATH=src`. Use the existing Python with
`-m pytest tests/ -o addopts='' -q --basetemp=<fresh external directory>`.
Expected current offline baseline is 2,029 passes/232 engine skips/one warning.
Record discrepancies; do not silently install or access hosted defaults.
Run existing frontend typecheck and production build with the existing Node.
Explicitly configure every local production preview; never inherit a real DSN.

[verified] Protected **tracked** video:
`submission/usage-proof/Workbuddy_evidence.mp4`, 49,394,082 bytes, SHA-256
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
Preserve its tracking/bytes and unrelated files. Snapshot before branching.
Current text uses LF. New writing has no em dashes or co-author trailers.
Standalone visualization files are HTML, never TSX. Existing production TSX
components remain the implementation files named by the approved contract.

[verified] Slice 19's named listeners 8316/8317/8318/8319 and target 55419 were
stopped. Recheck before reuse; stop only processes/tabs created by this session.
Scenario deadlines are fictional absolute values, not shifted to today's date.
Do not reuse old fixture cookies across episodes. The actual ledger page is
cookie-bound `/ledger`, not `/ledger/<id>`. A relative bootstrap redirect keeps
the host-only signed locator cookie; do not mix localhost and 127.0.0.1.

Do not blindly sync `.workbuddy-ai` memory into published logs or overwrite
historical redactions. Label Codex process accounts accurately; they are not new
organiser-usage evidence. Do not claim the in-app browser is Safari/VoiceOver.
The Larger text toggle is not browser zoom. An AX tree is not audible output.

Source mutations run serially with source writers idle, using external exact
backups including new/untracked files. Mutate the actual first refusal with
otherwise-valid input and require a collected assertion failure, green controls
before/after and exact restoration. Import/anchor/setup errors and skips are not
RED. After changed source/control fingerprints, regenerate the affected complete
current named proof plus truthfulness and relevant full suite. Do not aggregate
partial/superseded runs or relabel Slice 19 history as fresh Slice 20 evidence.

### 10. Read first

Read `AGENTS.md`, available software-factory/build/review skills,
`tasks/lessons.md`, `PROGRESS.md`, `docs/CHALLENGE_REQUIREMENTS_JUDGING.md`,
`docs/PLAN.md`, `docs/DESIGN_PRINCIPLES.md` sections 4/8 and every controlling
file under `docs/plans/urgent-advice-accessibility/`, following its file map.
Focus on `00-status.md` current acceptance/publication receipts and checklist,
Gate 2 section 5.2/13, Gate 3 sections 9.5 to 9.10/9.12 and Gate 4 sections
9.2 to 9.8, especially Slice 20 and the complete 9.6 matrix. Read exact approved
copy, twelve mockups and clinical/research blockers. Mockups are copy/design
references, never runtime proof. Read Slice 18/19 reviews for bounded evidence
and the Escape failure. Then inspect actual production components/tests, current
branch/index/log, live `git ls-remote --heads origin` and process state before
creating Slice 20 from verified main.

### 11. Done means and stopping boundary

Slice 20 is complete only when its entire approved production-browser matrix has
current evidence, including actual named assistive technology, all twelve states
and required branches, keyboard/focus/dialog/failure/reload behavior, separate
text enlargement and browser zoom, and cross-response consistency with positive
scanner controls. Prove each repair fails against broken behavior. Record any
unavailable path, flaky check, contradiction or unexpected announcement honestly.
Do not pass tests for the sake of passing or treat a green total as coverage.

Run relevant full suites, current named/truthfulness proof, production
typecheck/build and bounded architecture cleanup. Recheck tree/index/video,
approved gates/copy/config/manifests, LF/no-added-em-dash and `git diff --check`.
Clean up only named local processes/tabs. Update `00-status.md` as sole state
authority, operational `PROGRESS.md`, supporting records and the exact Slice 20
review. Show the actual visible result with bounded keyboard/reader/zoom evidence.

Stop for the user's **Slice 20 Check acceptance**. Do not commit, merge, push or
start Slice 21 automatically. Missing reader/zoom or inaccessible required paths
block full exit; show completed independent work and the precise unresolved gap.
Live ADP remains disabled pending Slice 21's separate operator/live-call authority.

Please proceed with Slice 20 within these boundaries.
