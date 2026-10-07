# Slice 8 adversarial review: the fixed card and the pre-registration

**Supporting note. Authoritative for nothing.** Independent adversarial review of the
Slice 8 work on `slice-8-fixed-card`, run 7 October 2026. The slice record is
`docs/plans/urgent-advice-accessibility/00-status.md` section "Slice 8"; the slice
plan is `04-slices.md`.

Reviewed at the user's "go" of 7 October 2026, with no brief beyond that word, so
this review follows the default contract: read-only apart from temporary mutations
that were reverted and md5-verified, no server started, no install, no credential,
no commit, no branch.

## Verdict

**The slice is sound as an artefact and the harness is honest, but one BLOCKER sits
in the scoring code, and the "stale mirror" the record carries is far wider than the
record says.**

The card is a genuine external artefact, the parity guards do pin the four lines,
the notice, the action text, the deadline, the route names and the permitted-route
set, the harness re-runs clean at 15 of 15 RED with a byte-exact restore, and every
count in the Slice 8 record that I re-derived is correct. What is wrong is (a) the
study's own scorer contradicts the pre-registration it claims to implement and the
product's own alias tables, and (b) the record treats a drift across nine live
documents as one stale sentence.

## Baseline, re-derived

| Claim in `00-status.md` | Re-derived | Holds |
|---|---|---|
| `tests/` = 716 passed, 0 skipped, 1 warning | 716 passed, 0 skipped, 1 warning, 21.4 s | yes |
| pre-slice baseline 614 passed, 0 skipped | 614 passed, 0 skipped (`--ignore=tests/test_study.py`) | yes |
| `tests/test_study.py` = 102 tests | 102 (6 + 5 + 2 + 59 + 1 + 13 + 7 + 9) | yes |
| harness 15 of 15 RED, 0 SURVIVED, 0 NOT PROVEN | re-run: 15 of 15, 0, 0 | yes |
| every file restored byte-exact | md5 identical on all three targets, before and after | yes |
| the card carries exactly one U+2014, inside the notice | 1 in `study/fixed-card.html`, 0 in the other three | yes |
| the four new files match the repository's line convention | all four CRLF, loneLF 0 | yes |
| `02-architecture.md` section 9 calls the comparator bilingual | true, but it is not the only place | understated, see S3 |

## Findings

