# Slice 21 schema-compliance handoff: 16 October 2026

[verified current-state pointer, 16 October 2026] Historical handoff, superseded for continuation by `00-status.md`. Confirmation-copy approval, the accepted disposable PostgreSQL proof and positive ADP product extraction are complete. Slice 21 is now accepted by bounded closure with seven live cases unrun. Preserve this history; do not restart its old pending work or infer new calls/shipping authority.

Supporting handoff. `docs/plans/urgent-advice-accessibility/00-status.md` owns gate and slice state.
This supersedes the 15 October continuation handoff on current facts only.
Slice 20's user-directed closure and its disclosed proof limits are preserved.

## The problem in one paragraph

[verified] The integration is built and fails closed through the actual local product, but no live ADP reply has ever been scored there.
The original model (Tencent Hy3) followed the schema but was too slow: three of five calls passed the 15-second cap.
After the operator switched to a faster non-reasoning model (name unknown), replies arrive in 6 to 11 seconds but break the schema.
Calls 14 and 15 (v1 schema) gave wrong offsets (`span_source`).
Under the approved span-text v2 schema, call 16 had a non-string field value (`span_text_type`) and call 17 lacked exactly the six keys (`object_keys`).
Raw model output is deliberately never persisted, so nobody has seen what the fast model actually returns.

## Current state

- Branch `slice-21-adp-enablement`, uncommitted, from published main `41db105`. Preserve every dirty and untracked file.
- Gates 2, 3 and 4 carry three approved Slice 21 amendments: 15-second live cap; 20-second frontend scoring timeout; span-text v2 (model returns phrase text, code locates one word-bounded exact occurrence, none or several is uncertain).
- Instruction `carerelay-readback-instruction-v2` is published AND active by operator report. Text: `submission/adp-agent-instruction.md`.
- Offline: 2,109 passed, 232 PostgreSQL skips, one warning. 159 named adapter/Slice 21 mutations RED with exact restores (`tests/_mutate_patient_experience.py`).
- Live ledger: 17 of 24 fictional calls used, 7 remain. `/tmp/carerelay-s21-implementation-20261015/live-call-ledger.json`.
- ADP is default-off. No Slice 21 commit, merge, push or deployment is authorised.

## Recommended angle: see the reply before changing anything

1. **Zero-call diagnosis.**
   Write a small local script that prints, without any credential, the exact server prompt `AdpReadbackExtractor.extract` sends for a fictional sentence (reuse its code path, not a copy).
   Ask the operator to paste that text into the ADP console's own test or Experience chat three times and report the raw reply shape.
   That uses the operator's console, not the 7 remaining product calls. Fictional words only.
2. **Read the vendor docs for a structured-output feature.**
   Look for a JSON mode, response format, output schema or workflow output variable in Tencent ADP for this app type.
   Use primary docs; record each claim as [vendor claim] until observed.
3. **Check prompt agreement.**
   The server prompt in `src/carerelay/adp_extraction.py` and the published v2 instruction both describe the schema.
   Confirm they never conflict (keys, wording, examples) and that the prompt does not invite the model to echo `correlation_id` or `instruction_version` as keys.
4. **Then choose one fix, with the user:**
   - instruction or server-prompt wording fix, if the reply shape shows a consistent wrapper or renamed key;
   - a vendor structured-output setting, if it exists and is observed to work;
   - back to the original model with a narrow live-cap amendment, if the fast model cannot hold the schema.
   Any schema or cap change needs a prepared Gate 2/3/4 amendment and explicit user approval first.
5. **Optional, content-free observability:** extend the bounded diagnostic pattern used for `span_text_type:<field>:<type>` to `object_keys`, recording only which of the six schema keys are missing and a count of extra keys, never the model's own key names or values. Prove it failing-first with a mutation.

## Rules that do not change

