# Usage proof: how this project was built with WorkBuddy

**Status: SKELETON.** Created at Slice 5, per `04-slices.md`. It is filled in as
slices ship and is completed at Slice 12. Nothing here is a claim about a result:
every row is a pointer to an artefact that exists.

This file is the written half. The screenshots are the other half, and the two
requirements are separate rows of `CHALLENGE_REQUIREMENTS_JUDGING.md`, not two
readings of one line.

| Line | Requirement | State | Where the evidence is |
|---|---|---|---|
| 128 | Proof of product usage: chat screenshots, API call logs, **or** a written development-process description | **MET** | `docs/session-logs/` |
| 164 | Chat history: **a minimum of 3 screenshots** of chat logs from CodeBuddy or WorkBuddy during development | **MET** | `submission/usage-proof/screenshots/` |

## 1. The written development history

`docs/session-logs/` holds one file per working day. The live session files stay at
`.workbuddy-ai/memory/`, which is git-ignored, so the published folder is a copy
refreshed when a slice ships. Its own `README.md` records that rule.

Two disclosures, made rather than left for a reader to find:

- The imported logs carry **155 em dashes**, counted across `docs/session-logs/` on
  9 October 2026. `AGENTS.md` section 6 bans em dashes in *new writing*; these are
  historical records, and rewriting them would falsify the evidence, so they are
  published as written. They are concentrated in the first week: `2026-09-30.md`
  alone carries 65, and `2026-10-01.md` to `2026-10-05.md` carry none. The figure
  here read 136 until 9 October 2026, when a re-sync of `2026-10-08.md` and
  `MEMORY.md` moved the count and the stale number was corrected rather than left.
- The logs contain the Windows username inside a handful of absolute paths. No
  token, key, credential, email address or real institution name appears in them.

`.workbuddy-ai/skills/` is **deliberately not published**: it holds third-party
files with no licence or author field, and the challenge requires the project to
be original.

## 2. The chat screenshots

Three, captured 1 October 2026 by Jaydon into
`submission/usage-proof/screenshots/`. The manifest and the redaction check are in
that folder's `README.md`.

## 3. Capture log

One row per capture moment, added as the work happens rather than reconstructed.

| Date | Slice | Moment captured | File |
|---|---|---|---|
| 2026-10-01 | Slice 4 | WorkBuddy conversation sidebar for the `ai-triage` workspace | `01-conversation-history-sidebar.png` |
| 2026-10-01 | Slice 3 | Gate 3 closed and committed, commit `e77d978` | `02-gate3-closed-and-committed.png` |
| 2026-10-01 | Gate 4 | Gate 4 drafted, K1 and K2 PASS, Gate A still unrun | `03-gate4-drafted-k1-k2-pass.png` |

## 4. Rules

- **Redact before committing.** No ADP AppKey, token, key or credential, in a
  screenshot or in a log. Names only, never a value.
- **Crop to the development history.** Blur or crop anything that is not part of it.
- **Name screenshots `NN-<what>-<when>.png`.**
- **Keep the manifest current.** A screenshot with no manifest row is not evidence.
- **Never reconstruct after the fact.** The chat history exists only in the session
  that produced it, which is why capture starts at the slice rather than at the end.

## 5. What Slice 12 adds

- The cover image and the three submission screenshots required by
  `CHALLENGE_REQUIREMENTS_JUDGING.md` section 8 (a different set from the chat
  history above).
- The final row-by-row reconciliation of this file against the submission table.
- Confirmation that no artefact here contradicts a claim made in the description.
