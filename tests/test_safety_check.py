"""Quick safety check (Gate 1 to 4 approval, 16 October 2026).

The rule is the challenge's Scenario 2 emergency tier, used verbatim: SpO2 below
90%, a respiratory rate of 30 or more, new chest pain, or confusion. "Not sure"
is never read as clear. Tests run the real TypeScript module through node.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / "frontend/lib/journey.ts").as_uri()
CLEAR = {"oxygen": "94_plus", "breathing": "no", "chest_pain": "no", "confusion": "no"}


def assess(*cases):
    script = (f"import {{assessSafety, emergencyLine, uncheckedLine, SAFETY_COPY, QUESTIONS}} from {json.dumps(MODULE)};\n"
              "import {readFileSync} from 'node:fs';\n"
              "const cases=JSON.parse(readFileSync(0,'utf8'));\n"
              "console.log(JSON.stringify({out: cases.map(c=>assessSafety(c)), copy: SAFETY_COPY, questions: QUESTIONS,\n"
              "  emergency: emergencyLine(['new chest pain','confusion']), unchecked: uncheckedLine(['your oxygen'])}));")
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
                            input=json.dumps(list(cases)), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("field,value,reason", [
    ("oxygen", "below_90", "oxygen below 90%"),
    ("breathing", "yes", "breathing 30 or more times a minute"),
    ("chest_pain", "yes", "new chest pain"),
    ("confusion", "yes", "confusion"),
])
def test_each_scenario_2_red_flag_alone_is_an_emergency(field, value, reason):
    assert assess({**CLEAR, field: value})["out"] == [{"result": "emergency", "reasons": [reason]}]


def test_no_warning_sign_is_clear_with_nothing_unchecked():
    assert assess(CLEAR)["out"] == [{"result": "clear", "unchecked": []}]


def test_oxygen_90_to_93_is_not_the_emergency_tier():
    """Scenario 2 places 90-93% in the same-day tier, which Mei's plan already is."""
    assert assess({**CLEAR, "oxygen": "90_93"})["out"] == [{"result": "clear", "unchecked": []}]


@pytest.mark.parametrize("field,value,label", [
    ("oxygen", "unknown", "your oxygen"),
    ("breathing", "unsure", "your breathing rate"),
    ("chest_pain", "unsure", "chest pain"),
    ("confusion", "unsure", "confusion"),
])
def test_not_sure_is_reported_as_unchecked_never_as_clear(field, value, label):
    assert assess({**CLEAR, field: value})["out"] == [{"result": "clear", "unchecked": [label]}]


def test_a_red_flag_wins_over_an_unknown():
    out = assess({"oxygen": "unknown", "breathing": "unsure", "chest_pain": "yes", "confusion": "unsure"})["out"]
    assert out == [{"result": "emergency", "reasons": ["new chest pain"]}]


def test_every_red_flag_is_named_in_order():
    out = assess({"oxygen": "below_90", "breathing": "yes", "chest_pain": "yes", "confusion": "yes"})["out"]
    assert out[0]["reasons"] == ["oxygen below 90%", "breathing 30 or more times a minute", "new chest pain", "confusion"]


@pytest.mark.parametrize("answers", [
    {}, {"oxygen": "below_90"}, {**CLEAR, "confusion": None}, {**CLEAR, "breathing": "maybe"}, {**CLEAR, "oxygen": "89"},
])
def test_an_incomplete_or_unknown_answer_set_decides_nothing(answers):
    """Even a red flag already given waits for the rest; the screen asks all four first."""
    assert assess(answers)["out"] == [{"result": "incomplete"}]


def test_the_approved_wording_is_verbatim():
    data = assess()
    copy, questions = data["copy"], data["questions"]
    assert copy["heading"] == "Quick safety check" and copy["intro"] == "Answer for right now."
    assert copy["source"] == "Uses the challenge's example warning signs (Scenario 2). Not clinical guidance."
    assert copy["emergency_heading"] == "Get emergency help now"
    assert copy["emergency_call"] == "Call 995 for an ambulance."
    assert copy["emergency_wait"] == "Do not wait for this app."
    assert copy["emergency_change"] == "Change my answers"
    assert copy["clear"] == "No warning signs from these four questions."
    assert (copy["next"], copy["back"]) == ("Next", "Back")
    assert questions["oxygen"]["text"] == "What is your oxygen reading right now?"
    assert [label for _, label in questions["oxygen"]["options"]] == ["Below 90%", "90% to 93%", "94% or higher", "I cannot measure it"]
    assert questions["breathing"]["text"] == "Are you breathing very fast, 30 or more breaths a minute?"
    assert questions["chest_pain"]["text"] == "Do you have new chest pain?"
    assert questions["confusion"]["text"] == "Are you confused, or has someone said you seem confused?"
    for field in ("breathing", "chest_pain", "confusion"):
        assert [label for _, label in questions[field]["options"]] == ["Yes", "No", "Not sure"]
    assert data["emergency"] == "You said: new chest pain, confusion."
    assert data["unchecked"] == "We could not check: your oxygen. If you get worse, call 995."
