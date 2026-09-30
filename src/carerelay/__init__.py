"""CareRelay — patient-facing self-triage and care navigation.

A labelled research demonstration. It is not a clinical device, not a diagnostic
tool, and not validated for patient use. See `docs/PLAN.md` and `docs/CHALLENGE_REQUIREMENTS_JUDGING.md`.

The architectural rule that governs this package: **the model interprets, code
decides.** `domain` is pure and imports no I/O; the coordinator proposes values
and `domain` validates them before anything can cause an action.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
