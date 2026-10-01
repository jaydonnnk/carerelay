# CareRelay: project and execution instructions

These instructions combine CareRelay's product and clinical-safety constraints with
the repository's execution rules. Product authority, clinical boundaries and evidence
labels always take precedence over generic workflow convenience.

---

## 1. Operating principles

- Honesty, accuracy and epistemic humility matter more than agreeableness. Never
  invent numbers, quotes, sources, test results, competitor behaviour or tool state.
- Every factual claim carries one of four labels: **[verified]** supported by the
  cited source, **[vendor claim]** advertised but not independently validated,
  **[hypothesis]** our judgment, **[unknown]** not established. This convention is
  load-bearing across `PLAN.md`, `DESIGN_PRINCIPLES.md` and
  `03-planback-closure-contract.md`. Keep it.
- Lead with the answer. Be brief. Explain complex choices in short, concrete steps
  suitable for a reader who benefits from extra structure and low cognitive load.
- For layman-terms or ADHD-friendly explanations of tasks, decisions, reviews or
  technical findings, invoke the user-level `layman-explain` skill
  (`C:/Users/jayd0/.qoder/skills/layman-explain/SKILL.md`) and follow its shape:
  one everyday sentence for what the thing is, literal examples with real values,
  scannable bullets and tables, no abstract or poetic framing, and the concrete
  ask stated last.
- Push back when the user's logic is weak. Lead with blockers, falsifiers, failure
  modes and uncertainty instead of softening a critique.
- Prefer the simplest complete solution. Find the root cause, change the narrowest
  responsible layer and avoid temporary fixes, unnecessary abstractions and side
  effects. Do not add dependencies the product does not need; Feasibility is a
  scored dimension.
- Challenge non-trivial work before presenting it: is there a simpler or more
  coherent solution, and would a senior reviewer accept the evidence?
- The latest explicit user instruction overrides older notes. Never infer approval
  for implementation, a later software-factory gate, an install, a credential or
  an external service.

## 2. Read order and authority

Before working on CareRelay, read:

1. `docs/CHALLENGE_REQUIREMENTS_JUDGING.md`: official challenge statements,
   submission requirements and the ten-dimension rubric. Keep product opinions out.
2. `docs/PLAN.md`: current direction, labelled evidence, scope, proof gates,
   schedule and score ranges.
3. `docs/plans/urgent-advice-accessibility/00-status.md` and every existing file
   beneath that folder: approved gate state, the file map, fresh-session notes.
4. `docs/DESIGN_PRINCIPLES.md` when the task touches scope, ambition, novelty or
   platform dependence. Read section 4 and section 8 before treating `PLAN.md`
   section 6 as settled.
5. `docs/plans/urgent-advice-accessibility/research-workarounds.md` when the task
   touches clinical blockers, recruitment, schedule fallbacks or Mandarin voice.
6. `C:/Users/jayd0/.agents/skills/software-factory/SKILL.md` when the task concerns
   a product gate, feature, architecture, program design, slice plan or
   implementation.
7. `tasks/lessons.md`: logged corrections and prevention rules. Check before
   working to avoid repeating known mistakes.

`CareRelay.md`, `ai-triage_casestudy2.md` and `medical-ai-framework_casestudy1.md`
are historical case-study inputs retained for context, not authority and not current
scope. `docs/ADDITIONAL_CHALLENGE_INFO.md` is the organiser's spoken framing of both
challenge statements.

Authority rules:

- Approved gate documents supersede provisional choices in `PLAN.md`. When a gate
  changes a durable decision, update the supporting brief so the documents stay
  consistent.
- `00-status.md` is the only authority for gate and slice state. `PROGRESS.md` is
  operational memory and may never record or imply a gate approval.
- Official rules, the handbook and primary sources supersede stored summaries
  whenever a time-sensitive external claim is made.
- A draft gate document authorises nothing. `02-architecture.md` revision 2 is
  approved; `00-status.md` records the approval and its limits.
- **File-map trap:** two supporting notes already occupy the `02-` and `03-`
  filenames that the Gate 2 and Gate 3 documents need. Read the map in
  `00-status.md` before assuming a file's role from its number.

