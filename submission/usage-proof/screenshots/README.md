# Chat screenshots: the missing half of the usage proof

## Why this folder exists

`CHALLENGE_REQUIREMENTS_JUDGING.md` asks for two different things, and only one of
them is done.

| Line | Requirement | State |
|---|---|---|
| 128 | Proof of product usage: chat screenshots, API call logs, **or** a written development-process description | **Met.** The written history is published at `docs/session-logs/` |
| 164 | Chat history: **a minimum of 3 screenshots** of your chat logs from CodeBuddy or WorkBuddy during the development process | **NOT MET.** Nothing has been captured |

The written history does not close line 164: it is a separate row in the
submission table, not an alternative reading of line 128. **Screenshots cannot be
reconstructed after the fact.** The chat history they have to show is only in the
session that produced it, so this is the one artefact that gets harder every day it
is deferred.

## Named person, named location

- **Named person: Jaydon.** The capture is deliberate and attributable, not a side effect.
- **Named location: this folder, `submission/usage-proof/screenshots/`.**

`submission/usage-proof.md`, the written skeleton, is **Slice 5's** artefact and is
deliberately not written here.

## Captured screenshots

Three, all saved on 1 October 2026. The sidebar image (01) is the strongest single
piece of evidence: it shows the WorkBuddy conversation history for the `ai-triage`
workspace across many sessions with relative timestamps from minutes to a day (22m,
18h, 19h, 20h, 21h, 1d, 1d, 1d). That is what the requirement means by "chat logs
... during the development process". The other two show concrete work the chat
produced: a gate being closed and committed, and Gate 4 being drafted with the two
kill conditions passing.

| # | Moment | What it shows | Filename |
|---|---|---|---|
| 1 | **Conversation history for the `ai-triage` workspace** | The WorkBuddy chat sidebar with nine sessions and relative timestamps from minutes to a day. This is the strongest "process over time" image: real sessions, in the real tool, on the real project | `01-conversation-history-sidebar.png` |
| 2 | **Gate 3 closed and committed** (titled "Draft gate 2 architecture plan") | A WorkBuddy reply showing commit `e77d978`, "Working tree clean", and a "What changed" file table covering `03-program-design.md`, `clinical-review-blocker.md`, `00-status.md`, `02-architecture.md`, `PROGRESS.md` | `02-gate3-closed-and-committed.png` |
| 3 | **Gate 4 drafted, K1 and K2 PASS, Gate A still not run** (titled "Start gate 4 and create ADR docs") | A WorkBuddy reply titled "Gate 4 is drafted. Two things came back green before any code." with a Check/Result table: K1 false-mismatch corpus PASS (15 tests, 0 failures), K2 urgent-before-read-back PASS, Slice 1 environment check PASS, Gate A "Still not run. No creds, no .env, no SDK package" | `03-gate4-drafted-k1-k2-pass.png` |

**Reconciliation with the earlier suggestion.** The earlier "three to capture" list
targeted the Slice 4 walkthrough plus two earlier-day shots. The conversation
sidebar is a better substitute for the date-spread than the dates themselves: a
judge looking for "chat logs ... during the development process" gets the
process-over-time signal from the sidebar even though all three files were saved
on the same day.

## Rules before committing

- **Redact secrets.** No ADP AppKey, no token, no key, no credential. The ADP AppKey is a secret: names only, never a value, never in a screenshot. Verified for these three: none contain any of the above.
- **Crop to the development history.** Blur or crop anything that is not part of it.
- **Name them `NN-<what>-<when>.png`.** Done.
- **Keep the manifest current.** Updated in this commit.

## Manifest

| File | What it shows | Captured by | Date |
|---|---|---|---|
| `01-conversation-history-sidebar.png` | WorkBuddy chat sidebar for the `ai-triage` workspace: nine sessions spanning minutes to a day | Jaydon | 2026-10-01 |
| `02-gate3-closed-and-committed.png` | WorkBuddy reply closing Gate 3: commit `e77d978`, "Working tree clean", file change table | Jaydon | 2026-10-01 |
| `03-gate4-drafted-k1-k2-pass.png` | WorkBuddy reply drafting Gate 4: K1 and K2 PASS, Gate A still not run | Jaydon | 2026-10-01 |
