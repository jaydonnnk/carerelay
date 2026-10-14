"""Patient-experience guards through Slice 16: SQLite/crypto/decoder/source parity.

Use --validate-only to resolve anchors, collect selectors and run their controls.
Run mutations only after all source writers stop. --filter and --resume retain
per-case evidence; resumed REDs apply only to byte-identical targets and metadata.
Actual browser and Postgres-engine observations remain separate obligations.
"""
from dataclasses import asdict, dataclass
import argparse
import hashlib
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
LOCATOR = "frontend/lib/episode-locator.ts"
STATE = "src/carerelay/state.py"
RULES = "src/carerelay/domain/rules.py"
SERVICE = "src/carerelay/service.py"
CODEC = "src/carerelay/journey_commands.py"
J = "tests/test_journey.py::"
D = "tests/test_journey_commands.py::"
C = "tests/test_journey_mutation_controls.py::"
F = "tests/test_journey_decoder.py::"
I = "tests/test_journey_guard_inventory.py::"

# A mutant that makes the product answer with its own typed refusal has changed
# observable behaviour just as much as one that trips an assert: a valid read that
# now returns 503, or a valid body that now refuses to canonicalize, is a real
# failure of a real control. Interpreter-level breakage stays excluded above, so a
# malformed mutant still cannot earn credit.
TYPED_REFUSAL = re.compile(
    r"carerelay\.[\w.]*(?:CommandInvalid|CommandConflict|JourneyUnavailable|MissingDisplayText"
    r"|DomainError|StateError|EpisodeNotFound|InvalidJourneyRecord|LockContention):")


@dataclass(frozen=True)
class Mutation:
    label: str
    target: str
    old: str
    new: str
    selector: str


def build_mutations():
    rows = []
    def add(label, target, old, new, selector):
        rows.append(Mutation(label, target, old, new, selector))
    add("G09 relative bootstrap redirect", "frontend/app/example/route.ts",
        'headers: { Location: "/" }', 'headers: { Location: "http://localhost:8140/" }',
        D + "test_real_bootstrap_handler_sets_cookie_before_any_backend_call")
    add("G09 bootstrap cookie", "frontend/app/example/route.ts",
        'response.cookies.set(LOCATOR_COOKIE, cookie, options);', '// omitted cookie',
        D + "test_real_bootstrap_handler_sets_cookie_before_any_backend_call")
    add("G01 API no-plan fallback", "src/carerelay/api.py",
        'return journey_surface(service.project_journey(episode_id))',
        'return {**journey_surface(service.project_journey(episode_id)), "lines": list(fixture.demo_lines().as_tuple())}',
        J + "test_no_plan_surfaces[api]")
    add("G01 no-plan options", SERVICE,
        'policy.permitted_route_ids if snapshot.disposition is not None else ()',
        'policy.permitted_route_ids', J + "test_no_plan_surfaces[options]")
    for field, old, new in [
        ("routes", 'permitted_route_ids=tuple(sorted(policy.permitted_route_ids)) if disposition is not None else (),', 'permitted_route_ids=tuple(sorted(policy.permitted_route_ids)),'),
        ("policy", 'policy_version=disposition.policy_version if disposition is not None else None,', 'policy_version=policy.version,')]:
        add("G01 MCP no-plan " + field, "src/carerelay/tools.py", old, new, J + "test_no_plan_surfaces[mcp]")
    add("G01 bare-root fallback", "src/carerelay/api.py",
        'return RedirectResponse(target, status_code=303, headers={"Cache-Control": "no-store"})',
        'return JSONResponse({"lines": list(fixture.demo_lines().as_tuple())})', J + "test_no_plan_surfaces[root]")
    add("G01 verified stored identity", RULES,
        'episode_id=bundle.episode_id, revision=bundle.revision,',
        'episode_id="demo-episode-001", revision=bundle.revision,', J + "test_no_event_identity_after_reopen_and_unknown")
    add("G02 recorded bundle lookup", STATE,
        'resolved = fixture.recorded_policy_bundle(version) if registered is not None else None',
        'resolved = (fixture.policy(), fixture.policy_text()) if registered is not None else None',
        J + "test_recorded_policy_selected")
    add("G37 persistent HTTP reads", "src/carerelay/api.py",
        'return journey_surface(service.project_journey(episode_id))',
        'raise HTTPException(status_code=404, detail="volatile registry")', J + "test_fresh_process_reads")
    add("G09 structural render mutation", "frontend/app/page.tsx",
        '  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;',
        '  await createEpisode();\n  const cookie = (await cookies()).get(LOCATOR_COOKIE)?.value;',
        D + "test_render_and_bootstrap_source_has_no_mutation")
    add("G09 cookie MAC", "frontend/lib/episode-locator.ts", '!timingSafeEqual(bytes, expected)', 'false', D + "test_cookie_codec_and_transport")
    add("G10 distinct locator identities", "frontend/lib/episode-locator.ts",
        'episode_id: randomUUID()', 'episode_id: "00000000-0000-4000-8000-000000000000"', D + "test_cookie_codec_and_transport")
    add("G31 no-plan consent", STATE, 'consent_granted=consent is not None and consent["state"] == "granted"',
        'consent_granted=False', J + "test_bundle_preserves_consent_without_exposing_guidance")
    source = (ROOT / STATE).read_text()
    start = source.index('    def journey_transaction(')
    end = source.index('    def create_with_claim_once(', start)
    block = source[start:end]
    no_tx = block.replace('self._conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")', 'self._conn.execute("SELECT 1")').replace('self._conn.execute("COMMIT")', 'self._conn.execute("SELECT 1")')
    add("G31 coherent assessed snapshot", STATE, block, no_tx, J + "test_assessed_snapshot_never_mixes_revisions[stop]")
    add("G31 coherent no-plan snapshot", STATE, block, no_tx, J + "test_snapshot_race")
    add("G11 intake receipt lookup", SERVICE, 'receipt = tx.find(binding)\n            if receipt is None:\n                bundle =',
        'receipt = None\n            if receipt is None:\n                bundle =', C + "test_intake_replay_does_not_reenter_stale_offer_check")
    add("G14 pending replay", STATE,
        'terminal["terminal_state"] if terminal else "pending",',
        'terminal["terminal_state"] if terminal else "applied",', D + "test_pending_and_terminal_replay")
    add("G12 intake digest", SERVICE,
        'if binding.body_sha256 != request_digest("select_example", {"example_id": example_id}):',
        'if False:', C + "test_unclaimed_intake_digest_is_not_masked_by_replay")
    for dimension in ["expected_revision", "disposition_version", "parent_restatement_id", "confirmation_id"]:
        conditions = {
            "expected_revision": ('binding.expected_revision != bundle.revision', 'False'),
            "disposition_version": ('binding.disposition_version != version', 'False'),
            "parent_restatement_id": ('binding.parent_restatement_id is not None or binding.confirmation_id is not None', 'binding.confirmation_id is not None'),
            "confirmation_id": ('binding.parent_restatement_id is not None or binding.confirmation_id is not None', 'binding.parent_restatement_id is not None'),
        }
        old, new = conditions[dimension]
        values = {"expected_revision": "0", "disposition_version": "1", "parent_restatement_id": "old-parent", "confirmation_id": "old-confirmation"}
        add("G13 claim " + dimension, STATE, old, new,
            (C + "test_claim_parent_with_valid_foreign_row" if dimension == "parent_restatement_id" else D + f"test_stale_unclaimed_start_dimensions_make_no_writes[{dimension}-{values[dimension]}]"))
    # Normalize exactly one signed dimension only in the verifier. Orthogonal
    # schema validation is isolated by the pinned MAC test, never production.
    original = dict(operation_id="mutation-create", episode_id="mutation-episode", disposition_version=None,
        expected_revision=0, kind="create", purpose="episode:create", body_sha256="",
        parent_restatement_id=None, confirmation_id=None, token_schema="carerelay-command-v1")
    from carerelay.journey_commands import request_digest
    original["body_sha256"] = request_digest("create", {})
    old = 'expected = _encode(hmac.digest(_key(signing_key), payload.encode("ascii"), "sha256"))'
    for dimension, value in original.items():
        normalize = ('mac_body = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))\n'
            f'        mac_body[{dimension!r}] = {value!r}\n'
            '        expected = _encode(hmac.digest(_key(signing_key), _encode(canonical(mac_body)).encode("ascii"), "sha256"))')
        add("G13 MAC " + dimension, CODEC, old, normalize, C + f"test_mac_dimension_without_shape_overlap[{dimension}]")
    add("G16 create state-receipt transaction", STATE,
        '            return tx.complete_once(binding.operation_id, state="applied", result_ref=binding.episode_id,',
        '            self._conn.commit()\n            return tx.complete_once(binding.operation_id, state="applied", result_ref=binding.episode_id,',
        D + "test_s15_real_crash_before_terminal_rolls_back_create")
    add("G16 intake state-receipt transaction", SERVICE,
        '                    receipt = tx.complete_once(binding.operation_id, state="applied", result_ref=str(disposition.version),',
        '                    self._store._conn.commit()\n                    receipt = tx.complete_once(binding.operation_id, state="applied", result_ref=str(disposition.version),',
        D + "test_real_crash_before_intake_terminal_rolls_back_disposition")
    # The engine tests prove other constraints accept each malformed row when
    # this binding trigger alone is absent.
    bindings = {"operation_id":"other-op", "episode_id":"other-episode", "disposition_version":"1",
        "expected_revision":"99", "claim_revision":"2", "kind":"select_example", "purpose":"other-purpose",
        "body_sha256":"f"*64, "parent_restatement_id":"valid-parent", "confirmation_id":"confirmation"}
    for dimension, value in bindings.items():
        add("G36 terminal-claim " + dimension, STATE, f'claim.{dimension} IS NEW.{dimension}', '1=1',
            D + f"test_s15_terminal_claim_binding_is_an_engine_guard[{dimension}-{value}]")
    checks = {
        "phase": ("phase IN ('claimed','completed')", '1'),
        "kind": ("kind IN ('create', 'select_example', 'readback_started', 'confirm_words', 'score_words', 'repair_words', 'show_plan', 'hide_plan', 'h3', 'select_barrier', 'grant_share', 'decline_share', 'revoke_share', 'request', 'supersede_extraction')", '1'),
        "digest_length": ('length(body_sha256) = 64', '1'),
        "digest_character": ("body_sha256 NOT GLOB '*[^0-9a-f]*'", '1'),
        "expected_revision": ('expected_revision >= 0', '1'),
        "claim_revision": ('claim_revision >= 0', '1'),
        "claimed_terminal": ("phase = 'claimed' AND terminal_state IS NULL AND result_kind IS NULL", "phase = 'claimed' AND 1 AND result_kind IS NULL"),
        "claimed_result_kind": ("phase = 'claimed' AND terminal_state IS NULL AND result_kind IS NULL", "phase = 'claimed' AND terminal_state IS NULL AND 1"),
        "claimed_result_ref": ('AND result_ref IS NULL AND scored = 0', 'AND 1 AND scored = 0'),
        "terminal_enum": ("terminal_state IN ('applied','refused','unavailable','superseded')", '1'),
        "completed_terminal_missing": ("phase = 'completed' AND terminal_state IS NOT NULL", "phase = 'completed' AND 1"),
        "result_enum": ("result_kind IN ('episode','disposition','confirmation','restatement','hint','barrier','consent','attempt','event')", '1'),
        "scored_enum": ('scored IN (0,1)', '1'),
        "scored_terminal": ("scored = 0 OR (terminal_state = 'applied' AND kind IN", 'scored = 0 OR (1 AND kind IN'),
        "scored_kind": ("kind IN ('score_words','repair_words')", '1'),
        "scored_result_kind_null": ("result_kind IS NOT NULL AND result_kind = 'restatement'", "1 AND result_kind = 'restatement'"),
        "scored_result_ref_null": ("result_kind = 'restatement' AND result_ref IS NOT NULL", "result_kind = 'restatement' AND 1"),
    }
    for dimension, (old, new) in checks.items():
        add("G36 schema " + dimension, STATE, old, new, C + "test_phase_enum_without_lifecycle_check" if dimension == "phase" else D + f"test_command_schema_constraints[{dimension}]")
    add("G36 receipt phase uniqueness", STATE, '    UNIQUE (operation_id, phase),', '    CHECK (1),', D + "test_claim_and_terminal_uniqueness")
    add("G36 migration append-only inclusion", STATE, '    "events",\n    "journey_commands",', '    "events",', D + "test_additive_migration_twice_preserves_old_histories")
    # Every branch below has its own stored-case selector and ordinary plan is
    # retained as a positive control in the complete control batch.
    predicates = {
        "documented": ('if closure.care_evidenced:\n        step, allowed = "documented", ()', 'if False:\n        step, allowed = "documented", ()', 'documented'),
        "expired": ('elif closure.closure is ClosureState.EXPIRED_UNRESOLVED:\n        step, allowed = "expired",', 'elif False:\n        step, allowed = "expired",', 'expired_accepted'),
        "accepted": ('elif closure.closure is ClosureState.CLOSED_WITH_EVIDENCE:\n        step, allowed = "accepted",', 'elif False:\n        step, allowed = "accepted",', 'accepted'),
        "handoff": ('elif closure.closure is ClosureState.ESCALATED_TO_HUMAN:\n        step, allowed = "handoff",', 'elif False:\n        step, allowed = "handoff",', 'handoff'),
        "stopped": ('elif stopped:\n        step, allowed = "stopped",', 'elif False:\n        step, allowed = "stopped",', 'stopped'),
        "failed_request": ('closure.execution is ExecutionStatus.FAILED or snapshot.escalation_outcome == "failed"', 'snapshot.escalation_outcome == "failed"', 'failed'),
        "failed_handoff": ('closure.execution is ExecutionStatus.FAILED or snapshot.escalation_outcome == "failed"', 'closure.execution is ExecutionStatus.FAILED', 'handoff_failed'),
        "acknowledged": ('elif closure.execution is ExecutionStatus.ACKNOWLEDGED or snapshot.escalation_id is not None:', 'elif snapshot.escalation_id is not None:', 'acknowledged'),
        "neutral_handoff": ('elif closure.execution is ExecutionStatus.ACKNOWLEDGED or snapshot.escalation_id is not None:', 'elif closure.execution is ExecutionStatus.ACKNOWLEDGED:', 'handoff_unknown'),
        "pending": ('    if pending:\n        question, allowed, interpretation = None, (), "pending"', '    if False:\n        question, allowed, interpretation = None, (), "pending"', 'pending'),
    }
    for dimension, (old, new, case) in predicates.items():
        add("G03 step " + dimension, RULES, old, new, (C + f"test_neutral_contact_wins_over_understood_round[{case}]" if dimension in {"acknowledged", "neutral_handoff"} else J + f"test_twelve_screens_and_contradictions[{case}]"))
    add("G03 independent stop and transfer", RULES, 'flow = FlowView(stopped, snapshot.flow_stop_reason,',
        'flow = FlowView(False if step in {"accepted", "handoff"} else stopped, snapshot.flow_stop_reason,',
        J + "test_twelve_screens_and_contradictions[stopped_accepted]")
    add("G03 unavailable interpretation", RULES, 'elif kind == "interpretation_unavailable":', 'elif False:',
        J + "test_twelve_screens_and_contradictions[unavailable]")
    add("G03 uncertainty interpretation", RULES, '"uncertain" if latest.comparison.uncertain else "scored"', '"scored"',
        J + "test_twelve_screens_and_contradictions[uncertain]")
    add("G03 readback disclosure", RULES, 'plan=None if redacted else plan,', 'plan=plan,', J + "test_twelve_screens_and_contradictions[readback]")
    extend_mutations(add)
    add_decoder_mutations(add)
    add_inventory_mutations(add)
    add_classification_mutations(add)
    add_slice16_domain_mutations(add)
    add_slice16_flow_mutations(add)
    add_slice16_binding_mutations(add)
    add_slice16_store_mutations(add)
    add_slice16_entry_mutations(add)
    add_slice16_lifecycle_mutations(add)
    add_slice16_closed_copy_mutations(add)
    add_slice16_pending_navigation_mutations(add)
    add_slice16_source_word_mutations(add)
    add_slice16_full_width_question_mutation(add)
    boundary = (ROOT / 'tests/test_boundaries.py').read_text()
    start = boundary.index('NO_PLAN_DETECTORS = {'); end = boundary.index('\n}', start)
    for name, pattern in re.findall(r'    "([a-z_]+)": r"([^"]+)",', boundary[start:end]):
        add("G07 detector " + name, 'tests/test_boundaries.py', f'    "{name}": r"{pattern}",',
            f'    "{name}": r"(?!)",', f'tests/test_boundaries.py::test_serialized_detection_controls[json-{name}]')
    return rows


