# Slice 2 adversarial review

**Kind:** supporting note, not a gate document. Authoritative for nothing.
**Subject:** the Slice 2 implementation on branch `slice-2-domain-core`.
**Written:** 30 September 2026 by a reviewer with no prior context, from the
review prompt at `docs/plans/urgent-advice-accessibility/04-slices.md` (Slice 2)
and the brief handed over in chat.
**Remediation:** the defects marked **fixed** were repaired the same day, at the
user's instruction, before Slice 3 began. See the last section for the diff.

Labels: **[verified]** ran it or read the line, **[inferred]**, **[hypothesis]**,
**[unknown]**.

---

## 1. Verdict

**The exit contract is met, with named caveats.** All five required tests are
fail-capable, the boundary check is enforcing and was reproduced red then green
on the real tree, and every count claim in `00-status.md` checked out.

The caveats were that C7's guarantee was weaker than claimed (the scanner was
evadable in five ways) and that `patient_lines` could print a deadline that was
not the disposition's deadline. Both are now fixed.

## 2. What was run

| Check | Result |
|---|---|
| `pytest tests -o addopts="" -q` | **109 passed, 1 warning** before the fixes **[verified]** |
| Split | 82 domain, 16 boundaries, 11 api, summing to 109 **[verified]** |
| Boundary check seen red | `import socket` inserted at `rules.py` line 40 produced `rules.py:40: imports forbidden module 'socket'`; removed; re-run green **[verified]** |
| Revert integrity | `rules.py` md5 `2f4a5ed525e3049ebe9545b4116d331b` identical before and after every experiment; `git status --short --untracked-files=all` identical throughout **[verified]** |
| Line counts claimed | 387 / 587 / 1211 / 416, all exact **[verified]** |
| Mutation checks on the fixes | 5 of 5 caught by their paired test **[verified]** |

The `-o addopts=""` flag is required: the project's `addopts = "-q"` plus a
second `-q` suppresses the summary line entirely.

## 3. Findings

| # | Severity | Location | What was wrong | Why it mattered | Status |
|---|---|---|---|---|---|
| F1 | BLOCKER | `rules.py:467` (used at `:475`, `:493`) | `deadline_display` was copied verbatim from `PolicyText`, decoupled from `disposition.clinical_deadline_utc` | Two sources of truth for the one fact the product exists to preserve. A reassessed disposition (deadline 1 Oct 18:00 SGT) rendered line 3 as `Before 6:00 PM on 30 September.`, a false statement to the patient, and it broke approved copy rule 5 (`02-architecture.md` section 7) | **fixed** |
| F2 | BLOCKER | `00-status.md:39` | Claimed "New files are CRLF, matching every tracked file (`core.autocrlf=true`). No line-ending damage" | False: all five new files were pure LF while every tracked file was CRLF. The review brief makes a false `00-status.md` claim blocker-grade | **fixed** |
| F3 | SHOULD FIX | `test_boundaries.py:158-168`, `:192-201`, `:43-100` | `_dotted_name` returned `""` for any call whose `func` was not a `Name`/`Attribute` chain, and the scanner skipped it. `builtins` and `sys` were absent from `FORBIDDEN_MODULES` | C7 is "provably pure", but the check was evadable in five ways. This was the author's own number-one risk, confirmed | **fixed** |
| F4 | SHOULD FIX | `rules.py:415-416` + `:479-483` | `closed_with_evidence` is reachable two ways, real evidence and a recorded human acceptance with `care_evidenced=False`. `patient_lines` raises for both | The acceptance route is a normal product state (`POST /acceptances`, `02-architecture.md` section 3.1) with no patient rendering anywhere. The declared Slice 9 deferral silently covered two materially different states | **open, needs a decision** |
| F5 | SHOULD FIX | `rules.py:429` | `simulated = not care_evidenced` | Conflates "this episode is a simulation" with "care is not evidenced". One field, two meanings | **open, needs a decision** |
| F6 | SHOULD FIX | `rules.py:426` | `action_owner_id` ignores `escalation_id` and `human_acceptance_id` | I4 names three possible actors including "an explicit human service". The projection cannot express that owner | **open, needs a decision** |
| F7 | SHOULD FIX | `rules.py:336-341` | The `raise` fired only on the lowest-`seq` row; the loop returned immediately | `[acknowledged(1), not_started(2)]` returned `acknowledged` and the corrupt row was silently ignored, contradicting the docstring. Also `derive_closure` never calls `project_attempt`, so the fail-loud crash lands on the Slice 3 read path, not in Slice 2 | **fixed** |
| F8 | SHOULD FIX | `test_boundaries.py:21-22`, `:284-285` | Docstrings claimed "Every detector below is paired with the input it must catch" and "One detector per forbidden form" | Verified false: deleting `"eval"` from `FORBIDDEN_CALLS` and `".today"` from `FORBIDDEN_CALL_SUFFIXES` left the suite green at 109. 12 of 13 call entries and 6 of 7 suffixes had no paired input | **fixed** |
| F9 | SHOULD FIX | `test_domain.py` corpus | Every one of the six K1 corpus entries is a literal key in one of the three resolution tables | The corpus proved dict lookup worked, not that the comparator handles language. Correct restatements outside the table ("go to the polyclinic", "6pm today", "today before 6") all degraded to `uncertain` | **fixed** |
| F10 | NIT | `00-status.md:14`, `tasks/todo.md` | "106 tests pass" | Stale; the verified figure was 109, and the same file said 109 at `:32` | **fixed** |
| F11 | NIT | `00-status.md:74` | "One em dash is used" | The file contains zero em dashes; `rules.py` writes it as the escape `\u2014`. The disclosure overstated a non-problem, so AGENTS.md section 6 was not in fact breached | **fixed** |
| F12 | NIT | `test_domain.py:817-821` | `test_origin_is_carried_on_every_transition` asserted enum tautologies and never exercised the projection | The name implied coverage of a behaviour `project_attempt` does not have | **fixed** |
| F13 | NIT | `rules.py:399-401` | An `expiry_event_id` with `disposition=None` produced `expired_unresolved` with `action_owner_id=None` | I4 requires exactly one party to act at every moment; this state named nobody | **fixed** |

