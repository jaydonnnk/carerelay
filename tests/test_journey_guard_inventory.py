"""Independent boundary guards. No network or engine resources are opened."""
import copy
import base64
import hashlib
import hmac
import json
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from carerelay.demo import fixture
from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import CommandInvalid, canonical, request_digest, validate_binding

ROOT = Path(__file__).resolve().parents[1]
DECODER_CASES = json.loads((Path(__file__).with_name("journey_decoder_cases.json")).read_text())


def change_body(body, changes):
    def parent(path):
        parts = path.split(".")
        target = body
        for key in parts[:-1]: target = target[int(key) if isinstance(target, list) else key]
        return target, int(parts[-1]) if isinstance(target, list) else parts[-1]
    for change in changes:
        target, key = parent(change["path"])
        if change["op"] == "copy":
            source, source_key = parent(change["from_path"])
            target[key] = copy.deepcopy(source[source_key])
        elif change["op"] == "duplicate":
            source = copy.deepcopy(target[key])
            destination, destination_key = parent(change["destination"])
            destination[destination_key].append(source)
        else:
            value = change["value"]
            if isinstance(value, dict) and "repeat" in value: value = value["repeat"] * value["count"] + value.get("suffix", "")
            target[key] = value


def decoder_case_body(tmp_path, case):
    from _journey_fixtures import seed_journey
    from test_journey_commands import command_service, s15_binding
    from carerelay.presentation import journey_surface
    service = command_service(tmp_path / (case["id"] + ".sqlite"))
    episode = "decoder-extra-" + case["id"]
    try:
        if case["trusted_screen"] == "start_created": service.start_example(s15_binding(episode=episode))
        else: seed_journey(service, episode, case["trusted_screen"])
        if any("record_hint_event" in s for s in case["trusted_setup"]): service.record_hint_event(episode, "H2", "shown")
        body = journey_surface(service.project_journey(episode))
    finally:
        service._store.close()
    return body


@pytest.mark.parametrize("case", DECODER_CASES, ids=lambda row: row["id"])
def test_remaining_decoder_guard(tmp_path, case):
    good = decoder_case_body(tmp_path, case)
    bad = copy.deepcopy(good)
    if case["entrypoint"] == "readCommand":
        good = {"receipt": case["good_receipt"], "journey": good}
        bad = copy.deepcopy(good)
    if case["entrypoint"] == "reconcileJourney":
        alternate = dict(case, id=case["id"] + "-next", trusted_screen=case["next_screen"], trusted_setup=[])
        bad = decoder_case_body(tmp_path, alternate)
        bad["episode_id"] = good["episode_id"]
        bad["revision"] = good["revision"] + 1
    else:
        change_body(bad, case["bad_changes"])
    script = '''import {readFileSync} from "node:fs";
import {decodeJourney,readJourney,readCommand,reconcileJourney} from "./frontend/lib/journey.ts";
const [good,bad,caseData]=JSON.parse(readFileSync(0,"utf8"));
const id=good.journey?.episode_id??good.episode_id;
async function decode(body,isBad){try {
 if(caseData.entrypoint==="decodeJourney")return decodeJourney(body,id)===null?"null":"decoded";
 if(caseData.entrypoint==="reconcileJourney")return reconcileJourney(good,body,true)===null?"null":"decoded";
 const status=isBad?(caseData.bad_http_status??caseData.http_status??200):(caseData.http_status??200);
 let bytes=new TextEncoder().encode(JSON.stringify(body));
 if(isBad&&caseData.bad_wire_operation){const text=JSON.stringify(body),start=text.indexOf('"action_text":"')+'"action_text":"'.length;
  bytes[new TextEncoder().encode(text.slice(0,start)).byteLength]=255}
 const response=new Response(bytes,{status,headers:{"Content-Type":"application/json"}});
 const value=caseData.entrypoint==="readCommand"?await readCommand(response,id):await readJourney(response,id);
 return value===null?"null":"decoded";
 }catch{return "threw"}}
console.log(JSON.stringify([await decode(good,false),await decode(bad,true)]));'''
    assert node(script, [good, bad, case]) == ["decoded", "null"]


def binding():
    return OperationBinding("guard-operation", "guard-episode", None, 0, "create",
        "episode:create", request_digest("create", {}), None, None)


