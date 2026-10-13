"""Slice 14 codec/decoder tests run real TypeScript with installed Node, no install.

These are runtime unit checks, not Next.js build or actual-browser evidence.
The cookie-before-create guard remains Slice 15, where creation exists.
"""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from carerelay.demo import fixture
from carerelay.presentation import journey_surface
from test_truthfulness import make_service

ROOT = Path(__file__).resolve().parents[1]


def node(script, data=None):
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps(data), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def module(name):
    return (ROOT / "frontend/lib" / (name + ".ts")).as_uri()


@pytest.fixture
def projection(tmp_path):
    service = make_service(tmp_path / "decoder.sqlite")
    service.ensure_episode("fictional-decoder", "fictional")
    body = json.loads(json.dumps(journey_surface(service.project_journey("fictional-decoder"))))
    service._store.close()
    return body


# Only one malformed dimension changes in each case.
INVALID = {
    "schema": ("schema_version", "unknown"), "id": ("episode_id", "wrong"),
    "revision": ("revision", -1), "unsafe_revision": ("revision", 9007199254740992),
    "time": ("as_of_utc", "not-time"), "calendar": ("as_of_utc", "2026-02-30T00:00:00+00:00"), "clock": ("clock_mode", "browser"),
    "step": ("step", "plan"), "redaction": ("plan_redacted", True),
    "disposition": ("disposition_version", 1), "policy": ("policy_version", "fictional"),
    "plan": ("plan", {}), "outcome": ("outcome", {}), "revealed": ("revealed_plan", {}),
    "question": ("question", [{"text":"one"},{"text":"two"}]), "closure": ("closure", "open"),
    "execution": ("execution", "attempted"), "evidence": ("evidence", "none"),
    "owner": ("action_owner_id", "patient"), "care": ("care_evidenced", True),
    "lines": ("lines", ["invented"]), "commands": ("commands", [{"kind":"request"}]),
    "simulated": ("simulated", False), "label": ("fixture_label", ""),
    "copy": ("text.heading", "invented"), "stopped": ("flow.stopped", True),
    "reason": ("flow.stop_reason", "stop"), "stop_version": ("flow.stopped_disposition_version", 1),
    "attempt": ("flow.readback_attempt_id", "attempt"), "restatement": ("flow.latest_restatement_id", "r"),
    "repair_field": ("flow.selected_repair_field", "deadline_utc"), "repairs": ("flow.completed_repairs", 1),
    "hint": ("flow.effective_hint", "H3"), "visible": ("flow.card_visible", True),
    "interpretation": ("flow.interpretation", "scored"), "extra": ("extra", "invented"),
    "flow_extra": ("flow.extra", "invented"), "text_extra": ("text.extra", "invented"),
}

@pytest.mark.parametrize("case", INVALID)
def test_projection_invariants(projection, case):
    path, value = INVALID[case]
    bad = copy.deepcopy(projection)
    keys = path.split("."); target = bad
    for key in keys[:-1]: target = target[key]
    target[keys[-1]] = value
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from "node:fs";
const [good,bad]=JSON.parse(readFileSync(0,"utf8"));
let rejected;try{{rejected=decodeJourney(bad,good.episode_id)===null}}catch{{rejected="threw"}}
console.log(JSON.stringify([decodeJourney(good,good.episode_id)!==null,rejected]));''', [projection, bad])
    assert result == [True, True]


def test_decoder_good_and_bounded_transport(projection):
    result = node(f'''import {{readJourney,MAX_JOURNEY_BYTES,ENTRY_COPY,RECOVERY_COPY,JOURNEY_LABEL}} from {json.dumps(module("journey"))};
import {{readFileSync}} from "node:fs";
const good=JSON.parse(readFileSync(0,"utf8")); const id=good.episode_id;
const wire=JSON.stringify(good);
const exact=wire+" ".repeat(MAX_JOURNEY_BYTES-new TextEncoder().encode(wire).length);
const values=[];
for(const body of [wire,exact,exact+" ","{{bad", new Uint8Array([255])]) {{
 values.push((await readJourney(new Response(body),id))!==null);
}}
console.log(JSON.stringify({{values,ENTRY_COPY,RECOVERY_COPY,JOURNEY_LABEL}}));''', projection)
    assert result["values"] == [True, True, False, False, False]
    assert result["ENTRY_COPY"] == fixture.JOURNEY_COPY["start"]
    assert result["RECOVERY_COPY"] == fixture.JOURNEY_COPY["recovery"]
    assert result["JOURNEY_LABEL"] == fixture.JOURNEY_LABEL


def test_cookie_codec_and_transport():
    result = node(f'''import * as c from {json.dumps(module("episode-locator"))};
