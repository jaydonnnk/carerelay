"""Mutation check for the Slice 9 guards. The Gate B response path.

Run: PYTHONPATH=src python tests/_mutate_slice9.py

Slice 9 builds the instrument that scores what a participant says and decides
whether PlanBack survives. The defects worth injecting are therefore the ones
that make the instrument decide wrongly while still looking decisive:

* an allocation that stops being frozen, so a condition can be chosen or a gap
  can be resequenced away;
* an unclassified response that becomes `incorrect`, because the cut rule reads
  the field it belongs to and a guess there kills or saves the mechanism by
  accident;
* a cut rule that fires when only one of its two halves holds, or that runs
  while rows are unresolved, below the protocol's minimum sample, or when the
  conditions are unequal;
* a protocol that stops stating the minimum sample the cut rule enforces;
* a write-up that quietly drops the parts the protocol requires: adverse
  reactions, the design limitation, the directional caveat;
* a consent guard that lets a session be recorded with no consent behind it, or
  lets a declined or stale consent authorise one anyway;
* a second scorer's verdict that resolves nothing, or a blinding check that
  passes because the facilitator was never named;
* a facilitator's script that drifts from the frozen wording, or speaks the
  status statement into the condition that must not hear it;
* a closed recall field scored from anything other than the option chosen,
  which is the amendment of 8 October 2026: a distractor scored correct,
  "I don't know" left unresolved, and a row with no option recorded guessed
  instead of queued;
* a write-up that prints an unknown as a wrong answer, and a raw sheet that
  forgets the words now that the recall columns carry the option.

Three conventions carried over from the Slice 8 harness, each of which cost this
project a wrong answer once:

* **A RED is read from a real test failure, never from the exit code alone.**
  pytest exits 4 for a selector that resolves to nothing, and a harness reading
  "non-zero means RED" reports a kill for a test that never ran.
* **The count of tests that ran comes off the progress characters**, and pytest
  right-pads that field, so the padding is stripped before counting.
* **The anchor is matched in the file's own newline convention.** The repository
  is CRLF, so an LF-written anchor silently fails to apply and a guard that was
  never touched is recorded as SURVIVED.

Every file is restored byte-identically and its cached bytecode purged, because a
`.pyc` compiled while a mutation was live can outlive the restore.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
PYTHON = sys.executable

OUTCOMES = "src/carerelay/study/outcomes.py"
SCORING = "src/carerelay/study/scoring.py"
SHEET = "src/carerelay/study/sheet.py"
#: Added 7 October 2026 with the section 13 floor amendment. The floor is a
#: document claim the guard enforces, so the protocol is a mutation target too.
PROTOCOL = "study/protocol.md"
#: Added 7 October 2026 with the recruitment preparation: consent, the second
#: scorer and the facilitator's script.
CONSENT = "src/carerelay/study/consent.py"
SECOND_SCORER = "src/carerelay/study/second_scorer.py"
MAIN = "src/carerelay/study/__main__.py"
#: Participant data must never be committed, so the ignore list is a guard.
GITIGNORE = ".gitignore"

TARGETS = {
    OUTCOMES: REPO / "src" / "carerelay" / "study" / "outcomes.py",
    SCORING: REPO / "src" / "carerelay" / "study" / "scoring.py",
    SHEET: REPO / "src" / "carerelay" / "study" / "sheet.py",
    PROTOCOL: REPO / "study" / "protocol.md",
    CONSENT: REPO / "src" / "carerelay" / "study" / "consent.py",
    SECOND_SCORER: REPO / "src" / "carerelay" / "study" / "second_scorer.py",
    MAIN: REPO / "src" / "carerelay" / "study" / "__main__.py",
    GITIGNORE: REPO / ".gitignore",
}

TESTS = "tests/test_study_instrument.py"
RECRUITMENT = "tests/test_study_recruitment.py"
ALLOCATION = f"{TESTS}::TestTheFrozenAllocation"
ROW = f"{TESTS}::TestTheRowKeepsItsVerbatimText"
CONJUNCTION = f"{TESTS}::TestBothCorrectIsAConjunction"
CUT = f"{TESTS}::TestThePreRegisteredCutRule"
QUEUE = f"{TESTS}::TestTheSecondScorerQueue"
SHEETTESTS = f"{TESTS}::TestTheRawOutcomeSheet"
WRITEUP = f"{TESTS}::TestTheResultIsWrittenDownHonestly"
#: Added 8 October 2026 with the closed recall instrument (protocol sections
#: 7, 10, 11 and 12 as amended) and the reporting defect it exposed.
CLOSED = f"{TESTS}::TestTheClosedRecallInstrument"
UNKNOWN = f"{TESTS}::TestAnUnknownIsNotReportedAsAWrongAnswer"

CONSENT_BEFORE = f"{RECRUITMENT}::TestConsentComesBeforeTheTask"
CONSENT_MINIMAL = f"{RECRUITMENT}::TestTheConsentRecordIsMinimal"
QUEUE_RESOLVED = f"{RECRUITMENT}::TestTheSecondScorerResolvesTheQueue"
VERDICT_RESOLVES = f"{RECRUITMENT}::TestAVerdictHasToResolveSomething"
NOT_SCORING = f"{RECRUITMENT}::TestTheFacilitatorDoesNotScore"
FROZEN_SCRIPT = f"{RECRUITMENT}::TestTheFrozenScript"
RECRUIT_CLI = f"{RECRUITMENT}::TestTheRecruitmentCommandLine"
IGNORED = f"{RECRUITMENT}::TestStudyDataNeverReachesTheRepository"

#: (label, target, anchor, replacement, selectors)
MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "A1  the allocation order stops alternating",
        OUTCOMES,
        b"    position: (APPLICATION_CONDITION if position % 2 == 1 else "
        b"CARD_CONDITION)",
        b"    position: (APPLICATION_CONDITION if position % 2 == 0 else "
        b"CARD_CONDITION)",
        [
            f"{ALLOCATION}::test_the_order_alternates_a_and_b",
            f"{ALLOCATION}::test_the_order_is_the_protocol_table",
        ],
    ),
    (
        "A2  next_position resequences past a gap",
        OUTCOMES,
        b"        if position not in taken:\n",
        b"        if True:\n",
        [
            f"{ALLOCATION}::test_the_next_position_is_the_lowest_unused",
            f"{ALLOCATION}::test_an_abandoned_session_leaves_a_gap",
        ],
    ),
    (
        "A3  a condition that contradicts its position is accepted",
        OUTCOMES,
        b"        if self.condition != expected:\n",
        b"        if False:\n",
        [f"{ROW}::test_a_condition_that_contradicts_its_position_is_refused"],
    ),
    (
        "A4  the card condition is allowed a hint level",
        OUTCOMES,
        b"        if self.hint_level is not None and self.condition != "
        b"APPLICATION_CONDITION:\n",
        b"        if False:\n",
        [f"{ROW}::test_the_card_condition_has_no_hint_level"],
    ),
    (
        "B1  an unclassified recall is guessed as incorrect",
        OUTCOMES,
        # Repointed 7 October 2026: the conjunction moved out of the row's
        # property into `both_correct_from`, so that the row's own view and the
        # second scorer's resolved view cannot disagree about it.
        b"    if UNCLASSIFIED in (action_label, deadline_label):\n"
        b"        return UNCLASSIFIED\n",
        b"    if False:\n        return UNCLASSIFIED\n",
        [f"{CONJUNCTION}::test_unclassified_when_either_field_is_unclassified"],
    ),
    (
        "F1  the primary outcome is scored instead of named",
        SCORING,
        b"            return FALSE_COMPLETION\n",
        b"            return CORRECT\n",
        [f"{ROW}::test_the_primary_outcome_is_named_not_scored"],
    ),
    (
        # Three mutations, one per field, because the first version of the guard
        # exercised the deadline field alone and this mutation SURVIVED with the
        # whole suite green: nothing had ever asked for an unclassifiable action.
        "K1  the second-scorer queue drops the action field",
        OUTCOMES,
        b"        if row.action_label == UNCLASSIFIED:\n",
        b"        if False:\n",
        [f"{QUEUE}::test_every_unclassifiable_field_is_queued_verbatim"],
    ),
    (
        "K2  the second-scorer queue drops the deadline field",
        OUTCOMES,
        b"        if row.deadline_label == UNCLASSIFIED:\n",
        b"        if False:\n",
        [f"{QUEUE}::test_every_unclassifiable_field_is_queued_verbatim"],
    ),
    (
        "K3  the second-scorer queue drops the false completion field",
        OUTCOMES,
        b"        if row.false_completion_label == UNCLASSIFIED:\n",
        b"        if False:\n",
        [f"{QUEUE}::test_every_unclassifiable_field_is_queued_verbatim"],
    ),
    (
        "C1  the cut rule fires on an equal burden",
        OUTCOMES,
        b"    lower_burden = medians[CARD_CONDITION] < medians["
        b"APPLICATION_CONDITION]",
        b"    lower_burden = medians[CARD_CONDITION] <= medians["
        b"APPLICATION_CONDITION]",
        [f"{CUT}::test_planback_is_kept_when_the_card_burden_is_only_equal"],
    ),
    (
        "C2  the cut rule fires when the card loses on recall",
        OUTCOMES,
        b"    recall_at_least_equal = counts[CARD_CONDITION] >= counts["
        b"APPLICATION_CONDITION]",
        b"    recall_at_least_equal = True",
        [f"{CUT}::test_planback_is_kept_when_the_card_loses_on_recall"],
    ),
    (
        "C3  the cut rule stops waiting for the second scorer",
        OUTCOMES,
        # The two-line form is ambiguous: `render_result` opens with the same
        # pair. The raise line is what makes this the cut rule's guard and not
        # the write-up's, so the anchor carries it.
        b"    pending = pending_second_scorer(rows)\n    if pending:\n"
        b"        raise UnresolvedResponses(\n",
        b"    pending = pending_second_scorer(rows)\n    if False:\n"
        b"        raise UnresolvedResponses(\n",
        [
            f"{CUT}"
            "::test_the_rule_refuses_while_a_response_awaits_the_second_scorer"
        ],
    ),
    (
        "C4  the cut rule stops checking that the conditions are equal",
        OUTCOMES,
        b"    sizes = dyad_counts(rows)\n"
        b"    if sizes[APPLICATION_CONDITION] != sizes[CARD_CONDITION]:\n",
        b"    sizes = dyad_counts(rows)\n    if False:\n",
        [f"{CUT}::test_the_rule_refuses_when_the_conditions_are_unequal"],
    ),
    (
        "C5  the cut rule fires below the protocol minimum",
        OUTCOMES,
        b"    if min(sizes.values()) < MIN_DYADS_PER_CONDITION:\n",
        b"    if False:\n",
        [f"{CUT}::test_the_rule_refuses_below_the_protocol_minimum"],
    ),
    (
        "P1  the protocol drops the cut rule's minimum sample",
        PROTOCOL,
        b"**The rule has a minimum sample: three dyads per condition.**",
        b"**The rule has no minimum sample.**",
        [f"{CUT}::test_the_cut_rule_states_the_minimum_sample_it_is_given"],
    ),
    (
        "D1  a withdrawn dyad is analysed anyway",
        OUTCOMES,
        b"    return [row for row in rows if not row.withdrawn]\n",
        b"    return list(rows)\n",
        [
            f"{CUT}::test_a_fully_withdrawn_study_has_no_result",
            f"{CUT}::test_withdrawn_rows_are_excluded_from_the_counts",
        ],
    ),
    (
        "E1  an empty condition is given a burden of zero",
        OUTCOMES,
        b'            raise NoGateBResult(f"condition {condition} has no '
        b'analysed dyad")',
        b"            medians[condition] = 0.0",
        [f"{CUT}::test_a_condition_with_no_analysed_dyad_has_no_median"],
    ),
    (
        "G1  the sheet drops the adverse reaction column",
        OUTCOMES,
        b'    "Adverse reaction",\n',
        b"",
        [f"{SHEETTESTS}::test_the_sheet_carries_the_protocol_columns"],
    ),
    (
        "J1  a missing sheet raises instead of being an empty study",
        SHEET,
        b"    if not target.exists():\n        return []\n",
        b"",
        [f"{SHEETTESTS}::test_a_missing_sheet_is_an_empty_study"],
    ),
    (
        "H1  the write-up drops adverse reactions",
        OUTCOMES,
        b"    reactions = [row for row in analysed(rows) "
        b"if row.adverse_reaction.strip()]\n",
        b"    reactions = []\n",
        [f"{WRITEUP}::test_adverse_reactions_are_reported"],
    ),
    (
        "H2  the write-up drops the design limitation",
        OUTCOMES,
        b'            "  Design limitation (protocol section 2): in condition A the "',
        b'            "  In condition A the "',
        [f"{WRITEUP}::test_the_design_limitation_travels_with_the_result"],
    ),
    (
        "R1  a session is recorded with no consent behind it",
        CONSENT,
        b"    if dyad in consented_dyads(records):\n        return\n",
        b"    if True:\n        return\n",
        [
            f"{CONSENT_BEFORE}::test_a_session_without_consent_is_refused",
            f"{CONSENT_BEFORE}::test_the_refusal_names_the_dyad",
            f"{CONSENT_BEFORE}::test_consent_for_another_dyad_is_not_consent_for_this_one",
        ],
    ),
    (
        "R2  a declined consent authorises the session",
        CONSENT,
        b"        if record.agreed and record.version == CONSENT_VERSION\n",
        b"        if True\n",
        [f"{CONSENT_BEFORE}::test_a_declined_consent_authorises_nothing"],
    ),
    (
        "R3  a stale consent version authorises the session",
        CONSENT,
        b"        if self.version != CONSENT_VERSION:\n",
        b"        if False:\n",
        [f"{CONSENT_BEFORE}::test_a_stale_version_authorises_nothing"],
    ),
    (
        "R4  the consent record starts holding participant detail",
        CONSENT,
        b'    agreed: bool\n    at: str = ""\n',
        b'    agreed: bool\n    participant_name: str = ""\n    at: str = ""\n',
        [f"{CONSENT_MINIMAL}::test_the_record_holds_no_participant_detail"],
    ),
    (
        "R5  a verdict resolves nothing",
        OUTCOMES,
        b"        verdict = self.resolutions.get((self.row.dyad, field_name))\n",
        b"        verdict = None\n",
        [
            f"{QUEUE_RESOLVED}::test_a_verdict_resolves_the_field",
            f"{QUEUE_RESOLVED}::test_the_cut_rule_runs_once_the_queue_is_resolved",
            f"{QUEUE_RESOLVED}::test_a_verdict_can_go_the_other_way",
        ],
    ),
    (
        "R6  an unclassified verdict is accepted as an answer",
        SECOND_SCORER,
        b"        if self.verdict == UNCLASSIFIED or self.verdict not in allowed:\n",
        b"        if False:\n",
        [
            f"{VERDICT_RESOLVES}::test_an_unclassified_verdict_is_refused",
            f"{VERDICT_RESOLVES}::test_a_verdict_the_field_cannot_carry_is_refused",
        ],
    ),
    (
        "R7  the facilitator scores their own session",
        SECOND_SCORER,
        b"    if scorer.strip().casefold() == facilitator.strip().casefold():\n",
        b"    if False:\n",
        [
            f"{NOT_SCORING}::test_the_facilitator_cannot_score_their_own_session",
            f"{NOT_SCORING}::test_the_check_survives_a_capitalisation_difference",
        ],
    ),
    (
        "R8  the blinding check passes when no facilitator is named",
        SECOND_SCORER,
        b"    if not facilitator.strip():\n",
        b"    if False:\n",
        [f"{NOT_SCORING}::test_an_unnamed_facilitator_is_refused"],
    ),
    (
        "R9  an anonymous verdict is accepted",
        SECOND_SCORER,
        b"        if not self.scorer.strip():\n",
        b"        if False:\n",
        [f"{NOT_SCORING}::test_an_anonymous_verdict_is_refused"],
    ),
    (
        "R10  the command line records a session with no consent",
        MAIN,
        b"            require_consent(args.dyad, read_consents(consent_file))\n",
        b"            pass\n",
        [
            f"{RECRUIT_CLI}::test_a_session_is_refused_without_consent",
            f"{RECRUIT_CLI}::test_a_declined_consent_still_refuses_the_session",
        ],
    ),
    (
        "R11  the command line takes a verdict from the facilitator",
        MAIN,
        b"            assert_blinded(args.scorer, args.facilitator)\n",
        b"            pass\n",
        [f"{RECRUIT_CLI}::test_a_verdict_from_the_facilitator_is_refused"],
    ),
    (
        # The drifted wording is deliberately not a substring of the frozen
        # sentence: a mutation that shortened it would still be found in the
        # document, and the guard would look like it had teeth.
        "R12  the script drifts from the frozen status statement",
        MAIN,
        b'STATUS_STATEMENT = "The booking link was tried. No one has agreed to '
        b'help yet."\n',
        b'STATUS_STATEMENT = "The booking link was tried. No one has agreed to '
        b'help so far."\n',
        [f"{FROZEN_SCRIPT}::test_the_script_is_the_frozen_protocol_script"],
    ),
    (
        "R13  the application condition is given the spoken statement",
        MAIN,
        b"    if condition == CARD_CONDITION:\n",
        b"    if True:\n",
        [f"{FROZEN_SCRIPT}::test_the_application_condition_does_not"],
    ),
    (
        "R14  the study data becomes committable",
        GITIGNORE,
        b"study/consent.jsonl\n",
        b"",
        [f"{IGNORED}::test_every_study_data_file_is_git_ignored"],
    ),
    # O1 to O9, added 8 October 2026 with the closed recall instrument. Two
    # per field, because the Slice 9 run proved a guard that exercises one
    # field leaves a mutation to the other SURVIVING with the suite green.
    (
        "O1  a distractor action option is scored correct",
        SCORING,
        b"    if letter in DISTRACTOR_ACTION_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n        return False\n",
        b"    if letter in DISTRACTOR_ACTION_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n        return True\n",
        [f"{CLOSED}::test_a_distractor_is_incorrect_not_unclassified"],
    ),
    (
        "O2  a distractor deadline option is scored correct",
        SCORING,
        b"    if letter in DISTRACTOR_DEADLINE_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n        return False\n",
        b"    if letter in DISTRACTOR_DEADLINE_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n        return True\n",
        [f"{CLOSED}::test_a_distractor_is_incorrect_not_unclassified"],
    ),
    (
        "O3  \"I don't know\" stops being scored, on the action field",
        SCORING,
        b"    if letter in DISTRACTOR_ACTION_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n",
        b"    if letter in DISTRACTOR_ACTION_OPTIONS:\n",
        [f"{CLOSED}::test_i_dont_know_is_incorrect_not_unclassified"],
    ),
    (
        "O4  \"I don't know\" stops being scored, on the deadline field",
        SCORING,
        b"    if letter in DISTRACTOR_DEADLINE_OPTIONS or letter == "
        b"DONT_KNOW_OPTION:\n",
        b"    if letter in DISTRACTOR_DEADLINE_OPTIONS:\n",
        [f"{CLOSED}::test_i_dont_know_is_incorrect_not_unclassified"],
    ),
    (
        "O5  an action row with no option recorded is guessed",
        SCORING,
        b"    raise UnclassifiableResponse(\n"
        b"        f\"no action option was recorded, record the words verbatim: "
        b'{option!r}"\n'
        b"    )\n",
        b"    return False\n",
        [
            f"{CLOSED}::test_no_recorded_option_is_refused_not_guessed",
            f"{ROW}::test_words_without_an_option_are_not_a_score",
        ],
    ),
    (
        "O6  a deadline row with no option recorded is guessed",
        SCORING,
        b"    raise UnclassifiableResponse(\n"
        b"        f\"no deadline option was recorded, record the words verbatim: "
        b'{option!r}"\n'
        b"    )\n",
        b"    return False\n",
        [
            f"{CLOSED}::test_no_recorded_option_is_refused_not_guessed",
            f"{ROW}::test_words_without_an_option_are_not_a_score",
        ],
    ),
    (
        "O7  the report counts an unknown as a wrong answer",
        OUTCOMES,
        b"    for row in analysed(rows):\n"
        b"        counts[row.condition][row.both_correct] += 1\n",
        b"    for row in analysed(rows):\n"
        b"        label = INCORRECT if row.both_correct == UNCLASSIFIED "
        b"else row.both_correct\n"
        b"        counts[row.condition][label] += 1\n",
        [
            f"{UNKNOWN}::test_the_breakdown_names_all_three_labels",
            f"{UNKNOWN}::test_the_write_up_reports_three_numbers",
        ],
    ),
    (
        "O8  the sheet renders the label instead of the option chosen",
        OUTCOMES,
        b"                    row.action_option,\n"
        b"                    row.deadline_option,\n",
        b"                    row.action_label,\n"
        b"                    row.deadline_label,\n",
        [
            f"{SHEETTESTS}"
            "::test_the_recall_columns_record_the_option_not_the_words"
        ],
    ),
    (
        "O9  the sheet stops carrying the words in Notes",
        OUTCOMES,
        b"    if row.action_recall.strip():\n",
        b"    if False:\n",
        [f"{SHEETTESTS}::test_the_words_are_rendered_into_notes"],
    ),
    # R15 and R16, added 8 October 2026: the facilitator's script now carries
    # the closed recall options, so drift there is a drift in what a participant
    # is offered.
    (
        "R15  the script stops carrying the closed recall options",
        MAIN,
        b"    for name, options in RECALL_OPTIONS.items():\n",
        b"    for name, options in ():\n",
        [
            f"{FROZEN_SCRIPT}"
            "::test_the_script_carries_the_closed_recall_options"
        ],
    ),
    (
        "R16  an action option on the script drifts from the frozen wording",
        MAIN,
        b'    "Call the fictional nurse line.",\n',
        b'    "Call the nurse line.",\n',
        [f"{FROZEN_SCRIPT}::test_the_script_is_the_frozen_protocol_script"],
    ),
]


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _newline(data: bytes) -> bytes:
    """The dominant newline convention of a file."""
    crlf = data.count(b"\r\n")
    lone = data.count(b"\n") - crlf
    return b"\r\n" if crlf > lone else b"\n"


def _conform(data: bytes, newline: bytes) -> bytes:
    """Rewrite an LF-written anchor or replacement in the target's convention."""
    if newline == b"\r\n":
        return data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return data.replace(b"\r\n", b"\n")


