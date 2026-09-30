# Adversarial review: CareRelay Slice 3 (the append-only record)

**Supporting note. Authoritative for nothing.**

Reviewed 30 September 2026 against branch `slice-3`, HEAD `e3d4dad`, working tree
uncommitted at the time of review. No commit, branch, push or tag was made. The tree was left exactly as
found: `git status --short --untracked-files=all` listed 9 paths before and after,
and `src/carerelay/state.py` hashed `326d31fa8473c7aeeb1bd39ab35491e3` before and
after every experiment. Scratch scripts were written to `%TEMP%` and deleted.

**This note now lives at `docs/reviews/slice3-adversarial-review.md`, and the record
has been corrected.** The brief's rule of engagement was "leave the tree exactly as
you found it", and it governed the review itself: nothing was committed, branched,
pushed or tagged, and the source was not touched. The corrections were a separate,
later step, authorised on 30 September 2026 and applied only to documentation, not to
code. `00-status.md` now carries the corrections to F2, F3, F11 and F12 and records
this review in its slice list. Section 8 says what was corrected and what was
deliberately left alone.

The 9 paths this review recorded describe the review session, not the tree today. The
30 September documentation restructure added `docs/README.md` and this note and renamed
four review files into `docs/reviews/`, and the whole Slice 3 work was then committed on
the user's explicit instruction and fast-forwarded into `main`.
`git status --short --untracked-files=all` is now empty.

Evidence labels: `[verified]` observed by me in this session, `[estimate]` my
judgement, `[guess]` a hunch, `[unknown]` not established.

---

## 1. Verdict

**Yes, with named caveats.** The store delivers what the exit contract asks for at
the store layer. Four of its five headline mechanisms survived independent attack:
the raw-SQL append-only proof, the double enforcement of D11, the `BEGIN IMMEDIATE`
concurrency claim, and the `source_ref` split are all real and all fail-capable. The
caveats are not cosmetic: one central claim in the slice's own docstring is falsified
by ordinary SQL, two statements in `00-status.md` are false, and five schema
constraints are asserted with no test that can fail without them.

The slice is not dishonest. It is a well-built layer with an overstated headline and
a record that has drifted from its own code. (The record was corrected on 30 September 2026; see section 8.)

---

## 2. Findings

### BLOCKER

**F1. `INSERT OR REPLACE` rewrites any row, including the clinical deadline, and no
test can see it.**
`src/carerelay/state.py:378-397` (`_append_only_ddl`), claim at
`src/carerelay/state.py:6-7` and `docs/plans/urgent-advice-accessibility/00-status.md:113`.

What I did: opened a raw `sqlite3` connection to a store database and ran
`INSERT OR REPLACE INTO dispositions (...) VALUES (...)` supplying version 1's
`(episode_id, version_no)` with a different `clinical_deadline_utc`, then committed.

What I observed: the statement succeeded and committed. The deadline changed from
`2026-10-01T10:00:00+00:00` to `1999-01-01T00:00:00+00:00` and the row count stayed
at 1. The same statement rewrote `episodes.persona` to `TAMPERED` and rewrote a
`callbacks` receipt, flipping `accepted` to 0 and replacing `callback_key_digest`
with a forged value. `PRAGMA recursive_triggers` is `0`, which is SQLite's default:
under `REPLACE` the implicit DELETE does not fire a `BEFORE DELETE` trigger.

What it means: `state.py:6-7` says "the database has no update path and no delete
path at all", and `00-status.md:113` repeats it. Both are false against ordinary
SQL. `REPLACE` is standard SQLite, not an exotic bypass, and it is the one statement
that reaches the exact row the deadline invariant protects. The Slice 3 tests cover
`UPDATE` and `DELETE` only, so the suite is green while the property does not hold.

Smallest fix, verified: add `PRAGMA recursive_triggers = ON` in
`SqliteEpisodeStore.__init__` next to the other pragmas. With it set, the same
statements are refused on `episodes`, `dispositions`, `events` and `callbacks` with
`IntegrityError: <table> is append-only: DELETE is refused`. Then add `REPLACE` as a
third parametrised case beside the existing `UPDATE` and `DELETE` cases.

