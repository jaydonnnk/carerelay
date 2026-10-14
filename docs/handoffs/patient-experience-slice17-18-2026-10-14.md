# CareRelay: Slice 16 record and context for Slices 17 and 18

Dated 14 October 2026. `00-status.md` owns gate and slice state.

## Shipping update: 14 October 2026

[verified] The user accepted the bounded Slice 16 local Check and authorised
scoped commit, fast-forward into main, push of origin/main and cleanup.
Shipping is in progress. Stop and notify before Slice 17. No Slice 17 branch
or code is created by this shipping session. `00-status.md` owns its receipt.
The build-session snapshot below is historical until the prompt is refreshed
with verified publication state.

## Build-session boundary before acceptance

[verified] The original assignment requested Slices 16, 17 and 18, one at a time,
on separate branches with separate Checks, continuations and shipping authority.
The user then asked to finish Slice 16 and stop, and to write this handoff for
Slices 17 and 18 with reference to that starting assignment. This file supplies
context. It grants no Git shipping or next-slice execution authority.

[verified] Slice 16's offline/SQLite local Check is ready: 1,769 passed,
51 Postgres skips, one existing Starlette warning; frontend typecheck/build pass.
One current full named mutation run is 631 RED, zero SURVIVED/NOT PROVEN, with
fourteen targets restored byte-exact. Current truthfulness is 39/39 RED.
Actual HTTP and a visible browser exercise the bounded flow. Thirty-eight stored
cases agree across API, SSR and RSC; 190 surfaces have 4,180/4,180 positive
scanner controls. This is local evidence, not ADP, Postgres or clinical proof.

[verified] Checkout is `slice-16-confirmed-readback`. HEAD and local main remain
`489dc2c9a977df4b1fff6cbc679993e96b33f43b`. Origin/main matched at preflight;
there was no push here. The slice code, proof and records are uncommitted.
User acceptance of this Check and Git shipping have not been given.
Slices 17 and 18 remain unstarted. Their branch names are still
`slice-17-permission-failure` and `slice-18-adp-boundary`.

[verified] The unrelated `submission/usage-proof/Workbuddy_evidence.mp4` remains
untracked, unstaged and byte-identical at
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
No installation, real configuration or credential change, external runtime,
live ADP, real Postgres access, deployment or participant work occurred.

## Decisions and traps specific to this session

[verified] Gate 1's five strings were approved explicitly with
"Approve these exact Gate 1 strings". They are in the copy inventory and
`00-status.md`. No repeat confirmation-copy approval is needed for those strings.
Specialized non-timing repair and system-date templates remain blocked.

[verified] The plain English word `tomorrow` remains uncertain. The approved
wrong-day example uses `tomorrow before 6pm`, then `today before six`.
The scenario remains 30 September 2026, 09:00 SGT, with stored deadline
`2026-09-30T10:00:00+00:00`. No expected field is filled into missing words.

[verified] The new source file is named `adp_extraction.py`, but it supplies only
the port and labelled offline extractor. No strict vendor parser, SSE profile,
network transport, enablement, credentials or publish operation exists from
Slice 16. `eligible_offline_output` deliberately refuses an ADP-mode result.
The later adapter cannot turn that refusal into live enablement.

[verified] The live browser caught the old start-only capability decoder,
answer-bearing initial HTML/RSC after client-only redaction, and a main-focus
callback that stole Escape focus. Actual server-generated read-back tokens now
cross the real Node decoder, start/hide can replace the document, and Escape
restores Show focus. DOM redaction alone is not evidence of RSC redaction.

[verified] A stopped screen initially retained retry prompts and then failed
its decoder after those prompts were removed. Whole producer-to-decoder cases
now cover stopped, confirmed, pending H3 and expired histories. Pending stop
keeps Show/Hide, with zero further scoring or supersede offer.

[verified] Exact offsets alone did not rule out `myself` inside `myselfish` or
`notmyself`. The port boundary now refuses embedded English words. A full-width
question in `today before six？` also falsely passed the earlier comparison;
its deadline now stays uncertain. These are bounded lexical controls, not
proof of general language understanding or clinical comprehension.

[verified] Do not reuse the earlier 489, 621 or 630 mutation snapshots as current
proof. Their source/control fingerprints differ, and the latter runs disclosed
survivors or NOT PROVEN cases. Only `/tmp/carerelay-slice16-full-named-4` is the final named run.
A failed pending-navigation mutation needed an assertion before the first
missing offer, rather than a `next()` lookup that raised StopIteration.

[verified] The browser ran visibly at 544x797 and supports a real
320px override. This does not retroactively pass Slice 15's blocked items.
The Slice 16 observations are bounded keyboard, pointer, screenshot, 320px,
enlarged-text-control and two-tab checks. Full assistive-technology and browser
zoom work remains Slice 20. CSS dimensions alone are not evidence.

## Files changed, with current line anchors

[verified] These groups describe the Slice 16 delta. The full diff remains
uncommitted; line anchors below are for this source snapshot.

