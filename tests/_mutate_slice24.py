"""Slice 24 named mutations of the live ADP reservation guard. Each must turn its selector RED.

Run from the repository root with APP_DATABASE_URL unset. Prints RED, SURVIVED and
NOT PROVEN separately; every target is restored byte-exact and its cache purged.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD, EXTRACT, STATE = "src/carerelay/adp_guard.py", "src/carerelay/adp_extraction.py", "src/carerelay/state.py"
TESTS = ["tests/test_adp_guard.py"]
DEMO = ["tests/test_demo_scripted_reply.py"]
SERVICE, API = "src/carerelay/service.py", "src/carerelay/api.py"
M = [
    ("transport opens without a ticket", EXTRACT,
     'ticket = self.guard.claim(body.get("RequestId")) if self.guard is not None else None', "ticket = None", TESTS),
    ("reserve skipped (guard bypassed)", EXTRACT,
     "        ticket = None\n        if live:\n", "        ticket = None\n        if False:\n", TESTS),
    ("halt ignored", GUARD, '            if latest and latest[0][0] == "halt":\n                raise GuardRefused("guard_halted")\n', "", TESTS),
    ("unfinished ignored", GUARD, '            if run(_UNFINISHED)[0][0]:\n                raise GuardRefused("guard_unfinished")\n', "", TESTS),
    ("episode ceiling ignored", GUARD, '                raise GuardRefused("guard_episode_ceiling")\n', "                pass\n", TESTS),
    ("day ceiling ignored", GUARD, '                raise GuardRefused("guard_day_ceiling")\n', "                pass\n", TESTS),
    ("total ceiling ignored", GUARD, '                raise GuardRefused("guard_total_ceiling")\n', "                pass\n", TESTS),
    ("lock removed", STATE,
     'self._conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")\n            except sqlite3.OperationalError as exc:\n                raise LockContention("guard lock unavailable")',
     'self._conn.execute("BEGIN")\n            except sqlite3.OperationalError as exc:\n                raise LockContention("guard lock unavailable")', TESTS),
    ("failure never halts", GUARD, "            if outcome in HALTING_OUTCOMES:\n", "            if False:\n", TESTS),
    ("refusal halts", GUARD, 'HALTING_OUTCOMES = frozenset({"invalid", "timeout", "transport", "lost"})',
     'HALTING_OUTCOMES = frozenset({"invalid", "timeout", "transport", "lost", "refused"})', TESTS),
    ("finish skipped", EXTRACT, "            if ticket is not None:\n                try:\n                    guard.finish(",
     "            if False:\n                try:\n                    guard.finish(", TESTS),
    ("transmitted marked void", GUARD, 'outcome = "void" if not transmitted else', 'outcome = "void" if True else', TESTS),
    ("void counted", GUARD, "WHERE (o.outcome IS NULL OR o.outcome <> 'void')\")", "WHERE (1 = 1)\")", TESTS),
    ("late send after finish allowed", GUARD, '            if self.finished:\n                raise GuardRefused("guard_finished")\n', "", TESTS),
    ("zero-padded ceiling accepted", GUARD, ' or raw.startswith("0")', "", TESTS),
    ("in-memory database accepted", GUARD, 'getattr(store, "path", None) != ":memory:"', "True", TESTS),
    ("configured live path unguarded", EXTRACT, "HttpsReadbackTransport(guard=build_guard(config, store))", "HttpsReadbackTransport()", TESTS),
    ("missing guard sends", EXTRACT, '            if guard is None:\n                return result("not_sent", failure="guard_config")\n', "", TESTS),
    ("unbound kind accepted", GUARD, "AND c.kind IN ('score_words', 'repair_words') ", "", TESTS),
    ("completed claim accepted", GUARD, "AND NOT EXISTS (SELECT 1 FROM journey_commands d \"\n                        \"WHERE d.operation_id = c.operation_id AND d.phase = 'completed')",
     "\"\n                        \"", TESTS),
    ("second send for one operation", STATE, "    operation_id TEXT NOT NULL UNIQUE,\n    episode_id TEXT NOT NULL REFERENCES episodes(id),\n    sgt_day",
     "    operation_id TEXT NOT NULL,\n    episode_id TEXT NOT NULL REFERENCES episodes(id),\n    sgt_day", TESTS),
    ("guard table not append-only", STATE, '    "adp_guard_controls",\n)', ")", TESTS),
    ("operator reason optional", GUARD, "if type(reason) is not str or not 1 <= len(reason.strip()) <= 200:", "if type(reason) is not str:", TESTS),
    ("default changed", EXTRACT, 'if flag in {"", "false", "0"}:', 'if flag in {"", "false"}:', TESTS),
    ("scripted reply never sent", SERVICE, "        if self._scripted_provider_reply and receipt.state", "        if False and receipt.state", DEMO),
    ("scripted reply not failed", SERVICE, "SCRIPTED_REPLY_TRANSITION = ExecutionStatus.FAILED", "SCRIPTED_REPLY_TRANSITION = ExecutionStatus.ACKNOWLEDGED", DEMO),
    # Not a mutation: the per-attempt key is not load-bearing. The store records any second
    # terminal callback on a failed attempt as a duplicate (observed SURVIVED, 16 October 2026).
    ("scripted reply on everywhere", API, "    return (config.get(APP_ENV_ENV) or \"\").strip().casefold() in PUBLIC_ENVS", "    return True", DEMO),
]


def main() -> int:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "src")}
    env.pop("APP_DATABASE_URL", None)
    env.pop("ADP_EXTRACTION_ENABLED", None)
    rows = []
    for name, file, old, new, selectors in M:
        path = ROOT / file
        original = path.read_bytes()
        text = original.decode()
        if text.count(old) != 1:
            rows.append((name, f"NOT PROVEN (anchor count {text.count(old)})"))
            continue
        try:
            path.write_text(text.replace(old, new, 1))
            run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *selectors],
                                 cwd=ROOT, env=env, capture_output=True, text=True, timeout=600)
            rows.append((name, "RED" if run.returncode == 1 else "SURVIVED" if run.returncode == 0
                         else f"NOT PROVEN rc={run.returncode}"))
        finally:
            path.write_bytes(original)
            for cache in path.parent.glob(f"__pycache__/{path.stem}.*.pyc"):
                cache.unlink()
        assert path.read_bytes() == original
    for row in rows:
        print("%-36s %s" % row)
    red = sum(r[1] == "RED" for r in rows)
    survived = sum(r[1] == "SURVIVED" for r in rows)
    print(f"RED {red} of {len(rows)}, SURVIVED {survived}, NOT PROVEN {len(rows) - red - survived}")
    return 0 if red == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
