# CareRelay: Slice 14 then Slice 15 implementation handoff

Context: 13 October 2026, Singapore time. This is the actionable handoff the
user requested, rather than the transfer-context skill's passive wait prompt.

## Completed in this session

[verified] Gate 4 section 9 is prepared and explicitly RE-APPROVED. The user
answered: "Yep i approve, now the handoff prompt for the next agent to start slice 14 and 15 please."
Gate line, checklist/history and supporting mirrors record this decision.
No upgrade implementation, application test run, live ADP or database proof was
performed. No slice is marked complete. No commit, merge or push occurred.

[verified] The prior documentary checks preserved code/tests/mockups and Gates
1/2/3, copied all 38 Gate 3 verification rows exactly, and checked slice arithmetic.
These are documentary results, not passing runtime evidence. The first heading
counter included historical slices; corrected and logged in `tasks/lessons.md`.

## Session-specific traps and remaining dependencies

- The approved Gate 4 amendment and its approval mirrors are still dirty files
  on the documentation branch. Main does not contain them yet.
- Slice 14 must precede Slice 15. Each has its own main-based branch. No Git
  shipping authority was given, so Slice 14 reaching main is a later dependency.
- [verified] This checkout has no `.venv` or `frontend/node_modules`. The external
  Python 3.13.12 interpreter exists; Node/npm commands are available. Current
  package/lockfile exist. This is not proof that frontend checks can run now.
- The build skill's install/venv/CRLF defaults are stale for this checkout.
  Repository/user authority requires no agent installs and current byte endings.
- [hypothesis] Slice 14: 4 to 7 hours. Slice 15: 14 to 23. Combined: 18 to 30,
  unmeasured, excluding operator setup and Git handoff delay. No date promise.

## Files changed for the handoff

- `docs/plans/urgent-advice-accessibility/00-status.md`: Gate 4 approval line,
  dated approval/history/checklist, unstarted slices and current handoff.
- `docs/plans/urgent-advice-accessibility/04-slices.md`: approval metadata only;
  approved section 9 slice/guard/effort contracts remain unchanged.
- `AGENTS.md`, `docs/PLAN.md`, `docs/DESIGN_PRINCIPLES.md`, `tasks/todo.md`,
  `patient-experience-upgrade.md`, `adp-and-deployment-impact.md` in the authority
  folder: current approval/scope/Git/environment receipt replaces pending note.
- `PROGRESS.md`: operational handoff checklist, not gate authority.
- `tasks/lessons.md`: current support-file discovery correction; no engine called.
- This handoff is new and untracked until separately authorised Git shipping.

## Prompt for New Chat

