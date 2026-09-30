# Architecture Decision Records

Short, dated records of the technical choices that outlive the feature that produced them. Each one answers: what was decided, what forced it, what it costs, and what would reverse it.

**Read this first if you are new to the repository.** These records are the entry point to *why* CareRelay is built the way it is. They are deliberately short. Each links to the gate document that carries the full reasoning, which remains the authority.

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-python-fastapi-sqlite-stack.md) | Python 3.13 + FastAPI + SQLite, server-rendered UI | accepted | 2026-09-25 |
| [0002](0002-pure-domain-core.md) | Pure `domain` core; model interprets, code decides | accepted | 2026-09-25 |
| [0003](0003-append-only-clinical-record.md) | Append-only clinical record; no mutable status | accepted | 2026-09-25 |
| [0004](0004-derived-closure.md) | Closure is derived, never stored | accepted | 2026-09-25 |
| [0005](0005-server-generated-idempotency-keys.md) | Server-generated idempotency keys | accepted | 2026-09-25 |
| [0006](0006-external-between-subjects-baseline.md) | Baseline is an external card, between-subjects | accepted (amended 2026-09-26) | 2026-09-25 |
| [0007](0007-canonicalisation-lives-in-domain.md) | PlanBack canonicalisation lives in `domain`, not the model | accepted (28 Sep, at Gate 4) | 2026-09-28 |
| [0008](0008-keep-full-scope-over-schedule-fit.md) | Keep full scope and record the schedule risk, rather than cut | accepted | 2026-09-28 |

## Conventions

- **Numbering is sequential and permanent.** `NNNN-slug.md`, four digits.
- **Never rewrite an accepted ADR.** To change a decision, add a new ADR and set the old one's status to `superseded by ADR-NNNN`. The history is the point.
- **Status values:** `proposed` · `accepted` · `superseded by ADR-NNNN` · `rejected`.
- **Every ADR carries four sections:** Context, Decision, Consequences, Reversal.
- **The gate documents remain authoritative.** An ADR summarises a decision; it does not override `00-status.md`, `02-architecture.md`, `03-program-design.md` or `04-slices.md`. Where they disagree, the gate documents win and the ADR is corrected.

## Where the authority lives

```
docs/plans/urgent-advice-accessibility/00-status.md   gate + slice state (ONLY authority)
docs/plans/urgent-advice-accessibility/02-architecture.md   D1-D12, approved 25 Sep
docs/plans/urgent-advice-accessibility/03-program-design.md  files, types, tests, approved 26 Sep
docs/plans/urgent-advice-accessibility/04-slices.md  build order, Gate 4
docs/adr/                                             this directory: why, for people arriving later
```

## Two standing rules that are not ADRs

They are product constraints, not technical choices, and they are repeated here only so a new contributor cannot miss them:

- **No cognitive-improvement, cognitive-training, screening or risk-score claim** — in the product, submission, video or pitch. Meta-analyses find no far transfer from cognitive training; the FTC fined Lumosity $2 million in 2016 over exactly this claim. The scaffold improves retention of *this plan* and nothing more.
- **No asset may name a real healthcare facility.** The fixture provider is fictional and labelled.
