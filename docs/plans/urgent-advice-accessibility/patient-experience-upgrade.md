# Patient experience upgrade: 12 October 2026

[verified] First checkpoint: a reviewable Gate 1 amendment, not completion of the
whole MVP upgrade. Gate 1 is now re-approved. Authority: `00-status.md`; product decisions:
`01-product.md`; exact proposed text: `patient-experience-copy.md`.

## What exists and what changed

[verified] The handoff's preview snapshot was incomplete. The committed branch
`design-patient-plan-preview` at `70bc49a` contains seven journey screens and the
original palette comparison. This run reuses the seven screens and adds five:
entry with no plan, unavailable/loading/resume, expiry, caregiver acceptance and
successful human handoff. The original branch is unchanged. The selected oat,
plum and tangerine palette is retained; all visualisation files are HTML.

[verified] At the design checkpoint, work was on `codex/patient-experience-gate1`,
created from the existing
checkout at `45a1309`. The inherited uncommitted backend repairs, tests, repair
report and Gate 2 amendment are preserved byte-for-byte. During that checkpoint the user's work was not stashed, staged,
committed, merged or deployed. Planning mirrors gain the explicit
then-pending Gate 1 state, subsequently re-approved by the user. The design checkpoint changed no production frontend or backend code.
[verified] The subsequent shipping request commits the inherited backend repairs
in `b652de0` and the approved journey in `735299a`. A fresh full suite passed
945 tests, with 46 Postgres skips and one existing warning.