def extend_mutations(add):
    for dimension in ["episode_id", "disposition_version", "expected_revision", "kind", "purpose", "body_sha256", "parent_restatement_id", "confirmation_id"]:
        add("G12 recorded replay " + dimension, STATE,
            'if key != "token_schema" and row[key] != value:',
            f'if key not in {{"token_schema", "{dimension}"}} and row[key] != value:',
            C + f"test_replayed_binding_dimension[{dimension}]")
    for name, old, new, case in [
        ("waiting", 'elif closure.execution is ExecutionStatus.ATTEMPTED:\n        step, allowed = "permission",', 'elif False:\n        step, allowed = "permission",', "waiting"),
        ("permission", 'elif barrier:\n        step, allowed = "permission",', 'elif False:\n        step, allowed = "permission",', "permission"),
        ("barrier", 'elif latest is not None and latest.comparison.is_clean() and latest.hint_level is not HintLevel.H3:', 'elif False:', "barrier"),
        ("readback", 'elif started is not None:\n        step = "repair" if repair_field else "readback"', 'elif False:\n        step = "repair" if repair_field else "readback"', "readback"),
        ("repair", 'step = "repair" if repair_field else "readback"', 'step = "readback"', "repair"),
    ]:
        add("G03 step " + name, RULES, old, new, J + f"test_twelve_screens_and_contradictions[{case}]")
    add("G03 future command filtering", RULES, 'for kind in kinds if kind in IMPLEMENTED_JOURNEY_COMMANDS)',
        'for kind in kinds)', J + "test_twelve_screens_and_contradictions[plan]")
    add("G03 reveal metadata waiting", RULES, 'if visible:\n        screen_text.update(',
        'if visible and step != "permission":\n        screen_text.update(', F + "test_revealed_plan_metadata_survives_outcome_substate[waiting]")
    add("G03 reveal metadata handoff", RULES, 'if visible:\n        screen_text.update(',
        'if visible and step != "handoff":\n        screen_text.update(', F + "test_revealed_plan_metadata_survives_outcome_substate[handoff]")
    add("G03 repair parent event", STATE, '"parent_restatement_id": parent_id, "disposition_version": disposition_version',
        '"parent_restatement_id": None, "disposition_version": disposition_version', J + "test_repair_event_records_latest_parent_identity")
    add("G03 comparison partition", RULES, 'if matched | mismatched | uncertain != frozenset(COMPARISON_FIELDS):',
        'if False:', J + "test_corrupt_comparison_refuses_instead_of_understood[empty]")
    add("G03 comparison unknown field", RULES, 'if matched | mismatched | uncertain != frozenset(COMPARISON_FIELDS):',
        'if False:', J + "test_corrupt_comparison_refuses_instead_of_understood[unknown]")
    add("G03 comparison overlap", RULES, 'if matched & mismatched or matched & uncertain or mismatched & uncertain:',
        'if False:', C + "test_comparison_overlap_with_consistent_recall_outcome")
    add("G03 recall consistency", RULES, 'if recalled != (row.comparison.is_clean() and row.hint_level is not HintLevel.H3):',
        'if False:', J + "test_corrupt_comparison_refuses_instead_of_understood[wrong_outcome]")
    add("G31 expiry before unrelated round decode", SERVICE, 'snapshot = tx.load_snapshot(episode_id)\n            if snapshot.disposition is not None:',
        'snapshot = tx.load_bundle(episode_id).snapshot\n            if snapshot.disposition is not None:', J + "test_expiry_survives_corrupt_unrelated_round")
    for error, selector in [("rules.DomainError", "test_expiry_survives_unavailable_date_and_clock_regression"),
                             ("InvalidJourneyRecord", "test_expiry_survives_corrupt_unrelated_round")]:
        add("G31 expiry commit on " + error, SERVICE, 'except (rules.DomainError, InvalidJourneyRecord) as error:\n                # Invalid display/round metadata must not roll back valid expiry.\n                projection_error = error',
            'except (rules.DomainError, InvalidJourneyRecord) as error:\n                raise error', J + selector)
    add("G31 typed corrupt snapshot", STATE, 'raise InvalidJourneyRecord("corrupt journey snapshot") from error',
        'raise error', C + "test_corrupt_reader_error_maps_to_typed_recovery[load_snapshot]")
    add("G31 typed corrupt bundle", STATE, 'raise InvalidJourneyRecord("corrupt journey record") from error',
        'raise error', C + "test_corrupt_reader_error_maps_to_typed_recovery[load_bundle]")
    add("G31 aware stored timestamp", STATE, 'raise InvalidJourneyRecord("stored timestamps must be timezone-aware")',
        'value = value.replace(tzinfo=timezone.utc)', J + "test_naive_stored_deadline_is_unavailable")
    for case, old, new in [
        ("missing", 'if isinstance(body, dict) and body.get("schema") == "record-v1":', 'if False:'),
        ("duplicate", 'if record_id not in by_id or record_id in ordered_ids:', 'if record_id not in by_id:'),
        ("foreign", 'if record_id not in by_id or record_id in ordered_ids:', 'if record_id in ordered_ids:'),
    ]:
        add("G31 recorded reference " + case, STATE, old, new, C + f"test_event_reference_guard_is_typed_before_order_lookup[{case}]")
    for operation in ["UPDATE", "DELETE"]:
        add("G36 journey receipt " + operation, STATE, 'for operation in ("UPDATE", "DELETE"):\n            statements.append(',
            f'for operation in ("UPDATE", "DELETE"):\n            if table == "journey_commands" and operation == "{operation}":\n                continue\n            statements.append(',
            f"tests/test_state.py::TestTheRecordIsAppendOnly::test_every_table_refuses_{operation.lower()}[journey_commands]")
    add("G36 journey receipt REPLACE", STATE, 'self._conn.execute("PRAGMA recursive_triggers = ON")',
        'self._conn.execute("PRAGMA recursive_triggers = OFF")',
        "tests/test_state.py::TestTheRecordIsAppendOnly::test_every_table_refuses_replace[journey_commands]")