```text
Implement CareRelay Slice 14 first, with Slice 15 as the next scoped target.
Workspace: /Users/jayd0/Desktop/carerelay
Snapshot: 13 October 2026, Singapore time.

AUTHORITY
The user explicitly approved Gate 4 and requested this implementation handoff:
"Yep i approve, now the handoff prompt for the next agent to start slice 14 and 15 please."
00-status.md records Gate 4 section 9 RE-APPROVED. Gates 1/2/3 remain approved.
This prompt starts the local Slice 14 build. Slice 15 follows Slice 14's verified
Check, architecture cleanup, continue-or-re-steer checkpoint and authorised Git
handoff into main. Do not start Slice 16 or collapse the two slices.

No commit, merge, push, installation, real credential/config change, live ADP,
production/disposable Postgres access, deployment, outreach or submission is
authorised by this prompt. Local disposable SQLite and fictional test data are
within the slice. Mockups/approved clinical-policy/copy are preserved.

READ FIRST
Read AGENTS.md and its required read order. 00-status.md owns gate/slice state.
Authority folder: docs/plans/urgent-advice-accessibility/
Use 04-slices.md section 9 as the approved build sequence, specifically:
- Slice 14 and Slice 15 rows: exact files, visible result, entry/exit and exclusions.
- 9.2 exposure/dependency rules; 9.3 common exit discipline.
- 9.5 guard allocation, including all separate mutations within each row.
- 9.6 actual-browser obligations; 9.8 owning-gate falsifier protocol.
Use approved 03-program-design.md section 9 for exact types/signatures, call
stacks, no-plan/contradiction matrix, token/transaction/migration contracts.
02-architecture.md revision 4 section 13 and section 5.2 remain binding.
01-product.md and patient-experience-copy.md own exact strings.

Use /Users/jayd0/.agents/skills/carerelay-slice-build/SKILL.md for each build.
At each slice close use /Users/jayd0/.agents/skills/architect-reviewer/SKILL.md.
Resolve skill defaults against current repository/user instructions: no installs,
no memory writes without a direct request, use current LF/CRLF per file, and
verify the available interpreter instead of creating a .venv. Refusal is not
automatically a durable clinical stop; preserve the approved receipt/stop rules.

GIT PREFLIGHT AND INHERITED WORK
Last verified HEAD/main/live remote main and program-design branch:
1a8fff92edaadeddd49d42e6ce0db5d8fe2a3bfb.
Current branch: codex/patient-experience-slice-plan. Gate 4 is NOT committed.
Dirty files: AGENTS.md, PROGRESS.md, docs/PLAN.md, docs/DESIGN_PRINCIPLES.md,
tasks/todo.md, tasks/lessons.md, and authority-folder 00-status.md, 04-slices.md,
patient-experience-upgrade.md, adp-and-deployment-impact.md. This handoff is new.
Recheck rather than trusting this snapshot:
    git status --short
    git branch --show-current
    git rev-parse HEAD main
    git ls-remote --heads origin main codex/patient-experience-program-design
Snapshot inherited dirty/untracked bytes outside the repo before changing
branches. Never reset/stash/discard/stage unrelated changes. Create
slice-14-journey-tracer from current main before its first implementation edit;
preserve/recheck the inherited approval records and code bytes through checkout.
If branch/state differs or Git refuses, inspect rather than force-recreate.

After Slice 14, do not silently commit/merge it to enable Slice 15. The approved
plan says "If prerequisite slices are not on main, stop for the authorised
handoff" and AGENTS.md requires each slice branch from current main. Request
only the missing Git authority when the verified result is reviewable. Once
that handoff is authorised/executed and checked, create slice-15-durable-start
from updated main. Never carry uncommitted Slice 14 code onto a branch from
old main or start Slice 15 on the Slice 14/documentation branch.

SLICE 14: MINIMAL VISIBLE NO-PLAN TRACER
Implement only its approved file/exit scope. Remove create-on-render and
pre-disposition fixture leakage at patient API/options/MCP/bare root. A real
no-disposition record has null plan/outcome/versions/owner aliases, false care,
empty lines/options and no scoring/action question or command. Unknown ID is
404/recovery. Bare FastAPI root redirects to the trusted frontend without
guidance or caller-selected redirect. Bootstrap may issue the signed candidate
locator, but creates no episode; the start mutation is not offered yet.
Thin renderer/runtime decoder shows approved entry/recovery copy. Refresh and
hint revalidation make zero POST/model/dispatch calls. Until assessed projection
is implemented, refuse to approved recovery rather than invent partial guidance.
No command-table migration, intake, scoring, consent/hint mutation or request.

Prove G01/G06/G07/G09 and no-plan G31/G37/G38 at their named surfaces, with
good-case controls and separate fallback/decoder/scanner mutations. A scanner
must detect injected needles on that same API/SSR/RSC/visible/accessibility
surface first. Cookie bootstrap controls belong here; the start-precondition
mutation requires actual creation in Slice 15. Show authenticated curl JSON and
the real production-code browser at a recorded local URL/port, keyboard Try
again, 320 CSS pixels/enlarged text, unknown/blocked API/bootstrap and zero POSTs.
Mark complete only after the full approved Check. Show result, update authority
and mirrors, invoke architecture cleanup, then stop for:
"Continue to slice 15, or re-steer?"
The user has named Slice 15 as the next target; this preserves the approved
visible checkpoint and the separately required main/Git handoff.

SLICE 15: DURABLE START AND COHERENT STORED JOURNEY
After those prerequisites, implement explicit allowlisted create plus intake,
distinct intentional examples and same-candidate reload/lost-response recovery.
Pair each mutation with the exact additive journey_commands schema/append-only
constraints, claimed/completed receipts, canonical digest/MAC bindings, event
revision and coherent both-engine repository protocol. Never cache replay prose:
completed replay returns its historical result reference and a fresh projection.
Changed body/stale unclaimed command refuses; pending is explicit; no auto retry.
Create and intake remain separate receipts; neither lost response creates v2.
Preserve all fourteen old tables/rows/triggers and existing truthfulness guards.
Recorded policy A stays A when configured B changes; unknown policy refuses.
Implement the full pure twelve-screen/contradiction matrix with trusted stored
fixtures, exposing only already implemented commands. Stored stop/outcome/expiry
remain independent; acknowledgement/unknown is neutral. No public caregiver
acceptance/handoff success control, no browser clinical derivation or stale repaint.

Prove the Slice 15 allocation: G02-G07/G09-G14/G16/G31/G36/G37/G38, separately
per token dimension, predicate/command filter, migration constraint and surface.
SQLite: seed old no-plan/active/stopped/expired/accepted/handoff histories; apply
DDL twice, reopen fresh, compare bytes/deadlines; seed matching rows for trigger
positive controls. Crash state/receipt writes, drop responses after create/intake
commit, double-tap, two tabs, explicit new example, rotation/missing locator,
malformed projection and restart. API/browser must agree on exact text/axes/
stop/current owner/original deadline. Current Postgres implementation/parity is
not actual engine proof; authorised disposable-engine work remains Slice 19.
No confirmation/scoring/repair, new action execution, ADP or hosted rollout.

ENVIRONMENT AND VERIFICATION
Verified executable: /Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python
Python was 3.13.12; dependency module specs were found, not a fresh full suite.
Recheck imports and tool availability. No .venv/frontend node_modules exists
in this snapshot. Complete manifests already exist. Operator-only setup command:
    npm --prefix /Users/jayd0/Desktop/carerelay/frontend ci
Do not execute it without separate install authority. Report this dependency
early and continue independent in-scope backend work; don't fake build/browser
completion. If an existing compatible toolchain can be reused without installing,
verify it before claiming checks passed. Lockfiles/config are preserved.

Use fresh baselines and relevant full suite, not the recorded 12 October figures.
Example offline test invocation, with an explicitly closed loopback fixture DSN
to prevent accidental fallback to a real Postgres (verify port 1 is closed first):
    PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local \
      CARERELAY_API_TOKEN='' CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled \
      PYTHONDONTWRITEBYTECODE=1 \
      /Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python \
      -m pytest tests -o addopts='' -ra --basetemp=/tmp/carerelay-slice14-baseline
Use a fresh per-run basetemp and inspect engine skip reasons. Pure parity tests
must run; resource skips are unproven, not successful engine evidence. No test
may use ambient APP_DATABASE_URL/real CARERELAY_TEST_DSN by convenience.
After new files exist, run focused journey/command/API/service/boundary tests,
each mutation alone with actual assertion failures and passing pre/post controls,
then relevant full suite. Back up untracked targets and restore byte-exact; don't
kill the harness or count collection/import/missing-anchor errors as RED.
If frontend tooling is available, run its existing typecheck/build commands and
actual browser paths. Authenticated live curl uses synthetic local test auth,
never a real credential. Finish with git diff --check and scope/secret/byte review.

CLAIMS AND STOP CONDITIONS
945 passed/46 Postgres skips/one warning and 39/39 mutations are recorded 12
October results, not today's baseline. Slice 9 study was cut, not passed; old
Slice 13 was never built. No study restart or benefit/clinical/WorkBuddy-runtime
claim follows. ADP is absent from the app; these two slices do not wire it.
Keep scenario 30 September 2026 and its stored deadline; no new date/copy,
bare-tomorrow interpretation or confirmation-control approval is supplied here.
If the approved contract itself is falsified, record the exact counterexample,
reopen its owning gate and stop for re-approval. No permissive workaround or
dropped proof to fit the estimate. A missing tool blocks its Check, not a licence
to mark the slice complete. Stop after Slice 15's visible Check/cleanup/report;
request further scope only through its continue-or-re-steer boundary.

Begin with current-state/tooling/Git preflight and Slice 14. Do not redo gates.
```

