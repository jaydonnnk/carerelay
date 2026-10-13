# CareRelay: Slice 15 implementation handoff

Snapshot: 13 October 2026, Singapore time. This is an actionable implementation
prompt requested by the user, overriding the transfer skill's passive template.

## Shipping receipt

[verified] Slice 14 and its approved records/handoffs were committed, main was
safely fast-forwarded, and origin/main was pushed and verified against local main.
The receipt publication is part of the same request. Current checkout is main;
no Slice 15 branch or implementation exists. Only the unrelated untracked
`submission/usage-proof/Workbuddy_evidence.mp4` remains outside the shipped tree.
No slice branch was published. Source/frontend bytes remain the tested bytes.

## Completed and authority

Slice 14 completed its bounded local Check. The user then requested: "Push to
main and then give a copy paste prompt for slice 15". This authorises shipping
Slice 14 and its inherited approved records to main, and this next-chat handoff.
The shipping receipt in `00-status.md` records the verified result; recheck Git.
Slice 15 has not started in the shipping session. No new gate cycle is needed.
Gate 3's `JourneyBundle.episode_id` correction was explicitly re-approved with
"approve" after the two-empty-episode identity counterexample.

Recorded local evidence: 1,033 tests passed, 46 Postgres skips, one warning;
frontend typecheck/build; 63/63 current journey guard mutants and 39/39 existing
truthfulness mutants RED, plus one separate live production-render mutant RED.
38 malformed projections recovered in the actual browser; API/SSR/RSC/visible/
accessibility scans used positive controls. These are prior results to refresh,
not promises about Slice 15 or actual Postgres/ADP/deployed behavior.

## Session-specific traps

- Slice 14 intentionally returns 503 for assessed patient GET. Its decoder only
  accepts no-plan. Several old assessed outcome assertions now use the unchanged
  service serializer plus authenticated HTTP ledger/refusal checks. Slice 15 must
  restore complete assessed HTTP/browser proof; leaving those service checks as
  the only patient evidence is insufficient. See `test_api.py`, `test_truthfulness.py`,
  `test_fault_sequences.py` and `test_ledger.py`.
- `JourneyBundle` currently supplies only the tracer inputs: policies and
  restatements/commands are not enriched for assessed rendering. Implement the
  full coherent bundle, recorded-policy registry and transactional protocol.
  A registered policy row alone must not fabricate a disposition.
- `HintCard` deliberately exposes nothing. The legacy judge ledger still calls
  `createEpisode`; legacy patient writes remain until the Slice 15 command
  boundary replaces their bypasses. Neither is durable-start implementation.
- `/example` must keep fixed relative Location redirects. The original absolute
  redirect switched 127.0.0.1 to localhost, losing its host-only cookie.
- The operator installed frontend dependencies. Node 24.21.0, Next.js 15.5.27,
  Python 3.13.12 were observed. No .venv is needed. npm audit reports moderate
  Next and high transitive PostCSS package findings; no upgrade or forced fix is
  authorised by this handoff. Manifests/lockfile were preserved.
- Old slice-specific mutation scripts have retired UI anchors. Use current
  `_mutate_patient_experience.py` and `_mutate_truthfulness.py` for current guards;
  extend them with Slice 15's distinct guards rather than claim old totals.
- Local preview used 127.0.0.1:8140 and backend 8139 with disposable SQLite in
  the prior chat's work directory. Do not trust those processes as a fresh
  baseline. Evidence lives under
  `/Users/jayd0/Documents/Codex/2026-10-13/files-pasted-by-the-user-carerelay-2/work/slice14/`.
  No real credentials are needed. Do not read/use the repository's real .env.

## Prompt for New Chat

