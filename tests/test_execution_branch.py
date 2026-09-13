"""Focused tests for the R8-20 Regenerate and Branch card.

The DoD is "Every regeneration has lineage", so the load-bearing test regenerates
a run and then reads the lineage back through a *fresh* repository, service and
HTTP client over the same database file — and asserts that the new run is a new
run, because "no destructive overwrite of prior run" is the card's out-of-scope
boundary. The rest pin what the card declares: the snapshot is reused, only the
policy may be overridden, lineage may name one result but only by all three
parts, and a run has at most one origin.
"""

import itertools
import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from workbench.api.execution_branches import create_execution_branches_router
from workbench.application.execution_branch_service import ExecutionBranchNotFoundServiceError, ExecutionBranchService, ExecutionBranchServiceError
from workbench.application.execution_run_service import ExecutionRunService
from workbench.domain.execution import (
    EXECUTION_BRANCH_SCHEMA_VERSION,
    ExecutionBranch,
    ExecutionInputProjection,
    ExecutionPolicy,
    ExecutionRun,
)
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.execution_branch_repository import (
    ExecutionBranchConflictError,
    ExecutionBranchNotFoundError,
    SqliteExecutionBranchRepository,
)
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


ROOT = Path(__file__).resolve().parents[1]
BRANCH = ROOT / "static/js/workbench/canvas/execution-branch-runtime.js"
BRANCH_CLIENT = ROOT / "static/js/workbench/canvas/execution-branch-api-client.js"

# A lineage seam owns no transport and never starts work.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
# Regeneration prepares a branch; starting it is not this seam's job.
FORBIDDEN_EXECUTION_MARKERS = ("execute(", "executeRun", "runExecutor", "spawn", "executor.execute")
# A branch never promotes a result into a Canvas node.
FORBIDDEN_MUTATION_MARKERS = ("createNode", "addNode", "materialize", "promoteToCanvas", "/api/canvas-nodes")


def run_program(body: str, *modules: Path) -> dict:
    """Run one sandbox program with the given modules loaded, in order."""
    loaders = "".join(
        f"vm.runInNewContext(fs.readFileSync({json.dumps(str(path))},'utf8'),sandbox);\n"
        for path in modules
    )
    script = f"""
const fs=require('fs'), vm=require('vm');
const sandbox={{window:{{}}}};
{loaders}
{body}
"""
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


class ExecutionBranchPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        # Ids are minted per test so a second service in the same test cannot
        # collide with the first one's runs.
        self._branch_seq = itertools.count(1)
        self._run_seq = itertools.count(1)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.now)
        projects.create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        projects.add_member(ProjectMember(project_id="project-1", actor_id="viewer", role="viewer", created_at=self.now))
        # A second project so a branch that claims the wrong project can be built.
        projects.create_project(ProjectRecord(
            id="project-2", name="Other", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        runs.create(ExecutionRun(
            id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
            input_projection=ExecutionInputProjection(inputs=[{
                "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt", "role": "prompt",
                "order": 0, "source_type": "literal", "source_ref": "literal-1", "value": "one", "source_snapshot": "one",
            }]),
            created_at=self.now,
        ), actor_id="owner")
        runs.create(ExecutionRun(
            id="run-other", project_id="project-2", task_id="task-9", execution_profile_ref="profile@9",
            policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
            input_projection=ExecutionInputProjection(inputs=[]),
            created_at=self.now,
        ), actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def branch_repository(self):
        return SqliteExecutionBranchRepository(self.database, clock=lambda: self.now)

    def run_repository(self):
        return SqliteExecutionRunRepository(self.database, clock=lambda: self.now)

    def service(self, actor_id="owner", branch_id=None, run_id=None):
        branch_factory = (lambda: branch_id) if branch_id is not None else (lambda: f"branch-{next(self._branch_seq)}")
        # "run-new-N" rather than "run-N": a regenerated run must never collide
        # with the source run it descends from.
        run_factory = (lambda: run_id) if run_id is not None else (lambda: f"run-new-{next(self._run_seq)}")
        run_service = ExecutionRunService(self.run_repository(), actor_id=actor_id, id_factory=run_factory, clock=lambda: self.now)
        return ExecutionBranchService(self.branch_repository(), run_service, actor_id=actor_id, id_factory=branch_factory, clock=lambda: self.now)

    def test_every_regeneration_has_lineage(self):
        # The DoD: regenerate, then read the lineage back through a fresh
        # repository, service and HTTP client over the same database file.
        branch = self.service().regenerate(source_run_id="run-1", source_attempt_id="attempt-1", source_output_name="poster.png", source_ordinal=2)
        # Pinned as a literal, not only against the imported constant: renaming
        # the constant must not silently relabel the schema that is stored.
        self.assertEqual(branch.schema_version, "workbench.execution-branch/1")
        self.assertEqual(branch.schema_version, EXECUTION_BRANCH_SCHEMA_VERSION)
        self.assertEqual(branch.source_run_id, "run-1")
        self.assertNotEqual(branch.run_id, "run-1")

        reopened = self.service(branch_id="unused", run_id="unused").get_for_run(branch.run_id)
        self.assertEqual((reopened.id, reopened.source_run_id), (branch.id, "run-1"))
        # Lineage to one result uses the three-part identity, not a guess.
        self.assertEqual(reopened.result_identity(), ("attempt-1", "poster.png", 2))
        self.assertTrue(reopened.has_result_lineage())

        payload = self.client().get("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}).json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["source_attempt_id"], "attempt-1")

    def test_regeneration_reuses_the_snapshot_and_applies_the_policy_override(self):
        service = self.service()
        branch = service.regenerate(source_run_id="run-1", policy_override=ExecutionPolicy(mode="single", retry=3))
        created = self.run_repository().get(branch.run_id, actor_id="owner")
        self.assertEqual(created.task_id, "task-1")
        self.assertEqual(created.execution_profile_ref, "profile@1")
        # The frozen input snapshot is reused verbatim.
        self.assertEqual(created.input_projection.model_dump(), ExecutionInputProjection(inputs=[{
            "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt", "role": "prompt",
            "order": 0, "source_type": "literal", "source_ref": "literal-1", "value": "one", "source_snapshot": "one",
        }]).model_dump())
        # Only the policy is overridden.
        self.assertEqual((created.policy.mode, created.policy.retry), ("single", 3))
        self.assertIsNotNone(branch.policy_override)
        # Without an override the source policy is carried over.
        plain = self.service().regenerate(source_run_id="run-1")
        self.assertIsNone(plain.policy_override)
        self.assertEqual(self.run_repository().get(plain.run_id, actor_id="owner").policy.mode, "batch")

    def test_the_source_run_is_never_overwritten(self):
        service = self.service()
        service.regenerate(source_run_id="run-1")
        source = self.run_repository().get("run-1", actor_id="owner")
        self.assertEqual(source.status, "prepared")
        self.assertEqual(source.revision, 1)
        self.assertEqual(len(source.summary), 0)
        self.assertIsNone(source.started_at)

    def test_lineage_walks_to_the_root_in_order(self):
        service = self.service()
        first = service.regenerate(source_run_id="run-1")
        second = service.regenerate(source_run_id=first.run_id)
        third = service.regenerate(source_run_id=second.run_id)
        chain = service.list_lineage(third.run_id)
        self.assertEqual([b.id for b in chain], [first.id, second.id, third.id])
        self.assertEqual(chain[0].source_run_id, "run-1")
        # A root run has no lineage at all.
        self.assertEqual(service.list_lineage("run-1"), [])
        self.assertEqual([b.id for b in service.list_children("run-1")], [first.id])

    def test_a_run_has_at_most_one_origin(self):
        service = self.service()
        branch = service.regenerate(source_run_id="run-1")
        with self.assertRaises(ExecutionBranchConflictError):
            self.branch_repository().create(ExecutionBranch(
                id="branch-dup", project_id="project-1", run_id=branch.run_id,
                source_run_id="run-1", created_at=self.now,
            ), actor_id="owner")

    def test_result_lineage_is_all_or_nothing(self):
        with self.assertRaises(ValueError):
            ExecutionBranch(id="b", project_id="project-1", run_id="run-2", source_run_id="run-1",
                            source_attempt_id="attempt-1", source_output_name="poster.png", created_at=self.now)
        # A branch may not descend from itself: a regeneration is a new run.
        with self.assertRaises(ValueError):
            ExecutionBranch(id="b", project_id="project-1", run_id="run-1", source_run_id="run-1", created_at=self.now)
        # A whole-run branch names no result and is still valid.
        whole = ExecutionBranch(id="b", project_id="project-1", run_id="run-2", source_run_id="run-1", created_at=self.now)
        self.assertFalse(whole.has_result_lineage())
        self.assertIsNone(whole.result_identity())

    def test_authorization_is_enforced_on_read_and_on_regenerate(self):
        service = self.service()
        branch = service.regenerate(source_run_id="run-1")
        viewer = self.service(actor_id="viewer")
        # A viewer may read the lineage but may not create one.
        self.assertEqual(len(viewer.list_children("run-1")), 1)
        self.assertEqual(len(viewer.list_lineage(branch.run_id)), 1)
        with self.assertRaises(PermissionError):
            viewer.regenerate(source_run_id="run-1")
        # A non-member cannot read it either.
        with self.assertRaises(PermissionError):
            self.service(actor_id="stranger").list_children("run-1")
        with self.assertRaises(PermissionError):
            self.branch_repository().get(branch.id, actor_id="stranger")

    def test_the_record_rejects_out_of_contract_values(self):
        # The same six pins the preceding canonical record carries: a wrong
        # schema version would silently mislabel a migration, and an open record
        # would let an unknown field or a zero revision through.
        base = dict(id="b", project_id="project-1", run_id="run-2", source_run_id="run-1", created_at=self.now)
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, revision=0)
        # The record is closed: an unknown field is refused rather than dropped.
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, unexpected="x")
        # Its kind is a closed set, and its schema is pinned.
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, kind="merge")
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, schema_version="workbench.execution-branch/99")
        # A named result is addressed by a non-empty output name and a
        # non-negative ordinal.
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, source_attempt_id="a", source_output_name="", source_ordinal=0)
        with self.assertRaises(ValueError):
            ExecutionBranch(**base, source_attempt_id="a", source_output_name="o", source_ordinal=-1)

    def test_a_lineage_cycle_terminates(self):
        # Two runs each descending from the other is reachable: UNIQUE(run_id)
        # bounds origins, not ancestry. Without the visited set the walk would
        # loop to the depth bound and report the same records 64 times over.
        runs = self.run_repository()
        for run_id in ("run-a", "run-b"):
            runs.create(ExecutionRun(
                id=run_id, project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
                policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
                input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now,
            ), actor_id="owner")
        repository = self.branch_repository()
        repository.create(ExecutionBranch(
            id="branch-ab", project_id="project-1", run_id="run-b", source_run_id="run-a", created_at=self.now,
        ), actor_id="owner")
        repository.create(ExecutionBranch(
            id="branch-ba", project_id="project-1", run_id="run-a", source_run_id="run-b", created_at=self.now,
        ), actor_id="owner")
        self.assertEqual(
            [b.id for b in repository.list_lineage("run-b", actor_id="owner")],
            ["branch-ba", "branch-ab"],
        )

    def test_the_repository_migrates_the_run_table_it_depends_on(self):
        # The composition root constructs only the branch repository, so this
        # table arriving for free is what makes a fresh database usable — and it
        # is invisible in the other tests because setUp migrates it already.
        import sqlite3

        fresh = Path(self.temp.name) / "fresh.sqlite3"
        SqliteExecutionBranchRepository(fresh, clock=lambda: self.now)
        with sqlite3.connect(fresh) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertIn("execution_runs", tables)
        self.assertIn("execution_branches", tables)

    def test_the_repository_refuses_a_viewer_on_every_path(self):
        # The run service refuses a viewer too, so these pins are what prove the
        # branch repository is not relying on an upstream guard to be safe.
        branch = self.service().regenerate(source_run_id="run-1")
        repository = self.branch_repository()
        with self.assertRaises(PermissionError):
            repository.create(ExecutionBranch(
                id="branch-viewer", project_id="project-1", run_id="run-new-9",
                source_run_id="run-1", created_at=self.now,
            ), actor_id="viewer")
        with self.assertRaises(PermissionError):
            repository.get_for_run(branch.run_id, actor_id="stranger")
        with self.assertRaises(PermissionError):
            repository.list_lineage(branch.run_id, actor_id="stranger")

    def test_a_branch_may_not_cross_projects(self):
        with self.assertRaises(ExecutionBranchConflictError):
            self.branch_repository().create(ExecutionBranch(
                id="branch-cross", project_id="project-2", run_id="run-other",
                source_run_id="run-1", created_at=self.now,
            ), actor_id="owner")

    def test_children_are_listed_in_a_stable_order(self):
        # Inserted out of id order on a fixed clock, so only the ordering clause
        # can put them back.
        self.service(branch_id="branch-z", run_id="run-new-1").regenerate(source_run_id="run-1")
        self.service(branch_id="branch-a", run_id="run-new-2").regenerate(source_run_id="run-1")
        self.assertEqual(
            [b.id for b in self.service().list_children("run-1")],
            ["branch-a", "branch-z"],
        )

    def test_the_new_run_records_where_it_came_from(self):
        branch = self.service().regenerate(source_run_id="run-1")
        created = self.run_repository().get(branch.run_id, actor_id="owner")
        self.assertEqual(created.summary, {"regenerated_from": "run-1"})

    def test_the_record_is_immutable_and_its_metadata_is_checked(self):
        branch = ExecutionBranch(
            id="b", project_id="project-1", run_id="run-2", source_run_id="run-1",
            created_at=self.now, metadata={"note": "why"},
        )
        with self.assertRaises(ValueError):
            branch.source_run_id = "run-3"
        with self.assertRaises(TypeError):
            branch.metadata["note"] = "changed"
        with self.assertRaises(ValueError):
            ExecutionBranch(
                id="b", project_id="project-1", run_id="run-2", source_run_id="run-1",
                created_at=self.now, metadata={"api_key": "secret"},
            )

    def test_audit_records_every_branch(self):
        self.service().regenerate(source_run_id="run-1")
        self.service().regenerate(source_run_id="run-1")
        with self.branch_repository()._connection() as connection:
            rows = connection.execute(
                "SELECT event_type FROM audit_outbox WHERE event_type LIKE 'execution.branch.%' ORDER BY rowid"
            ).fetchall()
        self.assertEqual([row["event_type"] for row in rows], ["execution.branch.created", "execution.branch.created"])

    def test_the_audit_names_what_was_branched_from(self):
        self.service().regenerate(
            source_run_id="run-1", source_attempt_id="attempt-1",
            source_output_name="poster.png", source_ordinal=2,
        )
        with self.branch_repository()._connection() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM audit_outbox WHERE event_type = 'execution.branch.created'"
            ).fetchall()
        self.assertEqual(len(rows), 1)
        payload = json.loads(rows[0]["payload_json"])
        self.assertEqual(payload["source_run_id"], "run-1")
        self.assertEqual(payload["kind"], "regenerate")
        self.assertTrue(payload["has_result_lineage"], msg="the audit must say a result was branched from")

    def test_a_conflict_is_reported_as_409(self):
        # A second branch landing on an id that already has one is a conflict,
        # not a silent overwrite and not a 500. The run id stays fresh so the
        # refusal can only come from the branch record itself.
        def factory(actor_id):
            return self.service(actor_id=actor_id, branch_id="branch-fixed")

        app = FastAPI()
        app.include_router(create_execution_branches_router(service_factory=factory))
        client = TestClient(app)
        first = client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}, json={})
        self.assertEqual(first.status_code, 201)
        conflict = client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}, json={})
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()["detail"]["code"], "conflict")

    def test_unknown_branch_is_reported_rather_than_created(self):
        with self.assertRaises(ExecutionBranchNotFoundServiceError):
            self.service().get("missing")
        with self.assertRaises(ExecutionBranchNotFoundServiceError):
            self.service().get_for_run("run-1")
        with self.assertRaises(ExecutionBranchNotFoundServiceError):
            self.service().regenerate(source_run_id="missing-run")
        # An unknown source run is the same absence at the repository boundary.
        with self.assertRaises(ExecutionBranchNotFoundError):
            self.branch_repository().list_children("missing-run", actor_id="owner")

    def client(self):
        def service_factory(actor_id):
            return self.service(actor_id=actor_id, branch_id="api-branch", run_id="api-run")

        app = FastAPI()
        app.include_router(create_execution_branches_router(service_factory=service_factory))
        return TestClient(app)

    def test_api_scopes_the_run_path_and_maps_errors(self):
        client = self.client()
        created = client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}, json={
            "source_attempt_id": "attempt-1", "source_output_name": "poster.png", "source_ordinal": 0,
        })
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["source_run_id"], "run-1")

        # An unknown source run has no lineage to branch from.
        self.assertEqual(client.post("/api/v1/execution-runs/missing/branches", headers={"X-User-ID": "owner"}, json={}).status_code, 404)
        self.assertEqual(client.get("/api/v1/execution-runs/missing/branches", headers={"X-User-ID": "owner"}).status_code, 404)
        # A branch is scoped to its own source run path.
        self.assertEqual(client.get("/api/v1/execution-runs/other-run/branches/api-branch", headers={"X-User-ID": "owner"}).status_code, 404)
        # A partial result name is refused at the boundary.
        self.assertEqual(client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}, json={
            "source_attempt_id": "a", "source_output_name": "o",
        }).status_code, 422)
        # So is a field the contract does not have.
        self.assertEqual(client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "owner"}, json={
            "input_projection": {"inputs": []},
        }).status_code, 422)
        # A missing actor is rejected, and a non-member is forbidden.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/branches").status_code, 401)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "stranger"}).status_code, 403)
        # The lineage endpoint is authorized in its own right.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/lineage", headers={"X-User-ID": "stranger"}).status_code, 403)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/lineage").status_code, 401)
        self.assertEqual(client.post("/api/v1/execution-runs/run-1/branches", headers={"X-User-ID": "viewer"}, json={}).status_code, 403)

    def test_composition_root_registers_the_branch_routes(self):
        # Every other test builds its own app, so this is the only place the real
        # wiring is checked.
        import main

        if not main.WORKBENCH_NODE_API_ENABLED:
            self.skipTest("the node API is disabled for this host")
        paths = main.app.openapi()["paths"]
        self.assertIn("/api/v1/execution-runs/{run_id}/branches", paths)
        self.assertIn("/api/v1/execution-runs/{run_id}/lineage", paths)
        self.assertTrue({"get", "post"} <= set(paths["/api/v1/execution-runs/{run_id}/branches"]))
        created = paths["/api/v1/execution-runs/{run_id}/branches"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertEqual(created["$ref"], "#/components/schemas/ExecutionBranch")

    def test_core_modules_stay_industry_neutral(self):
        for relative in (
            "workbench/domain/execution/branch.py",
            "workbench/repositories/execution_branch_repository.py",
            "workbench/application/execution_branch_service.py",
            "workbench/api/execution_branches.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("wholehouse", source, msg=f"{relative} must stay industry-neutral")


class ExecutionBranchSeamTests(unittest.TestCase):
    def test_result_identity_is_all_or_nothing(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasExecutionBranch;
console.log(JSON.stringify({
  none: api.resultIdentityOf({}),
  complete: api.resultIdentityOf({source_attempt_id:'a1', source_output_name:'poster.png', source_ordinal:2}),
  missingOrdinal: api.resultIdentityOf({source_attempt_id:'a1', source_output_name:'poster.png'}),
  missingName: api.resultIdentityOf({source_attempt_id:'a1', source_ordinal:2}),
  negativeOrdinal: api.resultIdentityOf({source_attempt_id:'a1', source_output_name:'o', source_ordinal:-1}),
}));
""", BRANCH)
        self.assertIsNone(payload["none"]["identity"])
        self.assertEqual(payload["complete"]["identity"], {"attempt_id": "a1", "output_name": "poster.png", "ordinal": 2})
        for key in ("missingOrdinal", "missingName", "negativeOrdinal"):
            self.assertEqual(payload[key]["error"], "partial_result", msg=f"{key} must be refused")

    def test_hydrate_builds_ancestors_and_children(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasExecutionBranch;
const c=api.create({});
c.hydrate({run_id:'run-3', lineage:[
  {id:'b1', run_id:'run-2', source_run_id:'run-1', kind:'regenerate'},
  {id:'b2', run_id:'run-3', source_run_id:'run-2', source_attempt_id:'a1', source_output_name:'poster.png', source_ordinal:2},
], branches:[{id:'b3', run_id:'run-4', source_run_id:'run-3'}]});
const before=c.snapshot();
// A record that cannot name both ends is ignored rather than half-keyed.
const ignored=c.hydrate({run_id:'run-9', lineage:[{id:'bad', run_id:'run-9'}]});
console.log(JSON.stringify({before, ignored}));
""", BRANCH)
        self.assertEqual(payload["before"]["run_id"], "run-3")
        self.assertEqual([e["id"] for e in payload["before"]["ancestors"]], ["b1", "b2"])
        self.assertEqual([e["id"] for e in payload["before"]["children"]], ["b3"])
        self.assertEqual(payload["before"]["depth"], 2)
        self.assertEqual(payload["before"]["children"][0]["result"], None)
        self.assertEqual(payload["before"]["ancestors"][1]["result"], {"attempt_id": "a1", "output_name": "poster.png", "ordinal": 2})
        self.assertEqual(payload["ignored"]["depth"], 0)

    def test_request_is_validated_with_explicit_reasons(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasExecutionBranch;
const c=api.create({});
console.log(JSON.stringify({
  accepted:c.requestFrom({run_id:'run-3', source_attempt_id:'a1', source_output_name:'o', source_ordinal:1}),
  wholeRun:c.requestFrom({run_id:'run-3'}),
  override:c.requestFrom({run_id:'run-3', policy_override:{mode:'single', retry:2}}),
  partial:c.requestFrom({run_id:'run-3', source_attempt_id:'a1', source_output_name:'o'}),
  unknown:c.requestFrom({source_attempt_id:'a1', source_output_name:'o', source_ordinal:0}),
}));
""", BRANCH)
        self.assertEqual(payload["accepted"]["reason"], "accepted")
        self.assertEqual(payload["accepted"]["request"]["source_ordinal"], 1)
        # A whole-run regeneration names no result.
        self.assertEqual(payload["wholeRun"]["request"], {"run_id": "run-3"})
        self.assertEqual(payload["override"]["request"]["policy_override"]["retry"], 2)
        self.assertEqual(payload["partial"]["reason"], "partial_result")
        self.assertIsNone(payload["partial"]["request"])
        self.assertEqual(payload["unknown"]["reason"], "unknown_run")

    def test_mounted_rows_carry_the_lineage(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasExecutionBranch;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const c=api.create({});
c.mount(host);
c.hydrate({run_id:'run-2', lineage:[
  {id:'b1', run_id:'run-2', source_run_id:'<run>&1', source_attempt_id:'a', source_output_name:'poster.png', source_ordinal:2},
  {id:'bad"id&x', run_id:'run-2b', source_run_id:'run-2'},
]});
console.log(JSON.stringify({attr:host.attrs['data-execution-branch'], html:host.innerHTML}));
""", BRANCH)
        self.assertEqual(payload["attr"], "workbench.execution-branch/1")
        for fragment in ('data-branch-id="b1"', 'data-branch-run="run-2"', 'data-branch-source="&lt;run&gt;&amp;1"',
                         'data-branch-result="poster.png #2"', 'data-branch-kind="ancestor"',
                         'data-branch-id="bad&quot;id&amp;x"'):
            self.assertIn(fragment, payload["html"], msg=f"row must carry {fragment}")
        self.assertNotIn("<run>&1", payload["html"])
        self.assertNotIn('bad"id&x', payload["html"])

    def test_unmounting_leaves_no_trace_and_a_override_must_be_an_object(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasExecutionBranch;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const c=api.create({});
const mounted=c.mount(host);
c.hydrate({run_id:'run-2', lineage:[{id:'b1', run_id:'run-2', source_run_id:'run-1'}]});
const hadMarker = 'data-execution-branch' in host.attrs;
mounted.destroy();
// A policy override that is not an object is dropped rather than forwarded.
const bad=c.requestFrom({run_id:'run-2', policy_override:'single'});
console.log(JSON.stringify({hadMarker, after:host.attrs, html:host.innerHTML, bad}));
""", BRANCH)
        self.assertTrue(payload["hadMarker"])
        self.assertEqual(payload["after"], {}, msg="destroy must take the marker with it")
        self.assertEqual(payload["html"], "")
        self.assertNotIn("policy_override", payload["bad"]["request"])

    def test_seam_owns_no_transport_and_never_executes(self):
        source = BRANCH.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TRANSPORT_MARKERS + FORBIDDEN_EXECUTION_MARKERS + FORBIDDEN_MUTATION_MARKERS:
            self.assertNotIn(marker, source, msg=f"branch seam must not reference {marker}")

    def test_canvas_page_and_node_shell_register_the_branch_seam(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/execution-branch-runtime.js"), 1)
        self.assertEqual(page.count("workbench/canvas/execution-branch-api-client.js"), 1)
        self.assertLess(page.index("result-selection-runtime.js"), page.index("execution-branch-runtime.js"))
        self.assertLess(page.index("execution-branch-runtime.js"), page.index("canvas-app-bootstrap.js"))

        # The seam is actually reachable: the node shell mounts it when the host
        # supplies options, rather than leaving it registered but unused.
        node = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        self.assertIn("function mountExecutionBranch(host, options)", node)
        self.assertIn("mountExecutionBranch,", node)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("settings.executionBranchOptions", shell)
        self.assertIn("mountExecutionBranch(executionBranchHost", shell)
        self.assertIn("data-execution-branch-host", shell)
        self.assertIn("mountedExecutionBranch?.destroy?.()", shell)

    def test_client_sends_the_canonical_request(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchExecutionBranchApiClient;
const calls=[];
const fakeFetch=async (url,options)=>{calls.push({url,method:options.method,headers:options.headers,body:options.body?JSON.parse(options.body):null});return {ok:true,status:201,json:async()=>({id:'b1'})};};
(async()=>{
  await client.create('run/1', {run_id:'run-1', source_attempt_id:'a1', source_output_name:'o', source_ordinal:2}, {actorId:'owner', fetch:fakeFetch});
  await client.list('run-1', {actorId:'owner', fetch:fakeFetch});
  await client.lineage('run-1', {actorId:'owner', fetch:fakeFetch});
  await client.create('run-1', {run_id:'run-1', metadata:{note:'why'}}, {actorId:'owner', fetch:fakeFetch});
  let noActor='', noRun='', blankLineage='';
  try { await client.list('run-1', {fetch:fakeFetch}); } catch(e) { noActor=e.message; }
  try { await client.create('run-1', {}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noRun=e.message; }
  try { await client.lineage('', {actorId:'owner', fetch:fakeFetch}); } catch(e) { blankLineage=e.message; }
  console.log(JSON.stringify({calls, noActor, noRun, blankLineage}));
})();
""", BRANCH_CLIENT)
        create, listing, lineage, withMetadata = payload["calls"]
        # The run id is a path segment, so it is escaped.
        self.assertEqual(create["url"], "/api/v1/execution-runs/run%2F1/branches")
        self.assertEqual(create["method"], "POST")
        self.assertEqual(create["headers"]["X-User-ID"], "owner")
        self.assertEqual(
            {k: create["body"][k] for k in ("source_attempt_id", "source_output_name", "source_ordinal")},
            {"source_attempt_id": "a1", "source_output_name": "o", "source_ordinal": 2},
        )
        self.assertEqual(listing["url"], "/api/v1/execution-runs/run-1/branches")
        self.assertEqual(listing["method"], "GET")
        # Listing is a read, but it still has to arrive as somebody.
        self.assertEqual(listing["headers"]["X-User-ID"], "owner")
        self.assertEqual(lineage["url"], "/api/v1/execution-runs/run-1/lineage")
        self.assertIn("actor id", payload["noActor"])
        self.assertIn("run id", payload["noRun"])
        self.assertIn("run id", payload["blankLineage"])
        # The caller's metadata reaches the request rather than being dropped.
        self.assertEqual(withMetadata["body"]["metadata"], {"note": "why"})


if __name__ == "__main__":
    unittest.main()