BINDING_BAD = {
    "schema": ("token_schema", "unknown"),
    "operation_type": ("operation_id", 1), "operation_empty": ("operation_id", ""),
    "operation_long": ("operation_id", "a" * 129), "episode_format": ("episode_id", "a/b"),
    "revision_type": ("expected_revision", True), "revision_negative": ("expected_revision", -1),
    "revision_unsafe": ("expected_revision", 9007199254740992),
    "version_type": ("disposition_version", True), "version_zero": ("disposition_version", 0),
    "kind": ("kind", "invented"), "purpose_type": ("purpose", 1), "purpose_empty": ("purpose", ""),
    "digest_type": ("body_sha256", 1), "digest_format": ("body_sha256", "A" * 64),
    "parent_type": ("parent_restatement_id", 1), "parent_empty": ("parent_restatement_id", ""),
    "parent_long": ("parent_restatement_id", "a" * 129),
    "confirmation_type": ("confirmation_id", 1), "confirmation_long": ("confirmation_id", "a" * 129),
}


@pytest.mark.parametrize("case", BINDING_BAD)
def test_binding_shape_has_typed_refusal(case):
    good = binding()
    assert validate_binding(good) is None
    field, value = BINDING_BAD[case]
    observed = None
    try:
        validate_binding(replace(good, **{field: value}))
    except Exception as error:
        observed = type(error)
    assert observed is CommandInvalid


@pytest.mark.parametrize("case", ["float", "key", "utf8", "duplicate", "kind", "create", "choice_keys"])
def test_canonical_boundary_refuses_without_normalizing(case):
    from carerelay.journey_commands import _pairs
    assert canonical({"text": " e\u0301 ", "nested": [True, None, 1]}) == b'{"nested":[true,null,1],"text":" e\xcc\x81 "}'
    observed = None
    try:
        if case == "float": canonical({"number": 1.5})
        elif case == "key": canonical({1: "not a string key"})
        elif case == "utf8": canonical({"text": "\ud800"})
        elif case == "duplicate": _pairs([("a", 1), ("a", 2)])
        elif case == "kind": request_digest("invented", {})
        elif case == "create": request_digest("create", {"persona": "chosen"})
        else: request_digest("select_example", {"example_id": "scripted-appointment", "extra": True})
    except Exception as error:
        observed = type(error)
    assert observed is CommandInvalid


@pytest.mark.parametrize("case", ["order", "kind", "legacy", "mixed"])
def test_record_order_is_event_order_with_explicit_legacy_fallback(case):
    from carerelay.state import _order_by_events
    now = fixture.SCENARIO_NOW_UTC
    rows = [{"id": "old"}, {"id": "a"}, {"id": "z"}]
    if case == "order":
        events = [("escalation_recorded", json.dumps({"schema": "record-v1", "record_id": x}), now) for x in ["z", "a", "old"]]
        kind, expected = "escalation_recorded", ["z", "a", "old"]
    elif case == "kind":
        events = [("unrelated", json.dumps({"record_id": "a"}), now)]
        kind, expected = "escalation_recorded", ["old", "a", "z"]
    elif case == "legacy":
        events = [("attempt_opened", "attempt=z route=fictional", now), ("attempt_opened", "attempt=a route=fictional", now)]
        kind, expected = "attempt_opened", ["old", "z", "a"]
    else:
        events = [("escalation_recorded", json.dumps({"schema": "record-v1", "record_id": x}), now) for x in ["z", "a"]]
        kind, expected = "escalation_recorded", ["old", "z", "a"]
    assert [row["id"] for row in _order_by_events(rows, events, kind)] == expected
    assert _order_by_events(rows, [], kind) == tuple(rows)


def node(source, data):
    child = subprocess.run(["node", "--input-type=module", "-e", source], cwd=ROOT,
        input=json.dumps(data), capture_output=True, text=True)
    assert child.returncode == 0, child.stderr
    return json.loads(child.stdout)


ACTION_CASES = ["origin_missing", "host_missing", "username", "password", "search", "hash", "path",
    "host", "insecure", "loopback_disabled", "cookie_missing", "episode", "kind", "operation", "revision",
    "form_missing", "form_duplicate", "form_extra", "form_blob"]


