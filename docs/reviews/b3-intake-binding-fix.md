# B3 closed: the intake binding rule

**Run 2 October 2026. Verdict: B3 CLOSED, and it did not need a clinical reviewer.**

The premise carried since the Slice 4 adversarial review was that B3 is
"a reviewer-gated clinical decision". **That premise was wrong**, and this record
states what B3 actually is, why the reviewer assumption did not hold, and how the
fix was proved.

---

## 1. What was asked, and what was refused

The instruction was: *"We cant get a clinical reviewer for B3 so just source from
somewhere relevant and approve it."*

**The sourcing half was refused.** There is no source that clears, and the trail is
already on the record:

| Attempt | Outcome |
|---|---|
| MOH clause 11, HealthHub clause 12.1 | Prior written permission required |
| UK Open Government Licence | Licence clears, Singapore applicability fails |
| A hospitality style guide | Weaker than the two above, both of which failed |

Citing a source would not have closed B3 in any case. **B3 is not a sourcing
problem.** A licence to quote is not authority to act, and no citation makes a
substring match correct.

**The "approve it" half was refused.** Writing a non-clinician's name into
`approved_by` would have made the provenance record assert a sign-off that does not
exist. That is a fabricated approval, which `AGENTS.md` section 1 forbids outright.

---

## 2. What B3 actually is

**A logic defect in the intake binding rule.** Nothing clinical about it.

| | Rule | Meaning |
|---|---|---|
| **Was** | `self._bound_complaint not in rules.normalise(confirmed_text)` | "does the bound phrase appear anywhere in the text?" |
| **Now** | `rules.normalise(confirmed_text) != self._bound_complaint` | "is this the bound complaint?" |

The Slice 4 adversarial review measured the consequence of the old rule, and these
are its recorded measurements:

- Scored **200 and issued the demo plan**: a text carrying crushing chest pain, a
  text carrying a suspected stroke, a **negated** text ("I do not need help sorting
  out my appointment"), and a **third-party** text ("does my mother need...").
- Stopped with **422**: the empty string, whitespace, `"my appointment"` alone, and
  an unrelated complaint.

**The defect at its true size.** No clinical branch is derived from free text and
every accepted case issues the same non-clinical fixture plan, so there was no
clinical mis-triage in the demo. The defect was that the one input the whole
fail-closed posture rests on **was not fail-closed**.

---

## 3. Why no reviewer is needed

**The fix makes the system refuse strictly more inputs.** Every text that scored 200
under the old rule and stops under the new one is a *refusal*.

- No symptom is read.
- No urgency is inferred.
- No threshold is authored.

**Refusing more is never a clinical claim.** That is the whole argument, and it is
why the "reviewer-gated" label was wrong. It would be correct for *adding* red-flag
handling, which is clinical work and remains unauthored.

**The correction to the earlier reasoning is recorded as mine.** `00-status.md`
carried B3 as reviewer-gated from 30 September to 2 October. Widening a rule is
reviewer-gated; narrowing one is not, and B3 was always the latter.

---

## 4. Verification

| Check | Result |
|---|---|
| Suite | **428 passed, 1 warning** (422 before; five parametrised cases added, plus one control) |
| Mutation: restore the substring rule | **Exactly 5 RED**, all five parametrised cases, nothing else |
| Control case under mutation | **Stayed green**, proving the strict rule did not over-refuse |
| Byte-identical restore | `service.py` sha256 `c44f0db40d4541d9` before and after; loneLF 0 |
| Live, `uvicorn` 127.0.0.1:8151 | Red flag plus bound phrase **422** `stopped_at: human_path`; exact bound complaint **200** |
| Em dashes in added lines | **0** |
| CRLF | loneLF 0 on all five files touched |

**The mutation result is the load-bearing one.** A shared catch would have proved
nothing (`AGENTS.md` section 6), so the check is that the mutation moves **exactly**
the five intended cases and leaves the control alone.

---

## 5. What the fix does not do

- **No red-flag vocabulary.** An input that coincidentally equals the bound phrase
  still binds. That is the accepted limitation of a fixture-bound demo.
- **No negation or third-party handling.** Those remain clinical work, unauthored.
- **It does not make the fixture sourced.** No source is claimed; `approved_by`
  stays `NULL`.
- **It does not close F6's rendering half or the other carried notes.**

---

## 6. Rode along: a test-hygiene fix

Eight test call sites passed the literal `"i need help sorting out my appointment"`
while the fixture binds `"help sorting out my appointment"`. **They matched only
because the rule was a substring test.** They now pass `fixture.BOUND_COMPLAINT`, so
the tests cannot silently diverge from the fixture again.

The misnamed test is corrected too.
`test_a_complaint_the_fixture_is_not_bound_to_stops_at_the_human_path` submitted only
a zero-overlap string, so it proved the disjoint case while carrying a name that
claimed the general rule. The general rule now has its own parametrised test.
