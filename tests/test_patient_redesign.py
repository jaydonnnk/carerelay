"""Slice 22: patient redesign and one-press start (Gate 3 section 10, Gate 4 section 10).

Each test runs the production TypeScript module or component offline through Node, the
same way `test_journey_decoder.py` and `test_journey_commands.py` do. No network, no Next.js.
"""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from carerelay.presentation import journey_surface
from test_truthfulness import make_service

ROOT = Path(__file__).resolve().parents[1]
JOURNEY = (ROOT / "frontend/lib/journey.ts").as_uri()
LOCATOR = (ROOT / "frontend/lib/episode-locator.ts").as_uri()
NM = ROOT / "frontend/node_modules"


def node(script, data=None):
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps(data), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def seeded(tmp_path, case):
    from _journey_fixtures import seed_journey
    service = make_service(tmp_path / f"s22-{case}.sqlite")
    try:
        episode = "s22-render-" + case
        seed_journey(service, episode, case)
        return json.loads(json.dumps(journey_surface(service.project_journey(episode))))
    finally:
        service._store.close()


def render(states):
    """Render `PatientJourney` to static HTML for each props object, with actions stubbed."""
    react = (NM / "react/index.js").as_uri()
    return node(f'''import {{readFileSync}} from 'node:fs';
import ts from {json.dumps((NM / "typescript/lib/typescript.js").as_uri())};
import React from {json.dumps(react)};
import {{renderToStaticMarkup}} from {json.dumps((NM / "react-dom/server.node.js").as_uri())};
const states=JSON.parse(readFileSync(0,'utf8'));
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const transpile=s=>ts.transpileModule(s,{{compilerOptions:{{module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}}}).outputText
 .replaceAll('"react"',{json.dumps(json.dumps(react))})
 .replaceAll('"react/jsx-runtime"',{json.dumps(json.dumps((NM / "react/jsx-runtime.js").as_uri()))});
const actions=url(['startExample','selectExample','prepareReadbackWords','submitReadback','prepareBarrierChoice','submitPermission'].map(n=>'export async function '+n+'(){{throw Error("render only")}}').join(';'));
const nav=url('export function useRouter(){{return {{refresh(){{}}}}}}');
const hint=url(transpile(readFileSync('frontend/components/HintCard.tsx','utf8')));
const source=readFileSync('frontend/components/PatientJourney.tsx','utf8').replace('"next/navigation"',JSON.stringify(nav))
 .replace('"@/app/actions"',JSON.stringify(actions)).replace('"@/lib/journey"',{json.dumps(json.dumps(JOURNEY))})
 .replace('"./HintCard"',JSON.stringify(hint));
const {{PatientJourney}}=await import(url(transpile(source)));
console.log(JSON.stringify(states.map(props=>renderToStaticMarkup(React.createElement(PatientJourney,props)))));''', states)


def test_s22_frame_ancestors_header_covers_every_route():
    """F4: only this app may frame its pages (Gate 2 D19)."""
    headers = node(f'''const config=(await import({json.dumps((ROOT / "frontend/next.config.mjs").as_uri())})).default;
console.log(JSON.stringify(await config.headers()));''')
    assert headers == [{"source": "/:path*", "headers": [
        {"key": "Content-Security-Policy", "value": "frame-ancestors 'self'"}]}]


def test_s22_parent_message_targets_the_exact_same_origin_only():
    """F6: the judge-stage message names its own origin, never "*", and carries only the revision."""
    observed = node(f'''import {{notifyParent}} from {json.dumps(JOURNEY)};
const origin="https://carerelay.test", posts=[];
const parent=(o,readable=true)=>({{postMessage:(m,t)=>posts.push([m,t]),get location(){{if(!readable)throw Error("cross-origin");return {{origin:o}}}}}});
const top={{location:{{origin}}}};top.parent=top;
const framed={{location:{{origin}},parent:parent(origin)}};
const foreign={{location:{{origin}},parent:parent("https://other.test")}};
const opaque={{location:{{origin}},parent:parent(origin,false)}};
const sent=[notifyParent(top,1),notifyParent(framed,2),notifyParent(foreign,3),notifyParent(opaque,4)];
console.log(JSON.stringify({{sent,posts}}));''')
    assert observed["sent"] == [False, True, False, False]
    assert observed["posts"] == [[{"type": "carerelay-journey", "revision": 2}, "https://carerelay.test"]]