@pytest.mark.parametrize("case", ACTION_CASES)
def test_real_action_refuses_before_backend(case):
    observed = node('''import {readFileSync} from "node:fs";
import {createRequire} from "node:module";
import {createHmac} from "node:crypto";
import * as locator from "./frontend/lib/episode-locator.ts";
const caseName=JSON.parse(readFileSync(0,"utf8"));
const require=createRequire(process.cwd()+"/frontend/package.json"),ts=require("typescript");
const key="synthetic-guard-key",a=locator.newLocator(),b=locator.newLocator();
let context={origin:"http://127.0.0.1:8176",host:"127.0.0.1:8176",cookie:locator.encodeLocator(a,key)};
let token=locator.creationOperation(a,key),fields=null,loopback=true;
function signed(body){const raw=JSON.stringify(Object.fromEntries(Object.keys(body).sort().map(k=>[k,body[k]])));
 const payload=Buffer.from(raw).toString("base64url"),separated=createHmac("sha256",key).update("carerelay:command:v1").digest();
 return payload+"."+createHmac("sha256",separated).update(payload).digest("base64url")}
const mod={exports:{}};let calls=0;
const code=ts.transpileModule(readFileSync("frontend/app/actions.ts","utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
new Function("require","module","exports",code)(name=>{
 if(name==="next/headers")return {headers:async()=>({get:k=>context[k]??null}),cookies:async()=>({get:()=>context.cookie?{value:context.cookie}:undefined})};
 if(name==="@/lib/episode-locator")return locator;
 if(name==="@/lib/api")return {createCommand:async()=>{calls++;return {ok:false}},selectExampleCommand:async()=>{calls++;return {ok:false}}};
 throw Error(name);
},mod,mod.exports);
process.env.CARERELAY_API_TOKEN=key;process.env.CARERELAY_LOOPBACK_TEST="1";
async function run(){let f=new FormData();for(const [k,v]of fields??[["operation_token",token]])f.append(k,v);await mod.exports.startExample(null,f)}
await run();const good=calls;calls=0;
if(caseName==="origin_missing")context.origin=null;
if(caseName==="host_missing")context.host=null;
for(const part of ["username","password","search","hash","path"])if(caseName===part){
 const url=new URL(context.origin); if(part==="username")url.username="caller";if(part==="password")url.password="synthetic";
 if(part==="search")url.search="?x=1";if(part==="hash")url.hash="#x";if(part==="path")url.pathname="/wrong";context.origin=url.toString()}
if(caseName==="host")context.host="foreign.invalid";
if(caseName==="insecure")context={...context,origin:"http://care.invalid",host:"care.invalid"};
if(caseName==="loopback_disabled")process.env.CARERELAY_LOOPBACK_TEST="0";
if(caseName==="cookie_missing")context.cookie=undefined;
if(["episode","kind","operation","revision"].includes(caseName)){
 const body=locator.decodeOperation(token,key);if(caseName==="kind"){body.kind="select_example";body.purpose="episode:select_example"}
 if(caseName==="episode")body.episode_id=b.episode_id;
 if(caseName==="operation")body.operation_id="other-operation";if(caseName==="revision")body.expected_revision=1;token=signed(body)}
if(caseName==="form_missing")fields=[];
if(caseName==="form_duplicate")fields=[["operation_token",token],["operation_token",token]];
if(caseName==="form_extra")fields=[["operation_token",token],["example_id","other"]];
if(caseName==="form_blob")fields=[["operation_token",new Blob([token])]];
await run();console.log(JSON.stringify({good,bad:calls}));''', case)
    assert observed == {"good": 1, "bad": 0}


@pytest.mark.parametrize("case", ["key_type", "key_empty", "key_spaces", "token_limit", "payload_base64", "body_canonical", "schema_key"])
def test_signed_token_transport_has_independent_typed_refusal(case):
    from dataclasses import asdict
    from carerelay.journey_commands import _key, issue_operation, verify_operation
    key = b"synthetic-token-guard"
    good = binding()
    assert verify_operation(issue_operation(good, signing_key=key), signing_key=key) == good
    body = asdict(good)
    def signed(raw, encoded=None):
        payload = encoded or base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
        separated = hmac.digest(key, b"carerelay:command:v1", "sha256")
        mac = base64.urlsafe_b64encode(hmac.digest(separated, payload.encode(), "sha256")).rstrip(b"=").decode()
        return payload + "." + mac
    observed = None
    try:
        if case.startswith("key_"):
            _key({"key_type": "wrong type", "key_empty": b"", "key_spaces": b" "}[case])
        elif case == "token_limit":
            token = issue_operation(replace(good, purpose="a" * 4000), signing_key=key)
            assert len(token) > 4096
            verify_operation(token, signing_key=key)
        elif case == "body_canonical":
            verify_operation(signed(json.dumps(body, indent=1).encode()), signing_key=key)
        elif case == "schema_key":
            del body["token_schema"]
            verify_operation(signed(canonical(body)), signing_key=key)
        else:
            raw = canonical(body)
            # Make the final base64 character carry nonzero unused padding bits.
            while len(raw) % 3 == 0:
                body["purpose"] += "a"
                raw = canonical(body)
            payload = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            changed = next(payload[:-1] + c for c in alphabet if c != payload[-1] and
                base64.urlsafe_b64decode(payload[:-1] + c + "=" * (-len(payload) % 4)) == raw)
            verify_operation(signed(raw, changed), signing_key=key)
    except Exception as error:
        observed = type(error)
    assert observed is CommandInvalid


