"""Slice 16 offline/field-repair controls. No live ADP."""
from dataclasses import replace
import importlib.util

import pytest

from carerelay.demo import fixture
from carerelay.domain import models, rules


def offline(text):
    assert importlib.util.find_spec("carerelay.adp_extraction") is not None, "offline port is missing"
    from carerelay.adp_extraction import ExtractionInput, OfflineReadbackExtractor
    p = fixture.policy()
    request = ExtractionInput(text, frozenset(p.action_aliases) | p.permitted_action_ids,
        frozenset(p.deadline_forms), frozenset(p.owner_aliases) | p.permitted_owner_ids,
        "fictional-correlation", "offline-fixture-v1", "carerelay-readback-v1")
    return OfflineReadbackExtractor().extract(request, budget_seconds=5.0)


def test_offline_exact_source_offsets():
    result = offline("🙂 Go to the clinic; today before six; myself.")
    assert (result.mode, result.validation) == ("local-sim", "valid")
    raw = result.raw
    assert raw is not None
    assert raw.action_span is not None
    assert raw.deadline_span is not None
    assert raw.next_owner_span is not None
    assert (raw.action_span.text, raw.action_span.start, raw.action_span.end) == ("Go to the clinic", 2, 18)
    assert (raw.deadline_span.text, raw.deadline_span.start, raw.deadline_span.end) == ("today before six", 20, 36)
    assert (raw.next_owner_span.text, raw.next_owner_span.start, raw.next_owner_span.end) == ("myself", 38, 44)
    assert raw.uncertain_fields == frozenset()
    assert result.trace_id is None and result.model_version is None


def test_offline_preserves_whitespace_and_chinese_offsets():
    raw = offline("Go\tto the clinic; 我自己 今天六点前").raw
    assert (raw.action_span.text, raw.action_span.start, raw.action_span.end) == ("Go\tto the clinic", 0, 16)
    assert (raw.next_owner_span.text, raw.next_owner_span.start, raw.next_owner_span.end) == ("我自己", 18, 21)
    assert (raw.deadline_span.text, raw.deadline_span.start, raw.deadline_span.end) == ("今天六点前", 22, 27)


def test_offline_bare_tomorrow_does_not_invent_a_time():
    raw = offline("tomorrow").raw
    assert raw.deadline_span is None
    assert raw.uncertain_fields == frozenset({"action_id", "deadline_utc", "next_owner_id"})
    assert rules.compare_plan(fixture.disposition("fictional", fixture.SCENARIO_NOW_UTC),
        models.ExtractedPlan(deadline_span="tomorrow"), policy=fixture.policy(),
        now_utc=fixture.SCENARIO_NOW_UTC, display_tz=fixture.DISPLAY_TZ).uncertain == frozenset(models.COMPARISON_FIELDS)


@pytest.mark.parametrize("text,want", [
    ("today before six. Actually I won't.", {"action_id", "deadline_utc", "next_owner_id"}),
    ("today before six if I can", {"deadline_utc"}),
    ("maybe today before six", {"deadline_utc"}),
    ("today before six?", {"deadline_utc"}),
    ("today before six or tomorrow before 6pm", {"deadline_utc"}),
    ("today before six; tomorrow before 6pm", {"deadline_utc"}),
    ("go to the clinic; wait_and_monitor", {"action_id"}),
    ("myself; caregiver", {"next_owner_id"}),
    ("today before six. Actually, forget that.", {"action_id", "deadline_utc", "next_owner_id"}),
    ("today before six. My neighbour will go.", {"next_owner_id"}),
    ("today before six; myself and my neighbour will go.", {"next_owner_id"}),
    ("today before six. Stay home.", {"action_id"}),
    ("go to the clinic myself. Tomorrow.", {"deadline_utc"}),
    ("today before six. I like tea.", set()),
    ("today before six. Maybe it will rain.", set()),
    ("go to the clinic today before six myself", set()),
])
def test_whole_answer_doubt_is_independent(text, want):
    check = getattr(rules, "independent_uncertainty", None)
    assert callable(check), "whole-answer checker is missing"
    assert check(text, policy=fixture.policy()) == frozenset(want)


def context(*, owner_known=True):
    assert hasattr(models, "ReadbackContext"), "field repair context is missing"
    retained = [models.RetainedMatch("action_id", "attend_same_day_review", "parent-0",
        "confirmation-0", models.SourceSpan("go to the clinic", 0, 16))]
    if owner_known:
        retained.append(models.RetainedMatch("next_owner_id", "patient", "parent-0",
            "confirmation-0", models.SourceSpan("myself", 37, 43)))
    return models.ReadbackContext("fictional", 1, fixture.POLICY_VERSION, "attempt-0",
        "parent-0", "confirmation-1", "today before six", "deadline_utc", 0,
        tuple(retained), models.HintLevel.H2, 9)


def merged(ctx, text):
    result = offline(text)
    spans = result.raw
    extracted = models.ExtractedPlan(
        spans.action_span.text if spans.action_span else None,
        spans.deadline_span.text if spans.deadline_span else None,
        spans.next_owner_span.text if spans.next_owner_span else None,
        spans.uncertain_fields)
    return rules.merge_field_repair(replace(ctx, confirmed_text=text), extracted,
        whole_answer_doubt=rules.independent_uncertainty(text, policy=fixture.policy()),
        policy=fixture.policy(), now_utc=fixture.SCENARIO_NOW_UTC, display_tz=fixture.DISPLAY_TZ)


def comparison(extracted):
    return rules.compare_plan(fixture.disposition("fictional", fixture.SCENARIO_NOW_UTC),
        extracted, policy=fixture.policy(), now_utc=fixture.SCENARIO_NOW_UTC, display_tz=fixture.DISPLAY_TZ)


def test_timing_only_retains_grounded_action_owner():
    extracted, retained = merged(context(), "today before six")
    assert comparison(extracted).matched == frozenset(models.COMPARISON_FIELDS)
    assert [(r.field, r.source_restatement_id, r.source_confirmation_id) for r in retained] == [
        ("action_id", "parent-0", "confirmation-0"), ("next_owner_id", "parent-0", "confirmation-0")]


def test_uncertain_owner_is_never_filled_from_expected():
    extracted, retained = merged(context(owner_known=False), "today before six")
    assert comparison(extracted).matched == frozenset({"action_id", "deadline_utc"})
    assert comparison(extracted).uncertain == frozenset({"next_owner_id"})
    assert [r.field for r in retained] == ["action_id"]


@pytest.mark.parametrize("text,field", [
    ("today before six; caregiver", "next_owner_id"),
    ("today before six; wait_and_monitor", "action_id"),
])
def test_explicit_other_field_replaces_retention(text, field):
    extracted, retained = merged(context(), text)
    assert comparison(extracted).mismatched == frozenset({field})
    assert field not in {r.field for r in retained}


def test_backward_correction_invalidates_all_retention():
    extracted, retained = merged(context(), "today before six. Actually I won't.")
    assert comparison(extracted).uncertain == frozenset(models.COMPARISON_FIELDS)
    assert retained == ()


def test_unrelated_aside_keeps_the_positive_control():
    extracted, retained = merged(context(), "today before six. I like tea.")
    assert comparison(extracted).is_clean()
    assert len(retained) == 2


def test_selected_field_is_not_retained_when_answer_is_missing():
    ctx = context()
    previous_time = models.RetainedMatch("deadline_utc", fixture.deadline_utc(fixture.SCENARIO_NOW_UTC),
        "parent-0", "confirmation-0", models.SourceSpan("today before six", 18, 34))
    extracted, retained = merged(replace(ctx, retained=ctx.retained + (previous_time,)), "unknown")
    assert extracted.deadline_span is None
    assert "deadline_utc" in comparison(extracted).uncertain
    assert "deadline_utc" not in {r.field for r in retained}


def test_bad_grounded_retention_refuses():
    ctx = context()
    forged = replace(ctx.retained[0], canonical_value="wait_and_monitor")
    with pytest.raises(rules.DomainError):
        merged(replace(ctx, retained=(forged,)), "today before six")


def test_full_answer_correction_does_not_borrow_missing_fields():
    extracted, retained = merged(replace(context(), repair_field=None), "today before six")
    assert comparison(extracted).uncertain == frozenset({"action_id", "next_owner_id"})
    assert retained == ()