## 3. Current state, gates and authorization

- **2026-09-30 current authority, revised 30 September 2026:** Gate 1 (Product),
  Gate 2 (Architecture, revision 3), Gate 3 (Program Design) and Gate 4 (Slice
  Plan) are **all APPROVED**. Gates 2, 3 and 4 were reopened on 30 September 2026
  to encode Decisions D-A to D-D and hosting Decision D-1b, and were **re-approved
  the same day**. `00-status.md` records both the reopen and the re-approval.
  Slices 1, 2, 3 and 4 are complete. **Slice 5 is next and is blocked on the Option C
  source**; it has not been begun. **Each slice stops
  for the user's "continue, or re-steer?" before the next one begins.**
- Gate 1 approval covers the reframe, PlanBack, the recall hint ladder, the Closure
  Contract, the two-axis state model, the design principles and the five HTML
  wireframes. It does not authorise implementation, installs, credentials, external
  calls, recruitment or deployment.
- Branch state (verified 30 September 2026, after the Slice 3 remediation): `slice-3`
  holds the Slice 3 work and its remediation in one series of commits (the store's
  command and result types, the append-only record, the documentation restructure,
  the record, the ship corrections, the O1 remediation, and the remediation record),
  and `main` is fast-forwarded to the same commit. `slice-2-domain-core` sits at
  `80245e4`. `gate-2-architecture` and `care-relay-adversarial-review` no longer
  exist as branches; their commits remain reachable from `main`. No gate authorises
  a commit or a push, so the Slice 1, 2 and 3 commits, the Slice 3 remediation, and
  the Gate 2, 3 and 4 revision-3 amendment were all made on the user's **explicit
  instruction** of 30 September 2026, as was the push that carried them to
  `origin`. `origin` holds the branches that hold the work, `main` and `slice-3`,
  each in sync with its local branch. They do not sit at the same commit: `slice-3`
  was frozen when its slice closed and `main` has moved on since. A push succeeds
  when it is asked for, so the credential failures recorded in `tasks/lessons.md`
  no longer apply. Commit counts and hashes are deliberately not stated here: both
  have gone stale in this file before.
- **Next hard dependency: the Gate A access spike, due 2026-09-26.** Approval of
  Gate 2 authorises the spike only (read-only credential checks and one typed tool
  call), not implementation code. The reversal is pre-recorded: if WorkBuddy access
  fails, fall back to labelled local simulation, carry the mandatory usage proof
  through genuine CodeBuddy development history, and weaken the platform-advantage
  claim accordingly.
- **Stack (revised 30 September 2026).** Backend: Python 3.13 + FastAPI + SQLite
  (WAL, busy timeout) on **Render** (Docker, paid plan, mounted persistent disk),
  with the SQLite path supplied by `APP_DATABASE_URL`. Frontend: a **Next.js
  clinical frontend on Vercel** calling the Render API as JSON. **The Node and
  Next.js reversal decision is made**, recorded here and dated: Slices 1 to 3 had
  already shipped, so the original "before the first domain-code commit" trigger
  could not be met, and the decision is taken on the user's explicit instruction
  of 30 September 2026. **Auth is a precondition of the public deployment**: a
  shared bearer token on every `/api` route and on `/ledger`, CORS locked to the
  Vercel origin. `02-architecture.md` D1, D13 and section 8 carry the detail.
- The scheduled-reassessment module (D9) was dropped at Gate 2. Under deadline
  pressure, cut TRTC voice before anything beyond one caregiver channel.
- **The public deployment, the public endpoint and the ADP surfaces are
  authorised by no gate yet.** Re-approval of Gates 2, 3 and 4 is what authorises
  them. Until then no gate authorises installs, credential changes, other external
  service calls, engaging a clinical reviewer, participant recruitment, the public
  deployment, publication, submission assets, or any commit or push.

Carried-forward unresolved Gate 1 risks. These were accepted rather than resolved
and remain live inputs to Gate 3:

- **Mandatory organiser-usage proof is still absent.** Without it the project does
  not proceed to scoring.
- **No qualified clinical reviewer and no authorised protocol.** The prototype must
  remain a labelled research demonstration on scripted fixtures.
