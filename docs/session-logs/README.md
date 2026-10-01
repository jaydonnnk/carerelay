# Session logs

The WorkBuddy session logs for CareRelay, one file per working day. They are the
project's **usage proof**: the record of the development process behind the code
in this repository.

## Why they are published

The challenge requires the development chat history as a submission item.
`docs/CHALLENGE_REQUIREMENTS_JUDGING.md` section 8 lists "CodeBuddy / WorkBuddy
Conversation History" as **Required**, and section 8 also states that proof of
product usage is mandatory and may take the form of "chat screenshots, API call
logs, or a written development-process description". These logs are the written
form, and submission is through this GitHub repository.

They are also the artefact `docs/plans/urgent-advice-accessibility/04-slices.md`
calls out as unreconstructable: the usage proof starts at Slice 4, and it cannot
be rebuilt once the session logs are gone.

## What is in here

| File | Covers |
| --- | --- |
| `2026-09-21.md` | The PlanBack and Closure Contract specification, and the Gate 1 reframe |
| `2026-09-25.md` | Gate 1 committed; the push blocked on credentials; the first `.gitignore` |
| `2026-09-26.md` | Gate 3 closed, including the clinical-review blocker it carried |
| `2026-09-28.md` | Gate 4 drafted, the kill tests pass, the ADR directory created |
| `2026-09-30.md` | The git object-store loss and recovery; Slices 1 to 3; the stack reversal; the revision-3 re-approval |
| `2026-10-01.md` | The Slice 4 adversarial review and its remediation |
| `MEMORY.md` | Curated project notes: working conventions and current state |

## These are copies

The live files are written by the WorkBuddy memory system to `.workbuddy-ai/memory/`,
which is git-ignored so that agent tooling state does not ship. This folder is the
published copy and is refreshed when a slice ships. If the two disagree, the live
file is the source and this copy is stale.

## Read them as written

These logs are published unedited, including their errors. They record wrong
turns, corrected claims and superseded decisions on purpose, because that is what
a development-process record is. `00-status.md` remains the only authority for
gate and slice state; a statement in a log is a record of what was believed on
that day, not a current fact.

Nothing here is a clinical claim. No value in the fixture is a clinical threshold,
and nothing in this folder has been shown to a participant.
