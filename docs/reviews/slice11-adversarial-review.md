# Slice 11 adversarial review: the fault harness and the seven sequences

**Supporting note, authoritative for nothing.** Run 8 October 2026 against
`slice-11-fault-harness` by a reviewer with no prior context on this slice's build.

## Verdict

**SOUND. Proceed to Slice 12. Two claims in the record overstate what was proved, and four substantive gaps sit in the new scanners and in what "both surfaces" means.** The guard coverage is the strongest evidence produced in this project so far: all seven mutations were independently re-run, each went RED for the right reason, and each was paired with a control that stayed GREEN. The weakness is not in the seven guards. It is in the two new scanners, whose detection lists are mostly untested, and in the second "serialized patient surface", which is a constant.

## Method

- Baseline: `python -m pytest tests -o addopts="" -q` -> **902 passed**, 0 skipped, per-file split sums to 902.
- All seven mutations re-run independently, one at a time, each with a control selector. Every target backed up outside the repository, md5 recorded, restored, and re-verified with a delayed re-read (OneDrive read-after-write).
- The new scanners were mutated entry by entry: every facility noun and every receipt key was deleted alone and the needle test re-run.
- No server was started, no install was made, nothing was committed, pushed, branched or stashed.

## Findings

| # | Severity | Location | What is wrong | Why it matters | Smallest fix |
|---|---|---|---|---|---|
| R1 | SHOULD FIX | `tests/test_boundaries.py:942` | `\b{noun}\b` does not match inflected forms. Measured: "General Hospitals", "the hospitals", "three nursing homes", "wards 12 and 13", "the polyclinics", "two hospices" all return `[]`, while their singulars are caught | The docstring at `:933` claims the scan catches "the shape every real facility name in this domain has". Plural usage is the same shape, so the stated scope is wider than the measured scope | Allow an optional plural suffix, for example `rf"\b{re.escape(noun)}(?:s|es)?\b"`, and add one plural needle per limb |
| R2 | SHOULD FIX | `tests/test_boundaries.py:906` (nouns), `:954` (keys) | Seven of eight facility nouns and one of three receipt keys are **dead entries**: deleting `polyclinic`, `nursing home`, `hospice`, `medical centre`, `medical center`, `casualty`, `a&e` or `ward` alone, or deleting `source_ref`, leaves `test_scanner_detects_injected_needle` GREEN. Only `hospital`, `provider_ref` and `receipt_id` have teeth | A denylist whose entries no test exercises can be emptied silently by a future edit, and the suite stays green. This is the same shape as the Slice 8 vocabulary finding, one layer down | One injected needle per entry, or state in the tuple's comment that the unexercised entries are anticipatory and deliberately unpinned |
| R3 | SHOULD FIX | `src/carerelay/api.py:540-571`, used at `tests/test_fault_sequences.py:361-362` | The second "serialized patient surface" is a **constant**. `patient_page` renders `fixture.demo_lines()` and never reads its `episode_id` argument, so the page shows the unresolved four lines in every state. The harness asserts only `status_code == 200` plus the scanners on it | `04-slices.md:253` requires each invariant at "**both** API and serialized patient surfaces". Only the JSON projection is really asserted. In the clock-change case (`:698`, `:704`, `:709`) the harness asserts `EXPIRED_LINES` on the API while the page still shows "Please act now." and the harness cannot see it | Either assert the tuple on the page as well (it will need the page to become episode-derived, which Slice 7 owns), or state in the section that the page is the static Slice 1 tracer bullet and only the scanners run on it |
| R4 | SHOULD FIX | `tests/test_fault_sequences.py:6-21`, `00-status.md` Slice 11 table row, against `04-slices.md:253` | "Each asserts I1 to I5" is not literally true. Measured per sequence: **I3** in 3 of 7 (timeout, duplicate, restart); **I5** in 3 of 7 (timeout, stale, consent); **I1**'s stored-instant half in 2 of 7 (timeout test 2, clock). I2 and I4 do ride on the tuple equality in all seven, and that half is sound | The contract line is a per-sequence requirement. A reader checking it against the code finds three sequences that assert neither I3 nor I5 | Correct the claim to name which invariant each sequence pins, in both the module docstring and the table row |
| R5 | SHOULD FIX | `tests/test_fault_sequences.py:215` (`open_store(tmp_path/...)`) against `render.yaml:9-10,48-54` and `api.py:344` | All seven sequences run on **SQLite**. The deployment runs **Postgres on Supabase** through `APP_DATABASE_URL`, and `PostgresEpisodeStore.record_callback_once` (`src/carerelay/postgres_store.py:805`) is a separate implementation using `SELECT ... FOR UPDATE` | **O8 is therefore closed for the SQLite store only**, and `00-status.md` records "O8 is CLOSED" unqualified. The crash-atomicity property is exactly the kind that differs between a single embedded transaction and a row-locked server transaction | Qualify the O8 row as SQLite-proven and Postgres-unproven, and either add the sequences to the Postgres suite or record the engine in the row |
| R6 | NIT | `tests/test_boundaries.py:943-944` | The "fictional" exemption looks only 16 characters **backward**. "hospital (fictional)" is flagged. Accurate to the docstring, asymmetric in effect | Low impact; the sanctioned form is "fictional X". Worth a half sentence rather than a change | State the direction in the docstring (it already says "shortly before it") |
| R7 | NIT | `tests/test_boundaries.py:954,975` | The key match is a casefolded substring, so `providerRef` and `provider-ref` are not caught. Partly disclosed at `:970` | Only bites if a surface ever stops serializing snake_case | Note it beside the existing limit, or normalise separators before the match |
| R8 | NIT | `tests/test_fault_sequences.py:364-372` | Measured: the JSON projection (315 bytes) and the page (840 bytes) contain **no** facility noun and **no** receipt key today, so the three negative scans cannot fire on the current product | Not a defect: a negative scan with no violation is the normal state, and the needle test is what gives it meaning. Stated so a reader does not read the passing scans as coverage | None. Keep the needle test |

