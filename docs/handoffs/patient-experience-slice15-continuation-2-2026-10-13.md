# Slice 15: second session handoff, 13 October 2026

[verified] The user requested this handoff when reporting about 350k active context.
The current build is dirty on `slice-15-durable-start`; Slice 15 is INCOMPLETE.
The earlier handoff describes inherited work. This document records the continuation
session delta. `00-status.md` remains the slice authority.

## Completed work and current evidence

- [verified] The 42 failures and 167 fixture errors were reproduced. Retired patient
  writes now have explicit service tests plus real HTTP refusal/no-write controls.
  Signed create/intake and assessed patient HTTP are exercised. Helper-authored
  fallback, dwell and consent assertions were replaced with production assertions.
- [verified] Next-day display refusal no longer rolls back expiry. A valid minimal
  snapshot records expiry before corrupt unrelated round metadata is refused.
  Naive timestamps and corrupt stored fields produce typed recovery errors.
- [verified] Both stores write identifying event references; new records use event
  order instead of timestamp/UUID order. SQLite and portable Postgres SELECT
  controls cover equal-time and regressed-clock records. Postgres initializes one
  mutex eagerly and refuses a nested writer for another episode. These checks are
  offline Python/SQL-contract proof, not actual Postgres behavior.
- [verified] Comparison partition/outcome guards reject corrupt understood results.
  Assessed decoder guards reject inconsistent steps, missing labels/questions and
  answer-bearing unknown keys. Lower/equal revision reconciliation preserves stop
  and sticky expiry. Waiting-outcome text retains revealed-plan metadata.
- [verified] Latest full suite: **1,299 passed, 46 Postgres skips, one existing
  Starlette warning**, 19.51 seconds. Frontend typecheck and isolated production
  build pass. Backend/frontend copies were hash-compared to restored source.
- [verified] Receipt tests cover two-connection create/intake races, lost replies,
  pending/current stopped replay, real child SIGKILL before each terminal receipt,
  independent SQL constraints, old row preservation after twice-applied additive
  SQLite DDL, and fresh authenticated interpreter reads of migrated histories.
- [verified] New harness: **207 RED, 2 SURVIVED, 0 NOT PROVEN** over 209 named cases.
  Initial run was 198/10/1; nine corrected isolated controls were 9/9 RED.
  Latest batch has 215 passing control cases. Each RED has before/after controls,
  actual assertion failure and byte-exact restore, independently rechecked here.
  Existing truthfulness harness: **39/39 RED**, with the same restore discipline.
  Named mutant totals do not establish exhaustive guard coverage.

## Bounded live result

[verified] Production Next.js `http://127.0.0.1:8166/` uses a loopback API proxy
at 8167 and API at 8165, synthetic auth and disposable fictional SQLite only.
Bootstrap produced zero records/POSTs. A proxy disconnected after committed
create and intake responses. Two tabs then read the same plan: controlled episode
`099c796b-b157-4a0e-8cd1-2291dcb72b57`, one disposition, four receipt rows,
zero attempts/restatements/consents and original `2026-09-30T10:00:00+00:00` deadline.
Keyboard start/intake move focus to main; skip link works. A distinct intentional
example created another identity. Backend restarted from PID 57599 to 59976;
authenticated actual curl patient/options/ledger stayed 200, unknown 404,
anonymous 401, root 303.

[verified] Saved real browser/API/SSR/RSC/visible/accessibility captures exist for
readback, repair, barrier, permission, failed, stopped, expired, accepted, handoff
and trusted documented fixtures. These were explicit operator-seeded histories,
not public outcome selectors or new patient scoring/action controls. Entry/no-plan,
plan and recovery were also observed. The complete contradiction/substate and
malformed-browser matrix is unfinished. Scanner-positive browser controls remain
unfinished. At measured 320 CSS pixels and 40px text, scroll width stayed 320.
This is not VoiceOver/Safari or browser-zoom proof.

## Decisions and traps

