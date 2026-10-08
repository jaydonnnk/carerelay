"""Research-participant consent, recorded apart from the outcome sheet. Slice 9.

Protocol section 4: research-participant consent is recorded on the consent sheet
**before any task begins**. It is separate from the clinical `consents` table and
is never written into it. A participant may withdraw at any point.

**What this record deliberately does not hold.** Section 4 collects the raw
outcome sheet, task time, the burden rating, the answer to the scripted question
and any adverse reaction, and then says "nothing else". So no participant name,
no signature and no contact detail is written here. The paper form the
participant reads and signs stays with the facilitator; the study record holds
only that consent was given, for which dyad, under which version of the form.

**Why the version is enforced.** A participant agrees to a wording, not to a
principle. If the form changes, what was recorded was agreement to the older
wording, and running a session against it would claim a consent that was never
given. The version is checked when the record is made and again when it is read.

**Why a declined consent is still written.** A refusal is evidence. Section 4
gives the participant the right to decline, and a consent log that only ever
held agreements could not show that anyone had.

**Why there is no timestamp comparison.** "Before any task begins" is enforced
structurally instead: a dyad's outcome row cannot be recorded until its consent
row exists, so consent precedes the session by construction, and both files are
append-only, so the order they were written in stays visible.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

#: The version of the form a participant agrees to. `study/consent-sheet.md`
#: carries this version in its own text, so the paper and the record can be
#: matched by hand if they ever need to be.
CONSENT_VERSION = "consent-v1"

#: The default consent log. Resolved from this file, like the outcome sheet, so
#: the instrument can be run from any working directory.
DEFAULT_CONSENT_PATH = Path(__file__).resolve().parents[3] / "study" / "consent.jsonl"


class NoConsentRecorded(ValueError):
    """No current consent for this dyad, so no session may be recorded.

    Protocol section 4 puts consent before the first task. Recording a session
    without it would make the study's own record the evidence that the protocol
    was broken, which is worse than having no session at all.
    """


class StaleConsentVersion(ValueError):
    """The consent was given under a different version of the form.

    An agreement to an older wording is not an agreement to this one, so a stale
    record authorises nothing. It is refused rather than rewritten, because
    rewriting it would invent a consent that was never given.
    """


@dataclass(frozen=True)
class ConsentRecord:
    """One dyad's consent, as the study record holds it.

    `agreed` is the participant's answer, not the facilitator's impression of
    it. A record with `agreed=False` is a declined consent: it is written, and
    it authorises nothing.
    """

    dyad: str
    version: str
    agreed: bool
    at: str = ""

    def __post_init__(self) -> None:
        if not self.dyad.strip():
            raise ValueError("a consent record names the dyad it covers")
        if self.version != CONSENT_VERSION:
            raise StaleConsentVersion(
                f"consent version {self.version!r} is not the current form "
                f"{CONSENT_VERSION!r}: an agreement to an older wording "
                f"authorises nothing"
            )


def append_consent(record: ConsentRecord, path: Path | None = None) -> Path:
    """Append one consent record. Returns the path written."""
    target = DEFAULT_CONSENT_PATH if path is None else path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(record), sort_keys=True, ensure_ascii=False)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
    return target


def read_consents(path: Path | None = None) -> list[ConsentRecord]:
    """Read the consent log back, in the order the records were written.

    A missing log is an empty study, not an error: nobody has been consented yet
    is a state the instrument has to report.
    """
    target = DEFAULT_CONSENT_PATH if path is None else path
    if not target.exists():
        return []
    records: list[ConsentRecord] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        records.append(ConsentRecord(**json.loads(line)))
    return records


def consented_dyads(records: Iterable[ConsentRecord]) -> set[str]:
    """The dyads a session may be recorded for.

    Agreement to the **current** form only. A declined consent and a stale
    version are both excluded, and neither is deleted from the log.
    """
    return {
        record.dyad
        for record in records
        if record.agreed and record.version == CONSENT_VERSION
    }


def require_consent(dyad: str, records: Iterable[ConsentRecord]) -> None:
    """Refuse to record a session for a dyad with no current consent.

    Protocol section 4. The refusal names the dyad, because "consent is missing"
    without a dyad is a statement a facilitator cannot act on.
    """
    if dyad in consented_dyads(records):
        return
    raise NoConsentRecorded(
        f"dyad {dyad} has no consent recorded under {CONSENT_VERSION}: "
        f"protocol section 4 requires consent before any task begins, and a "
        f"declined or stale consent authorises nothing"
    )
