# Session Transfer: CareRelay Gate 2 to Gate 3

**Historical handoff, superseded at the next checkpoint. [verified]** Gate 3
section 9 was subsequently prepared and re-approved on 13 October. The user
then authorised documentation shipping and a Gate 4 continuation prompt. Current
authority is `00-status.md`; current handoff is
`patient-experience-gate4-2026-10-13.md`. The earlier dirty-state and unprepared
Gate 3 statements below describe this handoff's original snapshot only.

Date: 13 October 2026, Singapore time.

The user requested an actionable continuation prompt in the original assignment
format. That explicit request determines the continuation block below. The
separate review block is optional and does not authorise continuation work.

## Completed

- [verified] Gate 2 revision 4 was prepared and explicitly re-approved by the user: "Yep i approve gate 2". `00-status.md` records the decision.
- [verified] Documentary checks passed. The 81 preserved hashes cover the
  inspected source/frontend/test/mockup and Gate 1/3/4 files; section 5.2 stayed
  unchanged. This is preservation evidence, not runtime proof.
- [verified] Approval mirrors and the Gate 3 handoff are prepared. No new code,
  application tests, commit, push, installation or deployment occurred.

## Decisions

- [verified approval] Existing patient read gains authoritative journey data,
  avoiding a second patient-state API and browser interpretation of sentences.
- [verified approval] Explicit start/no-plan and stable resume distinguish stored
  facts from the old synthetic fixture projection.
- [verified approval] One append-only command record gives request replay an
  atomic database boundary; attempt keys still prevent a fresh booking dispatch.
- [verified approval] Field-only repair retains same-version confirmed matches,
  with whole-answer contradiction checks; it cannot borrow expected answers.
- [verified approval] ADP is read-back extraction only; domain canonicalisation
  and local simulated action execution retain their own boundaries.
- [unknown] Whether these mechanisms are implementable and sufficient under all
  relevant races/language cases remains unproved; Gate 3 must expose gaps.

## Traps

- The approved amendment is uncommitted. HEAD and GitHub main do not contain it.
  Starting fresh from main or discarding the dirty tree would lose the decisions.
- Gate 3/4 old approvals do not authorise the upgrade. Slice 13’s unbuilt
  intake/classification contract does not cover the approved read-back role.
- Approval is not validation. Twelve mapping rows and preserved hashes are not
  twelve correct runtime paths; historical green tests are not fresh results.
- The published ADP action-ID schema is incompatible, positive extraction is
  unproved, and the local action origin cannot become platform just because an
  ADP interpreter is added.
- The prior temporary verification helper encodes Gate 2’s then-pending state.
  Its old state assertions are not the approval authority.
- One inherited U+2014 was retained on an edited table line, caught by preflight,
  corrected and logged. Current checkout uses LF; byte-preservation checks matter.

## Working Agreements

- This user explicitly approved Gate 2 and requested the next agent to prepare
  Gate 3 now, using an actionable prompt like the original assignment.
- The handoff is honest about approved design, actual code and unverified proof.
  No review verdict or user approval substitutes for runtime evidence.

## Files Changed

Ranges below describe this session’s working-tree diff against HEAD. Paths are
relative to `/Users/jayd0/Desktop/carerelay`; exact ranges may move on later edits.

- `docs/plans/urgent-advice-accessibility/02-architecture.md:3-48,443-770`:
  current source/evidence snapshot, revision 4, D14 to D18 and explicit approval;
  narrow earlier rows reconcile storage/auth/provenance facts.
- `docs/plans/urgent-advice-accessibility/00-status.md:4,14-58,83,668-672,1270`:
  gate line, checklist/history, next Gate 3 boundary and document/slice map.
- `AGENTS.md:3-23,118-120,190-194,383-385,531-533`:
  current scope/approval mirrors, source/config corrections and writing guard.
- `docs/PLAN.md:3-23,61-64,450-455` and `tasks/todo.md:3-23,48-57`:
  approved architecture, later gates and current approval checklist.
- `docs/DESIGN_PRINCIPLES.md:3-12`:
  approved scope with unproven platform/benefit boundaries.
- `docs/plans/urgent-advice-accessibility/patient-experience-upgrade.md:1-27,201`:
  amendment/approval, current gaps and later manual dependencies.
- `docs/plans/urgent-advice-accessibility/03-planback-closure-contract.md:3-17`
  and `docs/plans/urgent-advice-accessibility/adp-and-deployment-impact.md:4-16`:
  copy/ADP scope reconciliation.
