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
def test_redacted_readback_requires_question_and_omits_answers(plan, tmp_path, case):
    # Use a real redacted projection with Slice 16's guarded offers and copy.
    from _journey_fixtures import seed_journey
    service = make_service(tmp_path / "hidden.sqlite")
    seed_journey(service, "fictional-hidden", "readback")
    good = journey_surface(service.project_journey("fictional-hidden"))
    service._store.close()
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
 useLayoutEffect(effect,deps){hooks.useEffect(effect,deps)},
 useActionState(){throw Error("forms not mounted by this hook driver")}
};
const hintMod={exports:{}};const hintCode=ts.transpileModule(readFileSync("frontend/components/HintCard.tsx","utf8"),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
new Function("require","module","exports",hintCode)(name=>name==="react"?hooks:require(name),hintMod,hintMod.exports);
const module={exports:{}};
new Function("require","module","exports",code)(name=>{
 if(name==="react")return hooks;
 if(name==="next/navigation")return {useRouter:()=>({refresh:()=>{refreshes++}})};
 if(name==="@/app/actions")return {};
 if(name==="@/lib/journey")return journey;
 if(name==="./HintCard")return hintMod.exports;
 return require(name);
},module,module.exports);
globalThis.requestAnimationFrame=callback=>callback();
index=0;module.exports.PatientJourney({state:"loaded",journey:stopped});for(const effect of effects)effect();
const callbacks=slots.filter(value=>typeof value==="function");
if(callbacks.length!==1)throw Error("missing result callback");
callbacks[0]({state:"loaded",journey:plan});
console.log(JSON.stringify({step:slots[1].journey.step,stopped:slots[1].journey.flow.stopped,refreshes}));
''', plan) == {"step": "stopped", "stopped": True, "refreshes": 1}


def test_readback_transition_replaces_the_answer_bearing_document(plan, tmp_path):
    from _journey_fixtures import seed_journey
    service = make_service(tmp_path / "document.sqlite")
    seed_journey(service, plan["episode_id"], "readback")
    redacted = journey_surface(service.project_journey(plan["episode_id"]))
    service._store.close()
    result = node('''import {readFileSync} from "node:fs";import {createRequire} from "node:module";
import * as journey from "./frontend/lib/journey.ts";
const [plan,next]=JSON.parse(readFileSync(0,"utf8")),require=createRequire(process.cwd()+"/frontend/package.json"),ts=require("typescript");
const React=require("react"),paths=[];
const hooks={useState:v=>[typeof v==="function"?v():v,()=>{}],useRef:v=>({current:v}),useEffect(){},useLayoutEffect(){},useActionState(){throw Error("not mounted")}};
const mod={exports:{}},code=ts.transpileModule(readFileSync("frontend/components/PatientJourney.tsx","utf8"),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
new Function("require","module","exports",code)(name=>{
 if(name==="react")return hooks;if(name==="next/navigation")return {useRouter:()=>({refresh(){}})};
 if(name==="@/lib/journey")return journey;
 if(name==="@/app/actions")return {submitReadback:async()=>({state:"loaded",journey:next})};
 if(name==="./HintCard")return {HintCard(){return null}};return require(name);
},mod,mod.exports);
globalThis.window={location:{assign:path=>paths.push(path)}};globalThis.requestAnimationFrame=f=>f();
function find(node){if(!React.isValidElement(node))return null;
 if(node.type==="button"&&node.props.children===plan.text.readback_label)return node;
 for(const child of React.Children.toArray(node.props.children)){const found=find(child);if(found)return found}return null}
const button=find(mod.exports.PatientJourney({state:"loaded",journey:plan}));
if(!button)throw Error("missing start-readback control");await button.props.onClick();
console.log(JSON.stringify(paths));''', [plan, redacted])
    assert result == ["/patient"]


def test_hide_response_keeps_focus_on_the_show_opener(plan, tmp_path):
    from _journey_fixtures import seed_journey
    from carerelay.journey_commands import verify_operation
    from _legacy_service_probes import KEY
    service = make_service(tmp_path / "focus.sqlite")
    ep = "fictional-focus"
    seed_journey(service, ep, "readback")
    initial = journey_surface(service.project_journey(ep))
    def command(kind):
        offer = next(o for o in service.project_journey(ep).commands if o.kind == kind)
        return journey_surface(service.record_journey_event(verify_operation(offer.operation_token, signing_key=KEY)).journey)
    shown, hidden = command("show_plan"), command("hide_plan")
    service._store.close()
    observed = node('''import {readFileSync} from "node:fs";import {createRequire} from "node:module";
import * as journey from "./frontend/lib/journey.ts";
const [initial,plan,next]=JSON.parse(readFileSync(0,"utf8")),require=createRequire(process.cwd()+"/frontend/package.json"),ts=require("typescript"),React=require("react");
const focused=[];
const hooks={useState:v=>[v?.state==="loaded"?{state:"loaded",journey:plan}:typeof v==="function"?v():v,()=>{}],useRef:v=>({current:v}),useEffect(){},useLayoutEffect(){},useActionState(){throw Error("not mounted")}};
const mod={exports:{}},code=ts.transpileModule(readFileSync("frontend/components/PatientJourney.tsx","utf8"),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
function HintCard(){}
new Function("require","module","exports",code)(name=>{
 if(name==="react")return hooks;if(name==="next/navigation")return {useRouter:()=>({refresh(){}})};
 if(name==="@/lib/journey")return journey;if(name==="@/app/actions")return {submitReadback:async()=>({state:"loaded",journey:next})};
 if(name==="./HintCard")return {HintCard};return require(name);
},mod,mod.exports);
globalThis.window={location:{assign(){},search:""}};globalThis.requestAnimationFrame=f=>f();
const nodes=[];function walk(node){if(!React.isValidElement(node))return;nodes.push(node);React.Children.forEach(node.props.children,walk)}
walk(mod.exports.PatientJourney({state:"loaded",journey:initial}));
const main=nodes.find(n=>n.type==="main"),show=nodes.find(n=>n.type==="button"&&n.props.children===plan.text.show_label),card=nodes.find(n=>n.type===HintCard);
main.props.ref.current={focus:()=>focused.push("main")};show.props.ref.current={focus:()=>focused.push("show")};
card.props.onHide();await new Promise(resolve=>setImmediate(resolve));console.log(JSON.stringify(focused));''', [initial, shown, hidden])
    assert observed == ["show"]


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