def test_s22_middleware_issues_a_locator_only_when_none_is_present():
    """F7: an existing cookie, valid or not, is left for the page; a missing one gets a signed locator."""
    observed = node(f'''import {{locatorToIssue,decodeLocator,encodeLocator,newLocator}} from {json.dumps(LOCATOR)};
const key="fictional-s22-key", fresh=locatorToIssue(undefined,key), valid=encodeLocator(newLocator(),key);
let empty="returned";try{{locatorToIssue(undefined,"")}}catch{{empty="threw"}}
console.log(JSON.stringify({{fresh:decodeLocator(fresh,key)!==null,invalid:locatorToIssue("not-a-locator",key),
 blank:locatorToIssue("",key),valid:locatorToIssue(valid,key),empty}}));''')
    assert observed == {"fresh": True, "invalid": None, "blank": None, "valid": None, "empty": "threw"}


def test_s22_middleware_module_sets_and_forwards_the_locator(tmp_path):
    """The real middleware module, transpiled with its two imports mapped, under a NextRequest."""
    observed = node(f'''import {{readFileSync}} from 'node:fs';import {{createRequire}} from 'node:module';
const require=createRequire({json.dumps(str(ROOT / "frontend/package.json"))});
const ts=require("typescript"), {{NextRequest}}=require("next/server");
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const code=ts.transpileModule(readFileSync('frontend/middleware.ts','utf8'),{{compilerOptions:{{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}}}).outputText
 .replace('"next/server"',JSON.stringify({json.dumps((NM / "next/server.js").as_uri())})).replace('"@/lib/episode-locator"',{json.dumps(json.dumps(LOCATOR))});
const mod=await import(url(code));
const {{decodeLocator}}=await import({json.dumps(LOCATOR)});
process.env.CARERELAY_API_TOKEN="fictional-s22-key";process.env.CARERELAY_LOOPBACK_TEST="1";
const run=(cookie,u="http://127.0.0.1:8540/")=>mod.middleware(new NextRequest(u,{{headers:cookie?{{cookie}}:{{}}}}));
const first=run(), kept=run("carerelay_demo_locator=tampered"), remote=run(undefined,"http://example.test/");
const set=first.cookies.get("carerelay_demo_locator");
const forwarded=first.headers.get("x-middleware-request-cookie")??"";
console.log(JSON.stringify({{matcher:mod.config.matcher,runtime:mod.config.runtime,
 issued:set?decodeLocator(set.value,"fictional-s22-key")!==null:false,httpOnly:set?.httpOnly??null,
 forwarded:set?forwarded.includes(set.value):false,kept:kept.cookies.get("carerelay_demo_locator")??null,
 remote:remote.cookies.get("carerelay_demo_locator")??null}}));''')
    assert observed == {"matcher": ["/"], "runtime": "nodejs", "issued": True, "httpOnly": True,
                        "forwarded": True, "kept": None, "remote": None}


def test_s22_one_press_creates_then_selects_once():
    """The start press chains create then select with the offered token; nothing else runs."""
    observed = node(f'''import {{startThenSelect}} from {json.dumps(JOURNEY)};
const calls=[], offer=t=>({{kind:"select_example",offer_id:"select_example",permitted_choice_ids:["scripted-appointment"],operation_token:t}});
const create=result=>async form=>{{calls.push(["create",form.get("operation_token")]);return result}};
const select=async form=>{{calls.push(["select",form.get("operation_token")]);return {{state:"loaded",journey:{{commands:[],step:"plan"}}}}}};
const form=new FormData();form.set("operation_token","create-token");
const out=[];
out.push((await startThenSelect(form,create({{state:"loaded",journey:{{commands:[offer("select-token")]}}}}),select)).journey.step);
out.push((await startThenSelect(form,create({{state:"recovery"}}),select)).state);
out.push((await startThenSelect(form,create({{state:"loaded",journey:{{commands:[offer(null)],step:"start"}}}}),select)).journey.step);
console.log(JSON.stringify({{out,calls}}));''')
    assert observed["out"] == ["plan", "recovery", "start"]
    assert observed["calls"] == [["create", "create-token"], ["select", "select-token"],
                                 ["create", "create-token"], ["create", "create-token"]]