- **The load-bearing assumption is untested:** that a fixed bilingual card plus a
  direct booking link plus a NurseFirst fallback does not perform equally. This is
  the primary kill test and must run first.
- **Neither mechanism requires WorkBuddy.** WorkBuddy's genuine dependency is the
  coordinator, the real tool call, its real failure event and session resume.
- **Mandarin voice is a gated TRTC spike only.** No account access and no clinical
  accuracy has been demonstrated.

## 4. Product definition and scope filters

- CareRelay is a patient-facing self-triage service for community-dwelling older
  adults (65+) and their family caregivers: English text first, caregiver-assisted
  where desired. It helps them answer three questions without hiding uncertainty:
  what must I do and by when; can I actually do it; has help really been arranged,
  or is it still unresolved.
- The claim worth testing is **one contract, not a feature bundle**: the critical
  action and deadline must survive read-back, retry, restart and failed handoff
  without false completion.
- **The model interprets. Code decides.** A model grading comprehension can err in
  both directions: a false "you understood" is a safety failure, and a false "you
  did not" is a dignity failure.
- Demo unit: one clinician-governed recommendation, one caregiver, one simulated
  service, one interruption and one failed action. **Urgent guidance must appear
  before teach-back, navigation or caregiver acknowledgement, never after, and
  never waiting on a model call.**
- Demonstration boundary. Real: organiser runtime execution, interpretation, state,
  permissions, failure handling, UI and evaluation traces. Explicitly simulated:
  clinic availability, booking receipts, caregiver messages, clinical service
  acknowledgements. Out of scope: real patient triage, prescribing, EHR access,
  emergency dispatch, continuous monitoring, autonomous clinical decisions. Every
  simulated element stays labelled simulated in screenshots, video and metrics.
- Provisional persona: Mei, a fictional 72-year-old Mandarin-preferring adult with
  remote daughter support, in a bounded respiratory-symptom scenario that is an
  injected fixture until clinical review. **No asset may name a real healthcare
  facility, ward or clinician.**
- Prohibited claims. Any of these appearing in the product, submission, video or
  pitch is a defect: cognitive improvement, cognitive training, "keep your mind
  sharp" or dementia prevention; cognitive screening, risk score or diagnostic
  output; clinical validation, improved health outcomes or avoided admissions;
  "world-first" or an empty market.
- Prohibited language: "cognitive rot", "brain training", "use it or lose it" and
  any framing implying the patient's mind is decaying. The product helps someone
  remember their plan and stops prompting once they no longer need it. That is the
  whole description.
- The fading scaffold is **vanishing cues with errorless learning and spaced
  retrieval**, cited as prior art. It improves retention of this specific plan and
  nothing more.
- Longitudinal cognitive monitoring is an out-of-scope research hypothesis recorded
  in `PLAN.md` section 5.3 so the ambition is not lost. It is not presented in the
  submission.
- Mandarin and voice are accessibility modes, not new clinical authorities. English
  text remains the auditable reference until bilingual clinical content is reviewed.
- Honest dependency boundary: plan on the platform as the **execution substrate**,
  never as the source of clinical state, the deadline invariant, consent or the
  closure rule.
- The four internal tests (load-bearing, earliness, theme alignment, ambition) are
  our selection criteria, not organiser requirements. P1 is a lens requiring at
  least one genuinely load-bearing axis, not an exclusivity gate;
  `DESIGN_PRINCIPLES.md` section 4 explains why the literal rule is unsafe.

## 5. Required software-factory process

1. Product
2. Architecture
3. Program Design
4. Vertical Slice Plan

Rules:

- Workflow documents live in `docs/plans/urgent-advice-accessibility/`. `PLAN.md`
  is a supporting brief, not a substitute for the four gate documents.
- Write and review each gate separately. Obtain explicit approval at every gate and
  never infer it. Resume from the first unapproved gate in `00-status.md`. Do not
  redo an approved gate unless the user requests it or later evidence invalidates it.
- Gate 1 contains the problem, the measurable success metric, the announcement and
  plain HTML screen mockups. Keep implementation choices out of Gate 1.
