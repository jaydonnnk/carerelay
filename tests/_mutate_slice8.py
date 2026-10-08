"""Mutation check for the Slice 8 guards. The fixed card and its protocol.

Run: PYTHONPATH=src python tests/_mutate_slice8.py

Slice 8's deliverables are an HTML artefact and a markdown pre-registration, so the
defects worth injecting are not lines of Python: they are a card that reaches the
application, a card whose wording drifts from the fixture the app renders, a card
that re-imports clinical content, a protocol that stops declaring the design, and a
reporting rule that loses the floor that stops a percentage being drawn from four
dyads. Each mutation below injects one of those and requires **its own** guard to
fail.

Three conventions this harness keeps, each of which cost this project a wrong
answer once:

* **A RED is read from a real test failure, never from the exit code alone.**
  pytest exits 4 for a selector that resolves to nothing, and a harness reading
  "non-zero means RED" reports a kill for a test that never ran
  (`tasks/lessons.md`, 5 October 2026).
* **The count of tests that ran comes off the progress characters.** With `-q`,
  pytest prints no summary line at all for a small selection, so a count scraped
  from it is always zero and would mark every mutation NOT PROVEN.
* **The anchor is matched in the file's own newline convention.** The repository is
  CRLF and one test file is LF, so an anchor written in the wrong convention
  silently fails to apply and a guard that was never touched is recorded as
  SURVIVED.

Every file is restored byte-identically and its cached bytecode purged, because a
`.pyc` compiled while a mutation was live can outlive the restore.

**Repointed 7 October 2026.** Slice 9 lifted the reporting rule and the three
scorers out of `tests/test_study.py` into `src/carerelay/study/`, so eight
mutations now patch their new home instead of the test module. The guards they
must kill are unchanged and still live in `tests/test_study.py`, so every test
node id below is untouched: only the file being broken moved.
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

CARD = "study/fixed-card.html"
PROTOCOL = "study/protocol.md"
TESTS = "tests/test_study.py"
API = "src/carerelay/api.py"

#: Added 7 October 2026. Slice 9 lifted the reporting rule and the three scorers
#: out of `tests/test_study.py` and into the study package, so the mutations that
#: used to land in the test module now have to land where the code went. The test
#: node ids are unchanged: the guards still run from `tests/test_study.py`.
SCORING_MODULE = "src/carerelay/study/scoring.py"
REPORTING_MODULE = "src/carerelay/study/outcomes.py"

TARGETS = {
    CARD: REPO / "study" / "fixed-card.html",
    PROTOCOL: REPO / "study" / "protocol.md",
    TESTS: REPO / "tests" / "test_study.py",
    API: REPO / "src" / "carerelay" / "api.py",
    SCORING_MODULE: REPO / "src" / "carerelay" / "study" / "scoring.py",
    REPORTING_MODULE: REPO / "src" / "carerelay" / "study" / "outcomes.py",
}

STANDALONE = "tests/test_study.py::TestTheCardIsAStandaloneExternalArtefact"
WORDING = "tests/test_study.py::TestTheCardWordingMatchesTheFixture"
OPTIONS = "tests/test_study.py::TestTheCardOffersExactlyThePermittedOptions"
NEUTRAL = "tests/test_study.py::TestTheCardCarriesNoClinicalContent"
DASH = "tests/test_study.py::TestTheCardCarriesNoAuthoredEmDash"
PROTO = "tests/test_study.py::TestTheProtocolIsAPreRegistration"
REPORT = "tests/test_study.py::TestTheSmallSampleReportingRules"
SCORING = "tests/test_study.py::TestResponseScoring"

#: The footer line, used as a safe insertion point by three mutations. It is
#: unique in the card, and inserting a sibling after it cannot disturb the
#: `<li class="line">` sequence the wording guard reads.
FOOTER = b'    <footer class="card-footer">Fixed card, study instrument v1.</footer>'

#: (label, target, anchor, replacement, selectors)
MUTATIONS: list[tuple[str, str, bytes, bytes, list[str]]] = [
    (
        "C1  the card gains a script tag",
        CARD,
        FOOTER,
        FOOTER + b"\n    <script>window.plan = 1;</script>",
        [f"{STANDALONE}::test_the_card_loads_nothing_and_executes_nothing"],
    ),
    (
        "C2  the card gains an external stylesheet",
        CARD,
        b"  <style>\n",
        b'  <link rel="stylesheet" href="/style.css">\n  <style>\n',
        [
            f"{STANDALONE}"
            "::test_the_visible_card_loads_no_resource_and_never_reaches_the_application"
        ],
    ),
    (
        "C3  the card stops carrying its own styles",
        CARD,
        b"  <style>\n",
        b"  <!-- styles moved to an external file -->\n",
        [f"{STANDALONE}::test_the_card_is_self_contained_with_its_own_styles"],
    ),
    (
        "C4  the card gains a second address",
        CARD,
        FOOTER,
        b'    <p class="line"><a href="https://example.invalid/other">Other</a></p>\n'
        + FOOTER,
        [f"{STANDALONE}::test_the_only_address_on_the_card_cannot_resolve"],
    ),
    (
        "C5  line 1 drifts from the fixture wording",
        CARD,
        b'<li class="line">No one has agreed to help yet.</li>',
        b'<li class="line">No one has agreed to help.</li>',
        [f"{WORDING}::test_the_card_reproduces_the_four_patient_lines_in_order"],
    ),
    (
        "C6  the card offers a route the policy does not permit",
        CARD,
        b'<p class="booking" data-route-id="fictional_provider">',
        b'<p class="booking" data-route-id="walk_in">',
        [f"{OPTIONS}::test_the_offered_route_ids_are_the_policy_permitted_set"],
    ),
    (
        "C7  the card gains a clinical marker",
        CARD,
        FOOTER,
        b'    <p class="line">If you get chest pain, go now.</p>\n' + FOOTER,
        [
            f"{NEUTRAL}"
            "::test_the_card_carries_no_symptom_urgency_or_disposition_marker"
        ],
    ),
    (
        "C8  the card gains a numeric clinical threshold",
        CARD,
        FOOTER,
        b'    <p class="line">Take 500 mg twice a day.</p>\n' + FOOTER,
        [f"{NEUTRAL}::test_the_card_carries_no_numeric_clinical_threshold"],
    ),
    (
        "C9  a second em dash is authored onto the card",
        CARD,
        b"<title>Your plan</title>",
        "<title>Your plan \u2014 fixed card</title>".encode("utf-8"),
        [f"{DASH}::test_the_only_em_dash_is_the_one_inside_the_imported_notice"],
    ),
    (
        "P1  the protocol stops declaring between-subjects",
        PROTOCOL,
        b"**Design: between-subjects.**",
        b"**Design: within-subjects.**",
        [f"{PROTO}::test_the_design_is_between_subjects_with_no_crossover"],
    ),
    # Repointed a second time on 8 October 2026. The amendment that closed the
    # two recall questions rewrote section 17's freeze line, so the 7 October
    # anchor no longer exists and the mutation failed as NOT PROVEN rather than
    # SURVIVED. A harness that anchors into moved text goes quietly blind, so
    # the anchor moved with the sentence.
    (
        "P2  the protocol stops freezing itself before the first dyad",
        PROTOCOL,
        b"**Frozen on 7 October 2026, before the first dyad. Amended twice, still "
        b"before the\n"
        b"first dyad: section 13 on 7 October 2026, and sections 5 to 7, 10 and 11 "
        b"on\n"
        b"8 October 2026. Both amendments are recorded below.**",
        b"**To be confirmed.**",
        [f"{PROTO}::test_the_protocol_freezes_itself_before_the_first_dyad"],
    ),
    (
        "T1  the reporting rule loses its ten-participant floor",
        REPORTING_MODULE,
        b"    if total >= MIN_PARTICIPANTS_FOR_PERCENTAGES:\n",
        b"    if total >= 0:\n",
        [f"{REPORT}::test_no_percentage_appears_below_ten_participants"],
    ),
    (
        "T2  the no-claim rule loses its three-dyad floor",
        REPORTING_MODULE,
        b"    return min(counts.values()) >= MIN_DYADS_PER_CONDITION\n",
        b"    return True\n",
        [
            f"{REPORT}::test_two_dyads_in_one_condition_supports_no_claim",
            f"{REPORT}::test_an_empty_condition_supports_no_claim",
        ],
    ),
    (
        # Repointed 7 October 2026: `score_deadline_recall` became three-way, so
        # the old two-line anchor no longer exists. The mutation is the same one
        # in meaning, a deadline the fixture resolves to a different instant
        # scored as correct, and it now lands on the case-2 branch.
        "T3  the deadline scorer stops rejecting a different instant",
        SCORING_MODULE,
        b"    if normalised in {rules.normalise(form) for form in "
        b"DIFFERENT_DEADLINE_FORMS}:\n        return False\n",
        b"    if normalised in {rules.normalise(form) for form in "
        b"DIFFERENT_DEADLINE_FORMS}:\n        return True\n",
        [f"{SCORING}::test_a_wrong_deadline_is_incorrect_not_uncertain"],
    ),
    (
        "T4  an unclassifiable answer is guessed as a no",
        SCORING_MODULE,
        b'    raise UnclassifiableResponse(f"unclassifiable answer, record verbatim: '
        b'{answer!r}")\n',
        b"    return False\n",
        [f"{SCORING}::test_an_unclassifiable_answer_is_refused_not_guessed"],
    ),
    # Added 7 October 2026, one per finding in
    # docs/reviews/slice8-adversarial-review.md. B1 takes three because the
    # finding is one defect with three behaviours: derive the vocabulary, refuse
    # an unclassifiable action, refuse an unclassifiable deadline.
    (
        "B1a the scorer stops withdrawing the fixture's action vocabulary",
        SCORING_MODULE,
        b"    sorted(set(FIXTURE_ACTION_FORMS) | {fixture.ACTION_TEXT})",
        b"    sorted(set() | {fixture.ACTION_TEXT})",
        [
            f"{SCORING}",
            "-k",
            "test_every_action_alias_the_application_accepts_scores_correct",
        ],
    ),
    (
        "B1b the scorer stops withdrawing the fixture's deadline vocabulary",
        SCORING_MODULE,
        b"        set(FIXTURE_DEADLINE_FORMS)",
        b"        set()",
        [
            f"{SCORING}",
            "-k",
            "test_every_deadline_form_the_application_resolves_to_the_keyed_instant_scores_correct",
        ],
    ),
    (
        "B1c the action scorer guesses on an unclassifiable action",
        SCORING_MODULE,
        b"    raise UnclassifiableResponse(\n"
        b'        f"unclassifiable restated action, record verbatim: {restated!r}"\n'
        b"    )\n",
        b"    return False\n",
        [f"{SCORING}::test_an_unclassifiable_action_is_refused_not_guessed"],
    ),
    (
        "B1d the deadline scorer guesses on an unclassifiable instant",
        SCORING_MODULE,
        b"    raise UnclassifiableResponse(\n"
        b'        f"unclassifiable restated deadline, record verbatim: {restated!r}"\n'
        b"    )\n",
        b"    return False\n",
        [f"{SCORING}::test_an_unclassifiable_deadline_is_refused_not_guessed"],
    ),
    # S1 in both directions: the heading guard must fail whether the rename
    # happens in the application or on the card. It used to fail only on the card.
    (
        "S1a the application renames its heading",
        API,
        b'    <h1 class="screen-title">Your plan</h1>',
        b'    <h1 class="screen-title">Your Care Plan</h1>',
        [f"{WORDING}::test_the_card_heading_is_the_heading_the_application_renders"],
    ),
    (
        "S1b the card renames its heading",
        CARD,
        b'<h1 class="card-title">Your plan</h1>',
        b'<h1 class="card-title">Your Care Plan</h1>',
        [f"{WORDING}::test_the_card_heading_is_the_heading_the_application_renders"],
    ),
    (
        "S2a the javascript: pattern is withdrawn",
        TESTS,
        b'    r"javascript\\s*:",\n',
        b"",
        [f"{STANDALONE}::test_a_javascript_uri_is_detectable_on_a_card_shaped_surface"],
    ),
    (
        "S2b the inline event handler pattern is withdrawn",
        TESTS,
        b'    r"\\bon[a-z]+\\s*=",\n',
        b"",
        [
            f"{STANDALONE}"
            "::test_an_inline_event_handler_is_detectable_on_a_card_shaped_surface"
        ],
    ),
    (
        "N1  a threshold leak fires the threshold guard alone",
        CARD,
        FOOTER,
        b'    <p class="line">Take 500 mg twice a day.</p>\n' + FOOTER,
        [
            f"{NEUTRAL}::test_the_card_carries_no_symptom_urgency_or_disposition_marker",
            f"{NEUTRAL}::test_the_card_carries_no_numeric_clinical_threshold",
        ],
    ),
    (
        "N3  the css url() pattern is withdrawn",
        TESTS,
        b'    r"url\\s*\\(",\n',
        b"",
        [
            f"{STANDALONE}"
            "::test_a_css_url_resource_is_detectable_on_a_card_shaped_surface"
        ],
    ),
    (
        "N5  the card comment goes back to claiming 'anywhere'",
        CARD,
        b"    anywhere a participant can see. `tests/test_study.py` fails if any of that",
        b"    anywhere. `tests/test_study.py` fails if any of that",
        [
            f"{STANDALONE}"
            "::test_the_card_comment_claims_only_the_participant_visible_surface"
        ],
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


def _progress(stdout: str) -> tuple[int, int]:
    """(tests run, tests failed) from the progress characters.

    `-q` prints no summary line for a small selection, so this is the only count
    that is always available.

    pytest right-pads the progress field to a fixed width, so a one-test
    selection prints one dot followed by 72 spaces and `ran` used to report 73
    for a single test (finding N2 of the Slice 8 review). The padding is
    stripped before counting, which also makes the `ran == 0` branch below
    reachable in principle rather than dead. The verdict still keys on `failed`
    and the exit code; `ran` is display only.
    """
    ran = 0
    failed = 0
    for raw in stdout.splitlines():
        line = raw.strip()
        if not re.match(r"^[.FEsxX]+\s*\[", line):
            continue
        progress = line.split("[", 1)[0].rstrip()
        ran += len(progress)
        failed += sum(1 for char in progress if char in "FE")
    return ran, failed


def _run(selectors: list[str]) -> subprocess.CompletedProcess[str]:
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env["PYTHONPATH"] = "src"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [PYTHON, "-m", "pytest", "-o", "addopts=", "-q", *selectors],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


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
        print(f"[BASE] {name:24} md5={_md5(data)} CRLF={crlf} loneLF={lone}")

    # Pre-flight: every mutation must resolve to at least one test, or a
    # NOT PROVEN would be recorded as if the guard had been tested. This is the
    # check that a rename silently orphans (tasks/lessons.md, 5 October 2026).
    #
    # It is run once per mutation rather than once for all of them, because two
    # of the new guards are parametrised and are selected by a class node id plus
    # a `-k` pattern. A single collect run carrying every `-k` pattern at once
    # would intersect them and resolve to nothing at all.
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
        print(f"[CTRL] {name:24} restored, md5={_md5(path.read_bytes())}")

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
