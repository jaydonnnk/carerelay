# MEMORY.md: CareRelay project

Curated long-term project notes. Daily logs live beside this file.

## Working conventions

- **Prompts go in chat, not on disk.** When Jaydon asks for a copy-paste prompt (handover prompt, review brief, agent prompt), deliver the text in the reply. Do not write it as an untracked `.md` in the repo. Only reviews are written to disk, under `docs/reviews/`.
- **Em dashes are banned in new writing** (`AGENTS.md` section 6). The rule beats the local house style, which is full of em dashes. Verify the added-lines U+2014 count before handoff, not after.
- **CRLF everywhere**, except `.gitignore`, `CareRelay.md`, `ai-triage_casestudy2.md` and `tools/git-switch-safe.sh`. Verify with `b.count(b'\n') - b.count(b'\r\n') == 0`. Nuance found 1 Oct 2026: `core.autocrlf=true` and there is **no `.gitattributes`**, so every blob is LF regardless, and the four exempt files are LF in the worktree too. Only authoring discipline keeps the rest CRLF. A fresh clone would check everything out as CRLF, so the exemption is latent rather than enforced. Do not "fix" this with a `.gitattributes` renormalise before a push.
- **The session logs are published at `docs/session-logs/`.** Live files stay at `.workbuddy-ai/memory/` (git-ignored). The published copy is refreshed when a slice ships. `.workbuddy-ai/skills/` holds third-party skills with **no licence or author field** and must **never** be published: the challenge requires the project to be original.
- **Em dashes in imported records are kept.** The `AGENTS.md` section 6 ban is on *new writing*. A published historical log is not new writing, and stripping its em dashes would falsify the record. Disclose the count instead.
- **One edit per file per message.** Concurrent edits to one file silently lose writes.
- **`00-status.md` is the only authority for gate and slice state.** `PROGRESS.md` is operational memory and may never imply an approval.
- **Editing an approved gate document reopens that gate** (`AGENTS.md` section 5).
- **Never commit or push without an explicit instruction.** A commit instruction is not a push instruction.

## Current state, 1 October 2026

- Gates 1, 2 (revision 3), 3 and 4 are all **APPROVED**.
- **Slice 4 is SHIPPED but NOT COMPLETE.** Committed, fast-forwarded into `main`, and pushed. It is not marked complete because **the user's walkthrough has not happened**.
- Slice 4 verdict from the adversarial review: **APPROVE WITH CHANGES**. B1 and B2 closed; B3 is a claim correction with the rule deliberately unchanged. Six non-blocking findings (NF1 to NF6) are carried in `tasks/todo.md`, each anchored to the slice where it becomes live.
- **The intake and assessment path is scheduled in no slice.** Slice 4 closed it narrowly and correctly in shape. The full clarification loop is still unowned and unestimated.
- **`COORDINATOR_FALLBACK_TEXT` needs a Gate 1 touch.** Authored patient-facing copy with no approved source.
- Stack: Python 3.13 + FastAPI + SQLite on **Render** with a mounted persistent disk; **Next.js** clinical frontend on **Vercel**; **ADP additive only** (interpretation step, never execution or rendering).
- Plan: 14 slices, Slice 0 to Slice 13, **122 to 203 h** against 16 days of capacity.
- `src/carerelay/demo/fixture.py` is **clean and committed**. The earlier note that it carried an uncommitted change that was "not the agent's" was **stale**: that change was committed on 30 September 2026, and the Slice 4 policy block that followed is the agent's own work.
- Test suite: **383 passed, 1 warning**. Per file: 95 domain, 141 boundaries, 25 api, 91 state, 31 service.
- `pytest` sets `addopts = "-q"` in `pyproject.toml`, so passing another `-q` makes it `-qq` and **suppresses the summary line**. Use `-o addopts="" -q` to see the count.
