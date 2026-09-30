# Status: CareRelay urgent-advice accessibility

- Gate 1 — Product: **APPROVED** (25 September 2026; reopened and re-amended the same day — see the reopening section below)
- Gate 2 — Architecture: **APPROVED** (25 September 2026, revision 2)
- Gate 3: Program Design, **APPROVED** (26 September 2026)
- Gate 4 — Slice plan: **APPROVED** (28 September 2026)

## Slices

**Gate 4 is approved. Slices proceed one at a time, each ending with a "continue, or re-steer?" check.** Slice state below is the only authority.

- [ ] Slice 0 — kill tests (**PASS** 28 Sep) + Option C source (**open**, blocks Slice 5 only)
- [x] **Slice 1 — COMPLETE 28 Sep.** Tracer bullet runs; 11 tests pass; curl-verified live
- [x] **Slice 2: COMPLETE 30 Sep; adversarially reviewed and remediated the same day.** Pure domain core; boundary check seen red then green; 240 tests pass. Review at `docs/reviews/slice2-adversarial-review.md`
- [x] **Slice 3: COMPLETE 30 Sep; adversarially reviewed the same day, verdict yes with named caveats.** The append-only SQLite record; every table refuses UPDATE and DELETE by trigger; the callback representation proven atomic under two concurrent writers and a crash; 70 new tests (69 in the new `tests/test_state.py`, one added to `tests/test_domain.py`), 310 pass. The Slice 2 review's `source_ref` open item is settled here. Review at `docs/reviews/slice3-adversarial-review.md`; eight open items, of which O1 is blocking
- [ ] Slice 4 — PlanBack end to end, hint ladder, bounded repair ← **next**
- [ ] Slice 5 — judged fixture + abstention path (**blocked on the Option C source**)
- [ ] Slice 6 — action path, simulated provider, platform call + Gate A decision
- [ ] Slice 7 — baseline instrument: the external card (C1, parallel)
- [ ] Slice 8 — Gate B: run the comparison (**kill test**)
- [ ] Slice 9 — Closure Contract in full (starts only after the kill test)
- [ ] Slice 10 — fault harness + seven sequences
- [ ] Slice 11 — judge ledger + usage proof
- [ ] Slice 12 — submission assets

**Carried decisions.** Five items from the Slice 2 review were deliberately left undecided. **Slice 3 settled the `source_ref` mutation gap** (see the Slice 3 section below), so four remain. Each is settled (or asked about) at the slice where it becomes live, and recorded there: F4 and the §2.2 amendment at **Slice 9**; F5 at **Slice 6**; F6 at **Slice 5**. The full list and the reasons are in the Slice 2 review section below.

## Slice 2 complete, 30 September 2026

**The pure decision layer exists, and constraint C7 is enforced by a check that has been seen to fail.** Branch `slice-2-domain-core`, created from `main` at `6e9be4f` before any edit, per `AGENTS.md` section 6 ("never begin slice work on `main`"). **Committed, merged and pushed on the user's explicit instruction, 30 September 2026.** The range is `6e9be4f..b19b36e`: five commits on `slice-2-domain-core` (domain core and its unit tests; the C7 boundary check; this record and the review note; the writing-convention lessons), fast-forwarded into `main`, then one record-correction commit made on `slice-3` and also fast-forwarded into `main`. `git log --oneline` lists each concern. `main` and `slice-3` sit at `b19b36e`; `slice-2-domain-core` sits at `80245e4`. **Pushed:** `origin/main` is at `b19b36e` and is in sync with local `main` (0 ahead, 0 behind). `AGENTS.md` section 3 records that no gate authorises a commit or push, so this was a user-authorised action rather than a gate authorisation.

| Evidence | Result |
|---|---|
| `pytest tests/` | **240 passed, 1 warning** (Slice 1 baseline: 11 passed; 109 at first completion, before the review added 131 checks) |
| `tests/test_domain.py` | **88 passed** |
| `tests/test_boundaries.py` | **141 passed** |
| `tests/test_api.py` | 11 passed, unchanged |
| **Boundary check seen RED** | `import socket` added to `rules.py` line 40. `test_domain_import_boundary` **FAILED**, naming the file, the line and the module: `rules.py:40: imports forbidden module 'socket'`. Removed; re-run green. `grep -rn "socket\|TEMPORARY" src/carerelay/domain/` returns nothing |
| Injection against the **real** file | `test_scanner_detects_an_injected_import_in_the_real_rules_file` prepends the forbidden import to the actual `rules.py` source and requires detection. A scanner proven only on toy strings proves nothing about the file it polices |
| One detector per forbidden form | `TestScannerHasTeeth` covers module import, `from` import, nested import, wall-clock call after a `from` import, wall-clock call through the module, `time` call, bare `open`, and a model-client import. `TestEveryDetectorIsPairedWithItsInput` iterates the three lists themselves, so **every** entry in `FORBIDDEN_MODULES`, `FORBIDDEN_CALLS` and `FORBIDDEN_CALL_SUFFIXES` now carries an input that must be caught. It also asserts the check is **not** a blanket ban that would forbid the imports `domain` legitimately needs |
| Line endings | New files are CRLF, matching every tracked file (`core.autocrlf=true`). Verified byte-wise: zero lone LF across all five. No line-ending damage |
| Secret and prohibited-content scan | Clean. The only match for "secret" is the stdlib `secrets` module inside the forbidden-import list. No credential-shaped string, no prohibited claim, no real facility or clinician name |

**Files created.** `src/carerelay/domain/__init__.py` (16 lines), `src/carerelay/domain/models.py` (393 lines), `src/carerelay/domain/rules.py` (610 lines), `tests/test_domain.py` (1357 lines), `tests/test_boundaries.py` (507 lines). Line counts are post-remediation.

**The five tests Gate 4 required to be fail-capable.**

| Test | Where | The defect it must catch |
|---|---|---|
| `test_domain_import_boundary` | `test_boundaries.py` | An SDK, network, database, filesystem or wall-clock import or call under `domain/`. Seen failing on a real injected `import socket` |
| `test_planback_known_match_mismatch_uncertain` | `test_domain.py` | **K1.** The six-entry adversarial corpus of correct restatements produces zero false mismatches. `TestPlanBackAssertionsHaveTeeth` swaps in four defective comparators (surface-only, always-uncertain, unknown-as-mismatch, drops-extractor-doubt) and requires the corpus to catch each. **Added at review:** a second, independently-chosen natural-phrasing corpus, because every entry in the original six turned out to be a literal key in one of the resolution tables, plus a test that an unresolvable phrase is `uncertain` and never `mismatched` |
| `test_closed_vocab_and_missing_is_not_negative` | `test_domain.py` | A hallucinated route or change code must stop, and a missing code must assert nothing. Every stop reason is exercised separately |
| `test_disposition_deadline_is_append_only` | `test_domain.py` | A retry that updates v1 or mints v2. Includes a structural scan proving `domain` constructs no `Disposition` at all, with its own teeth test |
| `test_hint_disclosure_accessibility` | `test_domain.py` | **C8.** Card visibility derived from the event vocabulary alone; `dwell_seconds` never changes the outcome; H3 is never a comprehension pass |

**K1 is now a domain test, not a spike result.** The comparator was moved from `spike/kill_spike/planback.py` rather than rewritten: the alias, relative-time and owner tables and the six-entry corpus are carried across, and the resolution logic is the spike's, widened per section 1.1. The spike directory is untouched and remains throwaway.