Caveat the fix does not remove: the pragma is per-connection, while the triggers are
per-schema. After the fix the honest claim is "no update or delete path from this
module's connections, and `UPDATE`/`DELETE` refused from any connection", not "the
database has no update path".

**F2. The per-file test split in the record is wrong and does not sum.**
`docs/plans/urgent-advice-accessibility/00-status.md:119`.

What I did: ran the suite and each file separately with `-o addopts=""`.

What I observed: `310 passed, 1 warning`, split `89` domain, `141` boundaries, `11`
api, `69` state. The record says "**88** domain, **141** boundaries, **11** api, **69**
state" and "The four counts sum to the total". 88+141+11+69 = **309**, not 310. The
domain figure is stale from Slice 2; this slice added
`test_the_source_ref_half_of_the_guard_is_independently_proven` to `test_domain.py`.

What it means: the claim document contradicts its own arithmetic. A false statement
in `00-status.md` is blocker-grade by this project's own rule.

### SIGNIFICANT

**F3. The record names a file that does not exist, and its path count is wrong.**
`docs/plans/urgent-advice-accessibility/00-status.md:115`.

What I observed: `docs/plans/urgent-advice-accessibility/slice-3-review-prompt.md` is
absent, and `git status --short --untracked-files=all` listed **9** paths at review time, not the
claimed ten. This is the second consecutive slice where this exact row was wrong: the
Slice 2 version of the row said four paths when the tree held nine.

What it means: working-tree counts decay on the next edit, and a named file can
disappear. Re-derive this row immediately before finalising, or delete it. A count
that is wrong twice is a row that should not be a claim.

**F4. Contention past the busy timeout loses the receipt and leaks a raw
`OperationalError`.**
`src/carerelay/state.py:433-440` (docstring), `src/carerelay/state.py:481-498`
(`_write`).

What I did: held `BEGIN IMMEDIATE` open on one connection and called
`record_callback_once` on the store.

What I observed: after 5.5 s it raised `sqlite3.OperationalError: database is
locked` and wrote **0** receipts.

What it means: the docstring says "the second writer waits for the lock rather than
failing, so the losing callback is recorded as a duplicate instead of being lost".
That is true only inside the 5 s window. Beyond it, the R6 failure mode the slice
claims to have closed reappears as a lost receipt. The failure is loud rather than
silent, so the Slice 4 stop condition ("silently loses duplicates") is not breached.
Two things should change: qualify the docstring, and make lock contention a typed
`StateError` so the caller can tell "retry" from "refuse". Every other refusal in
this module is typed; this one is not, and Slice 6 is where a caller will need to
distinguish them.

**F5. Five schema constraints have no fail-capable test.**
`src/carerelay/state.py:301`, `:302`, `:303`, `:355`, `:261`.

What I did: neutralised each alone (`CHECK (1 = 1)`, or widened the `UNIQUE`) and ran
all of `tests/test_state.py`.

What I observed: **69 passed** every time. Nothing in the suite detects their
removal.

What it means: the CHECK at `:303` is the formal statement of the duplicate
representation, and the two at `:301`/`:302` are the "a refusal always carries a
reason" rule the record itself calls load-bearing (reading 3). The record's claim
that the guards were mutation-proven does not extend to them. Smallest fix: one test
per constraint that inserts the violating row through a raw connection and requires
`IntegrityError`.

**F6. The NULL-distinctness assumption is documented but unproven.**
`src/carerelay/state.py:17` documents it, `src/carerelay/state.py:291` depends on it.

What I did: called `record_callback_once` three times with one key, which is the
natural double-tap-plus-provider-retry case.

What I observed: the store wrote 1 accepted row and 2 duplicate rows, both with a
NULL `callback_key`. Every duplicate test in the suite delivers a key at most twice,
so no test ever creates more than one NULL-key row.

What it means: the representation rests on SQLite treating NULLs as distinct in a
UNIQUE column, and the suite would pass unchanged if it did not, because a single
NULL never conflicts with itself. The dependency is documented, so it is not
silently coupled; it is simply untested. Smallest fix: one test that delivers the
same key three times and asserts three receipts.

