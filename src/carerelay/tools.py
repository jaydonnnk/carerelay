"""The MCP tool surface. Slice 6.

`02-architecture.md` section 3.2 names three tools, cut from six under the
corrected cut order: `get_episode`, `submit_simulated_request` and
`record_evidence`. All three recheck authorisation, consent and the attempt key
**server side**, and all three carry the simulated label on their response.

**Why the recheck exists at all.** The tool is the last gate before something
touches the world. A caller that has already been authorised once is not thereby
authorised forever: consent can be revoked while an attempt is in flight, and the
attempt key is the only proof that this episode opened this attempt. Checking at
the boundary where the request arrives and nowhere else is the pattern that
section 4.1 was rewritten to forbid.

**What "authorisation" means here, stated exactly.** There is no end-user
credential at this slice. The shared bearer token lands with the deployment in
Slice 7 (D13), and pretending to have it now would be a claim the code does not
support. What a tool can enforce today is the only authorisation the product
actually has: that the route is one this episode's policy permits, and that the
attempt key names an attempt this episode opened. A tool that skipped either
would dispatch to a route the plan does not contain.

**Refusals are recorded, then raised.** Every refusal writes an event first, so
the ledger can show that the episode stopped and why. Raising alone would leave
a reader to guess whether a request was never made or was dropped.

**Origin, and the one claim this module refuses to make.** `submit_simulated_request`
returns the origin its provider reports. In this build that is
`Origin.LOCAL_SIM`, because the provider is `ScriptedProvider` and no tool is
executed through a platform. Gate A proved on 2 October 2026 that ADP's transport
carries an origin signal; it did **not** prove tool execution, and
`02-architecture.md` D8 says ADP may occupy the interpretation step only and
cannot carry the section 3.3 claim. This module therefore reports `local-sim`
and says so. Reporting `platform` here would be the precise softening section 3.3
exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from carerelay.domain import rules
from carerelay.domain.models import (
    EpisodeSnapshot,
    EvidenceLevel,
    EvidenceRecord,
    ExecutionStatus,
    Origin,
    PolicyFixture,
)
from carerelay.simulated_provider import ProviderPort
from carerelay.state import EpisodeStore


class ToolError(Exception):
    """Base class for a tool that refuses to proceed."""


class RouteNotPermitted(ToolError):
    """The route is not one this episode's policy permits."""


class UnknownAttemptKey(ToolError):
    """The attempt key does not name an attempt this episode opened."""


@dataclass(frozen=True)
class EpisodeBrief:
    """What `get_episode` returns: the scoped facts an executor may see.

    It is a projection over app-owned state, not a row, and it omits what an
    executor has neither need of nor right to: the patient's restatement, the
    transcript, the hint history, the dwell times. Handing an executor the
    patient's own words would widen the surface for no purpose, because
    execution needs the route and the key and nothing else.
    """

    episode_id: str
    policy_version: str
    disposition_version: int | None
    permitted_route_ids: tuple[str, ...]
    fallback_route_id: str | None
    consent_version: int | None
    simulated: bool


@dataclass(frozen=True)
class ToolResult:
    """What one tool call asserts back to the caller.

    `origin` is the field section 3.3 step 6 turns on: it says **where** the
    outcome came from, so a local simulation cannot be displayed as a platform
    failure and the two stay distinguishable by inspection.
    """

    route_id: str
    attempt_key: str
    outcome: ExecutionStatus
    origin: Origin
    simulated: bool
    provider_ref: str
    payload: str


