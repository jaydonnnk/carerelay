# CareRelay: Slice 20 continuation handoff, 15 October 2026

Supporting handoff only.
`docs/plans/urgent-advice-accessibility/00-status.md` remains the sole state authority and has NOT yet been updated for Slice 20.
The original Slice 20 instructions are in `docs/handoffs/patient-experience-slice20-2026-10-15.md`; they still control.
This file records where the interrupted session stopped.

## Copy-paste prompt for the next agent

You are continuing CareRelay Slice 20 only, in `/Users/jayd0/Desktop/carerelay` on macOS.
Read `docs/handoffs/patient-experience-slice20-2026-10-15.md` in full (its "Copy-paste prompt" section is the controlling contract), then this file, then `AGENTS.md`.
Use the `carerelay-slice-build` and `carerelay-slice-review` skills, and `architect-reviewer` for post-slice cleanup.
Do not commit, merge, push or start Slice 21.
Live ADP stays disabled.
Stop for the user's Slice 20 Check acceptance.

### 1. Git state you will find, and the first thing to do

- [verified] `main`, `origin/main` and `slice-20-accessibility-proof` all point at `6eec3fb350e6fa120244cb9d67dfa07c25681442`.
- [verified] The working tree is checked out on `main`, not on the slice branch. The reflog shows `reset: moving to HEAD` then `checkout: moving from slice-20-accessibility-proof to main` at 09:32 +0800. The previous agent did not run either command; treat it as an outside action.
- [verified] All Slice 20 edits are uncommitted and unstaged in the working tree (9 modified files, listed in section 3). Nothing is staged.
- [verified] Untracked `vibe_images/` (a cover image created 11:41) is not Slice 20 work. Leave it untouched.
- First action: snapshot the tree, the raw index and the protected video outside the repo, as the original handoff describes. Then run `git switch slice-20-accessibility-proof`; the commits are identical, so the dirty tree carries over. Confirm `git diff --stat` is unchanged afterwards.
- Protected tracked video `submission/usage-proof/Workbuddy_evidence.mp4` verified at 49,394,082 bytes, SHA-256 `cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.

### 2. Baseline and tools

- [verified] Fresh offline baseline before any edit: 2,029 passed, 232 Postgres skips, 1 Starlette warning (`/tmp/carerelay-s20-preflight/baseline-offline.log`). Preflight snapshot: `/tmp/carerelay-s20-preflight/`.
- [verified] Latest full offline suite on the current tree: 2,035 passed, 232 skips, 1 warning. Rerun after any change.
- Python: `/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python` (3.13.12, pytest 9.1.1). Node for builds: `/Users/jayd0/.workbuddy-ai/binaries/node/versions/22.22.2-6/bin`.
- [verified trap] The test suite's `node(...)` helper calls `node` from PATH, which is Node v24.21.0, not the 22.22.2 build Node. Record both versions.
- Offline env: `APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local CARERELAY_API_TOKEN='' ADP_EXTRACTION_ENABLED=false PYTHONDONTWRITEBYTECODE=1 CARERELAY_TEST_DSN=postgresql://127.0.0.1:1/carerelay_disabled PYTHONPATH=src`, with `-m pytest tests/ -o addopts='' -q --basetemp=<fresh dir>`.

### 3. Work done (uncommitted), with evidence

Source and test changes:

- `frontend/components/PatientJourney.tsx`
  - Pending command controls use `aria-disabled` through a `busy()` helper plus handler guards, instead of native `disabled`. A natively disabled control that holds focus dropped focus to BODY. This is the root cause of the known Escape/BODY failure: Escape focused "Show my plan", then the pending hide disabled it.
  - Result focus is decided after commit in a `useLayoutEffect`. A same-step update keeps a still-connected control (the consent checkbox no longer jumps to main, which was a WCAG 3.2.2 change of context). A step change, recovery or removed control focuses main. If focus is already on main, the step's `h1` (`tabIndex=-1`) takes focus instead.
  - `main` has `aria-labelledby="journey-heading journey-state"`, so focus announces the step heading and status (for example "May we share your plan? No reply yet. main").
  - One persistent `<p role="status" className="journey-live">` is always mounted. Previously status paragraphs were inserted with their text, and Safari with VoiceOver never announced them. Forms report pending through `useReportPending`. While a command is pending, stale feedback is replaced by "Loading. Nothing is confirmed yet."; fresh server feedback still wins.
  - The `?focus=show-plan` reload path focuses the opener (or main) and cleans the URL with `history.replaceState`.
  - Dialog children render the approved `reveal_notice` and `reveal_fallback`.
