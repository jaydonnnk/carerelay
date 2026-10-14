# Slice 15 guard-to-evidence classification, 14 October 2026

[verified] This closes the finding in `/tmp/carerelay-slice15-finish-20261013/review.md`
that "not every remaining implied/type/exception predicate has a final documented
classification. Named totals are insufficient." Every predicate in the regenerated
inventory now carries exactly one class, and every class below that denies
independent mutation credit names the mechanism that masks the guard and cites the
observed mutant run that proved it.

Review base and current HEAD are both `b91a4ad248fbd22e407b9536f1825d62b52ae8c2`.
All Slice 15 implementation work is uncommitted on `slice-15-durable-start`. This
document is evidence, not authority: `00-status.md` owns slice state.

## 1. The standard applied

`AGENTS.md` section 6 requires one real failure per guard branch, and treats a
fault two checks can both catch as proof of neither. So a named mutation count is
not coverage. Three things are separated here, because conflating them is what made
the earlier totals unreadable:

- **Proven independent**: removing this one guard, and nothing else, breaks a named
  control. The mutant is restored byte-exact and the control is green again.
- **Classified without credit**: removing the guard does not change observable
  behaviour, because a second layer, a downstream validator, the type system or the
  single approved fixture already refuses. These are recorded, not counted.
- **Allocated elsewhere**: real Postgres engine behaviour is Slice 19; confirmation,
  scoring, permission and request guards are Slices 16 to 18.

A count of predicates is structure, not coverage, and a matched compound anchor does
not prove every clause inside it. Both traps are named in `AGENTS.md` and both are
why this document exists.

## 2. Method

1. `inventory.py` (evidence root) re-executes `tests/_mutate_patient_experience.py`
   by AST with `carerelay` imports stripped, so the named mutation list is read from
   the harness itself rather than transcribed. It then walks the Python AST of the
   six scoped modules and the `if` conditions of the four scoped TypeScript modules,
   splitting each condition into top-level `&&` / `||` clauses.
2. Each predicate is cross-referenced two ways: whitespace-normalized substring
   match against every mutation anchor, and line-span overlap with every anchor.
   Substring matching alone under-reported coverage badly, because a multi-line
   clause extracted from source does not textually match the single-line anchor that
   removes it. Both are recorded.
3. Every predicate left unmatched by both methods became a **candidate mutation**
   with a pinned selector, and was run. The observed result, not the author's
   reasoning, decides the class:
   - **RED** with green controls and a byte-exact restore becomes a permanent named
     mutation.
   - **SURVIVED** (the pinned control still passed) or **NOT PROVEN** (the mutant
     failed for a reason that is not a behavioural refusal) is classified from the
     mutant log, and the candidate is removed from the named set so it cannot be
     carried as a permanent survivor.

The first probe ran 75 candidates: 28 RED, 33 SURVIVED, 13 NOT PROVEN, all targets
restored exact. Triage showed three distinct causes, and each was handled
differently rather than being waved through:

- **Wrong selector or wrong mutation.** 18 candidates pinned a control that did not
  exercise the guard, or mutated a clause whose neighbour still refused. These were
  repaired: correct selectors, a corrected `revision_unsafe` mutation that drops only
  the upper bound, and four new focused controls in
  `tests/test_journey_guard_inventory.py`.
- **Genuine redundancy.** The guard is masked by a second layer. Classified below
  with the mechanism and the observation.
- **Harness taxonomy gap.** The mutant changed product behaviour, but the failure
  surfaced as the product's own typed refusal rather than an `AssertionError`, so the
  harness scored it NOT PROVEN. See section 3.

The corrected probe ran 45 candidates: 43 RED, 1 SURVIVED, 1 NOT PROVEN. The
survivor was re-pinned to a new direct control and went RED. The NOT PROVEN case is
classified in section 5.

## 3. The harness change, and why it is a strengthening