**Signature amendments carried from Gate 4 section 1.1, made explicit rather than silent.**

| Item | Gate 3 said | Implemented as | Why |
|---|---|---|---|
| `ExtractedPlan` field names | `action_id`, `deadline_utc`, `next_owner_id` | `action_span`, `deadline_span`, `next_owner_span` | Under Reading A the coordinator returns **raw text**, so the old names would have been false. Section 1.1 requires the raw span and the extractor's own uncertainty to be carried separately, and `uncertain_fields` is now a real field that outranks a resolvable span |
| `compare_plan` widening | `(expected, extracted, action_aliases)` | `(expected, extracted, *, policy, now_utc, display_tz)` | Section 1.1 widened the signature with `action_aliases`, `deadline_forms` and `owner_aliases` "as explicit policy data". All three are carried on one `PolicyFixture` value rather than three parallel mappings, so a policy has one source of truth |

**Three readings the approved documents leave open, plus one completion. Each is implemented, documented in `rules.py`, and flagged here so it can be corrected.**

| # | Reading | The alternative | Why this one |
|---|---|---|---|
| 1 | **Closure precedence: expiry outranks a recorded human acceptance.** The approved condition for `closed_with_evidence` is "evidence >= documented **or** an explicit human acceptance is recorded", and a human acceptance is not evidence that care happened. Once the deadline has passed with no evidence, the state is `expired_unresolved` | Put acceptance above expiry, so an accepted handoff stays `closed_with_evidence` past the deadline | The other order lets a scripted acceptance report a resolved episode whose deadline passed with nothing to show for it. That is invariant I2, and it is the product thesis. **This is the one reading most worth an explicit yes or no** |
| 2 | **Line 2 is composed by owner.** "You must act now." when the owner is the patient; the approved "You or [named person] must act now." otherwise | Reproduce the approved literal, which yields the malformed "You or you must act now." that Slice 1 found by inspection | Carries the Slice 1 divergence forward instead of reintroducing the defect. The Slice 1 note still stands: Slice 9 implements whichever form the documents then carry |
| 3 | **`patient_lines` refuses for `closed_with_evidence`.** It raises `NoApprovedPatientWording` | Render the unresolved four lines | No approved rendering exists for a resolved episode. Rendering "Help is not arranged." over an episode where care is evidenced is a false statement to the patient. Slice 9 owns the Closure Contract rendering |
| 4 | **Execution axis completion.** `expired` is set on axis A when an attempt recorded no terminal outcome and the deadline has passed. A recorded `acknowledged`, `failed` or `superseded` outcome is never overwritten, and an episode with no attempt stays `not_started` | Leave `expired` unwired | Contract section 2.2 lists `expired` as an axis value. Left unwired it was unreachable vocabulary, and "we tried and nobody said yes, and the deadline has gone" had no rendering on axis A at all. Found by the post-slice cleanup scan, not by the tests |

**Two defects the post-slice cleanup scan found in this slice's own code, both fixed.** `models.DisplayZone` was defined and never used: removed, along with its now-unused `tzinfo` import. `ExecutionStatus.EXPIRED` was unreachable: reading 4 above wires it, with three tests (the attempt-with-no-outcome case, the recorded-terminal case, and the no-attempt case) each covering a distinct guard.

**The em dash question is settled by measurement, and the original claim was wrong.** The source contains **no** em dash character at all: line 4 of the expired rendering is written as the escape `\u2014`, so the rendered string reproduces the approved copy verbatim while the file stays clean of U+2014. `AGENTS.md` section 6 is therefore not breached and no approved clinical wording has drifted. Verified byte-wise across all five new files: zero U+2014. The first version of this entry said "one em dash is used", which overstated the problem.

**Not in this slice, and deliberately.** No database (Slice 3). No routes, no service, no coordinator. No `presentation.py` or `templates/` (the plan-versus-code drift recorded earlier today is untouched: `04-slices.md` still names `src/carerelay/templates/patient.html`, which does not exist, and `jinja2` is still imported nowhere). The Option C source is still unselected, so every alias table and every corpus entry here is **provisional** and nothing may be shown to a participant.

**What this evidence does not prove.** A passing static check is not evidence of WorkBuddy access, clinical safety, human learning or patient benefit. K1 remains a deterministic-layer result and depends on Reading A (ADR-0007, risk R5). The 88 domain tests exercise the pure layer only: the model's own extraction is not reachable offline.

## Slice 2 adversarial review and remediation (30 September 2026)

An independent adversarial review with no prior context was run against the branch, from the brief at `04-slices.md` (Slice 2). Full note: **`docs/reviews/slice2-adversarial-review.md`**. Verdict: **the exit contract is met, with named caveats.**

**Two blockers were found and fixed, both real.**

| # | Defect | Fix |
|---|---|---|
| 1 | `patient_lines` rendered `PolicyText.deadline_display` verbatim, decoupled from `disposition.clinical_deadline_utc`. A reassessed disposition (deadline 1 Oct) rendered line 3 as "Before 6:00 PM on 30 September." That is a false statement to the patient, and it breaks approved copy rule 5 in `02-architecture.md` section 7 | `PolicyText.deadline_display` is now `deadline_display_by_version`, keyed by disposition version, mirroring `owner_display_by_id` and `route_display_by_id`. An unworded version raises `MissingDisplayText` instead of printing a stale date |
| 2 | This entry claimed the new files were CRLF and matched every tracked file. They were pure LF | The five new files were normalised to CRLF, which is what the entry intended and what every tracked file uses. Verified byte-wise: zero lone LF |

**The review's highest-ranked risk was confirmed.** The boundary scanner was evadable in five ways, all of which reached a filesystem, a network, a database or the clock without importing a forbidden module: `__builtins__["open"](...)`, `builtins.open(...)`, `builtins.__import__("socket")`, `builtins.__import__("sqlite3")`, and `getattr(datetime, "now")()`. Root cause: `_dotted_name` returned `""` for any call whose `func` was itself a call, a subscript or a lambda, and the scanner skipped those. Fixed by refusing a dynamically produced call target and by adding `builtins` and `sys` to `FORBIDDEN_MODULES`. All five are now caught and each has its own regression test.

**Four further defects fixed.** `project_attempt` raised only on the lowest-`seq` row, so a corrupt row at a higher `seq` was silently ignored, contradicting its own docstring; every row is now validated. `derive_closure` returned `expired_unresolved` with no named owner when an expiry event arrived with no disposition, which I4 forbids; that is now refused. The K1 corpus was found to be self-serving, since all six entries are literal keys in the resolution tables; a second, independently-chosen natural-phrasing corpus was added, together with a test that an unresolvable phrase stays `uncertain` and never becomes a mismatch. Two docstrings claimed full detector coverage that the tests did not provide (deleting `"eval"` and `".today"` from the lists left the suite green); three parametrised tests now iterate the lists themselves.

**Five findings were deliberately left open**, because each needs a product, clinical or documentary decision rather than a code fix.

**They are not decided now. Standing instruction (user, 30 September 2026): each is decided (or put to the user as a question) at the slice where it first becomes live, and the decision is recorded here in that slice's section.** No later slice may silently implement one of these while building an earlier one.

