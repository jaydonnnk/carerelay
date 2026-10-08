"""The baseline instrument: the fixed card and its pre-registration. Slice 8.

Constraint **C1** is the reason this slice exists: the kill test must run before
the thing it might kill is finished. The card is the comparator Gate B measures
CareRelay against, so it is built and frozen here, before the Closure Contract
build in Slice 10.

Two artefacts are under test, and neither is code:

* `study/fixed-card.html` is the external artefact handed to a participant. It is
  deliberately **not** an in-app arm, so the guards below check that it loads
  nothing, executes nothing and never reaches the application, and that every word
  on it is a mirror of the fixture rather than a second source for it.
* `study/protocol.md` is the pre-registration. Its guards check that the
  allocation, the scripted question, the answer key, the cut rule and the
  small-sample reporting rules are stated and frozen **before the first dyad**,
  because a kill test whose rules are chosen after the results is not a test.

**Why the parity guards are the load-bearing ones.** The card duplicates fixture
wording by hand, because a card generated from the fixture would agree with it by
construction and could not be seen to drift. So the duplication is the risk, and
these tests are the control: change a line on the card and the card stops matching
the fixture the application renders.

**Where the scoring rules live now.** Slice 9 lifted `render_outcome_report`,
`hcd_claim_supported` and the three scorers out of this module and into
`carerelay.study`, because a rule that exists only inside a test cannot score a
real response. They are imported back in, so the guards here read the same
values and the move changed no assertion.

**The stated limit of the content scan.** `scan_clinical_content` catches a named
marker from a fixed vocabulary, and a number followed by a clinical unit. It does
not catch a clinical statement phrased with none of those words. It is a guard
against the specific regression the Option A decision removed, which is a
comparator that re-imports clinical content, and it is not a classifier.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.demo import fixture  # noqa: E402
from carerelay.study.outcomes import (  # noqa: E402
    MIN_DYADS_PER_CONDITION,
    MIN_PARTICIPANTS_FOR_PERCENTAGES,
    hcd_claim_supported,
    render_outcome_report,
)
from carerelay.study.scoring import (  # noqa: E402
    DIFFERENT_ACTION_FORMS,
    DIFFERENT_DEADLINE_FORMS,
    FIXTURE_ACTION_FORMS,
    FIXTURE_DEADLINE_FORMS,
    PROTOCOL_DEADLINE_FORMS,
    UnclassifiableResponse,
    score_action_recall,
    score_deadline_recall,
    score_false_completion,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CARD_PATH = REPO_ROOT / "study" / "fixed-card.html"
PROTOCOL_PATH = REPO_ROOT / "study" / "protocol.md"
API_PATH = REPO_ROOT / "src" / "carerelay" / "api.py"

CARD_INSTRUMENT = "fixed-card-v1"


def _application_heading() -> str:
    """The heading the application's patient screen renders, read from `api.py`.

    Finding S1 of the Slice 8 review: the expected heading used to be a constant
    declared in this file, so renaming the heading in `api.py` left the parity
    guard green while the card and the application quietly disagreed. The value
    is therefore read from the application's own source, so a rename on **either**
    side now fails. Exactly one `<h1>` is required, because the derivation is
    only meaningful while the patient screen has exactly one heading.
    """
    headings = re.findall(
        r"<h1[^>]*>(.*?)</h1>", API_PATH.read_text(encoding="utf-8"), re.DOTALL
    )
    if len(headings) != 1:
        raise AssertionError(f"api.py must render exactly one <h1>: {headings}")
    return headings[0].strip()


#: The heading the card must carry. Derived from the application, never declared
#: here, for the reason in `_application_heading`.
CARD_HEADING = _application_heading()

#: Anything that loads a resource, executes, or wires the card to the application.
#: The card is an external artefact, so there is no legitimate instance of any of
#: these anywhere in the file, comments included. Checked against the raw file.
EXECUTABLE_TAG_PATTERNS: tuple[str, ...] = (
    r"<script\b",
    r"<iframe\b",
    r"<embed\b",
    r"<object\b",
    r"<applet\b",
)

#: Resource loads and application wiring, checked against the participant-visible
#: surface. The comment block is repository-facing maintenance prose that cannot
#: execute and is not printed, so it is removed first; the executable tags above
#: are checked separately and without that exception.
#:
#: The last three are script-bearing needles, added after findings S2 and N3 of
#: the Slice 8 review proved this guard narrower than its own claim: a
#: `javascript:` URI, an inline `on*` handler and a CSS `url()` all passed while
#: the class docstring below promised a card that "runs script" would be caught.
#: `url\s*\(` is here because the address counter below matches `https?://` only,
#: so the protocol-relative form of a CSS resource was invisible to it as well.
RESOURCE_AND_WIRING_PATTERNS: tuple[str, ...] = (
    r"<link\b[^>]*\bhref\s*=",
    r"<img\b[^>]*\bsrc\s*=",
    r"<source\b",
    r"<video\b",
    r"<audio\b",
    r"@import\b",
    r"\bcarerelay\b",
    r"/api/",
    r"\blocalhost\b",
    r"\b127\.0\.0\.1\b",
    r"\bfetch\s*\(",
    r"\bxmlhttprequest\b",
    r"\bvercel\b",
    r"\bonrender\b",
    r"\buvicorn\b",
    r"javascript\s*:",
    r"\bon[a-z]+\s*=",
    r"url\s*\(",
)

#: The only address a card may carry is the direct booking link, and it must sit
#: under the reserved `.invalid` top-level domain (RFC 2606), which cannot resolve.
BOOKING_HOST_PREFIX = "https://booking.invalid/"

#: Clinical content, by vocabulary. Option A made the comparator content-neutral:
#: it names no symptom, urgency or disposition, and asserts no clinical claim. The
#: notice is the one permitted exception, because it negates a claim rather than
#: making one, and it is asserted separately and exactly once.
CLINICAL_SYMPTOM_MARKERS: tuple[str, ...] = (
    "chest pain",
    "shortness of breath",
    "cannot breathe",
    "difficulty breathing",
    "breathless",
    "wheez",
    "palpitation",
    "fever",
    "cough",
    "bleeding",
    "dizzy",
    "dizziness",
    "nausea",
    "vomiting",
    "rash",
    "swelling",
    "confusion",
    "fainted",
    "unconscious",
    "stroke",
    "seizure",
    "sore",
    "pain",
    "infection",
)

CLINICAL_URGENCY_MARKERS: tuple[str, ...] = (
    "emergency",
    "urgent",
    "immediately",
    "life-threatening",
    "life threatening",
    "as soon as possible",
    "ambulance",
    "hospital",
    "a&e",
    "casualty",
    "go now",
    "995",
    "999",
    "111",
)

CLINICAL_DISPOSITION_MARKERS: tuple[str, ...] = (
    "diagnos",
    "prescription",
    "prescribed",
    "dosage",
    "dose",
    "antibiotic",
    "paracetamol",
    "ibuprofen",
    "blood pressure",
    "temperature",
    "oxygen",
    "triage",
    "clinical advice",
    "medical advice",
    "treatment",
    "medication",
)

CLINICAL_MARKERS: tuple[str, ...] = (
    CLINICAL_SYMPTOM_MARKERS
    + CLINICAL_URGENCY_MARKERS
    + CLINICAL_DISPOSITION_MARKERS
)

#: A number carrying a clinical unit. Deliberately not a bare number, because the
#: card legitimately says "6pm today".
CLINICAL_THRESHOLD_PATTERN = re.compile(
    r"\d+\s*(?:mg|mcg|ml|mmhg|mmol|bpm|°c|celsius|degrees)",
    re.IGNORECASE,
)

#: The scoring vocabularies and thresholds that used to be declared here now
#: live in `carerelay.study`, where Slice 9 lifted them: `scoring` owns the
#: vocabularies, `outcomes` owns the two reporting thresholds. They are
#: imported at the top of this module, so every guard below still reads
#: exactly the value it read before the move.


# ---------------------------------------------------------------------------
# Reading the artefacts
# ---------------------------------------------------------------------------


def _card_raw() -> str:
    """The card as it is on disk, comments included."""
    return CARD_PATH.read_text(encoding="utf-8")


def _card_visible() -> str:
    """The participant-visible surface: the card with HTML comments removed.

    The comment block documents why the card is shaped the way it is, for whoever
    maintains it. It cannot execute and it is not printed, so the surface a
    participant sees is the file without it. Anything that loads or executes is
    checked against the raw file instead, with no such exception.
    """
    return re.sub(r"<!--.*?-->", "", _card_raw(), flags=re.DOTALL)


def _card_body_without_notice() -> str:
    """The visible surface with the verbatim notice removed.

    The notice is the single place a clinical phrase may appear, because it
    negates a claim. Removing it here means the content scan has **no** exception:
    a marker anywhere else on the card is a finding, and the notice itself is
    pinned by its own test.
    """
    return _card_visible().replace(fixture.FIXTURE_LABEL, "")


def _protocol() -> str:
    """The protocol with runs of whitespace collapsed to one space.

    The document is wrapped to a readable column, so a phrase can straddle a
    newline. Asserting against the raw text would make these guards fail on a
    reformat rather than on a change of meaning, which is the wrong failure.
    """
    return " ".join(PROTOCOL_PATH.read_text(encoding="utf-8").split())


def _card_shell(inner: str) -> str:
    """A minimal card-shaped surface for a scanner self-test.

    Deliberately built **without** the notice. A self-test that injected a marker
    into a shell already carrying the notice would pass for any marker the notice
    happens to contain, which is a test passing for the wrong reason.
    """
    return (
        '<main class="card">'
        f'<h1 class="card-title">{CARD_HEADING}</h1>'
        f"{inner}"
        '<footer class="card-footer">Fixed card, study instrument v1.</footer>'
        "</main>"
    )


def scan_clinical_markers(payload: str) -> list[str]:
    """Return the symptom, urgency and disposition markers in a payload.

    Split out of `scan_clinical_content` for finding N1 of the Slice 8 review:
    the marker guard and the threshold guard had byte-identical bodies, so a leak
    could not be attributed to either one. Each guard now scans its own
    vocabulary, and `scan_clinical_content` stays the combined scan the
    self-tests below use.
    """
    lowered = payload.casefold()
    return sorted({marker for marker in CLINICAL_MARKERS if marker in lowered})


def scan_clinical_content(payload: str) -> list[str]:
    """Return every clinical finding in a payload: markers and thresholds both.

    Reports findings rather than cleaning them, so a leak fails the build instead
    of being quietly removed. Its stated limit is in the module docstring.
    """
    found = scan_clinical_markers(payload)
    found.extend(
        f"threshold:{match}" for match in CLINICAL_THRESHOLD_PATTERN.findall(payload)
    )
    return sorted(set(found))


# The five functions that used to be defined here now live in
# `carerelay.study`: `render_outcome_report` and `hcd_claim_supported` in
# `outcomes`, and the three scorers in `scoring`. Slice 9 lifted them,
# because a rule that exists only inside a test cannot score a real
# response. They are imported at the top of this module, unchanged in
# behaviour, and every guard below tests them where it always did.


# ---------------------------------------------------------------------------
# The card is an external artefact, not an in-app arm
# ---------------------------------------------------------------------------


class TestTheCardIsAStandaloneExternalArtefact:
    def test_the_card_exists(self) -> None:
        assert CARD_PATH.exists(), f"the fixed card is missing: {CARD_PATH}"

    def test_the_card_loads_nothing_and_executes_nothing(self) -> None:
        """Checked against the raw file: there is no legitimate exception.

        A card that runs script, frames content or embeds an object is an in-app
        arm wearing paper, which is the design the Gate 2 D6 backtrack removed.
        """
        raw = _card_raw().casefold()
        for pattern in EXECUTABLE_TAG_PATTERNS:
            assert not re.search(pattern, raw), f"executable markup on the card: {pattern}"

    def test_the_visible_card_loads_no_resource_and_never_reaches_the_application(
        self,
    ) -> None:
        visible = _card_visible()
        for pattern in RESOURCE_AND_WIRING_PATTERNS:
            assert not re.search(pattern, visible, re.IGNORECASE), pattern

    def test_a_javascript_uri_is_detectable_on_a_card_shaped_surface(self) -> None:
        """Finding S2: `<a href="javascript:window.close()">` used to pass.

        `AGENTS.md` section 6: an absence guard needs a scanner self-test that
        injects the needle into a representative serialized surface and requires
        detection. Without one, the pattern set can shrink and the guard above
        stays green on a card that executes.
        """
        injected = _card_shell(
            '<p class="line"><a href="javascript:window.close()">Close</a></p>'
        )
        hits = [
            pattern
            for pattern in RESOURCE_AND_WIRING_PATTERNS
            if re.search(pattern, injected, re.IGNORECASE)
        ]
        assert hits, injected

    def test_an_inline_event_handler_is_detectable_on_a_card_shaped_surface(
        self,
    ) -> None:
        """Finding S2: `<img alt="x" onerror="alert(1)">` used to pass."""
        injected = _card_shell('<p class="line"><img alt="x" onerror="alert(1)"></p>')
        hits = [
            pattern
            for pattern in RESOURCE_AND_WIRING_PATTERNS
            if re.search(pattern, injected, re.IGNORECASE)
        ]
        assert hits, injected

    def test_a_css_url_resource_is_detectable_on_a_card_shaped_surface(self) -> None:
        """Finding N3: `url(//evil.example/pixel.png)` used to pass.

        The protocol-relative form is the one the address counter below cannot
        see, because it matches `https?://` only.
        """
        injected = _card_shell(
            '<p class="line" style="background-image: url(//evil.example/pixel.png)">'
            "x</p>"
        )
        hits = [
            pattern
            for pattern in RESOURCE_AND_WIRING_PATTERNS
            if re.search(pattern, injected, re.IGNORECASE)
        ]
        assert hits, injected

    def test_the_card_comment_claims_only_the_participant_visible_surface(self) -> None:
        """Finding N5: the comment claimed "no mention of the application anywhere".

        That was literally false of the file, whose own comment block names the
        application twice. What is true, and what the guards here actually check,
        is that no participant can see it. The comment is the maintenance
        contract for this file, so the claim is now the narrower one and is
        pinned rather than left to drift back.
        """
        collapsed = " ".join(_card_raw().split())
        assert (
            "no mention of the application anywhere a participant can see."
            in collapsed
        )
        assert "no mention of the application anywhere." not in collapsed

    def test_the_card_is_self_contained_with_its_own_styles(self) -> None:
        visible = _card_visible()
        assert "<style" in visible.casefold(), "the card must carry its own styles"

    def test_the_only_address_on_the_card_cannot_resolve(self) -> None:
        """One link, and its host is under the reserved `.invalid` domain.

        A card that named a real booking service would be a claim the fixture is
        not entitled to make, and a card with two addresses would offer a route
        the policy does not permit.
        """
        addresses = re.findall(r"https?://[^\s\"'<>)]+", _card_visible())
        assert len(addresses) == 1, addresses
        assert addresses[0].startswith(BOOKING_HOST_PREFIX), addresses[0]

    def test_the_control_the_card_is_not_empty(self) -> None:
        """Every guard above passes trivially on an empty file.

        This is the control that stops the class of defect where a check is green
        because it scanned nothing at all.
        """
        visible = _card_visible()
        assert fixture.FIXTURE_LABEL in visible
        assert len(visible) > 500


# ---------------------------------------------------------------------------
# Wording parity with the fixture
# ---------------------------------------------------------------------------


class TestTheCardWordingMatchesTheFixture:
    def test_the_card_reproduces_the_four_patient_lines_in_order(self) -> None:
        rendered = re.findall(
            r'<li class="line"[^>]*>(.*?)</li>', _card_visible(), re.DOTALL
        )
        assert [text.strip() for text in rendered] == list(fixture.demo_lines().as_tuple())

    def test_the_card_carries_the_notice_verbatim(self) -> None:
        assert fixture.FIXTURE_LABEL in _card_visible()

    def test_the_card_carries_the_action_wording_verbatim(self) -> None:
        assert fixture.ACTION_TEXT in _card_visible()

    def test_the_card_carries_the_deadline_and_the_route_wording_verbatim(self) -> None:
        visible = _card_visible()
        assert fixture.DEADLINE_DISPLAY in visible
        assert fixture.FALLBACK_ROUTE_TEXT in visible

    def test_the_application_renders_exactly_one_heading(self) -> None:
        """The precondition of the derived heading in `_application_heading`.

        `CARD_HEADING` is read from the one `<h1>` in `api.py`. If the patient
        screen ever renders two, the derivation silently takes the first and the
        parity claim becomes ambiguous, so the count is asserted outright.
        """
        source = API_PATH.read_text(encoding="utf-8")
        assert len(re.findall(r"<h1[^>]*>", source)) == 1

    def test_the_card_heading_is_the_heading_the_application_renders(self) -> None:
        """Finding S1: this guard is now bound to `api.py`, not to a constant.

        The expected value is derived at import from the application's own
        patient screen, so a rename on either side fails it. Both directions are
        mutation-proven in `tests/_mutate_slice8.py` (S1a renames the heading in
        `api.py`, S1b renames it on the card) and both go RED.
        """
        assert CARD_HEADING, "api.py renders no heading, so there is nothing to match"
        headings = re.findall(r"<h1[^>]*>(.*?)</h1>", _card_visible(), re.DOTALL)
        assert [heading.strip() for heading in headings] == [CARD_HEADING]


# ---------------------------------------------------------------------------
# Options parity with the policy
# ---------------------------------------------------------------------------


class TestTheCardOffersExactlyThePermittedOptions:
    def test_the_offered_route_ids_are_the_policy_permitted_set(self) -> None:
        """Set equality, not containment.

        A card offering a route the policy does not permit is a second, wider
        source of options, and containment would not see it.
        """
        offered = set(re.findall(r'data-route-id="([^"]+)"', _card_visible()))
        assert offered == set(fixture.policy().permitted_route_ids)

    def test_each_offered_route_is_named_with_its_policy_display_text(self) -> None:
        display = fixture.policy_text().route_display_by_id
        visible = _card_visible()
        for route_id in fixture.policy().permitted_route_ids:
            assert display[route_id] in visible, route_id


# ---------------------------------------------------------------------------
# Content neutrality
# ---------------------------------------------------------------------------


class TestTheCardCarriesNoClinicalContent:
    def test_the_notice_appears_exactly_once(self) -> None:
        assert _card_visible().count(fixture.FIXTURE_LABEL) == 1

    def test_the_card_carries_no_symptom_urgency_or_disposition_marker(self) -> None:
        """Finding N1: this scans the markers only, never the thresholds.

        The threshold guard beside it scans the threshold pattern only, so a
        marker-only leak fails this and a threshold-only leak fails that one, and
        the two are attributable. Before the fix both bodies were identical, so a
        leak failed both and neither identified it.
        """
        assert scan_clinical_markers(_card_body_without_notice()) == []

    def test_the_card_carries_no_numeric_clinical_threshold(self) -> None:
        """Finding N1: this used to be a byte-identical copy of the guard above.

        Two names, one body, so a marker-only leak and a threshold-only leak were
        indistinguishable by which test failed, and mutation C8 proved the pair
        was one assertion tested twice. It now scans the threshold pattern only,
        so `C8` fails this one alone and `C7` fails the marker one alone.
        """
        assert CLINICAL_THRESHOLD_PATTERN.findall(_card_body_without_notice()) == []

    @pytest.mark.parametrize("marker", CLINICAL_MARKERS)
    def test_every_marker_is_detectable_in_a_card_shaped_surface(self, marker: str) -> None:
        """`AGENTS.md` section 6: an inventory describes structure, not coverage.

        Each marker is injected on its own, so one working detector cannot cover
        for a missing one, and the shell carries no notice, so a marker that the
        notice happens to contain cannot pass on the notice's text.
        """
        injected = _card_shell(f'<li class="line">{marker}</li>')
        assert marker in scan_clinical_content(injected), marker

    def test_a_numeric_threshold_is_detectable(self) -> None:
        assert scan_clinical_content(_card_shell("<p>Take 500 mg twice a day.</p>"))

    def test_the_control_the_approved_wording_is_not_a_finding(self) -> None:
        """The control: the scan must not fire on the fixture's own wording."""
        assert scan_clinical_content(fixture.ACTION_TEXT) == []
        assert scan_clinical_content(fixture.FALLBACK_ROUTE_TEXT) == []
        assert scan_clinical_content(fixture.DEADLINE_DISPLAY) == []
        for line in fixture.demo_lines().as_tuple():
            assert scan_clinical_content(line) == [], line