class McpTools:
    """The three tools, over one store, one policy and one provider.

    The provider is injected rather than imported so a test can supply one whose
    `origin` differs, which is exactly what the Slice 6 Check needs: the same
    path rendering two origins that a reader can tell apart.
    """

    def __init__(
        self,
        store: EpisodeStore,
        *,
        policy: PolicyFixture,
        provider: ProviderPort,
    ) -> None:
        self._store = store
        self._policy = policy
        self._provider = provider

    @property
    def origin(self) -> Origin:
        """The origin every result from this surface will carry."""
        return self._provider.origin

    # -- tool 1 ------------------------------------------------------------

    def get_episode(self, episode_id: str, *, now_utc: datetime) -> EpisodeBrief:
        """The scoped snapshot an executor may look at.

        Requires the episode to exist and consent to be currently granted. A
        reader with no consent gets no clinical facts, including the deadline,
        which is the one fact this product exists to protect.
        """
        snapshot = self._store.load_snapshot(episode_id)
        self._recheck_consent(episode_id, "get_episode", now_utc)
        return _brief(episode_id, snapshot, self._policy)

    # -- tool 2 ------------------------------------------------------------

    def submit_simulated_request(
        self, episode_id: str, route_id: str, attempt_key: str, *, now_utc: datetime
    ) -> ToolResult:
        """Dispatch one request to the simulated provider.

        Three rechecks, in this order, each recorded before it is raised:

        1. **authorisation**: the route must be one the policy permits.
        2. **the attempt key**: it must name an attempt this episode opened, and
           that attempt's route must be the route being dispatched to. A key
           borrowed from another route would let a caller open one attempt and
           spend it on a different one.
        3. **consent**: current and granted, re-checked at execution time rather
           than trusted from the moment the attempt was opened.
        """
        try:
            rules.validate_route(route_id, self._policy.permitted_route_ids)
        except rules.PolicyViolation as exc:
            self._refuse(
                episode_id,
                "submit_simulated_request",
                f"route={route_id} reason={exc}",
                now_utc,
            )
            raise RouteNotPermitted(str(exc)) from exc

        attempt = self._store.get_attempt_by_key(attempt_key)
        if attempt is None:
            self._refuse(
                episode_id,
                "submit_simulated_request",
                f"route={route_id} reason=no attempt opened under this key",
                now_utc,
            )
            raise UnknownAttemptKey(
                f"no attempt was opened under key {attempt_key!r}; the key is "
                "generated by the server, so a caller cannot invent one"
            )
        if attempt.route_id != route_id:
            self._refuse(
                episode_id,
                "submit_simulated_request",
                f"route={route_id} reason=key belongs to route {attempt.route_id}",
                now_utc,
            )
            raise UnknownAttemptKey(
                f"key {attempt_key!r} opened an attempt on route "
                f"{attempt.route_id!r}, not on {route_id!r}"
            )

        self._recheck_consent(episode_id, "submit_simulated_request", now_utc)

        response = self._provider.submit_request(route_id, attempt_key)
        return ToolResult(
            route_id=response.route_id,
            attempt_key=response.attempt_key,
            outcome=response.outcome,
            origin=response.origin,
            simulated=response.simulated,
            provider_ref=response.provider_ref,
            payload=response.message,
        )

    # -- tool 3 ------------------------------------------------------------

    def record_evidence(
        self, episode_id: str, record: EvidenceRecord, *, now_utc: datetime
    ) -> EvidenceLevel:
        """Append one evidence row. Consent is rechecked before the write.

        D11 still governs what may be recorded: the store refuses a `documented`
        row that is simulated or unsourced, so a scripted 200 cannot close care.
        """
        self._recheck_consent(episode_id, "record_evidence", now_utc)
        self._store.record_evidence(episode_id, record, now_utc=now_utc)
        return record.level

    # -- internals ---------------------------------------------------------

    def _recheck_consent(
        self, episode_id: str, surface: str, now_utc: datetime
    ) -> None:
        """Consent must be current and granted at the moment of the call."""
        try:
            self._store.require_granted_consent(episode_id)
        except Exception as exc:  # noqa: BLE001 - re-raised, never swallowed
            self._refuse(episode_id, surface, f"reason={exc}", now_utc)
            raise

    def _refuse(
        self, episode_id: str, surface: str, reason: str, now_utc: datetime
    ) -> None:
        """Write the evidence that the episode stopped, then let the caller raise.

        A refusal that never reaches the record is indistinguishable from a
        request that was never made, and the ledger exists to tell those apart.
        """
        self._store.record_refusal(
            episode_id, surface=surface, reason=reason, now_utc=now_utc
        )


def _brief(
    episode_id: str, snapshot: EpisodeSnapshot, policy: PolicyFixture
) -> EpisodeBrief:
    """`EpisodeSnapshot` carries no episode id of its own, so it is passed in."""
    disposition = snapshot.disposition
    return EpisodeBrief(
        episode_id=episode_id,
        policy_version=policy.version,
        disposition_version=disposition.version if disposition is not None else None,
        permitted_route_ids=tuple(sorted(policy.permitted_route_ids)),
        fallback_route_id=(
            disposition.fallback_route_id if disposition is not None else None
        ),
        consent_version=snapshot.consent_version,
        simulated=True,
    )


__all__ = [
    "EpisodeBrief",
    "McpTools",
    "RouteNotPermitted",
    "ToolError",
    "ToolResult",
    "UnknownAttemptKey",
]