@pytest.mark.parametrize("case", ["policy", "field", "row", "confirmation", "unknown_value"])
def test_retention_requires_its_policy_and_grounded_identity(case):
    ctx = context()
    if case == "policy":
        ctx = replace(ctx, policy_version="different-policy")
    else:
        source = ctx.retained[0]
        source = replace(source, **{
            "field": {"field": "not-a-field", "canonical_value": fixture.deadline_utc(fixture.SCENARIO_NOW_UTC),
                      "source_span": models.SourceSpan("today before six", 0, 16)},
            "row": {"source_restatement_id": ""},
            "confirmation": {"source_confirmation_id": ""},
            "unknown_value": {"canonical_value": None, "source_span": models.SourceSpan("unknown", 0, 7)},
        }[case])
        ctx = replace(ctx, retained=(source,))
    with pytest.raises(rules.DomainError):
        merged(ctx, "today before six")


def test_owner_retention_must_resolve_its_grounded_value():
    ctx = context()
    forged = replace(ctx.retained[1], canonical_value="caregiver")
    with pytest.raises(rules.DomainError):
        merged(replace(ctx, retained=(forged,)), "today before six")


def test_deadline_retention_uses_its_grounded_value():
    deadline = models.RetainedMatch("deadline_utc", fixture.deadline_utc(fixture.SCENARIO_NOW_UTC),
        "parent-0", "confirmation-0", models.SourceSpan("today before six", 18, 34))
    ctx = replace(context(), repair_field="action_id", retained=(deadline,))
    extracted, retained = merged(ctx, "go to the clinic")
    assert comparison(extracted).matched == frozenset({"action_id", "deadline_utc"})
    assert retained == (deadline,)


@pytest.mark.parametrize("text,field", [
    ("today before six. My neighbour will go.", "next_owner_id"),
    ("today before six. Stay home.", "action_id"),
])
def test_unsupported_other_field_invalidates_retention(text, field):
    extracted, retained = merged(context(), text)
    assert field in comparison(extracted).uncertain
    assert field not in {r.field for r in retained}


@pytest.mark.parametrize("text", ["theme", "myselfish"])
def test_offline_owner_forms_have_word_boundaries(text):
    raw = offline(text + "; today before six").raw
    assert raw.next_owner_span is None
    assert "next_owner_id" in raw.uncertain_fields


def test_source_candidates_prefers_a_complete_overlapping_form():
    assert rules.source_candidates("go to the clinic", frozenset({"go to the clinic", "clinic"})) == (
        models.SourceSpan("go to the clinic", 0, 16),)


def test_empty_form_is_not_a_source_span():
    assert rules.source_candidates("fictional", frozenset({""})) == ()


@pytest.mark.parametrize("word", ["not", "no", "never", "cannot", "unsure", "uncertain",
    "maybe", "perhaps", "might", "may", "could", "would", "if", "or", "won't", "不", "没", "未"],
    ids=["not", "no", "never", "cannot", "unsure", "uncertain", "maybe", "perhaps", "might", "may",
         "could", "would", "if", "or", "contraction", "han_not", "han_no", "han_not_yet"])
def test_each_doubt_form_prevents_recall(word):
    text = f"{word} today before six"
    want = {"action_id", "deadline_utc", "next_owner_id"} if word == "won't" else {"deadline_utc"}
    assert rules.independent_uncertainty(text, policy=fixture.policy()) == frozenset(want)


def test_deadline_retention_refuses_a_different_source_value():
    ctx = context()
    source = models.RetainedMatch("deadline_utc", fixture.deadline_utc(fixture.SCENARIO_NOW_UTC),
        "parent-0", "confirmation-0", models.SourceSpan("tomorrow before 6pm", 0, 19))
    with pytest.raises(rules.DomainError):
        merged(replace(ctx, retained=(source,), repair_field="action_id"), "go to the clinic")


# New journey use cases are tested through real storage, separately from legacy
# operator probes. The extractor records input, but the assertions inspect rows,
# receipts and patient state produced by the actual service.
from carerelay.domain.models import OperationBinding
from carerelay.journey_commands import request_digest, verify_operation
from _legacy_service_probes import KEY
from test_truthfulness import make_service


def start_readback(service, episode="fictional-s16"):
    assert callable(getattr(service, "record_journey_event", None)), "journey event use case is missing"
    binding = OperationBinding("create-" + episode, episode, None, 0, "create", "episode:create",
        request_digest("create", {}), None, None)
    service.start_example(binding)
    token = next(o.operation_token for o in service.project_journey(episode).commands if o.kind == "select_example")
    service.select_example(verify_operation(token, signing_key=KEY), example_id="scripted-appointment")
    token = next(o.operation_token for o in service.project_journey(episode).commands if o.kind == "readback_started")
    result = service.record_journey_event(verify_operation(token, signing_key=KEY))
    assert result.journey.step == "readback"
    assert result.journey.plan is result.journey.revealed_plan is None
    return episode


def confirm(service, episode, text):
    journey = service.project_journey(episode)
    parent = journey.flow.latest_restatement_id
    token = service.prepare_command(episode, kind="confirm_words",
        body_sha256=request_digest("confirm_words", {"text": text, "parent_id": parent}), parent_id=parent)
    binding = verify_operation(token, signing_key=KEY)
    return service.confirm_words(binding, text=text)


def score(service, episode):
    journey = service.project_journey(episode)
    offer = next(o for o in journey.commands if o.kind in {"score_words", "repair_words"})
    binding = verify_operation(offer.operation_token, signing_key=KEY)
    return binding, service.score_confirmed(binding)


def test_confirmed_round_zero_and_grounded_timing_repair(tmp_path):
    service = make_service(tmp_path / "flow.sqlite")
    try:
        ep = start_readback(service)
        before = service._store.list_events(ep)
        parent = service.project_journey(ep).flow.latest_restatement_id
        service.prepare_command(ep, kind="confirm_words",
            body_sha256=request_digest("confirm_words", {"text": "go to the clinic tomorrow before 6pm myself", "parent_id": parent}), parent_id=parent)
        assert service._store.list_events(ep) == before
        saved = confirm(service, ep, "go to the clinic tomorrow before 6pm myself")
        assert saved.receipt.result_ref and not saved.receipt.scored
        _, initial = score(service, ep)
        assert initial.receipt.scored and initial.journey.step == "repair"
        assert initial.journey.flow.completed_repairs == 0
        assert initial.journey.flow.effective_hint is models.HintLevel.H2
        assert initial.journey.plan is initial.journey.revealed_plan is None
        confirm(service, ep, "today before six")
        _, repaired = score(service, ep)
        assert repaired.journey.step == "barrier"
        assert repaired.journey.flow.completed_repairs == 1
        row = service._store.list_restatements(ep)[-1]
        assert row.transcript_confirmed and row.comparison.is_clean()
        assert row.outcome is models.RecallOutcome.RECALL_CUED
        assert row.provenance["retained"][0]["source_confirmation_id"] == saved.receipt.result_ref
        assert repaired.journey.plan.deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
        # Slice 17 offers the booking barrier only; permission/request follow separately.
        assert [o.kind for o in repaired.journey.commands] == ["select_barrier", "show_plan", "hide_plan"]
    finally:
        service._store.close()


def test_two_uncertain_repairs_stop_without_round_zero_reset(tmp_path):
    service = make_service(tmp_path / "cap.sqlite")
    try:
        ep = start_readback(service)
        for round_no in (0, 1, 2):
            confirm(service, ep, "unknown")
            _, result = score(service, ep)
            assert result.journey.flow.completed_repairs == round_no
        assert result.journey.flow.stopped and result.journey.step == "stopped"
        assert "feedback" not in result.journey.text
        assert len(service._store.list_restatements(ep)) == 3
        assert not any(o.kind in {"readback_started", "confirm_words", "score_words", "repair_words"} for o in result.journey.commands)
        assert result.journey.plan.current_owner_id == "patient"
    finally:
        service._store.close()


def event(service, episode, kind):
    offer = next(o for o in service.project_journey(episode).commands if o.kind == kind)
    return service.record_journey_event(verify_operation(offer.operation_token, signing_key=KEY))


