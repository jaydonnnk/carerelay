# Patient wording pass: Slices 1 to 7

**Run 2 October 2026. Verdict: APPLIED, GATES REOPENED AND RE-APPROVED, CHECK CLOSED.**

**Outcome.** The wording pass was applied, which reopened Gate 1 and Gate 2. The user
answered the standing question with **"I have read and i re approve both gates"**, so
both gates are **APPROVED** again and the re-opened Slice 5 Check is **COMPLETE**.
**Slice 5 closes as of 2 October 2026.** Nothing is committed and nothing is pushed.

The user asked for the patient-facing wording to "sound like a human, and not a
robotic agent", and initially asked for the tone to be sourced from hospitality
sources. This record states what was done, what was refused and why, and what the
user re-approved. It follows `AGENTS.md` section 6 on mutation testing, em dashes and
line endings, and section 5 on gate reopening.

---

## 1. What the user asked for

> "How about help me to change the wordings from slice 1 to slice 7. Make the tone
> and the wording sound like a human, and not a robotic agent. Try to source tone of
> voice from credible hospitality sources if possible and change accordingly."

Two parts, and only one of them survived review.

---

## 2. The hospitality sourcing was refused, and this is why

**A hospitality brand guide is not a clinical authority, so it cannot close a gap
the clinical sources already left.**

| Candidate class | Why it does not work |
|---|---|
| A hotel or service brand style guide | Weaker than the sources that already failed. MOH clause 11 and HealthHub clause 12.1 both require prior written permission, and the UK Open Government Licence route fails Singapore applicability (`03-program-design.md` section 6.2). A style guide has no clinical standing at all. |
| Citing it anyway | Would **weaken** the provenance record by implying an authority that does not exist. The fixture has been explicitly unsourced since Option C was dropped on 1 October 2026. Its honesty rests on asserting no clinical claim, not on quoting one. |

**The user accepted the alternative** on 2 October 2026: the rewrite is applied
against the **five copy rules in `02-architecture.md` section 7**. Those rules are
already Gate-approved, were written for exactly this problem, and are a stronger
tone authority than any external style guide because they were derived from a
reviewer's specific rejection of an earlier draft as too blunt.

---

## 3. The change, line by line

Unresolved rendering:

| # | Was | Now |
|---|---|---|
| 1 | Help is not arranged. | No one has agreed to help yet. |
| 2 (self owner) | You must act now. | Please act now. |
| 2 (named owner) | You or *[name]* must act now. | Please act now: you, or *[name]*. |
| 3 | Before *[deadline]*. | Please do it before *[deadline]*. |
| 4 | If this route fails, call *[route]*. | If that does not work, call *[route]*. |

Expired rendering:

| # | Was | Now |
|---|---|---|
| 1 | Help still is not arranged. | No one has agreed to help yet. |
| 2 | You can still do this. | You can still do this. (unchanged) |
| 3 | It is past *[deadline]*, so please go now. | It is past *[deadline]*. Please go now. |
| 4 | Call *[route]* — they can help from here. | Call *[route]*. They can help from here. |

Coordinator fallback: **unchanged after review.** "We could not check that answer
just now. Your plan has not changed." is already plain speech, names no capability
and carries no exclamation mark.

---

## 4. Two rewrites were rejected, and both are now encoded as rules

This is the substantive part of the pass. Both proposals came from the user.

| Proposal | Why rejected | Now encoded as |
|---|---|---|
| Line 1 becomes a question: "do you want me to alert your emergency contact?" or "I'll contact your emergency contact" | **No invented capability.** CareRelay holds no emergency contact, has no channel to reach one, and has no consent record. The sentence promises a dispatch that cannot occur, which is a **false completion** and a direct **I2** violation. The question form also breaks **I4**: it moves the obligation back to the patient instead of naming the party who acts. | Copy rule 6, "no invented capability", in `02-architecture.md` section 7 and `01-product.md` |
| Line 2 becomes "Please act now!!" | **No alarm.** Copy rule 2 already banned alarms, because the reviewer killed the first expired draft as too blunt for a frightened older adult. A double exclamation is an alarm, not a courtesy, and it is **sterner** than the "You must act now." it replaces, not softer. | Copy rule 2 extended with "no exclamation marks", in both gate documents |

**Both rejections are fail-capable.** Two tests were added so the decisions cannot
silently drift back:

