# Slice 6 verification check (independent, second pass)

Supporting note. Authoritative for nothing; `00-status.md` remains the only
authority for gate and slice state.

**Provenance.** Run on 3 October 2026 at the user's instruction: "walk through in
place of me and fix how u deem fit then let me know". This is a *verification pass*
over the fixes the Slice 6 adversarial review applied, not a re-run of that review.
It has three parts: verify the two fixes are real and mutation-checked, verify the
record's post-fix numbers, and report what it could not establish.

---

## 1. Verdict

**The two fixes are real and correct. The record's post-fix numbers are correct.
Three claims in the record are wrong or stale, one of them added by me.**

| Item | Verdict |
|---|---|
| F-1, `/static` mount | **TRUE.** `GET /static/style.css` returns 200 with a non-empty body; the page links it |
| F-1, mutation-checked | **TRUE.** Removing the mount turns exactly the new stylesheet test RED |
| F-2, revocation refusal test | **TRUE.** The `refused` receipt is reachable over HTTP with a specific reason |
| F-2, mutation-checked | **TRUE, but the stated anchor is the wrong branch.** The test is fail-capable; the mutation the record names targets a branch the test does not depend on (finding V-2) |
| Suite total 484 | **TRUE.** Confirmed, and the per-file split sums correctly |
| The honesty claim | **TRUE.** Independently re-attacked, seven injections, no 200 ever read `platform` |
| `00-status.md` Slice 6 per-file split | **TRUE.** 100/141/57/103/60/23 = 484 |
| `00-status.md` harness line count | **FALSE claim.** The record says the harness line count is re-stated in the Slice 6 review section. It is not stated anywhere (V-1) |
| `PROGRESS.md` "482 pass" | **STALE.** The tree is at 484 (V-3) |
| "11 of 11 mutations RED" | **FALSE as shipped.** M11 was silently skipped, and the harness's own control **FAILED** (V-4). **Repaired and re-run the same day: 11 of 11 RED, tree byte-exact** |

---

## 2. Baseline, re-derived

```
PYTHONPATH=src C:/Users/jayd0/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe \
  -m pytest -o addopts="" -q
484 passed, 1 warning in 18.42s
```

`[verified]` **484 passed, 1 warning.** The warning is the pre-existing Starlette
`httpx` deprecation, not a Slice 6 artefact.

Per-file, each collected on its own, and they sum:

| file | count |
|---|---|
| test_domain.py | 100 |
| test_boundaries.py | 141 |
| test_api.py | **57** |
| test_state.py | 103 |
| test_service.py | 60 |
| test_coordinator.py | 23 |
| **sum** | **484** |

`[verified]` the split matches `00-status.md:276` exactly, including the `57` for
`test_api.py` (55 at review time, +2 for the two fixes).

---

## 3. F-1, verified

`[verified]` `Tests/.. api.py:86-90` mounts the static directory next to the app.

```
GET /static/style.css -> 200, len 1946
page links the path: True
```

**A number in the record is slightly off, and it is cosmetic.** The Slice 6 review
section at `00-status.md:288` says the stylesheet answers "200 (1944 bytes)". The
UTF-8 display length is **1946 characters**; 1944 is the byte length of the file on
disk (`ls -la` reports 1946 including CRLF, and the served body decodes to 1946
characters). The served response is a 200 with a non-empty body either way, so the
fix is unaffected. Recorded as N-3, not fixed, because it is a one-digit cosmetic
difference in a supporting note and `00-status.md:288` is the only place it appears.

**Mutation.** Removing the `app.mount(...)` block, byte-anchored, count 1, reverted
md5-clean:

```
rc=1  FAILED test_the_page_links_a_stylesheet_the_app_actually_serves
1 failed, 2 passed
RESTORED CLEAN
```

`[verified]` F-1 is a real fix with a fail-capable test behind it.

---

## 4. F-2, verified, with a correction to the mutation claim

**The behaviour is real.** `[verified]` over `TestClient`:

