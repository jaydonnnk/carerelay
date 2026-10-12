# Backend truthfulness repairs: 12 October 2026

[verified] Subsequent shipping authorisation, 12 October 2026: the user explicitly
requested committing the working tree and pushing to main. The initial repair-run
record below predates that instruction. Fresh pre-ship suite: 945 passed,
46 Postgres skips, one existing warning. No new engine proof is implied.


[verified] Work is uncommitted on `codex/truthfulness-repairs`, branched from
`main` at `45a1309`. `design-patient-plan-preview` remains at `70bc49a`.
No merge, push, dependency install or deployment occurred. HTML proposals and AI
integration are untouched. Gate 2 section 5.2 was explicitly re-approved by the
user during this run; `00-status.md` is the authority.

## Reproductions and repairs

1. **Failed handoff. [verified]** The snapshot discarded the escalation outcome,
   and closure/ownership treated any escalation id as a completed transfer.
   Before editing, failed, attempted and unknown outcomes each failed the
   authenticated regression, while the successful-handoff control passed.
   Both stores now retain the outcome; domain closure and ownership require
   `handed_off` or the existing `handed_over` spelling. The ledger carries the
   actual outcome. Approved unresolved copy and the original deadline remain.

2. **Evidence. [verified]** Callback and MCP boundaries trusted the caller's
   `simulated=false` flag and reference string. Two fabricated-reference probes
   (empty and invented provenance) and the direct MCP probe failed before the
   fix; a simulated self-report control passed. Both ingestion boundaries now
   reject non-simulated evidence, because this deployment has no real artefact
   verifier. Refusals are recorded. Simulated reports and acknowledgements remain
   available and never become documented care. The low-level store remains a
   trusted repository interface, not an artefact-verification service.

3. **Acceptance, separately from evidence. [verified]** The service checked only
   the owner's vocabulary. It ignored scope and permission, and projection ignored
   the accepting party. Seven probes failed before the fix. The service now
   requires a relevant handoff to another permitted party, both stores check
   current consent inside the write, and projection checks the recorded actor and
   scope. The ledger names the accepting caregiver. A historical unrelated
   patient acceptance stays unresolved on reload. A valid caregiver acceptance
   retains the approved "Someone has agreed to help." rendering, with
   `care_evidenced=false`.

4. **Negated read-back. [verified]** Positive substring matching ignored polarity
   and even extracted `me` from `appointment`. Eleven probes failed before the
   fix; three positive controls passed. The scanner now uses whole Latin words
   and marks fields inside negated, doubtful, conditional, alternative or
   questioning sentences uncertain. It does not accuse the patient of a definite
   mismatch. The existing fixture action text and reversed deadline phrase are
   recognised. Positive answers, partial answers and hint labels are covered.
   Final review additionally reproduced a negating second sentence with no
   repeated fields ("Actually I won't"); explicit backward references now
   make the answer uncertain too, with a separate mutation proof.

5. **Durable stops. [verified]** Round zero could restart an exhausted ladder;
   reassessment returned a stop without persisting it; action/MCP paths checked
   no stop; H3's response derived understanding from comparison alone. Four core
   probes failed before editing. Versioned stop events now persist alongside
   restatement/barrier records; old H3, exhausted-round and barrier-stop rows are
   also recognised. Service and MCP guards block automated continuation. Late
   success/evidence callbacks become refused audit receipts; failures, duplicate
   audit, plan display, consent changes and valid human transfers remain available.
   Only a test-only authorised new disposition version reopens the flow. Old
   restatements and attempt keys cannot authorise it; the old deadline row remains.

6. **Restart read defect found during verification. [verified]** A fresh process
   returned 404 for persisted patient/ledger records because the reads depended on
   a process-local episode registry. Those reads now use the durable record, with
   unknown episodes still returning 404. This was reproduced by the fresh-process
   tests before removing the registry.

The new checks live in `tests/test_truthfulness.py` and
`tests/test_truthfulness_postgres.py`. Production changes are confined to the
existing API, service, tools, coordinator, fixture aliases, domain and two stores.
No new table or patient-facing sentence was introduced.

## Evidence and limits