## 4. The four judgement calls

1. **Closure precedence, expiry outranks a recorded human acceptance: AGREE**, with a required amendment. `03-planback-closure-contract.md` section 2.2 defines `closed_with_evidence` as "Evidence >= documented, **or** an explicit human acceptance is recorded" and `expired_unresolved` as "Deadline passed with no evidence". Both rows fire on acceptance plus past-deadline plus no evidence, and the document states no order, so the author's "unsettled" claim was correct. Expiry wins on I2, and decisively because `patient_lines` raises for `closed_with_evidence`: the other order would make the state unrenderable on the patient read path. **Section 2.2 should be amended to state the order explicitly, because as written the two rows overlap.**
2. **Line 2 composed by owner: AGREE.** Sections 2.5 and 7 both give "You or *[named person]* must act now.", which with a patient owner yields "You or you must act now." The divergence is carried forward and flagged. The documents still need the fix at the next Gate 1 touch.
3. **Raising for `closed_with_evidence`: AGREE on the raise, DISAGREE that it is sufficient.** See F4. The deferral covers two different states and one has no rendering at all.
4. **Execution-axis `expired`: AGREE.** Section 2.2 lists `expired` on the axis, so it was contracted vocabulary and leaving it unwired made it unreachable. Never overwriting a recorded terminal outcome is the correct reading of "terminal states are absorbing" (`02-architecture.md` section 4.1). Note `EXPIRED` is deliberately not in `TERMINAL_TRANSITIONS`, so it is reachable only through `derive_closure`; consistent, but the two functions disagree on what a transition row may contain.

## 5. Boundary-check evasion

Five snippets passed `test_domain_import_boundary` unchanged **[verified]**. All
are now caught, and the tests that catch them are `TestScannerResistsDynamicCalls`
plus the `builtins` and `sys` entries in `FORBIDDEN_MODULES`.

```python
__builtins__["open"]("/etc/passwd")                        # filesystem, zero imports
import builtins; builtins.open("/etc/passwd")              # filesystem
import builtins; builtins.__import__("socket")             # network
import builtins; builtins.__import__("sqlite3").connect(x) # database
from datetime import datetime; getattr(datetime, "now")()  # wall clock
```

Root cause: `_dotted_name` returned `""` for any call whose `func` was a `Call`,
a `Subscript` or a `Lambda`, and the scanner did `if not dotted: continue`. The
fix checks the shape of `func` directly, so a dynamically produced call target is
refused rather than skipped. A method call on a literal (`" ".join(...)`) has an
`Attribute` for its `func` and is not affected; that boundary has its own test.

**Q4 is a pass, not a gap.** `DOMAIN_ROOT.rglob("*.py")` covers a new top-level
file and a new subpackage. Verified in a temporary copy: both were flagged and
the superset assertion still held. **[verified]**

## 6. Test-quality findings

- **Mutations.** The four defective comparators target four distinct faults, and
  the three closure guards are separately disabled. **[verified]** Removing the
  `uncertain_fields` precedence from `compare_plan` fails exactly two tests.
- **Redundant mutation.** `trust_simulated_evidence=True` disables the `simulated`
  and the `source_ref` halves of the D11 guard in one go, so
  `test_a_simulated_documented_row_cannot_close_care` and
  `test_an_unsourced_documented_row_cannot_close_care` share one mutation. The
  `source_ref` half has no independent mutation. **Not fixed**: it needs a second
  named flag, and the finding is recorded rather than papered over.
- **Same guard twice.** `test_an_empty_route_id_is_refused` and
  `test_a_hallucinated_route_id_is_refused` hit the same branch;
  `test_detects_a_forbidden_module_import` and `..._nested_in_a_function` exercise
  the same `ast.Import` branch; `test_every_stop_decision_returns_no_disposition`
  re-covers three already-separate stop tests. **Not fixed**: each is a distinct
  input, so they are redundant for failure-mode purposes but not wrong.
- **Unverified detector entries.** Fixed by three parametrised tests that iterate
  the lists themselves, so a new entry arrives with its own input.