class TestTheCardCarriesNoAuthoredEmDash:
    def test_the_only_em_dash_is_the_one_inside_the_imported_notice(self) -> None:
        """The notice is imported text, and it is the only source of a dash.

        `AGENTS.md` section 6 forbids the em dash in new writing. The notice is a
        verbatim import of an existing constant, so it is kept and counted rather
        than rewritten, and nothing else on the card may carry one.
        """
        raw = _card_raw()
        assert "\u2014" in fixture.FIXTURE_LABEL, "the notice no longer carries the dash"
        assert raw.count("\u2014") == 1, raw.count("\u2014")
        assert fixture.FIXTURE_LABEL in raw


# ---------------------------------------------------------------------------
# The protocol is a pre-registration
# ---------------------------------------------------------------------------


class TestTheProtocolIsAPreRegistration:
    def test_the_protocol_exists(self) -> None:
        assert PROTOCOL_PATH.exists(), f"the protocol is missing: {PROTOCOL_PATH}"

    def test_the_design_is_between_subjects_with_no_crossover(self) -> None:
        """The declaration, not the word.

        The first version asserted that the phrase "between-subjects" appeared
        somewhere in the document, and mutation P1 of `tests/_mutate_slice8.py`
        survived it: the phrase also appears in the rationale paragraph below the
        declaration, so flipping the declaration to "within-subjects" left the
        guard green. A guard that reads a word is not a guard that reads the
        decision, so this one pins the declaration and refuses the alternative.
        """
        text = _protocol()
        assert "**Design: between-subjects.**" in text
        assert "**Design: within-subjects.**" not in text
        assert "no crossover" in text.casefold()

    def test_the_card_condition_is_external(self) -> None:
        text = _protocol().casefold()
        assert "outside the application" in text
        assert "no application screen" in text

    def test_the_scripted_statement_and_question_are_frozen_verbatim(self) -> None:
        text = _protocol()
        assert "The booking link was tried. No one has agreed to help yet." in text
        assert "Has care been arranged for you?" in text

    def test_the_allocation_order_is_frozen(self) -> None:
        assert (
            "| Condition | A | B | A | B | A | B | A | B | A | B | A | B |"
            in _protocol()
        )

    def test_the_answer_key_is_the_fixture_and_is_stated(self) -> None:
        text = _protocol()
        for value in (
            fixture.ACTION_TEXT,
            fixture.DEADLINE_DISPLAY,
            fixture.FALLBACK_ROUTE_TEXT,
        ):
            assert value in text, value

    def test_the_cut_rule_is_pre_registered_with_all_three_conditions(self) -> None:
        text = _protocol().casefold()
        assert "equal action and deadline recall with lower burden" in text
        assert "any critical correct statement is flagged as a mismatch" in text
        assert "emergency guidance is delayed by read-back" in text

    def test_the_protocol_freezes_itself_before_the_first_dyad(self) -> None:
        text = _protocol()
        assert "Frozen on" in text
        assert "before the first dyad" in text
        assert "invalidates the pre-registration" in text

    def test_the_protocol_names_the_card_instrument_version(self) -> None:
        """The card and the protocol are bound to one another by the version.

        A change to either without the other is the drift this pins.
        """
        assert CARD_INSTRUMENT in _protocol()
        assert f'data-instrument="{CARD_INSTRUMENT}"' in _card_visible()

    def test_research_consent_is_separate_from_clinical_consent(self) -> None:
        assert "separate from the clinical `consents` table" in _protocol().casefold()

    def test_the_minimum_sample_and_the_no_claim_rule_are_stated(self) -> None:
        text = _protocol().casefold()
        assert "minimum: 3 dyads per condition" in text
        assert "no human-centred validation claim" in text

    def test_the_honest_claim_boundary_is_stated(self) -> None:
        text = _protocol().casefold()
        assert "does not validate clinical advice" in text
        assert "directional decision, not efficacy evidence" in text

    def test_the_protocol_carries_no_em_dash(self) -> None:
        assert "\u2014" not in _protocol()


