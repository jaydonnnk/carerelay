"""Slice 14: single-guard mutants, assertion failures and byte-exact restoration.

No engine/network/browser result follows. Structural render checks are explicitly
not execution evidence. Browser obligations stay blocked without Next.js.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DECODER = "frontend/lib/journey.ts"
J = "tests/test_journey.py::"
D = "tests/test_journey_commands.py::"
MUTATIONS = [
 ("G09 relative bootstrap redirect", "frontend/app/example/route.ts",
  'headers: { Location: "/" }',
  'headers: { Location: "http://localhost:8140/" }', D+"test_real_bootstrap_handler_sets_cookie_before_any_backend_call"),
 ("G09 bootstrap cookie", "frontend/app/example/route.ts",
  'response.cookies.set(LOCATOR_COOKIE, cookie, options);',
  '// cookie deliberately omitted by mutant', D+"test_real_bootstrap_handler_sets_cookie_before_any_backend_call"),
 ("G31 no-plan consent", "src/carerelay/state.py",
  'consent_granted=consent is not None and consent[1] == "granted",',
  'consent_granted=False,', J+"test_bundle_preserves_consent_without_exposing_guidance"),
 ("G01 API fixture fallback", "src/carerelay/api.py",
  'return journey_surface(service.project_journey(episode_id))',
  'return {**journey_surface(service.project_journey(episode_id)), "lines": list(fixture.demo_lines().as_tuple())}', J+"test_no_plan_surfaces[api]"),
 ("G01 options fallback", "src/carerelay/service.py",
  'self._policy.permitted_route_ids if snapshot.disposition is not None else ()',
  'self._policy.permitted_route_ids', J+"test_no_plan_surfaces[options]"),
 ("G01 MCP route fallback", "src/carerelay/tools.py",
  'permitted_route_ids=tuple(sorted(policy.permitted_route_ids)) if disposition is not None else (),',
  'permitted_route_ids=tuple(sorted(policy.permitted_route_ids)),', J+"test_no_plan_surfaces[mcp]"),
 ("G01 MCP policy fallback", "src/carerelay/tools.py",
  'policy_version=disposition.policy_version if disposition is not None else None,',
  'policy_version=policy.version,', J+"test_no_plan_surfaces[mcp]"),
 ("G01 bare root fixture", "src/carerelay/api.py",
  'return RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store"})',
  'return JSONResponse({"lines": list(fixture.demo_lines().as_tuple())})', J+"test_no_plan_surfaces[root]"),
 ("G01 assessed refusal", "src/carerelay/domain/rules.py",
  'if bundle.snapshot.disposition is not None:', 'if False:', J+"test_assessed_refuses_without_a_stop_or_implicit_expiry"),
 ("G01 identity propagation", "src/carerelay/domain/rules.py",
  'episode_id=bundle.episode_id, revision=bundle.revision,',
  'episode_id="demo-episode-001", revision=bundle.revision,', J+"test_no_event_identity_after_reopen_and_unknown"),
 ("G37 durable read", "src/carerelay/api.py",
  'return journey_surface(service.project_journey(episode_id))',
  'raise HTTPException(status_code=404, detail="mutant volatile registry")', J+"test_fresh_process_reads"),
 ("G09 structural create-on-render", "frontend/app/page.tsx",
  '  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;',
  '  await createEpisode();\n  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;', D+"test_render_and_bootstrap_source_has_no_mutation"),
]


def build_mutations():
    result = list(MUTATIONS)
    # The read transaction is one isolation guard: disabling both delimiters
    # avoids a COMMIT-without-BEGIN exception masquerading as an assertion kill.
    source = (ROOT / "src/carerelay/state.py").read_text()
    start = source.index('    def load_journey_bundle(')
    end = source.index('    def load_snapshot(', start)
    block = source[start:end]
    no_tx = block.replace('self._conn.execute("BEGIN")', 'self._conn.execute("SELECT 1")').replace('self._conn.execute("COMMIT")', 'self._conn.execute("SELECT 1")')
    result.append(("G31 SQLite snapshot isolation", "src/carerelay/state.py", block, no_tx, J+"test_snapshot_race"))
    checks = {
      "schema": ('value.schema_version !== "carerelay-journey-v1"', 'false'),
      "id": ('value.episode_id !== expectedId', 'false'),
      "revision": ('value.revision < 0', 'false'),
      "unsafe_revision": ('!Number.isSafeInteger(value.revision)', 'false'),
      "time": None,
      "calendar": ('new Date(value.as_of_utc).toISOString().slice(0, 19) !== value.as_of_utc.slice(0, 19)', 'false'),
      "clock": ('value.clock_mode !== "scenario" && value.clock_mode !== "system"', 'false'),
      "step": ('value.step !== "start"', 'false'), "redaction": ('value.plan_redacted !== false', 'false'),
      "care": ('value.care_evidenced !== false', 'false'),
      "lines": ('!Array.isArray(value.lines) || value.lines.length !== 0', 'false'),
      "commands": ('!Array.isArray(value.commands) || value.commands.length !== 0', 'false'),
      "simulated": ('value.simulated !== true', 'false'),
      "label": ('value.fixture_label !== JOURNEY_LABEL', 'false'),
      "copy": ('value.text[key] !== copy', 'key !== "heading" && value.text[key] !== copy'),
      "stopped": ('flow.stopped !== false', 'false'), "repairs": ('flow.completed_repairs !== 0', 'false'),
      "hint": ('flow.effective_hint !== "H1"', 'false'), "visible": ('flow.card_visible !== false', 'false'),
      "interpretation": ('flow.interpretation !== "idle"', 'false'),
    }
    # A malformed timestamp must return null rather than throw from decoding.
    del checks["time"]
    for label, (old,new) in checks.items():
        result.append(("G06 "+label, DECODER, old, new, D+f"test_projection_invariants[{label}]"))
    nulls = dict(disposition="disposition_version", policy="policy_version", plan="plan", outcome="outcome",
                 revealed="revealed_plan", question="question", closure="closure", execution="execution", evidence="evidence", owner="action_owner_id")
    for label,key in nulls.items():
        result.append(("G06 "+label, DECODER, 'if (value[key] !== null) return null;',
                       f'if (key !== "{key}" && value[key] !== null) return null;', D+f"test_projection_invariants[{label}]"))
    nulls = dict(reason="stop_reason", stop_version="stopped_disposition_version", attempt="readback_attempt_id",
                 restatement="latest_restatement_id", repair_field="selected_repair_field")
    for label,key in nulls.items():
        result.append(("G06 "+label, DECODER, 'if (flow[key] !== null) return null;',
                       f'if (key !== "{key}" && flow[key] !== null) return null;', D+f"test_projection_invariants[{label}]"))
    code=(ROOT/DECODER).read_text()
    for label, opening in [("time", '  if (typeof value.as_of_utc'), ("extra", '  if (!exactKeys(value,'), ("flow_extra", '  if (!record(value.flow)'), ("text_extra", '  if (!record(value.text)')]:
        a=code.index(opening);b=code.index(' return null;',a)+len(' return null;')
        old=code[a:b]
        result.append(("G06 "+label,DECODER,old,'  if (false) return null;',D+f"test_projection_invariants[{label}]"))
    result.append(("G06 bounded response",DECODER,'count > MAX_JOURNEY_BYTES','false',D+"test_decoder_good_and_bounded_transport"))
    boundary=(ROOT/'tests/test_boundaries.py').read_text()
    a=boundary.index('NO_PLAN_DETECTORS = {');b=boundary.index('\n}',a)
    for name, pattern in re.findall(r'    "([a-z_]+)": r"([^"]+)",',boundary[a:b]):
        old=f'    "{name}": r"{pattern}",'
        result.append(("G07 detector "+name,'tests/test_boundaries.py',old,f'    "{name}": r"(?!)",',
            f'tests/test_boundaries.py::test_serialized_detection_controls[json-{name}]'))
    result.append(("G09 cookie MAC",'frontend/lib/episode-locator.ts',
        '!timingSafeEqual(bytes, expected)','false',D+'test_cookie_codec_and_transport'))
    return result


def purge(path):
    for p in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"): p.unlink()


def run(selector, directory, label):
    xml=directory/f"{label}.xml"
    env=dict(os.environ, PYTHONPATH=str(ROOT/'src'), PYTHONDONTWRITEBYTECODE='1', APP_DATABASE_URL=':memory:',
             APP_CLOCK='scenario', APP_ENV='local', CARERELAY_API_TOKEN='',
             CARERELAY_TEST_DSN='postgresql://127.0.0.1:1/carerelay_disabled')
    completed=subprocess.run([sys.executable,'-m','pytest',selector,'-o','addopts=','-q',f'--junitxml={xml}',
        f'--basetemp={directory/"pytest"}'],cwd=ROOT,env=env,capture_output=True,text=True)
    (directory/f'{label}.log').write_text(completed.stdout+completed.stderr)
    cases=ET.parse(xml).findall('.//testcase') if xml.exists() else []
    errors=any(c.find('error') is not None or c.find('skipped') is not None for c in cases)
    failures=[f for c in cases for f in c.findall('failure')]
    green=completed.returncode==0 and bool(cases) and not failures and not errors
    red=(completed.returncode==1 and bool(failures) and not errors and
         all('AssertionError' in (f.text or '') or f.attrib.get('message','').startswith('assert ') for f in failures))
    return green,red


def main():
    mutations=build_mutations()
    directory=Path(tempfile.mkdtemp(prefix='carerelay-slice14-mutations-'))
    print(f'Evidence: {directory}',flush=True)
    originals={target:(ROOT/target).read_bytes() for _,target,*_ in mutations}
    for target, data in originals.items():
        backup=directory/'backup'/target;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(data);purge(ROOT/target)
    for number,(label,target,old,new,selector) in enumerate(mutations,1):
        path=ROOT/target; baseline=originals[target]
        assert baseline.count(old.encode())==1, f'NOT PROVEN anchor: {label}'
        assert run(selector,directory,f'{number}-before')[0], f'Control failed: {label}'
        try:
            path.write_bytes(baseline.replace(old.encode(),new.encode()));purge(path)
            result=run(selector,directory,f'{number}-mutant')
        finally:
            path.write_bytes(baseline);purge(path)
        assert path.read_bytes()==baseline
        assert result[1],f'SURVIVED or NOT PROVEN: {label}; see {directory}'
        assert run(selector,directory,f'{number}-after')[0],f'Restored control failed: {label}'
        print(f'RED {number}: {label}; controls GREEN; byte-exact restore',flush=True)
    assert all((ROOT/p).read_bytes()==data for p,data in originals.items())
    print(f'{len(mutations)}/{len(mutations)} RED, 0 SURVIVED, 0 NOT PROVEN',flush=True)
    print('Actual browser/SSR/RSC/revalidation proof: NOT RUN. G09 start creation: Slice 15.',flush=True)

if __name__=='__main__':main()
