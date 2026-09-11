"""Compatibility repository for the existing one-file-per-Canvas JSON store."""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable

from .canvas_repository import (
    CanvasDeletedError,
    CanvasNotFoundError,
    CanvasRepository,
    CanvasValidationError,
    StaleCanvasRevisionError,
)


class LegacyJsonCanvasRepository(CanvasRepository):
    """Preserves current JSON shape and monotonic ``updated_at`` save semantics."""

    def __init__(self, directory: str | Path, *, clock_ms: Callable[[], int], lock: Any):
        self._directory = Path(directory)
        self._clock_ms = clock_ms
        self._lock = lock

    def path_for(self, canvas_id: str) -> Path:
        cleaned = str(canvas_id or "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", cleaned):
            raise CanvasValidationError("invalid canvas id")
        return self._directory / f"{cleaned}.json"

    def load(self, canvas_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        path = self.path_for(canvas_id)
        if not path.exists():
            raise CanvasNotFoundError("canvas not found")
        with path.open("r", encoding="utf-8") as handle:
            canvas = json.load(handle)
        if canvas.get("deleted_at") and not include_deleted:
            raise CanvasDeletedError("canvas is deleted")
        return canvas

    def save(self, canvas: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return self._save_unlocked(canvas)

    def save_if_current(self, canvas: dict[str, Any], *, expected_updated_at: int | None) -> dict[str, Any]:
        canvas_id = str(canvas.get("id") or "")
        with self._lock:
            current = self.load(canvas_id, include_deleted=True)
            current_updated_at = int(current.get("updated_at") or 0)
            if expected_updated_at and current_updated_at and int(expected_updated_at) < current_updated_at:
                raise StaleCanvasRevisionError(current)
            return self._save_unlocked(canvas)

    def save_metadata(self, canvas: dict[str, Any]) -> dict[str, Any]:
        canvas_id = str(canvas.get("id") or "")
        path = self.path_for(canvas_id)
        with self._lock:
            if not path.exists():
                raise CanvasNotFoundError("canvas not found")
            self._write_payload(path, canvas)
        return canvas

    def list_payloads(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        return self.list_payloads_with_diagnostics(include_deleted=include_deleted)[0]

    def list_payloads_with_diagnostics(self, *, include_deleted: bool = False) -> tuple[list[dict[str, Any]], bool]:
        if not self._directory.exists():
            return [], True
        payloads = []
        unreadable = False
        for path in sorted(self._directory.glob("*.json")):
            try:
                with path.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
            except Exception:
                unreadable = True
                continue
            if include_deleted or not payload.get("deleted_at"):
                payloads.append(payload)
        return payloads, unreadable

    def purge_expired_deleted(self, *, before_ms: int) -> int:
        removed = 0
        for payload in self.list_payloads(include_deleted=True):
            if int(payload.get("deleted_at") or 0) and int(payload["deleted_at"]) < before_ms:
                removed += int(self.purge(str(payload.get("id") or "")))
        return removed

    def reassign_project(self, *, source_project_id: str, target_project_id: str) -> int:
        moved = 0
        for payload in self.list_payloads(include_deleted=True):
            if str(payload.get("project") or "") == source_project_id:
                payload["project"] = target_project_id
                self.save_metadata(payload)
                moved += 1
        return moved

    def purge(self, canvas_id: str) -> bool:
        path = self.path_for(canvas_id)
        with self._lock:
            if not path.exists():
                return False
            os.remove(path)
            return True

    def mutate_if_current(
        self,
        canvas_id: str,
        *,
        expected_updated_at: int | None,
        already_applied: Callable[[dict[str, Any]], bool] | None = None,
        mutation: Callable[[dict[str, Any]], None],
    ) -> dict[str, Any]:
        """Apply one caller-owned mutation while holding the Legacy Canvas lock."""
        with self._lock:
            canvas = self.load(canvas_id, include_deleted=False)
            if already_applied is not None and already_applied(canvas):
                return canvas
            current_updated_at = int(canvas.get("updated_at") or 0)
            if expected_updated_at and current_updated_at and int(expected_updated_at) < current_updated_at:
                raise StaleCanvasRevisionError(canvas)
            mutation(canvas)
            return self._save_unlocked(canvas)

    def _save_unlocked(self, canvas: dict[str, Any]) -> dict[str, Any]:
        canvas_id = str(canvas.get("id") or "")
        path = self.path_for(canvas_id)
        previous_updated_at = int(canvas.get("updated_at") or 0)
        current_updated_at = int(self._clock_ms())
        canvas["updated_at"] = max(current_updated_at, previous_updated_at + 1) if previous_updated_at else current_updated_at
        self._directory.mkdir(parents=True, exist_ok=True)
        self._write_payload(path, canvas)
        return canvas

    @staticmethod
    def _write_payload(path: Path, canvas: dict[str, Any]) -> None:
        """Durably replace one Legacy JSON record without exposing a partial file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(canvas, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