# ---------------------------------------------------------------------------
# Response scoring and the small-sample reporting rules
# ---------------------------------------------------------------------------


class TestResponseScoring:
    def test_a_yes_answer_is_a_false_completion(self) -> None:
        assert score_false_completion("Yes") is True

    def test_a_no_answer_is_not_a_false_completion(self) -> None:
        assert score_false_completion("no") is False

    def test_an_unclassifiable_answer_is_refused_not_guessed(self) -> None:
        with pytest.raises(ValueError):
            score_false_completion("I think someone called them")

    def test_a_correct_action_is_scored_correct(self) -> None:
        assert score_action_recall(fixture.ACTION_TEXT) is True

    @pytest.mark.parametrize("alias", FIXTURE_ACTION_FORMS)
    def test_every_action_alias_the_application_accepts_scores_correct(
        self, alias: str
    ) -> None:
        """Case 1 for actions, and the deflation finding B1 named.

        Condition A participants restate the plan to the application, which
        resolves every one of these aliases to the keyed action. Scoring any of
        them incorrect charges condition A for a correct answer, and condition A
        is the arm the cut rule can kill.
        """
        assert score_action_recall(alias) is True, alias

    def test_no_fixture_alias_resolves_to_a_different_action(self) -> None:
        """Case 2 for actions, which has no vocabulary today.

        `DIFFERENT_ACTION_FORMS` is derived, not omitted, and it is empty because
        the fixture carries aliases for the keyed action only. No alias is
        invented to fill it. This guard is what makes the emptiness a measured
        fact rather than an assumption: the day a second permitted action gains
        an alias, this goes RED and Slice 9 has to say whether that alias is a
        known-wrong value or a second correct one.
        """
        assert DIFFERENT_ACTION_FORMS == ()
        assert set(fixture.policy().action_aliases.values()) == {fixture.ACTION_ID}

    def test_an_unclassifiable_action_is_refused_not_guessed(self) -> None:
        """Case 3 for actions.

        **Renamed from `test_a_different_action_is_scored_incorrect`**, which
        asserted `score_action_recall("stay at home and rest") is False`. That
        input is not a form the fixture resolves at all, so under the corrected
        three-way semantics it is unclassifiable: the scorer must refuse it for
        the second scorer, not record a guess as a score. Keeping the old name
        would have left the name claiming a behaviour the body no longer has.
        """
        with pytest.raises(ValueError):
            score_action_recall("stay at home and rest")

    def test_an_accepted_deadline_form_is_scored_correct(self) -> None:
        assert score_deadline_recall("6pm") is True

    @pytest.mark.parametrize("form", FIXTURE_DEADLINE_FORMS)
    def test_every_deadline_form_the_application_resolves_to_the_keyed_instant_scores_correct(
        self, form: str
    ) -> None:
        """Case 1 for deadlines. Four of these six used to score incorrect."""
        assert score_deadline_recall(form) is True, form

    @pytest.mark.parametrize("form", DIFFERENT_DEADLINE_FORMS)
    def test_every_deadline_form_the_application_resolves_to_another_instant_is_incorrect(
        self, form: str
    ) -> None:
        """Case 2 for deadlines: recognised, and wrong."""
        assert score_deadline_recall(form) is False, form

    def test_a_wrong_deadline_is_incorrect_not_uncertain(self) -> None:
        """Kill condition K1 in miniature: a wrong value is not ambiguity.

        The fixture knows 20:00 is a different instant from 18:00, so it must be
        scored incorrect. Scoring it uncertain is how a critical correct statement
        ends up repaired into a wrong one. Under the corrected semantics this
        stays case 2: the form is recognised and it is wrong, so the scorer
        answers rather than refusing.
        """
        assert score_deadline_recall("today before 8pm") is False

    def test_an_unclassifiable_deadline_is_refused_not_guessed(self) -> None:
        """Case 3 for deadlines: an instant the fixture cannot resolve at all."""
        with pytest.raises(ValueError):
            score_deadline_recall("sometime next week")

    def test_the_protocol_names_the_deadline_forms_the_scorer_accepts(self) -> None:
        """`PROTOCOL_DEADLINE_FORMS` is pinned to the frozen document.

        Those four are the one part of the accepted vocabulary that does not come
        from the fixture, so they are checked against protocol section 10 in the
        same way the card's wording is checked against the fixture. Section 17
        freezes section 10, so a reword there is a change to the answer key.
        """
        text = _protocol()
        assert (
            "Any statement of the same instant on the same local day is correct"
            in text
        )
        for form in PROTOCOL_DEADLINE_FORMS:
            assert form in text, form


