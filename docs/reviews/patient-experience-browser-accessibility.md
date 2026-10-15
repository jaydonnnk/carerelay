# Slice 20 browser accessibility record: 15 October 2026

Supporting note, authoritative for nothing. `00-status.md` owns slice state.

## Publication addendum: 15 October 2026

[verified] The user separately accepted F6 and authorised the prepared Slice 20
commits, main integration and push. The original review and closure below are
historical observations, including the absence of F6 acceptance at that time.
That acceptance does not pass unfinished accessibility or named proof. Fresh
preparation suite is 2,035 passed/232 engine skips/one warning, with production
typecheck/build pass. Two F6 named cases are RED over one distinct edit with
exact restoration. Full suite after restoration also passes. Publication
progress and later Slice 21 authority are owned by `00-status.md`.

## User-directed closure

[verified user instruction] "Screw it just mark s20 as complete and just give me
a copy paste prompt for s21 to finally link the ADR".

[verified] Slice 20 is COMPLETE BY USER-DIRECTED CLOSURE. This records an
exception to its original proof exit, not a passing full accessibility Check.
The user stopped screen control and chose to move on. The original Gate 4
section 9.6 matrix remains the record of what was requested. Unfinished checks
below remain unfinished. No shipping, live ADP access or later implementation
is inferred from the handoff request. "ADR" is interpreted as ADP from Slice 21's
existing contract; no architecture decision record is being integrated.

## Verified local work

[verified] Checkout is uncommitted `slice-20-accessibility-proof` at
`6eec3fb350e6fa120244cb9d67dfa07c25681442`. Local main and live origin/main
matched that commit during closure. A 236-file external snapshot, logical and
raw index, and protected video preceded the branch switch. Tree, diff and
logical index survived exactly. Git refreshed raw index metadata.

[verified] The fresh continuation baseline was 2,035 passed, 232 Postgres
skips and one existing Starlette warning. Production typecheck and build passed.
All 35 frozen production-source fingerprints still match at closure. Only one
stale mutation anchor changed in this continuation, preserving the heading's
focus attributes while removing its ID. No product source changed here.
The full suite was not repeated after the interrupted mutation run.

[verified] Final production build: `/tmp/carerelay-s20-live/frontend-resume-final`.
Loopback frontend/API/viewer were 8420/8421/8419. Runtime checks used disposable
SQLite, scenario time, fictional words and an explicitly fake offline transport.
Real ADP stayed disabled. Restarted API processes imported the frozen snapshot,
so concurrent source mutations could not change the preview.

[verified versions] macOS 26.5.1 build 25F80; Safari 26.5 build
21624.2.5.11.4; installed VoiceOver 10; actual automated browser
Chrome 155.0.8059.79. Frontend builds used Node 22.22.2; pytest's Node helper
resolved Node 24.21.0. Installed reader/browser versions are not reader proof.

## Final-build keyboard and focus observations

[verified] Three trusted-key CDP walks completed without driver errors:
booking and decline each 28 recorded steps, transport 26. They cover skip to
main, explicit bootstrap/create/select, Show/Escape, empty answer, local review,
confirmation, both timing repairs, barrier error/radio arrows, consent
grant/revoke/grant, decline and request. Booking ends at neutral waiting;
transport records a stop. Consent changes keep focus on the checkbox.
Full-document bootstrap/read-back navigation has transient BODY focus.

[verified] Five dialog-close cases ended on Show my plan: plan Escape,
plan return button, server-rendered plan Escape, read-back Escape and enlarged
repair Escape. Four never sampled BODY. The server-rendered case deliberately
replaces the document to remove answer-bearing SSR data: BODY was sampled for
27 ms before the opener regained focus. That case's strict no-BODY predicate
is false. The final URL no longer contains the focus parameter.

[verified] Dialog opening focuses its title. The native modal refuses a
programmatic attempt to focus the background opener. Chrome Tab/Shift+Tab
cycles include document-edge BODY samples before returning inside the dialog;
these are disclosed rather than called continuous dialog focus containment.
There is no fresh Safari keyboard or audible announcement proof in this run.

## Final-build reflow and scanner observations

[verified] Each of 23 standard fixture cases ran under eight settings:
desktop default/larger text; 320 CSS px default/larger text; 200% default-font
enlargement at desktop/320 CSS px; 200% browser zoom; 400% browser zoom.
Measured desktop CSS viewport was 1280 by 813, narrow viewport 320 by 900,
200% zoom 640 by 406, and 400% zoom 320 by 203. Narrow width uses a CDP
device-metrics override because headless Chrome's native window has a 500 px floor.
Browser zoom uses the profile zoom setting, separately from text enlargement.

[verified] All 184 case/setting records have no detected horizontal scrolling,
horizontal clipping or hidden inner text. The selected plan, repair, failed and
handoff dialogs include the restored notice/fallback. Their close controls are
reachable by vertical scrolling. Narrow/enlarged dialog labels wrap over several
lines. These bounded geometry/screenshots do not establish target-user usability.

[verified] The standard corpus includes start, plan, read-back, timing repair,
uncertain, unavailable, barrier, permission, declined, waiting, acknowledged,
failed request, failed/attempted/unknown handoff, stop, H3, accepted, handoff,
stopped accepted/handoff, documented and pending fixtures. The five expired
branches were checked on earlier builds, not rerun on this final build.
Recovery and final-build dialog-failure/retry checks remain incomplete.

