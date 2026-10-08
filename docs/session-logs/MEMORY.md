# MEMORY.md: CareRelay project

Curated long-term notes. Daily logs sit beside this file (append-only) and hold the full detail; `tasks/lessons.md` is the full technical record.

## Working conventions

- **Prompts go in chat, not on disk.** Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes (U+2014) are banned in new writing** (`AGENTS.md` s6). Imported historical em dashes are kept and the count disclosed, never stripped.
- **CRLF everywhere**, except five tracked files that are LF on purpose: `CareRelay.md`, `ai-triage_casestudy2.md`, `tools/git-switch-safe.sh`, `tests/test_boundaries.py`, `.gitignore`. Two older notes each said four and each listed a different set; measured 7 Oct 2026, the union is five. A tool-written new file is usually LF and must be converted. Check `b.count(b"\n") - b.count(b"\r\n") == 0`. Blobs are LF (`core.autocrlf=true`); only authoring discipline keeps the worktree CRLF. Never renormalise before a push.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` may never imply approval. `AGENTS.md` s3 also states slice state and drifts; never trust it over `00-status.md`.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` s5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.
- **One question at a time** with Jaydon.
- **Checkboxes in `tasks/todo.md` go stale silently.** Verify against `00-status.md` or commit history; never tick on a forecast.
- Session logs publish to `docs/session-logs/`; live files stay in `.workbuddy-ai/memory/` (git-ignored). `.workbuddy-ai/skills/` holds third-party skills with no licence or author and must **never** be published.

## State

- **All four gates APPROVED.** Gate 1/2 were last reopened on 2 Oct 2026 by the patient-wording pass and re-approved the same day. Gate 4 was reopened on 8 Oct 2026 to execute the pre-recorded cut of the Gate B run and **re-approved the same day** ("Yep i re approve"), so Slice 10 may begin.
- **Slices 0-9 shipped to `main`** (Slice 9 fast-forward `2576dc7` -> `4f252dd`, 8 Oct 2026), in sync with `origin/main`; suite on `main` **870 passed, 0 skipped**. Slice branches are frozen at their closing commit, behind `main` by design; `slice-9` is not published to `origin`.
- **Slice 8 SHIPPED 7 Oct 2026** (fast-forward `ac62286` -> `2576dc7`): `study/fixed-card.html`, `study/protocol.md` (pre-registration), `tests/test_study.py` (126 tests), `tests/_mutate_slice8.py` (26/26 RED). Check COMPLETE (Jaydon read both), slice ticked. Remediated same day (B1, S1, S2, N1, N2, N3, N5). **Deliberately not done: S3** (N4 was closed by Slice 9).
- **Slice 9 SHIPPED 8 Oct 2026 as a CUT** (fast-forward `2576dc7` -> `4f252dd`). The Gate B run was removed: no dyad was recruited, so there is no Gate B result and **no human-centred validation claim is made**. It is **not a failed recruitment** and **not a null result** (protocol s18 as amended), because the run was cut before any recruitment was attempted. What shipped is the instrument the sessions would have been scored with, kept as design evidence, not a deliverable: `src/carerelay/study/` (`scoring.py`, `outcomes.py`, `sheet.py`, `__main__.py`, `consent.py`, `second_scorer.py`), the recruitment preparation (`study/consent-sheet.md`, `study/run-sheet.md`), and the evidence (`tests/test_study_instrument.py`, `tests/test_study_recruitment.py`, `tests/_mutate_slice9.py` 46/46 RED, `tests/_mutate_slice8.py` 26/26 RED, 0 SURVIVED, 0 NOT PROVEN). Suite **870 passed, 0 skipped** (846 was the 7 Oct build). **No second scorer is needed and none will be named.** The cut rule's minimum sample of 3 per condition stays (`BelowMinimumSample`), a pre-data amendment in protocol s17. The sheet is a FILE not a DB table (protocol s4: destroy 30 days after submission). No HTTP endpoint.
- Stack: Python 3.13 + FastAPI + SQLite (WAL) on **Render**; **Next.js** on **Vercel**; **ADP additive only** (interpretation, never execution/rendering). 14 slices (0-13), deadline 16 Oct 2026.
- **B3 CLOSED without a clinical reviewer** (substring match -> exact normalised match; narrowing is not reviewer-gated, widening is).
- **Gate A access spike PASSED 2 Oct 2026.** ADP `https://wss.lke.tencentcloud.com/adp/v2/chat`; auth is the **`AppKey` request-body** field; failures arrive as **HTTP 200 with an SSE `event: error` frame**. Proves the **transport only, not tool execution** (`origin = local-sim`, `OriginNotWired`). Harness `spike/gate_a/`.
- **Supabase/Live path** exists (DSN in env only, never in the repo; password rotated 5 Oct 2026 after a leak). Detail in the daily logs.

