# MEMORY.md: CareRelay project

Curated long-term notes. Daily logs beside this file (append-only) hold the full detail; `tasks/lessons.md` is the full technical record.

## Working conventions

- **Prompts go in chat, not on disk.** Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes (U+2014) are banned in new writing** (`AGENTS.md` s6). Historical em dashes are kept and the count disclosed, never stripped. Verify a doc edit by counting U+2014 on `+` lines minus `-` lines in `git diff -U0`, not by grepping the file.
- **CRLF everywhere**, except five tracked files that are LF on purpose: `CareRelay.md`, `ai-triage_casestudy2.md`, `tools/git-switch-safe.sh`, `tests/test_boundaries.py`, `.gitignore`. Check `b.count(b"\n") - b.count(b"\r\n") == 0`. Blobs are LF (`core.autocrlf=true`); only authoring discipline keeps the worktree CRLF. Never renormalise before a push. The `Write` tool emits LF, so normalise immediately after.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` may never imply approval; `AGENTS.md` s3 also states slice state and drifts.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` s5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.
- **One question at a time** with Jaydon.
- **Checkboxes in `tasks/todo.md` go stale silently.** Verify against `00-status.md` or commit history; never tick on a forecast.
- Session logs publish to `docs/session-logs/`; live files stay in `.workbuddy-ai/memory/` (git-ignored). `.workbuddy-ai/skills/` holds third-party skills with no licence or author and must **never** be published.

## State (verified 8 Oct 2026)

