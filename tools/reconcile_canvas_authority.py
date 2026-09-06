#!/usr/bin/env python3
"""Read-only reconciliation between Legacy Canvas JSON and the SQLite authority.

The reconciler never writes: the database is opened with SQLite ``mode=ro`` URI
semantics and Legacy files are only read. It reports counts, ID-set differences,
itemized payload/position/connection differences, trash-state mismatches,
unexpected rows, and the recorded canvas authority state, so persistence work
can start from a known-safe dataset without any destructive repair.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

REPORT_SCHEMA_VERSION = "workbench.canvas-authority-reconciliation-report/1"

# Matches the repository's own lossless-compare contract: the canonical row
# stores the resolved project inside the payload, so it is ignored here too.
PAYLOAD_IGNORED_KEYS = frozenset({"project"})


@dataclass(frozen=True)
class SqliteCanvasRow:
    canvas_id: str
    project_id: str
    title: str
    revision: int
    updated_at: str
    deleted: bool
    payload: dict[str, Any]


@dataclass(frozen=True)
class CanvasComparison:
    canvas_id: str
    matches: bool
    payload_key_differences: tuple[str, ...] = ()
    node_position_differences: tuple[dict[str, Any], ...] = ()
    connection_differences: dict[str, list[list[Any]]] = field(default_factory=dict)
    trash_state_mismatch: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "canvas_id": self.canvas_id,
            "matches": self.matches,
            "payload_key_differences": list(self.payload_key_differences),
            "node_position_differences": list(self.node_position_differences),
            "connection_differences": {key: list(value) for key, value in self.connection_differences.items()},
            "trash_state_mismatch": self.trash_state_mismatch,
        }


@dataclass(frozen=True)
class ReconciliationReport:
    legacy_file_count: int
    legacy_id_count: int
    duplicate_legacy_ids: list[str]
    sqlite_row_count: int
    sqlite_active_count: int
    sqlite_deleted_count: int
    legacy_only_ids: list[str]
    sqlite_only_ids: list[str]
    comparisons: list[CanvasComparison]
    unexpected_rows: list[dict[str, Any]]
    canvas_authority: str | None
    converged: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "legacy": {
                "file_count": self.legacy_file_count,
                "id_count": self.legacy_id_count,
                "duplicate_ids": self.duplicate_legacy_ids,
                "legacy_only_ids": self.legacy_only_ids,
            },
            "sqlite": {
                "row_count": self.sqlite_row_count,
                "active_count": self.sqlite_active_count,
                "deleted_count": self.sqlite_deleted_count,
                "sqlite_only_ids": self.sqlite_only_ids,
            },
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "unexpected_rows": self.unexpected_rows,
            "canvas_authority": self.canvas_authority,
            "converged": self.converged,
        }


def load_legacy_canvases(directory: Path) -> list[dict[str, Any]]:
    canvases: list[dict[str, Any]] = []
    for path in sorted(Path(directory).glob("*.json")):
        with path.open(encoding="utf-8") as source:
            payload = json.load(source)
        if not isinstance(payload, dict):
            raise ValueError(f"canvas JSON must be an object: {path}")
        canvases.append(payload)
    return canvases


def load_sqlite_rows(database_path: str | Path) -> tuple[dict[str, SqliteCanvasRow], str | None]:
    """Read canvases and authority state through a strictly read-only connection."""
    connection = sqlite3.connect(f"file:{Path(database_path).resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "canvases" not in tables:
            raise ValueError(f"database has no canvases table: {database_path}")
        rows: dict[str, SqliteCanvasRow] = {}
        for row in connection.execute("SELECT * FROM canvases ORDER BY id"):
            payload = json.loads(row["payload_json"])
            if not isinstance(payload, dict):
                raise ValueError(f"payload_json must be an object for canvas {row['id']}")
            rows[str(row["id"])] = SqliteCanvasRow(
                canvas_id=str(row["id"]),
                project_id=str(row["project_id"]),
                title=str(row["title"]),
                revision=int(row["revision"]),
                updated_at=str(row["updated_at"]),
                deleted=row["deleted_at"] is not None,
                payload=payload,
            )
        authority: str | None = None
        if "authority_state" in tables:
            state = connection.execute("SELECT canvas_authority FROM authority_state WHERE singleton=1").fetchone()
            authority = str(state["canvas_authority"]) if state else None
        return rows, authority
    finally:
        connection.close()


def _node_positions(nodes: Any) -> dict[str, tuple[Any, Any]]:
    positions: dict[str, tuple[Any, Any]] = {}
    if isinstance(nodes, dict):
        items: list[tuple[Any, Any]] = list(nodes.items())
    elif isinstance(nodes, list):
        items = [(node.get("id"), node) for node in nodes if isinstance(node, dict)]
    else:
        return positions
    for node_id, node in items:
        if node_id and isinstance(node, dict):
            positions[str(node_id)] = (node.get("x"), node.get("y"))
    return positions


def _connection_triples(connections: Any) -> set[tuple[Any, Any, Any]]:
    triples: set[tuple[Any, Any, Any]] = set()
    if isinstance(connections, list):
        for connection in connections:
            if isinstance(connection, dict):
                triples.add((connection.get("from"), connection.get("to"), connection.get("kind")))
    return triples


def compare_canvas(legacy: dict[str, Any], row: SqliteCanvasRow) -> CanvasComparison:
    canvas_id = str(legacy.get("id") or row.canvas_id)
    payload_keys = sorted(
        key
        for key in set(legacy) | set(row.payload)
        if key not in PAYLOAD_IGNORED_KEYS and legacy.get(key) != row.payload.get(key)
    )
    legacy_positions = _node_positions(legacy.get("nodes"))
    sqlite_positions = _node_positions(row.payload.get("nodes"))
    position_differences: list[dict[str, Any]] = []
    for node_id in sorted(set(legacy_positions) | set(sqlite_positions)):
        legacy_point = legacy_positions.get(node_id)
        sqlite_point = sqlite_positions.get(node_id)
        if legacy_point != sqlite_point:
            position_differences.append(
                {"node_id": node_id, "legacy": legacy_point, "sqlite": sqlite_point}
            )
    legacy_connections = _connection_triples(legacy.get("connections"))
    sqlite_connections = _connection_triples(row.payload.get("connections"))
    connection_differences = {
        "legacy_only": sorted(legacy_connections - sqlite_connections),
        "sqlite_only": sorted(sqlite_connections - legacy_connections),
    }
    legacy_trashed = bool(legacy.get("deleted_at"))
    trash_state_mismatch = (
        {"legacy_trashed": legacy_trashed, "sqlite_trashed": row.deleted}
        if legacy_trashed != row.deleted
        else None
    )
    matches = not (payload_keys or position_differences or any(connection_differences.values()) or trash_state_mismatch)
    return CanvasComparison(
        canvas_id=canvas_id,
        matches=matches,
        payload_key_differences=tuple(payload_keys),
        node_position_differences=tuple(position_differences),
        connection_differences=connection_differences,
        trash_state_mismatch=trash_state_mismatch,
    )


def reconcile(
    legacy_canvases: list[dict[str, Any]],
    sqlite_rows: dict[str, SqliteCanvasRow],
    *,
    canvas_authority: str | None = None,
    known_project_ids: set[str] | None = None,
) -> ReconciliationReport:
    legacy_by_id: dict[str, dict[str, Any]] = {}
    duplicates: set[str] = set()
    for payload in legacy_canvases:
        canvas_id = str(payload.get("id") or "").strip()
        if not canvas_id:
            continue
        if canvas_id in legacy_by_id:
            duplicates.add(canvas_id)
        legacy_by_id[canvas_id] = payload
    legacy_ids = set(legacy_by_id)
    sqlite_ids = set(sqlite_rows)

    unexpected: list[dict[str, Any]] = []
    unexpected.extend({"class": "duplicate_legacy_id", "canvas_id": canvas_id} for canvas_id in sorted(duplicates))
    for canvas_id in sorted(sqlite_ids):
        row = sqlite_rows[canvas_id]
        if row.payload.get("id") != row.canvas_id:
            unexpected.append({"class": "payload_id_mismatch", "canvas_id": canvas_id})
        if row.title != str(row.payload.get("title") or ""):
            unexpected.append(
                {"class": "title_column_mismatch", "canvas_id": canvas_id,
                 "detail": {"title_column": row.title, "payload_title": row.payload.get("title")}}
            )
    if known_project_ids is not None:
        for canvas_id in sorted(legacy_ids):
            project_id = str(legacy_by_id[canvas_id].get("project") or "").strip()
            if project_id and project_id not in known_project_ids:
                unexpected.append(
                    {"class": "legacy_project_mismatch", "canvas_id": canvas_id, "detail": {"project": project_id}}
                )

    comparisons = [
        compare_canvas(legacy_by_id[canvas_id], sqlite_rows[canvas_id])
        for canvas_id in sorted(legacy_ids & sqlite_ids)
    ]
    divergent = [comparison.canvas_id for comparison in comparisons if not comparison.matches]
    converged = (
        not divergent
        and legacy_ids == sqlite_ids
        and not duplicates
        and not unexpected
        and canvas_authority is not None
    )
    return ReconciliationReport(
        legacy_file_count=len(legacy_canvases),
        legacy_id_count=len(legacy_ids),
        duplicate_legacy_ids=sorted(duplicates),
        sqlite_row_count=len(sqlite_rows),
        sqlite_active_count=sum(1 for row in sqlite_rows.values() if not row.deleted),
        sqlite_deleted_count=sum(1 for row in sqlite_rows.values() if row.deleted),
        legacy_only_ids=sorted(legacy_ids - sqlite_ids),
        sqlite_only_ids=sorted(sqlite_ids - legacy_ids),
        comparisons=comparisons,
        unexpected_rows=unexpected,
        canvas_authority=canvas_authority,
        converged=converged,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canvases-dir", required=True, type=Path, help="Directory containing Legacy Canvas JSON files")
    parser.add_argument("--database", required=True, type=Path, help="SQLite database (opened read-only)")
    parser.add_argument("--projects", type=Path, help="Optional Legacy projects JSON for project-mismatch classification")
    parser.add_argument("--report", type=Path, help="Optional JSON report destination")
    args = parser.parse_args()

    legacy_canvases = load_legacy_canvases(args.canvases_dir)
    sqlite_rows, authority = load_sqlite_rows(args.database)
    known_project_ids: set[str] | None = None
    if args.projects is not None:
        with args.projects.open(encoding="utf-8") as source:
            projects_payload = json.load(source)
        projects = projects_payload.get("projects", []) if isinstance(projects_payload, dict) else projects_payload
        known_project_ids = {str(project.get("id") or "").strip() for project in projects if isinstance(project, dict)}

    report = reconcile(legacy_canvases, sqlite_rows, canvas_authority=authority, known_project_ids=known_project_ids)
    rendered = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    divergent = [comparison.canvas_id for comparison in report.comparisons if not comparison.matches]
    print(
        f"reconciliation: legacy={report.legacy_id_count} sqlite={report.sqlite_row_count} "
        f"legacy_only={len(report.legacy_only_ids)} sqlite_only={len(report.sqlite_only_ids)} "
        f"divergent={len(divergent)} unexpected={len(report.unexpected_rows)} "
        f"authority={report.canvas_authority} converged={report.converged}",
        file=sys.stderr,
    )
    return 0 if report.converged else 1


if __name__ == "__main__":
    raise SystemExit(main())