[verified] Review at
[the local HTML preview](http://127.0.0.1:8150/patient-journey/index.html).
Source: `design/mocks/patient-journey/index.html`, with one file per patient screen.
Reviewer controls are collapsed at the bottom; the entry URL opens directly
on the patient plan. Answers are not scored or persisted, and no request is sent.

## Reconciliation with the handoff

- [verified] Failed-handoff reassurance, fabricated evidence, unrelated acceptance,
  negated restatements, the positive phrase example, durable stops and reads after
  restart are addressed in the inherited repairs. Evidence and limits are in
  `docs/reviews/truthfulness-repairs-2026-10-12.md`. The focused truthfulness tests
  were re-run here and pass. The earlier full-suite and mutation results belong
  to that repair run; they were not re-run or represented as new evidence here.
- [verified] Before a disposition exists, `get_episode` in `src/carerelay/api.py`
  still returns `fixture.demo_lines()`. `frontend/app/page.tsx` creates the episode
  and reads that projection without providing the full intake/read-back journey.
  This is why the proposal has a no-plan state. The code repair belongs in the
  approved implementation plan after the design gates, not in this HTML prototype.
- [verified] `src/carerelay/coordinator.py` explicitly implements a labelled local
  simulator. This run introduces no runtime AI integration.
- [verified] `submission/honest-claims.md` still claims all five invariants at both
  surfaces and says "not a medical device". `submission/description.md` repeats
  the broad coverage claim. These need a source-by-source correction; the design
  preview does not resolve them. No regulatory conclusion is established here.
- [verified] `submission/usage-proof.md` records completion and lists three captured
  screenshots. Its contents supersede old "proof absent" planning summaries as a
  record, not as a fresh independent audit of screenshot provenance or redaction.
- [unknown] Deployed Postgres behaviour, stop/dispatch concurrency, target-user
  benefit and receiving-service ownership remain unestablished. The participant
  study was cut, not completed with a null result. Competition-date updates have
  not been checked in this design checkpoint; no current cutoff is promised.

## Incremental order after this checkpoint

1. [verified] Gate 1 is re-approved: layout, flow, non-clinical copy and
   acceptance targets. The user also authorised committing and pushing the tree.
2. [hypothesis] Prepare Gate 2 against the actual application: authoritative
   no-plan/status data, persisted episode resume, existing consent and action
   boundaries, server-owned text and accessible errors. Reopen and review the
   affected architecture explicitly; do not infer that old approval covers it.
3. [hypothesis] Prepare Gate 3 contracts and fail-capable checks, then Gate 4's
   small vertical build slices. Only then implement one authorised slice at a
   time, with a visible result and a continue-or-re-steer checkpoint.
4. [hypothesis] Complete the patient journey and verify browser/API agreement,
   then revise the demo around misunderstanding, barrier, failed request and
   truthful recovery. Correct submission claims to match the actual evidence.
5. [hypothesis] Address the six substance dimensions with proof, not new scores:
   assess value against the fixed card; separately decide useful AI interpretation;
   prove the remaining state and store behaviours; expose service and clinical
   limitations; demonstrate the mechanism rather than claim uniqueness; audit
   misleading outcomes and evidence claims. No participant study or integration
   is silently enabled by this sequence.

## Concise visual revision after user feedback

[verified] The user rejected the first version as wordy and boxy. The revised
preview removes card panels, sidebars, repeated introductions and the visible
review toolbar. It uses 22px patient text (26px when enlarged), flat labelled
calendar/clock/person rows, a single main action and concise questions. Critical
plan words and the four approved outcome sentences remain. The clock graphic
shows 6:00 alongside the explicit "6pm today" text. No symbol carries meaning alone.

[verified] The twelve patient screens and patient-first index are revised; a
separate `adp.html` diagram explains ADP for review. `api.py` constructs
`LocalSimulationCoordinator`; `submission/adp-agent-instruction.md` records the
separate published agent and the unrun positive interpretation probe. The patient
app does not call ADP. [hypothesis] Integrate interpretation of confirmed words
before deterministic plan comparison, subject to Gate 2 agreement and measured
extraction, negation, ambiguity, timeout and invalid-output checks. Never let ADP
choose urgency, execute a booking or write patient guidance. This question is now
explicitly part of the next architecture review; no service call is made here.

[verified] Verification of this revision: twelve screens checked at 1440px,
390px and 320px; 320px uses the new 26px setting. No document overflow in the
36 checked layouts. Empty answer, draft review, skip-to-main focus, plan-dialog
Escape/focus restoration, transport refusal, appointment routing, unchecked
permission and simulated waiting were exercised. No clinical or target-user
validation follows from these browser checks. Prior contrast numbers below
belong to the first version, not a fresh complete audit of this revision.

[verified] Earlier prototype saved outside the repository at
`/tmp/carerelay-preview-before-simplification/`. This revision changes mockups
and the pending design records only. The backend repairs remain untouched.

## Historical verification of the first proposal

[verified] The checks below describe the first proposal, superseded by the
concise revision. Do not treat its 24px text size or screenshot as current.

[verified] Existing interpreter, no installs:

```sh
PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local \
CARERELAY_API_TOKEN='' PYTHONDONTWRITEBYTECODE=1 \
/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python \
-m pytest tests/test_truthfulness.py -q \
--basetemp=/tmp/carerelay-design-baseline-20261012
```

[verified] Focused checks pass; the existing Starlette deprecation warning remains.
No Postgres or new full-suite result is claimed.

[verified] Browser inspection of all 12 patient screens: 1440px, 390px, and 320px
with the preview's 24px larger-text setting. All 36 layouts have document width
no greater than viewport width. The review index also fits 320px. Representative
plan and failure screens were visually inspected. This is reflow evidence, not a
full browser zoom or assistive-technology certification.

[verified] Exercised empty-answer feedback, draft review, uncertainty, empty barrier
selection, transport refusal, appointment routing, unchecked permission refusal,
waiting, simulated failure, unavailable/loading and a scripted stopped-record
return. The native plan dialog opens from the keyboard, closes with Escape and
returns focus to its opener. Revealing the plan displays the cued-outcome note.
The skip link initially lost its fragment during URL decoration; corrected and
rechecked with the main element receiving focus.

[verified] Visible leaf-text contrast was inspected across all 12 initial screens;
minimum measured ratio 5.269:1, no sampled ratio below 4.5:1. This bounded scanner
excludes hidden states, mixed-content parents, images and native controls; it is
not a WCAG audit. The first probe used unsupported browser NodeFilter support
and did not run; the replacement scanner used supported DOM element reads.

[verified] Rendered state checks show no deadline on entry/unavailable, unchanged
6pm scenario time on failure/stop, the approved expired form, and success wording
only on the independently selected acceptance/handoff examples. String-scanner
positive controls append each checked success phrase to the serialized main text
and require detection. These checks prove the selected HTML examples only, not
persistence or routing in the application. No care-documented path is offered:
real evidence ingestion remains disabled in the repaired backend.

[verified] All 13 HTML files have unique IDs and valid local link targets. No
console errors or warnings were observed in the inspected browser run. Static
review confirms no external resource dependencies or requests in these mockups.
`git diff --check` and the inherited-file hash comparison are run before delivery.

Evidence scratch: `/tmp/carerelay-patient-preview-qa/` contains the responsive,
contrast and state observations plus desktop/mobile screenshots. Pre-edit copies
and SHA-256 hashes: `/tmp/carerelay-patient-gate1-before/`.

## Manual dependencies

- [verified] Gate 1 decision received: approved 12 October 2026.
  Next product decision: Gate 2 integration; no credentials are requested now.
- [unknown] Later Postgres proof needs an authorised disposable test database and
  locally configured access, never a pasted secret or an unapproved production run.
- [verified boundary] A clinical-ready claim would require qualified clinical
  review and an authorised protocol. A target-user benefit claim needs actual
  authorised participant work; the cut study supplies no result.
- [unknown] Any future organiser/model integration needs a separately approved
  scope, verified service access and measured outputs. No key is requested now.
- [verified] Commit, fast-forward to main and push are explicitly authorised
  12 October 2026. Other external operations remain outside this shipping request.

## Preview lifecycle

[verified] Local-only server on `127.0.0.1:8150`, intentionally retained for review.
Command: `python3 -u -m http.server 8150 --bind 127.0.0.1 --directory design/mocks`.
Log: `/tmp/carerelay-patient-preview-8150.log`. Managed terminal session: `6763`.
To stop it, identify the listener with `lsof -nP -iTCP:8150 -sTCP:LISTEN`, verify
its command, then send SIGTERM to that process. Do not terminate a reused PID
without checking it. The previous repair server, if running, was not touched.