- `src/carerelay/adp_extraction.py:1-84`: port, offline exact-source extraction and invalid-output/word-edge refusal.
- `src/carerelay/domain/models.py:237-269` and `domain/rules.py:373-589`: immutable context/source types, exact confirmation, independent doubt, source retention and final rechecks. `rules.py:1215-1264` adds guarded offers and bounded read-back feedback/cue copy.
- `src/carerelay/state.py:241-339`: claim context, allowlisted provenance, exact owned confirmation/scoring and atomic append. Restatement envelope decoding preserves legacy unknown provenance; the Postgres writer adds the same optional provenance contract.
- `src/carerelay/service.py:935-1143`: read-only words preparation, exact confirmation, detached extraction, fresh final transaction, supersede and provenance. Projection commits timing exposure before display.
- `src/carerelay/api.py:460-494` and `639-767`: strict command endpoints and safe response mapping, replacing retired raw patient writes.
- `frontend/app/actions.ts:28-61`, `lib/api.ts`, `lib/episode-locator.ts:80-133` and `lib/journey.ts:98-296`: server-only command bridges, capability grammar and complete bounded lifecycle decoding.
- `frontend/components/PatientJourney.tsx:27-208`, `HintCard.tsx:1-29`, CSS and ledger: local escaped preview, explicit save/check/retry, native dialog, document replacement/focus, larger text and offline/legacy provenance labels.
- `tests/test_field_repair.py`, journey/decoder/guard files, `_mutate_patient_experience.py`, `journey_decoder_cases.json` and `test_boundaries.py`: new domain/service/store/API/Node controls, concrete falsifiers, current anchors and source-scanner coverage. Five new `test_journey_postgres.py` cases remain skipped.
- Authority/supporting records, lessons and `docs/reviews/slice16-local-check-2026-10-14.md`: local Check, scope, approval receipt and evidence limits. Gate 2/3/4 contracts, manifests and real configuration are byte-preserved.

## Open work and inherited assignment boundaries

[verified] Slice 16 still depends on user Check acceptance and separately scoped
Git shipping before Slice 17 can branch from current main. The current slice's
dirty changes are not a suitable base to carry onto a new branch from old main.
Slice 17's accepted Check, shipping to main and explicit continuation similarly
precede Slice 18. This handoff does not satisfy any of those dependencies.

[verified] Slice 17's contract is `04-slices.md` section 9: permission and truthful
simulated failure. Its guard allocation is G03 to G07, G12 to G14, G16, G17,
G22, G31 to G35, G37 and G38. The inherited `frontend/lib/api.ts:61` 401-versus-503
reason remains UNPROVEN-NO-CONTROL and belongs to Slice 17. No real provider,
message, ADP action, new actor, clinical branch or copy authority follows.
Duplicate invocation, split receipts, false success or bypass blocks further
feature work. Request purpose, once-consumed permit, crash and no-redispatch
requirements remain exactly those in Gate 3 section 9 and Gate 4's Slice 17.

[verified] Slice 18's contract remains strict `carerelay-readback-v1` extraction
through explicitly fake offline transports. Its guard allocation is G15,
G18 to G21, G24 to G30, G34 and G38. The exact six-key object, transport limits
and approved discriminator are unchanged. Default enable remains false.
There are no keys, network, publication or live activation. A permissive parser
workaround or inability to implement the approved discriminator reopens Gate 2.
It never enables ADP.

[unknown] Real Postgres concurrency, migration and restart proof remains Slice
19, blocked on separately authorised disposable access. ADP activation, profile
and positive extraction proof remains Slice 21. No Slice 19, 20 or 21 work is
included. Slice 9's participant run was CUT, with no participant validation;
Slice 13 remains historical and unbuilt.

## Reproduction details unique to this workstation

[verified] The existing runtimes are:

```text
Node PATH: /Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin
Python: /Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python
PYTHONPATH=src
APP_DATABASE_URL=:memory:
APP_CLOCK=scenario
APP_ENV=local
CARERELAY_API_TOKEN=''
PYTHONDONTWRITEBYTECODE=1
CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled
pytest: -o addopts='' -q, with a fresh --basetemp
```

[verified] Without Node on PATH, hundreds of subprocess tests fail with
FileNotFoundError. That is a toolchain gap. Mutation scripts exceed the shell's
120-second limit, so the previous runs used background command sessions.
Their targets and control sources remained frozen until completion, then were
independently compared with the external byte backups. No killed run earns proof.
Staged blob/mode entries still equal HEAD. Raw index cache bytes can change
when Git refreshes file statistics and are not a preservation claim.

[verified] Evidence locations are local and may be removed by workstation
cleanup. The durable repository summary is
`docs/reviews/slice16-local-check-2026-10-14.md` and `00-status.md`.

- Final suite: `/tmp/carerelay-s16-post-mutation-final.log`.
- Full named proof and backups: `/tmp/carerelay-slice16-full-named-4/`.
- Truthfulness: `/tmp/carerelay-s16-truthfulness-current-final.log` names its external evidence directory.
- Typecheck/build: `/tmp/carerelay-s16-typecheck-final.log` and `/tmp/carerelay-s16-build-final.log`.
- Runtime, scanner, cross-surface, reply-loss, screenshots and frozen-source hashes: `/tmp/carerelay-slice16-live/`.
- Preflight: `/tmp/carerelay-slice16-snapshot.json`, including the protected video hash.

