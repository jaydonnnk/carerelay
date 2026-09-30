"""The pure domain core: policy and rules, and nothing else.

D2 of `02-architecture.md` makes the trust boundary a module boundary. This
package imports **no** network, **no** SDK, **no** database, **no** filesystem and
**no** wall clock. That is not a convention held by discipline: the check in
`tests/test_boundaries.py` fails the build when a forbidden import or call
appears anywhere under `domain/`.

The rule the package exists to enforce is the one in `AGENTS.md`: **the model
interprets, code decides.** A coordinator may propose a value. Only these rules
may turn a proposal into a decision.
"""

from __future__ import annotations

__all__: list[str] = []
