"""R4 adapter exposing R3 SQLite authority through the Legacy Canvas contract."""

from copy import deepcopy
from typing import Any, Callable

from .canvas_repository import CanvasDeletedError, CanvasNotFoundError, CanvasRepository, CanvasValidationError, StaleCanvasRevisionError
from .sqlite_project_canvas_repository import CanonicalNotFoundError, CanonicalStaleRevisionError, SqliteProjectCanvasRepository


class SqliteCanvasCompatibilityRepository(CanvasRepository):
    """Lossless Legacy payload compatibility; canonical revision remains internal."""

    def __init__(self, repository: SqliteProjectCanvasRepository, *, actor_id: str, clock_ms: Callable[[], int]):
        self._repository = repository
        self._actor_id = actor_id
        self._clock_ms = clock_ms

    def load(self, canvas_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        try:
            payload = self._repository.load_canvas_snapshot(self._canvas_id(canvas_id)).payload
        except CanonicalNotFoundError as error:
            raise CanvasNotFoundError("canvas not found") from error
        if payload.get("deleted_at") and not include_deleted:
            raise CanvasDeletedError("canvas is deleted")
        return payload

    def save(self, canvas: dict[str, Any]) -> dict[str, Any]:
        canvas_id = self._canvas_id(canvas.get("id"))
        try:
            snapshot = self._repository.load_canvas_snapshot(canvas_id)
        except CanonicalNotFoundError:
            payload = self._with_compatibility_timestamp(canvas, None)
            _, saved = self._repository.create_canvas_payload(actor_id=self._actor_id, payload=payload)
        else:
            current = snapshot.payload
            payload = self._with_compatibility_timestamp(canvas, current)
            saved = self._replace_at_revision(canvas_id, snapshot.revision, payload)
        canvas.clear()
        canvas.update(saved)
        return canvas

    def save_if_current(self, canvas: dict[str, Any], *, expected_updated_at: int | None) -> dict[str, Any]:
        canvas_id = self._canvas_id(canvas.get("id"))
        snapshot = self._repository.load_canvas_snapshot(canvas_id)
        current = snapshot.payload
        self._reject_mismatched_expected_timestamp(current, expected_updated_at)
        payload = self._with_compatibility_timestamp(canvas, current)
        saved = self._replace_at_revision(canvas_id, snapshot.revision, payload)
        canvas.clear()
        canvas.update(saved)
        return canvas

    def save_metadata(self, canvas: dict[str, Any]) -> dict[str, Any]:
        canvas_id = self._canvas_id(canvas.get("id"))
        snapshot = self._repository.load_canvas_snapshot(canvas_id)
        saved = self._replace_at_revision(canvas_id, snapshot.revision, canvas)
        canvas.clear()
        canvas.update(saved)
        return canvas

    def list_payloads(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        return self._repository.list_canvas_payloads(include_deleted=include_deleted)

    def list_payloads_with_diagnostics(self, *, include_deleted: bool = False) -> tuple[list[dict[str, Any]], bool]:
        return self.list_payloads(include_deleted=include_deleted), False

    def purge_expired_deleted(self, *, before_ms: int) -> int:
        return self._repository.purge_expired_canvas_payloads(actor_id=self._actor_id, before_ms=before_ms)

    def reassign_project(self, *, source_project_id: str, target_project_id: str) -> int:
        return self._repository.reassign_canvas_projects(actor_id=self._actor_id, source_project_id=source_project_id, target_project_id=target_project_id)

    def purge(self, canvas_id: str) -> bool:
        return self._repository.purge_canvas_payload(actor_id=self._actor_id, canvas_id=self._canvas_id(canvas_id))

    def mutate_if_current(self, canvas_id: str, *, expected_updated_at: int | None, already_applied=None, mutation: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        canvas_id = self._canvas_id(canvas_id)
        snapshot = self._repository.load_canvas_snapshot(canvas_id)
        canvas = snapshot.payload
        if canvas.get("deleted_at"):
            raise CanvasDeletedError("canvas is deleted")
        if already_applied is not None and already_applied(canvas):
            return canvas
        self._reject_mismatched_expected_timestamp(canvas, expected_updated_at)
        mutation(canvas)
        payload = self._with_compatibility_timestamp(canvas, canvas)
        return self._replace_at_revision(canvas_id, snapshot.revision, payload)

    def _replace_at_revision(self, canvas_id: str, expected_revision: int, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            _, saved = self._repository.replace_canvas_payload(
                actor_id=self._actor_id, canvas_id=canvas_id, expected_revision=expected_revision, payload=payload,
            )
            return saved
        except CanonicalStaleRevisionError as error:
            try:
                current = self.load(canvas_id, include_deleted=True)
            except CanvasNotFoundError:
                current = {"id": canvas_id, "revision": error.current_revision}
            raise StaleCanvasRevisionError(current) from error

    @staticmethod
    def _canvas_id(value: Any) -> str:
        canvas_id = str(value or "").strip()
        if not canvas_id:
            raise CanvasValidationError("invalid canvas id")
        return canvas_id

    def _with_compatibility_timestamp(self, canvas: dict[str, Any], current: dict[str, Any] | None) -> dict[str, Any]:
        payload = deepcopy(canvas)
        previous = int((current or {}).get("updated_at") or 0)
        now = int(self._clock_ms())
        payload["updated_at"] = max(now, previous + 1) if previous else now
        return payload

    @staticmethod
    def _reject_mismatched_expected_timestamp(canvas: dict[str, Any], expected_updated_at: int | None) -> None:
        current_updated_at = int(canvas.get("updated_at") or 0)
        if expected_updated_at and current_updated_at and int(expected_updated_at) != current_updated_at:
            raise StaleCanvasRevisionError(canvas)