`tests/_mutate_patient_experience.py` scored a mutant RED only on an
`AssertionError`-shaped failure, and separately excluded interpreter-level breakage
(`SyntaxError`, `ImportError`, `NameError`, `AttributeError`, `TypeError`,
`KeyError`, `OperationalError`). That left a third category uncounted: a mutant that
makes the product answer with **its own typed refusal**. A valid stored read that now
returns `JourneyUnavailable`, or a valid body that now refuses to canonicalize, is a
real behavioural change and a real failure of a real control.

`TYPED_REFUSAL` now recognizes the product's namespaced refusal types
(`CommandInvalid`, `CommandConflict`, `JourneyUnavailable`, `MissingDisplayText`,
`DomainError`, `StateError`, `EpisodeNotFound`, `InvalidJourneyRecord`,
`LockContention`). The interpreter-breakage exclusion is unchanged and still
dominates, so a malformed mutant still cannot earn credit. This converted eight
candidates from NOT PROVEN to RED on their own evidence; the reason is recorded in
the harness source beside the pattern.

## 4. Newly proven independent guards

Forty-five guards the 13 October review inventoried as lacking an independent kill
are now named mutations, each RED with green before/after controls and a byte-exact
restore. They are listed by label in the harness and by result in
`mutations-full-final.log`; the groups are:

| Group | Count | Guards |
|---|---|---|
| Recorded stored input refuses (`G03 recorded input`, `G03 recorded identity`) | 9 | empty episode id, non-int revision, negative revision, unsafe revision, recorded policy version, recorded text version, action outside its policy, absent approved action wording, non-string readback identity |
| Projection screen copy and cue (`G03`) | 17 | no-plan disposition branch, later display day, unrelated event kind filter, foreign event version filter, readback/hint/barrier dispatch, H3 ladder, H2-or-shown ladder, recorded round wins the ladder, unavailable survives a later round, timing repair field, latest round gate, waiting screen text, pending/unavailable/uncertain feedback text |
| Codec and capability (`G12`, `G13`) | 8 | canonical scalar accept, canonical list accept, nullable disposition gate, **HMAC comparison**, exact create body, preparation log scrubbing, select token only for the allowlisted offer, intake replay does not rewrite the disposition |
| Receipt and record loading (`G02`, `G31`, `G37`) | 4 | recorded policy resolved in the transaction, recorded policy needs a registered version, replay requires a claim, unknown episode has no snapshot |
| Whole-response decoder (`G06 closure`) | 3 | reconcile compares one disposition version, reconcile keeps a foreign episode, equal revision needs a read |
| Entry-screen decoder cases (`G06 inventory entry_*`) | 4 | entry step, entry redaction, entry care flag, entry line count |

Two of these deserve to be named explicitly because they are the safety-critical
ones the earlier totals hid:

- **`G13 MAC comparison`** removes `if not hmac.compare_digest(signature, expected):`
  from `verify_operation`. The ten `G13 MAC <dimension>` mutations prove each binding
  dimension by altering what is signed; none of them proves the comparison happens at
  all. With the comparison removed, a token verifies under a rotated key. The pinned
  control `test_s15_mac_binds_each_dimension` asserts refusal under
  `b"rotated-synthetic-key"`, so it goes RED. This is also the offline half of the
  key-rotation check.
- **`G03 recorded input policy_version` / `text_version`** are the "bundle A remains
  A when configured B changes" exit criterion. Removing either lets a recorded
  disposition resolve against a different policy version.

### A selector can hide a real guard

`G37 unknown episode has no snapshot` was first pinned to
`test_unknown_and_auth_refusal` and **SURVIVED the complete 443-case run**, after
looking RED in a smaller probe. It was not flaky and the guard was not redundant. A
direct probe established the truth: with the guard removed,
`store.load_snapshot("never-created")` returns an empty snapshot instead of raising,
which is a real behaviour change. The pinned selector could not see it, because the
journey read path reaches `_load_bundle`'s own `EpisodeNotFound` a moment later, and
`test_unknown_and_auth_refusal` only exercises that path.

