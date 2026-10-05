"""Slice 7: the record must survive a restart, and the artefacts must be honest.

**Rewritten at Slice 7b, not ported.** This module used to prove three facts about
a SQLite file on Render's mounted disk: that a fresh process reads the record back,
that the triggers still refuse, and that the file is in WAL mode with its sidecar
beside it. The third of those is now meaningless and has been **deleted rather than
faked**: with the record in Postgres there is no `-wal` file, and asserting one
would have meant keeping a test that passes for a reason that no longer exists.

What replaced it is a different question, because the risk changed shape.

* **Before:** the container filesystem was ephemeral, so the risk was that the
  disk would not hold the database. The proof was about a *file* surviving.
* **Now:** the record is on a remote database, so the risk is that a new process
  does not reach the same database, or that the guarantee is a property of the
  connection rather than of the server. The proof is about *two separate
  interpreters* agreeing on rows that neither of them wrote in memory.

The persistence claim therefore rests on something stronger than before: a redeploy
replaces the container filesystem entirely, and a record that was never on it
cannot be lost with it. `04-slices.md` risk R8 is closed by the move, not by a
measurement, and the measurement below is what shows the move happened.

**Two halves, deliberately.** The SQLite half is kept, because the local demo and
the whole test suite still run on SQLite and a restart proof is cheap. It is
labelled as what it is: a property of the local path, not of the deployment.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from carerelay.demo import fixture  # noqa: E402
from carerelay.postgres_store import probe_dsn  # noqa: E402
from carerelay.service import EpisodeService, ScenarioClock  # noqa: E402
from carerelay.simulated_provider import ScriptedProvider  # noqa: E402
from carerelay.state import APPEND_ONLY_TABLES, open_store  # noqa: E402
from carerelay.tools import McpTools  # noqa: E402
from carerelay.coordinator import LocalSimulationCoordinator  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
EPISODE = fixture.DEMO_EPISODE_ID
SRC = str(REPO / "src")


def _dsn() -> str:
    """The DSN this module's engine-gated tests use.

    **It falls back to the store's own default rather than returning `None`,** and
    that is a correction, not a convenience. Gating on `CARERELAY_TEST_DSN` alone
    meant that on a machine with the local container up and no environment
    variable set, 40 of this project's 42 Postgres-gated tests ran and the two
    below skipped, because the other two Postgres modules gate on `probe_dsn()`,
    which has always had the fallback. R8 is the risk this class exists to close,
    so the one proof that matters most was the one that silently did not run on
    the project's documented default engine.

    The skip reason it produced was also false. It said "no Postgres reachable at
    `CARERELAY_TEST_DSN`" while a Postgres was reachable on `DEV_DSN`'s port and
    the rest of the suite was talking to it. A skip whose reason misdescribes why
    it skipped is worse than no skip, because it sends the next reader to debug
    the wrong thing.
    """
    return probe_dsn()


def _reachable() -> bool:
    try:
        import psycopg

        with psycopg.connect(_dsn(), connect_timeout=2):
            return True
    except Exception:
        return False


requires_postgres = pytest.mark.skipif(
    not _reachable(),
    reason=(
        "no Postgres reachable at CARERELAY_TEST_DSN, nor at the DEV_DSN default "
        "this module falls back to. The persistence proof is the whole point of "
        "this class, so it skips with a reason rather than reporting green "
        "without an engine. The docker run recipe is in the module docstring of "
        "tests/test_postgres_store.py, and its port is derived from DEV_DSN."
    ),
)


# -- what the image installs, and what src/ imports -------------------------

#: Import roots in `src/` that are satisfied without a line of their own in
#: `pyproject.toml`, each with the reason it is safe to omit one.
#:
#: An entry here is a decision, and the reason is the record of it. `starlette` is
#: imported directly by `api.py` for its middleware and exception types; declaring
#: it as well would create a second source of truth for a version `fastapi`
#: already pins, and the two could drift into an unsatisfiable install.
_SATISFIED_WITHOUT_A_DECLARATION = {
    "starlette": (
        "a hard requirement of the declared `fastapi`, so the resolver supplies it"
    ),
}

#: Declared distributions that `src/` never imports, each with the reason. The
#: control test needs this, because "nothing undeclared" is trivially true of an
#: empty dependency list and the interesting failure is a declaration deleted by
#: someone tidying up.
_INSTALLED_NOT_IMPORTED = {
    "uvicorn": "the container's CMD; it is executed, never imported",
}


def _distribution_name(requirement: str) -> str:
    """A requirement string reduced to the name pip compares.

    Extras and version specifiers are dropped and the three separators PEP 503
    treats as equivalent are folded together, so `psycopg[binary]>=3.3` and an
    import root of `psycopg` meet on the same string.
    """
    return re.split(r"[\[<>=!~;\s]", requirement, maxsplit=1)[0].lower().replace("_", "-")


def _declared_runtime_distributions() -> set[str]:
    """The names the deployed image actually gets.

    Only `project.dependencies`, and not the `test` extra: the Dockerfile runs
    `pip install --no-cache-dir .` with no extras, so a name declared under
    `[project.optional-dependencies]` is not present in the image and cannot
    satisfy an import in `src/`.
    """
    data = tomllib.loads((REPO / "pyproject.toml").read_bytes().decode("utf-8"))
    requirements = data.get("project", {}).get("dependencies", [])
    assert requirements, (
        "pyproject.toml declares no runtime dependencies at all, so this check "
        "would pass against an image that could import nothing"
    )
    return {_distribution_name(item) for item in requirements}


def _src_module_scope_imports() -> dict[str, set[str]]:
    """Every third-party root imported at module scope under `src/`, by file.

    Module scope only, because that is what runs when a container first imports
    the package. `state.py` imports `postgres_store` lazily inside `open_store`
    so a SQLite-only process never needs `psycopg`, and a function-level scan
    would report that as a startup dependency it is not.
    """
    found: dict[str, set[str]] = {}
    for path in sorted((REPO / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                # The stdlib check runs on the **raw** root and the distribution
                # fold runs after it, and that order is load-bearing. Folding
                # first turns `__future__` into `--future--`, which is in no
                # stdlib list and no dependency list, so every module carrying
                # `from __future__ import annotations` was reported as an
                # undeclared dependency. Found on this test's first run.
                if root in sys.stdlib_module_names or root == "carerelay":
                    continue
                found.setdefault(_distribution_name(root), set()).add(
                    path.relative_to(REPO).as_posix()
                )
    return found


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

#: The remote half: one interpreter writes through the product's own store, and
#: is then **gone**. Nothing is passed to the reader but an episode id.
_WRITE_REMOTE = r"""
import sys
sys.path.insert(0, sys.argv[1])
from datetime import datetime, timezone
from carerelay.domain.models import Disposition, DispositionSource
from carerelay.state import open_store

