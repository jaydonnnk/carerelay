# ADR-0002: A pure `domain` core — the model interprets, code decides

- **Status:** accepted
- **Date:** 2026-09-25
- **Source:** `02-architecture.md` D2, §2; `PLAN.md` §5.1
- **Supersedes:** —

## Context

The product asks a patient to say their care plan back in their own words, then decides whether they understood it. That decision has two failure directions and both are serious:

- **A false "you understood it"** means someone leaves believing they know when they do not. That is a safety failure.
- **A false "you did not understand"** means someone is told they are wrong when they are right, then made to repeat themselves. That is a dignity failure, and for an older adult it is a reason to stop using the product.

A model asked to grade comprehension can err in either direction, non-reproducibly. Two runs of the same sentence can produce different verdicts, and neither is auditable.

Separately, a coordinator that proposes actions must not be able to propose one the policy does not permit. A hallucinated route id or symptom code reaching the tool layer would dispatch a real request.

## Decision

**A pure `domain` core owns all policy, comparison and validation. It imports no network, no LLM client, no database, no filesystem and no wall clock.**

The flow is normative: **coordinator proposes → `domain` validates → state records.**

Specific rules:

- `compare_plan` is deterministic and total over extracted fields.
- Every coordinator-proposed route id and every classified symptom-change value is validated against the policy's permitted set **in `domain`** before it can cause an action.
- `domain` renders all patient-facing clinical text from policy. **No model-generated text reaches the patient.**
- Unknown extraction is `uncertain`, never a mismatch and never a match. Only a known, different canonical value is a mismatch.
- The coordinator never writes to the database and never sees credentials.

## Consequences

**Good**

- Comprehension decisions are reproducible and testable in a unit test with no model in the loop.
- A hallucinated id cannot reach the tool layer — the check is upstream of every action path.
- The "unknown is not an accusation" rule is enforceable in one place instead of at every call site.
- Fault injection becomes possible: the comparator can be mutated in a test to prove the assertions have teeth.

**Bad / accepted debt**

- The boundary needs an enforcing check, not discipline. Python will not refuse the import on its own. **Gate 3 names `test_domain_import_boundary` as the enforcing test, and it must be shown failing against a deliberate `import socket` before it counts as proof.**
- Canonicalisation has to live somewhere. Putting it in `domain` (ADR-0007, proposed) means `domain` needs the policy's alias and relative-time tables handed to it as data — a wider signature than the Gate 3 draft implies.
- Slightly more plumbing than letting the model return a clean boolean.

## Reversal

**Not reversible without reopening Gate 1.** D2 is the load-bearing architectural decision; if the boundary is a convention with a diagram rather than a failing check, the architecture is not what the documentation claims and the safety argument weakens materially.
