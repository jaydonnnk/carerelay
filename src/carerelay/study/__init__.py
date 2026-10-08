"""The Gate B study instrument. Slice 9.

The comparison the whole project is staked on runs here: the frozen allocation,
one row per dyad, the pre-registered scoring rules, the cut rule and the
reporting rules. It is a research instrument, so it sits beside the product and
not inside it: nothing in this package is reachable from a patient surface.

Three boundaries the package holds:

* `scoring` turns a response into correct, incorrect, or a refusal for the second
  scorer. It never guesses, and it never sees which condition the response came
  from.
* `outcomes` owns the row, the allocation, the cut rule and the reporting rules.
  It refuses to apply the cut rule while a row is unresolved or while the two
  conditions are not the same size.
* `sheet` is the only module here that touches the filesystem, and the sheet it
  writes is a plain file rather than a table, because protocol section 4
  requires the study data to be destroyed 30 days after submission.
"""

from __future__ import annotations

__all__: list[str] = []