| # | Open question | Decided at |
|---|---|---|
| F4 | `closed_with_evidence` is reachable both from real evidence and from a recorded human acceptance with no evidence, and `patient_lines` raises for both. The acceptance case is a normal product state (`POST /acceptances`) with no patient rendering at all. Slice 9 must render it, and must render the two cases separately | **Slice 9** |
| F5 | `simulated = not care_evidenced` conflates "this episode is a simulation" with "care is not evidenced". The code implements the D11 rule as written, so the meaning is a decision, not a defect | **Slice 6**, visible in the ledger at **Slice 11** |
| F6 | `action_owner_id` ignores `escalation_id` and `human_acceptance_id`, so I4's "explicit human service" owner is inexpressible | **Slice 5**, re-checked at **Slice 9** |
| §2.2 | The `closed_with_evidence` and `expired_unresolved` rows of `03-planback-closure-contract.md` section 2.2 overlap on acceptance plus past-deadline and state no order; the implementation puts expiry first. This is the documentary form of the F4 decision | **Slice 9** |
| `source_ref` | The D11 guard's `simulated` and `source_ref` halves share one mutation flag, so the `source_ref` half has no independent proof | **Slice 3** |

**Evidence.** 240 passed, 1 warning (88 domain, 141 boundaries, 11 api), up from 109. Five mutation checks confirmed the new tests are fail-capable: reverting each fix in turn caused its paired test to fail. Every mutation was reverted with an md5 check, and `git status --short --untracked-files=all` was identical before and after. No commit, branch or push was made **during the review itself**, and no gate was reopened. The work was committed afterwards, the same day, on the user's explicit instruction; see the commit list in the Slice 2 section above.

## Slice 3 complete, 30 September 2026

**The clinical record persists, and ordinary `UPDATE` and `DELETE` have no path through it.** `src/carerelay/state.py` implements the thirteen tables of `02-architecture.md` sections 4.1 and 4.2 behind repository methods, on SQLite with WAL and a busy timeout. Append-only is not a convention here: `BEFORE UPDATE` and `BEFORE DELETE` triggers are generated for **every** table, and the test that proves it opens its own raw connection and issues raw SQL, so this module's own guards are not in the loop.

**Branch `slice-3`, already the working branch when the slice began. Committed on this branch on the user's explicit instruction, 30 September 2026, and fast-forwarded into `main` the same day; not pushed.** Two new code files, `src/carerelay/state.py` and `tests/test_state.py`; three code files edited, `src/carerelay/domain/models.py`, `tests/test_domain.py` and `src/carerelay/api.py`; the documentation restructured: `AGENTS.md`, `PROGRESS.md`, `00-status.md` and `tasks/todo.md`, plus the new `docs/README.md` and four review files moved into `docs/reviews/`. `slice-3` has no upstream, so nothing here has been pushed.

**Correction, 30 September 2026 (Slice 3 review, F3).** This row previously asserted that `git status --short --untracked-files=all` "lists exactly ten paths and nothing else", and named `slice-3-review-prompt.md` as the tenth. That file does not exist, and the tree held **nine** paths. This is the second consecutive slice whose version of this row was wrong: the Slice 2 row claimed four paths when the tree held nine. **The count has been removed rather than corrected.** A working-tree count is falsified by the next edit, including an edit made while writing the review, so it is not a durable claim and does not belong in this document. The file lists above are the durable form.

| Evidence | Result |
|---|---|
| `pytest tests/` | **310 passed, 1 warning** (Slice 2 baseline: 240). Per file: **89** domain, **141** boundaries, **11** api, **69** state. The four counts sum to 310, the total. **Corrected 30 September 2026 (Slice 3 review, F2):** this row read 88 domain and asserted the four counts summed to the total, but 88+141+11+69 is 309. The domain figure was Slice 2's stale count; this slice added `test_the_source_ref_half_of_the_guard_is_independently_proven` to `test_domain.py`, taking it to 89 |
| **Every new guard seen RED, one at a time** | Eleven mutations of the guards, each applied alone to one anchor and each reverted with an md5 check. **All eleven made their paired test fail.** `md5 unchanged for every file: True`, and the suite returned to 310 passed afterwards. The mutations: the append-only triggers, the D11 Python guard, the D11 database `CHECK`, the consent re-check, expiry stickiness, the premature-expiry guard, duplicate detection, the attempt idempotency lookup, the transaction rollback, disposition-version monotonicity, and the `source_ref` flag below |
| **The concurrency claim, mutation-proven** | Two further mutations target the concurrency mechanism itself, not the guards. `BEGIN IMMEDIATE` appears once as executable code, inside the shared `_write` helper, so this is one mutation applied to several tests rather than several independent mutations. Changing it to a deferred `BEGIN` turns **both** race tests RED, and a `busy_timeout` of `0` turns **both** race tests RED as well (measured three times on 30 September 2026; this row said the callback race only), while in both cases the single-writer control tests stay GREEN. That control is what makes the result mean something: a mutation that also breaks single-writer writes would prove nothing about concurrency. The failure mode under a deferred `BEGIN` is `[OperationalError('database is locked'), True]`, one writer crashing on the lock upgrade instead of returning the correct duplicate-suppression answer. See the R6 row below |
| Append-only, proven against the schema | Raw `UPDATE` and raw `DELETE` refused on **all thirteen** tables, one parametrised case per table per verb. A row is seeded into every table first, because a `BEFORE UPDATE` trigger fires per row and an update against an empty table would prove nothing |
| The append-only control case | Dropping two triggers lets the same `UPDATE` and `DELETE` succeed, so the refusal is the triggers and not something incidental |
| D11 `CHECK`, independent of the Python guard | A raw `INSERT` of a simulated or unsourced `documented` row raises `IntegrityError`. A control table that is the same minus the `CHECK` accepts the identical row |
| **R6, two concurrent writers** | Two connections in two threads, one callback key, a `Barrier` so both arrive together. `sorted(outcomes) == [False, True]`: exactly one receipt applied, one recorded as a duplicate of it, one transition appended. The same construction for expiry yields exactly one event. **The mechanism is `BEGIN IMMEDIATE`, and that is now mutation-proven rather than asserted.** With a deferred `BEGIN` the second writer does not produce a wrong duplicate, it crashes with `OperationalError('database is locked')` on the lock upgrade, so the correct idempotent answer is lost. The race tests are what detect this; the single-writer controls are not disturbed, which is why the detection is attributable to concurrency and not to a broken write path |
| Crash atomicity | With the audit write made to raise, the attempt row and its event both roll back and the key is not poisoned. With the transition append made to raise, neither the receipt nor the transition survives |
| The Slice 2 review's `source_ref` gap | **Closed here.** `mutated_closure` now carries two named flags, one per half of the D11 guard, so neither subsumes the other. The new test fails when the flag is reverted to the Slice 2 form |
| Line endings | Both new files normalised to CRLF after writing and verified byte-wise: **zero lone LF**. The three edited code files were already CRLF and the editor preserved them. (This row said "the two edited files"; three code files were edited) |
| Em dashes | **Zero U+2014** in the two new files and in the three edited code files. `src/carerelay/api.py` carries 5 pre-existing U+2014, none added by this slice; across every edited code file the net change in em dash characters is 0. **Corrected 30 September 2026 (Slice 3 review, F12):** this row said "all four files this slice touched" when five code files were touched |
| Secret and prohibited-content scan | Clean. The only match for "secret" is a comment about a server-held secret at Slice 6. No credential, no real facility or clinician name |

**The five tests Gate 4 required to be fail-capable.**

