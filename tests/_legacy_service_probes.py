"""Explicit legacy service probes, never a TestClient transport replacement.

Probe.status_code is the former service-error classification, not HTTP evidence.
Each operation calls EpisodeService directly; retirement is tested with real POSTs.
Signed start and example selection below are real HTTP requests.
"""
from dataclasses import asdict, dataclass
from functools import wraps
import json

from carerelay.api import app, get_service, _restatement_body, COORDINATOR_FALLBACK_TEXT
from carerelay.coordinator import CoordinatorUnavailable
from carerelay.demo import fixture
from carerelay.domain.models import AttemptCommand, HintLevel, OperationBinding
from carerelay.domain.rules import PolicyViolation
from carerelay.journey_commands import CommandConflict, CommandInvalid, issue_operation, request_digest, verify_operation, PURPOSES
from carerelay.service import ActionOutcome, ServiceError, IntakeNotRecognised
from carerelay.state import EpisodeNotFound, RestatementNotFound, StateError, CLINICAL_SCOPE, derive_attempt_key

KEY = b"synthetic-legacy-service-probes"


def service():
    return app.dependency_overrides.get(get_service, get_service)()


@dataclass
class Probe:
    status_code: int
    body: dict

    @property
    def text(self):
        return json.dumps(self.body)

    def json(self):
        return self.body


def classified(fn):
    @wraps(fn)
    def invoke(*args, **kwargs):
        try:
            return Probe(200, fn(*args, **kwargs))
        except (EpisodeNotFound, RestatementNotFound) as exc:
            return Probe(404, {"detail": str(exc)})
        except IntakeNotRecognised as exc:
            return Probe(422, {"detail": {"detail": str(exc), "stopped_at": "human_path"}})
        except PolicyViolation as exc:
            detail = {"detail": str(exc), "stopped_at": "human_path"} if fn.__name__ in {"service_barrier", "service_action"} else str(exc)
            if fn.__name__ == "service_barrier":
                rows = service()._store.list_barriers(args[1])
                payload = kwargs["json"]
                detail["barrier_recorded"] = bool(rows and
                    rows[-1]["proposed_route_id"] == payload.get("proposed_route_id") and
                    rows[-1]["stopped_at_human_path"])
            return Probe(422, {"detail": detail})
        except (ServiceError, StateError, CommandInvalid, CommandConflict) as exc:
            return Probe(409, {"detail": str(exc)})
        except CoordinatorUnavailable:
            return Probe(503, {"detail": {"scored": False, "text_fallback": COORDINATOR_FALLBACK_TEXT}})
    return invoke


def signed_create(client, episode=fixture.DEMO_EPISODE_ID, **kwargs):
    binding = OperationBinding("legacy-probe-create-" + episode, episode, None, 0,
        "create", PURPOSES["create"], request_digest("create", {}), None, None)
    token = issue_operation(binding, signing_key=service()._operation_signing_key())
    return client.post("/api/episodes", json={"operation_token": token}, **kwargs)


def signed_intake(client, episode=fixture.DEMO_EPISODE_ID):
    prepared = client.get(f"/api/episodes/{episode}", params={"prepare_kind": "select_example",
        "body_sha256": request_digest("select_example", {"example_id": "scripted-appointment"})})
    assert prepared.status_code == 200, prepared.text
    return client.post(f"/api/episodes/{episode}/intake", json={
        "operation_token": prepared.json()["operation_token"], "example_id": "scripted-appointment"})


@classified
def service_intake(client, episode, *, json):
    d = service().intake(episode, json["confirmed_text"])
    return {"episode_id": episode, "disposition_version": d.version,
        "action_id": d.action_id, "deadline_utc": d.clinical_deadline_utc.isoformat(),
        "next_owner_id": d.next_owner_id, "fallback_route_id": d.fallback_route_id,
        "simulated": True, "fixture_label": fixture.FIXTURE_LABEL}


@classified
def service_restatement(client, episode, *, json):
    outcome = service().submit_restatement(episode, json["text"], json["hint_level"],
        json.get("transcript_confirmation_id"), input_mode=json.get("input_mode", "text"),
        dwell_seconds=json.get("dwell_seconds"))
    return _restatement_body(outcome).model_dump(mode="json")


@classified
def service_repair(client, episode, parent, *, json):
    outcome = service().repair_restatement(parent, json["text"], json["hint_level"],
        json.get("transcript_confirmation_id"), input_mode=json.get("input_mode", "text"),
        dwell_seconds=json.get("dwell_seconds"), episode_id=episode)
    return _restatement_body(outcome).model_dump(mode="json")


@classified
def service_confirmation(client, episode, *, json):
    return {"episode_id": episode, "confirmation_id": service().confirm_transcript(episode, json["corrected_text"])}


