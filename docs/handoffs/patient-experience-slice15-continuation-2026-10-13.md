# CareRelay Slice 15: interrupted implementation handoff

Snapshot: 13 October 2026, Singapore time. This is the user's requested actionable
continuation handoff. It overrides the transfer-context skill's passive wait ending.
The user requested closure around 350k active context, before 400k; this session
closed the current frontend wiring item rather than claiming the whole slice.

## Verified starting and stopping state

[verified] Slice 14 was already complete when the pasted older handoff arrived.
A separate chat, “Prepare Slice 14–15 handoff”, was shipping the same checkout
under the direct user request “Push to main and then give a copy paste prompt for
slice 15”. This chat waited until that chat was idle, then independently verified
local main/live remote main at `b91a4ad248fbd22e407b9536f1825d62b52ae8c2`.
`slice-15-durable-start` was created from that main before edits. All 208
snapshotted files/index survived byte-exact. No Git shipping occurred in this chat.
The new Slice 15 work is DIRTY and INCOMPLETE on that existing branch.

[verified] The unrelated untracked
`submission/usage-proof/Workbuddy_evidence.mp4` is byte-preserved. Gate 1/2/3/4
contracts, exact copy inventory and frontend manifests/config were hash-compared
against preflight and are unchanged. No gate was reopened. No installation,
real credential/configuration, ADP, Postgres engine or deployment operation occurred.

## Finished work items, limited proof

[verified] Fresh baseline: **1,033 passed, 46 Postgres skips, one warning**.
Current **23 Slice 15 receipt tests passed**, 42 other cases deselected, one warning.
They cover canonical word/reference sensitivity, ten MAC dimensions, create/replay,
real child SIGKILL before terminal completion, and ten SQL terminal/claim bindings.
These are passing focused tests, not independent mutation proof for every guard.

[verified] Frontend typecheck passed. Production build passed from a source copy
at `work/frontend-preview/`, using a symlink to the existing installed modules.
No .env was copied, no install ran and no version/lockfile/config changed.
The copy was hash-compared with all 16 current workspace frontend source files.
This isolated build avoided overwriting the old Slice 14 preview's .next directory.

[verified] Actual production-code browser at `http://127.0.0.1:8156/`:
initial inherited-cookie recovery; intentional `/example` bootstrap; explicit
create; separate explicit fixed-choice intake; stored plan; same-episode reload.
Main receives focus after both actions. The controlled first sequence had zero
bootstrap episodes/POSTs, then exactly create and intake, then a GET-only reload.
Its episode is `125dafb2-60d8-4b38-8cbc-45e91ee499dc`: one episode/disposition,
four command rows, zero attempts/restatements/consents, patient owner, care false,
and original deadline `2026-09-30T10:00:00+00:00`. Authenticated real curl of
patient/options/ledger returned 200. Later additional preview requests appeared;
their source is unknown and they are excluded from this controlled proof.
No full mobile, keyboard, zoom, twelve-state or malformed-browser matrix is claimed.

[verified] **Current full diagnostic suite is RED:** 42 failed, 850 passed,
46 skipped, one warning, 167 errors. This is not a completed Check. Many errors
come from old fixtures calling unsigned create/free-text intake, now deliberately
rejected. The complete failure set has NOT been triaged; do not assume every
failure is merely an expected contract change. No current mutation harness ran.

## What the local implementation contains

[verified by source] `journey_commands.py` adds exact UTF-8 canonical digest,
purpose-separated HMAC, complete token shape checks and deterministic preparation
identity. Stable preparation avoids rotating operation IDs at unchanged revision.
Models add command/receipt/plan/outcome/question/offer types. Both DDL modules add
journey_commands, indexes, phase/digest/scored checks, terminal-claim equality and
append-only inclusion. NULL result_kind is explicitly excluded from scored=1.

[verified by source, broad behavior unproved] The common JourneyTransaction SQL
facade is in state.py; both stores supply a transaction-bound executor. SQLite
uses BEGIN/BEGIN IMMEDIATE. Postgres adds episode-row locking to 15 existing write
contexts and reuses active cursors rather than rolling back a nested read.
Postgres has no actual-engine proof. Immutable known-version fixture lookup pins
policy/text A; unknown bundles refuse. Service projection, options and ledger
use coherent contexts. Create and intake have separate receipts; replay finds the
receipt before stale refusal and projects fresh. Bare-root behavior remains.