- `frontend/components/HintCard.tsx`: the dialog blurs the active element, calls `showModal()`, then focuses the `h2` title (`tabIndex=-1`) after two animation frames. This mirrors the approved mockup's focusable title. No `setTimeout` is used, because timers are banned.
- `frontend/app/globals.css`: `[aria-disabled="true"]` busy style; `.journey-live:empty { margin: 0; }`.
- `frontend/lib/journey.ts`: the decoder admits `reveal_notice` and `reveal_fallback` when the card is visible.
- `src/carerelay/domain/rules.py`, with explicit user approval to expand the footprint for dialog copy:
  1. The revealed card adds the approved strings "Fictional plan. No real care." and `If that does not work, call {plan.fallback_display}.`
  2. Bug found live with VoiceOver: one `interpretation_unavailable` event stuck to every later screen. The barrier screen kept saying "We could not check that answer just now"; on the waiting screen the decoder refused the stale feedback, so the patient saw "We cannot load your plan" right after requesting. A later `restatement_recorded` for the same disposition now resets interpretation. This second rules change was NOT separately approved by the user; disclose it prominently and ask.
- Tests:
  - `tests/test_journey_commands.py` adds five Slice 20 tests: pending controls stay focusable; revealed card copy; one live status region; named main; superseded unavailable (parametrized barrier and waiting).
  - `tests/test_journey_guard_inventory.py`: the one-status guard is strengthened (exactly one region, spoken only when there is something to say).
  - `tests/test_journey_decoder.py`: hand-written React hook shims gain `useLayoutEffect`. This is a forced footprint addition; disclose it.
  - `tests/_mutate_patient_experience.py` adds `add_slice20_mutations` and re-anchors two existing cases: "G22 S17 unchecked choice disables request" and "G06 one pending status". `--anchors-only` reports 851 unique anchors.

Mutation evidence (focused runs only, not the complete run):

- 13/13 pending-focus cases RED: `/tmp/carerelay-s20-live/mut-slice20-focused`.
- 6/6 dialog copy cases RED: `mut-slice20-dialog`.
- 6/6 live status and named main cases RED: `mut-slice20-live2`.
- G06 re-anchored RED: `mut-slice20-g06b`.
- 2/2 superseded-unavailable cases RED: `mut-slice20-stale`.
- Every run reported exact restores and an unchanged `git status`.
- The new render test was also RED against the HEAD `PatientJourney.tsx`, with an exact restore.

Browser evidence: headless Google Chrome 155.0.8059.79 over CDP with trusted key events. Harness scripts are in `/tmp/carerelay-s20-live/`.

- Escape proof (`focus-escape.mjs`):
  - Baseline build: all 5 close cases lost focus to BODY, and 3 stayed at BODY (`baseline-focus-escape.json`, 600 ms latency).
  - After the fix: 4 of 5 cases never leave the opener. The server-rendered case reloads the document by design: BODY for about 27 ms in the new document, then the opener, and the URL is cleaned.
  - Native modal Tab goes from the dialog to the document edge and back; background focus is refused (`fix4-tab-cycle.json`).