[verified] Standard-case captures cover loaded, shown, hidden and reloaded
states where applicable: 265 API JSON, SSR HTML, actual RSC, visible-text and
accessibility captures. The scanner performed 1,100 absence checks and 15,540
same-string positive injection controls, including JSON Unicode, HTML entities
and nested RSC-string forms. No detector failure, leak or contradiction was found.
RSC content type is `text/x-component`. Hidden read-back data is deliberately
redacted; exposed unresolved plans retain original deadline
`2026-09-30T10:00:00+00:00` and patient ownership. Operator fixtures retain their
actual recorded caregiver/human owner and separate simulation/evidence labels.

## Findings F1 to F9

- [verified] F1, repaired: pending native `disabled` dropped opener focus to
  BODY. `PatientJourney.tsx:41` uses focusable busy controls and guarded handlers.
  Earlier baseline failed all five close cases. Final observations are bounded
  by the deliberate reload exception above.
- [verified] F2, repaired: checkbox input moved focus to main. The final
  result-focus effect at `PatientJourney.tsx:265` preserves connected same-step
  controls. Earlier fix1 logs show the defect; final walks retain checkbox focus.
- [verified historical observation] F3, repaired in source: live regions were
  inserted with their text and Safari/VoiceOver did not announce them. One
  persistent region now exists at `PatientJourney.tsx:330`. Earlier reader logs
  observed loading/unavailable speech. Final clean audible proof is incomplete.
- [verified historical observation] F4, repaired in source: step changes spoke
  only "main". `PatientJourney.tsx:321` names main from heading and status.
  Earlier reader logs observed named steps. Final clean audible proof is incomplete.
- [verified inherited authority] F5, repaired: the continuation handoff records
  explicit user approval to expand the dialog-copy footprint into `rules.py`.
  Approved notice/fallback now travel through decoder and render. No new wording
  was authored in this continuation.
- [verified] F6, separate approval unresolved: `rules.py:1184` resets an old
  unavailable interpretation after a later current-version restatement. Without
  it, barrier feedback stayed stale and a later request rendered false recovery.
  The prior agent made this second domain change without separate approval.
  Two service-to-decoder tests exist. User-directed closure is not silently
  recorded as separate approval of this footprint expansion.
- [verified] F7, Gate 3 decision unresolved: a fresh `/example` bootstrap has a
  signed candidate but no record, so `page.tsx` shows "We cannot load your plan"
  before explicit creation. Gate 3 section 9.5 specifies this recovery behavior.
  The final keyboard walk reproduces it. No silent copy or behavior change occurred.
- [verified] F8, unresolved: production has no supporting icons although Gate 1
  copy/design specifies them. Text carries the information. No design waiver or
  claim that the icons exist is inferred.
- [unknown] F9, unresolved: reliable announcement after Show is unproved.
  Earlier reader runs were inconsistent and contaminated by a system prompt.
  The final title-focus approach in `HintCard.tsx:15` has no clean four-cycle
  VoiceOver result. A code comment describing intended announcement behavior is
  not evidence that it works.

## Interrupted proof and process disclosures

[verified] The complete named run was interrupted at 571 of 851 cases.
Those 571 records are RED with green controls and exact restores; the remaining
280 are unexecuted in that run, not passes. A complete current run and current
truthfulness rerun were not finished. Earlier focused runs and Slice 19's
39/39 truthfulness history are not relabelled as current complete Slice 20 proof.
All named target backups match the restored tree at closure.

[verified] The bounded architecture review found no new domain impurity or
deletion candidate. Five static scanner evasion snippets were refused and the
ordinary string-join positive control was allowed. New helpers remain referenced.
React render tests do not run browser focus effects or prove audible output.

[verified] The user confirmed "Permissions granted; no prompt; hands-off".
The shell still refused System Events assistive access with -25211. VoiceOver
Apple events eventually refused with -1743; native VoiceOver app binding timed
out. Native Safari inspection reached only a known loopback CareRelay window.
No Safari keys or typing were sent in this continuation. Screen control stopped
when the user said "Hold on". No non-loopback Safari tabs were listed or recorded.

[verified inherited disclosures, not independently reconstructed] The previous
agent reported possible demo text plus Return into a system password prompt,
at most one failed attempt; one broad `pkill -f next-server`; and one listing
of all Safari tab URLs while closing its tabs. The continuation handoff records
these incidents. None is presented as acceptable procedure or repeated here.

## Evidence and remaining boundaries

[verified] Current evidence root:
`/tmp/carerelay-s20-resume-20261015T072054Z/`. It contains baseline log, original
tree/index/video snapshot, branch preservation, frozen fingerprints, final
keyboard/focus/reflow/scanner captures, architecture review, partial named corpus,
user-hold source audit and closure evidence audit. Earlier proof and final
production builds/screenshots remain under `/tmp/carerelay-s20-live/`.
Temporary evidence can disappear. Missing files must not be treated as proof.

[verified] Exact owned preview PIDs 45720/45721/45722 were already stopped at
closure. No unrelated process was stopped. Protected video, approved gates,
copy and manifests are checked separately by the closure preservation audit.
No commit, merge, push, Slice 21 branch, install, hosted database, deployment,
live ADP call, clinical validation or participant benefit occurred here.

[unknown] Original full accessibility exit, remaining named/truthfulness proof,
F6 separate acceptance, F7 decision and F8 design resolution remain open.
The user chose workflow closure with those limits recorded. Later publication
and live integration keep their separate authority boundaries.