| # | Class | Where | What is wrong | Why it matters | Smallest fix |
|---|---|---|---|---|---|
| **B1** | **BLOCKER** | `tests/test_study.py:183-199` against `study/protocol.md:193-206` and `src/carerelay/demo/fixture.py:152-183` | The study scorer contradicts both the frozen pre-registration and the product it measures. All seven `ACTION_ALIASES` the application resolves to the keyed action score `False`; four of the six deadline forms the application resolves to 18:00 score `False`. And `score_action_recall` / `score_deadline_recall` return `False` for an unclassifiable response, where protocol section 11 requires the second scorer to resolve it and where the sibling `score_false_completion` correctly raises | The cut rule reads "both fields correct" counts. Condition A participants talk to the alias-accepting app and condition B participants read the card verbatim, so scoring a correct paraphrase as incorrect deflates A specifically and can move the kill decision. Protocol section 17 item 3 freezes section 11, so the code and the frozen rules currently disagree at the moment of freezing | Build both accepted lists from the fixture's own tables (`ACTION_ALIASES`, `DEADLINE_FORMS`) rather than a hand-written list, or record the narrower list as a deliberate deviation with a reason; and give the two recall scorers the same refuse-don't-guess behaviour as `score_false_completion`. Add one test per behaviour |
| **S1** | SHOULD FIX | `tests/test_study.py:417-419`, `:52-54`; `study/fixed-card.html:18-20` | The heading parity guard is one-sided. It compares the card's `<h1>` to a constant declared in the same test file, not to the application. Verified: changing `api.py:516` to "Your Care Plan" leaves `tests/test_study.py` at 102 passed, while changing the card's own `<h1>` fails it. The guard's name, the test docstring and the card's comment all claim the application link that is not tested | The card's comment is the maintenance contract for the one file whose whole purpose is parity, and it says "the parity test fails if any of them drifts". For the heading that is false. Every other parity claim routes through `fixture.*`; this one is the exception | Assert the heading against the application's own literal (extract it from `api.py`, or compare against the rendered screen) so a rename on either side fails |
| **S2** | SHOULD FIX | `tests/test_study.py:59-87`, `:372-381` | The "loads nothing, executes nothing" guard does not cover `javascript:` URIs or inline `on*` handlers. Verified GREEN for both `<a href="javascript:window.close()">` and `<img alt="x" onerror="alert(1)">`. The address counter at `:379` matches only `https?://`, so a `javascript:` link is invisible to it as well | The class docstring at `:352-356` claims a card that "runs script, frames content or embeds an object" is caught. The study's validity rests on the comparator provably not being the application, so a guard narrower than its claim is the wrong kind of green | Add `r"javascript\s*:"` and `r"\bon[a-z]+\s*="` to `RESOURCE_AND_WIRING_PATTERNS`, with one regression test each, and confirm each fails when the pattern is removed |
| **S3** | SHOULD FIX | `00-status.md:281` against nine live documents | The carried "stale mirror" names one sentence in `02-architecture.md` section 9. The comparator is described as bilingual in at least: `02-architecture.md:32` (**the D6 row itself**), `02-architecture.md:292`, `AGENTS.md:143`, `AGENTS.md:480`, `00-status.md:849`, `00-status.md:925`, `PLAN.md:425`, `03-program-design.md:290`, `03-planback-closure-contract.md:233`, `research-workarounds.md:13`, `clinical-review-blocker.md:20`, `PROGRESS.md:55` | `AGENTS.md` section 5 makes a stale mirror a blocking finding, and `02-architecture.md:32` is the decision line the slice executes against, not prose. Worse, `clinical-review-blocker.md:20` builds half of its blocker rationale on the bilingual premise, so a reader working from that note reaches a wrong conclusion about what still blocks Gate B | Correct the D6 row and section 9 at the next Gate 2 touch (both are inside an approved gate document, so this reopens Gate 2), and add the other seven to that same queue now, so they are not rediscovered at Slice 9 |
| **N1** | NIT | `tests/test_study.py:453-457` | Two guards have byte-identical bodies (`test_the_card_carries_no_symptom_urgency_or_disposition_marker` and `test_the_card_carries_no_numeric_clinical_threshold`); the AST dumps are equal. The second name promises a threshold-specific check that does not exist | The 102 count carries one non-discriminating test, and a marker-only leak and a threshold-only leak are indistinguishable by which test fails | Give the threshold guard its own assertion (scan only the threshold pattern), or fold the two into one and state 101 |
| **N2** | NIT | `tests/_mutate_slice8.py:222-237`, `:320-325` | The `ran` counter counts the padding pytest pads the progress line with. For a single-test selection the progress string is one dot plus 72 spaces, so `ran` reports **73**. Consequently `elif ran == 0 or failed == 0` can never fire on `ran` | The docstring at `:20-22` states the count "comes off the progress characters". It does, and then it counts the spaces. The RED verdict is unaffected, because it keys on `failed > 0` and the exit code, and `failed` is computed correctly; the pre-flight collect check at `:269-285` independently covers the unresolved-selector case | Strip the padding before counting (`line.split("[",1)[0].rstrip()`), or count only characters in `.FExX` |
| **N3** | NIT | `tests/test_study.py:71-87` | CSS `url()` is not in the resource pattern list. Verified GREEN for `background-image: url(//evil.example/pixel.png)`. The absolute `https://` form **is** caught, by the address counter, verified RED | The "loads no resource" guard is narrower than its name; only the protocol-relative form escapes | Add `r"url\s*\("` to `RESOURCE_AND_WIRING_PATTERNS`, or extend the address counter to protocol-relative forms |
| **N4** | NIT | `00-status.md:280` | Cites `study/protocol.md` section 15 for "the three scoring functions". Section 15 is the reporting rules; the scoring functions implement sections 8, 10 and 11. `render_outcome_report` and `hcd_claim_supported` are the ones section 15 covers | The record is a claim document and the citation sends a reader to the wrong section when checking the scorer against the protocol, which is exactly what B1 requires | Name sections 8, 10 and 11 for the three scoring functions and section 15 for the two reporting functions. The comment at `tests/test_study.py:173-176` already gets this right |
| **N5** | NIT | `study/fixed-card.html:12-13` | The comment claims "no mention of the application anywhere", and the comment block itself mentions it twice at `:18-19`. True of the participant-visible surface, which is what the guard checks; literally false of the file | The comment is the maintenance contract, and this project treats a false claim in a comment as a defect rather than as shorthand | Say "anywhere a participant can see" |

