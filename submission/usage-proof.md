# Usage proof: how this project was built with WorkBuddy

**Status: COMPLETED at Slice 12, on 11 October 2026.** The written history is
published, the minimum of three chat screenshots is in place, and every claim in
the submission description is traceable to the artefacts listed here or to the
files in the companion statement `honest-claims.md`.

This file is the written half. The screenshots are the other half, and the two
requirements are separate rows of `CHALLENGE_REQUIREMENTS_JUDGING.md`, not two
readings of one line.

| Line | Requirement | State | Where the evidence is |
|---|---|---|---|
| 128 | Proof of product usage: chat screenshots, API call logs, **or** a written development-process description | **MET** | `docs/session-logs/` (one file per working day) |
| 164 | Chat history: **a minimum of 3 screenshots** of chat logs from CodeBuddy or WorkBuddy during development | **MET** | `submission/usage-proof/screenshots/` (three captured 1 October 2026) |

## 1. The written development history

`docs/session-logs/` holds one file per working day from 30 September 2026 to
11 October 2026, with one entry per slice. The live session files stay at
`.workbuddy-ai/memory/`, which is git-ignored, so the published folder is a copy
refreshed when a slice ships. Its own `README.md` records that rule.

Two disclosures, made rather than left for a reader to find:

- The imported logs carry **155 em dashes**, counted across `docs/session-logs/` on
  9 October 2026. `AGENTS.md` section 6 bans em dashes in *new writing*; these are
  historical records, and rewriting them would falsify the evidence, so they are
  published as written. They are concentrated in the first week: `2026-09-30.md`
  alone carries 65, and `2026-10-01.md` to `2026-10-05.md` carry none.
- The logs contain the Windows username inside a handful of absolute paths. No
  token, key, credential, email address or real institution name appears in them.

`.workbuddy-ai/skills/` is **deliberately not published**: it holds third-party
files with no licence or author field, and the challenge requires the project to
be original.

## 2. The chat screenshots

Three, captured 1 October 2026 by Jaydon into
`submission/usage-proof/screenshots/`. The manifest and the redaction check are in
that folder's `README.md`.

| # | Moment | Filename |
|---|---|---|
| 1 | WorkBuddy conversation history for the `ai-triage` workspace, showing nine sessions with relative timestamps from minutes to a day | `01-conversation-history-sidebar.png` |
| 2 | Gate 3 closed and committed, commit `e77d978` | `02-gate3-closed-and-committed.png` |
| 3 | Gate 4 drafted, K1 and K2 PASS, Gate A still unrun | `03-gate4-drafted-k1-k2-pass.png` |

## 3. Reserved slots for later-slice captures

The user will capture additional screenshots from the later slices (8 to 12)
before the submission deadline and drop them into this folder. The names and the
moments they show are reserved here so a manifest row without a file is never the
final state.

| # | Filename | Moment (reserved) |
|---|---|---|
| 4 | `04-slice10-closure-renderings-live.md` or `.png` | Slice 10, all five closure screens proven live on 8 October 2026 |
| 5 | `05-slice11-fault-harness-and-ship.md` or `.png` | Slice 11, the seven fault sequences and 7 of 7 mutations RED on 9 October 2026 |
| 6 | `06-slice12-judge-ledger-and-submission.md` or `.png` | Slice 12, the ledger view and the submission assets landing on 11 October 2026 |

A file that matches the reserved name is the evidence. A reserved row with no file
is a placeholder, not a claim.

## 4. Rules (re-stated for the existence audit)

- **Redact before committing.** No ADP AppKey, token, key or credential, in a
  screenshot or in a log. Names only, never a value.
- **Crop to the development history.** Blur or crop anything that is not part of it.
- **Name screenshots `NN-<what>-<when>.png`.**
- **Keep the manifest current.** A screenshot with no manifest row is not evidence.
- **Never reconstruct after the fact.** The chat history exists only in the session
  that produced it, which is why capture starts at the slice rather than at the end.

## 5. Reconciliation against the submission table

| Submission item (`CHALLENGE_REQUIREMENTS_JUDGING.md` line) | Where it is in this repository |
|---|---|
| Line 128, written history | `docs/session-logs/` |
| Line 164, chat history (min 3 screenshots) | `submission/usage-proof/screenshots/` (three captured; slots 4 to 6 reserved) |
| Line 132, project title | `submission/description.md` |
| Line 135, short blurb | `submission/description.md` |
| Line 141, project description | `submission/description.md` |
| Line 153, true 16:9 cover | `submission/cover-16x9.svg` and `submission/cover-16x9.png` |
| Line 152, source code | The GitHub repository recorded at `docs/session-logs/2026-09-30.md:114` |
| Line 154, demo walkthrough | `submission/demo-walkthrough.md` |
| Line 152, architecture and trust-boundary diagram with trade-offs | `submission/architecture-trust-boundaries.svg` and `submission/architecture-trust-boundaries.png` |
| Honest-claims statement | `submission/honest-claims.md` |
| Submission runbook (Render and ADP) | `submission/setup-runbook.md` |
| ADP agent instruction text and observed behaviour | `submission/adp-agent-instruction.md` |
| Project link | Vercel frontend `https://carerelay-self.vercel.app`; Render API `https://carerelay-dzt3.onrender.com`; ADP Experience URL `https://adp.tencentcloud.com/webim_exp/#/chat/GkTbUc` |

## 6. Confirmation that nothing here contradicts a claim

Each row in section 5 was checked against the claim made in
`submission/description.md`. No contradiction found. Where a row in this file
points to an artefact that contains an em dash, the em dash is either historical
text in `docs/session-logs/` or the verbatim `FIXTURE_LABEL` inside a JSON
example, both disclosed.