@pytest.mark.parametrize("case", ["claim_episode", "snapshot_episode", "bundle_episode", "nested_episode", "read_to_write", "terminal_replay"])
def test_receipt_transaction_scope_and_terminal_replay(tmp_path, case):
    from carerelay.state import SqliteEpisodeStore, StateError
    from carerelay.journey_commands import CommandConflict
    now = fixture.SCENARIO_NOW_UTC
    with SqliteEpisodeStore(tmp_path / "scope.sqlite") as store:
        store.create_episode("guard-episode", "fictional", now_utc=now)
        store.create_episode("other-episode", "fictional", now_utc=now)
        with store.journey_transaction("guard-episode", write=case != "read_to_write") as tx:
            good = replace(binding(), expected_revision=tx.load_bundle("guard-episode").revision)
            if case == "terminal_replay":
                tx.claim_once(good, now_utc=now)
                first = tx.complete_once(good.operation_id, state="applied", result_ref="first", scored=False, now_utc=now)
                before = list(store._conn.iterdump())
                observed = None
                try:
                    again = tx.complete_once(good.operation_id, state="refused", result_ref="changed", scored=False, now_utc=now)
                    observed = (again.state, again.result_ref, again.replayed)
                except Exception:
                    pass
                assert observed == ("applied", "first", True)
                assert list(store._conn.iterdump()) == before
            else:
                before = list(store._conn.iterdump())
                observed = None
                try:
                    if case == "claim_episode": tx.claim_once(replace(good, episode_id="other-episode"), now_utc=now)
                    elif case == "snapshot_episode": tx.load_snapshot("other-episode")
                    elif case == "bundle_episode": tx.load_bundle("other-episode")
                    else:
                        with store.journey_transaction("other-episode" if case == "nested_episode" else "guard-episode", write=True):
                            pass
                except Exception as error:
                    observed = type(error)
                assert observed is (CommandConflict if case == "claim_episode" else StateError)
                assert list(store._conn.iterdump()) == before


@pytest.mark.parametrize("case", ["kind", "purpose", "choice", "date", "prepare_parent", "prepare_digest", "prepare_offer", "url_episode"])
def test_intake_and_preparation_refusals_preserve_real_record(tmp_path, case, monkeypatch):
    from datetime import timedelta
    from carerelay.journey_commands import CommandConflict, issue_operation
    from carerelay.service import ScenarioClock
    from test_journey_commands import command_service, s15_binding, selected_binding, S15_KEY
    from carerelay.api import app, get_service
    from fastapi.testclient import TestClient
    service = command_service(tmp_path / "intake-guards.sqlite")
    good = s15_binding()
    service.start_example(good)
    selected = selected_binding(service)
    if case == "url_episode": service.ensure_episode("other-episode", "fictional")
    before = list(service._store._conn.iterdump())
    observed = None
    try:
        try:
            if case == "kind": service.select_example(replace(selected, kind="create"), example_id="scripted-appointment")
            elif case == "purpose": service.select_example(replace(selected, purpose="caller-purpose"), example_id="scripted-appointment")
            elif case == "choice":
                service.select_example(replace(selected, body_sha256=request_digest("select_example", {"example_id": "other"})), example_id="other")
            elif case == "date":
                service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(days=1))
                service.select_example(selected, example_id="scripted-appointment")
            elif case.startswith("prepare_"):
                if case == "prepare_offer": service.select_example(selected, example_id="scripted-appointment"); before = list(service._store._conn.iterdump())
                service.prepare_command(good.episode_id, kind="select_example", body_sha256="f" * 64 if case == "prepare_digest" else selected.body_sha256,
                    parent_id="caller-parent" if case == "prepare_parent" else None)
            else:
                monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-route-key")
                app.dependency_overrides[get_service] = lambda: service
                with TestClient(app, headers={"Authorization": "Bearer synthetic-route-key"}) as client:
                    response = client.post("/api/episodes/other-episode/intake", json={"operation_token": issue_operation(selected, signing_key=S15_KEY), "example_id": "scripted-appointment"})
                    assert response.status_code == 409
                    observed = CommandConflict
        except Exception as error:
            observed = type(error)
        assert observed is (CommandConflict if case == "url_episode" else CommandInvalid)
        assert list(service._store._conn.iterdump()) == before
        service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC)
        if case != "prepare_offer": assert service.select_example(selected, example_id="scripted-appointment").receipt.state == "applied"
    finally:
        app.dependency_overrides.clear()
        service._store.close()