class TestTheSmallSampleReportingRules:
    def test_raw_counts_are_always_reported(self) -> None:
        report = render_outcome_report({"A": 2, "B": 3})
        assert "A: 2 dyads" in report
        assert "B: 3 dyads" in report

    def test_no_percentage_appears_below_ten_participants(self) -> None:
        report = render_outcome_report({"A": 4, "B": 4})
        assert not any("%" in line for line in report), report

    def test_the_control_a_percentage_appears_at_ten(self) -> None:
        """The control: the rule must not suppress percentages everywhere.

        Without this, a guard that never emits a percentage at any n would pass
        the test above while being wrong about the rule it implements.
        """
        report = render_outcome_report({"A": 6, "B": 6})
        assert any("%" in line for line in report), report

    def test_an_empty_sample_is_refused(self) -> None:
        with pytest.raises(ValueError):
            render_outcome_report({})

    def test_three_dyads_per_condition_support_a_claim(self) -> None:
        assert hcd_claim_supported({"A": 3, "B": 3}) is True

    def test_two_dyads_in_one_condition_supports_no_claim(self) -> None:
        assert hcd_claim_supported({"A": 6, "B": 2}) is False

    def test_an_empty_condition_supports_no_claim(self) -> None:
        assert hcd_claim_supported({"A": 6, "B": 0}) is False

    def test_no_sample_at_all_supports_no_claim(self) -> None:
        assert hcd_claim_supported({}) is False

    def test_the_thresholds_match_the_protocol(self) -> None:
        """The code and the document must state the same numbers."""
        text = _protocol()
        assert f"(n = {MIN_PARTICIPANTS_FOR_PERCENTAGES})" in text
        assert f"minimum: {MIN_DYADS_PER_CONDITION} dyads per condition" in text.casefold()
