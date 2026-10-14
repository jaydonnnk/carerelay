# Slice 18 bounded local Check: 14 October 2026

[verified at review time] Local implementation and its offline Check are ready for user
acceptance on uncommitted `slice-18-adp-boundary`. The user explicitly continued
from Slice 17 and requested this slice only. HEAD, main and live origin/main
matched `0fac90dde43882b9322d575fbd80114650e4dc19` at entry and final verification.
`00-status.md` owns state. No acceptance, commit, merge, push or later slice is
inferred from these observations.

## Result and boundary

[verified] The ADP adapter accepts only two pinned synthetic profiles,
`fake-incremental-v1` and `fake-complete-v1`, through an explicitly fake
transport. These nested envelope fields and optional `fake-trace-v1` /
`fake-model-v1` values are synthetic contracts, not observed vendor fields.
The default `ADP_EXTRACTION_ENABLED` constant and constructor remain false.
The ordinary application keeps its separately labelled lexical simulator.
Only external loopback demonstration code injects the enabled fake adapter.

[verified] Strict JSON has exactly six keys, duplicate-key detection at every
depth, checked types/version/uncertainty/refusal, and exact Unicode code-point
spans. Canonical fixture IDs cannot be answers. UTF-8, CR/LF and multiline SSE,
lifecycle, assistant/message/content identity, channel, correlation, ordering,
sequence conflicts, selected answer mode and terminal completion are checked.
Only final content enters the answer buffer. Bounded temporary framing is
discarded; reasoning is never accumulated as an answer, logged or persisted.

[verified] A monotonic deadline covers connection, full response and terminal.
Connection and blocked iteration have independent caller timeout enforcement.
The limits are 2,048 input code points, 16 KiB answer, 16 KiB frame and 64 KiB
wire, including ignored content. Exact-limit and independent limit+1 controls
pass. One call, fresh stateless identifiers, backend auth outside the prompt,
no redirects, no retry and no lexical fallback are controlled.
[hypothesis] These limits are engineering choices, not measured vendor limits.

[verified] Independent whole-answer doubt and deterministic comparison remain
outside model authority. Grounded positives match; supported wrong time repairs;
missing/negated input stays uncertain. Timing-only repair retains only grounded
latest-parent matches. Invalid/refused/disabled/timeout/transport output is
unscored and preserves confirmed words, question, plan, owner and deadline.

[verified] Both stores' existing outermost transaction contract is used for
claim and final application. The claim commits before extraction. Two independent
SQLite services produce one call; supersede and late cue/stop/revision/deadline
changes fence output. Existing independent final-context controls preserve every
other dimension. Late superseded calls append bounded provenance without
rewriting the immutable receipt. Adapter-origin proof binds immutable metadata;
unvalidated or tampered port metadata is discarded before storage or display.
No schema table, dependency, policy vocabulary or patient copy was added.

## Exact verification

- [verified] Fresh baseline: 1,869 passed, 54 Postgres skips, one existing
  Starlette warning. Final suite: 2,029 passed, 56 Postgres skips, one warning,
  exit 0. The two added skips are real-engine fake-readback/nested-score
  contracts. They are unproven until authorised Slice 19.
- [verified] Frontend typecheck and production build exit 0 with existing
  runtimes. Frozen preview source matches current production bytes.
- [verified] One complete current named run: 824 RED, zero SURVIVED or NOT
  PROVEN, green before/after controls and byte-exact restores. This is 805
  distinct edits, including 97 Slice 18 named cases over 94 distinct edits.
  Repeated prose/fence and source/UTF-16/byte selectors are not separate edits.
  All 17 target backups and 40 control-source hashes match current files.
- [verified] Current truthfulness: 39/39 RED, zero survivors/not proven and
  exact restores. No Postgres skip, missing anchor, syntax/import/collection
  error or runtime breakage was credited as RED.
- [verified] Authenticated real HTTP: positive, wrong time, missing, negated,
  invalid, refusal, transport, disabled and slow-terminal outcomes; one call
  per enabled operation, zero calls while disabled and zero booking calls.
  Real concurrent workers return 202 pending and one scored completion.
  Lost response replays 200 once; stale capability returns 409; strict body
  returns 422; auth/unknown return 401/404; unavailable returns 503.
- [verified] Actual production browser: keyboard confirmation, timing repair
  and retained-field success, eight stored positive/uncertain/unavailable
  views, explicit retry, reload and two actual tabs. Approved saved words,
  feedback and questions agree with API/SSR/RSC where exposed. Read-back
  redaction remains deliberate; stored owner is patient and original deadline
  is `2026-09-30T10:00:00+00:00` throughout unresolved cases.
