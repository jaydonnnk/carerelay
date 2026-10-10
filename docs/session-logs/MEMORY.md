# MEMORY.md: CareRelay project

Curated long-term notes. Daily logs beside this file (append-only) hold the detail; `tasks/lessons.md` is the full technical record. Condensed 10 Oct 2026 to fit the injection limit.

## Working conventions

- **Prompts go in chat, not on disk.** Only reviews get written to `docs/reviews/`.
- **Em dashes (U+2014) banned in new writing** (`AGENTS.md` s6). Historical ones are kept and the count disclosed. Verify by counting U+2014 on `+` minus `-` lines in `git diff -U0`.
- **CRLF everywhere**, except five LF-on-purpose files: `CareRelay.md`, `ai-triage_casestudy2.md`, `tools/git-switch-safe.sh`, `tests/test_boundaries.py`, `.gitignore`. Check `b.count(b"\n") - b.count(b"\r\n") == 0`. Blobs are LF (`core.autocrlf=true`); never renormalise before a push. The `Write` tool emits LF, so normalise immediately.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** Editing an approved gate document reopens that gate (`AGENTS.md` s5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.
- **One question at a time** with Jaydon.
- `tasks/todo.md` checkboxes go stale silently; verify against `00-status.md` or history.
- Logs publish to `docs/session-logs/` (re-sync at every ship). `.workbuddy-ai/skills/` must **never** be published (third-party, no licence).

## State (verified 9 Oct 2026)

- **All four gates APPROVED.** Gates 1 and 2 reopened and re-approved 8 Oct 2026 for the closure renderings; Gate 4 reopened and re-approved 8 Oct 2026 for the pre-recorded Gate B cut.
- **Slices 0-11 shipped to `main`**, in sync with `origin/main`. Slice branches freeze at their closing commit and sit behind `main` by design; `slice-9`, `slice-10`, `slice-11` are unpublished.
- Suite on `main`: **902 passed, 0 skipped**.
- **Slice 11** shipped 9 Oct 2026 (six commits `e245946` to `7aa5f5b`, pure ref move, pushed). `tests/test_fault_sequences.py` (11 tests, seven sequences), `_mutate_slice11.py` 7/7 RED, no `src/` change. Child-process SIGTERM proves the single transaction and closes **O8 for SQLite only**. **Adversarially reviewed: verdict SOUND.** Eight non-blocking findings in `docs/reviews/slice11-adversarial-review.md`; two overstated `00-status.md` claims corrected in sweep `72b92f0`. **R1, R2, R6, R7 remain open by choice** (they are decisions about what the scanner should catch).
- **Slice 9 was CUT as a run** (8 Oct 2026): no dyad recruited, so **no human-centred validation claim is made**. Not a failed recruitment, not a null result.
- **Slice 12 CODE HALF SHIPPED 10 Oct 2026** (built 9 Oct on `slice-12-ledger`): six commits `b87d402` to `046237c`, pure ff merge to `main`, pushed. Suite **927 passed** measured 9 Oct; **852 passed** re-measured 10 Oct, the 75 gap being three modules `psycopg` cannot import. `GET /api/episodes/{id}/ledger` and `/options`; `presentation.py` gained `RouteOption` / `OptionsSurface` / `FaultAssertion` / `LedgerSurface` (JSON only); `service.py` gained `project_ledger`, `permitted_options`, `_fault_assertions`; `frontend/app/ledger/page.tsx` + `getLedger`. Suite **927 passed, 0 skipped**. Harness `_mutate_slice12.py` 8/8 RED. **The ledger never writes** (the patient read is the expiry trigger, a judge read is not). **The submission half is NOT STARTED** (title, blurb, description, cover, diagrams, walkthrough, honest-claims statement, usage proof). **The ledger is served at two paths**: `/api/episodes/{id}/ledger` and, since 10 Oct 2026, the alias `/ledger/{id}` (stacked decorators, one implementation), which is what makes `02-architecture.md:296` true without editing that gate document. `/options` has no twin: it is not a guarded prefix.
- Stack: Python 3.13 + FastAPI; **record is Postgres on Supabase** via `APP_DATABASE_URL` (SQLite for local demo and tests); Next.js on Vercel; **ADP additive only**. 14 slices (0-13), deadline 16 Oct 2026.
- **B3 CLOSED without a clinical reviewer** (substring to exact normalised match; narrowing is not reviewer-gated).
- **Gate A spike PASSED 2 Oct 2026.** ADP `https://wss.lke.tencentcloud.com/adp/v2/chat`; auth is the **`AppKey` request-body** field; failures are **HTTP 200 with an SSE `event: error` frame**. Transport only. Harness `spike/gate_a/`.
- **Route 2 (8 Oct 2026): the study scorer reads the option, not the words.** `scoring.py` carries derived `ACTION_OPTIONS` / `DEADLINE_OPTIONS`. `_mutate_slice8.py` P2 was orphaned by that and repointed.

## Hard-won lessons (full record: `tasks/lessons.md`)

- **A ship's record sweep goes by token, not by section.** Grep the falsified tokens (`F4`, `OPEN`, the old count) across the whole file, including checkbox lists and decision tables.
- **Mutate each entry of a detection list; most are dead.** Deleting 7 of 8 facility nouns left the scanner test GREEN. Only entries a needle exercises have teeth.
- **A reporting list needs a falsifiability count, not a RED total.** Of the ledger's five fault assertions only I3 can be driven false; I1, I2, I4, I5 are unreachable by construction. Keep required mutations and probes in **separate lists** and print the ratio.
- **Run one heavy thing at a time.** A full suite sat at 13 minutes beside a `next build` and finished in 84.85 s alone.
- **`next build` cannot finish in the sandbox** (bulk-delete guard while clearing `.next/static`). `tsc --noEmit` is the frontend check that runs.
- **A word-boundary denylist misses inflected forms** (`\bhospital\b` misses "hospitals").
- **A mutation that trips a DB constraint still counts as RED**; count `F` and `E`.
- **For crash atomicity, kill a real process** (child `os.kill(os.getpid(), SIGTERM)` after a flushed reach marker). Verify the parent can see the child's committed write or the assertion is vacuous.
- **A guard that only saves a redundant write is not a guard.** Check the layer below first.
- **A Postgres-gated claim is not verified until it runs on the real engine.** `LIKE ... INCLUDING CONSTRAINTS` does not copy `DEFAULT`s; wrap scratch work in a `SAVEPOINT`.
- **A skipped test is not a passing test.** Skips sit on the class needing the engine, never module scope.
- **Python validates a `.pyc` against mtime and size only.** Delete `__pycache__`; `PYTHONDONTWRITEBYTECODE=1` on children.
- **The Edit tool has reversed CRLF to LF.** This file is CRLF; the daily logs are LF.
- **A pinned dependency can still be blocked without being changed.** 10 Oct 2026: `psycopg` 3.3.5 and its binary wheel were both intact on disk, but Windows Application Control blocked the `pq` extension at load, so three modules (75 tests) stopped collecting overnight and the suite fell from 927 to 852. Check `import psycopg` before blaming the code, and rule out the sandbox by re-running with it disabled.

## Running things

- **No venv in the project.** `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe`, `PYTHONPATH=src`, `pytest -o addopts="" -q` (a second `-q` suppresses the summary).
- **A backgrounded server dies between Bash calls.** Start uvicorn, `sleep 5`, curl, kill **in one call**.
- **Every `git` command prints a `PROGRAM BLOCKED BY SECURITY POLICY` note** naming `reg.exe`/`sc.exe`. It still succeeds.
- **Local Postgres for tests:** Docker `carerelay-pg`, port **15432**, `CARERELAY_TEST_DSN="postgresql://carerelay:carerelay_test@127.0.0.1:15432/carerelay"`. Without it every Postgres-gated test skips. Docker Desktop cannot be started from the sandbox.
- **`psycopg` pinned to 3.3.5** (3.3.6 `.pyd` blocked by Windows Application Control). Never run two pytest processes against `carerelay-pg` at once.
- Jaydon's shell is **PowerShell** (`$env:VAR = '...'`). Route credentials through a read prompt, never into chat.

## Patient copy, approved 2 October 2026

Line 1 "No one has agreed to help yet." / line 2 "Please act now." (self) or "Please act now: you, or [name]." / line 3 "Please do it before [deadline]." / line 4 "If that does not work, call [route]." Expired: "It is past [deadline]. Please go now." / "Call [route]. They can help from here."

Binding: **no exclamation marks, no invented capability**. Authored, unsourced, non-clinical. `PERMITTED_CHANGE_CODES` empty, `approved_by` NULL. Never cite a style guide or hospitality source. Tone authority is the five copy rules in `02-architecture.md` s7. Sourcing cannot substitute for a reviewer (MOH clause 11, HealthHub clause 12.1).