source_root, dsn, episode = sys.argv[1], sys.argv[2], sys.argv[3]
now = datetime(2026, 10, 1, 4, 0, tzinfo=timezone.utc)
deadline = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)

store = open_store(dsn)
store.create_episode(episode, "fictional older adult", now_utc=now)
store.register_policy_version(
    "fixture-provisional-0",
    content="{}",
    provenance="provisional non-clinical placeholder, authored rather than sourced",
    approved_by=None,
    now_utc=now,
)
store.insert_disposition(
    Disposition(
        episode_id=episode,
        version=1,
        policy_version="fixture-provisional-0",
        action_id="attend_same_day_review",
        clinical_deadline_utc=deadline,
        next_owner_id="patient",
        fallback_route_id="nurse_line",
        source=DispositionSource.FIXTURE,
    ),
    now_utc=now,
)
store.close()
print("written")
"""

#: A second interpreter, which has no memory of the first one. It opens its own
#: connection and asks for the record. This is the whole proof: if the row is
#: here, it was on the server and not in the process that wrote it.
_READ_REMOTE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import psycopg
from carerelay.state import open_store

source_root, dsn, episode = sys.argv[1], sys.argv[2], sys.argv[3]

store = open_store(dsn)
rows = store.list_dispositions(episode)
store.close()

# The triggers must still enforce on the server, not merely exist in the schema.
# The UPDATE names the episode so a row is actually matched: a row-level trigger
# fires per row, and `WHERE false` would report "not refused" for a database
# whose guards are intact.
conn = psycopg.connect(dsn)
update_refused = False
try:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE dispositions SET action_id = 'tampered' WHERE episode_id = %s",
            (episode,),
        )
except psycopg.errors.RestrictViolation:
    update_refused = True
finally:
    conn.rollback()
    conn.close()

print(json.dumps({
    "versions": [row.version for row in rows],
    "action_ids": [row.action_id for row in rows],
    "update_refused": update_refused,
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


class TestTheRecordSurvivesAProcessRestartOnTheLocalFile:
    """The SQLite half. A property of the local path, not of the deployment.

    The local demo, the whole test suite and the reviewer who clones the
    repository all run on SQLite, so this is still worth proving. What it no
    longer is: the deployment's persistence claim. That moved to the class below,
    and the label matters because a green test whose reason has expired is worse
    than no test.
    """

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
        """WAL is a persistent property of the SQLite file.

        **This is no longer a deployment claim.** It used to be the assertion that
        would fail first if Render's disk could not hold a write-ahead log, and
        the sidecar test that proved the harder half of that sat next to it. With
        the record in Postgres the deployment has no write-ahead log on the
        container at all, so this now says something about the local path and
        nothing about Render. It is kept because WAL is still what the local
        store is opened in, and a silent fall back to `DELETE` mode would be a
        real regression here.
        """
        path = tmp_path / "carerelay.db"
        _write_a_real_record(path)
        assert self._reopen(path)["journal"] == "wal"

    def _reopen(self, path: Path) -> dict:
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


@requires_postgres
class TestTheRecordSurvivesAProcessRestartOnTheServer:
    """R8, as it now stands: the record is on the server, not in the process.

    **Why "the server" and not "the remote database", which is what this class
    was called until 5 October 2026.** The property under test is that a separate
    database process holds the record, and the local container this suite reaches
    by default is exactly that: another process, another filesystem, nothing
    shared with the writer. "Remote" described where the engine happened to be
    rather than what is being proved, and once `_dsn()` gained its fallback the
    name would have been false on every run that used the default. When
    `CARERELAY_TEST_DSN` names Supabase the class proves it there too, and the
    difference is a network path, not a property.

    **Why two subprocesses and not two connections.** Two connections in one
    interpreter share memory, a driver cache and any in-flight transaction, which
    is exactly the state a redeploy destroys. The writer process exits before the
    reader starts, so the only thing that can carry the record between them is
    the database server itself.

    **What this does not need any more.** It does not check a mount path, a
    sidecar file or a journal mode. Those were the shape the risk took when the
    record was a file, and asserting them now would be theatre.

    **The trigger check is on the server too.** A record that survives but can be
    altered is not the product's claim, so the second process does not stop at
    reading the rows: it tries to change one and requires the refusal.
    """

    def test_a_disposition_written_by_one_process_is_read_by_another(self) -> None:
        import uuid

        episode = f"ep-remote-{uuid.uuid4().hex[:12]}"
        self._run(_WRITE_REMOTE, episode)
        result = self._run(_READ_REMOTE, episode)
        assert result["versions"] == [1], (
            "the disposition did not survive: the reader process, which shares "
            "nothing with the writer, found no row"
        )
        assert result["action_ids"] == ["attend_same_day_review"]

    def test_the_triggers_still_refuse_in_the_reading_process(self) -> None:
        """The refusal is a property of the server, not of the writer's session."""
        import uuid

        episode = f"ep-remote-{uuid.uuid4().hex[:12]}"
        self._run(_WRITE_REMOTE, episode)
        result = self._run(_READ_REMOTE, episode)
        assert result["update_refused"] is True, (
            "a fresh process could UPDATE a disposition, so the append-only "
            "guarantee did not survive the move to Postgres"
        )

    def _run(self, program: str, episode: str) -> dict:
        env = dict(os.environ)
        env["PYTHONPATH"] = SRC
        completed = subprocess.run(
            [sys.executable, "-c", program, SRC, _dsn(), episode],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            env=env,
        )
        assert completed.returncode == 0, completed.stderr
        last = completed.stdout.strip().splitlines()[-1]
        if last == "written":
            return {}
        return json.loads(last)