def add_inventory_mutations(add):
    add("G06 one permission prompt", "frontend/components/PatientJourney.tsx",
        'journey?.question && journey.question.text !== copy.heading', 'journey?.question',
        I + "test_renderer_announces_each_server_prompt_once[permission]")
    add("G06 one pending status", "frontend/components/PatientJourney.tsx",
        '{copy.feedback && <p role="status">{copy.feedback}</p>}',
        '{copy.feedback && <><p role="status">{copy.feedback}</p><p role="status">{copy.feedback}</p></>}',
        I + "test_renderer_announces_each_server_prompt_once[pending]")
    source = (ROOT / STATE).read_text()
    start = source.index("CREATE TABLE IF NOT EXISTS journey_commands (")
    end = source.index("\n);", start) + len("\n);")
    table = source[start:end]
    columns = {"operation_id": "TEXT", "phase": "TEXT", "episode_id": "TEXT", "expected_revision": "INTEGER",
        "claim_revision": "INTEGER", "kind": "TEXT", "purpose": "TEXT", "body_sha256": "TEXT", "scored": "INTEGER", "recorded_at": "TEXT"}
    for column, datatype in columns.items():
        add("G36 receipt required " + column, STATE, table,
            table.replace(f'{column} {datatype} NOT NULL', f'{column} {datatype}'),
            I + f"test_receipt_sql_required_values_and_claim_existence[{column}]")
    for case, old, new in [
        ("episode_fk", "episode_id TEXT NOT NULL REFERENCES episodes(id)", "episode_id TEXT NOT NULL"),
        ("parent_fk", "parent_restatement_id TEXT REFERENCES restatements(id)", "parent_restatement_id TEXT"),
        ("scored_result_kind", "result_kind = 'restatement'", "1"),
    ]:
        add("G36 receipt " + case, STATE, table, table.replace(old, new), I + f"test_receipt_sql_required_values_and_claim_existence[{case}]")
    add("G36 receipt claim exists", STATE,
        "SELECT RAISE(ABORT, 'completion requires matching claim') WHERE NOT EXISTS (",
        "SELECT RAISE(ABORT, 'completion requires matching claim') WHERE 0 AND NOT EXISTS (",
        I + "test_receipt_sql_required_values_and_claim_existence[claim_exists]")
    for row in json.loads((ROOT / "tests/journey_decoder_cases.json").read_text()):
        add("G06 inventory " + row["id"], row["target"], row["old"], row["new"], I + f'test_remaining_decoder_guard[{row["id"]}]')
    locator = "frontend/lib/episode-locator.ts"
    locator_clauses = {
        "keys": ('Object.keys(x).sort().join(",") === "episode_id,nonce,operation_id,schema"', 'true'),
        "schema": ('x.schema === "carerelay-locator-v1"', 'true'),
        "uuid_type": ('typeof v === "string" && UUID.test(v)', 'UUID.test(v as string)'),
        "key": ('if (!key.trim()) throw new Error("locator unavailable");', ''),
        "length": ('cookie.length > 1024', 'false'),
        "signature_canonical": ('bytes.toString("base64url") !== signature', 'false'),
        "operation_mac": ('!timingSafeEqual(actual, expected)', 'false'),
        "operation_payload": ('raw.toString("base64url") !== payload', 'false'),
        "operation_body": ('ordered(value) !== raw.toString("utf8")', 'false'),
        "operation_fields": ('Object.keys(value).sort().join(",") !== "body_sha256,confirmation_id,disposition_version,episode_id,expected_revision,kind,operation_id,parent_restatement_id,purpose,token_schema"', 'false'),
        "op_schema": ('value.token_schema !== "carerelay-command-v1"', 'false'),
        "op_revision_safe": ('!Number.isSafeInteger(value.expected_revision)', 'false'),
        "op_revision_negative": ('value.expected_revision < 0', 'false'),
        "op_id": ('!/^[A-Za-z0-9_-]{1,128}$/.test(value.operation_id)', 'false'),
        "op_episode": ('!UUID.test(value.episode_id)', 'false'),
        "op_digest": ('!/^[0-9a-f]{64}$/.test(value.body_sha256)', 'false'),
        "op_version": ('value.disposition_version !== null', 'false'),
        "op_parent": ('value.disposition_version !== null || value.parent_restatement_id !== null', 'value.disposition_version !== null || false'),
        "op_confirmation": ('value.parent_restatement_id !== null || value.confirmation_id !== null ||\n          value.purpose', 'value.parent_restatement_id !== null || false ||\n          value.purpose'),
        "op_kind": ('!["readback_started", "confirm_words", "score_words", "repair_words", "show_plan", "hide_plan", "h3", "supersede_extraction"].includes(value.kind)', 'false'),
        "op_purpose": ('value.purpose !== `episode:${value.kind}`', 'false'),
    }
    for index, case in enumerate(["nonce", "episode", "operation"]):
        locator_clauses[case] = ('[x.nonce, x.episode_id, x.operation_id].every(v => typeof v === "string" && UUID.test(v))',
            f'[x.nonce, x.episode_id, x.operation_id].filter((_, index) => index !== {index}).every(v => typeof v === "string" && UUID.test(v))')
    for case, (old, new) in locator_clauses.items():
        add("G09 locator " + case, locator, old, new, I + f"test_locator_and_operation_shape_have_real_signed_controls[{case}]")
    for field in ["action_id", "deadline_utc", "next_owner_id"]:
        add("G03 grounded match " + field, RULES,
            "if field in matched and field not in grounded.matched:",
            f'if field != "{field}" and field in matched and field not in grounded.matched:',
            J + f"test_matched_comparison_requires_recorded_grounded_span[absent-{field}]")
        add("G03 grounded mismatch " + field, RULES,
            "if field in mismatched and field not in grounded.mismatched:",
            f'if field != "{field}" and field in mismatched and field not in grounded.mismatched:',
            J + f"test_mismatched_comparison_requires_recorded_known_difference[absent-{field}]")
    add("G03 unknown hint kind", RULES,
        'visible = require_hint_event_kind(event.get("kind")) is HintEventKind.SHOWN',
        'visible = event.get("kind") == HintEventKind.SHOWN.value',
        J + "test_corrupt_current_journey_event_refuses_http_without_hiding_plan[unknown_hint_kind]")
    for kind in ["readback", "hint", "barrier"]:
        add("G03 malformed " + kind + " event", RULES,
            'if legacy is None:\n                raise JourneyUnavailable("invalid journey event")',
            'if legacy is None:\n                continue',
            J + f"test_corrupt_current_journey_event_refuses_http_without_hiding_plan[malformed_{kind}]")
    for name, old, new in [
        ("order", 'tuple(by_id[key] for key in ordered_ids)', 'tuple(by_id[key] for key in reversed(ordered_ids))'),
        ("kind", 'if event_kind != kind:', 'if False:'),
        ("legacy", 'body = {"record_id": payload.split(" ", 1)[0][8:]} if kind == "attempt_opened" and payload.startswith("attempt=") else {}', 'body = {}'),
        ("mixed", 'tuple(row for row in rows if row["id"] not in referenced)', 'tuple()'),
    ]:
        add("G31 event ordering " + name, STATE, old, new, I + f"test_record_order_is_event_order_with_explicit_legacy_fallback[{name}]")
    shape = {
        "schema": ('binding.token_schema != "carerelay-command-v1"', 'False'),
        "operation_type": ('type(value) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value)', 'not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value)'),
        "operation_empty": ('not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value)', 'False'),
        "revision_type": ('type(binding.expected_revision) is not int', 'False'),
        "revision_negative": ('not 0 <= binding.expected_revision <= SAFE_INTEGER', 'binding.expected_revision > SAFE_INTEGER'),
        "revision_unsafe": ('not 0 <= binding.expected_revision <= SAFE_INTEGER', 'binding.expected_revision < 0'),
        "version_type": ('type(binding.disposition_version) is not int', 'False'),
        "version_zero": ('binding.disposition_version < 1', 'False'),
        "kind": ('binding.kind not in COMMAND_KINDS', 'False'),
        "purpose_type": ('not isinstance(binding.purpose, str)', 'False'),
        "purpose_empty": ('not binding.purpose', 'False'),
        "digest_type": ('type(binding.body_sha256) is not str', 'False'),
        "digest_format": ('not re.fullmatch(r"[0-9a-f]{64}", binding.body_sha256)', 'False'),
        "parent_type": ('type(value) is not str or not 1 <= len(value) <= 128', 'not 1 <= len(value) <= 128'),
        "parent_empty": ('not 1 <= len(value) <= 128', 'len(value) > 128'),
        "confirmation_long": ('not 1 <= len(value) <= 128', 'len(value) < 1'),
    }
    for case, (old, new) in shape.items():
        add("G13 binding shape " + case, CODEC, old, new, I + f"test_binding_shape_has_typed_refusal[{case}]")
    for case, old, new in [
        ("float", 'raise CommandInvalid("unsupported canonical value")', 'return'),
        ("key", 'isinstance(x, dict) and all(type(k) is str for k in x)', 'isinstance(x, dict)'),
        ("duplicate", 'if key in result:', 'if False:'),
        ("kind", 'if kind not in COMMAND_KINDS:', 'if False:'),
        ("create", 'if kind == "create" and body != {}:', 'if False:'),
        ("choice_keys", 'if kind == "select_example" and set(body) != {"example_id"}:', 'if False:'),
    ]:
        add("G12 canonical " + case, CODEC, old, new, I + f"test_canonical_boundary_refuses_without_normalizing[{case}]")
    locator = "frontend/lib/episode-locator.ts"
    for case, old, new in [
        ("username", 'url.username || url.password', 'false || url.password'),
        ("password", 'url.username || url.password', 'url.username || false'),
        ("search", 'url.search || url.hash', 'false || url.hash'),
        ("hash", 'url.search || url.hash', 'url.search || false'),
        ("path", 'url.pathname !== "/"', 'false'),
        ("host", 'url.host.toLowerCase() !== host.toLowerCase()', 'false'),
        ("insecure", 'url.protocol !== "https:" && !(url.protocol === "http:" && local)', 'false'),
        ("loopback_disabled", 'loopbackTest && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)', '["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)'),
        ("episode", 'binding.episode_id !== locator.episode_id', 'false'),
        ("kind", 'binding.kind !== kind', 'false'),
        ("operation", 'binding.operation_id !== locator.operation_id', 'false'),
        ("revision", 'binding.expected_revision !== 0', 'false'),
    ]:
        add("G09 action " + case, locator, old, new, I + f"test_real_action_refuses_before_backend[{case}]")
    for case, old, new in [
        ("form_duplicate", 'keys.length !== 1', 'keys.length === 0'),
        ("form_extra", 'keys.length !== 1', 'keys.length === 0'),
    ]:
        add("G09 action " + case, "frontend/app/actions.ts", old, new, I + f"test_real_action_refuses_before_backend[{case}]")
    for case, old, new in [
        ("key_type", 'not isinstance(signing_key, bytes)', 'False'),
        ("key_empty", 'not signing_key.strip()', 'False'),
        ("token_limit", 'len(token) > 4096', 'False'),
        ("payload_base64", 'if _encode(raw) != payload:', 'if False:'),
        ("body_canonical", 'if canonical(body) != raw:', 'if False:'),
        ("schema_key", 'not isinstance(body, dict) or set(body) != set(OperationBinding.__dataclass_fields__)', 'not isinstance(body, dict)'),
    ]:
        add("G13 signed transport " + case, CODEC, old, new, I + f"test_signed_token_transport_has_independent_typed_refusal[{case}]")
    for case, old, new in [
        ("claim_episode", 'if binding.episode_id != self.episode_id:', 'if False:'),
        ("snapshot_episode", 'if episode_id != self.episode_id:\n            raise StateError("transaction episode mismatch")\n        try:', 'if False:\n            raise StateError("transaction episode mismatch")\n        try:'),
        ("bundle_episode", 'if episode_id != self.episode_id:\n            raise StateError("transaction episode mismatch")\n        row =', 'if False:\n            raise StateError("transaction episode mismatch")\n        row ='),
        ("nested_episode", 'self._journey_tx.episode_id != episode_id or (write and not self._journey_write)', '(write and not self._journey_write)'),
        ("read_to_write", 'self._journey_tx.episode_id != episode_id or (write and not self._journey_write)', 'self._journey_tx.episode_id != episode_id'),
        ("terminal_replay", 'if terminal is not None:\n            return CommandReceipt(operation_id,', 'if False:\n            return CommandReceipt(operation_id,'),
    ]:
        add("G31 transaction " + case, STATE, old, new, I + f"test_receipt_transaction_scope_and_terminal_replay[{case}]")
    for case, old, new in [
        ("kind", 'binding.kind != "select_example" or binding.purpose != PURPOSES["select_example"]', 'binding.purpose != PURPOSES["select_example"]'),
        ("purpose", 'binding.kind != "select_example" or binding.purpose != PURPOSES["select_example"]', 'binding.kind != "select_example"'),
        ("choice", 'if example_id != "scripted-appointment":', 'if False:'),
        ("date", 'if now_utc.astimezone(fixture.DISPLAY_TZ).date() != fixture.SCENARIO_NOW_UTC.astimezone(fixture.DISPLAY_TZ).date():', 'if False:'),
        ("prepare_parent", 'if kind not in {"select_example", "confirm_words"} or (kind == "select_example" and parent_id is not None):', 'if kind not in {"select_example", "confirm_words"}:'),
        ("prepare_digest", 'if kind == "select_example" and body_sha256 != request_digest(kind, {"example_id": "scripted-appointment"}):', 'if False:'),
        ("prepare_offer", 'if not any(o.kind == kind for o in journey.commands):', 'if False:'),
    ]:
        add("G13 intake " + case, SERVICE, old, new, I + f"test_intake_and_preparation_refusals_preserve_real_record[{case}]")
    add("G13 intake URL identity", "src/carerelay/api.py", '            if binding.episode_id != episode_id:', '            if False:', I + "test_intake_and_preparation_refusals_preserve_real_record[url_episode]")
    for suffix in ["transcript-confirmations", "hint-events", "restatements", "repairs", "barriers", "actions", "consents"]:
        source = (ROOT / "src/carerelay/api.py").read_text()
        start = source.index('async def require_implemented_patient_write'); end = source.index('\n\nasync def require_api_token', start)
        block = source[start:end]
        add("G38 retired route " + suffix, "src/carerelay/api.py", block,
            block.replace(f'"/{suffix}"', '"/__never_patient_route"'),
            "tests/test_api.py::TestRetiredPatientWrites::test_retired_post_refuses_without_state_change")


