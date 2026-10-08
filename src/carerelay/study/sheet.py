"""The raw outcome sheet on disk. Slice 9.

**Why a file and not a database table.** Protocol section 4 requires all study
data to be destroyed 30 days after submission, and the product's own tables are
append-only with update and delete triggers, so a row written into one of them
could not be destroyed at all. The same section requires research-participant
consent to stay out of the clinical `consents` table; keeping the outcome sheet
out of the clinical database is the same separation applied to the outcomes.

**Why append-only JSON, one object per line.** The sheet is evidence, so a row
is never rewritten: a correction is a new row, and the earlier one stays visible.
That is the same discipline the product's ledger keeps, for the same reason.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from carerelay.study.outcomes import OutcomeRow

#: The default sheet. Resolved from this file, not from the process working
#: directory, so a facilitator can run the instrument from anywhere.
DEFAULT_SHEET_PATH = Path(__file__).resolve().parents[3] / "study" / "outcomes.jsonl"


def append_row(row: OutcomeRow, path: Path | None = None) -> Path:
    """Append one dyad's row to the sheet. Returns the path written."""
    target = DEFAULT_SHEET_PATH if path is None else path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(row), sort_keys=True, ensure_ascii=False)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
    return target


def read_rows(path: Path | None = None) -> list[OutcomeRow]:
    """Read the sheet back, in the order the rows were written.

    A missing sheet is an empty study, not an error: no dyad has been recorded
    yet is a state the instrument has to report, and protocol section 18 says
    exactly how to report it.
    """
    target = DEFAULT_SHEET_PATH if path is None else path
    if not target.exists():
        return []
    rows: list[OutcomeRow] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(OutcomeRow(**json.loads(line)))
    return rows
