# CareRelay Slice 14: 13 October 2026

Operational record only. Gate/slice authority is `00-status.md`.

## Goal and limits

Build Slice 14 first; Slice 15 follows only after the approved Check, continuation
and authorised main handoff. No shipping/install/real credentials/ADP/Postgres/
deployment authority. Local disposable SQLite and fictional data only.

## Verified starting point

HEAD/main/live remote main and program-design branch: `1a8fff9`.
Inherited dirty approval records on `codex/patient-experience-slice-plan`, plus
untracked Slice 14/15 handoff. Snapshotted all 198 tracked/untracked files outside
the repo, including exact dirty bytes, manifest, patch and index:
`/Users/jayd0/Documents/Codex/2026-10-13/files-pasted-by-the-user-carerelay-2/work/slice14/preflight/`.
Created `slice-14-journey-tracer` from main; all snapshot bytes/index matched.
No implementation edits. Prior operational notes remain in that backup.

## Checklist

- [x] Read handoff, controlling contracts, required skills and relevant history.
- [x] Preflight Git/tools, snapshot and branch with byte preservation check.
- [x] Verify closed port 1 and run a fresh offline baseline: 945 passed,
  46 Postgres skips, one existing warning in 3.87 seconds.
- [x] Confirm identity signature gap with a reopened disposable SQLite probe.
- [x] Prepare proposed identity amendment and current-state mirrors.
- [x] User decision recorded in 00-status.md; identity amendment re-approved.
- [x] Implement Slice 14 no-plan/API/renderer/decoder/locator after user decision.
- [x] Focused/full tests, 63 new and 39 existing mutants, one live render mutant, curl and browser.
- [x] Visible Check and architecture cleanup; user continuation checkpoint pending.
- [!] Slice 15 also requires Slice 14 on main through separate Git authority.

## Evidence and environment

External interpreter: `/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`.
Python 3.13.12; pytest/fastapi/httpx/uvicorn/psycopg imports passed.
Preflight had no .venv/frontend node_modules. Node 24.21.0/npm 11.19.0 found; compatible Next.js
not located in bounded search. A broad file search was stopped without a result;
this is not proof that no installation exists elsewhere. Operator-only setup:
`npm --prefix /Users/jayd0/Desktop/carerelay/frontend ci`. No install performed.
A zsh optional-directory glob failed on absent paths, not on application code.

Commands use PYTHONPATH=src, APP_DATABASE_URL=:memory:, APP_CLOCK=scenario,
APP_ENV=local, CARERELAY_API_TOKEN='', PYTHONDONTWRITEBYTECODE=1 and
CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled after verifying
that loopback port is closed. Baseline command: external interpreter `-m pytest
tests -o addopts='' -ra --basetemp=/tmp/carerelay-slice14-baseline-20261013`.
Log and identity probe/JSON live under the chat's `work/slice14/` directory.
Pure parity tests ran; engine skips are not engine evidence.

Counterexample: two legal no-plan rows without events survive close/reopen;
the approved bundle inputs are equal but required IDs differ. No planned
projector exists or was executed. Proposed fix adds the verified episode ID to
the bundle. No mutation, application change, migration, server/browser or cleanup
completion is claimed. All long-running preflight searches/tests have ended.

## Result

Slice 14 preflight complete; implementation resumed after the user decision. At that earlier preflight, Slice 14 was incomplete and Slice 15 unstarted. No stage/commit/merge/push,
install, real config/credential change, ADP, Postgres or deployment. Final
preservation checks pass: 188 other snapshot files unchanged, source/tests/frontend
and Gates 1/2/4 byte-preserved, HEAD/main/index unchanged, LF and no new em dashes.
`git diff --check` passes. The reviewable decision/probe are exported in the chat
outputs directory.

## Final local verification receipt

Full suite after cleanup: 1,033 passed, 46 Postgres skips, one warning (7.46s).
Typecheck/build pass on operator-installed Next.js 15.5.27. No package/lockfile
change. Audit: one moderate/one high package finding, no remediation attempted.
63/63 current journey mutants, 39/39 existing truthfulness mutants, and one
separate production SSR create-on-render mutant seen RED; passing controls and
byte-exact restores. The deliberate live mutant alone generated a POST.
Normal browser/curl evidence: 91 GETs/zero POSTs before that mutation; 38 malformed
browser cases with good controls; five real surface scans with ten injected
needles each. Desktop 1280x900, 320px and 200% text, keyboard skip/retry verified.
No VoiceOver/Safari or 200%/400% zoom claim. No ADP/Postgres/deployment proof.

Actual preview: http://127.0.0.1:8140/; backend http://127.0.0.1:8139.
SQLite file and logs: chat work/slice14/live. Current backend PID 87396;
pre-restart PID 84906. Missing-key and mutation frontend servers stopped.
The API and normal frontend remain solely for the user's local review.
No Slice 15 work; commit/merge into main still requires separate user authority.
Authoritative completion and pending user decision are in 00-status.md.

Dropped-bootstrap proof: loopback proxy received real 303/cookie replies from
Next.js, dropped them before delivery, and browser returned ERR_EMPTY_RESPONSE.
Backend count stayed unchanged. Error-page inspection was URL-policy blocked;
no claim of app-rendered recovery for the dropped connection. Proxy stopped.
Normal preview PID: node 87410; backend PID: python 87396. Stop these only when
review is finished. No source change followed the final full suite/build.

## Shipping request: 13 October 2026

User requested main publication and the Slice 15 handoff. Commits are grouped
by coherent reads, visible tracer, mutation enforcement, historical log copies
and authority/handoff records. No Slice 15 implementation or branch created.
Fresh suite: 1,033 passed/46 skips/one warning. Main push verification pending.
New unrelated Workbuddy_evidence.mp4 remains untracked and untouched.