def add_classification_mutations(add):
    """Guards the 13 October review inventoried without an independent named kill.

    Every case here has a counterexample that changes observable behaviour. Guards
    whose removal is masked by a second layer, by a downstream validator, by the
    type system or by the single approved fixture are deliberately absent: they are
    classified with their empirical evidence in
    `docs/reviews/slice15-guard-evidence-classification.md` instead of being
    carried as permanent survivors.
    """
    identity = 'if not bundle.episode_id or type(bundle.revision) is not int or not 0 <= bundle.revision <= 9007199254740991:'
    policy = 'if policy is None or text is None or policy.version != disposition.policy_version or text.policy_version != disposition.policy_version:'
    display = 'if not action or not deadline or not original_owner or not fallback:'
    corrupt = I + "test_derive_journey_refuses_each_corrupt_recorded_input["
    ignores = I + "test_derive_journey_ignores_events_it_does_not_own["
    contract = I + "test_each_screen_carries_its_own_recorded_copy_and_cue["
    reconcile = F + "test_equal_command_cannot_reopen_known_stop_but_fresh_time_expiry_can_load"
    for case, old, new in [
        ("episode_id", identity, 'if type(bundle.revision) is not int or not 0 <= bundle.revision <= 9007199254740991:'),
        ("revision_type", identity, 'if not bundle.episode_id or not 0 <= bundle.revision <= 9007199254740991:'),
        ("revision_negative", identity, 'if not bundle.episode_id or type(bundle.revision) is not int:'),
        ("policy_version", policy, 'if policy is None or text is None or text.policy_version != disposition.policy_version:'),
        ("text_version", policy, 'if policy is None or text is None or policy.version != disposition.policy_version:'),
        ("action_outside_policy", 'if disposition.action_id not in policy.permitted_action_ids:', 'if False:'),
        ("action_text", display, 'if not deadline or not original_owner or not fallback:'),
        ("readback_identity", 'if not isinstance(started, str) or not started:', 'if not started:'),
    ]:
        add("G03 recorded input " + case, RULES, old, new, corrupt + case + "]")
    add("G03 recorded identity revision_unsafe", RULES,
        'not 0 <= bundle.revision <= 9007199254740991', 'not 0 <= bundle.revision', corrupt + "revision_unsafe]")
    add("G03 no-plan disposition branch", RULES,
        'disposition = bundle.snapshot.disposition\n    if disposition is None:',
        'disposition = bundle.snapshot.disposition\n    if False:', J + "test_no_plan_surfaces[api]")
    add("G03 later display day", RULES,
        'disposition.clinical_deadline_utc.astimezone(display_tz).date() != now_utc.astimezone(display_tz).date()',
        'False', I + "test_derive_journey_refuses_an_unusable_display_date[later_day]")
    add("G03 unrelated event kind filter", RULES,
        'if kind not in {"readback_started", "hint_event", "barrier_recorded", "interpretation_unavailable"}:',
        'if False:', ignores + "unrelated_non_dict_event]")
    add("G03 foreign event version filter", RULES,
        'if event.get("disposition_version", disposition.version) != disposition.version:', 'if False:',
        ignores + "foreign_version_event]")
    for case, old, new, selector in [
        ("readback dispatch", 'if kind == "readback_started":', 'if False:',
         J + "test_twelve_screens_and_contradictions[readback]"),
        ("hint dispatch", 'elif kind == "hint_event":', 'elif False:',
         F + "test_revealed_plan_metadata_survives_outcome_substate"),
        ("barrier dispatch", 'elif kind == "barrier_recorded":', 'elif False:',
         J + "test_twelve_screens_and_contradictions[permission]"),
        ("H3 sets the ladder", 'if level is HintLevel.H3:', 'if False:', contract + "h3_event]"),
        ("H2 or shown sets the ladder", 'elif hint is not HintLevel.H3 and (visible or level is HintLevel.H2):',
         'elif False:', F + "test_revealed_plan_metadata_survives_outcome_substate"),
        ("recorded round wins the ladder",
         'if latest.hint_level is HintLevel.H3 or (latest.hint_level is HintLevel.H2 and hint is not HintLevel.H3):',
         'if False:', contract + "h3_round]"),
        ("unavailable survives a later round", 'if interpretation != "unavailable":', 'if False:',
         J + "test_twelve_screens_and_contradictions[uncertain]"),
        ("timing repair field",
         'if "deadline_utc" in latest.comparison.mismatched and completed_repairs < MAX_REPAIR_ROUNDS:',
         'if False:', J + "test_twelve_screens_and_contradictions[repair]"),
        ("latest round gate", 'if latest is not None:', 'if False:',
         J + "test_twelve_screens_and_contradictions[repair]"),
        ("waiting screen text", 'if step == "permission" and closure.execution is ExecutionStatus.ATTEMPTED:',
         'if False:', contract + "waiting]"),
        ("pending feedback text", 'if interpretation == "pending":', 'if False:', contract + "pending]"),
        ("unavailable feedback text", 'elif interpretation == "unavailable":', 'elif False:', contract + "unavailable]"),
        ("uncertain feedback text", 'elif interpretation == "uncertain":', 'elif False:', 'tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[timing_uncertain_owner]'),
    ]:
        add("G03 " + case, RULES, old, new, selector)
    for case in ["scalar accept", "list accept"]:
        add("G12 canonical " + case, CODEC,
            'if x is None or type(x) in (str, bool, int):' if case == "scalar accept" else 'if isinstance(x, list):',
            'if False:', I + "test_canonical_boundary_refuses_without_normalizing[key]")
    add("G13 binding shape version_nullable", CODEC,
        'if binding.disposition_version is not None and (', 'if False and (',
        I + "test_binding_shape_has_typed_refusal[version_type]")
    add("G13 MAC comparison", CODEC, 'if not hmac.compare_digest(signature, expected):', 'if False:',
        D + "test_s15_mac_binds_each_dimension")
    add("G13 start exact body", SERVICE, 'if binding.body_sha256 != request_digest("create", {}):', 'if False:',
        I + "test_start_refuses_a_capability_it_did_not_issue[changed_create_body]")
    add("G13 preparation parameter log scrubbing", "src/carerelay/api.py",
        'if prepare_kind is not None or body_sha256 is not None or parent_id is not None:',
        'if prepare_kind is not None and body_sha256 is not None:',
        I + "test_preparation_requires_kind_and_digest_together[parent_only]")
    add("G13 select token only for the allowlisted offer", SERVICE, 'if offer.kind == "select_example":', 'if False:',
        D + "test_lost_create_and_intake_replay_projects_fresh")
    add("G31 replay requires a claim", SERVICE,
        'if receipt is None:\n                raise CommandConflict("operation has not been claimed")',
        'if False:\n                raise CommandConflict("operation has not been claimed")',
        I + "test_replay_reports_the_recorded_receipt_or_refuses[unclaimed]")
    add("G13 intake replay does not rewrite the disposition", SERVICE, 'if claimed.newly_claimed:', 'if False:',
        D + "test_lost_create_and_intake_replay_projects_fresh")
    add("G02 recorded policy resolved in the transaction", STATE, 'if resolved is not None:', 'if False:',
        J + "test_recorded_policy_selected")
    add("G02 recorded policy needs a registered version", STATE, 'if snapshot.disposition is not None:',
        'if False:', J + "test_recorded_policy_selected")
    add("G37 unknown episode has no snapshot", STATE,
        '        ).fetchone()\n        if episode is None:\n            raise EpisodeNotFound(episode_id)',
        '        ).fetchone()\n        if False:\n            raise EpisodeNotFound(episode_id)',
        I + "test_unknown_episode_has_no_snapshot_at_the_store")
    add("G06 closure reconcile compares one version", DECODER,
        'if (current.disposition_version === next.disposition_version &&', 'if (false &&', reconcile)
    add("G06 closure reconcile keeps a foreign episode", DECODER,
        'if (!current || current.episode_id !== next.episode_id) return next;', 'if (!current) return next;', reconcile)
    add("G06 closure reconcile equal revision needs a read", DECODER,
        'if (next.revision === current.revision && !fromRead) {', 'if (next.revision === current.revision) {', reconcile)


