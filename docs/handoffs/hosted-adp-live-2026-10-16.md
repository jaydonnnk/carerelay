# Handoff: hosted ADP read-back with a durable reservation guard

Copy everything below the line into a fresh agent session opened at the repository root.

---

You are continuing CareRelay, a hackathon project due 16 October 2026, in `/Users/jayd0/Desktop/carerelay`.
Your job is to make Tencent ADP read-back extraction run live on the public Render deployment, safely metered by a durable reservation guard that lives in this repository.

## Authority, quoted and bounded

- The user answered "Ive already set the ADP credentials on render( i approve hosted adp, so mark that down)". This is recorded in `docs/plans/urgent-advice-accessibility/00-status.md`, section "Hosted ADP approval: 16 October 2026".
- That approves hosted ADP in principle. It does not approve switching it on before the guard exists, and it does not approve any commit, push, merge or deployment command. Ask for those at the end, as one question.
- Earlier standing authority: "I give full approval for all live calls" (fictional ADP requests, recorded in `AGENTS.md`). Every call must still be reserved before transmission.
- Unchanged and not yours to change: the v2 schema, instruction v2, the 15-second whole-response cap, all byte limits, exactly one transport call per extraction, no retry, no lexical fallback, code-owned decisions, fictional-only processing. Changing any of them needs a prepared gate amendment and explicit approval.

## The danger to keep in mind

`configured_readback_extractor` in `src/carerelay/adp_extraction.py:831` switches to live ADP as soon as `ADP_EXTRACTION_ENABLED=true` is set.
Nothing in the repository meters those calls today.
The only guard that ever ran is a temporary local harness at `/private/tmp/carerelay-s21-product-20261015/harness/` (`live_guard.py`, `guarded_server.py`, `test_live_guard.py`, `mutate_live_guard.py`, `ledger.py`).
`/private/tmp` can be wiped on reboot, so copy those files somewhere durable outside the repository first, then read them as the reference design.
Never ask the user to set `ADP_EXTRACTION_ENABLED` on Render until your slice Check passes and the user accepts it.
The site is public: anyone who opens the patient page can trigger an extraction, so a ceiling is a safety control, not bookkeeping.

## Read first

1. `AGENTS.md`: process rules, evidence labels, the gate workflow, the Slice 21 live-evidence records and their lessons.
2. `docs/plans/urgent-advice-accessibility/00-status.md`: the "Hosted ADP approval", "Patient wording change" and Slice 21 to 23 sections.
3. `docs/reviews/adp-readback-observations.md`: observed ADP behaviour, latency of 5.1 to 6.2 s, and refusal cases.
4. `src/carerelay/adp_extraction.py`, `src/carerelay/postgres_store.py`, `src/carerelay/state.py`, `src/carerelay/api.py`.
5. `tasks/lessons.md`, above all the entries on spurious reservations, scanner gaps and mutation anchors.

## Step 1: gate amendments, then stop for approval

Draft these and ask the user exactly: `Approve Gates 2, 3 and 4 as drafted, or what should change?`

- Gate 2 (`02-architecture.md`, new section 15): the durable reservation guard.
  - A reservation row is committed in the application database before the HTTPS socket opens, inside the transport, so no code path can send unreserved.
  - The request id is written in that row.
  - States: reserved, finished, and void with no transmission. A row is finished on every outcome: valid, refused, invalid, timeout or transport error.
  - A refusal sends nothing and shows the existing approved unavailable sentence.
  - Refusal reasons: halted, unfinished reservation, ceiling reached.
  - Any transport, timeout or invalid result counts against the ceiling and halts later sends until an operator clears the halt.
  - The table is append-only, with triggers like the existing 14 tables, on both SQLite and Postgres.
  - Concurrency: two workers or two tabs must not exceed a ceiling. Use one locked counter row, or an equivalent the engine proves.
- Gate 3 (`03-program-design.md`, new section 11): the module, the table DDL, the transport hook, the operator commands (status, clear halt) and the configuration names.
- Gate 4 (`04-slices.md`, new Slice 24): the exit contract and the evidence list from Step 3.
- Ceilings are a product decision. Ask the user for numbers in the same message; do not invent them. Suggest per-episode, per-day and total ceilings, and say what happens when one is reached.
- Draft wording for any new patient or judge string, for example a judge line saying live ADP was used and what happens at the ceiling. Gate 1 needs those exact strings approved too.

## Step 2: build, after approval

- Create the branch `slice-24-hosted-adp-guard` from current `main`. Confirm with `git branch --show-current` before the first edit.
- Implement in the narrowest layer: the store and its schema, the transport wrapper and `configured_readback_extractor`.
- The guard must be impossible to bypass: when `ADP_EXTRACTION_ENABLED` is true and no guard can be built (for example a missing ceiling configuration), fail closed to the unavailable sentence. Never fall back to unguarded sends or to local scoring.
- Keep the default exactly as today: offline, no guard needed, no ADP contact.
- Verify the real environment-variable names in the code (`ADP_EXTRACTION_ENABLED`, `ADP_CHAT_ENDPOINT`, `ADP_APPKEY`; `.env.example` also lists `ADP_EXPERIENCE_URL` and `ADP_API_SECRET`). Tell the user which ones Render needs. Never print, log or commit a value.

## Step 3: evidence for the Check

- Failing-first tests for every guard branch, then one named mutation per branch, each RED with an exact restore.
- Keep the harness's 14 mutation categories: reserve after send, halt ignored, unfinished ignored, ceiling ignored, lock removed, failure never halts, refusal halts, finish skipped, and the rest.
- Tests must prove the real database and its reservation rows are untouched by test runs.
- A concurrency test with two writers released together, on SQLite and on a real Postgres engine.
  - Do not use the production Supabase database. Ask the user for a disposable DSN, or record the Postgres race as unproven.
- An end-to-end offline product run through the production Next.js build and FastAPI, with a no-network stub transport. Show the reservation exists before the request, a failure halts, the next submission is refused with zero connection attempts, and the database bytes for refused sends do not change.
- A serialized leak scan of API JSON, DOM, SSR and RSC payloads, logs and the database, with planted controls that are detected: no AppKey, no thought channel, no raw SSE, no done sentinel, no ConversationId.
- Full suite against the recorded baseline: 2,200 passed, 233 skips, one existing warning. Frontend typecheck and production build if `frontend/` changes.
- Latency: ADP takes about 5 to 6 s, and the frontend scoring timeout is 20 s (`frontend/lib/api.ts`). Measure that the guard's extra writes add little. Production now sits next to a Virginia Supabase project, at about 0.5 s per journey step.

## Step 4: going live, only after the Check is accepted

1. Ask the user for commit, merge-to-main and push authority, as one question.
2. After the push, the user redeploys Render (auto-deploy is off), sets the ceiling variables, then sets `ADP_EXTRACTION_ENABLED=true`.
3. Make one fictional live submission on `https://carerelay-self.vercel.app` using `I will go to the clinic today before 6pm`.
4. Record the request id, the timing, the reservation row, the judge stage's provenance text and a leak scan of that one response.
5. Stop at the first unexpected result, record it, and ask before any further live call.

## Stop and ask when

- Any approval above is missing, or a change would touch the schema, cap, byte limits, retry rules or code authority.
- You would need a credential value, production database access or a deployment command.
- Three materially different attempts at one step have failed.

Write in plain dashes, never the em dash. Put each sentence on its own line in long Markdown. Label every claim [verified], [vendor claim], [hypothesis] or [unknown].
