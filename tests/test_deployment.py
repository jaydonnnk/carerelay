"""Slice 7: the record must survive a restart, and the artefacts must be honest.

The first half is risk R8 in `04-slices.md`. The append-only guarantee rests on
two things: the triggers Slice 3 created, and the database being **the same
file** after a restart. A mounted disk that cannot hold SQLite's write-ahead log,
or a path that is not actually on the mount, turns that guarantee into a claim
the deployment does not have. This module proves the half that can be proven
locally: a real file, a real process boundary, and the record still there with its
triggers still refusing UPDATE and DELETE.

The second half checks the deployment artefacts for the two ways they can lie:
a secret value committed to the repository, and a database path that is not on
the persistent mount.

What this module cannot prove is stated at the bottom. Render's filesystem
behaviour is measured on Render, not here.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.demo import fixture  # noqa: E402
from carerelay.service import EpisodeService, ScenarioClock  # noqa: E402
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.state import APPEND_ONLY_TABLES, open_store  # noqa: E402
from carerelay.tools import McpTools  # noqa: E402
from carerelay.coordinator import LocalSimulationCoordinator  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
EPISODE = fixture.DEMO_EPISODE_ID

#: Run in a **fresh interpreter**, which is what a restart actually is. Reading
#: the file back with a second connection in the same process would prove nothing
#: about a deploy, because the process is the thing that died.
_REOPEN = r"""
import json, sqlite3, sys
path = sys.argv[1]
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row

tables = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table'")}
triggers = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'trigger'")}
journal = conn.execute("PRAGMA journal_mode").fetchone()[0]

expected_tables = json.loads(sys.argv[2])
missing_tables = sorted(set(expected_tables) - tables)
missing_triggers = sorted(
    f"{t}_no_{op}"
    for t in expected_tables
    for op in ("update", "delete")
    if f"{t}_no_{op}" not in triggers
)

dispositions = conn.execute(
    "SELECT version_no, action_id FROM dispositions WHERE episode_id = ?",
    (sys.argv[3],),
).fetchall()

# The triggers must still refuse, not merely exist. `RAISE(ABORT)` surfaces as
# `IntegrityError`, which is a subclass of `DatabaseError`, not of
# `OperationalError`; catching the narrow one would let this report "not refused"
# for a database whose triggers are perfectly intact.
refused = False
try:
    conn.execute("UPDATE dispositions SET action_id = 'tampered'")
except sqlite3.Error:
    refused = True

