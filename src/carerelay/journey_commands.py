"""Server-held, purpose-separated exact-request capabilities. No automatic retry."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import os
import threading
from collections.abc import Mapping
from dataclasses import asdict

from carerelay.domain.models import DispatchPermit, OperationBinding


_DISPATCH_PERMITS = {}
_PERMIT_LOCK = threading.Lock()


def _register_dispatch(binding, claim, attempt_key):
    """Only the newly claiming service path registers an original execution."""
    if not claim.newly_claimed or binding.kind != "request":
        raise CommandInvalid("replay has no dispatch authority")
    permit = DispatchPermit(binding.operation_id, attempt_key, claim.claim_revision)
    with _PERMIT_LOCK:
        _DISPATCH_PERMITS[id(permit)] = (permit, binding, os.getpid())
    return permit


def _consume_dispatch(permit):
    with _PERMIT_LOCK:
        registered = _DISPATCH_PERMITS.get(id(permit))
        if registered is None or registered[2] != os.getpid():
            raise CommandInvalid("dispatch permit is not original")
        del _DISPATCH_PERMITS[id(permit)]
    return registered[1]


def _discard_dispatch(permit):
    with _PERMIT_LOCK:
        _DISPATCH_PERMITS.pop(id(permit), None)

COMMAND_KINDS = (
    "create", "select_example", "readback_started", "confirm_words", "score_words",
    "repair_words", "show_plan", "hide_plan", "h3", "select_barrier", "grant_share",
    "decline_share", "revoke_share", "request", "supersede_extraction",
)
PURPOSES = {"create": "episode:create", "select_example": "episode:select_example"}
SAFE_INTEGER = 9007199254740991


class CommandInvalid(ValueError):
    """Malformed or unauthorised capability; never a clinical stop."""


class CommandConflict(ValueError):
    """A durable operation conflicts with its exact binding or current record."""


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CommandInvalid("duplicate key")
        result[key] = value
    return result


def canonical(value: object) -> bytes:
    def check(x: object) -> None:
        if x is None or type(x) in (str, bool, int):
            return
        if isinstance(x, dict) and all(type(k) is str for k in x):
            for v in x.values():
                check(v)
            return
        if isinstance(x, list):
            for v in x:
                check(v)
            return
        raise CommandInvalid("unsupported canonical value")
    check(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except ValueError as exc:
        raise CommandInvalid("invalid canonical UTF-8") from exc


def request_digest(kind: str, payload: Mapping[str, object]) -> str:
    if kind not in COMMAND_KINDS:
        raise CommandInvalid("unknown command")
    body = dict(payload)
    if kind == "create" and body != {}:
        raise CommandInvalid("create has no caller-selected persona")
    if kind == "select_example" and set(body) != {"example_id"}:
        raise CommandInvalid("invalid example payload")
    return hashlib.sha256(canonical({"schema": "carerelay-command-v1",
                                    "kind": kind, "payload": body})).hexdigest()


def validate_binding(binding: OperationBinding) -> None:
    if binding.token_schema != "carerelay-command-v1":
        raise CommandInvalid("unknown token schema")
    for name in ("operation_id", "episode_id"):
        value = getattr(binding, name)
        if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
            raise CommandInvalid("invalid identity")
    if type(binding.expected_revision) is not int or not 0 <= binding.expected_revision <= SAFE_INTEGER:
        raise CommandInvalid("invalid revision")
    if binding.disposition_version is not None and (
        type(binding.disposition_version) is not int or binding.disposition_version < 1
    ):
        raise CommandInvalid("invalid disposition")
    if binding.kind not in COMMAND_KINDS or not isinstance(binding.purpose, str) or not binding.purpose:
        raise CommandInvalid("invalid kind or purpose")
    if type(binding.body_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", binding.body_sha256):
        raise CommandInvalid("invalid body digest")
    for value in (binding.parent_restatement_id, binding.confirmation_id):
        if value is not None and (type(value) is not str or not 1 <= len(value) <= 128):
            raise CommandInvalid("invalid parent or confirmation")


def _key(signing_key: bytes) -> bytes:
    if not isinstance(signing_key, bytes) or not signing_key.strip():
        raise CommandInvalid("signing unavailable")
    return hmac.digest(signing_key, b"carerelay:command:v1", "sha256")


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def issue_operation(binding: OperationBinding, *, signing_key: bytes) -> str:
    validate_binding(binding)
    payload = _encode(canonical(asdict(binding)))
    return payload + "." + _encode(hmac.digest(_key(signing_key), payload.encode("ascii"), "sha256"))


def operation_identity(*, episode_id: str, kind: str, revision: int,
                       body_sha256: str, signing_key: bytes) -> str:
    """Read preparation has a stable identity for the same committed intent."""
    key = hmac.digest(_key(signing_key), b"carerelay:operation-identity:v1", "sha256")
    return hmac.digest(key, canonical({"episode_id": episode_id, "kind": kind,
        "revision": revision, "body_sha256": body_sha256}), "sha256").hex()


def verify_operation(token: str, *, signing_key: bytes) -> OperationBinding:
    try:
        if type(token) is not str or len(token) > 4096 or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token):
            raise CommandInvalid("invalid token")
        payload, signature = token.split(".")
        expected = _encode(hmac.digest(_key(signing_key), payload.encode("ascii"), "sha256"))
        if not hmac.compare_digest(signature, expected):
            raise CommandInvalid("invalid MAC")
        raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        if _encode(raw) != payload:
            raise CommandInvalid("noncanonical token")
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
        if not isinstance(body, dict) or set(body) != set(OperationBinding.__dataclass_fields__):
            raise CommandInvalid("invalid token fields")
        binding = OperationBinding(**body)
        validate_binding(binding)
        if canonical(body) != raw:
            raise CommandInvalid("noncanonical token body")
        return binding
    except (ValueError, TypeError, UnicodeError) as exc:
        raise CommandInvalid("invalid operation") from exc