| Test | What it proves |
|---|---|
| `test_attempt_open_atomic_and_double_tap` | One attempt and one audit row for one `(episode, route, purpose)` triple, however many times it is tapped. A crash between the attempt row and its audit row rolls both back and leaves the key usable |
| `test_callback_duplicate_and_reorder` | Every receipt is auditable; a duplicate appends no transition; a late acknowledgement is retained and non-winning because its `seq` is higher |
| `test_consent_revoke_in_flight` | Revocation blocks dispatch, callback success and evidence recording, and the refused receipt is still written with a reason, so the failure is visible rather than absent |
| `test_evidence_provenance_constraint` | A simulated or unsourced row cannot be `documented`, in Python and in the schema, each proven separately |
| `test_expiry_sticky_after_clock_regression` | The first overdue read persists expiry; a backwards clock cannot return the disposition to `open` |

**Files created.** `src/carerelay/state.py`, `tests/test_state.py`. **Files edited.** `src/carerelay/domain/models.py` (the two Gate 3 value types below), `tests/test_domain.py` (the `source_ref` flag), `src/carerelay/api.py` (one comment that this slice made false).

**Two Gate 3 value types were missing and are added here.** `03-program-design.md` section 3 names `AttemptCommand` and `CallbackResult`; Slice 2 did not need either, and the store protocol cannot be written without both. They are frozen values in `domain/models.py`, with no I/O, so nothing about the D2 boundary changes.

**Ten readings the approved documents leave open. Each is implemented, documented in `state.py`, and flagged here so it can be corrected.**

| # | Reading | The alternative | Why this one |
|---|---|---|---|
| 1 | **Every table is insert-only**, not only the four clinical tables D3 names | Enforce on `dispositions`, `attempt_transitions`, `evidence` and `consents` only | Nothing in the product has a legitimate UPDATE or DELETE, and a rule with exceptions is a rule someone finds the exception for. The strongest form is also the easiest to state and to test |
| 2 | **`callback_key_digest` is stored for every receipt; a duplicate's `callback_key` is NULL** | Store the received key in plaintext on the duplicate row as well | `03-program-design.md` section 3 requires the received key to be retained "only in a redacted or hashed audit field". The digest gives the audit trail without a second plaintext copy |
| 3 | **A refused receipt is written with `accepted = 0` and a `rejection_reason`** | Refuse and record nothing, or record a bare `accepted = 0` | "Records every callback received, including rejected duplicates" is in the approved schema. A bare flag leaves "why was this not applied" unanswerable, and the ledger is the artefact that has to answer it. `rejection_reason` is a column the approved column list does not name |
| 4 | **`record_expiry_once` refuses a premature event** | Record whatever the caller asks for | A premature expiry event tells a patient their window is gone while they still have time. That is a false statement of exactly the kind the product exists to prevent, and the store is the narrowest layer that can refuse it |
| 5 | **The existing-event check runs before the overdue check** | Check the deadline first | After a clock regression the deadline is in the future while the event is a fact that already happened. Checking the deadline first would raise `PrematureExpiry` on a sticky episode, which is the opposite of D12 |
| 6 | **The snapshot reports the expiry event for the current disposition version** | Report the latest expiry event for the episode, whatever version it names | An expiry event records that one version's deadline passed. A reassessment inserts a new version with a new deadline, so the earlier event no longer describes the current plan. The row is never deleted and stays in the ledger. Within one version, D12 stickiness is exactly as written. **This is the reading most worth an explicit yes or no** |
| 7 | **`attempts.purpose_id` is a stored column** | Derive the key from `(episode, route)` only | D5 derives the key from `(episode, route, attempt-purpose)`, and an authorised retry is a new purpose. Without the column the triple is not auditable from the record |
| 8 | **`dispositions` versions must be contiguous from 1** | Rely on `UNIQUE (episode_id, version_no)` alone | A gap means a version was rewritten rather than appended, which is the one thing the deadline invariant cannot survive |
| 9 | **The snapshot's attempt is the latest one** | Refuse to project when more than one attempt exists | `EpisodeSnapshot` carries a single attempt and the latest is the one the patient is waiting on. A retry legitimately creates a second |
| 10 | **`state.py` derives the attempt key** (`derive_attempt_key`) | Leave key derivation entirely to the service | D5's double-tap semantics only work if the key is a deterministic function of the triple. The function is small, pure and testable here, and without it the double-tap test would prove nothing about the key. A server-held secret can be folded in at Slice 6 without changing the signature |

**The `source_ref` gap is settled, and this is the decision.** The Slice 2 review recorded that one mutation flag disabled both halves of the D11 guard, so the `source_ref` half had no independent proof. `mutated_closure` in `tests/test_domain.py` now has two flags: `trust_simulated_evidence` removes the `simulated` half only, `trust_unsourced_evidence` removes the `source_ref` half only. The new test requires three things at once: the guard holds as written; removing the `source_ref` half alone lets an unsourced row through; and removing the `simulated` half alone does **not**. No product code changed, and no clinical wording was touched.

**This slice's exit check, run and shown.** A duplicate callback delivered with a contradictory claim (the first receipt says `failed`, the duplicate says `acknowledged`):

```
1. THE ATTEMPT IS OPENED ONCE, HOWEVER MANY TIMES IT IS TAPPED
   first open        attempt 9d3d9d2fd2c0  execution=attempted
   second open       attempt 9d3d9d2fd2c0  execution=attempted
   attempt rows in the record: 1
   audit rows: ['episode_created', 'disposition_recorded', 'consent_changed',
                'attempt_opened', 'attempt_duplicate_suppressed']

2. THE SCRIPTED FAILURE ARRIVES (origin = platform)
   applied: True
     line 1: Help is not arranged.
     line 2: You must act now.
     line 3: Before 6:00 PM on 1 October.
     line 4: If this route fails, call the fictional nurse line.
   closure=open  execution=failed  care_evidenced=False

3. THE SAME CALLBACK IS DELIVERED AGAIN, CLAIMING SUCCESS INSTEAD
   applied: False
   patient screen unchanged: True
   transitions appended: ['failed']

4. BOTH RECEIPTS ARE IN THE RECORD
    id            key dup_of accepted  reason
     1  callback-0001   None     True  None
     2         (null)      1    False  duplicate

5. THE RECORD HAS NO UPDATE PATH AND NO DELETE PATH
   REFUSED  UPDATE attempt_transitions SET transition = 'acknowledged'
             -> attempt_transitions is append-only: UPDATE is refused
   REFUSED  DELETE FROM callbacks
             -> callbacks is append-only: DELETE is refused
   REFUSED  UPDATE dispositions SET clinical_deadline_utc = '1999-01-01T00:00:00+00:00'
             -> dispositions is append-only: UPDATE is refused
```

**Not in this slice, and deliberately.** No routes, no service, no coordinator, no `presentation.py`, no templates, no ledger, no `tools.py`. `restatements` exists as a table with no write path, because the slice plan names it in this slice's deliverable; Slice 4 writes it. `api.py` still serves its Slice 1 in-memory episode and is not wired to the store: wiring the API is not in this slice's file list, and the comment there now says so. The Option C source is still unselected, so every string in the fixture remains provisional.