```text
Implement CareRelay Slice 15 only: explicit durable start and coherent stored
journey. Workspace: /Users/jayd0/Desktop/carerelay.

Read AGENTS.md and its required order, then
 docs/handoffs/patient-experience-slice15-2026-10-13.md
 docs/plans/urgent-advice-accessibility/00-status.md
 04-slices.md section 9: Slice 15, 9.2/9.3/9.5/9.6/9.8
 03-program-design.md section 9, including the re-approved 9.12 identity field.
Architecture revision 4 and section 5.2, Gate 1 copy and scenario remain binding.
Do not redo approved gates. This prompt authorises the local Slice 15 build,
its own main-based branch, disposable SQLite and fictional test data.

Verify current main, HEAD and live remote main, with tracked files clean.
A new untracked submission/usage-proof/Workbuddy_evidence.mp4 appeared during
shipping and was excluded; preserve it, do not stage/delete/publish it by inference. Slice 14 and the approved
records must already be on main. Inspect differences; never force, discard,
stash or silently carry unrelated work. Create slice-15-durable-start from
current main before editing; do not reuse the Slice 14 branch. If a branch
already exists, inspect it instead of resetting/recreating it.

Use carerelay-slice-build, then architect-reviewer at close. No installation,
real credential/config change, live ADP, production/disposable Postgres access,
deployment, outreach, new clinical copy, commit, merge or push is authorised.
The prior shipping request is exhausted. No Slice 16 work.

Implement the approved Slice 15 contract, not just the happy-path button:
- Explicit allowlisted create and intake as separate durable receipts; distinct
  intentional examples; same-candidate refresh/lost-response recovery. No automatic
  POST, retry, model call or dispatch on render/reload/revalidation.
- Exact additive journey_commands schema, append-only and phase/claim bindings,
  canonical digest/MAC bindings, event revision, atomic state/receipt writes and
  both-engine repository protocol. Preserve all fourteen old tables and history.
- Completed replay returns its historical result reference plus a fresh journey;
  changed body/stale unclaimed commands refuse, claimed-only is explicit pending.
  New IDs/tabs/tokens cannot create duplicate episodes/dispositions or bypass stop.
- Full pure twelve-screen/contradiction matrix, recorded policy A retained when
  configured B changes, unknown policy refuses. Expose only implemented commands.
  Stop, closure, expiry and owner remain independent. No public acceptance/handoff
  success selector, browser clinical derivation or stale-response repaint.
- Retire legacy patient-write and judge-ledger create-on-render bypasses as the
  command-backed boundary lands. Restore assessed HTTP/browser assertions alongside
  the preserved service/ledger truthfulness checks. No scoring, confirmation,
  new action execution or ADP integration in this slice.

Prove G02-G07/G09-G14/G16/G31/G36/G37/G38 separately per guard/token dimension,
constraint and surface. Seed old histories, apply DDL twice, reopen and compare
bytes/deadlines. Exercise crash atomicity, dropped create/intake responses,
double taps, two tabs, intentional second example, missing/rotated locator,
malformed/stale projection and fresh-process reads. Mutation controls must pass
before/after, with real assertion failures and byte-exact restoration. Back up
untracked targets outside the repo; never kill a running mutation harness.

Use the existing external interpreter:
/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python
Set PYTHONPATH=src, APP_DATABASE_URL=:memory:, APP_CLOCK=scenario, APP_ENV=local,
CARERELAY_API_TOKEN='', PYTHONDONTWRITEBYTECODE=1, and explicitly set
CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled after verifying port
1 is closed. Run pytest tests -o addopts='' -ra with a fresh /tmp basetemp.
Never inherit a real DSN. Pure parity tests must run; engine skips are unproved.
Recheck installed frontend tooling; run typecheck/build and actual production-code
browser checks with synthetic local auth, exact URL/port, keyboard/retry/320px and
API/SSR/RSC/visible/accessibility scanner-positive controls. Mockups are not proof.
Keep scenario 30 September 2026 and its stored 18:00 SGT deadline; no invented
current-date copy. Real Postgres proof remains separately authorised Slice 19.

Update authority and mirrors from actual evidence. Stop and reopen the owning
gate for a contract falsifier rather than bypassing it. Finish Slice 15's visible
Check and architecture cleanup, report limits, then ask:
"Continue to slice 16, or re-steer?"
Do not begin Slice 16; its confirmation-copy and later integration gates remain.
```

## Optional handoff review

Review this handoff against Gate 4's Slice 15 row and Gate 3 section 9. Be unbiased,
honest and thorough; assume claims may be flawed. Verify shipping refs and approval
receipts, stress-test replay/identity/stop/migration/exposure boundaries, and flag
weak or unproved tests. Do not pass tests for the sake of passing. This review
alone authorises no implementation, installs, live services, mutation or shipping.
Report PASS / ISSUES FOUND / FAIL with precise file/line evidence and corrections.
Deliver your verdict and wait for instructions.
