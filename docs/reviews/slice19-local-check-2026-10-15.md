# Slice 19 disposable PostgreSQL Check: 15 October 2026

## Acceptance and publication addendum: 15 October 2026

[verified] The user has accepted the bounded Check and explicitly requested
main publication and the Slice 20 handoff. `00-status.md` records the exact
authority and publication receipt. Fresh shipping checks reproduce 2,029
offline passes/232 engine skips/one warning; production typecheck/build pass.
Accepted engine/named/truthfulness proof matches current source/control bytes.
Five scoped commits reached main; first live origin/main matched `d19859b`.
The full safe offline suite on main reproduces the result above. Shipping does
not rerun or relabel those completed proof runs. The original review below is
retained as a pre-acceptance record; its pending/uncommitted
statements describe review time. Slice 20/21 implementation remains unstarted.

## Original review before acceptance

Supporting note, authoritative for nothing. `00-status.md` owns state.

[verified] The bounded local Slice 19 proof is ready for user Check acceptance.
The full PostgreSQL-enabled regression passes with zero engine skips.
Acceptance, shipping and later continuation remain separate.

## Scope and authority

[verified] The user continued Slice 19 only, including the supplied handoff.
The attached earlier conversation records "Whichever u recommend" against the
exact disposable-target approval question. Its scope is cluster creation/start,
connection, DDL, fictional writes, races, crash/restart and scoped cleanup.
Target: PostgreSQL 17.11 at `/tmp/carerelay-s19-postgres-17.11`, loopback 55419,
`carerelay_slice19_disposable`, role `carerelay_s19`. No install, hosted access,
real credentials, deployment or live ADP. Check acceptance and Git shipping are
separate. Neither is inferred here.

[verified] The existing dirty branch was retained. HEAD/main/live origin/main
were `a392b97abb24fe277e158c1926b1b808320088e4`. Its original preflight includes
231 files, index entries/raw bytes and protected video, a clean main offline
baseline of 2,029 passes/56 engine skips, and creation of the Slice 19 branch
before edits. The resume snapshot independently preserves all 231 current files.

## Findings and bounded repairs

[verified] `src/carerelay/state.py:332`: the shared pending-score query used an
untyped null parameter in `? IS NULL`. Real PostgreSQL refused initial scoring.
The text cast preserves null-parent equality on both engines. The paired engine
mutation restores the original query and requires a valid-receipt assertion to
fail. No domain rule, patient copy or schema changed.

[verified] `tests/test_journey_postgres.py:54`: the original journey helper
constructed Postgres with a SQLite-only argument. It now constructs the proper
store and isolates each test's immutable policy registration using the existing
clean-schema fixture. `tests/test_postgres_store.py:134` supplies valid digest
and scored fields for receipt seeding. Production constructors/constraints stay
strict.

[verified] `tests/test_deployment.py:249`: the older restart writer reused a
global policy ID with different content/provenance. Two tests failed after
other engine runs. It now uses an episode-specific test policy ID; both isolated
restart controls pass. This is test isolation, not relaxed policy immutability.

[verified] The migration fixture now accepts the actual old store directly,
requires the exact fourteen-table pre-upgrade catalog with no command table,
and avoids relying on a warm current-schema cache. The phase-enum probe removes
the independent lifecycle constraint before testing phase membership. The reused
intake replay control uses its matching test signing key. An initial phase
selector and test-key mismatch were setup failures, never credited as RED.

## Real-engine proof map

[verified] All selectors below are in `tests/test_journey_postgres.py`.

- [verified] G11/G12/G14: `test_s19_same_create_and_intake_race_and_lost_response`,
  `test_s19_replayed_binding_first_refusal`, pending duplicate/supersede and
  explicit intake-replay controls. One episode/disposition and one extraction;
  changed bindings refuse; replay projects current stopped state.
- [verified] G15/G16: late terminal supersede, nested outermost claim/final refusal and
  SIGKILL before create/intake/score terminal commit. Score and terminal receipt
  roll back together. A committed extraction claim remains pending.