def test_reveal_hide_reload_keeps_highest_cue(tmp_path):
    path = tmp_path / "cue.sqlite"
    service = make_service(path)
    try:
        ep = start_readback(service)
        shown = event(service, ep, "show_plan")
        assert shown.journey.revealed_plan is not None
        assert shown.journey.flow.effective_hint is models.HintLevel.H2
        hidden = event(service, ep, "hide_plan")
        assert hidden.journey.revealed_plan is None
        assert hidden.journey.flow.effective_hint is models.HintLevel.H2
        assert [(h.level.value, h.kind.value) for h in service._store.list_hint_events(ep)] == [
            ("H2", "shown"), ("H2", "patient_hid")]
        confirm(service, ep, "go to the clinic today before six myself")
        _, scored = score(service, ep)
        assert scored.journey.step == "barrier"
    finally:
        service._store.close()
    service = make_service(path)
    try:
        assert service.project_journey(ep).flow.effective_hint is models.HintLevel.H2
        assert service._store.list_restatements(ep)[-1].outcome is models.RecallOutcome.RECALL_CUED
    finally:
        service._store.close()


def test_h3_stops_without_extraction_or_round(tmp_path):
    service = make_service(tmp_path / "h3.sqlite")
    try:
        ep = start_readback(service)
        stopped = event(service, ep, "h3")
        assert stopped.journey.flow.stopped and stopped.journey.step == "stopped"
        assert stopped.journey.flow.effective_hint is models.HintLevel.H3
        assert service._store.list_restatements(ep) == ()
        assert stopped.journey.plan.current_owner_id == "patient"
    finally:
        service._store.close()


from concurrent.futures import ThreadPoolExecutor
from threading import Event
from carerelay.adp_extraction import OfflineReadbackExtractor


class PausedExtractor:
    def __init__(self):
        self.entered, self.release = Event(), Event()
        self.inputs = []

    def extract(self, request, *, budget_seconds):
        self.inputs.append(request)
        self.entered.set()
        assert self.release.wait(5), "test did not release the extractor"
        return OfflineReadbackExtractor().extract(request, budget_seconds=budget_seconds)


def test_pending_duplicate_calls_one_extractor_and_supersede_fences_late_output(tmp_path, monkeypatch):
    service = make_service(tmp_path / "pending.sqlite")
    paused = PausedExtractor()
    service._readback_extractor = paused
    try:
        ep = start_readback(service)
        confirm(service, ep, "go to the clinic today before six myself")
        offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(offer.operation_token, signing_key=KEY)
        with ThreadPoolExecutor(1) as worker:
            pending = worker.submit(service.score_confirmed, binding)
            assert paused.entered.wait(2)
            try:
                duplicate = service.score_confirmed(binding)
                assert duplicate.receipt.state == "pending" and not duplicate.receipt.scored
                assert duplicate.receipt.replayed
                assert not any(o.kind in {"score_words", "repair_words", "request"} for o in duplicate.journey.commands)
                assert len(paused.inputs) == 1
                supersede = next(o for o in duplicate.journey.commands if o.kind == "supersede_extraction")
                replacement = service.supersede_extraction(verify_operation(supersede.operation_token, signing_key=KEY),
                    old_operation_id=binding.operation_id)
                assert replacement.receipt.state == "applied"
                assert any(o.kind == "score_words" for o in replacement.journey.commands)
                # Superseded output must stop before a second context evaluation.
                # A revision fence deeper in that evaluation is not this control.
                def no_late_evaluation(*args, **kwargs):
                    raise AssertionError("terminal extraction was evaluated again")
                monkeypatch.setattr(rules, "readback_context_current", no_late_evaluation)
            finally:
                paused.release.set()
            late = pending.result(2)
            assert late.receipt.state == "superseded" and not late.receipt.scored
        assert service._store.list_restatements(ep) == ()
        assert len(paused.inputs) == 1
    finally:
        paused.release.set()
        service._store.close()


