# CareRelay: Slices 19 to 21 handoff, 14 October 2026

`00-status.md` owns gate and slice state. This supporting handoff was requested
after the user accepted Slice 18 and authorised its commits, main integration
and origin/main push. Publication is recorded separately in `00-status.md`.

[verified] Seven scoped commits were integrated by safe fast-forward and main
push; the first live remote check matched local main at `6dc765b`. The receipt
is published within the same request. Final refs are verified after publication
and should be queried afresh by the next agent. The local Slice 18 branch is
retained/aligned; only main is pushed. Tree/index/video preservation passes.

This session does not start Slices 19, 20 or 21. Submitting the prompt below
continues Slice 19 only; engine access still requires its explicit named scope.

## Copy-paste prompt for the next agent

You are continuing CareRelay in `/Users/jayd0/Desktop/carerelay` on macOS.
Start with Slice 19 only. Read this complete handoff and its controlling
documents before editing. Re-verify Git, evidence and tooling rather than
trusting old hashes or temporary files. Use `carerelay-slice-build` and
`carerelay-slice-review`; perform `architect-reviewer` cleanup after the slice.
The numbered structure follows the supplied Envoi template. None of Envoi's
database, account, deployment or credential permissions transfer to CareRelay.

### 1. Project in brief

[verified design] CareRelay is a labelled research demonstration for an older
adult and caregiver using fictional advice. Its critical action, absolute
deadline and actual owner must survive read-back, retry, restart and failed
handoff without false completion. Code decides urgency, guidance, comparison,
permissions and closure. A model may extract confirmed words only. The patient
journey and judge ledger serve different purposes; provider reasoning and
credentials belong in neither. Actions and receiving-service actors remain
simulated. An invocation receipt is not a booking, callback, acceptance or care.

[verified approval] Gate 1's five confirmation/help and pending/retry strings
were narrowly re-approved on 14 October. Gate 2 revision 4 and Gates 3/4 section
9 are re-approved; Gate 3 includes section 9.12's episode identity amendment.
Read their recorded receipts. Approval is design authority, not runtime proof.
Keep exact approved copy; specialized non-timing/system-date copy remains
blocked. Bare `tomorrow` is still uncertain in `fixture-provisional-0`.

### 2. Where work sits

[verified] Slices 14 to 17 are accepted and shipped. Slice 18's bounded offline
Check was accepted with the disclosed Escape-focus failure, and the user
authorised scoped main publication. Its source branch is
`slice-18-adp-boundary`, created from verified local/live main
`0fac90dde43882b9322d575fbd80114650e4dc19`. Read the latest Slice 18 publication
receipt and query live origin/main for the final entry tip; the original base
above is historical. Do not branch from it when main has advanced.

[verified] Slices 19, 20 and 21 are unstarted. Their order is disposable Postgres
proof, full production accessibility, then separately authorised live ADP.
Each stops for its own bounded Check acceptance and continuation decision.
Later shipping needs separate explicit authority before the following slice
can branch from the verified updated main. Slice 13 remains conditional and
unbuilt; it is not a prerequisite. Slice 9's participant run remains cut.

### 3. Completed Slice 18 and exact evidence

[verified in the Slice 18 session] The strict adapter implements the exact six
keys of `carerelay-readback-v1`, source-grounded Unicode code-point spans,
strict JSON/UTF-8, lifecycle/channel/correlation/terminal validation and two
pinned **synthetic** profiles: `fake-incremental-v1`, `fake-complete-v1`.
The synthetic envelope is not an observed vendor contract. It enforces one
five-second whole-response budget, 2,048 input code points, 16 KiB answer,
16 KiB frame and 64 KiB wire independently. One transport call, no redirects,
retry or lexical fallback. ADP is disabled by default and no real transport
client or credential loader was enabled. The ordinary lexical simulator is
separately labelled; the positive ADP boundary demos use injected fake code.

[verified] Score claim and final application require the existing outermost
transaction contract in both stores. Claim commits before extraction; no
database transaction/mutex spans the fake transport. Final revision, disposition,
confirmation, latest parent, cue, stop and fresh deadline rechecks fence output.
Independent whole-answer uncertainty and deterministic comparison remain.
Unavailable/refused/invalid/timeout output is unscored and preserves the plan.
Immutable adapter-origin proof prevents relabelled or tampered port metadata;
late superseded output records bounded provenance without rewriting its receipt.
The judge ledger distinguishes fake transport and configured assertions from
unverified live/model identity. No schema table, dependency or patient copy was
added in Slice 18. Original dispatch permits and permission guards remain.