- `test_no_patient_line_carries_an_exclamation_mark`
- `test_no_patient_line_offers_an_unbuilt_capability`

---

## 5. Files changed

| File | Change | Gate |
|---|---|---|
| `01-product.md` | Approved patient-facing copy gained the four-line rendering and the two new binding rules | **Gate 1** |
| `02-architecture.md` section 7 | Rendering table updated; line-by-line change record added; copy rules 2 and 6 amended | **Gate 2** |
| `00-status.md` | Both reopens recorded; the standing re-approval question added; the Slice 5 Check re-opened because the wording it asks the user to read has changed | state authority |
| `03-planback-closure-contract.md` sections 2.5 and 4 | Mirrors updated to the current copy | not a gate document |
| `PLAN.md` section 6.1 | Patient-facing rule mirrors updated | not a gate document |
| `mockups/03-unresolved-handoff.html` | Heading and all four lines updated | not a gate document |
| `src/carerelay/domain/rules.py` | Both renderings reworded | implementation |
| `src/carerelay/demo/fixture.py` | `SELF_OWNER_SENTENCE` and `demo_lines()` reworded | implementation |
| `fixtures/scripted_episode.json` | `note` records the reword date | implementation |
| `tests/test_domain.py` | Three assertions updated, two copy-rule tests added | tests |
| `tests/test_state.py` | One expired-rendering assertion updated | tests |
| `tests/test_api.py` | Docstring updated only; no assertion changed | tests |

`src/carerelay/api.py` was reviewed and **not changed**: the coordinator fallback
string and the screen chrome ("Your plan", "Hide the plan") were judged already
plain enough.

---

## 6. Verification

| Check | Result |
|---|---|
| Suite | **422 passed, 1 warning** (420 before the pass; two tests added) |
| Live render, `uvicorn` on 127.0.0.1:8145 | Matches the approved table exactly, both the JSON projection and the HTML screen |
| Expired render, through the store | Passes; line 1 is the reworded form, the deadline is intact, line 4 names the route |
| Em dashes in added lines | **3, all quotations of pre-existing text, none new prose.** See the disclosure below |
| CRLF | loneLF is 0 on all 13 files touched |
| Total added lines | 236 |

### Disclosure: the 3 em dashes

`AGENTS.md` section 6 bans em dashes in new writing. Three added lines carry one:

1. The mockup's line 2, `<strong>Please act now</strong> — or wait for your daughter,
   Mei-Ling.` **This sentence already carried an em dash before the pass**; only the
   words around it changed. It is not new writing.
2. The change-record table row that **quotes** the old and new expired line 4.
   Both are quotations.
3. The paragraph that **documents** the carried mockup em dash. Naming the character
   requires writing it.

None of the three is new prose using an em dash as punctuation.

---

## 7. What the user was asked, and the answer

> **Do you re-approve Gate 1 and Gate 2?**

**ANSWERED YES, 2 October 2026: "I have read and i re approve both gates".** Gate 1
and Gate 2 are APPROVED again. Gate 1 carries the patient copy; Gate 2 section 7
carries the table, the change record and the five copy rules.

**The same answer closed the re-opened Slice 5 Check.** Slice 5's Check is "the user
reads the fixture wording and the provenance record". It was re-opened because the
wording it asked the user to read had changed in this pass. The user has confirmed
that read. **Slice 5 closes as of 2 October 2026.**

**What this approval does not do:** it does not authorise a commit or a push; it does
not make the fixture clinical, reviewed or sourced (`approved_by` stays `NULL`); and
it does not close Slice 5's carried notes (F6's rendering half, O7 reachability, the
scoped O1 guarantee, the two dead functions, the 422 field-name mismatch), which stay
anchored to their later slices.

---

## 8. What this pass does not prove

- **It does not make the wording clinically reviewed.** No reviewer exists, and
  `approved_by` is still `NULL`.
- **It does not make the fixture sourced.** No source is claimed for any string. The
  wording is authored, and the provenance record is unchanged.
- **It does not establish that the new wording is better.** No participant has read
  either version. "Reads more like a person" is a judgement, not a measurement, and
  the study design measures the mechanism, not the copy.
- **It does not close F6's rendering half.** That is still anchored to Slice 10.
- **It does not authorise a commit or a push.** Nothing is committed and nothing is
  pushed.