print(json.dumps({
    "missing_tables": missing_tables,
    "missing_triggers": missing_triggers,
    "journal": journal,
    "dispositions": [dict(r) for r in dispositions],
    "update_refused": refused,
}))
"""


def _write_a_real_record(path: Path) -> None:
    """Write through the service, not through raw SQL.

    A hand-written INSERT would prove that SQLite can persist a row. What needs
    proving is that the product's own write path leaves a record that a later
    process can read.
    """
    store = open_store(path, check_same_thread=False)
    try:
        service = EpisodeService(
            store,
            coordinator=LocalSimulationCoordinator(
                McpTools(store, policy=fixture.policy(), provider=ScriptedProvider())
            ),
            clock=ScenarioClock(fixture.SCENARIO_NOW_UTC),
            policy=fixture.policy(),
            display_tz=fixture.DISPLAY_TZ,
            disposition_factory=fixture.disposition,
            bound_complaint=fixture.BOUND_COMPLAINT,
            policy_provenance="test: provisional",
        )
        service.ensure_episode(EPISODE, "test persona")
        service.intake(EPISODE, fixture.BOUND_COMPLAINT)
    finally:
        store.close()


class TestTheRecordSurvivesAProcessRestart:
    """R8, the half that is provable without a deployment."""

    def test_the_disposition_is_readable_after_a_fresh_process(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)

        result = self._reopen(path)
        assert result["dispositions"], "the disposition did not survive the restart"
        assert result["dispositions"][0]["version_no"] == 1

    def test_every_append_only_table_is_still_there(self, tmp_path: Path) -> None:
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)
        result = self._reopen(path)
        assert result["missing_tables"] == [], (
            f"tables lost across the restart: {result['missing_tables']}"
        )

    def test_every_append_only_trigger_is_still_there(self, tmp_path: Path) -> None:
        """A table without its trigger is a mutable table with a hopeful name."""
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)
        result = self._reopen(path)
        assert result["missing_triggers"] == [], (
            f"triggers lost across the restart: {result['missing_triggers']}"
        )

    def test_the_triggers_still_refuse_an_update(self, tmp_path: Path) -> None:
        """The stronger form: not merely present, still enforcing."""
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)
        assert self._reopen(path)["update_refused"] is True

    def test_the_journal_mode_is_still_wal_after_the_restart(
        self, tmp_path: Path
    ) -> None:
        """WAL is a persistent property of the file, and R8 is about WAL.

        If a filesystem cannot hold the write-ahead log, this is the assertion
        that would fail first. It passes locally; that is evidence about SQLite,
        not about Render's disk, and the difference is recorded below.
        """
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)
        assert self._reopen(path)["journal"] == "wal"

    def test_the_wal_sidecar_is_written_beside_the_database(self, tmp_path: Path) -> None:
        """A mount that holds only the main file, not `DB-wal`, is a trap.

        SQLite needs the write-ahead log next to the database, so a deployment
        that syncs or snapshots a single file would lose committed transactions.
        The sidecar is checked while the connection is still open, because a
        clean close checkpoints and removes it, which is correct behaviour and
        not the thing being tested.
        """
        path = tmp_path / "carerelay.db"
        store = open_store(path, check_same_thread=False)
        try:
            store.create_episode(
                EPISODE, "test persona", now_utc=fixture.SCENARIO_NOW_UTC
            )
            assert path.with_name(path.name + "-wal").exists(), (
                "no WAL sidecar beside the database: this filesystem cannot hold "
                "SQLite in WAL mode"
            )
        finally:
            store.close()

    def _reopen(self, path: Path) -> dict:
        import json

        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                _REOPEN,
                str(path),
                json.dumps(list(APPEND_ONLY_TABLES)),
                EPISODE,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert completed.returncode == 0, completed.stderr
        return json.loads(completed.stdout.strip().splitlines()[-1])


class TestTheDeploymentArtefactsAreHonest:
    """The two ways `render.yaml` and the `Dockerfile` can quietly lie."""

    def test_the_dockerfile_exists(self) -> None:
        assert (REPO / "Dockerfile").exists()

    def test_the_render_definition_exists(self) -> None:
        assert (REPO / "render.yaml").exists()

    def test_the_database_path_is_on_the_persistent_mount(self) -> None:
        """The single most expensive mistake available in this slice.

        `APP_DATABASE_URL` outside the mount path means the record is lost on
        every redeploy while the configuration looks fine. The mount path and
        the database path are read from the same file and compared, so drifting
        one cannot go unnoticed.
        """
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        assert "mountPath: /var/data" in text
        assert "value: /var/data/carerelay.db" in text, (
            "APP_DATABASE_URL is not under the disk mount path: the record would "
            "be lost on every redeploy while the config looked correct"
        )

    def test_the_token_is_not_in_the_repository(self) -> None:
        from test_boundaries import SECRET_MARKERS, scan_for_secrets

        victims = [
            REPO / "render.yaml",
            REPO / "Dockerfile",
            REPO / ".dockerignore",
            REPO / "pyproject.toml",
        ]
        for path in victims:
            assert path.exists(), path
            found = scan_for_secrets(path.read_text(encoding="utf-8"))
            assert found == [], f"{path.name} carries a secret-shaped value: {found}"

    def test_the_token_is_declared_without_a_value(self) -> None:
        """`sync: false` is Render's way of saying "set this in the dashboard"."""
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        assert "CARERELAY_API_TOKEN" in text
        assert "sync: false" in text

    def test_the_public_environment_is_declared(self) -> None:
        """`APP_ENV=public` is what arms auth without a second flag."""
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        assert "key: APP_ENV" in text
        assert "value: public" in text

    def test_cors_names_an_origin_and_not_a_wildcard(self) -> None:
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        assert "CORS_ORIGINS" in text
        assert "value: *" not in text

    def test_the_dockerignore_excludes_local_databases_and_evidence(self) -> None:
        """A local `.sqlite3` in the image would overwrite nothing but would be
        published, and the record in it is real clinical-shaped data."""
        text = (REPO / ".dockerignore").read_text(encoding="utf-8")
        for pattern in ("*.sqlite3", "submission/", ".env"):
            assert pattern in text, f".dockerignore does not exclude {pattern}"


# ---------------------------------------------------------------------------
# What this module does not prove
# ---------------------------------------------------------------------------
#
# Everything above runs on the local filesystem. It proves that SQLite, this
# schema and this service leave a record that a fresh process can read, with the
# triggers still enforcing, under WAL. It does **not** prove that Render's
# mounted disk behaves the same way. [hypothesis] Render's disks are SSD block
# storage, and WAL needs `mmap` and two sidecar files beside the database, which
# ordinary block storage provides; but the claim is measured on the deployment,
# not here. `04-slices.md` risk R8 stays open until the record has been read back
# on Render after a restart *and* after a redeploy, and the honest fallback if it
# fails is `journal_mode = DELETE` stated as a fallback, not applied quietly.