def test_authenticated_confirmed_scoring_over_real_routes(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from carerelay.api import app, get_service
    service = make_service(tmp_path / "http.sqlite")
    monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-s16-http-only")
    monkeypatch.setenv("APP_ENV", "production")
    app.dependency_overrides[get_service] = lambda: service
    try:
        ep = start_readback(service)
        base = "/api/episodes/" + ep
        with TestClient(app, headers={"Authorization": "Bearer synthetic-s16-http-only"}) as client:
            words = "go to the clinic tomorrow before 6pm myself"
            response = client.get(base, params={"prepare_kind": "confirm_words",
                "body_sha256": request_digest("confirm_words", {"text": words, "parent_id": None})})
            assert response.status_code == 200
            saved = client.post(base + "/transcript-confirmations", json={"operation_token": response.json()["operation_token"], "text": words})
            assert saved.status_code == 200, saved.text
            score_offer = next(o for o in saved.json()["journey"]["commands"] if o["kind"] == "score_words")
            scored = client.post(base + "/restatements", json={"operation_token": score_offer["operation_token"]})
            assert scored.status_code == 200, scored.text
            assert scored.json()["receipt"]["scored"] is True
            assert scored.json()["journey"]["step"] == "repair"
            assert scored.json()["journey"]["flow"]["effective_hint"] == "H2"
            assert client.post(base + "/restatements", json={"text": words, "hint_level": "H0"}).status_code == 422
            replay = client.post(base + "/restatements", json={"operation_token": score_offer["operation_token"]})
            assert replay.status_code == 200 and replay.json()["receipt"]["replayed"]
            assert len(service._store.list_restatements(ep)) == 1
    finally:
        app.dependency_overrides.clear()
        service._store.close()


def test_same_body_preparation_recovers_the_confirmed_operation(tmp_path):
    service = make_service(tmp_path / "lost-confirm.sqlite")
    try:
        ep = start_readback(service)
        text = "go to the clinic today before six myself"
        digest = request_digest("confirm_words", {"text": text, "parent_id": None})
        first_token = service.prepare_command(ep, kind="confirm_words", body_sha256=digest, parent_id=None)
        first = service.confirm_words(verify_operation(first_token, signing_key=KEY), text=text)
        recovered_token = service.prepare_command(ep, kind="confirm_words", body_sha256=digest, parent_id=None)
        assert recovered_token == first_token
        recovered = service.confirm_words(verify_operation(recovered_token, signing_key=KEY), text=text)
        assert recovered.receipt.replayed and recovered.receipt.result_ref == first.receipt.result_ref
        assert len([k for k, _, _ in service._store.list_events(ep) if k == "words_confirmed"]) == 1
    finally:
        service._store.close()


def test_unavailable_repair_preserves_words_parent_and_round(tmp_path):
    from carerelay.adp_extraction import ExtractionResult
    class TimeoutExtractor:
        def extract(self, request, *, budget_seconds):
            return ExtractionResult("local-sim", "timeout", None, request.correlation_id, None,
                "offline-fixture-v1", "carerelay-readback-v1", None, "timeout")
    service = make_service(tmp_path / "unavailable.sqlite")
    try:
        ep = start_readback(service)
        confirm(service, ep, "unknown")
        _, initial = score(service, ep)
        parent = initial.receipt.result_ref
        confirm(service, ep, "today before six")
        service._readback_extractor = TimeoutExtractor()
        _, unavailable = score(service, ep)
        assert unavailable.receipt.state == "unavailable" and not unavailable.receipt.scored
        assert unavailable.journey.flow.latest_restatement_id == parent
        assert unavailable.journey.flow.completed_repairs == 0 and not unavailable.journey.flow.stopped
        assert unavailable.journey.text["feedback"] == "We could not check that answer just now. Your plan has not changed."
        assert unavailable.journey.text["saved_words"] == "today before six"
        assert len(service._store.list_restatements(ep)) == 1
    finally:
        service._store.close()


def test_ledger_names_offline_provenance_and_keeps_legacy_unknown(tmp_path):
    service = make_service(tmp_path / "provenance.sqlite")
    try:
        ep = start_readback(service)
        confirm(service, ep, "go to the clinic tomorrow before 6pm myself")
        score(service, ep)
        confirm(service, ep, "today before six")
        score(service, ep)
        ledger = service.project_ledger(ep).as_dict()
        assert isinstance(ledger["restatements"][0].get("extraction_provenance"), dict)
        assert ledger["restatements"][0]["extraction_provenance"]["mode"] == "local-sim"
        assert ledger["restatements"][1]["extraction_provenance"]["retained"][0]["source_restatement_id"] == ledger["restatements"][0]["restatement_id"]
        legacy = "fictional-legacy"
        service.ensure_episode(legacy, "fictional")
        service.intake(legacy, fixture.BOUND_COMPLAINT)
        service.submit_restatement(legacy, "go to the clinic today before six myself", models.HintLevel.H1)
        assert service.project_ledger(legacy).as_dict()["restatements"][0]["extraction_provenance"] is None
    finally:
        service._store.close()


def test_schema_error_does_not_echo_words_or_details(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from carerelay.api import app, get_service
    service = make_service(tmp_path / "error.sqlite")
    monkeypatch.setenv("CARERELAY_API_TOKEN", "synthetic-s16-errors-only")
    app.dependency_overrides[get_service] = lambda: service
    try:
        ep = start_readback(service)
        with TestClient(app, headers={"Authorization": "Bearer synthetic-s16-errors-only"}) as client:
            result = client.post("/api/episodes/" + ep + "/transcript-confirmations",
                json={"operation_token": "invalid", "text": "fictional words", "extra": "planted-synthetic-private-detail"})
            assert result.status_code == 422
            assert "planted-synthetic-private-detail" not in result.text
            assert "fictional words" not in result.text
        assert service._store.list_restatements(ep) == ()
    finally:
        app.dependency_overrides.clear()
        service._store.close()


def test_store_will_not_score_without_an_owned_scoring_claim(tmp_path):
    from carerelay.journey_commands import CommandConflict
    service = make_service(tmp_path / "owned.sqlite")
    try:
        ep = start_readback(service)
        saved = confirm(service, ep, "go to the clinic today before six myself")
        with service._store.journey_transaction(ep, write=True) as tx:
            bundle = tx.load_bundle(ep)
            ctx = models.ReadbackContext(ep, 1, fixture.POLICY_VERSION, saved.journey.flow.readback_attempt_id,
                None, saved.receipt.result_ref, "go to the clinic today before six myself", None, 0, (), models.HintLevel.H1, bundle.revision)
            extracted = models.ExtractedPlan("go to the clinic", "today before six", "myself")
            compared = comparison(extracted)
            with pytest.raises(CommandConflict):
                tx.append_scored_round(ctx, extracted, compared, now_utc=fixture.SCENARIO_NOW_UTC, provenance={})
        assert service._store.list_restatements(ep) == ()
    finally:
        service._store.close()


@pytest.mark.parametrize("payload", ["{bad-json", "[]", '{"schema":"unknown"}'])
def test_corrupt_new_confirmation_is_recovery_without_detail(tmp_path, payload):
    from fastapi.testclient import TestClient
    from carerelay.api import app, get_service
    service = make_service(tmp_path / "bad-confirm.sqlite")
    app.dependency_overrides[get_service] = lambda: service
    try:
        ep = start_readback(service)
        with service._store.journey_transaction(ep, write=True) as tx:
            tx.execute("INSERT INTO events(episode_id,kind,payload,recorded_at) VALUES (?,?,?,?)",
                (ep, "words_confirmed", payload, fixture.SCENARIO_NOW_UTC.isoformat()))
        with TestClient(app, raise_server_exceptions=False) as client:
            result = client.get("/api/episodes/" + ep)
            assert result.status_code == 503
            assert result.json() == {"detail": "journey unavailable"}
        assert service._store.list_restatements(ep) == ()
    finally:
        app.dependency_overrides.clear()
        service._store.close()


@pytest.mark.parametrize("change", ["cue", "stop", "expiry", "revision"])
def test_late_extraction_never_applies_after_changed_context(tmp_path, change):
    from datetime import timedelta
    from carerelay.service import ScenarioClock
    service = make_service(tmp_path / "late.sqlite")
    paused = PausedExtractor()
    service._readback_extractor = paused
    try:
        ep = start_readback(service)
        confirm(service, ep, "go to the clinic today before six myself")
        offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(offer.operation_token, signing_key=KEY)
        with ThreadPoolExecutor(1) as worker:
            result = worker.submit(service.score_confirmed, binding)
            assert paused.entered.wait(2)
            try:
                if change == "cue": event(service, ep, "show_plan")
                elif change == "stop": service._store.record_flow_stop(ep, 1, "fixture-stop", "nurse_line", now_utc=fixture.SCENARIO_NOW_UTC)
                elif change == "expiry": service._clock = ScenarioClock(fixture.SCENARIO_NOW_UTC + timedelta(hours=10))
                else:
                    with service._store.journey_transaction(ep, write=True) as tx:
                        tx._event("fixture-audit", {}, fixture.SCENARIO_NOW_UTC)
            finally:
                paused.release.set()
            refused = result.result(2)
        assert refused.receipt.state == "refused" and not refused.receipt.scored
        assert service._store.list_restatements(ep) == ()
        assert len(paused.inputs) == 1
        assert service._store.load_snapshot(ep).disposition.clinical_deadline_utc.isoformat() == "2026-09-30T10:00:00+00:00"
        assert not refused.journey.outcome.care_evidenced
    finally:
        paused.release.set()
        service._store.close()


def test_exact_confirmed_words_and_latest_parent_are_not_substitutable(tmp_path):
    from carerelay.journey_commands import CommandConflict, CommandInvalid
    service = make_service(tmp_path / "exact.sqlite")
    try:
        ep = start_readback(service)
        text = "go to the clinic tomorrow before 6pm myself"
        token = service.prepare_command(ep, kind="confirm_words", body_sha256=request_digest("confirm_words", {"text": text, "parent_id": None}), parent_id=None)
        binding = verify_operation(token, signing_key=KEY)
        with pytest.raises(CommandConflict, match="confirmed words changed"):
            service.confirm_words(binding, text=text + " ")
        assert service._store.list_restatements(ep) == ()
        service.confirm_words(binding, text=text)
        old_score, first = score(service, ep)
        first_parent = first.receipt.result_ref
        confirm(service, ep, "unknown")
        _, second = score(service, ep)
        assert first_parent != second.receipt.result_ref
        with pytest.raises(CommandInvalid):
            service.prepare_command(ep, kind="confirm_words", body_sha256=request_digest("confirm_words", {"text": "today before six", "parent_id": first_parent}), parent_id=first_parent)
        replay = service.score_confirmed(old_score)
        assert replay.receipt.replayed and replay.journey.flow.latest_restatement_id == second.receipt.result_ref
        assert len(service._store.list_restatements(ep)) == 2
    finally:
        service._store.close()


def test_legacy_digest_confirmation_does_not_grant_scoring(tmp_path):
    from carerelay.journey_commands import CommandConflict
    service = make_service(tmp_path / "legacy-confirm.sqlite")
    try:
        ep = start_readback(service)
        legacy = service.confirm_transcript(ep, "go to the clinic today before six myself")
        journey = service.project_journey(ep)
        forged = models.OperationBinding("forged-legacy", ep, 1, journey.revision, "score_words",
            service._readback_purpose(journey, "score_words"), request_digest("score_words", {"confirmation_id": legacy}), None, legacy)
        with pytest.raises(CommandConflict): service.score_confirmed(forged)
        assert service._store.list_restatements(ep) == ()
        assert not any(o.kind == "score_words" for o in journey.commands)
    finally:
        service._store.close()


def test_identical_words_in_different_rounds_have_distinct_confirmations(tmp_path):
    service = make_service(tmp_path / "round-identities.sqlite")
    try:
        ep = start_readback(service)
        ids = []
        for round_no in (0, 1, 2):
            ids.append(confirm(service, ep, "unknown").receipt.result_ref)
            score(service, ep)
        assert len(set(ids)) == 3
        assert len(service._store.list_restatements(ep)) == 3
    finally:
        service._store.close()


def test_real_pending_projection_decodes_without_scoring_offer(tmp_path):
    import json, subprocess
    from pathlib import Path
    from carerelay.presentation import command_surface
    service = make_service(tmp_path / "pending-decode.sqlite")
    paused = PausedExtractor()
    service._readback_extractor = paused
    try:
        ep = start_readback(service)
        confirm(service, ep, "go to the clinic today before six myself")
        offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(offer.operation_token, signing_key=KEY)
        with ThreadPoolExecutor(1) as worker:
            future = worker.submit(service.score_confirmed, binding)
            assert paused.entered.wait(2)
            try:
                pending = command_surface(service.score_confirmed(binding))
                script = '''import {readFileSync} from "node:fs";import {readCommand} from "./frontend/lib/journey.ts";
const data=JSON.parse(readFileSync(0,"utf8"));const r=await readCommand(new Response(JSON.stringify(data),{status:202}),data.journey.episode_id,"score_words");
console.log(JSON.stringify(r!==null));'''
                result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=Path(__file__).resolve().parents[1],
                    input=json.dumps(pending), capture_output=True, text=True)
                assert result.returncode == 0, result.stderr
                assert json.loads(result.stdout) is True
            finally:
                paused.release.set()
            future.result(2)
    finally:
        paused.release.set()
        service._store.close()


def test_process_crash_between_score_and_receipt_rolls_back_both(tmp_path):
    import json, os, subprocess, sys
    from pathlib import Path
    path = tmp_path / "score-crash.sqlite"
    service = make_service(path)
    ep = start_readback(service)
    confirm(service, ep, "go to the clinic today before six myself")
    offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
    token = offer.operation_token
    service._store.close()
    script = '''import os,signal
from test_truthfulness import make_service
from carerelay.state import JourneyTransaction
from carerelay.journey_commands import verify_operation
from _legacy_service_probes import KEY
service=make_service(PATH)
def crash(*args,**kwargs):os.kill(os.getpid(),signal.SIGKILL)
JourneyTransaction.complete_once=crash
service.score_confirmed(verify_operation(TOKEN,signing_key=KEY))
'''.replace("PATH", repr(str(path))).replace("TOKEN", repr(token))
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=str(root / "src") + os.pathsep + str(root / "tests"),
        APP_DATABASE_URL=":memory:", APP_ENV="local", APP_CLOCK="scenario", CARERELAY_API_TOKEN="", PYTHONDONTWRITEBYTECODE="1",
        CARERELAY_TEST_DSN="postgresql://127.0.0.1:1/carerelay_disabled")
    child = subprocess.run([sys.executable, "-c", script], cwd=root, env=env, capture_output=True, text=True)
    assert child.returncode == -9, child.stderr
    service = make_service(path)
    try:
        assert service._store.list_restatements(ep) == ()
        replay = service.score_confirmed(verify_operation(token, signing_key=KEY))
        assert replay.receipt.state == "pending" and not replay.receipt.scored
        rows = service._store._conn.execute("SELECT phase FROM journey_commands WHERE operation_id=?", (replay.receipt.operation_id,)).fetchall()
        assert [r[0] for r in rows] == ["claimed"]
        assert replay.journey.text["saved_words"] == "go to the clinic today before six myself"
    finally:
        service._store.close()


