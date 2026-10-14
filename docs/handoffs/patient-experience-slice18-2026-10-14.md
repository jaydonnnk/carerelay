# CareRelay: Slice 18 implementation handoff, 14 October 2026

`00-status.md` owns gate and slice state. This supporting handoff does not start
Slice 18 or grant authority by itself. The prompt below is intended for the user
to submit to another agent as the explicit Slice 18 continuation.

## Current handoff state

[verified] The user accepted Slice 17's bounded local Check and requested:
"Yes i accept the check, commit the working tree and push to main, then give a
concrete and thorough copy paste handoff prompt for slice 18 for another agent".
Slice 17 shipping is being completed under that request. The dated publication
receipt in `00-status.md` and live Git refs, rather than an old hash copied here,
establish the final entry tip. No Slice 18 branch or implementation is made in
this session. Later shipping authority remains separate.

[verified] Accepted Slice 17 proof: 1,869 passed, 54 Postgres skips, one existing
Starlette warning; typecheck/build pass. One final named run has 727 RED,
zero SURVIVED/NOT PROVEN and exact current target/control fingerprints.
Truthfulness has 39/39 RED. Local HTTP, process crash/ordering, visible browser
and scanner evidence is bounded as recorded in
`docs/reviews/slice17-local-check-2026-10-14.md`. This is SQLite/simulator proof.

[verified] The video is now tracked, despite older untracked snapshots:
`submission/usage-proof/Workbuddy_evidence.mp4`, 49,394,082 bytes, SHA-256
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
The user separately approved clearing exactly two credential-bearing sample
assignments in `.env.example`. They are empty. No real configuration access,
credential rotation or history rewrite occurred; credential validity is unknown.

[unknown] Real Postgres proof remains Slice 19, full accessibility and old
Slice 15 blockers remain Slice 20, and live ADP remains Slice 21. Slice 9's
participant run is cut. No clinical or participant benefit is established.

## Session-specific mechanisms and traps

[verified] `adp_extraction.py` currently contains the port, result types and
explicit `OfflineReadbackExtractor`. It contains no strict ADP parser or SSE
adapter. `eligible_offline_output` deliberately refuses an ADP-mode result.
Slice 18 needs a separately justified, strictly validated eligible ADP path;
merely deleting the mode refusal or relabelling offline results would defeat
the intended boundary. The service currently calls the port outside its score
transaction and final-rechecks current state before applying a result.

[verified] Slice 17's final dispatch needs the original, identity/PID-bound,
once-consumed `DispatchPermit`; serialized or reconstructed permits refuse.
`McpTools` requires the injected `now` callable, which is read inside final
episode serialization. Both stores' `journey_transaction` have additive
`outermost=True` enforcement for action claim/final dispatch. The permit registry
contains no clock. Observation and applied invocation receipt are not callback
evidence. Keep these controls intact while adding extraction.

[verified] Raw patient barrier/consent/action routes are retired. A new token,
caller-chosen purpose, replay, restart or direct old MCP/service key cannot
redispatch. `tests/_legacy_service_probes.py::command_action` is a command-backed
positive regression helper; `historical_attempt` seeds old store history without
calling a provider. Do not replace these with permissive bypass fixtures or
weaken precise refusal assertions merely to migrate a constructor.

[verified] Pending projection cannot override an accepted/handoff terminal
screen. `barrier_stop` feedback applies only to a stopped screen. Preserve the
original deadline and patient owner in unresolved failure/unknown views.
Five exact Slice 16 confirmation/help/pending/retry strings are approved.
Specialized non-timing repair and system-date strings remain blocked.

[verified] `tomorrow` alone remains uncertain in `fixture-provisional-0`.
The bounded timing story uses `tomorrow before 6pm`, then `today before six`.
Scenario time remains 30 September 2026, 09:00 SGT, with stored deadline
`2026-09-30T10:00:00+00:00`. Actual calendar date must not shift fixture policy.
Embedded English word spans and full-width questions already have controls.

[verified] The named harness requires `--run` for mutations. Its default,
`--anchors-only` and validation/collection modes are not mutation proof.
Only `/tmp/carerelay-s17-full-named-4/` is the final current Slice 17 corpus;
earlier runs had survivors or older control hashes. Truthfulness's complete run
is `/tmp/carerelay-s17-truthfulness-current3.log`; two preceding attempts stopped
at stale anchors after 29/34 RED. Do not merge their totals.