[verified by source, broad behavior unproved] Pure derive_journey contains the
full intended screen/contradiction selection with independent closure/stop/expiry;
only select_example is offered, and only after a completed create receipt.
No-plan remains without guidance/owner/deadline. Actual assessed API read now
works. Most matrix predicates, redaction and legacy ordering are not tested yet.

[verified by source] Backend create/intake now require an operation token; intake
is only scripted-appointment. Read-only preparation extends GET. The new app
dependency closes legacy transcript/hint/restatement/repair/barrier/action/consent
writes until their journey commands land. Callback/acceptance/escalation/reassessment
operator paths remain. This retirement is a major source of old test failures:
reconcile meaningful setup/assertions rather than re-enable the bypasses or weaken
truthfulness proof. Review whether any allowed operator or durable-stop availability
was accidentally blocked; this point has not been resolved by the partial check.

[verified by source] Frontend actions validate Origin/host, signed locator and
cookie-bound command before backend calls. Bootstrap stays read-only. Page offers
same-candidate explicit create only after authoritative 404, then a separate
select-example action. Full decoder, thin renderer, equal/lower revision handling
and ledger read without creation are wired. frontend/app/actions.ts was already
tracked before this session: it is a replacement of the legacy action surface,
not an additional file. Backend text supplies loaded labels. Plan rows appear on
the plan screen; outcome lines preserve their order. Intentional new navigation
uses approved “Try an example”; Try again reads. No future progression control is
exposed, and no scoring/confirmation/ADP/action execution was implemented here.

## Traps and review priorities

- [verified] The full suite's secret scanner flags actions.ts's non-literal
  `const token = form.get("operation_token")` as token=<28 chars>. No credential
  literal is present there. Resolve the lexical false positive with meaningful
  positive controls; do not rename the variable just to evade the detector.
- [verified] Old no-token/free-text API setup no longer creates records. Old
  assessed-503 expectations are now stale. Many old truthfulness/fault/ledger
  assertions need restoration to actual assessed HTTP alongside their existing
  service/MCP proof. New append-only table lacks the old test_state seed helper.
- [verified] _mutate_patient_experience.py still contains Slice 14 anchors;
  current guard changes need repointing/extension and independent failures.
  _mutate_truthfulness.py may have failing controls because its API setup is old.
  Neither is passing current evidence. Back up untracked targets before running.
- [hypothesis] Inspect expiry persistence if projection rejects missing date/copy
  or policy inside the write transaction: a thrown projection may roll back the
  just-appended expiry. Probe 30 September deadline, read on 1 October, then clock
  regression; this possible bug has not been executed or fixed here.
- [hypothesis] Inspect full comparison partition/legacy provenance validation,
  H3/stop contradictions, unaided outcome-field leakage, pending metadata and
  all decoder invariants. The current matrix is substantial but not certified.
- [hypothesis] Postgres connection mutex initialization, nested cursor lifetimes,
  every writer's post-lock read order, equal-time legacy restatement ordering and
  create collision rollback/replay require source/parity review and later real
  engine proof. Do not call implemented methods engine validation.
- [verified] A placeholder helper import, a reversed-order patch, an unwrapped
  SQLite read error, a revision fixture that changed nothing, and an entry-copy
  union type error occurred and were corrected/logged. The final full diagnostic
  remains red. A later global smoke-count assertion failed because additional
  preview interactions occurred; proof was narrowed to the controlled episode/
  first sequence instead of attributing all preview activity to the agent.

## Evidence and active preview

[verified] All logs/snapshots are under:
`/tmp/carerelay-slice15-20261013-01a13510/`

- `preflight/manifest.json`, `preflight/files/`, refs/index: inherited byte backup.
- `baseline.log`, `focused-wiring-close.log`, `full-diagnostic-close.log`.
- `typecheck-final-wiring.log`, `build-wiring.log`, `frontend-preview-hashes.json`.
- `live/bootstrap-control.json`, `live/requests.jsonl`, `live/smoke-summary.json`.
- `live/partial-plan.png`, `live/backend.log`, `live/frontend.log`, `live/preview.sqlite`.
- `changed-ranges.md`: exact current added-diff ranges.

[verified] Own live servers remain for handoff: backend PID 29817 on 8155;
Next.js PID 29842 on 8156. These are disposable fictional data and synthetic local
auth only. The frontend serves the copied build, so workspace edits do not update
it until copied/rebuilt/restarted. Backend currently has imported modules cached.
No real .env or credential is needed. Existing installed Python/Next.js suffice.
This /tmp evidence may be transient; preserve it outside the repo before destructive
cleanup. Old Slice 14 preview/evidence belongs to the previous chat and is history.