- [verified] Forty patient surfaces and five ledger surfaces were captured.
  Patient detectors have 1,569 positive controls, including nine process-log
  controls. Ledger absence checks reject 30 same-surface injected markers.
  Actual clean captures contain no reasoning/auth markers or false completion.
- [verified] Measured 320px and 1280px views have no horizontal overflow.
  The larger-text control changes main text from 20px to 40px at 320px;
  button bounds remain within the viewport. Empty-answer error focuses the
  textarea; keyboard confirmation focuses main. Native modal opens with its
  return button focused and confines the observed Tab interaction.

## Observed limitations and corrections

[verified limitation] Escape closes the plan dialog but focus ends at BODY,
not its opener, in the unchanged patient component. This basic accessibility
failure is recorded for Slice 20, not passed or concealed. VoiceOver/Safari,
browser zoom and full accessibility remain unproven. Browser observations used
Codex's in-app browser, IDs 1/2; engine version was not exposed by its read-only
scope. The temporary viewport was reset and both temporary tabs were closed.

[verified] Review corrected nested scoring under an uncommitted outer lock,
Unicode line splitting/CR framing, unsafe metadata, missing late-call provenance,
an unused outcome assertion, one omitted canonical ID, and excessive-integer
classification. The first new probe had three masked refusals and one attribute
error. Its corrected 98-case rerun was RED; the final origin-proof changes made
that corpus historical. Only the complete 824-case run is current evidence.

[verified] Swapping fixture cookies while two tabs were open made a stale tab
action recover instead of mutating another episode. Same-fixture reload agreed;
the subsequent correctly bound one-tab explicit retry preserved unavailable
state. Browser pending capture showed the existing request-busy loading sentence,
not an independently verified screen-reader announcement.

[verified] Independent final review found no remaining code blocker or narrow
cleanup deletion. Public contract methods, referenced fixtures and prior proof
are retained. No production module orphan or unused addition was found.

[unknown] Real Postgres remains Slice 19; full accessibility remains Slice 20;
live ADP/profile/model correctness remains Slice 21. No clinical or participant
benefit, real provider action, deployment or external enablement is established.

## Evidence and preservation

[verified] Baseline `/tmp/carerelay-s18-baseline.log`; final suite
`/tmp/carerelay-s18-final-suite.log`; typecheck/build
`/tmp/carerelay-s18-{typecheck,build}.log`; complete named corpus
`/tmp/carerelay-s18-full-named-1/`; truthfulness
`/tmp/carerelay-s18-truthfulness.log`; proof audit
`/tmp/carerelay-s18-proof-audit.json`; HTTP/curl/browser/scanner and frozen source
`/tmp/carerelay-s18-live/`; original snapshot `/tmp/carerelay-s18-preflight/`.
Temporary evidence may disappear; regenerate missing evidence rather than claim it.

[verified] Protected tracked video is 49,394,082 bytes, SHA-256
`cd5fbe68ab2d439f853ae8bd4b85bc6561216c951d1b374f73e62465c9c3a106`.
Approved gate/copy documents, manifests and configuration are byte-preserved.
No staged change, added em dash or non-LF change; `git diff --check` is clean.
Only named preview listeners were stopped: API 74253/8317, Next 74929/8318,
fixture viewer 85599/8319 and disabled fake API 77766/8320. Ports are free.

Boundary: bounded local Check ready for user acceptance. No Git shipping or
Slices 19/20/21 begin automatically.

## Acceptance and publication addendum: 14 October 2026

[verified] The user accepted this bounded Check and requested commits, main
integration, origin/main push and a numbered next-agent handoff starting with
Slice 19. Acceptance includes the disclosed Escape-focus failure, not a claim
that it passes. This addendum preserves the original review observations.
Fresh shipping checks reproduce 2,029 passed, 56 Postgres skips, one warning and
passing frontend typecheck/build. Current named/truthfulness proof hashes and
backups match; no new mutation or live corpus is claimed during shipping.
Seven scoped commits were safely fast-forwarded before checkout and pushed to
main. All 231 files/index entries survived exactly; first live remote check
matched `6dc765b`. This dated receipt is published within that same request;
00-status.md owns state and final live refs are reported after publication.
Only main is pushed. No later-slice branch or implementation is created.
