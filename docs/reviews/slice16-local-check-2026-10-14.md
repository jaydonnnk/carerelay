# Slice 16 local Check and architecture cleanup

[verified] Offline/SQLite exit: PASS. Human Check acceptance and Git shipping
were pending at the time of the build-session review. This is a source and
local-runtime review, not independent
clinical, deployed, ADP, participant or Postgres validation.

## Findings fixed before the Check

- [verified] `frontend/lib/episode-locator.ts:84`: new valid read-back capabilities were refused by the old start-only decoder. Real Python-to-Node token controls and the browser path now pass.
- [verified] `frontend/components/PatientJourney.tsx:153`: visible redaction left the initial plan in HTML/RSC. Read-back replaces the document; restored server answers also require document replacement on Hide.
- [verified] `frontend/components/PatientJourney.tsx:163`: main focus stole Escape's opener focus. Same-step Hide now restores Show, with native dialog keyboard checks and a reversible mutation.
- [verified] `src/carerelay/domain/rules.py:1236` and `frontend/lib/journey.ts:215`: stopped and expired histories had retry copy or a decoder refusal after its removal. Complete producer/decoder controls now cover those histories, including confirmed and pending H3.
- [verified] `src/carerelay/domain/rules.py:1219`: pending stop lost safe navigation. Show/Hide remain offered, with no scoring, repeated H3 or supersede progression.
- [verified] `src/carerelay/adp_extraction.py:78`: exact offsets alone accepted embedded English words. Word-edge controls now reject injected subword outputs as unavailable without a scored row.
- [verified] `src/carerelay/domain/rules.py:391`: a full-width question falsely yielded a clean timing repair. Its deadline stays uncertain in domain, service and the actual browser.

## Evidence and judgment calls

[verified] Fresh pre-edit baseline: 1,547 passed, 46 Postgres skips, one existing
warning. Current post-mutation suite: 1,769 passed, 51 Postgres skips, the same
warning. Frontend typecheck and production build pass. One full named run at
`/tmp/carerelay-slice16-full-named-4`: 631 RED, zero SURVIVED/NOT PROVEN.
All fourteen targets were independently compared with pre-run SHA-256 values.
Current truthfulness: 39/39 RED, exact seven-target restores.

[verified] Claim/context commits precede extraction outside DB locks. Fresh
rechecks and an exact owned pending claim precede the atomic score/provenance/
stop/receipt write. Actual HTTP pending/supersede and process-kill tests found
one extraction and zero partial committed scores. Response loss was induced
by delaying the already-committed response past curl's timeout; replay recovered
the same confirmation and score with no repeated extraction.

[verified] Both-engine writers use the shared transaction facade. Five new
Postgres cases are authored but skipped. They do not establish engine ordering.
Keeping the old unknown provenance is intentional; no legacy digest is promoted
into confirmation permission and no expected field repairs an uncertain answer.
The bounded doubt checker and offline lexical match are demonstration mechanisms,
not proof of patient comprehension.

[verified] Thirty-eight trusted stored cases agree across current API, SSR and
RSC reads, with no hidden-answer leaks in the declared hidden views. Scanner:
190 captured surfaces and 4,180 of 4,180 injection controls. Semantic text and
accessibility attributes derived from SSR are identified as serialized surfaces;
separate actual DOM/AX observations cover the live keyboard flow. Exact approved
closure copy is allowed only on its corresponding recorded closure fixtures.

[verified] The real browser is visible. Keyboard review/confirm/repair, native
modal Tab/Shift-Tab/Escape and opener focus, pointer text control, 320px and
2x text-control screenshots, stale second-tab refusal, escaped markup preview
and reload were observed. The markup review added zero HTTP requests, events,
commands or rounds. Browser zoom, named screen-reader pairs and complete
accessibility proof remain Slice 20. No old Slice 15 blocked item is relabelled.

## Post-slice cleanup mode

[verified] Repository inventory and the twenty-four source-module imports were
checked. The new port and types have service/test references; field-repair tests
are collected by pytest. Guard metadata points at current source, and otherwise
valid controls preserve the first refusal layer. No new orphan or scratch source
file requires deletion. Proof servers, databases and scripts live outside the
repository under `/tmp/carerelay-slice16-live`.

[verified] Keep the legacy coordinator/service probes: existing tests, trusted
fixture seeds and historical assets still use them. Keep old mutation/review
records as historical evidence, future-engine cases for Slice 19, and the
unrelated video exactly as the user required. No deletion is proposed.
`api.ts`'s original line 61 auth-versus-unavailable reason remains
UNPROVEN-NO-CONTROL for Slice 17. No future feature or shipping authority follows.

[verified] Every preview/test process started here is stopped. Ports 8315, 8316
and 8317 are verified free. Temporary browser viewport override was reset.

## Shipping verification: 14 October 2026

[verified] The user accepted this bounded Check and authorised main publication
and cleanup. Fresh suite: 1,769 passed, 51 Postgres skips, one existing warning;
frontend typecheck/build pass. Every one of the 631 recorded RED cases matches
its current source fingerprint, exact backup and current control hashes. No
new mutation, HTTP, browser or Postgres run is claimed for this shipping session.
Cleanup removed three backed-up Finder metadata files. Referenced source, tests,
fixtures, proof records and the protected video are kept. `00-status.md` owns
the publication receipt. Stop and notify before Slice 17.