[verified] External live drivers initially failed from wrong policy provenance,
shared callback/operation IDs and an inherited expired clock. The final driver
isolates identities and resets each scenario, asserts literal expected
step/deadline before capture, and uses authenticated operator transfer paths.
A case name or self-consistent producer/decoder pair is not independent proof.
Later two-tab/transport interactions changed designated fixtures after captures.

[verified] Native browser observations caught a missing API `Literal` import
(real POST 500) and duplicated question heading. Tests now cover both. A viewport
request once affected the other tab; only measured width/scrollWidth/font values
count. Larger text is exposed differently by AX and DOM roles; query the actual
surface. HTML-derived accessibility text does not establish VoiceOver or zoom.

## Evidence and existing runtimes

[verified] Build-session evidence is outside Git and may disappear across hosts:

- `/tmp/carerelay-s17-full-named-4/`: `results.json`, control hashes, backups and
  individual passing/failing/restored artifacts for 727 named cases.
- `/tmp/carerelay-s17-final-suite.log`,
  `/tmp/carerelay-s17-truthfulness-current3.log`,
  `/tmp/carerelay-s17-typecheck.log`, `/tmp/carerelay-s17-build-final.log`.
- `/tmp/carerelay-slice17-live/`: authenticated HTTP/curl, lost responses,
  fault/process scripts, literal matrix captures, scanner controls, browser
  screenshots and independently matched final source hashes.
- `/tmp/carerelay-slice17-preflight/`: original tree/video/index snapshot.
- `/tmp/carerelay-s17-shipping/`: pre-shipping snapshot and fresh publication
  verification logs. These are shipping checks, not fresh mutation execution.

[verified] Existing Python:
`/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`.
Existing Node bin directory:
`/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`.
Frontend dependencies are already present. No installation is authorised.
The standard offline suite command, with a NEW temporary basetemp, is:

```sh
PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local \
CARERELAY_API_TOKEN='' PYTHONDONTWRITEBYTECODE=1 \
CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled \
/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python \
-m pytest tests/ -o addopts='' -q --basetemp=/tmp/carerelay-s18-baseline-UNIQUE
```

The fake disabled DSN prevents an inherited real database value from becoming
test authority. Do not load real `.env` values. Use synthetic loopback runtime
settings and disposable SQLite files outside the repository for live checks.
Slice 17 stopped only its named processes; ports 8317/8318/8319/8320 were free.
Recheck before reuse and stop only processes you create/identify.

## Copy-paste prompt for the next agent