- **The Gate B ambiguity blocker was the vocabularies, not a missing second scorer** (found 8 Oct 2026, verified by running the scorers). It is closed by the cut: the run is removed, so nothing queues and nothing blocks, and no second scorer is needed.

- **Route 2 is built (8 Oct 2026): the scorer reads the option, not the words.** `scoring.py` carries derived `ACTION_OPTIONS` / `DEADLINE_OPTIONS` and `score_action_option` / `score_deadline_option`; `OutcomeRow` carries `action_option` / `deadline_option` and keeps the words in `action_recall`. "I don't know" is `incorrect`. The word vocabularies stay (section 17's measurement; the Slice 8 guards pin them) but no longer score a row. `tests/test_study.py` is byte-identical, so the pinned `DIFFERENT_ACTION_FORMS == ()` was **not** amended. **P2 in `_mutate_slice8.py` was orphaned by the 8 Oct section 17 amendment and is repointed:** a harness that anchors into moved text goes blind quietly.

## Hard-won lessons (full record: `tasks/lessons.md`)

- **A Postgres-gated claim is not verified until it runs on the real engine.** `LIKE ... INCLUDING CONSTRAINTS` does not copy `DEFAULT`s; use `INCLUDING CONSTRAINTS INCLUDING DEFAULTS`, wrap scratch work in a `SAVEPOINT`.
- **A skipped test is not a passing test.** Skips sit on the class that needs the engine, never module scope.
- **Python validates a `.pyc` against source mtime and size only, never content.** Delete `__pycache__`; `PYTHONDONTWRITEBYTECODE=1` on children.
- **The Edit tool rewrites the whole file and has reversed CRLF to LF.** For a CRLF patch at byte level: read bytes, normalise `\r\n` to `\n`, replace, convert once back, assert no `\r\r\n`. This file and `~/.workbuddy-ai/USER.md` are CRLF; `.workbuddy-ai/memory/YYYY-MM-DD.md` is LF.

## Running things

- **No venv in the project.** Interpreter `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe` (3.13.x, pytest 9.x). Run `PYTHONPATH=src <python> -m pytest -o addopts="" -q`. (`pyproject.toml` sets `addopts = "-q"`, so a second `-q` suppresses the summary.)
- **A backgrounded server dies between Bash calls.** Start uvicorn, `sleep 5`, curl, kill **in one call**.
- **Every `git` command here prints a `PROGRAM BLOCKED BY SECURITY POLICY` note** naming `reg.exe`/`sc.exe`. The command still succeeds.
- **Local Postgres for tests:** Docker container `carerelay-pg`, port **15432**, `CARERELAY_TEST_DSN="postgresql://carerelay:carerelay_test@127.0.0.1:15432/carerelay"`. Without it every Postgres-gated test skips. Docker Desktop **cannot be started from the sandbox**; Jaydon starts it by hand.
- **`psycopg` pinned to 3.3.5** (3.3.6 `_psycopg` `.pyd` is blocked by Windows Application Control).
- **Never run two pytest processes against `carerelay-pg` at once.** Alone the whole suite is ~40 s.
- Jaydon's shell is **PowerShell**. Use `$env:VAR = '...'`. Route credentials through a read prompt, never into chat.

## Patient copy, approved 2 October 2026

Line 1 "No one has agreed to help yet." / line 2 "Please act now." (self) or "Please act now: you, or [name]." / line 3 "Please do it before [deadline]." / line 4 "If that does not work, call [route]." Expired: "It is past [deadline]. Please go now." / "Call [route]. They can help from here."

Binding rules: **no exclamation marks, no invented capability**. Authored, unsourced, non-clinical. `PERMITTED_CHANGE_CODES` stays empty, `approved_by` stays NULL. Never cite a style guide, hotel brand or hospitality source. Tone authority is the five copy rules in `02-architecture.md` s7. Sourcing cannot substitute for a reviewer (MOH clause 11, HealthHub clause 12.1).