- **Asserts current behaviour, not the invariant.** `test_an_escalation_before_the_deadline_is_escalated_to_human`
  asserted `action_owner_id == NEXT_OWNER_ID`, enshrining F6. Left in place,
  because F6 is a decision, not a defect.
- **Synthetic surface.** `TestPatientSurfaceHasNoTimerAndNoDwell._surface()` builds
  the "patient surface" inside the test, so the dwell and timer absence is proven
  against test code, not production serialisation. There is no production
  serialiser in Slice 2, so this is an acceptable scaffold, but it is not the D11
  evidence it reads as.

## 7. False claims in `00-status.md`

Two, both now corrected.

1. `:39` claimed the new files were CRLF and matched every tracked file. They were
   pure LF. Fixed by normalising the five new files to CRLF, which is what the
   author intended and what every tracked file uses.
2. `:14` said "106 tests pass". The verified count was 109, and `:32` in the same
   file said 109. The stale figure was also mirrored into `tasks/todo.md`.

One imprecision: `:74` said "One em dash is used". The file contains none.

Everything else checked out: the 82/16/11 split, the exact `rules.py:40` failure
message, the `grep socket|TEMPORARY` claim, the absence of `DisplayZone`, and the
wiring of `ExecutionStatus.EXPIRED`.

**On the two disclosures.** The em-dash call was correct: `rules.py` contains no
em dash at all, so approved copy was reproduced without breaching AGENTS.md
section 6. The branch call was correct: AGENTS.md section 6 says "Never begin
slice work on `main`" and the branch was created before any edit.

## 8. What could not be verified

- **Runtime behaviour.** No uvicorn, no route, no HTTP. Every rendering finding is
  unit-level; no patient screen was observed.
- **Whether `patient_lines` is ever called with a stale `PolicyText`.** That is
  Slice 4 and Slice 9 wiring, which does not exist. F1's fix makes the coupling
  explicit and fail-closed rather than relying on the caller.
- **Whether `project_attempt`'s raise surfaces as a 500.** `derive_closure` does
  not call it, so the read path is not established yet.
- **WorkBuddy access, clinical content, the Option C source.** Untouched by
  instruction.

## 9. What was deliberately not changed

Five findings need a product, clinical or documentary decision rather than a code
fix. They are open.

**Where each is decided (standing instruction, user, 30 September 2026).** None of
these is decided now. Each is decided (or put to the user as a question) **at the
slice where it first becomes live**, and the decision is recorded in `00-status.md`
in that slice's section. A later slice must not silently implement one of these
while building an earlier one.

| # | Open finding | Decided at |
|---|---|---|
| F4 | Rendering `closed_with_evidence` needs approved patient wording, and AGENTS.md forbids authoring clinical strings. Slice 9 must render it, and must render the acceptance case (`care_evidenced = False`) separately from the evidence case, because they are not the same fact | **Slice 9** |
| F5 | Whether `simulated` means "this episode is a simulation" or "this closure claim is not evidenced" is a product decision. The code implements the D11 rule as written, so it was left alone | **Slice 6**, visible in the ledger at **Slice 11** |
| F6 | Whether an escalated episode's owner is still the patient or becomes the human service is a product decision about I4 | **Slice 5**, re-checked at **Slice 9** |
| §2.2 | The `closed_with_evidence` and `expired_unresolved` rows of `03-planback-closure-contract.md` section 2.2 overlap on acceptance plus past-deadline, and the document states no order. The implementation puts expiry first. This is the documentary form of the F4 decision | **Slice 9** |
| `source_ref` | The D11 guard's `simulated` and `source_ref` halves share one mutation flag, so the `source_ref` half has no independent proof. One extra named flag closes it | **Slice 3** |

## 10. Diff applied by the remediation

| File | Change |
|---|---|
| `src/carerelay/domain/models.py` | `PolicyText.deadline_display: str` becomes `deadline_display_by_version: Mapping[int, str]`, keyed by disposition version |
| `src/carerelay/domain/rules.py` | `patient_lines` looks the deadline wording up by `disposition.version` and raises `MissingDisplayText` for an unworded version; `project_attempt` validates every row, not only the winning one; `derive_closure` refuses an expiry event with no disposition |
| `tests/test_boundaries.py` | `builtins` and `sys` added to `FORBIDDEN_MODULES`; dynamically produced call targets refused; `TestEveryDetectorIsPairedWithItsInput` and `TestScannerResistsDynamicCalls` added |
| `tests/test_domain.py` | Independent natural-phrasing corpus and unresolvable-phrase set added; the origin test replaced with an origin-independence test; three new closure and rendering tests |
| `docs/plans/urgent-advice-accessibility/00-status.md` | Slice 2 entry corrected and the review recorded |
| `tasks/todo.md` | Stale test count corrected |

**Suite after remediation: 240 passed, 1 warning** (88 domain, 141 boundaries, 11
api). Five mutation checks confirmed the new tests are fail-capable **[verified]**.
No commit, branch or push was made **during the review itself**, and no gate was
reopened. The work was committed and pushed afterwards, the same day, on the user's
explicit instruction; the commit range and the resulting branch state are recorded in
`00-status.md`.