- Keyboard walks (`walk.mjs`), on fix4 (before the live-region and focus changes; rerun them): skip link, explicit create and select, Show and Escape, empty-answer error focus, both repair rounds, barrier radio arrows and empty error, consent checkbox, request, plus the decline and transport branches. The only BODY samples were the two deliberate full-document loads.
- Reflow (`reflow.mjs`), on fix3 for 23 cases and fix4 for 5 expired cases: desktop 1280; 320 CSS px by device-metrics override (the headless window floor is 500); 320 with Larger text; 200% text (default font 32); 200% zoom (640 CSS); 400% zoom (320 CSS). No horizontal scroll or clipping on any of the 28 screens. The only observation beyond the contract: 400% zoom plus Larger text (8x) needs scrolling to reach the dialog button. Must be rerun on the final build because the dialog gained two lines.
- Cross-surface scanner (`capture.mjs` and `scan.py`, reusing `test_boundaries` detectors), on fix4: 23 cases plus 5 expired, with loaded, shown, hidden-after-show and reloaded-after-hide states. 290 captures, 1,195 absence checks and 16,860 same-string positive controls (raw, JSON-unicode, HTML-entity and RSC-string forms). 0 leaks, 0 contradictions, RSC `text/x-component`. Must be rerun on the final build.
- Dialog failure (`dialog-failure.mjs`, fix4): API down during Show or Hide gives recovery with focus on main; keyboard Try again returns to the same episode; reload while shown reopens with focus inside; cue history keeps H2 (ledger events `shown` and `patient_hid`, `dwell_seconds` null).