- **[verified] Fresh baseline:** 889 passed, 43 skipped, one existing Starlette
  deprecation warning. **Final:** 945 passed, 46 skipped, the same warning.
- **[verified] New focused checks:** 54 pass on local SQLite; three new Postgres
  checks skip. The remaining 43 skips are the existing Postgres-gated checks.
- **[verified] Mutation harness:** `tests/_mutate_truthfulness.py`, 39/39 RED,
  zero survived or not proven. Each selector has passing pre/post controls;
  actual assertion failures are required and every target is restored byte-exact.
- **[verified] Affected earlier harnesses:** Slice 6 all 11 mutations RED;
  Slice 7 10/10; Slice 8 26/26; Slice 10 16/16; Slice 11 7/7; Slice 12 10/10.
  Slice 7's control has two Postgres skips. Three pre-existing harness defects
  were repaired: a CRLF-only assumption and two non-unique anchors. The removed
  process-local 404 guard's mutation was repointed to the persisted-read handler.
- **[verified] Existing tests corrected, not weakened:** the old H3 assertion
  explicitly required `understood=true`, contrary to its own contract; it now
  requires false and human routing. Acceptance success fixtures now supply the
  consent prerequisite. The deliberately broken-cap control mutates the domain
  cap as well as service/store caps. The store-surface inventory includes both
  new stop methods; signatures still match both implementations.
- **[verified] Serialization:** authenticated API calls assert exact patient text,
  labels, closure, owner, evidence and ledger fields, including the `/ledger`
  alias. Fresh interpreter tests cover repair, H3, reassessment and barrier stops.
  Existing serialized scanner self-tests remain in the passing boundary suite.
- **[unknown] Postgres runtime behaviour:** code and signature checks cover both
  implementations, but no Postgres engine was reachable. New Postgres tests and
  Postgres-specific mutations have not run. SQLite proves no deployed-store claim.
- **[unknown] General language comprehension:** this remains a bounded lexical
  simulator, not AI integration or clinical validation. Complex negation scope,
  corrections and cross-sentence references remain outside its measured corpus.
- **[verified] Real evidence ingestion remains unavailable.** Caller prose is not
  authenticity proof. Direct repository fixtures still exercise documented-care
  rendering; this does not verify an artefact or retrofit verification onto any
  previously stored row. Human identities remain simulated shared-token actors.
- **[unknown] Multi-process races involving stops/reassessment:** fresh-process
  persistence is tested, not concurrent stop-versus-dispatch ordering across
  multiple backend workers. No concurrency or deployment claim is made.

## Live local check

[verified] Authenticated `curl` against the real running API: unauthenticated read
401; authenticated creation, intake, escalation and reads 200. Posting
`{"human_path":"nurse_line","outcome":"failed"}` produced:

- `closure=open`, `care_evidenced=false`, `action_owner_id=patient`.
- "No one has agreed to help yet."
- "Please act now."
- "Please do it before 6pm today."
- "If that does not work, call the fictional nurse line."

[verified] Stored deadline before and after:
`2026-09-30T10:00:00+00:00`, 6pm Singapore time on the **scenario date**.
The deadline row did not change. Patient and ledger JSON were identical after
terminating and restarting the API process against the same local SQLite file.

The local inspection server remains available at
`http://127.0.0.1:65515/api/episodes/demo-episode-001` and
`http://127.0.0.1:65515/api/episodes/demo-episode-001/ledger`.
After the authenticated check it was restarted in the app's local mode on loopback
for inspection; this is not a public deployment. Stop its process with
the pid recorded in `/tmp/carerelay-truthfulness-live/pid`, after confirming
that it still names this run's server.

Local captures and server script: `/tmp/carerelay-truthfulness-live/`.
Suite and failing-before logs: `/tmp/carerelay-truthfulness-*.log`.
The successful mutation log names the separate byte-backup/XML evidence directory.

Reproduce the suite with the existing interpreter, without installs:

```sh
PYTHONPATH=src APP_DATABASE_URL=:memory: APP_CLOCK=scenario APP_ENV=local \
CARERELAY_API_TOKEN='' PYTHONDONTWRITEBYTECODE=1 \
/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/bin/python \
-m pytest tests --basetemp=/tmp/carerelay-truthfulness-final -ra
```
