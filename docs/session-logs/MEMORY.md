# MEMORY.md: CareRelay project

Curated long-term project notes. Daily logs live beside this file.

## Working conventions

- **Prompts go in chat, not on disk.** A copy-paste prompt (handover, review brief, agent prompt) is delivered in the reply. Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes are banned in new writing** (`AGENTS.md` section 6). Verify the added-lines U+2014 count before handoff. Em dashes inside **imported historical** records are kept and the count disclosed, not stripped.
- **CRLF everywhere**, except `.gitignore`, `CareRelay.md`, `ai-triage_casestudy2.md`, `tools/git-switch-safe.sh`. Verify `b.count(b'\n') - b.count(b'\r\n') == 0`. `core.autocrlf=true` and there is no `.gitattributes`, so blobs are LF regardless; only authoring discipline keeps the worktree CRLF. Do not "fix" with a renormalise before a push.
- **Session logs are published at `docs/session-logs/`**; live files stay at `.workbuddy-ai/memory/` (git-ignored). `.workbuddy-ai/skills/` holds third-party skills with no licence or author field and must **never** be published.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` may never imply an approval.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` section 5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.
- **One question at a time** when asking Jaydon.

## Current state, 3 October 2026

- **All four gates are APPROVED.** Gates 1 and 2 were reopened by the 2 October patient-wording pass and re-approved the same day ("I have read and i re approve both gates"). Gate 3 was re-approved after the Option C drop. Gate 4 untouched since 30 Sep.
- **Slices 0 to 5 are COMPLETE (committed and pushed). Slice 6 is BUILT on `slice-6`, 3 October 2026 afternoon, UNCOMMITTED and UNPUSHED.** Action path (`POST /actions`, `POST /callbacks/{route_id}`, `POST /consents`), `simulated_provider.py`, `tools.py` (three MCP tools, three rechecks each), `coordinator.execute_tool`, `OriginNotWired`. F5 split, O2 `LockContention`, O5 `ReceiptOutcome`, NF5 honest boundary claim, all closed. 482 pass, 11 mutations RED. Live curl proven. Awaiting the Slice 6 Check. No gate authorises a commit.
- Test suite at the last full run: **482 passed, 1 warning** (was 419 before Slice 6; +53 across coordinator/service/api/state).
- **Gate A limit, honoured at Slice 6:** the spike proved the transport carries an origin signal, not tool execution. D8 forbids ADP carrying the section 3.3 claim, so `origin = local-sim` everywhere and no external call is wired. The honesty is encoded as `OriginNotWired`, which rejects a caller-stated `platform`.
- Plan: 14 slices, Slice 0 to 13, **122 to 203 h** against 16 days. Deadline 16 Oct 2026.
- Stack: Python 3.13 + FastAPI + SQLite (WAL) on **Render** with a mounted persistent disk; **Next.js** clinical frontend on **Vercel**; **ADP additive only** (interpretation step, never execution or rendering).
- **B3 is CLOSED without a clinical reviewer.** It was a logic defect, not a clinical one: the intake binding rule was a substring match, so "help sorting out my appointment, also I have chest pain and cannot breathe" scored 200. It is now an exact normalised match. Widening a rule is reviewer-gated; narrowing one is not.

## Patient copy, approved 2 October 2026

Line 1 "No one has agreed to help yet." / line 2 "Please act now." (self) or "Please act now: you, or [name]." / line 3 "Please do it before [deadline]." / line 4 "If that does not work, call [route]." Expired: "It is past [deadline]. Please go now." / "Call [route]. They can help from here."

Binding rules: **no exclamation marks**, **no invented capability**. The copy is **authored, unsourced and non-clinical**; it asserts no clinical claim and that absence is what makes it honest. `PERMITTED_CHANGE_CODES` stays empty and `approved_by` stays NULL. **Never add a citation to a style guide, hotel brand or hospitality source: it lowers the authority.** The tone authority is the five copy rules in `02-architecture.md` section 7. **Sourcing cannot substitute for a reviewer** (MOH clause 11 and HealthHub clause 12.1 both require prior written permission); a licence to quote is not authority to act.

## Gate A access spike: RUN AND PASSED, 2 October 2026

- **PASS, exit 0.** Q1 `request_ack` returned; Q2 proven by recall (two separate clients sharing only a `ConversationId`; turn 2 answered "lantern"); Q3 a platform error frame with numeric `Code` and populated `TraceId`. The `AGENTS.md` `local-sim` reversal for *access* does not apply.
- **ADP endpoint** `https://wss.lke.tencentcloud.com/adp/v2/chat`. Auth is the **`AppKey` request-body field**, not a header; only documented header is `Content-Type: application/json`. There is no second secret.
- **`ConversationId` and `RequestId` are caller-supplied**, `^[a-zA-Z0-9_-]{32,64}$`. The platform issues no session id.
- **Failures arrive as HTTP 200 carrying an SSE `event: error` frame**, never HTTP 4xx. A bare 200 is not success; the harness requires `request_ack`.
- Harness `spike/gate_a/probe.py` + `test_probe.py`, 34 tests, three mutations each RED. Result JSON is git-ignored. Exit codes: PASS 0, PARTIAL/FAIL 1, BLOCKED_NO_CREDENTIAL 2.
- **The limit that matters for Slice 6:** the spike proves the **transport** carries an origin signal. It does **not** prove tool execution. Q3's failure was a validation rejection provoked by an empty `ConversationId`. Wiring ADP into `src/` is separate later work, and `02-architecture.md` D8 says ADP may occupy the **interpretation step only** and **cannot carry the section 3.3 claim**.
- **Jaydon's shell is PowerShell**, not Git Bash. Use `$env:VAR = '...'`; the `VAR=value cmd` prefix and a trailing `\` continuation both fail. Route credentials through a read prompt, never into the chat.

## Running things

- **There is no venv in the project.** Interpreter: `C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe` (3.13.x, pytest 9.x, fastapi). Run with `PYTHONPATH=src <that python> -m pytest -o addopts="" -q`.
- `pyproject.toml` sets `addopts = "-q"`, so another `-q` makes it `-qq` and **suppresses the summary line**. Use `-o addopts=""`.
- **A backgrounded server dies between Bash calls.** Start `uvicorn`, `sleep 5`, curl, `kill` **in one call**.
- **Mutation harness:** `cp` the source aside, patch with a small string replace, run the targeted test with `-k`, restore, re-run the full suite. Report the count of mutations seen RED.
