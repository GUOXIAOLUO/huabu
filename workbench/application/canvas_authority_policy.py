"""Explicit canonical authority policy for Canvas repository routing.

R4 split-brain guard: when the SQLite authority state is active, the normal
runtime must never silently route writable Canvas traffic to Legacy JSON. The
resolver is a small total function so startup enforcement and per-request
wiring share exactly one decision. Explicit recovery paths (migration
import/compare and the tested lossless rollback export) are unaffected: they
do not route through this policy.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


class CanvasAuthoritySplitBrainError(RuntimeError):
    """Raised when routing would combine active SQLite authority with writable Legacy JSON."""


@dataclass(frozen=True)
class CanvasAuthorityDecision:
    authority_state: str | None
    canonical_routing_enabled: bool
    use_sqlite: bool
    split_brain_forbidden: bool
    reason: str


def resolve_canvas_authority(
    *, authority_state: str | None, canonical_routing_enabled: bool
) -> CanvasAuthorityDecision:
    """Resolve the routing decision; never raises, so diagnostics stay inspectable."""
    if authority_state == "sqlite":
        if canonical_routing_enabled:
            return CanvasAuthorityDecision(
                authority_state=authority_state,
                canonical_routing_enabled=True,
                use_sqlite=True,
                split_brain_forbidden=False,
                reason="sqlite_authority_with_canonical_routing",
            )
        return CanvasAuthorityDecision(
            authority_state=authority_state,
            canonical_routing_enabled=False,
            use_sqlite=False,
            split_brain_forbidden=True,
            reason="sqlite_authority_with_disabled_routing_would_fork_writes",
        )
    if authority_state == "legacy_json":
        return CanvasAuthorityDecision(
            authority_state=authority_state,
            canonical_routing_enabled=canonical_routing_enabled,
            use_sqlite=False,
            split_brain_forbidden=False,
            reason="legacy_json_authority",
        )
    return CanvasAuthorityDecision(
        authority_state=authority_state,
        canonical_routing_enabled=canonical_routing_enabled,
        use_sqlite=False,
        split_brain_forbidden=False,
        reason="authority_state_unavailable",
    )


def read_canvas_authority_state(database_path: str | Path) -> str | None:
    """Tolerantly read ``authority_state`` through a read-only connection.

    A missing, empty, or unreadable database yields ``None`` so the legacy
    recovery path keeps working; only a readable ``authority_state`` row can
    forbid writable Legacy routing.
    """
    path = Path(database_path)
    if not path.exists():
        return None
    try:
        connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "authority_state" not in tables:
            return None
        row = connection.execute("SELECT canvas_authority FROM authority_state WHERE singleton=1").fetchone()
        return str(row["canvas_authority"]) if row else None
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def split_brain_error(decision: CanvasAuthorityDecision) -> CanvasAuthoritySplitBrainError:
    return CanvasAuthoritySplitBrainError(
        "SQLite canvas authority is active but canonical Canvas routing is disabled "
        f"(authority_state={decision.authority_state!r}, "
        f"canonical_routing_enabled={decision.canonical_routing_enabled!r}). "
        "Writable Legacy JSON routing would fork the dataset. Restore one dataset "
        "first: run the tested lossless rollback export to legacy_json authority, "
        "or re-enable canonical routing."
    )