## Judgement calls

| Call | Verdict | Document relied on |
|---|---|---|
| The card is English-only, while D6 and eight other live documents say the comparator is bilingual | **Agree with Slice 8.** The backtrack table at `00-status.md:782-786` already reads "Content-neutral instruction task, same shape, **no clinical content**" in its *After* column, and `AGENTS.md` section 4 keeps English as the auditable reference. The card is the authorised artefact and the documents are stale, which is S3 and not a defect in the slice | `00-status.md:782-786`; `AGENTS.md` section 4 |
| The card's wording is hand-written rather than generated from `demo/fixture.py` | **Agree.** A generated card would agree with the fixture by construction and could not be seen to drift, which is the point of the duplication | `tests/test_study.py:19-23` |
| The carried item that "Slice 9 must lift the small-sample reporting and scoring rules into the response path" | **Agree, and B1 makes it urgent rather than tidy.** What Slice 9 would lift currently disagrees with the protocol it claims to implement | `00-status.md:280` |
| Whether the cut rule's "lower median burden" comparison is well formed | **Cannot determine.** It depends on the raw outcome sheet, which is blank by design, and on how ties are treated, which no document states | `study/protocol.md:231-247` |
| Whether a second scorer exists | **Unknown.** Protocol section 11 and section 16 require one and none is named, recruited or budgeted anywhere I read | `study/protocol.md:193-206`, `:283-291` |
| The one U+2014 on the card is imported, not authored | **Agree.** It sits inside `fixture.FIXTURE_LABEL`, reproduced verbatim for parity, and the disclosure is mechanical rather than asserted | `study/fixed-card.html`; `tests/test_study.py:482-493` |

## What got past the guards

Four injections, each applied alone to an md5-verified backup, each reverted and
re-verified, all against the whole of `tests/test_study.py`:

| Injection | Result | Finding |
|---|---|---|
| `api.py` heading changed to "Your Care Plan" | **GREEN, 102 passed** | S1 |
| `<a href="javascript:window.close()">` added to the card | **GREEN, 102 passed** | S2 |
| `<img alt="x" onerror="alert(1)">` added to the card | **GREEN, 102 passed** | S2 |
| `background-image: url(//evil.example/pixel.png)` added to the card's `<style>` | **GREEN, 102 passed** | N3 |
| Control: the card's own `<h1>` changed | **RED**, `test_the_card_heading_is_the_heading_the_application_renders` | proves S1 is one-sided rather than absent |
| Control: `background-image: url(https://evil.example/pixel.png)` | **RED**, `test_the_only_address_on_the_card_cannot_resolve` | proves N3 is the protocol-relative form only |

## Test quality

- **15 of 102 tests are mutation-covered** by `tests/_mutate_slice8.py`, which is
  14.7 percent. The remaining 87 are not, and I spot-checked the ones that carry a
  claim rather than proving all of them. Treat "15 of 15 RED" as evidence about 15
  mechanisms, not about the file.