**What this evidence does not prove.** A green suite is not evidence of WorkBuddy access, clinical safety, human learning or patient benefit. No route, service or coordinator exists, so nothing here has been exercised end to end. The two-writer tests use threads in one process on one machine: they prove `BEGIN IMMEDIATE` plus the busy timeout serialises the lookup and the insert (now mutation-proven, see the concurrency row above), not that the design survives a hostile multi-process load. The append-only triggers refuse `UPDATE` and `DELETE` from any connection, and they do **not** refuse `INSERT OR REPLACE`, which is ordinary SQL too: see the correction at the top of this section and open item O1 below. They also do not protect against someone who drops a trigger, and the control case in the tests shows exactly that. Separately, a real four-process race on one key yields exactly one applied receipt, and a real process kill mid-transaction is recovered by WAL with `integrity_check` ok, so the concurrency mechanism is stronger than the thread-only tests show while the multi-machine case stays untested.

### Slice 3 adversarial review, 30 September 2026

**Verdict: the slice serves its purpose, with named caveats.** An independent adversarial review with no prior context was run against the branch, from the brief at `04-slices.md` (Slice 3). Full note: `docs/reviews/slice3-adversarial-review.md`. It re-ran five of the thirteen reported guard mutations and confirmed all five were real, went red alone, and reverted with an md5 match. Two of the reviewer's own first attempts were invalid and were re-run, which is recorded because a mutation experiment fails silently when the anchor or the test selection is not asserted.

**What it confirmed.** The raw-SQL append-only proof and its control case; the DELETE-trigger generation attributing exactly 13 `refuses_delete` failures with the 13 `refuses_update` cases green; `BEGIN IMMEDIATE` as load-bearing with green single-writer controls; D11 enforced twice **and independently**, since removing either half alone fails only its own test; the `source_ref` split; 310 passing; 1280 and 1136 lines; 69 state tests; zero lone LF; thirteen tables matching `04-slices.md`; the five Gate 4 named tests; `restatements` with no writer; `api.py` unwired.

**Two blocking findings.** F1, the `INSERT OR REPLACE` gap, is corrected in the opening claim of the Slice 3 section above and carried as O1 below. F2, the per-file split, is corrected in the evidence table above.

**Open items this review raised.** These are defects and test gaps rather than product decisions, so they are recorded here and not in the Slice 2 open-questions table above. No later slice may silently implement one early.

| # | Open item | Decided at |
|---|---|---|
| O1 | **`INSERT OR REPLACE` rewrites any row, including `dispositions.clinical_deadline_utc`, defeating I1's structural protection.** Fix: `PRAGMA recursive_triggers = ON` in `SqliteEpisodeStore.__init__` plus a `REPLACE` case in the parametrised append-only test. A Slice 3 defect left unfixed on the user's instruction of 30 September 2026, which declined code changes at this point | **Slice 4**, before any route writes to the store |
| O2 | Contention past the 5 s busy timeout makes `record_callback_once` raise a raw `sqlite3.OperationalError` and write no receipt, while the docstring at `state.py:437-439` says the losing callback is never lost. Fix: qualify the docstring and make lock contention a typed `StateError`, so a caller can tell "retry" from "refuse" | **Slice 6**, where the action path consumes the return value |
| O3 | Five schema constraints have no fail-capable test: the three `CHECK`s on `callbacks` (`state.py:301`, `:302`, `:303`), the `restatements.hint_level` `CHECK` (`:355`) and `UNIQUE (episode_id, version_no)` on `dispositions` (`:261`). Neutralising each alone leaves all 69 tests green. The `:303` constraint is the formal statement of the duplicate representation | **Slice 4**, one test per constraint |
| O4 | The duplicate representation rests on SQLite treating NULLs as distinct in a UNIQUE column. Documented at `state.py:17`, but no test creates more than one NULL-key row, so a suite that would pass under equal-NULL semantics proves nothing about the assumption it rests on | **Slice 4**, one test delivering the same key three times |
| O5 | `record_callback_once` returns a bare `bool`, so a duplicate and a consent refusal are indistinguishable without re-reading the record. A bool cannot express "we refused a success because consent was revoked" | **Slice 6**, where the action path consumes it |
| O6 | The D11 `CHECK` is weaker than the Python guard: an empty or whitespace `source_ref` passes the `CHECK` while the guard refuses it, so "enforced twice" is only equivalent for `source_ref IS NULL` | **Slice 4**, add `trim(source_ref) <> ''` to the `CHECK` |
| O7 | `insert_disposition` does not require a reassessment to move the deadline later. A version 2 with an earlier deadline than an expired version 1 would make reading 6 report no expiry event and could return the episode to `open` | **Slice 5**, where reassessment is built |
| O8 | The "Crash atomicity" row above tests the in-process rollback path, not a crash. A subprocess kill mid-transaction was verified separately to be recovered by WAL, so the property holds; the row label and the test's reach overstate it | **Slice 10**, the fault harness |

**Note on the exit check.** `04-slices.md`'s Check for this slice, "show the user a duplicate callback being recorded and the projection not changing", was run at the store layer and shown as console output above. It could not be run through the product, because this slice's file list is `state.py` and `test_state.py` only and the routes arrive at Slices 4 to 6. The gap is the plan's, and it is recorded rather than papered over.

## Gate 4 approval — 28 September 2026
The user approved **Gate 4 (Slice plan)** on 28 September 2026 with the instruction **"continue"**, following the approval question in this file. `04-slices.md` now records the approval.

**Approval authorises implementation code, slice by slice, in the planned order.** It does **not** authorise installs beyond the declared test dependencies, credentials, recruitment, external calls, deployment, or a push. Each slice still stops for the user's "continue, or re-steer?" before the next begins.

**Two sub-questions were open at drafting. Both resolved at approval, under the recommendation given:**

| # | Question | Resolution |
|---|---|---|
| 1 | **ADR-0007 — which layer owns canonicalisation?** | **Reading A accepted.** Canonicalisation lives in `domain`; the coordinator returns raw spans. ADR-0007 is now `accepted`, and the Gate 3 `compare_plan` signature is amended. `ExtractedPlan` carries **both** the raw span and `uncertain_fields`. |
| 2 | **The Option C source.** | **Scheduling only.** Still unselected, licensing still unchecked. Blocks Slice 5 and nothing earlier. If no source clears by 2 October → Option B; clinical wording is **not** authored to unblock the schedule. |

**If either resolution is wrong, say so** — ADR-0007 affects Slices 2 and 4, the source affects Slice 5.

## Slice 1 complete — 28 September 2026

**Tracer bullet runs end to end.** `POST /api/episodes` → `GET /api/episodes/{id}` → the four-line patient page, served from `127.0.0.1` with no database, no domain layer and no coordinator.

| Evidence | Result |
|---|---|
| `pytest tests/` | **11 passed** |
| Live `curl` on `127.0.0.1:8137` | health, create, projection and 404 all correct |
| Missing route → 404 | confirmed |
| Simulated label inside the serialized projection | confirmed (D11) |
| No `http-equiv="refresh"`, no `<script>`, no CSS animation/transition | confirmed (C8 — no timer anywhere) |

**Defect found and fixed during this slice — a real one.** The first live render produced **"You or you must act now."** on line 2. `PLAN.md` §6.1, `02-architecture.md` §7 and `01-product.md` all render line 2 as "You or *[named person]* must act now."; with a patient owner that sentence is malformed. **The test suite did not catch it — inspection of the running app did**, which is exactly why Gate 4's standing rule is "run it and show the result" rather than "the tests pass".