@classified
def service_hint(client, episode, *, json):
    h = service().record_hint_event(episode, json["hint_level"], json["event"], json.get("dwell_seconds"))
    return {"episode_id": episode, "hint_level": h.level.value, "card_visible": h.card_visible}


@classified
def service_consent(client, episode, *, json):
    granted = json["granted"]
    version = service().change_consent(episode, granted)
    return {"episode_id": episode, "scope": CLINICAL_SCOPE, "version": version,
        "granted": granted, "simulated": True, "fixture_label": fixture.FIXTURE_LABEL}


@classified
def service_action(client, episode, *, json):
    """Direct service dispatch probe with explicit trusted prior-history setup.

    Caller purpose is a historical fixture label; the command fixes its purpose.
    Raw-caller rejection is tested independently, not inferred from this probe.
    """
    outcome = command_action(service(), episode, route_id=json["route_id"])
    return action_body(outcome)


def action_body(outcome):
    body = asdict(outcome)
    body.pop("tool")
    body.update(execution=outcome.execution.value, origin=outcome.origin.value,
        outcome=outcome.tool.outcome.value if outcome.tool else None,
        provider_ref=outcome.tool.provider_ref if outcome.tool else None,
        payload=outcome.tool.payload if outcome.tool else None, fixture_label=fixture.FIXTURE_LABEL)
    return body


def prepared_binding(service, episode, kind, payload=None):
    if kind in {"select_example", "confirm_words", "select_barrier"}:
        token = service.prepare_command(episode, kind=kind,
            body_sha256=request_digest(kind, payload or {}), parent_id=None)
    else:
        token = next(offer.operation_token for offer in service.project_journey(episode).commands
                     if offer.kind == kind)
    return verify_operation(token, signing_key=service._operation_signing_key())


def seed_booking_history(service, episode):
    """Trusted understood fixture, followed by the real supported booking command."""
    snapshot = service._store.load_snapshot(episode)
    if not any(row.disposition_version == snapshot.disposition.version
               for row in service._store.list_restatements(episode)):
        service.submit_restatement(episode, "see the doctor today before 6pm myself", HintLevel.H1)
    journey = service.project_journey(episode)
    if any(offer.kind == "select_barrier" for offer in journey.commands):
        service.record_barrier_choice(prepared_binding(service, episode, "select_barrier",
            {"choice_id": "booking"}), choice_id="booking")


def command_action(service, episode, *, route_id="fictional_provider", binding=None):
    """Invoke only the command path and capture its actual coordinator observation."""
    # Existing raw guards remain exercised before fixture setup changes the record.
    try:
        service.open_action(episode, route_id, "raw-probe")
    except CommandInvalid as exc:
        assert str(exc) == "legacy action requires a journey command"
    else:
        raise AssertionError("raw action unexpectedly dispatched")
    if route_id != "fictional_provider":
        raise CommandInvalid("journey request uses the fixed booking route")
    attempts = service._store.list_attempts(episode)
    if binding is None and attempts:
        # Reuse the original exact durable command, never prepare a fresh retry.
        with service._store.journey_transaction(episode, write=False) as tx:
            rows = [row for row in tx.load_bundle(episode).commands
                    if row["kind"] == "request" and row["phase"] == "claimed"
                    and row["disposition_version"] == attempts[-1].disposition_version]
        if rows:
            binding = OperationBinding(**{name: rows[-1][name]
                for name in OperationBinding.__dataclass_fields__ if name != "token_schema"})
    if binding is None:
        seed_booking_history(service, episode)
        binding = prepared_binding(service, episode, "request")
    captured = []
    coordinator = service._coordinator
    execute = coordinator.execute_tool
    def capture(request, *, now_utc):
        result = execute(request, now_utc=now_utc)
        captured.append(result)
        return result
    coordinator.execute_tool = capture
    try:
        response = service.request_appointment(binding)
    finally:
        coordinator.execute_tool = execute
    attempt = service._store.list_attempts(episode)[-1]
    return ActionOutcome(episode, attempt.attempt_id, attempt.idempotency_key,
        attempt.route_id, binding.purpose, attempt.disposition_version,
        attempt.consent_version, attempt.execution, response.receipt.replayed,
        captured[0] if captured else None, service.available_origin, True)


def historical_attempt(service, episode, *, route_id="fictional_provider", purpose="historical-callback"):
    """Seed an old attempt row for callback guards. Does not dispatch a provider."""
    snapshot = service._store.load_snapshot(episode)
    return service._store.open_attempt_once(
        AttemptCommand(episode, route_id, purpose, snapshot.consent_version),
        derive_attempt_key(episode, route_id, purpose), now_utc=service._clock.now_utc())


@classified
def service_barrier(client, episode, *, json):
    outcome = service().record_barrier(episode, json["barrier_text"], json.get("proposed_route_id"))
    return dict(asdict(outcome), fixture_label=fixture.FIXTURE_LABEL)