[verified] Fresh shipping suite: **2,029 passed, 56 Postgres skips, one existing
Starlette warning**, exit 0; frontend typecheck/build pass. The new extraction
file has 159 cases; one scanner case adds another pass. Two new real-engine
contracts are skipped, not proved. One current complete mutation run has
**824 named RED over 805 distinct edits**, zero SURVIVED/NOT PROVEN, green
controls before/after and exact restores. The Slice 18 subset is 97 named over
94 edits. All 17 target backups and 40 control-source hashes match current
bytes. Truthfulness is **39/39 RED**, seven exact target restores. Shipping
audited these existing runs; it did not rerun or aggregate historical probes.

[verified] Real authenticated HTTP/curl proved positive, wrong time, missing,
negated, invalid, refused, transport, disabled and slow-terminal paths; lost
response, stale capability and two workers. Enabled extraction made one call,
disabled made zero and booking made zero. Production browser covered stored
views, keyboard confirmation, timing-only repair retaining grounded fields,
retry, reload, two tabs and measured 320px/wide reflow. Text changed 20px to
40px. Forty patient surfaces and five ledger surfaces were captured; 1,569
patient/log positive controls and 30 same-surface ledger injection controls
proved their detectors. These are bounded observations, not full accessibility.

Review: `docs/reviews/slice18-local-check-2026-10-14.md`. Session evidence:

- `/tmp/carerelay-s18-full-named-1/`: current results, coverage, control hashes,
  target backups and per-case before/mutant/after logs and JUnit.
- `/tmp/carerelay-s18-truthfulness.log`: current 39-case proof; its first line
  locates the exact backup directory.
- `/tmp/carerelay-s18-live/`: frozen source, HTTP/curl/scanner/browser captures,
  actual screenshots, process cleanup and architecture audit.
- `/tmp/carerelay-s18-shipping/`: fresh suite/typecheck/build logs, current proof
  audit and external 230-file pre-shipping tree/index/video snapshot.
- `/tmp/carerelay-s18-preflight/`: original implementation snapshot;
  `/tmp/carerelay-s18-final-suite.log`: pre-acceptance final suite.

Temporary artifacts may disappear. Missing evidence must be regenerated or
marked unavailable. The committed review is a record, not a replacement for
actual rerunnable proof. Do not count earlier partial or superseded probes.

### 4. User decisions and unresolved findings

[verified] User acceptance/publication request, 14 October 2026:
"Yep i accept pls commit and merge and push to main the provide me with a copy
paste handoff prompt." The request identifies Slices 19 to 21 and says:
"Should start with slice 19 first". This shipping session creates the handoff,
not the later implementation. This prompt, when submitted, continues Slice 19.

[verified failure] Native Escape closes the plan dialog but focus ends at BODY
instead of the opener in the unchanged `PatientJourney` component. The user
accepted the bounded Check with this disclosed; it is a Slice 20 remediation
obligation, not an accessibility pass. VoiceOver/Safari, 200%/400% browser zoom
and announcement behavior remain unproven. The in-app browser's engine version
was not exposed. Earlier Slice 15 viewport blockers were never retroactively
passed. Rerun the whole approved Slice 20 matrix against actual production code.

[verified] Independent code review corrected nested score transactions, Unicode
SSE line handling, unsafe/absent provenance, an omitted canonical ID, excessive
JSON integer classification and weak first-refusal controls. Its final bounded
review found no remaining code blocker or cleanup deletion. A second agent is
not an oracle; behavioral evidence remains necessary.

### 5. Slice 19 entry, branch and exact contract

Owner: `04-slices.md` section 9.3, **Slice 19**; transactions/migrations:
`03-program-design.md` sections 9.8/9.9; guards: both documents' complete ledger.
Proposed branch: **`slice-19-postgres-proof`**. Estimate 11 to 18 person-hours
is unmeasured, not a deadline. Confirm Slices 15 to 18's offline acceptance and
shipping, current main/live origin/main and a separately authorised disposable
engine/DSN. Snapshot tree/index/protected video outside the repo and establish
a fresh safe offline baseline. Create the branch from verified current main
before its first edit. Preserve unrelated work; never reset/stash it away.