```text
Implement CareRelay Slice 18 only in /Users/jayd0/Desktop/carerelay. I explicitly
continue from the accepted and shipped Slice 17 local Check. Finish Slice 18's
bounded offline Check, show me the visible result and stop for my acceptance.
Do not commit, merge or push Slice 18, and do not begin Slice 19, 20 or 21.

Read docs/handoffs/patient-experience-slice18-2026-10-14.md first. This is the
current handoff. Slice 17's publication receipt is in 00-status.md; use current
Git refs and live ls-remote to verify it rather than relying on a historical hash.
Use carerelay-slice-build and carerelay-slice-review. carerelay-slice-ship applies
only after a later explicit Git instruction. Read AGENTS.md's top checkpoints
and sections 3, 5 and 6, PROGRESS.md, tasks/lessons.md, then the controlling set:

- docs/plans/urgent-advice-accessibility/00-status.md, the sole state authority;
- 01-product.md and patient-experience-copy.md;
- 02-architecture.md section 13, especially 13.6;
- 03-program-design.md section 9, especially 9.5-9.10 and 9.12;
- 04-slices.md section 9: entry/exposure rules, common exit discipline, Slice 18,
  complete guard allocation and browser matrix;
- docs/reviews/slice17-local-check-2026-10-14.md and the historical
  docs/handoffs/patient-experience-slice15-continuation-4-2026-10-14.md for carried
  limitations. The older slice17-18 handoff has superseded build snapshots.

Preflight before editing:
1. Inspect status, current refs and live origin/main. Slice 17 must be accepted
   and on verified main. Stop on unexplained divergence or unrelated changes;
   do not discard, stash, reset or carry dirty Slice 17 files onto another branch.
2. Snapshot file presence/bytes, tracked/untracked paths, index entries and the
   protected tracked video outside the repository. Verify the handoff's video
   hash and preserve its tracking. Run a fresh offline baseline with the existing
   interpreter/toolchain; disclose failures and skips honestly.
3. Create slice-18-adp-boundary from verified current main before the first edit.
   Inspect an existing branch if present; never silently repoint it. Verify the
   branch and snapshot after checkout. No next-slice branch is authorised.

Scope: strict ADP read-back extraction using explicitly fake offline transports.
Confirmed fictional words go through the new adapter; deterministic domain
comparison remains the decision-maker. A grounded positive answer can match;
known wrong time yields approved timing repair; missing/negated/ambiguous input
stays uncertain. Invalid/refused/disabled/slow-terminal output is unscored
unavailable, preserving the confirmed answer, current question, owner, closure
and original deadline, with zero repair rounds or clinical stop consumed.
The default ADP_EXTRACTION_ENABLED flag remains false. No keys, real config or
credentials, provider network calls, external runtime, live ADP, publish or
activation, Postgres access, installs, deployment or participant work. Local
loopback HTTP for tests is allowed. Action origin remains local-sim.

Work at the narrowest responsible layers. Approved file footprint:
src/carerelay/adp_extraction.py, domain/rules.py, domain/models.py, service.py,
coordinator.py, api.py, presentation.py; frontend/lib/api.ts, lib/journey.ts,
components/PatientJourney.tsx, app/ledger/page.tsx; tests/test_adp_extraction.py,
test_field_repair.py, test_journey_commands.py, test_journey_postgres.py,
test_api.py, test_boundaries.py, test_deployment.py and
_mutate_patient_experience.py. Only touch callers actually needed. Do not build
a general ADP SDK, invent a schema table or alter approved copy to simplify work.
Existing TSX paths are production files; standalone visualisations must be HTML.

Strict object contract from Gate 3 section 9.7:
- Exactly one carerelay-readback-v1 JSON object with exactly schema_version,
  action_span, deadline_span, next_owner_span, uncertain_fields and refused.
- Each span is null or exactly {text:string,start:integer,end:integer}. Offsets
  are Python Unicode code points into the exact confirmed string, half-open.
  Reject bool-as-int, UTF-16/byte offsets, negative/empty/out-of-range spans and
  any source-slice mismatch. Preserve existing word-boundary controls.
- Reject duplicate keys at every depth, extra/missing keys, wrong versions,
  canonical IDs supplied as answers, wrong types, repeated/unknown uncertainty,
  invalid UTF-8, nonfinite numbers, multiple objects, prose and fences.
- Refusal requires all spans null and all three fields uncertain. Missing spans
  require corresponding uncertainty; uncertainty may coexist with grounded spans.
  Never store/show provider refusal prose or invent missing spans lexically.
- Union provider uncertainty with independent whole-answer doubt/contradiction
  before canonicalisation/comparison and latest-parent retention. A source span
  inside a negation, question, alternative or later correction is not a match.
  Bare tomorrow stays uncertain; do not change fixture policy or date wording.

Transport/profile contract:
- Implement the approved extraction signatures and an injectable fake transport
  with explicit pinned fake profiles for incremental final-answer OR one complete
  final-answer payload. Do not present synthetic nested fields as observed vendor
  fields. The live discriminator remains unverified and blocked until Slice 21.
- Eligible final content must match lifecycle/event, assistant message, content,
  correlation, channel, ordering and terminal profile. Explicitly profiled
  heartbeat/lifecycle/reasoning can be ignored; reasoning is never buffered,
  logged, persisted or shown. Count ignored bytes toward the wire budget.
- Bounded incremental UTF-8 and multiline SSE framing must work across chunk
  boundaries. Provider error, unknown/mixed channels, conflicting IDs, ambiguous
  duplicate chunks, multiple finals, truncated stream, premature/missing terminal
  and delta+final doubling all refuse. Deduplicate sequence IDs only when the
  pinned protocol supplies them and bytes agree. HTTP 200, EOF and first byte
  are insufficient. Do not join best-effort text from an unrecognised profile.
- One monotonic five-second deadline covers connection through the full answer
  and terminal, never refreshed per chunk. Input limit 2,048 code points; final
  answer 16 KiB UTF-8; envelope frame 16 KiB; total wire 64 KiB. Prove exact-limit
  success and each limit+1 refusal independently. Limits remain unmeasured choices.
- Exactly one call: no automatic/SDK retry and no offline lexical fallback after
  failure. Disabled mode performs zero transport calls. Fresh ConversationId and
  RequestId use the approved 32-64-character alphanumeric/underscore/hyphen form;
  VisitorId is anonymous per call. No vendor session resume. Assert request-body
  shape with fake auth: backend AppKey, Contents text, Stream/Incremental; AppKey
  never enters the prompt. Server-configured endpoint only; no browser override,
  redirects forwarding credentials or ADP_API_SECRET on this SSE path.
- Prompt contains confirmed words, independent vocabulary sets, instruction,
  schema and correlation only: no expected disposition/answer pairing, canonical
  target, selected plan, profile, consent or receipt. Vocabulary may reveal likely
  fixture answers; grounding and independent doubt remain required.
- Judge provenance identifies fake transport and configured profile/instruction/
  schema versions, correlation, exposed trace, validation/failure category and
  model version if actually present. Configured instruction is an operator
  assertion; absent model version is null/unknown. Persist only bounded validated
  fictional extraction, never raw SSE, secrets, reasoning or unvalidated output.

Integration and concurrency:
Keep command claim/context fencing before extraction, perform transport outside
database locks, and recheck revision, disposition version, confirmation, latest
parent, cue, stop and fresh deadline before atomic score/receipt completion.
Prove two score workers cause one call, supersede fences an old answer, and each
concurrent change separately makes a late result unscored. Unavailable never
consumes a round or fabricates a receipt. Implement both-engine code contracts;
real Postgres stays explicitly skipped/unproven. Preserve all Slice 17 permit,
fresh-clock, fixed-purpose, once-only dispatch and truthfulness boundaries.

Verification must be adversarial and fail-capable:
- Own/extend G15, G18-G21, G24-G30, G34 and G38 and applicable projection/scanner
  controls. Use good and bad fake profiles; an always-refuse adapter must fail a
  positive control. Matching output alone is not sufficient evidence.
- For every validator/profile/limit/final-recheck dimension, collect the exact
  test, run its passing control, remove only that guard, and show an assertion
  failure at the first refusal layer. Another later refusal masking it is not
  proof. Independently test no retry/fallback and each reasoning/secret surface.
- Freeze writers before one complete current named mutation run, plus current
  truthfulness. Mutate serially, purge target bytecode, back up tracked and
  untracked targets outside Git, verify byte-exact restores and source/control
  hashes. Missing anchors, skipped engines, collection/import/syntax errors are
  NOT PROVEN. Never kill a live mutation harness or weaken a test to get green.
- Run focused checks then fresh full suite, frontend typecheck and production
  build with existing runtimes. Keep skips and warning counts separate.
- Exercise authenticated real HTTP/curl and an actual production browser with
  fake positive, wrong-time, missing/negated and unavailable cases. Verify same
  answer/question/owner/deadline across API, SSR/RSC and visible state. Check
  strict bodies, pending/replay/stale responses, reload and two-worker races.
  Extraction makes one fake transport call and zero booking-provider calls.
- Plant reasoning and synthetic secret markers into the SAME API/SSR/RSC/visible/
  accessibility/log surface each detector claims to scan; prove detection would
  fail if leaked. Real clean captures plus positive injection controls are needed.
  Include all new files/functions in real-file boundary and secret scanners.
- Observe basic keyboard/focus, dialog/recovery, measured 320px/wide reflow and
  enlarged text for new controls. Record actual browser/URL/port/PIDs/engine.
  Carry full accessibility and old blockers to Slice 20, not retroactive passes.

If the approved discriminator cannot be implemented without a permissive parser
or a different architecture, reopen Gate 2 narrowly and wait for its re-approval.
Do not enable ADP or invent live-profile proof to bypass that blocker.

At completion invoke architect-reviewer for cleanup, retain referenced fixtures
and proof, update the current records required by Gate 4 section 9.3 and keep
00-status.md as sole state authority. Preserve LF, check every added line for
em dashes and run git diff --check. Verify video/gate/copy/manifest preservation.
Stop only your named servers and clean temporary tabs/viewport state. Show the
actual visible Slice 18 result, summarize exact evidence and limitations, then
ask for Check acceptance and stop. Git shipping and continuation to Slice 19
remain separate explicit user decisions.
```