- For Gate 1 UI, create one plain `.html` file per screen with no framework and no
  build step. More generally, create visualization files as `.html`, never `.tsx`.
- At a gate approval pause, ask exactly: `Approve Gate 1, or what should change?`,
  substituting the gate in play. A review, a critique or "proceed with the fixes"
  is not approval.
- Editing an approved gate document reopens that gate: update the document, set the
  gate to in progress in `00-status.md`, and obtain explicit re-approval before
  proceeding. Never apply queued edits ahead of re-approval.
- No implementation code may exist before Gate 4 approval. Direction selection,
  context updates, research and evidence plans are not gate approval.
- Record approvals consistently in `00-status.md`: the gate line, the checklist, a
  dated entry and the approval history. A stale or missing mirror is a blocking
  finding.
- After Gate 4 approval, implement one vertical slice at a time. Each slice must end
  in a visible, working, testable result and its evidence must be recorded before
  continuing. Do not build horizontal layers that cannot run end to end.
- After each slice, show the actual result, update `00-status.md`, then invoke the
  `architect-reviewer` skill in post-slice cleanup mode to scan for stale or
  redundant files before asking whether to continue or re-steer.
- Documentation-only maintenance, instruction consolidation and other changes that
  do not alter product behaviour do not create a new product gate.

## 6. Execution discipline

### Before editing

- Inspect `git status`. Treat existing changes as the user's work unless proven
  otherwise. Never stash, discard, rewrite or stage unrelated changes.
- For a non-trivial task outside the gate workflow, write a short actionable plan
  before editing. Re-plan when evidence invalidates the approach. Skip process
  ceremony for a small, obvious, one-file change.
- Establish a baseline proportional to risk. Documentation-only changes do not
  require a test suite. The repository currently has no application code and no
  automated test suite, so the baseline is documentary evidence; that changes at
  Slice 1.
- Do not install tools or dependencies merely because they are missing. Record the
  unavailable check unless the user has authorised installation. The user runs
  environment installs themselves and wants complete manifests and exact commands,
  not an agent that installs.

### While working

- Keep the change inside the user's requested scope and preserve existing behaviour
  outside it. Once the applicable gate authority exists, fix in-scope bugs directly
  from logs, failing tests and reproducible evidence instead of asking for
  step-by-step guidance.
- After a user correction, revise the active plan and any in-scope durable decision
  record that would otherwise repeat the mistake. Do not create generic lessons
  files or widen the diff merely to document a correction.
- Use subagents only when the user explicitly requests them or the active runtime
  policy allows them, and only for bounded, independent work. Give each agent one
  focused task. A second LLM is never an independent oracle for correctness and is
  never the reviewer of record.
- Prefer non-interactive commands. Never launch an editor, interactive rebase,
  login flow or confirmation prompt during an unattended run.
- On Windows, prefer `rg`, `Get-Content`, `npm.cmd` and `npx.cmd`. Do not assume
  PowerShell permits `.ps1` npm shims.
- Do not create branches, commits, tags or pushes unless the user has authorised
  that Git operation. Never stage everything implicitly. Never add a co-author
  trailer.
- **Every slice gets its own branch, created before the first edit of that slice.**
  Create it from the current tip of `main` and confirm with
  `git branch --show-current` before touching a file. Two things are absolute:
  never begin slice work on `main`, and never continue a slice on the previous
  slice's branch.
- **Name it `slice-<N>-<slug>`**, two or three words for the slice, as
  `slice-2-domain-core` does. Keep the name stable for the life of the slice, and
  record it in the slice's section of `00-status.md`. `slice-3` and `slice-4` predate
  this rule and carry no slug; they are grandfathered, not the pattern to copy.
- **The branch is part of the slice's authorised work, not a separate Git
  authorisation.** The rule above, that no branch is created without the user
  authorising that operation, is satisfied by the authorisation to implement the
  slice: Gate 4 authorises implementation slice by slice, and each slice still stops
  for the user's "continue, or re-steer?". No branch is created for a slice the user
  has not authorised, and a slice branch is pushed only if the user asks.