## The seven mutations, re-run independently

Every one went RED **for the right reason**, with a control that stayed GREEN, and every file restored CLEAN (md5 verified after a delayed re-read).

| Mutation | Target | Observed failure | Control |
|---|---|---|---|
| T1 empty branch returns `failed` | `rules.py:420-421` | `assert 'failed' == 'attempted'` (`:407`) | Reordered GREEN |
| S1 route recheck skipped | `tools.py:160-162` | `DID NOT RAISE RouteNotPermitted` (`:467`) | Duplicate GREEN |
| D1 duplicate lookup never fires | `state.py:1156-1159` | `IntegrityError: UNIQUE constraint failed: callbacks.callback_key` | Reordered GREEN |
| R1 `ordered[-1]` wins | `rules.py:422` | `assert 'acknowledged' == 'failed'` (`:590`) | Timeout GREEN |
| X1 receipt commits alone | `state.py:1216-1219` | parent read a surviving `CallbackReceipt` (`:634`) | Duplicate + restart companion GREEN |
| C1 expiry stickiness dropped | `rules.py:496-498` | line 1 diff `'Please act now.' != 'You can still do this.'` (`:355`) | Duplicate GREEN |
| V1 consent recheck forced to `None` | `state.py:1186-1188` | `assert 'applied' == 'refused'` (`:748`) | Duplicate GREEN |

**X1 is the single most valuable test in the slice**, and it survives scrutiny on the point that could have broken it. The risk was that the parent's connection holds a stale WAL snapshot and therefore cannot see the child's committed receipt, which would make the "nothing survives" assertion true even under the mutation. It does not: the RED message shows the parent reading the surviving `CallbackReceipt` by value. The test discriminates.

## Judgement calls