const key="synthetic-codec-only";const a=c.newLocator();const b=c.newLocator();
const signed=c.encodeLocator(a,key);
const swapped=Buffer.from(JSON.stringify({{...a,episode_id:b.episode_id}})).toString("base64url")+"."+signed.split(".")[1];
const failures=[swapped,signed+"x",signed.replace(/^./,signed[0]==="a"?"b":"a"),"junk","a."+"x".repeat(1100)];
let missing=false;try{{c.encodeLocator(a,"")}}catch{{missing=true}}
const options=c.locatorCookieOptions(new URL("https://example.invalid"),false);
const local=c.locatorCookieOptions(new URL("http://127.0.0.1:8140"),true);
let remote=false, insecure=false;
try{{c.locatorCookieOptions(new URL("http://example.invalid"),true)}}catch{{remote=true}}
try{{c.locatorCookieOptions(new URL("http://127.0.0.1:8140"),false)}}catch{{insecure=true}}
console.log(JSON.stringify({{same:c.decodeLocator(signed,key),a,distinct:a.episode_id!==b.episode_id&&a.nonce!==b.nonce&&a.operation_id!==b.operation_id,
 invalid:failures.map(x=>c.decodeLocator(x,key)===null),rotation:c.decodeLocator(signed,"rotated")===null,
 missing,options,local,remote,insecure,missingRead:c.decodeLocator(signed,"")===null}}));''')
    assert result["same"] == result["a"]
    assert result["distinct"] and all(result["invalid"]) and result["rotation"]
    assert result["missing"] and result["missingRead"] and result["remote"] and result["insecure"]
    assert result["options"] == dict(httpOnly=True, secure=True, sameSite="lax", path="/")
    assert result["local"] == dict(httpOnly=True, secure=False, sameSite="lax", path="/")


def test_render_and_bootstrap_source_has_no_mutation():
    # Structural guard only. Network/render/revalidation proof requires Next.js.
    for file in ("app/page.tsx", "app/example/route.ts", "components/PatientJourney.tsx", "components/HintCard.tsx"):
        source = (ROOT / "frontend" / file).read_text()
        for forbidden in ("createEpisode(", "recordHintEvent(", "showCard(", "hideCard(", 'method: "POST"', '<form'):
            assert forbidden not in source, (file, forbidden)
    route = (ROOT / "frontend/app/example/route.ts").read_text()
    assert '"@/lib/api"' not in route
    assert "LOCATOR_COOKIE, cookie, options" in route


def test_real_bootstrap_handler_sets_cookie_before_any_backend_call():
    if not (ROOT / "frontend/node_modules/next/server.js").exists():
        pytest.skip("Next.js absent: real bootstrap handler check NOT RUN; operator npm ci required")
    # Execute the production handler, resolving only its two import paths.
    # Native Node strips types; no handler code or crypto predicate is replaced.
    result = node(f'''import {{readFileSync}} from "node:fs";
import {{stripTypeScriptTypes}} from "node:module";
import {{NextRequest}} from {json.dumps((ROOT / "frontend/node_modules/next/server.js").as_uri())};
let source=readFileSync("frontend/app/example/route.ts","utf8");
source=source.replace('"next/server"',{json.dumps(json.dumps((ROOT / "frontend/node_modules/next/server.js").as_uri()))});
source=source.replace('"@/lib/episode-locator"',{json.dumps(json.dumps(module("episode-locator")))});
const code=stripTypeScriptTypes(source);
const {{GET}}=await import("data:text/javascript;base64,"+Buffer.from(code).toString("base64"));
let calls=0;globalThis.fetch=async()=>{{calls++;throw Error("no backend call allowed")}};
process.env.CARERELAY_API_TOKEN="synthetic-bootstrap-only";process.env.CARERELAY_LOOPBACK_TEST="1";
const good=GET(new NextRequest("http://127.0.0.1:8140/example?redirect=https://attacker.invalid"));
process.env.CARERELAY_API_TOKEN="";
const bad=GET(new NextRequest("http://127.0.0.1:8140/example"));
console.log(JSON.stringify({{calls,status:good.status,location:good.headers.get("location"),cookie:good.headers.get("set-cookie"),
 badStatus:bad.status,badLocation:bad.headers.get("location"),badCookie:bad.headers.get("set-cookie")}}));''')
    assert result["status"] == result["badStatus"] == 303
    assert result["location"] == "/"
    assert result["badLocation"] == "/?recovery=1"
    assert result["badCookie"] is None
    assert result["calls"] == 0
    assert isinstance(result["cookie"], str)
    assert "HttpOnly" in result["cookie"] and "SameSite=lax" in result["cookie"]
    assert "Domain=" not in result["cookie"] and "Secure" not in result["cookie"]