The guard is now pinned to `test_unknown_episode_has_no_snapshot_at_the_store`, which
calls the store directly, and it is RED. The lesson is recorded because it is the
failure mode this whole document exists to catch: **a green control batch does not
mean the selector touches the guard.** Nine legacy patient and ledger reads call
`load_snapshot` with no bundle read behind them, so for those callers this guard is
the only refusal, and only a store-level control can prove it.

## 5. Classified without independent mutation credit

Each row names the masking mechanism and the observed mutant result. Evidence root
for the observations: `classification-observations.json` in this session's evidence
directory, with the two probe roots named inside it.

| Guard | Class | Mechanism, with the observed mutant result |
|---|---|---|
| `rules.py` `now_utc.tzinfo is None` | IMPLIED | The domain models already refuse a naive datetime. Mutant raised `DomainError: now_utc must be timezone-aware; domain never guesses a timezone` before reaching the guard. |
| `rules.py` `policy is None or text is None` | CRASH-CONVERSION | Removing it yields `AttributeError: 'NoneType' object has no attribute 'version'` instead of `JourneyUnavailable`. Both refuse; the HTTP mapping differs (500 rather than 503). Recorded as a real difference that this harness deliberately does not score, because `AttributeError` is on the interpreter-breakage exclusion list. |
| `rules.py` `not deadline` and `not fallback` in the display guard | DUPLICATE-DOWNSTREAM | `MissingDisplayText` from the display validators refuses first: observed `'no approved deadline wording for disposition version 1' is not in the permitted set` and `'nurse_line' is not in the permitted set`. |
| `rules.py` `not original_owner` | DUPLICATE-DOWNSTREAM | Emptying `owner_display_by_id` still refused; the pinned control passed unchanged under the mutant. |
| `rules.py` `not isinstance(event, dict)` | CRASH-CONVERSION | For a known kind with a non-dict payload, removal yields `AttributeError` on `event.get`. The unknown-kind filter means the branch is unreachable for unrelated kinds. |
| `rules.py` `if bundle.consent_granted:` | IMPLIED | `_journey_offers` filters to `IMPLEMENTED_JOURNEY_COMMANDS`, which excludes `request`, so the added kind never reaches a projection. `G03 future command filtering` carries the proof. |
| `rules.py` `step == "handoff" and escalated_human_path != "nurse_line"` | UNREACHABLE-FIXTURE | The single approved fixture only ever escalates to `nurse_line`. Defence in depth for a path no approved content produces. Not deleted, because deleting it would silently pre-approve a future path. |
| `rules.py` `if pending: return ()` in `_journey_offers` | IMPLIED | The pending branch in `derive_journey` already sets `allowed = ()`. |
| `service.py` `if projection_error is not None: raise` | CRASH-CONVERSION | Removal yields `UnboundLocalError: cannot access local variable 'journey'`. The guard converts a crash into the typed 503 the API contract promises. Not scored, because `UnboundLocalError` is a `NameError` subclass. |
| `service.py` start kind/purpose clauses | DUPLICATE-LAYER | `state.create_with_claim_once` repeats the same capability check, so a single-layer removal is masked. The store layer is proven by `G31 creation refuses a foreign capability`'s pinned controls at the store boundary; the service layer's own distinct guard, the exact create body, is RED. |
| `api.py` `if prepare_kind is None or body_sha256 is None:` | DUPLICATE-LAYER | `service.prepare_command` refuses a `None` digest, so the route still answers 422. The route's own distinct guard, query-string scrubbing before the access log, is RED. |
| `service.py` `snapshot.expiry_event_id is None` | DUPLICATE-LAYER | `record_expiry_once` is itself idempotent, so dropping the condition records nothing twice. |
| `service.py` `if not any(o.kind == "select_example" ...)` | DUPLICATE-LAYER | A replayed claim short-circuits before the offer check; `test_intake_replay_does_not_reenter_stale_offer_check` pins that ordering, and `G13 intake prepare_offer` carries the preparation-layer proof. |
| `state.py` `existing is not None` in `claim_once` | DUPLICATE-LAYER | `create_with_claim_once` performs its own `tx.find` first, so the inner replay branch is unreachable from the create path. |
| `state.py` `row is None` in `complete_once` | DUPLICATE-ENGINE | The `journey_commands_claim_binding` trigger refuses a completion with no claim on SQLite; `test_s15_terminal_claim_binding_is_an_engine_guard` pins the trigger. Real engine behaviour is Slice 19. |
| `state.py` episode-exists check in `create_with_claim_once` | DUPLICATE-ENGINE | The `episodes` primary key refuses the second insert. |
| `state.py` `if not self._journey_write` in `_write_unlocked` | DUPLICATE-LAYER | `journey_transaction` refuses the same read-to-write upgrade; `G31 transaction read_to_write` carries that proof. |
| `state.py` `record_id is None` in `_order_by_events` | DUPLICATE-DOWNSTREAM | The next guard raises the same typed `InvalidJourneyRecord` for a `None` identity, only with a different message. |
| `state.py` `row is None` in `find` and `_load_bundle` | STRUCTURAL | Removal dereferences `None`, which crashes rather than misbehaves. |
| `episode-locator.ts` `!value` / `typeof value !== "object"` / `Array.isArray(value)` in `valid()` | IMPLIED | The exact-key clause on the following line refuses any non-record, and the enclosing `try` catches the `Object.keys(null)` throw. The exact-key clause is itself mutated (`G09 locator keys`). |
| `episode-locator.ts` the same three clauses in `decodeOperation` | IMPLIED | The exact-field-set clause on the same line is mutated as `G09 locator operation_fields`. |
| `episode-locator.ts` `token.length > 4096` | IMPLIED-BOUND | A denial-of-service bound, not a correctness guard: an over-long token still fails the alphabet, MAC or canonicality check. |
| `episode-locator.ts` `!origin` / `!host` in `allowAction` | IMPLIED | `new URL(null)` and `null.toLowerCase()` both throw inside the `try`, so the function still returns `null`. The surrounding clauses are mutated individually as `G09 action username/password/search/hash/path/host/insecure`. |
| `journey.ts` `!record(value.text)` | IMPLIED | `exactKeys(value.text, selectedTextKeys)` on line 192 refuses any non-record text for an assessed body, and `exactKeys(value.text, Object.keys(ENTRY_COPY))` refuses it for the entry body. A probe case was added, observed SURVIVED, and then removed rather than carried. |
| `journey.ts` `!current` in `reconcileJourney` | CRASH-CONVERSION | Removal dereferences `null` and throws out of a function with no `catch`. |
| `api.ts` `response.status === 401 \|\| response.status === 503` | UNPROVEN-NO-CONTROL | The distinction is the `reason` string (`unauthorised` versus `unavailable`). No current control asserts it, so no honest kill exists. Recorded as an open item for Slice 17, which owns the request/failure surfaces. |
| `postgres_store.py` eager mutex, nested read/write, episode and attempt scope, cursor reuse, isolation, lock-before-read, conflict replay after rollback | ENGINE-SLICE-19 | Not executable offline. Their SQLite twins in `state.py` are mutated; the portable SQL is pinned by the schema-parity and shared-surface controls. Real locks, isolation, trigger failures and driver transaction cleanup are Slice 19 obligations, and are not a hidden Slice 15 failure. |

## 6. What this does not prove

[unknown] No real Postgres engine behaviour. No assistive-technology or zoom
behaviour. No deployed persistence. No live ADP. No clinical suitability and no
participant benefit. Predicate inventories are extracted by AST and by a
parenthesis-matching scan of `if` conditions; a guard expressed without `if` (a
ternary, a `match`, a comprehension filter, a decorator) is not in the inventory and
is therefore not classified here. That is a limit of the method, not a claim that no
such guard exists.
