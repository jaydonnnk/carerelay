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


# Slice 15 receipts are tested through the real repository and crypto codec.
from dataclasses import asdict, replace
import base64
import hashlib
import hmac
import os
import sqlite3
import sys

from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import (
    CommandConflict, CommandInvalid, PURPOSES, canonical, issue_operation,
    request_digest, verify_operation,
)
from carerelay.state import JourneyTransaction, SqliteEpisodeStore

S15_KEY = b"synthetic-slice15-codec-only"


def test_s16_server_capabilities_decode_at_the_real_frontend_boundary(tmp_path):
    from test_field_repair import start_readback, confirm
    from _legacy_service_probes import KEY
    service = make_service(tmp_path / "frontend-cap.sqlite")
    try:
        ep = start_readback(service, "00000000-0000-4000-8000-000000000016")
        readback = service.project_journey(ep)
        confirm(service, ep, "go to the clinic today before six myself")
        ready = service.project_journey(ep)
        tokens = [o.operation_token for o in (*readback.commands, *ready.commands) if o.operation_token]
        assert tokens
        script = '''import {readFileSync} from "node:fs";
import {decodeOperation} from "./frontend/lib/episode-locator.ts";
const data=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify(data.tokens.map(token=>decodeOperation(token,data.key)!==null)));
'''
        result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
            input=json.dumps({"tokens": tokens, "key": KEY.decode()}), capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == [True] * len(tokens)
    finally:
        service._store.close()


def s15_binding(episode="fictional-s15", operation="fictional-s15-create"):
    return OperationBinding(operation, episode, None, 0, "create", PURPOSES["create"],
                            request_digest("create", {}), None, None)


def test_s15_digest_preserves_exact_words_and_references():
    a = request_digest("score_words", {"text": "today before six", "parent": "a"})
    assert a == request_digest("score_words", {"parent": "a", "text": "today before six"})
    for body in ({"text": "today before six ", "parent": "a"},
                 {"text": "today before six", "parent": "b"},
                 {"text": "today\u00a0before six", "parent": "a"}):
        assert a != request_digest("score_words", body)
    assert canonical({"text": "e\u0301"}) != canonical({"text": "\u00e9"})
    with pytest.raises(CommandInvalid):
        request_digest("create", {"persona": "caller-selected"})
    with pytest.raises(CommandInvalid):
        canonical({"number": float("nan")})


@pytest.mark.parametrize("field,value", [
    ("operation_id", "other-op"), ("episode_id", "other-episode"),
    ("disposition_version", 1), ("expected_revision", 1),
    ("kind", "select_example"), ("purpose", "other-purpose"),
    ("body_sha256", "f" * 64), ("parent_restatement_id", "parent"),
    ("confirmation_id", "confirmation"), ("token_schema", "other-schema"),
])
def test_s15_mac_binds_each_dimension(field, value):
    binding = s15_binding()
    token = issue_operation(binding, signing_key=S15_KEY)
    assert verify_operation(token, signing_key=S15_KEY) == binding
    encoded, signature = token.split(".")
    data = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    data[field] = value
    changed = base64.urlsafe_b64encode(canonical(data)).rstrip(b"=").decode()
    with pytest.raises(CommandInvalid):
        verify_operation(changed + "." + signature, signing_key=S15_KEY)
    with pytest.raises(CommandInvalid):
        verify_operation(token, signing_key=b"rotated-synthetic-key")