```
POST /consents {"granted": false} -> 200, version 2
POST /callbacks/fictional_provider -> 200
  receipt: "refused"
  applied: false
  rejection_reason: "clinical_share consent is revoked at version 2"
  execution: "attempted"
```

**The mutation claim needs a correction, and this is the one substantive finding.**
The review section (`00-status.md:291`) and the review note section 11 both say the
mutation "neutralis[es] the revocation refusal in `_consent_rejection_reason`" and
that this turns the new callback test RED. Measured branch by branch:

| branch removed inside `_consent_rejection_reason` | F-2 API test alone |
|---|---|
| `if state != "granted":` return (`state.py:921-922`) | **RED** |
| `if version != stamped_version:` return (`state.py:923-927`) | **GREEN** |

`[verified]` A revocation is a *state* change, so the `state != "granted"` branch
fires first and short-circuits. The `version != stamped_version` branch is reachable
only when consent is still granted but the version moved, which is a different case
that the API test does not exercise.

**The version branch is not untested, it is tested elsewhere.** `[verified]`
`tests/test_state.py:1093 test_a_changed_consent_version_also_blocks` asserts the
exact string `"changed from 1 to 3"` in the rejection reason, which only the
`version != stamped_version` branch can produce. So both branches are load-bearing
and both have a fail-capable test; they are simply pinned at **different layers**:

| branch | pinned by |
|---|---|
| `state != "granted"` (revoked) | `test_api.py::TestCallbackRoute::test_a_success_arriving_after_revocation_is_refused_and_says_why` |
| `version != stamped_version` (moved while granted) | `test_state.py::TestConsentRevokeInFlight::test_a_changed_consent_version_also_blocks` |

**What this means.** The conclusion the record needs is true: the F-2 test IS
fail-capable, and the `refused` receipt IS pinned at the HTTP boundary. But the
record names a single mutation and a single test for a mechanism that is split
across two branches and two layers. The correction is worth keeping because the
record now describes a mutation that, as written, would not have turned *that* test
red.

**Note on method.** My first attempt to measure this produced a false GREEN for the
`state != "granted"` branch, caused by a stale `.pyc` in the working tree; the
branch-by-branch table above is from isolated single-test runs after clearing that.
I record it because a false GREEN on a mutation check is precisely the failure this
project has met before, and it argued for re-measuring rather than reading the
harness's word.

---

## 5. The honesty claim, re-attacked

Seven injections, all over the real ASGI app:

| attack | outcome |
|---|---|
| top-level `origin: "platform"` | 422 |
| `{"origin":"platform"}` inside `payload` | 200, body reads `local-sim` |
| `Origin: platform` HTTP header | 200, body reads `local-sim` |
| `X-Origin: platform` HTTP header | 200, body reads `local-sim` |
| `origin: "PLATFORM"` | 422 |
| `origin: "platform "` (trailing space) | 422 |
| `origin: null` | 422 |

`[verified]` No 200 body ever read `platform`. The marker comes from the
coordinator's wiring (`service.py:385, 900-907`), and a caller-stated origin is
compared, never trusted. This matches the first review's finding independently.

---

## 6. Record claims checked

| claim | source | verdict |
|---|---|---|
| 484 passed, 1 warning | `00-status.md:276` | **True** |
| split 100/141/57/103/60/23 = 484 | `00-status.md:276` | **True** |
| F-1 answers 200 | `00-status.md:288` | **True** (length off by 2, see N-3) |
| "harness line count re-stated ... below" | `00-status.md:276` | **False** (V-1) |
| "482 pass" | `PROGRESS.md:280` | **Stale** (V-3) |
| new files CRLF, zero lone LF | `00-status.md:276` | **True** (`test_coordinator.py` 420 CRLF, `tools.py` 272, `simulated_provider.py` 140; loneLF 0 each) |
| no added line carries U+2014 | `00-status.md:276` | **True** (0 added on every changed tracked file) |
| `slice6-live-check.md` 8 U+2014, quoted | review N-2 | **True**, and the file now discloses them in its section 6 |

---

## 7. Findings