**Required engine permission is absent from this handoff.** Gate 4 says
"No authorised DSN means blocked." Identify a concrete disposable local target
and obtain explicit authority for its connection, DDL, test writes and cleanup,
or let the user provision and authorise it. Do useful read-only/source/offline
preparation meanwhile, but do not connect, create/drop a database, install or
run engine tests until that authority exists. Never use an inherited real DSN,
Supabase, production, or Envoi's database. No password is pasted into chat/logs.
Existing fixtures drop/rebuild all public tables in their selected database;
therefore an authorised **dedicated disposable database** is mandatory. A
generic reachable Postgres server is insufficient. Use exact target names for
cleanup, and leave unrelated servers/data alone.

Exact test footprint: `tests/test_journey_postgres.py`,
`tests/test_journey_commands.py`, `tests/test_postgres_store.py`,
`tests/test_truthfulness_postgres.py`, `tests/test_deployment.py`,
`tests/test_boundaries.py`, `tests/_mutate_patient_experience.py`.
Only evidence-led fixes within the approved contract in
`src/carerelay/state.py`, `postgres_schema.py`, `postgres_store.py`, `service.py`,
`tools.py`, `api.py` are in scope. Do not refactor other layers speculatively.

Build and prove on real Postgres, with independent connections/processes and
deterministic barriers, rather than sleeps/source inspection/SQLite substitutes:

- G11 to G17/G31 to G38: coherent bundle snapshots, same-operation claim,
  pending/replay, supersede, atomic application/receipt, lost create/intake and
  body-conflict binding. Use otherwise-valid fixtures at the first refusal.
- Writers lock episode before reads, then sorted episode/attempt/command order;
  after a waited lock, reread fresh state. Pure options/ledger reads use
  REPEATABLE READ READ ONLY; patient expiry reads are episode-serialized.
- Stop/revoke committed before invocation gives zero calls. Invocation before
  a waiting stop is ordered and at most once; late success cannot advance.
  Callback ordering and first terminal, original consent/permit ownership and
  every action claim/invocation/effect/receipt crash window retain neutral
  pending/unknown after restart and never redispatch.
- During a paused fake extraction, independently change each final dimension:
  revision/version/confirmation/latest parent/cue/stop/fresh deadline. No score
  or round advances; preserve original deadline/owner. Prove another connection
  can proceed and no connection mutex/transaction remains across the transport.
- Apply additive migration twice to seeded **pre-upgrade** no-plan, active,
  stopped, expired and accepted/handoff histories; reopen in a fresh process.
  Compare prior row bytes, absolute deadlines and histories; equal timestamps
  still use event order for latest parent. Legacy provenance remains unknown.
- Exact table/trigger parity, matching seeded receipt UPDATE/DELETE/TRUNCATE/
  ON CONFLICT UPDATE refusals, phase shape and immutable claim/completion
  binding. Remove just each guard with a valid matching row and require its
  own assertion failure, fresh green controls and byte-exact restoration.
- Fresh authenticated backend after actual termination reads the same episode,
  patient/options/ledger, stop/deadline/receipts; unknown IDs stay 404. Replay
  after response loss agrees with committed state. Production browser refresh
  returns to that episode with no extraction, dispatch or POST.

Current source-only query parity in `test_journey_postgres.py` runs SELECTs
through a SQLite cursor; it is explicitly not an engine result. Existing
engine tests and mutex/nesting tests do not yet prove every listed race. Map
each obligation to real-engine controls and mutations; add missing proof rather
than rename or relabel old cases. Record actual server/driver versions,
connection/process identities, barrier order, failures, exit codes and skip
reasons. Required engine cases must have **zero skips** for the proof claimed.

### 6. Later Slice 20, after the Slice 19 boundary

