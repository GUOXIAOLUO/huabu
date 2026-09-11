#!/usr/bin/env python3
"""Migrate projects.json into SQLite, compare it, and optionally cut over authority."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workbench.application.project_migration import ProjectMigrationService
from workbench.repositories.project_repository import SqliteProjectRepository


def _read_projects(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    projects = payload.get("projects", []) if isinstance(payload, dict) else payload
    if not isinstance(projects, list) or not all(isinstance(item, dict) for item in projects):
        raise ValueError("projects input must be a JSON list or an object with a projects list")
    return projects


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projects", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()

    repository = SqliteProjectRepository(args.database, legacy_projects_path=args.projects)
    service = ProjectMigrationService(repository)
    projects = _read_projects(args.projects)
    report = service.migrate_and_compare(projects, now=datetime.now(UTC))
    if args.activate:
        report = service.activate_after_compare(projects, report)
    output = {"schema_version": "workbench.project-migration-report/1", "project_authority": repository.project_authority(), **report.__dict__}
    output["differences"] = list(output["differences"])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if not report.differences else 1


if __name__ == "__main__":
    raise SystemExit(main())