class TestTheDeploymentArtefactsAreHonest:
    """The ways `render.yaml` and the `Dockerfile` can quietly lie."""

    def test_the_dockerfile_exists(self) -> None:
        assert (REPO / "Dockerfile").exists()

    def test_the_render_definition_exists(self) -> None:
        assert (REPO / "render.yaml").exists()

    def test_the_database_url_is_declared_without_a_value(self) -> None:
        """The DSN carries a password, so it cannot be in this repository.

        `sync: false` is Render's way of saying "set this in the dashboard". This
        replaced an assertion that the path was under the disk mount, which was
        the right check when the database was a file and would now be a check
        for a deployment that no longer exists.
        """
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        assert "key: APP_DATABASE_URL" in text
        assert "sync: false" in text
        for marker in ("value: /var/data", "carerelay.db", "sqlite"):
            assert marker not in text.lower(), (
                f"render.yaml still names a local database file ({marker!r}), so "
                "the deployment would put the record back on an ephemeral "
                "filesystem while this test claimed otherwise"
            )

    def test_the_deployment_names_a_postgres_target(self) -> None:
        """The scheme is what selects the engine, so the DSN has to be a secret.

        `api._open_store` dispatches on `postgresql://`. A DSN set in the
        dashboard is invisible to this repository, so what can be checked here is
        the declaration's *shape*: `APP_DATABASE_URL` must be present, must carry
        `sync: false`, and must carry no `value:`. Asserting only that the word
        "postgres" appears somewhere in the file would pass on a comment saying
        the opposite, which is what this replaced.
        """
        text = (REPO / "render.yaml").read_text(encoding="utf-8")
        lines = text.splitlines()
        starts = [
            index
            for index, line in enumerate(lines)
            if line.strip() == "- key: APP_DATABASE_URL"
        ]
        assert len(starts) == 1, (
            f"APP_DATABASE_URL is declared {len(starts)} times in render.yaml"
        )
        block: list[str] = []
        for line in lines[starts[0] + 1 :]:
            stripped = line.strip()
            if stripped.startswith("- key:") or (stripped and not line.startswith(" ")):
                break
            block.append(stripped)
        assert "sync: false" in block, (
            f"APP_DATABASE_URL is not marked sync: false; its block is {block}. "
            "A DSN carries a password and must be set in the dashboard, not here."
        )
        assert not any(entry.startswith("value:") for entry in block), (
            f"APP_DATABASE_URL carries a value in the repository: {block}"
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

    def test_the_wal_sidecar_assertion_is_gone_rather_than_faked(self) -> None:
        """The one thing this rewrite must not do.

        The deleted test asserted a `-wal` file beside the database. With the
        record in Postgres there is no such file, and the two ways to make that
        test pass again are both dishonest: create a file the deployment has no
        use for, or drop the assertion and leave the name. This asserts the
        assertion is absent, so the temptation is recorded as a failure.
        """
        text = (REPO / "tests" / "test_deployment.py").read_text(encoding="utf-8")
        # The needle is assembled rather than written as one literal: this test
        # has to name what it is looking for, and a literal would match itself
        # and fail on its own source. That is not a trick, it is the one way a
        # file can assert the absence of something it must also mention.
        needle = "    def test_the_" + "wal_sidecar_is_written_beside_the_database"
        assert needle not in text, (
            "the deleted sidecar test is back; it cannot pass honestly on a "
            "deployment with no write-ahead log"
        )
        offenders = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith("assert") and "-wal" in line
        ]
        assert offenders == [], (
            f"a WAL sidecar assertion is back: {offenders}. The deployment has "
            "no write-ahead log on the container any more; see the module "
            "docstring before restoring anything like this."
        )

    def test_every_import_in_src_is_a_declared_dependency(self) -> None:
        """The image installs `pyproject.toml` and nothing else.

        **The defect this exists for, and it was live on `main`.** Slice 7b put
        `import psycopg` at module scope in `postgres_store.py` and pointed
        `render.yaml` at a `postgresql://` DSN, but never declared the driver. The
        Dockerfile runs `pip install --no-cache-dir .`, so the deployed image had
        no `psycopg` in it, and the first request that made `open_store` see a
        Postgres scheme would have died with `ModuleNotFoundError`. Observed by
        blocking the import and calling `open_store("postgresql://...")`: the
        SQLite path opens fine and the Postgres path raises. Every test stayed
        green throughout, because no test builds the image and every development
        machine had the driver installed for the local container.

        **Why module scope only.** A function-level import is reached only on a
        path a given deployment may never take, and `state.py` imports
        `postgres_store` lazily *on purpose*, so a SQLite-only process does not
        need the driver. Module scope is what executes when the package is first
        imported, which is what a container does at startup.

        **What this does not prove.** It compares import roots to declared
        distribution names, which works only where the two are spelled alike. They
        are for everything in `src/` today; a dependency whose import name differs
        from its distribution name (`PIL` from `Pillow`) would need an entry in
        `_SATISFIED_WITHOUT_A_DECLARATION` below with its reason, and adding one
        is a decision that has to be written down. It also says nothing about
        whether a declared version floor is satisfiable, or about the `test`
        extra, which the image does not install.
        """
        declared = _declared_runtime_distributions()
        undeclared = [
            f"{module} (imported at module scope by {', '.join(sorted(files))})"
            for module, files in sorted(_src_module_scope_imports().items())
            if module not in declared and module not in _SATISFIED_WITHOUT_A_DECLARATION
        ]
        assert undeclared == [], (
            "the image installs only what `pyproject.toml` declares, so these "
            f"would fail at container startup: {undeclared}"
        )

    def test_the_exemption_lists_do_not_outlive_the_dependencies_they_excuse(self) -> None:
        """The control for the test above, so it cannot pass by declaring less.

        A guard that only ever asks "is anything imported but undeclared?" is
        satisfied by an empty dependency list, and the mutation worth fearing is
        someone tidying `pyproject.toml` while the suite stays green.

        **This test's first version did not work, and the mutation check is what
        showed it.** It asserted that nothing was declared without being
        imported, exempting `_INSTALLED_NOT_IMPORTED`. Deleting `uvicorn` from
        `pyproject.toml` therefore changed nothing: the name left `declared` and
        the exemption was never consulted, so the assertion still held. An
        exemption list makes a check blind to exactly the entries it excuses,
        which is why the exemption has to be asserted *present* as well. Measured
        after the fix: deleting `uvicorn` turns this RED while the guard above
        stays GREEN, and deleting `psycopg` turns the guard RED while this stays
        GREEN, so the two are discriminating and not merely both fail-capable.
        """
        declared = _declared_runtime_distributions()
        imported = set(_src_module_scope_imports())

        stale_exemptions = sorted(
            name
            for name in _INSTALLED_NOT_IMPORTED
            if _distribution_name(name) not in declared
        )
        assert stale_exemptions == [], (
            f"exempted from the import check but not declared at all: "
            f"{stale_exemptions}. Either the declaration was deleted, which the "
            "image would notice at startup, or the exemption is stale and should "
            "come out of `_INSTALLED_NOT_IMPORTED`."
        )

        undeclared_exemptions = sorted(
            name
            for name in _SATISFIED_WITHOUT_A_DECLARATION
            if _distribution_name(name) in declared
        )
        assert undeclared_exemptions == [], (
            f"declared in `pyproject.toml` and still exempted as transitive: "
            f"{undeclared_exemptions}. The exemption is now redundant and hides "
            "the declaration from review."
        )

        assert {"fastapi", "pydantic", "psycopg"} <= imported, (
            "the runtime imports this project is built around are missing from "
            f"`src/`: found only {sorted(imported)}"
        )


# ---------------------------------------------------------------------------
# What this module does not prove
# ---------------------------------------------------------------------------
#
# The local half proves that SQLite, this schema and this service leave a record
# that a fresh process can read, with the triggers still enforcing, under WAL. It
# is a claim about the local path.
#
# The remote half proves that a disposition written by one interpreter is read by
# another, on the reachable Postgres instance, with the triggers still refusing.
# It is a claim about that instance and that network path.
#
# Neither proves that **Render** reaches the same database. The DSN is set in the
# dashboard and is invisible here, so a service configured with the wrong one, or
# with none, would still pass everything above while writing to `:memory:` and
# losing the record on every restart. [hypothesis] Supabase's session pooler and
# Render's Singapore region are close enough for the connection to be reliable;
# that is measured on the deployment, not here. The check that closes this is the
# `/health` route reporting the engine it actually opened, which is not built.
# `04-slices.md` risk R8 stays open until a disposition written on Render has been
# read back after a real redeploy.