## Prompt for Handoff Review

```text
Review the CareRelay Gate 4 approval receipt and Slice 14/15 implementation handoff.
Workspace: /Users/jayd0/Desktop/carerelay. Read AGENTS.md and controlling gate docs.
Gate 4 section 9 was approved 13 October; no implementation is claimed in the
handoff session. Approval/scope mirrors are dirty on the documentation branch,
and no commit/merge/install/database/ADP/deployment authority was given.

Be unbiased and thorough; assume the handoff may be flawed. Check the actual
approval line/checklist/history, unchanged Gate 1/2/3 contracts and preserved
Gate 4 build/guard/effort sections. Stress whether Slice 14 truly remains read-only
and Slice 15 has its replay/stop/snapshot/migration boundaries before exposure.
Check the inherited-tree/main-based branch dependency and missing frontend
tooling; the prompt must not imply unavailable checks passed or authorise Git
shipping/install by inference. Verify documentary claims against bytes, not
approval as an oracle. Do not pass checks for the sake of passing; flag weak,
trivial or unverified proof and concrete shortcuts.

Read-only review only: no mutation, runtime suite, engine/ADP call, installation
or implementation. Report PASS / ISSUES FOUND / FAIL with specific file/line
evidence, severity and concrete correction. Deliver your verdict and wait for
instructions.
```
