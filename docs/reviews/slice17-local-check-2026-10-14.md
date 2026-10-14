# Slice 17 local Check: ready, 14 October 2026

Supporting note, authoritative for nothing. `00-status.md` owns state.

[verified] The user explicitly continued Slice 17 after accepting and shipping Slice 16. Work is uncommitted on `slice-17-permission-failure`, from verified local/live main `e57e23a1741b5db6d6ad51c11bdf6520a0a36cc3`. This Check covers local SQLite and the bounded simulator. User acceptance, shipping and Slice 18 continuation are absent.

## Result and mechanism

[verified] Understood plan -> supported booking barrier -> unchecked permission -> separate grant and simulated request -> neutral waiting -> separate winning failed callback -> exact unresolved lines. Transport/other stops honestly; decline starts no attempt. Revoke/reload and duplicate tokens/tabs cannot invoke again. The patient owner and original deadline `2026-09-30T10:00:00+00:00` remain. Scenario is 30 September, 09:00 SGT.

[verified] Barrier/hint/consent/request writes have bound claim/completion receipts and current-state checks. Purpose is server-fixed `disposition:<version>:request_appointment`, route `fictional_provider`. Original newly-claiming execution alone receives an identity/PID-bound once-consumed permit. No permit/clock crosses tool JSON or patient responses. Claim and final dispatch each require their own committing transaction. Final MCP reads its required injected clock after serialization, checks current membership/version/purpose/understanding/stop/consent/expiry/route, then writes reservation/observation/terminal together. Observation is not a callback or care.

[verified] SIGKILL after claim, after effect and before terminal receipt preserves one pending/unknown attempt and never redispatches. Separate processes prove stop/revoke committed first gives zero calls, and invocation first makes a later writer wait. Late success remains refused. Both stores implement the transaction/clock contract; actual Postgres behavior is unproven.

## Current evidence

[verified] Post-restoration suite: **1,869 passed, 54 Postgres skips, one existing Starlette warning**, exit 0. Frontend typecheck and production build pass. Final named run: **727 RED, zero SURVIVED/NOT PROVEN**, exact target restores. Every final mutation fingerprint, target backup and control-source hash matches current bytes. Current truthfulness: **39/39 RED**, passing before/after controls and exact restores. Named cases are not a count of distinct mechanisms; some cases cover different inputs to the same predicate.

[verified] Real authenticated HTTP/curl covers strict barrier/consent/request bodies, 401/404/409/422, truly unread request response followed by explicit replay, restart, failure callback and preserved patient/ledger state. One attempt remains after loss/replay. Fixed local fault HTTP returns 503 unavailable then 202 pending for identical replay, one invocation, no raw detail or false failure heading. Store failure never invents a receipt.

[verified] Visible Codex In-app Browser covers keyboard barrier error/selection, unchecked permission, decline, grant and separate request; pointer, Show/Tab/Escape opener restoration, reload/revoke and two tabs. The two-tab interval has one grant, one attempt/dispatch record, one revoke, and refused late acknowledgement. Actual transport selection persisted stop with zero attempts. Measured paragraph/heading fonts double from 20px/34px to 40px/68px. Observed 320px and 1280px views have no horizontal overflow. Browser version and full VoiceOver/zoom path remain unknown.

[verified] Twenty-seven stored cases were checked against literal step/deadline values before captures; API/SSR/RSC and actual browser family views agree. Five serialized forms per case give **135 captures and 2,970/2,970 positive scanner controls**, no misses. HTML-derived accessibility text is a bounded scan; actual DOM/AX observations are separate. Entry/recovery have separate captures. Later two-tab/transport interactions intentionally changed designated fixtures and do not relabel earlier captures.

## Findings corrected and historical proof failures

[verified] Review reproduced/fixed nested effect-before-commit rollback/redispatch, ToolError 500 mapping, pending action overriding terminal transfer, barrier feedback corrupting expiry/transfer, missing Literal request annotation and repeated barrier question. Barrier/consent receipts identify their actual referent types. The required tool-held clock interface and retired-action/internal-request docs now match the approved design.

[verified] First named run: 721 RED/five SURVIVED/zero NOT PROVEN, exact restores. New permission predicates masked five old fixtures; actual producer contexts now isolate those first refusals. Their separate proof is 5/5 RED. The second full run was 726/726 RED; a third was 727/727 RED after clock alignment. Truthfulness attempts stopped on retired anchors after 29 and 34 RED records. These incomplete/historical proofs are not combined into the current complete totals. The final named run uses the re-anchored truthfulness corpus.

[verified] First live matrix setups failed on shared callback/pending identities, inherited scenario clock and provenance mismatch. The final external driver isolates identities/clock and checks literal expected state before capture. A viewport request initially applied to another tab; only the measured 1280px observation is wide-layout evidence.

## Preservation, cleanup and limits

[verified] Exact Gate 1 copy/Gates 2-4, manifests and hosting configuration match preflight bytes. The protected video is now tracked at main and remains SHA-256 `cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`. Baseline was 1 failed/1,768 passed/51 skips because two credential-bearing sample DSNs were tracked. The user approved clearing exactly those assignments; no rotation/access/history rewrite occurred. Credential validity is unknown.

[verified] Architecture cleanup found no new production module orphan or proposed deletion. Internal module imports resolve; referenced fixtures/assets/old audit data remain. Existing public/legacy fixture types are retained. Required constructor migration also changes a deployment test fixture, without deployment/CI/config changes. All named processes were stopped; ports 8317, 8318, 8319 and 8320 are free, two temporary tabs closed and viewport reset. LF/no-added-em-dash/diff checks pass.

[unknown] Real Postgres concurrency/migration/restart remains Slice 19. Full accessibility and earlier Slice 15 blockers remain Slice 20. Live ADP profile/activation/positive extraction remains Slice 21. No clinical or participant-benefit proof, real provider/message, deployment, install, real configuration/credential change or Slice 18 is included. Clearing a worktree example does not remove prior Git history or rotate an active credential.

## Evidence and reproduction

[verified] Current full suite: `/tmp/carerelay-s17-final-suite.log`. Current named proof: `/tmp/carerelay-s17-full-named-4/`, 727 cases. Truthfulness: `/tmp/carerelay-s17-truthfulness-current3.log`, whose first line names its external backup directory. Typecheck/build: `/tmp/carerelay-s17-typecheck.log`, `/tmp/carerelay-s17-build-final.log`. Live HTTP/curl/fault/process/browser/scanner/source hashes: `/tmp/carerelay-slice17-live/`. Preflight: `/tmp/carerelay-slice17-preflight/`.

[verified] Existing runtimes are Node PATH `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`, Python `/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`. Use `PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local CARERELAY_API_TOKEN='' PYTHONDONTWRITEBYTECODE=1 CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled`, pytest `-o addopts='' -q` and a fresh basetemp. Run the named harness with `--run` only after source writers freeze; never run concurrent mutations or kill it. `--anchors-only` and default validation are not mutation proof. The current live source copy was independently byte-checked against final repository files.

Boundary: local Check ready for user acceptance. No commit/push or Slice 18 starts automatically.

## Acceptance and shipping update: 14 October 2026

[verified] After the local review session, the user accepted this bounded Check
and authorised committing the working tree and pushing to main, with a concrete
Slice 18 handoff for another agent. Main publication is verified; the dated
receipt is published within that same request. Statements
above describe the local review before acceptance; `00-status.md` owns current
state. No Slice 18 implementation or external authority follows.