Branch: `slice-20-accessibility-proof`; entry: completed Slices 14 to 19, exact
confirmation copy approval and explicit continuation. `04-slices.md` sections
9.3/9.6 control. Intended manual pair: **VoiceOver with Safari on macOS**.
Record actual OS/browser/reader versions. If unavailable, disclose the blocked
path, finish independent checks and stop short of a full exit; no install is
inferred. Fix the known BODY-focus failure within the approved behavior.

Operate actual production code through all twelve states/substates, keyboard
start/review/confirm/two repairs/barrier/checkbox/decline/revoke/request/show/
hide/Escape/retry; meaningful visible focus, error association, dialog inertness
and focus restoration, reload/rerender/show/hide failures. Observe actual reader
questions/errors/pending/results/unavailable/failure/recovery announcements
once, without rerender chatter or hidden answers/reasoning. Check 320 CSS px,
desktop, 200% text and **separately** 200% and 400% browser zoom. Record effective
viewport and usable action/deadline/status/buttons. Agreement and positive
scanners at API/SSR/RSC/visible/accessibility surfaces include G03/G06 to G09/
G23/G38. DOM alone, a mockup or an HTML PASS report is insufficient.

Exact files are listed in the Slice 20 contract, chiefly existing production
`PatientJourney.tsx`, `HintCard.tsx`, page/actions/CSS/journey decoder and their
tests. Record results in `docs/reviews/patient-experience-browser-accessibility.md`.
No new patient wording without Gate 1 approval. Standalone visualizations are
HTML. Accessibility observations do not establish target-user benefit.

### 7. Later Slice 21: separate live authority required

Branch: `slice-21-adp-enablement`; entry: completed Slices 18/19/20, explicit
continuation **and separately scoped operator/live-call authority**. Read Gate 2
13.6/13.7, Gate 3 9.2/9.7 and Gate 4's Slice 21 contract. Credentials are locally
configured by the operator. Review fictional processing/region/retention first;
`clinical_share` permission is not general vendor-processing permission.
Deliberately publish **and activate** compatible instructions/schema, inspect
knowledge base/tools/guardrails, then use fresh stateless fictional sessions.
Old asset files or two historic refusals prove no positive extraction.

Observe a grounded positive paraphrase, definite wrong time, missing values,
advice/refusal/injection, negation, alternatives and backward corrections.
Pin the actually observed Type/message/content/correlation/channel/terminal
profile, request/version/latency/failures and replay redacted captures offline.
Configured instruction version is an operator assertion until observed; absent
model identity remains unknown. Synthetic Slice 18 envelopes cannot be
advertised as live vendor evidence. Bounded fault cases remain offline controls.

Use server-held `ADP_APPKEY`/`ADP_CHAT_ENDPOINT`, default-off
`ADP_EXTRACTION_ENABLED`; no credential/expectation pair in prompt/browser/logs
or persisted SSE, no retries/fallback or action call triggered by extraction.
Only observed approved profile/config wiring and the exact Slice 21 tests/review
are in scope; operator edits to instruction/runbook need their separate authority.
Missing positive extraction, incompatible profile, leaked reasoning, legitimate
over-budget frames or unverifiable activation keep ADP disabled. Reopen Gate 2
with the counterexample if its boundary is impossible; do not weaken parsing,
limits or channel discrimination. No clinical/general-language/WorkBuddy-runtime
or deployment claim follows from the bounded fictional corpus.

### 8. Authority and out of scope

This prompt continues **Slice 19 only**, subject to the named engine permission.
The Slice 18 shipping request is exhausted after its verified publication. Do
not commit/merge/push Slice 19, start Slice 20/21, install tools, alter real
configuration/credentials, use external providers, access hosted databases,
deploy, contact participants or restart the cut study without separate explicit
instructions. No main publication is implicit in a Check acceptance alone.
Push may trigger configured automation; it is not manual deployment proof.

Apply in-scope implementation fixes and reversible offline work autonomously.
Do not ask again for permissions already explicitly granted in the next session.
When a required scope is missing, name the precise controlling gate instruction
and the concrete action needing approval. Never import Envoi permissions.
If the approved invariant itself is falsified, record the input/observed outcome
and reopen its owning gate instead of changing copy/contracts to obtain green.

### 9. Tooling, preservation and traps

[verified in this session] Existing Python:
`/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`.
Existing Node bin: `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`.
Frontend dependencies are already installed. Recheck availability; do not install.
Run from repository cwd, with Node on PATH and `PYTHONPATH=src`; tests spawn
relative paths. Clear pytest addopts once to retain its result summary.