- [verified] Projection failures preserve a valid expiry fact but do not invent
  clinical stop or display new date wording. Invalid timestamp data stays refused.
- [verified] Legacy mutation services remain internal regression/fixture entrypoints;
  no public MCP dispatcher was found. Direct command/dispatch permits belong to
  Slice 17. Public legacy patient writes stay retired.
- [verified] H1 success is `recall_scaffolded`. Documented-care fixtures retain the
  existing actual owner, including patient. Neither may be rejected by an invented
  decoder or test constraint. Expiry retains a real recorded transfer owner.
- [verified] A policy-provenance mismatch initially broke the live fixture seeder.
  The seeder now uses the actual configured local service. No policy record was
  overwritten. Old-store fixture exceptions also have distinct Python class IDs;
  the migration seed creates episode rows explicitly before using service helpers.
- [verified] A viewport request first affected the other tab. The 320px observation
  was repeated on the measured tab. Requested dimensions alone are not proof.
- [verified] A raw Git index-byte comparison failed because Git refreshed stat
  metadata. Index entries are unchanged and nothing is staged. No index restore
  was applied. Protected gate/copy/manifests/config and video bytes are unchanged.
- [verified] Mutation loops temporarily alter shared source. Preview copies are
  isolated. No mutation was killed. The default harness validates only; `--run`
  mutates, and exact `--only` plus fingerprinted `--resume` select existing work.

## Open work status

[verified] Slice 15 Check has not passed. The two surviving labels are
`G06 flow string stop_reason` and `G06 flow string selected_repair_field`.
Other semantic validators catch their malformed inputs. Those overlapping catches
are not independent proof for the surviving validators. The report also leaves
ordering-helper mutations and an exhaustive codec/decoder guard inventory open.

[verified] Browser lost-response/two-tab/basic keyboard/reflow and representative
stored outcomes have bounded evidence. Remaining contradictions, waiting/declined/
acknowledged/unknown/pending substates, malformed assessed inputs, rotation/missing
locator/bootstrap-drop, scanner-positive injections and corresponding restoration
controls are not a completed browser Check. Actual Postgres cases/proof remain
separate; the current new Postgres file is primarily offline query-contract proof.
Architecture cleanup and final Check records are unfinished. No Slice 16 began.

## Evidence and active processes

[verified] Evidence root: `/tmp/carerelay-slice15-resume-20261013/`.
The prior `/tmp/carerelay-slice15-20261013-01a13510/` is inherited historical proof.
Current logs: `handoff-final-suite.log`, `typecheck.log`, `build.log`,
`truthfulness-mutations.log`, `mutation-run-1.log`, `mutation-isolated-followup.log`.
Reports: `mutation-author-report.md`, `mutation-combined-summary.json`,
`final-backend-review.md`, `test-migration-review.md`, `frontend-review/report.md`.
Mutation evidence is copied under `mutation-evidence/` with backups/JUnit/statuses.
`preflight/`, `manifest.json`, `preservation.json` and `session-changed-ranges.md`
capture inherited bytes, the unchanged video/index entries and exact session hunks.

[verified] Live evidence is under `live/`: request logs, drop summary, curl after
restart, matrix captures and `preview.sqlite`. `runtime-src/` and
`frontend-preview/` are hashed source copies. Backend PID 59976, proxy PID 57616,
frontend PID 57635 remain for the handoff. Ports are 8165/8167/8166. Workspace
edits do not refresh them. Unified exec session IDs: 90865/71007/40227.
These temporary files may be transient; no cleanup erased them. Older previews
and other chats' processes were not stopped.

## Session file changes

[verified] These spans contain this session's changes, with unchanged context
between hunks. Exact individual hunks are in `session-changed-ranges.md`.

