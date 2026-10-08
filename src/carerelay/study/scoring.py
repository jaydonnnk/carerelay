"""The pre-registered scoring rules for the Gate B comparison. Slice 9.

These five functions used to live in `tests/test_study.py`, where they were the
reference meaning of `study/protocol.md` sections 10, 11 and 15 rather than the
implementation Gate B would call. `00-status.md` records that as a carried item
against this slice: a rule that exists only inside a test cannot score a real
response, so the protocol's rules would have governed nothing. They are lifted
here with their behaviour unchanged, and the test module now imports them.

**Why every scorer is three-way.** Protocol section 11 sends a response the
scorer cannot classify to the second scorer, recorded verbatim. Two of the three
scorers were two-way until finding B1 of the Slice 8 review measured that an
unclassifiable restatement was recorded as `False`, which is a guess written
down as a measurement. The third case therefore raises.

**Why the vocabularies are derived, never hand-typed.** Finding B1 of the Slice 8
review: the accepted lists used to be written out by hand and they disagreed with
the product they measure. Four of the six deadline forms the application resolves
to 18:00 scored incorrect, and all seven action aliases the application resolves
to the keyed action scored incorrect, which deflates condition A specifically,
because condition A participants talk to the alias-accepting application while
condition B participants read the card verbatim. Deriving the sets makes the
disagreement unrepresentable rather than merely unlikely.

**Why none of these functions takes a condition.** Protocol section 16: the
scorer sees the answer key and the response, not the project hypothesis. A
condition argument would put the arm label inside the scorer, which is the
blinding the protocol exists to protect.

**Why there are two vocabularies, and which one scores a row.** The amendment
of 8 October 2026 closed the two recall questions, so a row is scored from the
**option chosen** (`score_action_option`, `score_deadline_option`) and not from
the words. The word vocabularies and their scorers are kept: they are the
measurement section 17 records, and the guards that pin them are what makes
that paragraph true rather than asserted. They are no longer the path a row
takes, and nothing in the instrument calls them to score a response.

**Why the option sets are derived, never typed.** The same discipline as the
word vocabularies, for the same reason. The three action options are the
fixture's three permitted actions, and the three deadline options are the three
instants its deadline table already resolves, so the keyed value and its
distractors cannot drift from the product they measure. Only the letters come
from this study, and they are pinned against section 7 by a test.
"""

from __future__ import annotations

from collections.abc import Callable

from carerelay.demo import fixture
from carerelay.domain import rules

#: The three outcomes a response can be given. `UNCLASSIFIED` is not a score: it
#: is the refusal, and the row keeps the verbatim text so the second scorer can
#: resolve it (protocol section 11).
CORRECT = "correct"
INCORRECT = "incorrect"
UNCLASSIFIED = "unclassified"

#: The primary outcome is not a recall score, so `CORRECT` and `INCORRECT` are
#: the wrong words for it: a participant who answers "no" has answered correctly,
#: and calling that "incorrect" would read as a scoring error. These name what
#: was measured instead.
FALSE_COMPLETION = "false completion"
NO_FALSE_COMPLETION = "no false completion"


class UnclassifiableResponse(ValueError):
    """A response the scorer cannot classify.

    Raised rather than scored, because protocol section 11 sends such a response
    to the second scorer and forbids the facilitator who ran the session from
    resolving it. Returning `False` here would record a guess as a measurement,
    which is finding B1 of the Slice 8 review.
    """


#: The keyed deadline instant. Protocol section 10: the answer key is the
#: fixture's value, so the key is derived rather than restated.
KEYED_DEADLINE_INSTANT: tuple[int, str] = (0, fixture.DEADLINE_LOCAL_HHMM)

#: Every deadline form the **application** resolves to the keyed instant.
FIXTURE_DEADLINE_FORMS: tuple[str, ...] = tuple(
    sorted(
        form
        for form, instant in fixture.DEADLINE_FORMS.items()
        if instant == KEYED_DEADLINE_INSTANT
    )
)

#: Every deadline form the application resolves to a **different** instant. A
#: known wrong value must be scored incorrect, never uncertain: that is kill
#: condition K1 and protocol section 10.
DIFFERENT_DEADLINE_FORMS: tuple[str, ...] = tuple(
    sorted(
        form
        for form, instant in fixture.DEADLINE_FORMS.items()
        if instant != KEYED_DEADLINE_INSTANT
    )
)

#: Paraphrases the frozen protocol names in section 10 that the fixture's own
#: resolver does not carry. They are kept because section 17 freezes section 10,
#: and `test_the_protocol_names_the_deadline_forms_the_scorer_accepts` pins each
#: one against the document, so they cannot drift from it silently.
PROTOCOL_DEADLINE_FORMS: tuple[str, ...] = (
    "18:00",
    "6pm",
    "six in the evening",
    "6pm today",
)

ACCEPTED_DEADLINE_FORMS: tuple[str, ...] = tuple(
    sorted(
        set(FIXTURE_DEADLINE_FORMS)
        | set(PROTOCOL_DEADLINE_FORMS)
        | {fixture.DEADLINE_DISPLAY, fixture.DEADLINE_LOCAL_HHMM}
    )
)

