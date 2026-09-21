# AGENTS.md

> For long tasks that run without a person watching. Fill in project-specific details before starting. Do not load this file for short interactive work; it adds overhead that only pays off on long runs.

---

## 1. Core Principles

* **Simplicity First**: Make every change as simple as possible. Impact minimal code[cite: 1].
* **No Laziness**: Find root causes. No temporary fixes. Hold yourself to senior developer standards[cite: 1].
* **Minimal Impact**: Only touch what's necessary. Ensure zero side effects or newly introduced bugs[cite: 1].

---

## 2. Workflow Orchestration & Strategy

* **Plan Mode Default**: Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)[cite: 1]. If execution goes sideways, STOP and re-plan immediately[cite: 1]. Use plan mode for verification steps, not just building[cite: 1]. Write detailed specs upfront to reduce ambiguity[cite: 1].
* **Subagent Strategy**: Use subagents liberally to keep the main context window clean[cite: 1]. Offload research, exploration, and parallel analysis to subagents[cite: 1]. For complex problems, allocate more compute via subagents with one focused task per subagent[cite: 1].
* **Self-Improvement Loop**: After ANY correction from the user, update `tasks/lessons.md` with the pattern[cite: 1]. Write rules for yourself that prevent repeating the same mistake[cite: 1]. Ruthlessly iterate on these lessons until the mistake rate drops[cite: 1]. Review lessons at session start for the relevant project[cite: 1].
* **Demand Elegance (Balanced)**: For non-trivial changes, pause and ask: *"Is there a more elegant way?"*[cite: 1] If a fix feels hacky: *"Knowing everything I know now, implement the elegant solution."*[cite: 1] Skip this for simple, obvious fixes—do not over-engineer[cite: 1]. Challenge your own work before presenting it[cite: 1].
* **Autonomous Bug Fixing**: When given a bug report, fix it directly without asking for hand-holding[cite: 1]. Point at logs, errors, or failing tests, and resolve them[cite: 1]. Automatically fix failing CI tests without needing step-by-step guidance[cite: 1].

---

## 3. Task Management Framework

1. **Plan First**: Write actionable steps to `tasks/todo.md` with checkable items[cite: 1].
2. **Verify Plan**: Check in or confirm alignment before starting implementation[cite: 1].
3. **Track Progress**: Mark items complete as you proceed[cite: 1].
4. **Explain Changes**: Provide a concise, high-level summary at each completed step[cite: 1].
5. **Document Results**: Add a clear review section to `tasks/todo.md`[cite: 1].
6. **Capture Lessons**: Update `tasks/lessons.md` immediately after any corrections[cite: 1].

---

## 4. Unattended Operation & Execution Rules

Nobody is watching this session, and questions will not be answered.
* If a step is covered by the original request and can be undone, execute it without asking.
* If the request is ambiguous, pick the reading a careful colleague would choose, record the assumption in `PROGRESS.md`, and continue.
* If part of the request is impossible, harmful, or contradicted by the code, complete all other parts, record why that part was skipped in `PROGRESS.md`, and finish.
* Do not stop because the session is long, context was compacted, or work remains. Stop only at a hard stop or when every step is complete or marked blocked.

---

## 5. Starting or Resuming a Task

Before doing anything else:
1. **Check `PROGRESS.md`**: If it exists with unchecked steps, this is a resumed run. Read it fully, trust it over memory or compaction summaries, re-verify the last done step, and continue from the first unchecked step. Never redo finished steps or start over.
2. **Initialize Progress Tracking**: If `PROGRESS.md` does not exist, create it with the goal in one line and a checklist of steps. Order steps by dependency, putting the riskiest independent steps first to surface blockers early. Keep steps small enough to verify and commit individually.
3. **Inspect Git State**: Run `git status`. If there are uncommitted changes you did not make, leave them alone, never stash or discard them, and document them in `PROGRESS.md`.
4. **Branching**: If on the default branch, create a dedicated task branch before making changes.
5. **Establish Baseline**: Run the full test suite once and record the baseline in `PROGRESS.md` (including existing test failures, which are not yours to fix). If tools are missing, install them from project lockfiles/requirements; if unavailable, record it and continue without that check.

---

## 6. Maintaining the Progress Memory (`PROGRESS.md`)

`PROGRESS.md` is the only memory that survives context compaction and session restarts.
* **Checklist Marks**: `[ ]` Not started, `[x]` Done and verified, `[!]` Blocked (with a one-line reason).
* **State Transfers**: After each step, mark it and write the key facts needed for the next step.
* **Run Log**: Maintain a dated log of run starts, resumptions, baseline test results, and blockers.
* **Audit Trail**: Record every assumption, unaddressed problem, command failure, and exact verification command.
* **Result Section**: Before final output, document what was done, what was verified and how, and what was left out and why.
* **File Size & Hygiene**: Apply small inline edits rather than full rewrites. Keep under ~150 lines by condensing old entries. Never store secrets, tokens, or credentials.
* **Commits**: Commit `PROGRESS.md` alongside each step so git history accurately reflects progress.

---

## 7. Verification & Quality Standards

* **Definition of Done**: A step is done only when tests, build, and linting pass, and results match requirements[cite: 1].
* **Strict Assertion Rules**: Never make a check pass by deleting tests, skipping checks, weakening assertions, loosening types, or silencing linters[cite: 1]. If a test is invalid, document it in `PROGRESS.md`.
* **Config Integrity**: Never modify CI configs, lint configs, or lockfiles unless the task explicitly requires it.
* **Flaky Tests**: If a test fails once and passes on rerun, log it as flaky and continue. Do not count a flaky pass as verification of a change.
* **Full Suite Verification**: Run the entire test suite—not just modified tests—before marking the final step complete[cite: 1]. Compare against baseline; any new failure is yours[cite: 1].
* **Staff Engineer Standard**: Diff behavior between main and your changes[cite: 1]. Ask: *"Would a staff engineer approve this?"*[cite: 1]

---

## 8. Failure Handling & Circuit Breakers

* **Three-Attempt Rule**: After three failed attempts at the same step, stop trying. Record the failure output, mark the step `[!]`, and move to an independent step.
* **Dependency Cascading**: Mark dependent steps `[!]` with the cause of the blockage.
* **Graceful Termination**: If no independent steps remain, write the Result section and finish. A clear record of blocked state is a valid outcome; guessing past it is not.

---

## 9. Context Window Optimization

Context growth forces compaction, causing long runs to lose state.
* **Selective Reading**: Read only necessary line ranges or use `grep`. Never `cat` files longer than a few hundred lines.
* **Quiet Output**: Tail logs, run tests in quiet mode, and suppress lockfiles, dependency trees, binary dumps, or large payloads.
* **No Redundant Reads**: Do not re-read files immediately after editing to confirm changes.
* **No Echoing**: Do not repeat back plans or progress file contents in conversation messages; they exist on disk.

---

## 10. Command Execution Safeguards

Commands waiting for user input will hang indefinitely and terminate the run silently.
* **Forbidden Interactive Commands**: Never execute editors, `git rebase -i`, `git add -p`, login flows, or interactive confirmation prompts.
* **Non-Interactive Flags**: Always pass automated flags (`-y`, `--quiet`), set `CI=true`, and redirect standard input from `/dev/null` (`< /dev/null`) when uncertain.
* **Background Processes**: Run servers, file watchers, or long-lived daemons explicitly in the background with detached PIDs/logging redirection.