### MINOR

**F7. The SQL `CHECK` is weaker than the Python guard on empty strings.**
`src/carerelay/state.py:314` against `src/carerelay/state.py:1022-1029`.

Observed: a raw `INSERT` with `level='documented'`, `simulated=0`, `source_ref=''`
(and `'   '`) is **accepted** by the CHECK. The Python guard refuses both, because
`not record.source_ref` is true for an empty string.

Means: `00-status.md:124` says "A raw INSERT of a simulated or unsourced `documented`
row raises `IntegrityError`". True for `source_ref IS NULL`; false for an empty or
whitespace `source_ref`. The two enforcements are independent, but they are not
equivalent. Smallest fix: add `AND trim(source_ref) <> ''` to the CHECK.

**F8. The exit check was demonstrated through a script, not the product.**
`docs/plans/urgent-advice-accessibility/00-status.md:163-198` against
`docs/plans/urgent-advice-accessibility/04-slices.md:134`. See section 3.

**F9. `test_the_check_is_what_refuses_the_row` does not detect the CHECK's absence.**
`tests/test_state.py:859-898`.

Observed: with the CHECK removed, this test still passed; only
`test_the_database_check_is_independent_of_the_python_guard` failed.

Means: it asserts the control table accepts the row and that `evidence` is empty,
but it never issues the rejected `INSERT` against `evidence`. The refusal half lives
entirely in the other test, so the two are only jointly meaningful. Its docstring
("Without this, the refusal above could come from a column type, a trigger or
anything else") claims more than the test does.

**F10. The "Crash atomicity" evidence is an in-process exception, not a crash.**
`tests/test_state.py:480-498`, `:639-658`, `00-status.md:126`.

The mechanism tested is the context manager's `except: ROLLBACK`, which the record's
own row text admits ("With the audit write made to raise"). The row label does not.
I did test a real crash: a subprocess that began a transaction, inserted, and called
`os._exit(9)` without committing. On reopen the row was absent and
`PRAGMA integrity_check` returned `ok`. So the property holds; the label and the
test's reach overstate it. A subprocess-kill test would make the label true.

**F11. "Two edited files" where three code files were edited.**
`00-status.md:128` and `00-status.md:425`. Three code files were edited
(`domain/models.py`, `test_domain.py`, `api.py`), plus four documentation files.

**F12. "Zero U+2014 in all four files this slice touched".**
`00-status.md:129`. Five code files were touched. `src/carerelay/api.py` contains 5
U+2014 characters, but `difflib` against `HEAD` shows 0 added and 0 removed on
em-dash-bearing lines: they are pre-existing. Across every edited file the net
change in em dash characters is 0 (`tasks/todo.md` 2 added and 2 removed,
`00-status.md` 1 and 1, `PROGRESS.md` 0 and 1), so no new em dash character was
introduced anywhere. The substance is right and the noun and the count are wrong.

### NOTE

**N1.** The file map lists `clinical-review-blocker.md` twice
(`00-status.md:390` and `:394`). Pre-existing.

**N2.** The record says a `busy_timeout` of 0 "turns the callback race RED". Over
three consecutive runs both race tests failed. The record understates its own
mechanism. `[verified]`

**N3.** `mutated_closure` (`tests/test_domain.py:1148-1223`) is a hand-maintained
reimplementation of `derive_closure`, not a mutation of it. The two-flag split is
real and the new test does exactly what the record says, but the closure precedence
ladder is copied by hand at `:1201-1212`, so the harness cannot detect drift in the
real function. A real mutation (edit `rules.derive_closure`, run, revert) is what the
project rule asks for.

**N4.** `insert_disposition` does not require a reassessment to move the deadline
later. A version 2 with an earlier deadline than an already-expired version 1 would
make `load_snapshot` report no expiry event and could return an episode to `open`.
Reassessment is not built, so this is a Slice 5 obligation, not a Slice 3 defect, but
reading 6's correctness depends on it.

---

## 3. The exit contract, quoted, and judged

`04-slices.md:134`, verbatim:

> | **Check** | Show the user a duplicate callback being recorded and the projection not changing. |

And the Goal at `04-slices.md:128`, verbatim:

> | **Goal** | The clinical record persists, and **I1 (immutable deadline) holds because no retry code path writes a disposition**, stated honestly, as §10 of the architecture requires. |
>
> Quoted verbatim except for the punctuation between "disposition" and "stated": the source uses an em dash there, and this note does not reproduce em dashes.

**The check is satisfied at the store layer and dodged at the product layer.**
`[verified]` The output pasted at `00-status.md:163-198` is genuine: I reproduced the
duplicate path and the three refusals independently. But it is console output from a
script, not a demonstration through a running product.

That dodge is the plan's, not the author's. `04-slices.md:130` gives Slice 3 exactly
two files, `state.py` and `test_state.py`, and routes arrive at Slices 4 to 6. The
product surface the check implies does not exist at Slice 3 by the plan's own
sequencing, so the check as written was not runnable. The author should have said so
in one line rather than presenting script output under the heading "This slice's exit
check, run and shown". A plan-level gap, recorded honestly, is not a defect; a
plan-level gap presented as a met check is.

On the Goal: the slice **does** meet it, and meets it in the honest form the plan
asked for. I1 is not structurally enforced by this slice, and `02-architecture.md:27`
and `:291` both say so. What then fails is F1: the slice's own record re-upgrades the
honest weak claim to a strong structural one that the mechanism does not deliver.

---

## 4. Claims I verified as true

One line each. These parts of the record can be relied on.

1. `310 passed, 1 warning`. `[verified]`
2. `tests/test_state.py` is 1136 lines and contains 69 tests. `[verified]`
3. `src/carerelay/state.py` is 1280 lines. `[verified]`
4. Zero lone LF in both new files and in all three edited code files. `[verified]`
5. Thirteen tables, and the set matches `04-slices.md:129` exactly. `[verified]`
6. A `BEFORE UPDATE` and a `BEFORE DELETE` trigger generated per table from
   `APPEND_ONLY_TABLES`. `[verified]`
7. The append-only proof runs against a raw connection and raw SQL, so the module's
   Python guards are not in the loop. `[verified]`
8. The control case works: dropping two triggers lets the same `UPDATE` and `DELETE`
   through. `[verified]`
9. Stopping DELETE-trigger generation fails exactly the 13 `refuses_delete` cases and
   leaves all 13 `refuses_update` cases green, so the attribution is exact.
   `[verified]`
10. `BEGIN IMMEDIATE` is load-bearing: `BEGIN` fails both race tests and leaves both
    single-writer controls green. `[verified]`
11. `BEGIN IMMEDIATE` occurs once as executable code (`state.py:491`) and four times
    in docstrings, so the two "concurrency mutations" are one edit applied twice, as
    the record says. `[verified]`
12. D11 is enforced twice **and independently**: dropping the CHECK fails only
    `test_the_database_check_is_independent_of_the_python_guard`; removing the Python
    guard fails only `test_evidence_provenance_constraint`. `[verified]`
13. The five Gate 4 named tests exist under their approved names. `[verified]`
14. `test_callback_duplicate_and_reorder` does test reorder, not only duplicate:
    kinds `[FAILED, ACKNOWLEDGED]`, seqs `[1, 2]`, and both `project_attempt` and the
    store's attempt snapshot return `FAILED`. `[verified]`
15. `restatements` exists with no writer: the only references in `src/` are the table
    DDL and its entry in `APPEND_ONLY_TABLES`. `[verified]`
16. `api.py` is still not wired to the store, and the edit is one comment, which is
    accurate. `[verified]`
17. `AttemptCommand` and `CallbackResult` are frozen dataclasses with no I/O.
    `[verified]`
18. The `source_ref` settlement is real: the two flags remove one half of the guard
    each, and the new test's four assertions do what the record says. `[verified]`
19. `derive_attempt_key` is length-prefixed, so `("ab","c")` and `("a","bc")` do not
    collide. `[verified]`
20. A real **four-process** race on one key yields exactly one applied receipt:
    outcomes `[False, False, False, True]`, 4 receipts, 1 accepted, 1 transition.
    `[verified]`
21. A real process kill mid-transaction is recovered: row absent, `integrity_check`
    `ok`. `[verified]`
22. No test in the suite has zero assertions (AST scan of all three test files).
    `[verified]`
23. Every append-only table has a seed row before the trigger tests run, with an
    assertion that enforces it. `[verified]`

---

## 5. Claims I could not verify

- **The eleven guard mutations as a set.** I do not have the author's anchors, so I
  cannot confirm that each of the eleven was applied to a unique anchor and that none
  was a silent no-op. I independently re-ran five: DELETE-trigger generation, the D11
  CHECK, the D11 Python guard, `BEGIN IMMEDIATE` and the busy timeout. All five were
  real, all went red alone, all reverted with an md5 match. The other six are
  `[unknown]`.
- **"Zero U+2014 in every file written"** as a claim about
  `slice-3-review-prompt.md`. The file does not exist, so it cannot be scanned.
- **Whether the slice actually took its budgeted 12 to 20 hours.** No time record
  appears in the slice note. `[unknown]`
- **Durability across a kill after COMMIT but before the OS flush**, which is what
  `synchronous = FULL` is for. I tested only the pre-COMMIT case. `[unknown]`
- **Whether the record's claim that the suite "returned to 310 passed afterwards"**
  held at the time. It holds now. `[verified]` for now, `[unknown]` for then.

---

## 6. The strongest argument against my verdict

If you hold that the store is the only writer of this database, that no code in the
repository uses `REPLACE` (I grepped `src/` and `tests/`: nothing does), and that
every caller goes through the repository methods, then F1 is a theoretical hole and
the slice is sound for the deadline. That case is genuinely strong, and it is why my
verdict is "yes with caveats" rather than "no".

My answer is that the slice did not make a claim about its own module. It made a
claim about **the database** ("no update path and no delete path at all"), it chose
triggers rather than a Python guard precisely so the proof would be against raw SQL,
and the test that proves it opens a raw connection and issues raw SQL but omits the
one ordinary statement that defeats the mechanism. The cost of being wrong here is
one pragma and one parametrised test case. The cost of the claim being wrong is a
false statement in the document a judge reads, in the layer the product thesis rests
on.

---

## 7. Answers to the numbered attack surfaces

**A1. "Append-only" overclaims?** Yes. `state.py:6-7` and `00-status.md:113` claim
more than the mechanism delivers, and F1 is the counterexample. Mechanisms not
reached for: `PRAGMA recursive_triggers = ON` (one line, verified to close the hole),
a SQLite authorizer callback via `set_authorizer` (would refuse any statement outside
a whitelist, at the cost of complexity), and a read-only connection for the read
path. The omission is not justified for the pragma. File permissions and a read-only
connection do not apply to the writer role.

**A2. I1.** The architecture is honest: `02-architecture.md:27` and `:291` both
restate I1 as "a code-review property, not a structural impossibility".
`03-planback-closure-contract.md:155` still asserts immutability as an invariant. The
document that retreats from honesty is the Slice 3 record, which re-upgrades it to a
structural claim the mechanism does not deliver. So: the restatement is honest, the
headline is not.

**A3. R6 across processes and machines.** The thread construction is the weakest
available, and I ran the stronger one: four processes on one file produced exactly one
applied receipt, so the mechanism is not thread-specific. `[verified]` What it does
not survive is contention longer than the busy timeout (F4). A multi-machine version
would need a real server; SQLite over a network filesystem is unsupported and the
architecture does not claim otherwise. No durability claim is made that the tests
cannot reach, except the unconditional line at `state.py:437-439`.

**B4. Reading 6, the snapshot reports the expiry event for the current disposition
version: yes.** `[estimate]` An expiry event names a version. A reassessment inserts a
new version with its own deadline, so the earlier event describes a plan that is no
longer current. Under the opposite reading `load_snapshot` would report an expiry
event for version 1 while version 2 is current, and `derive_closure` would return
`expired_unresolved` for an episode whose current deadline has not passed. That tells
a patient their window has gone while they still have time, which is the exact false
statement the product exists to prevent. The opposite reading also makes
`expiry_events.disposition_version` a meaningless column. Keep reading 6. The v1 row
is never deleted, so the ledger still shows it; only the current-plan projection
ignores it. One caveat, N4: nothing stops a reassessment from setting an earlier
deadline, and reading 6's correctness depends on that not happening.

**B5. `restatements` with no write path: correct sequencing, not a liability.**
`[estimate]` The trigger generation is driven by `APPEND_ONLY_TABLES`, so the table
inherits both triggers automatically and its presence creates no violation path: the
only write available is an `INSERT`. It does add a second place where a CHECK is
asserted with no test (F5, the `hint_level` constraint), which is a Slice 4
obligation. Keep it.

**B6. `record_callback_once` returning a bare bool: a real surface defect.**
`[verified]` It is not hypothetical. The product must distinguish "already received"
from "refused for consent", and today the caller has to re-read `list_callbacks` and
scan for the reason, which is exactly what the tests do (`tests/test_state.py:747`,
`:774`). Both refusals do write a row, so the information exists, but the return
surface hides it. Smallest fix: return the `CallbackReceipt`, or a small result value
carrying `accepted` and `rejection_reason`. It matters most at Slice 6, where a bool
makes "we refused a success because consent was revoked" indistinguishable from "the
provider retried". Note that the concurrency test's `sorted(outcomes, key=str) ==
[False, True]` would need updating.

**B7. The NULL `callback_key` and SQLite's multiple-NULL rule.** Documented, not
silently coupled: `state.py:17` says "SQLite permits many nulls under a unique
constraint". Unproven: no test creates two NULL-key rows, and the suite would pass
unchanged if NULLs were treated as equal, because a single NULL never conflicts with
itself. See F6.

**B8. `derive_attempt_key` with a fixed namespace and no secret: a risk to key
secrecy only, not to double-tap semantics.** `[estimate]` The key is a deterministic
function of the triple, and that determinism is precisely what I3 needs. An attacker
who can guess the triple can compute the key, and the only thing that buys them is
colliding their own key with a legitimate attempt, which produces an
`IdempotencyKeyCollision` refusal or a suppressed duplicate, not a dispatch. The key
never leaves the server, because D5 says the client never supplies one. A secret
becomes load-bearing only if a key is ever exposed to a client or must be stable
across deployments, which is the stated Slice 6 reason. Not a Slice 3 defect.

**C9. Vacuous assertions: none found.** `[verified]` Every test function contains at
least one `assert` or `pytest.raises`. The two weakest are
`test_every_append_only_table_has_a_row_to_attack` (a precondition, `count >= 1`) and
`test_the_key_is_derived_from_the_triple` (a determinism check, but it also asserts
inequality across all three fields, so a constant function fails it). Neither passes
against a stub.

**C10. Does `test_callback_duplicate_and_reorder` test reorder?** Yes.
`tests/test_state.py:586-596` asserts the transition kinds, the sequence numbers, and
that both the domain projection and the store's own snapshot return `FAILED`. The
reorder half is three assertions about the losing outcome, not one assertion about
`seq`. The name is justified.

**C11. Python guard versus SQL CHECK: the redundancy is justified.** `[verified]` I
removed each alone and each has its own failing test (F5's neighbours, M2b and M4b).
In production the Python guard runs first and the CHECK is the backstop for a writer
that bypasses the module, which is the case the slice explicitly designed for. So
neither is dead code and neither is untested. One qualification: the CHECK is weaker
than the guard on empty strings (F7), so "belt and braces" is only true for
`source_ref IS NULL`.

**C12. Guards reached by a path outside the module's own methods.** The append-only
proof does, and I verified it: raw connection, raw SQL, no module code in the loop.
The D11 CHECK does, and I verified it the same way. The concurrency tests do not use
raw SQL, but they use independent connections, which is the property under test. The
remaining guards (consent re-check, premature expiry, duplicate detection,
idempotency collision, disposition contiguity, rollback) are reached only through
their own public methods. That is defensible for pure-Python guards, since there is
no other path to them, but it means "each guard is independently proven" is true for
the schema guards and, for the Python guards, only through the `mutated_closure`
reimplementation in the domain tests (N3).

**C13. The mutation tally.** `[verified]` for five of thirteen. I re-ran the
DELETE-trigger generation, the D11 CHECK, the D11 Python guard, `BEGIN IMMEDIATE` and
the busy timeout. All were real, all went red alone with correct attribution, all
reverted with an md5 match, and the suite returned to 310. None was a silent no-op.
The remaining eight are `[unknown]`. Worth recording: two of my own first attempts
were invalid, one because a `-k` pattern matched a different test name and one
because an LF anchor was written against a CRLF file. Both failed silently. The
author's procedure (assert the anchor count, revert with an md5 check) is the right
one and I used it.

**C14. Does the slice make the Closure Contract invariants hold?** It makes them
**computable**, and it structurally enforces two of them. `[estimate]` I3 (no
duplicate dispatch) is enforced by the UNIQUE idempotency key and the
`open_attempt_once` duplicate path. The append-only substrate that I1 and I2 rest on
is real for `UPDATE` and `DELETE` and not for `REPLACE` (F1). I1 itself is not
enforced, and the architecture says so. I2 and I5 are `domain` properties from Slice
2. I4 is not enforced: `load_snapshot` returns `human_acceptance_id` and
`escalation_id`, and nothing checks that an owner is named. So the title "with the
Closure Contract invariants" is accurate about the substrate and misleading about
enforcement. `04-slices.md:128` asked for exactly the honest weak form, so the slice
meets its own plan; the overclaim is in the record, and it is a slice-level gap that
one pragma and one test would close.

**C15. Is the slice over-built for the deadline?** Partly. `[estimate]` The shape is
right: append-only is the architecture's central decision and the deadline invariant
is the product thesis, so a real enforcement layer is not gold-plating. Three things
are wider than the exit contract. First, breadth: making all thirteen tables
insert-only goes beyond D3's four clinical tables, and three of the constraints in
that extra width have no test (F5). Second, the exit contract asked for one visible
demonstration and received 1280 lines of module plus 1136 lines of tests for a layer
no route and no user touches yet. Third, `derive_attempt_key` (reading 10) is a
service-layer decision placed in the store. Against that: this is the substrate for
everything downstream, it is a self-contained layer a revert can remove cleanly, and the tests are
mostly doing real work. My verdict is not "over-built" but "wider than the contract,
with unproven constraints inside the extra width". If the schedule (R1: 102 to 169
hours against 144 available) has to give, the extra width is where to cut, not the
append-only proof.

---

## 8. What I did not examine

The boundary of this review, stated so the emptiness is not mistaken for coverage:

- `tests/test_boundaries.py` and the Slice 2 scanner remediation. I did not re-test
  the five recorded evasions or hunt for new ones. That was Slice 2's review and its
  subject.
- `rules.py` and the domain comparator beyond the `source_ref` split. The 89 domain
  tests were counted, not reviewed.
- `fixtures/scripted_episode.json`, `spike/`, `tools/`, `recovery-20260928/`.
- The other eight guard mutations (section 5).
- `api.py` behaviour beyond confirming that the edit is one comment and that the API
  is not wired to the store.
- Any judgement on clinical wording, the Option C source, or the patient-facing
  strings. Those are product and clinical decisions, not review findings.
- Windows-specific WAL and busy-timeout behaviour under a network filesystem, and
  anything multi-machine.
- I did not start `uvicorn`, make an external call, install anything, or touch
  credentials, per the project's review skill.

**What was corrected, and what was not.** On the user's explicit instruction of
30 September 2026, the documentation was corrected: the per-file split now reads
89/141/11/69, the path-count row was re-derived and the missing
`slice-3-review-prompt.md` reference dropped, the em dash row was reworded, and this
note was added to the file map and the slice list. The record's own account of the
review, including the O1-O8 open items, is in `00-status.md`.

**Not applied, on the same instruction.** No code changed. `state.py:6-7` and
`:437-439` still carry their overclaims, and the five constraints in O3 still have no
fail-capable test. Those are carried as O1, O2 and O3 in `00-status.md`, anchored to
Slice 4 and Slice 6.