- `PROGRESS.md:112-147`: operational evidence and handoff checklist only.
- `tasks/lessons.md:63-64`: punctuation preflight failure and prevention.
- This file: session digest, actionable Gate 3 prompt and separate review prompt.

## Open Work

- [verified status] Gate 3 upgrade contracts are not prepared. Gate 4 upgrade
  slices depend on their approval; neither existing contract was edited here.
- [verified status] Production journey/ADP integration is unbuilt. Live ADP
  positive interpretation and Postgres stop/dispatch proof are unestablished.
- [verified status] Submission assets/usage-proof files exist but need review
  against new evidence; clinical and participant claims remain unsupported.

---

## Prompt for New Chat

```text
Prepare the Gate 3 program-design amendment for CareRelay’s patient-experience upgrade and approved ADP read-back integration.

Workspace: /Users/jayd0/Desktop/carerelay
Context snapshot: 13 October 2026, Singapore time.

Read AGENTS.md and follow its required read order. Use the software-factory skill at:
/Users/jayd0/.agents/skills/software-factory/SKILL.md

CURRENT STATE
[verified] The user explicitly approved Gate 2 revision 4 on 13 October: “Yep i approve gate 2”. The approval, checklist and history are recorded in 00-status.md. Gate 1 remains re-approved for the twelve concise HTML screens and their exact copy.

Gate 3 and Gate 4 still carry their previous approved contracts. Neither has been amended for this upgrade. This assignment is Gate 3 preparation, not implementation or Gate 4 planning.

[verified snapshot] Current branch: codex/patient-experience-architecture.
HEAD: aca4594485f3e465daa461bf8139033458b2b81c.
Local/remote main matched that commit when checked on 13 October.

The working tree is DIRTY: approved Gate 2 documentation, its approval mirrors and this handoff are uncommitted. The new architecture is not on GitHub main. Recheck git status and preserve all existing work. Create codex/patient-experience-program-design from the current checkout, carrying those edits forward; do not reset, stash, discard or stage them. If branch state differs, inspect before changing it.

This assignment authorises that documentation branch and Gate 3 preparation. It authorises no commit, merge, push, install, credential change, live ADP call, database mutation, deployment or participant outreach. The earlier shipping request is complete.

PRODUCT CONTEXT
CareRelay helps older adults and caregivers answer:
1. What must I do, and by when?
2. Can I actually do it?
3. Has someone agreed to help, or is it unresolved?

PlanBack compares confirmed read-back and repairs specific misunderstandings. The Closure Contract preserves the deadline and separates attempts, acceptance, successful handoff and evidence. This remains a scripted research demonstration using fictional services. It provides no validated symptom assessment. Benefit over a clear instruction card remains unproven.

WHAT IS COMPLETE
[verified] Work through Slice 12 and backend truthfulness repairs shipped before this amendment. The Slice 9 participant run was cut, not passed. Conditional Slice 13 was never built.

Gate 1’s prototypes and copy are approved. The production journey is not rebuilt. Gate 2 revision 4, especially section 13, is now approved architecture; this is approval of design, not proof that its mechanisms work.

[verified recorded results, not fresh checks] The 12 October record reports 945 passed, 46 Postgres skips and one existing warning; the repair report records 39/39 truthfulness mutations RED. This architecture session ran documentary/preservation checks, not the application suite, live ADP probes or a Postgres engine.

READ THESE SESSION ARTIFACTS
Authority folder:
/Users/jayd0/Desktop/carerelay/docs/plans/urgent-advice-accessibility/

Key files within it:
- 00-status.md: Gate 2 approval and current scope.
- 02-architecture.md: revision 4; section 13 is the upgrade architecture. Preserve section 5.2’s previously approved durable-stop rule.
- 03-program-design.md: existing Gate 3 contract to amend, not replace wholesale.
- 04-slices.md: existing Gate 4 contract; leave it unchanged during this assignment.
- 01-product.md and patient-experience-copy.md: approved product/copy boundaries.
- patient-experience-upgrade.md: prior gap reconciliation and manual dependencies.

Mockups: /Users/jayd0/Desktop/carerelay/design/mocks/patient-journey/
Repair evidence: /Users/jayd0/Desktop/carerelay/docs/reviews/truthfulness-repairs-2026-10-12.md
ADP observed limitations: /Users/jayd0/Desktop/carerelay/submission/adp-agent-instruction.md
Canonicalisation decision: /Users/jayd0/Desktop/carerelay/docs/adr/0007-canonicalisation-lives-in-domain.md

ACTUAL APPLICATION GAPS
[verified by prior source inspection; recheck]
- api.py creates the shared demo-episode-001 ID and returns fixture.demo_lines() before a disposition exists. The bare FastAPI / also renders fixture guidance.
- frontend/app/page.tsx creates on every render. Its API type lacks the structured journey data, including existing closure/evidence fields.
- /options returns policy routes without a disposition. Separate reads do not establish one consistent journey snapshot.
- repair_restatement scores the repair text as a whole plan; timing-only answers need the approved same-version field-retention rule.
- The app constructs LocalSimulationCoordinator. Action origin remains local-sim. ADP is separate, and its published schema is incompatible with the approved raw-span/uncertainty boundary.

These are gaps to design for, not evidence that the shipped truthfulness repairs failed. Do not revive the old “not yet fixed” repair list.

YOUR GATE 3 DELIVERABLE
Inspect the actual code, then amend 03-program-design.md with exact files, types/signatures without implementation bodies, call stacks, migrations, fail-capable test cases, least-confident decisions and an evidence-bounded effort estimate.

Resolve these programming contracts explicitly:

1. Authoritative journey projection
Define nullable no-plan fields, episode/disposition/policy identity, durable revision, action/deadline/timezone, original and current owner, independent outcome/stop data, one next question, allowed choices/commands and approved text. Map all twelve screens and contradictory state combinations to those values. Use the recorded policy version. No browser inference or sentence parsing; no answer leakage into unaided read-back.

2. Start, resume and request replay
Specify how the locator/start nonce reaches the browser before any backend mutation, how intentional examples obtain distinct IDs, and how a lost create response reuses the same episode. Define the append-only journey_commands claim/terminal receipt, atomic application, body-digest conflicts, pending/crashed claims and fresh projection on replay. No create-on-render, automatic redispatch or client-invented request purpose.

3. Read-back and field-only repair
Define explicit confirmation, latest-parent/version binding, retained known matches, whole-answer contradictions, cue provenance across show/hide/reload, uncertain versus definite mismatch, repair consumption and the two-repair/H3 stop rules. Never fill missing fields from the expected plan. Only timing-repair copy is explicitly illustrated; other field-specific strings need Gate 1 approval before exposure.

4. ADP extraction boundary
Confirmed fictional words → ADP extraction → deterministic CareRelay comparison.
Define the strict versioned raw-span/offset/uncertainty/refusal schema, stream-envelope handling, exact source grounding, independent negation/correction checks and provenance. Domain owns canonicalisation; the model receives no expected disposition or answer pairing.

The approved starting limits are a five-second whole-response budget, no automatic retry, 2,048 input characters and 16 KiB assembled answer. They are unmeasured engineering choices. Timeout, refusal or invalid output stays unscored and consumes no repair. No silent lexical fallback presented as ADP.

Keep ADP separate from action execution. It cannot choose urgency, book, write patient guidance, transfer responsibility or declare care arranged. No provider reasoning reaches the patient.

5. Transactions and permission boundaries
Specify coherent snapshot/revision reads, atomic receipt/state writes, no DB lock held across ADP calls, and post-extraction stop/version/parent/deadline rechecks. Define SQLite and Postgres episode serialization for stop/consent versus final simulated-provider invocation, crash windows and late callbacks. Dispatch already begun cannot be undone; do not promise exactly-once external effects.

Preserve server-held credentials, current provider-sharing consent, evidence-ingestion refusal and the approved durable-stop rule at service/MCP entry points. An episode locator is not authentication. Shared-token actors remain simulated; no new public control may impersonate an accepting caregiver or successful handoff.

6. Verification and migration contracts
For each new guard, name the concrete counterexample, observable serialized result, test and single-guard mutation that would falsify it. Include scanner detection controls, same-episode reload, duplicates/lost responses, malformed projection, field repair, hint honesty, ADP positive/negative/invalid/timeout cases and disposable-Postgres races/restarts.

Separate offline deterministic tests, live ADP observations, actual Postgres proof and browser/accessibility checks. Planned checks are not passing results. Cover keyboard, focus/dialog restoration, 320 CSS pixels, enlarged text/zoom and screen-reader status/errors. No participant benefit or clinical-safety claim follows from engineering checks.

HONEST REVIEW BOUNDARY
Be unbiased, honest and thorough. Treat approval as design authority, not a correctness oracle. Challenge hidden assumptions and find the smallest sufficient contracts. If actual code or a counterexample invalidates an approved Gate 1/2 decision, document the falsifier, reopen the owning gate and stop for its re-approval. Do not silently repair architecture inside Gate 3 or rationalise a defect away.

Reopen Gate 3 in 00-status.md when amending its document. Mirror changed decisions wherever supporting records carry them. Preserve Gate 1 copy and Gate 2 semantics; do not change Gate 4 contracts or write implementation/tests/migrations yet.

LATER MANUAL DEPENDENCIES
Gate 3 drafting needs no credentials or installation. Later ADP enablement requires an operator to revise/publish/activate the compatible instruction, check knowledge-base/tool settings and exercise positive extraction plus refusal/negation probes. The backend configuration and explicit enablement flag stay server-side. The current published agent has not proved the positive path.

Later Postgres proof needs authorised disposable test access, never a production run. Processor/region/retention review, clinical review and authorised participant research remain separate dependencies. Existing provider-sharing consent grants no general ADP-processing authority. This upgrade uses fictional words; no real-patient data boundary is opened.

REMAINING SEQUENCE
Gate 3 approval → separate Gate 4 upgrade slice plan → small visible journey/ADP slices → accessibility/API/Postgres verification → corrected demo/claims/assets → separately authorised deployment and submission.

Existing submission assets and usage proof need verification and revision. The cut study remains cut.

BEGIN NOW
Prepare the concrete Gate 3 amendment. Present the key contracts and remaining uncertainties, then ask exactly:
“Approve Gate 3, or what should change?”

Stop at that approval boundary.

```