#: Every alias the application resolves to the keyed action, read from
#: `policy().action_aliases` rather than written out.
FIXTURE_ACTION_FORMS: tuple[str, ...] = tuple(
    sorted(
        alias
        for alias, action_id in fixture.policy().action_aliases.items()
        if action_id == fixture.ACTION_ID
    )
)

#: Aliases the application resolves to a **different permitted** action. This is
#: empty today and the emptiness is derived, not assumed: `fixture.ACTION_ALIASES`
#: carries aliases for the keyed action only, so the fixture has no vocabulary
#: for a known-wrong action. No alias is invented to fill it.
#: `test_no_fixture_alias_resolves_to_a_different_action` fails the moment one
#: arrives, which is the open item this slice carried forward.
DIFFERENT_ACTION_FORMS: tuple[str, ...] = tuple(
    sorted(
        alias
        for alias, action_id in fixture.policy().action_aliases.items()
        if action_id in fixture.policy().permitted_action_ids
        and action_id != fixture.ACTION_ID
    )
)

ACCEPTED_ACTION_FORMS: tuple[str, ...] = tuple(
    sorted(set(FIXTURE_ACTION_FORMS) | {fixture.ACTION_TEXT})
)

AFFIRMATIVE_ANSWERS: frozenset[str] = frozenset(
    {"yes", "y", "yeah", "yep", "yes i have", "yes it has", "i have"}
)
NEGATIVE_ANSWERS: frozenset[str] = frozenset(
    {"no", "n", "nope", "no i have not", "no it has not", "not yet"}
)

#: The closed recall instrument, protocol section 7 as amended on 8 October 2026.
#:
#: The two recall questions are closed, so a response is scored from the
#: **option chosen** and the words are no longer the thing being scored. A
#: closed question needs no vocabulary of paraphrases, which is what the
#: amendment exists to remove: an open question needed one and did not have one.
#:
#: The letters are the only part of this that comes from the study. The keyed
#: value takes the first position because section 7 lists it first, the other
#: values the fixture already resolves follow it in the fixture's own order, and
#: "I don't know" is last. `tests/test_study_instrument.py` pins every letter
#: against the document and against the fixture, so neither set can drift from
#: either.
KEYED_OPTION = "a"
DONT_KNOW_OPTION = "d"


def _option_letters(count: int) -> tuple[str, ...]:
    """The first `count` option letters: a, b, c, and so on."""
    return tuple(chr(ord("a") + index) for index in range(count))


def option_letter(recorded: str) -> str:
    """The option letter a facilitator recorded, case and punctuation aside.

    Protocol section 12: the recall columns record the option chosen, A to D.
    Anything else is not an option, so a row carrying no letter is left
    unresolved rather than guessed. That is the one recall case the second
    scorer still has to resolve, and section 11 as amended names it.
    """
    return rules.normalise(recorded).strip(".").strip()


#: The permitted actions the closed question offers, minus the keyed one. Read
#: from the policy, so a distractor is a route the fixture already resolves
#: rather than one written for this study.
DISTRACTOR_ACTION_IDS: tuple[str, ...] = tuple(
    sorted(fixture.policy().permitted_action_ids - {fixture.ACTION_ID})
)

#: Option letter to action id. The keyed action is first, because section 7
#: lists it first.
ACTION_OPTIONS: dict[str, str] = dict(
    zip(
        _option_letters(1 + len(DISTRACTOR_ACTION_IDS)),
        (fixture.ACTION_ID, *DISTRACTOR_ACTION_IDS),
        strict=True,
    )
)

#: Every option that is a known wrong action. "I don't know" is scored the same
#: way and is named separately, because it is a different kind of wrong: the
#: field was not recalled, which section 11 calls a measurement and not an
#: absence of one.
DISTRACTOR_ACTION_OPTIONS: tuple[str, ...] = tuple(
    letter for letter in ACTION_OPTIONS if letter != KEYED_OPTION
)


def _deadline_option_text(instant: tuple[int, str]) -> str:
    """Render a fixture deadline instant as the option text the study reads.

    Derived from the instant, so "6pm today" is not a string written for this
    study: it is the same value the card prints and the application resolves,
    in the words the closed question uses.
    """
    day, hhmm = instant
    hour = int(hhmm.split(":")[0])
    day_word = {0: "today", 1: "tomorrow"}[day]
    return f"{hour % 12 or 12}{'pm' if hour >= 12 else 'am'} {day_word}"


#: The instants the closed question offers, minus the keyed one. Read from the
#: fixture's own deadline table, and sorted so the letters are stable.
DISTRACTOR_DEADLINE_INSTANTS: tuple[tuple[int, str], ...] = tuple(
    sorted(set(fixture.DEADLINE_FORMS.values()) - {KEYED_DEADLINE_INSTANT})
)

