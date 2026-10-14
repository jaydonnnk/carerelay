"""Run the production TypeScript decoder and response reconciliation offline."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from carerelay.demo import fixture
from carerelay.presentation import journey_surface
from test_truthfulness import make_service

ROOT = Path(__file__).resolve().parents[1]
MODULE = (ROOT / "frontend/lib/journey.ts").as_uri()


def node(script, data):
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps(data), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.fixture
def plan(tmp_path):
    service = make_service(tmp_path / "decoder.sqlite")
    service.ensure_episode("fictional-decoder", "fictional")
    service.intake("fictional-decoder", fixture.BOUND_COMPLAINT)
    body = journey_surface(service.project_journey("fictional-decoder"))
    service._store.close()
    return body


@pytest.mark.parametrize("case", ["start", "plan", "readback", "repair", "uncertain", "unavailable",
    "barrier", "permission", "declined", "waiting", "acknowledged", "failed", "stopped", "h3",
    "handoff", "handoff_failed", "handoff_attempted", "handoff_unknown", "accepted", "stopped_accepted",
    "stopped_handoff", "expired_accepted", "expired_handoff", "expired_stopped", "documented", "expired_documented", "pending"])
def test_trusted_stored_screen_projections_decode(tmp_path, case):
    from _journey_fixtures import seed_journey
    service = make_service(tmp_path / "trusted-decoder.sqlite")
    episode = "fictional-decoder-" + case
    try:
        seed_journey(service, episode, case)
        projection = journey_surface(service.project_journey(episode))
    finally:
        service._store.close()
    if case in {"documented", "expired_documented"}:
        assert projection["step"] == "documented"
        assert projection["care_evidenced"] is True
        assert projection["action_owner_id"] == "patient"
    assert node(f'''import {{decodeJourney}} from {json.dumps(MODULE)};
import {{readFileSync}} from "node:fs";
const body=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify(decodeJourney(body,body.episode_id)!==null));''', projection) is True


@pytest.mark.parametrize("case", ["labels", "plan_question", "stop", "h3", "expiry", "owner", "unknown_copy"])
def test_assessed_contradictions_reject_whole_response(plan, case):
    bad = copy.deepcopy(plan)
    if case == "labels":
        del bad["text"]["deadline_label"]
    elif case == "plan_question":
        bad["question"] = {"question_id": "plan", "text": "Invented question", "choices": []}
    elif case == "stop":
        bad["flow"].update(stopped=True, stop_reason="fictional-stop", stopped_disposition_version=1)
    elif case == "h3":
        bad["flow"]["effective_hint"] = "H3"
    elif case == "expiry":
        bad["outcome"]["expiry_recorded"] = True
    elif case == "owner":
        bad["plan"].update(current_owner_id="caregiver", current_owner_display="Caregiver")
        bad["action_owner_id"] = "caregiver"
    else:
        bad["text"]["answer"] = bad["plan"]["action_text"]
    assert node(f'''import {{decodeJourney}} from {json.dumps(MODULE)};
import {{readFileSync}} from "node:fs";
const [good,bad]=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify([decodeJourney(good,good.episode_id)!==null,decodeJourney(bad,good.episode_id)===null]));''', [plan, bad]) == [True, True]


@pytest.mark.parametrize("case", ["missing_question", "answer_copy", "owner_answer", "wrong_question_id", "unexpected_choice"])
def test_redacted_readback_requires_question_and_omits_answers(plan, case):
    good = copy.deepcopy(plan)
    good.update(step="readback", plan_redacted=True, plan=None, action_owner_id=None, lines=[],
                text={"heading": "What is your plan?"},
                question={"question_id": "readback", "text": "What will you do, when, and who will act?", "choices": []})
    good["flow"]["readback_attempt_id"] = "fictional-round"
    bad = copy.deepcopy(good)
    if case == "missing_question":
        bad["question"] = None
    elif case == "answer_copy":
        bad["text"]["answer"] = plan["plan"]["action_text"]
    elif case == "owner_answer":
        bad["outcome"]["escalation_path"] = "nurse_line"
    elif case == "wrong_question_id":
        bad["question"]["question_id"] = "permission"
    else:
        bad["question"]["choices"] = [{"choice_id": "booking", "text": "Choose booking"}]
    assert node(f'''import {{decodeJourney}} from {json.dumps(MODULE)};
import {{readFileSync}} from "node:fs";
const [good,bad]=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify([decodeJourney(good,good.episode_id)!==null,decodeJourney(bad,good.episode_id)===null]));''', [good, bad]) == [True, True]


def test_equal_command_cannot_reopen_known_stop_but_fresh_time_expiry_can_load(plan):
    stopped = copy.deepcopy(plan)
    stopped.update(step="stopped", text={"heading": "Let’s stop the questions"})
    stopped["flow"].update(stopped=True, stop_reason="fictional-stop", stopped_disposition_version=1)
    stale = copy.deepcopy(plan)
    expired = copy.deepcopy(plan)
    expired.update(step="expired", closure="expired_unresolved", execution="expired",
                   text={"heading": "Your plan still needs action"})
    expired["outcome"].update(closure="expired_unresolved", execution="expired")
    expired["as_of_utc"] = "2026-09-30T11:00:00+00:00"
    other = copy.deepcopy(plan)
    other["episode_id"] = "fictional-distinct"
    newer = copy.deepcopy(plan)
    newer["revision"] += 1
    newer["disposition_version"] = newer["plan"]["disposition_version"] = 2
    lower = copy.deepcopy(plan)
    lower["revision"] -= 1
    assert node(f'''import {{reconcileJourney}} from {json.dumps(MODULE)};
import {{readFileSync}} from "node:fs";
const [plan,stopped,stale,expired,other,lower,newer]=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify([
 reconcileJourney(stopped,stale,false)===null,
 reconcileJourney(stopped,stale,true)===null,
 reconcileJourney(plan,expired,false)===null,
 reconcileJourney(plan,expired,true)?.step,
 reconcileJourney(stopped,other,false)?.episode_id,
 reconcileJourney(plan,lower,true)===null,
 reconcileJourney(plan,structuredClone(plan),false)?.step,
 reconcileJourney(stopped,newer,true)?.disposition_version
]));''', [plan, stopped, stale, expired, other, lower, newer]) == [True, True, True, "expired", "fictional-distinct", True, "plan", 2]


def test_component_reads_fresh_after_equal_response_without_reopening_stop(plan):
    # Execute the complete component with only React request context supplied.
    # No production guard or source statement is replaced.
    assert node('''import {readFileSync} from "node:fs";
import {createRequire} from "node:module";
const require=createRequire(process.cwd()+"/frontend/package.json");
const ts=require("typescript");
const journey=await import("./frontend/lib/journey.ts");
const plan=JSON.parse(readFileSync(0,"utf8"));
const stopped=structuredClone(plan);
stopped.step="stopped";stopped.flow.stopped=true;stopped.flow.stop_reason="fictional-stop";
stopped.flow.stopped_disposition_version=1;
stopped.text={heading:"Let’s stop the questions"};
const code=ts.transpileModule(readFileSync("frontend/components/PatientJourney.tsx","utf8"),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
let slots=[],index=0,effects=[],refreshes=0;
const hooks={
 useState(initial){const n=index++;if(!(n in slots))slots[n]=typeof initial==="function"?initial():initial;
  return [slots[n],value=>{slots[n]=typeof value==="function"?value(slots[n]):value}]},
 useRef(value){const n=index++;if(!(n in slots))slots[n]={current:value};return slots[n]},
 useEffect(effect,deps){const n=index++;const previous=slots[n];
  if(!previous||deps.some((v,i)=>v!==previous[i]))effects.push(effect);slots[n]=deps},
 useActionState(){throw Error("forms not mounted by this hook driver")}
};
const module={exports:{}};
new Function("require","module","exports",code)(name=>{
 if(name==="react")return hooks;
 if(name==="next/navigation")return {useRouter:()=>({refresh:()=>{refreshes++}})};
 if(name==="@/app/actions")return {};
 if(name==="@/lib/journey")return journey;
 return require(name);
},module,module.exports);
globalThis.requestAnimationFrame=callback=>callback();
index=0;module.exports.PatientJourney({state:"loaded",journey:stopped});for(const effect of effects)effect();
slots[6]({state:"loaded",journey:plan});
console.log(JSON.stringify({step:slots[1].journey.step,stopped:slots[1].journey.flow.stopped,refreshes}));
''', plan) == {"step": "stopped", "stopped": True, "refreshes": 1}


@pytest.mark.parametrize("case", ["waiting", "handoff"])
def test_revealed_plan_metadata_survives_outcome_substate(tmp_path, case):
    from _journey_fixtures import seed_journey
    service = make_service(tmp_path / "revealed.sqlite")
    episode = "revealed-" + case
    seed_journey(service, episode, case)
    service.record_hint_event(episode, "H2", "shown")
    body = journey_surface(service.project_journey(episode))
    assert body["flow"]["card_visible"]
    assert body["revealed_plan"]["action_text"] == fixture.ACTION_TEXT
    assert body["text"].get("reveal_action_label") == "What to do"
    assert node(f'''import {{decodeJourney}} from {json.dumps(MODULE)};
import {{readFileSync}} from "node:fs";
const body=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify(decodeJourney(body,body.episode_id)!==null));''',body) is True
    service._store.close()