VoiceOver evidence (macOS 26.5.1, Safari 26.5 (21624.2.5.11.4), VoiceOver 10). It was driven by System Events keystrokes (Option+Tab, which is Safari's default for links and buttons) and logged with `vo-poll.js` (VoiceOver `last phrase`). Markers and phrases are `vo-run*-markers.jsonl` and `vo-run*-phrases.jsonl`; merge them with `vo-transcript.py`.

Observed on fix6 to fix8 (runs 6 and 8):

- On a fresh read-back document VoiceOver reads "heading level 1 What is your plan?" then the question once.
- Empty review gives "Your words … invalid data text entry area" plus "Add your words, or show your plan."
- Pending and unavailable give "Loading. Nothing is confirmed yet." then "We could not check that answer just now. Your plan has not changed." (run 4, fix5).
- Step changes give "heading level 1 Let's check the time" and "heading level 1 What makes it difficult?" (run 8).
- Barrier: empty error "Choose one to continue."; radios "Getting there selected radio button, 2 of 3".
- Checkbox: "dimmed checked I agree to share this plan. checkbox" while busy.
- Request: "May we share your plan? No reply yet. main".
- After the operator failure callback and reload: "The request did not work main".
- On the server-rendered card, Escape speaks "Show my plan dimmed button", then the deliberate reload re-reads the page. DOM focus is on the opener (proven by one Option+Tab reaching "Try an example").

### 4. Unresolved: what is left to finish Slice 20

1. Dialog announcement with VoiceOver after pressing Show is NOT proven reliable.
   - Run 7 spoke "Your example plan web dialog with 5 items heading level 2 Your example plan". Runs 8 to 12 were silent, and VoiceOver's keyboard cursor became unreadable.
   - Those runs were contaminated: a macOS LocalAuthentication (`coreautha`) password prompt stayed open on screen. The user has now dismissed it.
   - The current HintCard approach (blur, `showModal`, title focus after two frames; build `frontend-fix10`) has had no clean VoiceOver run. Rerun at least 4 Show/Escape cycles from a clean Safari tab, and keep or revert the blur based on evidence.
2. A complete VoiceOver path on the final build is still needed: start, read-back question, empty error, pending, unavailable, uncertain or refused, repair, barrier, permission, request, failed request, Show/Escape, recovery with the API stopped, and Try again. Record every expected and observed announcement.
   - The fake transport's `refused` token produced a second "unavailable" outcome, not "uncertain". Exercise the approved uncertain feedback ("We could not confirm that. Try different words, or show your plan.") some other way, for example with the `uncertain` fixture case or words lacking an owner span.
   - Known residual: a repeated identical result after a fast check may be silent. Disclose it if it is still observed.
3. Rerun the full CDP evidence on the final build: Escape proof, the three walks, the reflow matrix (all settings, 23 plus 5 expired cases, including the dialog with its new lines), the scanner over all states, and dialog failure.
4. Run a complete current named mutation run (`tests/_mutate_patient_experience.py --run` into a fresh directory, about 45 minutes, with source writers idle), then the truthfulness harness (`tests/_mutate_truthfulness.py`, 39 expected).
5. Run frontend typecheck and production build (`./node_modules/.bin/tsc --noEmit`, `next build`) and the full offline suite.
6. Do a bounded `architect-reviewer` cleanup; scanning `tests/test_boundaries.py` should also confirm no new domain impurity.
7. Writing checks:
   - LF only.
   - No added em dash: check with Python on the `git diff -U0` plus lines.
   - `git diff --check`.
   - Gates, approved copy and manifests byte-unchanged.
   - Tree, index and video recheck against the snapshot.
8. Records:
   - Create `docs/reviews/patient-experience-browser-accessibility.md`, the exact Slice 20 review, with versions, viewport, zoom, steps, expected and observed focus and announcements, failures, fixes and limits.
   - Update `00-status.md` (Slice 20 section and checklist), `PROGRESS.md` and supporting records.
   - Show the visible result, then stop for Check acceptance.

### 5. Findings to surface to the user at Check (do not silently resolve)

- F1, fixed: Escape/BODY focus root cause, pending `disabled`.
- F2, fixed: the consent checkbox moved focus to main (change of context on input).
- F3, fixed: status live regions were never announced by Safari with VoiceOver.
- F4, fixed: VoiceOver said only "main" after step changes.
- F5, fixed with explicit approval: approved dialog copy was missing in production.
- F6, fixed WITHOUT separate approval (`rules.py`): the stale unavailable interpretation produced a false recovery after request. Ask the user to accept this footprint expansion.
- F7, open, needs a gate decision: a normal first-run bootstrap shows recovery copy "We cannot load your plan" before creating. Gate 3 (`03-program-design.md` around lines 668 to 686) specifies recovery for any absent candidate, so this cannot be changed without reopening Gate 3.
- F8, open: the production app shows no icons, whereas the approved copy says icons accompany text. Words carry everything, so no information is lost.
- F9, open: the dialog announcement after Show is not yet reliably proven (section 4 item 1).
- Process disclosures:
  - The earlier VoiceOver run may have typed the demo sentence plus Return into a system password prompt (at most one failed attempt). The guard was then hardened.
  - A broad `pkill -f next-server` was used once; no other Next listener was seen before or after.
  - The previous agent listed all Safari tab URLs once while closing its own tabs; they are not recorded anywhere.

### 6. Live harness and safety rules (reuse, all outside the repo, in `/tmp/carerelay-s20-live/`)

- `rebuild.sh <tag>`: typecheck, copy the frontend to `frontend-<tag>` and production-build it.
- `start-matrix.sh <frontend dir> <tag> [clock offset hours]`: loopback API 8421 (`fake_app.py`, fictional offline transport, synthetic token `synthetic-s20-local-token`, disposable SQLite `<tag>.sqlite`), Next 8420, fixture viewer 8419. It seeds every matrix case through the trusted `tests/_journey_fixtures.seed_journey` into `matrix-index.json`. Pass `10` as the third argument for the expired branch (`matrix-index-<tag>.json`).
- `api-ctl.sh stop|start <tag>`: stop or restart only the API.
- Background servers must run with the tool's background mode. Stop only exact PIDs from `<tag>-pids.txt` after confirming each PID's cwd. Never use broad `pkill`.
- zsh trap: write `${L}:tests`, not `$L:tests`, because `:t` is a zsh modifier.
- The shared-store trap is already handled: callback keys must be unique per episode.
- VoiceOver driving requires the user to stay hands-off and to have Accessibility for Claude plus VoiceOver AppleScript control enabled (both were enabled on 15 October).
  - `vo-drive.js` must abort before any Return, Space or typing unless VoiceOver's keyboard cursor is readable, verifiably on the expected CareRelay control, and nothing secure or authentication-related is in view. Only Escape is allowed with an unreadable cursor.
  - Never type into, or press keys at, a password or authentication field. If one appears, stop and ask the user to dismiss it.
  - Before driving, confirm with the user that no system prompt is open and that they are hands-off.
  - Touch only Safari tabs whose URL starts with `http://127.0.0.1:84`. Never list or record other tabs.
- No installs, credentials, hosted databases or deployment. Close your own loopback Safari tabs and stop your own processes at the end.