def test_s15_create_and_replay_are_one_atomic_operation(tmp_path):
    path = tmp_path / "start.sqlite"
    binding = s15_binding()
    with SqliteEpisodeStore(path) as store:
        first = store.create_with_claim_once(binding, persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        assert first.state == "applied" and not first.scored and not first.replayed
        assert first.result_ref == binding.episode_id
        replay = store.create_with_claim_once(binding, persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        assert replay.replayed and replay.result_ref == first.result_ref
        assert store._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1
        assert store._conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
        rows = store._conn.execute("SELECT * FROM journey_commands ORDER BY id").fetchall()
        assert [r["phase"] for r in rows] == ["claimed", "completed"]
        assert [k for k, _, _ in store.list_events(binding.episode_id)] == ["command_claimed", "episode_created", "command_completed"]
        assert rows[0]["claim_revision"] == rows[1]["claim_revision"] == 1
        with pytest.raises(CommandConflict):
            store.create_with_claim_once(replace(binding, body_sha256="f" * 64), persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        with pytest.raises(CommandConflict):
            store.create_with_claim_once(replace(binding, operation_id="another-operation"), persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC)
    with SqliteEpisodeStore(path) as store:
        assert store.create_with_claim_once(binding, persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC).replayed
        assert len(store.load_journey_bundle(binding.episode_id).commands) == 2


def test_s15_real_crash_before_terminal_rolls_back_create(tmp_path):
    path = tmp_path / "crash.sqlite"
    script = '''
import os,signal
from carerelay.state import SqliteEpisodeStore,JourneyTransaction
from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import PURPOSES,request_digest
from carerelay.demo import fixture
def crash(*args,**kwargs):
    os.kill(os.getpid(),signal.SIGKILL)
JourneyTransaction.complete_once=crash
s=SqliteEpisodeStore(PATH)
b=OperationBinding('fictional-s15-create','fictional-s15',None,0,'create',PURPOSES['create'],request_digest('create',{}),None,None)
s.create_with_claim_once(b,persona='fictional',now_utc=fixture.SCENARIO_NOW_UTC)
'''.replace("PATH", repr(str(path)))
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), APP_DATABASE_URL=":memory:",
               APP_ENV="local", CARERELAY_API_TOKEN="", APP_CLOCK="scenario",
               CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled", PYTHONDONTWRITEBYTECODE="1")
    child = subprocess.run([sys.executable, "-c", script], cwd=ROOT, env=env, capture_output=True, text=True)
    assert child.returncode == -9, child.stderr
    with SqliteEpisodeStore(path) as store:
        for table in ("episodes", "journey_commands", "events"):
            assert store._conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
        assert not store.create_with_claim_once(s15_binding(), persona="fictional", now_utc=fixture.SCENARIO_NOW_UTC).replayed


@pytest.mark.parametrize("field,value", [
    ("operation_id", "other-op"), ("episode_id", "other-episode"),
    ("disposition_version", 1), ("expected_revision", 99),
    ("claim_revision", 2), ("kind", "select_example"),
    ("purpose", "other-purpose"), ("body_sha256", "f" * 64),
    ("parent_restatement_id", "valid-parent"), ("confirmation_id", "confirmation"),
])
def test_s15_terminal_claim_binding_is_an_engine_guard(tmp_path, field, value):
    with SqliteEpisodeStore(tmp_path / "binding.sqlite") as store:
        binding = s15_binding()
        store.create_episode(binding.episode_id, "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        store.create_episode("other-episode", "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        with store.journey_transaction(binding.episode_id, write=True) as tx:
            current = tx.load_bundle(binding.episode_id).revision
            binding = replace(binding, expected_revision=current)
            tx.claim_once(binding, now_utc=fixture.SCENARIO_NOW_UTC)
        if field == "parent_restatement_id":
            # A valid FK prevents a second guard from masking claim-binding removal.
            store._conn.execute("INSERT INTO restatements (id,episode_id,disposition_version,hint_level,input_mode,transcript_confirmed,extracted_json,mismatches,repair_round,outcome,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("valid-parent", binding.episode_id, 1, "H1", "text", 1, "{}", "{}", 0, "not_recalled", fixture.SCENARIO_NOW_UTC.isoformat()))
        claim = dict(store._conn.execute("SELECT * FROM journey_commands").fetchone())
        claim.pop("id")
        complete = dict(claim, phase="completed", terminal_state="applied", result_kind="episode", result_ref=binding.episode_id)
        broken = dict(complete, **{field: value})
        sql = "INSERT INTO journey_commands(" + ",".join(broken) + ") VALUES(" + ",".join("?" for _ in broken) + ")"
        with pytest.raises(sqlite3.IntegrityError, match="matching claim"):
            store._conn.execute(sql, tuple(broken.values()))
        # Independent engine control: the broken row is otherwise admissible.
        store._conn.execute("SAVEPOINT binding_control")
        store._conn.execute("DROP TRIGGER journey_commands_claim_binding")
        store._conn.execute(sql, tuple(broken.values()))
        assert store._conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 2
        store._conn.execute("ROLLBACK TO binding_control")
        store._conn.execute("RELEASE binding_control")
        store._conn.execute(sql, tuple(complete.values()))
        assert store._conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 2


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
        for forbidden in ("createEpisode(", "recordHintEvent(", "showCard(", "hideCard(", 'method: "POST"'):
            assert forbidden not in source, (file, forbidden)
        # Slice 15 permits only an explicit action form, never a render-time call.
        if file != "components/PatientJourney.tsx":
            assert "<form" not in source
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


def command_service(path):
    service = make_service(path)
    service._operation_signing_key = lambda: S15_KEY
    return service


def selected_binding(service, episode="fictional-s15"):
    body = journey_surface(service.project_journey(episode))
    assert len(body["commands"]) == 1
    return verify_operation(body["commands"][0]["operation_token"], signing_key=S15_KEY)


def test_lost_create_and_intake_replay_projects_fresh(tmp_path):
    from carerelay.service import ScenarioClock
    from datetime import timedelta
    service = command_service(tmp_path / "lost.sqlite")
    binding = s15_binding()
    first = service.start_example(binding)
    intake = selected_binding(service)
    # Simulate response loss after each durable commit, followed by explicit replay.
    assert service.start_example(binding).receipt.replayed
    result = service.select_example(intake, example_id="scripted-appointment")
    assert result.receipt.state == "applied"
    service._store.record_flow_stop(binding.episode_id, 1, "reassessment_stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
    replay = service.select_example(intake, example_id="scripted-appointment")
    assert replay.receipt.replayed
    assert replay.journey.step == "stopped" and replay.journey.flow.stopped
    assert replay.journey.revision > result.journey.revision
    assert service.start_example(binding).journey.step == "stopped"
    conn = service._store._conn
    assert conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 4
    assert conn.execute("SELECT COUNT(*) FROM restatements").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
    service._store.close()


@pytest.mark.parametrize("field,value", [
    ("expected_revision", 0), ("disposition_version", 1),
    ("parent_restatement_id", "old-parent"), ("confirmation_id", "old-confirmation"),
])
def test_stale_unclaimed_start_dimensions_make_no_writes(tmp_path, field, value):
    service = command_service(tmp_path / "stale.sqlite")
    service.start_example(s15_binding())
    binding = selected_binding(service)
    changed = replace(binding, **{field: value})
    before = list(service._store._conn.iterdump())
    with pytest.raises(CommandConflict):
        service.select_example(changed, example_id="scripted-appointment")
    assert list(service._store._conn.iterdump()) == before
    service._store.close()


def test_body_digest_conflict_has_fresh_authenticated_journey(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from carerelay.api import app, get_service
    token = "synthetic-s15-api-only"
    monkeypatch.setenv("CARERELAY_API_TOKEN", token)
    monkeypatch.setenv("APP_ENV", "local")
    service = command_service(tmp_path / "conflict.sqlite")
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app, headers={"Authorization": "Bearer " + token}) as client:
            binding = s15_binding()
            create = client.post("/api/episodes", json={"operation_token": issue_operation(binding, signing_key=S15_KEY)})
            assert create.status_code == 200
            intake = selected_binding(service)
            original = issue_operation(intake, signing_key=S15_KEY)
            assert client.post(f"/api/episodes/{binding.episode_id}/intake", json={"operation_token": original, "example_id": "scripted-appointment"}).status_code == 200
            before = list(service._store._conn.iterdump())
            conflicting = issue_operation(replace(intake, body_sha256="f" * 64), signing_key=S15_KEY)
            conflict = client.post(f"/api/episodes/{binding.episode_id}/intake", json={"operation_token": conflicting, "example_id": "scripted-appointment"})
            assert conflict.status_code == 409
            assert conflict.json()["journey"]["episode_id"] == binding.episode_id
            assert conflict.json()["journey"]["step"] == "plan"
            assert list(service._store._conn.iterdump()) == before
            for bad in [original[:-1] + ("a" if original[-1] != "a" else "b"), "garbage"]:
                assert client.post("/api/episodes", json={"operation_token": bad}).status_code == 422
            assert list(service._store._conn.iterdump()) == before
    finally:
        app.dependency_overrides.clear()
        service._store.close()


def test_pending_and_terminal_replay(tmp_path):
    service = command_service(tmp_path / "pending.sqlite")
    service.start_example(s15_binding())
    binding = selected_binding(service)
    with service._store.journey_transaction(binding.episode_id, write=True) as tx:
        claim = tx.claim_once(binding, now_utc=fixture.SCENARIO_NOW_UTC)
        assert claim.newly_claimed
    result = service.select_example(binding, example_id="scripted-appointment")
    assert result.receipt.state == "pending" and result.receipt.replayed
    assert result.journey.flow.interpretation == "pending"
    assert result.journey.commands == ()
    assert service._store._conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 0
    service._store.close()


def test_two_connections_create_and_intake_once(tmp_path):
    import threading
    path = tmp_path / "race.sqlite"
    a, b = command_service(path), command_service(path)
    barrier = threading.Barrier(2)
    errors, results = [], []
    def run(service, operation):
        try:
            barrier.wait(timeout=5)
            results.append(operation(service))
        except BaseException as error:
            errors.append(repr(error))
    for operation in [lambda s: s.start_example(s15_binding()),
                      lambda s: s.select_example(selected_binding(a), example_id="scripted-appointment")]:
        # Preparation must precede the intake race; both workers use the exact same token.
        if results:
            intake = selected_binding(a)
            operation = lambda s: s.select_example(intake, example_id="scripted-appointment")
        results.clear()
        threads = [threading.Thread(target=run, args=(s, operation)) for s in (a,b)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=10)
        assert not any(t.is_alive() for t in threads)
        assert errors == []
        assert sorted(r.receipt.replayed for r in results) == [False, True]
    assert a._store._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0] == 1
    assert a._store._conn.execute("SELECT COUNT(*) FROM dispositions").fetchone()[0] == 1
    assert a._store._conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 4
    a._store.close(); b._store.close()


def test_real_crash_before_intake_terminal_rolls_back_disposition(tmp_path):
    path = tmp_path / "intake-crash.sqlite"
    service = command_service(path)
    service.start_example(s15_binding())
    binding = selected_binding(service)
    before = list(service._store._conn.iterdump())
    service._store.close()
    script = '''
import os,signal
from test_journey_commands import command_service
from carerelay.state import JourneyTransaction
from carerelay.domain.models import OperationBinding
def crash(*a,**k): os.kill(os.getpid(),signal.SIGKILL)
JourneyTransaction.complete_once=crash
s=command_service(PATH)
s.select_example(OperationBinding(**BINDING),example_id='scripted-appointment')
'''.replace("PATH", repr(str(path))).replace("BINDING", repr(asdict(binding)))
    env = dict(os.environ, PYTHONPATH=str(ROOT/"src") + os.pathsep + str(ROOT/"tests"), APP_DATABASE_URL=":memory:",
               APP_ENV="local", CARERELAY_API_TOKEN="", APP_CLOCK="scenario",
               CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled", PYTHONDONTWRITEBYTECODE="1")
    child = subprocess.run([sys.executable,"-c",script],cwd=ROOT,env=env,capture_output=True,text=True)
    assert child.returncode == -9, child.stderr
    service = command_service(path)
    assert list(service._store._conn.iterdump()) == before
    assert service.select_example(binding,example_id="scripted-appointment").receipt.state == "applied"
    service._store.close()


def test_additive_migration_twice_preserves_old_histories(tmp_path):
    import importlib.util
    from _journey_fixtures import seed_journey
    from carerelay.coordinator import LocalSimulationCoordinator
    from carerelay.tools import McpTools
    from carerelay.simulated_provider import ScriptedProvider
    source = subprocess.check_output(["git", "show", "b91a4ad248fbd22e407b9536f1825d62b52ae8c2:src/carerelay/state.py"], cwd=ROOT)
    old_path = tmp_path / "old_state.py"
    old_path.write_bytes(source)
    spec = importlib.util.spec_from_file_location("carerelay_preupgrade_state", old_path)
    old = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = old
    spec.loader.exec_module(old)
    path = tmp_path / "migration.sqlite"
    service = command_service(":memory:")
    service._store.close()
    service._store = old.SqliteEpisodeStore(path, check_same_thread=False)
    service._coordinator = LocalSimulationCoordinator(McpTools(service._store,
        policy=fixture.policy(), provider=ScriptedProvider(), now=lambda: service._clock.now_utc()))
    cases = ["start", "plan", "stopped", "accepted", "handoff", "expired", "h3", "failed"]
    for case in cases:
        service._clock = __import__("carerelay.service", fromlist=["ScenarioClock"]).ScenarioClock(fixture.SCENARIO_NOW_UTC)
        service._store.create_episode("old-" + case, "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        seed_journey(service, "old-" + case, case)
        if case == "expired": service.project_patient("old-" + case)
    conn = service._store._conn
    old_tables = old.APPEND_ONLY_TABLES
    before = {table: [tuple(r) for r in conn.execute("SELECT * FROM " + table)] for table in old_tables}
    assert "journey_commands" not in {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    service._store.close()
    with SqliteEpisodeStore(path) as upgraded:
        from carerelay.state import _SCHEMA_SQL, _append_only_ddl
        for _ in range(2):
            upgraded._conn.executescript(_SCHEMA_SQL)
            upgraded._conn.executescript(_append_only_ddl())
        assert {table: [tuple(r) for r in upgraded._conn.execute("SELECT * FROM " + table)] for table in old_tables} == before
        from carerelay.state import APPEND_ONLY_TABLES
        assert set(APPEND_ONLY_TABLES) == set(old_tables) | {"journey_commands"}
        assert upgraded._conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert upgraded._conn.execute("PRAGMA foreign_key_check").fetchall() == []
    service = command_service(path)
    for case in cases:
        body = journey_surface(service.project_journey("old-" + case))
        expected = {"start":"start", "plan":"plan", "stopped":"stopped", "accepted":"accepted", "handoff":"handoff", "expired":"expired", "h3":"stopped", "failed":"unresolved"}[case]
        assert body["step"] == expected
        if case != "start": assert body["plan"]["deadline_utc"] == "2026-09-30T10:00:00+00:00"
    assert {table: [tuple(r) for r in service._store._conn.execute("SELECT * FROM " + table)] for table in old_tables} == before
    service._store.close()
    # Fresh interpreter exercises migrated legacy rows, not a current-schema seed.
    script = """
import json
from fastapi.testclient import TestClient
from carerelay.api import app
with TestClient(app,headers={'Authorization':'Bearer synthetic-migration-only'}) as c:
 output={}
 for case in CASES:
  r=c.get('/api/episodes/old-'+case)
  output[case]={'status':r.status_code,'step':r.json().get('step'),'deadline':(r.json().get('plan') or {}).get('deadline_utc')}
 print(json.dumps(output))
""".replace("CASES",repr(cases))
    env=dict(os.environ,PYTHONPATH=str(ROOT/"src"),APP_DATABASE_URL=str(path),APP_ENV="local",APP_CLOCK="scenario",
             CARERELAY_API_TOKEN="synthetic-migration-only",CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled",PYTHONDONTWRITEBYTECODE="1")
    child=subprocess.run([sys.executable,"-c",script],cwd=ROOT,env=env,capture_output=True,text=True)
    assert child.returncode==0,child.stderr
    output=json.loads(child.stdout)
    for case in cases:
        assert output[case]["status"]==200
        assert output[case]["step"]=={"start":"start","plan":"plan","stopped":"stopped","accepted":"accepted","handoff":"handoff","expired":"expired","h3":"stopped","failed":"unresolved"}[case]
        assert output[case]["deadline"]==(None if case=="start" else "2026-09-30T10:00:00+00:00")


SCHEMA_CASES = {
    "phase": {"phase": "wrong"},
    "kind": {"kind": "wrong"},
    "digest_length": {"body_sha256": "a" * 63},
    "digest_character": {"body_sha256": "a" * 63 + "G"},
    "expected_revision": {"expected_revision": -1},
    "claim_revision": {"claim_revision": -1},
    "claimed_terminal": {"terminal_state": "applied"},
    "claimed_result_kind": {"result_kind": "episode"},
    "claimed_result_ref": {"result_ref": "fictional"},
    "terminal_enum": {"phase": "completed", "terminal_state": "wrong"},
    "completed_terminal_missing": {"phase": "completed"},
    "result_enum": {"phase": "completed", "terminal_state": "applied", "result_kind": "wrong"},
    "scored_enum": {"phase": "completed", "terminal_state": "applied", "kind": "score_words", "result_kind": "restatement", "result_ref": "r", "scored": 2},
    "scored_terminal": {"phase": "completed", "terminal_state": "refused", "kind": "score_words", "result_kind": "restatement", "result_ref": "r", "scored": 1},
    "scored_kind": {"phase": "completed", "terminal_state": "applied", "kind": "create", "result_kind": "restatement", "result_ref": "r", "scored": 1},
    "scored_result_kind_null": {"phase": "completed", "terminal_state": "applied", "kind": "score_words", "result_ref": "r", "scored": 1},
    "scored_result_ref_null": {"phase": "completed", "terminal_state": "applied", "kind": "score_words", "result_kind": "restatement", "scored": 1},
}


@pytest.mark.parametrize("case", SCHEMA_CASES)
def test_command_schema_constraints(tmp_path, case):
    with SqliteEpisodeStore(tmp_path / "constraints.sqlite") as store:
        store.create_episode("fictional", "fictional", now_utc=fixture.SCENARIO_NOW_UTC)
        # Isolate CHECK constraints from the separately tested matching-claim trigger.
        store._conn.execute("DROP TRIGGER journey_commands_claim_binding")
        good = dict(operation_id="fixture", episode_id="fictional", phase="claimed",
                    expected_revision=0, claim_revision=0, kind="create", purpose="episode:create",
                    body_sha256="a" * 64, scored=0, recorded_at=fixture.SCENARIO_NOW_UTC.isoformat())
        bad = dict(good, **SCHEMA_CASES[case])
        sql = "INSERT INTO journey_commands(" + ",".join(bad) + ") VALUES(" + ",".join("?" for _ in bad) + ")"
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            store._conn.execute(sql, tuple(bad.values()))
        columns = list(good)
        store._conn.execute("INSERT INTO journey_commands(" + ",".join(columns) + ") VALUES(" + ",".join("?" for _ in columns) + ")", tuple(good.values()))
        assert store._conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 1


def test_claim_and_terminal_uniqueness(tmp_path):
    service = command_service(tmp_path / "uniqueness.sqlite")
    service.start_example(s15_binding())
    conn = service._store._conn
    for phase in ["claimed", "completed"]:
        row = dict(conn.execute("SELECT * FROM journey_commands WHERE phase=?", (phase,)).fetchone())
        row.pop("id")
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
            conn.execute("INSERT INTO journey_commands(" + ",".join(row) + ") VALUES(" + ",".join("?" for _ in row) + ")", tuple(row.values()))
    assert conn.execute("SELECT COUNT(*) FROM journey_commands").fetchone()[0] == 2
    service._store.close()


def s17_frontend_token(kind, *, purpose=None, parent=None, confirmation=None, **dimensions):
    """Sign exact test capabilities so decoding is tested independently of issuance."""
    payload = dict(operation_id="frontend-s17-op", episode_id="00000000-0000-4000-8000-000000000017",
        disposition_version=1, expected_revision=5, kind=kind,
        purpose=purpose or f"disposition:1:{'request_appointment' if kind == 'request' else kind}",
        body_sha256="a" * 64, parent_restatement_id=parent, confirmation_id=confirmation,
        token_schema="carerelay-command-v1")
    payload.update(dimensions)
    wire = base64.urlsafe_b64encode(canonical(payload)).rstrip(b"=").decode()
    separated = hmac.new(S15_KEY, b"carerelay:command:v1", hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(hmac.new(separated, wire.encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    return wire + "." + signature


def test_s17_permission_capabilities_have_exact_fixed_purpose_and_no_readback_refs():
    kinds = ["select_barrier", "grant_share", "decline_share", "revoke_share", "request"]
    good = [s17_frontend_token(kind) for kind in kinds]
    bad = [s17_frontend_token(kind, purpose="disposition:1:caller-chosen") for kind in kinds]
    bad += [s17_frontend_token(kind, parent="parent") for kind in kinds]
    bad += [s17_frontend_token(kind, confirmation="confirmation") for kind in kinds]
    result = node(f'''import {{decodeOperation}} from {json.dumps(module("episode-locator"))};
import {{readFileSync}} from "node:fs";
const d=JSON.parse(readFileSync(0,"utf8"));
console.log(JSON.stringify(d.tokens.map(t=>decodeOperation(t,d.key)!==null)));''',
        {"key": S15_KEY.decode(), "tokens": good + bad})
    assert result == [True] * len(good) + [False] * len(bad)


def test_s17_real_api_distinguishes_auth_refusal_from_unavailable():
    # Execute the API module unchanged apart from its server-only marker and import
    # resolution. Real loopback HTTP returns each status; fetch is not mocked.
    result = node(f'''import {{readFileSync}} from "node:fs";
import {{stripTypeScriptTypes}} from "node:module";
import {{createServer}} from "node:http";
const server=createServer((req,res)=>{{const status=Number(req.url.split('/')[3]);res.writeHead(status,{{'Content-Type':'application/json'}});res.end('{{"detail":"synthetic-control"}}');}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try {{
 process.env.CARERELAY_API_URL='http://127.0.0.1:'+server.address().port;
 let source=readFileSync('frontend/lib/api.ts','utf8').replace('import "server-only";','');
 source=source.replace('"./journey"',{json.dumps(json.dumps(module("journey")))});
 const api=await import('data:text/javascript;base64,'+Buffer.from(stripTypeScriptTypes(source)).toString('base64'));
 const results=[];
 for(const status of [401,503,404]) results.push((await api.getLedger(String(status))).reason);
 console.log(JSON.stringify(results));
}} finally {{await new Promise(resolve=>server.close(resolve));}}''')
    assert result == ["unauthorised", "unavailable", "not_found"]


@pytest.fixture
def s17_permission_projection(tmp_path):
    service = make_service(tmp_path / "frontend-s17-projection.sqlite")
    ep = "00000000-0000-4000-8000-000000000017"
    try:
        service.ensure_episode(ep, "fictional")
        service.intake(ep, fixture.BOUND_COMPLAINT)
        body = journey_surface(service.project_journey(ep))
    finally:
        service._store.close()
    body["step"] = "permission"
    body["commands"] = [{"kind": k, "offer_id": k, "permitted_choice_ids": [],
        "operation_token": s17_frontend_token(k)} for k in ("grant_share", "decline_share", "request")]
    body["question"] = {"question_id": "permission", "text": "May we share your plan?", "choices": []}
    body["text"] = dict(heading="May we share your plan?", description="With the fictional provider, to request an appointment.",
        shared="Shared: the action and deadline. No caregiver message.", consent_label="I agree to share this plan.",
        consent_error="Agree above, or choose “Not now”.", request_label="Try the simulated request", decline_label="Not now")
    return body


def test_s17_permission_decoder_allows_only_separate_permission_commands(s17_permission_projection):
    good = s17_permission_projection
    bad = copy.deepcopy(good)
    bad["commands"][0]["kind"] = "caller_dispatch"
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from "node:fs";
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.map(x=>decodeJourney(x,x.episode_id)!==null)));''', [good, bad])
    assert result == [True, False]


def test_s17_permission_decoder_refuses_request_on_waiting_stopped_or_redacted(s17_permission_projection):
    good = s17_permission_projection
    variants = []
    for case in ("waiting", "stopped", "redacted", "expired", "choices", "null_token"):
        bad = copy.deepcopy(good)
        if case == "waiting":
            bad["outcome"]["execution"] = bad["execution"] = "attempted"
            bad["question"] = None
            bad["text"] = dict(heading="May we share your plan?", status="No reply yet.", notice="Simulated request.")
        elif case == "stopped":
            bad["flow"].update(stopped=True, stop_reason="h3", stopped_disposition_version=1)
        elif case == "redacted":
            bad["plan_redacted"] = True
        elif case == "expired":
            bad["outcome"]["expiry_recorded"] = True
        elif case == "choices":
            bad["commands"][-1]["permitted_choice_ids"] = ["booking"]
        else:
            bad["commands"][-1]["operation_token"] = None
        variants.append(bad)
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from "node:fs";
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.map(x=>decodeJourney(x,x.episode_id)!==null)));''', [good] + variants)
    assert result == [True] + [False] * len(variants)


def test_s17_real_frontend_command_routes_and_choice_digest(s17_permission_projection):
    good = s17_permission_projection
    result = node(f'''import {{readFileSync}} from 'node:fs';
import {{stripTypeScriptTypes}} from 'node:module';
import {{createServer}} from 'node:http';
import {{createHash}} from 'node:crypto';
import * as codec from {json.dumps(module("episode-locator"))};
const d=JSON.parse(readFileSync(0,'utf8'));const calls=[];
const server=createServer(async(req,res)=>{{let body='';for await(const part of req)body+=part;
 calls.push({{method:req.method,url:req.url,body:body?JSON.parse(body):null}});
 res.writeHead(200,{{'Content-Type':'application/json'}});
 res.end(JSON.stringify(req.method==='GET'?{{operation_token:'synthetic.signature'}}:
 {{receipt:{{operation_id:'synthetic-operation',state:'applied',result_ref:'synthetic-reference',scored:false,replayed:false}},journey:d}}));}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
try{{process.env.CARERELAY_API_URL='http://127.0.0.1:'+server.address().port;
 let source=readFileSync('frontend/lib/api.ts','utf8').replace('import "server-only";','');
 source=source.replace('"./journey"',{json.dumps(json.dumps(module("journey")))});
 const api=await import('data:text/javascript;base64,'+Buffer.from(stripTypeScriptTypes(source)).toString('base64'));
 const present=typeof api.prepareBarrierCommand==='function'&&typeof api.permissionCommand==='function'&&typeof codec.barrierChoiceDigest==='function';
 let outcomes=[];let rejected=[];let digest=null;
 if(present){{digest=codec.barrierChoiceDigest('booking');outcomes.push((await api.prepareBarrierCommand(d.episode_id,digest)).ok);
 for(const kind of ['select_barrier','grant_share','decline_share','revoke_share','request']) outcomes.push((await api.permissionCommand(d.episode_id,'synthetic.signature',kind,kind==='select_barrier'?'booking':undefined)).ok);}}
 if(present){{for(const choice of ['unapproved',undefined])rejected.push((await api.permissionCommand(d.episode_id,'synthetic.signature','select_barrier',choice)).ok);}}
 console.log(JSON.stringify({{present,calls,outcomes,rejected,digest}}));
}}finally{{await new Promise(resolve=>server.close(resolve));}}''', good)
    assert result["present"] is True
    assert result["outcomes"] == [True] * 6
    assert result["rejected"] == [False, False]
    expected_digest = hashlib.sha256(canonical({"kind": "select_barrier", "payload": {"choice_id": "booking"}, "schema": "carerelay-command-v1"})).hexdigest()
    assert result["digest"] == expected_digest
    from urllib.parse import parse_qs, urlsplit
    prepared = result["calls"][0]
    assert prepared["method"] == "GET" and prepared["body"] is None
    assert parse_qs(urlsplit(prepared["url"]).query) == {"prepare_kind": ["select_barrier"], "body_sha256": [expected_digest]}
    writes = result["calls"][1:]
    base = "/api/episodes/" + good["episode_id"]
    assert [call["url"] for call in writes] == [base + suffix for suffix in ("/barriers", "/consents", "/consents", "/consents", "/actions")]
    assert [call["body"] for call in writes] == [{"operation_token": "synthetic.signature", "choice_id": "booking"}] + [{"operation_token": "synthetic.signature"}] * 4


def test_s17_permission_server_action_rejects_unchecked_and_forged_context(s17_permission_projection):
    result = node(f'''import {{readFileSync}} from 'node:fs';
import {{stripTypeScriptTypes}} from 'node:module';
import {{createServer}} from 'node:http';
import * as codec from {json.dumps(module("episode-locator"))};
const d=JSON.parse(readFileSync(0,'utf8'));let calls=0;
const server=createServer(async(req,res)=>{{calls++;for await(const part of req){{}}
 res.writeHead(200,{{'Content-Type':'application/json'}});res.end(JSON.stringify({{receipt:{{operation_id:'synthetic-operation',state:'applied',result_ref:'synthetic-reference',scored:false,replayed:false}},journey:d.journey}}));}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const load=async source=>import('data:text/javascript;base64,'+Buffer.from(stripTypeScriptTypes(source)).toString('base64'));
try{{process.env.CARERELAY_API_URL='http://127.0.0.1:'+server.address().port;process.env.CARERELAY_API_TOKEN=d.key;process.env.CARERELAY_LOOPBACK_TEST='1';
 let apiSource=readFileSync('frontend/lib/api.ts','utf8').replace('import "server-only";','').replace('"./journey"',{json.dumps(json.dumps(module("journey")))});
 const apiUrl='data:text/javascript;base64,'+Buffer.from(stripTypeScriptTypes(apiSource)).toString('base64');
 const locator={{schema:'carerelay-locator-v1',nonce:'00000000-0000-4000-8000-000000000001',operation_id:'00000000-0000-4000-8000-000000000002',episode_id:d.journey.episode_id}};
 globalThis.s17Context={{origin:'http://127.0.0.1:8140',host:'127.0.0.1:8140',cookie:codec.encodeLocator(locator,d.key)}};
 const ctxUrl='data:text/javascript;base64,'+Buffer.from('export async function headers(){{return new Map([["origin",globalThis.s17Context.origin],["host",globalThis.s17Context.host]])}};export async function cookies(){{return {{get:()=>({{value:globalThis.s17Context.cookie}})}}}}').toString('base64');
 let source=readFileSync('frontend/app/actions.ts','utf8').replace('"next/headers"',JSON.stringify(ctxUrl)).replace('"@/lib/api"',JSON.stringify(apiUrl))
 .replace('"@/lib/episode-locator"',{json.dumps(json.dumps(module("episode-locator")))})
 .replace('"@/lib/journey"',{json.dumps(json.dumps(module("journey")))});
 const actions=await load(source);const present=typeof actions.submitPermission==='function'&&typeof actions.prepareBarrierChoice==='function';const states=[];
 if(present){{
 const form=(kind,token)=>{{const f=new FormData();f.set('kind',kind);f.set('operation_token',token);return f;}};
 const grant=form('grant_share',d.grant);states.push((await actions.submitPermission(grant)).state);
 grant.set('agreed','yes');states.push((await actions.submitPermission(grant)).state);
 const request=form('request',d.request);states.push((await actions.submitPermission(request)).state);
 globalThis.s17Context.origin='https://attacker.invalid';states.push((await actions.submitPermission(request)).state);
 globalThis.s17Context.origin='http://127.0.0.1:8140';globalThis.s17Context.cookie+='forged';states.push((await actions.submitPermission(request)).state);
 globalThis.s17Context.cookie=codec.encodeLocator(locator,d.key);request.set('unexpected','yes');states.push((await actions.submitPermission(request)).state);
 const swapped=form('grant_share',d.request);swapped.set('agreed','yes');states.push((await actions.submitPermission(swapped)).state);
 }}console.log(JSON.stringify({{present,calls,states}}));
}}finally{{await new Promise(resolve=>server.close(resolve));}}''',
        {"key": S15_KEY.decode(), "journey": s17_permission_projection,
         "grant": s17_frontend_token("grant_share"), "request": s17_frontend_token("request")})
    assert result["present"] is True
    assert result["states"] == ["recovery", "loaded", "loaded", "recovery", "recovery", "recovery", "recovery"]
    assert result["calls"] == 2


def test_s17_real_react_render_starts_permission_unchecked_and_barrier_unselected(s17_permission_projection):
    permission = s17_permission_projection
    barrier = copy.deepcopy(permission)
    barrier["step"] = "barrier"
    barrier["commands"] = [{"kind": "select_barrier", "offer_id": "select_barrier", "permitted_choice_ids": ["booking", "transport", "other"], "operation_token": None}]
    barrier["question"] = {"question_id": "barrier", "text": "What makes it difficult?", "choices": [
        {"choice_id": "booking", "text": "Finding an appointment"}, {"choice_id": "transport", "text": "Getting there"}, {"choice_id": "other", "text": "Something else"}]}
    barrier["text"] = dict(heading="What makes it difficult?", description="Choose one.", choice_error="Choose one to continue.", continue_label="Continue")
    result = node(f'''import {{readFileSync}} from 'node:fs';
import ts from {json.dumps((ROOT / "frontend/node_modules/typescript/lib/typescript.js").as_uri())};
import React from {json.dumps((ROOT / "frontend/node_modules/react/index.js").as_uri())};
import {{renderToStaticMarkup}} from {json.dumps((ROOT / "frontend/node_modules/react-dom/server.node.js").as_uri())};
const d=JSON.parse(readFileSync(0,'utf8'));globalThis.s17RenderCalls=0;
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const transpile=s=>ts.transpileModule(s,{{compilerOptions:{{module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}}}).outputText
 .replaceAll('"react"',{json.dumps(json.dumps((ROOT / "frontend/node_modules/react/index.js").as_uri()))})
 .replaceAll('"react/jsx-runtime"',{json.dumps(json.dumps((ROOT / "frontend/node_modules/react/jsx-runtime.js").as_uri()))});
const actionNames=['startExample','selectExample','prepareReadbackWords','submitReadback','prepareBarrierChoice','submitPermission'];
const actions=url(actionNames.map(n=>'export async function '+n+'(){{globalThis.s17RenderCalls++;throw Error("render mutation")}}').join(';'));
const nav=url('export function useRouter(){{return {{refresh(){{}}}}}}');
const hint=url(transpile(readFileSync('frontend/components/HintCard.tsx','utf8')));
let source=readFileSync('frontend/components/PatientJourney.tsx','utf8').replace('"next/navigation"',JSON.stringify(nav))
 .replace('"@/app/actions"',JSON.stringify(actions)).replace('"@/lib/journey"',{json.dumps(json.dumps(module("journey")))})
 .replace('"./HintCard"',JSON.stringify(hint));
const {{PatientJourney}}=await import(url(transpile(source)));
console.log(JSON.stringify({{html:d.map(journey=>renderToStaticMarkup(React.createElement(PatientJourney,{{state:'loaded',journey}}))),calls:globalThis.s17RenderCalls}}));''', [permission, barrier])
    from html.parser import HTMLParser
    class Inputs(HTMLParser):
        def __init__(self):
            super().__init__(); self.inputs = []; self.buttons = []
        def handle_starttag(self, tag, attrs):
            if tag == "input": self.inputs.append(dict(attrs))
            if tag == "button": self.buttons.append(dict(attrs))
    consent, choices = Inputs(), Inputs()
    consent.feed(result["html"][0]); choices.feed(result["html"][1])
    checkboxes = [x for x in consent.inputs if x.get("type") == "checkbox"]
    assert len(checkboxes) == 1 and "checked" not in checkboxes[0]
    assert checkboxes[0].get("id") == "share-plan-consent"
    assert any("disabled" in button for button in consent.buttons)
    assert "I agree to share this plan." in result["html"][0] and "Try the simulated request" in result["html"][0]
    radios = [x for x in choices.inputs if x.get("type") == "radio"]
    assert [x.get("value") for x in radios] == ["booking", "transport", "other"]
    assert all("checked" not in x for x in radios)
    assert "<fieldset" in result["html"][1] and "<legend" in result["html"][1]
    assert result["html"][1].count("What makes it difficult?") == 1
    assert result["html"][1].count("Choose one.") == 1
    assert "<legend>Choose one.</legend>" in result["html"][1]
    assert result["calls"] == 0


def test_s17_actual_server_projections_and_tokens_decode_through_failure_and_stop(tmp_path):
    from test_journey import s17_understood, s17_binding
    from carerelay.domain.models import CallbackResult, ExecutionStatus, Origin
    service = make_service(tmp_path / "frontend-s17-server.sqlite")
    bodies, tokens = [], []
    def capture(ep):
        body = journey_surface(service.project_journey(ep))
        bodies.append(body)
        tokens.extend(o["operation_token"] for o in body["commands"] if o["operation_token"])
    try:
        ep = s17_understood(service)
        capture(ep)
        service.record_barrier_choice(s17_binding(service, ep, "select_barrier", "booking"), choice_id="booking")
        capture(ep)
        service.change_share_consent(s17_binding(service, ep, "decline_share"), granted=False)
        capture(ep)
        service.change_share_consent(s17_binding(service, ep, "grant_share"), granted=True)
        capture(ep)
        service.request_appointment(s17_binding(service, ep, "request"))
        capture(ep)
        service.receive_callback(ep, "fictional_provider", "frontend-actual-failure", CallbackResult(transition=ExecutionStatus.FAILED), Origin.LOCAL_SIM)
        capture(ep)
        stopped = s17_understood(service, "00000000-0000-4000-8000-000000000018")
        service.record_barrier_choice(s17_binding(service, stopped, "select_barrier", "transport"), choice_id="transport")
        capture(stopped)
        key = service._operation_signing_key().decode()
    finally:
        service._store.close()
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{decodeOperation}} from {json.dumps(module("episode-locator"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify({{projections:d.bodies.map(x=>decodeJourney(x,x.episode_id)!==null),tokens:d.tokens.map(t=>decodeOperation(t,d.key)!==null)}}));''',
        {"bodies": bodies, "tokens": tokens, "key": key})
    assert result["projections"] == [True] * len(bodies)
    assert result["tokens"] == [True] * len(tokens)


def test_s17_pending_request_is_neutral_and_keeps_read_only_recovery(tmp_path, monkeypatch):
    from test_journey import s17_understood, s17_binding
    from carerelay.service import ScenarioClock
    from datetime import timedelta
    service = make_service(tmp_path / "frontend-s17-pending.sqlite")
    class LostOwningInvocation(BaseException):
        pass
    def lose_owner(*args, **kwargs):
        raise LostOwningInvocation()
    bodies = []
    try:
        ep = s17_understood(service)
        service.record_barrier_choice(s17_binding(service, ep, "select_barrier", "booking"), choice_id="booking")
        service.change_share_consent(s17_binding(service, ep, "grant_share"), granted=True)
        binding = s17_binding(service, ep, "request")
        monkeypatch.setattr(service._coordinator, "execute_tool", lose_owner)
        with pytest.raises(LostOwningInvocation):
            service.request_appointment(binding)
        pending = service.request_appointment(binding)
        assert pending.receipt.state == "pending" and pending.receipt.replayed
        body = journey_surface(pending.journey)
        assert body["step"] == "permission" and body["text"]["status"] == "No reply yet."
        assert body["question"] is None and "feedback" not in body["text"]
        assert {o["kind"] for o in body["commands"]} == {"show_plan", "hide_plan", "revoke_share"}
        bodies.append(body)
        service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(hours=10))
        bodies.append(journey_surface(service.project_journey(ep)))
    finally:
        service._store.close()
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.map(x=>decodeJourney(x,x.episode_id)!==null)));''', bodies)
    assert result == [True, True]


def test_s17_permission_decoder_rejects_noninitial_execution(s17_permission_projection):
    good = s17_permission_projection
    cases = [good]
    for execution in ("acknowledged", "failed", "expired", "superseded"):
        bad = copy.deepcopy(good)
        bad["execution"] = bad["outcome"]["execution"] = execution
        cases.append(bad)
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.map(x=>decodeJourney(x,x.episode_id)!==null)));''', cases)
    assert result == [True, False, False, False, False]


def s17_action_boundary_script():
    """Real server actions/crypto with test-only request and API boundary hooks.

    The API hook isolates first refusal in the action from downstream validation.
    The independent loopback HTTP tests above cover the actual API module.
    """
    return f'''import {{readFileSync}} from 'node:fs';
import {{stripTypeScriptTypes}} from 'node:module';
import * as codec from {json.dumps(module("episode-locator"))};
const d=JSON.parse(readFileSync(0,'utf8'));const calls=[];
const url=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
process.env.CARERELAY_API_TOKEN=d.key;process.env.CARERELAY_LOOPBACK_TEST='1';
const locator={{schema:'carerelay-locator-v1',nonce:'00000000-0000-4000-8000-000000000001',operation_id:'00000000-0000-4000-8000-000000000002',episode_id:d.journey.episode_id}};
const goodCookie=codec.encodeLocator(locator,d.key);
globalThis.s17Boundary={{origin:'http://127.0.0.1:8140',host:'127.0.0.1:8140',cookie:goodCookie,token:d.prepared,calls,journey:d.journey}};
const context=url('export async function headers(){{return new Map([["origin",globalThis.s17Boundary.origin],["host",globalThis.s17Boundary.host]])}};export async function cookies(){{return {{get:()=>({{value:globalThis.s17Boundary.cookie}})}}}}');
const api=url(`export async function prepareBarrierCommand(...args){{globalThis.s17Boundary.calls.push({{method:'prepare',args}});return {{ok:true,value:globalThis.s17Boundary.token}}}}
export async function permissionCommand(...args){{globalThis.s17Boundary.calls.push({{method:'permission',args}});return {{ok:true,value:{{journey:globalThis.s17Boundary.journey}}}}}}
export async function createCommand(){{throw Error('unexpected creation')}};export async function selectExampleCommand(){{throw Error('unexpected selection')}};
export async function prepareWordsCommand(){{throw Error('unexpected words')}};export async function readbackCommand(){{throw Error('unexpected readback')}};`);
let source=readFileSync('frontend/app/actions.ts','utf8').replace('"next/headers"',JSON.stringify(context)).replace('"@/lib/api"',JSON.stringify(api))
 .replace('"@/lib/episode-locator"',{json.dumps(json.dumps(module("episode-locator")))})
 .replace('"@/lib/journey"',{json.dumps(json.dumps(module("journey")))});
const actions=await import(url(stripTypeScriptTypes(source)));
function form(kind,token){{const f=new FormData();f.set('kind',kind);f.set('operation_token',token);return f;}}
'''


@pytest.mark.parametrize("case", ["agreed_no", "choice_unknown", "choice_type", "choice_digest",
    "form_extra", "form_duplicate", "form_missing_agreement", "unknown_kind", "token_type", "token_kind", "origin", "cookie", "episode"])
def test_s17_permission_action_first_refusal(s17_permission_projection, case):
    digest = hashlib.sha256(canonical({"kind": "select_barrier", "payload": {"choice_id": "booking"}, "schema": "carerelay-command-v1"})).hexdigest()
    other_digest = hashlib.sha256(canonical({"kind": "select_barrier", "payload": {"choice_id": "unapproved"}, "schema": "carerelay-command-v1"})).hexdigest()
    data = {"key": S15_KEY.decode(), "journey": s17_permission_projection, "case": case,
        "request": s17_frontend_token("request"), "grant": s17_frontend_token("grant_share"),
        "barrier": s17_frontend_token("select_barrier", body_sha256=digest),
        "unknown_choice": s17_frontend_token("select_barrier", body_sha256=other_digest),
        "wrong_episode": s17_frontend_token("request", episode_id="00000000-0000-4000-8000-000000000019")}
    result = node(s17_action_boundary_script() + '''
const good=form('grant_share',d.grant);good.set('agreed','yes');
const control=await actions.submitPermission(good);calls.length=0;
let bad=form('request',d.request);
if(d.case==='agreed_no'||d.case==='form_missing_agreement'){bad=form('grant_share',d.grant);if(d.case==='agreed_no')bad.set('agreed','no');}
if(d.case==='choice_unknown'||d.case==='choice_type'||d.case==='choice_digest'){
 bad=form('select_barrier',d.case==='choice_unknown'?d.unknown_choice:d.barrier);
 bad.set('choice_id',d.case==='choice_unknown'?'unapproved':d.case==='choice_type'?new Blob(['booking']):'transport');
}
if(d.case==='form_extra')bad.set('extra','unexpected');
if(d.case==='form_duplicate')bad.append('kind','request');
if(d.case==='unknown_kind')bad.set('kind','caller_dispatch');
if(d.case==='token_type')bad.set('operation_token',new Blob(['synthetic.signature']));
if(d.case==='token_kind'){bad=form('grant_share',d.request);bad.set('agreed','yes');}
if(d.case==='origin')globalThis.s17Boundary.origin='https://attacker.invalid';
if(d.case==='cookie'){const [payload,signature]=goodCookie.split('.');const data=JSON.parse(Buffer.from(payload,'base64url'));data.nonce='00000000-0000-4000-8000-000000000003';globalThis.s17Boundary.cookie=Buffer.from(JSON.stringify(data)).toString('base64url')+'.'+signature;}
if(d.case==='episode')bad=form('request',d.wrong_episode);
const defect=await actions.submitPermission(bad);
console.log(JSON.stringify({control:control.state,defect:defect.state,calls}));''', data)
    assert result["control"] == "loaded"
    assert result["defect"] == "recovery"
    assert result["calls"] == []


@pytest.mark.parametrize("case", ["kind", "episode", "digest", "parent", "confirmation", "signature", "choice_unknown", "choice_type", "form_extra", "form_duplicate", "origin", "cookie"])
def test_s17_barrier_preparation_first_refusal(s17_permission_projection, case):
    digest = hashlib.sha256(canonical({"kind": "select_barrier", "payload": {"choice_id": "booking"}, "schema": "carerelay-command-v1"})).hexdigest()
    good = s17_frontend_token("select_barrier", body_sha256=digest)
    invalid = {
        "kind": s17_frontend_token("grant_share", body_sha256=digest),
        "episode": s17_frontend_token("select_barrier", body_sha256=digest, episode_id="00000000-0000-4000-8000-000000000019"),
        "digest": s17_frontend_token("select_barrier", body_sha256="b" * 64),
        "parent": s17_frontend_token("select_barrier", body_sha256=digest, parent="parent"),
        "confirmation": s17_frontend_token("select_barrier", body_sha256=digest, confirmation="confirmation"),
        "signature": good + "forged",
    }.get(case, good)
    result = node(s17_action_boundary_script() + '''
const good=new FormData();good.set('choice_id','booking');
const control=await actions.prepareBarrierChoice(good);calls.length=0;globalThis.s17Boundary.token=d.invalid;
const bad=new FormData();bad.set('choice_id','booking');
if(d.case==='choice_unknown')bad.set('choice_id','unapproved');
if(d.case==='choice_type')bad.set('choice_id',new Blob(['booking']));
if(d.case==='form_extra')bad.set('extra','unexpected');
if(d.case==='form_duplicate')bad.append('choice_id','booking');
if(d.case==='origin')globalThis.s17Boundary.origin='https://attacker.invalid';
if(d.case==='cookie'){const [payload,signature]=goodCookie.split('.');const data=JSON.parse(Buffer.from(payload,'base64url'));data.nonce='00000000-0000-4000-8000-000000000003';globalThis.s17Boundary.cookie=Buffer.from(JSON.stringify(data)).toString('base64url')+'.'+signature;}
const defect=await actions.prepareBarrierChoice(bad);
console.log(JSON.stringify({control:control.ok,defect:defect.ok,calls}));''',
        {"key": S15_KEY.decode(), "journey": s17_permission_projection, "case": case, "prepared": good, "invalid": invalid})
    assert result["control"] is True and result["defect"] is False
    if case in {"kind", "episode", "digest", "parent", "confirmation", "signature"}:
        assert len(result["calls"]) == 1 and result["calls"][0]["method"] == "prepare"
    else:
        assert result["calls"] == []


@pytest.mark.parametrize("case", ["version_zero", "version_type", "version_unsafe"])
def test_s17_capability_version_first_refusal(case):
    version = {"version_zero": 0, "version_type": "1", "version_unsafe": 9007199254740992}[case]
    good = s17_frontend_token("grant_share")
    bad = s17_frontend_token("grant_share", disposition_version=version, purpose=f"disposition:{version}:grant_share")
    result = node(f'''import {{decodeOperation}} from {json.dumps(module("episode-locator"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.tokens.map(t=>decodeOperation(t,d.key)!==null)));''',
        {"key": S15_KEY.decode(), "tokens": [good, bad]})
    assert result == [True, False]


@pytest.mark.parametrize("case", ["waiting_request", "pending_request", "stopped_request", "expired_request", "acknowledged_request",
    "barrier_execution", "barrier_choice_count", "barrier_choice_duplicate", "barrier_choice_unknown", "barrier_token"])
def test_s17_decoder_command_first_refusal(s17_permission_projection, case):
    good = copy.deepcopy(s17_permission_projection)
    if case.startswith("barrier_"):
        good["step"] = "barrier"
        good["commands"] = [{"kind": "select_barrier", "offer_id": "select_barrier", "permitted_choice_ids": ["booking", "transport", "other"], "operation_token": None}]
        good["question"] = {"question_id": "barrier", "text": "What makes it difficult?", "choices": [
            {"choice_id": "booking", "text": "Finding an appointment"}, {"choice_id": "transport", "text": "Getting there"}, {"choice_id": "other", "text": "Something else"}]}
        good["text"] = dict(heading="What makes it difficult?", description="Choose one.", choice_error="Choose one to continue.", continue_label="Continue")
    else:
        good["commands"] = []
        good["question"] = None
        if case in {"waiting_request", "pending_request"}:
            good["outcome"]["execution"] = good["execution"] = "attempted"
            good["text"] = dict(heading="May we share your plan?", status="No reply yet.", notice="Simulated request.")
            if case == "pending_request": good["flow"]["interpretation"] = "pending"
        elif case == "stopped_request":
            good["step"] = "stopped"
            good["flow"].update(stopped=True, stop_reason="h3", stopped_disposition_version=1)
            good["text"] = dict(heading="Let’s stop the questions")
        elif case == "expired_request":
            good["step"] = "expired"
            good["outcome"].update(execution="expired", closure="expired_unresolved", expiry_recorded=True)
            good.update(execution="expired", closure="expired_unresolved")
            good["text"] = dict(heading="Your plan still needs action")
        else:
            good["step"] = "plan"
            good["outcome"]["execution"] = good["execution"] = "acknowledged"
            good["text"] = dict(heading="Your next step", action_label="What to do", deadline_label="Before", owner_label="Who acts")
    bad = copy.deepcopy(good)
    if not case.startswith("barrier_"):
        bad["commands"] = [{"kind": "request", "offer_id": "request", "permitted_choice_ids": [], "operation_token": s17_frontend_token("request")}]
    elif case == "barrier_execution":
        bad["outcome"]["execution"] = bad["execution"] = "attempted"
    elif case == "barrier_choice_count":
        bad["commands"][0]["permitted_choice_ids"].append("booking")
    elif case == "barrier_choice_duplicate":
        bad["commands"][0]["permitted_choice_ids"] = ["booking", "transport", "booking"]
    elif case == "barrier_choice_unknown":
        bad["commands"][0]["permitted_choice_ids"] = ["booking", "transport", "unapproved"]
    else:
        bad["commands"][0]["operation_token"] = s17_frontend_token("select_barrier")
    result = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(d.map(x=>decodeJourney(x,x.episode_id)!==null)));''', [good, bad])
    assert result == [True, False]


@pytest.mark.parametrize("choice", ["booking", "transport", "other"])
def test_s17_exact_barrier_choice_digest(choice):
    result = node(f'''import {{barrierChoiceDigest}} from {json.dumps(module("episode-locator"))};
import {{readFileSync}} from 'node:fs';
const choice=JSON.parse(readFileSync(0,'utf8'));
console.log(JSON.stringify(barrierChoiceDigest(choice)));''', choice)
    assert result == hashlib.sha256(canonical({"kind": "select_barrier", "payload": {"choice_id": choice}, "schema": "carerelay-command-v1"})).hexdigest()


@pytest.mark.parametrize("later", ["barrier", "waiting"])
def test_s20_superseded_unavailable_check_leaves_no_stale_feedback(tmp_path, later):
    """Slice 20, found with VoiceOver: one unavailable check stuck to every later screen.

    After a later recorded round the barrier screen still said "We could not check that
    answer just now", and the waiting projection carried that feedback, which the decoder
    rightly refuses, so a patient who had just requested saw "We cannot load your plan".
    A later recorded round or a new read-back attempt supersedes the earlier event.
    """
    from _journey_fixtures import seed_journey
    from _legacy_service_probes import historical_attempt
    from carerelay.domain.models import HintLevel
    service = make_service(tmp_path / "s20-stale.sqlite")
    ep = "00000000-0000-4000-8000-000000000021"
    try:
        seed_journey(service, ep, "unavailable")
        assert service.project_journey(ep).flow.interpretation == "unavailable"
        service.submit_restatement(ep, "see the doctor today before 6pm myself", HintLevel.H1)
        if later == "waiting":
            service.record_barrier(ep, "booking", "fictional_provider")
            service.change_consent(ep, granted=True)
            historical_attempt(service, ep, purpose="s20-waiting")
        body = json.loads(json.dumps(journey_surface(service.project_journey(ep))))
    finally:
        service._store.close()
    assert body["step"] == ("barrier" if later == "barrier" else "permission")
    assert body["flow"]["interpretation"] == "scored"
    assert "feedback" not in body["text"], body["text"]
    decoded = node(f'''import {{decodeJourney}} from {json.dumps(module("journey"))};
import {{readFileSync}} from 'node:fs';
const d=JSON.parse(readFileSync(0,'utf8'));console.log(JSON.stringify(decodeJourney(d,d.episode_id)!==null));''', body)
    assert decoded is True
