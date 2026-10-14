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
        policy=fixture.policy(), provider=ScriptedProvider()))
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