@pytest.mark.parametrize("dimension", ["episode", "version", "policy", "revision", "stop", "sticky_expiry",
    "deadline", "attempt", "parent", "cue", "repair_count", "confirmation", "words", "h3", "cap"])
def test_final_context_fences_are_independent(tmp_path, dimension, monkeypatch):
    import json
    service = make_service(tmp_path / "fences.sqlite")
    paused = PausedExtractor()
    service._readback_extractor = paused
    try:
        ep = start_readback(service)
        confirm(service, ep, "go to the clinic today before six myself")
        offer = next(o for o in service.project_journey(ep).commands if o.kind == "score_words")
        binding = verify_operation(offer.operation_token, signing_key=KEY)
        with ThreadPoolExecutor(1) as worker:
            future = worker.submit(service.score_confirmed, binding)
            assert paused.entered.wait(2)
            try:
                bundle = service._store.load_journey_bundle(ep)
                claim = next(r for r in bundle.commands if r["operation_id"] == binding.operation_id and r["phase"] == "claimed")
                event_data = next(json.loads(p) for k, p, _ in bundle.events if k == "command_claimed" and json.loads(p)["operation_id"] == binding.operation_id)
                context_data = event_data["readback_context"]
                ctx = models.ReadbackContext(**context_data, claim_revision=claim["claim_revision"])
                now = fixture.SCENARIO_NOW_UTC
                assert rules.readback_context_current(ctx, bundle, now_utc=now) is True
                if dimension == "episode": ctx = replace(ctx, episode_id="foreign-episode")
                elif dimension == "version": ctx = replace(ctx, disposition_version=2)
                elif dimension == "policy": ctx = replace(ctx, policy_version="foreign-policy")
                elif dimension == "revision": ctx = replace(ctx, claim_revision=0)
                elif dimension == "stop": bundle = replace(bundle, snapshot=replace(bundle.snapshot, flow_stop_reason="fixture-stop"))
                elif dimension == "sticky_expiry": bundle = replace(bundle, snapshot=replace(bundle.snapshot, expiry_event_id="fictional-expiry"))
                elif dimension == "deadline": now = bundle.snapshot.disposition.clinical_deadline_utc
                elif dimension == "attempt":
                    ctx = replace(ctx, attempt_id="foreign-attempt")
                    events = []
                    for k, p, t in bundle.events:
                        if k == "words_confirmed":
                            data = json.loads(p); data["attempt_id"] = ctx.attempt_id; p = json.dumps(data)
                        events.append((k,p,t))
                    bundle = replace(bundle, events=tuple(events))
                elif dimension == "parent":
                    ctx = replace(ctx, parent_id="foreign-parent")
                    events = []
                    for k, p, t in bundle.events:
                        if k == "words_confirmed":
                            data = json.loads(p); data["parent_id"] = ctx.parent_id; p = json.dumps(data)
                        events.append((k,p,t))
                    bundle = replace(bundle, events=tuple(events))
                elif dimension == "cue": ctx = replace(ctx, effective_hint=models.HintLevel.H2)
                elif dimension == "repair_count": ctx = replace(ctx, completed_repairs=1)
                elif dimension == "confirmation": ctx = replace(ctx, confirmation_id="foreign-confirmation")
                elif dimension == "words": ctx = replace(ctx, confirmed_text=ctx.confirmed_text + " ")
                if dimension in {"h3", "cap"}:
                    journey = rules.derive_journey(bundle, now_utc=now)
                    ctx = replace(ctx, effective_hint=models.HintLevel.H3) if dimension == "h3" else replace(ctx, completed_repairs=2)
                    flow = replace(journey.flow, effective_hint=ctx.effective_hint, completed_repairs=ctx.completed_repairs)
                    with monkeypatch.context() as controlled:
                        controlled.setattr(rules, "derive_journey", lambda *args, **kwargs: replace(journey, flow=flow))
                        assert rules.readback_context_current(ctx, bundle, now_utc=now) is False
                else:
                    assert rules.readback_context_current(ctx, bundle, now_utc=now) is False
            finally:
                paused.release.set()
            future.result(2)
    finally:
        paused.release.set()
        service._store.close()


@pytest.mark.parametrize("case", ["mode", "validation", "missing_raw", "schema", "refused_type", "refused",
    "uncertainty_type", "unknown_uncertainty", "null_without_uncertainty", "span_type", "start_bool",
    "end_bool", "text_type", "negative", "empty", "end_overrun", "ungrounded"])
def test_offline_output_boundary_refuses_each_invalid_shape(case):
    from types import SimpleNamespace
    from carerelay.adp_extraction import eligible_offline_output
    text = "go to the clinic today before six myself"
    if case == "start_bool": text = " " + text
    elif case == "end_bool": text = "g " + text
    good = offline(text)
    assert eligible_offline_output(good, confirmed_text=text) is not None
    result, raw = good, good.raw
    if case == "mode": result = replace(result, mode="adp")
    elif case == "validation": result = replace(result, validation="timeout")
    elif case == "missing_raw": result = replace(result, raw=None)
    elif case == "schema": raw = replace(raw, schema_version="unknown")
    elif case == "refused_type": raw = replace(raw, refused=0)
    elif case == "refused": raw = replace(raw, refused=True)
    elif case == "uncertainty_type": raw = replace(raw, uncertain_fields=set())
    elif case == "unknown_uncertainty": raw = replace(raw, uncertain_fields=frozenset({"unknown"}))
    elif case == "null_without_uncertainty": raw = replace(raw, action_span=None)
    else:
        span = raw.action_span
        if case == "span_type": span = SimpleNamespace(text=span.text, start=span.start, end=span.end)
        elif case == "start_bool": span = models.SourceSpan(text[1:17], True, 17)
        elif case == "end_bool": span = models.SourceSpan(text[0:1], 0, True)
        elif case == "text_type": span = replace(span, text=1)
        elif case == "negative": span = models.SourceSpan(text[-1:], -1, len(text))
        elif case == "empty": span = models.SourceSpan("", 0, 0)
        elif case == "end_overrun": span = models.SourceSpan(text, 0, len(text)+1)
        elif case == "ungrounded": span = replace(span, text="invented source")
        raw = replace(raw, action_span=span)
    if case not in {"mode", "validation", "missing_raw"}: result = replace(result, raw=raw)
    assert eligible_offline_output(result, confirmed_text=text) is None