- **Fix applied:** line 2 now reads "Myself must act now.", with `OWNER_DISPLAY` as a named-owner constant.
- **Regression test added:** `test_line_two_does_not_render_a_doubled_owner`.
- **Flagged, not silently absorbed:** this **diverges from three approved documents.** The correction belongs in those documents at the next Gate 1 touch. Slice 9 must implement whichever form they then carry — the Slice 1 literal is not the authority.

**Files created:** `pyproject.toml`, `src/carerelay/__init__.py`, `src/carerelay/api.py`, `src/carerelay/demo/fixture.py`, `src/carerelay/demo/__init__.py`, `src/carerelay/static/style.css`, `fixtures/scripted_episode.json`, `tests/test_api.py`.

**Not yet done, and deliberately:** no database (Slice 3), no disposition is written on episode creation (`02-architecture.md` §3.1 — confirmed by `test_create_episode_returns_an_id_and_no_disposition`), and the fixture wording is still a **provisional placeholder** pending the Option C source check.

## Gate 4 draft — 28 September 2026

`04-slices.md` is written and **awaiting explicit approval**. Drafting it authorises no code. Thirteen slices, full Gate 3 scope, with constraint C1 satisfied: the external card (Slice 7) completes before the Closure Contract build (Slice 9).

**User instructions at drafting (28 September 2026):**

| # | Instruction | Consequence |
|---|---|---|
| 1 | Re-verify Gate A before planning against it | Gate A re-checked. Findings below. |
| 2 | **Keep the full scope** — do not cut to fit the schedule | No capability cut. The schedule risk is recorded as R1 in `04-slices.md` §6/§5 rather than resolved by cutting. |

**Gate A re-verification, 28 September 2026.** No `WORKBUDDY_API_KEY` or `WORKBUDDY_AGENT_ID` in the environment; no `.env`; no `workbuddy` or `codebuddy` Python package installed. **On that evidence the platform path is [unknown]-to-unavailable.** Gate A remains **overdue** since 26 September and has still not run. Slice 6 therefore plans the labelled local-simulation fallback as the default and wires the platform path only if credentials appear. The pre-recorded Gate 2 §3.3 reversal applies if Gate A has not passed by 11 October.

**Two results already in hand, before any product code:**

- **K1 and K2 PASS** — `spike/tests/test_kill_conditions.py`, 15 tests, 0 failures, Python 3.13.14, including four defect-injection tests confirming the assertions can fail. This is a **deterministic-layer spike result**, not an implementation result.
- **Slice 1's environment check passes** — the FastAPI stack installs and imports into an isolated venv; the intermittent AppControl block on stdlib venv creation did not fire.

**Open items at drafting:**

- **The Option C source is not selected.** Licensing and Singapore applicability unchecked. This blocks Slice 5 (the judged fixture) and nothing earlier. If no source can be cleared by 2 October, escalate to Option B — do not author clinical wording to unblock the schedule.
- **ADR-0007 is `proposed`.** It amends the Gate 3 `compare_plan` signature so canonicalisation lives in `domain` (Reading A). It affects what K1 can claim and needs acknowledgment at Gate 4 approval.
- **The schedule does not fit.** 102–169 h against 144 h available, solo, 18 days. Recorded as R1.

**Gate 4 approval question:** Approve Gate 4 as drafted, or what should change?

## Decision records

`docs/adr/` now holds eight Architecture Decision Records capturing the choices that outlive this feature — ADR-0001 to ADR-0008 — plus an index at `docs/adr/README.md`. They summarise decisions already approved at Gates 1–3 and the Gate 4 drafting instructions. **The gate documents remain authoritative**; where an ADR disagrees with them, the gate document wins and the ADR is corrected.


## Gate 3 approval — 26 September 2026

The user approved **Gate 3 (Program Design)** on 26 September 2026, on the same day it was drafted, with two amendments made at approval.

Approval covers: the planned file footprint, the type and method contracts, the call stacks, the failure-capable test plan, the callback dedupe representation, the Gate B protocol, and the 90–150 h build plus 20–35 h baseline estimate.

**Gate 3 approval authorises drafting Gate 4 only.** It does **not** authorise code, installs, credentials, recruitment, external calls, or a push. Gate 4 remains pending and no code may be written before Gate 4 is approved.

### Amendments made at approval

| # | Amendment | Where |
|---|---|---|
| 1 | **§6.1 added — the two reviewer-free kill conditions.** Two of the three PlanBack cut conditions (false mismatch on correct restatements; emergency guidance delayed by read-back) are pure system properties. They are lifted out of the stalled study and execute **before any participant work**, requiring no clinical review and no Gate A | `03-program-design.md` §6.1, §5 |
| 2 | **§6.2 rewritten — Option A + C selected.** The comparator is now **non-clinical** (Option A) and the fixture is **sourced verbatim from attributable published guidance** (Option C). The original text said the study "cannot run as specified"; that dependency is resolved by decision | `03-program-design.md` §6.2, §8.3 |

### Gate 2 backtrack — D6 comparator material

**Option A changes D6's comparator content, so Gate 2 D6 is formally backtracked.** The decision itself is unchanged — external artefact, between-subjects, scripted post-failure question, pre-registered cut rule. What changes is the *material*: it now carries no symptom, urgency or disposition content.

| | Before | After |
|---|---|---|
| Comparator content | Bilingual clinical card with the fixture wording | Content-neutral instruction task, same shape, **no clinical content** |
| Review required to run | Clinical + native-speaker + bilingual clinical | **None** — no guidance is administered to anyone |
| What the result supports | Understanding of care advice | Understanding of the **mechanism** only |

**Consequence the submission must state:** the study measures whether read-back plus truthful status changes comprehension, burden and false-completion belief. It does **not** validate clinical advice. Impact & Relevance loses weight accordingly, and no claim may imply otherwise.

### Open at approval

- **Source selection for Option C.** No source chosen; licensing and Singapore applicability unchecked. **This precedes use** and is a Gate 4 task. Note `CareRelay.md` records that wholesale copying of licensed Schmitt–Thompson protocols is out of scope.
- **Option B rejected but not closed.** A reviewer remains valuable for clinical-credibility language, but no longer blocks the study. Not chased on a clock.
- The two §6.1 kill tests have **not been written yet** and must precede participant work.

## Gate 3 draft: 26 September 2026 (superseded by the approval above)

`03-program-design.md` is now **APPROVED** (see the approval record above). It pins planned files, types, call stacks, failure-capable tests, the callback dedupe representation, and a 90–150 person-hour build estimate plus 20–35 hours for the baseline. Gate 4 remains pending and no implementation is authorised. Gate A, participant recruitment and the participant comparison remain unproved.

**The clinical-review blocker has a decision paper: `clinical-review-blocker.md` (26 September 2026).** Headline finding: the hackathon does **not** require a clinical reviewer, and the blocker was narrower than `03-program-design.md` §6 implied — the build, the fixture, the fault harness and the ledger were **not** blocked. Two of the three PlanBack kill conditions (false-mismatch and delayed-emergency-guidance) are **testable with no participants and no reviewer at all**; they are now lifted out of the stalled study as Gate 3 §6.1 and run first. **The user selected Option A + C on 26 September 2026**, which removed the blocking dependency and triggered the Gate 2 D6 backtrack recorded above. Option B (one reviewer) was not chased on a clock but is not closed.

The `02-architecture.md` header previously read "Not approved". Fixed 26 September 2026 — it now records the Gate 2 approval and points to this file for authority.