### V-1. `00-status.md:276` claims a harness line count that is never given

`[verified]` The sentence reads "Per-file counts and the harness line count are
re-stated after the review fixes in the Slice 6 review section below." The review
section gives the per-file counts but **no line count for any file**, and the number
184 (`wc -l tests/_mutate_slice6.py`) appears nowhere in `00-status.md`. Smallest
fix: either drop "and the harness line count" from that sentence, or state it.

### V-2. The F-2 mutation anchor names the wrong branch

`[verified]` See section 4. Both branches are load-bearing, but they are pinned at
different layers: the `state != "granted"` branch by the new API test, the
`version != stamped_version` branch by `test_state.py:1093`. The record's single
mutation sentence names the second while crediting the first test. Smallest fix:
correct the sentence in `00-status.md:291` and review note section 11 to name both
branches and both tests.

### V-3. `PROGRESS.md` still says "482 pass"

`[verified]` `PROGRESS.md:280` records "482 pass" for Slice 6. The tree is at 484
after the two review fixes. `PROGRESS.md` is operational memory, not authority, so
this is not blocker-grade, but it contradicts the corrected record. Smallest fix:
append the +2 and the two fixes, or note the correction.

### N-3. The stylesheet length is stated as 1944; it is 1946 characters

`[verified]` Cosmetic. `00-status.md:288` only.

### V-4. The mutation harness is not self-verifying: M11 was skipped and the control FAILED

`[verified]` The harness was re-run in full on the tree it ships with. Its own
output, verbatim in the parts that matter:

```
[SKIP] M11 the idempotency triple stops binding the key: anchor not found in state.py
...
[CONTROL] restored tree:
    1 failed, 64 passed, 1 warning in 97.15s (0:01:37)
    *** CONTROL FAILED: a file was not restored ***

=== result ===
  PROBLEM: M11 the idempotency triple stops binding the key
  PROBLEM: control
```

**Two distinct defects, and the second is the serious one.**

1. **M11 never ran.** The harness reported `anchor not found` and skipped it, so the
   figure the harness produced was **10 of 11 mutations seen RED** against the record's
   claim of 11 of 11. The harness *correctly detected and flagged* this rather than
   silently passing, which is to its credit, but no one acted on the flag. (After the
   repair below, M11 runs and the true figure is 11 of 11.)

2. **The control failed, and the tree was left dirty.** After the run,
   `src/carerelay/state.py` carried a live mutation (`if False:  # mutated`) and the
   file's md5 was `202130f5c14fce3091c5fbe476355ea8` against the original
   `1dcc54ea39ae13a24f3c595e90c40449`. I reverted it by hand and the file is back to
   the original md5, CRLF 1885, lone LF 0.

**Root cause, found and fixed.** The harness used `Path.read_text()` and
`Path.write_text()`. On this interpreter `read_text()` applies universal-newline
translation, so a CRLF file comes back as LF in memory, and `write_text()` then writes
a **pure-LF** file over the CRLF original: every mutation silently converted its
target to LF, and the restore was never byte-exact even when it ran. Separately,
every `state.py` anchor in the harness was written with `\n`, so against a CRLF file
it could not match. That is why M11 was skipped, and why the LF conversion (the
write-back) was the actual "not restored" event the control caught.

**Fixed, and re-run.** `tests/_mutate_slice6.py` now: reads and writes in **binary**,
normalises its anchors to CRLF in one helper, **fails hard when an anchor is missing
or non-unique** (a skipped mutation can no longer pass silently), verifies the restore
against a pre-mutation md5 and aborts on mismatch, and checks every mutated file
against its pre-run bytes in the control. All eleven anchors were confirmed to match
uniquely before the run, and the run's result is at the end of this note.