LOCATOR_CASES = ["keys", "schema", "nonce", "episode", "operation", "uuid_type", "key", "length", "signature_canonical",
    "operation_mac", "operation_payload", "operation_body", "operation_fields", "operation_trailing_segment", "op_schema",
    "op_revision_safe", "op_revision_negative", "op_id", "op_episode", "op_digest", "op_version", "op_parent",
    "op_confirmation", "op_kind", "op_purpose"]


@pytest.mark.parametrize("case", LOCATOR_CASES)
def test_locator_and_operation_shape_have_real_signed_controls(case):
    assert node('''import {readFileSync} from "node:fs";import {createHmac} from "node:crypto";
import * as c from "./frontend/lib/episode-locator.ts";
const test=JSON.parse(readFileSync(0,"utf8")),key="synthetic-locator-shape",a=c.newLocator();
function sign(raw,domain,payload=Buffer.from(raw).toString("base64url")){
 const separated=createHmac("sha256",key).update(domain).digest();return payload+"."+createHmac("sha256",separated).update(payload).digest("base64url")}
function padding(text){const bytes=Buffer.from(text,"base64url"),alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
 return [...alphabet].map(ch=>text.slice(0,-1)+ch).find(value=>value!==text&&Buffer.from(value,"base64url").equals(bytes))}
const cookie=c.encodeLocator(a,key),token=c.creationOperation(a,key);
const good=c.decodeLocator(cookie,key)?.episode_id===a.episode_id&&c.decodeOperation(token,key)?.episode_id===a.episode_id;
let bad,body=structuredClone(a);
if(test==="key"){let refused=false;try{c.encodeLocator(a,"")}catch{refused=true}bad=refused}
else if(test==="signature_canonical"){const [p,s]=cookie.split(".");bad=c.decodeLocator(p+"."+padding(s),key)===null}
else if(["keys","schema","nonce","episode","operation","uuid_type","length"].includes(test)){
 if(test==="keys")body.extra=true;if(test==="schema")body.schema="unknown";
 if(test==="nonce")body.nonce="wrong";if(test==="episode")body.episode_id="wrong";if(test==="operation")body.operation_id="wrong";
 if(test==="uuid_type")body.nonce=[body.nonce];
 const raw=(test==="length"?" ".repeat(1100):"")+JSON.stringify(body);
 bad=c.decodeLocator(sign(raw,"carerelay:locator:v1"),key)===null
}else{
 body=c.decodeOperation(token,key);
 if(test==="op_schema")body.token_schema="unknown";
 if(test==="op_revision_safe")body.expected_revision=9007199254740992;
 if(test==="op_revision_negative")body.expected_revision=-1;
 if(test==="op_id")body.operation_id="bad/id";if(test==="op_episode")body.episode_id="wrong";
 if(test==="op_digest")body.body_sha256="A".repeat(64);
 if(test==="op_version")body.disposition_version=1;if(test==="op_parent")body.parent_restatement_id="parent";
 if(test==="op_confirmation")body.confirmation_id="confirmation";if(test==="op_kind"){body.kind="request";body.purpose="episode:request"}
 if(test==="op_purpose")body.purpose="caller-purpose";if(test==="operation_fields")body.extra=true;
 function ordered(){return JSON.stringify(Object.fromEntries(Object.keys(body).sort().map(k=>[k,body[k]])))}
 let raw=test==="operation_body"?JSON.stringify(body,null,1):ordered(),payload;
 if(test==="operation_payload"){while(Buffer.byteLength(raw)%3===0){body.operation_id+="a";raw=ordered()}payload=padding(Buffer.from(raw).toString("base64url"))}
 let signed=sign(raw,"carerelay:command:v1",payload);
 if(test==="operation_mac"){const [p,s]=signed.split(".");signed=p+"."+(s[0]==="a"?"b":"a")+s.slice(1)}
 if(test==="operation_trailing_segment")signed=signed+".extra";
 bad=c.decodeOperation(signed,key)===null;
}
console.log(JSON.stringify([good,bad]));''', case) == [True, True]