- [verified] G17/G32/G35: stop, revoke, sticky expiry and fresh deadline before invocation
  give zero calls. The private permit remains process-owned and single-use.
  SIGKILL before action-claim commit permits one explicit retry; after claim,
  during invocation, after simulated effect and before receipt commit retain
  neutral pending/unknown and refuse redispatch across fresh services/MCP.
- [verified] G31: coherent repeatable/read-only snapshots during stop/consent/acceptance;
  actual `pg_blocking_pids` waits for patient and callback writers; fresh reads
  after lock acquisition. Event references preserve latest records under equal
  and regressed timestamps. Current operations serialize one episode and then
  its attempts/commands; nested cross-episode writes refuse.
- [verified] G33: bounded invocation holds the episode lock while stop/revoke waits.
  Dispatch observation precedes that writer. Late success refuses; first
  terminal callback remains winning in both callback orders.
- [verified] G34: paused extraction allows another connection to alter cue, stop, deadline,
  revision, disposition version, confirmation or latest parent. Late results do
  not score or advance a round. Engine transaction status is IDLE and the
  connection mutex is independently obtainable during extraction. Separate
  engine-bundle counterexamples isolate each overlapping final-context guard.
  Those isolated in-memory substitutions are not advertised as extra races.
- [verified] G36: additive upgrade plus two forced reapplications over nine genuine old histories, fresh
  process projection, exact prior row JSON bytes/deadlines/history and unknown
  legacy provenance. Exact table/trigger catalog; matching claimed/completed
  UPDATE, DELETE, TRUNCATE and upsert refusals; phase shape, uniqueness and all
  ten immutable matching-claim fields. Single-guard controls are independent.
- [verified] G37/G38: actual fresh authenticated backend/engine recovery and unchanged
  patient/options/ledger, lost-response replay, browser refresh and existing
  truthfulness regressions over Postgres. HTTP/browser details follow below.

## Current evidence

[verified] Final full suite with PostgreSQL enabled: **2,261 passed,
zero skips, one existing Starlette warning**, exit 0. All 232 Postgres-gated
cases execute. Final offline regression: 2,029 passed,
232 named Postgres skips, one warning. Offline skips are not engine
proof. The JUnit per-file totals sum to 2,261; the evidence JSON
contains the exact split.

[verified] One complete current engine corpus: **156 named RED over
141 distinct edits**, zero survivors/unproven, 153
green control cases and exact restores. One complete current offline corpus:
**824 named RED over 805 edits**, zero survivors/unproven
and exact restores. Existing truthfulness: **39/39 RED**, exact restores.
These are separate runs, not an aggregate. A supplementary request-specific
pending-state mutant also fails its literal action assertion over Postgres,
with green before/after controls and exact frozen-source restoration. It is
reported separately, not added to the named corpus count.

[verified] PostgreSQL 17.11, psycopg 3.3.6, Node v22.22.2,
Next.js 15.5.27, macOS 26.5.1. Actual catalog: 15 tables and
46 enabled user triggers. Lock observations include actual backend
PIDs and `pg_blocking_pids`, recorded in the full engine log. Independent
subprocess SIGKILL cases retain their exit-code assertions. Frontend typecheck
and production build pass against the frozen production files.

[verified] The real HTTP fixture performs lost create/intake response recovery,
confirmed wrong-time scoring, grounded timing repair, a local simulated request,
failure callback, durable stop and refused late success. After backend SIGKILL
and PostgreSQL immediate shutdown, server logs show automatic WAL recovery.
Fresh authenticated patient/options/ledger projections and serialized row values
are exact. Two backend termination boundaries have recorded distinct PIDs.
Known/unknown curl responses remain 200/404 with exact bodies. Exact confirmation
replay returns 200; a changed valid body returns 409 with no new row. Three
committed-operation replays add no work. The main HTTP fixture's counters remain
two fake extraction calls and one local simulated provider invocation.