@pytest.mark.parametrize('case', ['parent_version', 'parent_attempt', 'cycle', 'missing_ancestor',
    'nonancestor', 'source_policy', 'source_attempt', 'source_version', 'source_match',
    'confirmation_missing', 'confirmation_episode', 'confirmation_attempt', 'confirmation_version',
    'confirmation_parent', 'span_shape', 'start_type', 'end_type', 'offset_negative', 'offset_empty',
    'offset_overrun', 'offset_text', 'unknown_value'])
def test_grounded_chain_refuses_each_untrusted_source(tmp_path, case):
    import copy, json
    service = make_service(tmp_path / 'grounding.sqlite')
    try:
        ep = start_readback(service)
        saved = confirm(service, ep, 'go to the clinic tomorrow before 6pm myself unknown')
        _, first = score(service, ep)
        confirm(service, ep, 'unknown')
        _, second = score(service, ep)
        with service._store.journey_transaction(ep, write=False) as tx: bundle = tx.load_bundle(ep)
        attempt, parent = second.journey.flow.readback_attempt_id, second.receipt.result_ref
        good = rules.grounded_parent_matches(bundle, attempt_id=attempt, parent_id=parent)
        assert [(m.field, m.source_restatement_id) for m in good] == [
            ('action_id', first.receipt.result_ref), ('next_owner_id', first.receipt.result_ref)]
        rows = [replace(r, provenance=copy.deepcopy(r.provenance)) for r in bundle.restatements]
        source, latest = rows
        meta = source.provenance
        expected = None
        if case == 'parent_version': rows[1] = replace(latest, disposition_version=2); expected = 'parent is not this chain'
        elif case == 'parent_attempt': latest.provenance['attempt_id'] = 'other'; expected = 'parent is not this chain'
        elif case == 'cycle': latest.provenance['parent_id'] = parent; expected = 'cyclic retention chain'
        elif case == 'missing_ancestor': latest.provenance['parent_id'] = 'absent'; expected = 'missing retention ancestor'
        elif case == 'nonancestor':
            rows.append(replace(source, restatement_id='other-fork'))
            latest.provenance['retained'][0]['source_restatement_id'] = 'other-fork'; expected = 'source is not an ancestor'
        elif case == 'source_policy': meta['policy_version'] = 'other'; expected = 'source binding changed'
        elif case == 'source_attempt': meta['attempt_id'] = 'other'; expected = 'source binding changed'
        elif case == 'source_version': rows[0] = replace(source, disposition_version=2); expected = 'source binding changed'
        elif case == 'source_match': rows[0] = replace(source, comparison=replace(source.comparison, matched=frozenset({'next_owner_id'}))); expected = 'source binding changed'
        else:
            events = []
            for kind, payload, at in bundle.events:
                data = json.loads(payload) if kind == 'words_confirmed' else {}
                if kind == 'words_confirmed' and data.get('confirmation_id') == saved.receipt.result_ref:
                    key = {'confirmation_missing': 'confirmation_id', 'confirmation_episode': 'episode_id',
                        'confirmation_attempt': 'attempt_id', 'confirmation_version': 'disposition_version',
                        'confirmation_parent': 'parent_id'}.get(case)
                    if key: data[key] = 2 if key == 'disposition_version' else 'other'
                events.append((kind, json.dumps(data) if kind == 'words_confirmed' else payload, at))
            bundle = replace(bundle, events=tuple(events))
            if case.startswith('confirmation_'): expected = 'source confirmation changed'
            else:
                span = meta['raw']['action_span']
                if case == 'span_shape': meta['raw']['action_span'] = None; expected = 'no source span'
                elif case == 'start_type': span.update(start=True, end=16, text='o to the clinic')
                elif case == 'end_type': span.update(start=0, end=True, text='g')
                elif case == 'offset_negative': span.update(start=-1, end=16, text='')
                elif case == 'offset_empty': span.update(start=0, end=0, text='')
                elif case == 'offset_overrun': span.update(start=0, end=1000, text='go to the clinic tomorrow before 6pm myself unknown')
                elif case == 'offset_text': span['text'] = 'invented'
                elif case == 'unknown_value': span.update(start=44, end=51, text='unknown'); expected = 'value is unknown'
                expected = expected or 'offsets are not grounded'
        bad = replace(bundle, restatements=tuple(rows))
        with pytest.raises(rules.JourneyUnavailable, match=expected):
            rules.grounded_parent_matches(bad, attempt_id=attempt, parent_id=parent)
    finally: service._store.close()


@pytest.mark.parametrize('case', ['version', 'attempt', 'episode', 'policy', 'text_type', 'text_empty',
    'text_long', 'id_type', 'id_empty', 'parent'])
def test_confirmation_event_requires_each_binding(tmp_path, case):
    import json
    service = make_service(tmp_path / 'confirmation-binding.sqlite')
    try:
        ep = start_readback(service)
        saved = confirm(service, ep, 'go to the clinic today before six myself')
        attempt = saved.journey.flow.readback_attempt_id
        with service._store.journey_transaction(ep, write=False) as tx: bundle = tx.load_bundle(ep)
        assert rules.readback_confirmation(bundle, attempt_id=attempt, parent_id=None)['text'] == 'go to the clinic today before six myself'
        events = []
        changes = {'version': ('disposition_version', 2), 'attempt': ('attempt_id', 'other'),
            'episode': ('episode_id', 'other'), 'policy': ('policy_version', 'other'), 'text_type': ('text', 1),
            'text_empty': ('text', ' '), 'text_long': ('text', 'a' * 2049), 'id_type': ('confirmation_id', 1),
            'id_empty': ('confirmation_id', ''), 'parent': ('parent_id', 'other')}
        for kind, payload, at in bundle.events:
            data = json.loads(payload) if kind == 'words_confirmed' else {}
            if kind == 'words_confirmed':
                key, value = changes[case]; data[key] = value
            events.append((kind, json.dumps(data) if kind == 'words_confirmed' else payload, at))
        bad = replace(bundle, events=tuple(events))
        if case in {'version', 'attempt', 'parent'}:
            assert rules.readback_confirmation(bad, attempt_id=attempt, parent_id=None) is None
        else:
            with pytest.raises(rules.JourneyUnavailable): rules.readback_confirmation(bad, attempt_id=attempt, parent_id=None)
    finally: service._store.close()


@pytest.mark.parametrize('case', ['claim', 'kind', 'revision', 'parent', 'digest', 'episode', 'version',
    'policy', 'attempt', 'latest_parent', 'stop', 'sticky_expiry', 'deadline'])
def test_confirmation_store_refuses_at_its_first_boundary(tmp_path, case, monkeypatch):
    from carerelay.journey_commands import CommandConflict
    from datetime import timedelta
    service = make_service(tmp_path / 'store-confirm.sqlite')
    try:
        foreign_parent = None
        if case in {'parent','latest_parent'}:
            service.ensure_episode('foreign', 'fictional')
            service.intake('foreign', fixture.BOUND_COMPLAINT)
            service.submit_restatement('foreign', 'go to the clinic today before six myself', models.HintLevel.H1)
            foreign_parent = service._store.list_restatements('foreign')[0].restatement_id
        ep = start_readback(service)
        text = 'go to the clinic today before six myself'
        digest = request_digest('confirm_words', {'text': text, 'parent_id': None})
        token = service.prepare_command(ep, kind='confirm_words', body_sha256=digest, parent_id=None)
        binding = verify_operation(token, signing_key=KEY)
        with service._store.journey_transaction(ep, write=True) as tx:
            bundle = tx.load_bundle(ep); journey = rules.derive_journey(bundle, now_utc=fixture.SCENARIO_NOW_UTC)
            ctx = models.ReadbackContext(ep, 1, fixture.POLICY_VERSION, journey.flow.readback_attempt_id,
                None, binding.operation_id, text, None, 0, (), models.HintLevel.H1, 0)
            owned = binding
            if case == 'kind': owned = replace(binding, kind='show_plan')
            elif case == 'parent': owned = replace(binding, parent_restatement_id=foreign_parent)
            elif case == 'digest': owned = replace(binding, body_sha256='f' * 64)
            elif case == 'latest_parent': owned = replace(binding, parent_restatement_id=foreign_parent,
                body_sha256=request_digest('confirm_words', {'text':text, 'parent_id':foreign_parent}))
            if case == 'stop': service._store.record_flow_stop(ep, 1, 'fixture-stop', 'nurse_line', now_utc=fixture.SCENARIO_NOW_UTC)
            if case == 'stop': owned = replace(owned, expected_revision=tx.load_bundle(ep).revision)
            if case != 'claim': tx.claim_once(owned, now_utc=fixture.SCENARIO_NOW_UTC)
            if case == 'sticky_expiry':
                original_load = tx.load_bundle
                monkeypatch.setattr(tx, 'load_bundle', lambda episode: replace(original_load(episode), snapshot=replace(original_load(episode).snapshot, expiry_event_id='fixture-expiry')))
            if case == 'revision': tx._event('fixture-audit', {}, fixture.SCENARIO_NOW_UTC)
            now = fixture.SCENARIO_NOW_UTC
            if case == 'episode': ctx = replace(ctx, episode_id='other')
            elif case == 'version': ctx = replace(ctx, disposition_version=2)
            elif case == 'policy': ctx = replace(ctx, policy_version='other')
            elif case == 'attempt': ctx = replace(ctx, attempt_id='other')
            elif case == 'latest_parent': ctx = replace(ctx, parent_id=foreign_parent)
            elif case == 'deadline': now += timedelta(hours=10)
            expected = 'exact owned claim' if case in {'claim','kind','revision','parent','digest'} else 'context changed'
            with pytest.raises(CommandConflict, match=expected): tx.append_confirmed_words(ctx, now_utc=now)
        assert service._store.list_restatements(ep) == ()
    finally: service._store.close()


