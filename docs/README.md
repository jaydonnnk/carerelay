# CareRelay documentation map

**Where everything lives, and which file wins when two disagree.**

This is the entry point for a reader with no prior context. Read it once, then follow
the read order below.

---

## The one authority

`docs/plans/urgent-advice-accessibility/00-status.md` is the **only** authority for
gate state and slice state. `PROGRESS.md` is operational memory and may never record
or imply a gate approval. Everything else is supporting.

---

## The five locations

| Location | Holds | Authority |
|---|---|---|
| repo root | `AGENTS.md` (execution rules), `PROGRESS.md` (operational memory), three historical case-study inputs | `AGENTS.md` binds how work is done; the case studies are context, not scope |
| `docs/` | the official challenge rules and the plan: `CHALLENGE_REQUIREMENTS_JUDGING.md`, `ADDITIONAL_CHALLENGE_INFO.md`, `PLAN.md`, `DESIGN_PRINCIPLES.md`, `organiser-tech-load-bearing-audit.html` | official rules and primary sources override any stored summary |
| `docs/plans/urgent-advice-accessibility/` | the four gate documents, their supporting notes and the seven HTML mockups | the gate documents; `00-status.md` is the only state authority |
| `docs/reviews/` | adversarial reviews and the review briefs handed to independent reviewers | a review is authoritative for nothing; it is evidence about a slice or a gate. The per-file map of this folder is in the Document map section of `00-status.md` |
| `docs/adr/` | dated decisions that outlive the feature | summarises a decision; never overrides a gate document |

---

## Convention (set 30 September 2026)

- **All review artefacts and documentation go under `docs/`.** A review is filed in
  `docs/reviews/`, not beside the record it reviews and not outside the repository.
- Reviews and review briefs: `docs/reviews/`.
- Decisions that outlive the feature: `docs/adr/`, one numbered file each, with an
  index in `docs/adr/README.md`.
- Feature and gate documents: `docs/plans/<feature>/`.
- New folders under `docs/` are welcome when a category appears. Add a row here and in
  the map in `00-status.md` when you add one.

---

## Read order for a fresh session

1. `docs/CHALLENGE_REQUIREMENTS_JUDGING.md` (official rules and the rubric)
2. `docs/PLAN.md` (direction, labelled evidence, scope, schedule)
3. `docs/plans/urgent-advice-accessibility/00-status.md` and every file under that folder
4. `docs/DESIGN_PRINCIPLES.md` when scope, ambition or novelty is in question
5. `docs/plans/urgent-advice-accessibility/research-workarounds.md` when a blocker is in play
6. `tasks/lessons.md` before working, to avoid repeating a logged mistake

---

## The file-map trap

Two supporting notes already occupy the `02-` and `03-` filenames that the Gate 2 and
Gate 3 documents would use:

- `02-architecture.md` is the **Gate 2** document (approved revision 2).
- `03-program-design.md` is the **Gate 3** document.
- `03-planback-closure-contract.md` is a **supporting note** that carries the `03-`
  number; it is not the Gate 3 document.

Read the map in `00-status.md` before assuming a file's role from its number.

---

## Where the authority lives

```
docs/plans/urgent-advice-accessibility/00-status.md           gate + slice state (ONLY authority)
docs/plans/urgent-advice-accessibility/02-architecture.md     D1 to D12, approved 25 Sep
docs/plans/urgent-advice-accessibility/03-program-design.md   files, types, tests, approved 26 Sep
docs/plans/urgent-advice-accessibility/04-slices.md           build order, Gate 4
docs/reviews/                                                 adversarial reviews and briefs
docs/adr/                                                     why, for people arriving later
```

---

## Evidence labels

Every factual claim in a CareRelay document carries one label. Keep this convention.

- `[verified]` supported by the cited source
- `[vendor claim]` advertised but not independently validated
- `[hypothesis]` our judgement
- `[unknown]` not established

Reviews use a narrower set: `[verified]` observed in that session, `[estimate]` the
reviewer's judgement, `[guess]` a hunch, `[unknown]` not established.