## Actionable prompt for the next agent

```text
Continue the INCOMPLETE local CareRelay Slice 15 build in
/Users/jayd0/Desktop/carerelay on EXISTING branch slice-15-durable-start.
Read AGENTS.md and its required order, then this handoff:
docs/handoffs/patient-experience-slice15-continuation-2026-10-13.md
00-status.md owns the slice state. Use Gate 4 section 9's Slice 15 contract and
Gate 3 section 9, including the approved identity correction. Do not redo gates.

The branch already comes from shipped main b91a4ad. Preserve the dirty work and
unrelated untracked Workbuddy_evidence.mp4; do not recreate/reset the branch.
This is continuation authority for Slice 15 only. No install, real credentials/
config, live ADP, Postgres access, deployment, commit/merge/push or Slice 16.

Reverify Git/files/tooling and inspect the current red diagnostic log. Finish
coherent stored-journey/receipt guards and reconcile retired API test contracts
without restoring bypasses, deleting tests or masking targeted safety failures.
Treat the handoff's hypotheses as review leads, not established facts. Preserve
23 passing new receipt controls and existing truthfulness guards. Complete the
full allocated matrix, migration/crash/replay/token/snapshot/decoder tests and
independent mutation proofs with byte-exact restores. Current harnesses have
unreconciled anchors/controls; previous Slice 14 mutation totals are not new proof.

Use the existing external interpreter and explicit offline environment from
PROGRESS.md; port 1 must be closed and no ambient real DSN may be inherited.
Refresh backend/full suite and typecheck/build after source changes. Actual
Postgres remains separately authorised Slice 19. The preview is a copied build:
refresh it from current source before using it as runtime evidence.

Complete actual production-browser/curl lost-response, two-tab, distinct-example,
restart, all outcome/contradiction/malformed, keyboard/320px and scanner-positive
controls required for Slice 15. No clinical benefit or engine/ADP proof follows.
Update authority/mirrors only from actual evidence, invoke architecture cleanup,
show the completed Check, then stop: Continue to slice 16, or re-steer?
If a contract itself is falsified, use its owning-gate stop protocol; fix ordinary
implementation bugs within this approved scope. Do not mark Slice 15 complete
until its entire required Check passes.
```

## Optional read-only handoff review

Review this partial Slice 15 work and handoff against the controlling gate docs.
Be unbiased and thorough; assume the work may be flawed. It claims only bounded
wiring/focused checks, and explicitly reports a red full suite and no mutation/
complete matrix proof. Inspect the diff, logs, preserved authority and all weak
or unproved guards. Flag shortcuts, accidental operator restrictions, false
positives, expiry/ordering/redaction risks and missing proof with exact file/line
evidence. Do not pass tests for the sake of passing or use approval as an oracle.
This review alone authorises no mutation, implementation or external operation.
Deliver PASS / ISSUES FOUND / FAIL and wait for instructions.

## Current changed-line inventory

- `AGENTS.md:3-13`
- `PROGRESS.md:1-65`
- `docs/DESIGN_PRINCIPLES.md:3-13`
- `docs/PLAN.md:3-13`
- `docs/plans/urgent-advice-accessibility/00-status.md:6-25`
- `docs/plans/urgent-advice-accessibility/adp-and-deployment-impact.md:3-13`
- `docs/plans/urgent-advice-accessibility/patient-experience-upgrade.md:3-13`
- `frontend/app/actions.ts:2-23`
- `frontend/app/globals.css:170-180`
- `frontend/app/ledger/page.tsx:1-38`
- `frontend/app/page.tsx:3-17`
- `frontend/components/PatientJourney.tsx:2-74`
- `frontend/lib/api.ts:2-107`
- `frontend/lib/episode-locator.ts:2-102`
- `frontend/lib/journey.ts:1-202`
- `src/carerelay/api.py:41-708`
- `src/carerelay/demo/fixture.py:38-292`
- `src/carerelay/domain/models.py:534-632`
- `src/carerelay/domain/rules.py:64-1036`
- `src/carerelay/postgres_schema.py:77-307`
- `src/carerelay/postgres_store.py:65-1871`
- `src/carerelay/presentation.py:225-246`
- `src/carerelay/service.py:54-1206`
- `src/carerelay/state.py:71-2277`
- `tasks/lessons.md:77-84`
- `tasks/todo.md:3-13`
- `tests/test_journey_commands.py:20-155`
- `tests/test_postgres_stage2.py:252-254`
- `src/carerelay/journey_commands.py`: new, untracked codec file.