def _purge_bytecode(path: pathlib.Path) -> None:
    """Delete cached bytecode compiled from `path`.

    Python validates a `.pyc` against the source's mtime and size only, never its
    content, so a `.pyc` written while a mutation was live can be imported long
    after the source is restored. Restoring bytes is not enough.
    """
    cache = path.parent / "__pycache__"
    if not cache.is_dir():
        return
    for stale in cache.glob(f"{path.stem}.*.pyc"):
        stale.unlink()


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env=env,
    )


def _progress(stdout: str) -> tuple[int, int]:
    """(tests run, tests failed) from the progress characters, padding stripped."""
    ran = 0
    failed = 0
    for raw in stdout.splitlines():
        line = raw.strip()
        if not re.match(r"^[.FEsxX]+\s*\[", line):
            continue
        progress = line.split("[", 1)[0].rstrip()
        ran += len(progress)
        failed += progress.count("F") + progress.count("E")
    return ran, failed


def _failing_ids(stdout: str) -> list[str]:
    return [
        line.split(" - ")[0].replace("FAILED ", "").strip()
        for line in stdout.splitlines()
        if line.startswith("FAILED ")
    ]


def main() -> int:
    baselines = {name: path.read_bytes() for name, path in TARGETS.items()}
    for name, data in baselines.items():
        crlf = data.count(b"\r\n")
        lone = data.count(b"\n") - crlf
        print(f"[BASE] {name:36} md5={_md5(data)} CRLF={crlf} loneLF={lone}")

    # Pre-flight: every mutation must resolve to at least one test, or a
    # NOT PROVEN would be recorded as if the guard had been tested. This is the
    # check that a rename silently orphans (tasks/lessons.md, 5 October 2026).
    unresolved: list[str] = []
    for label, _target, _anchor, _replacement, selectors in MUTATIONS:
        collected = _run(["--collect-only", *selectors])
        ids = [
            line.strip()
            for line in collected.stdout.splitlines()
            if line.strip().startswith("tests/")
        ]
        if not ids:
            unresolved.append(f"{label}  {selectors}")
    if unresolved:
        print("\n[FAIL] mutations that resolve to no test:")
        for item in unresolved:
            print(f"  {item}")
        return 1
    print(f"[PRE ] all {len(MUTATIONS)} mutations resolve to at least one test\n")

    red = 0
    survived: list[str] = []
    not_proven: list[str] = []

    for label, target, anchor, replacement, selectors in MUTATIONS:
        path = TARGETS[target]
        original = baselines[target]
        newline = _newline(original)
        real_anchor = _conform(anchor, newline)
        real_replacement = _conform(replacement, newline)

        if real_anchor not in original:
            print(f"[FAIL] {label}: anchor not found in {target}")
            not_proven.append(f"{label} (anchor not found)")
            continue
        if original.count(real_anchor) != 1:
            print(f"[FAIL] {label}: anchor appears {original.count(real_anchor)} times")
            not_proven.append(f"{label} (anchor not unique)")
            continue

        path.write_bytes(original.replace(real_anchor, real_replacement))
        try:
            completed = _run(selectors)
        finally:
            path.write_bytes(original)
            _purge_bytecode(path)

        ran, failed = _progress(completed.stdout)
        ids = _failing_ids(completed.stdout)
        print(f"[RUN ] {label}  (ran={ran} failed={failed} exit={completed.returncode})")
        for test_id in ids:
            print(f"       RED: {test_id}")

        if completed.returncode == 0:
            print("       *** SURVIVED: the guard has no teeth ***")
            survived.append(label)
        elif ran == 0 or failed == 0:
            print("       *** NOT PROVEN: nothing actually failed ***")
            not_proven.append(f"{label} (no test failed)")
        else:
            red += 1

    print()
    damaged = [
        name for name, path in TARGETS.items() if path.read_bytes() != baselines[name]
    ]
    if damaged:
        for name in damaged:
            print(f"[FAIL] restore is not byte-identical: {name}")
        return 1
    for name, path in TARGETS.items():
        print(f"[CTRL] {name:36} restored, md5={_md5(path.read_bytes())}")

    print(f"\n=== result: {red} of {len(MUTATIONS)} mutations seen RED ===")
    print(f"    SURVIVED={len(survived)}  NOT PROVEN={len(not_proven)}")
    for item in survived:
        print(f"  SURVIVED: {item}")
    for item in not_proven:
        print(f"  NOT PROVEN: {item}")
    if survived or not_proven:
        return 1
    print("  every mutation was seen RED; every file was restored byte-exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