@pytest.mark.parametrize('case', ['kind','version','revision','confirmation','parent','purpose','digest','terminal'])
def test_scoring_store_requires_each_owned_claim_dimension(tmp_path, case):
    from carerelay.journey_commands import CommandConflict
    service = make_service(tmp_path / 'store-score.sqlite')
    try:
        ep = start_readback(service)
        saved = confirm(service, ep, 'go to the clinic today before six myself')
        binding = verify_operation(next(o.operation_token for o in saved.journey.commands if o.kind == 'score_words'), signing_key=KEY)
        with service._store.journey_transaction(ep, write=True) as tx:
            changed = {'episode': {'episode_id':'other'}, 'kind': {},
                'version': {'disposition_version':2}, 'revision': {'claim_revision':0},
                'confirmation': {'confirmation_id':'other'}, 'parent': {'parent_id':'other'},
                'purpose': {}, 'digest': {}, 'terminal': {}}[case]
            claim = binding
            if case == 'purpose': claim = replace(binding, purpose='other')
            elif case == 'digest': claim = replace(binding, body_sha256='f'*64)
            elif case == 'kind': claim = replace(binding, kind='repair_words')
            elif case == 'version': claim = replace(binding, purpose=binding.purpose.replace('disposition:1:', 'disposition:2:'))
            elif case == 'confirmation': claim = replace(binding, body_sha256=request_digest('score_words', {'confirmation_id':'other'}))
            elif case == 'parent': claim = replace(binding, kind='repair_words', purpose=binding.purpose.replace(':score_words', ':repair_words'), body_sha256=request_digest('repair_words', {'confirmation_id':binding.confirmation_id}))
            acquired = tx.claim_once(claim, now_utc=fixture.SCENARIO_NOW_UTC)
            ctx = models.ReadbackContext(ep, 1, fixture.POLICY_VERSION, saved.journey.flow.readback_attempt_id,
                None, binding.confirmation_id, 'go to the clinic today before six myself', None, 0, (), models.HintLevel.H1, acquired.claim_revision)
            ctx = replace(ctx, **changed)
            if case == 'terminal': tx.complete_once(binding.operation_id, state='superseded', result_ref=None, scored=False, now_utc=fixture.SCENARIO_NOW_UTC)
            extracted = models.ExtractedPlan('go to the clinic', 'today before six', 'myself')
            with pytest.raises(CommandConflict, match='exact owned pending claim'):
                tx.append_scored_round(ctx, extracted, comparison(extracted), now_utc=fixture.SCENARIO_NOW_UTC, provenance={})
        assert service._store.list_restatements(ep) == ()
    finally: service._store.close()


@pytest.mark.parametrize('case', ['purpose', 'offer', 'parent', 'scoring_kind', 'scoring_confirmation', 'scoring_digest',
    'event_kind', 'event_confirmation', 'event_digest', 'confirmation_kind', 'confirmation_id', 'words_type', 'words_empty', 'words_long'])
def test_service_readback_refuses_before_claim_or_extraction(tmp_path, case):
    from carerelay.journey_commands import CommandConflict, CommandInvalid
    service = make_service(tmp_path / 'service-boundary.sqlite')
    try:
        ep = start_readback(service)
        saved = confirm(service, ep, 'go to the clinic today before six myself')
        score_binding = verify_operation(next(o.operation_token for o in saved.journey.commands if o.kind == 'score_words'), signing_key=KEY)
        show_binding = verify_operation(next(o.operation_token for o in saved.journey.commands if o.kind == 'show_plan'), signing_key=KEY)
        words = 'another fictional answer'
        confirm_binding = verify_operation(service.prepare_command(ep, kind='confirm_words', parent_id=None,
            body_sha256=request_digest('confirm_words', {'text':words,'parent_id':None})), signing_key=KEY)
        before = len(service._store.list_events(ep))
        if case in {'purpose','offer','parent'}:
            changed = replace(score_binding, **{'purpose': {'purpose':'other'}, 'offer': {'kind':'request'}, 'parent': {'parent_restatement_id':'old'}}[case])
            with service._store.journey_transaction(ep, write=False) as tx:
                with pytest.raises(CommandConflict, match={'purpose':'purpose changed','offer':'not offered','parent':'parent is not latest'}[case]):
                    if case == 'offer': changed = replace(changed, purpose=service._readback_purpose(saved.journey, 'request'))
                    service._require_readback_offer(changed, tx.load_bundle(ep), fixture.SCENARIO_NOW_UTC)
        elif case.startswith('scoring_'):
            bad = replace(score_binding, **{'scoring_kind': {'kind':'show_plan'}, 'scoring_confirmation': {'confirmation_id':None}, 'scoring_digest': {'body_sha256':'f'*64}}[case])
            with pytest.raises(CommandConflict if case == 'scoring_digest' else CommandInvalid): service.score_confirmed(bad)
        elif case.startswith('event_'):
            bad = replace(show_binding, **{'event_kind': {'kind':'score_words'}, 'event_confirmation': {'confirmation_id':'other'}, 'event_digest': {'body_sha256':'f'*64}}[case])
            with pytest.raises(CommandConflict if case == 'event_digest' else CommandInvalid): service.record_journey_event(bad)
        else:
            bad = replace(confirm_binding, kind='show_plan') if case == 'confirmation_kind' else replace(confirm_binding, confirmation_id='other') if case == 'confirmation_id' else confirm_binding
            words = {'words_type':1,'words_empty':' ','words_long':'a'*2049}.get(case, words)
            with pytest.raises(CommandInvalid): service.confirm_words(bad, text=words)
        assert len(service._store.list_events(ep)) == before
        assert service._store.list_restatements(ep) == ()
    finally: service._store.close()


@pytest.mark.parametrize('case', ['version_type','version_zero','purpose_type','ref_type','ref_format','purpose_parts',
    'purpose_prefix','purpose_version','purpose_role','purpose_attempt','purpose_kind','start_attempt','missing_attempt',
    'event_parent','event_confirmation','confirm_id','score_confirmation','score_parent','repair_parent'])