- `src/carerelay/service.py:828-858`: minimal expiry snapshot and typed projection failure commit.
- `src/carerelay/state.py:152-2208`: event order/references, parent metadata, typed invalid records and naive-date refusal.
- `src/carerelay/postgres_store.py:104-1855`: eager mutex, nested episode scope and recorded-order parity.
- `src/carerelay/domain/rules.py:899-1008`: comparison validity and reveal metadata order.
- `frontend/lib/journey.ts:150-211`: assessed invariants and revision reconciliation.
- `frontend/components/PatientJourney.tsx:5-42`: fresh-read versus command reconciliation.
- `tests/test_api.py:1-1235`, `test_truthfulness.py:9-501`, `test_fault_sequences.py:5-800`, `test_ledger.py:38-287`: service/HTTP contract migration and literal safety assertions.
- `tests/test_boundaries.py:595-660`: expression/literal secret-scanner controls.
- `tests/test_state.py:323-330`: matched new-table seed for append-only attacks.
- `tests/test_journey.py:97-508`: assessed matrix, corrupt/expiry/reference and fresh-process regressions.
- `tests/test_journey_commands.py:134-587`: valid-FK controls, receipts/races/crashes/schema/migration.
- `tests/_mutate_patient_experience.py:1-480`: current scoped/resumable independent mutation runner.
- New `tests/_legacy_service_probes.py:1-139`, `_journey_fixtures.py:1-58`: explicit internal test fixtures, no transport interception.
- New `tests/test_journey_decoder.py:1-191`, `test_journey_postgres.py:1-102`, `test_journey_mutation_controls.py:1-333`: TypeScript, offline query and isolated mutation controls.
- Authority/mirror checkpoint entries and `PROGRESS.md` record this incomplete handoff.

## Prompt for New Chat

```text
Background context for CareRelay in /Users/jayd0/Desktop/carerelay.
The current branch is dirty slice-15-durable-start and must be preserved.
The latest session record is docs/handoffs/patient-experience-slice15-continuation-2-2026-10-13.md.
AGENTS.md, PROGRESS.md and 00-status.md describe the current scope/state.
Slice 15 is INCOMPLETE. Latest full suite: 1,299 passed, 46 Postgres skips, one warning.
Typecheck/build pass. New mutation result: 207 RED, 2 SURVIVED, 0 NOT PROVEN; truthfulness 39/39 RED.
Remaining work includes the two overlapping-validator proofs, guard inventory,
full browser/scanner matrix and architecture cleanup. No full Check is claimed.
Existing authorisation covers local Slice 15 only. No Slice 16, installation,
external services, real configuration/credentials, deployment or Git shipping.
The unrelated Workbuddy_evidence.mp4 is byte-preserved and must remain untouched.
Current evidence/preview is in /tmp/carerelay-slice15-resume-20261013/.
Wait for instructions before taking any action.
```

## Prompt for Handoff Review

```text
Review the incomplete CareRelay Slice 15 continuation in /Users/jayd0/Desktop/carerelay.
The latest handoff is docs/handoffs/patient-experience-slice15-continuation-2-2026-10-13.md.
It claims 1,299 passing tests, 46 Postgres skips, one warning, passing typecheck/build,
207 RED/2 SURVIVED/0 NOT PROVEN named mutants and 39/39 truthfulness RED. It does
not claim Slice 15 completion or a complete browser/scanner/engine Check.
Be unbiased, thorough and honest. Assume the work may be flawed. Stress-test it
against Gate 3 section 9 and Gate 4's Slice 15/G01-G14/G16/G31/G36-G38 requirements.
Inspect actual diffs and evidence, re-run focused offline tests, and probe missed
cases. Safe single-guard mutations require all source writers idle, external
backups, pinned assertions and exact restoration. Do not pass tests for the sake
of passing. Flag helper-authored assertions, weak controls, overlapping catches,
missing guard inventory, unverified claims, scope creep and implementation defects.
Keep the existing dirty branch and unrelated video. No installation, real secrets,
external service/engine/deployment/Git shipping or later-slice work is authorised.
Report PASS / ISSUES FOUND / FAIL with specific file/line/test evidence.
Deliver your verdict and wait for instructions.
```