SQL_REQUIRED = ["operation_id", "phase", "episode_id", "expected_revision", "claim_revision", "kind", "purpose", "body_sha256", "scored", "recorded_at"]


@pytest.mark.parametrize("case", SQL_REQUIRED + ["episode_fk", "parent_fk", "claim_exists", "scored_result_kind"])
def test_receipt_sql_required_values_and_claim_existence(tmp_path, case):
    import sqlite3
    from carerelay.state import SqliteEpisodeStore
    now = fixture.SCENARIO_NOW_UTC
    with SqliteEpisodeStore(tmp_path / "required-sql.sqlite") as store:
        store.create_episode("guard-episode", "fictional", now_utc=now)
        good = dict(operation_id="guard-operation", phase="claimed", episode_id="guard-episode", expected_revision=0,
            claim_revision=0, kind="create", purpose="episode:create", body_sha256="a" * 64, scored=0, recorded_at=now.isoformat())
        if case != "claim_exists": store._conn.execute("DROP TRIGGER journey_commands_claim_binding")
        bad = dict(good)
        if case in SQL_REQUIRED: bad[case] = None
        elif case == "episode_fk": bad["episode_id"] = "absent-episode"
        elif case == "parent_fk": bad["parent_restatement_id"] = "absent-parent"
        elif case == "claim_exists": bad.update(phase="completed", terminal_state="applied", result_kind="episode", result_ref="guard-episode")
        else: bad.update(phase="completed", terminal_state="applied", kind="score_words", result_kind="episode", result_ref="r", scored=1)
        def insert(row):
            store._conn.execute("INSERT INTO journey_commands(" + ",".join(row) + ") VALUES(" + ",".join("?" for _ in row) + ")", tuple(row.values()))
        with pytest.raises(sqlite3.IntegrityError): insert(bad)
        insert(good)
        if case == "claim_exists": insert(bad)
        assert store._conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == (2 if case == "claim_exists" else 1)


@pytest.mark.parametrize("case", ["permission", "pending"])
def test_renderer_announces_each_server_prompt_once(tmp_path, case):
    body = decoder_case_body(tmp_path, {"id": "prompt-" + case, "trusted_screen": case, "trusted_setup": []})
    observed = node('''import {readFileSync} from "node:fs";import {createRequire} from "node:module";
import * as journey from "./frontend/lib/journey.ts";
const body=JSON.parse(readFileSync(0,"utf8")),require=createRequire(process.cwd()+"/frontend/package.json"),ts=require("typescript"),React=require("react");
const mod={exports:{}};const code=ts.transpileModule(readFileSync("frontend/components/PatientJourney.tsx","utf8"),{
 compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
new Function("require","module","exports",code)(name=>{
 if(name==="next/navigation")return {useRouter:()=>({refresh(){}})};
 if(name==="@/app/actions")return {};
 if(name==="@/lib/journey")return journey;
 return require(name);
},mod,mod.exports);
const html=require("react-dom/server").renderToStaticMarkup(React.createElement(mod.exports.PatientJourney,{state:"loaded",journey:body}));
const needle=body.question?.text??body.text.feedback;
console.log(JSON.stringify({count:html.split(needle).length-1,status:(html.match(/role="status"/g)||[]).length}));''', body)
    assert observed == {"count": 1, "status": 1 if case == "pending" else 0}


def assessed_bundle(tmp_path, screen="plan"):
    from _journey_fixtures import seed_journey
    from test_journey_commands import command_service
    service = command_service(tmp_path / ("bundle-" + screen + ".sqlite"))
    episode = "guard-bundle-" + screen
    try:
        seed_journey(service, episode, screen)
        return service._store.load_journey_bundle(episode)
    finally:
        service._store.close()