- Work that is not a slice (a gate revision, an adversarial review) takes a
  descriptive branch by the same rule, as `gate-2-architecture` and
  `care-relay-adversarial-review` did; never begin it on `main` either. When a slice
  is complete, fast-forward it into `main` on the user's instruction
  (`git merge --ff-only`) and leave the branch in place unless the user asks for it
  to be deleted.
- Commit in coherent batches, one concern at a time, with messages that name what
  changed and why. One commit covering an entire slice with a message such as
  "implement slice 1" is not acceptable.
- Do not modify CI configuration, lint configuration or lockfiles unless the task
  requires it.
- Never store secrets, tokens or credentials in repository notes, logs, fixtures or
  documentation. `02-architecture.md` lists environment variable names only.
- Do not use em dashes in new writing. Never write a bare `S` for a slice; write
  `S1` or `Slice 1`.

### Mistake logging

- After an error (broken build, failed test, wrong output, reverted change, stale
  or missing mirror of an approved decision), append an entry to `tasks/lessons.md`
  with: what happened, root cause, and a prevention rule.
- Before starting work, scan `tasks/lessons.md` for entries relevant to the current
  task and follow their prevention rules.
- When a failure pattern repeats four or more times, graduate it from
  `tasks/lessons.md` into a permanent rule in this file. Graduated entries stay in
  `tasks/lessons.md` as incident history unless the user asks for their removal.

### Verification

- A step is complete only when its result matches the request and the relevant
  tests, build, lint, type checks or rendered output have been verified in
  proportion to the change's risk.
- Tests must be capable of failing against the broken or pre-change behaviour.
  Never delete, skip, weaken or silence a check merely to obtain green output.
- Prove coverage, do not count it. A check that names every input it tries is not
  evidence that every guard branch fires: mutate each branch independently and
  require one real failure per branch, and treat a fault two checks can both catch
  as proof of neither.
- For every absence or leak assertion, prove the needle can match the surface as
  serialized, not as held in memory. Add a scanner self-test that injects the
  needle into a representative serialized surface and requires detection. This
  applies directly to the fixture and label rules: a real facility name, a real
  clinician name, an unlabelled simulated receipt or a credential must be
  detectable in the surface where it would leak. On Windows a JSON response
  backslash-escapes absolute paths, so path needles must be checked in raw,
  unescaped and forward-slash forms.
- Inventories describe structure, not coverage. A count of surfaces scanned is not
  evidence that any individual needle is capable of failing.
- If a test is invalid, explain why and preserve the evidence. If it fails once and
  passes on rerun, report it as flaky; do not treat one rerun as clean proof.
- For implementation, run focused checks while iterating and the relevant full
  suite before final completion. Compare with the baseline; any new failure is yours.
- Inspect the final diff for accidental scope, secrets, generated noise and
  line-ending damage. Run `git diff --check`.
- For local previews, report the actual URL and port. For UI, inspect representative
  desktop and mobile views rather than relying on CSS values alone. `http-preview.log`
  and `http-preview.err.log` in the repository root are untracked preview scratch,
  not product files.
- Documentary consistency is part of the definition of done. A changed decision must
  be mirrored in the same change across `00-status.md`, `PLAN.md`, `tasks/todo.md`
  and this file wherever those files carry it.

## 7. Long unattended runs

Apply this section when the user explicitly asks for work to run without them
watching, or when a gate run is long enough that context will be compacted.

### Progress state

- If `PROGRESS.md` exists with unchecked steps and this is a resumed run, read it
  fully, re-verify the last completed step and resume from the first unchecked step.
  Do not restart completed work or trust a compaction summary over the file.
- Otherwise create or extend `PROGRESS.md` with the goal, a dependency-ordered
  checklist, relevant dirty-worktree state and a dated run log. Put risky independent
  checks early so blockers surface before broad edits.
- Use `[ ]` for pending, `[x]` for done and verified, and `[!]` for blocked with a
  one-line reason. After each step, record only the facts needed to resume.
- Keep `PROGRESS.md` under roughly 150 lines by condensing old entries. Include
  assumptions, failures, exact verification commands, skipped scope and a final
  Result section.
- `PROGRESS.md` is operational memory only. It may never record or imply a product
  gate approval; `00-status.md` is authoritative for gates and slices, and approved
  gate documents are authoritative for decisions.
