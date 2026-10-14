"""Run isolated truthfulness mutations; require assertion failures and exact restore.

Uses the running interpreter, no installs or database credentials. Each selector
has a green control before and after mutation. JUnit distinguishes assertions
from collection errors, missing selectors, runtime errors and skipped tests.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_truthfulness.py::"
RULES = "src/carerelay/domain/rules.py"
SERVICE = "src/carerelay/service.py"
COORDINATOR = "src/carerelay/coordinator.py"

# A single mutant is paired with one targeted assertion path. Never run mutants
# concurrently: the working files are shared. Byte backups live outside the repo.
MUTATIONS = [
    ("handoff closure", RULES,
     'elif snapshot.escalation_id is not None and snapshot.escalation_outcome in {"handed_off", "handed_over"}:',
     'elif snapshot.escalation_id is not None:',
     'TestFailedHandoff::test_unsuccessful_handoff_stays_unresolved[failed]'),
    ("handoff owner", RULES,
     'if snapshot.escalation_id is None or snapshot.escalation_outcome not in {"handed_off", "handed_over"}:',
     'if snapshot.escalation_id is None:',
     'TestFailedHandoff::test_unsuccessful_handoff_stays_unresolved[failed]'),
    ("SQLite handoff outcome", "src/carerelay/state.py",
     'escalation_outcome=escalation["outcome"] if escalation is not None else None,',
     'escalation_outcome="handed_off" if escalation is not None else None,',
     'TestFailedHandoff::test_unsuccessful_handoff_stays_unresolved[failed]'),
    ("ledger outcome", SERVICE,
     '"outcome": snapshot.escalation_outcome,', '"outcome": "handed_off",',
     'TestFailedHandoff::test_unsuccessful_handoff_stays_unresolved[failed]'),
    ("callback evidence boundary", SERVICE,
     'rules.validate_adapter_evidence(result.evidence)', 'pass # mutant',
     'TestEvidenceTrust::test_caller_labels_cannot_make_real_documentation[]'),
    ("MCP evidence boundary", "src/carerelay/tools.py",
     'rules.validate_adapter_evidence(record)', 'pass # mutant',
     'TestEvidenceTrust::test_mcp_cannot_launder_caller_labelled_real_evidence'),
    ("evidence authenticity rule", RULES,
     'if not record.simulated:', 'if False:',
     'TestEvidenceTrust::test_caller_labels_cannot_make_real_documentation[]'),
    ("acceptance scope", RULES,
     'return scope == "handoff" and bool(accepted_by)', 'return True and bool(accepted_by)',
     'TestAcceptanceAuthority::test_only_a_relevant_transfer_can_close[caregiver-unrelated]'),
    ("acceptance transfer", RULES,
     'and accepted_by not in {"patient", owner}', 'and True',
     'TestAcceptanceAuthority::test_only_a_relevant_transfer_can_close[patient-handoff]'),
    ("acceptance consent", "src/carerelay/state.py",
     'acceptance_id = uuid.uuid4().hex\n        with self._write():\n            self.require_granted_consent(episode_id)',
     'acceptance_id = uuid.uuid4().hex\n        with self._write():\n            pass # mutant',
     'TestAcceptanceAuthority::test_acceptance_requires_current_permission[False]'),
    ("acceptance projection", RULES,
     'elif _has_handoff_acceptance(snapshot):', 'elif snapshot.human_acceptance_id is not None:',
     'TestAcceptanceAuthority::test_historical_unrelated_acceptance_cannot_close_on_reload'),
    ("acceptance owner", RULES,
     'return snapshot.accepted_by', 'return disposition.next_owner_id',
     'TestAcceptanceAuthority::test_valid_acceptance_names_the_new_owner_without_claiming_care'),
    ("negation uncertainty", COORDINATOR,
     'if _DOUBT.search(sentence):', 'if False:',
     'TestReadBackPolarity::test_negated_or_uncertain_answers_are_not_understanding[I will not see the doctor today before 6pm myself.]'),
    ("word start boundary", COORDINATOR,
     'pattern = r"(?<!\\w)" + pattern', 'pattern = pattern',
     'TestReadBackPolarity::test_partial_answer_does_not_invent_an_owner_from_a_substring[theme]'),
    ("word end boundary", COORDINATOR,
     'pattern += r"(?!\\w)"', 'pattern += ""',
     'TestReadBackPolarity::test_partial_answer_does_not_invent_an_owner_from_a_substring[myselfish]'),
    ("fixture action recognition", "src/carerelay/demo/fixture.py",
     '    ACTION_TEXT.rstrip(".").casefold(): ACTION_ID,\n', '',
     "TestReadBackPolarity::test_known_positive_answers_still_match[Go to the fictional provider's same-day review before 6pm today and you are the owner.]"),
    ("fixture deadline recognition", "src/carerelay/demo/fixture.py",
     '    "before 6pm today": (0, "18:00"),\n', '',
     "TestReadBackPolarity::test_known_positive_answers_still_match[Go to the fictional provider's same-day review before 6pm today and you are the owner.]"),
]
MUTATIONS += [('H3 response truth',
  'src/carerelay/service.py',
  'return self.hint_level is not HintLevel.H3 and not self.comparison.mismatched and not '
  'self.comparison.uncertain',
  'return not self.comparison.mismatched and not self.comparison.uncertain',
  'TestDurableStops::test_h3_never_reports_understanding_or_offers_repair'),
 ('H3 routing truth',
  'src/carerelay/service.py',
  'understood = level is not HintLevel.H3 and not comparison.mismatched and not '
  'comparison.uncertain',
  'understood = not comparison.mismatched and not comparison.uncertain',
  'TestDurableStops::test_h3_never_reports_understanding_or_offers_repair'),
 ('H3 repair suppression',
  'src/carerelay/service.py',
  'next_field = None if level is HintLevel.H3 else rules.next_repair(comparison, repair_round)',
  'next_field = rules.next_repair(comparison, repair_round)',
  'TestStopRecordGuards::test_h3_mismatch_still_routes_to_human_without_a_repair_offer'),
 ('H3 persisted rule',
  'src/carerelay/domain/rules.py',
  'return level is HintLevel.H3 or (',
  'return False or (',
  'TestStopRecordGuards::test_legacy_stop_rows_are_still_binding[H3-0]'),
 ('repair cap persisted rule',
  'src/carerelay/domain/rules.py',
  'repair_round >= MAX_REPAIR_ROUNDS and outcome is RecallOutcome.NOT_RECALLED',
  'repair_round > MAX_REPAIR_ROUNDS and outcome is RecallOutcome.NOT_RECALLED',
  'TestStopRecordGuards::test_legacy_stop_rows_are_still_binding[H0-2]'),
 ('successful repair control',
  'src/carerelay/domain/rules.py',
  'repair_round >= MAX_REPAIR_ROUNDS and outcome is RecallOutcome.NOT_RECALLED',
  'repair_round >= MAX_REPAIR_ROUNDS',
  'TestStopAlternatesAndRecovery::test_correct_second_repair_does_not_stop'),
 ('stop version filter',
  'src/carerelay/state.py',
  'if payload["disposition_version"] == version:',
  'if True:',
  'TestStopAlternatesAndRecovery::test_authorised_new_version_reopens_without_reusing_old_keys'),
 ('reassessment stop persistence',
  'src/carerelay/service.py',
  '        if stops:\n            self._store.record_flow_stop(',
  '        if False:\n            self._store.record_flow_stop(',
  'TestStopRecordGuards::test_reassessment_stop_is_recorded_with_version_and_fallback'),
 ('restatement stop atomic audit',
  'src/carerelay/state.py',
  'if rules.restatement_stops(hint_level, outcome, repair_round):',
  'if False:',
  'TestStopRecordGuards::test_h3_stop_event_is_atomic_with_its_restatement'),
 ('unfinished ladder reset',
  'src/carerelay/service.py',
  'if rounds and rounds[-1].outcome is RecallOutcome.NOT_RECALLED:',
  'if False:',
  'TestStopAlternatesAndRecovery::test_round_zero_cannot_reset_an_unfinished_ladder'),
 ('scoring stop guard',
  'src/carerelay/service.py',
  '        self._store.require_active_flow(episode_id)\n        self._require_scorable(',
  '        self._require_scorable(',
  'TestStopRecordGuards::test_reassessment_stop_blocks_repair_without_rescoring'),
 ('action opening stop guard',
  'src/carerelay/service.py',
  '        self._store.require_active_flow(episode_id)\n        route = rules.validate_route',
  '        route = rules.validate_route',
  'TestStopAlternatesAndRecovery::test_stop_blocks_alternate_endpoints_in_a_fresh_process[reassessment]'),
 ('MCP dispatch stop guard',
  RULES,
  '    if bundle.snapshot.flow_stop_reason is not None:\n'
  '        return "dispatch flow stopped"',
  '    if False:\n        return "dispatch flow stopped"',
  'TestDurableStops::test_direct_mcp_dispatch_cannot_bypass_reassessment_stop'),
 ('MCP evidence stop guard',
  'src/carerelay/tools.py',
  '        self._store.require_active_flow(episode_id)\n'
  '        self._recheck_consent(episode_id, "record_evidence", now_utc)',
  '        self._recheck_consent(episode_id, "record_evidence", now_utc)',
  'TestStopAlternatesAndRecovery::test_mcp_evidence_cannot_progress_a_stopped_plan'),
 ('callback acknowledgement stop guard',
  'src/carerelay/state.py',
  '(result.transition is ExecutionStatus.ACKNOWLEDGED or result.evidence is not None)',
  '(False or result.evidence is not None)',
  'TestStopAlternatesAndRecovery::test_inflight_success_is_a_refused_receipt_after_stop[acknowledged]'),
 ('callback evidence stop guard',
  'src/carerelay/state.py',
  '(result.transition is ExecutionStatus.ACKNOWLEDGED or result.evidence is not None)',
  '(result.transition is ExecutionStatus.ACKNOWLEDGED or False)',
  'TestStopAlternatesAndRecovery::test_inflight_success_is_a_refused_receipt_after_stop[evidence]'),
 ('barrier continuation stop guard',
  'src/carerelay/service.py',
  '        self._store.require_active_flow(episode_id)\n'
  '        now_utc = self._clock.now_utc()\n'
  '        permitted_route_id: str | None = None',
  '        now_utc = self._clock.now_utc()\n        permitted_route_id: str | None = None',
  'TestStopAlternatesAndRecovery::test_stop_blocks_alternate_endpoints_in_a_fresh_process[barrier]'),
 ('retired caller-purpose action guard',
  'src/carerelay/service.py',
  'raise CommandInvalid("legacy action requires a journey command")',
  'return None',
  'TestStopAlternatesAndRecovery::test_authorised_new_version_reopens_without_reusing_old_keys'),
 ('old MCP key guard',
  'src/carerelay/tools.py',
  'or attempt.disposition_version != snapshot.disposition.version',
  'or False',
  'TestStopAlternatesAndRecovery::test_authorised_new_version_reopens_without_reusing_old_keys'),
 ('old restatement guard',
  'src/carerelay/service.py',
  'if snapshot.disposition is None or parent.disposition_version != '
  'snapshot.disposition.version:',
  'if False:',
  'TestStopAlternatesAndRecovery::test_authorised_new_version_reopens_without_reusing_old_keys'),
 ('restart reads persistent existence',
  'src/carerelay/api.py',
  '    with _DB_LOCK:\n        return service.project_ledger(episode_id).as_dict()',
  '    raise HTTPException(status_code=404, detail="mutant process-local registry")\n'
  '    with _DB_LOCK:\n'
  '        return service.project_ledger(episode_id).as_dict()',
  'TestStopAlternatesAndRecovery::test_stop_blocks_alternate_endpoints_in_a_fresh_process[reassessment]')]
MUTATIONS.append(('cross-sentence negation reference', 'src/carerelay/coordinator.py', 'if _PLAN_REFERENCE.search(sentence):', 'if False:', "TestReadBackPolarity::test_negated_or_uncertain_answers_are_not_understanding[I will see the doctor today before 6pm myself. Actually I won't.]"))


def purge(path):
    for p in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
        p.unlink()


def run(selector, directory, label):
    xml = directory / f"{label}.xml"
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
               PYTHONDONTWRITEBYTECODE="1", APP_DATABASE_URL=":memory:",
               APP_CLOCK="scenario", APP_ENV="local", CARERELAY_API_TOKEN="")
    result = subprocess.run([sys.executable, "-m", "pytest", TEST + selector,
                             "-o", "addopts=", "-q", f"--junitxml={xml}",
                             f"--basetemp={directory / 'pytest'}"],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    (directory / f"{label}.log").write_text(result.stdout + result.stderr)
    if not xml.exists():
        raise AssertionError(f"No test report: {label}")
    cases = ET.parse(xml).findall(".//testcase")
    return result.returncode, cases


def green(result):
    code, cases = result
    return code == 0 and bool(cases) and all(len(case) == 0 for case in cases)


def red(result):
    code, cases = result
    failures = [f for case in cases for f in case.findall("failure")]
    return (code == 1 and bool(failures)
            and not any(case.find("error") is not None or case.find("skipped") is not None for case in cases)
            and all(f.attrib.get("message", "").startswith(("assert ", "DID NOT RAISE", "Failed: DID NOT RAISE"))
                    or "AssertionError" in (f.text or "") for f in failures))


def main():
    directory = Path(tempfile.mkdtemp(prefix="carerelay-truthfulness-mutations-"))
    print(f"Evidence: {directory}", flush=True)
    baselines = {target: (ROOT / target).read_bytes() for _, target, *_ in MUTATIONS}
    for target, baseline in baselines.items():
        backup = directory / "backup" / target
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_bytes(baseline)
        purge(ROOT / target)
    killed = 0
    for number, (label, target, before, after, selector) in enumerate(MUTATIONS, 1):
        path = ROOT / target
        baseline = baselines[target]
        newline = "\r\n" if b"\r\n" in baseline else "\n"
        anchor, replacement = (s.replace("\n", newline).encode() for s in (before, after))
        assert baseline.count(anchor) == 1, f"Non-unique anchor: {label}"
        assert green(run(selector, directory, f"{number}-before")), f"Control failed: {label}"
        try:
            path.write_bytes(baseline.replace(anchor, replacement))
            purge(path)
            result = run(selector, directory, f"{number}-mutant")
        finally:
            path.write_bytes(baseline)
            purge(path)
        assert path.read_bytes() == baseline
        assert red(result), f"SURVIVED or NOT PROVEN: {label}; inspect {directory}"
        assert green(run(selector, directory, f"{number}-after")), f"Restore control failed: {label}"
        killed += 1
        print(f"RED {number}: {label}; controls GREEN; restored byte-exact", flush=True)
    assert all((ROOT / target).read_bytes() == b for target, b in baselines.items())
    print(f"{killed}/{len(MUTATIONS)} RED, 0 SURVIVED, 0 NOT PROVEN", flush=True)


if __name__ == "__main__":
    main()