def corrupt_bundle(case, bundle):
    """Each case removes exactly one recorded-input guarantee from a trusted bundle."""
    from carerelay.domain import rules
    if case == "episode_id":
        return replace(bundle, episode_id=""), None
    if case == "revision_type":
        return replace(bundle, revision=True), None
    if case == "revision_negative":
        return replace(bundle, revision=-1), None
    if case == "revision_unsafe":
        return replace(bundle, revision=9007199254740992), None
    if case == "policy_missing":
        return replace(bundle, policy=None), None
    if case == "policy_text_missing":
        return replace(bundle, policy_text=None), None
    if case == "policy_version":
        return replace(bundle, policy=replace(bundle.policy, version=bundle.policy.version + "-other")), None
    if case == "text_version":
        text = replace(bundle.policy_text, policy_version=bundle.policy_text.policy_version + "-other")
        return replace(bundle, policy_text=text), None
    if case == "action_outside_policy":
        return replace(bundle, policy=replace(bundle.policy, permitted_action_ids=())), None
    if case == "action_text":
        return bundle, dict(rules.JOURNEY_ACTION_TEXT, **{bundle.policy.version: {}})
    if case == "deadline_display":
        return replace(bundle, policy_text=replace(bundle.policy_text, deadline_display_by_version={})), None
    if case == "owner_display":
        return replace(bundle, policy_text=replace(bundle.policy_text, owner_display_by_id={})), None
    if case == "route_display":
        return replace(bundle, policy_text=replace(bundle.policy_text, route_display_by_id={})), None
    if case == "readback_identity":
        payload = json.dumps({"disposition_version": bundle.snapshot.disposition.version, "readback_attempt_id": 7})
        return replace(bundle, events=bundle.events + (("readback_started", payload, fixture.SCENARIO_NOW_UTC),)), None
    raise AssertionError("unclassified case " + case)


BUNDLE_CASES = ["episode_id", "revision_type", "revision_negative", "revision_unsafe", "policy_missing",
    "policy_text_missing", "policy_version", "text_version", "action_outside_policy", "action_text",
    "deadline_display", "owner_display", "route_display", "readback_identity"]


@pytest.mark.parametrize("case", BUNDLE_CASES)
def test_derive_journey_refuses_each_corrupt_recorded_input(tmp_path, case, monkeypatch):
    from carerelay.domain import rules
    bundle = assessed_bundle(tmp_path)
    assert rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC).step == "plan"
    bad, action_text = corrupt_bundle(case, bundle)
    if action_text is not None:
        monkeypatch.setattr(rules, "JOURNEY_ACTION_TEXT", action_text)
    with pytest.raises(rules.JourneyUnavailable):
        rules.derive_journey(bad, now_utc=fixture.SCENARIO_NOW_UTC)


@pytest.mark.parametrize("case", ["unrelated_non_dict_event", "foreign_version_event"])
def test_derive_journey_ignores_events_it_does_not_own(tmp_path, case):
    """An event this disposition does not own cannot change or hide the plan."""
    from carerelay.domain import rules
    bundle = assessed_bundle(tmp_path)
    good = rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC)
    version = bundle.snapshot.disposition.version
    extra = (("unrelated_kind", "[1,2]", fixture.SCENARIO_NOW_UTC) if case == "unrelated_non_dict_event"
             else ("readback_started", json.dumps({"disposition_version": version + 1,
                   "readback_attempt_id": "foreign-attempt"}), fixture.SCENARIO_NOW_UTC))
    observed = rules.derive_journey(replace(bundle, events=bundle.events + (extra,)),
                                    now_utc=fixture.SCENARIO_NOW_UTC)
    assert observed == good
    assert observed.step == "plan" and observed.flow.readback_attempt_id is None


@pytest.mark.parametrize("case", ["naive_clock", "later_day"])
def test_derive_journey_refuses_an_unusable_display_date(tmp_path, case):
    from datetime import timedelta, timezone
    from carerelay.domain import rules
    bundle = assessed_bundle(tmp_path, "plan")
    now = fixture.SCENARIO_NOW_UTC
    if case == "naive_clock":
        now = now.replace(tzinfo=None)
    else:
        now = now.astimezone(timezone.utc) + timedelta(days=1)
    with pytest.raises(rules.JourneyUnavailable, match="approved date display unavailable"):
        rules.derive_journey(bundle, now_utc=now)