def add_slice16_domain_mutations(add):
    """Partial Slice 16 domain proof; no claim about its unfinished flow."""
    selector = "tests/test_field_repair.py::"
    def pin(label, target, old, new, test):
        add("Slice16 " + label, target, old, new, selector + test)
    pin("G18 offline extraction use", "src/carerelay/adp_extraction.py",
        'spans = tuple(source_candidates(request.confirmed_text, forms) for forms in fields)',
        'spans = ((), (), ())', "test_offline_exact_source_offsets")
    pin("G18 exact source offsets", RULES,
        'SourceSpan(match.group(), match.start(), match.end())',
        'SourceSpan(match.group(), 0, len(match.group()))', "test_offline_exact_source_offsets")
    pin("G18 exact source text", RULES, 'SourceSpan(match.group(), match.start(), match.end())',
        'SourceSpan(normalise(match.group()), match.start(), match.end())', "test_offline_preserves_whitespace_and_chinese_offsets")
    pin("G18 source start boundary", RULES, 'pattern = r"(?<!\\w)" + pattern',
        'pattern = pattern', "test_offline_owner_forms_have_word_boundaries[theme]")
    pin("G18 source end boundary", RULES, 'pattern += r"(?!\\w)"',
        'pattern += ""', "test_offline_owner_forms_have_word_boundaries[myselfish]")
    pin("G18 source empty form", RULES, 'if pattern:\n            for match in re.finditer',
        'if True:\n            for match in re.finditer', "test_empty_form_is_not_a_source_span")
    pin("G18 overlapping form", RULES,
        'other.start <= span.start and span.end <= other.end and other != span',
        'False', "test_source_candidates_prefers_a_complete_overlapping_form")
    pin("G18 offline missing span uncertainty", "src/carerelay/adp_extraction.py",
        'if span is None)\n        raw = RawExtraction',
        'if False)\n        raw = RawExtraction', "test_offline_bare_tomorrow_does_not_invent_a_time")
    for word in ["not", "no", "never", "cannot", "unsure", "uncertain", "maybe", "perhaps", "might", "may", "could", "would", "if", "or"]:
        old = r'\b(?:not|no|never|cannot|unsure|uncertain|maybe|perhaps|might|may|could|would|if|or)\b'
        values = [x for x in "not|no|never|cannot|unsure|uncertain|maybe|perhaps|might|may|could|would|if|or".split("|") if x != word]
        new = r'\b(?:' + "|".join(values) + r')\b'
        pin("G20 doubt " + word, RULES, old, new, "test_each_doubt_form_prevents_recall[" + word + "]")
    for label, old, new, test in [
        ("negated contraction", r"|\b\w+n['’]t\b|\?|？|不|没|未", r"|\?|？|不|没|未", "test_each_doubt_form_prevents_recall[contraction]"),
        ("question", r"|\b\w+n['’]t\b|\?|？|不|没|未", r"|\b\w+n['’]t\b|？|不|没|未", "test_whole_answer_doubt_is_independent"),
        ("chinese not", "|不|没|未", "|没|未", "test_each_doubt_form_prevents_recall[han_not]"),
        ("chinese no", "|不|没|未", "|不|未", "test_each_doubt_form_prevents_recall[han_no]"),
        ("chinese not yet", "|不|没|未", "|不|没", "test_each_doubt_form_prevents_recall[han_not_yet]"),
        ("backward correction", 'if _READBACK_BACKWARD.search(sentence):', 'if False:', "test_backward_correction_invalidates_all_retention"),
        ("unsupported correction", 'elif _READBACK_BACKWARD.search(sentence) and re.search(', 'elif False and re.search(', "test_whole_answer_doubt_is_independent"),
        ("multiple candidates", 'if len(resolved) > 1:', 'if False:', "test_whole_answer_doubt_is_independent"),
        ("unsupported new value", 'if any(not any(span.start <= hit.start() and hit.end() <= span.end',
            'if False and any(not any(span.start <= hit.start() and hit.end() <= span.end', "test_unsupported_other_field_invalidates_retention"),
    ]:
        pin("G20 " + label, RULES, old, new, test)
    for label, old, new, test in [
        ("policy", 'if context.policy_version != policy.version:', 'if False:', "test_retention_requires_its_policy_and_grounded_identity[policy]"),
        ("field", 'if source.field not in COMPARISON_FIELDS:', 'if False:', "test_retention_requires_its_policy_and_grounded_identity[field]"),
        ("row identity", 'if not source.source_restatement_id or not source.source_confirmation_id:',
            'if not source.source_confirmation_id:', "test_retention_requires_its_policy_and_grounded_identity[row]"),
        ("confirmation identity", 'if not source.source_restatement_id or not source.source_confirmation_id:',
            'if not source.source_restatement_id:', "test_retention_requires_its_policy_and_grounded_identity[confirmation]"),
        ("grounded source", 'if value is None or value != source.canonical_value:', 'if value != source.canonical_value:', "test_retention_requires_its_policy_and_grounded_identity[unknown_value]"),
        ("source canonical value", 'if value is None or value != source.canonical_value:', 'if value is None:', "test_bad_grounded_retention_refuses"),
        ("full answer", 'if context.repair_field is None:', 'if False:', "test_full_answer_correction_does_not_borrow_missing_fields"),
        ("selected field", 'if source.field == context.repair_field:', 'if False:', "test_selected_field_is_not_retained_when_answer_is_missing"),
        ("explicit replacement", 'if values.get(source.field) is not None:', 'if False:', "test_explicit_other_field_replaces_retention"),
        ("whole answer doubt", 'if source.field in whole_answer_doubt:', 'if False:', "test_backward_correction_invalidates_all_retention"),
        ("known match retained", 'values[source.field] = source.source_span.text', 'values[source.field] = None', "test_timing_only_retains_grounded_action_owner"),
        ("missing doubt cleared only for retained", 'uncertain.discard(source.field)', 'pass', "test_timing_only_retains_grounded_action_owner"),
        ("transitive reference", 'retained.append(source)', 'pass', "test_timing_only_retains_grounded_action_owner"),
        ("owner source resolution", 'value = _resolve_id(source.source_span.text, policy.owner_aliases, policy.permitted_owner_ids)',
            'value = source.canonical_value', "test_owner_retention_must_resolve_its_grounded_value"),
        ("deadline source resolution", 'value = _resolve_deadline(source.source_span.text, now_utc, display_tz, policy.deadline_forms)',
            'value = source.canonical_value', "test_deadline_retention_refuses_a_different_source_value"),
    ]:
        pin("G19 retention " + label, RULES, old, new, test)



def add_slice16_flow_mutations(add):
    field = "tests/test_field_repair.py::"
    adp = "src/carerelay/adp_extraction.py"
    def pin(label, target, old, new, selector):
        add("Slice16 " + label, target, old, new, selector)
    for dimension, old, new in [
        ("episode", 'context.episode_id != bundle.episode_id', 'False'),
        ("version", 'context.disposition_version != disposition.version', 'False'),
        ("policy", 'context.policy_version != disposition.policy_version', 'False'),
        ("revision", 'if bundle.revision != context.claim_revision:', 'if False:'),
        ("stop", 'bundle.snapshot.flow_stop_reason is not None or bundle.snapshot.expiry_event_id is not None', 'bundle.snapshot.expiry_event_id is not None'),
        ("sticky_expiry", 'bundle.snapshot.flow_stop_reason is not None or bundle.snapshot.expiry_event_id is not None', 'bundle.snapshot.flow_stop_reason is not None'),
        ("deadline", 'if now_utc >= disposition.clinical_deadline_utc:', 'if False:'),
        ("attempt", 'context.attempt_id != journey.flow.readback_attempt_id or context.parent_id != journey.flow.latest_restatement_id', 'context.parent_id != journey.flow.latest_restatement_id'),
        ("parent", 'context.attempt_id != journey.flow.readback_attempt_id or context.parent_id != journey.flow.latest_restatement_id', 'context.attempt_id != journey.flow.readback_attempt_id'),
        ("cue", 'context.effective_hint != journey.flow.effective_hint or context.effective_hint is HintLevel.H3', 'context.effective_hint is HintLevel.H3'),
        ("repair_count", 'if context.completed_repairs != journey.flow.completed_repairs or context.completed_repairs >= MAX_REPAIR_ROUNDS:', 'if False:'),
        ("confirmation", 'confirmed["confirmation_id"] == context.confirmation_id and confirmed["text"] == context.confirmed_text', 'confirmed["text"] == context.confirmed_text'),
        ("words", 'confirmed["confirmation_id"] == context.confirmation_id and confirmed["text"] == context.confirmed_text', 'confirmed["confirmation_id"] == context.confirmation_id'),
    ]:
        pin("G34 final " + dimension, RULES, old, new, field + "test_final_context_fences_are_independent[" + dimension + "]")
    for case, old, new in [
        ("mode", 'result.mode != "local-sim"', 'False'),
        ("validation", 'result.validation != "valid"', 'False'),
        ("schema", 'raw.schema_version != "carerelay-readback-v1"', 'False'),
        ("refused_type", 'type(raw.refused) is not bool', 'False'),
        ("refused", 'or raw.refused:', 'or False:'),
        ("uncertainty_type", 'not isinstance(raw.uncertain_fields, frozenset)', 'False'),
        ("unknown_uncertainty", 'not raw.uncertain_fields <= frozenset(COMPARISON_FIELDS)', 'False'),
        ("null_without_uncertainty", 'if field not in raw.uncertain_fields:', 'if False:'),
        ("span_type", 'not isinstance(span, SourceSpan)', 'False'),
        ("start_bool", 'type(span.start) is not int', 'False'),
        ("end_bool", 'type(span.end) is not int', 'False'),
        ("negative", 'not 0 <= span.start < span.end <= len(confirmed_text)', 'not span.start < span.end <= len(confirmed_text)'),
        ("empty", 'not 0 <= span.start < span.end <= len(confirmed_text)', 'not 0 <= span.start <= span.end <= len(confirmed_text)'),
        ("end_overrun", 'not 0 <= span.start < span.end <= len(confirmed_text)', 'not 0 <= span.start < span.end'),
        ("ungrounded", 'confirmed_text[span.start:span.end] != span.text', 'False'),
    ]:
        pin("G18 offline boundary " + case, adp, old, new, field + "test_offline_output_boundary_refuses_each_invalid_shape[" + case + "]")
    pin("G16 scored state atomic receipt", SERVICE,
        'receipt = tx.complete_once(binding.operation_id, state="applied", result_ref=ref, result_kind="restatement",',
        'self._store._conn.commit()\n                receipt = tx.complete_once(binding.operation_id, state="applied", result_ref=ref, result_kind="restatement",',
        field + "test_process_crash_between_score_and_receipt_rolls_back_both")
    pin("G15 late terminal fences score", SERVICE,
        'if receipt.state != "pending":\n                pass',
        'if False:\n                pass', field + "test_pending_duplicate_calls_one_extractor_and_supersede_fences_late_output")
    pin("G14 claimed replay avoids extraction", SERVICE,
        'if receipt is not None:\n            return CommandResponse(receipt, self.project_journey(binding.episode_id))',
        'if receipt is not None:\n            return self.score_confirmed(replace(binding, operation_id=binding.operation_id + "r"))',
        field + "test_pending_duplicate_calls_one_extractor_and_supersede_fences_late_output")
    pin("G18 exact confirmation body", SERVICE,
        'if binding.body_sha256 != request_digest("confirm_words", {"text": text, "parent_id": binding.parent_restatement_id}):',
        'if False:', field + "test_exact_confirmed_words_and_latest_parent_are_not_substitutable")
    pin("G19 latest confirmation preparation parent", SERVICE,
        'if kind == "confirm_words" and parent_id != journey.flow.latest_restatement_id:',
        'if False:', field + "test_exact_confirmed_words_and_latest_parent_are_not_substitutable")
    pin("G18 lost confirmation preserves identity", SERVICE,
        'if kind == "confirm_words":\n                for row in reversed(bundle.commands):',
        'if False:\n                for row in reversed(bundle.commands):', field + "test_same_body_preparation_recovers_the_confirmed_operation")
    pin("G18 store owns scoring claim", STATE,
        'if owned is None:\n            raise CommandConflict("score has no exact owned pending claim")',
        'if False:\n            raise CommandConflict("score has no exact owned pending claim")', field + "test_store_will_not_score_without_an_owned_scoring_claim")
    pin("G22 H3 stop", SERVICE,
        'if binding.kind == "h3":\n                        tx._event("flow_stopped",',
        'if False:\n                        tx._event("flow_stopped",', field + "test_h3_stops_without_extraction_or_round")
    pin("G23 hide does not lower cue", SERVICE,
        'journey.flow.effective_hint if binding.kind == "hide_plan" else HintLevel.H2',
        'HintLevel.H1 if binding.kind == "hide_plan" else HintLevel.H2', field + "test_reveal_hide_reload_keeps_highest_cue")
    pin("G23 timing exposure commits before display", SERVICE,
        'if journey.step == "repair" and journey.flow.effective_hint not in {HintLevel.H2, HintLevel.H3}:',
        'if False:', field + "test_confirmed_round_zero_and_grounded_timing_repair")
    pin("G18 persisted provenance", STATE, 'provenance=provenance,', 'provenance=None,', field + "test_ledger_names_offline_provenance_and_keeps_legacy_unknown")
    pin("G08 fresh document on readback", "frontend/components/PatientJourney.tsx",
        'window.location.assign("/"); // A fresh document removes the prior plan\'s HTML/RSC.',
        '// omitted document replacement', F + "test_readback_transition_replaces_the_answer_bearing_document")
    pin("G23 hide keeps opener focus", "frontend/components/PatientJourney.tsx",
        'if (result.journey.step === journey?.step) showOpener.current?.focus();',
        'if (result.journey.step === journey?.step) main.current?.focus();', F + "test_hide_response_keeps_focus_on_the_show_opener")
    pin("G18 new capability decoder", LOCATOR,
        'if (["create", "select_example"].includes(value.kind)) {',
        'if (true) {', D + "test_s16_server_capabilities_decode_at_the_real_frontend_boundary")



