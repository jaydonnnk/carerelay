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
from carerelay.domain.models import OperationBinding
from carerelay.domain.rules import PolicyViolation
from carerelay.journey_commands import issue_operation, request_digest, PURPOSES
from carerelay.service import ServiceError, IntakeNotRecognised
from carerelay.state import EpisodeNotFound, RestatementNotFound, StateError, CLINICAL_SCOPE

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
        except (ServiceError, StateError) as exc:
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
    outcome = service().open_action(episode, json["route_id"], json["purpose_id"])
    body = asdict(outcome)
    body.pop("tool")
    body.update(execution=outcome.execution.value, origin=outcome.origin.value,
        outcome=outcome.tool.outcome.value if outcome.tool else None,
        provider_ref=outcome.tool.provider_ref if outcome.tool else None,
        payload=outcome.tool.payload if outcome.tool else None, fixture_label=fixture.FIXTURE_LABEL)
    return body


@classified
def service_barrier(client, episode, *, json):
    outcome = service().record_barrier(episode, json["barrier_text"], json.get("proposed_route_id"))
    return dict(asdict(outcome), fixture_label=fixture.FIXTURE_LABEL)