- 2,048 input code points, 16 KiB answer/frame, 64 KiB wire, 15-second live cap, one call, no retry, no lexical fallback, default-off, fresh sessions.
- Code alone decides comparison, guidance, deadlines, permissions and closure. Action origin stays `local-sim`.
- Never read or print `.env` values; load only `ADP_APPKEY` and `ADP_CHAT_ENDPOINT` privately into a child backend process.
- Every live call is reserved in the ledger before it is sent and counted even if lost.
- Use disposable SQLite, scenario time, loopback URLs, synthetic local token. No hosted database, desktop control or VoiceOver.
- Protect `submission/usage-proof/Workbuddy_evidence.mp4` (SHA-256 `cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`), `vibe_images/` and `submission/workbuddy_usage.txt`.
- No em dashes in new writing.

## Evidence and tools

- Product harness: `/tmp/carerelay-s21-product-20261015/harness/` (`launch_backend.py`, `launch_frontend.py`, `corpus.mjs`, `cdp.mjs`, `ledger.py`, `run_one.py`, `product_ledger.py`, `secret_scan.py`, `safe_stop.py`). Temporary files may disappear; regenerate rather than claim.
- Production frontend build copy: `/tmp/carerelay-s21-product-20261015/frontend-build/`.
- Observations: `docs/reviews/adp-readback-observations.md`. Approved v2 proposal: `docs/reviews/slice21-span-text-amendment-proposal.md`.
- Python: `/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python`. Node: `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin/node`.
- Offline suite:

```bash
env PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 APP_DATABASE_URL=:memory: APP_ENV=local APP_CLOCK=scenario CARERELAY_API_TOKEN= ADP_APPKEY= ADP_CHAT_ENDPOINT= ADP_EXTRACTION_ENABLED=false CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled /Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python -m pytest tests -o addopts='' -q
```

## Copy-paste prompt for the next agent

```text
Continue CareRelay in /Users/jayd0/Desktop/carerelay, Slice 21 only, on the existing uncommitted branch slice-21-adp-enablement. Preserve every dirty and untracked file.

Read in full first: docs/handoffs/patient-experience-slice21-schema-compliance-2026-10-16.md, then AGENTS.md, then the Slice 21 sections at the top of docs/plans/urgent-advice-accessibility/00-status.md, then docs/reviews/adp-readback-observations.md.

Problem: the live ADP read-back integration is built and fails closed through the real local product, but no live reply has ever been scored. The original model followed the schema but missed the 15-second cap in three of five calls. The faster model now active replies in 6 to 11 seconds but breaks the schema: wrong offsets (calls 14, 15), then under the approved span-text v2 schema a non-string field (call 16, span_text_type) and a wrong key set (call 17, object_keys). Raw model output is never persisted, so nobody has seen what the fast model returns.

Take a different angle from repeating product calls. First diagnose without spending any of the 7 remaining calls: build a credential-free local script that prints the exact server prompt the production adapter sends for one fictional sentence, and ask me to paste it into the ADP console test chat and report the reply shape. In parallel, check Tencent ADP primary documentation for a structured-output, JSON-mode or response-schema feature, labelling claims [vendor claim] until observed, and confirm the server prompt and the published v2 instruction never conflict. Then recommend exactly one fix with evidence: a wording fix, a vendor structured-output setting, or returning to the original model with a narrow live-cap amendment. Any schema, cap or contract change needs a prepared Gate 2/3/4 amendment and my explicit approval before you apply it.

Spend no live product call until I approve a specific plan and call count. Every live call must be reserved in the existing ledger before sending, with no retry, and stop at the first failure. Keep all byte limits, the 15-second cap, one call, no lexical fallback, default-off configuration and code authority over comparison, guidance, deadlines, permissions and closure. Never read or print .env values or ask for secrets. Use disposable SQLite, scenario time and loopback only. No VoiceOver, desktop control, hosted database, commit, merge, push or deployment.

Record results honestly in 00-status.md and the observations review, with failing-first tests and named mutations for any code change. Stop for my decision or for Slice 21 Check acceptance.
```