def test_frontend_s16_capability_grammar_has_independent_controls(case):
    import subprocess, json
    from pathlib import Path
    good = dict(operation_id='operation-fixture', episode_id='12345678-1234-4234-9234-123456789abc',
        disposition_version=1, expected_revision=4, kind='score_words', purpose='disposition:1:readback:attempt-fixture:score_words',
        body_sha256='a'*64, parent_restatement_id=None, confirmation_id='confirmation-fixture', token_schema='carerelay-command-v1')
    if case in {'start_attempt','event_parent','event_confirmation'}:
        good.update(kind='readback_started', purpose='disposition:1:readback:none:readback_started', confirmation_id=None)
    elif case == 'confirm_id': good.update(kind='confirm_words', purpose='disposition:1:readback:attempt-fixture:confirm_words', confirmation_id=None)
    elif case == 'repair_parent': good.update(kind='repair_words', purpose='disposition:1:readback:attempt-fixture:repair_words', parent_restatement_id='parent-fixture')
    bad = dict(good)
    changes = {'version_type':('disposition_version',True),'version_zero':('disposition_version',0),
        'purpose_type':('purpose',1),'ref_type':('confirmation_id',1),'ref_format':('confirmation_id','bad/ref'),
        'purpose_parts':('purpose','disposition:1:readback:attempt-fixture:score_words:extra'),
        'purpose_prefix':('purpose','other:1:readback:attempt-fixture:score_words'),
        'purpose_version':('purpose','disposition:2:readback:attempt-fixture:score_words'),
        'purpose_role':('purpose','disposition:1:other:attempt-fixture:score_words'),
        'purpose_attempt':('purpose','disposition:1:readback:bad/ref:score_words'),
        'purpose_kind':('purpose','disposition:1:readback:attempt-fixture:repair_words'),
        'start_attempt':('purpose','disposition:1:readback:attempt-fixture:readback_started'),
        'missing_attempt':('purpose','disposition:1:readback:none:score_words'),
        'event_parent':('parent_restatement_id','parent-fixture'),'event_confirmation':('confirmation_id','confirmation-fixture'),
        'confirm_id':('confirmation_id','confirmation-fixture'),'score_confirmation':('confirmation_id',None),
        'score_parent':('parent_restatement_id','parent-fixture'),'repair_parent':('parent_restatement_id',None)}
    key, value = changes[case]; bad[key] = value
    if case in {'version_type','version_zero'}:
        bad['purpose'] = 'disposition:' + ('true' if case == 'version_type' else '0') + ':readback:attempt-fixture:score_words'
    script = '''import {createHmac} from "node:crypto";import {decodeOperation} from "./frontend/lib/episode-locator.ts";import {readFileSync} from "node:fs";
const [good,bad,key]=JSON.parse(readFileSync(0,'utf8'));
function token(v){const payload=Buffer.from(JSON.stringify(Object.fromEntries(Object.keys(v).sort().map(k=>[k,v[k]])))).toString('base64url');const split=createHmac('sha256',key).update('carerelay:command:v1').digest();return payload+'.'+createHmac('sha256',split).update(payload).digest('base64url')}
console.log(JSON.stringify([decodeOperation(token(good),key)!==null,decodeOperation(token(bad),key)===null]));'''
    result = subprocess.run(['node','--input-type=module','-e',script],cwd=Path(__file__).resolve().parents[1],input=json.dumps([good,bad,KEY.decode()]),capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [True,True]


@pytest.mark.parametrize('case', ['hidden','shown','confirmed','pending','unavailable','timing','timing_uncertain_owner',
    'repaired','cap','h3_confirmed','pending_h3','stopped_confirmed','expired_confirmed','expired_uncertain'])
def test_producer_and_frontend_agree_on_each_new_lifecycle(tmp_path, case):
    import subprocess, json
    from pathlib import Path
    from datetime import timedelta
    from carerelay.service import ScenarioClock
    from carerelay.presentation import journey_surface
    service = make_service(tmp_path / 'whole-projection.sqlite')
    try:
        ep = start_readback(service)
        if case=='shown': event(service, ep, 'show_plan')
        elif case not in {'hidden'}:
            words = 'unknown' if case in {'cap','expired_uncertain'} else 'go to the clinic tomorrow before 6pm' if case=='timing_uncertain_owner' else 'go to the clinic tomorrow before 6pm myself'
            saved = confirm(service,ep,words)
            if case in {'pending','pending_h3'}:
                binding=verify_operation(next(o.operation_token for o in saved.journey.commands if o.kind=='score_words'),signing_key=KEY)
                with service._store.journey_transaction(ep,write=True) as tx:tx.claim_once(binding,now_utc=fixture.SCENARIO_NOW_UTC)
                assert {o.kind for o in service.project_journey(ep).commands}=={'show_plan','hide_plan','h3','supersede_extraction'}
                if case=='pending_h3':
                    stopped=event(service,ep,'h3')
                    assert {o.kind for o in stopped.journey.commands}=={'show_plan','hide_plan'}
                    hidden=event(service,ep,'hide_plan')
                    assert not hidden.journey.flow.card_visible and hidden.journey.flow.effective_hint is models.HintLevel.H3
            elif case=='h3_confirmed':event(service,ep,'h3')
            elif case=='stopped_confirmed':service._store.record_flow_stop(ep,1,'fixture-stop','nurse_line',now_utc=fixture.SCENARIO_NOW_UTC)
            elif case in {'expired_confirmed','expired_uncertain'}:
                if case=='expired_uncertain':score(service,ep)
                service._clock=ScenarioClock(fixture.SCENARIO_NOW_UTC+timedelta(hours=10))
            elif case=='unavailable':
                class TimeoutExtractor:
                    def extract(self,request,*,budget_seconds):
                        from carerelay.adp_extraction import ExtractionResult
                        return ExtractionResult('local-sim','timeout',None,request.correlation_id,None,'offline-fixture-v1','carerelay-readback-v1',None,'timeout')
                service._readback_extractor=TimeoutExtractor();score(service,ep)
            elif case not in {'confirmed'}:
                score(service,ep)
                if case=='repaired':confirm(service,ep,'today before six');score(service,ep)
                elif case=='cap':
                    for _ in range(2):confirm(service,ep,'unknown');score(service,ep)
        body=journey_surface(service.project_journey(ep))
        if case=='timing_uncertain_owner':
            assert body['step']=='repair' and body['flow']['interpretation']=='uncertain'
            assert body['text'].get('feedback')=='We could not confirm that. Try different words, or show your plan.'
        if body['step'] not in {'readback','repair'}:
            assert not {'feedback','saved_words','retry_label','retry_help','input_label','confirmation_label'} & set(body['text'])
        script='''import{decodeJourney}from"./frontend/lib/journey.ts";import{readFileSync}from"node:fs";const body=JSON.parse(readFileSync(0,'utf8'));console.log(JSON.stringify(decodeJourney(body,body.episode_id)!==null));'''
        result=subprocess.run(['node','--input-type=module','-e',script],cwd=Path(__file__).resolve().parents[1],input=json.dumps(body),capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout) is True, ('producer projection rejected',case,body['text'])
    finally:service._store.close()


@pytest.mark.parametrize('side', ['prefix','suffix'])
def test_injected_exact_subword_is_not_a_grounded_field(tmp_path, side):
    from carerelay.adp_extraction import eligible_offline_output
    text='go to the clinic today before six ' + ('notmyself' if side=='prefix' else 'myselfish')
    start=text.index('myself')
    good=offline('go to the clinic today before six myself')
    raw=replace(good.raw, next_owner_span=models.SourceSpan('myself',start,start+6), uncertain_fields=frozenset())
    fake=replace(good,raw=raw)
    assert text[start:start+6]=='myself'  # Exact offsets alone do not prove a field.
    assert eligible_offline_output(good,confirmed_text='go to the clinic today before six myself') is not None
    assert eligible_offline_output(fake,confirmed_text=text) is None
    class SubwordExtractor:
        def extract(self,request,*,budget_seconds):return replace(fake,request_id=request.correlation_id)
    service=make_service(tmp_path/'subword.sqlite');service._readback_extractor=SubwordExtractor()
    try:
        ep=start_readback(service);confirm(service,ep,text);_,result=score(service,ep)
        assert result.receipt.state=='unavailable' and not result.receipt.scored
        assert result.journey.flow.completed_repairs==0 and not result.journey.flow.stopped
        assert service._store.list_restatements(ep)==()
    finally:service._store.close()


def test_full_width_question_never_becomes_a_clean_timing_repair(tmp_path):
    assert rules.independent_uncertainty('today before six？',policy=fixture.policy())==frozenset({'deadline_utc'})
    assert rules.independent_uncertainty('today before six. I like tea.',policy=fixture.policy())==frozenset()
    service=make_service(tmp_path/'full-width-question.sqlite')
    try:
        ep=start_readback(service);confirm(service,ep,'go to the clinic tomorrow before 6pm myself');score(service,ep)
        confirm(service,ep,'today before six？');_,result=score(service,ep)
        row=service._store.list_restatements(ep)[-1]
        assert row.comparison.matched==frozenset({'action_id','next_owner_id'})
        assert row.comparison.uncertain==frozenset({'deadline_utc'})
        assert row.outcome is models.RecallOutcome.NOT_RECALLED
        assert result.journey.step=='readback' and result.journey.flow.completed_repairs==1
    finally:service._store.close()