**Why this matters more than the count.** The harness is the evidence source for
every "seen RED, restored clean" claim in the Slice 6 record. Before the fix, running
it left the tree dirty and silently dropped a mutation. A reviewer who ran it and then
ran the suite would see 484 passed and conclude all was well, because **the skipped
M11 mutation does not break any test in the full suite** (its test is the
`IdempotencyKeyCollision` case, which the mutated branch disables only for the exact
triple that never occurs in the slice's own flows). The failure was invisible from the
suite alone.

**Status: fixed in the tree, and carried as a note anyway.** The harness was repaired
on 3 October 2026 at the user's instruction, and the repaired version was re-run in
full. Because a harness that silently converted CRLF files to LF is exactly the class
of defect this project keeps re-finding, V-4 stays on the carried list in
`tasks/todo.md` until the Slice 6 ship, so the fix is reviewed alongside the slice
rather than trusted on sight.

### Re-run of the repaired harness, 3 October 2026

`[verified]` All eleven anchors were confirmed to match uniquely before the run. The
run, verbatim:

```
[BASE] state.py: md5=1dcc54ea39ae13a24f3c595e90c40449 CRLF=1885 loneLF=0
...
[RUN ] M11 the idempotency triple stops binding the key
    1 failed, 6 passed in 20.96s
...
[CONTROL] restored tree:
    65 passed, 1 warning in 19.99s

=== result ===
  every mutation was seen RED; every file restored byte-exact; tree green
```

`[verified]` **11 of 11 seen RED**, M11 included (it was skipped before), and the
control is green. After the run, the four mutated files match their pre-run md5
exactly and are still CRLF with zero lone LF:

| file | md5 | endings |
|---|---|---|
| `state.py` | `1dcc54ea39ae13a24f3c595e90c40449` | CRLF 1885, loneLF 0 |
| `tools.py` | `6a890955b371f2d2820614a4dcbe6e1b` | CRLF 272, loneLF 0 |
| `service.py` | `528ad9dec2699373baf12e209e852d04` | CRLF 1089, loneLF 0 |
| `simulated_provider.py` | `5ed19e0fda796b53bec7de6edb681f4d` | CRLF 140, loneLF 0 |

The repaired harness is also far slower for M13 (563 s against 250 s) because it now
runs the real `test_state.py` selection rather than short-circuiting on a skipped
mutation. That is the cost of the guard being real.

---

## 8. What I could not verify, and why

- **A `uvicorn` run.** I drove the real ASGI app through `TestClient`. The status
  codes and bodies are the real ones; this is not literally a `curl` against a bound
  socket. `[unknown as a curl run]`
- **M6 to M16 individually.** The harness ran in full (result recorded in
  `00-status.md`); I verified its conclusion from its own output rather than
  re-deriving each anchor by hand. `[verified for the conclusion; inferred per anchor]`
- **Anything needing ADP, credentials or a network call.** Not attempted.
- **The two `tools/_fix_*.py` scripts' effect.** They write to the tree, so I read
  them and confirmed they target anchors that exist, but did not run them.

---

## 9. Tree state, and one incident to record honestly

`[verified]` After the whole pass, `git status --short --untracked-files=all` is
identical to the pre-experiment listing, plus this note. Suite 484 passed. No commit,
no push, no gate document touched.

**One incident.** While measuring V-2 I applied a compound mutation that removed two
branches at once and **the restore did not run**, because my helper's backup had
already been overwritten by an earlier mutation in the same process. `state.py` was
left short one branch and the suite went to `1 failed, 483 passed`
(`test_a_changed_consent_version_also_blocks`). I detected it from the md5 change,
recovered the exact block from `git diff`, and restored `state.py` to its original
md5 `1dcc54ea39ae13a24f3c595e90c40449` (CRLF 1885, lone LF 0). The suite returned to
484.

**A second, larger incident, and it is V-4.** Running the project's own harness left
`state.py` carrying a live mutation until I reverted it by hand. That is the same
failure mode as my own, in the shipped tool, and it is why V-4 is written as a finding
rather than a note.

The lesson is the one the review skill already states and it is worth restating: **a
backup taken inside the same process that later mutates the file is not a backup.** A
restore must verify the md5 *before* it is trusted, and a `finally` that can be
skipped is not a restore. This is recorded rather than hidden because this repository
has three logged git incidents and the near-miss count matters.