## Gate 2 approval — 25 September 2026

The user approved **Gate 2 (Architecture) revision 2** on 25 September 2026, following an independent round-2 adversarial review whose verdict was APPROVE WITH CHANGES and whose eleven blocking items were all applied or explicitly resolved.

Approval covers: D1–D12, the module and trust boundaries, the pinned tool-execution path (§3.3), the UI API and the three-tool MCP surface, the attempt/transition/callback schema (§4.1), the three flows, D11 evidence provenance and D12 sticky expiry, the non-functional surfaces (§8), the pre-registered baseline study (§9), the amended expired-screen rendering with its copy rules (§7), and the change log (§11).

**Gate 2 approval authorises the Gate A access spike only.** It does **not** authorise implementation code. Gates 3 and 4 remain pending, and no code may be written before Gate 4.

### Carried into Gate 3

- **A real effort estimate.** The round-2 review's 90–150 h (plus 20–35 h for the baseline) is unverified. The user has accepted it as achievable; Gate 3 must still produce its own estimate.
- **Gate 4 must sequence the baseline comparison (Gate B) before the Closure Contract build.** `PLAN.md` §7 currently schedules the sessions *after* the state machine — wrong order.
- **The Gate A spike is due 26 September.** If it fails, §3.3's fallback applies and the platform-advantage claim is weakened and stated as weakened.
- **D9 (scheduled reassessment) is not deliverable.** The P1 load-bearing answer is "execution substrate". `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is not delivered and must not be implied in the submission.

## Gate 1 reopening — 25 September 2026 (approved)

Gate 1 was **deliberately reopened** after its first approval to resolve the H2 accessibility hazard the round-2 adversarial review identified, and to approve the expired-screen wording. Both changes were approved by the user the same day.

| Change | Decision | Files |
|---|---|---|
| **H2 no longer has a timer** | The plan card at H2 **stays on screen until the patient hides it**. No countdown, no auto-dismiss, no auto-advance anywhere in the product. `dwell_seconds` is recorded for the judge ledger and never shown to the patient. Rationale: a five-second rule is unreadable for older adults, unusable with a screen reader, and un-extendable — it penalised the exact population the product exists for | `PLAN.md` §5.2 + new §5.2.1, `01-product.md`, `mockups/02` |
| **Expired-screen wording** | Approved with **softer, human-centred wording**. The first draft ("The time to go was [deadline]. It has passed." / "Call [route] now") was rejected as too blunt. Final rendering plus five copy rules: no reproach, no alarm, no false comfort, a named route, deadline stays visible | `02-architecture.md` §7 |

**Gate 1 remains APPROVED** with these amendments. Both changes were made openly in the documents, not silently at Gate 3.

## Gate 1 approval — 25 September 2026 (original)

The user explicitly approved Gate 1 on 25 September 2026. This covers the Gate 1
scope below: the reframe, PlanBack, the recall hint ladder, the Closure Contract,
the two-axis state model, the design principles and the five HTML wireframes.

Approval of the product specification does **not** authorise implementation.
Gates 2–4 remain pending and no code may be written until Gate 2 is approved.

### Carried forward as explicit, unresolved Gate 1 risks

These were surfaced by the adversarial review, accepted rather than resolved, and
must be treated as live inputs to Gate 2:

- **Mandatory organiser-usage proof is still absent.** Without it the project does
  not proceed to scoring.
- **No qualified clinical reviewer and no authorised protocol.** The prototype must
  remain a labelled research demonstration using scripted fixtures.
- **The load-bearing assumption is untested:** that a fixed bilingual card does not
  perform equally well. It should be tested before the mechanisms are built.
- **Neither mechanism requires WorkBuddy.** WorkBuddy's genuine dependency is the
  coordinator, the real tool call, its real failure event, and session resume.
- **Mandarin voice is a gated TRTC spike only.** No account access or clinical
  accuracy has been demonstrated.

## Gate 1 scope as of 21 September 2026

Gate 1 was opened with a broader product definition. It has since been narrowed by the independent adversarial review and expanded by two new mechanisms. Both changes were approved on 25 September 2026.

| Change | Where |
|---|---|
| Reframe: closed-loop confirmation of urgent advice, not the ledger | `docs/reviews/gate2-adversarial-review-round1.md` |
| PlanBack — read-back with deterministic critical-field comparison and bounded repair | `03-planback-closure-contract.md`, `PLAN.md` §5.1 |
| Recall hint ladder (H0–H3) with the level always recorded | `PLAN.md` §5.2, `01-product.md`, `mockups/02` |
| Closure Contract — two independent axes and five fault invariants | `03-planback-closure-contract.md`, `PLAN.md` §6.1 |
| Corrected single-ladder state model to two axes | `PLAN.md` §6 |
| Patient sees four lines; the ledger is judge-facing | `PLAN.md` §6.1, `mockups/03` |
| Four design principles adopted; load-bearing audit fails the current scope | `docs/DESIGN_PRINCIPLES.md` |

## Document map

The skill's canonical gate filenames are reserved for Gates 2 to 4. Two supporting documents already occupy those numbers, so a fresh session should read the map below rather than assume by number.

The map spans three folders, reorganised on 30 September 2026 so that a review artefact is not filed beside the record it reviews. Gate documents and their supporting notes stay in this folder. Adversarial reviews and review briefs live in `docs/reviews/`. Decisions that outlive this feature live in `docs/adr/`. The layout is described once, for a reader with no prior context, in `docs/README.md`.

**This folder, `docs/plans/urgent-advice-accessibility/`**

| File | Kind | Purpose |
|---|---|---|
| `00-status.md` | state | this file |
| `01-product.md` | **Gate 1 doc** | problem, success metric, announcement, product rules, screens |
| `02-architecture.md` | **Gate 2 doc** | **approved revision 2** (25 Sep), D1 to D12, pinned tool path, attempt-transition schema, external between-subjects baseline, non-functional surfaces, change log |
| `03-program-design.md` | **Gate 3 doc** | **approved 26 September 2026**: files, types, call stacks, failure-capable tests, effort |
| `04-slices.md` | **Gate 4 doc** | **APPROVED 28 September 2026**: 13 slices, full scope, Gate A re-verification, R1 schedule risk |
| `03-planback-closure-contract.md` | supporting note | specification and feasibility for PlanBack and the Closure Contract. Carries the `03-` filename that Gate 3 needed |
| `clinical-review-blocker.md` | supporting note | decision paper, 26 Sep: what the reviewer blocker actually blocks, and three routes through |
| `research-workarounds.md` | supporting note | which blockers are workaroundable and which are hard gates. Listed here for the first time: it was named in `AGENTS.md` section 2 but was missing from this map |
| `mockups/` | Gate 1 assets | five plain-HTML screens, throwaway by design |

**`docs/reviews/`**

| File | Kind | Purpose |
|---|---|---|
| `gate2-adversarial-review-round1.md` | review | independent review, 21 Sep: verdict, competitors, scores, kill dates. Renamed from `02-adversarial-review.md`, which collided with the Gate 2 number and is the documented cause of the file-map trap |
| `gate2-review-prompt-thorough.md` | review brief | the prompt handed to the independent round-2 reviewer |
| `gate2-adversarial-review-thorough.md` | review | independent round-2 review: APPROVE WITH CHANGES, three blocking defects |
| `slice2-adversarial-review.md` | review | independent adversarial review of Slice 2, 30 Sep: verdict, findings, judgement calls, evasion, test quality, and the remediation applied before Slice 3 |
| `slice3-adversarial-review.md` | review | independent adversarial review of Slice 3, 30 Sep: verdict (yes, with named caveats), two blocking findings, five unproven constraints, and the open items it raised |

**`docs/adr/`**

| File | Kind | Purpose |
|---|---|---|
| `README.md` | index | ADR index |
| `0001` to `0008` | decision records | decisions that outlive this feature. **The gate documents remain authoritative**; where an ADR disagrees with them, the gate document wins and the ADR is corrected |

## Notes for a fresh session

- Product identity: CareRelay must not stop at advice; it checks understanding and feasibility, preserves the clinical deadline, and reports failed or unconfirmed handoffs truthfully.
- **PlanBack:** the patient restates the plan; **code, not a model**, compares `action`, `deadline` and `next_owner`; a mismatch is repaired field by field, bounded to two rounds, then a human path. The model only extracts fields.
- **Hint ladder:** H0 unaided → H1 structural slots → H2 card shown then hidden → H3 plan given. The level used is **always recorded**, because a hint containing the answer turns a comprehension check into a reading test.
- **The ladder fades.** A new plan starts at H1; an unaided success lowers the starting level next time; a failure restores it; changes happen on trends, not single rounds; fading is invisible to the patient. This is **vanishing cues with errorless learning and spaced retrieval** — an established cognitive-rehabilitation technique, cited as prior art.
- **Cognitive claims are prohibited.** No cognitive improvement, “keep your mind sharp,” dementia prevention, screening, risk score or diagnostic output — in the product, submission, video or pitch. Meta-analyses find no far transfer from cognitive training; the FTC fined Lumosity $2 million in 2016 for exactly this claim. The scaffold improves retention of *this plan* and nothing more.
- **Language rule:** never “cognitive rot,” “brain training” or “use it or lose it” in anything user-facing.
- **Longitudinal cognitive signal is research, not a demo claim.** Recorded in `PLAN.md` §5.3 as an out-of-scope hypothesis so the ambition is not lost; it is not presented in the submission.
- **Closure Contract:** execution status and evidence status are two independent axes; the clinical deadline is immutable to operational retries; five invariants are test cases, not slogans.
- **The load-bearing untested assumption:** that a fixed bilingual card plus a direct booking link plus a NurseFirst fallback does *not* perform equally. This is the primary kill test and must run first.
- **Honest dependency boundary:** PlanBack and the Closure Contract are application logic and do not require WorkBuddy. WorkBuddy's genuine contribution is the coordinator, the real tool call, its real failure event and session resume.
- **Open question from `docs/DESIGN_PRINCIPLES.md` (re-verified 22 Sep, resolved 25 Sep):** the P1 load-bearing answer is **"execution substrate"**. The scheduled-reassessment module (D9 in the Gate 2 draft) was dropped after the round-2 adversarial review found it unbuildable as specified — no scenario, no ingress endpoint, no estimate. `DESIGN_PRINCIPLES.md` §8's "monitored episode that cannot lie" is **not** delivered. The submission must state this rather than imply a capability that is switched off.
- Mandarin and voice are accessibility modes. English text remains the auditable reference until bilingual clinical content is reviewed.
- Provisional persona: Mei, 72, Mandarin-preferring, with remote daughter support. The respiratory-symptom recommendation remains an injected fixture until clinical review.
- **No asset may name a real healthcare facility.** The fixture provider is fictional and labelled.
- No implementation code may be written before Gate 4 approval. **Gate 4 was approved 28 September 2026; implementation is now authorised slice by slice.**
- **Gate 4 approved 28 Sep** with the instruction "continue". Full scope was kept on the user's explicit instruction; the schedule risk is recorded as R1 in `04-slices.md`, not resolved by cutting. Constraint C1 is honoured: the external card (Slice 7) completes before the Closure Contract build (Slice 9), with the Gate B kill test (Slice 8) between them.
- **ADR-0007 accepted 28 Sep** — canonicalisation lives in `domain` (Reading A). The Gate 3 `compare_plan` signature is amended, and `ExtractedPlan` carries both the raw span and `uncertain_fields`.
- **Gate A has still not run** and is now more than a day overdue. Re-verified 28 Sep: no credentials, no `.env`, no SDK package. Plan for the labelled `local-sim` fallback; take the platform path only if access appears.
- **K1 and K2 pass** (spike, 15/15). Deterministic layer only, and dependent on Reading A (ADR-0007).
- **ADR-0007 is proposed, not accepted** — it amends the approved Gate 3 `compare_plan` signature. Needs acknowledgment at Gate 4 approval or an explicit instruction to keep the original signature and accept a weaker K1 claim.
- Gate 2 draft (`02-architecture.md` revision 2) pins D1–D12: Python+FastAPI default (reversible only before the first domain-code commit), pure domain core, append-only attempt transitions, derived closure with sticky expiry, external between-subjects baseline, deterministic abstention with a closed vocabulary, **D9 dropped**, voice deferred and isolated. **The Gate A access spike is due 26 Sep** with a pre-recorded fallback decision.
- **Two items that needed a user decision are now both resolved** (25 Sep):
  1. The **H2 timed hide is gone.** The plan card stays until the patient hides it; no timers anywhere in the product; `dwell_seconds` recorded for the ledger only. Gate 1 was reopened deliberately and re-approved.
  2. The **expired patient screen** wording is approved, softened on the user's instruction, with five copy rules in `02-architecture.md` §7.
- Round-2 review effort estimate: **90–150 h** for this architecture plus 20–35 h baseline. The user has reviewed this and **accepted the estimate as achievable** (25 Sep). Gate 3 still produces a real estimate; the acceptance is not a substitute for one.
- Branch and commit state, re-verified 30 September 2026 after the Slice 3 ship: `main`, `slice-3` and `slice-4` all sit at the tip of the Slice 3 work, whose four substantive commits are `4841b71` (the store's command and result types), `ad3401a` (the append-only record), `6b831f3` (the documentation restructure) and `27bed4b` (the record), followed by the two record corrections that fix the branch state they falsified. `slice-2-domain-core` sits at `80245e4`. `gate-2-architecture` and `care-relay-adversarial-review` no longer exist as branches; their commits remain reachable from `main`. `origin` holds exactly one branch, `refs/heads/main`, still at `e3d4dad`, so **`main` is ahead of the remote by the whole Slice 3 work: nothing is pushed**. No gate authorises a commit or a push; the Slice 1, 2 and 3 commits were made on the user's explicit instruction of 30 September 2026. The push itself succeeds when it is asked for, so the earlier credential failures no longer apply.
- **Slice 3 is complete** (30 September 2026): the append-only record exists at `src/carerelay/state.py`, `restatements` has no writer yet, and `api.py` is still not wired to the store. The `source_ref` open item from the Slice 2 review is settled. Ten readings of the approved documents are flagged in the Slice 3 section above; reading 6 (the snapshot reports the expiry event for the current disposition version) is the one most worth an explicit yes or no. The Slice 3 review gives reading 6 an explicit **yes**, with reasoning at section 7 (B4) of the review note; the decision remains the user's. **Reviewed 30 September 2026:** verdict yes with named caveats, two blocking findings corrected above, and eight open items O1 to O8. O1, the `INSERT OR REPLACE` gap, blocks any claim of structural immutability. Full note: `docs/reviews/slice3-adversarial-review.md`.