#: Option letter to deadline option text.
DEADLINE_OPTIONS: dict[str, str] = dict(
    zip(
        _option_letters(1 + len(DISTRACTOR_DEADLINE_INSTANTS)),
        [
            _deadline_option_text(instant)
            for instant in (KEYED_DEADLINE_INSTANT, *DISTRACTOR_DEADLINE_INSTANTS)
        ],
        strict=True,
    )
)

DISTRACTOR_DEADLINE_OPTIONS: tuple[str, ...] = tuple(
    letter for letter in DEADLINE_OPTIONS if letter != KEYED_OPTION
)


def score_false_completion(answer: str) -> bool:
    """Score the primary outcome from the participant's uncoached answer.

    A yes is a false completion, because the status is unresolved and no care is
    arranged. An answer that is neither a yes nor a no is not scored here: the
    protocol records it verbatim and the second scorer resolves it.
    """
    normalised = rules.normalise(answer)
    if normalised in AFFIRMATIVE_ANSWERS:
        return True
    if normalised in NEGATIVE_ANSWERS:
        return False
    raise UnclassifiableResponse(f"unclassifiable answer, record verbatim: {answer!r}")


def score_action_recall(restated: str) -> bool:
    """Three-way, like `score_false_completion`, and for the same reason.

    Correct when the fixture resolves the restatement to the keyed action;
    incorrect when it resolves it to a different permitted action; and a refusal
    when it resolves to nothing, because protocol section 11 sends an
    unclassifiable response to the second scorer instead of letting the first
    scorer guess. Returning `False` for that third case was finding B1: it
    recorded a guess as if it were a score.
    """
    normalised = rules.normalise(restated)
    if normalised in {rules.normalise(form) for form in ACCEPTED_ACTION_FORMS}:
        return True
    if normalised in {rules.normalise(form) for form in DIFFERENT_ACTION_FORMS}:
        return False
    raise UnclassifiableResponse(
        f"unclassifiable restated action, record verbatim: {restated!r}"
    )


def score_deadline_recall(restated: str) -> bool:
    """Three-way, like `score_false_completion`.

    Correct for any surface form of the keyed instant, incorrect for a form the
    fixture resolves to a different instant (never uncertain, protocol section
    10), and a refusal for a restatement the fixture resolves to nothing at all.
    """
    normalised = rules.normalise(restated)
    if normalised in {rules.normalise(form) for form in ACCEPTED_DEADLINE_FORMS}:
        return True
    if normalised in {rules.normalise(form) for form in DIFFERENT_DEADLINE_FORMS}:
        return False
    raise UnclassifiableResponse(
        f"unclassifiable restated deadline, record verbatim: {restated!r}"
    )


def score_action_option(option: str) -> bool:
    """Score the closed action question from the option chosen.

    Protocol section 11 as amended on 8 October 2026. Correct for the keyed
    option; **incorrect** for a distractor, and for "I don't know", which is a
    measurement rather than an absence of one; and a refusal only when no
    option was recorded at all, because a row with no letter is the one recall
    case the second scorer still resolves.
    """
    letter = option_letter(option)
    if letter == KEYED_OPTION:
        return True
    if letter in DISTRACTOR_ACTION_OPTIONS or letter == DONT_KNOW_OPTION:
        return False
    raise UnclassifiableResponse(
        f"no action option was recorded, record the words verbatim: {option!r}"
    )


def score_deadline_option(option: str) -> bool:
    """Score the closed deadline question from the option chosen.

    The same three cases as `score_action_option`, and for the same reason: a
    distractor is an instant the fixture already resolves to a different one,
    so choosing it is a known wrong value and is scored incorrect (K1), never
    uncertain.
    """
    letter = option_letter(option)
    if letter == KEYED_OPTION:
        return True
    if letter in DISTRACTOR_DEADLINE_OPTIONS or letter == DONT_KNOW_OPTION:
        return False
    raise UnclassifiableResponse(
        f"no deadline option was recorded, record the words verbatim: {option!r}"
    )


def classify(scorer: Callable[[str], bool], text: str) -> str:
    """Score a response into one of three labels, never guessing.

    The scorers raise on the third case, which is right for a rule and wrong for
    a sheet: a row must still be recorded when its response cannot be scored.
    This wraps them, so `UNCLASSIFIED` reaches the row instead of an exception,
    and the verbatim text stays on the row for the second scorer.

    A `ValueError` that is **not** an `UnclassifiableResponse` is not swallowed:
    catching every `ValueError` here would turn a bug in a scorer into a silent
    "unclassified" row.
    """
    try:
        return CORRECT if scorer(text) else INCORRECT
    except UnclassifiableResponse:
        return UNCLASSIFIED


def classify_false_completion(answer: str) -> str:
    """Three-way label for the primary outcome.

    `classify` is reused for the two recall fields but not here, because the
    primary outcome is a belief about the status rather than a recall of it, so
    the labels above name what was measured instead of scoring it.
    """
    try:
        if score_false_completion(answer):
            return FALSE_COMPLETION
    except UnclassifiableResponse:
        return UNCLASSIFIED
    return NO_FALSE_COMPLETION
