# MEMORY.md: CareRelay project

Curated long-term project notes. Daily logs live beside this file.

## Working conventions

- **Prompts go in chat, not on disk.** When Jaydon asks for a copy-paste prompt (handover prompt, review brief, agent prompt), deliver the text in the reply. Do not write it as an untracked `.md` in the repo. Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes are banned in new writing** (`AGENTS.md` section 6). The rule beats the local house style, which is full of em dashes. Verify the added-lines U+2014 count before handoff, not after.
- **CRLF everywhere**, except `.gitignore`, `CareRelay.md`, `ai-triage_casestudy2.md` and `tools/git-switch-safe.sh`. Verify with `b.count(b'\n') - b.count(b'\r\n') == 0`.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` is operational memory and may never imply an approval.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` section 5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.

## Current state, 30 September 2026

- Gates 1, 2 (revision 3), 3 and 4 are all **APPROVED**. Slice 4 is next and may begin.
- Stack: Python 3.13 + FastAPI + SQLite on **Render** with a mounted persistent disk; **Next.js** clinical frontend on **Vercel**; **ADP additive only** (interpretation step, never execution or rendering).
- Plan: 14 slices, Slice 0 to Slice 13, **122 to 203 h** against 16 days of capacity.
- `src/carerelay/demo/fixture.py` carries an uncommitted change that is **not the agent's** and was deliberately left alone.
