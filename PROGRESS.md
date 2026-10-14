# CareRelay Slice 17: 14 October 2026

Operational memory only. `00-status.md` owns state.

[verified] Local Check accepted by the user; shipping in progress on `slice-17-permission-failure`, from main/live main `e57e23a1741b5db6d6ad51c11bdf6520a0a36cc3`. Working-tree commits and origin/main publication are authorised. Slice 18 remains unstarted.

- [x] Tree/video/index snapshot and branch before edits. Video now tracked, unchanged SHA-256 `cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
- [x] Fresh baseline: 1 failed, 1,768 passed, 51 skips, one warning. User-approved clearing of exactly two sample DSN assignments resolved scanner failure; no rotation/access.
- [x] Fixed-purpose commands, original process permit, tool-held fresh clock, outermost claim/effect transactions and atomic receipts.
- [x] Frontend guarded barrier/unchecked grant/separate request/decline/revoke; exact copy, decoder and old caller migration.
- [x] Final full named run: 727 RED, zero SURVIVED/NOT PROVEN, exact restores and current source/control fingerprints. Current truthfulness 39/39 RED.
- [x] Final suite: 1,869 passed, 54 Postgres skips, one warning. Typecheck/build pass.
- [x] Real HTTP/curl/lost-response/503/202; process ordering/SIGKILL/fork; visible browser and two tabs.
- [x] Twenty-seven literal stored cases, API/SSR/RSC, 135 serialized surfaces and 2,970/2,970 scanner positives; separate DOM/AX observations.
- [x] Review, architect cleanup, records, LF/diff/no-added-em-dash checks. Ports 8317/8318/8319/8320 free; tabs closed and viewport reset.
- [x] User accepts Check and authorises working-tree commits and main publication.
- [ ] Verify final main publication and deliver Slice 18 handoff; stop before implementation.

## Evidence and resume

Review: `docs/reviews/slice17-local-check-2026-10-14.md`.
Full named: `/tmp/carerelay-s17-full-named-4/`; suite `/tmp/carerelay-s17-final-suite.log`; truthfulness `/tmp/carerelay-s17-truthfulness-current3.log`.
Frontend: `/tmp/carerelay-s17-typecheck.log`, `/tmp/carerelay-s17-build-final.log`.
HTTP/browser/scanner/source hashes: `/tmp/carerelay-slice17-live/`.
Preflight: `/tmp/carerelay-slice17-preflight/`; implementation plan `/tmp/carerelay-slice17-plan.md`.

[verified] Earlier proof failures are retained: first named 721 RED/five survivors, later historical 726/726 and 727/727 runs. Final run uses the refreshed truthfulness control corpus. Two truthfulness attempts stopped on stale anchors after 29/34 RED; final 39/39 passes. Failed live fixture setups used shared IDs/clock; final driver isolates them and checks literals. Review fixed nested rollback redispatch, error mapping, projection contradictions, type import and duplicate question. Tool clock now matches Gate 3's required constructor.

[unknown] Postgres is Slice 19; full accessibility/old blockers Slice 20; live ADP Slice 21. No clinical/participant benefit, install, real config/credentials, external runtime, deployment or later slice. Samples cleared, credential validity/history/rotation unverified.

Node PATH `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`; Python `/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`.
Offline tests: `PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local CARERELAY_API_TOKEN='' PYTHONDONTWRITEBYTECODE=1 CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled`, pytest `-o addopts='' -q`, fresh basetemp. Mutations serial with frozen writers/external backups; never kill them.