@pytest.mark.parametrize("case,expected", [("plan", 1), ("readback", 2), ("repair", 2), ("barrier", 3),
    ("permission", 4), ("waiting", 4), ("acknowledged", None), ("failed", None), ("stopped", None), ("expired", None)])
def test_s22_step_counter_follows_the_server_step(tmp_path, case, expected):
    body = seeded(tmp_path, case)
    assert node(f'''import {{progressStep}} from {json.dumps(JOURNEY)};import {{readFileSync}} from 'node:fs';
console.log(JSON.stringify(progressStep(JSON.parse(readFileSync(0,'utf8')))));''', body) == expected


def test_s22_rendered_screens_match_the_approved_redesign(tmp_path):
    plan, readback, failed = (seeded(tmp_path, c) for c in ("plan", "readback", "failed"))
    # The frontend gate is independent of the domain: consent offered on the plan step still renders nothing.
    offered = copy.deepcopy(plan)
    offered["commands"] += [{"kind": k, "offer_id": k, "permitted_choice_ids": [], "operation_token": k}
                            for k in ("grant_share", "revoke_share")]
    offered["text"].update(consent_label="I agree to share this plan.", decline_label="Not now")
    html = render([{"state": "loaded", "journey": offered}, {"state": "loaded", "journey": readback},
                   {"state": "loaded", "journey": failed}, {"state": "start", "creationToken": "create-token"},
                   {"state": "recovery"}])
    plan_html, readback_html, failed_html, start_html, recovery_html = html

    assert 'class="slip"' in plan_html and "Your plan" in plan_html and "Step 1 of 4" in plan_html
    for value in ("Go to the clinic for a same-day review.", "6pm today", "You"):
        assert value in plan_html
    assert 'type="checkbox"' not in plan_html and "Not now" not in plan_html
    assert "Show my plan" not in plan_html and "Say it in your words" in plan_html

    assert "Your plan is folded away while you say it in your words." in readback_html
    folded = readback_html[readback_html.index('class="slip folded"'):]
    assert "Show my plan" in folded[:folded.index("</section>")]
    assert "6pm" not in readback_html and "Step 2 of 4" in readback_html

    assert failed_html.count('class="slip"') == 1 and "Fictional" not in failed_html
    lines = ["No one has agreed to help yet.", "Please act now.", "Please do it before 6pm today.",
             "If that does not work, call the nurse helpline."]
    positions = [failed_html.index(line) for line in lines]
    assert positions == sorted(positions)
    assert failed_html.index('class="slip"') < positions[3]
    assert "Step " not in failed_html and 'type="checkbox"' not in failed_html and "Not now" not in failed_html

    assert "We cannot load your plan" not in start_html and start_html.count(">Start<") == 1
    assert "We cannot load your plan" in recovery_html and ">Start<" not in recovery_html


def test_fonts_are_self_hosted_and_never_fetched_at_build_time():
    """The Google font download at build time intermittently broke builds; fonts ship in the repo."""
    layout = (ROOT / "frontend/app/layout.tsx").read_text()
    assert 'from "next/font/local"' in layout and "next/font/google" not in layout
    for name in ("AtkinsonHyperlegibleNext-latin.woff2", "AtkinsonHyperlegibleMono-latin.woff2"):
        assert f'"./fonts/{name}"' in layout
        assert (ROOT / "frontend/app/fonts" / name).read_bytes()[:4] == b"wOF2"
    for name in ("OFL-AtkinsonHyperlegibleNext.txt", "OFL-AtkinsonHyperlegibleMono.txt"):
        assert "SIL OPEN FONT LICENSE" in (ROOT / "frontend/app/fonts" / name).read_text()
