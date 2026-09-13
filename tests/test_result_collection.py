"""Focused tests for the R8-21 Result to Collection card.

The DoD is "Selected results can populate a Collection without Canvas node
creation", so the load-bearing test collects a run's selected results and then
asserts both halves: the items carry the four-part result identity, and no
Canvas was touched at all. The rest pin what the card declares — only what the
user selected is collected, the lineage is preserved, and a result is never
converted into an Asset or an Artifact to get there.
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

from workbench.api.result_collections import create_result_collections_router
from workbench.application.collection_service import CollectionService
from workbench.application.execution_run_service import ExecutionRunService
from workbench.application.result_collection_service import ResultCollectionNotFoundServiceError, ResultCollectionService, ResultCollectionServiceError
from workbench.application.result_selection_service import ResultSelectionService
from workbench.domain.collection import Collection, CollectionColumn, CollectionExecutionResultCell, CollectionItem, CollectionSchema
from workbench.domain.execution import ExecutionInputProjection, ExecutionPolicy, ExecutionRun
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.collection_repository import SqliteCollectionRepository
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.result_selection_repository import SqliteResultSelectionRepository
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


ROOT = Path(__file__).resolve().parents[1]
SEAM = ROOT / "static/js/workbench/canvas/result-collection-runtime.js"
CLIENT = ROOT / "static/js/workbench/canvas/result-collection-api-client.js"

# A collection seam owns no transport and never builds a Canvas node.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
FORBIDDEN_NODE_MARKERS = ("createNode", "addNode", "materializeToCanvas", "promoteToCanvas", "/api/canvas-nodes", "/api/v1/canvases")
# A result is collected as itself; converting it is a later card's job.
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


class ResultCollectionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        self._item_seq = itertools.count(1)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.now)
        projects.create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        projects.add_member(ProjectMember(project_id="project-1", actor_id="viewer", role="viewer", created_at=self.now))
        # A second project so collecting across the boundary can be attempted.
        projects.create_project(ProjectRecord(
            id="project-2", name="Other", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        runs = SqliteExecutionRunRepository(self.database, clock=lambda: self.now)
        for run_id, project_id in (("run-1", "project-1"), ("run-empty", "project-1"), ("run-other", "project-2")):
            runs.create(ExecutionRun(
                id=run_id, project_id=project_id, task_id="task-1", execution_profile_ref="profile@1",
                policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
                input_projection=ExecutionInputProjection(inputs=[]), created_at=self.now,
            ), actor_id="owner")
        self._selection_ids = itertools.count(1)
        selection_service = ResultSelectionService(
            SqliteResultSelectionRepository(self.database, clock=lambda: self.now),
            actor_id="owner", id_factory=lambda: f"selection-{next(self._selection_ids)}", clock=lambda: self.now,
        )
        # What the user decided: two of the three results are selected.
        for attempt_id, output_name, ordinal, selected in (
            ("attempt-1", "poster.png", 0, True),
            ("attempt-1", "poster.png", 1, False),
            ("attempt-2", "thumb.png", 0, True),
        ):
            selection_service.create(
                run_id="run-1", attempt_id=attempt_id, output_name=output_name,
                ordinal=ordinal, selected=selected,
            )
        self.collection_repository().create(Collection(
            id="collection-1", project_id="project-1", name="Picks",
            collection_schema=CollectionSchema(id="schema-1", name="Picks", columns=[]),
        ), actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def collection_repository(self):
        return SqliteCollectionRepository(self.database, clock=lambda: self.now)

    def collection_service(self, actor_id="owner"):
        return CollectionService(self.collection_repository(), actor_id=actor_id)

    def selection_service(self, actor_id="owner"):
        return ResultSelectionService(
            SqliteResultSelectionRepository(self.database, clock=lambda: self.now),
            actor_id=actor_id, id_factory=lambda: f"selection-{next(self._selection_ids)}", clock=lambda: self.now,
        )

    def run_service(self, actor_id="owner"):
        return ExecutionRunService(SqliteExecutionRunRepository(self.database, clock=lambda: self.now), actor_id=actor_id)

    def service(self, actor_id="owner", item_id=None):
        factory = (lambda: item_id) if item_id is not None else (lambda: f"item-{next(self._item_seq)}")
        return ResultCollectionService(
            self.collection_service(actor_id), self.selection_service(actor_id), self.run_service(actor_id),
            actor_id=actor_id, id_factory=factory,
        )

    def canvas_count(self) -> int:
        with self.collection_repository()._connection() as connection:
            return connection.execute("SELECT COUNT(*) AS total FROM canvases").fetchone()["total"]

    def test_selected_results_populate_a_collection_without_canvas_nodes(self):
        # The DoD, both halves: the items carry the lineage, and no Canvas was
        # created to get them there.
        self.assertEqual(self.canvas_count(), 0)
        updated = self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        self.assertEqual(updated.revision, 2)
        self.assertEqual(len(updated.items), 2)
        self.assertEqual(
            [(item.values["result"].run_id, item.values["result"].attempt_id,
              item.values["result"].output_name, item.values["result"].ordinal) for item in updated.items],
            [("run-1", "attempt-1", "poster.png", 0), ("run-1", "attempt-2", "thumb.png", 0)],
        )
        # Collected as a result, not converted into an Asset or an Artifact.
        self.assertIsInstance(updated.items[0].values["result"], CollectionExecutionResultCell)
        self.assertEqual(self.canvas_count(), 0)

        # And it is really stored that way, not merely returned.
        reopened = self.collection_service().get("collection-1")
        self.assertEqual(len(reopened.items), 2)
        self.assertEqual(reopened.items[0].values["result"].output_name, "poster.png")

    def test_the_result_cell_rejects_out_of_contract_values(self):
        base = dict(run_id="run-1", attempt_id="attempt-1")
        with self.assertRaises(ValueError):
            CollectionExecutionResultCell(**base, output_name="", ordinal=0)
        with self.assertRaises(ValueError):
            CollectionExecutionResultCell(**base, output_name="poster.png", ordinal=-1)
        # Every part of the identity is required: a blank attempt would point at
        # the wrong result rather than at none.
        with self.assertRaises(ValueError):
            CollectionExecutionResultCell(run_id="run-1", attempt_id="", output_name="poster.png", ordinal=0)
        # The cell is closed: an unknown field is refused rather than dropped.
        with self.assertRaises(ValueError):
            CollectionExecutionResultCell(**base, output_name="poster.png", ordinal=0, unexpected="x")

    def test_a_taken_column_id_is_refused(self):
        self.collection_repository().create(Collection(
            id="collection-4", project_id="project-1", name="Odd",
            collection_schema=CollectionSchema(id="schema-4", name="Odd", columns=[
                CollectionColumn(id="result", key="chosen", label="Chosen", value_type="literal"),
            ]),
        ), actor_id="owner")
        with self.assertRaises(ResultCollectionServiceError) as caught:
            self.service().add_selected(collection_id="collection-4", run_id="run-1", expected_revision=1, column_key="result")
        self.assertEqual(caught.exception.code, "column_conflict")

    def test_an_aggregate_that_cannot_be_validated_is_not_stored(self):
        # The new item id collides with one already there. The aggregate is
        # refused rather than persisted with duplicate item ids, which is what
        # `CollectionService.update` would do on its own because it copies
        # without re-running validators.
        self.collection_repository().create(Collection(
            id="collection-5", project_id="project-1", name="Fixed",
            collection_schema=CollectionSchema(id="schema-5", name="Fixed", columns=[
                CollectionColumn(id="result", key="result", label="Result", value_type="execution_result"),
            ]),
            items=[CollectionItem(id="item-dup", order=0, values={})],
        ), actor_id="owner")
        with self.assertRaises(ResultCollectionServiceError) as caught:
            self.service(item_id="item-dup").add_selected(collection_id="collection-5", run_id="run-1", expected_revision=1)
        self.assertEqual(caught.exception.code, "invalid_collection")
        self.assertEqual(len(self.collection_service().get("collection-5").items), 1)

    def test_only_what_the_user_selected_is_collected(self):
        updated = self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        collected = {(item.values["result"].attempt_id, item.values["result"].ordinal) for item in updated.items}
        self.assertEqual(collected, {("attempt-1", 0), ("attempt-2", 0)})
        self.assertNotIn(("attempt-1", 1), collected)

    def test_the_collection_gains_a_typed_column_when_it_has_none(self):
        updated = self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1, column_key="chosen")
        column = next(column for column in updated.collection_schema.columns if column.key == "chosen")
        self.assertEqual(column.value_type, "execution_result")

    def test_an_existing_column_of_another_type_is_never_retyped(self):
        self.collection_repository().create(Collection(
            id="collection-2", project_id="project-1", name="Notes",
            collection_schema=CollectionSchema(id="schema-2", name="Notes", columns=[
                CollectionColumn(id="result", key="result", label="Result", value_type="literal"),
            ]),
        ), actor_id="owner")
        with self.assertRaises(ResultCollectionServiceError) as caught:
            self.service().add_selected(collection_id="collection-2", run_id="run-1", expected_revision=1)
        self.assertEqual(caught.exception.code, "column_type_mismatch")
        # The refused write left the schema alone.
        self.assertEqual(self.collection_service().get("collection-2").collection_schema.columns[0].value_type, "literal")

    def test_a_run_without_a_selection_is_reported_rather_than_ignored(self):
        with self.assertRaises(ResultCollectionServiceError) as caught:
            self.service().add_selected(collection_id="collection-1", run_id="run-empty", expected_revision=1)
        self.assertEqual(caught.exception.code, "nothing_selected")

    def test_an_unknown_collection_or_run_is_absent(self):
        with self.assertRaises(ResultCollectionNotFoundServiceError):
            self.service().add_selected(collection_id="missing", run_id="run-1", expected_revision=1)
        with self.assertRaises(ResultCollectionNotFoundServiceError):
            self.service().add_selected(collection_id="collection-1", run_id="missing-run", expected_revision=1)

    def test_a_stale_revision_is_refused_and_leaves_the_collection_alone(self):
        self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        with self.assertRaises(ResultCollectionServiceError) as caught:
            self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        self.assertEqual(caught.exception.code, "stale_revision")
        self.assertEqual(len(self.collection_service().get("collection-1").items), 2)

    def test_a_result_may_not_be_collected_into_another_project(self):
        self.collection_repository().create(Collection(
            id="collection-3", project_id="project-2", name="Other picks",
            collection_schema=CollectionSchema(id="schema-3", name="Other picks", columns=[]),
        ), actor_id="owner")
        with self.assertRaises(ResultCollectionServiceError) as caught:
            # A collection in project-2 holding a result from project-1 would be
            # unreadable by the people who can read the result.
            self.service().add_selected(collection_id="collection-3", run_id="run-1", expected_revision=1)
        self.assertEqual(caught.exception.code, "cross_project")

    def test_appending_twice_keeps_orders_unique(self):
        first = self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        second = self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=first.revision)
        self.assertEqual(len(second.items), 4)
        orders = [item.order for item in second.items]
        self.assertEqual(len(orders), len(set(orders)))
        self.assertEqual(orders, sorted(orders))

    def test_authorization_is_enforced_on_collect_and_on_read(self):
        with self.assertRaises(PermissionError):
            self.service(actor_id="viewer").add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        with self.assertRaises(PermissionError):
            self.service(actor_id="stranger").add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        # Nothing was written by either refusal.
        self.assertEqual(len(self.collection_service().get("collection-1").items), 0)

    def test_audit_records_the_collection_update(self):
        self.service().add_selected(collection_id="collection-1", run_id="run-1", expected_revision=1)
        with self.collection_repository()._connection() as connection:
            rows = connection.execute(
                "SELECT event_type FROM audit_outbox WHERE event_type LIKE 'collection.%' ORDER BY rowid"
            ).fetchall()
        self.assertEqual([row["event_type"] for row in rows], ["collection.created", "collection.updated"])

    def client(self):
        def factory(actor_id):
            return self.service(actor_id=actor_id)

        app = FastAPI()
        app.include_router(create_result_collections_router(service_factory=factory))
        return TestClient(app)

    def test_api_reports_the_outcomes(self):
        client = self.client()
        added = client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 1,
        })
        self.assertEqual(added.status_code, 200)
        self.assertEqual(len(added.json()["items"]), 2)
        # An absent Collection and an absent run are both 404.
        self.assertEqual(client.post("/api/v1/collections/missing/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 1,
        }).status_code, 404)
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "missing-run", "expected_revision": 2,
        }).status_code, 404)
        # A stale revision is a conflict, and a field the contract lacks is refused.
        stale = client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 1,
        })
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["detail"]["code"], "stale_revision")
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 2, "unexpected": "x",
        }).status_code, 422)
        # Appending is a write to a shared aggregate, so a zero revision is refused.
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 0,
        }).status_code, 422)
        # Identifiers are addressed by a non-empty, bounded name.
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "", "expected_revision": 2,
        }).status_code, 422)
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "owner"}, json={
            "run_id": "run-1", "expected_revision": 2, "column_key": "",
        }).status_code, 422)
        # A missing actor is rejected, and a viewer is forbidden.
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", json={
            "run_id": "run-1", "expected_revision": 2,
        }).status_code, 401)
        self.assertEqual(client.post("/api/v1/collections/collection-1/results", headers={"X-User-ID": "viewer"}, json={
            "run_id": "run-1", "expected_revision": 2,
        }).status_code, 403)

    def test_composition_root_registers_the_route(self):
        # Every other test builds its own app, so this is the only place the real
        # wiring is checked.
        import main

        if not main.WORKBENCH_NODE_API_ENABLED:
            self.skipTest("the node API is disabled for this host")
        paths = main.app.openapi()["paths"]
        self.assertIn("/api/v1/collections/{collection_id}/results", paths)
        self.assertIn("post", paths["/api/v1/collections/{collection_id}/results"])

    def test_core_modules_stay_industry_neutral(self):
        for relative in (
            "workbench/application/result_collection_service.py",
            "workbench/api/result_collections.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("wholehouse", source, msg=f"{relative} must stay industry-neutral")


class ResultCollectionSeamTests(unittest.TestCase):
    def test_a_record_keeps_the_four_part_identity(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCollection;
console.log(JSON.stringify({
  complete: api.recordFrom({id:'item-1', order:0, values:{result:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:2}}}),
  noCell: api.recordFrom({id:'item-2', order:1, values:{}}),
  partial: api.recordFrom({id:'item-3', order:2, values:{result:{run_id:'run-1', attempt_id:'a1'}}}),
  literalCell: api.recordFrom({id:'item-4', order:3, values:{result:{type:'literal', value:'x'}}}),
  emptyName: api.recordFrom({id:'item-5', order:4, values:{result:{run_id:'run-1', attempt_id:'a1', output_name:'', ordinal:0}}}),
}));
""", SEAM)
        self.assertEqual(payload["complete"], {"id": "item-1", "order": 0, "run_id": "run-1", "attempt_id": "a1", "output_name": "poster.png", "ordinal": 2})
        # An empty part is as good as a missing one: a blank name would point at
        # the wrong result rather than at none.
        for key in ("noCell", "partial", "literalCell", "emptyName"):
            self.assertIsNone(payload[key], msg=f"{key} must be ignored rather than half-rendered")

    def test_request_is_validated_with_explicit_reasons(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCollection;
console.log(JSON.stringify({
  accepted: api.requestFrom({collection_id:'c1', run_id:'run-1', expected_revision:3}),
  defaulted: api.requestFrom({collection_id:'c1', run_id:'run-1', expected_revision:1}),
  noCollection: api.requestFrom({run_id:'run-1', expected_revision:1}),
  noRun: api.requestFrom({collection_id:'c1', expected_revision:1}),
  zeroRevision: api.requestFrom({collection_id:'c1', run_id:'run-1', expected_revision:0}),
}));
""", SEAM)
        self.assertEqual(payload["accepted"]["reason"], "accepted")
        self.assertEqual(payload["accepted"]["request"]["expected_revision"], 3)
        self.assertEqual(payload["defaulted"]["request"]["column_key"], "result")
        self.assertEqual(payload["noCollection"]["reason"], "unknown_collection")
        self.assertEqual(payload["noRun"]["reason"], "unknown_run")
        self.assertEqual(payload["zeroRevision"]["reason"], "bad_revision")
        self.assertIsNone(payload["zeroRevision"]["request"])

    def test_mounted_rows_carry_the_lineage_and_are_escaped(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCollection;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const c=api.create({});
c.mount(host);
c.hydrate({collection_id:'c1', revision:2, items:[
  {id:'i1', order:1, values:{result:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0}}},
  {id:'i"2', order:0, values:{result:{run_id:'<run>&1', attempt_id:'a1', output_name:'thumb.png', ordinal:1}}},
  {id:'i3', order:2, values:{}},
]});
console.log(JSON.stringify({attr:host.attrs['data-result-collection'], html:host.innerHTML, snap:c.snapshot()}));
""", SEAM)
        self.assertEqual(payload["attr"], "workbench.collection/1")
        # The revision that came back from persistence is what a further append
        # would have to name, so it is kept rather than defaulted.
        self.assertEqual(payload["snap"]["revision"], 2)
        # Ordered by the item's order, and the item with no result cell is dropped.
        self.assertEqual([entry["id"] for entry in payload["snap"]["items"]], ['i"2', "i1"])
        self.assertEqual(payload["snap"]["count"], 2)
        for fragment in ('data-result-id="i&quot;2"', 'data-result-run="&lt;run&gt;&amp;1"',
                         'data-result-output="thumb.png"', 'data-result-ordinal="1"'):
            self.assertIn(fragment, payload["html"], msg=f"row must carry {fragment}")
        self.assertNotIn("<run>&1", payload["html"])

    def test_unmounting_leaves_no_trace(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCollection;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const mounted=api.create({}).mount(host);
mounted.hydrate({collection_id:'c1', revision:1, items:[{id:'i1', order:0, values:{result:{run_id:'r', attempt_id:'a', output_name:'o', ordinal:0}}}]});
mounted.destroy();
console.log(JSON.stringify({attrs:host.attrs, html:host.innerHTML}));
""", SEAM)
        self.assertEqual(payload["attrs"], {})
        self.assertEqual(payload["html"], "")

    def test_a_custom_column_key_is_honoured_end_to_end(self):
        # The API lets a caller choose the column, so the seam must be able both
        # to ask for it and to read it back — a seam hard-coded to `result` would
        # make a real capability unreachable from the only client.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultCollection;
const host={attrs:{},setAttribute(n,v){this.attrs[n]=v;},removeAttribute(n){delete this.attrs[n];},innerHTML:''};
const c=api.create({columnKey:'chosen'});
c.mount(host);
c.hydrate({collection_id:'c1', revision:3, items:[
  {id:'i1', order:0, values:{chosen:{run_id:'run-1', attempt_id:'a1', output_name:'poster.png', ordinal:0}}},
  {id:'i2', order:1, values:{result:{run_id:'run-1', attempt_id:'a9', output_name:'ignored.png', ordinal:9}}},
]});
console.log(JSON.stringify({
  snap:c.snapshot(),
  request:c.requestFrom({collection_id:'c1', run_id:'run-1', expected_revision:3}),
  html:host.innerHTML,
}));
""", SEAM)
        self.assertEqual(payload["snap"]["count"], 1)
        # Only the chosen column counts; the `result` column is not this seam's.
        self.assertEqual(payload["snap"]["items"][0]["attempt_id"], "a1")
        self.assertEqual(payload["request"]["request"]["column_key"], "chosen")
        self.assertIn('data-result-output="poster.png"', payload["html"])
        self.assertNotIn("ignored.png", payload["html"])

    def test_seam_owns_no_transport_and_never_creates_nodes(self):
        source = SEAM.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TRANSPORT_MARKERS + FORBIDDEN_NODE_MARKERS + FORBIDDEN_CONVERSION_MARKERS:
            self.assertNotIn(marker, source, msg=f"collection seam must not reference {marker}")

    def test_canvas_page_and_node_shell_register_the_seam(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-collection-runtime.js"), 1)
        self.assertEqual(page.count("workbench/canvas/result-collection-api-client.js"), 1)
        self.assertLess(page.index("execution-branch-runtime.js"), page.index("result-collection-runtime.js"))
        self.assertLess(page.index("result-collection-runtime.js"), page.index("canvas-app-bootstrap.js"))

        # The seam is actually reachable: the node shell mounts it when the host
        # supplies options, rather than leaving it registered but unused.
        node = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        self.assertIn("function mountResultCollection(host, options)", node)
        self.assertIn("mountResultCollection,", node)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        self.assertIn("settings.resultCollectionOptions", shell)
        self.assertIn("mountResultCollection(resultCollectionHost", shell)
        self.assertIn("data-result-collection-host", shell)
        self.assertIn("mountedResultCollection?.destroy?.()", shell)

    def test_client_sends_the_canonical_request(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultCollectionApiClient;
const calls=[];
const fakeFetch=async (url,options)=>{calls.push({url,method:options.method,headers:options.headers,body:options.body?JSON.parse(options.body):null});return {ok:true,status:200,json:async()=>({id:'c1',revision:2})};};
(async()=>{
  await client.add('coll/1', {run_id:'run-1', expected_revision:4}, {actorId:'owner', fetch:fakeFetch});
  await client.add('c1', {run_id:'run-1', expected_revision:1}, {actorId:'owner', fetch:fakeFetch});
  let noActor='', noRun='', zeroRevision='';
  try { await client.add('c1', {run_id:'run-1', expected_revision:1}, {fetch:fakeFetch}); } catch(e) { noActor=e.message; }
  try { await client.add('c1', {expected_revision:1}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { noRun=e.message; }
  try { await client.add('c1', {run_id:'run-1', expected_revision:0}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { zeroRevision=e.message; }
  console.log(JSON.stringify({calls, noActor, noRun, zeroRevision}));
})();
""", CLIENT)
        escaped, plain = payload["calls"]
        # The collection id is a path segment, so it is escaped.
        self.assertEqual(escaped["url"], "/api/v1/collections/coll%2F1/results")
        self.assertEqual(escaped["method"], "POST")
        self.assertEqual(escaped["headers"]["X-User-ID"], "owner")
        self.assertEqual(escaped["headers"]["Content-Type"], "application/json")
        self.assertEqual(escaped["body"], {"run_id": "run-1", "expected_revision": 4, "column_key": "result"})
        self.assertEqual(plain["url"], "/api/v1/collections/c1/results")
        self.assertIn("actor id", payload["noActor"])
        self.assertIn("run id", payload["noRun"])
        self.assertIn("positive expected revision", payload["zeroRevision"])

    def test_client_surfaces_the_api_error_message(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultCollectionApiClient;
const fakeFetch=async ()=>({ok:false,status:409,json:async()=>({detail:{code:'stale_revision',message:'collection revision is stale; current revision is 7'}})});
(async()=>{
  let message='';
  try { await client.add('c1', {run_id:'run-1', expected_revision:1}, {actorId:'owner', fetch:fakeFetch}); } catch(e) { message=e.message; }
  console.log(JSON.stringify({message}));
})();
""", CLIENT)
        self.assertIn("current revision is 7", payload["message"])


if __name__ == "__main__":
    unittest.main()
