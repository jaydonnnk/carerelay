# MEMORY.md: CareRelay project

Curated long-term notes. Daily logs sit beside this file (append-only) and hold the full detail.

## Working conventions

- **Prompts go in chat, not on disk.** Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes (U+2014) are banned in new writing** (`AGENTS.md` s6). Verify the added-lines count before handoff. Em dashes inside **imported historical** records are kept and the count disclosed, not stripped.
- **CRLF everywhere**, except four tracked files: `CareRelay.md`, `ai-triage_casestudy2.md`, `tools/git-switch-safe.sh` and **`tests/test_boundaries.py`**. Verified 7 Oct 2026 by scanning `git ls-files`: 122 CRLF, 4 LF. A brand-new file written by a tool is usually LF and must be converted. Check `b.count(b'\n') - b.count(b'\r\n') == 0`. `core.autocrlf=true`, no `.gitattributes`, so blobs are LF regardless; only authoring discipline keeps the worktree CRLF. Never "fix" with a renormalise before a push.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` may never imply approval. `AGENTS.md` s3 also states slice state and **drifts**; check it, but do not trust it over `00-status.md`.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` s5). Documentation-only maintenance creates no gate.
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.
- **One question at a time** with Jaydon.
- **Checkboxes in `tasks/todo.md` go stale silently.** Verify each against `00-status.md` or commit history before ticking; never tick on a forecast.
- Session logs publish to `docs/session-logs/`; live files stay in `.workbuddy-ai/memory/` (git-ignored). `.workbuddy-ai/skills/` holds third-party skills with no licence or author and must **never** be published.

## State