- **All four gates APPROVED.** Gates 1 and 2 were reopened and re-approved 8 Oct 2026 for the closure renderings (Gate 1 closed when mockups 06/07 existed). Gate 4 was reopened and re-approved 8 Oct 2026 for the pre-recorded Gate B cut.
- **Slices 0-10 shipped to `main`**, in sync with `origin/main`. Suite on `main`: **890 passed, 0 skipped**. Slice branches are frozen at their closing commit, behind `main` by design; `slice-9` and `slice-10` are unpublished.
- **Slice 10** (8 Oct 2026): `POST /api/episodes/{id}/acceptances`, the expiry read-path, JSON-only `presentation.py`, a derived patient projection, `validate_owner` + `UnpermittedOwnerId`, required `policy_text` on `EpisodeService` (5 sites). **F4, F6, F6-render and §2.2 are CLOSED** by the approved closure copy; the dead `NoApprovedPatientWording` 409 path was deleted. Harness 16/16 RED.
- **Slice 9 was CUT as a run** (8 Oct 2026): no dyad recruited, so **no human-centred validation claim is made**. It is not a failed recruitment and not a null result. What shipped is the scoring instrument plus recruitment prep, as design evidence. No second scorer is needed or named.
- **Slice 11 SHIPPED to `main` 9 Oct 2026** (built 8 Oct 2026 on `slice-11-fault-harness`), six commits `e245946` to `7aa5f5b`, pure ref move because `main` and the slice branch sat at the same commit, pushed to `origin`. **The slice branch itself stays unpublished**, matching the Slice 9 and Slice 10 precedent. `tests/test_fault_sequences.py` (11 tests, seven sequences), `tests/_mutate_slice11.py` (7/7 RED), `test_scanner_detects_injected_needle`. Suite **902 passed, 0 skipped** (baseline 890, +11 +1). **No `src/` change.** Child-process SIGTERM kill proves the single transaction and closes **O8 for SQLite only**.
- **Slice 11 ADVERSARIALLY REVIEWED 8 Oct 2026: verdict SOUND, proceed to Slice 12.** All seven mutations independently re-run RED for the right reason with GREEN controls; tree restored byte-exact. Eight findings, none blocking, in `docs/reviews/slice11-adversarial-review.md` (committed). Two `00-status.md` claims were overstated and are **now corrected** (sweep commit `72b92f0`, 9 Oct 2026): "each sequence asserts I1 to I5" replaced with the measured per-sequence counts (I3 in 3 of 7, I5 in 3 of 7, I1's stored-instant half in 2 of 7), and "O8 is CLOSED" qualified to SQLite-only with the Postgres reason stated. **R1, R2, R6 and R7 remain open by choice:** they are findings against the two new scanners, and fixing them is a decision about what the scanner should catch, not a record sweep.
- **Slice 12 CODE HALF BUILT 9 Oct 2026 on `slice-12-ledger`** (cut from `main`), uncommitted and unreviewed. `GET /api/episodes/{id}/ledger` and `/options` at the paths `02-architecture.md` 3.1 names; `presentation.py` gained `RouteOption` / `OptionsSurface` / `FaultAssertion` / `LedgerSurface` (JSON only); `service.py` gained `project_ledger`, `permitted_options` and `_fault_assertions`; `frontend/app/ledger/page.tsx` plus `getLedger` in `frontend/lib/api.ts`. Suite **927 passed, 0 skipped** (baseline 902). Harness `tests/_mutate_slice12.py` **8 of 8 RED**. **The ledger never writes:** the patient read is the expiry trigger and a judge read is not, so `project_ledger` skips the expiry read-path and says so. **The submission half of Slice 12 is NOT STARTED** (title, blurb, description, cover, diagrams, walkthrough, honest-claims statement, usage proof).
- **No top-level `/ledger` or `/options` alias, on purpose.** The bearer dependency enforces on a prefix test installed once on the app, so `/api` is guarded and a top-level `/options` would not be. `/ledger` is already in `GUARDED_PREFIXES`, but no alias was added.
- Stack: Python 3.13 + FastAPI; **record is Postgres on Supabase** via `APP_DATABASE_URL` (Slice 7b; SQLite remains for local demo and tests); Next.js on Vercel; **ADP additive only**. 14 slices (0-13), deadline 16 Oct 2026.
- **B3 CLOSED without a clinical reviewer** (substring to exact normalised match; narrowing is not reviewer-gated, widening is).
- **Gate A access spike PASSED 2 Oct 2026.** ADP `https://wss.lke.tencentcloud.com/adp/v2/chat`; auth is the **`AppKey` request-body** field; failures arrive as **HTTP 200 with an SSE `event: error` frame**. Transport only, not tool execution. Harness `spike/gate_a/`.
- **The Gate B ambiguity blocker was the vocabularies, not a missing second scorer.** Closed by the cut.
- **Route 2 (8 Oct 2026): the study scorer reads the option, not the words.** `scoring.py` carries derived `ACTION_OPTIONS` / `DEADLINE_OPTIONS`; word vocabularies stay for section 17's measurement but no longer score a row. `tests/test_study.py` is byte-identical, so the pinned `DIFFERENT_ACTION_FORMS == ()` was not amended. **P2 in `_mutate_slice8.py` was orphaned by that amendment and repointed.**

## Hard-won lessons (full record: `tasks/lessons.md`)

- **A ship's record sweep must go by token, not by section.** Found 8 Oct 2026: three rows (Slice 10 checklist, F4 decision table, O7 row) still read as current claims. Grep the falsified tokens (`F4`, `OPEN`, the old count) across the whole file, including checkbox lists and decision tables.
- **Mutate each entry of a detection list; most of them are dead.** Slice 11 review, 8 Oct 2026: deleting 7 of 8 facility nouns or `source_ref` left `test_scanner_detects_injected_needle` GREEN. Only the entries a needle exercises have teeth. Same shape as the Slice 8 vocabulary finding.
- **A reporting list needs a falsifiability count, not a RED total.** Slice 12, 9 Oct 2026: the ledger carries five fault assertions, and forcing each one true showed only I3 can be driven false by a sequence this build permits. I1, I2, I4 and I5 are unreachable by construction (the store refuses a backwards deadline; `derive_closure` cannot resolve without an owner or without evidence; `project_attempt` derives `failed` from the rows I5 inspects). Keep the required mutations and the probes in **separate lists** and print the ratio, so display fields are never counted as coverage.
- **Run one heavy thing at a time on this machine.** A full-suite run sat at 13 minutes with no output because a `next build` ran beside it; the same suite finished in 84.85 s alone. When a run goes quiet, kill it and re-run verbosely to a log rather than piping `-q`.
- **`next build` cannot finish in the sandbox.** It dies on the sandbox bulk-delete guard (`SAFE_DELETE_BULK_CONFIRM_REQUIRED`, threshold 50) while clearing `.next/static`. `tsc --noEmit` is the frontend check that does run.
- **A word-boundary denylist misses inflected forms.** `\bhospital\b` does not match "hospitals"; likewise wards, polyclinics, hospices, nursing homes. State the true scope or allow a plural suffix.
- **A mutation that trips a database constraint still counts as RED**; that is the second line of defence working. The harness must count `F` and `E` and say so.
- **For a crash-atomicity claim, kill a real process**; in-process raising only proves the rollback path. Child monkeypatches the store method to `os.kill(os.getpid(), SIGTERM)` after a flushed reach marker; parent asserts absent rows. On Windows SIGTERM is TerminateProcess. **Verify the parent can actually see the child's committed write**, or the assertion is vacuous (Slice 11: confirmed it can).
- **A guard that only saves a redundant write is not a guard.** Check whether the layer below already enforces the property before writing a mutation; report the survivor as the harness being right.
- **A Postgres-gated claim is not verified until it runs on the real engine.** `LIKE ... INCLUDING CONSTRAINTS` does not copy `DEFAULT`s; wrap scratch work in a `SAVEPOINT`.
- **A skipped test is not a passing test.** Skips sit on the class that needs the engine, never module scope.
- **Python validates a `.pyc` against source mtime and size only, never content.** Delete `__pycache__`; set `PYTHONDONTWRITEBYTECODE=1` on children.
- **The Edit tool rewrites the whole file and has reversed CRLF to LF.** This file is CRLF; `.workbuddy-ai/memory/YYYY-MM-DD.md` is LF.

## Running things

- **No venv in the project.** Interpreter `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe` (3.13.x, pytest 9.x). Run `PYTHONPATH=src <python> -m pytest -o addopts="" -q` (`pyproject.toml` sets `addopts = "-q"`, so a second `-q` suppresses the summary).
- **A backgrounded server dies between Bash calls.** Start uvicorn, `sleep 5`, curl, kill **in one call**.
- **Every `git` command prints a `PROGRAM BLOCKED BY SECURITY POLICY` note** naming `reg.exe`/`sc.exe`. The command still succeeds.
- **Local Postgres for tests:** Docker `carerelay-pg`, port **15432**, `CARERELAY_TEST_DSN="postgresql://carerelay:carerelay_test@127.0.0.1:15432/carerelay"`. Without it every Postgres-gated test skips. Docker Desktop **cannot be started from the sandbox**; Jaydon starts it by hand.
- **`psycopg` pinned to 3.3.5** (3.3.6 `_psycopg` `.pyd` is blocked by Windows Application Control). Never run two pytest processes against `carerelay-pg` at once.
- Jaydon's shell is **PowerShell**. Use `$env:VAR = '...'`. Route credentials through a read prompt, never into chat.

## Patient copy, approved 2 October 2026

Line 1 "No one has agreed to help yet." / line 2 "Please act now." (self) or "Please act now: you, or [name]." / line 3 "Please do it before [deadline]." / line 4 "If that does not work, call [route]." Expired: "It is past [deadline]. Please go now." / "Call [route]. They can help from here."

Binding rules: **no exclamation marks, no invented capability**. Authored, unsourced, non-clinical. `PERMITTED_CHANGE_CODES` stays empty, `approved_by` stays NULL. Never cite a style guide, hotel brand or hospitality source. Tone authority is the five copy rules in `02-architecture.md` s7. Sourcing cannot substitute for a reviewer (MOH clause 11, HealthHub clause 12.1).