- **"Stale availability" re-read as the execution-time route recheck: AGREE, given the disclosure.** `04-slices.md:253` names the sequence and the build has no availability table, so the re-reading cannot be falsified against the plan. It is stated in the module docstring (`:35-41`) and repeated in `00-status.md` rather than left to be inferred from the name. This is the honest available reading.
- **No `src/` change: AGREE, verified.** `git status --short -- src/` is empty. The `04-slices.md:256` file list anticipated `state.py`; finding that no change was needed is a result, and the slice reports it as one.
- **O8 closed: PARTIALLY AGREE.** Closed for SQLite (proved, see X1). Not proved for Postgres, see R5.
- **`test_boundaries.py` keeping LF: AGREE.** The whole file is LF including the 888 pre-existing lines and the diff carries additions only, so this session did not convert it. Note that git warns "LF will be replaced by CRLF the next time Git touches it", so the exemption rests on convention rather than on a `.gitattributes` entry.

## Attempted breakage that failed

- **Anchor discipline in `_mutate_slice11.py`.** All seven anchors are unique in `read_bytes()` (count 1) and the harness conforms them to the target's newline, so the CRLF trap that cost Slice 6 does not apply. The pre-flight runs `--collect-only` per selector and refuses to proceed when one resolves to nothing, so a rename cannot silently orphan a mutation as it did on Slice 6.
- **The "NOT PROVEN" half of the harness.** The `[SKIP]` failure mode of Slice 6 is gone: a missing or non-unique anchor is recorded as NOT PROVEN and the run returns 1.
- **Test counts.** 902 collected and 902 passed; per-file split sums to 902 exactly; `test_fault_sequences.py` holds 11, `test_boundaries.py` gained 1 def (43 -> 44), so baseline 890 plus 12 is arithmetically consistent.
- **Line endings.** `test_fault_sequences.py` and `_mutate_slice11.py` are CRLF with zero lone LF.
- **Em dashes.** Zero on added lines in all six modified or added files, computed as (`+` lines carrying U+2014) minus (`-` lines carrying U+2014), not by grepping the file.
- **The `INSERT OR REPLACE` bypass from Slice 3.** `PRAGMA recursive_triggers = ON` is still present at `state.py:668`.
- **Scanner limbs.** Making `scan_for_unlabelled_receipts` return `[]`, neutralising `_SIMULATED_TRUE`, and dropping `hospital`, `provider_ref` or `receipt_id` each turn the needle test RED. The needle test has teeth on the entries it uses. Its gap is the entries it does not use (R2).

## False claims in `00-status.md`

Two, both in the Slice 11 section added 8 October 2026:

1. **"Each sequence asserts I1 to I5 at both serialized surfaces"** is overstated twice over: not all five invariants in every sequence (R4), and only one of the two surfaces is content-asserted (R3).
2. **"O8 is CLOSED"** is unqualified while the proof is SQLite-only and the deployment is Postgres (R5).

Everything else measured in that section was accurate: 902 passed against a 890 baseline, 11 fault tests plus 1 scanner self-test, 7 of 7 RED with 0 SURVIVED and 0 NOT PROVEN, zero em dashes, the CRLF and LF conventions, and no `src/` change.

## Could not be verified

- **The live `uvicorn` and `curl` run.** No server was started by this review, and no transcript of it is in the tree. All seven live bullets in the section are unverified here.
- **Whether `04-slices.md`'s "stale availability" meant something narrower.** There is no availability table to test against, so the re-reading is unfalsifiable against the plan text.
- **Postgres behaviour of the seven guards.** No DSN was used by this review, so R5 is a scope finding rather than a measured Postgres failure.
- **Whether the 902-baseline figure of 890 was itself measured on the same tree.** It is consistent with 902 minus this slice's 12 tests, which is what the record says, but the 890 run was not repeated.

## Outstanding corrections, not applied

This review wrote no record file. R4 and R5 need edits to the Slice 11 section, the O8 row and the "Crash atomicity" row of `00-status.md`, plus mirrors in `PROGRESS.md` and `tasks/todo.md`. Those edits are a separate step and need their own instruction.