- **All four gates APPROVED.** Gates 1-2 reopened by the 2 Oct patient-wording pass, re-approved same day. Gate 3 re-approved after the Option C drop. Gate 4 untouched since 30 Sep.
- **Slices 0-7b shipped and pushed.** `main` = `ac62286` (7 Oct 2026), in sync with `origin/main`. Suite on `main`: **614 passed, 0 skipped**. Slice branches are frozen at their closing commit, behind `main` by design.
- **Slice 8 built 7 Oct 2026 on `slice-8-fixed-card`, NOT committed and NOT pushed.** The fixed card and the pre-registration: `study/fixed-card.html`, `study/protocol.md`, `tests/test_study.py` (**126 tests**), `tests/_mutate_slice8.py` (**26 of 26 mutations RED, 0 SURVIVED, 0 NOT PROVEN**). Suite **740 passed, 0 skipped, 1 warning**. The Check ("the user reads the card and the frozen protocol before any participant sees either") is **COMPLETE**, Jaydon having read both on 7 Oct 2026, so the slice is **ticked** in `00-status.md` and `tasks/todo.md`. **Still not committed, pushed or staged.** **Remediated the same day** from `docs/reviews/slice8-adversarial-review.md`: B1 (the scoring vocabularies are now derived from `fixture`, and both recall scorers are three-way: correct / incorrect / raise for the second scorer), S1 (`CARD_HEADING` is read from the one `<h1>` in `api.py`, so a rename on either side fails), S2 and N3 (`javascript:`, `on*=` and CSS `url(` added to the resource patterns, each with a scanner self-test), N1 (the marker guard and the threshold guard now scan different things, so C7 and C8 fail disjoint tests), N2 (`_progress` rstrips pytest's padding: `ran` reported 73 for one test, now 1), N5 (the card comment now says "anywhere a participant can see"). **Deliberately not done: S3 and N4**, both record corrections and S3 reopens Gate 2.
- **Three carried items for Slice 9:** the small-sample reporting and scoring rules still live in the test module and **Slice 9 must lift them into the response path it builds**; **the action scorer's case 2 has no vocabulary** (`fixture.ACTION_ALIASES` carries aliases for the keyed action only), so "a different permitted action" is unreachable today and Slice 9 must decide when an alias for a second action arrives; and `02-architecture.md` section 9 still calls the comparator "a printed/PDF bilingual card" (S3, nine live documents, next Gate 2 touch).
- Stack: Python 3.13 + FastAPI + SQLite (WAL) on **Render** with a mounted disk; **Next.js** on **Vercel**; **ADP additive only** (interpretation step, never execution or rendering). Plan: 14 slices (0-13), **122-203 h**, deadline 16 Oct 2026.
- **B3 CLOSED without a clinical reviewer** — a substring match scored 200 on "help sorting out my appointment, also I have chest pain and cannot breathe", now an exact normalised match. Widening a rule is reviewer-gated; narrowing is not.
- **Gate A access spike PASSED, 2 Oct 2026** (exit 0). ADP endpoint `https://wss.lke.tencentcloud.com/adp/v2/chat`; auth is the **`AppKey` request-body** field; `ConversationId`/`RequestId` are caller-supplied `^[a-zA-Z0-9_-]{32,64}$`; failures arrive as **HTTP 200 with an SSE `event: error` frame**. It proves the **transport only, not tool execution** — `02-architecture.md` D8 keeps ADP to the interpretation step, `origin = local-sim` (`OriginNotWired`). Harness `spike/gate_a/`, 34 tests.
- **Supabase/Live path** exists (DSN in env only, never in the repo; password rotated 5 Oct 2026 after a leak). 21 pass on both pooler ports against PostgreSQL 17.11 (4 Oct 2026). Details in the daily logs.

## Hard-won technical lessons (detail in daily logs; `tasks/lessons.md` is the full record)

- **A Postgres-gated claim is not verified until it runs on the real engine.** A scratch table built with `LIKE ... INCLUDING CONSTRAINTS` does not copy `DEFAULT`s; use `INCLUDING CONSTRAINTS INCLUDING DEFAULTS`, and wrap scratch work in a `SAVEPOINT`.
- **A skipped test is not a passing test.** Skips sit on the class that needs the engine, never at module scope. Count the skip set.
- **Python validates a `.pyc` against source mtime and size only, never content.** A stale pyc ran different SQL than its source with no visible difference. Delete `__pycache__`; use `PYTHONDONTWRITEBYTECODE=1` on children. When a test contradicts its source, read `fn.__code__.co_consts`, not `inspect.getsource`.
- **Never hand-type a multi-line anchor into a mutation harness.** Build it from the file and assert it resolves exactly once.
- **Edit tool vs byte-safe patch.** The Edit tool rewrites the whole file and has **reversed CRLF to LF**. For any CRLF file patch at byte level: read bytes, normalise `\r\n`->`\n`, replace, convert once back, assert no `\r\r\n`. Note `~/.workbuddy-ai/USER.md` and this file are CRLF; `.workbuddy-ai/memory/YYYY-MM-DD.md` is LF.
- **An insertion anchor must stop before the insertion point.** Anchoring on "X\n\n**Next heading" and appending after the anchor splits that heading in two. Anchor on the last line *before* the insertion, then assert the following heading still appears intact in the result.
- **A full Postgres-gated mutation run costs 20-30 min** (the module-scope `engine` fixture rebuilds 14 tables and 42 triggers per child). Run it in the background; never start a second: a file edit mid-run makes the harness's restore **overwrite the edit**.
- **`COMMIT` on an aborted PostgreSQL transaction does not fail.** It returns the `ROLLBACK` tag with no error and psycopg 3's `_commit_gen` ignores the result. The transaction is silently discarded. So "catching without a savepoint makes the commit fail" is **false**; the real consequence is losing the whole transaction.
- **`git diff --check` does not flag lines over 79 chars**; long single-line records in `tasks/todo.md` and `00-status.md` are by design. Length is not enforced; the em dash rule and CRLF are.

## Running things

- **No venv in the project.** Interpreter `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe` (3.13.x, pytest 9.x, fastapi). Run `PYTHONPATH=src <python> -m pytest -o addopts="" -q`. (`pyproject.toml` sets `addopts = "-q"`, so a second `-q` suppresses the summary.)
- **A backgrounded server dies between Bash calls.** Start uvicorn, `sleep 5`, curl, kill **in one call**.
- **Every `git` command here prints a `PROGRAM BLOCKED BY SECURITY POLICY` note** naming `reg.exe`/`sc.exe`. The command still succeeds. Not a failure.
- **Local Postgres for tests:** Docker container `carerelay-pg`, port **15432**, `CARERELAY_TEST_DSN="postgresql://carerelay:carerelay_test@127.0.0.1:15432/carerelay"`. Without it every Postgres-gated test skips. Docker Desktop **cannot be started from the sandbox** — Jaydon starts it by hand.
- **`psycopg` is pinned to 3.3.5** (7 Oct 2026): 3.3.6's `_psycopg` `.pyd` is blocked by Windows Application Control (WinError 4551).
- **Never run two pytest processes against `carerelay-pg` at once.** Contending runs hang at teardown with zero DB activity and zero CPU. Alone the whole suite takes ~40 s.
- Jaydon's shell is **PowerShell**, not Git Bash. Use `$env:VAR = '...'`. Route credentials through a read prompt, never into chat.

## Patient copy, approved 2 October 2026

Line 1 "No one has agreed to help yet." / line 2 "Please act now." (self) or "Please act now: you, or [name]." / line 3 "Please do it before [deadline]." / line 4 "If that does not work, call [route]." Expired: "It is past [deadline]. Please go now." / "Call [route]. They can help from here."

Binding rules: **no exclamation marks, no invented capability**. Authored, unsourced, non-clinical. `PERMITTED_CHANGE_CODES` stays empty, `approved_by` stays NULL. Never cite a style guide, hotel brand or hospitality source: it lowers the authority. Tone authority is the five copy rules in `02-architecture.md` s7. Sourcing cannot substitute for a reviewer (MOH clause 11, HealthHub clause 12.1).
