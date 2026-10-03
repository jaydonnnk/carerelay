"""One deterministic, local-only scripted provider. Slice 6.

`03-program-design.md` maps this file to "one deterministic, local-only scripted
provider port. Every response has `simulated: true`."

It occupies the position a clinic-side booking system would occupy. It is not
one, it contacts nothing, and every response says so in a field that travels with
the response rather than in a comment or a page heading. D11 is the reason: an
unlabelled simulated artefact is a false-completion path, because a surface that
renders it without the label is telling a reader that something happened in the
world when nothing did.

**Why the scripted outcome is a failure.** `02-architecture.md` section 5.1 step
6 pins the demo path: the adapter fails as scripted, the attempt becomes
`failed`, evidence stays `none`, and the clinical deadline is untouched. A
provider that succeeded would close the episode and leave the Closure Contract
nothing to show. Failure is the scripted fact here, not a defect and not a
fallback for one.

**The script is data, not a rule.** `ScriptedProvider` accepts a route-to-outcome
mapping so a later slice can script an acknowledgement for a fault sequence. The
default is `failed` for every route, because that is the one episode this
product demonstrates. Changing the script changes what the demo shows, so it is
carried explicitly rather than inferred.

**Determinism.** The response is a pure function of `(route_id, attempt_key)`.
No clock is read here (D5) and no random value is drawn, so the same two inputs
give the same response in a test, in a walkthrough and in the running demo. A
provider that varied between runs could not be asserted against.

**Origin, which is the load-bearing field.** `origin` says **where** an outcome
came from. This provider is `Origin.LOCAL_SIM`. A platform-backed adapter would
report `Origin.PLATFORM` in the same field, which is what makes the two
distinguishable by inspection, the property section 3.3 step 6 exists to
guarantee. Nothing here may report `platform`: no tool is executed through a
platform in this build, and claiming otherwise would be the exact softening
section 3.3 was written to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from carerelay.domain.models import ExecutionStatus, Origin, TERMINAL_TRANSITIONS

#: The reference a receipt carries for this provider. It is deliberately not a
#: URL, a facility name or a claim about a real service: it identifies the
#: simulator so the ledger can say which thing answered.
PROVIDER_REF = "simulated:local-only:carerelay-demo"


@dataclass(frozen=True)
class ProviderResponse:
    """One answer from the provider.

    `outcome` is restricted to a terminal transition. A provider that returned
    `attempted` or `not_started` would leave the attempt in flight forever with
    no row that says so, which is the state `02-architecture.md` section 4.1 was
    rewritten to make unrepresentable.
    """

    route_id: str
    attempt_key: str
    outcome: ExecutionStatus
    origin: Origin
    simulated: bool
    provider_ref: str
    message: str


class ProviderPort(Protocol):
    """The provider boundary, as section 3.3 needs it.

    `origin` is on the port rather than on the response factory so that the
    answer to "where did this come from" is a property of the implementation,
    not a value the caller can choose to supply.
    """

    simulated: bool
    origin: Origin

    def submit_request(self, route_id: str, attempt_key: str) -> ProviderResponse: ...


class ScriptedProvider(ProviderPort):
    """A deterministic scripted stand-in for a real provider.

    Two limits, stated rather than hidden:

    * **It never succeeds by default.** Every route resolves to `failed` unless
      the caller scripts otherwise. Success would close the episode.
    * **It holds no state.** It does not remember which attempts it has seen, so
      a repeated call returns the same answer. Idempotency is the attempt key's
      job (`02-architecture.md` section 4.1), not the provider's.
    """

    simulated = True
    origin = Origin.LOCAL_SIM

    def __init__(self, script: Mapping[str, ExecutionStatus] | None = None) -> None:
        """`script` maps a route id to the outcome the demo needs it to give.

        A terminal outcome outside `TERMINAL_TRANSITIONS` is refused at
        construction rather than at call time, so a bad script cannot produce a
        response that the store would then have to reject mid-episode.
        """
        self._script: dict[str, ExecutionStatus] = {}
        for route_id, outcome in (script or {}).items():
            if outcome not in TERMINAL_TRANSITIONS:
                raise ValueError(
                    f"route {route_id!r} is scripted to {outcome.value!r}, which is "
                    "not a terminal outcome; a provider answer must settle the "
                    f"attempt, so pick one of "
                    f"{sorted(member.value for member in TERMINAL_TRANSITIONS)}"
                )
            self._script[route_id] = outcome

    def submit_request(self, route_id: str, attempt_key: str) -> ProviderResponse:
        outcome = self._script.get(route_id, ExecutionStatus.FAILED)
        return ProviderResponse(
            route_id=route_id,
            attempt_key=attempt_key,
            outcome=outcome,
            origin=self.origin,
            simulated=self.simulated,
            provider_ref=PROVIDER_REF,
            message=(
                f"the simulated provider returned {outcome.value} for route "
                f"{route_id!r}; no real provider was contacted"
            ),
        )


__all__ = [
    "PROVIDER_REF",
    "ProviderPort",
    "ProviderResponse",
    "ScriptedProvider",
]