- Never commit `PROGRESS.md` or any other file unless commits are explicitly
  authorised.

### Autonomy and hard stops

- Execute reversible steps clearly covered by the request without waiting. If a
  harmless ambiguity remains, choose the reading a careful colleague would choose,
  record the assumption and continue.
- If one part is impossible, unsafe or contradicted by evidence, complete the
  independent in-scope work and record why that part was skipped.
- Stop for missing authority, destructive or irreversible ambiguity, a required
  product or clinical decision, credentials, payment, participant outreach,
  deployment, or any software-factory approval. Unattended mode never widens
  authorization.
- Stop above all for anything touching clinical content or safety boundaries:
  approving clinical strings, inventing a symptom-to-disposition path, weakening the
  abstention stop, or presenting a fixture as reviewed guidance.
- After three materially different failed attempts at the same step, record the
  outputs, mark it blocked and move to an independent step. Mark dependent steps
  blocked with the same cause. If no independent work remains, finish with a clear
  blocked result instead of guessing.

### Context and output hygiene

- Treat files as durable context. Update progress after each verified step and
  before a likely compaction so a fresh session can continue without chat history.
- The mandatory read order still applies. After that, prefer targeted line ranges,
  `rg`, quiet test output and tailed logs. Avoid dependency trees, binary dumps,
  lockfile output and redundant full-file reads.
- Do not echo the full plan or progress log into chat. Give concise milestone
  updates.
- Run servers and watchers in a controllable background session with captured logs;
  record how to stop them and clean them up before completion unless still needed.

## 8. Technology, access and evidence boundaries

- WorkBuddy account access, region, quotas and billing are **[unknown]**. Gate A is
  unrun. Never claim a platform capability as available until the spike proves it.
- The managed scheduler is enterprise-owned with a documented five-minute floor.
  Never place urgent escalation on it, and never claim concurrency or population
  scale, which the brief does not require.
- Agent versioning: publishing a version does not activate it, and activation affects
  new sessions. Existing-episode pinning and migration are our work, not a vendor
  guarantee.
- Checkpoints are runtime snapshot and restore, not external-action rollback and not
  exactly-once execution. A hook is not automatically an authorisation barrier.
  Authorisation and consent are re-checked at execution, in our code.
- TRTC supplies ASR and TTS primitives. No verified Singapore-accent or clinical
  accuracy exists, and code-switching is a **[vendor claim]**. The Mandarin release
  gate in `research-workarounds.md` is binding: native-speaker review of every
  critical Chinese string, bilingual clinical approval of clinical strings, at least
  30 fixed utterances, and zero silent critical-fact errors.
- No real clinic, booking, EHR, HealthHub, NHG or NTU integration exists and none may
  be claimed. Adapters are scripted and local-only, and the `simulated: true` label
  must survive from the adapter response through the evidence record to the UI
  projection.
- Clinical content: without a qualified reviewer and an authorised protocol the
  product is a research demonstration on injected fixtures. Do not present a
  symptom-to-disposition path as patient-ready, do not invent thresholds, and do not
  treat the organiser's example thresholds as validated Singapore guidance.
- HSA assesses intended purpose and function, so "not diagnosis" does not settle
  regulatory status. PDPA obligations cover purpose, consent or legal basis,
  protection, retention limits and overseas transfer; deployment region and
  processor arrangements are **[unknown]**.
- **ADP (added 30 September 2026).** ADP is a published agent surface, additive to
  WorkBuddy and never a replacement for it. Its documented capabilities are
  orchestration, knowledge base, workflow and guardrails. **Tool execution is a
  [vendor claim]** (`CHALLENGE_REQUIREMENTS_JUDGING.md` section 7); **the MCP tool,
  the platform-originated failure event and session resume are [unknown]**, and the
  ADP guide documents none of them. ADP may occupy the **interpretation step only**:
  never the execution path, never the rendering path. The ADP AppKey is a secret:
  names only, never a value, never committed, never in a screenshot.
- **The public deployment (added 30 September 2026).** The product is publicly
  deployed on Render with a Next.js frontend on Vercel, behind a shared bearer
  token. **The deployment region and the processor arrangements are [unknown] and
  must be recorded** under PDPA before submission. The append-only record's
  persistence depends on a mounted disk, which is a paid feature and a recurring
  cost, not a default.
