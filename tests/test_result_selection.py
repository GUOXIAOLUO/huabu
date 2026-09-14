"""Focused tests for the R8-19 Result Selection and Rating card.

The DoD is "Candidate preference survives reload", so the load-bearing test
writes a preference and then reads it back through a *fresh* repository, service
and HTTP client over the same database file. The rest of the suite pins the
boundaries the card declares: a result is identified by the attempt plus output
name plus ordinal, the rating is user-assigned rather than computed, and no
approval or frozen state is modelled.
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

from workbench.api.result_selections import create_result_selections_router
from workbench.application.result_selection_service import ResultSelectionNotFoundServiceError, ResultSelectionService, ResultSelectionServiceError
from workbench.domain.execution import (
    RESULT_SELECTION_MAX_COMMENT_LENGTH,
    RESULT_SELECTION_MAX_RATING,
    RESULT_SELECTION_MIN_RATING,
    ExecutionInputProjection,
    ExecutionPolicy,
    ExecutionRun,
    ResultSelection,
)
from workbench.domain.project.models import ProjectMember, ProjectRecord
from workbench.repositories.execution_run_repository import SqliteExecutionRunRepository
from workbench.repositories.result_selection_repository import (
    ResultSelectionConflictError,
    ResultSelectionNotFoundError,
    ResultSelectionStaleRevisionError,
    SqliteResultSelectionRepository,
)
from workbench.repositories.sqlite_project_canvas_repository import SqliteProjectCanvasRepository


ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "static/js/workbench/canvas/result-selection-runtime.js"
CLIENT = ROOT / "static/js/workbench/canvas/result-selection-api-client.js"
ASSET_CLIENT = ROOT / "static/js/workbench/canvas/result-asset-materialization-api-client.js"

# A preference seam owns no transport and no client persistence.
FORBIDDEN_TRANSPORT_MARKERS = ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "require(")
# The rating is what the user assigned; nothing may compute, rank or weight it.
FORBIDDEN_SCORING_MARKERS = ("score", "rank", "weight", "confidence", "similarity")
# Out of scope: no Approval/Frozen semantics. Freezing a design is a later,
# separate concept, so a preference record may not carry or imply one.
FORBIDDEN_APPROVAL_MARKERS = ("approval", "approve", "freeze", "frozen", "locked", "signoff", "sign_off")
# A preference seam never promotes a result into a Canvas node.
FORBIDDEN_MUTATION_MARKERS = ("createNode", "addNode", "materialize", "promoteToCanvas", "graphMutation", "/api/canvas-nodes")


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


class ResultSelectionPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "workbench.sqlite3"
        self.now = datetime(2026, 9, 12, tzinfo=UTC)
        projects = SqliteProjectCanvasRepository(self.database, clock=lambda: self.now)
        projects.create_project(ProjectRecord(
            id="project-1", name="Project", workspace_id="local", created_by="owner",
            created_at=self.now, updated_at=self.now,
        ))
        projects.add_member(ProjectMember(project_id="project-1", actor_id="viewer", role="viewer", created_at=self.now))
        SqliteExecutionRunRepository(self.database, clock=lambda: self.now).create(ExecutionRun(
            id="run-1", project_id="project-1", task_id="task-1", execution_profile_ref="profile@1",
            policy=ExecutionPolicy(mode="batch", concurrency=1, retry=0),
            input_projection=ExecutionInputProjection(inputs=[{
                "input_id": "input-1", "binding_id": "binding-1", "target": "task.prompt", "role": "prompt",
                "order": 0, "source_type": "literal", "source_ref": "literal-1", "value": "one", "source_snapshot": "one",
            }]),
            created_at=self.now,
        ), actor_id="owner")

    def tearDown(self):
        self.temp.cleanup()

    def repository(self):
        return SqliteResultSelectionRepository(self.database, clock=lambda: self.now)

    def service(self, actor_id="owner", selection_id=None):
        # A real caller supplies a unique id per record; a service that minted the
        # same id twice would collide on the primary key rather than on the
        # per-result uniqueness this suite is pinning.
        if selection_id is None:
            counter = itertools.count(1)
            factory = lambda: f"selection-{next(counter)}"
        else:
            factory = lambda: selection_id
        return ResultSelectionService(self.repository(), actor_id=actor_id, id_factory=factory, clock=lambda: self.now)

    def test_candidate_preference_survives_reload(self):
        # The DoD, end to end: write a preference, then read it back through a
        # fresh repository and service over the same database file.
        created = self.service().create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0, selected=True, favorite=True, rating=4, comment="strongest composition")
        self.assertEqual((created.schema_version, created.revision), ("workbench.result-selection/1", 1))

        reopened = self.service(selection_id="unused").list_for_run("run-1")
        self.assertEqual(len(reopened), 1)
        record = reopened[0]
        self.assertEqual((record.attempt_id, record.output_name, record.ordinal), ("attempt-1", "poster", 0))
        self.assertEqual((record.selected, record.favorite, record.rating, record.comment), (True, True, 4, "strongest composition"))

        # The HTTP boundary re-reads the same preference after a reload too.
        client = self.client()
        response = client.get("/api/v1/execution-runs/run-1/selections", headers={"X-User-ID": "owner"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual((payload[0]["favorite"], payload[0]["rating"], payload[0]["comment"]), (True, 4, "strongest composition"))

    def test_update_restates_the_whole_preference_and_identity_is_fixed(self):
        service = self.service()
        created = service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0, selected=True, rating=4, comment="first")
        # A restatement clears the rating rather than treating None as "unchanged".
        updated = service.update("selection-1", expected_revision=1, selected=False, favorite=True, rating=None, comment="")
        self.assertEqual((updated.selected, updated.favorite, updated.rating, updated.comment), (False, True, None, ""))
        self.assertEqual(updated.revision, 2)
        # Identity is fixed at creation and cannot be re-pointed by an update.
        self.assertEqual((updated.run_id, updated.attempt_id, updated.output_name, updated.ordinal), ("run-1", "attempt-1", "poster", 0))
        # Metadata is restated with the rest of the preference, not merged.
        restated = service.update("selection-1", expected_revision=2, selected=False, favorite=False, rating=None, comment="", metadata={"note": "second"})
        self.assertEqual(restated.metadata, {"note": "second"})
        # A created record leaves updated_at unset; every restatement stamps it.
        self.assertIsNone(created.updated_at)
        self.assertEqual(updated.updated_at, self.now)
        self.assertEqual(restated.updated_at, self.now)

    def test_rating_bounds_and_comment_length_are_validated(self):
        service = self.service()
        with self.assertRaises(Exception):
            service.create(run_id="run-1", attempt_id="a", output_name="o", ordinal=0, rating=RESULT_SELECTION_MAX_RATING + 1)
        with self.assertRaises(Exception):
            service.create(run_id="run-1", attempt_id="a", output_name="o", ordinal=0, rating=RESULT_SELECTION_MIN_RATING - 1)
        with self.assertRaises(Exception):
            service.create(run_id="run-1", attempt_id="a", output_name="o", ordinal=0, comment="x" * (RESULT_SELECTION_MAX_COMMENT_LENGTH + 1))
        # A boundary rating is accepted.
        record = service.create(run_id="run-1", attempt_id="a", output_name="o", ordinal=0, rating=RESULT_SELECTION_MAX_RATING)
        self.assertEqual(record.rating, RESULT_SELECTION_MAX_RATING)

    def test_stale_revision_is_rejected_and_reports_the_current_one(self):
        service = self.service()
        service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0)
        service.update("selection-1", expected_revision=1, selected=True, favorite=False, rating=None, comment="")
        with self.assertRaises(ResultSelectionStaleRevisionError) as caught:
            self.repository().update("selection-1", expected_revision=1, actor_id="owner", selected=False, favorite=False, rating=None, comment="", metadata={})
        self.assertEqual(caught.exception.current_revision, 2)
        # The refused write left nothing behind: the stored revision is untouched
        # and the preference still reads back as the accepted one.
        stored = self.repository().get("selection-1", actor_id="owner")
        self.assertEqual(stored.revision, 2)
        self.assertTrue(stored.selected)

    def test_record_rejects_out_of_contract_values(self):
        base = dict(id="selection-x", run_id="run-1", attempt_id="attempt-1", output_name="poster", created_at=self.now)
        with self.assertRaises(ValueError):
            ResultSelection(**base, ordinal=-1)
        with self.assertRaises(ValueError):
            ResultSelection(**base, ordinal=0, revision=0)
        # The record is closed: an unknown field is refused rather than dropped.
        with self.assertRaises(ValueError):
            ResultSelection(**base, ordinal=0, unexpected="x")
        # A metadata bag may not smuggle credentials.
        with self.assertRaises(ValueError):
            ResultSelection(**base, ordinal=0, metadata={"api_key": "leaked"})
        # The record is addressed by a non-empty output name, and its schema is
        # pinned so a migration cannot be silently mislabelled.
        with self.assertRaises(ValueError):
            ResultSelection(**{**base, "output_name": ""}, ordinal=0)
        with self.assertRaises(ValueError):
            ResultSelection(**base, ordinal=0, schema_version="workbench.result-selection/99")
        # A JSON-shaped bag is accepted and frozen.
        record = ResultSelection(**base, ordinal=0, metadata={"note": "ok"})
        self.assertEqual(record.metadata["note"], "ok")

    def test_one_record_per_result_and_authorization_is_enforced(self):
        service = self.service()
        service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0)
        with self.assertRaises(ResultSelectionConflictError):
            self.repository().create(ResultSelection(
                id="selection-2", run_id="run-1", attempt_id="attempt-1", output_name="poster",
                ordinal=0, created_at=self.now,
            ), actor_id="owner")
        # The same collision through the application boundary is a `conflict`,
        # which the API turns into a 409 rather than a silent second record.
        with self.assertRaises(ResultSelectionServiceError) as caught:
            service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0)
        self.assertEqual(caught.exception.code, "conflict")
        # A different output of the same attempt is a different result.
        other = service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=1)
        self.assertEqual(other.ordinal, 1)

        # A viewer may read the preference but may not change it.
        viewer = self.service(actor_id="viewer")
        self.assertEqual(len(viewer.list_for_run("run-1")), 2)
        with self.assertRaises(PermissionError):
            viewer.create(run_id="run-1", attempt_id="attempt-2", output_name="poster", ordinal=0)
        # A non-member cannot read it either.
        with self.assertRaises(PermissionError):
            self.service(actor_id="stranger").list_for_run("run-1")

        # Reading one record by id is authorized too, not just the listing: a
        # viewer may read it, and a non-member may not.
        self.assertEqual(viewer.get("selection-1").id, "selection-1")
        with self.assertRaises(PermissionError):
            self.repository().get("selection-1", actor_id="stranger")
        # Writing one record requires edit, which a viewer does not have.
        with self.assertRaises(PermissionError):
            self.repository().update("selection-1", expected_revision=1, actor_id="viewer", selected=True, favorite=False, rating=None, comment="", metadata={})
        # The refused write left the record untouched.
        self.assertFalse(self.repository().get("selection-1", actor_id="owner").selected)

    def test_audit_outbox_records_every_preference_change(self):
        service = self.service()
        service.create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0, selected=True)
        service.update("selection-1", expected_revision=1, selected=False, favorite=False, rating=None, comment="")
        with self.repository()._connection() as connection:
            rows = connection.execute(
                "SELECT event_type FROM audit_outbox WHERE event_type LIKE 'execution.result_selection.%' ORDER BY rowid"
            ).fetchall()
        self.assertEqual([row["event_type"] for row in rows], [
            "execution.result_selection.created", "execution.result_selection.updated",
        ])

    def test_listing_is_deterministically_ordered(self):
        # Persistence, not the caller, fixes the order: attempt, then output
        # name, then that output's occurrence in the batch.
        service = self.service()
        service.create(run_id="run-1", attempt_id="b", output_name="a", ordinal=1)
        service.create(run_id="run-1", attempt_id="a", output_name="b", ordinal=0)
        service.create(run_id="run-1", attempt_id="a", output_name="a", ordinal=2)
        service.create(run_id="run-1", attempt_id="a", output_name="a", ordinal=0)
        order = [(r.attempt_id, r.output_name, r.ordinal) for r in service.list_for_run("run-1")]
        self.assertEqual(order, [("a", "a", 0), ("a", "a", 2), ("a", "b", 0), ("b", "a", 1)])

    def test_a_comment_alone_is_a_preference(self):
        record = self.service().create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0, comment="worth keeping")
        self.assertTrue(record.has_preference())
        # Whitespace carries no decision, so it is not a preference.
        blank = self.service(selection_id="selection-blank").create(run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=1, comment="   ")
        self.assertFalse(blank.has_preference())

    def test_a_rating_alone_is_a_preference(self):
        # The rating is one of the four declared preference fields, so it counts
        # on its own even when nothing else was chosen.
        self.assertTrue(self.service().create(
            run_id="run-1", attempt_id="attempt-1", output_name="poster", ordinal=0, rating=3,
        ).has_preference())

    def test_the_record_is_immutable_and_its_metadata_is_frozen(self):
        # A canonical object is frozen: mutating it after validation, or
        # smuggling credentials into its metadata afterwards, must be refused.
        record = ResultSelection(
            id="selection-x", run_id="run-1", attempt_id="attempt-1", output_name="poster",
            ordinal=0, created_at=self.now, metadata={"note": "ok"},
        )
        with self.assertRaises(ValueError):
            record.selected = True
        with self.assertRaises(ValueError):
            record.metadata = {"api_key": "leaked"}
        with self.assertRaises(TypeError):
            record.metadata["note"] = "changed"
        self.assertEqual(record.metadata["note"], "ok")

    def test_unknown_selection_is_reported_rather_than_created(self):
        with self.assertRaises(ResultSelectionNotFoundError):
            self.repository().get("missing", actor_id="owner")
        with self.assertRaises(ResultSelectionNotFoundError):
            self.repository().update("missing", expected_revision=1, actor_id="owner", selected=True, favorite=False, rating=None, comment="", metadata={})
        # The application boundary reports the same absence as `not_found`.
        with self.assertRaises(ResultSelectionNotFoundServiceError):
            self.service().get("missing")
        with self.assertRaises(ResultSelectionServiceError) as caught:
            self.service().update("missing", expected_revision=1, selected=True, favorite=False, rating=None, comment="")
        self.assertEqual(caught.exception.code, "not_found")

    def client(self):
        def service_factory(actor_id):
            return ResultSelectionService(self.repository(), actor_id=actor_id, id_factory=lambda: "api-selection", clock=lambda: self.now)

        app = FastAPI()
        app.include_router(create_result_selections_router(service_factory=service_factory))
        return TestClient(app)

    def test_api_scopes_the_run_path_and_maps_errors(self):
        client = self.client()
        created = client.post("/api/v1/execution-runs/run-1/selections", headers={"X-User-ID": "owner"}, json={
            "attempt_id": "attempt-1", "output_name": "poster", "ordinal": 0, "selected": True, "rating": 5,
        })
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["rating"], 5)

        # An unknown run has no preference to list.
        self.assertEqual(client.get("/api/v1/execution-runs/missing-run/selections", headers={"X-User-ID": "owner"}).status_code, 404)
        # An unknown selection inside a known run is a 404 too, not an empty 200.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections/missing", headers={"X-User-ID": "owner"}).status_code, 404)
        # A selection is scoped to its own run path, on read and on write.
        self.assertEqual(client.get("/api/v1/execution-runs/other-run/selections/api-selection", headers={"X-User-ID": "owner"}).status_code, 404)
        self.assertEqual(client.put("/api/v1/execution-runs/other-run/selections/api-selection", headers={"X-User-ID": "owner"}, json={
            "expected_revision": 1, "selected": True, "favorite": False, "rating": None, "comment": "",
        }).status_code, 404)
        # Stale revision is a conflict, not a silent overwrite.
        stale = client.put("/api/v1/execution-runs/run-1/selections/api-selection", headers={"X-User-ID": "owner"}, json={
            "expected_revision": 9, "selected": True, "favorite": False, "rating": None, "comment": "",
        })
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(stale.json()["detail"]["code"], "stale_revision")
        # A missing actor is rejected, and a non-member is forbidden.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections").status_code, 401)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections", headers={"X-User-ID": "stranger"}).status_code, 403)
        # Authorization is enforced per path, not only on the listing: a
        # non-member may not fetch one record, and a viewer may not write one.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections/api-selection", headers={"X-User-ID": "stranger"}).status_code, 403)
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections/api-selection", headers={"X-User-ID": "viewer"}).status_code, 200)
        self.assertEqual(client.put("/api/v1/execution-runs/run-1/selections/api-selection", headers={"X-User-ID": "viewer"}, json={
            "expected_revision": 1, "selected": True, "favorite": False, "rating": None, "comment": "written by a viewer",
        }).status_code, 403)
        self.assertEqual(client.post("/api/v1/execution-runs/run-1/selections", headers={"X-User-ID": "viewer"}, json={
            "attempt_id": "attempt-9", "output_name": "poster", "ordinal": 0, "selected": True,
        }).status_code, 403)
        # The refused viewer write left the stored comment untouched.
        self.assertEqual(client.get("/api/v1/execution-runs/run-1/selections/api-selection", headers={"X-User-ID": "owner"}).json()["comment"], "")
        # An out-of-range rating is refused at the boundary.
        self.assertEqual(client.post("/api/v1/execution-runs/run-1/selections", headers={"X-User-ID": "owner"}, json={
            "attempt_id": "a", "output_name": "o", "ordinal": 0, "rating": 99,
        }).status_code, 422)

    def test_composition_root_registers_the_selection_routes(self):
        # Every other test builds its own app, so this is the only place the real
        # wiring is checked: deleting the include_router line would otherwise
        # leave the whole card unreachable in the shipped app.
        import main

        if not main.WORKBENCH_NODE_API_ENABLED:
            self.skipTest("the node API is disabled for this host")
        paths = main.app.openapi()["paths"]
        collection = "/api/v1/execution-runs/{run_id}/selections"
        item = f"{collection}/{{selection_id}}"
        self.assertIn(collection, paths)
        self.assertIn(item, paths)
        self.assertTrue({"get", "post"} <= set(paths[collection]))
        self.assertTrue({"get", "put"} <= set(paths[item]))
        # The mounted router is this card's, not a coincidentally named path.
        created = paths[collection]["post"]["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertEqual(created["$ref"], "#/components/schemas/ResultSelection")

    def test_preference_record_models_no_approval_frozen_or_scoring_state(self):
        fields = set(ResultSelection.model_fields)
        for marker in FORBIDDEN_APPROVAL_MARKERS:
            self.assertEqual({name for name in fields if marker in name.lower()}, set(), msg=f"no approval/frozen field via {marker}")
        for marker in FORBIDDEN_SCORING_MARKERS:
            self.assertEqual({name for name in fields if marker in name.lower()}, set(), msg=f"no computed scoring field via {marker}")
        # The rating is user-assigned: optional, and never derived.
        self.assertIn("rating", fields)
        self.assertTrue(ResultSelection.model_fields["rating"].is_required() is False)
        self.assertFalse(any(name.startswith("computed") for name in fields))

    def test_core_modules_stay_industry_neutral(self):
        for relative in (
            "workbench/domain/execution/selection.py",
            "workbench/repositories/result_selection_repository.py",
            "workbench/application/result_selection_service.py",
            "workbench/api/result_selections.py",
        ):
            source = (ROOT / relative).read_text(encoding="utf-8").lower()
            self.assertNotIn("wholehouse", source, msg=f"{relative} must stay industry-neutral")


class ResultSelectionSeamTests(unittest.TestCase):
    def test_identity_requires_all_three_parts(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
console.log(JSON.stringify({
  complete: api.identityOf({attempt_id:'attempt-1', output_name:'poster', ordinal:0}),
  missingAttempt: api.identityOf({output_name:'poster', ordinal:0}),
  missingName: api.identityOf({attempt_id:'attempt-1', ordinal:0}),
  missingOrdinal: api.identityOf({attempt_id:'attempt-1', output_name:'poster'}),
  negativeOrdinal: api.identityOf({attempt_id:'attempt-1', output_name:'poster', ordinal:-1}),
  same: api.sameResult({attempt_id:'a', output_name:'o', ordinal:0}, {attempt_id:'a', output_name:'o', ordinal:0}),
  differentOrdinal: api.sameResult({attempt_id:'a', output_name:'o', ordinal:0}, {attempt_id:'a', output_name:'o', ordinal:1}),
  differentName: api.sameResult({attempt_id:'a', output_name:'o', ordinal:0}, {attempt_id:'a', output_name:'p', ordinal:0}),
  differentAttempt: api.sameResult({attempt_id:'a', output_name:'o', ordinal:0}, {attempt_id:'b', output_name:'o', ordinal:0}),
}));
""", SELECTION)
        self.assertEqual(payload["complete"], {"attempt_id": "attempt-1", "output_name": "poster", "ordinal": 0})
        for key in ("missingAttempt", "missingName", "missingOrdinal", "negativeOrdinal"):
            self.assertIsNone(payload[key], msg=f"{key} must have no identity")
        self.assertTrue(payload["same"])
        # All three parts take part in the identity, not just two of them.
        self.assertFalse(payload["differentOrdinal"])
        self.assertFalse(payload["differentName"])
        self.assertFalse(payload["differentAttempt"])

    def test_preference_is_validated_with_explicit_reasons_and_never_clamped(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const c=api.create({});
const item={attempt_id:'attempt-1', output_name:'poster', ordinal:0};
const applied=c.setPreference(item,{selected:true, rating:4, comment:'nice'});
const tooHigh=c.setPreference(item,{rating:99});
const tooLow=c.setPreference(item,{rating:0});
const fractional=c.setPreference(item,{rating:2.5});
const tooLong=c.setPreference(item,{comment:'x'.repeat(api.MAX_COMMENT_LENGTH+1)});
const unknown=c.setPreference({output_name:'poster', ordinal:0},{selected:true});
console.log(JSON.stringify({
  applied,
  tooHigh, tooLow, fractional, tooLong, unknown,
  preference:c.preferenceFor(item),
  bounds:[api.RATING_MIN, api.RATING_MAX],
}));
""", SELECTION)
        self.assertEqual(payload["applied"]["reason"], "applied")
        self.assertEqual(payload["applied"]["preference"]["rating"], 4)
        for key in ("tooHigh", "tooLow", "fractional"):
            self.assertEqual(payload[key]["reason"], "rating_out_of_range", msg=f"{key} must be refused")
            # The refusal leaves the accepted preference untouched, so nothing was clamped.
            self.assertEqual(payload[key]["preference"]["rating"], 4)
        self.assertEqual(payload["tooLong"]["reason"], "comment_too_long")
        self.assertEqual(payload["tooLong"]["preference"]["comment"], "nice")
        self.assertEqual(payload["unknown"]["reason"], "unknown_result")
        self.assertIsNone(payload["unknown"]["result"])
        self.assertEqual(payload["bounds"], [1, 5])

    def test_pending_reports_create_update_and_clear_with_revisions(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const c=api.create({});
const first={attempt_id:'attempt-1', output_name:'poster', ordinal:0};
const second={attempt_id:'attempt-1', output_name:'poster', ordinal:1};
c.setPreference(first,{selected:true});
c.setPreference(second,{favorite:true, rating:3});
const created=c.pending();
// Persist both, then change one and clear the other.
c.markSaved([
  {id:'sel-1', attempt_id:'attempt-1', output_name:'poster', ordinal:0, selected:true, favorite:false, rating:null, comment:'', revision:1},
  {id:'sel-2', attempt_id:'attempt-1', output_name:'poster', ordinal:1, selected:false, favorite:true, rating:3, comment:'', revision:1},
]);
const clean=c.pending();
c.setPreference(first,{comment:'changed'});
c.clearPreference(second);
const dirty=c.pending();
console.log(JSON.stringify({created, clean, dirty, count:c.snapshot().count}));
""", SELECTION)
        self.assertEqual([entry["action"] for entry in payload["created"]], ["create", "create"])
        self.assertEqual([entry["revision"] for entry in payload["created"]], [0, 0])
        # Every change carries the canonical identity parts, not just the internal
        # index key, so a caller can hand it straight to persistence.
        self.assertEqual(
            {key: payload["created"][0][key] for key in ("attempt_id", "output_name", "ordinal")},
            {"attempt_id": "attempt-1", "output_name": "poster", "ordinal": 0},
        )
        self.assertEqual(
            {key: payload["dirty"][1][key] for key in ("attempt_id", "output_name", "ordinal")},
            {"attempt_id": "attempt-1", "output_name": "poster", "ordinal": 1},
        )
        self.assertEqual(payload["clean"], [])
        self.assertEqual([entry["action"] for entry in payload["dirty"]], ["update", "clear"])
        update = payload["dirty"][0]
        self.assertEqual((update["selection_id"], update["revision"], update["comment"]), ("sel-1", 1, "changed"))
        self.assertEqual(payload["dirty"][1]["selection_id"], "sel-2")
        # The cleared record is no longer a marked preference.
        self.assertEqual(payload["count"], 1)

    def test_hydrate_replaces_the_baseline_and_leaves_nothing_pending(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const c=api.create({});
const item={attempt_id:'attempt-1', output_name:'poster', ordinal:0};
c.hydrate([{id:'sel-1', attempt_id:'attempt-1', output_name:'poster', ordinal:0, selected:true, favorite:true, rating:null, comment:'', revision:2}]);
const afterLoad={preference:c.preferenceFor(item), pending:c.pending()};
// A record that cannot supply an identity is ignored rather than half-keyed.
const ignored=c.hydrate([{id:'bad', output_name:'poster', ordinal:0, selected:true}]).count;
const absent={preference:c.preferenceFor(item), pending:c.pending()};
console.log(JSON.stringify({afterLoad, ignored, absent, has:c.has(item)}));
""", SELECTION)
        self.assertEqual(payload["afterLoad"]["preference"], {"selected": True, "favorite": True, "rating": None, "comment": ""})
        self.assertEqual(payload["afterLoad"]["pending"], [])
        self.assertEqual(payload["ignored"], 0)
        self.assertEqual(payload["absent"]["preference"], {"selected": False, "favorite": False, "rating": None, "comment": ""})
        self.assertEqual(payload["absent"]["pending"], [])
        self.assertFalse(payload["has"])

    def test_a_comment_alone_counts_as_a_preference(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const c=api.create({});
const item={attempt_id:'attempt-1', output_name:'poster', ordinal:0};
const applied=c.setPreference(item,{comment:'worth keeping'});
const whitespace=c.setPreference({attempt_id:'attempt-1', output_name:'poster', ordinal:1},{comment:'   '});
console.log(JSON.stringify({
  reason:applied.reason, has:c.has(item), count:c.snapshot().count,
  pending:c.pending().length,
  whitespaceReason:whitespace.reason, whitespaceCount:c.snapshot().count,
  ratingOnly:api.hasPreference({rating:3}),
  noPreference:api.hasPreference({rating:null}),
}));
""", SELECTION)
        self.assertEqual(payload["reason"], "applied")
        self.assertTrue(payload["has"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["pending"], 1)
        # Whitespace carries no decision: nothing marked, nothing to persist.
        self.assertEqual(payload["whitespaceReason"], "unchanged")
        self.assertEqual(payload["whitespaceCount"], 1)
        # The rating counts as a preference on its own; its absence does not.
        self.assertTrue(payload["ratingOnly"])
        self.assertFalse(payload["noPreference"])

    def test_clearing_a_value_is_an_explicit_restatement(self):
        # Absent means "leave as is"; an explicit null clears. A partial patch
        # could not tell those apart, which is why the whole preference is restated.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const c=api.create({});
const item={attempt_id:'attempt-1', output_name:'poster', ordinal:0};
c.setPreference(item,{selected:true, rating:4, comment:'nice'});
const ratingCleared=c.setPreference(item,{rating:null});
const blanked=c.setPreference(item,{selected:false, comment:''});
console.log(JSON.stringify({ratingCleared, blanked, preference:c.preferenceFor(item), count:c.snapshot().count}));
""", SELECTION)
        self.assertEqual(
            payload["ratingCleared"]["preference"],
            {"selected": True, "favorite": False, "rating": None, "comment": "nice"},
        )
        # Removing the last decision leaves nothing marked and nothing to persist.
        self.assertEqual(
            payload["blanked"]["preference"],
            {"selected": False, "favorite": False, "rating": None, "comment": ""},
        )
        self.assertEqual(payload["count"], 0)
        self.assertEqual(payload["preference"], {"selected": False, "favorite": False, "rating": None, "comment": ""})

    def test_mounted_rows_carry_the_canonical_identity(self):
        # A rendered row must be addressable by the identity persistence uses,
        # and a comment is user text rather than markup.
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const host={attributes:{},setAttribute(n,v){this.attributes[n]=v;},removeAttribute(n){delete this.attributes[n];},innerHTML:''};
const c=api.create({});
const mounted=c.mount(host);
c.setPreference({attempt_id:'attempt-1', output_name:'poster', ordinal:3},{selected:true, rating:5, comment:'<b>x</b>'});
console.log(JSON.stringify({
  attr:host.attributes['data-result-selection'],
  html:host.innerHTML,
  count:mounted.snapshot().count,
}));
""", SELECTION)
        self.assertEqual(payload["attr"], "workbench.result-selection/1")
        for fragment in (
            'data-selection-attempt="attempt-1"',
            'data-selection-output="poster"',
            'data-selection-ordinal="3"',
            'data-selection-selected="true"',
            'data-selection-rating="5"',
        ):
            self.assertIn(fragment, payload["html"], msg=f"row must carry {fragment}")
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", payload["html"])
        self.assertNotIn("<b>x</b>", payload["html"])
        self.assertEqual(payload["count"], 1)

    def test_selected_row_exposes_explicit_asset_action_and_callback(self):
        payload = run_program("""
const api=sandbox.window.WorkbenchCanvasResultSelection;
const calls=[];
const host={attributes:{},listeners:{},setAttribute(n,v){this.attributes[n]=v;},removeAttribute(n){delete this.attributes[n];},innerHTML:'',addEventListener(n,fn){this.listeners[n]=fn;},removeEventListener(){}};
const c=api.create({onSaveAsAsset: record => calls.push(record)});
c.mount(host);
c.setPreference({attempt_id:'attempt-1', output_name:'poster', ordinal:0},{selected:true});
const key=JSON.stringify(['attempt-1','poster',0]);
host.listeners.click({target:{closest: selector => selector === '[data-result-save-asset]' ? {getAttribute: () => key} : null}});
console.log(JSON.stringify({hasAction:host.innerHTML.includes('data-result-save-asset'), calls}));
""", SELECTION)
        self.assertTrue(payload["hasAction"])
        self.assertEqual(payload["calls"][0]["attempt_id"], "attempt-1")
        self.assertEqual(payload["calls"][0]["output_name"], "poster")

    def test_asset_materialization_client_posts_declared_result_content(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultAssetMaterializationApiClient;
const calls=[];
const fakeFetch=async (url, options)=>{calls.push({url, options, body:JSON.parse(options.body)});return {ok:true,status:201,json:async()=>({ref:{asset_id:'a1',version_id:'v1'}})};};
(async()=>{
  await client.materialize('run/1', {project_id:'project-1',attempt_id:'attempt-1',output_name:'poster',ordinal:0,title:'Poster',type:'image',content:{location:'/output/poster',checksum:'sha256:'+'a'.repeat(64),mime_type:'image/png',size_bytes:12}}, {actorId:'owner',fetch:fakeFetch});
  console.log(JSON.stringify({url:calls[0].url, method:calls[0].options.method, actor:calls[0].options.headers['X-User-ID'], body:calls[0].body}));
})();
""", ASSET_CLIENT)
        self.assertEqual(payload["url"], "/api/v1/execution-runs/run%2F1/assets")
        self.assertEqual(payload["method"], "POST")
        self.assertEqual(payload["actor"], "owner")
        self.assertEqual(payload["body"]["content"]["checksum"], "sha256:" + "a" * 64)

    def test_asset_materialization_client_builds_explicit_selection_handler(self):
        payload = run_program("""
const client=sandbox.window.WorkbenchResultAssetMaterializationApiClient;
const calls=[];
const fakeFetch=async (url, options)=>{calls.push({url, body:JSON.parse(options.body)});return {ok:true,status:201,json:async()=>({ref:'asset-ref'})};};
(async()=>{
  const handler=client.createHandler({runId:'run-1',projectId:'project-1',actorId:'owner',fetch:fakeFetch,type:'image',contentFor:record=>({location:'/output/'+record.output_name,checksum:'sha256:'+'b'.repeat(64),mime_type:'image/png',size_bytes:3})});
  await handler({attempt_id:'attempt-1',output_name:'poster',ordinal:0,selected:true});
  console.log(JSON.stringify({url:calls[0].url, body:calls[0].body}));
})();
""", ASSET_CLIENT)
        self.assertEqual(payload["url"], "/api/v1/execution-runs/run-1/assets")
        self.assertEqual(payload["body"]["project_id"], "project-1")
        self.assertEqual(payload["body"]["content"]["location"], "/output/poster")

    def test_seam_has_no_transport_no_scoring_and_no_approval_semantics(self):
        source = SELECTION.read_text(encoding="utf-8")
        for marker in FORBIDDEN_TRANSPORT_MARKERS:
            self.assertNotIn(marker, source, msg=f"selection seam must not reference {marker}")
        for marker in FORBIDDEN_SCORING_MARKERS:
            self.assertNotIn(marker, source, msg=f"selection seam must not compute {marker}")
        for marker in FORBIDDEN_MUTATION_MARKERS:
            self.assertNotIn(marker, source, msg=f"selection seam must not reference {marker}")
        # No approval/frozen state: the only `frozen` occurrences are the header
        # comment's explicit denial and the record objects it returns.
        self.assertNotIn("approval", source.lower())
        self.assertNotIn("frozen_at", source.lower())
        self.assertNotIn("approve", source.lower())

    def test_canvas_page_registers_the_selection_seam_and_client(self):
        page = (ROOT / "static" / "canvas.html").read_text(encoding="utf-8")
        self.assertEqual(page.count("workbench/canvas/result-selection-runtime.js"), 1)
        self.assertEqual(page.count("workbench/canvas/result-selection-api-client.js"), 1)
        self.assertLess(page.index("result-compare-runtime.js"), page.index("result-selection-runtime.js"))
        self.assertLess(page.index("result-selection-runtime.js"), page.index("canvas-app-bootstrap.js"))

    def test_task_node_exposes_the_shared_selection_mount(self):
        source = (ROOT / "static/js/workbench/canvas/task-rich-node.js").read_text(encoding="utf-8")
        self.assertIn("function mountResultSelection(host, options)", source)
        self.assertIn("mountResultSelection,", source)
        shell = (ROOT / "static/js/workbench/canvas/node-shell.js").read_text(encoding="utf-8")
        host = (ROOT / "static/js/workbench/canvas/node-card-host.js").read_text(encoding="utf-8")
        self.assertIn("settings.resultSelectionOptions", shell)
        self.assertIn("taskRichNode.mountResultSelection(resultSelectionHost, settings.resultSelectionOptions)", shell)
        self.assertIn("const resultSelectionOptions = resolvedRendererOptions.resultSelectionOptions", host)
        self.assertIn("WorkbenchResultAssetMaterializationApiClient.createHandler", host)
        page = (ROOT / "static/js/workbench/canvas/canvas-app-media-editor.js").read_text(encoding="utf-8")
        self.assertIn("function canvasTaskRendererOptions(node)", page)
        self.assertIn("node.type === 'task' ? canvasTaskRendererOptions(node)", page)

    def test_pending_feed_the_client_into_the_api_payload_shape(self):
        # The seam reports what to persist and the client is the only transport;
        # together they must produce the payload the versioned API accepts.
        payload = run_program("""
const selection=sandbox.window.WorkbenchCanvasResultSelection;
const client=sandbox.window.WorkbenchResultSelectionApiClient;
const calls=[];
const fakeFetch=async (url,options)=>{calls.push({url,method:options.method,headers:options.headers,body:options.body?JSON.parse(options.body):null});return {ok:true,status:201,json:async()=>({id:'sel-9',revision:1})};};
const item={attempt_id:'attempt-1', output_name:'poster', ordinal:2};
const c=selection.create({});
c.setPreference(item,{selected:true, favorite:true, rating:5, comment:'best'});
const pending=c.pending();
(async()=>{
  await client.create('run-1', {...pending[0], metadata:{}}, {actorId:'owner', fetch:fakeFetch});
  const record={revision:1, selected:false, favorite:true, rating:null, comment:''};
  await client.update('run-1','sel-9', record, {actorId:'owner', fetch:fakeFetch});
  await client.list('run-1', {actorId:'owner', fetch:fakeFetch});
  console.log(JSON.stringify({pending, calls}));
})();
""", SELECTION, CLIENT)
        self.assertEqual(payload["pending"][0]["action"], "create")
        create, update, listing = payload["calls"]
        self.assertEqual(create["url"], "/api/v1/execution-runs/run-1/selections")
        self.assertEqual(create["method"], "POST")
        self.assertEqual(create["headers"]["X-User-ID"], "owner")
        # The client sends the canonical identity parts, never a composite id.
        self.assertEqual(
            {key: create["body"][key] for key in ("attempt_id", "output_name", "ordinal")},
            {"attempt_id": "attempt-1", "output_name": "poster", "ordinal": 2},
        )
        self.assertEqual((create["body"]["selected"], create["body"]["favorite"], create["body"]["rating"]), (True, True, 5))
        self.assertNotIn("key", create["body"])
        self.assertEqual(update["method"], "PUT")
        self.assertEqual(update["body"]["expected_revision"], 1)
        self.assertIsNone(update["body"]["rating"])
        self.assertEqual(listing["method"], "GET")
        self.assertEqual(listing["url"], "/api/v1/execution-runs/run-1/selections")

    def test_client_refuses_a_request_without_an_actor(self):
        # The client is the only transport, so it is the last place a request can
        # be stopped before it leaves without an identity.
        payload = run_program("""
const client=sandbox.window.WorkbenchResultSelectionApiClient;
const calls=[];
const fakeFetch=async (url,options)=>{calls.push(url);return {ok:true,status:200,json:async()=>([])};};
(async()=>{
  let listError='', createError='', runError='';
  try { await client.list('run-1', {fetch:fakeFetch}); } catch (error) { listError=error.message; }
  try { await client.create('run-1', {}, {fetch:fakeFetch}); } catch (error) { createError=error.message; }
  try { await client.list('', {actorId:'owner', fetch:fakeFetch}); } catch (error) { runError=error.message; }
  console.log(JSON.stringify({listError, createError, runError, calls}));
})();
""", CLIENT)
        self.assertIn("actor id", payload["listError"])
        self.assertIn("actor id", payload["createError"])
        self.assertIn("run id", payload["runError"])
        # Nothing reached the transport.
        self.assertEqual(payload["calls"], [])

    def test_client_encodes_the_run_id_and_refuses_a_bad_revision(self):
        # The run id is a path segment, so it must be escaped; and an update
        # without a positive revision would silently target the wrong one.
        payload = run_program("""
const client=sandbox.window.WorkbenchResultSelectionApiClient;
const urls=[];
const fakeFetch=async (url,options)=>{urls.push(url);return {ok:true,status:200,json:async()=>({id:'x',revision:1})};};
(async()=>{
  await client.list('run/1?x=2', {actorId:'owner', fetch:fakeFetch});
  let zero='', missing='';
  try { await client.update('run-1','s1',{revision:0},{actorId:'owner',fetch:fakeFetch}); } catch(e){ zero=e.message; }
  try { await client.update('run-1','s1',{},{actorId:'owner',fetch:fakeFetch}); } catch(e){ missing=e.message; }
  console.log(JSON.stringify({urls, zero, missing}));
})();
""", CLIENT)
        self.assertEqual(payload["urls"], ["/api/v1/execution-runs/run%2F1%3Fx%3D2/selections"])
        self.assertIn("positive revision", payload["zero"])
        self.assertIn("positive revision", payload["missing"])

    def test_client_surfaces_the_api_error_message(self):
        # The client is the only transport, so a swallowed message would leave a
        # caller with nothing but a status code.
        payload = run_program("""
const client=sandbox.window.WorkbenchResultSelectionApiClient;
const fakeFetch=async ()=>({ok:false,status:409,json:async()=>({detail:{code:'stale_revision',message:'result selection revision is stale; current revision is 7'}})});
(async()=>{
  let message='';
  try { await client.list('run-1', {actorId:'owner', fetch:fakeFetch}); } catch(e){ message=e.message; }
  console.log(JSON.stringify({message}));
})();
""", CLIENT)
        self.assertIn("current revision is 7", payload["message"])


if __name__ == "__main__":
    unittest.main()