[verified] Every preview/test process started here is stopped. Ports 8315, 8316
and 8317 are verified free. Temporary browser viewport override was reset.

## Prompt for New Chat

CareRelay context for `/Users/jayd0/Desktop/carerelay`, 14 October 2026:

The original assignment covered Slices 16, 17 and 18 one at a time, each on its
own branch and ending in its own visible Check and explicit continuation.
The latest steering was to finish Slice 16 and stop, with this handoff prepared
for Slices 17 and 18. The current record is
`docs/handoffs/patient-experience-slice17-18-2026-10-14.md`.

Slice 16 is built and its offline/SQLite local Check is ready on dirty
`slice-16-confirmed-readback`, HEAD/local main `489dc2c`. Current proof is
1,769 passed, 51 Postgres skips, one warning, 631 named mutations RED with
zero SURVIVED/NOT PROVEN and exact restores, plus 39/39 truthfulness RED.
User Check acceptance and Git shipping remain absent. The five exact Gate 1
confirmation/help/pending/retry strings are explicitly approved; other blocked
copy stays blocked. ADP remains disabled. The video stays untracked at the hash
in this handoff. The current browser supports visible checks, but full
accessibility and old Slice 15 blockers still belong to Slice 20.

The controlling read set from that starting assignment is AGENTS.md's top
checkpoints and sections 3, 5 and 6; PROGRESS.md as operational memory;
`docs/plans/urgent-advice-accessibility/00-status.md` as the only gate/slice
state authority; Gate 3 `03-program-design.md` section 9, especially 9.5 to 9.10
and 9.12; Gate 4 `04-slices.md` section 9, especially entry blockers, exit
discipline, guard allocation, browser matrix and the Slice 17/18 contracts;
`01-product.md` and `patient-experience-copy.md`; and the prior record
`docs/handoffs/patient-experience-slice15-continuation-4-2026-10-14.md`.

The build/review skills remain `carerelay-slice-build` and
`carerelay-slice-review`; `carerelay-slice-ship` applies only after explicit Git
authority. The original per-slice discipline remains in effect, including
fresh baseline and video/tree snapshot before editing, both-engine code with
real Postgres explicitly skipped/unproven, fail-capable controls at the first
refusal layer, one clean full named mutation run plus truthfulness, real
HTTP curl, production-browser and positive scanner controls, architect cleanup,
current records, LF/no-added-em-dash/diff checks and named-port cleanup.

Slice 17 is permission and truthful simulated failure on
`slice-17-permission-failure`, from verified main only after Slice 16 is accepted,
shipped and explicitly continued. Its guards and the api.ts reason control are
listed in this handoff. Slice 18 is strict ADP extraction on
`slice-18-adp-boundary`, from main only after Slice 17 is accepted, shipped and
continued. The default ADP flag remains false and transports remain fake.
The original no-install, no-real-config/credentials, no-external-runtime,
no-live-ADP, no-Postgres-access, no-deployment, no-participant and no-Slice-19/20/21
boundaries remain. Later blockers and the protected untracked video hash are
unchanged. Git authority is separate and currently absent. Each authorised
shipping close uses coherent named staging, no co-author, the safe fast-forward
main ref update before checkout, push of origin/main and live ls-remote verification;
tracking-ref loss does not prove push failure, and shipping-made-false records
need a sweep. No approval or continuation is inferred from this context.

Wait for instructions before taking any action.

## Optional Prompt for Handoff Review

Independently review the uncommitted Slice 16 in
`/Users/jayd0/Desktop/carerelay`, against Gate 3 section 9 and Gate 4's exact
Slice 16 exit. Assume it may be flawed. Be unbiased, thorough and honest.
The claimed scope is offline confirmed read-back, field repair, cue/cap and
atomic claim/receipt handling, with the bounded evidence in this handoff and
`00-status.md`; no real ADP, Postgres, deployment or participant proof is claimed.

Re-run the documented baseline/current checks, inspect the actual diff including
untracked source and tests, and stress-test confirmation, retention, pending,
late answers, crashes, hidden HTML/RSC, SourceSpan bounds/word edges, question
markers, and complete producer-to-frontend decoding. Probe every caller when a
guard is masked. Require each named test to be fail-capable with an otherwise
valid counterexample and a reversible, byte-backed mutation. Do not pass tests
for the sake of passing. Flag weak tests, hidden assumptions, scope creep and
unsupported claims. A green batch or passing total is not guard proof.

Use `carerelay-slice-review` and architect cleanup within the original authority.
No installs, Git shipping, external runtime, real configuration/credentials,
live ADP or Postgres access are authorised. Temporary mutations require
external backups, unique anchors, serial writers and exact restoration.
Report PASS, ISSUES FOUND or FAIL, with file/line evidence, actual outputs,
quality findings and explicit limitations. Deliver your verdict and wait for
instructions.