def add_slice16_binding_mutations(add):
    add('Slice16 G19 grounding parent_version', RULES, 'parent.disposition_version != bundle.snapshot.disposition.version', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[parent_version]')
    add('Slice16 G19 grounding parent_attempt', RULES, 'parent.provenance.get("attempt_id") != attempt_id', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[parent_attempt]')
    add('Slice16 G19 grounding nonancestor', RULES, 'source_id not in ancestors', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[nonancestor]')
    add('Slice16 G19 grounding source_policy', RULES, 'meta.get("policy_version") != bundle.policy.version', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[source_policy]')
    add('Slice16 G19 grounding source_attempt', RULES, 'meta.get("attempt_id") != attempt_id or field not in source.comparison.matched', 'False or field not in source.comparison.matched', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[source_attempt]')
    add('Slice16 G19 grounding source_version', RULES, 'source.disposition_version != bundle.snapshot.disposition.version', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[source_version]')
    add('Slice16 G19 grounding source_match', RULES, 'field not in source.comparison.matched', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[source_match]')
    add('Slice16 G19 grounding confirmation_episode', RULES, 'event is None or event.get("episode_id") != bundle.episode_id', 'event is None or False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[confirmation_episode]')
    add('Slice16 G19 grounding confirmation_attempt', RULES, 'event.get("attempt_id") != attempt_id\n                or event.get("disposition_version")', 'False\n                or event.get("disposition_version")', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[confirmation_attempt]')
    add('Slice16 G19 grounding confirmation_version', RULES, 'event.get("disposition_version") != source.disposition_version', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[confirmation_version]')
    add('Slice16 G19 grounding confirmation_parent', RULES, 'event.get("parent_id") != meta.get("parent_id")', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[confirmation_parent]')
    add('Slice16 G19 grounding start_type', RULES, 'type(span.start) is not int or type(span.end) is not int or not 0 <= span.start < span.end <= len(event["text"])', 'False or type(span.end) is not int or not 0 <= span.start < span.end <= len(event["text"])', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[start_type]')
    add('Slice16 G19 grounding end_type', RULES, 'type(span.end) is not int or not 0 <= span.start < span.end <= len(event["text"])', 'False or not 0 <= span.start < span.end <= len(event["text"])', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[end_type]')
    add('Slice16 G19 grounding offset_negative', RULES, 'not 0 <= span.start < span.end <= len(event["text"])', 'not span.start < span.end <= len(event["text"])', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[offset_negative]')
    add('Slice16 G19 grounding offset_empty', RULES, 'not 0 <= span.start < span.end <= len(event["text"])', 'not 0 <= span.start <= span.end <= len(event["text"])', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[offset_empty]')
    add('Slice16 G19 grounding offset_overrun', RULES, 'not 0 <= span.start < span.end <= len(event["text"])', 'not 0 <= span.start < span.end', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[offset_overrun]')
    add('Slice16 G19 grounding offset_text', RULES, 'event["text"][span.start:span.end] != span.text', 'False', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[offset_text]')
    add('Slice16 G19 grounding unknown_value', RULES, 'if value is None:\n            raise JourneyUnavailable("retention value is unknown")', 'if False:\n            raise JourneyUnavailable("retention value is unknown")', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[unknown_value]')
    add('Slice16 G19 grounding confirmation_missing', RULES, 'if (event is None or event.get("episode_id") != bundle.episode_id', 'if event is None:\n            event = {"episode_id": bundle.episode_id, "attempt_id": attempt_id, "disposition_version": source.disposition_version, "parent_id": meta.get("parent_id"), "text": "go to the clinic"}\n        if (False or event.get("episode_id") != bundle.episode_id', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[confirmation_missing]')
    add('Slice16 G19 grounding span_shape', RULES, 'if not isinstance(span_data, dict):\n            raise JourneyUnavailable("retention has no source span")', 'if not isinstance(span_data, dict):\n            span_data = {"text": "go to the clinic", "start": 0, "end": 16}', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[span_shape]')
    add('Slice16 G19 grounding missing_ancestor', RULES, 'if previous is not None and node is None:\n            raise JourneyUnavailable("missing retention ancestor")', 'if previous is not None and node is None:\n            break', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[missing_ancestor]')
    add('Slice16 G19 grounding cycle', RULES, 'if node.restatement_id in ancestors:\n            raise JourneyUnavailable("cyclic retention chain")', 'if node.restatement_id in ancestors:\n            break', 'tests/test_field_repair.py::test_grounded_chain_refuses_each_untrusted_source[cycle]')
    add('Slice16 G18 confirmation version', RULES, 'event.get("disposition_version") != bundle.snapshot.disposition.version', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[version]')
    add('Slice16 G18 confirmation attempt', RULES, 'event.get("attempt_id") != attempt_id:\n            continue', 'False:\n            continue', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[attempt]')
    add('Slice16 G18 confirmation episode', RULES, 'event.get("episode_id") != bundle.episode_id or event.get("policy_version") != bundle.policy.version', 'False or event.get("policy_version") != bundle.policy.version', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[episode]')
    add('Slice16 G18 confirmation policy', RULES, 'event.get("policy_version") != bundle.policy.version', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[policy]')
    add('Slice16 G18 confirmation text_type', RULES, 'not isinstance(event.get("text"), str) or not event["text"].strip() or len(event["text"]) > 2048', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[text_type]')
    add('Slice16 G18 confirmation text_empty', RULES, 'not event["text"].strip()', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[text_empty]')
    add('Slice16 G18 confirmation text_long', RULES, 'len(event["text"]) > 2048', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[text_long]')
    add('Slice16 G18 confirmation id_type', RULES, 'not isinstance(event.get("confirmation_id"), str)', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[id_type]')
    add('Slice16 G18 confirmation id_empty', RULES, 'not event["confirmation_id"]', 'False', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[id_empty]')
    add('Slice16 G18 confirmation parent', RULES, 'current.get("parent_id") == parent_id', 'True', 'tests/test_field_repair.py::test_confirmation_event_requires_each_binding[parent]')
    add("Slice16 G18 missing output stays unavailable", "src/carerelay/adp_extraction.py", 'if result.mode != "local-sim" or result.validation != "valid" or result.raw is None:\n        return None', 'if result.mode != "local-sim" or result.validation != "valid" or result.raw is None:\n        return RawExtraction("carerelay-readback-v1", None, None, None, frozenset(COMPARISON_FIELDS), False)', "tests/test_field_repair.py::test_offline_output_boundary_refuses_each_invalid_shape[missing_raw]")



def add_slice16_store_mutations(add):
    add('Slice16 G18 store confirmation claim', STATE, 'if (claim is None or claim["kind"] != "confirm_words" or claim["claim_revision"] != bundle.revision\n                or claim["parent_restatement_id"] != context.parent_id\n                or claim["body_sha256"] != request_digest("confirm_words", {"text": context.confirmed_text, "parent_id": context.parent_id})):', 'if False:', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[claim]')
    add('Slice16 G18 store confirmation kind', STATE, 'claim["kind"] != "confirm_words"', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[kind]')
    add('Slice16 G18 store confirmation revision', STATE, 'claim["claim_revision"] != bundle.revision', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[revision]')
    add('Slice16 G18 store confirmation parent', STATE, 'claim["parent_restatement_id"] != context.parent_id', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[parent]')
    add('Slice16 G18 store confirmation digest', STATE, 'claim["body_sha256"] != request_digest("confirm_words", {"text": context.confirmed_text, "parent_id": context.parent_id})', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[digest]')
    add('Slice16 G18 store confirmation episode', STATE, 'context.episode_id != self.episode_id', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[episode]')
    add('Slice16 G18 store confirmation version', STATE, 'context.disposition_version != journey.disposition_version', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[version]')
    add('Slice16 G18 store confirmation policy', STATE, 'context.policy_version != journey.policy_version', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[policy]')
    add('Slice16 G18 store confirmation attempt', STATE, 'context.attempt_id != journey.flow.readback_attempt_id', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[attempt]')
    add('Slice16 G18 store confirmation latest_parent', STATE, 'context.parent_id != journey.flow.latest_restatement_id', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[latest_parent]')
    add('Slice16 G18 store confirmation stop', STATE, 'or journey.flow.stopped or bundle.snapshot.expiry_event_id is not None', 'or False or bundle.snapshot.expiry_event_id is not None', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[stop]')
    add('Slice16 G18 store confirmation deadline', STATE, 'now_utc >= bundle.snapshot.disposition.clinical_deadline_utc', 'False', 'tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[deadline]')
    add('Slice16 G18 owned score kind', STATE, 'AND c.kind = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[kind]')
    add('Slice16 G18 owned score version', STATE, 'AND c.disposition_version = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[version]')
    add('Slice16 G18 owned score revision', STATE, 'AND c.claim_revision = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[revision]')
    add('Slice16 G18 owned score confirmation', STATE, 'AND c.confirmation_id = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[confirmation]')
    add('Slice16 G18 owned score parent', STATE, 'AND (c.parent_restatement_id = ? OR (c.parent_restatement_id IS NULL AND ? IS NULL))', 'AND (? IS NOT NULL OR ? IS NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[parent]')
    add('Slice16 G18 owned score purpose', STATE, 'AND c.purpose = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[purpose]')
    add('Slice16 G18 owned score digest', STATE, 'AND c.body_sha256 = ?', 'AND (? IS NOT NULL)', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[digest]')
    add('Slice16 G18 owned score terminal', STATE, "AND NOT EXISTS (SELECT 1 FROM journey_commands t WHERE t.operation_id = c.operation_id AND t.phase = 'completed')", 'AND 1', 'tests/test_field_repair.py::test_scoring_store_requires_each_owned_claim_dimension[terminal]')
    add("Slice16 G34 source scanner includes new server files", "tests/test_boundaries.py", 'VICTIM_FILES += tuple(("readback server source", name) for name in (', 'VICTIM_FILES += tuple(("readback server source", name) for name in () if False for name in (', "tests/test_boundaries.py::test_new_readback_server_files_are_scanned_with_positive_controls")


def add_slice16_entry_mutations(add):
    add("Slice16 G22 stopped screen ends repair prompting", RULES,
        'if not stopped and closure.closure is ClosureState.OPEN:', 'if closure.closure is ClosureState.OPEN:',
        "tests/test_field_repair.py::test_two_uncertain_repairs_stop_without_round_zero_reset")
    add('Slice16 G18 service entry purpose', SERVICE, 'if binding.purpose != self._readback_purpose(journey, binding.kind):', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[purpose]')
    add('Slice16 G18 service entry offer', SERVICE, 'if not any(o.kind == binding.kind for o in journey.commands):', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[offer]')
    add('Slice16 G18 service entry parent', SERVICE, 'if binding.parent_restatement_id != parent:', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[parent]')
    add('Slice16 G18 service entry scoring_kind', SERVICE, 'binding.kind not in {"score_words", "repair_words"}', 'False', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[scoring_kind]')
    add('Slice16 G18 service entry scoring_confirmation', SERVICE, 'or binding.confirmation_id is None:\n            raise CommandInvalid("unpermitted scoring")', 'or False:\n            raise CommandInvalid("unpermitted scoring")', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[scoring_confirmation]')
    add('Slice16 G18 service entry scoring_digest', SERVICE, 'if binding.body_sha256 != request_digest(binding.kind, {"confirmation_id": binding.confirmation_id}):', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[scoring_digest]')
    add('Slice16 G18 service entry event_kind', SERVICE, 'binding.kind not in {"readback_started", "show_plan", "hide_plan", "h3"}', 'False', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[event_kind]')
    add('Slice16 G18 service entry event_confirmation', SERVICE, 'or binding.confirmation_id is not None:\n            raise CommandInvalid("unpermitted readback event")', 'or False:\n            raise CommandInvalid("unpermitted readback event")', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[event_confirmation]')
    add('Slice16 G18 service entry event_digest', SERVICE, 'if binding.body_sha256 != request_digest(binding.kind, {}):', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[event_digest]')
    add('Slice16 G18 service entry confirmation_kind', SERVICE, 'binding.kind != "confirm_words"', 'False', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[confirmation_kind]')
    add('Slice16 G18 service entry confirmation_id', SERVICE, 'or binding.confirmation_id is not None:\n            raise CommandInvalid("unpermitted confirmation")', 'or False:\n            raise CommandInvalid("unpermitted confirmation")', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[confirmation_id]')
    add('Slice16 G18 service entry words_type', SERVICE, 'if type(text) is not str or not text.strip() or len(text) > 2048:', 'if False:', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[words_type]')
    add('Slice16 G18 service entry words_empty', SERVICE, 'not text.strip()', 'False', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[words_empty]')
    add('Slice16 G18 service entry words_long', SERVICE, 'len(text) > 2048', 'False', 'tests/test_field_repair.py::test_service_readback_refuses_before_claim_or_extraction[words_long]')
    add('Slice16 G18 frontend capability version_type', LOCATOR, '!Number.isSafeInteger(value.disposition_version)', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[version_type]')
    add('Slice16 G18 frontend capability version_zero', LOCATOR, 'value.disposition_version < 1', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[version_zero]')
    add('Slice16 G18 frontend capability ref_type', LOCATOR, 'typeof ref !== "string"', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[ref_type]')
    add('Slice16 G18 frontend capability ref_format', LOCATOR, '!/^[A-Za-z0-9_-]{1,128}$/.test(ref)', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[ref_format]')
    add('Slice16 G18 frontend capability purpose_parts', LOCATOR, 'parts.length !== 5', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_parts]')
    add('Slice16 G18 frontend capability purpose_prefix', LOCATOR, 'parts[0] !== "disposition"', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_prefix]')
    add('Slice16 G18 frontend capability purpose_version', LOCATOR, 'parts[1] !== String(value.disposition_version)', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_version]')
    add('Slice16 G18 frontend capability purpose_role', LOCATOR, 'parts[2] !== "readback"', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_role]')
    add('Slice16 G18 frontend capability purpose_attempt', LOCATOR, '!/^[A-Za-z0-9_-]{1,128}$/.test(parts[3])', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_attempt]')
    add('Slice16 G18 frontend capability purpose_kind', LOCATOR, 'parts[4] !== value.kind', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[purpose_kind]')
    add('Slice16 G18 frontend capability start_attempt', LOCATOR, 'value.kind === "readback_started" && parts[3] !== "none"', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[start_attempt]')
    add('Slice16 G18 frontend capability missing_attempt', LOCATOR, 'parts[3] === "none"', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[missing_attempt]')
    add('Slice16 G18 frontend capability event_parent', LOCATOR, '(value.parent_restatement_id !== null || value.confirmation_id !== null)) return null;', '(false || value.confirmation_id !== null)) return null;', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[event_parent]')
    add('Slice16 G18 frontend capability event_confirmation', LOCATOR, '(value.parent_restatement_id !== null || value.confirmation_id !== null)) return null;', '(value.parent_restatement_id !== null || false)) return null;', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[event_confirmation]')
    add('Slice16 G18 frontend capability confirm_id', LOCATOR, 'value.kind === "confirm_words" && value.confirmation_id !== null', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[confirm_id]')
    add('Slice16 G18 frontend capability score_confirmation', LOCATOR, 'value.confirmation_id === null) return null;', 'false) return null;', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[score_confirmation]')
    add('Slice16 G18 frontend capability score_parent', LOCATOR, 'value.kind === "score_words" && value.parent_restatement_id !== null', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[score_parent]')
    add('Slice16 G18 frontend capability repair_parent', LOCATOR, 'value.kind === "repair_words" && value.parent_restatement_id === null', 'false', 'tests/test_field_repair.py::test_frontend_s16_capability_grammar_has_independent_controls[repair_parent]')
    add('Slice16 G22 final absolute h3', RULES, 'context.effective_hint is HintLevel.H3', 'False', 'tests/test_field_repair.py::test_final_context_fences_are_independent[h3]')
    add('Slice16 G22 final absolute cap', RULES, 'or context.completed_repairs >= MAX_REPAIR_ROUNDS', 'or False', 'tests/test_field_repair.py::test_final_context_fences_are_independent[cap]')
    add("Slice16 G18 store sticky expiry", STATE, 'or journey.flow.stopped or bundle.snapshot.expiry_event_id is not None', 'or journey.flow.stopped', "tests/test_field_repair.py::test_confirmation_store_refuses_at_its_first_boundary[sticky_expiry]")


def add_slice16_lifecycle_mutations(add):
    add("Slice16 G08 decoder accepts stopped histories", DECODER,
        '  if (["readback", "repair"].includes(value.step as string)) {', '  if (true) {',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[cap]")


def add_slice16_closed_copy_mutations(add):
    add("Slice16 G31 expired screen ends readback prompts", RULES,
        'if not stopped and closure.closure is ClosureState.OPEN:', 'if not stopped:',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[expired_uncertain]")
    add("Slice16 G22 stopped decoder needs no retry feedback", DECODER,
        '!flow.stopped && outcome.closure === "open" &&', 'outcome.closure === "open" &&',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[cap]")
    add("Slice16 G31 expired decoder needs no retry feedback", DECODER,
        '!flow.stopped && outcome.closure === "open" &&', '!flow.stopped &&',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[expired_uncertain]")


def add_slice16_pending_navigation_mutations(add):
    add("Slice16 G12 pending navigation before stop stays usable", RULES,
        'if extraction_pending and closure.closure is ClosureState.OPEN:', 'if False:',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[pending_h3]")
    add("Slice16 G12 stopped pending cannot supersede or H3 again", RULES,
        '("show_plan", "hide_plan") if stopped else ("show_plan", "hide_plan", "h3", "supersede_extraction")',
        '("show_plan", "hide_plan", "h3", "supersede_extraction")',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[pending_h3]")
    add("Slice16 G12 decoder accepts stopped pending navigation", DECODER,
        'flow.stopped && outcome.closure === "open" ? ["show_plan", "hide_plan"]',
        'false ? ["show_plan", "hide_plan"]',
        "tests/test_field_repair.py::test_producer_and_frontend_agree_on_each_new_lifecycle[pending_h3]")


def add_slice16_source_word_mutations(add):
    add("Slice16 G18 source word begins at a boundary", "src/carerelay/adp_extraction.py",
        'span.text[:1].isascii() and span.text[:1].isalnum() and span.start > 0', 'False',
        "tests/test_field_repair.py::test_injected_exact_subword_is_not_a_grounded_field[prefix]")
    add("Slice16 G18 source word ends at a boundary", "src/carerelay/adp_extraction.py",
        'span.text[-1:].isascii() and span.text[-1:].isalnum() and span.end < len(confirmed_text)', 'False',
        "tests/test_field_repair.py::test_injected_exact_subword_is_not_a_grounded_field[suffix]")


def add_slice16_full_width_question_mutation(add):
    add("Slice16 G20 full width question invalidates its field", RULES, r"|？|不|没|未", r"|不|没|未",
        "tests/test_field_repair.py::test_full_width_question_never_becomes_a_clean_timing_repair")

def add_decoder_mutations(add):
    clauses = {
        "root_keys": ('!exactKeys(value, ROOT_KEYS)', 'false'),
        "schema": ('value.schema_version !== "carerelay-journey-v1"', 'false'),
        "identity": ('value.episode_id !== expectedId', 'false'),
        "revision_negative": ('Number(value.revision) < 0', 'false'),
        "revision_unsafe": ('!Number.isSafeInteger(value.revision)', 'false'),
        "timestamp_format": ('!instant(value.as_of_utc)', 'false'),
        "timestamp_calendar": ('new Date(x).toISOString().slice(0, 19) === x.slice(0, 19)', 'true'),
        "clock": ('value.clock_mode !== "scenario" && value.clock_mode !== "system"', 'false'),
        "simulation": ('value.simulated !== true', 'false'),
        "label": ('value.fixture_label !== JOURNEY_LABEL', 'false'),
        "flow_keys": ('!exactKeys(value.flow, FLOW_KEYS)', 'false'),
        "stop_type": ('typeof flow.stopped !== "boolean"', 'false'),
        "visible_type": ('typeof flow.card_visible !== "boolean"', 'false'),
        "repair_integer": ('!Number.isInteger(flow.completed_repairs)', 'false'),
        "repair_negative": ('Number(flow.completed_repairs) < 0', 'false'),
        "repair_cap": ('Number(flow.completed_repairs) > 2', 'false'),
        "hint_enum": ('!["H0", "H1", "H2", "H3"].includes(flow.effective_hint as string)', 'false'),
        "interpretation_enum": ('!["idle", "pending", "scored", "unavailable", "uncertain"].includes(flow.interpretation as string)', 'false'),
        "repair_field_enum": ('flow.selected_repair_field !== null && !["action_id", "deadline_utc", "next_owner_id"].includes(flow.selected_repair_field as string)', 'false'),
        "execution_enum": ('!["not_started", "attempted", "acknowledged", "failed", "superseded", "expired"].includes(outcome.execution as string)', 'false'),
        "evidence_enum": ('!["none", "self_reported", "documented"].includes(outcome.evidence as string)', 'false'),
        "outcome_keys": ('!exactKeys(value.outcome, OUTCOME_KEYS)', 'false'),
        "execution_alias": ('value.execution !== outcome.execution', 'false'),
        "evidence_alias": ('value.evidence !== outcome.evidence', 'false'),
        "closure_alias": ('value.closure !== outcome.closure', 'false'),
        "care_alias": ('value.care_evidenced !== outcome.care_evidenced', 'false'),
        "stop_version": ('flow.stopped_disposition_version !== value.disposition_version', 'false'),
        "stop_reason": ('!bounded(flow.stop_reason, 128)', 'false'),
        "plan_version": ('value.disposition_version !== version', 'false'),
        "plan_policy": ('value.policy_version !== policy', 'false'),
        "plan_timezone": ('value.display_timezone !== "Asia/Singapore"', 'false'),
        "plan_deadline": ('!instant(value.deadline_utc)', 'false'),
        "plan_keys": ('!exactKeys(value, PLAN_KEYS)', 'false'),
        "owner_pair": ('(value.current_owner_id === null) !== (value.current_owner_display === null)', 'false'),
        "owner_alias": ('value.action_owner_id !== value.plan.current_owner_id', 'false'),
        "question_id": ('value.question.question_id !== value.step', 'false'),
        "question_extra": ('!exactKeys(value.question, ["question_id", "text", "choices"])', 'false'),
        "question_text": ('!bounded(value.question.text)', 'false'),
        "readback_choice": (': choiceIds.length !== 0) return null;', ': false) return null;'),
        "barrier_choices": ('choiceIds.length !== 3', 'false'),
        "missing_question": ('needsQuestion !== (value.question !== null)', 'false'),
        "redacted_owner": ('value.plan_redacted && (outcome.accepted_by !== null || outcome.escalation_path !== null)', 'false'),
        "readback_identity": ('["readback", "repair"].includes(value.step as string) && flow.readback_attempt_id === null', 'false'),
        "stopped_open": ('flow.stopped && outcome.closure === "open" && value.step !== "stopped"', 'false'),
        "h3_stop": ('flow.effective_hint === "H3" && flow.stopped !== true', 'false'),
        "sticky_expiry": ('outcome.expiry_recorded && value.step !== "expired" && value.step !== "documented"', 'false'),
        "open_owner": ('outcome.closure === "open" && value.plan && value.plan.current_owner_id !== value.plan.original_owner_id', 'false'),
        "text_keys": ('!exactKeys(value.text, selectedTextKeys)', 'false'),
        "text_labels": ('!exactKeys(value.text, selectedTextKeys)', 'false'),
        "unresolved_failure": ('value.step === "unresolved" && outcome.execution !== "failed" && outcome.escalation_outcome !== "failed"', 'false'),
    }
    for label, (old, new) in clauses.items():
        add("G06 assessed " + label, DECODER, old, new, C + f"test_decoder_independent_invariant[{label}]")
    for field in ["action_id", "action_text", "deadline_display", "original_owner_id", "original_owner_display", "fallback_route_id", "fallback_display"]:
        add("G06 plan bounded " + field, DECODER, 'if (!bounded(value[key])) return false;',
            f'if (key !== "{field}" && !bounded(value[key])) return false;', C + f"test_decoder_independent_invariant[plan_{field}]")
    for field in ["accepted_by", "accepted_scope", "escalation_path", "escalation_outcome"]:
        add("G06 outcome string " + field, DECODER, 'if (!nullableString(outcome[key])) return null;',
            f'if (key !== "{field}" && !nullableString(outcome[key])) return null;', C + f"test_decoder_independent_invariant[outcome_{field}]")
    for field in ["readback_attempt_id", "latest_restatement_id"]:
        add("G06 flow string " + field, DECODER, 'if (!nullableString(flow[key])) return null;',
            f'if (key !== "{field}" && !nullableString(flow[key])) return null;', C + f"test_decoder_independent_invariant[flow_{field}]")
    no_plan = {"plan":"plan", "outcome":"outcome", "revealed":"revealed_plan", "question":"question", "closure":"closure", "execution":"execution", "evidence":"evidence", "owner":"action_owner_id", "policy":"policy_version"}
    for label, field in no_plan.items():
        add("G06 no-plan null " + field, DECODER, 'if (value[key] !== null) return null;',
            f'if (key !== "{field}" && value[key] !== null) return null;', D + f"test_projection_invariants[{label}]")
    for label, field in {"reason":"stop_reason", "stop_version":"stopped_disposition_version", "attempt":"readback_attempt_id", "restatement":"latest_restatement_id", "repair_field":"selected_repair_field"}.items():
        add("G06 no-plan flow null " + field, DECODER, 'if (flow[key] !== null) return null;',
            f'if (key !== "{field}" && flow[key] !== null) return null;', D + f"test_projection_invariants[{label}]")
    add("G06 no-plan entry copy", DECODER, 'value.text[key] !== copy', 'key !== "heading" && value.text[key] !== copy', D + "test_projection_invariants[copy]")
    add("G06 no-plan card visibility", DECODER, 'flow.stopped !== false || flow.card_visible !== false', 'flow.stopped !== false || false', D + "test_projection_invariants[visible]")
    add("G06 no-plan stopped", DECODER, 'flow.stopped !== false || flow.card_visible !== false', 'false || flow.card_visible !== false', D + "test_projection_invariants[stopped]")
    add("G06 no-plan repair count", DECODER, 'flow.completed_repairs !== 0', 'false', D + "test_projection_invariants[repairs]")
    add("G06 no-plan hint", DECODER, 'flow.effective_hint !== "H1"', 'false', D + "test_projection_invariants[hint]")
    add("G06 no-plan interpretation", DECODER, 'flow.interpretation !== "idle" && flow.interpretation !== "pending"', 'false', D + "test_projection_invariants[interpretation]")
    add("G06 bounded response", DECODER, 'count > MAX_JOURNEY_BYTES', 'false', D + "test_decoder_good_and_bounded_transport")
    add("G06 lower revision", DECODER, 'next.revision < current.revision', 'false', F + "test_equal_command_cannot_reopen_known_stop_but_fresh_time_expiry_can_load")
    add("G06 equal revision changes", DECODER, 'JSON.stringify(previous) !== JSON.stringify(incoming)', 'false', F + "test_equal_command_cannot_reopen_known_stop_but_fresh_time_expiry_can_load")


def purge(path):
    for compiled in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
        compiled.unlink()


def env():
    return dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1",
        APP_DATABASE_URL=":memory:", APP_CLOCK="scenario", APP_ENV="local", CARERELAY_API_TOKEN="",
        CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled")


def run(selectors, directory, label, collect=False):
    xml = directory / f"{label}.xml"
    command = [sys.executable, "-m", "pytest", *selectors, "-o", "addopts=", "-q",
        f"--basetemp={directory / (label + '-pytest')}"]
    command += ["--collect-only"] if collect else [f"--junitxml={xml}"]
    child = subprocess.run(command, cwd=ROOT, env=env(), capture_output=True, text=True)
    output = child.stdout + child.stderr
    (directory / f"{label}.log").write_text(output)
    if collect:
        return {"green": child.returncode == 0 and "collected" in output, "red": False, "exit": child.returncode}
    cases = ET.parse(xml).findall(".//testcase") if xml.exists() else []
    failures = [failure for case in cases for failure in case.findall("failure")]
    invalid = any(case.find("error") is not None or case.find("skipped") is not None for case in cases)
    runtime = re.search(r"(?:SyntaxError|IndentationError|ImportError|ModuleNotFoundError|NameError|AttributeError|TypeError|KeyError|OperationalError):", output)
    def assertion(failure):
        text = failure.text or ""
        message = failure.attrib.get("message", "")
        return ("AssertionError" in text or message.startswith("assert ") or
            "DID NOT RAISE" in message or "DID NOT RAISE" in text or
            bool(TYPED_REFUSAL.search(text)))
    return {"green": child.returncode == 0 and bool(cases) and not failures and not invalid,
        "red": child.returncode == 1 and bool(failures) and not invalid and not runtime and all(map(assertion, failures)),
        "exit": child.returncode, "cases": len(cases), "failures": len(failures), "runtime_error": bool(runtime)}


def fingerprint(mutation, original):
    return hashlib.sha256(original + json.dumps(asdict(mutation), sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Mutate only with all source writers idle")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--anchors-only", action="store_true")
    parser.add_argument("--filter", default="")
    parser.add_argument("--only", action="append", default=[], help="Exact named cases, repeatable")
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    mutations = [m for m in build_mutations() if args.filter.casefold() in m.label.casefold() and (not args.only or m.label in args.only)]
    if not mutations:
        raise SystemExit("No matching mutations; no proof claimed")
    directory = args.resume or Path(tempfile.mkdtemp(prefix="carerelay-slice15-mutations-"))
    directory.mkdir(parents=True, exist_ok=True)
    print(f"Evidence: {directory}", flush=True)
    manifest = directory / "results.json"
    results = json.loads(manifest.read_text()) if manifest.exists() else {}
    controls = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted([*(ROOT / "tests").glob("*.py"), ROOT / "tests/journey_decoder_cases.json"])}
    control_manifest = directory / "control-sources.json"
    if control_manifest.exists() and json.loads(control_manifest.read_text()) != controls:
        raise SystemExit("Resume control source differs; select affected guards in a fresh directory")
    control_manifest.write_text(json.dumps(controls, indent=2))
    for name in controls:
        snapshot = directory / "control-source" / name
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes((ROOT / name).read_bytes())
    originals = {m.target: (ROOT / m.target).read_bytes() for m in mutations}
    for target, data in originals.items():
        backup = directory / "backup" / target
        backup.parent.mkdir(parents=True, exist_ok=True)
        if backup.exists() and backup.read_bytes() != data:
            raise SystemExit(f"Resume baseline differs: {target}; use a fresh evidence directory")
        backup.write_bytes(data)
        purge(ROOT / target)
    validation = []
    for mutation in mutations:
        count = originals[mutation.target].count(mutation.old.encode())
        validation.append(dict(label=mutation.label, target=mutation.target, selector=mutation.selector,
            anchor_count=count, fingerprint=fingerprint(mutation, originals[mutation.target])))
    (directory / "coverage.json").write_text(json.dumps(validation, indent=2))
    bad = [row for row in validation if row["anchor_count"] != 1]
    if bad:
        for row in bad:
            print(f"NOT PROVEN anchor {row['label']}: {row['anchor_count']} matches", flush=True)
        raise SystemExit(2)
    if args.anchors_only:
        print(f"{len(mutations)} unique anchors; no tests/mutations run", flush=True)
        return
    selectors = sorted({m.selector for m in mutations})
    selectors += [J + "test_reader_annotations_resolve_for_both_engines", F + "test_trusted_stored_screen_projections_decode[plan]",
        "tests/test_postgres_store.py::TestTheTwoSchemasAgree",
        "tests/test_postgres_stage2.py::TestTheTwoStoresShareOneSurface"]
    collected = run(selectors, directory, "collect", collect=True)
    if not collected["green"]:
        raise SystemExit("NOT PROVEN: pinned selector collection failed")
    control = run(selectors, directory, "all-before")
    if not control["green"]:
        raise SystemExit("NOT PROVEN: control batch failed; no mutations run")
    if args.validate_only or not args.run:
        print(f"VALIDATED {len(mutations)} anchors; {control['cases']} control cases GREEN; no mutations run", flush=True)
        return
    try:
        for number, mutation in enumerate(mutations, 1):
            baseline = originals[mutation.target]
            signature = fingerprint(mutation, baseline)
            previous = results.get(mutation.label, {})
            if previous.get("status") == "RED" and previous.get("fingerprint") == signature:
                print(f"RESUMED existing RED: {mutation.label}", flush=True)
                continue
            path = ROOT / mutation.target
            if path.read_bytes() != baseline:
                raise RuntimeError(f"Concurrent source change detected: {mutation.target}")
            prefix = hashlib.sha256(mutation.label.encode()).hexdigest()[:12]
            before = run([mutation.selector], directory, prefix + "-before")
            result = {"status": "NOT PROVEN", "fingerprint": signature, "before": before}
            if before["green"]:
                try:
                    path.write_bytes(baseline.replace(mutation.old.encode(), mutation.new.encode()))
                    purge(path)
                    result["mutant"] = run([mutation.selector], directory, prefix + "-mutant")
                finally:
                    path.write_bytes(baseline)
                    purge(path)
                result["restored_exact"] = path.read_bytes() == baseline
                result["after"] = run([mutation.selector], directory, prefix + "-after")
                if result["restored_exact"] and result["after"]["green"]:
                    result["status"] = "RED" if result["mutant"]["red"] else "SURVIVED" if result["mutant"]["green"] else "NOT PROVEN"
            results[mutation.label] = result
            manifest.write_text(json.dumps(results, indent=2))
            print(f"{result['status']} {number}/{len(mutations)}: {mutation.label}", flush=True)
    finally:
        for target, data in originals.items():
            # Even untracked targets have their exact pre-run bytes outside the repo.
            (ROOT / target).write_bytes(data)
            purge(ROOT / target)
    restored = all((ROOT / target).read_bytes() == data for target, data in originals.items())
    counts = {status: sum(results.get(m.label, {}).get("status") == status for m in mutations)
        for status in ["RED", "SURVIVED", "NOT PROVEN"]}
    print(json.dumps(dict(counts=counts, all_targets_restored_exact=restored)), flush=True)
    print("Browser/SSR/RSC execution and actual Postgres engine proof are separate; G38 remains the independent truthfulness harness.", flush=True)
    if not restored or counts["SURVIVED"] or counts["NOT PROVEN"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