---

## Prompt for Handoff Review

```text
Review CareRelay’s Gate 2 revision 4 documentation and approval record independently.

Workspace: /Users/jayd0/Desktop/carerelay
Snapshot: 13 October 2026. Branch: codex/patient-experience-architecture.
Committed HEAD: aca4594485f3e465daa461bf8139033458b2b81c.
The Gate 2 amendment and approval mirrors are uncommitted. No new implementation or application tests were written.

Read AGENTS.md, its required authority files, current git status/diff and 02-architecture.md section 13. The user explicitly approved revision 4 on 13 October; 00-status.md must reflect that in its gate line, checklist and history. User approval is not proof of correctness.

Be unbiased, thorough and honest. Assume the work may be flawed. Seek concrete contradictions and unsafe gaps, not confirmation of the author’s conclusions. Assess quality as well as completion: scope, simplicity, implementability, hidden assumptions, concurrency, privacy/consent and evidence strength.

Scope changed: 02-architecture.md adds D14 to D18 and reconciles source/config facts. 00-status.md records reopening/re-approval and scope limits. AGENTS.md, PLAN.md, todo.md, DESIGN_PRINCIPLES.md and three supporting planning notes mirror them. PROGRESS.md is operational only; lessons.md records an inherited punctuation error caught before delivery. The handoff is a new documentation file. Gate 1 assets/copy, Gate 3/4 contract documents and application/frontend/test files were preserved.

Stress-test the twelve screen mappings and precedence against actual domain/service/store behavior. Probe no-plan/options, stable start nonce and lost-response recovery, append-only command claims/terminal receipts, atomic revisions, stale text/repair/hint tokens, field-only matching, stop versus invocation and late callbacks. Inspect actual code rather than treating a future mechanism as present. Validate the raw-span ADP boundary, negation limits, refusal/timeout behavior and separation from action origin. Inspect the published agent instruction as recorded evidence; do not claim a live positive path.

Verification claimed for the architecture run: documentary consistency and byte/diff checks, twelve mapping rows, five decision headings, 81 preserved-file hashes, unchanged section 5.2 and a bounded credential scan with detection controls. Those checks do not prove behavioral correctness. Earlier 945-pass/46-skip and 39/39 mutation results belong to 12 October; no application suite, ADP probe or Postgres engine was rerun here.

Re-run appropriate local/read-only checks and inspect the evidence behind relevant existing tests; re-run focused existing tests only if needed to evaluate a concrete claim and record their actual environment/results. Proposed Gate 3 tests do not exist yet. If a test is trivial, weakened, incapable of failing, or proves less than claimed, flag it. Do not pass tests for the sake of passing. Green output is not proof. No installs, credentials, live service probes, production database access, code mutation, commits, pushes or deployment are authorised by this review prompt.

Report PASS / ISSUES FOUND / FAIL with specific findings, severity, file paths/line numbers, reproductions or outputs, and explicit unknowns. Distinguish a defect requiring Gate 2 backtracking from details legitimately left for Gate 3. A second model’s agreement is not independent correctness evidence.

Deliver your verdict and wait for instructions.

```