@pytest.mark.parametrize("case", ["unpermitted_kind", "unpermitted_purpose", "changed_create_body"])
def test_start_refuses_a_capability_it_did_not_issue(tmp_path, case):
    from carerelay.journey_commands import CommandConflict, CommandInvalid, PURPOSES
    from test_journey_commands import command_service, s15_binding
    service = command_service(tmp_path / "start-guards.sqlite")
    good = s15_binding(episode="guard-start")
    bad = {"unpermitted_kind": replace(good, kind="select_example", purpose=PURPOSES["select_example"]),
           "unpermitted_purpose": replace(good, purpose="episode:select_example"),
           "changed_create_body": replace(good, body_sha256="b" * 64)}[case]
    expected = CommandConflict if case == "changed_create_body" else CommandInvalid
    try:
        with pytest.raises(expected):
            service.start_example(bad)
        assert service._store._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 0
        assert service.start_example(good).receipt.state == "applied"
    finally:
        service._store.close()


@pytest.mark.parametrize("case", ["kind_only", "digest_only", "parent_only"])
def test_preparation_requires_kind_and_digest_together(tmp_path, case, monkeypatch):
    from fastapi.testclient import TestClient
    from test_journey_commands import command_service, s15_binding
    from carerelay.api import app, get_service
    service = command_service(tmp_path / "prepare-guards.sqlite")
    service.start_example(s15_binding(episode="guard-prepare"))
    query = {"kind_only": {"prepare_kind": "select_example"},
             "digest_only": {"body_sha256": "c" * 64},
             "parent_only": {"parent_id": "caller-parent"}}[case]
    try:
        monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-route-key")
        app.dependency_overrides[get_service] = lambda: service
        with TestClient(app, headers={"Authorization": "Bearer synthetic-route-key"}) as client:
            response = client.get("/api/episodes/guard-prepare", params=query)
        assert response.status_code == 422
        assert "operation_token" not in response.text
    finally:
        app.dependency_overrides.clear()
        service._store.close()


PROJECTION_CONTRACT = {
    "pending": ("text", "feedback", "Loading. Nothing is confirmed yet."),
    "unavailable": ("text", "feedback", "We could not check that answer just now. Your plan has not changed."),
    "uncertain": ("text", "feedback", "We could not confirm that. Try different words, or show your plan."),
    "waiting": ("text", "status", "No reply yet."),
    "h3_event": ("flow", "effective_hint", "H3"),
    "h3_round": ("flow", "effective_hint", "H3"),
}


@pytest.mark.parametrize("case", PROJECTION_CONTRACT)
def test_each_screen_carries_its_own_recorded_copy_and_cue(tmp_path, case):
    """One screen, one recorded line. Read with .get so a dropped key is a failure."""
    from _journey_fixtures import seed_journey
    from test_journey_commands import command_service
    from carerelay.presentation import journey_surface
    service = command_service(tmp_path / ("contract-" + case + ".sqlite"))
    episode = "guard-contract-" + case
    screen = {"h3_event": "plan", "h3_round": "h3"}.get(case, case)
    try:
        seed_journey(service, episode, screen)
        if case == "h3_event":
            service.record_hint_event(episode, "H3", "shown")
        body = journey_surface(service.project_journey(episode))
    finally:
        service._store.close()
    section, field, expected = PROJECTION_CONTRACT[case]
    assert body[section].get(field) == expected


@pytest.mark.parametrize("case", ["unclaimed", "claimed"])
def test_replay_reports_the_recorded_receipt_or_refuses(tmp_path, case):
    """`service.replay` is the Gate 3 section 9 contract method; no route calls it yet."""
    from carerelay.journey_commands import CommandConflict
    from test_journey_commands import command_service, s15_binding
    service = command_service(tmp_path / "replay-guards.sqlite")
    good = s15_binding(episode="guard-replay")
    try:
        if case == "unclaimed":
            service.ensure_episode("guard-replay", "fictional")
            with pytest.raises(CommandConflict):
                service.replay(good)
        else:
            service.start_example(good)
            response = service.replay(good)
            assert response.receipt.result_ref == "guard-replay" and response.receipt.replayed
    finally:
        service._store.close()


def test_unknown_episode_has_no_snapshot_at_the_store(tmp_path):
    """The legacy patient and ledger reads call `load_snapshot` with no bundle read
    behind it, so this guard is the only thing that refuses an unknown episode there.
    The journey path reaches the same refusal through `_load_bundle` first."""
    from carerelay.state import EpisodeNotFound, SqliteEpisodeStore
    with SqliteEpisodeStore(tmp_path / "unknown-episode.sqlite") as store:
        store.create_episode("known-episode", "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        with pytest.raises(EpisodeNotFound):
            store.load_snapshot("never-created")
        assert store.load_snapshot("known-episode").disposition is None