- The baseline is a first-class external artefact, not an in-app arm. Gate B uses a
  between-subjects comparison against a concise bilingual action card with identical
  clinical wording, identical legitimate options and a direct booking link. CareRelay
  must win through repair and truthful recovery, not through better clinical content.
- Scores: no built-project score is justified today. The 21 September artifact-only
  estimate is **39/100**, and the conditional working target is **73 to 84/100** if
  the demonstration and proof gates are met. Never present these as an official or
  expected score.
- Capacity: the full package is estimated at **180 to 270 person-hours** and the two
  new mechanisms at **76 to 124 hours**, which does not fit the 16 October deadline
  alongside the full scope. Scope cuts are real, not rhetorical.

## 9. Adjudication warnings and proof boundaries

- Categories are occupied. Chat-to-care-navigation is taken (Infermedica, Clearstep,
  Healthdirect). Longitudinal reassessment is taken (Clearstep 2021, Infermedica
  2023 and 2025). Appointment and no-show recovery is taken (Hippocratic AI, Luma).
  Cohort monitoring is taken (Hippocratic AI, Healthline AI). Abstention in medical
  ML is not new (2021 literature, Canvas Dx). Treat the remaining differentiation as
  a bounded hypothesis, not verified uniqueness.
- The plausible gap is measured fail-closed abstention in patient-facing longitudinal
  LLM triage. An exact match was not found in a bounded search. That is not a
  world-first claim, and absence of public documentation is not proof that a
  competitor lacks it.
- The nine-surface taxonomy in `DESIGN_PRINCIPLES.md` section 3 is our internal
  diagnostic, not an organiser scorecard. The handbook treats CodeBuddy or WorkBuddy
  usage proof, not feature counting, as the eligibility gate.
- Deterministic rules are not safe by themselves; they can misapply a misheard fact.
  Using native platform features is not innovation by itself. A simulated integration
  does not prove real-world readiness.
- Health-literacy figures are instrument classifications, not triage error rates.
  Human teach-back evidence from one US emergency-department trial does not validate
  automated comprehension scoring. MedQAbstain shows LLMs systematically overcommit
  under medical uncertainty, which is precisely why code, not a model, decides the
  comparison.
- Zero observed misses in 15 independent emergency examples still implies roughly an
  18 percent one-sided 95 percent upper miss-rate bound. Passing Gate D supports
  regression claims, not clinical safety.
- A second LLM is not an independent oracle. Never dispatch one to certify correctness.

## 10. Repository history and closed directions

- `CareRelay.md`, `ai-triage_casestudy2.md` and `medical-ai-framework_casestudy1.md`
  are historical case-study inputs. They are context, not authority.
- Closed and corrected directions. Do not resurrect any of these without an explicit
  user instruction:
  - The one-shot "advice that closes" scope is superseded by truthful execution
    and unresolved-state reporting. The proposed monitored episode is not delivered
    after the Gate 2 cut of scheduled reassessment (D9).
  - Patient-facing ledger detail is cut. The patient sees four lines; the two-axis
    ledger is judge-facing evidence only. Do not move the ledger onto the patient
    screen.
  - The single-ladder state model is a corrected defect. Urgency and certainty are
    separate, understanding and feasibility are separate, and execution and evidence
    are two independent axes that never collapse into one ladder.
  - Evaluating a voice transcript before the patient confirms or corrects it is a
    known defect class. Transcript confirmation comes first, always.
  - Mandarin voice, broad respiratory intake, caregiver orchestration beyond one
    channel, and booking integration stay cut from the judged slice. CodeBuddy is not
    the default plan; WorkBuddy is the primary runtime path. Miora, ADP and Agent
    Runtime are optional and only with measured need.
  - Multi-agent proliferation, a clinician authoring platform, real EHR integration,
    avatar or voice-first design, broad language coverage before native review, and
    autonomous clinical decisions are excluded.
  - The Mei and Mandarin respiratory scenario is a convenient feature container, not
    an evidence-backed best scenario. It remains provisional.