- **C7 and C8 are one guard tested twice.** Both mutations land on the same
  assertion, so each fails both tests. The harness's stated convention that each
  mutation "requires **its own** guard to fail" is not literally true for that pair.
  This is N1 seen from the harness side, and it does not make either RED false.
- **`test_each_offered_route_is_named_with_its_policy_display_text`
  (`tests/test_study.py:437-441`) is a containment check, not equality, and is not
  mutation-covered.** A route display name appearing anywhere on the card satisfies
  it. The route-id check beside it is genuine set equality and is proven by C6.
- **The pair `test_the_control_the_card_is_not_empty` and the empty-shell control in
  `_card_shell` are good practice** and are the reason the absence assertions mean
  something. Credit where it is due: this is the control the project has had to add
  after the fact on earlier slices.
- **No `skipif` anywhere in the file**, so nothing in this slice can be silently
  skipped, and the 0-skip count is real rather than a quiet omission.

## False claims in `00-status.md`

Two, both understatements rather than inventions:

- `:281` says the stale bilingual mirror is `02-architecture.md` section 9. It is
  nine documents and includes the D6 decision row. **S3.**
- `:280` cites section 15 for the three scoring functions. **N4.**

Everything else I checked holds: the counts, the per-file arithmetic, the mutation
result, the em dash disclosure, the line endings and the "0 skipped means the engine
was reached" reasoning.

## What I could not verify

- **No live server was started**, per the review contract, so the card was never
  rendered in a browser. The "printable, no timer, no countdown, no animation, no
  auto-advance" claims at `study/fixed-card.html:30-31` and `:102-106` are read from
  source and **not observed**. The print media query and the `@media print` block are
  therefore **[hypothesis]** about the rendered result.
- **The Postgres engine is inferred, not confirmed.** 0 skipped is consistent with
  the engine being reachable and is the same evidence the record uses, but I did not
  open a connection or check the container myself.
- **One timing observation I did not chase:** the full suite took 21.4 s and the
  `--ignore` subset took 59.5 s, so the smaller selection ran about three times
  slower. That is the opposite of warm-up and may be machine load, or may be
  per-child cost in the Postgres-gated module fixture. It is not evidence of a
  defect, but a reviewer reporting both counts should say what they saw.
- **Whether Slice 9 consumes these functions unchanged.** The record says it must
  lift them; Slice 9 does not exist yet, so B1 is latent today and live the moment
  Slice 9 wires the scorer.
- **Whether a second scorer or a facilitator exists**, per the judgement-call table.

## What I tried to break and could not

- **The harness.** Re-ran it end to end: 15 of 15 RED, 0 SURVIVED, 0 NOT PROVEN, all
  three targets md5-identical before and after, verified with a retry loop for the
  OneDrive read-after-write trap. It does **not** carry the Slice 6 defect: it uses
  `read_bytes` / `write_bytes`, conforms every anchor to the target's own newline
  convention, asserts anchor uniqueness before writing, purges stale bytecode, and
  fails hard on an unresolved selector instead of skipping. Its own control passes.
- **The line-ending trap.** All four new files are CRLF with loneLF 0.
- **The em dash rule.** Zero em dashes on the added lines of all five modified
  tracked files, computed with `difflib` against `HEAD` rather than read off
  `git diff`. The card carries exactly one, inside the imported notice, as disclosed.
- **The bare-`S` rule.** Zero occurrences on added lines.
- **The route-set guard.** Genuine set equality rather than containment, and C6
  proves it fails on an extra route.
- **The design-declaration guard.** P1 proves it now reads the decision rather than
  the word, which is the defect the slice found in its own guard and fixed.
- **The empty-file class.** Both the card and the shell controls are present and
  fail-capable.

## Tree state

Left exactly as found, apart from this note. Verified after every experiment:
`git status --porcelain --untracked-files=all` lists the same five modified files and
the same four untracked paths, `tests/__pycache__` does not exist, and no probe
script was written inside the repository. Probe backups live outside the repo under
`%TEMP%/slice8-review-bak/`.
