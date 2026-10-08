"""Run the Gate B instrument from a shell. Slice 9.

    PYTHONPATH=src python -m carerelay.study script
    PYTHONPATH=src python -m carerelay.study consent --dyad d1
    PYTHONPATH=src python -m carerelay.study record --dyad d1 --position 1 \
        --task-time 42 --action-option A --deadline-option A \
        --action "go to the clinic" --deadline "6pm" \
        --answer "no" --barrier yes --burden 2
    PYTHONPATH=src python -m carerelay.study resolve --dyad d1 \
        --field "deadline recall" --verdict correct \
        --scorer "A. Second" --facilitator "J. Facilitator"
    PYTHONPATH=src python -m carerelay.study report
    PYTHONPATH=src python -m carerelay.study sheet

**The order is enforced, not advisory.** `consent` comes first and `record`
refuses a dyad with no current consent, because protocol section 4 puts consent
before any task begins. `resolve` takes a verdict from a **named** second scorer
and refuses one from whoever ran the session, because section 16 gives scoring
to someone who did not run it. Only then can `report` apply the cut rule, which
refuses while any response is still queued (section 11).

`render_script` prints the closed recall options as well as the questions, so a
session can be run from the command line without opening the protocol.

`report` renders the **resolved** view: the raw rows with the second scorer's
verdicts applied. `sheet` renders the raw sheet, which is this slice's Check:
the user is shown the raw sheet, not a summary statistic.

**Two answers per recall question, and only one is scored.** `--action-option`
and `--deadline-option` take the letter the facilitator recorded, A to D, and
that is what the scorer reads. `--action` and `--deadline` take the words, which
are kept on the row for the second scorer and printed into Notes, but are not
scored. A row recorded with no letter is left unclassified rather than guessed.

`main` takes the file paths as arguments so a test can point it at temporary
files. It is not an entry point that guesses where its data lives.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from carerelay.study.consent import (
    CONSENT_VERSION,
    ConsentRecord,
    NoConsentRecorded,
    StaleConsentVersion,
    append_consent,
    read_consents,
    require_consent,
)
from carerelay.demo import fixture
from carerelay.study.outcomes import (
    CARD_CONDITION,
    HINT_LEVELS,
    RESOLVABLE_FIELDS,
    OutcomeRow,
    condition_for_position,
    next_position,
    render_outcome_sheet,
    render_result,
)
from carerelay.study.scoring import DEADLINE_OPTIONS
from carerelay.study.second_scorer import (
    FIELD_VERDICTS,
    SecondScorerDecision,
    append_decision,
    assert_blinded,
    read_decisions,
    resolved_rows,
)
from carerelay.study.sheet import append_row, read_rows

#: The frozen script, protocol section 7. It is written out here so a
#: facilitator can run a session without opening the protocol, and
#: `test_the_script_is_the_frozen_protocol_script` pins every line against the
#: document, so it cannot drift from it silently.
STATUS_STATEMENT = "The booking link was tried. No one has agreed to help yet."
POST_FAILURE_QUESTION = "Has care been arranged for you?"
REDIRECT_ANSWER = "I cannot answer that. Please give me your own answer."

#: The closed recall instrument, protocol section 7 as amended on 8 October
#: 2026. The facilitator reads the options aloud, so the script has to carry
#: them: a script that asks the question without the choices cannot run the
#: instrument the amendment exists to create.
#:
#: The deadline options are read from the scorer, so the script cannot offer a
#: deadline the scorer does not score. Action options B and C are the renderings
#: the amendment wrote for the two other permitted actions: the fixture carries
#: ids and no wording for them, so they are pinned to the document by a test
#: rather than derived.
DONT_KNOW_TEXT = "I don't know"
ACTION_OPTION_TEXT: tuple[str, ...] = (
    fixture.ACTION_TEXT,
    "Call the fictional nurse line.",
    "Wait and monitor.",
    DONT_KNOW_TEXT,
)
DEADLINE_OPTION_TEXT: tuple[str, ...] = tuple(
    [DEADLINE_OPTIONS[letter] for letter in sorted(DEADLINE_OPTIONS)]
    + [DONT_KNOW_TEXT]
)
#: Keyed by the field name in `SECONDARY_QUESTIONS`, so the options can never be
#: printed against the wrong question.
RECALL_OPTIONS: dict[str, tuple[str, ...]] = {
    "Action recall": ACTION_OPTION_TEXT,
    "Deadline recall": DEADLINE_OPTION_TEXT,
}
SECONDARY_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("Action recall", "Which of these were you asked to do?"),
    ("Deadline recall", "By when?"),
    (
        "Barrier recognition",
        "Was there anything that would have stopped you doing it?",
    ),
    (
        "Burden",
        "How hard was it to keep track of this plan? Answer 1 for very easy, "
        "up to 5 for very hard",
    ),
)

#: Every verdict any field accepts, for the command line only. Which verdicts a
#: given field accepts is decided in `second_scorer.FIELD_VERDICTS`.
ALL_VERDICTS: tuple[str, ...] = tuple(
    sorted({verdict for verdicts in FIELD_VERDICTS.values() for verdict in verdicts})
)


def render_script(position: int) -> list[str]:
    """The facilitator's script for one position, in the frozen wording.

    The condition comes from the position and is never chosen, so the script
    cannot be used to run the wrong arm.
    """
    condition = condition_for_position(position)
    lines = [
        f"Position {position}. Condition {condition}.",
        "",
        "Speak exactly as written. No prompt, no hint, no repetition of the "
        "plan, no re-reading of the card. The first answer stands.",
        "",
    ]
    if condition == CARD_CONDITION:
        lines.append(f"Status statement, spoken verbatim: {STATUS_STATEMENT}")
    else:
        lines.append(
            "Status statement: none. The screen carries it. Do not speak it."
        )
    lines.extend(["", f"Post-failure question: {POST_FAILURE_QUESTION}", ""])
    lines.append("Secondary-outcome questions:")
    lines.extend(f"  {name}: {question}" for name, question in SECONDARY_QUESTIONS)
    lines.append("")
    lines.append(
        "Closed recall options. Read them aloud in this order, after the "
        "material is out of sight, and record the letter chosen."
    )
    for name, options in RECALL_OPTIONS.items():
        rendered = " ".join(
            f"{chr(ord('A') + index)}. {option}"
            for index, option in enumerate(options)
        )
        lines.append(f"  {name}: {rendered}")
    lines.extend(["", f"If the participant asks what you think: {REDIRECT_ANSWER}"])
    return lines


def _build() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--sheet", type=Path, default=None)
    common.add_argument("--consent-file", type=Path, default=None)
    common.add_argument("--decisions-file", type=Path, default=None)

    parser = argparse.ArgumentParser(
        prog="carerelay.study", description=__doc__.splitlines()[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)

    script = sub.add_parser("script", parents=[common])
    script.add_argument("--position", type=int, default=None)

    consent = sub.add_parser("consent", parents=[common])
    consent.add_argument("--dyad", required=True)
    consent.add_argument("--declined", action="store_true")
    consent.add_argument("--at", default="")

    record = sub.add_parser("record", parents=[common])
    record.add_argument("--dyad", required=True)
    record.add_argument("--position", type=int, required=True)
    record.add_argument("--task-time", type=int, required=True)
    record.add_argument("--action-option", default="")
    record.add_argument("--deadline-option", default="")
    record.add_argument("--action", required=True)
    record.add_argument("--deadline", required=True)
    record.add_argument("--answer", required=True)
    record.add_argument("--barrier", choices=("yes", "no"), default=None)
    record.add_argument("--burden", type=int, required=True)
    record.add_argument("--hint", choices=HINT_LEVELS, default=None)
    record.add_argument("--adverse", default="")
    record.add_argument("--notes", default="")
    record.add_argument("--withdrawn", action="store_true")

    resolve = sub.add_parser("resolve", parents=[common])
    resolve.add_argument("--dyad", required=True)
    resolve.add_argument("--field", choices=RESOLVABLE_FIELDS, required=True)
    resolve.add_argument("--verdict", choices=ALL_VERDICTS, required=True)
    resolve.add_argument("--scorer", required=True)
    resolve.add_argument("--facilitator", required=True)
    resolve.add_argument("--note", default="")

    sub.add_parser("report", parents=[common])
    sub.add_parser("sheet", parents=[common])
    return parser


def main(
    argv: list[str],
    sheet_path: Path | None = None,
    consent_path: Path | None = None,
    decisions_path: Path | None = None,
) -> int:
    """Run one command. Returns 0 on success and 2 on a refused or invalid row."""
    args = _build().parse_args(argv)
    sheet = sheet_path if sheet_path is not None else args.sheet
    consent_file = consent_path if consent_path is not None else args.consent_file
    decision_file = (
        decisions_path if decisions_path is not None else args.decisions_file
    )

    if args.command == "consent":
        try:
            record = ConsentRecord(
                dyad=args.dyad,
                version=CONSENT_VERSION,
                agreed=not args.declined,
                at=args.at,
            )
        except ValueError as error:
            print(f"refused: {error}", file=sys.stderr)
            return 2
        append_consent(record, consent_file)
        state = "agreed" if record.agreed else "declined"
        print(f"consent {state} for {record.dyad} under {record.version}")
        if not record.agreed:
            print("  a declined consent authorises nothing: no session may be run")
        return 0

    if args.command == "record":
        try:
            require_consent(args.dyad, read_consents(consent_file))
        except (NoConsentRecorded, StaleConsentVersion) as error:
            # A declined or unconsented dyad, and a log holding an older version
            # of the form, both refuse the session. Caught narrowly on purpose:
            # a corrupt log raises `JSONDecodeError`, which is also a
            # `ValueError`, and reporting that as a refusal would hide it.
            print(f"refused: {error}", file=sys.stderr)
            return 2
        barrier = None if args.barrier is None else args.barrier == "yes"
        try:
            row = OutcomeRow(
                dyad=args.dyad,
                position=args.position,
                condition=condition_for_position(args.position),
                task_time_s=args.task_time,
                action_recall=args.action,
                deadline_recall=args.deadline,
                action_option=args.action_option,
                deadline_option=args.deadline_option,
                false_completion=args.answer,
                barrier_recognised=barrier,
                burden=args.burden,
                hint_level=args.hint,
                adverse_reaction=args.adverse,
                notes=args.notes,
                withdrawn=args.withdrawn,
            )
        except ValueError as error:
            print(f"refused: {error}", file=sys.stderr)
            return 2
        append_row(row, sheet)
        print(f"recorded {row.dyad} at position {row.position} (condition {row.condition})")
        print(f"  action={row.action_label} deadline={row.deadline_label}")
        print(f"  both correct={row.both_correct} false completion={row.false_completion_label}")
        return 0

    if args.command == "resolve":
        try:
            assert_blinded(args.scorer, args.facilitator)
            decision = SecondScorerDecision(
                dyad=args.dyad,
                field=args.field,
                verdict=args.verdict,
                scorer=args.scorer,
                note=args.note,
            )
        except ValueError as error:
            print(f"refused: {error}", file=sys.stderr)
            return 2
        append_decision(decision, decision_file)
        print(f"{decision.scorer} resolved {decision.dyad}, {decision.field}: {decision.verdict}")
        return 0

    rows = read_rows(sheet)
    if args.command == "sheet":
        print("\n".join(render_outcome_sheet(rows)))
        return 0
    if args.command == "report":
        resolved = resolved_rows(rows, read_decisions(decision_file))
        print("\n".join(render_result(resolved)))
        return 0

    position = (
        next_position([row.position for row in rows])
        if args.position is None
        else args.position
    )
    print("\n".join(render_script(position)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
