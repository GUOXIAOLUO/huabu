"""Focused tests for the R8-22 Result to Canvas Materialization card.

The DoD is "Only explicit user/application action creates Canvas node", so the
load-bearing test materializes one result and then asserts both halves: the node
carries the result's four-part address and the producing run, and nothing else
created a node — an unselected sibling result, an unnamed result and a run nobody
selected anything in all refuse to produce one.

The rest pin what the card declares: a materialized node is a result node rather
than an Asset or an Artifact, it is stored where a Canvas can find it, and it can
be read back as the record it was written as.
"""

import itertools
import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from main import WORKBENCH_NODE_API_ENABLED
from workbench.api.result_materializations import create_result_materializations_router
from workbench.application.execution_run_service import ExecutionRunService
from workbench.application.node_creation import NodeCreateCommand, NodeCreationError, NodeCreationService, NodeCreationSource
from workbench.application.node_mutation import NodeDeleteCommand, NodeMutationService
from workbench.application.result_materialization_service import (
    ResultMaterializationNotFoundServiceError,
    ResultMaterializationService,
    ResultMaterializationServiceError,
)
from workbench.application.result_node_definitions import ResultNodeDefinitionRegistry, ResultNodeModelCompatibilityPolicy
from workbench.application.result_selection_service import ResultSelectionService
from workbench.domain.canvas.canonical_adapter import is_canonical_payload, payload_from_record, record_from_payload
from workbench.domain.canvas.legacy_adapter import LegacyCanvasAdapter
from workbench.domain.canvas.models import DefinitionRef, Position
from workbench.domain.canvas.port_type_registry import create_core_port_type_registry
from workbench.domain.execution import ExecutionInputProjection, ExecutionPolicy, ExecutionResultIdentity, ExecutionRun
from workbench.domain.project.models import ProjectRecord
from workbench.repositories.canonical_json_node_repository import CanonicalJsonNodeCreationRepository
from workbench.repositories.canvas_repository import StaleCanvasRevisionError
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.jsonl_audit_sink import JsonlAuditSink
from workbench.repositories.legacy_json_canvas_repository import LegacyJsonCanvasRepository
from workbench.repositories.legacy_json_node_repository import (
    LegacyCanvasProjectAuthorizer,
    LegacyJsonNodeMutationRepository,
)
from workbench.repositories.result_selection_repository import SqliteResultSelectionRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


ROOT = Path(__file__).resolve().parents[1]
SEAM = ROOT / "static/js/workbench/canvas/result-materialization-runtime.js"
CLIENT = ROOT / "static/js/workbench/canvas/result-materialization-api-client.js"

# A materialization seam owns no transport and never converts a result.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
FORBIDDEN_CONVERSION_MARKERS = ("asset_version", "artifact_version", "/api/v1/assets", "/api/v1/artifacts")


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


class ResultMaterializationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        self.clock_ms = 100
        self._selection_ids = itertools.count(1)
        self._node_ids = itertools.count(1)

        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.now)
        for project_id, name in (("project-1", "Project"), ("project-2", "Other")):
            projects.create_project(ProjectRecord(
                id=project_id, name=name, workspace_id="local", created_by="owner",
                created_at=self.now, updated_at=self.now,
            ))

        runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        for run_id, project_id in (("run-1", "project-1"), ("run-empty", "project-1"), ("run-other", "project-2")):
            runs.create(ExecutionRun(
                id=run_id, project_id=project_id, task_id="task-1", execution_profile_ref="profile@1",
                policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
                input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now,
            ), actor_id="owner")

        # What the user decided: two of the three results are selected. The third
        # is the one that must never be materialized on its own.
        selections = ResultSelectionService(
            SqliteResultSelectionRepository(self.database, clock=lambda: self.now),
            actor_id="owner", id_factory=lambda: f"selection-{next(self._selection_ids)}", clock=lambda: self.now,
        )
        for attempt_id, output_name, ordinal, selected in (
            ("attempt-1", "poster.png", 0, True),
            ("attempt-1", "poster.png", 1, False),
            ("attempt-2", "thumb.png", 0, True),
        ):
            selections.create(
                run_id="run-1", attempt_id=attempt_id, output_name=output_name,
                ordinal=ordinal, selected=selected,
            )

        self.canvas_repository = LegacyJsonCanvasRepository(self.root / "canvases", clock_ms=lambda: self.clock_ms, lock=Lock())
        # An existing Legacy node, so a canonical one is proven not to disturb it.
        self.canvas_repository.save({
            "id": "canvas-1", "project": "project-1", "owner": "owner", "updated_at": 99,
            "nodes": [{"id": "legacy-1", "type": "image", "x": 0, "y": 0, "url": "", "name": "old"}],
            "connections": [],
        })
        # A Canvas this actor cannot edit.
        self.canvas_repository.save({
            "id": "canvas-2", "project": "project-1", "owner": "someone-else", "updated_at": 99,
            "nodes": [], "connections": [],
        })
        self.audit_path = self.root / "audit" / "events.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def selection_service(self, actor_id="owner"):
        return ResultSelectionService(
            SqliteResultSelectionRepository(self.database, clock=lambda: self.now),
            actor_id=actor_id, id_factory=lambda: f"selection-{next(self._selection_ids)}", clock=lambda: self.now,
        )

    def run_service(self, actor_id="owner"):
        return ExecutionRunService(SqliteExecutionRunRepository(self.database, clock=lambda: self.now), actor_id=actor_id)

    def node_creation_service(self, actor_id="owner"):
        return NodeCreationService(
            authorizer=LegacyCanvasProjectAuthorizer(self.canvas_repository),
            definitions=ResultNodeDefinitionRegistry(),
            model_policy=ResultNodeModelCompatibilityPolicy(),
            repository=CanonicalJsonNodeCreationRepository(self.canvas_repository),
            audit_sink=JsonlAuditSink(self.audit_path, lock=Lock()),
            node_id_factory=lambda: f"node-{next(self._node_ids)}",
            port_types=create_core_port_type_registry(),
            clock=lambda: self.now,
        )

    def service(self, actor_id="owner"):
        return ResultMaterializationService(
            self.node_creation_service(actor_id), self.selection_service(actor_id), self.run_service(actor_id),
            actor_id=actor_id,
        )

    def materialize(self, **overrides):
        values = {
            "request_id": "request-1", "project_id": "project-1", "canvas_id": "canvas-1",
            "run_id": "run-1", "attempt_id": "attempt-1", "output_name": "poster.png",
            "ordinal": 0, "position": Position(x=20, y=30), "expected_revision": 100,
        }
        values.update(overrides)
        return self.service().materialize(**values)

    def stored_nodes(self, canvas_id="canvas-1"):
        return self.canvas_repository.load(canvas_id)["nodes"]

    def audit_events(self):
        if not self.audit_path.exists():
            return []
        return [json.loads(line) for line in self.audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_materializing_one_selected_result_creates_one_node_with_its_lineage(self):
        # The DoD: one explicit call, one node, and the node knows which result it
        # stands for and which run produced it.
        before = len(self.stored_nodes())
        result = self.materialize()
        self.assertTrue(result.created)
        self.assertEqual(result.canvas_revision, 101)
        node = result.node
        self.assertEqual(node.kind, "result")
        self.assertEqual(node.definition_ref, DefinitionRef(type="workbench", id="execution-result", version="1"))
        self.assertEqual(node.config["result"], {
            "schema_version": "workbench.result-identity/1",
            "run_id": "run-1", "attempt_id": "attempt-1", "output_name": "poster.png", "ordinal": 0,
        })
        self.assertEqual(node.provenance_ref, "run-1")
        self.assertEqual(node.title, "poster.png#0")
        # The literal, not the enum: this is what a stored node says, so it is a
        # format constant rather than something free to rename.
        self.assertEqual(node.metadata["creation"]["source"], "result_materialization")
        # A materialized result has not been converted into an Asset or an
        # Artifact, so the node may not claim to accept or produce typed values.
        self.assertEqual((node.ports.inputs, node.ports.outputs), ([], []))
        self.assertEqual(len(self.stored_nodes()), before + 1)

    def test_the_node_is_stored_where_the_canvas_can_find_it(self):
        self.materialize()
        stored = self.stored_nodes()[-1]
        # Pinned as the literal: the marker is part of a stored file's format.
        self.assertEqual(stored["type"], "workbench-result")
        # Legacy consumers only understand geometry, so it is repeated for them.
        self.assertEqual((stored["x"], stored["y"]), (20.0, 30.0))
        self.assertEqual((stored["w"], stored["h"]), (320.0, 240.0))
        self.assertTrue(is_canonical_payload(stored))
        # The idempotency key is part of a stored file's format and is shared
        # with the Legacy writer, so it is pinned as the literal rather than
        # read back through the constant that defines it.
        self.assertIn("_workbench_node_create_request_id", stored)

    def test_the_stored_node_reads_back_as_the_record_it_was_written_as(self):
        result = self.materialize()
        # The shared Legacy adapter must not flatten a canonical node into a
        # Legacy one: the existing node read path has to answer honestly.
        read_back = LegacyCanvasAdapter.node_to_record(self.stored_nodes()[-1], canvas=self.canvas_repository.load("canvas-1"))
        self.assertEqual(read_back, result.node)
        self.assertEqual(read_back.kind, "result")
        self.assertEqual(read_back.provenance_ref, "run-1")

    def test_an_existing_legacy_node_is_untouched(self):
        self.materialize()
        legacy = LegacyCanvasAdapter.node_to_record(self.stored_nodes()[0], canvas=self.canvas_repository.load("canvas-1"))
        self.assertEqual(legacy.id, "legacy-1")
        self.assertEqual(legacy.kind, "asset")
        self.assertEqual(legacy.definition_ref.type, "legacy")

    def test_an_unselected_result_is_refused(self):
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            self.materialize(ordinal=1, request_id="request-unselected")
        self.assertEqual(caught.exception.code, "result_not_selected")
        self.assertEqual(len(self.stored_nodes()), 1)

    def test_a_result_nobody_named_is_not_found(self):
        with self.assertRaises(ResultMaterializationNotFoundServiceError):
            self.materialize(attempt_id="attempt-9", request_id="request-missing")
        self.assertEqual(len(self.stored_nodes()), 1)

    def test_a_run_with_no_selections_has_nothing_to_materialize(self):
        with self.assertRaises(ResultMaterializationNotFoundServiceError):
            self.materialize(run_id="run-empty", request_id="request-empty")

    def test_an_unknown_run_is_not_found(self):
        with self.assertRaises(ResultMaterializationNotFoundServiceError):
            self.materialize(run_id="run-nope", request_id="request-nope")

    def test_a_result_cannot_be_materialized_into_another_project(self):
        # A node whose provenance points into another project is a node its
        # readers cannot follow.
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            self.materialize(project_id="project-2", request_id="request-cross")
        self.assertEqual(caught.exception.code, "cross_project")

    def test_an_actor_who_cannot_edit_the_canvas_is_forbidden(self):
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            self.materialize(canvas_id="canvas-2", request_id="request-forbidden")
        self.assertEqual(caught.exception.code, "forbidden")

    def test_a_stale_canvas_revision_is_refused(self):
        with self.assertRaises(StaleCanvasRevisionError):
            self.materialize(expected_revision=50, request_id="request-stale")

    def test_one_request_creates_one_node_however_often_it_arrives(self):
        first = self.materialize()
        second = self.materialize()
        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(second.node.id, first.node.id)
        self.assertEqual(len(self.stored_nodes()), 2)

    def test_two_requests_create_two_nodes(self):
        # Materializing twice is two writes to a shared Canvas, so the second
        # call has to name the revision the first one produced.
        self.materialize(request_id="request-a")
        current = self.canvas_repository.load("canvas-1")["updated_at"]
        self.materialize(request_id="request-b", expected_revision=current)
        self.assertEqual(len(self.stored_nodes()), 3)

    def test_an_explicit_title_is_honoured(self):
        self.assertEqual(self.materialize(title="Hero shot").node.title, "Hero shot")

    def test_a_blank_part_of_the_address_is_refused(self):
        for overrides in (
            {"output_name": " "},
            {"attempt_id": " "},
            {"run_id": " "},
            {"canvas_id": " "},
            {"project_id": " "},
            {"request_id": " "},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ResultMaterializationServiceError) as caught:
                    self.materialize(**overrides)
                self.assertEqual(caught.exception.code, "invalid_request")

    def test_a_negative_ordinal_is_refused(self):
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            self.materialize(ordinal=-1)
        self.assertEqual(caught.exception.code, "invalid_request")

    def test_a_zero_expected_revision_is_refused(self):
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            self.materialize(expected_revision=0)
        self.assertEqual(caught.exception.code, "invalid_request")

    def test_the_service_refuses_a_zero_revision_before_asking_for_a_node(self):
        # The node-creation service enforces the same bound one layer down, so
        # this pins that the materialization service refuses on its own rather
        # than relying on something else to notice.
        calls = []

        class RecordingNodeCreation:
            def create(self, command):
                calls.append(command)
                raise AssertionError("the service must not ask for a node")

        service = ResultMaterializationService(
            RecordingNodeCreation(), self.selection_service(), self.run_service(), actor_id="owner",
        )
        with self.assertRaises(ResultMaterializationServiceError) as caught:
            service.materialize(
                request_id="request-1", project_id="project-1", canvas_id="canvas-1", run_id="run-1",
                attempt_id="attempt-1", output_name="poster.png", ordinal=0,
                position=Position(x=1, y=2), expected_revision=0,
            )
        self.assertEqual(caught.exception.code, "invalid_request")
        self.assertEqual(calls, [])

    def test_creating_a_node_writes_one_audit_event(self):
        self.materialize()
        events = self.audit_events()
        self.assertEqual(len(events), 1)
        # The audit records the materialization as the source, not as a Legacy
        # or agent-driven creation.
        self.assertEqual(events[0]["source"], "result_materialization")
        self.assertEqual(events[0]["event"], "canvas.node.created")

    def test_a_replayed_request_writes_no_second_audit_event(self):
        self.materialize()
        self.materialize()
        self.assertEqual(len(self.audit_events()), 1)

    def test_the_canonical_repository_refuses_a_non_canonical_definition(self):
        repository = CanonicalJsonNodeCreationRepository(self.canvas_repository)
        node = self.materialize().node.model_copy(
            update={"definition_ref": DefinitionRef(type="legacy", id="image", version="0")},
        )
        with self.assertRaises(ValueError):
            repository.create_node(node, expected_revision=None, request_id="request-other")

    def test_the_identity_requires_every_part(self):
        complete = ExecutionResultIdentity(run_id="run-1", attempt_id="attempt-1", output_name="poster.png", ordinal=0)
        self.assertEqual(complete.label(), "poster.png#0")
        for field in ("run_id", "attempt_id", "output_name"):
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    ExecutionResultIdentity.model_validate({**complete.model_dump(mode="json"), field: ""})
        with self.assertRaises(ValueError):
            ExecutionResultIdentity.model_validate({**complete.model_dump(mode="json"), "ordinal": -1})
        with self.assertRaises(ValueError):
            ExecutionResultIdentity.model_validate({**complete.model_dump(mode="json"), "schema_version": "workbench.result-identity/2"})

    def test_the_identity_is_a_frozen_closed_record(self):
        # The identity is stored inside a node's config, which is a plain dict,
        # so the record itself has to refuse mutation and refuse unknown fields.
        complete = ExecutionResultIdentity(run_id="run-1", attempt_id="attempt-1", output_name="poster.png", ordinal=0)
        with self.assertRaises(ValidationError):
            complete.output_name = "other.png"
        with self.assertRaises(ValidationError):
            ExecutionResultIdentity.model_validate({**complete.model_dump(mode="json"), "unknown": 1})

    def test_the_identity_bounds_the_output_name(self):
        for name in ("x" * 255, "x" * 256):
            with self.subTest(length=len(name)):
                if len(name) > 255:
                    with self.assertRaises(ValidationError):
                        ExecutionResultIdentity(run_id="run-1", attempt_id="a1", output_name=name, ordinal=0)
                else:
                    self.assertEqual(
                        ExecutionResultIdentity(run_id="run-1", attempt_id="a1", output_name=name, ordinal=0).output_name,
                        name,
                    )

    def test_reading_a_stored_node_does_not_rewrite_it(self):
        # `record_from_payload` strips the store-only keys; without a copy it
        # would strip them from the canvas still held in memory.
        node = self.materialize().node
        payload = payload_from_record(node, request_id="request-1")
        before = json.dumps(payload, sort_keys=True)
        self.assertEqual(record_from_payload(payload), node)
        self.assertEqual(json.dumps(payload, sort_keys=True), before)

    def test_the_stored_payload_round_trips(self):
        node = self.materialize().node
        payload = payload_from_record(node, request_id="request-1")
        self.assertEqual(record_from_payload(payload), node)

    def test_api_answers_the_outcomes_the_service_declares(self):
        app = FastAPI()
        app.include_router(create_result_materializations_router(service_factory=lambda actor_id: self.service(actor_id)))
        client = TestClient(app)

        def post(**overrides):
            body = {
                "request_id": "request-api", "project_id": "project-1", "run_id": "run-1",
                "attempt_id": "attempt-1", "output_name": "poster.png", "ordinal": 0,
                "position": {"x": 1, "y": 2}, "expected_revision": 100,
            }
            body.update(overrides)
            headers = {"X-User-ID": "owner"} if "headers" not in overrides else overrides["headers"]
            body.pop("headers", None)
            return client.post("/api/v1/canvases/canvas-1/result-nodes", json=body, headers=headers)

        created = post()
        self.assertEqual(created.status_code, 201, msg=created.text)
        self.assertTrue(created.json()["created"])
        self.assertEqual(created.json()["node"]["kind"], "result")

        no_actor = post(headers={})
        self.assertEqual(no_actor.status_code, 401)

        forbidden = client.post(
            "/api/v1/canvases/canvas-2/result-nodes",
            json={"request_id": "r", "project_id": "project-1", "run_id": "run-1", "attempt_id": "attempt-1",
                  "output_name": "poster.png", "ordinal": 0, "position": {"x": 0, "y": 0}},
            headers={"X-User-ID": "owner"},
        )
        self.assertEqual(forbidden.status_code, 403)

        not_found = post(run_id="run-nope", request_id="request-api-3")
        self.assertEqual(not_found.status_code, 404)

        not_selected = post(ordinal=1, request_id="request-api-4")
        self.assertEqual(not_selected.status_code, 409)

        stale = post(expected_revision=50, request_id="request-api-5")
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["detail"]["code"], "stale_revision")

        invalid = post(ordinal=-1, request_id="request-api-6")
        self.assertEqual(invalid.status_code, 422)
        # Refused by the payload contract itself rather than by the service:
        # FastAPI reports a validation list where the service reports a coded
        # object, so the two are distinguishable.
        self.assertIsInstance(invalid.json()["detail"], list)

    def test_a_replayed_request_id_returns_the_node_it_first_created(self):
        # Idempotency is keyed on the request, not on the parameters: a retry
        # must not silently materialize a different result than the one that was
        # asked for the first time.
        first = self.materialize(request_id="request-1")
        replayed = self.materialize(
            request_id="request-1", attempt_id="attempt-2", output_name="thumb.png",
        )
        self.assertFalse(replayed.created)
        self.assertEqual(replayed.node.id, first.node.id)
        self.assertEqual(replayed.node.config["result"]["output_name"], "poster.png")

    def test_a_canonical_node_survives_another_writer_on_the_same_canvas(self):
        # The canonical node shares the node list with Legacy nodes, so a Legacy
        # mutation must not quietly discard it.
        self.materialize()
        mutations = NodeMutationService(
            authorizer=LegacyCanvasProjectAuthorizer(self.canvas_repository),
            repository=LegacyJsonNodeMutationRepository(self.canvas_repository),
            audit_sink=JsonlAuditSink(self.audit_path, lock=Lock()),
        )
        mutations.delete(NodeDeleteCommand(
            actor_id="owner", project_id="project-1", canvas_id="canvas-1",
            node_id="legacy-1", expected_revision=self.canvas_repository.load("canvas-1")["updated_at"],
        ))
        stored = self.stored_nodes()
        self.assertEqual(len(stored), 1)
        self.assertTrue(is_canonical_payload(stored[0]))
        self.assertEqual(stored[0]["id"], "node-1")

    def test_the_generic_node_route_cannot_create_a_canonical_result_node(self):
        # The DoD is that only the materialization action creates one, so the
        # generic creation path must be unable to produce the same node.
        from workbench.application.legacy_definitions import LegacyDefinitionRegistry, LegacyImageModelCompatibilityPolicy
        from workbench.repositories.legacy_json_node_repository import LegacyJsonNodeCreationRepository

        generic = NodeCreationService(
            authorizer=LegacyCanvasProjectAuthorizer(self.canvas_repository),
            definitions=LegacyDefinitionRegistry(),
            model_policy=LegacyImageModelCompatibilityPolicy(),
            repository=LegacyJsonNodeCreationRepository(self.canvas_repository),
            audit_sink=JsonlAuditSink(self.audit_path, lock=Lock()),
            node_id_factory=lambda: "node-generic",
            port_types=create_core_port_type_registry(),
        )
        with self.assertRaises(NodeCreationError) as caught:
            generic.create(NodeCreateCommand(
                request_id="request-generic", actor_id="owner", project_id="project-1", canvas_id="canvas-1",
                source=NodeCreationSource.RESULT_MATERIALIZATION,
                definition_ref=ResultNodeDefinitionRegistry.EXECUTION_RESULT,
                position=Position(x=0, y=0), expected_revision=100,
            ))
        self.assertEqual(caught.exception.code, "definition_not_found")
        self.assertEqual(len(self.stored_nodes()), 1)

    def test_api_marks_a_cross_project_result_as_a_bad_request(self):
        app = FastAPI()
        app.include_router(create_result_materializations_router(service_factory=lambda actor_id: self.service(actor_id)))
        client = TestClient(app)
        response = client.post(
            "/api/v1/canvases/canvas-1/result-nodes",
            json={"request_id": "r", "project_id": "project-1", "run_id": "run-other", "attempt_id": "attempt-1",
                  "output_name": "poster.png", "ordinal": 0, "position": {"x": 0, "y": 0}},
            headers={"X-User-ID": "owner"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "cross_project")

    def test_api_reports_a_run_with_no_selections_as_not_found(self):
        app = FastAPI()
        app.include_router(create_result_materializations_router(service_factory=lambda actor_id: self.service(actor_id)))
        client = TestClient(app)
        response = client.post(
            "/api/v1/canvases/canvas-1/result-nodes",
            json={"request_id": "r", "project_id": "project-1", "run_id": "run-empty", "attempt_id": "attempt-1",
                  "output_name": "poster.png", "ordinal": 0, "position": {"x": 0, "y": 0}},
            headers={"X-User-ID": "owner"},
        )
        self.assertEqual(response.status_code, 404)

    def test_api_refuses_an_overlong_actor(self):
        app = FastAPI()
        app.include_router(create_result_materializations_router(service_factory=lambda actor_id: self.service(actor_id)))
        client = TestClient(app)
        response = client.post(
            "/api/v1/canvases/canvas-1/result-nodes",
            json={"request_id": "r", "project_id": "project-1", "run_id": "run-1", "attempt_id": "attempt-1",
                  "output_name": "poster.png", "ordinal": 0, "position": {"x": 0, "y": 0}},
            headers={"X-User-ID": "x" * 256},
        )
        self.assertEqual(response.status_code, 401)

    def test_api_reports_which_result_was_refused(self):
        app = FastAPI()
        app.include_router(create_result_materializations_router(service_factory=lambda actor_id: self.service(actor_id)))
        client = TestClient(app)
        response = client.post(
            "/api/v1/canvases/canvas-1/result-nodes",
            json={"request_id": "r", "project_id": "project-1", "run_id": "run-1", "attempt_id": "attempt-1",
                  "output_name": "poster.png", "ordinal": 1, "position": {"x": 0, "y": 0}},
            headers={"X-User-ID": "owner"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "result_not_selected")
        self.assertIn("poster.png#1", response.json()["detail"]["message"])

    @unittest.skipUnless(WORKBENCH_NODE_API_ENABLED, "the node API is disabled for this host")
    def test_composition_root_registers_the_materialization_route(self):
        # The route is only delivered if the shipped app mounts it; this test
        # exists because the wiring, not the router, is what can silently rot.
        import main

        paths = main.app.openapi()["paths"]
        self.assertIn("/api/v1/canvases/{canvas_id}/result-nodes", paths)
        self.assertIn("post", paths["/api/v1/canvases/{canvas_id}/result-nodes"])

    def test_core_modules_stay_industry_neutral(self):
        for relative in (
            "workbench/application/result_materialization_service.py",
            "workbench/application/result_node_definitions.py",
            "workbench/api/result_materializations.py",
            "workbench/repositories/canonical_json_node_repository.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("wholehouse", source, msg=f"{relative} must stay industry-neutral")


class ResultMaterializationSeamTests(unittest.TestCase):
    def test_a_record_keeps_the_four_part_identity(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const node={id:'node-1', title:'Hero', canvas_id:'canvas-1', provenance_ref:'run-1',
            config:{result:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:2}}};
console.log(JSON.stringify({
  complete: api.recordFrom(node),
  wrapped: api.recordFrom({node:node}),
  noLineage: api.recordFrom({id:'node-2'}),
  noConfig: api.recordFrom({id:'node-3', config:{}}),
  partial: api.recordFrom({id:'node-4', config:{result:{run_id:'run-1', attempt_id:'a1'}}}),
  emptyName: api.recordFrom({id:'node-5', config:{result:{run_id:'run-1', attempt_id:'a1', output_name:'', ordinal:0}}}),
  badOrdinal: api.recordFrom({id:'node-6', config:{result:{run_id:'run-1', attempt_id:'a1', output_name:'p.png', ordinal:-1}}}),
}));
""", SEAM)
        self.assertEqual(payload["complete"], {
            "id": "node-1", "title": "Hero", "run_id": "run-1", "attempt_id": "a1",
            "output_name": "poster.png", "ordinal": 2, "canvas_id": "canvas-1", "provenance_ref": "run-1",
        })
        self.assertEqual(payload["wrapped"], payload["complete"])
        for key in ("noLineage", "noConfig", "partial", "emptyName", "badOrdinal"):
            self.assertIsNone(payload[key], msg=f"{key} must be ignored rather than half-rendered")

    def test_a_record_without_a_title_falls_back_to_the_result_name(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
console.log(JSON.stringify(api.recordFrom({id:'n1', config:{result:{run_id:'r', attempt_id:'a', output_name:'p.png', ordinal:3}}})));
""", SEAM)
        self.assertEqual(payload["title"], "p.png #3")

    def test_request_is_validated_with_explicit_reasons(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const good={canvas_id:'c1', request_id:'req-1', run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0, position:{x:1,y:2}};
console.log(JSON.stringify({
  accepted: api.requestFrom(good),
  noCanvas: api.requestFrom({...good, canvas_id:''}),
  noRequest: api.requestFrom({...good, request_id:''}),
  noRun: api.requestFrom({...good, run_id:''}),
  noAttempt: api.requestFrom({...good, attempt_id:''}),
  noOutput: api.requestFrom({...good, output_name:''}),
  badOrdinal: api.requestFrom({...good, ordinal:-1}),
  noPosition: api.requestFrom({...good, position:undefined}),
  nanPosition: api.requestFrom({...good, position:{x:'left', y:2}}),
}));
""", SEAM)
        self.assertEqual(payload["accepted"]["reason"], "accepted")
        self.assertEqual(payload["accepted"]["request"], {
            "request_id": "req-1", "project_id": "", "run_id": "run-1", "attempt_id": "a1",
            "output_name": "poster.png", "ordinal": 0, "position": {"x": 1, "y": 2},
        })
        self.assertEqual(payload["noCanvas"]["reason"], "unknown_canvas")
        self.assertEqual(payload["noRequest"]["reason"], "unknown_request")
        self.assertEqual(payload["noRun"]["reason"], "unknown_run")
        self.assertEqual(payload["noAttempt"]["reason"], "unknown_result")
        self.assertEqual(payload["noOutput"]["reason"], "unknown_result")
        self.assertEqual(payload["badOrdinal"]["reason"], "bad_ordinal")
        self.assertEqual(payload["noPosition"]["reason"], "bad_position")
        self.assertEqual(payload["nanPosition"]["reason"], "bad_position")
        for key in ("noCanvas", "noRequest", "noRun", "badOrdinal", "noPosition"):
            self.assertIsNone(payload[key]["request"], msg=f"{key} must produce no request")

    def test_optional_parts_are_sent_only_when_present(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const good={canvas_id:'c1', request_id:'req-1', run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0, position:{x:0,y:0}};
console.log(JSON.stringify({
  bare: api.requestFrom(good).request,
  withRevision: api.requestFrom({...good, expected_revision:7}).request,
  withTitle: api.requestFrom({...good, title:' Hero '}).request,
}));
""", SEAM)
        self.assertNotIn("expected_revision", payload["bare"])
        self.assertNotIn("title", payload["bare"])
        self.assertEqual(payload["withRevision"]["expected_revision"], 7)
        self.assertEqual(payload["withTitle"]["title"], "Hero")

    def test_mounted_rows_carry_the_lineage_and_are_escaped(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const c=api.create({});
c.mount(host);
c.hydrate({canvas_revision:100, node:{id:'node"1', canvas_id:'canvas-1', title:'Hero', provenance_ref:'run-1',
  config:{result:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0}}}});
c.hydrate({canvas_revision:101, node:{id:'node-2', canvas_id:'canvas-1', title:'<x>"&', provenance_ref:'run-1',
  config:{result:{run_id:'<run>&1', attempt_id:'a1', output_name:'thumb.png', ordinal:1}}}});
c.hydrate({canvas_revision:102, node:{id:'node-3'}});
console.log(JSON.stringify({attr:host.attrs['data-result-materialization'], html:host.innerHTML, snap:c.snapshot()}));
""", SEAM)
        self.assertEqual(payload["attr"], "workbench.node/1")
        self.assertEqual(payload["snap"]["revision"], 102)
        self.assertEqual([entry["id"] for entry in payload["snap"]["nodes"]], ['node"1', "node-2"])
        self.assertEqual(payload["snap"]["count"], 2)
        for fragment in ('data-result-node="node&quot;1"', 'data-result-node="node-2"',
                         'data-result-run="&lt;run&gt;&amp;1"',
                         'data-result-output="thumb.png"', 'data-result-ordinal="1"'):
            self.assertIn(fragment, payload["html"], msg=f"row must carry {fragment}")
        self.assertNotIn("<run>&1", payload["html"])
        self.assertNotIn("<x>\"&", payload["html"])
        self.assertNotIn('"node"1"', payload["html"])

    def test_hydrating_the_same_node_twice_does_not_duplicate_it(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const c=api.create({});
const host={attrs:{},setAttribute(){},removeAttribute(){},innerHTML:''};
c.mount(host);
const node={canvas_revision:100, node:{id:'node-1', title:'Hero', provenance_ref:'run-1',
  config:{result:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0}}}};
c.hydrate(node); c.hydrate(node);
console.log(JSON.stringify(c.snapshot()));
""", SEAM)
        self.assertEqual(payload["count"], 1)

    def test_unmounting_leaves_no_trace(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const mounted=api.create({}).mount(host);
mounted.hydrate({canvas_revision:100, node:{id:'node-1', title:'Hero', provenance_ref:'run-1',
  config:{result:{run_id:'r', attempt_id:'a', output_name:'o', ordinal:0}}}});
mounted.destroy();
console.log(JSON.stringify({attrs:host.attrs, html:host.innerHTML}));
""", SEAM)
        self.assertEqual(payload["attrs"], {})
        self.assertEqual(payload["html"], "")

    def test_a_destroyed_seam_stops_writing_to_its_host(self):
        # Unmounting has to detach, not just clear: a seam still bound to a host
        # would keep rendering into a node nobody is looking at.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultMaterialization;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const mounted=api.create({}).mount(host);
mounted.hydrate({canvas_revision:100, node:{id:'node-1', title:'Hero',
  config:{result:{run_id:'r', attempt_id:'a', output_name:'o', ordinal:0}}}});
mounted.destroy();
mounted.hydrate({canvas_revision:101, node:{id:'node-2', title:'Later',
  config:{result:{run_id:'r', attempt_id:'a', output_name:'o2', ordinal:1}}}});
console.log(JSON.stringify({html:host.innerHTML, attrs:host.attrs}));
""", SEAM)
        # A detached seam may still hold state, but it must never render into a
        # host that has already been torn down.
        self.assertEqual(payload["html"], "")
        self.assertEqual(payload["attrs"], {})

    def test_seam_owns_no_transport_and_never_converts_a_result(self):
        source = SEAM.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TRANSPORT_MARKERS + FORBIDDEN_CONVERSION_MARKERS:
            self.assertNotIn(marker, source, msg=f"materialization seam must not reference {marker}")

    def test_canvas_page_and_node_shell_register_the_seam(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-materialization-runtime.js"), 1)
        self.assertEqual(page.count("workbench/canvas/result-materialization-api-client.js"), 1)
        self.assertLess(page.index("result-collection-runtime.js"), page.index("result-materialization-runtime.js"))
        self.assertLess(page.index("result-materialization-runtime.js"), page.index("canvas-app-bootstrap.js"))

        # The seam is actually reachable: the node shell mounts it when the host
        # supplies options, rather than leaving it registered but unused.
        node = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        self.assertIn("function mountResultMaterialization(host, options)", node)
        self.assertIn("mountResultMaterialization,", node)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("settings.resultMaterializationOptions", shell)
        self.assertIn("mountResultMaterialization(resultMaterializationHost", shell)
        self.assertIn("data-result-materialization-host", shell)
        self.assertIn("mountedResultMaterialization?.destroy?.()", shell)

    def test_client_sends_the_canonical_request(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultMaterializationApiClient;
const calls=[];
const fakeFetch=async (url,options)=>{calls.push({url,method:options.method,headers:options.headers,body:options.body?JSON.parse(options.body):null});return {ok:true,status:201,json:async()=>({created:true})};};
const good={request_id:'req-1', project_id:'p1', run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0, position:{x:1,y:2}};
(async()=>{
  await client.materialize('canvas/1', good, {actorId:'owner', fetch:fakeFetch});
  await client.materialize('c1', {...good, expected_revision:9, title:'Hero'}, {actorId:'owner', fetch:fakeFetch});
  let noActor='', noCanvas='', noRequest='', noRun='', noAttempt='', noOutput='', badOrdinal='';
  try { await client.materialize('c1', good, {fetch:fakeFetch}); } catch(e) { noActor=e.message; }
  try { await client.materialize('', good, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noCanvas=e.message; }
  try { await client.materialize('c1', {...good, request_id:''}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noRequest=e.message; }
  try { await client.materialize('c1', {...good, run_id:''}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noRun=e.message; }
  try { await client.materialize('c1', {...good, attempt_id:''}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noAttempt=e.message; }
  try { await client.materialize('c1', {...good, output_name:''}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noOutput=e.message; }
  try { await client.materialize('c1', {...good, ordinal:-1}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { badOrdinal=e.message; }
  console.log(JSON.stringify({calls, noActor, noCanvas, noRequest, noRun, noAttempt, noOutput, badOrdinal}));
})();
""", CLIENT)
        escaped, plain = payload["calls"]
        self.assertEqual(escaped["url"], "/api/v1/canvases/canvas%2F1/result-nodes")
        self.assertEqual(escaped["method"], "POST")
        self.assertEqual(escaped["headers"]["X-User-ID"], "owner")
        self.assertEqual(escaped["headers"]["Content-Type"], "application/json")
        self.assertEqual(escaped["body"], {
            "request_id": "req-1", "project_id": "p1", "run_id": "run-1", "attempt_id": "a1",
            "output_name": "poster.png", "ordinal": 0, "position": {"x": 1, "y": 2},
        })
        self.assertEqual(plain["url"], "/api/v1/canvases/c1/result-nodes")
        self.assertEqual(plain["body"]["expected_revision"], 9)
        self.assertEqual(plain["body"]["title"], "Hero")
        self.assertIn("actor id", payload["noActor"])
        self.assertIn("canvas id", payload["noCanvas"])
        self.assertIn("request id", payload["noRequest"])
        self.assertIn("run id", payload["noRun"])
        self.assertIn("attempt id", payload["noAttempt"])
        self.assertIn("output name", payload["noOutput"])
        self.assertIn("non-negative ordinal", payload["badOrdinal"])

    def test_client_surfaces_the_api_error_message(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultMaterializationApiClient;
const fakeFetch=async ()=>({ok:false,status:409,json:async()=>({detail:{code:'result_not_selected',message:'result is not selected: poster.png#1'}})});
(async()=>{
  let message='';
  try { await client.materialize('c1', {request_id:'r', run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:1, position:{x:0,y:0}}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { message=e.message; }
  console.log(JSON.stringify({message}));
})();
""", CLIENT)
        self.assertIn("poster.png#1", payload["message"])


if __name__ == "__main__":
    unittest.main()