[verified] Actual browser refresh at the observed 544 by 797 viewport returns
to the same stopped episode with identical visible text and serialized rows.
The proxy and backend each record GET only. Zero POST, extraction and dispatch
deltas. The real ledger shows failed execution, open closure, patient owner,
no care evidence, the original absolute deadline and explicit fake provenance.
No console error is observed in those two views. This is not an accessibility
certificate. All 41 frozen source/frontend files match current unmutated bytes.

[verified] 249 same-surface positive controls over five patient
API/SSR/RSC/visible/AX captures, five ledger captures and process logs pass.
RSC content types are verified. Each bounded prohibited-success/entity/credential
needle and each synthetic reasoning/auth marker is detected in the applicable
captured string, including escaped forms. Clean captures have no detected leak.
The first optional ledger probe used the wrong `/ledger/<id>` route and got 404;
the corrected cookie-bound `/ledger` route is verified in the browser and scans.

[verified] Evidence root: `/tmp/carerelay-s19-resume-20261015/`. Current corpus
folders are `current-engine-mutations/`, `current-offline-mutations/`, and the
truthfulness directory named in `current-truthfulness.log`. Use
`post-mutation-engine.xml`, `current-offline.xml`, `proof-audit.json` and `live/`
for final results. Preparatory runs are superseded, never combined. Temporary
files can disappear; the repository tests remain rerunnable after an
operator authorises a disposable target. This branch itself is uncommitted.


## Adversarial and architecture review

[verified] Verdict: no remaining in-scope blocker identified by the bounded
review. Local Slice 19 proof is ready for user Check acceptance.

[verified] Judgments: the shared SQL type cast is the narrow fix; test constructor,
seed shape and isolated policy identities repair fixtures without relaxing
production refusals. Immutable receipts and unknown action-crash outcomes remain.
The independent final-dimension probes deliberately isolate overlapping domain
conditions over an engine-loaded bundle; the actual writer races are listed
separately. Named selectors and distinct edits are counted separately.

[verified] Attempts to break the contract include removing each listed engine
guard, bypassing snapshot isolation/episode locks, splitting receipt commits,
accepting late output, consuming forged/forked permits, rewriting matching
receipts, changing claim-binding fields and first-terminal order. Their paired
assertions fail and restored controls pass. The additional original-action
claim barrier observes a second connection returning pending with zero calls
before release, then exactly one invocation and one attempt. The full boundary
suite also rejects `import socket` prepended to actual rules source, plus
literal/from/nested import and serialized-needle controls. No evasion passed
that bounded set; no universal static-analysis guarantee is asserted.

[verified] Architecture cleanup checks the 231-file tracked inventory and current
production ASTs. Only the state query changes runtime logic; Postgres-store edits
correct documentation. No new production file, dependency, schema or patient
wording is added. The protected 24 gate/copy/config/manifest files are exact.
No in-scope orphan or cleanup deletion is identified. Gates remain unchanged.

[verified] Tree/video/index checks are recorded in the final preservation audit.
The tracked video retains 49,394,082 bytes and SHA-256
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
Index entries are exact. Git refreshed only stat fields in the raw index; both
raw versions and their structural comparison are saved. No index content was
restored or rewritten by the agent. Preview ports/tabs and the exact disposable
cluster have their own cleanup receipts. No unrelated cleanup is performed.


## Limits and stopping boundary

[unknown] Hosted Supabase/Render persistence, live ADP behavior/model identity,
external exactly-once effects, full accessibility and clinical/user benefit are
not established. Synthetic extraction and local provider effects remain labelled
fictional.

[verified] Frontend bytes are preserved. The prior Escape/BODY-focus failure
remains allocated to Slice 20 and was not re-tested here. No Slice 20/21 work,
install, commit, merge, push or manual deployment occurred.

[verified] Stop for the user's bounded Slice 19 Check acceptance. Acceptance alone
adds no shipping or next-slice authority.