For an **offline baseline**, explicitly set `APP_DATABASE_URL=:memory:`,
`APP_CLOCK=scenario`, `APP_ENV=local`, `CARERELAY_API_TOKEN=''`,
`PYTHONDONTWRITEBYTECODE=1` and
`CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled` to prevent
inherited real database access. Run the existing Python with
`-m pytest tests/ -o addopts='' -q --basetemp=<fresh external directory>`.
For later engine proof, replace only with the explicitly authorised disposable
target; don't let defaults or startup dotenv load a hosted DB. Explicitly set
all server configuration for frozen production previews outside the repo.

[verified] Protected **tracked** video:
`submission/usage-proof/Workbuddy_evidence.mp4`, 49,394,082 bytes, SHA-256
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
Keep its bytes/tracking, gate/copy/config/manifests and unrelated work intact.
No new em dashes/co-author trailers; preserve current LF. Historical log
redactions and labelled Codex process accounts must not be overwritten by a
blind WorkBuddy log sync. Codex prose is not new organiser-usage evidence.

[verified] Named Slice 18 listeners on 8317/8318/8319/8320 were stopped, two
temporary browser tabs closed and viewport reset. Recheck ports before use;
never kill an unrelated listener. Do not reuse old fixture cookies across
episodes/tabs: bind each case correctly and assert actual state, not its label.
Scenario deadlines such as `2026-09-30T10:00:00+00:00` are fictional absolute
values, not shifted to today's real date. A fresh real clock is a different test.

Mutation proof requires an actual collected assertion failure at the isolated
first refusal, not missing anchors/imports/attributes/skips or overlapping
guards. Run source mutations serially with every source writer idle; keep byte
backups outside Git, including untracked new files. After changes, produce one
complete current named run plus truthfulness, not an aggregate of partial runs.
Changed source/control fingerprints invalidate old proof; do not resume it as
current. Verify restorations and rerun the relevant full suite afterward.

### 10. Read first

Read `AGENTS.md`, the available software-factory/build/review skills,
`tasks/lessons.md`, `PROGRESS.md`, `docs/CHALLENGE_REQUIREMENTS_JUDGING.md`,
`docs/PLAN.md`, `docs/DESIGN_PRINCIPLES.md` sections 4/8 and every controlling
file under `docs/plans/urgent-advice-accessibility/`, respecting its file map.
Focus on `00-status.md` current receipts/slice checklist, Gate 2 section 5.2/13,
Gate 3 sections 9.5 to 9.10/9.12 and Gate 4 sections 9.2 to 9.8, especially
Slice 19 and guard allocation. Read exact copy, clinical/research blockers and
the Slice 18 local review. Inspect existing tests, `_postgres_probes.py` and
`postgres_store.probe_dsn` before designing engine fixtures; do not guess helpers.
Then inspect current branch/status/index/log, live `git ls-remote --heads origin`
and process state. Verify main remotely before creating Slice 19.

### 11. Done means and stopping boundary

Slice 19 is complete only when **every assigned real-engine race, restart,
migration, trigger and truthfulness obligation** has its own current evidence,
green positive/negative controls and isolated meaningful mutation failure.
Record zero skipped required engine cases and actual versions, fresh-process
authenticated HTTP/curl, lost-response replay, production-browser refresh with
zero POST/extraction/dispatch, and same-surface scanner positive controls.
Run relevant full suites and frontend typecheck/build, narrow architecture
cleanup and preservation/LF/no-added-em-dash/diff checks. Stop only named local
processes/tabs and disclose all failures, unproved paths and unknowns.

Update `00-status.md` as sole state authority, operational `PROGRESS.md`, current
supporting records and a concrete Slice 19 review. Show the **actual visible
result**, exact tests/mutations/versions/evidence and bounded limitations.
Stop for the user's **Slice 19 Check acceptance**. Do not ship it or start
Slice 20 automatically. An inaccessible engine or flaky/unproved required
race/trigger prevents full engine completion, regardless of SQLite totals.
After acceptance, shipping and continuation remain separate explicit actions.

Please proceed with Slice 19 within these boundaries.
